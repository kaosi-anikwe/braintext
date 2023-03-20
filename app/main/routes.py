import os
from datetime import datetime
from twilio.rest import Client
from app.models import OTP, get_otp, Users, UserSettings
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for


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

    return render_template("main/profile.html", settings=settings)


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
    return render_template("auth/add-number.html", reverify=reverify)


# Send OTP
@main.route("/send-otp", methods=["POST"])
@login_required
def send_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

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


# Resend OTP
@main.route("/resend-otp", methods=["POST"])
@login_required
def resend_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
    if check_otp:
        check_otp.otp = get_otp()
        send_otp_message(
            otp=check_otp.otp, name=current_user.first_name, phone_no=phone_no
        )
        check_otp.update()

        return jsonify({"otp": check_otp.otp})


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
