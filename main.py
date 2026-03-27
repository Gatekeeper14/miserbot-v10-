from flask import Flask
from routes.webhook import webhook_blueprint

app = Flask(__name__)
app.register_blueprint(webhook_blueprint)

@app.route("/")
def home():
    return "Miserbot is running 🔥"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
