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
        print("❌ Telegram error:", e)

# ---------------- EMAIL SEND (WITH DEBUG) ----------------
def send_email(subject, body):
    print("📧 Attempting to send email...")
    print("EMAIL_USER:", EMAIL_USER)
    print("EMAIL_PASS exists:", bool(EMAIL_PASS))

    if not EMAIL_USER:
        print("❌ EMAIL_USER missing")
        return

    if not EMAIL_PASS:
        print("❌ EMAIL_PASS missing")
        return

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        print("📧 Connecting to Gmail...")

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)

        print("📧 Logged in successfully")

        server.send_message(msg)
        server.quit()

        print("✅ EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("❌ EMAIL FAILED:", str(e))

# ---------------- HOME ----------------
@app.route("/", methods=["GET"])
def home():
    return "MiserBot FULL System Running 🚀"

# ---------------- TEST ----------------
@app.route("/test", methods=["GET"])
def test():
    message = "🔥 DIRECT EMAIL TEST 🔥"

    send_telegram("📲 Running full system test...")
    send_email("Test Lead", message)

    return "Test triggered — check logs"

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

    send_telegram(message)
    send_email("New Lead", message)

    return jsonify({"status": "success"})

# ---------------- SMART TELEGRAM RECEPTIONIST ----------------
user_data = {}

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message", {})

    # 🚨 STOP LOOP
    if message.get("from", {}).get("is_bot"):
        return "ok"

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return "ok"

    user = user_data.get(chat_id, {"step": 0})

    if user["step"] == 0:
        reply = (
            "👋 Welcome to GetMiserBot.com\n\n"
            "We specialize in automated business solutions and client acquisition systems.\n\n"
            "To better assist you, may I have your full name?"
        )
        user["step"] = 1

    elif user["step"] == 1:
        user["name"] = text
        reply = (
            f"Thank you, {user['name']}.\n\n"
            "Could you please provide your best email address so our team can follow up?"
        )
        user["step"] = 2

    elif user["step"] == 2:
        user["email"] = text
        reply = (
            "Great, thank you.\n\n"
            "Lastly, may we have a contact number for direct assistance?"
        )
        user["step"] = 3

    elif user["step"] == 3:
        user["phone"] = text

        message_text = f"""
🔥 NEW LEAD 🔥

Name: {user['name']}
Email: {user['email']}
Phone: {user['phone']}
"""

        send_telegram(message_text)
        send_email("New Lead", message_text)

        reply = (
            "✅ Thank you for your information.\n\n"
            "A representative from GetMiserBot will be contacting you shortly.\n\n"
            "We appreciate your interest."
        )

        user = {"step": 0}

    user_data[chat_id] = user

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": reply})

    return "ok"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
