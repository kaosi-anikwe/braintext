# python imports
import re
import os
import requests
import traceback
from datetime import timedelta
from typing import Any, Dict, Union, Literal

# installed imports
from PIL import Image
from dotenv import load_dotenv
from flask import url_for, request

# local imports
from ..models import (
    User,
    AnonymousUser,
    UserSetting,
    MessageRequest,
)
from .. import logger
from config import Config
from ..modules.functions import *
from ..modules.calculate import *
from ..modules.functions2 import record_message
from ..modules.email_utility import send_registration_email
from ..modules.verification import generate_confirmation_token

load_dotenv()

USD2BT = int(os.getenv("USD2BT"))
FILES = Config.FILES
TEMP_FOLDER = Config.TEMP_FOLDER
TOKEN = os.getenv("META_VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
BASE_URL = "https://graph.facebook.com/v17.0"
URL = f"{BASE_URL}/{PHONE_NUMBER_ID}/messages"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}",
}


def _preprocess(data: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Preprocess incoming data from webhook.
    This function is meant to be called internally
    """
    return data["entry"][0]["changes"][0]["value"]


def is_message(data: Dict[Any, Any]) -> bool:
    """
    Determines if incoming payload is from a message.
    Returns `bool`
    """
    data = _preprocess(data)
    if "messages" in data:
        return True
    return False


def is_valid_email(email):
    # Regular expression pattern for a basic email address validation
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    # Use the re.match function to check if the string matches the pattern
    if re.match(pattern, email):
        return True
    else:
        return False


def is_reply(data: Dict[Any, Any]) -> bool:
    """
    Returns `True` if message is a reply, else returns `False`.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "context" in data["messages"][0]:
            return True
        return False
    return False


def is_interative_reply(data: Dict[Any, Any]) -> bool:
    """
    Returns `True` if message is a reply to an interactive message, else returns `False`.
    """
    is_reply = False
    data = _preprocess(data)
    if "interactive" in data["messages"][0]:
        is_reply = True
    return is_reply


def is_old(data):
    """
    Returns `True` if message is too old to reply to (more than 3 minutes old).
    """
    age = datetime.utcnow() - get_timestamp(data)
    if age < timedelta(minutes=0.25):
        return False
    logger.info(f"Old message is {age}")
    return True


def get_phone_id(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the WhatsApp phone number id of the recipeint.
    """
    data = _preprocess(data)
    if "metadata" in data:
        return data["metadata"]["phone_number_id"]


def get_number(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the mobile number of the sender.
    """
    data = _preprocess(data)
    if "contacts" in data:
        return data["contacts"][0]["wa_id"]


def get_name(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the name of the sender.
    """
    data = _preprocess(data)
    if "contacts" in data:
        return data["contacts"][0]["profile"]["name"]


def get_message(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the message from the payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        return data["messages"][0]["text"]["body"]


def get_timestamp(data: Dict[Any, Any]) -> datetime:
    """
    Extracts timestamp from message from message.
    """
    data = _preprocess(data)
    if "messages" in data:
        return datetime.fromtimestamp(float(data["messages"][0]["timestamp"]))


def get_message_id(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extacts the message id from the payload.
    Zubbee is writing code.
    Osheyyyy
    """
    data = _preprocess(data)
    if "messages" in data:
        return data["messages"][0]["id"]


def get_message_timestamp(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the timestamp of the message
    Zubbee again
    Peace out!
    """
    data = _preprocess(data)
    if "messages" in data:
        return data["messages"][0]["timestamp"]


def mark_as_read(message_id: str) -> bool:
    """
    Mark a message as read.
    """
    data = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }
    response = requests.post(
        f"{BASE_URL}/{PHONE_NUMBER_ID}/messages", headers=HEADERS, json=data
    )
    if response.status_code == 200:
        return True
    return False


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


def send_reaction(emoji, message_id, recipient) -> bool:
    """
    Sends a reaction message to a WhatsApp user's message.

    Args: `emoji`: Unicode value of emoji to be sent.
    """
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "reaction",
        "reaction": {"message_id": message_id, "emoji": emoji},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def send_template(template: str, recipient: str, components: Any) -> bool:
    """
    Sends a template message with it's components.
    """
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": "en"},
            "components": components,
        },
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def send_image(image_link: str, recipient: str, caption=None) -> bool:
    """
    Sends an image with its link.
    """
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "image",
        "image": {"link": image_link, "caption": caption},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def send_sticker(sticker_link: str, recipient: str) -> bool:
    """
    Sends a sticker to the user with its link.
    """
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "sticker",
        "sticker": {"link": sticker_link},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def send_audio(audio_link: str, recipient: str) -> bool:
    """
    Sends an audio message to the user with its link.
    """
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "audio",
        "audio": {"link": audio_link},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def send_video(video_link: str, recipient: str, caption=None) -> bool:
    """
    Sends a video to the user with its link.
    """
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "video",
        "video": {"link": video_link, "caption": caption},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def send_document(document_link: str, recipient: str, caption=None) -> bool:
    """
    Sends a document to the user with its link.
    """
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "document",
        "document": {"link": document_link, "caption": caption},
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        return True
    return False


def _create_interaction(
    interactive: Dict[Any, Any], type: Literal["button", "list"] = "button"
) -> Dict[Any, Any]:
    """
    Creates a button to be used to send interactive messages.
    This function is meant to be called internally.
    """
    data = {"type": type, "action": interactive.get("action")}
    if interactive.get("header"):
        data["header"] = {"type": "text", "text": interactive.get("header")}
    if interactive.get("body"):
        data["body"] = {"text": interactive.get("body")}
    if interactive.get("footer"):
        data["footer"] = {"text": interactive.get("footer")}
    return data


def send_interactive_message(
    interactive: Dict[Any, Any],
    recipient: str,
    interactive_type: Literal["button", "list", "cta_url"] = "button",
) -> Union[str, None]:
    """
    Sends an interactive message to the user.

    Args: `button`: button created with `_create_button`
    """
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "interactive",
        "interactive": _create_interaction(interactive, type=interactive_type),
    }
    response = requests.post(URL, headers=HEADERS, json=data)
    if response.status_code == 200:
        data = response.json()
        return str(data["messages"][0]["id"])
    return None


def get_media_url(media_id: str) -> Union[str, None]:
    """
    Retrieves the url of media from the media id
    """
    response = requests.get(f"{BASE_URL}/{media_id}", headers=HEADERS)
    if response.status_code == 200:
        return response.json()["url"]
    return None


def download_media(
    media_url: str, file_name: str, file_path: str = TEMP_FOLDER
) -> Union[str, None]:
    """
    Download media from media url and return its file path.
    """
    response = requests.get(media_url, headers=HEADERS, timeout=5)
    if response.status_code == 200:
        try:
            full_path = os.path.join(file_path, file_name)
            with open(full_path, "wb") as f:
                f.write(response.content)
            return full_path
        except:
            logger.error(traceback.format_exc())
            return None
    return None


def generate_interactive_button(
    body: str,
    button_texts: list[str],
    header: str = None,
    footer: str = "Learn through conversations, evolve with AI.",
):
    """
    Genereates the button to be used as a parameter to the `send_interactive_message` function.
    """
    data = {
        "action": {"buttons": []},
        "header": header,
        "body": body,
        "footer": footer,
    }
    for i, text in enumerate(button_texts):
        data["action"]["buttons"].append(
            {
                "type": "reply",
                "reply": {
                    "id": f"{header.lower().replace(' ', '_')}_{i}",
                    "title": text,
                },
            }
        )
    return data


def generate_list_message(
    body: str,
    header: str,
    button_text: str,
    sections: list,
    footer: str = "Learn through conversations, evolve with AI.",
):
    """
    Genereates the messsage list to be used as a parameter to the `send_interactive_message` function.
    """
    data = {
        "action": {"button": button_text, "sections": []},
        "header": header,
        "body": body,
        "footer": footer,
    }
    for section in sections:
        data["action"]["sections"].append(
            {
                "title": section.get("title"),
                "rows": [
                    {
                        "id": row.get("id"),
                        "title": row.get("title"),
                        "description": row.get("description"),
                    }
                    for row in section.get("rows")
                ],
            }
        )
    return data


def generate_cta_action(
    header: str,
    body: str,
    button_text: str,
    button_url: str,
    footer: str = "Learn through conversations, evolve with AI.",
):
    """Generate a CTA button to send to the user"""
    data = {
        "action": {
            "name": "cta_url",
            "parameters": {"display_text": button_text, "url": button_url},
        },
        "header": header,
        "body": body,
        "footer": footer,
    }
    return data


def get_interactive_response(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the response of the interactive message from the payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "interactive" in data["messages"][0]:
            return data["messages"][0]["interactive"]


def get_image(data: Dict[Any, Any]) -> Union[Dict[Any, Any], None]:
    """
    Extracts the image id from the message payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "image" in data["messages"][0]:
            return data["messages"][0]["image"]


def get_document(data: Dict[Any, Any]) -> Union[Dict[Any, Any], None]:
    """
    Extracts the document id from the message payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "document" in data["messages"][0]:
            return data["messages"][0]["document"]


def get_audio_id(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Extracts the audio id from the message payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "audio" in data["messages"][0]:
            return data["messages"][0]["audio"]["id"]


def get_video(data: Dict[Any, Any]) -> Union[Dict[Any, Any], None]:
    """
    Extracts the video id from the message payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "video" in data["messages"][0]:
            return data["messages"][0]["video"]


def get_message_type(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Gets the message type from the message payload.
    """
    data = _preprocess(data)
    if "messages" in data:
        return data["messages"][0]["type"]


def get_message_status(data: Dict[Any, Any]) -> Union[str, None]:
    """
    Gets status of message from payload.
    """
    data = _preprocess(data)
    if "statuses" in data:
        return data["statuses"][0]["status"]


def send_otp_message(otp: int, number: str):
    components = [
        {
            "type": "body",
            "parameters": [
                {
                    "type": "text",
                    "text": str(otp),
                }
            ],
        },
        {
            "type": "button",
            "sub_type": "url",
            "index": "0",
            "parameters": [{"type": "text", "text": str(otp)}],
        },
    ]
    try:
        success = send_template(
            template="phone_number_verification",
            recipient=number,
            components=components,
        )
        return success
    except:
        logger.error(traceback.format_exc())
        raise Exception


def meta_split_and_respond(
    text: str,
    number: str,
    prev_mssg_id: str,
    max_length=WHATSAPP_CHAR_LIMIT,
    reply=False,
):
    """
    Recursively split and send response to user.
    """
    # If the text is shorter than the maximum length, process it directly
    if len(text) <= max_length:
        return (
            send_text(text, number)
            if not reply
            else reply_to_message(prev_mssg_id, number, text)
        )

    # Otherwise, split the text into two parts and process each part recursively
    middle_index = len(text) // 2

    # Find the index of the nearest whitespace to the middle index
    while middle_index < len(text) and not text[middle_index].isspace():
        middle_index += 1

    first_half = text[:middle_index]
    second_half = text[middle_index:]

    # Process the first half recursively
    meta_split_and_respond(first_half, number, prev_mssg_id)

    # Process the second half recursively
    meta_split_and_respond(second_half, number, prev_mssg_id)


def image_recognition(
    user: User,
    data: Dict[Any, Any],
    prompt: str,
    message_list: list,
    message_request: MessageRequest,
):
    """Perform image recognition with OpenAI's GPT-4V"""
    name = get_name(data)
    number = f"+{get_number(data)}"
    try:
        message_id = get_message_id(data)
        isreply = is_reply(data)
        user_db_path = get_user_db(name=name, number=number)
        messages = load_messages(
            user=user,
            db_path=user_db_path,
            prompt=prompt,
            message_list=message_list,
        )
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=messages,
            temperature=1,
            max_tokens=4000,
        )
        text = response.choices[0].message.content
        tokens = int(response.usage.prompt_tokens), int(
            response.usage.completion_tokens
        )
        logger.info(f"GPT 4 VISION TOKENS: {tokens}")
        role = response.choices[0].message.role
        # update request records
        message_request.gpt_4_input = tokens[0]
        message_request.gpt_4_output = tokens[1]
        message_request.update()
        # charge user
        cost = gpt_4_vision_cost({"input": tokens[0], "output": tokens[1]})
        bt_cost = cost * USD2BT
        debit_user(
            user=user,
            name=name,
            bt_cost=bt_cost,
            message_request=message_request,
            reason="GPT4-Vision",
        )
        # log response
        log_response(
            name=name,
            number=number,
            message=prompt,
            tokens=tokens,
        )

        # record ChatGPT response
        new_message = {"role": role, "content": text}
        new_message = Messages(new_message, user_db_path)
        new_message.insert()

        if len(text) < WHATSAPP_CHAR_LIMIT:
            return (
                send_text(text, number)
                if not isreply
                else reply_to_message(message_id, number, text)
            )
        return (
            meta_split_and_respond(text, number, message_id)
            if not isreply
            else meta_split_and_respond(text, number, message_id, reply=True)
        )
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        record_message(name=name, number=number, message=text)
        return reply_to_message(message_id, number, text)


def meta_chat_response(
    data: Dict[Any, Any],
    user: User,
    message_request: MessageRequest,
    message: str = None,
    anonymous: bool = None,
):
    """
    Typical WhatsApp text response with Meta functions.
    """
    name = get_name(data)
    number = f"+{get_number(data)}"
    user_db_path = get_user_db(name=name, number=number)
    if not message:
        message = get_message(data)
    messages = load_messages(
        user=user,
        prompt=message,
        db_path=user_db_path,
    )
    message_id = get_message_id(data)
    isreply = is_reply(data)
    greeting = contains_greeting(message)
    thanks = contains_thanks(message)
    try:
        # check balance
        num_tokens = num_tokens_from_messages(messages)
        logger.info(f"INPUT TOKENS: {num_tokens}")
        cost = gpt_3_5_cost({"input": num_tokens, "output": 0})
        bt_cost = cost * USD2BT
        if bt_cost > user.balance:
            text = f"Insufficent balance. Cost is {round(bt_cost, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
            logger.info(
                f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
            )
            record_message(name=name, number=number, message=text)
            return send_text(text, number)
        # react to message
        (
            send_reaction(chr(128075), message_id, number) if greeting else None
        )  # react waving hand
        (
            send_reaction(chr(128153), message_id, number) if thanks else None
        )  # react blue love emoji

        try:
            response = chatgpt_response(
                data=data,
                user=user,
                messages=messages,
                message=message,
                number=number,
                message_id=message_id,
                message_request=message_request,
            )
            logger.info(f"CHATGPT RESPONSE: {response}")
            if not response:  # function called from ChatGPT response
                return
            text, tokens, role = response[0], response[1], response[2]
            logger.info(f"CHATGPT RESPONSE TOKENS: {tokens[0], tokens[1]}")
            # update request records
            message_request.gpt_3_input = tokens[0]
            message_request.gpt_3_output = tokens[1]
            message_request.update()
            # charge user
            cost = gpt_3_5_cost({"input": tokens[0], "output": tokens[1]})
            bt_cost = cost * USD2BT
            debit_user(
                user=user,
                name=name,
                bt_cost=bt_cost,
                message_request=message_request,
                reason="ChatGPT",
            )
        except:
            logger.error(traceback.format_exc())
            text = (
                "Sorry, I can't respond to that at the moment. Please try again later."
            )
            record_message(name=name, number=number, message=text)
            return reply_to_message(message_id, number, text)

        log_response(
            name=name,
            number=number,
            message=message,
            tokens=tokens,
        )
        # record ChatGPT response
        new_message = {"role": role, "content": text}
        new_message = Messages(new_message, user_db_path)
        new_message.insert()

        if text:
            if len(text) < WHATSAPP_CHAR_LIMIT:
                return (
                    send_text(text, number)
                    if not isreply
                    else reply_to_message(message_id, number, text)
                )
            return (
                meta_split_and_respond(text, number, message_id)
                if not isreply
                else meta_split_and_respond(text, number, message_id, reply=True)
            )
        else:
            text = "I was unable to retrieve the requested information. Please try again later."
            record_message(name=name, number=number, message=text)
            return reply_to_message(message_id, number, text)
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        record_message(name=name, number=number, message=text)
        return reply_to_message(message_id, number, text)


def meta_audio_response(
    user: User,
    data: Dict[Any, Any],
    message_request: MessageRequest,
    anonymous: bool = False,
):
    """WhatsApp audio response with Meta functions."""
    name = get_name(data)
    number = f"+{get_number(data)}"
    message_id = get_message_id(data)
    message = "`audio recording`"

    try:
        audio_url = get_media_url(get_audio_id(data))
        audio_file = download_media(
            audio_url,
            f"{datetime.utcnow().strftime('%M%S%f')}",
        )
        duration = get_audio_duration(audio_file)
        cost = whisper_cost(duration)
        bt_cost = cost * USD2BT
        logger.info(f"AUDIO DURATION: {duration}")
        logger.info(f"WHISPER COST IN USD: {cost}")
        logger.info(f"WHISPER COST IN BT: {bt_cost}")
        if bt_cost > user.balance:
            text = f"Insufficent balance. Cost is {round(bt_cost, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
            logger.info(
                f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
            )
            record_message(name=name, number=number, message=message, assistant=False)
            record_message(name=name, number=number, message=text)
            return send_text(text, number)
        try:
            transcript = openai_transcribe_audio(audio_file)
            message = transcript
            greeting = contains_greeting(transcript)
            thanks = contains_thanks(transcript)
            # update request records
            message_request.whisper = duration
            message_request.update()
            # charge user
            debit_user(
                user=user,
                name=name,
                bt_cost=bt_cost,
                message_request=message_request,
                reason="ChatGPT",
            )
        except:
            logger.error(traceback.format_exc())
            text = "Error transcribing audio. Please try again later."
            record_message(name=name, number=number, message=message, assistant=False)
            record_message(name=name, number=number, message=text)
            return send_text(text, number)
        finally:
            # delete audio file
            delete_file(audio_file)
        # reactions
        (
            send_reaction(chr(128075), message_id, number) if greeting else None
        )  # react waving hand
        (
            send_reaction(chr(128153), message_id, number) if thanks else None
        )  # react blue love emoji

        try:
            user_db_path = get_user_db(name, number)
            messages = load_messages(
                user=user,
                prompt=transcript,
                db_path=user_db_path,
            )
            num_tokens = num_tokens_from_messages(messages)
            logger.info(f"INPUT TOKENS: {num_tokens}")
            cost = gpt_3_5_cost({"input": num_tokens, "output": 0})
            bt_cost = cost * USD2BT
            if bt_cost > user.balance:
                text = f"Insufficent balance. Cost is {round(bt_cost, 2)} BT.\nCurrent balance is {round(user.balance, 2)} BT"
                logger.info(
                    f"INSUFFICIENT BALANCE - user: {user.phone_no}. BALANCE: {user.balance}"
                )
                record_message(
                    name=name, number=number, message=message, assistant=False
                )
                record_message(name=name, number=number, message=text)
                return send_text(text, number)
            response = chatgpt_response(
                data=data,
                user=user,
                messages=messages,
                message=transcript,
                number=number,
                message_id=message_id,
                message_request=message_request,
            )
            if not response:  # function called from ChatGPT response
                return
            text, tokens, role = response[0], response[1], response[2]
            # update request records
            message_request.gpt_3_input = tokens[0]
            message_request.gpt_3_output = tokens[1]
            message_request.update()
            # charge user
            cost = gpt_3_5_cost({"input": tokens[0], "output": tokens[1]})
            bt_cost = cost * USD2BT
            debit_user(
                user=user,
                name=name,
                bt_cost=bt_cost,
                message_request=message_request,
                reason="ChatGPT",
            )
        except:
            logger.error(traceback.format_exc())
            text = (
                "Sorry I can't respond to that at the moment. Please try again later."
            )
            record_message(name=name, number=number, message=text)
            return send_text(text, number)

        user_settings = user.user_settings() if not anonymous else None
        if user_settings:
            if not user_settings.audio_responses:
                if len(text) < WHATSAPP_CHAR_LIMIT:
                    return send_text(text, number)
                else:
                    return meta_split_and_respond(
                        text,
                        number,
                        get_message_id(data),
                    )
        return speech_synthesis(
            data=data,
            text=text,
            tokens=tokens,
            message=transcript,
            message_request=message_request,
        )

    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        record_message(name=name, number=number, message=text)
        return send_text(text, number)


def meta_image_response(
    user: User,
    data: Dict[Any, Any],
    message_request: MessageRequest,
    anonymous: bool = False,
):
    """WhatsApp image response wtih Meta functions."""
    name = get_name(data)
    number = f"+{get_number(data)}"
    run = False
    if isinstance(user, User):
        if user.user_settings().image_recognition:
            run = True
    else:
        run = True

    if run:
        try:
            image = get_image(data)
            image_url = get_media_url(image["id"])
            image_path = download_media(
                image_url,
                f"{datetime.utcnow().strftime('%M%S%f')}.jpg",
            )
            # convert to png
            image_content = Image.open(image_path)
            image_content = image_content.convert(
                "RGBA"
            )  # If the image has an alpha channel (transparency)
            image_content.save(image_path, format="PNG")
            prompt = image.get("caption", "")
            base64_image = encode_image(image_path)
            message_list = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]
            return image_recognition(
                user=user,
                data=data,
                prompt=prompt,
                message_list=message_list,
                message_request=message_request,
            )
        except:
            logger.error(traceback.format_exc())
            text = "Something went wrong. Please try again later."
            record_message(name=name, number=number, message=text)
            return send_text(text, number)
        finally:
            delete_file(image_path)


def meta_interactive_response(
    data: Dict[Any, Any],
    **kwargs,
):
    """WhatsApp interactive message response."""
    response = get_interactive_response(data)
    logger.info(response)
    number = f"+{get_number(data)}"
    user: User
    user = User.query.filter(User.phone_no == number).one_or_none()
    if not user:
        text = "Access to this feature requires an account. Please create an account to proceed."
        return send_text(text, number)
    user_settings = user.user_settings()
    type = response.get("type", "button_reply")
    if type == "button_reply":
        reply_id = response[type]["id"]
        if "settings" in str(response[type]["title"]).lower():
            with open(os.path.join(FILES, "settings.json")) as settings_file:
                settings = json.load(settings_file)

            if "user" in str(response[type]["title"]).lower():
                message_list = generate_list_message(
                    header="Settings",
                    body="Here are the available user settings",
                    button_text="User settings",
                    sections=settings["userSettings"],
                )
                return send_interactive_message(message_list, number, "list")
            elif "chatbot" in str(response[type]["title"]).lower():
                message_list = generate_list_message(
                    header="Settings",
                    body="Here are the available chatbot settings",
                    button_text="Chatbot settings",
                    sections=settings["chatbotSettings"],
                )
                return send_interactive_message(message_list, number, "list")
        # RECHARGE ACCOUNT
        if "recharge_now" in reply_id:
            text = response["button_reply"]["title"]
            record_message(get_name(data), number, text, assistant=False)
            if "Yes" in text:
                from ..payment.routes import BANK_CODES

                header = "Choose Bank"
                body = f"Choose your preferred bank from the options. To use a bank not listed here, please visit our website to proceed.\n{request.host_url}recharge"
                choices = [
                    {
                        "title": "Accepted Banks",
                        "rows": [
                            {
                                "id": f"bank_{code}",
                                "title": bank,
                                "description": f"Recharge with {bank}.",
                            }
                            for bank, code in list(BANK_CODES.items())[:10]
                        ],
                    }
                ]
                message_list = generate_list_message(
                    header=header,
                    body=body,
                    button_text="Select Bank",
                    sections=choices,
                )
                record_message(get_name(data), number, body)
                return send_interactive_message(message_list, number, "list")
            else:
                text = "That's alright."
                record_message(get_name(data), number, text)
                return send_text(text, number)
        # CHATBOT SETTINGS
        if "response_type" in reply_id:
            # handle response type
            response_type = bool(int(reply_id.removeprefix("response_type_")))
            response_type = "simplified" if not response_type else "elaborated"
            logger.info(f"NEW RESPONSE TYPE: {response_type}")
            user_settings.response_type = response_type
            user_settings.update()
            text = f"Response settings updated successfully!"
            return send_text(text, number)
        if "image_generation" in reply_id:
            # handle image gen toggle
            image_gen = bool(int(reply_id.removeprefix("image_generation_")))
            logger.info(f"NEW IMAGE TOGGLE: {image_gen}")
            user_settings.image_generation = image_gen
            user_settings.update()
            text = f"Image generation settings updated successfully!"
            return send_text(text, number)
        if "online_search" in reply_id:
            # handle image gen toggle
            online_search = bool(int(reply_id.removeprefix("online_search_")))
            logger.info(f"NEW ONLINE TOGGLE: {online_search}")
            user_settings.online_search = online_search
            user_settings.update()
            text = f"Online search settings updated successfully!"
            return send_text(text, number)
        if "media_search" in reply_id:
            # handle image gen toggle
            media_search = bool(int(reply_id.removeprefix("media_search_")))
            logger.info(f"NEW MEDIA TOGGLE: {media_search}")
            user_settings.media_search = media_search
            user_settings.update()
            text = f"Media search settings updated successfully!"
            return send_text(text, number)
        if "audio_responses" in reply_id:
            # handle image gen toggle
            audio_responses = bool(int(reply_id.removeprefix("audio_responses_")))
            logger.info(f"NEW AUDIO TOGGLE: {audio_responses}")
            user_settings.audio_responses = audio_responses
            user_settings.update()
            text = f"Audio response settings updated successfully!"
            return send_text(text, number)
        if "image_recognition" in reply_id:
            # handle image gen toggle
            image_recognition = bool(int(reply_id.removeprefix("image_recognition_")))
            logger.info(f"NEW IMG RECOG TOGGLE: {image_recognition}")
            user_settings.image_recognition = image_recognition
            user_settings.update()
            text = f"Image recognition settings updated successfully!"
            return send_text(text, number)
        if "accept_links" in reply_id:
            # handle web scrapping toggle
            web_scrapping = bool(int(reply_id.removeprefix("accept_links_")))
            logger.info(f"NEW WEB SCRAPE TOGGLE: {web_scrapping}")
            user_settings.web_scrapping = web_scrapping
            user_settings.update()
            text = f"Chat settings updated successfully!"
            return send_text(text, number)
        if "image_model" in reply_id:
            # change image model settings
            model = int(reply_id.removeprefix("image_model_"))
            model = "dalle2" if not model else "dalle3"
            logger.info(f"NEW IMG MODEL: {model}")
            user_settings.image_generation_model = model
            user_settings.update()
            text = f"Image model settings updated successfully!"
            return send_text(text, number)
        if "image_style" in reply_id:
            # change image style settings
            style = int(reply_id.removeprefix("image_style_"))
            style = "vivid" if not style else "natural"
            logger.info(f"NEW IMG STYLE: {style}")
            user_settings.image_generation_style = style
            user_settings.update()
            text = f"Image style settings updated successfully!"
            return send_text(text, number)
        if "image_quality" in reply_id:
            # change image quality settings
            quality = int(reply_id.removeprefix("image_quality_"))
            quality = "standard" if not quality else "hd"
            logger.info(f"NEW IMG QUALITY: {quality}")
            user_settings.image_generation_quality = quality
            user_settings.update()
            text = f"Image quality settings updated successfully!"
            return send_text(text, number)
        if "image_size" in reply_id:
            # change image size settings
            if user_settings.image_generation_model == "dalle2":
                sizes = ["256x256", "512x512", "1024x1024"]
            else:
                sizes = ["1024x1024", "1024x1792", "1792x1024"]
            size = int(reply_id.removeprefix("image_size_"))
            size = sizes[size]
            logger.info(f"NEW IMG SIZE: {size}")
            user_settings.image_generation_size = size
            user_settings.update()
            text = f"Image size settings updated successfully!"
            return send_text(text, number)
        # USER SETTINGS
        if "email_updates" in reply_id:
            # handle email updates settings
            update = bool(int(reply_id.removeprefix("email_updates_")))
            logger.info(f"NEW EMAIL SETTING: {update}")
            user_settings.email_updates = update
            user_settings.update()
            text = f"Email update settings updated successfully!"
            return send_text(text, number)

    if type == "list_reply":
        reply_id = response[type]["id"]
        # RECHARGE ACCOUNT
        if "bank_" in reply_id:
            from ..payment.routes import BANK_CODES

            user_code = reply_id.removeprefix("bank_")
            user_bank = ""
            for bank_name, bank_code in BANK_CODES.items():
                if bank_code == user_code:
                    user_bank = bank_name
            if not user_bank:
                raise Exception(f"Bank with code: '{user_code}' not found")

            header = "Select amount"
            body = f"Select amount to recharge with {user_bank}"
            choices = [
                {
                    "title": "Amount to Recharge",
                    "rows": [
                        {
                            "id": f"bt_{user_code}_{i}",
                            "title": f"₦{i}",
                            "description": "",
                        }
                        for i in [100, 200, 500, 1000, 2000, 5000]
                    ],
                }
            ]
            message_list = generate_list_message(
                header=header,
                body=body,
                button_text="Choose Amount",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        if "bt_" in reply_id:
            from ..payment.routes import BANK_CODES
            from ..payment.functions import recharge_account

            user_code = reply_id.split("_")[1]
            user_bank = ""
            for bank_name, bank_code in BANK_CODES.items():
                if bank_code == user_code:
                    user_bank = bank_name
            if not user_bank:
                raise Exception(f"Bank with code: '{user_code}' not found")
            amount = reply_id.split("_")[2]
            message = response[type]["title"]
            return recharge_account(
                data=data,
                tokens=0,
                message=message,
                amount=int(amount),
                currency="NGN",
                bank_name=user_bank,
            )
        # CHATBOT SETTINGS
        # Handle Context and Responses settings
        if reply_id == "context_and_responses":
            logger.info(f"REPLY ID: {reply_id}")
            choices = [
                {
                    "title": "Context and Responses",
                    "rows": [
                        {
                            "id": "context_messages",
                            "title": "Context length",
                            "description": "Set length of message context.",
                        },
                        {
                            "id": "max_response_length",
                            "title": "Max Length of Response",
                            "description": "Define the maximum length allowed for chatbot responses.",
                        },
                        {
                            "id": "response_type",
                            "title": "Response Type",
                            "description": "Choose the manner the chatbot response to prompts.",
                        },
                    ],
                }
            ]
            message_list = generate_list_message(
                header="Context and Responses",
                body=f"Customize your context settings and response type.",
                button_text="Choose setting",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        # Handle response type
        if reply_id == "response_type":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Response Type",
                body=f"Set the nature of the responses to prompts. *Elaborated* tends to use more prompts which may increase cost.\nCurrent setting is *{user_settings.response_type}*.",
                button_texts=["Simplified", "Elaborated"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle Context length
        if reply_id == "context_messages":
            logger.info(f"REPLY ID: {reply_id}")
            choices = [
                {
                    "title": "Context Length",
                    "rows": [
                        {
                            "id": f"context_{i}",
                            "title": f"{i}",
                            "description": f"Send back {i} pairs of messages.",
                        }
                        for i in range(0, 12, 2)
                    ],
                }
            ]
            message_list = generate_list_message(
                header="Context Length",
                body=f"The context length defines how many of your previous messages will be sent back in order to keep the conversation context.\n*Note that this increases cost.*\nCurrent setting is {user_settings.context_messages}",
                button_text="Choose length",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        elif "context_" in reply_id:
            # change context settings
            context = int(reply_id.removeprefix("context_"))
            logger.info(f"NEW CONTEXT: {context}")
            user_settings.context_messages = context
            user_settings.update()
            text = f"Context settings updated successfully!"
            return send_text(text, number)
        # Handle response length
        if reply_id == "max_response_length":
            logger.info(f"REPLY  ID: {reply_id}")
            nums = [20, 50, 100, 200, 500, 1000]
            choices = [
                {
                    "title": "Max Response Size",
                    "rows": [
                        {
                            "id": f"response_len_{i}",
                            "title": f"{i}",
                            "description": f"Response will not be longer than {i} tokens.",
                        }
                        for i in nums
                    ],
                }
            ]
            choices[0]["rows"].append(
                {
                    "id": "response_len_unltd",
                    "title": "Unlimited",
                    "description": "No upper bound for response size.",
                }
            )
            message_list = generate_list_message(
                header="Max Response Size",
                body=f"This number defines the maximum number of words that can be in a response. Reducing this helps save cost.\n*Note that a low number may cause issues in response.*\nCurrent setting is {'*Unlimited*' if not user_settings.max_response_length else user_settings.max_response_length}",
                button_text="Choose size",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        elif "response_len" in reply_id:
            # change max response length
            try:
                max_response = int(reply_id.removeprefix("response_len_"))
            except ValueError:
                max_response = None
            logger.info(f"NEW MAX RESPONSE: {max_response}")
            user_settings.max_response_length = max_response
            user_settings.update()
            text = f"Max response length updated successfully!"
            return send_text(text, number)
        # Handle image gen toggle
        if reply_id == "image_generation":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Image Generation",
                body=f"Toggle the ability of the chatbot to generate images at will. This setting is currently {'*enabled*.' if user_settings.image_generation else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle online search toggle
        if reply_id == "online_search":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Online Search",
                body=f"Toggle the ability of the chatbot to perform online searches to better answer questions. This setting is currently {'*enabled*.' if user_settings.online_search else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle media search toggle
        if reply_id == "media_search":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Media Search",
                body=f"Toggle the ability of the chatbot to retrieve images and documents from the internet. This setting is currently {'*enabled*.' if user_settings.media_search else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle audio response toggle
        if reply_id == "audio_responses":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Audio Responses",
                body=f"Toggle the ability of the chatbot to respond with audio at will. This setting is currently {'*enabled*.' if user_settings.audio_responses else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle image recognition toggle
        if reply_id == "image_recognition":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Image Recognition",
                body=f"Toggle the ability of the chatbot to recognize and respond to images. This setting is currently {'*enabled*.' if user_settings.image_recognition else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle web scrapping toggle
        if reply_id == "accept_links":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Accept Links",
                body=f"Toggle the ability of the chatbot to be prompted with links.\n*Note that some websites cannot be scrapped and will cause an error.*\nThis setting is currently {'*enabled*.' if user_settings.web_scrapping else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        # Handle audio voice change
        if reply_id == "audio_voice":
            logger.info(f"REPLY ID: {reply_id}")
            with open(os.path.join(FILES, "settings.json")) as settings_file:
                settings = json.load(settings_file)
            voices = settings["chatbotSettings"][2]["rows"][0]["voices"]
            choices = [
                {
                    "title": "Audio Voice",
                    "rows": [
                        {
                            "id": f"audio_voice_{voice['name']}",
                            "title": voice["name"],
                            "description": (
                                "Male voice"
                                if voice["gender"] == "male"
                                else "Female voice"
                            ),
                        }
                        for voice in voices
                    ],
                }
            ]
            message_list = generate_list_message(
                header="Audio Voice",
                body=f"Choose your preferred audio voice from the provided list.\nThe current voice is {user_settings.audio_voice}",
                button_text="Choose voice",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        elif "audio_voice_" in reply_id:
            # change audio voice
            voice = reply_id.removeprefix("audio_voice_")
            logger.info(f"NEW AUDIO VOICE: {voice}")
            user_settings.audio_voice = voice
            user_settings.update()
            text = f"Audio voice settings updated successfully!"
            return send_text(text, number)
        # Handle image generation settings
        if reply_id == "image_gen_settings":
            logger.info(f"REPLY ID: {reply_id}")
            settings = ["Image Model", "Image Style", "Image Quality", "Image Size"]
            choices = [
                {
                    "title": "Image Settings",
                    "rows": [
                        {
                            "id": f"img_{setting}",
                            "title": setting,
                            "description": f"Change {setting}",
                        }
                        for setting in settings
                    ],
                }
            ]
            message_list = generate_list_message(
                header="Image Settings",
                body=f"Modify your image generation settings.",
                button_text="Choose setting",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        elif "img_" in reply_id:
            # change image gen settings
            setting = reply_id.removeprefix("img_")
            if "model" in reply_id.lower():
                logger.info(f"REPLY ID: {reply_id}")
                button = generate_interactive_button(
                    header=f"Image Model",
                    body=f"Choose your preferred image generation model. Remember to adjust size settings too as there may be incompatibility issues with some sizes.\nCurrent setting is {'*Dalle-2*.' if '2' in user_settings.image_generation_model else '*Dalle-3*.'}",
                    button_texts=["Dalle-2", "Dalle-3"],
                )
                return send_interactive_message(interactive=button, recipient=number)
            elif "style" in reply_id.lower():
                logger.info(f"REPLY ID: {reply_id}")
                if user_settings.image_generation_model == "dalle2":
                    text = f"This setting is only available if the image generation model is Dalle-3."
                    return send_text(text, number)
                button = generate_interactive_button(
                    header=f"Image Style",
                    body=f"Choose your preferred image generation style. Current setting is *{user_settings.image_generation_style}*",
                    button_texts=["Vivid", "Natural"],
                )
                return send_interactive_message(interactive=button, recipient=number)
            elif "quality" in reply_id.lower():
                logger.info(f"REPLY ID: {reply_id}")
                if user_settings.image_generation_model == "dalle2":
                    text = f"This setting is only available if the image generation model is Dalle-3."
                    return send_text(text, number)
                button = generate_interactive_button(
                    header=f"Image Quality",
                    body=f"Choose your preferred image generation style\n*Note that HD has a higher cost.*\nCurrent setting is *{user_settings.image_generation_quality}*",
                    button_texts=["Standard", "HD"],
                )
                return send_interactive_message(interactive=button, recipient=number)
            elif "size" in reply_id.lower():
                if user_settings.image_generation_model == "dalle2":
                    button_texts = ["256x256", "512x512", "1024x1024"]
                else:
                    button_texts = ["1024x1024", "1024x1792", "1792x1024"]
                button = generate_interactive_button(
                    header=f"Image Size",
                    body=f"Choose your preferred image generation style. Current setting is *{user_settings.image_generation_size}*",
                    button_texts=button_texts,
                )
                return send_interactive_message(interactive=button, recipient=number)

        # USER SETTINGS
        # Handle warn low balance
        if reply_id == "warn_low_balance":
            logger.info(f"REPLY ID: {reply_id}")
            choices = [
                {
                    "title": "Warn on Low Balance",
                    "rows": [
                        {
                            "id": f"warn_{i}",
                            "title": f"{i} BT",
                            "description": f"Warn when balance is below {i} BT.",
                        }
                        for i in [0.2, 0.5, 1, 2, 5]
                    ],
                }
            ]
            message_list = generate_list_message(
                header="Warn on Low Balance",
                body=f"Get notified when balance is below this threshold.\nCurrent setting is {user_settings.warn_low_balance}",
                button_text="Set threshold",
                sections=choices,
            )
            return send_interactive_message(message_list, number, "list")
        elif "warn_" in reply_id:
            # change warn setting
            threshold = float(reply_id.removeprefix("warn_"))
            logger.info(f"NEW WARN: {threshold}")
            user_settings.warn_low_balance = threshold
            user_settings.update()
            text = f"Warn threshold settings updated successfully!"
            return send_text(text, number)
        # Handle email updates
        if reply_id == "email_updates":
            logger.info(f"REPLY ID: {reply_id}")
            button = generate_interactive_button(
                header=f"Email Updates",
                body=f"Receive email updates about new features and services and other important information. This setting is currently {'*enabled*.' if user_settings.email_updates else '*disabled*.'}",
                button_texts=["Disable", "Enable"],
            )
            return send_interactive_message(interactive=button, recipient=number)
        if "change" in reply_id:
            cta_action = generate_cta_action(
                header="User Settings",
                body="Navigate to your profile to complete this action.",
                button_text="Go to Profile",
                button_url=f"{request.host_url}profile?settings=True",
            )
            return send_interactive_message(cta_action, number, "cta_url")


def whatsapp_signup(
    data: Dict[Any, Any], user: AnonymousUser, interactive_reply: bool = False
):
    message_id = get_message_id(data)
    number = f"+{get_number(data)}"

    try:
        if interactive_reply:
            response = get_interactive_response(data)
            response_id = response["button_reply"][
                "id"
            ]  # to determind what what was replied to
            text = response["button_reply"]["title"]  # actual response

            if "register_now" in response_id:
                if "Yes" in text:
                    body = "How would you like to register?"
                    header = "Register to continue"
                    button_texts = ["Our website", "Continue here"]
                    button = generate_interactive_button(
                        body=body, header=header, button_texts=button_texts
                    )
                    send_interactive_message(interactive=button, recipient=number)
                elif "Maybe later" in text:
                    message = "That's alright."
                    send_text(message, number)
            elif "register_to_continue" in response_id:
                if "Our website" in text:
                    message = f"Follow this link to continue the registration process. {request.host_url}register"
                    send_text(message, number)
                elif "Continue here" in text:
                    user.signup_stage = "firstname_prompted"
                    user.update()
                    message = "Okay, let's get started. What's your first name?"
                    send_text(message, number)
            elif "confirm_name" in response_id:
                if "No" in text:
                    user.signup_stage = "firstname_prompted"
                    user.update()
                    message = "What is your first name?"
                    send_text(message, number)
                elif "Yes" in text:
                    user.signup_stage = "email_prompted"
                    user.update()
                    message = (
                        f"Alright {user.display_name()}, what is your email address?"
                    )
                    send_text(message, number)
        else:
            if user.signup_stage == "firstname_prompted":
                first_name = get_message(data).strip()
                user.first_name = first_name
                user.signup_stage = "lastname_prompted"
                user.update()
                message = f"Okay {user.first_name}, what is your last name?"
                send_text(message, number)
            elif user.signup_stage == "lastname_prompted":
                last_name = get_message(data).strip()
                user.last_name = last_name
                user.signup_stage = "confirm_name"
                user.update()
                # confirm name
                header = "Confirm name"
                body = f"Your name is registered as {user.display_name()}. Is that correct?"
                button_texts = ["Yes", "No"]
                button = generate_interactive_button(
                    body=body, header=header, button_texts=button_texts
                )
                send_interactive_message(interactive=button, recipient=number)
            elif user.signup_stage == "email_prompted":
                email = get_message(data).strip()
                if not is_valid_email(email):
                    message = "Please enter a valid email address."
                    send_text(message, number)
                else:
                    check = User.query.filter(User.email == email).first()
                    if check:  # email already used
                        message = "An account already exists with this email. Please use a different email address to continue."
                        send_text(message, number)
                    else:
                        user.email = email
                        user.signup_stage = "completed"
                        user.update()
                        # setup account
                        password = number
                        new_user = User(
                            first_name=user.first_name,
                            last_name=user.last_name,
                            email=user.email,
                            password=password,
                            timezone_offset=0,
                        )
                        new_user.uid = user.uid
                        new_user.phone_no = number
                        new_user.phone_verified = True
                        new_user.from_anonymous = True
                        new_user.balance = user.balance
                        new_user.insert()
                        # create user setting instance
                        user_settings = UserSetting(new_user.id)
                        user_settings.insert()

                        send_registration_email(new_user)
                        message = f"New WhatsAppp sign up from {user.display_name()}.\nNumber: {user.phone_no}"
                        send_text(message=message, recipient="+2349016456964")

                        token = generate_confirmation_token(new_user.email)
                        change_url = url_for(
                            "auth.change_password",
                            token=token,
                            _external=True,
                            _scheme="https",
                        )
                        message = f"Awesome! You're all set up.\nCheck your inbox for a verification link.\nLogin to edit your profile or change settings. {request.host_url}profile?settings=True. Settings can also be changed from here.\n*Your password is the number you're texting with in the international format.*\nFollow the link below to change your password.\nThank you for choosing BrainText 💙"
                        cta_action = generate_cta_action(
                            header="Account Created!",
                            body=message,
                            button_text="Change password",
                            button_url=change_url,
                        )
                        send_interactive_message(cta_action, number, "cta_url")
                        # send welcome audio
                        media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename=welcome.ogg"
                        send_audio(media_url, number)
                        # send account settings
                        body = f"The user settings interface provides you with the ability to manage both your account and chatbot settings in one place. You can access and update your personal information, notification preferences, chatbot interactions, and more. With this interface, you can customize your experience to best suit your needs and preferences."
                        header = "Change settings"
                        button_texts = ["Chatbot settings", "User settings"]
                        button = generate_interactive_button(
                            body=body, header=header, button_texts=button_texts
                        )
                        send_interactive_message(interactive=button, recipient=number)
    except:
        logger.error(traceback.format_exc())
        text = "Something went wrong. Please try again later."
        send_text(text, number)
