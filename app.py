from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ENV
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_USER")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

user_data = {}
processed = set()

print("🔥 MISERBOT X LOADED — STABLE + AI + MULTI SERVICE")

# ---------------- TELEGRAM ----------------
def send_message(chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print("TELEGRAM ERROR:", e)

# ---------------- EMAIL ----------------
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
        print("📧 EMAIL:", response.status_code)
    except Exception as e:
        print("EMAIL ERROR:", e)

# ---------------- AI (CONTROLLED) ----------------
def ai_reply(user_message, service):
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
                        "content": f"You are a professional assistant for GetMiserBot specializing in {service}. Keep responses short, clear, and business-focused."
                    },
                    {"role": "user", "content": user_message}
                ]
            }
        )
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Thank you. Let’s get a few details so we can assist you."

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

    # RESET
    if text.lower() == "reset":
        user_data[chat_id] = {"step": 0}
        send_message(chat_id, "🔄 Reset complete.")
        return "ok"

    user = user_data.get(chat_id, {"step": 0})

    try:
        # STEP 0 - MENU
        if user["step"] == 0:
            reply = (
                "👋 Welcome to GetMiserBot.com\n\n"
                "How can we assist you today?\n\n"
                "1️⃣ Business Automation\n"
                "2️⃣ Astrocartography\n"
                "3️⃣ Real Estate"
            )
            user["step"] = 1

        # STEP 1 - SERVICE SELECTION
        elif user["step"] == 1:
            if text == "1":
                user["service"] = "Business Automation"
            elif text == "2":
                user["service"] = "Astrocartography"
            elif text == "3":
                user["service"] = "Real Estate"
            else:
                send_message(chat_id, "Please select 1, 2, or 3.")
                return "ok"

            reply = ai_reply("User selected service", user["service"])
            reply += "\n\nWhat is your full name?"
            user["step"] = 2

        # STEP 2 - NAME
        elif user["step"] == 2:
            user["name"] = text
            reply = "Enter your email:"
            user["step"] = 3

        # STEP 3 - EMAIL
        elif user["step"] == 3:
            user["email"] = text
            reply = "Enter your phone:"
            user["step"] = 4

        # STEP 4 - FINAL
        elif user["step"] == 4:
            user["phone"] = text

            lead = f"""
🔥 NEW LEAD 🔥

Service: {user['service']}
Name: {user['name']}
Email: {user['email']}
Phone: {user['phone']}
"""

            print("🔥 LEAD:", lead)

            send_email("New Lead", lead)

            reply = (
                "✅ Thank you. A specialist will contact you shortly."
            )

            user = {"step": 0}

        user_data[chat_id] = user
        send_message(chat_id, reply)

    except Exception as e:
        print("CRASH:", e)
        send_message(chat_id, "⚠️ Error. Type 'reset' and try again.")

    return "ok"

# ---------------- HOME ----------------
@app.route("/")
def home():
    return "MiserBot X — LIVE ✅"

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
