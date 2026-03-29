from flask import Flask, request, jsonify
import requests
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

user_data = {}

# ---------------- TELEGRAM ----------------
def send_telegram(message):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": message}
    )

# ---------------- EMAIL ----------------
def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email error:", e)

# ---------------- AI RESPONSE ----------------
def ai_reply(user_message):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a professional AI business assistant for GetMiserBot. Speak clearly, professionally, and help qualify the user."},
                    {"role": "user", "content": user_message}
                ]
            }
        )

        return response.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("AI error:", e)
        return "Thank you for reaching out. Could you provide more details about your request?"

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    message = data.get("message", {})

    if message.get("from", {}).get("is_bot"):
        return "ok"

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "").strip()

    if not chat_id:
        return "ok"

    user = user_data.get(chat_id, {"step": "intent"})

    # STEP 1: Understand intent
    if user["step"] == "intent":
        user["intent"] = text

        reply = ai_reply(text) + "\n\nTo better assist you, may I have your full name?"
        user["step"] = "name"

    elif user["step"] == "name":
        user["name"] = text
        reply = "Thank you. Please provide your email address."
        user["step"] = "email"

    elif user["step"] == "email":
        user["email"] = text
        reply = "Great. Lastly, your phone number?"
        user["step"] = "phone"

    elif user["step"] == "phone":
        user["phone"] = text

        lead = f"""
🔥 NEW LEAD 🔥

Service: {user.get('intent')}
Name: {user['name']}
Email: {user['email']}
Phone: {user['phone']}
"""

        send_telegram(lead)
        send_email("New Lead", lead)

        reply = "✅ Thank you. Our team will contact you shortly."

        user = {"step": "intent"}

    user_data[chat_id] = user

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": reply}
    )

    return "ok"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "MiserBot Claw Mode Running 🚀"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
