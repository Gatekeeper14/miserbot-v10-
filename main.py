import os
from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

@app.route("/")
def home():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if chat_id and text:
        reply = f"AI Response: {text}"

        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": reply
        }

        requests.post(url, json=payload)

    return "ok"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
