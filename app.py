# ============================================================
# MISERBOT v4.0 (SALES + LEADS + EMAIL ALERTS)
# ============================================================

import os
import re
import sqlite3
import logging
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# ─── ENV ─────────────────────────────────

OPENAI_API_KEY     = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SENDGRID_API_KEY   = os.environ.get("SENDGRID_API_KEY")
ADMIN_EMAIL        = os.environ.get("ADMIN_EMAIL")

openai.api_key = OPENAI_API_KEY

# ─── DATABASE ────────────────────────────

def init_db():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE,
        name TEXT,
        email TEXT,
        need TEXT,
        created_at TEXT
    )
    """)

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

# ─── 🧠 MASTER BRAIN ─────────────────────

SYSTEM_PROMPT = """
You are MiserBot, an elite AI business assistant for Miserbot.ai.

You are a real representative, not an AI.

Your job:
- Capture leads
- Understand needs
- Move toward sales

Always:
1. Answer question
2. Ask ONE question forward

Collect:
- Name
- Business
- Need
- Email (later)

Never let conversation die.
"""

# ─── MEMORY ─────────────────────────────

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

# ─── LEAD EXTRACTION ─────────────────────

def extract_lead(user_id, message):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    email = None
    name  = None

    email_match = re.search(r'\S+@\S+\.\S+', message)
    if email_match:
        email = email_match.group()

    # crude name capture
    if "my name is" in message.lower():
        name = message.split("is")[-1].strip()

    if email or name:
        c.execute("""
        INSERT OR IGNORE INTO leads (user_id, name, email, need, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, email, message, datetime.now().isoformat()))

        c.execute("""
        UPDATE leads
        SET name = COALESCE(name, ?),
            email = COALESCE(email, ?),
            need = ?
        WHERE user_id = ?
        """, (name, email, message, user_id))

        conn.commit()

        # send email alert if email captured
        if email:
            send_email_alert(name, email, message)

    conn.close()

# ─── EMAIL ALERT ─────────────────────────

def send_email_alert(name, email, need):
    if not SENDGRID_API_KEY or not ADMIN_EMAIL:
        return

    requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "personalizations": [{"to": [{"email": ADMIN_EMAIL}]}],
            "from": {"email": ADMIN_EMAIL},
            "subject": "🔥 New MiserBot Lead",
            "content": [{
                "type": "text/plain",
                "value": f"Name: {name}\nEmail: {email}\nNeed: {need}"
            }]
        }
    )

# ─── AI ────────────────────────────────

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

    extract_lead(user_id, message)

    return reply

# ─── TELEGRAM ──────────────────────────

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

# ─── ADMIN VIEW ─────────────────────────

@app.route("/admin/leads")
def view_leads():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    return jsonify(rows)

# ─── HEALTH ────────────────────────────

@app.route("/")
def home():
    return {"status": "MiserBot v4.0 LIVE 🔥"}

if __name__ == "__main__":
    app.run(debug=False)
