# python imports
import os
import requests
import traceback
from typing import Any, Dict, Union

# installed imports
from flask import url_for, after_this_request
from dotenv import load_dotenv
from PIL import Image

# local imports
from ..models import Users, BasicSubscription, StandardSubscription, PremiumSubscription
from ..modules.functions import *

load_dotenv()

TEMP_FOLDER = os.getenv("TEMP_FOLDER")
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
    Returns ```bool```
    """
    data = _preprocess(data)
    if "messages" in data:
        return True
    return False


def is_reply(data: Dict[Any, Any]) -> bool:
    """
    Returns ```True``` if message is a reply, else returns ```False```.
    """
    data = _preprocess(data)
    if "messages" in data:
        if "context" in data["messages"][0]:
            return True
        return False
    return False


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

    Args: ```emoji```: Unicode value of emoji to be sent.
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


def _create_button(button: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Creates a button to be used to send interactive messages. This function is meant to be called internally.
    """
    data = {"type": "list", "action": button.get("action")}
    if button.get("header"):
        data["header"] = {"type": "text", "text": button.get("header")}
    if button.get("body"):
        data["body"] = {"text": button.get("body")}
    if button.get("footer"):
        data["footer"] = {"text": button.get("footer")}
    return data


def send_button_message(button: Dict[Any, Any], recipient: str) -> Union[str, None]:
    """
    Sends an interactive message to the user.

    Args: ```button```: button created with ```_create_button```
    """
    data = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "interactive",
        "interactive": _create_button(button),
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
    response = requests.get(media_url, headers=HEADERS)
    if response.status_code == 200:
        try:
            full_path = os.path.join(file_path, file_name)
            with open(full_path, "wb") as f:
                f.write(response.content)
            return full_path
        except:
            print(traceback.format_exc())
            return None
    return None


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
        print(traceback.format_exc())
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


def speech_synthesis(text: str, voice_type: str, number: str):
    """Synthesize audio output and send to user."""
    try:
        audio_filename = synthesize_speech(
            text=text,
            voice=voice_type,
        )
        if audio_filename == None:
            text = "AWS session expired."
            return send_text(text, number)
        audio_path = os.path.join(TEMP_FOLDER, audio_filename)
        converted_filename = f"{audio_filename.split('.')[0]}.opus"
        converted_path = os.path.join(TEMP_FOLDER, converted_filename)

        # convert to ogg with ffmpeg
        conversion = subprocess.Popen(
            f"ffmpeg -i '{audio_path}' -c:a libopus '{converted_path}'",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).wait()
        print(f"Convesion result: {conversion}")

        # remove original audio
        if os.path.exists(audio_path):
            os.remove(audio_path)

        media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename={converted_filename}"
        print(media_url)

        return send_audio(media_url, number)
    except BotoCoreError:
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)
    except ClientError:
        print(traceback.format_exc())
        text = "Sorry, you're response was too long. Please rephrase the question or break it into segments."
        return send_text(text, number)


def speech_response(data: Dict[Any, Any], voice_type: str):
    """Respond with audio from WhatsApp text."""
    try:
        name = get_name(data)
        number = get_number(data)
        message = get_message(data)
        message_id = get_message_id(data)
        greeting = contains_greeting(message)
        thanks = contains_thanks(message)

        try:
            user_db_path = get_user_db(name, number)
            messages = load_messages(
                prompt=message,
                db_path=user_db_path,
            )
            text, tokens, role = text_response(
                messages=messages,
                number=number,
                message_id=message_id,
            )
        except:
            print(traceback.format_exc())
            text = (
                "Sorry I can't respond to that at the moment. Please try again later."
            )
            return reply_to_message(message_id, number, text)

        # record ChatGPT response
        new_message = {
            "role": role,
            "content": text,
        }
        new_message = Messages(new_message, user_db_path)
        new_message.insert()

        log_response(
            name=name,
            number=number,
            message=message,
            tokens=tokens,
        )

        send_reaction(
            chr(128075), message_id, number
        ) if greeting else None  # react waving hand
        send_reaction(
            chr(128153), message_id, number
        ) if thanks else None  # react blue love emoji

        return speech_synthesis(text=text, voice_type=voice_type, number=number)
    except:
        print(traceback.format_exc())
        text = "Sorry I can't respond to that at the moment. Please try again later."
        return reply_to_message(message_id, number, text)


def meta_chat_response(
    data: Dict[Any, Any],
    user: Users,
    subscription: Union[
        BasicSubscription, StandardSubscription, PremiumSubscription
    ] = None,
):
    """
    Typical WhatsApp text response with Meta functions.
    """
    name = get_name(data)
    number = f"+{get_number(data)}"
    message = get_message(data)
    message_id = get_message_id(data)
    greeting = contains_greeting(message)
    thanks = contains_thanks(message)
    isreply = is_reply(data)
    image = False
    audio = False
    user_db_path = get_user_db(name=name, number=number)
    messages = load_messages(
        prompt=message,
        db_path=user_db_path,
    )
    try:
        if subscription:
            if subscription.expired():
                subscription.update_account(user.id)
                text = "It seems your subscription has expired. Plese renew your subscription to continue to enjoy your services. \nhttps://braintext.io/profile"
                return reply_to_message(message_id, number, text)
        try:
            if "dalle" in message.lower():
                # Image generation
                image = True
                prompt = message.lower().replace("dalle", "")
                image_url = image_response(prompt)
                log_response(
                    name=name,
                    number=number,
                    message=message,
                )
                return send_image(image_url, number)  # function ends here
            elif "voicegen" in message.lower():
                # Speech synthesis
                audio = True
                text = message.lower().replace("voicegen", "")
                voice_type = user.user_settings().ai_voice_type
                log_response(
                    name=name,
                    number=number,
                    message=message,
                )
                return speech_synthesis(text=text, voice_type=voice_type, number=number)
            elif "whysper" in message.lower():
                # Audio response
                audio = True
                text = message.lower().replace("whysper", "")
                voice_type = user.user_settings().ai_voice_type
                log_response(
                    name=name,
                    number=number,
                    message=message,
                )
                return speech_response(
                    data=data,
                    voice_type=voice_type,
                )
            else:
                text, tokens, role = text_response(
                    messages=messages, number=number, message_id=message_id
                )
                log_response(
                    name=name,
                    number=number,
                    message=message,
                    tokens=tokens,
                )
        except:
            print(traceback.format_exc())
            text = (
                "Sorry, I can't respond to that at the moment. Please try again later."
            )
            return reply_to_message(message_id, number, text)

        if not image and not audio:
            # record ChatGPT response
            new_message = {"role": role, "content": text}
            new_message = Messages(new_message, user_db_path)
            new_message.insert()

        send_reaction(
            chr(128075), message_id, number
        ) if greeting else None  # react waving hand
        send_reaction(
            chr(128153), message_id, number
        ) if thanks else None  # react blue love emoji
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
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return reply_to_message(message_id, number, text)


def meta_audio_response(user: Users, data: Dict[Any, Any]):
    """WhatsApp audio response with Meta functions."""
    name = get_name(data)
    number = f"+{get_number(data)}"
    message_id = get_message_id(data)

    try:
        audio_url = get_media_url(get_audio_id(data))
        audio_file = download_media(
            audio_url,
            f"{datetime.utcnow().strftime('%M%S%f')}",
        )
        try:
            transcript = transcribe_audio(audio_file)
            greeting = contains_greeting(transcript)
            thanks = contains_thanks(transcript)
        except:
            print(traceback.format_exc())
            text = "Error transcribing audio. Please try again later."
            return send_text(text, number)

        # delete audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)
        try:
            user_db_path = get_user_db(name, number)
            messages = load_messages(
                prompt=transcript,
                db_path=user_db_path,
            )
            text, tokens, role = text_response(
                messages=messages,
                number=number,
                message_id=message_id,
            )
        except:
            print(traceback.format_exc())
            text = (
                "Sorry I can't respond to that at the moment. Please try again later."
            )
            return send_text(text, number)

        # record ChatGPT response
        new_message = {
            "role": role,
            "content": text,
        }
        new_message = Messages(new_message, user_db_path)
        new_message.insert()

        log_response(
            name=name,
            number=number,
            message=transcript,
            tokens=tokens,
        )
        send_reaction(
            chr(128075), message_id, number
        ) if greeting else None  # react waving hand
        send_reaction(
            chr(128153), message_id, number
        ) if thanks else None  # react blue love emoji

        user_settings = user.user_settings()
        if user_settings.voice_response:
            return speech_synthesis(
                text=text, voice_type=user_settings.ai_voice_type, number=number
            )
        else:
            if len(text) < WHATSAPP_CHAR_LIMIT:
                return send_text(text, number)
            else:
                return meta_split_and_respond(
                    text,
                    number,
                    get_message_id(data),
                )
    except:
        print(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)


def meta_image_response(data: Dict[Any, Any]):
    """WhatsApp image response wtih Meta functions."""
    name = get_name(data)
    number = f"+{get_number(data)}"
    try:
        image = get_image(data)
        image_url = get_media_url(image["id"])
        prompt = ""
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
        if "caption" in image:
            prompt = image["caption"]
            if "variation" in prompt.lower():
                image_url = image_variation(image_path)
            else:
                image_url = image_edit(image_path, prompt)
        else:
            # Image variation
            image_url = image_variation(image_path)

        log_response(
            name=name,
            number=number,
            message=prompt,
        )
        send_image(image_url, number)
    except:
        print(traceback.format_exc())
        text = "Something went wrong. Please try again later."
        return send_text(text, number)
