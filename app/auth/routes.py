from app.models import Users, BasicSubscription
from flask_login import login_user, current_user, logout_user
from flask import Blueprint, render_template, request, redirect, url_for, flash

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("main.profile"))
        return render_template(
            "auth/auth.html", title="Login", login=True, next=request.args.get("next")
        )
    else:
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter(Users.email == email).first()
        if not user or not user.check_password(password):
            flash("Invalid username or password.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        next_page = request.args.get("next")
        if next_page != "None":
            print(next_page)
            flash("You are now signed in!", "success")
            return redirect(next_page)
        else:
            flash("You are now signed in!", "success")
            return redirect(url_for("main.profile"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("main.profile"))
        return render_template("auth/auth.html", title="Sign up")

    else:
        first_name = request.form.get("firstname")
        last_name = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")

        check = Users.query.filter(Users.email == email).first()
        if check:
            flash(
                "An account already exists with this email. Please use a different email to sign up",
                "danger",
            )
            return redirect(url_for("auth.register"))

        new_user = Users(first_name, last_name, email, password)
        new_user.insert()
        basic_sub = BasicSubscription(new_user.id)
        basic_sub.insert()
        flash(
            "Your account has been created successfully! Please proceed to login.",
            "success",
        )
        return redirect(url_for("auth.login"))


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))
