import os
import requests
from urllib.parse import quote

CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php"


def send_whatsapp(message: str) -> bool:
    phone = os.getenv("WHATSAPP_PHONE")
    apikey = os.getenv("CALLMEBOT_APIKEY")

    if not phone or not apikey:
        print(f"[SEM WHATSAPP] {message}")
        return False

    try:
        response = requests.get(
            CALLMEBOT_URL,
            params={"phone": phone, "text": message, "apikey": apikey},
            timeout=10,
        )
        return response.status_code == 200
    except requests.RequestException as e:
        print(f"Erro ao enviar WhatsApp: {e}")
        return False
