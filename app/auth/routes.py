from flask import Blueprint, render_template

auth = Blueprint("auth", __name__)

@auth.route("/login")
def login():
    return render_template("auth.html", login=True)

@auth.route("/register")
def register():
    return render_template("auth.html")
