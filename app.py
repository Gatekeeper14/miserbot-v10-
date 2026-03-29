from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ENV VARIABLES (set these in Railway)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram not configured")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }

    try:
        requests.post(url, json=data)
    except Exception as e:
        print("Telegram error:", e)

# ROOT ROUTE (health check)
@app.route("/", methods=["GET"])
def home():
    return "MiserBot Backend Running 🚀"

# LEAD CAPTURE ROUTE
@app.route("/lead", methods=["POST"])
def capture_lead():
    data = request.json

    name = data.get("name", "N/A")
    email = data.get("email", "N/A")
    phone = data.get("phone", "N/A")

    print("NEW LEAD:", name, email, phone)

    message = f"""
🔥 NEW LEAD 🔥

Name: {name}
Email: {email}
Phone: {phone}
"""

    send_telegram(message)

    return jsonify({"status": "success"})

# START SERVER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
