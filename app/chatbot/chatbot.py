import os
import subprocess
import openai
from datetime import datetime
from dotenv import load_dotenv
from flask import Blueprint, request, url_for, send_file
from twilio.twiml.messaging_response import MessagingResponse
from app.models import (
    Users,
    BasicSubscription,
    StandardSubscription,
    PremiumSubscription,
)

from boto3 import Session
from botocore.exceptions import BotoCoreError, ClientError
from contextlib import closing
import os
import subprocess


load_dotenv()

chatbot = Blueprint("chatbot", __name__)

openai_url = "https://api.openai.com/v1/completions"
openai.api_key = os.getenv("OPENAI_API_KEY")

# create log folder if not exists
if not os.path.exists("logs/chatbot"):
    os.makedirs("logs/chatbot")
# create tmp folder if not exists
if not os.path.exists("/home/braintext/website/tmp"):
    os.makedirs("/home/braintext/website/tmp")

log_dir = "logs/chatbot"
tmp_folder = "/home/braintext/website/tmp"


def synthesize_speech(text: str, voice: str) -> str:
    # Create a client using the credentials and region defined in the [adminuser]
    # section of the AWS credentials file (~/.aws/credentials).
    session = Session(profile_name="AdministratorAccess-138631087373")
    polly = session.client("polly")

    try:
        # Request speech synthesis
        response = polly.synthesize_speech(
            Text=text, OutputFormat="ogg_vorbis", Engine="neural", VoiceId=voice
        )
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        print(error)

    # Access the audio stream from the response
    if "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            filename = f"{str(datetime.utcnow().strftime('%d-%m-%Y_%H-%M-%S'))}.ogg"
            output = f"{tmp_folder}/{filename}"

            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
                return output
            except IOError as error:
                # Could not write to file, exit gracefully
                print(error)

    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")


def log_location(name: str, number: str) -> str:
    """Create directory matching first letter of display name.
    \nTo organise logs in alphabetical order.
    \nExample log directory `logs/chatbot/AAA/display_name/<date>`
    \nReturns the log directory to store based on name passed in.
    \nCreates it if it doesn't exist.
    """
    first_char = str(name[0]).upper()
    if first_char.isalpha():  # first character is a letter
        directory = f"{log_dir}/{first_char}{first_char}{first_char}"
        if not os.path.exists(directory):
            os.mkdir(directory)
        user_directory = f"{directory}/{name.replace(' ', '_').strip()}_{number}"
        if not os.path.exists(user_directory):
            os.mkdir(user_directory)
        day_log = f"{user_directory}/{datetime.utcnow().strftime('%d-%m-%Y')}.log"
        return day_log

    else:  # first character is not a letter
        directory = f"{log_dir}/###"
        if not os.path.exists(directory):
            os.mkdir(directory)
        user_directory = f"{directory}/{name.replace(' ', '_').strip()}_{number}"
        if not os.path.exists(user_directory):
            os.mkdir(user_directory)
        day_log = f"{user_directory}/{datetime.utcnow().strftime('%d-%m-%Y')}.log"
        return day_log


def respond_text(text: str) -> str:
    response = MessagingResponse()
    message = response.message()
    message.body(text)

    return str(response)


def respond_media(image_url: str) -> str:
    response = MessagingResponse()
    message = response.message()
    message.media(image_url)

    return str(response)


def text_response(message: str, number: str) -> tuple:
    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=message,
        max_tokens=2000,
        temperature=0.2,
        user=f"{str(number)}",
    )
    text = completion.choices[0].text
    tokens = int(completion.usage.total_tokens)

    return text, tokens


def image_response(prompt: str) -> str:
    image_response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
    image_url = image_response.data[0].url
    return image_url


def log_response(name: str, number: str, message: str, tokens: int = 0) -> None:
    with open(log_location(name, number), "a") as file:
        message = message.replace("\n", " ")
        print(
            f"{message} ({tokens}) -- {str(datetime.now().strftime('%H:%M'))}",
            file=file,
        )


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
                        if subscription.respond():
                            incoming_msg = request.values.get("Body", "")
                            name = request.values.get("ProfileName")
                            try:
                                completion = text_response(incoming_msg, number)
                                text = completion[0]
                                tokens = completion[1]

                                log_response(
                                    name=name,
                                    number=number,
                                    message=incoming_msg,
                                    tokens=tokens,
                                )
                                return respond_text(text)

                            except Exception as e:
                                print(e)
                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                return respond_text(text)
                        else:
                            text = f"You have exceed your limit for the week.\nYour prompts will be renewed on {subscription.expire_date.strftime('%A, %d/%m/%Y')} at {subscription.expire_date.strftime('%I:%M %p')}.\nUpgrade your account to decrease limits.\nhttps://braintext.io/profile"
                            return respond_text(text)
                    else:
                        text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                        return respond_text(text)

                if user.account_type == "Standard":
                    # get all records for user
                    subscriptions = StandardSubscription.query.filter(
                        StandardSubscription.user_id == user.id
                    ).all()
                    subscription = None
                    for sub in subscriptions:
                        # get the active subscription or assign None
                        if not sub.expired():
                            subscription = sub
                    if subscription:

                        incoming_msg = request.values.get("Body", "")
                        name = request.values.get("ProfileName")
                        # Image generation
                        if "dalle" in incoming_msg.lower():
                            prompt = incoming_msg.lower().replace("dalle", "")
                            try:
                                image_url = image_response(prompt)
                                log_response(name=name, number=number, message=prompt)
                                return respond_media(image_url)
                            except Exception as e:
                                print(e)
                                text = (
                                    text
                                ) = "Sorry, I cannot respond to that at the moment, please try again later."
                                return respond_text(text)
                        else:
                            # Chat response
                            try:
                                completion = text_response(incoming_msg, number)
                                text = completion[0]
                                tokens = completion[1]

                                log_response(
                                    name=name,
                                    number=number,
                                    message=incoming_msg,
                                    tokens=tokens,
                                )
                                return respond_text(text)
                            except Exception as e:
                                print(e)
                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                return respond_text(text)
                    else:
                        text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                        return respond_text(text)

                if user.account_type == "Premium":
                    # get all records for user
                    subscriptions = PremiumSubscription.query.filter(
                        PremiumSubscription.user_id == user.id
                    ).all()
                    subscription = None
                    for sub in subscriptions:
                        # get the active subscription or assign None
                        if not sub.expired():
                            subscription = sub
                    if subscription:
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

                            with open(f"{tmp_file}.mp3", "rb") as file:
                                transcript = openai.Audio.transcribe("whisper-1", file)

                            # remove tmp files
                            if os.path.exists(f"{tmp_file}.ogg"):
                                os.remove(f"{tmp_file}.ogg")
                            if os.path.exists(f"{tmp_file}.mp3"):
                                os.remove(f"{tmp_file}.mp3")

                            prompt = transcript.text
                            try:
                                completion = text_response(prompt, number)
                                text = completion[0]
                                tokens = completion[1]

                                log_response(
                                    name=name,
                                    number=number,
                                    message=prompt,
                                    tokens=tokens,
                                )

                                audio_filename = synthesize_speech(text=text, voice=user.ai_voice)

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

                                media_url = f"{url_for('chatbot.send_voice_note', _external=True)}?filename={audio_filename.split('.')[0]}.opus"

                                return respond_media(media_url)
                            except Exception as e:
                                print(e)
                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                return respond_text(text)

                        # Image generation
                        if "dalle" in incoming_msg.lower():
                            prompt = incoming_msg.lower().replace("dalle", "")
                            try:
                                image_url = image_response(prompt)
                                log_response(name=name, number=number, message=prompt)
                                return respond_media(image_url)
                            except Exception as e:
                                print(e)
                                text = (
                                    text
                                ) = "Sorry, I cannot respond to that at the moment, please try again later."
                                return respond_text(text)
                        else:
                            # Chat response
                            try:
                                completion = text_response(incoming_msg, number)
                                text = completion[0]
                                tokens = completion[1]

                                log_response(
                                    name=name,
                                    number=number,
                                    message=incoming_msg,
                                    tokens=tokens,
                                )
                                return respond_text(text)
                            except Exception as e:
                                print(e)
                                text = "Sorry, I cannot respond to that at the moment, please try again later."
                                return respond_text(text)
                            # TODO: add whisper
                            # add image variation
                            # remebering pervious message
                    else:
                        text = "There's a problem, I can't respond at this time.\nCheck your settings in your profle. https://braintext.io/profile"
                        return respond_text(text)
            else:
                text = "Please verify your email to access the service. https://braintext.io/profile"
                respond_text(text)
        else:
            text = "Please verify your number to access the service. https://braintext.io/profile"
    else:  # no account found
        text = "To use BrainText, please sign up for an account at https://braintext.io"
        return respond_text(text)


@chatbot.post("/braintext-chatbot-fallback")
def fallback():
    print("Timed out")
    return bot()
