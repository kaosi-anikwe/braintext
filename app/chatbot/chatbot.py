# python imports
import os
import threading
import traceback

# installed imports
from dotenv import load_dotenv
from flask import (
    Blueprint,
    request,
    jsonify,
    send_file,
    after_this_request,
    current_app,
)

# local imports
from .. import logger
from .functions import *
from ..modules.functions2 import record_message
from ..modules.functions import *
from ..models import (
    Users,
    AnonymousUsers,
    MessageRequests,
)


load_dotenv()

chatbot = Blueprint("chatbot", __name__)
META_VERIFY_TOKEN = os.getenv("META_VERIFY_TOKEN")
BASE_COST = float(os.getenv("BASE_COST"))


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
        # check for test account
        if is_message(data):
            if get_phone_id(data) == os.getenv("PHONE_NUMBER_ID"):
                if not is_old(data):
                    number = f"+{get_number(data)}"
                    logger.info(number)
                    name = get_name(data)
                    message_id = get_message_id(data)
                    message_type = get_message_type(data)
                    mark_as_read(message_id)
                    try:
                        message = get_message(data)
                    except KeyError:
                        message = ""
                    # try to get user
                    user = Users.query.filter(Users.phone_no == number).one_or_none()
                    if user:  # user account exists
                        if user.phone_verified:
                            if user.email_verified:
                                # check user balance
                                if not is_interative_reply(data):
                                    if BASE_COST > user.balance:
                                        text = f"Insufficent balance. Cost is {round(BASE_COST, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
                                        logger.info(
                                            f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
                                        )
                                        header = "Recharge Now"
                                        body = "Instantly top up your balance directly on WhatsApp"
                                        button_texts = ["Yes", "No"]
                                        button = generate_interactive_button(
                                            header=header,
                                            body=body,
                                            button_texts=button_texts,
                                        )
                                        # record messages
                                        record_message(
                                            name=name,
                                            number=number,
                                            message=message,
                                            assistant=False,
                                        )
                                        record_message(
                                            name=name, number=number, message=text
                                        )
                                        send_text(text, number)
                                        return send_interactive_message(
                                            interactive=button, recipient=user.phone_no
                                        )

                                    # charge base cost
                                    user.balance -= BASE_COST
                                    user.update()
                                    logger.info(
                                        f"DEDUCTED {BASE_COST} (BASE COST) FROM USER BALANCE IS {user.balance}"
                                    )
                                message_request = MessageRequests(user.id)
                                message_request.interactive = (
                                    True if is_interative_reply(data) else False
                                )
                                message_request.insert()
                                if message_type == "audio":
                                    # Audio response
                                    meta_audio_response(
                                        user=user,
                                        data=data,
                                        message_request=message_request,
                                    )
                                if message_type == "image":
                                    # Image editing/variation
                                    meta_image_response(
                                        user=user,
                                        data=data,
                                        message_request=message_request,
                                    )
                                if message_type == "text":
                                    # Chat/Dalle response
                                    meta_chat_response(
                                        user=user,
                                        data=data,
                                        message_request=message_request,
                                    )
                                if message_type == "interactive":
                                    meta_interactive_response(
                                        user=user,
                                        data=data,
                                        message_request=message_request,
                                    )
                            else:
                                text = f"Please verify your email to access the service. Check your inbox for the verification link, or login to request another. {request.host_url}profile"
                                record_message(
                                    name=name,
                                    number=number,
                                    message=message,
                                    assistant=False,
                                )
                                record_message(name=name, number=number, message=text)
                                reply_to_message(
                                    message_id, number, text
                                ) if message_type == "text" else send_text(text, number)
                        else:
                            text = f"Please verify your number to access the service. Login to your profile to verify your number. {request.host_url}profile"
                            record_message(
                                name=name,
                                number=number,
                                message=message,
                                assistant=False,
                            )
                            record_message(name=name, number=number, message=text)
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
                                text = f"Thank you for choosing BrainText 💙. We value your privacy and aim to provide the best service possible. In order to use our service, please review and agree to our Terms of Service {request.host_url}terms-of-service and Privacy Policy {request.host_url}privacy-policy. \nThese agreements outline how we collect, use, and protect your personal information. If you have any questions or concerns, please don't hesitate to contact us. \n\nThank you for your trust."
                                send_text(text, number)
                                # send list of features
                                with open(f"{TEMP_FOLDER}/features.txt") as f:
                                    get_features = f.readlines()
                                features = "\n".join(get_features)
                                send_text(features, number)
                                # send option to sign up
                                body = f"Joining BrainText can enhance your experience by providing access to renewed prompts and features. Would you like to create an account now?"
                                header = "Register Now"
                                button_texts = ["Yes", "Maybe later"]
                                button = generate_interactive_button(
                                    body=body, header=header, button_texts=button_texts
                                )
                                send_interactive_message(
                                    interactive=button, recipient=number
                                )
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
                            # charge base cost
                            user.balance -= BASE_COST
                            user.update()
                            logger.info(
                                f"DEDUCTED {BASE_COST} (BASE COST) FROM USER BALANCE IS {user.balance}"
                            )
                            message_request = MessageRequests(user.id, True)
                            message_request.insert()
                            if message_type == "image":
                                # Image editing/variation
                                meta_image_response(
                                    user=user,
                                    data=data,
                                    message_request=message_request,
                                    anonymous=True,
                                )
                            if message_type == "text":
                                # Chat/Dalle response
                                meta_chat_response(
                                    user=user,
                                    data=data,
                                    message_request=message_request,
                                    anonymous=True,
                                )
                            elif message_type == "audio":
                                # Audio response
                                meta_audio_response(
                                    user=user,
                                    data=data,
                                    message_request=message_request,
                                    anonymous=True,
                                )
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
                            send_interactive_message(
                                interactive=button, recipient=number
                            )
            # WOKSPRO
            if not is_old(data):
                from app.models import Threads
                from app.modules.wokspro import wokspro_response, record_wokspro_message

                wokspro_id = os.getenv("WOKSPRO_NUMBER_ID")
                if get_phone_id(data) == wokspro_id:
                    number = f"+{get_number(data)}"
                    message_id = get_message_id(data)
                    message_type = get_message_type(data)
                    try:
                        message = get_message(data)
                    except KeyError:
                        message = ""
                    try:
                        logger.info(number)
                        mark_as_read(message_id, wokspro_id)
                        # find message thread with number
                        thread = Threads.query.filter(
                            Threads.phone_no == number
                        ).one_or_none()
                        if thread:
                            wokspro_response(thread=thread, data=data)
                        else:  # new user
                            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
                            client = OpenAI(api_key=OPENAI_API_KEY)
                            thread_id = client.beta.threads.create().id
                            logger.info(f"New thread created with ID: {thread_id}")
                            thread = Threads(thread_id=thread_id, phone_no=number)
                            wokspro_response(thread=thread, data=data)
                    except:
                        logger.error("WOKSPRO ERROR")
                        logger.error(traceback.format_exc())
                        text = "Sorry, I can't respond to that at the moment. Please try again later."
                        thread = record_wokspro_message(thread, message)
                        thread = record_wokspro_message(thread, text, "assistant")
                        reply_to_message(
                            message_id, number, text, wokspro_id
                        ) if message_type == "text" else send_text(
                            text, number, wokspro_id
                        )

    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I can't respond to that at the moment. Please try again later."
        record_message(name=name, number=number, message=message, assistant=False)
        record_message(name=name, number=number, message=text)
        reply_to_message(
            message_id, number, text
        ) if message_type == "text" else send_text(text, number)
    finally:
        response = jsonify(success=True)
        response.status_code = 200
        return response
