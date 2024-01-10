# python imports
import os
import time
import uuid
import math
import random
from datetime import datetime, timedelta, timezone

# installed imports
import jwt
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# local imports
from app import db, login_manager
from app.modules.calculate import *


BASE_COST = 0.3

# generate 6 digit OTP
def get_otp() -> int:
    digits = "0123456789"
    otp = ""
    for i in range(6):
        otp += digits[math.floor(random.random() * 10)]
    if otp.startswith("0"):
        return get_otp()
    return int(otp)


# timestamp to be inherited by other class models
class TimestampMixin(object):
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def format_date(self):
        self.created_at = self.created_at.strftime("%d %B, %Y %I:%M")

    def format_time(self):
        try:
            self.datetime = self.datetime.strftime("%d %B, %Y %I:%M")
        except:
            pass


# db helper functions
class DatabaseHelperMixin(object):
    def update(self):
        db.session.commit()

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))


class Users(db.Model, TimestampMixin, UserMixin, DatabaseHelperMixin):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(20), default="regular")
    balance = db.Column(db.Float, default=5)
    timezone_offset = db.Column(db.Integer)
    phone_no = db.Column(db.String(20))
    phone_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    from_anonymous = db.Column(db.Boolean, default=False)
    edited = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __init__(self, first_name, last_name, email, password, timezone_offset) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = self.get_password_hash(password)
        self.uid = uuid.uuid4().hex
        self.timezone_offset = timezone_offset

    # generate user password i.e. hashing
    def get_password_hash(self, password):
        return generate_password_hash(password)

    # check user password is correct
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # for reseting a user password
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )

    # return concatenated name
    def display_name(self):
        return f"{self.first_name} {self.last_name}"

    # get local timezone
    def get_timezone(self):
        return timezone(offset=timedelta(seconds=self.timezone_offset))

    # get local time with timezone
    def timenow(self):
        return (
            datetime.now(tz=self.get_timezone())
            if not self.from_anonymous
            else datetime.utcnow()
        )

    # verify token generated for resetting password
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except:
            return None
        return Users.query.get(id)

    def user_settings(self):
        settings: UserSettings
        settings = UserSettings.query.filter(UserSettings.user_id == self.id).one()
        return settings


class UserSettings(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "user_setting"

    id = db.Column(db.Integer, primary_key=True)
    context_messages = db.Column(db.Integer, default=int(os.getenv("CONTEXT_LIMIT")))
    max_response_length = db.Column(db.Integer)
    image_generation = db.Column(db.Boolean, default=True)
    online_search = db.Column(db.Boolean, default=True)
    media_search = db.Column(db.Boolean, default=True)
    audio_responses = db.Column(db.Boolean, default=True)
    image_recognition = db.Column(db.Boolean, default=True)
    audio_voice = db.Column(db.String(50), default="Mia")
    image_generation_model = db.Column(db.String(50), default="dalle3")
    image_generation_style = db.Column(db.String(50), default="natural")
    image_generation_quality = db.Column(db.String(50), default="standard")
    image_generation_size = db.Column(db.String(50), default="1024x1024")
    warn_low_balance = db.Column(db.Integer, default=2)
    email_updates = db.Column(db.Boolean, default=True)
    change_number = db.Column(db.Boolean, default=True)
    change_first_name = db.Column(db.Boolean, default=True)
    change_last_name = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.ForeignKey("user.id"))

    def __init__(self, user_id):
        self.user_id = user_id

    def image_confg(self):
        if self.image_generation_model == "dalle2":
            return f"{self.image_generation_model}.{self.image_generation_size}"
        elif self.image_generation_model == "dalle3":
            return f"{self.image_generation_model}.{self.image_generation_style}.{self.image_generation_quality}-{self.image_generation_size}"

    def functions(self):
        return [
            {"name": "generate_image", "enabled": self.image_generation},
            {"name": "google_search", "enabled": self.online_search},
            {"name": "media_search", "enabled": self.media_search},
            {"name": "speech_synthesis", "enabled": self.audio_responses},
            {"name": "get_account_balance", "enabled": True},
            {"name": "recharge_account", "enabled": True},
            {"name": "account_settings", "enabled": True},
        ]


class AnonymousUsers(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "anonymous_user"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone_no = db.Column(db.String(20))
    signup_stage = db.Column(db.String(50))
    balance = db.Column(db.Float, default=5)

    def __init__(self, phone_no) -> None:
        self.phone_no = phone_no
        self.uid = uuid.uuid4().hex
        self.signup_stage = "anonymous"

    def respond(self) -> bool:
        if BASE_COST < self.balance:
            return True
        return False

    # return concatenated name
    def display_name(self):
        return f"{self.first_name} {self.last_name}"


class MessageRequests(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "usage"

    id = db.Column(db.Integer, primary_key=True)
    gpt_3_input = db.Column(db.Integer, default=0)
    gpt_3_output = db.Column(db.Integer, default=0)
    gpt_4_input = db.Column(db.Integer, default=0)
    gpt_4_output = db.Column(db.Integer, default=0)
    dalle_2 = db.Column(db.String(50), default="")
    dalle_3 = db.Column(db.String(50), default="")
    tts = db.Column(db.Integer, default=0)
    whisper = db.Column(db.Float, default=0)
    anonymous = db.Column(db.Boolean, default=False)
    alert_low = db.Column(db.Boolean, default=False)
    interactive = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer)

    def __init__(self, user_id, anonymous: bool = None):
        self.user_id = user_id
        if anonymous:
            self.anonymous = anonymous

    def usage(self):
        return {
            "gpt_3_input": self.gpt_3_input,
            "gpt_3_output": self.gpt_3_output,
            "gpt_4_intput": self.gpt_4_input,
            "gpt_4_output": self.gpt_4_output,
            "dalle_2": self.dalle_2,
            "dalle_3": self.dalle_3,
            "tts": self.tts,
            "whisper": self.whisper,
        }

    def cost(self):
        gpt_3_tokens = {"input": self.gpt_3_input, "output": self.gpt_3_output}
        gpt_4_tokens = {"input": self.gpt_3_input, "output": self.gpt_4_output}
        dalle_3 = {
            "type": self.dalle_3.split("-")[0],
            "res": self.dalle_3.split("-")[1],
        }
        cost = {
            "gpt_3": gpt_3_5_cost(gpt_3_tokens),
            "gpt_4": gpt_4_vision_cost(gpt_4_tokens),
            "dalle_2": dalle2_cost(self.dalle_2),
            "dalle_3": dalle3_cost(dalle_3),
            "tts": tts_cost(self.tts),
            "whisper": whisper_cost(self.whisper),
        }
        cost["total"] = sum(price for price in cost.values())
        return cost


class Transactions(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="pending")
    currency = db.Column(db.String(10), default="NGN")
    mode = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    usd_value = db.Column(db.Float)
    notified = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(50))
    tx_ref = db.Column(db.String(100), nullable=False)
    flw_tx_id = db.Column(db.String(100), nullable=False)
    flw_tx_ref = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.ForeignKey("user.id"))

    def __init__(
        self,
        message,
        mode,
        amount,
        tx_ref,
        flw_tx_id,
        flw_tx_ref,
        user_id,
        currency=None,
    ):
        self.message = message
        self.mode = mode
        self.amount = amount
        self.user_id = user_id
        self.tx_ref = tx_ref
        self.flw_tx_id = flw_tx_id
        self.flw_tx_ref = flw_tx_ref
        self.currency = currency if currency else "NGN"

    def output(self, code: str = None, ussd_code: str = None):
        return {
            "message": self.message,
            "status": self.status,
            "amount": self.amount,
            "currency": self.currency,
            "code": code,
            "ussd_code": ussd_code,
        }


class OTP(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "otp"

    id = db.Column(db.Integer, primary_key=True)
    phone_no = db.Column(db.String(20), nullable=False)
    otp = db.Column(db.Integer, nullable=False)
    verified = db.Column(db.Boolean, default=False)

    def __init__(self, phone_no) -> None:
        self.otp = get_otp()
        self.phone_no = phone_no
        self.verified = False


class Voices(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "voice"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(20))
    type = db.Column(db.String(20))

    def __init__(self, code, name, gender, type):
        self.code = code
        self.name = name
        self.gender = gender
        self.type = type
        self.insert()
