import os
import telebot
import requests
from openai import OpenAI

# ====== ENV VARIABLES ======
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_KEY)

# ====== STATE ======
watchdog = False

# ====== SAFE SEND ======
def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except:
        pass

# ====== BTC PRICE ======
def get_btc():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
        data = r.json()
        return float(data["bitcoin"]["usd"])
    except:
        return None

# ====== AI RESPONSE ======
def ai_reply(user_msg):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Miserbot X, a powerful royal AI assistant. Keep replies short, smart, and useful."},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    except:
        return "❌ AI not responding"

# ====== COMMANDS ======

@bot.message_handler(commands=['start'])
def start(msg):
    safe_send(msg.chat.id,
"""👑 Miserbot X

1. 💰 Trading
2. ❤️ Family
3. 💳 Credit
4. ⚙️ Status
5. 🤖 Auto Mode
6. 🧠 AI

Type a number or name""")

@bot.message_handler(func=lambda m: True)
def handle(msg):
    global watchdog

    text = msg.text.lower()
    chat_id = msg.chat.id

    # ===== ADMIN LOCK =====
    if chat_id != ADMIN_ID:
        safe_send(chat_id, "⛔ Access denied")
        return

    # ===== MENU =====
    if text in ["menu", "start"]:
        start(msg)

    # ===== STATUS =====
    elif text in ["4", "status"]:
        safe_send(chat_id, "✅ Running\nPlan: AI ENABLED")

    # ===== BTC =====
    elif text in ["1", "btc", "btc price"]:
        price = get_btc()
        if price:
            safe_send(chat_id, f"💰 BTC: ${price}")
        else:
            safe_send(chat_id, "❌ Price error")

    # ===== AUTO MODE =====
    elif text in ["5", "auto"]:
        watchdog = not watchdog
        state = "ON" if watchdog else "OFF"
        safe_send(chat_id, f"🤖 Auto Mode: {state}")

    # ===== AI MODE =====
    elif text.startswith("ai "):
        user_msg = msg.text[3:]
        reply = ai_reply(user_msg)
        safe_send(chat_id, f"🧠 {reply}")

    # ===== DEFAULT =====
    else:
        safe_send(chat_id, "❓ Unknown command")

# ===== RUN =====
print("🚀 Miserbot X V48 Running...")
bot.infinity_polling()
