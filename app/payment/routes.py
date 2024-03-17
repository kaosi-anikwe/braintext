# python imports
import os
import time
import traceback
from datetime import datetime


# installed imports
import requests
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

# local imports
from app import logger
from app.models import Users, Transactions
from flask_login import login_required, current_user
from app.payment.functions import exchange_rates, generate_tx_ref


payment = Blueprint("payment", __name__)

load_dotenv()


USD2BT = int(os.getenv("USD2BT"))
RAVE_PUB_KEY = os.getenv("RAVE_PUBLIC_KEY")
RAVE_SEC_KEY = os.getenv("RAVE_SECRET_KEY")
LOG_DIR = os.getenv("LOG_DIR")
WEBHOOK_LOG = os.path.join(LOG_DIR, "webhooks")
BANK_CODES = {
    "Access Bank": "044",
    "First Bank of Nigeria": "011",
    "Fidelity Bank": "070",
    "FCMB": "214",
    "Guaranty Trust Bank": "058",
    "UBA": "033",
    "Zenith Bank": "057",
    "Wema Bank": "035",
    "Stanbic IBTC Bank": "221",
    "Ecobank": "050",
    "Keystone Bank": "082",
    "Union Bank": "032",
    "Unity Bank": "215",
    "Sterling Bank": "232",
    "Heritage Bank": "030",
    "VFD Microfinance Bank": "090110",
}
os.makedirs(WEBHOOK_LOG, exist_ok=True)


# Pricing page ----------------------------------
@payment.get("/pricing")
def pricing():
    return render_template("payment/pricing.html", title="Pricing")


# Checkout --------------------------------------
@payment.route("/recharge")
@login_required
def recharge():
    if not current_user.phone_no:
        flash("Please verify your WhatsApp number to proceed.")
        return redirect(url_for("main.profile"))

    return render_template(
        "payment/recharge.html",
        amount=request.args.get("amount"),
        title="Recharge Account",
    )


# Get current rates
@payment.get("/rates")
@login_required
def get_rates():
    try:
        # TODO: add other currencies
        return {"rates": {"USD": exchange_rates("USD")}}
    except:
        logger.error(traceback.format_exc())
        return jsonify(success=False), 500


# Create Transaction
@payment.post("/tx_ref")
@login_required
def create_transaction():
    try:
        data = request.get_json()
        user_uid = data["user_id"]
        amount = data["amount"]
        currency = data["currency"]
        logger.info(
            f"Generating tx_ref for user: {user_uid}, amount: {amount}, currency: {currency}"
        )
        tx_ref = generate_tx_ref("web", user_uid)
        logger.info(f"TX REF: {tx_ref}")
        return jsonify(tx_ref=tx_ref)
    except:
        logger.error(traceback.format_exc())
        return jsonify(success=False), 500


# Payment callback
@payment.route("/verify-payment")
@login_required
def payment_callback():
    from ..chatbot.functions import send_text

    message = "Your payment failed, please contact support."
    try:
        payload = request.args
        # get transaction details from payload
        status = payload.get("status")
        tx_ref = payload.get("tx_ref")
        flw_tx_id = payload.get("transaction_id")

        tx = Transactions.query.filter(
            Transactions.tx_ref == tx_ref,
        ).one_or_none()
        if not tx:  # new transaction
            # get transaction status
            if status == "completed" or status == "successful":
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
                        # create transaction
                        flw_tx_ref = data["data"]["flw_ref"]
                        amount = data["data"]["amount"]
                        currency = data["data"]["currency"]
                        user_id = data["data"]["meta"]["user_id"]
                        bt_amount = float(data["data"]["meta"]["bt_amount"])
                        user = Users.query.filter(Users.uid == user_id).one_or_none()
                        tx = Transactions(
                            message="",
                            mode="web",
                            amount=amount,
                            tx_ref=tx_ref,
                            flw_tx_id=flw_tx_id,
                            flw_tx_ref=flw_tx_ref,
                            user_id=user.id,
                            currency=currency,
                        )
                        tx.insert()
                        if data["status"] == "success":
                            # update record as successful
                            tx.status = "completed"
                            tx.usd_value = bt_amount
                            tx.update()
                            # update user balance
                            user.balance += bt_amount
                            user.update()
                            logger.info(
                                f"ADDED {bt_amount} TO USER #{user.id}. BALANCE is {user.balance}"
                            )
                            if not tx.notified:
                                # inform user
                                text = f"Account recharge of {bt_amount} BT was successful. Thank you for using BrainText 💙"
                                send_text(text, user.phone_no)
                                tx.notified = True
                                tx.update()

                            message = "Thank you for completing the payment ❤️✨"
                            flash(message, "success")
                            return redirect(url_for("main.profile"))
                        else:
                            tx.status = data["status"]
                            tx.update()
                            if not tx.notified:
                                # inform user
                                text = f"Your attempt to recharge your account failed. Please try again later. Thank you for using BrainText 💙"
                                send_text(text, user.phone_no)
                                tx.notified = True
                                tx.update()

                            flash(message, "danger")
                            return redirect(url_for("main.profile"))
                    else:
                        logger.info(
                            f"Failed to verify transaction. Response: {response.status_code}"
                        )
                        flash(message, "danger")
                        return redirect(url_for("main.profile"))
                except:
                    logger.error(traceback.format_exc())
                    flash(message, "danger")
                    return redirect(url_for("main.profile"))
            else:
                logger.info("Payment was not completed successfully")
                flash(message, "danger")
                return redirect(url_for("main.profile"))
        else:
            # transaction already exists
            logger.info(f"PAYMENT ALREADY VERIFIED: {tx_ref}. STATUS: {tx.status}")
            if tx.status == "completed" or tx.status == "successful":
                message = "Thank you for completing the payment ❤️✨"
            flash(message, "success")
            return redirect(url_for("main.profile"))
    except:
        logger.error(traceback.format_exc())
        flash(message, "danger")
        return redirect(url_for("main.profile"))


# Payment webhook
@payment.route("/verify-payment-webhook", methods=["GET", "POST"])
def payment_webhook():
    if request.headers.get("verif-hash") == RAVE_SEC_KEY:
        time.sleep(5)
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

            tx = Transactions.query.filter(
                Transactions.tx_ref == tx_ref,
            ).one_or_none()
            if not tx:  # new transaction
                # get transaction status
                if status == "completed" or status == "successful":
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
                            # create transaction
                            flw_tx_ref = data["data"]["flw_ref"]
                            amount = data["data"]["amount"]
                            currency = data["data"]["currency"]
                            user_id = data["data"]["meta"]["user_id"]
                            bt_amount = float(data["data"]["meta"]["bt_amount"])
                            user = Users.query.filter(
                                Users.uid == user_id
                            ).one_or_none()

                            tx = Transactions(
                                message="",
                                mode="web",
                                amount=amount,
                                tx_ref=tx_ref,
                                flw_tx_id=flw_tx_id,
                                flw_tx_ref=flw_tx_ref,
                                user_id=user.id,
                                currency=currency,
                            )
                            tx.insert()
                            if data["status"] == "success":
                                # update record as successful
                                tx.status = "completed"
                                tx.usd_value = bt_amount
                                tx.update()
                                # update user balance
                                user.balance += bt_amount
                                user.update()
                                logger.info(
                                    f"ADDED {bt_amount} TO USER #{user.id}. BALANCE is {user.balance}"
                                )
                                if not tx.notified:
                                    # inform user
                                    text = f"Account recharge of {bt_amount} BT was successful. Thank you for using BrainText 💙"
                                    send_text(text, user.phone_no)
                                    tx.notified = True
                                    tx.update()

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
                        else:
                            logger.info(
                                f"Failed to verify transaction. Response: {response.status_code}"
                            )
                            return jsonify({"success": False}), 417
                    except:
                        logger.error(traceback.format_exc())
                        return jsonify({"success": False}), 500
                else:
                    logger.info("Payment was not completed successfully")
                    return jsonify({"success": False}), 417
            else:
                # transaction already exists
                logger.info(f"PAYMENT ALREADY VERIFIED: {tx_ref}. STATUS: {tx.status}")
                return jsonify({"success": True}), 200
        except:
            logger.error(traceback.format_exc())
            return jsonify({"success": False}), 500
    else:
        logger.info(
            f"Verif header: {request.headers.get('verif-hash')} doesn't match SEC KEY"
        )
        return jsonify({"success": False}), 401
