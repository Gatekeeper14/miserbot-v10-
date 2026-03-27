from flask import Flask, request, Response
from twilio.rest import Client
from openai import OpenAI
import os

app = Flask(__name__)

# 🔍 DEBUG: check environment variables
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
twilio_number = os.environ.get("TWILIO_PHONE_NUMBER")
openai_key = os.environ.get("OPENAI_API_KEY")

print("SID:", account_sid)
print("Token set:", bool(auth_token))
print("Number:", twilio_number)
print("OpenAI key set:", bool(openai_key))

client = Client(account_sid, auth_token)
client_ai = OpenAI(api_key=openai_key)

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    try:
        # 🔍 DEBUG: see exactly what Twilio sends
        print("RAW DATA:", request.data)
        print("FORM DATA:", request.form)

        # ✅ Correct Twilio fields
        incoming = request.form.get('Body', '')
        from_number = request.form.get('From', '')

        print(f"FROM: {from_number}, MESSAGE: {incoming}")

        # 🚨 Guard (prevents crash)
        if not incoming or not from_number:
            print("⚠️ Missing data from Twilio")
            return Response("No message received", status=400)

        # 🧠 AI response
        ai_response = client_ai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MiserBot, a smart assistant for business, automation, and conversation."},
                {"role": "user", "content": incoming}
            ]
        )

        reply_text = ai_response.choices[0].message.content

        # 📤 Send SMS
        message = client.messages.create(
            body=reply_text,
            from_=twilio_number,
            to=from_number
        )

        print("SENT SID:", message.sid)

    except Exception as e:
        print(f"ERROR: {e}")

    return Response("OK", status=200)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
