from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from openai import OpenAI

# Create Flask app FIRST (this fixes your crash)
app = Flask(__name__)

# OpenAI client (make sure env var is set in Railway)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# SMS route (Twilio hits this)
@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    print("Incoming:", incoming_msg)

    resp = MessagingResponse()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MiserBot. Be witty, slightly savage, but helpful."},
                {"role": "user", "content": incoming_msg}
            ]
        )

        reply_text = completion.choices[0].message.content.strip()
        print("Reply:", reply_text)

    except Exception as e:
        print("ERROR:", str(e))
        reply_text = "Something went wrong."

    resp.message(reply_text)
    return str(resp)

# Root route (prevents Railway shutdown)
@app.route("/", methods=["GET"])
def home():
    return "MiserBot is running."

# REQUIRED for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
