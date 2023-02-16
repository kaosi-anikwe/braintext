from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.main.routes import main
    from app.auth.routes import auth
    from app.errors import errors

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)

    return app