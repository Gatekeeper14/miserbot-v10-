from flask import Flask, request, Response
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio
client = Client(
    os.environ.get("TWILIO_ACCOUNT_SID"),
    os.environ.get("TWILIO_AUTH_TOKEN")
)
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

# 🧠 simple memory (per user)
users = {}

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    incoming = request.form.get('Body', '').strip()
    from_number = request.form.get('From', '')

    print(f"FROM: {from_number}, MESSAGE: {incoming}")

    if not incoming or not from_number:
        return Response("No message", status=400)

    # initialize user
    if from_number not in users:
        users[from_number] = {"step": "name"}

    step = users[from_number]["step"]

    # 🧠 FLOW LOGIC
    if step == "name":
        users[from_number]["name"] = incoming
        users[from_number]["step"] = "service"
        reply = f"Nice to meet you {incoming}! What service do you need?"

    elif step == "service":
        users[from_number]["service"] = incoming
        users[from_number]["step"] = "contact"
        reply = "Got it 👍 What’s the best email or phone to reach you?"

    elif step == "contact":
        users[from_number]["contact"] = incoming
        users[from_number]["step"] = "done"

        name = users[from_number]["name"]
        service = users[from_number]["service"]
        contact = users[from_number]["contact"]

        print("🔥 NEW LEAD:", name, service, contact)

        reply = f"Thanks {name}! We’ll reach out soon about {service} 👍"

    else:
        reply = "Hey 👋 Want help with something? Just tell me!"

    # send SMS
    message = client.messages.create(
        body=reply,
        from_=twilio_number,
        to=from_number
    )

    print("SENT SID:", message.sid)

    return Response("OK", status=200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
