# python imports
import os
import traceback

# installed imports
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify, send_file, after_this_request

# local imports
from .. import logger
from .functions import *
from ..modules.functions import *
from ..models import (
    Users,
    AnonymousUsers,
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
                os.remove(file_) if filename != "welcome.ogg" else None
                return response

            return send_file(file_)
        else:
            return "Not found", 404
    return "Not found", 404


@chatbot.get("/send-media")
def send_media():
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


@chatbot.post("/meta-chatbot")
def webhook():
    data = request.get_json()
    try:
        if is_message(data):
            if not is_old(data):
                number = f"+{get_number(data)}"
                logger.info(number)
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
                                            meta_image_response(user=user, data=data)
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
                                        if not user.from_anonymous:
                                            text = f"You have exceed your limit for the week.\nYour prompts will be renewed on {subscription.get_expire_date().strftime('%A, %d/%m/%Y')} at {subscription.get_expire_date().strftime('%I:%M %p')}.\nUpgrade your account to decrease limits.\nhttps://braintext.io/profile"
                                        else:
                                            text = f"You have exceed your limit for the week.\nYour prompts will be renewed on {subscription.get_expire_date().strftime('%A, %d/%m/%Y')} at {subscription.get_expire_date().strftime('%I:%M %p')} GMT.\nUpgrade your account to decrease limits.\nhttps://braintext.io/profile"
                                        reply_to_message(
                                            message_id, number, text
                                        ) if message_type == "text" else send_text(
                                            text, number
                                        )
                                else:
                                    text = "There's a problem, I can't respond at this time. Your subscription may have expired.\nCheck your profle to confirm. https://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        text, number
                                    )
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
                                            meta_image_response(user=user, data=data)
                                        elif message_type == "text":
                                            # Chat/Dalle response
                                            meta_chat_response(
                                                user=user,
                                                data=data,
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
                                    text = "There's a problem, I can't respond at this time. Your subscription may have expired.\nCheck your profle to confirm. https://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        text, number
                                    )
                            if user.account_type == "Premium":
                                subscription = user.get_active_sub()
                                if subscription:
                                    if not subscription.expired():
                                        if message_type == "audio":
                                            # Audio response
                                            meta_audio_response(user=user, data=data)
                                        if message_type == "image":
                                            # Image editing/variation
                                            meta_image_response(user=user, data=data)
                                        if message_type == "text":
                                            # Chat/Dalle response
                                            meta_chat_response(
                                                user=user,
                                                data=data,
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
                                    text = "There's a problem, I can't respond at this time. Your subscription may have expired.\nCheck your profle to confirm. https://braintext.io/profile"
                                    reply_to_message(
                                        message_id, number, text
                                    ) if message_type == "text" else send_text(
                                        text, number
                                    )
                        else:
                            text = "Please verify your email to access the service. Check your inbox for the verification link, or login to request another. https://braintext.io/profile"
                            reply_to_message(
                                message_id, number, text
                            ) if message_type == "text" else send_text(text, number)
                    else:
                        text = "Please verify your number to access the service. Login to your profile to verify your number. https://braintext.io/profile"
                        reply_to_message(
                            message_id, number, text
                        ) if message_type == "text" else send_text(text, number)
                else:  # no account found
                    # Anonymous user
                    user = AnonymousUsers.query.filter(
                        AnonymousUsers.phone_no == number
                    ).one_or_none()
                    if not user:
                        user = AnonymousUsers(phone_no=number)
                        user.insert()

                        # first time message. send tos and pp
                        @after_this_request
                        def first_time(response):
                            text = "Thank you for choosing BrainText 💙. We value your privacy and aim to provide the best service possible. In order to use our service, please review and agree to our Terms of Service https://braintext.io/terms-of-service and Privacy Policy https://braintext.io/privacy-policy. \nThese agreements outline how we collect, use, and protect your personal information. If you have any questions or concerns, please don't hesitate to contact us. \n\nThank you for your trust."
                            send_text(text, number)
                            # send list of features
                            with open(f"{TEMP_FOLDER}/features.txt") as f:
                                get_features = f.readlines()
                            features = "\n".join(get_features)
                            send_text(features, number)
                            # send option to sign up
                            body = "Joining BrainText can enhance your experience by providing access to renewed prompts and features. Would you like to create an account now?"
                            header = "Register Now"
                            button_texts = ["Yes", "Maybe later"]
                            button = generate_interactive_button(
                                body=body, header=header, button_texts=button_texts
                            )
                            send_interactive_message(button=button, recipient=number)
                            return response

                    signup = is_interative_reply(data)
                    if signup or user.signup_stage != "anonymous":
                        whatsapp_signup(
                            data,
                            user,
                            interactive_reply=signup,
                        )  # processing ends here as this sends a response to user
                        signup = True
                    if not signup and user.respond():
                        user.prompts += 1
                        user.update()
                        if message_type == "image":
                            # Image editing/variation
                            meta_image_response(user=user, data=data, anonymous=True)
                        if message_type == "text":
                            # Chat/Dalle response
                            meta_chat_response(
                                user=user,
                                data=data,
                                anonymous=True,
                            )
                        elif message_type == "audio":
                            # Audio response
                            meta_audio_response(user=user, data=data, anonymous=True)
                    elif not signup and not user.respond():
                        text = "Thank you for using our service. We're sorry to inform you that you have reached your limit of prompts. To continue receiving prompts, please consider signing up for an account at BrainText. Here, you can access more prompts and enhance your experience. Thank you for your understanding and support."
                        reply_to_message(
                            message_id, number, text
                        ) if message_type == "text" else send_text(text, number)
                        # send option to sign up
                        body = "How would you like to register?"
                        header = "Register to continue"
                        button_texts = ["Our website", "Continue here"]
                        button = generate_interactive_button(
                            body=body, header=header, button_texts=button_texts
                        )
                        send_interactive_message(button=button, recipient=number)
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I can't respond to that at the moment. Plese try again later."
        reply_to_message(
            message_id, number, text
        ) if message_type == "text" else send_text(text, number)
    finally:
        response = jsonify(success=True)
        response.status_code = 200
        return response
