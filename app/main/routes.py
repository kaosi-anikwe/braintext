import os
import traceback
from datetime import datetime, timedelta
from twilio.rest import Client
from app.models import (
    OTP,
    get_otp,
    Users,
    UserSettings,
    StandardSubscription,
    PremiumSubscription,
    BasicSubscription,
)
from app.email_utility import send_email
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
import traceback

def send_otp_message(otp: int, name: str, phone_no: str) -> str:
    message = client.messages.create(
        body=f"Hi {name}! Here's your One Time Password to verify your number at Braintext. \n{otp} \nThe OTP will expire in 3 minutes.",
        from_="whatsapp:+15076094633",
        to=f"whatsapp:{phone_no}",
    )
    print(f"{message.sid} -- {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return message.sid


account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)


main = Blueprint("main", __name__)

# Index ---------------------------------------------
@main.route("/")
def index():
    return render_template("main/index.html")


@main.route("/email-template")
def email_template():
    return render_template("email_base.html")


# User Account -----------------------------------------
@main.route("/profile")
@login_required
def profile():
    settings = True if request.args.get("settings") else False
    user_settings = UserSettings.query.filter(
        UserSettings.user_id == current_user.id
    ).one()

    current_user.notify_on_profile_change = user_settings.notify_on_profile_change
    current_user.product_updates = user_settings.product_updates
    current_user.subscription_expiry = user_settings.subscription_expiry
    current_user.ai_voice_type = user_settings.ai_voice_type
    current_user.voice_response = user_settings.voice_response

    # check account expiry
    subscription = None
    if current_user.account_type == "Standard":
        subscriptions = StandardSubscription.query.filter(
            StandardSubscription.user_id == current_user.id,
            StandardSubscription.payment_status == "completed",
        ).all()
        for sub in subscriptions:
            if not sub.expired() and sub.sub_status == "active":
                subscription = sub
    elif current_user.account_type == "Premium":
        subscriptions = PremiumSubscription.query.filter(
            PremiumSubscription.user_id == current_user.id,
            PremiumSubscription.payment_status == "completed",
        ).all()
        for sub in subscriptions:
            if not sub.expired() and sub.sub_status == "active":
                subscription = sub

    if not subscription:  # all subscriptions have expired
        current_user.account_type = "Basic"
        current_user.update()

    if subscription:
        # calculate expiry date
        days_left = (subscription.get_expire_date() - current_user.timenow()).days
        if days_left < 1:
            hours_left = (
                subscription.get_expire_date() - current_user.timenow()
            ).total_seconds() / 3600
            expire_time = current_user.timenow() + timedelta(hours=hours_left)
            if expire_time.day > current_user.timenow().day:
                # next day
                days_left = f"tomorrow at {expire_time.strftime('%I:%M %p')}"
            else:
                days_left = f"expires today at {expire_time.strftime('%I:%M %p')}"
        else:
            days_left = (
                f"{days_left} days left" if days_left > 1 else f"{days_left} day left"
            )

        current_user.days_left = days_left

    return render_template("main/profile.html", settings=settings, title="Profile")


# OTP AND VERIFICATION ---------------------------------
# Verify OTP page
@main.route("/verify-number")
@login_required
def add_number():
    if current_user.phone_no and current_user.phone_verified:
        flash("Your WhatsApp number is already verified.")
        return redirect(url_for("main.profile"))
    if not current_user.email_verified:
        flash("Please verify your email to proceed.", "danger")
        return redirect(url_for("main.profile"))
    reverify = True if request.args.get("reverify") else False
    return render_template(
        "auth/add-number.html", reverify=reverify, title="Verify Number"
    )


# Send OTP
@main.route("/send-otp", methods=["POST"])
@login_required
def send_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    try:
        check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
        if check_otp:
            check_user = Users.query.filter(
            Users.phone_no == phone_no, Users.phone_verified == True
        ).one_or_none()
            if check_user:
                # number already used by another user
                return jsonify({"error": True})
            else:
                check_otp.otp = get_otp()
                send_otp_message(
                otp=check_otp.otp, name=current_user.first_name, phone_no=phone_no
            )
                check_otp.update()

                return jsonify({"otp": check_otp.otp})
        else:
            otp = OTP(phone_no)
            send_otp_message(otp=otp.otp, name=current_user.first_name, phone_no=phone_no)
            otp.insert()

            return jsonify({"otp": otp.otp})
    except:
        print(traceback.format_exc())
        return jsonify({"error": True})


# Resend OTP
@main.route("/resend-otp", methods=["POST"])
@login_required
def resend_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    try:
        check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
        if check_otp:
            check_otp.otp = get_otp()
            send_otp_message(
            otp=check_otp.otp, name=current_user.first_name, phone_no=phone_no
        )
            check_otp.update()

            return jsonify({"otp": check_otp.otp})
    except:
        print(traceback.format_exc())
        return jsonify({"error": True})


# Veriry OTP
@main.route("/verify-otp", methods=["POST"])
@login_required
def verify_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
    if check_otp:
        if check_otp.updated_at:
            if int((datetime.utcnow() - check_otp.updated_at).total_seconds()) >= 180:

                return jsonify({"expired": True})
        elif check_otp.created_at:
            if int((datetime.utcnow() - check_otp.created_at).total_seconds()) >= 180:

                return jsonify({"expired": True})

    current_user.phone_no = phone_no
    current_user.phone_verified = True
    current_user.update()
    check_otp.verified = True
    check_otp.update()
    flash("Phone number updated successfully", "success")
    return redirect(url_for("main.profile"))


@main.post("/send-email")
def send_contact_email():
    data = request.get_json()

    name = data["name"]
    email = data["email"]
    subject = data["subject"]
    body = data["body"]

    user = Users.query.filter(Users.email == email).one_or_none()
    if user:
        body = f"Name: {name} \nEmail: {email} \nUser ID: {user.uid} \n\n{body}"
    else:
        body = f"Name: {name} \nEmail: {email} \n\n{body}"

    try:
        if send_email(
            receiver_email="support@braintext.io",
            subject=subject,
            plaintext=body,
            sender_email=email,
        ):
            return jsonify({"success": True}), 200
    except:
        print(traceback.format_exc())
        return jsonify({"success": False}), 400


@main.get("/terms-of-service")
def terms_of_service():
    return render_template("main/tos.html", title="Terms of Service")


@main.get("/privacy-policy")
def privacy_policy():
    return render_template("main/privacy.html", title="Pricacy Policy")
