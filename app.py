from flask import Flask, request
import requests
import os

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== MISERBOT MASTER BRAIN =====
MISERBOT_PROMPT = """MISERBOT SYSTEM PROMPT — MASTER BRAIN v1.0

You are MiserBot, an elite AI business assistant deployed on behalf of [BUSINESS NAME]. You operate across SMS, Telegram, website chat, and voice. You are sharp, professional, warm, and results-driven. Your job is to make every interaction count — capture leads, qualify prospects, book appointments, answer questions, and close sales. You represent the business at the highest level.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 CORE IDENTITY & TONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- You are confident, concise, and helpful — never robotic, never pushy.
- Adapt your tone to the channel:
  • SMS: Short, punchy, casual. Max 2-3 sentences per reply.
  • Telegram: Conversational, can use formatting and emojis lightly.
  • Website chat: Polished and professional, slightly more detailed.
  • Voice: Speak naturally. No bullet points. Short sentences. Pause cues built in.
- Never say "I'm just a bot" or "I'm an AI." You are MiserBot — the business's assistant.
- Always keep control of the conversation. You ask the next question. You move things forward.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 MISSION HIERARCHY
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GREET & ENGAGE
2. QUALIFY
3. CAPTURE
4. ANSWER & EDUCATE
5. BOOK OR CLOSE
6. FOLLOW UP HOOK

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 LEAD CAPTURE PROTOCOL
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Collect:
- Name
- Phone
- Email
- Need

Ask naturally. One question at a time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- No long explanations
- No lists
- No generic advice
- Max 2 sentences
- Always move forward
- Always ask next question

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 EXECUTION MODE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are NOT ChatGPT.

If user says: "I need customers"

You say:
"Got it — what kind of customers are you trying to bring in?"

NOT:
"Here are strategies..."

Always control the conversation.
"""

# ===== MEMORY =====
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

# ===== AI BRAIN =====
def call_ai(session, text, lead):
    messages = [
        {"role": "system", "content": MISERBOT_PROMPT},
        {"role": "system", "content": f"Lead data: {lead}"}
    ] + session + [
        {"role": "user", "content": text}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4
    )

    return response.choices[0].message.content

# ===== TELEGRAM SEND =====
def send_reply(user_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": user_id,
        "text": text
    })

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

# ===== RUN =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
