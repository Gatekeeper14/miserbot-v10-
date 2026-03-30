# ============================================================
# MISERBOT FINAL v9.0 — FULL UI + SALES SYSTEM
# ============================================================

import os
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
        business_type TEXT,
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

You represent MiserBot as a real company ("we").

You are a high-level sales assistant.

Goals:
- Capture leads
- Qualify
- Close
- Push toward payment

Use urgency, authority, and confidence.
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

def send_email_alert(user_id, score, message, biz):
    if not SENDGRID_API_KEY or not ADMIN_EMAIL:
        return

    content = f"""
🔥 NEW LEAD

User: {user_id}
Score: {score}
Business: {biz}

Message:
{message}
"""

    requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"},
        json={
            "personalizations":[{"to":[{"email":ADMIN_EMAIL}]}],
            "from":{"email":ADMIN_EMAIL},
            "subject":f"{score} Lead",
            "content":[{"type":"text/plain","value":content}]
        }
    )

# ─── FOLLOW UPS ─────────────────────────

def schedule_followups(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    now = datetime.now()

    msgs = [
        "Still thinking about automating your business?",
        "We can still get you set up quickly.",
        "Last chance — want to get started?"
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

# ─── AI CORE ───────────────────────────

def ai_reply(user_id, message):
    msg = message.lower()

    if any(x in msg for x in ["price","cost","ready","pay","yes","get started"]):
        score = "HOT"
    elif any(x in msg for x in ["how","what","interested"]):
        score = "WARM"
    else:
        score = "COLD"

    biz = None
    if "real estate" in msg: biz="Real Estate"
    elif "barber" in msg or "salon" in msg: biz="Salon"
    elif "restaurant" in msg: biz="Restaurant"

    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("INSERT OR IGNORE INTO leads (user_id, business_type, lead_score, created_at) VALUES (?, ?, ?, ?)",
              (user_id, biz, score, datetime.now().isoformat()))

    c.execute("UPDATE leads SET lead_score=?, business_type=COALESCE(business_type, ?) WHERE user_id=?",
              (score, biz, user_id))

    conn.commit()
    conn.close()

    history = get_history(user_id)

    messages = [{"role":"system","content":SYSTEM_PROMPT}] + history + [{"role":"user","content":message}]

    res = openai.chat.completions.create(model="gpt-4o", messages=messages)

    reply = res.choices[0].message.content

    save_msg(user_id,"user",message)
    save_msg(user_id,"assistant",reply)

    if score == "HOT":
        send_email_alert(user_id, score, message, biz)
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

# ─── UI DASHBOARD ──────────────────────

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("SELECT user_id, business_type, lead_score, created_at FROM leads ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()

    html = """
    <html>
    <head>
    <title>MiserBot Dashboard</title>
    <style>
    body { background:#0f172a; color:white; font-family:Arial; padding:20px;}
    h1 { color:#38bdf8; }
    .card { background:#1e293b; padding:15px; margin:10px 0; border-radius:10px;}
    .hot { border-left:5px solid #22c55e;}
    .warm { border-left:5px solid #facc15;}
    .cold { border-left:5px solid #ef4444;}
    </style>
    </head>
    <body>
    <h1>🔥 MiserBot Dashboard</h1>
    """

    for r in rows:
        cls = (r[2] or "cold").lower()
        html += f"""
        <div class="card {cls}">
            <b>User:</b> {r[0]}<br>
            <b>Business:</b> {r[1] or "Unknown"}<br>
            <b>Score:</b> {r[2]}<br>
            <b>Time:</b> {r[3]}
        </div>
        """

    html += "</body></html>"
    return html

# ─── HEALTH ────────────────────────────

@app.route("/")
def home():
    return {"status":"MiserBot v9 LIVE 💰"}

if __name__ == "__main__":
    app.run(debug=False)
