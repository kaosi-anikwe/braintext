import os
import logging
from flask import Flask
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from config import Config
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

load_dotenv()

log_dir = os.getenv("CHATBOT_LOG")
tmp_folder = os.getenv("TEMP_FOLDER")
# create log folder if not exists
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# create tmp folder if not exists
if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
migrate = Migrate()

# configure logger
logging.basicConfig(
    filename=os.path.join("logs", "website", "debug.log"),
    level=logging.INFO,
    format="%(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("braintext")


def create_app(config=Config):
    app = Flask(__name__)

    app.config.from_object(config)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from app.main.routes import main
    from app.auth.routes import auth
    from app.errors.handlers import errors
    from app.payment.routes import payment
    from app.chatbot.chatbot import chatbot as meta_chabot
    from app.twilio_chatbot.chatbot import chatbot as twilio_chatbot
    from app.vonage_chatbot.chatbot import chatbot as vonage_chatbot

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)
    app.register_blueprint(payment)
    app.register_blueprint(meta_chabot)
    app.register_blueprint(twilio_chatbot)
    app.register_blueprint(vonage_chatbot)

    csrf.exempt(payment)
    csrf.exempt(meta_chabot)
    csrf.exempt(twilio_chatbot)
    csrf.exempt(vonage_chatbot)

    return app
