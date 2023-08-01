from flask import Blueprint, request

chatbot = Blueprint("chatbot", __name__)


@chatbot.route("/meta-chatbot")
def webhook():
    verify_token = request.args["hub.verify_token"]
    print(verify_token)
    return "200"
