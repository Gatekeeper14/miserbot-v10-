from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
from openai import OpenAI

# THIS LINE WAS MISSING ❗
app = Flask(__name__)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    print("Incoming:", incoming_msg)

    resp = MessagingResponse()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MiserBot. Be witty and savage."},
                {"role": "user", "content": incoming_msg}
            ]
        )

        reply_text = completion.choices[0].message.content.strip()
        print("Reply:", reply_text)

    except Exception as e:
        print("ERROR:", str(e))
        reply_text = "Error: " + str(e)

    resp.message(reply_text)
    return str(resp)


@app.route("/", methods=["GET"])
def home():
    return "Bot is alive"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
