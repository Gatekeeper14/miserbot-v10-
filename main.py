from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "OK"

@app.route("/sms", methods=["POST"])
def sms():
    msg = request.form.get("Body")

    print("Incoming:", msg)

    resp = MessagingResponse()
    resp.message("Received")

    return str(resp)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
