from flask import Flask, request, Response
import os
import logging

app = Flask(__name__)

# Silence logs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route("/")
def home():
    return "MiserBot is running"

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/apple-touch-icon.png')
def apple_touch_icon():
    return '', 204

@app.route('/apple-touch-icon-precomposed.png')
def apple_touch_icon_precomposed():
    return '', 204

# 🔥 TWILIO WEBHOOK
@app.route("/webhook", methods=["POST"])
def webhook():
    print("🔥 TWILIO HIT")

    from_number = request.form.get("From")
    body = request.form.get("Body")

    print("FROM:", from_number)
    print("MESSAGE:", body)

    reply = f"Bot received: {body}"

    return Response(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{reply}</Message>
</Response>""",
        mimetype="application/xml"
    )

# ✅ Required for Railway
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
