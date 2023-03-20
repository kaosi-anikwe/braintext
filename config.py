import os, secrets
from dotenv import load_dotenv

load_dotenv()

# define base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # key for CSF
    SECRET_KEY = os.environ.get("SECRET_KEY")
    # SECRET_KEY = secrets.token_hex(32)
    # sqlalchemy .db location (for sqlite)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # sqlalchemy track modifications in sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")
    # SECURITY_PASSWORD_SALT = secrets.token_hex(32)
    SMTP_SERVER = os.environ.get("SMTP_SERVER")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
    PASSWORD = os.environ.get("PASSWORD")
    # MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    # MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # ADMINS = ['email@email.com']
