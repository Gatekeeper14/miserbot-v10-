from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_USER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBSITE_URL = os.getenv("WEBSITE_URL")

user_data = {}
processed = set()

print("🔥 MISERBOT X — WEBSITE READY")

# ---------------- TELEGRAM ----------------
def send_message(chat_id, text, buttons=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": buttons
        }

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json=payload
    )

# ---------------- EMAIL ----------------
def send_email(subject, body):
    try:
        requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": "MiserBot <onboarding@resend.dev>",
                "to": [EMAIL_TO],
                "subject": subject,
                "html": body
            }
        )
        print("📧 EMAIL SENT")
    except Exception as e:
        print("EMAIL ERROR:", e)

# ---------------- AI ----------------
def ai_reply(service):
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a professional assistant for {service}. Keep it short and persuasive."
                    }
                ]
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Let’s get a few details so we can assist you."

# ---------------- WEBHOOK ----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # BUTTON CLICK HANDLER
    if "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        choice = query["data"]

        user = user_data.get(chat_id, {"step": 1})

        services = {
            "automation": "Business Automation",
            "astro": "Astrocartography",
            "realestate": "Real Estate"
        }

        user["service"] = services.get(choice, "General")

        reply = ai_reply(user["service"]) + "\n\nWhat is your full name?"
        user["step"] = 2

        user_data[chat_id] = user

        send_message(chat_id, reply)

        return "ok"

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

    # RESET
    if text.lower() == "reset":
        user_data[chat_id] = {"step": 0}
        send_message(chat_id, "🔄 Reset complete.")
        return "ok"

    user = user_data.get(chat_id, {"step": 0})

    try:
        # STEP 0 - SHOW BUTTON MENU
        if user["step"] == 0:
            buttons = [
                [{"text": "🤖 Business Automation", "callback_data": "automation"}],
                [{"text": "🌍 Astrocartography", "callback_data": "astro"}],
                [{"text": "🏠 Real Estate", "callback_data": "realestate"}]
            ]

            send_message(
                chat_id,
                "👋 Welcome to GetMiserBot.com\n\nSelect a service below:",
                buttons
            )

            user["step"] = 1

        # STEP 2 - NAME
        elif user["step"] == 2:
            user["name"] = text
            send_message(chat_id, "Enter your email:")
            user["step"] = 3

        # STEP 3 - EMAIL
        elif user["step"] == 3:
            user["email"] = text
            send_message(chat_id, "Enter your phone:")
            user["step"] = 4

        # STEP 4 - FINAL
        elif user["step"] == 4:
            user["phone"] = text

            lead_html = f"""
<h2>🔥 New Lead</h2>
<p><b>Service:</b> {user['service']}</p>
<p><b>Name:</b> {user['name']}</p>
<p><b>Email:</b> {user['email']}</p>
<p><b>Phone:</b> {user['phone']}</p>

<br>
<a href="{WEBSITE_URL}">🌐 Visit Your Website</a>
"""

            send_email("New Lead", lead_html)

            send_message(chat_id, "✅ Thank you. We will contact you shortly.")

            user = {"step": 0}

        user_data[chat_id] = user

    except Exception as e:
        print("CRASH:", e)
        send_message(chat_id, "⚠️ Error. Type 'reset'.")

    return "ok"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "MiserBot Website Ready 🚀"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
