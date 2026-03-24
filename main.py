from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os

app = Flask(__name__)

# Home route (so Railway shows it's running)
@app.route("/")
def home():
    return "MiserBot is running"

# SMS reply route
@app.route("/sms", methods=["POST"])
def sms():
    incoming_msg = request.form.get("Body")
    print("Incoming:", incoming_msg)

    resp = MessagingResponse()
    resp.message(f"You said: {incoming_msg}")

    return str(resp)

# Required for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
