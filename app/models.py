import jwt
import time
import uuid
import math
import random
from app import db, login_manager, logger
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

    def get_active_sub(self):
        subscription = None
        if self.account_type == "Standard":
            subscriptions = StandardSubscription.query.filter(
                StandardSubscription.user_id == self.id,
                StandardSubscription.payment_status == "completed",
                StandardSubscription.sub_status == "active",
            ).all()
            for sub in subscriptions:
                if not sub.expired():
                    subscription = sub

        elif self.account_type == "Premium":
            subscriptions = PremiumSubscription.query.filter(
                PremiumSubscription.user_id == self.id,
                PremiumSubscription.payment_status == "completed",
                PremiumSubscription.sub_status == "active",
            ).all()
            for sub in subscriptions:
                if not sub.expired():
                    subscription = sub
        return subscription

    def user_settings(self):
        return UserSettings.query.filter(UserSettings.user_id == self.id).one()


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


class AnonymousUsers(db.Model, TimestampMixin, DatabaseHelperMixin):
    __tablename__ = "anonymous_user"

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(200), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100))
    phone_no = db.Column(db.String(20))
    prompts = db.Column(db.Integer)
    signup_stage = db.Column(db.String(50))

    def __init__(self, phone_no) -> None:
        self.phone_no = phone_no
        self.prompts = 0
        self.uid = uuid.uuid4().hex
        self.signup_stage = "anonymous"

    def respond(self) -> bool:
        if self.prompts < 20:
            return True
        return False

    # return concatenated name
    def display_name(self):
        return f"{self.first_name} {self.last_name}"


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
        return (
            self.expire_date.replace(tzinfo=user.get_timezone())
            if not user.from_anonymous
            else self.expire_date
        )

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
            logger.error(e)
            return False

    def respond(self) -> bool:
        if self.expired():
            self.renew()
        if self.prompts < 10:
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
        return (
            self.expire_date.replace(tzinfo=user.get_timezone())
            if not user.from_anonymous
            else self.expire_date
        )

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

    def update_account(self, user_id) -> None:
        # updates account after expiry
        user = Users.query.get(user_id)
        user.account_type = "Basic"
        user.update()
        # renew basic sub
        basic_sub = BasicSubscription.query.filter(
            BasicSubscription.user_id == user_id
        ).one()
        if not basic_sub.renew():
            logger.warning(
                f"Failed to renew basic sub for user: {user.display_name()} with user ID: {user.id}"
            )


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
        return (
            self.expire_date.replace(tzinfo=user.get_timezone())
            if not user.from_anonymous
            else self.expire_date
        )

    def expired(self) -> bool:
        user = Users.query.get(self.user_id)
        if user.timenow() > self.get_expire_date():
            if self.sub_status != "expired":
                self.sub_status = "expired"
                self.update()
            return True
        else:
            return False

    def update_account(self, user_id) -> None:
        # updates account after expiry
        user = Users.query.get(user_id)
        user.account_type = "Basic"
        user.update()
        # renew basic sub
        basic_sub = BasicSubscription.query.filter(
            BasicSubscription.user_id == user_id
        ).one()
        if not basic_sub.renew():
            logger.warning(
                f"Failed to renew basic sub for user: {user.display_name()} with user ID: {user.id}"
            )

    @staticmethod
    def create_fake(user_id):
        user = Users.query.get(user_id)
        tx_ref = "0000000000000000"
        subscription = PremiumSubscription(tx_ref=tx_ref, user_id=user_id)
        subscription.flw_ref = "################"
        subscription.payment_status = "completed"
        subscription.sub_status = "active"
        subscription.tx_id = "$$$$$$$$$$$$$"
        subscription.expire_date = user.timenow() + timedelta(days=100)
        # localize time
        subscription.expire_date = subscription.expire_date.replace(
            tzinfo=user.get_timezone()
        )
        subscription.insert()
        # check for old sub
        old_subs = (
            StandardSubscription.query.filter(
                StandardSubscription.sub_status == "active",
                StandardSubscription.user_id == user.id,
            )
            .order_by(StandardSubscription.id.desc())
            .all()
        )
        for old_sub in old_subs:
            if not old_sub.expired():
                old_sub.upgrade()
        old_subs = (
            PremiumSubscription.query.filter(
                PremiumSubscription.id != subscription.id,
                PremiumSubscription.sub_status == "active",
                PremiumSubscription.user_id == user.id,
            )
            .order_by(PremiumSubscription.id.desc())
            .all()
        )
        for old_sub in old_subs:
            if not old_sub.expired():
                old_sub.upgrade()

        user.account_type = "Premium"
        user.update()

        return subscription


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
