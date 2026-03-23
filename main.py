import os
from twilio.rest import Client

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
        print("✅ SMS sent:", message.sid)
    except Exception as e:
        print("❌ SMS error:", e)

# ===== TEST FUNCTION =====
def test_sms():
    send_sms(
        "+12393490904",   # ← PUT YOUR REAL NUMBER HERE
        "🔥 Miserbot is LIVE!"
    )

# ===== RUN TEST =====
if __name__ == "__main__":
    test_sms()
