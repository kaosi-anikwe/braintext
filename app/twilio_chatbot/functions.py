# python imports
from datetime import datetime

# installed imports
import openai
import timeout_decorator
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse


load_dotenv()


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


def get_original_message(client: Client, sid: str) -> str:
    message = client.messages(sid).fetch()
    return message.body
