from flask import Flask
from flask_login import LoginManager
from config import Config
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app(config=Config):
    app = Flask(__name__)

    app.config.from_object(config)
    db.init_app(app)
    login_manager.init_app(app)

    from app.main.routes import main
    from app.auth.routes import auth
    from app.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)

    return app