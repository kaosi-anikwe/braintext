from flask import Blueprint, render_template

payment = Blueprint("payment", __name__)

# Checkout --------------------------------------
# TODO: Make seperate blueprint to improve security
@payment.route("/checkout")
def checkout():
    return render_template("payment/checkout.html")
    