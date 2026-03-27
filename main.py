from flask import Flask, request, Response
from twilio.rest import Client
from openai import OpenAI
import os

app = Flask(__name__)

# Twilio credentials
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")

client = Client(account_sid, auth_token)

# OpenAI client
client_ai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    incoming = request.form.get('Body')
    from_number = request.form.get('From')

    print(f"FROM: {from_number}, MESSAGE: {incoming}")

    try:
        # 🧠 AI response
        ai_response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MiserBot, a smart assistant that helps users with business, automation, and general questions."},
                {"role": "user", "content": incoming}
            ]
        )

        reply_text = ai_response.choices[0].message.content

        # 📤 Send SMS
        client.messages.create(
            body=reply_text,
            from_=twilio_number,
            to=from_number
        )

    except Exception as e:
        print(f"ERROR: {e}")

    return Response("OK", status=200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
