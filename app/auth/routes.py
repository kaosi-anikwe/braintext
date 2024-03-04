# python imports
from datetime import datetime
import traceback

# installed imports
from flask_login import login_user, current_user, logout_user, login_required
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

# local imports
from app import db, csrf, logger
from app.modules.verification import confirm_token
from app.modules.functions import send_text
from app.models import Users, UserSettings
from app.modules.email_utility import (
    send_registration_email,
    send_forgot_password_email,
)

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("main.profile"))
        return render_template(
            "auth/auth.html",
            title="Login",
            login=True,
            next=request.args.get("next") or None,
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
        text = "You are now signed in!"
        if not user.phone_no:
            text += " Please add your phone number."
        if next_page:
            flash(text, "success")
            return redirect(next_page)
        else:
            flash(text, "success")
            return redirect(url_for("main.profile"))


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("main.profile"))
        return render_template("auth/auth.html", title="Sign up")

    else:
        first_name = request.form.get("firstname").strip()
        last_name = request.form.get("lastname").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        get_browser_time = request.form.get("time").split()[:5]

        check = Users.query.filter(Users.email == email).first()
        if check:
            flash(
                "An account already exists with this email. Please use a different email to sign up",
                "danger",
            )
            return redirect(url_for("auth.register"))

        # get user local time
        browser_time = ""
        for i in get_browser_time:
            browser_time += f"{i} "
        browser_time = datetime.strptime(browser_time.strip(), "%a %b %d %Y %H:%M:%S")
        timezone_offset = round((browser_time - datetime.utcnow()).seconds, -2)

        # create user class instance / database record
        new_user = Users(first_name, last_name, email, password, timezone_offset)
        new_user.insert()
        # create user setting instance / database record
        user_settings = UserSettings(new_user.id)
        user_settings.insert()

        send_registration_email(new_user)
        message = f"New website sign up from {new_user.display_name()}.\nNumber: {new_user.phone_no}"
        send_text(message=message, recipient="+2349016456964")

        flash(
            "Your account has been created successfully! Please proceed to login.",
            "success",
        )
        return redirect(url_for("auth.login"))


@auth.post("/edit-profile")
@login_required
def edit_profile():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    phone_no = request.form.get("phone_no")
    email = request.form.get("email")

    try:
        first_name_edited = current_user.first_name != first_name
        last_name_edited = current_user.last_name != last_name
        phone_no_edited = current_user.phone_no != phone_no
        email_edited = current_user.email != email

        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        if current_user.phone_no != phone_no:
            current_user.phone_no = phone_no
            current_user.phone_verified = False

        current_user.edited = (
            True
            if first_name_edited or last_name_edited or phone_no_edited or email_edited
            else False
        )
        # TODO: Send update email
        current_user.update()

        flash("Profile updated successfully!", "success")
        return redirect(url_for("main.profile"))
    except:
        logger.error(traceback.format_exc())
        db.session.rollback()

        flash("Failed to update profile. Please try again later.", "danger")
        return redirect(url_for("main.profile"))


@auth.post("/edit-settings")
@login_required
def edit_settings():
    notify_on_profile_change = request.form.get("notify_on_profile_change")
    product_updates = request.form.get("product_updates")
    subscription_expiry = request.form.get("subscription_expiry")
    ai_voice_type = request.form.get("ai_voice_type") or "Joanna"
    voice_respnse = request.form.get("voice_response")

    try:
        user_settings = UserSettings.query.filter(
            UserSettings.user_id == current_user.id
        ).one()
        user_settings.notify_on_profile_change = (
            True if notify_on_profile_change else False
        )
        user_settings.product_updates = True if product_updates else False
        user_settings.subscription_expiry = True if subscription_expiry else False
        user_settings.ai_voice_type = ai_voice_type if ai_voice_type else "Joanna"
        user_settings.voice_response = True if voice_respnse else False

        user_settings.update()
        flash("Account settings updated successfully!", "success")
        return redirect(f"{url_for('main.profile')}?settings=True")
    except:
        logger.error(traceback.format_exc())
        flash("Failed to update account settings. Please try again later.", "danger")
        return redirect(f"{url_for('main.profile')}?settings=True")


# Confirm email
@auth.route("/confirm/<token>")
def confirm_email(token):
    logout_user()
    try:
        email = confirm_token(token)
        if email:
            user = Users.query.filter(Users.email == email).one()
            if user:
                user.email_verified = True
                user.update()
                return render_template("thanks/verify-email.html", success=True)
        else:
            return render_template("thanks/verify-email.html", success=False)
    except:
        logger.error(traceback.format_exc())
        return render_template("thanks/verify-email.html", success=False)


# Send verification email
@auth.get("/send-verification-email")
@login_required
def verification_email():
    try:
        if send_registration_email(current_user):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False}), 500
    except:
        logger.error(traceback.format_exc())
        return jsonify({"success": False}), 500


# Change password
@auth.route("/change-password/<token>")
def change_password(token):
    email = confirm_token(token)
    logout_user()
    if email:
        return render_template(
            "auth/update_password.html", email=email, title="Change password"
        )
    else:
        return render_template(
            "thanks/password_change.html", success=False, title="Change password"
        )


# Forgot password
@auth.post("/forgot-password")
def forgot_password():
    email = request.form.get("email")
    user = Users.query.filter(Users.email == email).one_or_none()
    if user:
        try:
            send = send_forgot_password_email(user)
            if send:
                flash("Follow the link we sent to reset your password.", "success")
                return render_template("auth/auth.html")
            flash(
                "There was an error sending the email please try again later.", "danger"
            )
            return render_template("auth/auth.html")
        except:
            flash(
                "There was an error sending the email, please try again later.",
                "danger",
            )
            return render_template("auth/auth.html")
    flash("Your account was not found. Please proceed to create an account.", "danger")
    return render_template("auth/auth.html")


@auth.post("/confirm-new-password")
@csrf.exempt
def confirm_new_password():
    try:
        email = request.form.get("email")
        password = request.form.get("password")

        user = Users.query.filter(Users.email == email).one_or_none()
        if user:
            user.password_hash = user.get_password_hash(password)
            user.update()

            return render_template("thanks/password_change.html", success=True)
        else:
            return render_template("thanks/password_change.html", success=False)
    except:
        logger.error(traceback.format_exc())
        return render_template("thanks/password_change.html", success=False)


@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))
