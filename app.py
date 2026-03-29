from flask import Flask, request, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)

# 🔐 ENV VARIABLES (set these in Railway later)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
EMAIL_API_KEY = os.getenv("EMAIL_API_KEY")  # optional

# 🧠 HOME ROUTE (health check)
@app.route("/", methods=["GET"])
def home():
    return "MiserBot Backend Running 🚀"

# 🔥 LEAD CAPTURE ROUTE
@app.route("/lead", methods=["POST"])
def capture_lead():
    try:
        data = request.json

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 🧾 LOG TO CONSOLE
        print("🔥 NEW LEAD RECEIVED")
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Phone: {phone}")
        print(f"Time: {timestamp}")

        # 📲 SEND TO TELEGRAM (if configured)
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            message = f"""
🔥 NEW LEAD

👤 Name: {name}
📧 Email: {email}
📱 Phone: {phone}
⏰ Time: {timestamp}
            """

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            })

        # 📧 SEND EMAIL (optional - SendGrid)
        if EMAIL_API_KEY:
            requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {EMAIL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{
                        "to": [{"email": "youremail@example.com"}]
                    }],
                    "from": {"email": "bot@miserbot.com"},
                    "subject": "🔥 New Lead",
                    "content": [{
                        "type": "text/plain",
                        "value": f"Name: {name}\nEmail: {email}\nPhone: {phone}\nTime: {timestamp}"
                    }]
                }
            )

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"status": "error"}), 500


# 🚀 START SERVER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
