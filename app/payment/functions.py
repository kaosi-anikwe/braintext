# python imports
import os
import time
import traceback
from typing import Dict, Any

# installed imports
import requests
from flask import request
from dotenv import load_dotenv

# local imports
from app import logger
from app.modules.messages import Messages
from app.models import Users, Transactions

load_dotenv()

USSD_CHARGE_URL = "https://api.flutterwave.com/v3/charges?type=ussd"
USD2BT = int(os.getenv("USD2BT"))
RAVE_PUB_KEY = os.getenv("RAVE_PUBLIC_KEY")
RAVE_SEC_KEY = os.getenv("RAVE_SECRET_KEY")
FLW_HEADERS = {
    "Authorization": f"Bearer {RAVE_SEC_KEY}",
    "content-type": "application/json",
}


def get_account_balance(data: Dict[Any, Any], **kwargs):
    """Retrieves user's account balance"""
    from ..modules.functions import log_response, get_user_db
    from ..chatbot.functions import get_number, send_text, get_name

    text = ""
    number = f"+{get_number(data)}"
    name = get_name(data)
    message = kwargs.get("message")
    tokens = kwargs.get("tokens")
    try:
        try:
            # get user
            user = Users.query.filter(Users.phone_no == number).one_or_none()
            if not user:
                text = "Access to this feature requires an account. Please create an account to proceed."
                return send_text(text, number)
            text = f"Your estimated balance is {round(user.balance, 2)} BT"
            return send_text(text, number)
        except:
            logger.error(traceback.format_exc())
            text = (
                "Sorry, I cannot respond to that at the moment, please try again later."
            )
            return send_text(text, number)
        finally:
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
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)


def recharge_account(data, **kwargs):
    # get user
    from ..payment.routes import BANK_CODES
    from ..payment.functions import exchange_rates
    from ..modules.functions import log_response, get_user_db
    from ..chatbot.functions import get_number, send_text, get_name

    number = f"+{get_number(data)}"
    name = get_name(data)
    tokens = kwargs.get("tokens")
    message = kwargs.get("message")
    try:
        user = Users.query.filter(Users.phone_no == number).one_or_none()
        if not user:
            text = "Access to this feature requires an account. Please create an account to proceed."
            return send_text(text, number)

        text = ""
        amount = kwargs.get("amount")
        currency = kwargs.get("currency", "NGN")
        bank_name = kwargs.get("bank_name")
        bank_code = BANK_CODES.get(bank_name)
        tx_ref = generate_tx_ref("ussd", user.uid)
        if not bank_code:
            bank_list = "\n".join(BANK_CODES.keys())
            text = f"Sorry, the selected bank is not eligible for USSD top-up. Please select one of the followng banks:\n{bank_list}"
            return send_text(text, number)
        # create transaction
        data = {
            "account_bank": bank_code,
            "amount": amount,
            "currency": currency,
            "email": user.email,
            "fullname": user.display_name(),
            "tx_ref": tx_ref,
            "meta": {
                "bt_amount": round(float(amount) / exchange_rates("USD") * USD2BT, 2),
                "user_id": user.uid,
            },
        }
        try:
            response = requests.post(USSD_CHARGE_URL, headers=FLW_HEADERS, json=data)
            if response.ok:
                logger.info(
                    f"USSD CHARGE FOR USER #{user.id} INITATED. AMOUNT: {amount}"
                )
                response_data = response.json()
                if response_data["status"] == "success":
                    flw_tx_id = response_data["data"]["id"]
                    flw_tx_ref = response_data["data"]["flw_ref"]
                    code = response_data["data"]["payment_code"]
                    ussd_code = response_data["meta"]["authorization"]["note"]
                    text = f"Your request to top-up ₦{amount} through {bank_name} has been initiated successfully!\nPlease dial the provided code to complete the transaction."
                    send_text(text, number)
                    send_text(f"{ussd_code}", number)
                    return
                text = f"There was a problem initiating your recharge request. Please try again later.\nIf the issue persists, try again from your profile.\n{request.host_url}profile"
                return send_text(text, number)
        except:
            logger.error(traceback.format_exc())
            text = f"There was a problem initiating your recharge request. Please try again later.\nIf the issue persists, try again from your profile.\n{request.host_url}profile"
            return send_text(text, number)
        finally:
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
    except:
        logger.error(traceback.format_exc())
        text = "Sorry, I cannot respond to that at the moment, please try again later."
        return send_text(text, number)


def exchange_rates(currency: str):
    return 1650


def generate_tx_ref(mode: str, user_uid: str):
    return f"{mode}-{user_uid}-{str(time.time()).split('.')[0]}"
