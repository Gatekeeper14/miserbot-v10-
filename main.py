import os
import telebot
import requests
import time
import threading
from openai import OpenAI

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_KEY)

watchdog = False
family_contacts = {}
family_state = {}
auto_family = {}
last_sent = {}

# ===== SAFE SEND =====
def safe_send(chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except:
        pass

# ===== BTC =====
def get_btc():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
        return float(r.json()["bitcoin"]["usd"])
    except:
        return None

# ===== AI =====
def ai_reply(msg):
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": msg}
            ]
        )
        return res.choices[0].message.content
    except:
        return "❌ AI error"

# ===== FAMILY =====
def add_contact(user, name, target):
    if user not in family_contacts:
        family_contacts[user] = {}
    family_contacts[user][name.lower()] = target

def list_contacts(user):
    if user not in family_contacts or not family_contacts[user]:
        return "No contacts saved"
    return "\n".join([f"- {n}" for n in family_contacts[user]])

def send_contact(user, name, msg):
    target = family_contacts.get(user, {}).get(name.lower())
    if not target:
        return False
    try:
        bot.send_message(target, f"📩 {msg}")
        return True
    except:
        return False

# ===== AUTO FAMILY LOOP =====
def auto_family_loop():
    while True:
        now = time.time()

        for user, enabled in auto_family.items():
            if not enabled:
                continue

            contacts = family_contacts.get(user, {})
            if not contacts:
                continue

            if now - last_sent.get(user, 0) < 21600:
                continue

            for name, target in contacts.items():
                try:
                    msg = ai_reply(f"Write a short caring message to {name}")
                    bot.send_message(target, f"❤️ {msg}")
                except:
                    pass

            last_sent[user] = now

        time.sleep(60)

threading.Thread(target=auto_family_loop, daemon=True).start()

# ===== START =====
@bot.message_handler(commands=['start'])
def start(msg):
    safe_send(msg.chat.id,
"""👑 Miserbot X

1. BTC
2. Family
3. Status
4. Auto
5. AI

Commands:
family auto on / off""")

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle(msg):
    global watchdog

    text = msg.text.lower()
    chat = msg.chat.id

    if chat != ADMIN_ID:
        safe_send(chat, "⛔ Access denied")
        return

    # STATUS
    if text in ["status", "3"]:
        safe_send(chat, "✅ Running")

    # BTC
    elif text in ["btc", "1"]:
        price = get_btc()
        safe_send(chat, f"💰 BTC: ${price}" if price else "❌ Error")

    # AUTO
    elif text in ["auto", "4"]:
        watchdog = not watchdog
        safe_send(chat, f"🤖 Auto {'ON' if watchdog else 'OFF'}")

    # AI
    elif text.startswith("ai "):
        reply = ai_reply(msg.text[3:])
        safe_send(chat, f"🧠 {reply}")

    # ===== FAMILY MENU =====
    elif text in ["family", "2"]:
        family_state[chat] = "menu"
        safe_send(chat,
"""❤️ Family

1 Add
2 Send
3 List
4 AI msg""")

    elif family_state.get(chat) == "menu":
        if text == "1":
            family_state[chat] = "add_name"
            safe_send(chat, "Name?")
        elif text == "2":
            family_state[chat] = "send_name"
            safe_send(chat, "Who?")
        elif text == "3":
            safe_send(chat, list_contacts(chat))
        elif text == "4":
            family_state[chat] = "ai_msg"
            safe_send(chat, "What to say?")

    elif family_state.get(chat) == "add_name":
        family_state[chat] = {"step": "id", "name": text}
        safe_send(chat, "Chat ID?")

    elif isinstance(family_state.get(chat), dict) and family_state[chat].get("step") == "id":
        add_contact(chat, family_state[chat]["name"], text)
        family_state[chat] = "menu"
        safe_send(chat, "✅ Saved")

    elif family_state.get(chat) == "send_name":
        family_state[chat] = {"step": "msg", "name": text}
        safe_send(chat, "Message?")

    elif isinstance(family_state.get(chat), dict) and family_state[chat].get("step") == "msg":
        ok = send_contact(chat, family_state[chat]["name"], text)
        safe_send(chat, "✅ Sent" if ok else "❌ Fail")
        family_state[chat] = "menu"

    elif family_state.get(chat) == "ai_msg":
        msg_ai = ai_reply(text)
        safe_send(chat, f"🤖 {msg_ai}")
        family_state[chat] = "menu"

    # AUTO FAMILY
    elif text == "family auto on":
        auto_family[chat] = True
        safe_send(chat, "❤️ Auto ON")

    elif text == "family auto off":
        auto_family[chat] = False
        safe_send(chat, "🛑 Auto OFF")

    else:
        safe_send(chat, "❓ Unknown")

print("🚀 Running")
bot.infinity_polling()
