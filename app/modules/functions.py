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
import tiktoken
import timeout_decorator
from boto3 import Session
from sqlalchemy import desc
from dotenv import load_dotenv
from twilio.rest import Client
from botocore.exceptions import BotoCoreError, ClientError
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech

# local imports
from ..modules.messages import create_all, get_engine, Messages
from ..twilio_chatbot.functions import (
    respond_text,
    get_original_message,
)

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


def check_and_respond_text(client: Client, text: str, number: str) -> str:
    print(f"Text is {len(text)} characters long.")
    text_length = len(text)
    while text_length >= 3200:
        first
    # check if response is too long
    if len(text) >= 3200:
        # too long even if halved
        text = "Your response is too long. Please rephrase your question."
        return respond_text(text)
    elif len(text) >= 1600:
        print(f"Text was split.")
        # split message into 2. Send first half and return second half
        sentences = text.split(". ")
        sentence_count = len(sentences)
        print(f"Number of sentences: {sentence_count}")
        first = int(sentence_count / 2)
        second = sentence_count - first
        first_part = ""
        second_part = ""
        for index, sentence in enumerate(sentences):
            if index <= first:
                if index == 0:
                    first_part += f"{sentence}"
                first_part += f". {sentence}"
            elif index >= second:
                if index == second:
                    second_part += f"{sentence}"
                second_part += f". {sentence}"
        print(f"Length of first part: {len(first_part)}")
        print(f"Lenght of second part: {len(second_part)}")
        if len(first_part) >= 1600:
            # further divide into 2 and send individually
            sentences = first_part.split(". ")
            sentence_count = len(sentences)
            first = int(sentence_count / 2)
            second = sentence_count - first
            part_one = ""
            part_two = ""
            for index, sentence in enumerate(sentences):
                if index <= first:
                    part_one += f". {sentence}"
                elif index >= second:
                    part_two += f". {sentence}"

            send_whatspp_message(client=client, message=part_one, phone_no=number)
            send_whatspp_message(client=client, message=part_two, phone_no=number)

            text = second_part
            return respond_text(text)

        elif len(second_part) >= 1600:
            # further divide into 2 and send first part
            sentences = first_part.split(". ")
            sentence_count = len(sentences)
            first = int(sentence_count / 2)
            second = sentence_count - first
            part_one = ""
            part_two = ""
            for index, sentence in enumerate(sentences):
                if index <= first:
                    part_one += f". {sentence}"
                elif index >= second:
                    part_two += f". {sentence}"

            send_whatspp_message(client=client, message=first_part, phone_no=number)
            send_whatspp_message(client=client, message=part_one, phone_no=number)

            text = part_two
            return respond_text(text)

        # send message
        send_whatspp_message(client=client, message=first_part, phone_no=number)

        text = second_part
        return respond_text(text)
    else:
        return respond_text(text)


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


def text_response(messages: list, number: str, message_id: str = None) -> tuple:
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
        model="gpt-3.5-turbo-0301",
        messages=messages,
        temperature=0.8,
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


def chat_reponse(
    client, request_values, name, number, incoming_msg, user, subscription=None
):
    """Typical WhatsApp text response"""
    try:
        if subscription:
            if subscription.expired():
                subscription.update_account(user.id)
                text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                return respond_text(text)
        try:
            isreply = False
            if request_values.get("OriginalRepliedMessageSender"):
                # message is a reply. Get original
                original_message_sid = request_values.get("OriginalRepliedMessageSid")
                original_message = get_original_message(client, original_message_sid)
                isreply = True
            user_db_path = get_user_db(name=name, number=number)
            messages = (
                load_messages(
                    prompt=incoming_msg,
                    db_path=user_db_path,
                    original_message=original_message,
                )
                if isreply
                else load_messages(prompt=incoming_msg, db_path=user_db_path)
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
            message=incoming_msg,
            tokens=tokens,
        )
        if len(text) < WHATSAPP_CHAR_LIMIT:
            return respond_text(text)
        return split_and_respond(client, text, number)
    except:
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return respond_text(text)


def user_dir(name: str, number: str) -> str:
    """Returns the user's folder"""
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

    return log_path


def are_same_day(datetime_obj1, datetime_obj2):
    return (
        datetime_obj1.year == datetime_obj2.year
        and datetime_obj1.month == datetime_obj2.month
        and datetime_obj1.day == datetime_obj2.day
    )


def get_user_db(name: str, number: str) -> str:
    """Returns the current user's message database"""
    db_path = os.path.join(user_dir(name, number), "messages.db")
    if os.path.exists(db_path):
        dp_mtime = datetime.fromtimestamp(os.path.getmtime(db_path))
        if not are_same_day(dp_mtime, datetime.utcnow()):
            # delete database
            os.remove(db_path)
    create_all(get_engine(db_path))
    return db_path


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
    return messages


def transcribe_audio(
    audio_file: str,
    project_id="braintext-394611",
) -> cloud_speech.RecognizeResponse:
    """Transcribe an audio file."""
    # Instantiates a client
    client = SpeechClient()

    # Reads a file as bytes
    with open(audio_file, "rb") as f:
        content = f.read()

    config = cloud_speech.RecognitionConfig(
        auto_decoding_config=cloud_speech.AutoDetectDecodingConfig(),
        language_codes=["en-US"],
        model="long",
    )

    request = cloud_speech.RecognizeRequest(
        recognizer=f"projects/{project_id}/locations/global/recognizers/_",
        config=config,
        content=content,
    )

    # Transcribes the audio into text
    response = client.recognize(request=request)

    transcript = ""
    for result in response.results:
        transcript += f"{result.alternatives[0].transcript}. "

    return transcript


def contains_greeting(text):
    # Convert the input text to lowercase to make the comparison case-insensitive
    text = text.lower()

    # Define a regular expression pattern to match different greetings
    greeting_pattern = r"\b(hello|hi|hey|good morning|good afternoon|good evening)\b"

    # Use the re.search() function to find the pattern in the text
    match = re.search(greeting_pattern, text)

    # If a match is found, return True; otherwise, return False
    return bool(match)


def contains_thanks(text):
    # Convert the input text to lowercase to make the comparison case-insensitive
    text = text.lower()

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


def split_and_respond(client, text: str, number: str, max_length=WHATSAPP_CHAR_LIMIT):
    """Recursively split and send response to user."""
    # If the text is shorter than the maximum length, process it directly
    if len(text) <= max_length:
        return send_whatspp_message(client=client, message=text, phone_no=number)

    # Otherwise, split the text into two parts and process each part recursively
    middle_index = len(text) // 2

    # Find the index of the nearest whitespace to the middle index
    while middle_index < len(text) and not text[middle_index].isspace():
        middle_index += 1

    first_half = text[:middle_index]
    second_half = text[middle_index:]

    # Process the first half recursively
    split_and_respond(client, first_half, number, max_length)

    # Process the second half recursively
    split_and_respond(client, second_half, number, max_length)

    # after splitting
    return "200"
