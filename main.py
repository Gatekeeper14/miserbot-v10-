from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    incoming = request.form.get('Body')
    from_number = request.form.get('From')

    print(f"FROM: {from_number}, MESSAGE: {incoming}")

    resp = MessagingResponse()
    resp.message("Got your message!")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
