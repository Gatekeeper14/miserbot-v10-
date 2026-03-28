import os
import requests
from flask import Flask, request
import threading
import sendgrid
from sendgrid.helpers.mail import Mail
import json
from datetime import datetime
import re

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
            subject="🔥 MiserBot Notification",
            plain_text_content=message
        )

        response = sg.send(email)
        print("✅ EMAIL SENT (SendGrid)", response.status_code)

    except Exception as e:
        print("❌ SENDGRID ERROR:", str(e))

# ===== SAVE LEADS =====
def save_lead(lead):
    try:
        lead["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("leads.json", "a") as f:
            f.write(json.dumps(lead) + "\n")

        print("✅ LEAD SAVED")

    except Exception as e:
        print("❌ SAVE ERROR:", str(e))

# ===== LEAD FLOW STORAGE =====
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

        # ===== RESET =====
        if text == "/start":
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            send_telegram(chat_id, "🔥 Welcome to MiserBot\n\nLet’s get you set up.")
            return "ok"

        # ===== START FLOW =====
        if chat_id not in user_states:
            user_states[chat_id] = "ask_name"
            send_telegram(chat_id, "👋 What’s your name?")
            return "ok"

        # ===== NAME =====
        if user_states[chat_id] == "ask_name":
            user_data[chat_id] = {"name": text}
            user_states[chat_id] = "ask_email"
            send_telegram(chat_id, "📧 What’s your best email so we can contact you?")
            return "ok"

        # ===== EMAIL (VALIDATION) =====
        if user_states[chat_id] == "ask_email":
            email = text.strip()

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                send_telegram(chat_id, "❌ Please enter a valid email address.")
                return "ok"

            user_data[chat_id]["email"] = email
            user_states[chat_id] = "ask_goal"
            send_telegram(chat_id, "📈 What result are you trying to achieve?")
            return "ok"

        # ===== GOAL =====
        if user_states[chat_id] == "ask_goal":
            user_data[chat_id]["goal"] = text
            user_states[chat_id] = "ask_budget"
            send_telegram(chat_id, "💰 Do you have a budget in mind?")
            return "ok"

        # ===== FINAL STEP =====
        if user_states[chat_id] == "ask_budget":
            user_data[chat_id]["budget"] = text

            lead = user_data[chat_id]

            # SAVE LEAD
            save_lead(lead)

            # EMAIL TO YOU
            message_body = f"""
🔥 HIGH VALUE LEAD

👤 Name: {lead['name']}
📧 Email: {lead['email']}
📈 Goal: {lead['goal']}
💰 Budget: {lead['budget']}

⏱ Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

            thread = threading.Thread(
                target=send_email_async,
                args=(EMAIL_USER, message_body)
            )
            thread.start()

            # AUTO EMAIL TO CUSTOMER
            customer_message = f"""
Hi {lead['name']},

Thanks for reaching out — we received your request:

"{lead['goal']}"

Our team is reviewing your details and will contact you shortly.

If your request is urgent, feel free to reply to this email.

– MiserBot Team
"""

            thread2 = threading.Thread(
                target=send_email_async,
                args=(lead['email'], customer_message)
            )
            thread2.start()

            # TELEGRAM CONFIRMATION
            send_telegram(
                chat_id,
                "✅ Thanks! Your request has been received.\n\nWe’ll contact you shortly."
            )

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
    return "🔥 MiserBot Business System Running"

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
