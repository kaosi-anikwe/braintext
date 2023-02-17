from flask_login import login_required
from flask import Blueprint, render_template, request, flash

main = Blueprint("main", __name__)

# Index ---------------------------------------------
@main.route("/")
def index():
    return render_template("index.html")

# User Account -----------------------------------------
@main.route("/profile")
@login_required
def profile():
    settings = True if request.args.get("settings") else False
    return render_template("profile.html", settings=settings)

@main.route("/verify")
@login_required
def add_number():
    return render_template("add-number.html")
