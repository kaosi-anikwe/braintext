from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    from app.main import main
    from app.auth import auth
    from app.errors import errors

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(errors)
