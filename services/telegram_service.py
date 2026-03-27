from services.ai_service import get_ai_response
from services.sms_service import send_sms

def handle_telegram_update(data):
    try:
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not text:
            return

        # AI response (mock for now)
        reply = get_ai_response(text)

        # simulate sending SMS trigger
        if "text client" in text.lower():
            send_sms("+1234567890", "Client message triggered")

        print(f"[Telegram] {chat_id}: {reply}")

    except Exception as e:
        print("Telegram error:", e)
