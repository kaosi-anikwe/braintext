# python imports
import os
import requests
import traceback
import subprocess
from io import BytesIO
from queue import Queue
from datetime import datetime

# installed modules
import openai
from PIL import Image
from dotenv import load_dotenv
from twilio.rest import Client
from botocore.exceptions import BotoCoreError, ClientError
from flask import Blueprint, request, url_for, send_file, abort

# local imports
from .functions import respond_text, respond_media, get_original_message
from ..modules.messages import Messages
from ..models import (
    Users,
    BasicSubscription,
)
from ..modules.functions import (
    log_response,
    chat_reponse,
    split_and_respond,
    text_response,
    image_response,
    image_edit,
    image_variation,
    synthesize_speech,
    get_user_db,
    load_messages,
    transcribe_audio,
    TimeoutError,
    WHATSAPP_CHAR_LIMIT,
)

load_dotenv()

task_queue = Queue()
chatbot = Blueprint("twilio_chatbot", __name__)
openai_url = "https://api.openai.com/v1/completions"
openai.api_key = os.getenv("OPENAI_API_KEY")
account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)
TEMP_FOLDER = os.getenv("TEMP_FOLDER")


@chatbot.get("/send-voice-note")
def send_voice_note():
    filename = request.args.get("filename")
    file_ = f"{TEMP_FOLDER}/{filename}"
    if os.path.exists(file_):
        return send_file(file_)
    else:
        return "Not found", 404


@chatbot.post("/braintext-chatbot")
def webhook():
    number = request.values.get("From").replace("whatsapp:", "")
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
                        incoming_msg = request.values.get("Body", "")
                        name = request.values.get("ProfileName")
                        # Image generation
                        if "dalle" in incoming_msg.lower():
                            text = "You don't have access to this service. Please upgrade your account to decrease limits. \nhttps://braintext.io/profile"
                            return respond_text(text=text)
                        elif request.values.get("MediaContentType0"):
                            # audio response
                            text = "You don't have access to this service. Please upgrade your account to decrease limits. \nhttps://braintext.io/profile"
                            return respond_text(text=text)
                        if subscription.respond():
                            # chat response
                            return chat_reponse(
                                client=client,
                                request_values=request.values,
                                name=name,
                                number=number,
                                incoming_msg=incoming_msg,
                                user=user,
                            )
                        else:
                            text = f"You have exceed your limit for the week.\nYour prompts will be renewed on {subscription.get_expire_date().strftime('%A, %d/%m/%Y')} at {subscription.get_expire_date().strftime('%I:%M %p')}.\nUpgrade your account to decrease limits.\nhttps://braintext.io/profile"
                            return respond_text(text)
                    else:
                        text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                        return respond_text(text)

                if user.account_type == "Standard":
                    subscription = user.get_active_sub()
                    if subscription:
                        if not subscription.expired():
                            incoming_msg = request.values.get("Body", "")
                            name = request.values.get("ProfileName")
                            content_type = request.values.get("MediaContentType0", "")

                            if "audio" in content_type:
                                # audio response
                                text = "You don't have access to this service. Please upgrade your account to decrease limits. \nhttps://braintext.io/profile"
                                return respond_text(text=text)
                            if "image" in content_type:
                                # Image editing/variation
                                try:
                                    image_url = request.values.get("MediaUrl0")
                                    response = requests.get(image_url)
                                    if response.ok:
                                        image_path = f"tmp/{str(datetime.utcnow())}.png"
                                        image = Image.open(BytesIO(response.content))
                                        # Convert the image to PNG format
                                        image = image.convert(
                                            "RGBA"
                                        )  # If the image has an alpha channel (transparency)
                                        image.save(image_path, format="PNG")
                                        if (
                                            not incoming_msg
                                            or "variation" in incoming_msg.lower()
                                        ):
                                            # Image variation
                                            image_url = image_variation(image_path)
                                        else:
                                            # Image editing
                                            image_url = image_edit(
                                                image_path, incoming_msg
                                            )
                                        log_response(
                                            name=name,
                                            number=number,
                                            message=incoming_msg,
                                        )
                                        return respond_media(image_url)
                                    else:
                                        text = "Something went wrong. Please try again later."
                                        return respond_text(text)
                                except:
                                    print(traceback.format_exc())
                                    text = (
                                        "Something went wrong. Please try again later."
                                    )
                                    return respond_text(text)
                            if "dalle" in incoming_msg.lower():
                                # Image generation
                                prompt = incoming_msg.lower().replace("dalle", "")
                                try:
                                    image_url = image_response(prompt)
                                    log_response(
                                        name=name, number=number, message=prompt
                                    )
                                    return respond_media(image_url)
                                except:
                                    print(traceback.format_exc())
                                    text = "Sorry, I cannot respond to that at the moment, please try again later."
                                    return respond_text(text)
                            else:
                                # chat response
                                return chat_reponse(
                                    client=client,
                                    request_values=request.values,
                                    name=name,
                                    number=number,
                                    incoming_msg=incoming_msg,
                                    user=user,
                                    subscription=subscription,
                                )
                        else:
                            subscription.update_account(user.id)
                            text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                            return respond_text(text)
                    else:
                        text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                        return respond_text(text)

                if user.account_type == "Premium":
                    subscription = user.get_active_sub()
                    if subscription:
                        if not subscription.expired():
                            incoming_msg = request.values.get("Body", "")
                            name = request.values.get("ProfileName")
                            content_type = request.values.get("MediaContentType0", "")

                            if "audio" in content_type:
                                # Audio response
                                audio_url = request.values.get("MediaUrl0")
                                tmp_file = f"{TEMP_FOLDER}/{str(datetime.utcnow())}.ogg"
                                # get audio file in ogg
                                subprocess.Popen(
                                    f"wget {audio_url} -O '{tmp_file}'",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.STDOUT,
                                ).wait()
                                # convert to mp3 with ffmpeg
                                # subprocess.Popen(
                                #     f"ffmpeg -i '{tmp_file}.ogg' '{tmp_file}.mp3'",
                                #     shell=True,
                                #     stdout=subprocess.DEVNULL,
                                #     stderr=subprocess.STDOUT,
                                # ).wait()
                                try:
                                    transcript = transcribe_audio(tmp_file)
                                    # with open(tmp_file, "rb") as file:
                                    #     transcript = openai.Audio.transcribe(
                                    #         "whisper-1", file
                                    #     )
                                except:
                                    print(traceback.format_exc())
                                    text = "Error transcribing audio. Please try again later."
                                    return respond_text(text)

                                # remove tmp file
                                if os.path.exists(tmp_file):
                                    os.remove(tmp_file)

                                task_queue.put(transcript)
                                abort(500)  # abort to continue with fallback function

                            if "image" in content_type:
                                # Image editing/variation
                                try:
                                    image_url = request.values.get("MediaUrl0")
                                    response = requests.get(image_url)
                                    if response.ok:
                                        image_path = f"tmp/{str(datetime.utcnow())}.png"
                                        image = Image.open(BytesIO(response.content))
                                        # Convert the image to PNG format
                                        image = image.convert(
                                            "RGBA"
                                        )  # If the image has an alpha channel (transparency)
                                        image.save(image_path, format="PNG")
                                        if (
                                            not incoming_msg
                                            or "variation" in incoming_msg.lower()
                                        ):
                                            # Image variation
                                            image_url = image_variation(image_path)
                                        else:
                                            # Image editing
                                            image_url = image_edit(
                                                image_path, incoming_msg
                                            )
                                        log_response(
                                            name=name,
                                            number=number,
                                            message=incoming_msg,
                                        )
                                        return respond_media(image_url)
                                    else:
                                        text = "Something went wrong. Please try again later."
                                        return respond_text(text)
                                except:
                                    print(traceback.format_exc())
                                    text = (
                                        "Something went wrong. Please try again later."
                                    )
                                    return respond_text(text)
                            if "dalle" in incoming_msg.lower():
                                # Image generation
                                prompt = incoming_msg.lower().replace("dalle", "")
                                try:
                                    image_url = image_response(prompt)
                                    log_response(
                                        name=name, number=number, message=prompt
                                    )
                                    return respond_media(image_url)
                                except:
                                    print(traceback.format_exc())
                                    text = "Sorry, I cannot respond to that at the moment, please try again later."
                                    return respond_text(text)
                            else:
                                # chat response
                                return chat_reponse(
                                    client=client,
                                    request_values=request.values,
                                    name=name,
                                    number=number,
                                    incoming_msg=incoming_msg,
                                    user=user,
                                    subscription=subscription,
                                )
                        else:
                            subscription.update_account(user.id)
                            text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                            return respond_text(text)
                    else:
                        text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                        return respond_text(text)
            else:
                text = "Please verify your email to access the service. https://braintext.io/profile"
                return respond_text(text)
        else:
            text = "Please verify your number to access the service. https://braintext.io/profile"
            return respond_text(text)
    else:  # no account found
        text = "To use BrainText, please sign up for an account at https://braintext.io"
        return respond_text(text)


@chatbot.post("/braintext-chatbot-fallback")
def fallback():
    try:
        number = request.values.get("From").replace("whatsapp:", "")

        user = Users.query.filter(Users.phone_no == number).one_or_none()
        name = request.values.get("ProfileName")
        content_type = request.values.get("MediaContentType0")

        if content_type == "audio/ogg":
            prompt = task_queue.get()
            try:
                # Chat response
                try:
                    isreply = False
                    if request.values.get("OriginalRepliedMessageSender"):
                        # message is a reply. Get original
                        original_message_sid = request.values.get(
                            "OriginalRepliedMessageSid"
                        )
                        original_message = get_original_message(
                            client, original_message_sid
                        )
                        isreply = True
                    user_db_path = get_user_db(name=name, number=number)
                    messages = (
                        load_messages(
                            prompt=prompt,
                            db_path=user_db_path,
                            original_message=original_message,
                        )
                        if isreply
                        else load_messages(prompt=prompt, db_path=user_db_path)
                    )
                    text, tokens, role = text_response(messages=messages, number=number)
                except TimeoutError:
                    text = "Sorry, your response is taking too long. Try rephrasing your question or breaking it into sections."
                    return respond_text(text)

                # record ChatGPT response
                new_message = {"role": role, "content": text}
                new_message = Messages(new_message, user_db_path)
                new_message.insert()

                log_response(
                    name=name,
                    number=number,
                    message=prompt,
                    tokens=tokens,
                )
                user_settings = user.user_settings()

                if user_settings.voice_response:
                    try:
                        audio_filename = synthesize_speech(
                            text=text, voice=user_settings.ai_voice_type
                        )
                        if audio_filename == None:
                            text = "AWS session expired."
                            return respond_text(text)

                        audio_path = f"{TEMP_FOLDER}/{audio_filename}"

                        # convert to ogg with ffmpeg
                        subprocess.Popen(
                            f"ffmpeg -i '{audio_path}' -c:a libopus '{audio_path.split('.')[0]}.opus'",
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT,
                        ).wait()

                        # remove tts audio
                        if os.path.exists(audio_path):
                            os.remove(audio_path)

                        media_url = f"{url_for('twilio_chatbot.send_voice_note', _external=True, _scheme='https')}?filename={audio_filename.split('.')[0]}.opus"
                        print(media_url)

                        return respond_media(media_url)
                    except BotoCoreError:
                        print(traceback.format_exc())
                        text = "Sorry, I cannot respond to that at the moment, please try again later."
                        return respond_text(text)
                    except ClientError:
                        print(traceback.format_exc())
                        text = "Sorry, you're response was too long. Please rephrase the question or break it into segments."
                        return respond_text(text)
                else:
                    if len(text) < WHATSAPP_CHAR_LIMIT:
                        return respond_text(text)
                    return split_and_respond(client, text, number)
            except:
                print(traceback.format_exc())
                text = "Sorry, I cannot respond to that at the moment, please try again later."
                return respond_text(text)
        else:
            return webhook()
    except:
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return respond_text(text)


@chatbot.post("/receive-sms")
def receive_sms():
    data = request.form
    print(data)
    return "200"
