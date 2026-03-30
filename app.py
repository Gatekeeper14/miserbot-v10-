from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# =========================
# SYSTEM ROOT
# =========================
@app.route("/")
def home():
    return "👑 MiserBot Empire Running"

# =========================
# CHAT ROUTE (MULTI MODE)
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").lower()
    mode = data.get("mode", "business")

    print(f"🔥 MODE: {mode} | MESSAGE: {message}")

    if mode == "realestate":
        reply = real_estate_ai(message)

    elif mode == "astrology":
        reply = astrology_ai(message)

    else:
        reply = business_ai(message)

    return jsonify({"reply": reply})


# =========================
# BUSINESS AI (SALES CLOSER)
# =========================
def business_ai(msg):

    if "price" in msg or "cost" in msg:
        return "💼 Our automation systems typically range from $99–$499/month depending on scale. What type of business are you running?"

    if "what do you do" in msg:
        return "We build AI systems that capture leads, respond instantly, and close clients through chat, SMS, and automation."

    if "hi" in msg or "hello" in msg:
        return "👋 Welcome to MiserBot. What kind of business do you own?"

    return "Tell me about your business and I’ll show you how we can automate and increase your revenue."


# =========================
# REAL ESTATE AI
# =========================
def real_estate_ai(msg):

    if "rent" in msg:
        return "🏡 Looking to rent? Tell me your city and budget."

    if "buy" in msg:
        return "🏡 Looking to buy? Share location + price range."

    if any(city in msg for city in ["miami", "orlando", "tampa"]):
        return "🔥 I found properties in your area. What’s your budget range?"

    return "🏡 Tell me:\n• Location\n• Budget\n• Rent or Buy\n\nI’ll match you with properties."


# =========================
# ASTROLOGY AI
# =========================
def astrology_ai(msg):

    if "love" in msg:
        return "❤️ Your love energy shows strong emotional alignment coming soon. Are you currently in a relationship?"

    if "money" in msg:
        return "💰 Financial energy is shifting — new opportunities are opening. Stay aligned and focused."

    if "birth" in msg:
        return "🔮 Give me your birth date, time, and city for a full reading."

    return "🔮 Ask about love, money, or your future — or provide your birth details for a full reading."


# =========================
# LEAD CAPTURE
# =========================
@app.route("/lead", methods=["POST"])
def lead():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    interest = data.get("interest", "unknown")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("🔥 NEW LEAD")
    print("Name:", name)
    print("Email:", email)
    print("Phone:", phone)
    print("Interest:", interest)
    print("Time:", timestamp)

    # You already have SendGrid working — keep it here if needed

    return jsonify({"status": "success"})


# =========================
# HEALTH CHECK
# =========================
@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
