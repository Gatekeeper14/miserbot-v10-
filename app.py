from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================
# MEMORY STORE
# =========================
sessions = {}

def get_session(user_id):
    if user_id not in sessions:
        sessions[user_id] = {"messages": []}
    return sessions[user_id]

# =========================
@app.route("/")
def home():
    return "👑 MiserBot AI Brain Active"

# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "")
    mode = data.get("mode", "business")
    user_id = request.remote_addr

    session = get_session(user_id)

    system_prompt = build_system_prompt(mode)

    # Build conversation history
    messages = [{"role": "system", "content": system_prompt}] + session["messages"]
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        reply = response.choices[0].message.content

        # Save memory
        session["messages"].append({"role": "user", "content": message})
        session["messages"].append({"role": "assistant", "content": reply})

        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ GPT ERROR:", e)
        return jsonify({"reply": "⚠️ AI is temporarily unavailable."})


# =========================
# SYSTEM PROMPTS (THE REAL MAGIC)
# =========================
def build_system_prompt(mode):

    if mode == "realestate":
        return """
You are a high-end real estate AI assistant.

Your job:
- Help users find properties
- Ask for location, budget, rent/buy
- Sound professional and confident
- Guide them toward becoming a lead

Always:
- Be concise
- Ask questions
- Move toward closing the user
"""

    elif mode == "astrology":
        return """
You are a mystical but accurate astrology AI.

Your job:
- Provide engaging readings
- Talk about love, money, and future
- Ask for birth details when needed
- Sound confident and insightful

Keep responses intriguing but clear.
"""

    else:
        return """
You are MiserBot — an elite AI sales assistant.

Your job:
- Talk to business owners
- Understand their problems
- Offer automation solutions
- Move them toward becoming a lead

You should:
- Ask questions step-by-step
- Be persuasive but not pushy
- Sound premium and intelligent
- Lead them to submit their contact info
"""


# =========================
# LEAD CAPTURE
# =========================
@app.route("/lead", methods=["POST"])
def lead():
    data = request.json

    print("🔥 LEAD:", data)

    return jsonify({"status": "ok"})


# =========================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
