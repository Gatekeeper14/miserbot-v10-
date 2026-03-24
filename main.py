from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from openai import OpenAI

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    print("Incoming:", incoming_msg)

    try:
        # Generate AI response
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MiserBot. Be witty, slightly savage, but helpful."},
                {"role": "user", "content": incoming_msg}
            ]
        )

        reply_text = completion.choices[0].message.content.strip()

    except Exception as e:
        print("Error:", e)
        reply_text = "Something broke. Try again."

    # Send reply back to Twilio
    resp = MessagingResponse()
    resp.message(reply_text)

    return str(resp)


# ROOT ROUTE (so Railway doesn't think it's dead)
@app.route("/", methods=["GET"])
def home():
    return "MiserBot is alive!"


# IMPORTANT: Railway needs this
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
