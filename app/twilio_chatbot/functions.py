# python imports
from datetime import datetime

# installed imports
import openai
import timeout_decorator
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

# local imports
from ..modules.functions import *


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
            text, tokens, role = chatgpt_response(messages=messages, number=number)
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
