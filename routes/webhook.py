from flask import Blueprint, request
from services.telegram_service import handle_telegram_update

webhook_blueprint = Blueprint("webhook", __name__)

@webhook_blueprint.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    handle_telegram_update(data)
    return "ok"
