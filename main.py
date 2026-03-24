from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "MiserBot is running!"

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body", "")

    print("Incoming:", incoming_msg)

    # Create Twilio response
    resp = MessagingResponse()

    # Simple reply (you can change this later)
    reply = f"You said: {incoming_msg}"

    resp.message(reply)

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
