def send_sms(to, message):
    try:
        print(f"[MOCK SMS] Sending to {to}: {message}")
        return True
    except Exception as e:
        print("SMS error:", e)
        return False
