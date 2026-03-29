from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from threading import Thread

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ENV VARIABLES
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")

# SIMPLE MEMORY
user_data = {}

# SENDGRID EMAIL (WITH TIMEOUT - NO HANG)
def send_email(subject, html):
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "personalizations": [
                    {
                        "to": [{"email": EMAIL_USER}],
                        "subject": subject
                    }
                ],
                "from": {"email": EMAIL_USER},
                "content": [
                    {
                        "type": "text/html",
                        "value": html
                    }
                ]
            },
            timeout=10
        )

        print("✅ SendGrid status:", response.status_code)

    except Exception as e:
        print("⚠️ Email failed:", str(e))

# HOME
@app.route("/", methods=["GET"])
def home():
    return "MiserBot System Running 🚀"

# CHAT SYSTEM (RECEPTIONIST + LEAD CAPTURE)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    user_id = "web_user"

    if user_id not in user_data:
        user_data[user_id] = {"step": 0}

    step = user_data[user_id]["step"]

    if step == 0:
        user_data[user_id]["step"] = 1
        return jsonify({
            "reply": "👋 Welcome to GetMiserBot.com\n\nWe specialize in automated business solutions.\n\nMay I have your full name?"
        })

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
            html = f"""
            <h2>🔥 New Chat Lead</h2>
            <p><b>Name:</b> {name}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Phone:</b> {phone}</p>
            """
            send_email("New Chat Lead", html)

        Thread(target=send_async).start()

        user_data[user_id]["step"] = 0

        return jsonify({
            "reply": "✅ Thank you. Our team will contact you shortly."
        })

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
            html = f"""
            <h2>🌐 Website Lead</h2>
            <p><b>Name:</b> {name}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Phone:</b> {phone}</p>
            <p><b>Service:</b> {service}</p>
            """
            send_email("New Website Lead", html)

        Thread(target=send_async).start()

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ Lead error:", e)
        return jsonify({"status": "error"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
