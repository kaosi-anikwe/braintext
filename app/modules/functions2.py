# python imports
import os
import traceback
from typing import Dict, Any

# installed imports
from dotenv import load_dotenv

# local imports
from app import logger
from ..models import Users

load_dotenv()

FILES = os.getenv("FILES")


def account_settings(data: Dict[Any, Any], **kwargs):
    from .functions import log_response, get_user_db
    from ..chatbot.functions import (
        send_text,
        get_name,
        get_number,
        send_interactive_message,
        generate_interactive_button,
    )

    name = get_name(data)
    number = f"+{get_number(data)}"
    message = kwargs.get("message")
    tokens = kwargs.get("tokens")
    text = ""

    try:
        user = Users.query.filter(Users.phone_no == number).one_or_none()
        if not user:
            text = "Access to this feature requires an account. Please create an account to proceed."
            return send_text(text, number)
        body = f"The user settings interface provides you with the ability to manage both your account and chatbot settings in one place. You can access and update your personal information, notification preferences, chatbot interactions, and more. With this interface, you can customize your experience to best suit your needs and preferences."
        header = "Change settings"
        button_texts = ["Chatbot settings", "User settings"]
        button = generate_interactive_button(
            body=body, header=header, button_texts=button_texts
        )
        return send_interactive_message(interactive=button, recipient=number)
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)
    finally:
        log_response(
            name=name,
            number=number,
            message=message,
            tokens=tokens,
        )

        # record ChatGPT response
        record_message(name, number, text)


def record_message(name: str, number: str, message: str, assistant=True):
    try:
        from .messages import Messages
        from .functions import get_user_db

        user_db_path = get_user_db(name=name, number=number)
        new_message = {"role": "assistant" if assistant else "user", "content": message}
        new_message = Messages(new_message, user_db_path)
        new_message.insert()
        return True
    except:
        logger.error(traceback.format_exc())
        return False
