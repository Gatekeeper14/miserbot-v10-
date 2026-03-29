from flask import Flask, request
import requests
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

user_data = {}
processed_messages = set()

# ---------------- TELEGRAM REPLY ONLY ----------------
def send_message(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

# ---------------- EMAIL (ONLY LEAD OUTPUT) ----------------
def send_email(subject, body):
    try:
        print("📧 Sending email...")

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        print("✅ EMAIL SENT")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message")

    if not message:
        return "ok"

    # 🚨 Ignore bot messages
    if message.get("from", {}).get("is_bot"):
        return "ok"

    message_id = message.get("message_id")

    # 🚨 Prevent duplicates
    if message_id in processed_messages:
        return "ok"
    processed_messages.add(message_id)

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not text:
        return "ok"

    user = user_data.get(chat_id, {"step": 0})

    # FLOW
    if user["step"] == 0:
        reply = (
            "👋 Welcome to GetMiserBot.com\n\n"
            "We specialize in automated business solutions.\n\n"
            "May I have your full name?"
        )
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

        # 🚨 ONLY EMAIL — NO TELEGRAM
        send_email("New Lead", lead)

        reply = "✅ Thank you. Our team will contact you shortly."

        # reset clean
        user = {"step": 0}

    user_data[chat_id] = user

    send_message(chat_id, reply)

    return "ok"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "MiserBot EMAIL-ONLY MODE ✅"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
