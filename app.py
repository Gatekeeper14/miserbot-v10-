from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_USER")  # your email

user_data = {}
processed = set()

# ---------------- TELEGRAM ----------------
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

# ---------------- EMAIL VIA RESEND ----------------
def send_email(subject, body):
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "MiserBot <onboarding@resend.dev>",
                "to": [EMAIL_TO],
                "subject": subject,
                "text": body
            }
        )

        print("EMAIL STATUS:", response.text)

    except Exception as e:
        print("EMAIL ERROR:", e)

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message")

    if not message:
        return "ok"

    if message.get("from", {}).get("is_bot"):
        return "ok"

    msg_id = message.get("message_id")
    if msg_id in processed:
        return "ok"
    processed.add(msg_id)

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if not text:
        return "ok"

    user = user_data.get(chat_id, {"step": 0})

    try:
        if user["step"] == 0:
            reply = "👋 Welcome to GetMiserBot.com\n\nMay I have your full name?"
            user["step"] = 1

        elif user["step"] == 1:
            user["name"] = text
            reply = "Please provide your email address."
            user["step"] = 2

        elif user["step"] == 2:
            user["email"] = text
            reply = "Lastly, your phone number?"
            user["step"] = 3

        elif user["step"] == 3:
            user["phone"] = text

            lead = f"""
🔥 NEW LEAD 🔥

Name: {user['name']}
Email: {user['email']}
Phone: {user['phone']}
"""

            send_email("New Lead", lead)

            reply = "✅ Thank you. We will contact you shortly."

            user = {"step": 0}

        user_data[chat_id] = user

        send_message(chat_id, reply)

    except Exception as e:
        print("CRASH:", e)
        send_message(chat_id, "⚠️ System error. Please try again.")

    return "ok"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "MiserBot FINAL EMAIL SYSTEM 🚀"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
