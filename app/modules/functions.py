# python imports
import os
import re
import time
import requests
import traceback
import threading
import subprocess
from typing import Union
from datetime import datetime
from contextlib import closing

# installed imports
import openai
import langid
import tiktoken
import pycountry
import pytesseract
from PIL import Image
from boto3 import Session
from sqlalchemy import desc
from dotenv import load_dotenv
from pydub import AudioSegment
from twilio.rest import Client
from google.cloud import texttospeech, storage
from google.oauth2 import service_account
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from botocore.exceptions import BotoCoreError, ClientError

# local imports
from ..models import Voices
from ..twilio_chatbot.functions import (
    respond_text,
    get_original_message,
)
from ..modules.messages import create_all, get_engine, Messages


load_dotenv()

LOG_DIR = os.getenv("CHATBOT_LOG")
TEMP_FOLDER = os.getenv("TEMP_FOLDER")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
WHATSAPP_TEMPLATE_NAMESPACE = os.getenv("WHATSAPP_TEMPLATE_NAMESPACE")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")
CONTEXT_LIMIT = int(os.getenv("CONTEXT_LIMIT"))
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


class TimeoutError(Exception):
    # custom timeout class to handle ChatGPT timeout
    pass


def send_otp_message(client: Client, otp: int, name: str, phone_no: str) -> str:
    message = client.messages.create(
        body=f"Hi {name}! Here's your One Time Password to verify your number at Braintext. \n{otp} \nThe OTP will expire in 3 minutes.",
        from_="whatsapp:+15076094633",
        to=f"whatsapp:{phone_no}",
    )
    print(f"{message.sid} -- {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return message.sid


def send_whatspp_message(client: Client, message: str, phone_no: str) -> str:
    message = client.messages.create(
        body=message,
        from_="whatsapp:+15076094633",
        to=f"whatsapp:{phone_no}",
    )
    print(f"{message.sid} -- {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return message.sid


def send_text(message: str, recipient: str) -> Union[str, None]:
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": True, "body": message},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        data = response.json()
        return str(data["messages"][0]["id"])
    return None


def reply_to_message(message_id: str, recipient: str, message: str) -> Union[str, None]:
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "context": {"message_id": message_id},
        "text": {"preview_url": True, "body": message},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
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
        print(error)

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
                print(error)

    else:
        # The response didn't contain audio data, exit gracefully
        print("Could not stream audio")
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
        print(traceback.format_exc())
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


def image_response(prompt: str) -> str:
    image_response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
    image_url = image_response.data[0].url
    return image_url


def image_edit(image_path: str, prompt: str) -> str:
    image = open(image_path, "rb")
    image_response = openai.Image.create_edit(
        image=image, prompt=prompt, n=1, size="1024x1024"
    )
    image_url = image_response.data[0].url
    if os.path.exists(image_path):
        os.remove(image_path)
    return image_url


def image_variation(image_path: str) -> str:
    image = open(image_path, "rb")
    image_response = openai.Image.create_variation(image=image, n=1, size="1024x1024")
    image_url = image_response.data[0].url
    if os.path.exists(image_path):
        os.remove(image_path)
    return image_url


def log_response(name: str, number: str, message: str, tokens: int = 0) -> None:
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


def chatgpt_response(messages: list, number: str, message_id: str = None) -> tuple:
    """Get response from ChatGPT"""

    # Event to signal the status update function to stop if OpenAI responds on time
    stop_event = threading.Event()

    def status_update():
        """Wait ```n``` seconds and send status update."""
        if not stop_event.wait(15):
            text = "Sorry for the wait. I'm still working on your request. Thanks for your patience!"
            send_text(
                message=text, recipient=number
            ) if not message_id else reply_to_message(
                message_id=message_id, recipient=number, message=text
            )

    # set timer
    thread = threading.Thread(target=status_update)
    thread.start()

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        temperature=1,
        user=f"{str(number)}",
    )

    text = completion.choices[0].message.content
    tokens = int(completion.usage.total_tokens)
    role = completion.choices[0].message.role

    # Signal the status update function to stop
    stop_event.set()

    # Wait for status update thread to complete
    thread.join()

    return text, tokens, role


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
        print(traceback.format_exc())
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
                print(f"No log time found in {newest_file}")
                return None
        # construct last message time
        last_message_time = datetime.strptime(
            f"{message_date} {message_time}", "%d-%m-%Y %H:%M"
        )
        return last_message_time
    except:
        print(traceback.format_exc())
        return None


def load_messages(prompt: str, db_path: str, original_message=None):
    if original_message:
        assistant_mssg = {"role": "assistant", "content": original_message}
        new_assistant_mssg = Messages(assistant_mssg, db_path)
        new_assistant_mssg.insert()
    user_message = {"role": "user", "content": prompt}
    message = Messages(user_message, db_path)
    message.insert()
    # load previous messages
    session = message.session()
    get_messages = (
        session.query(Messages).order_by(desc(Messages.id)).limit(CONTEXT_LIMIT).all()
    )
    messages = [
        {"role": message.role, "content": message.content}
        for message in reversed(get_messages)
    ]

    while num_tokens_from_messages(messages) > 4000:
        messages.pop(0)

    # add system prompt
    system = {
        "role": "system",
        "content": "You are a youthfull personal assistant. Never tell anyone that you're an AI language model or language model. You always give your opinion on things. You're conservative about your age. Your name is BrainText.",
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


def transcribe_audio(
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
        print(f"Processing {duration} sec long audio")
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


def text_to_speech(text: str, voice_name: str) -> str | None:
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
        print(traceback.format_exc())
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


# ChatGPT ----------------------------------
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print(
            "Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301."
        )
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print(
            "Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314."
        )
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
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
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    # print(str(num_tokens))
    return num_tokens


def split_text(text):
    middle_index = len(text) // 2

    # Find the index of the nearest whitespace to the middle index
    while middle_index < len(text) and not text[middle_index].isspace():
        middle_index += 1

    first_half = text[:middle_index]
    second_half = text[middle_index:]
    return first_half, second_half
