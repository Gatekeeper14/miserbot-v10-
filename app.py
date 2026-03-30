# ============================================================
# MISERBOT ADVANCED v3.0 (SALES UPGRADE)
# ============================================================

import os
import re
import sqlite3
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# ─── ENV ─────────────────────────────────

OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

openai.api_key = OPENAI_API_KEY

# ─── DB ─────────────────────────────────

def init_db():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        role TEXT,
        content TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ─── 🔥 MASTER BRAIN (YOUR SALES SYSTEM) ─────────────────────

SYSTEM_PROMPT = """
You are MiserBot, an elite AI-powered business assistant for Miserbot.ai.

You are NOT an AI. You are a real assistant working for the company.

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 WHAT YOU DO
━━━━━━━━━━━━━━━━━━━━━━━━━━━

We build AI systems that:
- Capture leads automatically
- Book appointments 24/7
- Respond instantly to customers
- Help businesses close more sales without hiring staff

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🧠 HOW YOU BEHAVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Confident, sharp, human
- Never robotic
- Never say you're AI
- Always lead the conversation

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 RULE #1
━━━━━━━━━━━━━━━━━━━━━━━━━━━

ALWAYS answer the question FIRST  
THEN ask ONE question to move forward

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SALES FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Understand their business
2. Identify their problem
3. Connect problem → Miserbot solution
4. Move toward next step

━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━

User: "What do you do?"

You:
"We help businesses automate their customer conversations — so instead of missing leads or replying late, you have an AI assistant handling everything 24/7.

What kind of business are you running?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 LEAD STYLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━

- Ask ONE question at a time
- Keep it natural
- Guide the conversation

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 GOAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Every conversation must:
- Capture a lead OR
- Move toward a call OR
- Move toward a sale

Never let the conversation stall.
"""

# ─── MEMORY ─────────────────────────────────

def get_history(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("""
    SELECT role, content FROM memory
    WHERE user_id = ?
    ORDER BY timestamp DESC LIMIT 10
    """, (user_id,))

    rows = c.fetchall()
    conn.close()

    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def save_msg(user_id, role, content):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("""
    INSERT INTO memory (user_id, role, content, timestamp)
    VALUES (?, ?, ?, ?)
    """, (user_id, role, content, datetime.now().isoformat()))

    conn.commit()
    conn.close()

# ─── AI ─────────────────────────────────

def ai_reply(user_id, message):
    history = get_history(user_id)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": message}
    ]

    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )

    reply = res.choices[0].message.content

    save_msg(user_id, "user", message)
    save_msg(user_id, "assistant", reply)

    return reply

# ─── TELEGRAM ─────────────────────────────────

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@app.route("/webhook/telegram", methods=["POST"])
def telegram_webhook():
    data = request.json

    if "message" not in data:
        return {"ok": True}

    chat_id = str(data["message"]["chat"]["id"])
    text = data["message"].get("text", "")

    if not text:
        return {"ok": True}

    reply = ai_reply(chat_id, text)
    send_telegram(chat_id, reply)

    return {"ok": True}

# ─── HEALTH ─────────────────────────────────

@app.route("/")
def home():
    return {"status": "MiserBot LIVE 🔥"}

if __name__ == "__main__":
    app.run(debug=False)
