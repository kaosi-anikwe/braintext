# python imports
import os
import traceback
from datetime import datetime, timedelta

# installed imports
from dotenv import load_dotenv
from flask_login import login_required, current_user
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    jsonify,
    redirect,
    url_for,
    session,
)

# local imports
from .. import logger
from ..modules.email_utility import send_email
from ..chatbot.functions import send_text, send_otp_message, send_audio
from ..models import (
    OTP,
    get_otp,
    Users,
    Voices,
)

load_dotenv()

TEMP_FOLDER = os.getenv("TEMP_FOLDER")

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
    user_settings = current_user.user_settings()

    current_user.notify_on_profile_change = user_settings.notify_on_profile_change
    current_user.product_updates = user_settings.product_updates
    current_user.subscription_expiry = user_settings.subscription_expiry
    current_user.ai_voice_type = user_settings.ai_voice_type
    current_user.voice_response = user_settings.voice_response

    # get voices
    voices = {}
    male_voices = Voices.query.filter(
        Voices.gender == "male", Voices.type == "openai"
    ).all()
    male_voices = [voice.name for voice in male_voices]
    female_voices = Voices.query.filter(
        Voices.gender == "female", Voices.type == "openai"
    ).all()
    female_voices = [voice.name for voice in female_voices]
    voices["male"] = male_voices
    voices["female"] = female_voices

    return render_template(
        "main/profile.html", settings=settings, voices=voices, title="Profile"
    )


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
                    otp=check_otp.otp,
                    number=phone_no,
                )
                check_otp.update()

                return jsonify({"otp": check_otp.otp})
        else:
            otp = OTP(phone_no)
            send_otp_message(
                otp=otp.otp,
                number=phone_no,
            )
            otp.insert()

            return jsonify({"otp": otp.otp})
    except:
        logger.error(traceback.format_exc())
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
                otp=check_otp.otp,
                number=phone_no,
            )
            check_otp.update()

            return jsonify({"otp": check_otp.otp})
    except:
        logger.error(traceback.format_exc())
        return jsonify({"error": True})


# Veriry OTP
@main.route("/verify-otp", methods=["POST"])
@login_required
def verify_otp():
    try:
        data = request.get_json()
        phone_no = data["phone_no"]

        check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
        if check_otp:
            if check_otp.updated_at:
                if (
                    int((datetime.utcnow() - check_otp.updated_at).total_seconds())
                    >= 180
                ):
                    return jsonify({"expired": True})
            elif check_otp.created_at:
                if (
                    int((datetime.utcnow() - check_otp.created_at).total_seconds())
                    >= 180
                ):
                    return jsonify({"expired": True})

        current_user.phone_no = phone_no
        current_user.phone_verified = True
        current_user.update()
        check_otp.verified = True
        check_otp.update()
        flash("Phone number updated successfully", "success")

        # send list of features
        message = "Thank you for verifying your number. You're all set up and ready to use BrainText!"
        send_text(message, phone_no)
        with open(f"{TEMP_FOLDER}/features.txt") as f:
            get_features = f.readlines()
        features = "\n".join(get_features)
        send_text(features, phone_no)

        # send welcome audio
        media_url = f"{url_for('chatbot.send_voice_note', _external=True, _scheme='https')}?filename=welcome.ogg"
        send_audio(media_url, phone_no)

        return redirect(url_for("main.profile"))
    except:
        logger.error(traceback.format_exc())
        return jsonify({"error": True})


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
        logger.error(traceback.format_exc())
        return jsonify({"success": False}), 400


@main.get("/terms-of-service")
def terms_of_service():
    return render_template("main/tos.html", title="Terms of Service")


@main.get("/privacy-policy")
def privacy_policy():
    return render_template("main/privacy.html", title="Pricacy Policy")
