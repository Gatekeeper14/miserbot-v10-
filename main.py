import requests
from config import TELEGRAM_TOKEN
from services.ai_service import get_ai_response
from services.sms_service import send_sms

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, json=payload)


def handle_telegram_update(data):
    try:
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not text:
            return

        # AI response
        reply = get_ai_response(text)

        # Trigger SMS simulation
        if "text client" in text.lower():
            send_sms("+1234567890", "Client message triggered")

        # 🔥 SEND MESSAGE BACK TO USER
        send_telegram_message(chat_id, reply)

    except Exception as e:
        print("Telegram error:", e)
