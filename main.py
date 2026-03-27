from flask import Flask, request, Response
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "MiserBot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 TWILIO HIT")

    from_number = request.form.get("From")
    body = request.form.get("Body")

    print("FROM:", from_number)
    print("MESSAGE:", body)

    reply = f"Bot received: {body}"

    return Response(f"""
<Response>
    <Message>{reply}</Message>
</Response>
""", mimetype="text/xml")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
