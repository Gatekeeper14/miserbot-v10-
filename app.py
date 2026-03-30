from flask import Flask, request
import json
import requests
import os

app = Flask(__name__)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== MEMORY =====
sessions = {}
leads = {}

# ===== HELPERS =====
def normalize_message(data):
    message = data.get("message", {})
    return {
        "user_id": str(message.get("chat", {}).get("id")),
        "text": message.get("text", "")
    }

def get_session(user_id):
    return sessions.setdefault(user_id, [])

def get_lead(user_id):
    return leads.setdefault(user_id, {
        "name": "",
        "email": "",
        "phone": "",
        "need": "",
        "score": "cold"
    })

def classify_intent(text):
    text = text.lower()
    if "@" in text:
        return "email"
    if "price" in text or "cost" in text:
        return "pricing"
    if "book" in text:
        return "booking"
    return "general"

# ===== AI TEMP =====
def call_ai(user_text):
    return "Got it — what’s your email?"

# ===== TELEGRAM SEND =====
def send_reply(user_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": text
    }
    requests.post(url, json=payload)

# ===== ROUTES =====
@app.route("/")
def home():
    return "OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        print("🔥 WEBHOOK HIT")

        data = request.json
        msg = normalize_message(data)

        user_id = msg["user_id"]
        text = msg["text"]

        print("📩", text)

        reply = call_ai(text)

        send_reply(user_id, reply)

        return "OK", 200

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR", 500

# ===== RUN (CRITICAL FIX) =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
