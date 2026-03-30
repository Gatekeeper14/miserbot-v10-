from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# =========================
# OPENAI SAFE INIT
# =========================
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_KEY:
    client = OpenAI(api_key=OPENAI_KEY)
else:
    client = None
    print("❌ OPENAI_API_KEY MISSING")

# =========================
# CONFIG
# =========================
LEADS_FILE = "leads.json"

TWILIO_ENABLED = False  # keep OFF

# =========================
# MEMORY
# =========================
sessions = {}

def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {
            "messages": [],
            "lead": {"name": None, "email": None, "phone": None},
            "mode": "business"
        }
    return sessions[user_id]

# =========================
# SAVE LEAD
# =========================
def save_lead(lead, mode):
    data = []

    if os.path.exists(LEADS_FILE):
        with open(LEADS_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = []

    lead_entry = {
        "name": lead["name"],
        "email": lead["email"],
        "phone": lead["phone"],
        "mode": mode,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    data.append(lead_entry)

    with open(LEADS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("🔥 SAVED LEAD:", lead_entry)

# =========================
@app.route("/")
def home():
    return "👑 MiserBot Running"

# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    mode = data.get("mode", "business")
    user_id = request.remote_addr

    print("📩 Incoming:", message)

    session = get_session(user_id)
    session["mode"] = mode

    extract_lead(session, message)

    if all(session["lead"].values()):
        save_lead(session["lead"], mode)

        session["lead"] = {"name": None, "email": None, "phone": None}

        return jsonify({
            "reply": "🔥 You're all set. We’ll contact you shortly."
        })

    system_prompt = build_prompt(mode, session["lead"])

    messages = [{"role": "system", "content": system_prompt}] + session["messages"]
    messages.append({"role": "user", "content": message})

    try:
        if not client:
            raise Exception("No OpenAI client")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        print("🤖 GPT:", reply)

    except Exception as e:
        print("❌ GPT ERROR:", str(e))

        reply = "I’m here — tell me about your business and I’ll guide you step by step."

    session["messages"].append({"role": "user", "content": message})
    session["messages"].append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply})

# =========================
def extract_lead(session, message):

    if "@" in message and not session["lead"]["email"]:
        session["lead"]["email"] = message.strip()

    elif any(c.isdigit() for c in message) and len(message) >= 7 and not session["lead"]["phone"]:
        session["lead"]["phone"] = message.strip()

    elif not session["lead"]["name"] and len(message.split()) <= 3:
        session["lead"]["name"] = message.strip()

# =========================
def build_prompt(mode, lead):

    missing = [k for k, v in lead.items() if not v]

    capture = ""
    if missing:
        capture = f"""
Your goal is to collect this info naturally: {missing}
Ask casually, one at a time.
"""

    if mode == "realestate":
        base = "You are a luxury real estate AI helping users find homes and become leads."
    elif mode == "astrology":
        base = "You are an astrology AI giving engaging and insightful readings."
    else:
        base = "You are a high-end AI sales assistant helping businesses automate and grow."

    return base + capture

# =========================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
