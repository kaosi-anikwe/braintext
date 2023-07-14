import os
import openai
import subprocess
import timeout_decorator
from boto3 import Session
from datetime import datetime
from contextlib import closing
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

LOG_DIR = os.getenv("CHATBOT_LOG")
TEMP_FOLDER = os.getenv("TEMP_FOLDER")
WHATSAPP_NUMBER = os.getenv("WHATSAPP_NUMBER")
WHATSAPP_TEMPLATE_NAMESPACE = os.getenv("WHATSAPP_TEMPLATE_NAMESPACE")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME")


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
    # check if response is too long
    if len(text) >= 3200:
        # too long even if halved
        text = "Your response is too long. Please rephrase your question."
        return respond_text(text)
    elif len(text) >= 1600:
        # split message into 2. Send first half and return second half
        sentences = text.split(". ")
        sentence_count = len(sentences)
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
def text_response(prompt: str, number: str) -> tuple:
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


## Vonage functions
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
