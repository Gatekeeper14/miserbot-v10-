from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import smtplib
from email.mime.text import MIMEText
from threading import Thread

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ENV
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# TEMP MEMORY (per session)
user_data = {}

# EMAIL
def send_email(subject, html):
    try:
        msg = MIMEText(html, "html")
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent")

    except Exception as e:
        print("❌ EMAIL ERROR:", str(e))

# HOME
@app.route("/", methods=["GET"])
def home():
    return "MiserBot System Running 🚀"

# CHAT + RECEPTIONIST SYSTEM
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    user_id = "web_user"  # simple session

    if user_id not in user_data:
        user_data[user_id] = {"step": 0}

    step = user_data[user_id]["step"]

    # STEP FLOW
    if step == 0:
        user_data[user_id]["step"] = 1
        return jsonify({"reply": "👋 Welcome to GetMiserBot.com\n\nWe specialize in automated business solutions.\n\nMay I have your full name?"})

    elif step == 1:
        user_data[user_id]["name"] = message
        user_data[user_id]["step"] = 2
        return jsonify({"reply": "Thank you. What is your best email address?"})

    elif step == 2:
        user_data[user_id]["email"] = message
        user_data[user_id]["step"] = 3
        return jsonify({"reply": "Perfect. Lastly, may I have your phone number?"})

    elif step == 3:
        user_data[user_id]["phone"] = message

        name = user_data[user_id]["name"]
        email = user_data[user_id]["email"]
        phone = user_data[user_id]["phone"]

        print("🔥 CHAT LEAD:", name, email, phone)

        # SEND EMAIL ASYNC
        def send_async():
            try:
                html = f"""
                <h2>🔥 New Chat Lead</h2>
                <p><b>Name:</b> {name}</p>
                <p><b>Email:</b> {email}</p>
                <p><b>Phone:</b> {phone}</p>
                """
                send_email("New Chat Lead", html)
            except Exception as e:
                print("Email failed:", e)

        Thread(target=send_async).start()

        user_data[user_id]["step"] = 0  # reset

        return jsonify({"reply": "✅ Thank you. Our team will contact you shortly."})

# FORM LEAD (WEBSITE FORM)
@app.route("/lead", methods=["POST"])
def lead():
    try:
        data = request.json

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        service = data.get("service")

        print("🔥 FORM LEAD:", name, email, phone, service)

        def send_async():
            try:
                html = f"""
                <h2>🌐 Website Lead</h2>
                <p><b>Name:</b> {name}</p>
                <p><b>Email:</b> {email}</p>
                <p><b>Phone:</b> {phone}</p>
                <p><b>Service:</b> {service}</p>
                """
                send_email("New Website Lead", html)
            except Exception as e:
                print("Email failed:", e)

        Thread(target=send_async).start()

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ Lead error:", e)
        return jsonify({"status": "error"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
