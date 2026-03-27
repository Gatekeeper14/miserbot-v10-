from flask import Flask, request, Response
import os

app = Flask(__name__)

@app.route('/')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def sms_reply():
    incoming = request.form.get('Body')
    from_number = request.form.get('From')

    print(f"FROM: {from_number}, MESSAGE: {incoming}")

    return Response(
        """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>Got your message!</Message>
</Response>""",
        mimetype="application/xml"
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
