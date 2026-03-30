from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# CONFIG
# =========================
LEADS_FILE = "leads.json"

# Twilio (PRE-WIRED OFF)
TWILIO_ENABLED = False
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

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

    # 🚧 FUTURE: Twilio hook (disabled)
    if TWILIO_ENABLED:
        send_sms_notification(lead_entry)

# =========================
# TWILIO PLACEHOLDER
# =========================
def send_sms_notification(lead):
    print("📲 Twilio ready (currently disabled)")
    # When ready, enable and implement

# =========================
@app.route("/")
def home():
    return "👑 MiserBot Empire (Production Mode)"

# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    mode = data.get("mode", "business")
    user_id = request.remote_addr

    session = get_session(user_id)
    session["mode"] = mode

    extract_lead(session, message)

    # If lead complete → save
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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        session["messages"].append({"role": "user", "content": message})
        session["messages"].append({"role": "assistant", "content": reply})

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ GPT ERROR:", e)
        return jsonify({"reply": "⚠️ AI temporarily unavailable."})

# =========================
# LEAD EXTRACTION
# =========================
def extract_lead(session, message):

    if "@" in message and not session["lead"]["email"]:
        session["lead"]["email"] = message.strip()

    elif any(c.isdigit() for c in message) and len(message) >= 7 and not session["lead"]["phone"]:
        session["lead"]["phone"] = message.strip()

    elif not session["lead"]["name"] and len(message.split()) <= 3:
        session["lead"]["name"] = message.strip()

# =========================
# PROMPTS
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
