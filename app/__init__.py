from flask import Flask
from flask_wtf import CSRFProtect
from flask_login import LoginManager
from config import Config
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
csrf = CSRFProtect()
migrate = Migrate()


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
    from app.chatbot.chatbot import chatbot
    from app.vonage_chatbot.vonage_chatbot import newbot

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)
    app.register_blueprint(payment)
    app.register_blueprint(chatbot)
    app.register_blueprint(newbot)

    csrf.exempt(payment)
    csrf.exempt(chatbot)
    csrf.exempt(newbot)

    return app
