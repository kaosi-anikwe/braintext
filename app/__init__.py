# python imports
import os
import logging
from logging.handlers import RotatingFileHandler

# installed imports
from flask import Flask
from dotenv import load_dotenv
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# local imports
from config import Config

load_dotenv()

base_dir = os.getenv("BASE_DIR")
log_dir = os.path.join(base_dir, "logs")
tmp_folder = os.path.join(base_dir, "tmp")
chatlog_dir = os.path.join(log_dir, "chatbot")
weblog_dir = os.path.join(log_dir, "website")

# create folder if not exists
os.makedirs(chatlog_dir, exist_ok=True)
os.makedirs(weblog_dir, exist_ok=True)
os.makedirs(tmp_folder, exist_ok=True)

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
migrate = Migrate()

# Configure logger
log_filename = "run.log"
log_max_size = 1 * 1024 * 1024  # 1 MB

# Create a logger
logger = logging.getLogger("braintext")
logger.setLevel(logging.INFO)

# Create a file handler with log rotation
handler = RotatingFileHandler(
    os.path.join(weblog_dir, log_filename), maxBytes=log_max_size, backupCount=5
)

# Create a formatter
formatter = logging.Formatter("%(asctime)s [%(levelname)s] - %(message)s")
handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(handler)


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
