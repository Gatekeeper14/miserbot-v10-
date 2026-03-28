import os
import requests
from flask import Flask, request
import threading
import sendgrid
from sendgrid.helpers.mail import Mail

app = Flask(__name__)

# ===== ENV VARIABLES =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")  # verified sender

# ===== TELEGRAM SEND =====
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("TELEGRAM ERROR:", str(e))

# ===== SENDGRID EMAIL =====
def send_email_async(to_email, message):
    try:
        print("Sending via SendGrid...")

        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

        email = Mail(
            from_email=EMAIL_USER,
            to_emails=to_email,
            subject="🔥 New Lead from MiserBot",
            plain_text_content=message
        )

        response = sg.send(email)
        print("✅ EMAIL SENT (SendGrid)", response.status_code)

    except Exception as e:
        print("❌ SENDGRID ERROR:", str(e))

# ===== AI FUNCTION =====
def get_ai_response(user_text):
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": user_text}]
        }

        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            json=data,
            headers=headers
        )

        return r.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI ERROR:", str(e))
        return "⚠️ AI error"

# ===== LEAD STORAGE =====
user_states = {}
user_data = {}

# ===== WEBHOOK =====
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        message = data.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")

        if not chat_id:
            return "ok"

        print("MESSAGE:", text)

        # ===== START =====
        if text == "/start":
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            send_telegram(chat_id, "🔥 MiserBot X is LIVE\n\nType anything to begin 🚀")
            return "ok"

        # ===== START LEAD FLOW =====
        if chat_id not in user_states:
            user_states[chat_id] = "ask_name"
            send_telegram(chat_id, "👋 What's your name?")
            return "ok"

        # ===== NAME =====
        if user_states[chat_id] == "ask_name":
            user_data[chat_id] = {"name": text}
            user_states[chat_id] = "ask_email"
            send_telegram(chat_id, "📧 What's your email?")
            return "ok"

        # ===== EMAIL =====
        if user_states[chat_id] == "ask_email":
            user_data[chat_id]["email"] = text
            user_states[chat_id] = "ask_need"
            send_telegram(chat_id, "💬 What do you need help with?")
            return "ok"

        # ===== NEED =====
        if user_states[chat_id] == "ask_need":
            user_data[chat_id]["need"] = text

            lead = user_data[chat_id]

            message_body = f"""
🔥 NEW LEAD

Name: {lead['name']}
Email: {lead['email']}
Request: {lead['need']}
"""

            # 🚀 SEND LEAD TO YOUR EMAIL
            thread = threading.Thread(
                target=send_email_async,
                args=("miserbot.ai@gmail.com", message_body)
            )
            thread.start()

            send_telegram(chat_id, "✅ Thanks! We'll contact you soon.")

            # RESET USER
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)

            return "ok"

        return "ok"

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return "ok"

# ===== HOME =====
@app.route("/")
def home():
    return "🔥 MiserBot Running (Lead System Active)"

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
