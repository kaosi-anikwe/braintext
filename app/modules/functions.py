# python imports
import os
import re
import json
import requests
import traceback
import threading
import subprocess
from typing import Union, Dict, Any
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
from flask import url_for
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
from .. import logger
from ..models import Voices, Users
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
        logger.error(error)

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
    image_response = openai.Image.create_edit(
        image=image, prompt=prompt, n=1, size="1024x1024"
    )
    image_url = image_response.data[0].url
    if os.path.exists(image_path):
        os.remove(image_path)
    return image_url


def create_image_variation(image_path: str) -> str:
    """Creates a variation of an image."""
    image = open(image_path, "rb")
    image_response = openai.Image.create_variation(image=image, n=1, size="512x512")
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


def load_messages(user: Users, prompt: str, db_path: str, original_message=None):
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
        {"role": message.role, "content": message.content if message.content else ""}
        for message in reversed(get_messages)
    ]

    while num_tokens_from_messages(messages) > 4000:
        messages.pop(0)

    # add system prompt
    system = {
        "role": "system",
        "content": f"""
                    You are a youthfull personal assistant. 
                    You always give your opinion on things. 
                    You're conservative about your age. 
                    Your name is BrainText. 
                    Don't make assumptions about what values to plug into functions. 
                    Ask for clarification if a user request is ambiguous.
                    The user's first name is {user.first_name if user.first_name else 'not known'},
                    and the user's last name is {user.last_name if user.last_name else 'not known'}.
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
        logger.error(traceback.format_exc())
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


# ChatGPT ----------------------------------
def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.error("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        logger.warning(
            "Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301."
        )
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        logger.warning(
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
            num_tokens += len(encoding.encode(str(value)))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def chatgpt_response(
    data: Dict[Any, Any], messages: list, number: str, message_id: str = None
) -> tuple | None:
    """Get response from ChatGPT"""
    try:
        # Event to signal the status update function to stop if OpenAI responds on time
        stop_event = threading.Event()

        def status_update():
            """Wait ```n``` seconds and send status update."""
            if not stop_event.wait(15):
                import random

                text = random.choice(WAIT_MESSAGES)
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
            functions=CHATGPT_FUNCTION_DESCRIPTIONS,
            function_call="auto",
        )
        # check for function call
        if completion.choices[0].message.get("function_call"):
            logger.info(completion.choices[0].message.function_call)
            # get function name and arguments
            function_name = completion.choices[0].message.function_call.name
            function_arguments = json.loads(
                completion.choices[0].message.function_call.arguments
            )
            # pass in the request data to the function to be called
            function_arguments["data"] = data
            # pass in the number of tokens used for logging
            function_arguments["tokens"] = int(completion.usage.total_tokens)
            # pass in current user message
            function_arguments["message"] = messages[-1]["content"]
            # call function with arguments as kwargs
            if (
                function_name == "google_search"
                and not function_arguments.get("image_search")
                and not function_arguments.get("file_type")
            ):
                # typical google search
                results = CHATGPT_FUNCTIONS[function_name](**function_arguments)
                messages.append(
                    {"role": "function", "name": "google_search", "content": results}
                )

                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-0613",
                    messages=messages,
                    temperature=1,
                    user=f"{str(number)}",
                    functions=CHATGPT_FUNCTION_DESCRIPTIONS,
                    function_call="auto",
                )

                text = completion.choices[0].message.content
                tokens = int(completion.usage.total_tokens)
                role = completion.choices[0].message.role

                return text, tokens, role
            else:
                CHATGPT_FUNCTIONS[function_name](**function_arguments)
                return None

        text = completion.choices[0].message.content
        tokens = int(completion.usage.total_tokens)
        role = completion.choices[0].message.role

        return text, tokens, role
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I can't respond to that at the moment. Plese try again later."
        return text, 0, "assistant"
    finally:
        # Signal the status update function to stop
        stop_event.set()

        # Wait for status update thread to complete
        thread.join()


# ChatGPT Functions ----------------------------


def generate_image(data: Dict[Any, Any], tokens: int, message: str, prompt: str) -> str:
    """Genereates an image with the given prompt and returns the URL to the image."""
    from ..chatbot.functions import (
        get_name,
        get_number,
        send_image,
    )

    image_response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
    image_url = image_response.data[0].url
    # log response
    name = get_name(data)
    number = f"+{get_number(data)}"
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

    return send_image(image_url, number)


def speech_synthesis(data: Dict[Any, Any], tokens: int, message: str, text: str):
    """Synthesize audio output and send to user."""
    from ..chatbot.functions import (
        send_audio,
        get_number,
        get_name,
    )

    try:
        name = get_name(data)
        number = f"+{get_number(data)}"
        # get voice type
        user = Users.query.filter(Users.phone_no == number).one_or_none()
        voice_type = user.user_settings().ai_voice_type if user else "Joanna"
        # synthesize text
        audio_filename = text_to_speech(
            text=text,
            voice_name=voice_type,
        )
        if audio_filename == None:
            text = "Error synthesizing speech. Please try again later or change the voice type in your settings. https://braintext.io/profile?settings=True"
            return send_text(text, number)
        media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={audio_filename}"
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

        return send_audio(media_url, number)
    except BotoCoreError:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)
    except ClientError:
        logger.error(traceback.format_exc())
        text = "Sorry, your response was too long. Please rephrase the question or break it into segments."
        return send_text(text, number)


def google_search(
    data: Dict[Any, Any],
    tokens: int,
    message: str,
    query: str,
    image_search: bool = False,
    num: int = 0,
    file_type: str = None,
):
    from bs4 import BeautifulSoup
    from ..chatbot.functions import (
        get_number,
        get_name,
    )

    text = None
    number = f"+{get_number(data)}"
    name = get_name(data)
    api_key = str(os.getenv("GOOGLE_SEARCH_API_KEY"))
    cse_id = str(os.getenv("GOOGLE_SEARCH_ENGINE_ID"))
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
    }
    if num > 0:
        params["num"] = num
    if file_type:
        params["fileType"] = file_type
    if image_search:
        params["searchType"] = "image"

    def extract_main_section(soup: BeautifulSoup):
        main_section = soup.find("main")

        if main_section:
            # Exclude headers, footers and sidebars by selecting only the relevant content
            for unwanted_tag in main_section.find_all(["header", "footer", "aside"]):
                unwanted_tag.extract()

            # Extract the remaining text content
            main_content = main_section.get_text()
            return main_content.strip()
        else:
            return False

    try:
        response = requests.get(base_url, params=params)
        response_data = response.json()
        results = ""

        if "items" in response_data:
            items = response_data["items"]
            if items:
                # image search
                if image_search:
                    text = f"{num} Google images of {query}"
                    from ..chatbot.functions import send_image, download_media

                    for image in items:
                        image_name = f"{datetime.now().strftime('%M%S%f')}.png"
                        download_media(image.get("link", ""), image_name)
                        image_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={image_name}"
                        send_image(image_link=image_url, recipient=number)
                    return
                # document search
                if file_type:
                    text = f"{num} {file_type}'s from Google on {query}"
                    from ..chatbot.functions import send_document, download_media

                    for i, document in enumerate(items):
                        document_name = f"{i}_{query}.{file_type}"
                        download_media(document.get("link", ""), document_name)
                        document_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={document_name}"
                        send_document(document_link=document_url, recipient=number)
                    return
                # typical google search
                for item in items:
                    if results:
                        break
                    # Extract the search result link
                    results = item.get("snippet", "")
                    # link = item.get("link", "")
                    # # Scrape content from page
                    # page = requests.get(link)
                    # soup = BeautifulSoup(page.text, "html.parser")
                    # results = extract_main_section(soup)

            else:
                results = f"No results found for: '{query}'"
        else:
            results = f"No results found for: '{query}'"

        # log response
        log_response(
            name=name,
            number=number,
            message=message,
            tokens=tokens,
        )
        # record ChatGPT response
        if text:
            user_db_path = get_user_db(name=name, number=number)
            new_message = {"role": "assistant", "content": text}
            new_message = Messages(new_message, user_db_path)
            new_message.insert()

        return results

    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)


CHATGPT_FUNCTION_DESCRIPTIONS = [
    {
        "name": "generate_image",
        "description": "Generates an image from a user's prompt. Enhance prompt if necessary to give a more detailed prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The image prompt or description to be used to generate the image.",
                },
            },
            "required": ["prompt"],
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
            },
            "required": ["text"],
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
            },
            "required": ["text"],
        },
    },
    {
        "name": "google_search",
        "description": "Searches online for latest information only when it is not already known. Searches for images and documents as requested by the user with the specfied type for document search and number for image and document search.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to be searched online.",
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
                    "description": "Number of images or files requested by the user. Only required if image_search is true or file_type is not empty.",
                },
            },
            "required": ["query"],
        },
    },
]

CHATGPT_FUNCTIONS = {
    "generate_image": generate_image,
    "speech_synthesis": speech_synthesis,
    "google_search": google_search,
}


WAIT_MESSAGES = [
    "Sorry for making you wait. I'm still on it, thanks for being patient!",
    "My bad for the delay. I'm still working on your request. Thanks for hanging in there!",
    "Oops, sorry it's taking a bit longer. I'm still working on it though. Thanks for bearing with me!",
    "Apologies for the wait. I'm still on the case. Thanks for your patience!",
    "My apologies for the holdup. I'm still working on it. Thanks for being cool about it!",
    "Sorry for the delay. I'm still working on your request.",
    "Hey, sorry it's taking a bit longer than expected. I'm still on it, thanks for waiting!",
    "Sorry for keeping you waiting. Just wanted to let you know I'm still working on it. Thanks for being understanding!",
    "Oops, sorry for the wait. I'm still working on your request. Thanks for being patient with me!",
    "My bad for the delay. I'm still on it, thanks for waiting!",
    "Sorry for the wait. I'm still working on your request. Thanks for your patience!",
]
