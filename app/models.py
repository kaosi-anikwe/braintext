import jwt
import time
import uuid
import math
import random
from app import db, login_manager
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


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
    account_type = db.Column(db.String(20), default="Basic")
    timezone_offset = db.Column(db.Integer)
    phone_no = db.Column(db.String(20))
    phone_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    edited = db.Column(db.Boolean, default=False)
    password_hash = db.Column(db.String(128), nullable=False)

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
        return datetime.now(tz=self.get_timezone())

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

    def __init__(self, first_name, last_name, email, password, timezone_offset) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password_hash = self.get_password_hash(password)
        self.uid = uuid.uuid4().hex
        self.timezone_offset = timezone_offset


class UserSettings(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "user_setting"

    id = db.Column(db.Integer, primary_key=True)
    notify_on_profile_change = db.Column(db.Boolean, default=False)
    product_updates = db.Column(db.Boolean, default=False)
    subscription_expiry = db.Column(db.Boolean, default=True)
    ai_voice_type = db.Column(db.String(50))
    voice_response = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.ForeignKey("user.id"))

    def __init__(self, user_id) -> None:
        self.notify_on_profile_change = False
        self.product_updates = False
        self.subscription_expiry = True
        self.ai_voice_type = "Joanna"
        self.user_id = user_id


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


# Subscription Types
class BasicSubscription(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "basic_subscription"

    id = db.Column(db.Integer, primary_key=True)
    expire_date = db.Column(db.DateTime(timezone=True))
    time
    sub_status = db.Column(db.String(20))
    prompts = db.Column(db.Integer)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)

    def __init__(self, user_id) -> None:
        self.prompts = 0
        self.expire_date = datetime.utcnow() + timedelta(days=7)
        self.sub_status = "active"
        self.user_id = user_id

    # helper functions
    def upgrade(self) -> None:
        if self.sub_status != "upgraded":
            self.sub_status = "upgraded"
            self.update()

    # get localized expire_date
    def get_expire_date(self):
        user = Users.query.get(self.user_id)
        return self.expire_date.replace(tzinfo=user.get_timezone())

    def expired(self) -> bool:
        user = Users.query.get(self.user_id)
        if user.timenow() > self.get_expire_date():
            return True
        else:
            return False

    def renew(self) -> bool:
        try:
            user = Users.query.get(self.user_id)
            while self.get_expire_date() < user.timenow():
                self.expire_date = self.expire_date + timedelta(days=7)
            self.prompts = 0
            self.update()
            return True
        except Exception as e:
            print(e)
            return False


    def respond(self) -> bool:
        if self.expired():
            self.renew()
        if self.prompts < 3:
            self.prompts += 1
            self.update()
            return True
        else:
            return False


class StandardSubscription(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "standard_subscription"

    id = db.Column(db.Integer, primary_key=True)
    tx_ref = db.Column(db.String(100), nullable=False)
    tx_id = db.Column(db.String(100))
    flw_ref = db.Column(db.String(100))
    payment_status = db.Column(db.String(20))
    sub_status = db.Column(db.String(20))
    expire_date = db.Column(db.DateTime(timezone=True))
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)

    def __init__(self, tx_ref, user_id) -> None:
        self.tx_ref = tx_ref
        self.payment_status = "pending"
        self.user_id = user_id

    # helper functions
    def upgrade(self) -> None:
        if self.sub_status != "upgraded":
            self.sub_status = "upgraded"
            self.update()

    # get localized expire_date
    def get_expire_date(self):
        user = Users.query.get(self.user_id)
        return self.expire_date.replace(tzinfo=user.get_timezone())

    def expired(self) -> bool:
        # return False
        user = Users.query.get(self.user_id)
        if user.timenow() > self.get_expire_date():
            if self.sub_status != "expired":
                self.sub_status = "expired"
                self.update()
            return True
        else:
            return False


class PremiumSubscription(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "premium_subscription"

    id = db.Column(db.Integer, primary_key=True)
    tx_ref = db.Column(db.String(100), nullable=False)
    tx_id = db.Column(db.String(100))
    flw_ref = db.Column(db.String(100))
    payment_status = db.Column(db.String(20))
    sub_status = db.Column(db.String(20))
    expire_date = db.Column(db.DateTime(timezone=True))
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)

    def __init__(self, tx_ref, user_id) -> None:
        self.tx_ref = tx_ref
        self.payment_status = "pending"
        self.user_id = user_id

    # helper functions
    def upgrade(self) -> None:
        if self.sub_status != "upgraded":
            self.sub_status = "upgraded"
            self.update()

    # get localized expire_date
    def get_expire_date(self):
        user = Users.query.get(self.user_id)
        return self.expire_date.replace(tzinfo=user.get_timezone())

    def expired(self) -> bool:
        user = Users.query.get(self.user_id)
        if user.timenow() > self.get_expire_date():
            if self.sub_status != "expired":
                self.sub_status = "expired"
                self.update()
            return True
        else:
            return False
