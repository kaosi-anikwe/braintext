import os
import time
import traceback
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Blueprint, request, render_template, redirect, url_for, jsonify, flash
from flask_login import login_required, current_user
from app.models import StandardSubscription, PremiumSubscription, Users
from app.chatbot.chatbot import send_whatspp_message


payment = Blueprint("payment", __name__)

load_dotenv()

flw_pub_key = os.getenv("RAVE_PUBLIC_KEY")
flw_sec_key = os.getenv("RAVE_SECRET_KEY")


# Checkout --------------------------------------
@payment.route("/checkout/<package>")
@login_required
def checkout(package):
    if not current_user.phone_no:
        flash("Please verify your WhatsApp number to proceed.")
        return redirect(url_for("main.profile"))
    check_standard = StandardSubscription.query.filter(
        StandardSubscription.user_id == current_user.id,
        StandardSubscription.payment_status == "pending",
    ).one_or_none()
    check_premium = PremiumSubscription.query.filter(
        PremiumSubscription.user_id == current_user.id,
        PremiumSubscription.payment_status == "pending",
    ).one_or_none()
    if not check_premium and not check_standard:
        tx_id = f"{current_user.uid}-{str(time.time()).split('.')[0]}"
    elif check_standard:
        tx_id = check_standard.tx_ref.replace("stnrd-", "")
    elif check_premium:
        tx_id = check_premium.tx_ref.replace("prmum-", "")
    return render_template("payment/checkout.html", package=package, tx_id=tx_id, title="Checkout")


# Create Transaction
@payment.post("/create-transaction")
@login_required
def create_transaction():
    data = request.get_json()
    tx_ref = data["tx_ref"]
    if str(tx_ref).startswith("stnrd"):
        # create standard account instance if not found
        check_pending = StandardSubscription.query.filter(
            StandardSubscription.payment_status == "pending",
            StandardSubscription.user_id == current_user.id,
        ).one_or_none()
        if not check_pending:
            subscription = StandardSubscription(tx_ref, current_user.id)
            subscription.insert()
        print(f"{tx_ref} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    elif str(tx_ref).startswith("prmum"):
        # create premium account instance if not found
        check_pending = PremiumSubscription.query.filter(
            PremiumSubscription.payment_status == "pending",
            PremiumSubscription.user_id == current_user.id,
        ).one_or_none()
        if not check_pending:
            subscription = PremiumSubscription(tx_ref, current_user.id)
            subscription.insert()
        print(f"{tx_ref} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    return jsonify({"success": True})


# Payment callback
@payment.route("/verify-payment")
def payment_callback():
    standard = False
    premium = False
    tx_ref = request.args.get("tx_ref")
    # get transaction details from database
    if str(tx_ref).startswith("stnrd"):
        subscription = StandardSubscription.query.filter(
            StandardSubscription.tx_ref == tx_ref,
            StandardSubscription.payment_status == "pending",
            StandardSubscription.user_id == current_user.id,
        ).one_or_none()
        standard = True
    elif str(tx_ref).startswith("prmum"):
        subscription = PremiumSubscription.query.filter(
            PremiumSubscription.tx_ref == tx_ref,
            PremiumSubscription.payment_status == "pending",
            PremiumSubscription.user_id == current_user.id,
        ).one_or_none()
        premium = True
    # get transaction status
    if request.args.get("status") == "cancelled":
        # update record as cancelled
        subscription.payment_status = "cancelled"
        subscription.update()
        print(f"Payment cancelled - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        return redirect(url_for("main.profile"))
    elif request.args.get("status") == "successful":
        transaction_id = request.args.get("transaction_id")
        verify_url = (
            f"https://api.flutterwave.com/v3/transactions/{int(transaction_id)}/verify"
        )
        try:
            # verify transaction
            response = requests.get(
                verify_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {flw_sec_key}",
                },
            )
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    # update record as successful
                    flw_ref = data["data"]["flw_ref"]
                    subscription.flw_ref = flw_ref
                    subscription.payment_status = "completed"
                    subscription.sub_status = "active"
                    subscription.tx_id = transaction_id
                    # expiry date is the current day of the next month
                    subscription.expire_date = (
                        current_user.timenow().replace(day=1) + timedelta(days=32)
                    ).replace(day=datetime.utcnow().day)
                    # localize time
                    subscription.expire_date = subscription.expire_date.replace(
                        tzinfo=current_user.get_timezone()
                    )
                    subscription.update()

                    # check for existing subscriptions and update user account
                    if standard:
                        old_sub = PremiumSubscription.query.filter(
                            PremiumSubscription.sub_status == "active",
                            PremiumSubscription.user_id == current_user.id,
                        ).one_or_none()
                        if old_sub:
                            if not old_sub.expired():
                                old_sub.upgrade()
                        current_user.account_type = "Standard"
                        current_user.update()
                        # send thank you message
                        message = "*Thank you for upgrading your account!*\nYour Standard account has been activated.\nCheck your account settings to adjust preferences.\nhttps://braintext.io/profile?settings=True"
                        send_whatspp_message(
                            message=message, phone_no=current_user.phone_no
                        )
                    if premium:
                        old_sub = StandardSubscription.query.filter(
                            StandardSubscription.sub_status == "active",
                            StandardSubscription.user_id == current_user.id,
                        ).one_or_none()
                        if old_sub:
                            if not old_sub.expired():
                                old_sub.upgrade()
                        current_user.account_type = "Premium"
                        current_user.update()
                        # send thank you message
                        message = "*Thank you for upgrading your account!*\nYour account has been fully activated.\nCheck your account settings to adjust preferences.\nhttps://braintext.io/profile?settings=True"
                        send_whatspp_message(
                            message=message, phone_no=current_user.phone_no
                        )

                    print(
                        f"Payment successful - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                    return render_template("thanks/thanks.html", premium=premium)
            else:
                # update record as failed
                subscription.payment_status = "failed"
                subscription.update()
                return redirect(url_for("main.profile"))
        except Exception as e:
            traceback.format_exc()
            # update record as error
            subscription.payment_status = "error"
            subscription.update()
            print(f"Payment Failed - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
            return redirect(url_for("main.profile"))


# Payment webhook
@payment.route("/verify-payment-webhook", methods=["GET", "POST"])
def payment_webhook():
    if request.headers.get("verif-hash") == flw_sec_key:
        standard = False
        premium = False
        payload = request.get_json()

        import json

        # create directory for each day
        directory = f"logs/webhooks/{datetime.utcnow().strftime('%d-%m-%Y')}"
        if not os.path.exists(directory):
            os.mkdir(directory)
        with open(
            f"{directory}/{str(datetime.utcnow().strftime('%d-%m-%Y_%H:%M:%S'))}.json",
            "w",
        ) as file:
            json.dump(payload, file)

        # get transaction/user details from payload
        tx_ref = payload["data"]["tx_ref"]
        status = payload["data"]["status"]
        transaction_id = int(payload["data"]["id"])
        user_uid = str(tx_ref).split("-")[1]
        user = Users.query.filter(Users.uid == user_uid).one_or_none()

        if user:
            # get transaction details from database
            if str(tx_ref).startswith("stnrd"):
                subscription = StandardSubscription.query.filter(
                    StandardSubscription.tx_ref == tx_ref,
                    StandardSubscription.user_id == user.id,
                ).one_or_none()
                standard = True if subscription else False
            elif str(tx_ref).startswith("prmum"):
                subscription = PremiumSubscription.query.filter(
                    PremiumSubscription.tx_ref == tx_ref,
                    PremiumSubscription.user_id == user.id,
                ).one_or_none()
                premium = True if subscription else False
            if standard or premium:  # transaction found
                # get transaction status
                if status == "successful":
                    verify_url = f"https://api.flutterwave.com/v3/transactions/{int(transaction_id)}/verify"
                    try:
                        # verify transaction
                        response = requests.get(
                            verify_url,
                            headers={
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {flw_sec_key}",
                            },
                        )
                        if response.status_code == 200:
                            data = response.json()
                            if data["status"] == "success":
                                # update record as successful
                                if (
                                    subscription.payment_status != "completed"
                                ):  # transaction was pending
                                    flw_ref = data["data"]["flw_ref"]
                                    subscription.flw_ref = flw_ref
                                    subscription.tx_id = transaction_id
                                    subscription.payment_status = "completed"
                                    subscription.sub_status = "active"
                                    # expiry date is the current day of the next month
                                    subscription.expire_date = (
                                        user.timenow().replace(day=1)
                                        + timedelta(days=32)
                                    ).replace(day=datetime.utcnow().day)
                                    subscription.update()
                                    # TODO: send thank you email
                                elif (
                                    subscription.payment_status == "completed"
                                    and subscription.tx_id != transaction_id
                                ):  # subcription renewal
                                    # expiry date is the current day of the next month
                                    subscription.expire_date = (
                                        datetime.utcnow().replace(day=1)
                                        + timedelta(days=32)
                                    ).replace(day=datetime.utcnow().day)
                                    subscription.expire_date.replace(
                                        tzinfo=user.timezone
                                    )
                                    subscription.update()
                                    # TODO: send thank you email

                                # check for existing subscriptions and update user account
                                if standard:
                                    old_sub = PremiumSubscription.query.filter(
                                        PremiumSubscription.sub_status == "active",
                                        PremiumSubscription.user_id == user.id,
                                    ).one_or_none()
                                    if old_sub:
                                        if not old_sub.expired():
                                            old_sub.upgrade()
                                    user.account_type = "Standard"
                                    user.update()
                                if premium:
                                    old_sub = StandardSubscription.query.filter(
                                        StandardSubscription.sub_status == "active",
                                        StandardSubscription.user_id == user.id,
                                    ).one_or_none()
                                    if old_sub:
                                        if not old_sub.expired():
                                            old_sub.upgrade()
                                    user.account_type = "Premium"
                                    user.update()

                                return jsonify({"success": True}), 200
                        else:
                            # update record as failed
                            subscription.payment_status = "failed"
                            subscription.update()
                            return jsonify({"success": False}), 417
                    except Exception as e:
                        traceback.format_exc()
                        # update record as error
                        subscription.payment_status = "error"
                        subscription.update()
                        return jsonify({"success": False}), 500
            else:
                return jsonify({"success": False}), 404
        else:
            return jsonify({"success": False}), 404
    else:
        return jsonify({"success": False}), 401