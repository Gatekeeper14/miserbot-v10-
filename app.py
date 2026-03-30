from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json
from datetime import datetime
from openai import OpenAI
import requests

app = Flask(__name__)
CORS(app)

# =========================
# CONFIG
# =========================
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_KEY = os.getenv("SENDGRID_API_KEY")

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

LEADS_FILE = "leads.json"
sessions = {}

# =========================
# MEMORY
# =========================
def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {
            "messages": [],
            "lead": {"name": None, "email": None, "phone": None},
            "mode": "business"
        }
    return sessions[user_id]

# =========================
# SAVE LEAD + EMAIL
# =========================
def save_lead(lead, mode):

    entry = {
        "name": lead.get("name"),
        "email": lead.get("email"),
        "phone": lead.get("phone"),
        "mode": mode,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # Save locally
    data = []
    if os.path.exists(LEADS_FILE):
        try:
            with open(LEADS_FILE, "r") as f:
                data = json.load(f)
        except:
            data = []

    data.append(entry)

    with open(LEADS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("🔥 SAVED LEAD:", entry)

    # Send email (SAFE — no hanging)
    if SENDGRID_KEY:
        try:
            requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {SENDGRID_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{
                        "to": [{"email": "Miserbot.ai@gmail.com"}]
                    }],
                    "from": {"email": "Miserbot.ai@gmail.com"},
                    "subject": "🔥 New MiserBot Lead",
                    "content": [{
                        "type": "text/plain",
                        "value": f"""
Name: {entry['name']}
Email: {entry['email']}
Phone: {entry['phone']}
Mode: {entry['mode']}
Time: {entry['time']}
"""
                    }]
                },
                timeout=10
            )
            print("📧 Email sent")
        except Exception as e:
            print("⚠️ Email failed:", e)

# =========================
# LEAD EXTRACTION
# =========================
def extract_lead(session, message):

    if not session["lead"]["name"] and len(message.split()) <= 3:
        session["lead"]["name"] = message.strip()

    elif not session["lead"]["email"] and "@" in message:
        session["lead"]["email"] = message.strip()

    elif not session["lead"]["phone"] and any(c.isdigit() for c in message):
        session["lead"]["phone"] = message.strip()

# =========================
# SMART PROMPT (NO LOOPING)
# =========================
def build_prompt(mode, lead):

    name = lead.get("name")
    email = lead.get("email")
    phone = lead.get("phone")

    if not name:
        next_step = "Ask for their name naturally."
    elif not email:
        next_step = "Ask for their email naturally."
    elif not phone:
        next_step = "Ask for their phone naturally."
    else:
        next_step = "All info collected."

    base = "You are a high-end AI business consultant."

    return f"""
{base}

You are also capturing a lead.

STRICT RULES:
- Never repeat a question
- Ask only ONE thing at a time
- Order: name → email → phone
- Be smooth, confident, human

Current:
Name: {name}
Email: {email}
Phone: {phone}

Next:
{next_step}
"""

# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return "👑 MiserBot Running"

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    user_id = request.remote_addr

    print("📩", message)

    session = get_session(user_id)

    extract_lead(session, message)

    if all(session["lead"].values()):
        save_lead(session["lead"], session["mode"])
        session["lead"] = {"name": None, "email": None, "phone": None}
        return jsonify({"reply": "🔥 Done. We’ll contact you shortly."})

    prompt = build_prompt(session["mode"], session["lead"])

    try:
        if not client:
            raise Exception("No API key")

        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": message}
            ]
        )

        reply = res.choices[0].message.content

    except Exception as e:
        print("❌ GPT:", e)
        reply = "Tell me a bit about your business."

    return jsonify({"reply": reply})

# 🔥 FIXED BUTTON ENDPOINT
@app.route("/lead", methods=["POST"])
def lead():
    data = request.json

    save_lead({
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone")
    }, "form")

    return jsonify({"status": "success"})

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
