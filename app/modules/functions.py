# python imports
import os
import re
import json
import base64
import tempfile
import requests
import tempfile
import traceback
import threading
import subprocess
from bs4 import BeautifulSoup
from datetime import datetime
from bs4 import BeautifulSoup
from contextlib import closing
from typing import Union, Dict, Any

# installed imports
import langid
import tiktoken
import pycountry
import pytesseract
from PIL import Image
from boto3 import Session
from openai import OpenAI
from sqlalchemy import desc
from pydub import AudioSegment
from datetime import timedelta
from dotenv import load_dotenv
from flask import url_for, request
from google.cloud import texttospeech, storage
from google.oauth2 import service_account
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from botocore.exceptions import BotoCoreError, ClientError

# local imports
from .. import logger
from ..modules.calculate import *
from ..payment.routes import BANK_CODES
from ..models import Voices, Users, AnonymousUsers, MessageRequests, Threads
from ..modules.messages import create_all, get_engine, Messages
from ..modules.wokspro import record_wokspro_message

# chatgpt functions
from .functions2 import account_settings, record_message
from ..payment.functions import get_account_balance, recharge_account


load_dotenv()

USD2BT = int(os.getenv("USD2BT"))
LOG_DIR = os.getenv("CHATBOT_LOG")
TEMP_FOLDER = os.getenv("TEMP_FOLDER")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
WHATSAPP_TEMPLATE_NAMESPACE = os.getenv("WHATSAPP_TEMPLATE_NAMESPACE")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")
WHATSAPP_CHAR_LIMIT = int(os.getenv("WHATSAPP_CHAR_LIMIT"))
# Meta
TOKEN = os.getenv("META_VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
BASE_URL = "https://graph.facebook.com/v17.0"
URL = f"{BASE_URL}/{PHONE_NUMBER_ID}/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}
# gcloud
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CREDENTIALS = service_account.Credentials.from_service_account_file(
    GOOGLE_APPLICATION_CREDENTIALS
)

# openai
openai_client = OpenAI()


def send_text(
    message: str, recipient: str, phone_number_id=PHONE_NUMBER_ID
) -> Union[str, None]:
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": True, "body": message},
    }
    response = requests.post(
        f"{BASE_URL}/{phone_number_id}/messages", headers=HEADERS, json=data
    )
    if response.status_code == 200:
        data = response.json()
        return str(data["messages"][0]["id"])
    return None


def reply_to_message(
    message_id: str, recipient: str, message: str, phone_number_id=PHONE_NUMBER_ID
) -> Union[str, None]:
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "context": {"message_id": message_id},
        "text": {"preview_url": True, "body": message},
    }
    response = requests.post(
        f"{BASE_URL}/{phone_number_id}/messages", headers=HEADERS, json=data
    )
    if response.status_code == 200:
        data = response.json()
        return str(data["messages"][0]["id"])
    return False


def synthesize_speech(text: str, voice: str) -> str | None:
    # Create a client using the credentials and region defined in the [adminuser]
    # section of the AWS credentials file (~/.aws/credentials).
    session = Session(profile_name="AdministratorAccess-138631087373")
    polly = session.client("polly")
    response = None

    try:
        # Request speech synthesis
        response = polly.synthesize_speech(
            Text=text, OutputFormat="mp3", Engine="neural", VoiceId=voice
        )
    except (BotoCoreError, ClientError) as error:
        # The service returned an error, exit gracefully
        logger.error(error)
        return str(error)

    # Access the audio stream from the response
    if response and "AudioStream" in response:
        # Note: Closing the stream is important because the service throttles on the
        # number of parallel connections. Here we are using contextlib.closing to
        # ensure the close method of the stream object will be called automatically
        # at the end of the with statement's scope.
        with closing(response["AudioStream"]) as stream:
            filename = f"{str(datetime.utcnow().strftime('%d-%m-%Y_%H-%M-%S'))}.mp3"
            output = f"{TEMP_FOLDER}/{filename}"

            try:
                # Open a file for writing the output as a binary stream
                with open(output, "wb") as file:
                    file.write(stream.read())
                return filename
            except IOError as error:
                # Could not write to file, exit gracefully
                logger.error(error)
                return str(error)

    else:
        # The response didn't contain audio data, exit gracefully
        logger.error("Could not stream audio")
        return response


def detect_language(text: str) -> str:
    """
    Detect language using `langid.py`
    """
    language, _ = langid.classify(text)
    return language


def get_country_code(language_code):
    for country in pycountry.countries:
        if hasattr(country, "languages") and language_code in country.languages:
            return country.alpha_2
    return None


def image_to_string(image_path: str):
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        if text:
            return text
        return None
    except:
        logger.error(traceback.format_exc())
        return None


def log_location(name: str, number: str) -> str:
    """Create directory matching first letter of display name.
    \nTo organise logs in alphabetical order.
    \nExample log directory `logs/chatbot/AAA/display_name/<date>`
    \nReturns the log directory to store based on name passed in.
    \nCreates it if it doesn't exist.
    """
    first_char = str(name[0]).upper()
    if first_char.isalpha():  # first character is a letter
        directory = f"{LOG_DIR}/{first_char}{first_char}{first_char}"
        if not os.path.exists(directory):
            os.mkdir(directory)
        user_directory = f"{directory}/{name.replace(' ', '_').strip()}_{number}"
        if not os.path.exists(user_directory):
            os.mkdir(user_directory)
        month_log = os.path.join(
            user_directory, f"{datetime.utcnow().strftime('%m-%Y')}"
        )
        if not os.path.exists(month_log):
            os.mkdir(month_log)
        day_log = f"{month_log}/{datetime.utcnow().strftime('%d-%m-%Y')}.log"
        return day_log

    else:  # first character is not a letter
        directory = f"{LOG_DIR}/###"
        if not os.path.exists(directory):
            os.mkdir(directory)
        user_directory = f"{directory}/{name.replace(' ', '_').strip()}_{number}"
        if not os.path.exists(user_directory):
            os.mkdir(user_directory)
        month_log = os.path.join(
            user_directory, f"{datetime.utcnow().strftime('%m-%Y')}"
        )
        if not os.path.exists(month_log):
            os.mkdir(month_log)
        day_log = f"{month_log}/{datetime.utcnow().strftime('%d-%m-%Y')}.log"
        return day_log


def edit_image(image_path: str, prompt: str) -> str:
    """Edit's a picture with a second picture acting as a mask."""
    image = open(image_path, "rb")
    image_response = openai_client.images.edit(
        image=image,
        prompt=prompt,
        size="512x512",
        n=1,
    )
    image_url = image_response.data[0].url
    if os.path.exists(image_path):
        os.remove(image_path)
    return image_url


def create_image_variation(image_path: str) -> str:
    """Creates a variation of an image."""
    image = open(image_path, "rb")
    image_response = openai_client.images.create_variation(
        image=image,
        size="512x512",
        n=1,
    )
    image_url = image_response.data[0].url
    if os.path.exists(image_path):
        os.remove(image_path)
    return image_url


def log_response(name: str, number: str, message: str, tokens: tuple = 0) -> None:
    with open(log_location(name, number), "a") as file:
        message = message.replace("\n", " ")
        print(
            f"{message} ({tokens}) -- {str(datetime.utcnow().strftime('%H:%M'))}",
            file=file,
        )


def get_audio(audio_url: str, file_name: str) -> None:
    subprocess.Popen(
        f"wget {audio_url} -O '{file_name}.ogg'",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    ).wait()
    # convert to mp3 with ffmpeg
    subprocess.Popen(
        f"ffmpeg -i '{file_name}.ogg' '{file_name}.mp3'",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    ).wait()


def delete_file(filename: str) -> None:
    if os.path.exists(filename):
        os.remove(filename)


def user_dir(number: str, name: str = None) -> str:
    """Returns the user's folder"""
    try:
        if name:
            # get user folder with name and number
            first_char = str(name[0]).upper()
            if first_char.isalpha():
                log_path = os.path.join(
                    LOG_DIR,
                    f"{first_char}{first_char}{first_char}",
                    f"{name.replace(' ', '_').strip()}_{number}",
                )
            else:
                log_path = os.path.join(
                    LOG_DIR,
                    "###",
                    f"{name.replace(' ', '_').strip()}_{number}",
                )
            if not os.path.exists(log_path):
                os.makedirs(log_path, exist_ok=True)
        else:
            # get newest folder in log dir with number
            log_path = None
            newest_timestamp = 0
            for root, dirs, _ in os.walk(LOG_DIR):
                for dir_name in dirs:
                    if number in dir_name:
                        dir_path = os.path.join(root, dir_name)
                        timestamp = os.path.getctime(dir_path)
                        if timestamp > newest_timestamp:
                            newest_timestamp = timestamp
                            log_path = dir_path
        return log_path

    except:
        logger.error(traceback.format_exc())
        return None


def are_same_day(datetime_obj1, datetime_obj2):
    return (
        datetime_obj1.year == datetime_obj2.year
        and datetime_obj1.month == datetime_obj2.month
        and datetime_obj1.day == datetime_obj2.day
    )


def get_user_db(name: str, number: str) -> str:
    """Returns the current user's message database"""
    db_path = os.path.join(user_dir(name=name, number=number), "messages.db")
    if os.path.exists(db_path):
        dp_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
        if not are_same_day(dp_mtime, datetime.utcnow()):
            # delete database
            os.remove(db_path)
    create_all(get_engine(db_path))
    return db_path


def get_last_message_time(user_dir: str) -> datetime | None:
    """Get user's last message time."""
    try:
        # get newest log file in user folder
        newest_file = None
        newest_timestamp = 0

        for root, _, files in os.walk(user_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if not file_path.endswith(".db"):
                    file_timestamp = os.path.getctime(file_path)
                    if file_timestamp > newest_timestamp:
                        newest_timestamp = file_timestamp
                        newest_file = file_path
        if not newest_file:
            return newest_file
        message_date = str(os.path.basename(newest_file)).replace(".log", "")
        # get last message time from file
        message_time = None
        # use re to match time format (HH:MM)
        timestamp_pattern = r" -- (\d{2}:\d{2})$"
        # read last line of log file
        with open(newest_file, "r") as log_file:
            last_line = log_file.readlines()[-1]
            match = re.search(timestamp_pattern, last_line)
            if match:
                message_time = match.group(1)
            else:
                logger.warning(f"No log time found in {newest_file}")
                return None
        # construct last message time
        last_message_time = datetime.strptime(
            f"{message_date} {message_time}", "%d-%m-%Y %H:%M"
        )
        return last_message_time
    except:
        logger.error(traceback.format_exc())
        return None


def load_messages(
    user: Users,
    db_path: str,
    prompt: str = None,
    message_list: list = [],
    original_message=None,
):
    if original_message:
        assistant_mssg = {"role": "assistant", "content": original_message}
        new_assistant_mssg = Messages(assistant_mssg, db_path)
        new_assistant_mssg.insert()
    user_message = {"role": "user", "content": prompt}
    message = Messages(user_message, db_path)
    message.insert()
    # load previous messages
    session = message.session()
    if isinstance(user, Users):
        context_limit = int(user.user_settings().context_messages) or 1
    else:
        context_limit = 10
    get_messages = (
        session.query(Messages).order_by(desc(Messages.id)).limit(context_limit).all()
    )
    messages = [
        {"role": message.role, "content": message.content if message.content else ""}
        for message in reversed(get_messages)
    ]

    if message_list:
        messages.append(message_list[0])
    else:
        while num_tokens_from_messages(messages) > 16000:
            messages.pop(0)

    # add system prompt
    system = {
        "role": "system",
        "content": f"""
                    You are a young personal assistant.
                    You always give your opinion on things.
                    Your name is BrainText.
                    You operate on a currency know as BrainText Tokens (BT)
                    If asked about this currency, refer the user to the usage page ({request.host_url}usage)
                    or pricing page({request.host_url}pricing) based on the nature of the enquire to learn more.
                    Always give {user.user_settings().response_type if isinstance(user, Users) else 'elaborated'} answers.
                    You are in a WhatsApp environment, use the appropriate formatting style.
                    Don't make assumptions about what values to plug into functions and never return an empty response.
                    The user's first name is {user.first_name if user.first_name else 'not known'},
                    and the user's last name is {user.last_name if user.last_name else 'not known'}.
                    The current time is {user.timenow().strftime("%A, %Y-%m-%d %I:%M:%S %p")}\
                    The user's timezone/location is {user.timezone().zone}
                """,
    }
    messages.insert(0, system)
    return messages


def get_audio_duration(file_path) -> float:
    """
    Determine duration of audio file with pydub.\n
    Returns duration as a float in seconds.
    """
    audio_file = AudioSegment.from_file(file_path)
    duration = audio_file.duration_seconds
    return duration


def google_transcribe_audio(
    audio_file: str,
    number: str,
    project_id="braintext-394611",
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file."""
    # Instantiates a client
    client = SpeechClient(credentials=GOOGLE_CREDENTIALS)

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
    )

    # determine audio duration
    duration = get_audio_duration(audio_file)
    if duration < 60:  # synchronous processing
        request = cloud_speech.RecognizeRequest(
            recognizer=f"projects/{project_id}/locations/global/recognizers/_",
            config=config,
            content=content,
        )

        # Transcribes the audio into text
        response = client.recognize(request=request)

        transcript = ""
        for result in response.results:
            transcript += f"{result.alternatives[0].transcript} "

        return transcript
    else:  # asynchronous processing
        logger.info(f"Processing {duration} sec long audio")
        text = "Your audio is longer than a minute. Processing might take longer than usual, please hold on."
        message_id = send_text(text, number)
        # upload to google cloud storage
        bucket_name = "braintext_audio"
        destination_blob_name = f"{datetime.utcnow().strftime('%M%S%f')}"
        storage_client = storage.Client(credentials=GOOGLE_CREDENTIALS)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(audio_file)

        # construct GS URI
        gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"

        file_metadata = cloud_speech.BatchRecognizeFileMetadata(uri=gcs_uri)

        request = cloud_speech.BatchRecognizeRequest(
            recognizer=f"projects/{project_id}/locations/global/recognizers/_",
            config=config,
            files=[file_metadata],
            recognition_output_config=cloud_speech.RecognitionOutputConfig(
                inline_response_config=cloud_speech.InlineOutputConfig(),
            ),
        )

        # Transcribes the audio into text
        operation = client.batch_recognize(request=request)

        response = operation.result(timeout=120)

        transcript = ""
        for result in response.results[gcs_uri].transcript.results:
            transcript += f"{result.alternatives[0].transcript}"

        # delete blob
        blob.delete()

        text = "Almost done."
        reply_to_message(message_id, number, text)

        return transcript


def google_text_to_speech(text: str, voice_name: str) -> str | None:
    """Synthesizes speech from the input string of text or ssml.
    Make sure to be working in a virtual environment.

    Note: ssml must be well-formed according to:
        https://www.w3.org/TR/speech-synthesis/
    """
    try:
        # Instantiates a client
        client = texttospeech.TextToSpeechClient(credentials=GOOGLE_CREDENTIALS)

        # Set the text input to be synthesized
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build the voice request, select the language code
        # Get voice code from db
        voice_code = Voices.query.filter(Voices.name == voice_name).first().code

        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=voice_code,
        )

        # Select the type of audio file you want returned
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.OGG_OPUS
        )

        # Perform the text-to-speech request on the text input with the selected
        # voice parameters and audio file type
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        # The response's audio_content is binary.
        filename = f"{str(datetime.utcnow().strftime('%d-%m-%Y_%H-%M-%S'))}.ogg"
        output = os.path.join(TEMP_FOLDER, filename)
        with open(output, "wb") as out:
            # Write the response to the output file.
            out.write(response.audio_content)
        return filename
    except:
        logger.error(traceback.format_exc())
        return None


def openai_transcribe_audio(
    audio_filepath: str,
):
    """Transcribes an audio file using OpenAI's Whisper"""
    try:
        audio_filepath = convert_audio(audio_filepath)
        audio_file = open(audio_filepath, "rb")
        transcript = openai_client.audio.transcriptions.create(
            file=audio_file, model="whisper-1"
        )
        return transcript.text
    except:
        logger.error(traceback.format_exc())
        if os.path.exists(audio_filepath):
            os.remove(audio_filepath)
        raise Exception("Failed to transcribe audio.")
    finally:
        delete_file(audio_filepath)


def openai_text_to_speech(text: str, voice_name: str, speed: float = 1.0):
    """Performs TTS with the latest TTS model from OpenAI"""
    try:
        # Get voice code from db
        voice_code = Voices.query.filter(Voices.name == voice_name).first().code
        filename = f"{str(datetime.now().strftime('%d-%m-%Y_%H-%M-%S'))}.ogg"
        output = os.path.join(TEMP_FOLDER, filename)
        response = openai_client.audio.speech.create(
            input=text,
            model="tts-1",
            voice=voice_code,
            response_format="opus",
            speed=speed,
        )
        response.stream_to_file(output)
        return filename
    except:
        logger.error(traceback.format_exc())
        if os.path.exists(output):
            os.remove(output)
        return None


def contains_greeting(text):
    # Convert the input text to lowercase to make the comparison case-insensitive
    text = str(text).lower()

    # Define a regular expression pattern to match different greetings
    greeting_pattern = r"\b(hello|hi|yo|hey|good morning|good afternoon|good evening)\b"

    # Use the re.search() function to find the pattern in the text
    match = re.search(greeting_pattern, text)

    # If a match is found, return True; otherwise, return False
    return bool(match)


def contains_thanks(text):
    # Convert the input text to lowercase to make the comparison case-insensitive
    text = str(text).lower()

    # Define a regular expression pattern to match greetings and thanks
    thanks_pattern = r"\b(thank|thanks)\b"

    # Use the re.search() function to find the patterns in the text
    thanks_match = re.search(thanks_pattern, text)

    # If either a greeting or a thanks is found, return True; otherwise, return False
    return bool(thanks_match)


def split_text(text):
    middle_index = len(text) // 2

    # Find the index of the nearest whitespace to the middle index
    while middle_index < len(text) and not text[middle_index].isspace():
        middle_index += 1

    first_half = text[:middle_index]
    second_half = text[middle_index:]
    return first_half, second_half


def get_active_users(timeframe=24):
    from app import create_app
    from app.models import AnonymousUsers

    try:
        app = create_app()
        with app.app_context():
            users = Users.query.filter(Users.phone_no != None).all()
            anonymous_users = AnonymousUsers.query.filter(
                AnonymousUsers.phone_no != None,
                AnonymousUsers.signup_stage != "completed",
            ).all()
            people = [*users, *anonymous_users]
            print(len(users), "users")
            print(len(anonymous_users), "anonymous_users")
            print(len(people), "numbers")
            active = 0
            inactive = 0
            print("Calculating active users.")
            for user in people:
                try:
                    user_folder = user_dir(user.phone_no)
                    if user_folder:
                        last_message = get_last_message_time(user_folder)
                        if not last_message:
                            print(
                                f"Couldn't get last message time for {user.display_name()}"
                            )
                            continue
                        if datetime.now() - last_message > timedelta(hours=timeframe):
                            inactive += 1
                        else:
                            active += 1
                except:
                    print(user_dir(user.phone_no))
                    print(user.display_name())
                    pass
            print("Done")
            print(f"There are about {inactive} inactive users.")
            print(f"There are about {active} active users.")
            return
    except:
        print(traceback.format_exc())
        return


def convert_audio(inputfile: str, outputfile: str = None, dst_format: str = "wav"):
    try:
        if not outputfile:
            outputfile = inputfile
        outputfile = f"{os.path.join(os.path.dirname(outputfile), os.path.basename(outputfile))}.{dst_format}"
        conversion = subprocess.Popen(
            f"ffmpeg -i {inputfile} {outputfile}",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        ).wait()
        if conversion == 0:
            return outputfile
        raise Exception(f"Failed to convert {inputfile} to {dst_format}")
    except:
        logger.error(traceback.format_exc())
        return None


def encode_image(image_path):
    # Function to encode image for image recognition
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def debit_user(
    user: Users,
    name: str,
    bt_cost: float,
    message_request: MessageRequests,
    reason: str = None,
):
    """Debit user and check/alert low balance"""
    user.balance -= bt_cost
    user.update()
    logger.info(
        f"DEDUCTED {bt_cost} FROM USER #{user.id} {reason}. BALANCE IS {user.balance}"
    )
    if isinstance(user, Users):
        if user.balance < user.user_settings().warn_low_balance:
            if not message_request.alert_low:
                from ..chatbot.functions import (
                    generate_interactive_button,
                    send_interactive_message,
                )

                text = f"Your balance is running low. Consider recharging your account.\nCurrent balance is {round(user.balance, 2)}."
                header = "Recharge Now"
                body = "Instantly top up your balance directly on WhatsApp"
                button_texts = ["Yes", "No"]
                button = generate_interactive_button(
                    header=header, body=body, button_texts=button_texts
                )
                record_message(name, user.phone_no, text)
                send_text(text, user.phone_no)
                send_interactive_message(interactive=button, recipient=user.phone_no)
                message_request.alert_low = True
                message_request.update()


# ChatGPT ----------------------------------
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-1106"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.error("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if "gpt-3.5-turbo" in model:
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-4" in model:
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def scrape_website(url, max_words=5000):
    try:
        # Create a temporary file to store the downloaded HTML
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".html"
        ) as temp_file:
            temp_filename = temp_file.name

            # Use wget to download the webpage
            subprocess.run(["wget", "-O", temp_filename, url], check=True)

        # Read the downloaded HTML file
        with open(temp_filename, "r", encoding="utf-8") as html_file:
            html_content = html_file.read()

        # Parse the HTML content of the page
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract text from the main section of the page
        main_content = soup.find("main") or soup.find("body")
        if main_content:
            text = main_content.get_text()

            # Remove extra whitespaces
            text = " ".join(text.split())

            # If the text is less than the specified max_words, return the entire article
            if len(text.split()) < max_words:
                return True, text

            # Limit the text to the specified word count
            text = " ".join(text.split())[:max_words]

            return True, text

        else:
            return False, "Error: Main content not found on the page."

    except subprocess.CalledProcessError as e:
        return False, f"Error: Failed to download the webpage using wget. {e}"

    except Exception as e:
        return False, f"An unexpected error occurred: {e}"

    finally:
        # Clean up temporary HTML file
        if temp_filename and os.path.exists(temp_filename):
            os.remove(temp_filename)


def chatgpt_response(
    data: Dict[Any, Any],
    user: Users,
    messages: list,
    message: str,
    number: str,
    message_request: MessageRequests,
    message_id: str = None,
) -> tuple | None:
    """Get response from ChatGPT"""
    from ..chatbot.functions import get_name

    try:
        # Event to signal the status update function to stop if OpenAI responds on time
        stop_event = threading.Event()

        def status_update():
            """Wait ```n``` seconds and send status update."""
            if not stop_event.wait(15):
                import random

                text = random.choice(WAIT_MESSAGES)
                (
                    send_text(message=text, recipient=number)
                    if not message_id
                    else reply_to_message(
                        message_id=message_id, recipient=number, message=text
                    )
                )

        # set timer
        thread = threading.Thread(target=status_update)
        thread.start()

        # usage tokens
        tokens = [0, 0]

        # get enabled functions
        if isinstance(user, Users):
            enabled_functions = [
                description
                for function in user.user_settings().functions()
                for description in CHATGPT_FUNCTION_DESCRIPTIONS
                if function["name"] == description["name"] and function["enabled"]
            ]
        else:
            enabled_functions = CHATGPT_FUNCTION_DESCRIPTIONS + ANONYMOUS_FUNCTIONS

        logger.info(
            f"Enabled functions: {[func['name'] for func in enabled_functions]}"
        )

        completion = openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            temperature=1,
            functions=enabled_functions,
            function_call="auto",
            max_tokens=user.user_settings().max_response_length
            if isinstance(user, Users)
            else None,
        )
        # update tokens
        tokens[0] += int(completion.usage.prompt_tokens)
        tokens[1] += int(completion.usage.completion_tokens)
        # check for function call
        if completion.choices[0].message.function_call:
            logger.info(completion.choices[0].message.function_call)
            # get function name and arguments
            function_name = completion.choices[0].message.function_call.name
            function_arguments = json.loads(
                completion.choices[0].message.function_call.arguments
            )
            # pass in the request data to the function to be called
            function_arguments["data"] = data
            # pass in the number of tokens used for logging
            function_arguments["tokens"] = tokens
            # pass in current user message
            function_arguments["message"] = message
            # pass in current user message request
            function_arguments["message_request"] = message_request
            # call function with arguments as kwargs
            if CHATGPT_FUNCTIONS[function_name]["type"] == "callback":
                messages.append(
                    completion.choices[0].message.dict(exclude={"tool_calls"})
                )
                logger.info(f"FUNCTION CALL: {messages[-1]}")
                results = CHATGPT_FUNCTIONS[function_name]["function"](
                    **function_arguments
                )
                logger.info(f"CALLBACK FUNCTION CALL RESULTS: {results}")
                messages.append(
                    {"role": "function", "name": function_name, "content": str(results)}
                )
                completion = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo-1106",
                    messages=messages,
                    temperature=1,
                    functions=CHATGPT_FUNCTION_DESCRIPTIONS,
                    function_call="auto",
                )
                # update tokens
                tokens[0] += int(completion.usage.prompt_tokens)
                tokens[1] += int(completion.usage.completion_tokens)

                text = completion.choices[0].message.content
                role = completion.choices[0].message.role
                return text, tokens, role
            else:
                # update request records
                message_request.gpt_3_input = completion.usage.prompt_tokens
                message_request.gpt_3_output = completion.usage.completion_tokens
                message_request.update()
                # charge user
                cost = gpt_3_5_cost(
                    {
                        "input": completion.usage.prompt_tokens,
                        "output": completion.usage.completion_tokens,
                    }
                )
                bt_cost = cost * USD2BT
                # charge user
                debit_user(
                    user=user,
                    name=get_name(data),
                    bt_cost=bt_cost,
                    message_request=message_request,
                    reason="ChatGPT Function call",
                )
                logger.info(
                    f"FUNCTION CALL TOKENS: {int(completion.usage.prompt_tokens), int(completion.usage.completion_tokens)}"
                )
                CHATGPT_FUNCTIONS[function_name]["function"](**function_arguments)
                return None
        else:
            text = completion.choices[0].message.content
            role = completion.choices[0].message.role

            return text, tokens, role
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I can't respond to that at the moment. Plese try again later."
        return text, (0, 0), "assistant"
    finally:
        # Signal the status update function to stop
        stop_event.set()

        # Wait for status update thread to complete
        thread.join()


# ChatGPT Functions ----------------------------
def generate_image(
    data: Dict[Any, Any],
    tokens: int,
    message: str,
    prompt: str,
    message_request: MessageRequests = None,
    **kwargs,
) -> str:
    """Genereates an image with the given prompt and returns the URL to the image."""
    from ..chatbot.functions import (
        get_name,
        get_number,
        send_image,
    )

    # get user
    name = get_name(data)
    number = f"+{get_number(data)}"
    response = kwargs.get("response")
    user = Users.query.filter(Users.phone_no == number).one_or_none()
    image_confg = (
        user.user_settings().image_confg()
        if user
        else "dalle3.natural.standard-1024x1024"
    )
    image_type = image_confg.split(".")[0]
    if not user:
        user = AnonymousUsers.query.filter(
            AnonymousUsers.phone_no == number
        ).one_or_none()
    logger.info(f"DALLE CONFG: {image_confg}")
    if "dalle2" in image_type:
        d2_res = image_confg.split(".")[1]
        if message_request:
            cost = dalle2_cost(image_confg.split(".")[1])
            bt_cost = cost * USD2BT
            if bt_cost > user.balance:
                text = f"Insufficent balance. Cost is {round(bt_cost, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
                logger.info(
                    f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
                )
                record_message(name=name, number=number, message=text)
                return send_text(text, number)
        image_response = openai_client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size=d2_res,
            n=1,
        )
        if message_request:
            # update request records
            message_request.dalle_2 = image_confg
            message_request.update()
            # charge user
            debit_user(
                user=user,
                name=name,
                bt_cost=bt_cost,
                message_request=message_request,
                reason="Dalle2",
            )

    elif "dalle3" in image_type:
        d3_type = image_confg.split(".")[-1].split("-")[0]
        d3_res = image_confg.split(".")[-1].split("-")[1]
        d3_style = image_confg.split(".")[1]
        img_confg = {"type": d3_type, "res": d3_res}
        if message_request:
            cost = dalle3_cost(img_confg)
            bt_cost = cost * USD2BT
            if bt_cost > user.balance:
                text = f"Insufficent balance. Cost is {round(bt_cost, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
                logger.info(
                    f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
                )
                record_message(name=name, number=number, message=text)
                return send_text(text, number)
        image_response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=d3_res,
            quality=d3_type,
            style=d3_style,
            n=1,
        )
        if message_request:
            # update request records
            message_request.dalle_3 = image_confg
            message_request.update()
            # charge user
            debit_user(
                user=user,
                name=name,
                bt_cost=bt_cost,
                message_request=message_request,
                reason="Dalle3",
            )

    image_url = image_response.data[0].url
    if message_request:
        log_response(
            name=name,
            number=number,
            message=message,
            tokens=tokens,
        )
        # record ChatGPT response
        user_db_path = get_user_db(name=name, number=number)
        new_message = {
            "role": "assistant",
            "content": f"```an AI generated image of {prompt}```",
        }
        new_message = Messages(new_message, user_db_path)
        new_message.insert()

    return (
        send_image(image_url, number, caption=response)
        if message_request
        else send_image(
            image_url,
            number,
            caption=response,
            phone_number_id=kwargs.get("wokspro_id"),
        )
    )


def speech_synthesis(
    data: Dict[Any, Any],
    tokens: tuple,
    message: str,
    text: str,
    message_request: MessageRequests = None,
    speed: float = 1.0,
    thread: Threads = None,
    **kwargs,
):
    """Synthesize audio output and send to user."""
    from ..chatbot.functions import (
        send_audio,
        get_number,
        get_name,
    )

    anonymous = False
    wokspro_id = kwargs.get("wokspro_id") or os.getenv("WOKSPRO_NUMBER_ID")
    # get user
    name = get_name(data)
    number = f"+{get_number(data)}"
    user = Users.query.filter(Users.phone_no == number).one_or_none()
    if not user:
        anonymous = True
        user = AnonymousUsers.query.filter(
            AnonymousUsers.phone_no == number
        ).one_or_none()
    try:
        if not text:
            text = "Error synthesizing speech. Please try again later."
            record_message(
                name=name, number=number, message=text
            ) if message_request else record_wokspro_message(thread, text, "assistant")
            return (
                send_text(text, number)
                if message_request
                else send_text(text, number, wokspro_id)
            )
        if message_request:
            cost = tts_cost(len(text))
            logger.info(f"TTS COST: {len(text)} CHARACTERS")
            bt_cost = cost * USD2BT
            if bt_cost > user.balance:
                text = f"Insufficent balance. Cost is {round(bt_cost, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
                logger.info(
                    f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
                )
                record_message(name=name, number=number, message=text)
                return send_text(text, number)

        # get voice type
        voice_type = user.user_settings().audio_voice if not anonymous else "Mia"
        # synthesize text
        audio_filename = openai_text_to_speech(
            text=text, voice_name=voice_type, speed=speed
        )
        if audio_filename == None:
            text = "Error synthesizing speech. Please try again later."
            record_message(
                name=name, number=number, message=text
            ) if message_request else record_wokspro_message(thread, text, "assistant")
            return (
                send_text(text, number)
                if message_request
                else send_text(text, number, wokspro_id)
            )
        if message_request:
            # update request records
            message_request.tts = len(text)
            message_request.update()
            # charge user
            debit_user(
                user=user,
                name=name,
                bt_cost=bt_cost,
                message_request=message_request,
                reason="TTS",
            )
        media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={audio_filename}"
        if message_request:
            # log response
            log_response(
                name=name,
                number=number,
                message=message,
                tokens=tokens,
            )
            # record ChatGPT response
            user_db_path = get_user_db(name=name, number=number)
            new_message = {"role": "assistant", "content": text}
            new_message = Messages(new_message, user_db_path)
            new_message.insert()

        return (
            send_audio(media_url, number)
            if message_request
            else send_audio(media_url, number, wokspro_id)
        )
    except BotoCoreError:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        record_message(
            name=name, number=number, message=text
        ) if message_request else record_wokspro_message(thread, text, "assistant")
        return (
            send_text(text, number)
            if message_request
            else send_text(text, number, wokspro_id)
        )
    except ClientError:
        logger.error(traceback.format_exc())
        text = "Sorry, your response was too long. Please rephrase the question or break it into segments."
        record_message(
            name=name, number=number, message=text
        ) if message_request else record_wokspro_message(thread, text, "assistant")
        return (
            send_text(text, number)
            if message_request
            else send_text(text, number, wokspro_id)
        )


def google_search(
    data: Dict[Any, Any],
    query: str,
    **kwargs,
):
    api_key = str(os.getenv("GOOGLE_SEARCH_API_KEY"))
    cse_id = str(os.getenv("GOOGLE_SEARCH_ENGINE_ID"))
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
    }

    try:
        response = requests.get(base_url, params=params)
        response_data = response.json()
        results = ""
        success = False

        items = response_data.get("items", [])
        logger.info(f"Result items: {len(items)}")
        if items:
            # typical google search
            for item in items:
                if success:
                    break
                # Extract the search result link
                results = item.get("snippet", "")
                url = item.get("link", "")
                try:
                    # Scrape content from page
                    success, results = scrape_website(url)
                except Exception as e:
                    logger.error(e)
                if not results:
                    results = f"No results found for: '{query}'"
        else:
            results = f"No results found for: '{query}'"

        return {"results": results}  # to be returned to ChatGPT to format for user

    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return {"error": text}


def media_search(data: Dict[Any, Any], **kwargs):
    from ..chatbot.functions import (
        get_number,
        get_name,
    )

    not_found = False
    image_search = kwargs.get("image_search")
    num = int(kwargs.get("num", 1))
    file_type = kwargs.get("file_type")
    message = kwargs.get("message")
    tokens = kwargs.get("tokens")
    number = f"+{get_number(data)}"
    name = get_name(data)
    query = kwargs.get("query")
    api_key = str(os.getenv("GOOGLE_SEARCH_API_KEY"))
    cse_id = str(os.getenv("GOOGLE_SEARCH_ENGINE_ID"))
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": num,
    }
    if file_type:
        params["fileType"] = file_type
    if image_search:
        params["searchType"] = "image"
    try:
        response = requests.get(base_url, params=params)
        response_data = response.json()
        search_response = kwargs.get("response")
        results = ""

        items = response_data.get("items", [])
        logger.info(f"Result items: {len(items)}")
        if items:
            # image search
            if image_search:
                if kwargs.get("message_request"):
                    send_text(search_response, number) if search_response else None
                else:
                    send_text(
                        search_response, number, kwargs.get("wokspro_id")
                    ) if search_response else None
                results = f"{num} Google images of {query}"
                from ..chatbot.functions import send_image, download_media

                for image in items:
                    image_name = f"{datetime.now().strftime('%M%S%f')}.png"
                    logger.info(f"IMAGE URL: {image.get('link', '')}")
                    ok = download_media(image.get("link", ""), image_name)
                    if ok:
                        image_url = f"{url_for('chatbot.send_media', _external=True, _scheme='https')}?filename={image_name}"
                        send_image(
                            image_link=image_url, recipient=number
                        ) if kwargs.get("message_request") else send_image(
                            image_link=image_url,
                            recipient=number,
                            phone_number_id=kwargs.get("wokspro_id"),
                        )
            # document search
            if file_type:
                if kwargs.get("message_request"):
                    send_text(search_response, number) if search_response else None
                else:
                    send_text(
                        search_response, number, kwargs.get("wokspro_id")
                    ) if search_response else None
                results = f"{num} {file_type}'s from Google on {query}"
                from ..chatbot.functions import send_document, download_media

                for i, document in enumerate(items):
                    document_name = f"{i}_{query}.{file_type}".replace(" ", "_")
                    logger.info(f"DOCUMENT URL: {document.get('link', '')}")
                    ok = download_media(document.get("link", ""), document_name)
                    if ok:
                        document_url = f"{url_for('chatbot.send_media', _external=True, _scheme='https')}?filename={document_name}"
                        send_document(
                            document_link=document_url, recipient=number
                        ) if kwargs.get("message_request") else send_document(
                            document_link=document_url,
                            recipient=number,
                            phone_number_id=kwargs.get("wokspro_id"),
                        )
        else:
            results = f"No results found for: '{query}'"
            not_found = True

        if kwargs.get("message_request"):
            log_response(
                name=name,
                number=number,
                message=message,
                tokens=tokens,
            )

            # record ChatGPT response
            user_db_path = get_user_db(name=name, number=number)
            new_message = {"role": "assistant", "content": results}
            new_message = Messages(new_message, user_db_path)
            new_message.insert()

        if kwargs.get("message_request"):
            return send_text(results, number) if not_found else None
        else:
            return (
                send_text(results, number, kwargs.get("wokspro_id"))
                if not_found
                else None
            )
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        record_message(name=name, number=number, message=text) if kwargs.get(
            "message_request"
        ) else None
        return (
            send_text(text, number)
            if kwargs.get("message_request")
            else send_text(text, number, kwargs.get("wokspro_id"))
        )


def web_scrapping(data: Dict[Any, Any], **kwargs):
    url = kwargs.get("url")
    instructions = kwargs.get("instruction", "Summarize this.")
    try:
        _, results = scrape_website(url)
        return {"instructions": instructions, "results": results}
    except:
        logger.error(traceback.format_exc())
        return {"error": "Error scrapping URL."}


def create_account(data: Dict[Any, Any], **kwargs):
    from ..chatbot.functions import (
        get_number,
        generate_interactive_button,
        send_interactive_message,
    )

    number = f"+{get_number(data)}"
    body = "How would you like to register?"
    header = "Register to Continue"
    button_texts = ["Our website", "Continue here"]
    button = generate_interactive_button(
        body=body, header=header, button_texts=button_texts
    )
    return send_interactive_message(interactive=button, recipient=number)


CHATGPT_FUNCTION_DESCRIPTIONS = [
    {
        "name": "generate_image",
        "description": "Generates an image with prompt extracted from user only on explicit request.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The image prompt or description to be used to generate the image.",
                },
                "response": {
                    "type": "string",
                    "description": "User friendly response to prompt.",
                },
            },
            "required": ["prompt", "response"],
        },
    },
    {
        "name": "speech_synthesis",
        "description": "Synthesize text response of prompts to audio when user requests for an audio response.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text prompt response to be synthesized",
                },
                "speed": {
                    "type": "number",
                    "description": "How fast or slow the audio response should be. Values range from 0.25 to 4.0. The default is 1.0",
                },
            },
            "required": ["text", "speed"],
        },
    },
    {
        "name": "speech_synthesis",
        "description": "Performs text-to-speech synthesis on user request.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to be synthesized into speech.",
                },
                "speed": {
                    "type": "number",
                    "description": "How fast or slow the synthesised speech should be. Values range from 0.25 to 4.0. The default is 1.0",
                },
            },
            "required": ["text", "speed"],
        },
    },
    {
        "name": "google_search",
        "description": "Performs online searches to retrieve information only on explicit request.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to be searched online coined from user prompt.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "media_search",
        "description": "Performs media searches on the internet. Takes in a user-friendly response to the query, a boolean for if image search or not, the file type if a document was requested, and the number of results",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to be searched online coined from user prompt.",
                },
                "response": {
                    "type": "string",
                    "description": "User-friendly response to prompt for image and document search.",
                },
                "image_search": {
                    "type": "boolean",
                    "description": "Wether or not the user requested for an image in the query.",
                },
                "file_type": {
                    "type": "string",
                    "description": "The type of file requested by the user in the query.",
                },
                "num": {
                    "type": "integer",
                    "description": "Number of results to be gotten. Default is 1.",
                },
            },
            "required": ["query", "num", "response"],
        },
    },
    {
        "name": "web_scrapping",
        "description": "Scrapes the URL provided by the user with the provided instruction.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to be scrapped.",
                },
                "instruction": {
                    "type": "string",
                    "description": "Sentence instruction for formatting web scrapping results. The default is to summarize.",
                },
            },
            "required": ["url", "instruction"],
        },
    },
    {
        "name": "get_account_balance",
        "description": "Returns the user's balance on enquiry.",
        "parameters": {},
    },
    {
        "name": "recharge_account",
        "description": f"Creates a new account recharge request. Verify with the user the amount, currency, and bank from this list of banks: {[bank for bank in BANK_CODES.keys()]}. Non NGN requests are not accepted.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "The amount the user wishes to recharge.",
                },
                "currency": {
                    "type": "string",
                    "description": "The currency code the user wishes to recharge (eg NGN).",
                },
                "bank_name": {
                    "type": "string",
                    "description": "The selected bank from the list provided.",
                },
            },
            "required": ["amount", "currency", "bank_name"],
        },
    },
    {
        "name": "account_settings",
        "description": "Returns the user's settings",
        "parameters": {},
    },
]


ANONYMOUS_FUNCTIONS = [
    {
        "name": "create_account",
        "description": "Enables the user to create an account.",
        "parameters": {},
    }
]


CHATGPT_FUNCTIONS = {
    "generate_image": {
        "type": "non-callback",
        "function": generate_image,
    },
    "speech_synthesis": {
        "type": "non-callback",
        "function": speech_synthesis,
    },
    "google_search": {
        "type": "callback",
        "function": google_search,
    },
    "media_search": {
        "type": "non-callback",
        "function": media_search,
    },
    "web_scrapping": {
        "type": "callback",
        "function": web_scrapping,
    },
    "get_account_balance": {
        "type": "non-callback",
        "function": get_account_balance,
    },
    "recharge_account": {
        "type": "non-callback",
        "function": recharge_account,
    },
    "account_settings": {"type": "non-callback", "function": account_settings},
    "create_account": {"type": "non-callback", "function": create_account},
}


WAIT_MESSAGES = [
    "Sorry for making you wait.",
    "My bad for the delay.",
    "Oops, sorry it's taking a bit longer.",
    "Apologies for the wait.",
    "My apologies for the holdup.",
    "Sorry for the delay.",
    "Hey, sorry it's taking a bit longer than expected.",
    "Sorry for keeping you waiting.",
    "Oops, sorry for the wait.",
    "My bad for the delay.",
    "Sorry for the wait.",
]
