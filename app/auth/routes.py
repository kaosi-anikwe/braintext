from app.models import Users
from werkzeug.urls import url_parse
from flask_login import login_user, current_user, logout_user
from flask import Blueprint, render_template, request, redirect, url_for

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return "<h1>Dashboard</h1>"
        return render_template("auth.html", title="Login", login=True)
    else:
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = Users.query.filter(Users.email==email).first()
        if not user or not user.check_password(password):
            return redirect(url_for("auth.login"))

        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = "<h1>Dashboard</h1>"
        # return redirect(next_page)
        return next_page

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            return "<h1>Dashboard</h1>"
        return render_template("auth.html", title="Sign up")

    else:
        first_name = request.form.get("firstname")
        last_name = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")

        new_user = Users(first_name, last_name, email, password)
        new_user.insert()        
        return redirect(url_for("auth.login"))

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
