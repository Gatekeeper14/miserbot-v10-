# ============================================================
# MISERBOT FINAL v7.0 — FULL SALES SYSTEM
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

OPENAI_API_KEY      = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN")
SENDGRID_API_KEY    = os.environ.get("SENDGRID_API_KEY")
ADMIN_EMAIL         = os.environ.get("ADMIN_EMAIL")
STRIPE_PAYMENT_LINK = os.environ.get("STRIPE_PAYMENT_LINK")

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
        business_type TEXT,
        need TEXT,
        lead_score TEXT,
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

# ─── SYSTEM PROMPT ───────────────────────

SYSTEM_PROMPT = """
You are MiserBot from GetMiserBot.com.

You represent MiserBot as a real company ("we", not "I").

Your job:
- Capture leads
- Qualify
- Push toward payment

Always:
- Answer first
- Move conversation forward
- Close when possible

If user shows interest → push payment
If unsure → qualify and guide

Tone:
Confident, direct, professional, slightly aggressive
"""

# ─── MEMORY ─────────────────────────────

def get_history(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM memory WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def save_msg(user_id, role, content):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("INSERT INTO memory VALUES (NULL, ?, ?, ?, ?)",
              (user_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ─── EMAIL ─────────────────────────────

def send_email(name, email, need):
    if not SENDGRID_API_KEY or not ADMIN_EMAIL:
        return

    requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
        json={
            "personalizations": [{"to": [{"email": ADMIN_EMAIL}]}],
            "from": {"email": ADMIN_EMAIL},
            "subject": "🔥 New Lead",
            "content": [{"type": "text/plain",
                         "value": f"Name: {name}\nEmail: {email}\nNeed: {need}"}]
        }
    )

# ─── FOLLOW UPS ─────────────────────────

def schedule_followups(user_id, chat_id, name):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    now = datetime.now()

    msgs = [
        "Hey {name}, still thinking about getting this set up?",
        "Quick one {name} — want help getting this live?",
        "Last call {name} — spots filling up, want in?"
    ]

    for i, d in enumerate([1,3,7]):
        send_time = (now + timedelta(days=d)).isoformat()
        msg = msgs[i].format(name=name or "there")
        c.execute("INSERT INTO followups VALUES (NULL, ?, ?, ?, ?, 0)",
                  (user_id, chat_id, msg, send_time))

    conn.commit()
    conn.close()

def process_followups():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute("SELECT id, chat_id, message FROM followups WHERE sent = 0 AND send_time <= ?", (now,))
    rows = c.fetchall()

    for fid, chat_id, msg in rows:
        send_telegram(chat_id, msg)
        c.execute("UPDATE followups SET sent = 1 WHERE id = ?", (fid,))

    conn.commit()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(process_followups, "interval", minutes=5)
scheduler.start()

# ─── AI CORE ───────────────────────────

def ai_reply(user_id, message):
    msg = message.lower()

    # 🔥 LEAD SCORING
    if any(x in msg for x in ["price","cost","ready","pay","get started","yes"]):
        score = "HOT"
    elif any(x in msg for x in ["interested","how","what"]):
        score = "WARM"
    else:
        score = "COLD"

    # 🧠 BUSINESS TYPE
    biz = None
    if "real estate" in msg: biz="Real Estate"
    elif "barber" in msg or "salon" in msg: biz="Salon"
    elif "restaurant" in msg: biz="Restaurant"

    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("""
    INSERT OR IGNORE INTO leads (user_id, lead_score, business_type, created_at)
    VALUES (?, ?, ?, ?)
    """, (user_id, score, biz, datetime.now().isoformat()))

    c.execute("""
    UPDATE leads SET lead_score=?, business_type=COALESCE(business_type, ?)
    WHERE user_id=?
    """, (score, biz, user_id))

    conn.commit()
    conn.close()

    history = get_history(user_id)

    messages = [
        {"role":"system","content":SYSTEM_PROMPT},
        *history,
        {"role":"user","content":message}
    ]

    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    reply = res.choices[0].message.content

    save_msg(user_id,"user",message)
    save_msg(user_id,"assistant",reply)

    # 💳 PAYMENT AUTO DROP
    if STRIPE_PAYMENT_LINK and score == "HOT":
        reply += f"\n\n💳 Secure your spot:\n{STRIPE_PAYMENT_LINK}"

    return reply

# ─── TELEGRAM ──────────────────────────

def send_telegram(chat_id, text):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": text}
    )

@app.route("/webhook/telegram", methods=["POST"])
def telegram():
    data = request.json
    if "message" not in data:
        return {"ok": True}

    chat_id = str(data["message"]["chat"]["id"])
    text = data["message"].get("text","")

    reply = ai_reply(chat_id, text)
    send_telegram(chat_id, reply)

    return {"ok": True}

# ─── HEALTH ────────────────────────────

@app.route("/")
def home():
    return {"status":"MiserBot v7 LIVE 💰"}

if __name__ == "__main__":
    app.run(debug=False)
