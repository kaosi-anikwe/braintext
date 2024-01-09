import os
import time
import traceback
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import (
    Blueprint,
    request,
    render_template,
    redirect,
    url_for,
    jsonify,
    flash,
    json,
)
from flask_login import login_required, current_user
from app.models import Users, Transactions
from app.payment.functions import usd_exchange_rate
from app import logger


from rave_python import Rave
from rave_python.rave_ussd import Ussd

payment = Blueprint("payment", __name__)

load_dotenv()


USD2BT = int(os.getenv("USD2BT"))
RAVE_PUB_KEY = os.getenv("RAVE_PUBLIC_KEY")
RAVE_SEC_KEY = os.getenv("RAVE_SECRET_KEY")
LOG_DIR = os.getenv("LOG_DIR")
WEBHOOK_LOG = os.path.join(LOG_DIR, "webhooks")
BANK_CODES = {
    "Access Bank": "044",
    "Ecobank": "050",
    "Fidelity Bank": "070",
    "First Bank of Nigeria": "011",
    "FCMB (First City Monument Bank)": "214",
    "Guaranty Trust Bank": "058",
    "Heritage Bank": "030",
    "Keystone Bank": "082",
    "Stanbic IBTC Bank": "221",
    "Sterling Bank": "232",
    "Union Bank": "032",
    "United Bank for Africa (UBA)": "033",
    "Unity Bank": "215",
    "VFD Microfinance Bank": "090110",
    "Wema Bank": "035",
    "Zenith Bank": "057",
}
os.makedirs(WEBHOOK_LOG, exist_ok=True)


# Checkout --------------------------------------
@payment.route("/checkout/<package>")
@login_required
def checkout(package):
    pass
    # if not current_user.phone_no:
    #     flash("Please verify your WhatsApp number to proceed.")
    #     return redirect(url_for("main.profile"))
    # check_standard = (
    #     StandardSubscription.query.filter(
    #         StandardSubscription.user_id == current_user.id,
    #         StandardSubscription.payment_status == "pending",
    #     )
    #     .order_by(StandardSubscription.id.desc())
    #     .first()
    # )
    # check_premium = (
    #     PremiumSubscription.query.filter(
    #         PremiumSubscription.user_id == current_user.id,
    #         PremiumSubscription.payment_status == "pending",
    #     )
    #     .order_by(PremiumSubscription.id.desc())
    #     .first()
    # )
    # if not check_premium and not check_standard:
    #     tx_id = f"{current_user.uid}-{str(time.time()).split('.')[0]}"
    # elif check_standard:
    #     tx_id = check_standard.tx_ref.replace("stnrd-", "")
    # elif check_premium:
    #     tx_id = check_premium.tx_ref.replace("prmum-", "")
    # return render_template(
    #     "payment/checkout.html", package=package, tx_id=tx_id, title="Checkout"
    # )


# Create Transaction
@payment.post("/create-transaction")
@login_required
def create_transaction():
    pass
    # data = request.get_json()
    # tx_ref = data["tx_ref"]
    # if str(tx_ref).startswith("stnrd"):
    #     # create standard account instance if not found
    #     check_pending = (
    #         StandardSubscription.query.filter(
    #             StandardSubscription.payment_status == "pending",
    #             StandardSubscription.user_id == current_user.id,
    #         )
    #         .order_by(StandardSubscription.id.desc())
    #         .all()
    #     )
    #     if not check_pending:
    #         subscription = StandardSubscription(tx_ref, current_user.id)
    #         subscription.insert()
    #     logger.info(f"{tx_ref} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    # elif str(tx_ref).startswith("prmum"):
    #     # create premium account instance if not found
    #     check_pending = (
    #         PremiumSubscription.query.filter(
    #             PremiumSubscription.payment_status == "pending",
    #             PremiumSubscription.user_id == current_user.id,
    #         )
    #         .order_by(PremiumSubscription.id.desc())
    #         .all()
    #     )
    #     if not check_pending:
    #         subscription = PremiumSubscription(tx_ref, current_user.id)
    #         subscription.insert()
    #     logger.info(f"{tx_ref} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    # return jsonify({"success": True})


# Payment callback
@payment.route("/verify-payment")
@login_required
def payment_callback():
    pass
    # standard = False
    # premium = False
    # tx_ref = request.args.get("tx_ref")
    # # get transaction details from database
    # if str(tx_ref).startswith("stnrd"):
    #     subscription = (
    #         StandardSubscription.query.filter(
    #             StandardSubscription.tx_ref == tx_ref,
    #             StandardSubscription.payment_status == "pending",
    #             StandardSubscription.user_id == current_user.id,
    #         )
    #         .order_by(StandardSubscription.id.desc())
    #         .first()
    #     )
    #     standard = True if subscription else False
    # elif str(tx_ref).startswith("prmum"):
    #     subscription = (
    #         PremiumSubscription.query.filter(
    #             PremiumSubscription.tx_ref == tx_ref,
    #             PremiumSubscription.payment_status == "pending",
    #             PremiumSubscription.user_id == current_user.id,
    #         )
    #         .order_by(PremiumSubscription.id.desc())
    #         .first()
    #     )
    #     premium = True if subscription else False
    # # get transaction status
    # if standard or premium:  # transaction found
    #     if request.args.get("status") == "cancelled":
    #         # update record as cancelled
    #         subscription.payment_status = "cancelled"
    #         subscription.update()
    #         logger.info(
    #             f"Payment cancelled - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    #         )
    #         return redirect(url_for("main.profile"))
    #     elif request.args.get("status") != "cancelled":
    #         transaction_id = request.args.get("transaction_id")
    #         verify_url = f"https://api.flutterwave.com/v3/transactions/{int(transaction_id)}/verify"
    #         try:
    #             # verify transaction
    #             response = requests.get(
    #                 verify_url,
    #                 headers={
    #                     "Content-Type": "application/json",
    #                     "Authorization": f"Bearer {flw_sec_key}",
    #                 },
    #             )
    #             if response.status_code == 200:
    #                 data = response.json()
    #                 if data["status"] == "success":
    #                     # update record as successful
    #                     flw_ref = data["data"]["flw_ref"]
    #                     subscription.flw_ref = flw_ref
    #                     subscription.payment_status = "completed"
    #                     subscription.sub_status = "active"
    #                     subscription.tx_id = transaction_id
    #                     # expiry date is the current day of the next month
    #                     subscription.expire_date = (
    #                         current_user.timenow().replace(day=1) + timedelta(days=32)
    #                     ).replace(day=datetime.utcnow().day)
    #                     # localize time
    #                     subscription.expire_date = subscription.expire_date.replace(
    #                         tzinfo=current_user.get_timezone()
    #                     )
    #                     subscription.update()

    #                     # check for existing subscriptions and update user account
    #                     if standard:
    #                         old_sub = (
    #                             PremiumSubscription.query.filter(
    #                                 PremiumSubscription.sub_status == "active",
    #                                 PremiumSubscription.user_id == current_user.id,
    #                             )
    #                             .order_by(PremiumSubscription.id.desc())
    #                             .first()
    #                         )
    #                         if old_sub:
    #                             if not old_sub.expired():
    #                                 old_sub.upgrade()
    #                         current_user.account_type = "Standard"
    #                         current_user.update()
    #                         # send thank you message
    #                         message = "*Thank you for upgrading your account!*\nYour Standard account has been activated.\nCheck your account settings to adjust preferences.\nhttps://braintext.io/profile?settings=True"
    #                         send_text(
    #                             message=message,
    #                             recipient=current_user.phone_no,
    #                         )
    #                     if premium:
    #                         old_sub = (
    #                             StandardSubscription.query.filter(
    #                                 StandardSubscription.sub_status == "active",
    #                                 StandardSubscription.user_id == current_user.id,
    #                             )
    #                             .order_by(StandardSubscription.id.desc())
    #                             .first()
    #                         )
    #                         if old_sub:
    #                             if not old_sub.expired():
    #                                 old_sub.upgrade()
    #                         current_user.account_type = "Premium"
    #                         current_user.update()
    #                         # send thank you message
    #                         message = "*Thank you for upgrading your account!*\nYour account has been fully activated.\nCheck your account settings to adjust preferences.\nhttps://braintext.io/profile?settings=True"
    #                         send_text(
    #                             message=message,
    #                             recipient=current_user.phone_no,
    #                         )

    #                     logger.info(
    #                         f"Payment successful - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    #                     )
    #                     return render_template("thanks/thanks.html", premium=premium)
    #             else:
    #                 # update record as failed
    #                 subscription.payment_status = "failed"
    #                 subscription.update()
    #                 return redirect(url_for("main.profile"))
    #         except:
    #             logger.error(traceback.format_exc())
    #             # update record as error
    #             subscription.payment_status = "error"
    #             subscription.update()
    #             logger.info(
    #                 f"Payment Failed - {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
    #             )
    #             flash("Your payment failed. Please contact support", "danger")
    #             return redirect(url_for("main.profile"))
    # else:
    #     flash("Thank you for upgrading your account!", "success")
    #     return redirect(url_for("main.profile"))


# Payment webhook
@payment.route("/verify-payment-webhook", methods=["GET", "POST"])
def payment_webhook():
    if request.headers.get("verif-hash") == RAVE_SEC_KEY:
        try:
            from ..chatbot.functions import send_text

            payload = request.get_json()

            # create directory for each day
            directory = os.path.join(
                WEBHOOK_LOG, datetime.utcnow().strftime("%d-%m-%Y")
            )
            os.makedirs(directory, exist_ok=True)
            log_file = os.path.join(
                directory, f"{datetime.utcnow().strftime('%H:%M:%S')}.json"
            )
            with open(log_file, "w") as file:
                json.dump(payload, file)

            # get transaction/user details from payload
            status = payload["data"]["status"]
            tx_ref = payload["data"]["tx_ref"]
            flw_tx_id = payload["data"]["id"]
            flw_tx_ref = payload["data"]["flw_ref"]
            user_uid = str(tx_ref).split("-")[1]
            user = Users.query.filter(Users.uid == user_uid).one_or_none()

            if user:
                # get transaction details from database
                tx = Transactions.query.filter(
                    Transactions.tx_ref == tx_ref,
                    Transactions.flw_tx_id == flw_tx_id,
                    Transactions.flw_tx_ref == flw_tx_ref,
                    Transactions.user_id == user.id,
                ).one_or_none()
                if tx:  # transaction found
                    # get transaction status
                    if status == "successful":
                        verify_url = f"https://api.flutterwave.com/v3/transactions/{int(flw_tx_id)}/verify"
                        try:
                            # verify transaction
                            response = requests.get(
                                verify_url,
                                headers={
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {RAVE_SEC_KEY}",
                                },
                            )
                            if response.status_code == 200:
                                data = response.json()
                                if data["status"] == "success":
                                    # update record as successful
                                    if (
                                        tx.status != "completed"
                                    ):  # transaction was pending
                                        amount = payload["data"]["amount"]
                                        currency = payload["data"]["currency"]
                                        usd_value = round(
                                            amount / usd_exchange_rate(currency), 2
                                        )
                                        tx.amount = amount
                                        tx.currency = currency
                                        tx.usd_value = usd_value
                                        tx.status = "completed"
                                        tx.update()
                                        # add to user balance
                                        bt_value = usd_value * USD2BT
                                        user.balance += bt_value
                                        user.update()
                                        logger.info(
                                            f"ADDED {bt_value} TO USER #{user.id}. BALANCE is {user.balance}"
                                        )
                                        if not tx.notified:
                                            # inform user
                                            text = f"Account recharge of {bt_value}BT was successful. Thank you for using BrainText 💙"
                                            send_text(text, user.phone_no)
                                            tx.notified = True
                                            tx.update()
                                    elif tx.status == "completed":
                                        logger.info(
                                            f"TX #{tx.flw_tx_id} ALREADY VERIFIED"
                                        )

                                    return jsonify({"success": True}), 200
                                else:
                                    tx.status = data["status"]
                                    tx.update()
                                    if not tx.notified:
                                        # inform user
                                        text = f"Your attempt to recharge your account failed. Please try again later. Thank you for using BrainText 💙"
                                        send_text(text, user.phone_no)
                                        tx.notified = True
                                        tx.update()
                                    return jsonify({"success": False}), 417
                            else:
                                # update record as failed
                                tx.status = "failed"
                                tx.update()
                                if not tx.notified:
                                    # inform user
                                    text = f"Your attempt to recharge your account failed. Please try again later. Thank you for using BrainText 💙"
                                    send_text(text, user.phone_no)
                                    tx.notified = True
                                    tx.update()
                                return jsonify({"success": False}), 417
                        except:
                            logger.error(traceback.format_exc())
                            # update record as error
                            tx.status = "error"
                            tx.update()
                            if not tx.notified:
                                # inform user
                                text = f"Your attempt to recharge your account failed. Please try again later. Thank you for using BrainText 💙"
                                send_text(text, user.phone_no)
                                tx.notified = True
                                tx.update()
                            return jsonify({"success": False}), 500
                    else:
                        tx.status = status
                        tx.update()
                        if not tx.notified:
                            # inform user
                            text = f"Your attempt to recharge your account failed. Please try again later. Thank you for using BrainText 💙"
                            send_text(text, user.phone_no)
                            tx.notified = True
                            tx.update()
                        return jsonify({"success": False}), 417
                else:
                    return jsonify({"success": False}), 404
            else:
                return jsonify({"success": False}), 404
        except:
            logger.error(traceback.format_exc())
            # update record as error
            tx.status = "error"
            tx.update()
            return jsonify({"success": False}), 500

    else:
        return jsonify({"success": False}), 401
