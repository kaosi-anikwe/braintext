import os, secrets
from dotenv import load_dotenv

load_dotenv()

# define base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # important directories
    BASE_DIR = os.getenv("BASE_DIR")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    CHATLOG_DIR = os.path.join(LOG_DIR, "chatbot")
    WEBHOOK_LOG = os.path.join(LOG_DIR, "webhooks")
    TEMP_FOLDER = os.path.join(BASE_DIR, "tmp")
    FILES = os.path.join(BASE_DIR, "files")
    # key for CSF
    SECRET_KEY = os.environ.get("SECRET_KEY")
    # sqlalchemy .db location (for sqlite)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    # sqlalchemy track modifications in sqlalchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")
    # mail
    SMTP_SERVER = os.environ.get("SMTP_SERVER")
    SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
    PASSWORD = os.environ.get("PASSWORD")
    # app
    HOSTNAME = os.environ.get("HOSTNAME")
    PREFERRED_URL_SCHEME = "https"
