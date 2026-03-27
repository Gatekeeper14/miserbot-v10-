from flask import Flask, request, Response
from twilio.rest import Client
import os

app = Flask(__name__)

account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

client = None
if account_sid and auth_token:
    client = Client(account_sid, auth_token)

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    try:
        incoming = request.form.get('Body')
        from_number = request.form.get('From')

        print(f"FROM: {from_number}, MESSAGE: {incoming}")

        if client and twilio_number:
            message = client.messages.create(
                body="Got your message!",
                from_=twilio_number,
                to=from_number
            )
            print(f"SID: {message.sid}")
        else:
            print("⚠️ Twilio client not configured")

        return Response("OK", status=200)

    except Exception as e:
        print(f"ERROR: {e}")
        return Response("error", status=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
