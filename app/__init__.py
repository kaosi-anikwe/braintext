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

chatlog_dir = os.getenv("CHATBOT_LOG")
log_dir = os.getenv("LOG_DIR")
tmp_folder = os.getenv("TEMP_FOLDER")

# create folder if not exists
os.makedirs(chatlog_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)
os.makedirs(tmp_folder, exist_ok=True)

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
migrate = Migrate()

# configure logger
logging.basicConfig(
    filename=os.path.join(log_dir, "website", "debug.log"),
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

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)
    app.register_blueprint(payment)
    app.register_blueprint(meta_chabot)

    csrf.exempt(payment)
    csrf.exempt(meta_chabot)

    return app
