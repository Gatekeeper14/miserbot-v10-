from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/")
def home():
    return "Miserbot is running"

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")

    print(f"Incoming: {incoming_msg}")

    resp = MessagingResponse()
    resp.message("I got your message: " + incoming_msg)

    return str(resp)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
