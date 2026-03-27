from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging

app = Flask(__name__)

# Silence default logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/")
def home():
    return "MiserBot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 TWILIO HIT")

    incoming_msg = request.form.get("Body")
    from_number = request.form.get("From")

    print("FROM:", from_number)
    print("MESSAGE:", incoming_msg)

    resp = MessagingResponse()
    resp.message(f"Bot received: {incoming_msg}")

    return str(resp)

# Required for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
