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
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")

# ===== TELEGRAM SEND =====
def send_telegram(chat_id, text, buttons=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if buttons:
        payload["reply_markup"] = {
            "keyboard": buttons,
            "resize_keyboard": True,
            "one_time_keyboard": True
        }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("TELEGRAM ERROR:", str(e))

# ===== SENDGRID EMAIL =====
def send_email_async(to_email, subject, message):
    try:
        print("📤 Sending email...")

        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

        email = Mail(
            from_email=EMAIL_USER,
            to_emails=to_email,
            subject=subject,
            plain_text_content=message
        )

        response = sg.send(email)
        print("✅ EMAIL SENT", response.status_code)

    except Exception as e:
        print("❌ EMAIL ERROR:", str(e))

# ===== SAVE LEAD =====
def save_lead(lead):
    try:
        lead["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open("leads.json", "a") as f:
            f.write(json.dumps(lead) + "\n")

        print("💾 LEAD SAVED")

    except Exception as e:
        print("❌ SAVE ERROR:", str(e))

# ===== LEAD SCORING =====
def score_lead(lead):
    score = 0

    if "$" in lead.get("budget", ""):
        try:
            amount = int(re.sub("[^0-9]", "", lead["budget"]))
            if amount >= 500:
                score += 2
            elif amount >= 100:
                score += 1
        except:
            pass

    goal = lead.get("goal", "").lower()
    if "customer" in goal or "sales" in goal:
        score += 1
    if "urgent" in goal or "asap" in goal:
        score += 2

    if score >= 3:
        return "🔥 HOT"
    elif score >= 1:
        return "⚠️ WARM"
    else:
        return "❄️ COLD"

# ===== STATE STORAGE =====
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

        print("📩 MESSAGE:", text)

        # ===== BUTTON HANDLING =====
        if text == "🚀 Start" or text == "🚀 Start Again":
            user_states[chat_id] = "ask_name"
            send_telegram(chat_id, "👋 What’s your name?")
            return "ok"

        if text == "🔄 Restart":
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            send_telegram(chat_id, "🔄 Restarted. Click Start.", buttons=[["🚀 Start"]])
            return "ok"

        if text == "ℹ️ Help":
            send_telegram(
                chat_id,
                "This bot collects your request and connects you with support.\n\nClick Start to begin.",
                buttons=[["🚀 Start"]]
            )
            return "ok"

        # ===== RESET COMMAND =====
        if text == "/start":
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)
            send_telegram(
                chat_id,
                "🔥 Welcome to MiserBot\n\nChoose an option:",
                buttons=[
                    ["🚀 Start"],
                    ["ℹ️ Help", "🔄 Restart"]
                ]
            )
            return "ok"

        # ===== START FLOW =====
        if chat_id not in user_states:
            send_telegram(
                chat_id,
                "Click Start to begin.",
                buttons=[["🚀 Start"]]
            )
            return "ok"

        # ===== NAME =====
        if user_states[chat_id] == "ask_name":
            user_data[chat_id] = {"name": text}
            user_states[chat_id] = "ask_email"
            send_telegram(chat_id, "📧 What’s your best email?")
            return "ok"

        # ===== EMAIL =====
        if user_states[chat_id] == "ask_email":
            email = text.strip()

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                send_telegram(chat_id, "❌ Enter a valid email.")
                return "ok"

            user_data[chat_id]["email"] = email
            user_states[chat_id] = "ask_goal"
            send_telegram(chat_id, "📈 What result are you trying to achieve?")
            return "ok"

        # ===== GOAL =====
        if user_states[chat_id] == "ask_goal":
            user_data[chat_id]["goal"] = text
            user_states[chat_id] = "ask_budget"

            send_telegram(
                chat_id,
                "💰 Select your budget:",
                buttons=[
                    ["$100–$500"],
                    ["$500–$1000"],
                    ["$1000+"]
                ]
            )
            return "ok"

        # ===== FINAL STEP =====
        if user_states[chat_id] == "ask_budget":
            user_data[chat_id]["budget"] = text
            lead = user_data[chat_id]

            # SCORE
            lead_score = score_lead(lead)
            lead["score"] = lead_score

            # SAVE
            save_lead(lead)

            # EMAIL TO YOU
            admin_msg = f"""
🔥 NEW LEAD ({lead_score})

👤 Name: {lead['name']}
📧 Email: {lead['email']}
📈 Goal: {lead['goal']}
💰 Budget: {lead['budget']}

⏱ Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

            threading.Thread(
                target=send_email_async,
                args=(EMAIL_USER, "🔥 New Lead", admin_msg)
            ).start()

            # EMAIL TO CUSTOMER
            customer_msg = f"""
Hi {lead['name']},

Thanks — we received your request:

"{lead['goal']}"

Our team will contact you shortly.

– MiserBot
"""

            threading.Thread(
                target=send_email_async,
                args=(lead['email'], "We received your request", customer_msg)
            ).start()

            # TELEGRAM RESPONSE
            send_telegram(
                chat_id,
                "✅ Thanks! We’ll contact you shortly.",
                buttons=[["🚀 Start Again"]]
            )

            # RESET
            user_states.pop(chat_id, None)
            user_data.pop(chat_id, None)

            return "ok"

        return "ok"

    except Exception as e:
        print("❌ WEBHOOK ERROR:", str(e))
        return "ok"

# ===== HOME =====
@app.route("/")
def home():
    return "🔥 MiserBot Master System Running"

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
