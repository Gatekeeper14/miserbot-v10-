# ============================================================
# MISERBOT v5.0 (SALES + LEADS + EMAIL + FOLLOW-UP SYSTEM)
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
from apscheduler.schedulers.background import BackgroundScheduler

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

    c.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        chat_id TEXT,
        message TEXT,
        send_time TEXT,
        sent INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ─── 🧠 SYSTEM PROMPT ─────────────────────

SYSTEM_PROMPT = """
You are MiserBot, a high-level AI sales assistant for Miserbot.ai.

You are not an AI. You are a real business representative.

Your job:
- Capture leads
- Understand their business
- Move toward closing

Always:
1. Answer their question
2. Ask ONE question forward

Collect:
- Name
- Business
- Need
- Email

Speak like a confident sales rep, not a robot.
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

# ─── EMAIL ─────────────────────────────

def send_email(name, email, need):
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
            "subject": "🔥 New Lead",
            "content": [{
                "type": "text/plain",
                "value": f"Name: {name}\nEmail: {email}\nNeed: {need}"
            }]
        }
    )

# ─── FOLLOW-UP SYSTEM ───────────────────

FOLLOWUP_TEMPLATES = [
    "Hey {name}, just checking in — still thinking about automating your business?",
    "Quick one {name} — we’ve helped businesses like yours get more clients fast. Want to see how?",
    "Last follow-up {name} — we’re filling spots this week. Want me to hold one for you?"
]

def schedule_followups(user_id, chat_id, name):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    now = datetime.now()

    for i, days in enumerate([1, 3, 7]):
        send_time = (now + timedelta(days=days)).isoformat()
        message = FOLLOWUP_TEMPLATES[i].format(name=name or "there")

        c.execute("""
        INSERT INTO followups (user_id, chat_id, message, send_time)
        VALUES (?, ?, ?, ?)
        """, (user_id, chat_id, message, send_time))

    conn.commit()
    conn.close()

def process_followups():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    now = datetime.now().isoformat()

    c.execute("""
    SELECT id, chat_id, message FROM followups
    WHERE sent = 0 AND send_time <= ?
    """, (now,))

    rows = c.fetchall()

    for fid, chat_id, message in rows:
        send_telegram(chat_id, message)
        c.execute("UPDATE followups SET sent = 1 WHERE id = ?", (fid,))

    conn.commit()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(process_followups, "interval", minutes=5)
scheduler.start()

# ─── LEAD EXTRACTION ─────────────────────

def extract_lead(user_id, chat_id, message):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    email = None
    name = None

    email_match = re.search(r'\S+@\S+\.\S+', message)
    if email_match:
        email = email_match.group()

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

        if email:
            send_email(name, email, message)
            schedule_followups(user_id, chat_id, name)

    conn.close()

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

    extract_lead(chat_id, chat_id, text)

    send_telegram(chat_id, reply)

    return {"ok": True}

# ─── ADMIN ─────────────────────────────

@app.route("/admin/leads")
def leads():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM leads ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return jsonify(rows)

# ─── HEALTH ────────────────────────────

@app.route("/")
def home():
    return {"status": "MiserBot v5.0 LIVE 🚀"}

if __name__ == "__main__":
    app.run(debug=False)
