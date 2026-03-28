from flask import Flask, request, Response
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio setup
client = Client(
    os.environ.get("TWILIO_ACCOUNT_SID"),
    os.environ.get("TWILIO_AUTH_TOKEN")
)

twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

# 🧠 simple memory
users = {}

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    raw_body = request.form.get('Body', '').strip()
    from_number = request.form.get('From', '')

    print(f"FROM: {from_number}, RAW MESSAGE: {raw_body}")

    if not raw_body or not from_number:
        return Response("No message", status=400)

    # 🔥 Handle multi-line input
    parts = [p.strip() for p in raw_body.split("\n") if p.strip()]

    # init user
    if from_number not in users:
        users[from_number] = {}

    user = users[from_number]

    # 🧠 Assign data based on what’s missing
    if "name" not in user and len(parts) >= 1:
        user["name"] = parts[0]

    if "service" not in user and len(parts) >= 2:
        user["service"] = parts[1]

    if "contact" not in user and len(parts) >= 3:
        user["contact"] = parts[2]

    # 🧠 Decide next step
    if "name" not in user:
        reply = "Hey 👋 What’s your name?"

    elif "service" not in user:
        reply = f"Nice to meet you {user['name']}! What service do you need?"

    elif "contact" not in user:
        reply = "Got it 👍 What’s the best email or phone to reach you?"

    else:
        # 🔥 Lead complete
        print("🔥 NEW LEAD:", user["name"], user["service"], user["contact"])

        reply = f"Thanks {user['name']}! We’ll reach out soon about {user['service']} 👍"

        # optional: reset user for new leads later
        users[from_number] = {}

    # 📤 send SMS
    try:
        message = client.messages.create(
            body=reply,
            from_=twilio_number,
            to=from_number
        )
        print("SENT SID:", message.sid)
    except Exception as e:
        print("SEND ERROR:", e)

    return Response("OK", status=200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
