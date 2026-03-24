from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming = request.form.get("Body")
    print("Incoming:", incoming)

    resp = MessagingResponse()
    resp.message("MiserBot is alive")

    return str(resp)

@app.route("/")
def home():
    return "Running"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
