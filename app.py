from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import smtplib
from email.mime.text import MIMEText
from threading import Thread

app = Flask(__name__)

# ✅ Enable CORS (Vercel → Railway)
CORS(app, resources={r"/*": {"origins": "*"}})

# 🔐 ENV VARIABLES (set in Railway)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# 📧 EMAIL FUNCTION (stable)
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

# 🌐 ROOT
@app.route("/", methods=["GET"])
def home():
    return "MiserBot Website Ready 🚀"

# 🧠 AI CHAT (CONNECTED TO SITE)
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

# 📥 LEAD (NO TIMEOUT — ASYNC EMAIL)
@app.route("/lead", methods=["POST"])
def lead():
    try:
        data = request.json

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        service = data.get("service")

        print("🔥 LEAD RECEIVED:", name, email, phone, service)

        # 🚀 SEND EMAIL IN BACKGROUND (NO BLOCKING)
        def send_async_email():
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
                print("⚠️ Email failed:", e)

        Thread(target=send_async_email).start()

        # ✅ INSTANT RESPONSE (NO TIMEOUT EVER)
        return jsonify({"status": "success"})

    except Exception as e:
        print("❌ Lead error:", e)
        return jsonify({"status": "error"})

# 🚀 START APP (Railway uses this with Gunicorn)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
