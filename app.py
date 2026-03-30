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

# MEMORY (simple session)
user_data = {}

# SEND EMAIL (NON-BLOCKING SAFE)
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
            timeout=10  # 🔥 prevents hanging
        )

        print("✅ SendGrid status:", response.status_code)

    except Exception as e:
        print("⚠️ Email failed:", str(e))

# ROOT
@app.route("/", methods=["GET"])
def home():
    return "MiserBot System Running 🚀"

# CHAT (ALWAYS ALIVE + LEAD CAPTURE)
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message", "").strip()
    msg_lower = message.lower()
    user_id = "web_user"

    # INIT USER
    if user_id not in user_data:
        user_data[user_id] = {"step": 0}

    # 🔥 ALWAYS RESTART COMMAND
    if msg_lower in ["hi", "hello", "start", "reset"]:
        user_data[user_id] = {"step": 1}
        return jsonify({
            "reply": "👋 Welcome to GetMiserBot.com\n\nWe specialize in automated business solutions.\n\nMay I have your full name?"
        })

    step = user_data[user_id].get("step", 0)

    try:
        # STEP 1 → NAME
        if step == 1:
            user_data[user_id]["name"] = message
            user_data[user_id]["step"] = 2
            return jsonify({"reply": "Thank you. What is your best email address?"})

        # STEP 2 → EMAIL
        elif step == 2:
            user_data[user_id]["email"] = message
            user_data[user_id]["step"] = 3
            return jsonify({"reply": "Perfect. Lastly, may I have your phone number?"})

        # STEP 3 → PHONE + SEND EMAIL
        elif step == 3:
            user_data[user_id]["phone"] = message

            name = user_data[user_id]["name"]
            email = user_data[user_id]["email"]
            phone = user_data[user_id]["phone"]

            print("🔥 CHAT LEAD:", name, email, phone)

            # 🔥 SEND EMAIL IN BACKGROUND (SIMULTANEOUS)
            def send_async():
                html = f"""
                <h2>🔥 New Chat Lead</h2>
                <p><b>Name:</b> {name}</p>
                <p><b>Email:</b> {email}</p>
                <p><b>Phone:</b> {phone}</p>
                """
                send_email("New Chat Lead", html)

            Thread(target=send_async).start()

            # RESET FLOW
            user_data[user_id] = {"step": 0}

            return jsonify({
                "reply": "✅ Thank you. Our team will contact you shortly.\n\nType 'hi' anytime to start again."
            })

        # FALLBACK (RECOVERY MODE)
        else:
            user_data[user_id] = {"step": 1}
            return jsonify({
                "reply": "👋 Welcome to GetMiserBot.com\n\nMay I have your full name?"
            })

    except Exception as e:
        print("❌ Chat error:", e)
        user_data[user_id] = {"step": 0}
        return jsonify({"reply": "⚠️ System reset. Please type 'hi' to start again."})

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

        # 🔥 SEND EMAIL IN BACKGROUND
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
