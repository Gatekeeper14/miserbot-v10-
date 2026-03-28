import os
import requests
from flask import Flask, request
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ====== ENV VARIABLES ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMAIL_USER = os.getenv("EMAIL_USER")   # your gmail
EMAIL_PASS = os.getenv("EMAIL_PASS")   # 16-char app password

# ====== TELEGRAM SEND ======
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

# ====== EMAIL FUNCTION ======
def send_email(to_email, subject, message):
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        return "✅ Email sent successfully"

    except Exception as e:
        return f"❌ Email error: {str(e)}"

# ====== AI RESPONSE ======
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

        r = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
        return r.json()["choices"][0]["message"]["content"]

    except:
        return "⚠️ AI error"

# ====== WEBHOOK ======
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return "ok"

    print("MESSAGE:", text)

    # ===== COMMANDS =====

    # /start
    if text == "/start":
        send_telegram(chat_id, "🔥 MiserBot X is LIVE\n\nCommands:\n/email\n/ai")
        return "ok"

    # /email test@example.com Hello world
    if text.startswith("/email"):
        try:
            parts = text.split(" ", 2)
            to_email = parts[1]
            message_body = parts[2]

            result = send_email(
                to_email,
                "📩 Message from MiserBot",
                message_body
            )

            send_telegram(chat_id, result)

        except:
            send_telegram(chat_id, "❌ Format:\n/email email@example.com Your message")

        return "ok"

    # /ai your question
    if text.startswith("/ai"):
        prompt = text.replace("/ai", "").strip()

        reply = get_ai_response(prompt)
        send_telegram(chat_id, reply)
        return "ok"

    # ===== DEFAULT AI CHAT =====
    reply = get_ai_response(text)
    send_telegram(chat_id, reply)

    return "ok"


# ====== HEALTH CHECK ======
@app.route("/")
def home():
    return "🔥 MiserBot Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
