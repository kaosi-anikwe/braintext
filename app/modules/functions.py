# python imports
import os
import traceback
import subprocess
from datetime import datetime
from contextlib import closing

# installed imports
import openai
import tiktoken
import timeout_decorator
from boto3 import Session
from pprint import pprint
from sqlalchemy import desc
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError
from twilio.twiml.messaging_response import MessagingResponse

# local imports
from app.modules.messages import create_all, get_engine, Messages

load_dotenv()

LOG_DIR = os.getenv("CHATBOT_LOG")
TEMP_FOLDER = os.getenv("TEMP_FOLDER")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
WHATSAPP_TEMPLATE_NAMESPACE = os.getenv("WHATSAPP_TEMPLATE_NAMESPACE")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")
CONTEXT_LIMIT = int(os.getenv("CONTEXT_LIMIT"))
WHATSAPP_CHAR_LIMIT = int(os.getenv("WHATSAPP_CHAR_LIMIT"))


class TimeoutError(Exception):
    # custom timeout class to handle ChatGPT timeout
    pass


def send_otp_message(client, otp: int, name: str, phone_no: str) -> str:
    message = client.messages.create(
        body=f"Hi {name}! Here's your One Time Password to verify your number at Braintext. \n{otp} \nThe OTP will expire in 3 minutes.",
        from_="whatsapp:+15076094633",
        to=f"whatsapp:{phone_no}",
    )
    print(f"{message.sid} -- {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return message.sid


def send_whatspp_message(client, message: str, phone_no: str) -> str:
    message = client.messages.create(
        body=message,
        from_="whatsapp:+15076094633",
        to=f"whatsapp:{phone_no}",
    )
    print(f"{message.sid} -- {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return message.sid


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
            output = f"{TEMP_FOLDER}/{filename}"

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


def respond_text(text: str) -> str:
    response = MessagingResponse()
    message = response.message()
    message.body(text)

    return str(response)


def check_and_respond_text(client, text: str, number: str) -> str:
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


def respond_media(image_url: str) -> str:
    response = MessagingResponse()
    message = response.message()
    message.media(image_url)

    return str(response)


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


@timeout_decorator.timeout(13.5, use_signals=False, timeout_exception=TimeoutError)
def text_response(messages: list, number: str) -> tuple:
    """Get response from ChatGPT"""
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=messages,
        temperature=0.8,
        user=f"{str(number)}",
    )

    text = completion.choices[0].message.content
    tokens = int(completion.usage.total_tokens)
    role = completion.choices[0].message.role

    return text, tokens, role


def chat_reponse(client, name, number, incoming_msg, user, subscription=None):
    """Typical WhatsApp text response"""
    try:
        if subscription:
            if subscription.expired():
                subscription.update_account(user.id)
                text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                return respond_text(text)
        try:
            user_db_path = get_user_db(name=name, number=number)
            messages = load_messages(prompt=incoming_msg, db_path=user_db_path)
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
            # delte database
            os.remove(db_path)
    create_all(get_engine(db_path))
    return db_path


def load_messages(prompt: str, db_path: str):
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
    return messages


## Vonage functions ---------------------------------------------------
def vonage_text_response(prompt: str, number: str) -> tuple:
    completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=2000,
        temperature=0.7,
        user=f"{str(number)}",
    )

    text = completion.choices[0].text
    tokens = int(completion.usage.total_tokens)

    return text, tokens


def vonage_send_text(
    client,
    text: str,
    to: str,
):
    return client.messages.send_message(
        {
            "channel": "whatsapp",
            "message_type": "text",
            "to": to,
            "from": WHATSAPP_NUMBER,
            "text": text,
        }
    )


def vonage_send_audio(client, audio_url, to):
    return client.messages.send_message(
        {
            "channel": "whatsapp",
            "message_type": "audio",
            "to": to,
            "from": WHATSAPP_NUMBER,
            "audio": {
                "url": audio_url,
            },
        }
    )


def vonage_send_image(client, image_url, to):
    return client.messages.send_message(
        {
            "channel": "whatsapp",
            "message_type": "image",
            "to": to,
            "from": WHATSAPP_NUMBER,
            "image": {"url": image_url},
        }
    )


def vonage_send_otp(
    client,
    to_number: str,
    otp: str,
):
    return client.messages.send_message(
        {
            "channel": "whatsapp",
            "message_type": "template",
            "to": to_number,
            "from": WHATSAPP_NUMBER,
            "template": {
                "name": f"{WHATSAPP_TEMPLATE_NAMESPACE}:{WHATSAPP_TEMPLATE_NAME}",
                "parameters": [
                    otp,
                ],
            },
            "whatsapp": {"policy": "deterministic", "locale": "en-GB"},
        }
    )


# ChatGPT ----------------------------------
def num_tokens_from_messages(messages, model="gpt-4-0314"):
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
