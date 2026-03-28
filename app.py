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
EMAIL_USER = os.getenv("EMAIL_USER")  # must be verified in SendGrid

# ===== TELEGRAM SEND =====
def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        print("TELEGRAM ERROR:", str(e))

# ===== SENDGRID EMAIL (ASYNC + SAFE) =====
def send_email_async(to_email, message):
    try:
        print("Sending via SendGrid...")

        if not SENDGRID_API_KEY:
            print("❌ Missing SENDGRID_API_KEY")
            return

        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

        email = Mail(
            from_email=EMAIL_USER,
            to_emails=to_email,
            subject="📩 Message from MiserBot",
            plain_text_content=message
        )

        response = sg.send(email)

        print("✅ EMAIL SENT (SendGrid)", response.status_code)

    except Exception as e:
        print(f"❌ SENDGRID ERROR: {str(e)}")

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
            send_telegram(chat_id, "🔥 MiserBot X is LIVE\n\nCommands:\n/email\n/ai")
            return "ok"

        # ===== EMAIL COMMAND (NON-BLOCKING SENDGRID) =====
        if text.startswith("/email"):
            try:
                command_removed = text.replace("/email", "", 1).strip()
                first_space = command_removed.find(" ")

                if first_space == -1:
                    send_telegram(chat_id, "❌ Format:\n/email email@example.com Your message")
                    return "ok"

                to_email = command_removed[:first_space].strip()
                message_body = command_removed[first_space:].strip()

                print("EMAIL TO:", to_email)
                print("MESSAGE:", message_body)

                # 🚀 Background thread (instant response)
                thread = threading.Thread(
                    target=send_email_async,
                    args=(to_email, message_body)
                )
                thread.start()

                send_telegram(chat_id, "📤 Sending email...")

            except Exception as e:
                print("EMAIL HANDLER ERROR:", str(e))
                send_telegram(chat_id, f"❌ Email failed: {str(e)}")

            return "ok"

        # ===== AI COMMAND =====
        if text.startswith("/ai"):
            prompt = text.replace("/ai", "", 1).strip()
            reply = get_ai_response(prompt)
            send_telegram(chat_id, reply)
            return "ok"

        # ===== DEFAULT AI =====
        reply = get_ai_response(text)
        send_telegram(chat_id, reply)

        return "ok"

    except Exception as e:
        print("WEBHOOK ERROR:", str(e))
        return "ok"

# ===== HOME =====
@app.route("/")
def home():
    return "🔥 MiserBot Running (SendGrid)"

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
