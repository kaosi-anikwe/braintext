import os
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv
from app.models import OTP, get_otp
from flask_login import login_required, current_user
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for

load_dotenv()

def send_otp_message(otp: int, phone_no: str) -> str:
    message = client.messages.create(body=f'Here is your OTP for verifying your number on BrainText. {otp} \nIt will expire in 3 minutes.', from_='+14706196055', to=f'{phone_no}')
    print(message.sid)
    return message.sid

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)


main = Blueprint("main", __name__)

# Index ---------------------------------------------
@main.route("/")
def index():
    return render_template("index.html")

# User Account -----------------------------------------
@main.route("/profile")
@login_required
def profile():
    print(current_user.phone_no)
    settings = True if request.args.get("settings") else False
    return render_template("profile.html", settings=settings)

@main.route("/verify")
@login_required
def add_number():
    return render_template("add-number.html")


@main.route("/send-otp", methods=["POST"])
@login_required
def send_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
    if check_otp:
        check_otp.otp = get_otp()
        send_otp_message(check_otp.otp, phone_no)
        check_otp.update()

        return jsonify({"otp": check_otp.otp})

    otp = OTP(phone_no)
    send_otp_message(otp.otp, phone_no)
    otp.insert()

    return jsonify({"otp": otp.otp})


@main.route("/resend-otp", methods=["POST"])
@login_required
def resend_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    check_otp = OTP.query.filter(OTP.phone_no == phone_no).one_or_none()
    if check_otp:
        check_otp.otp = get_otp()
        send_otp_message(check_otp.otp, phone_no)
        check_otp.update()

        return jsonify({"otp": check_otp.otp})


@main.route("/verify-otp", methods=["POST"])
@login_required
def verify_otp():
    data = request.get_json()
    phone_no = data["phone_no"]

    check_otp = OTP.query.filter(OTP.phone_no == phone_no, OTP.verified == False).one_or_none()
    # if check_otp.updated_at:
    #     if (datetime.now() - check_otp.updated_at) >= 180:
    #         print((datetime.now() - check_otp.updated_at), "updated")
    #         check_otp.expired = True
    #         check_otp.update()

    #         return jsonify({"expired": True})
    # elif check_otp.created_at:
    #     if (datetime.now() - check_otp.created_at) >= 180:
    #         print((datetime.now() - check_otp.created_at), "created")
    #         check_otp.expired = True
    #         check_otp.update()

    #         return jsonify({"expired": True})
    
    print((datetime.now() - check_otp.created_at).seconds, "default")
    print((datetime.now() - check_otp.updated_at).seconds, "default")
    # current_user.phone_no = phone_no
    # current_user.update()
    flash("Phone number updated successfully", "success")
    return redirect(url_for("main.profile"))

    
