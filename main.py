from flask import Flask, request
import requests
import os

app = Flask(__name__)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # safer to load from env

@app.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 WEBHOOK HIT")
    data = request.json
    print("Received JSON:", data)

    message = data.get("message")
    if not message:
        print("⚠️ No message payload, skipping")
        return "ok"

    chat_id = message.get("chat", {}).get("id")
    text = message.get("text")

    if not chat_id or not text:
        print("⚠️ Missing chat_id or text, skipping")
        return "ok"

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": f"AI Response: {text}"}
        r = requests.post(url, json=payload)
        print("SEND STATUS:", r.status_code, r.text)
    except Exception as e:
        print("❌ Failed to send message:", e)

    return "ok"
