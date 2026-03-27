@app.route('/webhook', methods=['POST'])
def sms_reply():
    try:
        incoming = request.form.get('Body')
        from_number = request.form.get('From')

        print(f"FROM: {from_number}, MESSAGE: {incoming}")

        resp = MessagingResponse()
        resp.message("Got your message!")

        return str(resp)

    except Exception as e:
        print(f"ERROR: {e}")
        return "error", 500
