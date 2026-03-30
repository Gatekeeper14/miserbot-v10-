# ============================================================
# MISERBOT ADVANCED v3.0 (FIXED + DEPLOYABLE)
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
from twilio.rest import Client as TwilioClient
from twilio.twiml.messaging_response import MessagingResponse
import stripe
from apscheduler.schedulers.background import BackgroundScheduler

# ─── APP INIT ────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# ─── ENV ─────────────────────────────────────────────────────

OPENAI_API_KEY      = os.environ.get("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN")
TWILIO_ACCOUNT_SID  = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN   = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
STRIPE_SECRET_KEY   = os.environ.get("STRIPE_SECRET_KEY")
STRIPE_PAYMENT_LINK = os.environ.get("STRIPE_PAYMENT_LINK")

openai.api_key = OPENAI_API_KEY
stripe.api_key = STRIPE_SECRET_KEY
twilio_client  = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ─── DATABASE ────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            channel TEXT,
            name TEXT,
            phone TEXT,
            email TEXT,
            business_type TEXT,
            need TEXT,
            budget TEXT,
            timeline TEXT,
            lead_score TEXT DEFAULT 'COLD',
            appointment_time TEXT,
            paid INTEGER DEFAULT 0,
            created_at TEXT,
            last_seen TEXT
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

# ─── SYSTEM PROMPT (YOUR BRAIN) ──────────────────────────────

SYSTEM_PROMPT = """You are MiserBot, an elite AI assistant for Miserbot.ai.
You capture leads, qualify, and close. Always answer first, then move forward.
Keep responses short, confident, and always ask ONE question.
"""

# ─── MEMORY ──────────────────────────────────────────────────

def get_history(user_id):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM memory WHERE user_id=? ORDER BY id DESC LIMIT 10", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

def save_message(user_id, role, content):
    conn = sqlite3.connect("miserbot.db")
    c = conn.cursor()
    c.execute("INSERT INTO memory VALUES (NULL, ?, ?, ?, ?)",
              (user_id, role, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ─── AI CORE ─────────────────────────────────────────────────

def ai_reply(user_id, text):
    history = get_history(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [
        {"role": "user", "content": text}
    ]

    res = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.4
    )

    reply = res.choices[0].message.content

    save_message(user_id, "user", text)
    save_message(user_id, "assistant", reply)

    return reply

# ─── TELEGRAM ────────────────────────────────────────────────

def send_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

@app.route("/webhook/telegram", methods=["POST"])
def telegram():
    data = request.json

    if "message" not in data:
        return jsonify({"ok": True})

    chat_id = str(data["message"]["chat"]["id"])
    text = data["message"].get("text", "")

    if not text:
        return jsonify({"ok": True})

    reply = ai_reply(chat_id, text)
    send_telegram(chat_id, reply)

    return jsonify({"ok": True})

# ─── SMS ─────────────────────────────────────────────────────

@app.route("/webhook/sms", methods=["POST"])
def sms():
    from_number = request.form.get("From")
    body = request.form.get("Body")

    reply = ai_reply(from_number, body)

    resp = MessagingResponse()
    resp.message(reply)

    return str(resp)

# ─── HEALTH ──────────────────────────────────────────────────

@app.route("/")
def home():
    return "MiserBot v3 Running", 200

# ─── RUN ─────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
