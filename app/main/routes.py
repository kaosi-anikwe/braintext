# python imports
import os
import calendar
import traceback
from datetime import datetime

# installed imports
from dotenv import load_dotenv
from sqlalchemy import extract
from flask_login import login_required, current_user
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    jsonify,
    redirect,
    url_for,
)

# local imports
from .. import logger, csrf
from ..payment.functions import exchange_rates
from ..modules.email_utility import send_email
from ..chatbot.functions import send_text, send_otp_message, send_audio
from ..models import OTP, get_otp, User, Voice, MessageRequest, Transaction, FAQ

load_dotenv()

TEMP_FOLDER = os.getenv("TEMP_FOLDER")

main = Blueprint("main", __name__)


# Index ---------------------------------------------
@main.route("/")
def index():
    faqs = FAQ.query.all()
    return render_template(
        "main/index.html", faqs=faqs, exchange_rate=exchange_rates("USD")
    )


# User Account -----------------------------------------
@main.route("/profile")
@login_required
def profile():
    settings = True if request.args.get("settings") else False
    user_settings = current_user.user_settings()

    # get voices
    voices = {}
    male_voices = Voice.query.filter(
        Voice.gender == "male", Voice.type == "openai"
    ).all()
    male_voices = [voice.name for voice in male_voices]
    female_voices = Voice.query.filter(
        Voice.gender == "female", Voice.type == "openai"
    ).all()
    female_voices = [voice.name for voice in female_voices]
    voices["male"] = male_voices
    voices["female"] = female_voices

    return render_template("main/profile.html", title="Profile")


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
            check_user = User.query.filter(
                User.phone_no == phone_no, User.phone_verified == True
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

    user = User.query.filter(User.email == email).one_or_none()
    if user:
        body = f"Name: {name} \nEmail: {email} \nUser ID: {user.uid} \n\n{body}"
    else:
        body = f"Name: {name} \nEmail: {email} \n\n{body}"

    try:
        if send_email(
            receiver_email="support@braintext.io",
            subject=subject,
            plaintext=body,
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


@main.route("/usage", methods=["POST", "GET"])
@login_required
def usage():
    if request.method == "POST":
        try:
            data = request.get_json()
            month = int(data.get("month", datetime.utcnow().month))
            year = int(data.get("year", datetime.utcnow().year))
            records = MessageRequest.query.filter(
                extract("month", MessageRequest.created_at) == month,
                extract("year", MessageRequest.created_at) == year,
                MessageRequest.user_id == current_user.id,
            ).all()
            usage = []
            usage_total = 0
            # extract cost usage for each day
            days = calendar.monthrange(year, month)[1]
            for day in range(1, days + 1):
                date = datetime(year=year, month=month, day=day)
                label = date.strftime("%d %b")
                day_cost = {}
                day_usage = [
                    record.cost() for record in records if record.created_at.day == day
                ]
                if day_usage:
                    for key in day_usage[0].keys():
                        total = sum(day[key] for day in day_usage)
                        usage_total += total
                        day_cost[key] = total
                    usage.append({label: day_cost})
                else:
                    usage.append({label: MessageRequest.empty()})
            # get user's range
            oldest = (
                MessageRequest.query.filter(MessageRequest.user_id == current_user.id)
                .order_by(MessageRequest.created_at.asc())
                .first()
            )
            usage_range = (
                [
                    {
                        "month": oldest.created_at.month - 1,
                        "year": oldest.created_at.year,
                    },
                    {"month": datetime.now().month - 1, "year": datetime.now().year},
                ]
                if oldest
                else [
                    {"month": datetime.now().month - 1, "year": datetime.now().year},
                    {"month": datetime.now().month - 1, "year": datetime.now().year},
                ]
            )
            return jsonify(usage=usage, total=usage_total, range=usage_range)
        except:
            logger.error(traceback.format_exc())
            return jsonify(success=False), 500
    return render_template("main/usage.html")


@main.post("/recharge-history")
@login_required
def recharge_history():
    try:
        data = request.get_json()
        month = int(data.get("month", datetime.utcnow().month))
        year = int(data.get("year", datetime.utcnow().year))
        records = Transaction.query.filter(
            extract("year", Transaction.created_at) == year,
            Transaction.user_id == current_user.id,
            Transaction.status == "completed",
        ).all()
        tx_records = [
            {"date": row.created_at.strftime("%d %b"), "amount": row.usd_value}
            for row in records
            if row.created_at.month == month
        ]
        return jsonify(records=tx_records)
    except:
        logger.error(traceback.format_exc())
        return jsonify(success=False), 500


# FAQ -----------------------------------------------
@main.post("/index-faq")
@login_required
@csrf.exempt
def get_faqs():
    try:
        data = request.get_json()
        action = data["action"]
        if action == "add":
            question = data["question"]
            answer = data["answer"]
            FAQ(question, answer, current_user.id)
            return jsonify(success=True)
        if action == "edit":
            faq_id = data["faq_id"]
            question = data["question"]
            answer = data["answer"]
            faq = FAQ.query.get(int(faq_id))
            faq.question = question
            faq.answer = answer
            faq.update()
            return jsonify(success=True)
        if action == "delete":
            faq_id = data["faq_id"]
            faq = FAQ.query.get(int(faq_id))
            faq.delete()
            return jsonify(success=True)
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify(success=False, error=str(e)), 500
