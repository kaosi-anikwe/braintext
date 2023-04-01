from flask import Blueprint, render_template

errors = Blueprint("errors", __name__)


@errors.app_errorhandler(400)
def bad_request(error):
    return render_template("errors/400.html"), 400


@errors.app_errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401


@errors.app_errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@errors.app_errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@errors.app_errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500
