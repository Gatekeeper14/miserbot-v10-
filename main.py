@app.route("/sms", methods=["POST"])
def sms_reply():
    incoming_msg = request.form.get("Body")
    print("Incoming:", incoming_msg)

    resp = MessagingResponse()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are MiserBot. Be witty and a little savage."},
                {"role": "user", "content": incoming_msg}
            ]
        )

        reply_text = completion.choices[0].message.content.strip()
        print("Reply:", reply_text)

    except Exception as e:
        print("ERROR:", str(e))
        reply_text = "Bot error: " + str(e)

    resp.message(reply_text)
    return str(resp)
