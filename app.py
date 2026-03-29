from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ✅ FIX CORS (allows Vercel to talk to Railway)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔐 ENV VARIABLES (make sure these exist in Railway)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# 📧 EMAIL FUNCTION
def send_email(subject, html):
    try:
        msg = MIMEText(html, "html")
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        print("✅ Email sent")

    except Exception as e:
        print("❌ Email error:", e)

# 🌐 ROOT (for testing)
@app.route("/", methods=["GET"])
def home():
    return "MiserBot Website Ready 🚀"

# 🧠 AI CHAT ENDPOINT
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    message = data.get("message")

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a professional AI assistant for GetMiserBot. Help users and guide them to submit their info."},
                    {"role": "user", "content": message}
                ]
            }
        )

        reply = response.json()["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except Exception as e:
        print("❌ Chat error:", e)
        return jsonify({"reply": "⚠️ AI error."})

# 📥 LEAD FORM ENDPOINT
@app.route("/lead", methods=["POST"])
def lead():
    try:
        data = request.json

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        service = data.get("service")

        print("🔥 LEAD RECEIVED:", name, email, phone, service)

        html = f"""
        <h2>🌐 Website Lead</h2>
        <p><b>Name:</b> {name}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Phone:</b> {phone}</p>
        <p><b>Service:</b> {service}</p>
        """

        send_email("New Website Lead", html)

        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ Lead error:", e)
        return jsonify({"status": "error"})
