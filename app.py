from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# MEMORY
# =========================
sessions = {}

def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {
            "messages": [],
            "lead": {
                "name": None,
                "email": None,
                "phone": None
            }
        }
    return sessions[user_id]

# =========================
@app.route("/")
def home():
    return "👑 MiserBot Auto Closer Active"

# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    mode = data.get("mode", "business")
    user_id = request.remote_addr

    session = get_session(user_id)

    # 🧠 Extract lead info automatically
    extract_lead_info(session, message)

    # If lead is complete → save it
    if all(session["lead"].values()):
        print("🔥 AUTO LEAD CAPTURED:", session["lead"])
        session["lead"] = {"name": None, "email": None, "phone": None}
        return jsonify({
            "reply": "🔥 You're all set. Our team will contact you shortly."
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
        print("❌ ERROR:", e)
        return jsonify({"reply": "⚠️ AI temporarily unavailable."})


# =========================
# LEAD EXTRACTION
# =========================
def extract_lead_info(session, message):

    if "@" in message and not session["lead"]["email"]:
        session["lead"]["email"] = message.strip()

    elif any(char.isdigit() for char in message) and len(message) >= 7 and not session["lead"]["phone"]:
        session["lead"]["phone"] = message.strip()

    elif not session["lead"]["name"] and len(message.split()) <= 3:
        session["lead"]["name"] = message.strip()


# =========================
# SMART PROMPTS
# =========================
def build_prompt(mode, lead):

    missing = [k for k, v in lead.items() if not v]

    capture_instruction = ""
    if missing:
        capture_instruction = f"""
Your goal is to naturally collect this missing info: {missing}

Ask casually, one at a time.
Do NOT ask everything at once.
"""

    if mode == "realestate":
        base = """
You are a high-end real estate AI.
Help find properties and guide user to becoming a lead.
"""
    elif mode == "astrology":
        base = """
You are an astrology AI giving readings and engaging users.
"""
    else:
        base = """
You are a sales AI helping businesses automate and grow.
"""

    return base + capture_instruction


# =========================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
