from flask import Flask, request, jsonify
import requests
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ENV VARIABLES
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ---------------- TELEGRAM SEND ----------------
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print("Telegram error:", e)

# ---------------- EMAIL SEND ----------------
def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

    except Exception as e:
        print("Email error:", e)

# ---------------- HOME ----------------
@app.route("/", methods=["GET"])
def home():
    return "MiserBot FULL System Running 🚀"

# ---------------- TEST ----------------
@app.route("/test", methods=["GET"])
def test():
    message = """
🔥 TEST LEAD 🔥

Name: Test User
Email: test@test.com
Phone: 1234567890
"""

    send_telegram(message)
    send_email("Test Lead", message)

    return "Test sent ✅"

# ---------------- LEAD CAPTURE ----------------
@app.route("/lead", methods=["POST"])
def capture_lead():
    data = request.json

    name = data.get("name", "N/A")
    email = data.get("email", "N/A")
    phone = data.get("phone", "N/A")

    message = f"""
🔥 NEW LEAD 🔥

Name: {name}
Email: {email}
Phone: {phone}
"""

    print("NEW LEAD:", name, email, phone)

    send_telegram(message)
    send_email("New Lead", message)

    return jsonify({"status": "success"})

# ---------------- TELEGRAM RECEPTIONIST ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return "ok"

    # SIMPLE AUTO RESPONSE
    reply = "👋 Welcome! Send your name, email, and phone and we’ll contact you."

    if "hi" in text.lower():
        reply = "👋 Hey! Looking for services? Send your details and we’ll reach out."

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply})

    return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
