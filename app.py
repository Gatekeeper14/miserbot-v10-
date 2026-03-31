# ============================================================
# MISERBOT MASTER v12 — FULL SYSTEM (SALES + EMAIL + ONBOARD)
# ============================================================

import os
import re
import sqlite3
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, request
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
        email TEXT,
        lead_score TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS onboarding (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        business_name TEXT,
        service_type TEXT,
        contact_pref TEXT,
        completed INTEGER DEFAULT 0
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

You represent a real company. Always speak as "we".

We provide AI automation systems that help businesses capture leads,
book appointments, and close sales automatically.

We CAN:
- send emails
- follow up automatically
- onboard clients
- process payments

Never say you can't do something.

STYLE:
Confident, direct, persuasive, slightly urgent.

GOAL:
Capture → Qualify → Close → Onboard → Deliver

Always move the conversation forward toward payment or onboarding.
"""

# ─── MEMORY ─────────────────────────────

def get_history(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM memory WHERE user_id=? ORDER BY timestamp DESC LIMIT 10", (user_id,))
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

# ─── EMAIL ALERT ─────────────────────────

def send_email_alert(user_id, email):
    if not SENDGRID_API_KEY or not ADMIN_EMAIL:
        return

    requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
        json={
            "personalizations":[{"to":[{"email":ADMIN_EMAIL}]}],
            "from":{"email":ADMIN_EMAIL},
            "subject":"🔥 New MiserBot Lead",
            "content":[{"type":"text/plain","value":f"User: {user_id}\nEmail: {email}"}]
        }
    )

# ─── FOLLOW UPS ─────────────────────────

def schedule_followups(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    now = datetime.now()

    msgs = [
        "Hey — still thinking about automating your business?",
        "We can still get you set up this week.",
        "Last chance to secure your spot — want in?"
    ]

    for i, d in enumerate([1,3,7]):
        c.execute("INSERT INTO followups VALUES (NULL, ?, ?, ?, ?, 0)",
                  (user_id, user_id, msgs[i], (now + timedelta(days=d)).isoformat()))

    conn.commit()
    conn.close()

def process_followups():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    now = datetime.now().isoformat()

    c.execute("SELECT id, chat_id, message FROM followups WHERE sent=0 AND send_time<=?", (now,))
    rows = c.fetchall()

    for fid, chat_id, msg in rows:
        send_telegram(chat_id, msg)
        c.execute("UPDATE followups SET sent=1 WHERE id=?", (fid,))

    conn.commit()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(process_followups, "interval", minutes=5)
scheduler.start()

# ─── ONBOARDING ─────────────────────────

def start_onboarding(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO onboarding (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    return "🎉 You're in. Let’s get your system built.\n\nWhat’s your business name?"

def handle_onboarding(user_id, message):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("SELECT business_name, service_type, contact_pref FROM onboarding WHERE user_id=?", (user_id,))
    row = c.fetchone()

    if not row[0]:
        c.execute("UPDATE onboarding SET business_name=? WHERE user_id=?", (message, user_id))
        conn.commit()
        conn.close()
        return "What service do you provide?"

    elif not row[1]:
        c.execute("UPDATE onboarding SET service_type=? WHERE user_id=?", (message, user_id))
        conn.commit()
        conn.close()
        return "How should we contact you?"

    elif not row[2]:
        c.execute("UPDATE onboarding SET contact_pref=?, completed=1 WHERE user_id=?", (message, user_id))
        conn.commit()
        conn.close()
        return "🔥 Setup complete. We’ll reach out and begin building your system."

    conn.close()
    return None

def is_onboarding(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("SELECT completed FROM onboarding WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 0

# ─── AI CORE ───────────────────────────

def ai_reply(user_id, message):

    msg = message.lower()

    if "paid" in msg or "done" in msg:
        return start_onboarding(user_id)

    if is_onboarding(user_id):
        response = handle_onboarding(user_id, message)
        if response:
            return response

    # lead scoring
    if any(x in msg for x in ["price","cost","ready","pay","yes"]):
        score = "HOT"
    elif any(x in msg for x in ["how","what","interested"]):
        score = "WARM"
    else:
        score = "COLD"

    # email detection
    email_match = re.search(r'\S+@\S+\.\S+', message)
    email = email_match.group() if email_match else None

    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO leads (user_id, email, lead_score, created_at) VALUES (?, ?, ?, ?)",
              (user_id, email, score, datetime.now().isoformat()))

    if email:
        c.execute("UPDATE leads SET email=? WHERE user_id=?", (email, user_id))
        send_email_alert(user_id, email)

    c.execute("UPDATE leads SET lead_score=? WHERE user_id=?", (score, user_id))

    conn.commit()
    conn.close()

    history = get_history(user_id)

    messages = [{"role":"system","content":SYSTEM_PROMPT}] + history + [{"role":"user","content":message}]

    res = openai.chat.completions.create(model="gpt-4o", messages=messages)
    reply = res.choices[0].message.content

    save_msg(user_id,"user",message)
    save_msg(user_id,"assistant",reply)

    if score == "HOT":
        schedule_followups(user_id)

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

# ─── DASHBOARD ─────────────────────────

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("SELECT user_id, email, lead_score FROM leads ORDER BY created_at DESC")
    leads = c.fetchall()

    c.execute("SELECT user_id, business_name, service_type, contact_pref, completed FROM onboarding")
    onboard = c.fetchall()

    conn.close()

    html = "<h1>🔥 MiserBot Dashboard</h1>"

    html += "<h2>Leads</h2>"
    for l in leads:
        html += f"<div>{l}</div>"

    html += "<h2>Onboarding</h2>"
    for o in onboard:
        html += f"<div>{o}</div>"

    return html

# ─── HEALTH ────────────────────────────

@app.route("/")
def home():
    return {"status":"MiserBot MASTER v12 LIVE 💰"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
