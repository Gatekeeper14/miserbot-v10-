from flask import Flask, request, Response
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio credentials from Railway
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    incoming = request.form.get('Body')
    from_number = request.form.get('From')

    print(f"FROM: {from_number}, MESSAGE: {incoming}")

    # 🔥 FORCE send message from your number
    message = client.messages.create(
        body="Got your message!",
        from_=twilio_number,
        to=from_number
    )

    print(f"SID: {message.sid}")

    return Response("OK", status=200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
