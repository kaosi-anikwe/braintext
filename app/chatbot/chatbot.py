import os
import openai
import traceback
import subprocess
from queue import Queue
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError
from flask import Blueprint, request, url_for, send_file, abort
from ..modules.functions import (
    respond_text,
    text_response,
    log_response,
    check_and_respond_text,
    image_response,
    respond_media,
    synthesize_speech,
    get_user_db,
    load_messages,
    chat_reponse,
    TimeoutError,
)
from app.models import (
    Users,
    BasicSubscription,
    StandardSubscription,
    PremiumSubscription,
    UserSettings,
)


load_dotenv()

chatbot = Blueprint("chatbot", __name__)

openai_url = "https://api.openai.com/v1/completions"
openai.api_key = os.getenv("OPENAI_API_KEY")
log_dir = os.getenv("CHATBOT_LOG")
tmp_folder = os.getenv("TEMP_FOLDER")

# create log folder if not exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# create tmp folder if not exists
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)


task_queue = Queue()

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


@chatbot.get("/send-voice-note")
def send_voice_note():
    filename = request.args.get("filename")
    if os.path.exists(str(filename)):
        return send_file(f"{filename}")
    else:
        return "Not found", 404


@chatbot.post("/braintext-chatbot")
def bot():
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
                            elif request.values.get("MediaContentType0"):
                                # audio response
                                text = "You don't have access to this service. Please upgrade your account to decrease limits. \nhttps://braintext.io/profile"
                                return respond_text(text=text)
                            else:
                                # chat response
                                return chat_reponse(
                                    client=client,
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
                            content_type = request.values.get("MediaContentType0")

                            if content_type == "audio/ogg":
                                # Audio response
                                audio_url = request.values.get("MediaUrl0")
                                tmp_file = f"tmp/{str(datetime.utcnow())}"
                                # get audio file in ogg
                                subprocess.Popen(
                                    f"wget {audio_url} -O '{tmp_file}.ogg'",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.STDOUT,
                                ).wait()
                                # convert to mp3 with ffmpeg
                                subprocess.Popen(
                                    f"ffmpeg -i '{tmp_file}.ogg' '{tmp_file}.mp3'",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.STDOUT,
                                ).wait()
                                try:
                                    with open(f"{tmp_file}.mp3", "rb") as file:
                                        transcript = openai.Audio.transcribe(
                                            "whisper-1", file
                                        )
                                except:
                                    print(traceback.format_exc())
                                    return respond_text(
                                        "Error transcribing audio. Please try again later."
                                    )

                                # remove tmp files
                                if os.path.exists(f"{tmp_file}.ogg"):
                                    os.remove(f"{tmp_file}.ogg")
                                if os.path.exists(f"{tmp_file}.mp3"):
                                    os.remove(f"{tmp_file}.mp3")

                                prompt = transcript.text
                                task_queue.put(prompt)
                                abort(500)  # abort to continue with fallback function

                            # Image generation
                            if "dalle" in incoming_msg.lower():
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
                                    name=name,
                                    number=number,
                                    incoming_msg=incoming_msg,
                                    user=user,
                                    subscription=subscription,
                                )
                                # TODO:
                                # add image variation
                                # remebering pervious message
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
                    text, tokens = text_response(prompt=prompt, number=number)
                except TimeoutError:
                    text = "Sorry, your response is taking too long. Try rephrasing your question or breaking it into sections."
                    return respond_text(text)

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

                        # convert to ogg with ffmpeg
                        subprocess.Popen(
                            f"ffmpeg -i '{audio_filename}' -c:a libopus '{audio_filename.split('.')[0]}.opus'",
                            shell=True,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT,
                        ).wait()

                        # remove tts audio
                        if os.path.exists(audio_filename):
                            os.remove(audio_filename)

                        media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={audio_filename.split('.')[0]}.opus"
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
                    return check_and_respond_text(client, text, number)
            except:
                print(traceback.format_exc())
                text = "Sorry, I cannot respond to that at the moment, please try again later."
                return respond_text(text)
        else:
            return bot()
    except:
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return respond_text(text)
