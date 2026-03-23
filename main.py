import os
import telebot
import requests
from openai import OpenAI

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_KEY)

watchdog = False

def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except:
        pass

def get_btc():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
        data = r.json()
        return float(data["bitcoin"]["usd"])
    except:
        return None

def ai_reply(user_msg):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are Miserbot X, a smart assistant."},
                {"role": "user", "content": user_msg}
            ]
        )
        return response.choices[0].message.content
    except:
        return "❌ AI error"

@bot.message_handler(commands=['start'])
def start(msg):
    safe_send(msg.chat.id,
"""👑 Miserbot X

1. 💰 Trading
2. ❤️ Family
3. 💳 Credit
4. ⚙️ Status
5. 🤖 Auto
6. 🧠 AI

Type a number or name""")

@bot.message_handler(func=lambda m: True)
def handle(msg):
    global watchdog
    text = msg.text.lower()
    chat_id = msg.chat.id

    if chat_id != ADMIN_ID:
        safe_send(chat_id, "⛔ Access denied")
        return

    if text in ["menu", "start"]:
        start(msg)

    elif text in ["status", "4"]:
        safe_send(chat_id, "✅ Running | AI Active")

    elif text in ["btc", "btc price", "1"]:
        price = get_btc()
        if price:
            safe_send(chat_id, f"💰 BTC: ${price}")
        else:
            safe_send(chat_id, "❌ Price error")

    elif text in ["auto", "5"]:
        watchdog = not watchdog
        safe_send(chat_id, f"🤖 Auto: {'ON' if watchdog else 'OFF'}")

    elif text.startswith("ai "):
        reply = ai_reply(msg.text[3:])
        safe_send(chat_id, f"🧠 {reply}")

    else:
        safe_send(chat_id, "❓ Unknown command")

print("🚀 Miserbot Running")
bot.infinity_polling()
