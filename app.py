from flask import Flask, request
import json

app = Flask(__name__)

# ===== MEMORY =====
sessions = {}
leads = {}

# ===== CONFIG =====
MISERBOT_PROMPT = """PASTE YOUR MASTER PROMPT HERE LATER"""

# ===== HELPERS =====
def normalize_message(data):
    message = data.get("message", {})
    return {
        "channel": "telegram",
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
    if any(x in text for x in ["price", "cost"]):
        return "pricing"
    if any(x in text for x in ["book", "appointment"]):
        return "booking"
    return "general"

# ===== AI (TEMP) =====
def call_ai(session, user_text, intent, lead):
    return {
        "reply": "Got it — what’s your email?",
        "actions": [],
        "lead_update": {}
    }

# ===== ACTIONS =====
def execute_actions(decision, lead):
    updates = decision.get("lead_update", {})
    for k, v in updates.items():
        if k in lead:
            lead[k] = v

    if "save_lead" in decision.get("actions", []):
        print("💾 Lead saved:", lead)

    if "send_email" in decision.get("actions", []):
        print("📧 Email sent")

# ===== REPLY (TEMP) =====
def send_reply(user_id, text):
    print(f"📤 Reply to {user_id}: {text}")

# ===== ROUTES =====
@app.route("/")
def home():
    return "Miserbot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        print("🔥 WEBHOOK HIT")

        data = request.json
        msg = normalize_message(data)

        user_id = msg["user_id"]
        text = msg["text"]

        print("📩 Incoming:", text)

        # MEMORY
        session = get_session(user_id)
        lead = get_lead(user_id)

        # INTENT
        intent = classify_intent(text)
        print("🧠 Intent:", intent)

        # AI DECISION
        decision = call_ai(session, text, intent, lead)

        reply = decision.get("reply", "Got it.")
        print("🤖 Reply:", reply)

        # ACTIONS
        execute_actions(decision, lead)

        # REPLY
        send_reply(user_id, reply)

        # MEMORY UPDATE
        session.append({"role": "user", "content": text})
        session.append({"role": "assistant", "content": reply})
        sessions[user_id] = session[-10:]

        print("🧾 Lead:", lead)

        return "OK", 200

    except Exception as e:
        print("❌ ERROR:", str(e))
        return "ERROR", 500

# ===== RUN =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
