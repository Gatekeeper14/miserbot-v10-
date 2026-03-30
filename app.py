from flask import Flask, request
import requests
import os

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

MISERBOT_PROMPT = """PASTE YOUR FULL MISERBOT MASTER PROMPT HERE"""

sessions = {}
leads = {}

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
        "need": ""
    })

def call_ai(session, text, lead):
    messages = [
        {"role": "system", "content": MISERBOT_PROMPT},
        {"role": "system", "content": f"Lead: {lead}"}
    ] + session + [
        {"role": "user", "content": text}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )

    return response.choices[0].message.content

def send_reply(user_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": user_id,
        "text": text
    })

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

        session = get_session(user_id)
        lead = get_lead(user_id)

        reply = call_ai(session, text, lead)

        send_reply(user_id, reply)

        session.append({"role": "user", "content": text})
        session.append({"role": "assistant", "content": reply})
        sessions[user_id] = session[-10:]

        return "OK", 200

    except Exception as e:
        print("❌ ERROR:", e)
        return "ERROR", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
