# python imports
import os
import traceback
from contextlib import contextmanager

# installed imports
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, send_file, after_this_request

# local imports
from .functions import *
from ..modules.functions import *
from ..models import (
    Users,
    BasicSubscription,
)

load_dotenv()

chatbot = Blueprint("chatbot", __name__)
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")


@chatbot.get("/send-voice-note")
def send_voice_note():
    filename = request.args.get("filename") or None
    if filename:
        file_ = os.path.join(TEMP_FOLDER, filename)
        if os.path.exists(file_):

            @after_this_request
            def delete_file(response):
                os.remove(file_)
                return response

            return send_file(file_)
        else:
            return "Not found", 404
    return "Not found", 404


# @chatbot.after_request


@chatbot.route("/meta-chatbot", methods=["GET", "POST"])
def webhook():
    data = request.get_json()
    try:
        if is_message(data):
            number = f"+{get_number(data)}"
            message_id = get_message_id(data)
            message_type = get_message_type(data)
            mark_as_read(message_id)
            # try to get user
            user = Users.query.filter(Users.phone_no == number).one_or_none()
            if user:  # user account exists
                if user.phone_verified:
                    if user.email_verified:
                        # identify user account type
                        if user.account_type == "Basic":
                            subscription = BasicSubscription.query.filter(
                                BasicSubscription.user_id == user.id
                            ).one_or_none()
                            if subscription:
                                if subscription.respond():
                                    if message_type == "image":
                                        # Image editing/variation
                                        meta_image_response(data=data)
                                    if message_type == "text":
                                        # Chat/Dalle response
                                        meta_chat_response(
                                            data=data,
                                            user=user,
                                            subscription=subscription,
                                        )
                                    elif message_type == "audio":
                                        # Audio response
                                        meta_audio_response(user=user, data=data)
                                else:
                                    text = f"You have exceed your limit for the week.\nYour prompts will be renewed on {subscription.get_expire_date().strftime('%A, %d/%m/%Y')} at {subscription.get_expire_date().strftime('%I:%M %p')}.\nUpgrade your account to decrease limits.\nhttps://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        text, number
                                    )
                            else:
                                text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(text, number)
                        if user.account_type == "Standard":
                            subscription = user.get_active_sub()
                            if subscription:
                                if not subscription.expired():
                                    if message_type == "audio":
                                        # Audio response
                                        text = "You don't have access to this service. Please upgrade your account to decrease limits. \nhttps://braintext.io/profile"
                                        reply_to_message(message_id, number, text)
                                    elif message_type == "image":
                                        # Image editing/variation
                                        meta_image_response(data)
                                    elif message_type == "text":
                                        # Chat/Dalle response
                                        meta_chat_response(
                                            data=data,
                                            user=user,
                                            subscription=subscription,
                                        )
                                else:
                                    text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        text, number
                                    )
                            else:
                                text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(text, number)
                        if user.account_type == "Premium":
                            subscription = user.get_active_sub()
                            if subscription:
                                if not subscription.expired():
                                    if message_type == "audio":
                                        # Audio response
                                        meta_audio_response(user=user, data=data)
                                    if message_type == "image":
                                        # Image editing/variation
                                        meta_image_response(data)
                                    if message_type == "text":
                                        # Chat/Dalle response
                                        meta_chat_response(
                                            data=data,
                                            user=user,
                                            subscription=subscription,
                                        )
                                else:
                                    text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        text, number
                                    )
                            else:
                                text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(text, number)
                    else:
                        text = "Please verify your email to access the service. https://braintext.io/profile"
                        reply_to_message(
                            message_id, number, text
                        ) if message_type == "text" else send_text(text, number)
                else:
                    text = "Please verify your number to access the service. https://braintext.io/profile"
                    reply_to_message(
                        message_id, number, text
                    ) if message_type == "text" else send_text(text, number)
            else:  # no account found
                text = "To use BrainText, please sign up for an account at https://braintext.io"
                reply_to_message(
                    message_id, number, text
                ) if message_type == "text" else send_text(text, number)
    except:
        print(traceback.format_exc())
        text = "Sorry, I can't respond to that at the moment. Plese try again later."
        reply_to_message(
            message_id, number, text
        ) if message_type == "text" else send_text(text, number)

    response = jsonify(success=True)
    response.status_code = 200
    return response
