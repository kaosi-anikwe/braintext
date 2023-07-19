import os
import vonage
import openai
import traceback
from queue import Queue
from dotenv import load_dotenv
from pprint import pprint
import subprocess
from datetime import datetime
from flask import Blueprint, request, abort, url_for
from botocore.exceptions import BotoCoreError, ClientError
from app.models import Users, StandardSubscription, PremiumSubscription, UserSettings
from app.modules.functions import (
    delete_file,
    get_audio,
    image_response,
    log_response,
    synthesize_speech,
    vonage_text_response,
    vonage_send_audio,
    vonage_send_image,
    vonage_send_text,
)

load_dotenv()

newbot = Blueprint("vonage_chatbot", __name__)

VONAGE_APPLICATION_ID = os.getenv("VONAGE_APPLICATION_ID")
VONAGE_APPLICATION_PRIVATE_KEY_PATH = os.getenv("VONAGE_APPLICATION_PRIVATE_KEY_PATH")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
WHATSAPP_TEMPLATE_NAMESPACE = os.getenv("WHATSAPP_TEMPLATE_NAMESPACE")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")
TEMP_FOLDER = os.getenv("TEMP_FOLDER")


client = vonage.Client(
    application_id=VONAGE_APPLICATION_ID,
    private_key=VONAGE_APPLICATION_PRIVATE_KEY_PATH,
)

openai_url = "https://api.openai.com/v1/completions"
openai.api_key = os.getenv("OPENAI_API_KEY")
log_dir = os.getenv("CHATBOT_LOG")
tmp_folder = os.getenv("TEMP_FOLDER")
task_queue = Queue()

# create log folder if not exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# create tmp folder if not exists
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)


@newbot.post("/vonage-chatbot")
def chatbot():
    try:
        data = request.get_json()
        print(data)
        number = data["from"]
        user = Users.query.filter(Users.phone_no == f"+{number}").one_or_none()
        name = data["profile"]["name"]
        incoming_msg = data["text"] if data["message_type"] != "audio" else None

        if user:
            if user.phone_verified:
                if user.email_verified:
                    if data["message_type"] == "audio":
                        # Audio response
                        audio_url = data["audio"]["url"]
                        tmp_file = f"{TEMP_FOLDER}/{str(datetime.utcnow())}"
                        # get audio file in ogg
                        get_audio(audio_url, tmp_file)
                        try:
                            with open(f"{tmp_file}.mp3", "rb") as file:
                                transcript = openai.Audio.transcribe("whisper-1", file)
                        except:
                            print(traceback.format_exc())
                            text = "Error transcribing audio. Please try again later."
                            return vonage_send_text(client, text, number), 200

                        # remove tmp files
                        delete_file(f"{tmp_file}.ogg")
                        delete_file(f"{tmp_file}.mp3")

                        prompt = transcript.text

                        try:
                            text, tokens = vonage_text_response(
                                prompt=prompt, number=number
                            )
                        except TimeoutError:
                            text = "Sorry, your response is taking too long. Try rephrasing your question or breaking it into sections."
                            return vonage_send_text(client, text, number), 200

                        log_response(
                            name=name,
                            number=f"+{number}",
                            message=prompt,
                            tokens=tokens,
                        )
                        user_settings = UserSettings.query.filter(
                            UserSettings.user_id == user.id
                        ).one()

                        if user_settings.voice_response:
                            try:
                                audio_filename = synthesize_speech(
                                    text=text, voice=user_settings.ai_voice_type
                                )
                                voice_note = f'{audio_filename.split(".")[0]}.opus'
                                # convert to ogg with ffmpeg

                                subprocess.Popen(
                                    f"ffmpeg -i '{audio_filename}' -c:a libopus {voice_note}",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.STDOUT,
                                ).wait()

                                # remove tts audio
                                if os.path.exists(audio_filename):
                                    os.remove(audio_filename)

                                media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={voice_note}"
                                print(media_url)

                                return vonage_send_audio(client, media_url, number), 200
                            except BotoCoreError:
                                print(traceback.format_exc())
                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                return vonage_send_text(client, text, number), 200
                            except ClientError:
                                print(traceback.format_exc())
                                text = "Sorry, you're response was too long. Please rephrase the question or break it into segments."
                                return vonage_send_text(client, text, number), 200
                        else:
                            return vonage_send_text(client, text, number), 200

                    # Image generation
                    if "dalle" in incoming_msg.lower():
                        prompt = incoming_msg.lower().replace("dalle", "")
                        try:
                            image_url = image_response(prompt)
                            log_response(name=name, number=f"+{number}", message=prompt)
                            return vonage_send_image(client, image_url, number), 200
                        except:
                            print(traceback.format_exc())
                            text = "Sorry, I cannot respond to that at the moment, please try again later."
                            return vonage_send_text(client, text, number), 200
                    else:
                        try:
                            # Chat response
                            try:
                                text, tokens = vonage_text_response(
                                    prompt=incoming_msg, number=number
                                )
                            except TimeoutError:
                                text = "Sorry, your response is taking too long. Try rephrasing your question or breaking it into sections."
                                return vonage_send_text(client, text, number), 200

                            log_response(
                                name=name,
                                number=f"+{number}",
                                message=incoming_msg,
                                tokens=tokens,
                            )

                            return vonage_send_text(client, text, number), 200
                        except:
                            print(traceback.format_exc())
                            text = "Sorry, I cannot respond to that at the moment, please try again later."
                            return vonage_send_text(client, text, number), 200
                else:
                    text = "Please verify your email to access the service. https://braintext.io/profile"
                    return vonage_send_text(client, text, number), 200
            else:
                text = "Please verify your number to access the service. https://braintext.io/profile"
                return vonage_send_text(client, text, number), 200
        else:  # no account found
            text = "To use BrainText, please sign up for an account at https://braintext.io"
            return vonage_send_text(client, text, number), 200
    except:
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return vonage_send_text(client, text, number), 200


@newbot.post("/vonage-chatbot-status")
def vonage_chatbot_status():
    # data = request.get_json()
    # pprint(data)
    return "200"
