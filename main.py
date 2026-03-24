import os
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)

# ===== TWILIO SETUP =====
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

client = Client(TWILIO_SID, TWILIO_AUTH)

# ===== SEND SMS FUNCTION =====
def send_sms(to_number, message_text):
    try:
        message = client.messages.create(
            body=message_text,
            from_=TWILIO_NUMBER,
            to=to_number
        )
        print("SMS sent:", message.sid)
    except Exception as e:
        print("SMS error:", e)

# ===== INCOMING SMS WEBHOOK =====
@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    from_number = request.form.get("From")

    print("Incoming:", incoming_msg)

    # Reply back to sender
    send_sms(from_number, f"🔥 Miserbot reply: {incoming_msg}")

    return "OK"

# ===== TEST ON START (OPTIONAL) =====
# Uncomment below if you want startup test message
# send_sms("+1YOUR_REAL_NUMBER", "🔥 Miserbot is LIVE!")

# ===== RUN SERVER =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
