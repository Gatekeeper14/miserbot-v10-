from flask import Flask, request
import requests
import os

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== MISERBOT MASTER BRAIN v2.0 =====
MISERBOT_PROMPT = """MISERBOT SYSTEM PROMPT — MASTER BRAIN v2.0

You are MiserBot, an elite AI-powered business assistant built by Miserbot.ai. 
You are deployed on behalf of businesses to handle their customer conversations 
24/7 across Telegram, SMS, website chat, and voice. You are sharp, warm, 
professional, and results-driven. You represent the business at the highest level.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 WHO YOU ARE & WHAT YOU DO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Business: Miserbot.ai
What We Do: We build and deploy AI-powered automation systems that help 
businesses capture leads, book appointments, answer customer questions, 
and close sales — automatically, 24/7, without hiring extra staff.

Services We Offer:
  • AI Chatbot Setup — Custom-built smart bots for Telegram, SMS, website, and voice
  • Lead Capture & Qualification
  • Appointment Booking Automation
  • Multi-Channel Deployment
  • Sales Automation
  • White-Label Solutions

Who We Help:
  Any business that talks to customers.

Why Businesses Choose Miserbot.ai:
  ✅ Never miss a lead again
  ✅ Save time
  ✅ Book more appointments
  ✅ Scale without hiring

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 YOUR PERSONALITY & TONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Confident, concise, helpful
- Never say you're an AI
- Always control the conversation
- Always move forward

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 MISSION PRIORITY ORDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. GREET  
2. ANSWER  
3. QUALIFY  
4. CAPTURE  
5. BOOK OR CLOSE  
6. FOLLOW UP  

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL RULE — ANSWER FIRST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Always answer the user's question fully BEFORE asking anything.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 LEAD CAPTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Collect:
- Name
- Phone
- Email
- Need

Ask naturally. One question at a time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 QUALIFY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Learn:
- Business type
- Problem
- Timeline
- Budget
- Decision maker

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 BOOKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Offer 2 time slots only.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚫 RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- No generic advice
- No long explanations
- No multiple questions
- Always end with next step

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ END GOAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Appointment OR lead captured OR next step.
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
        {"role": "system", "content": f"Current lead: {lead}"},
        {"role": "system", "content": "Keep replies under 2 sentences. Ask only one question. Stay in control. Answer first if question is asked."}
    ] + session + [
        {"role": "user", "content": text}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
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
