from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import os

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///smart_roster.db'), SQLALCHEMY_TRACK_MODIFICATIONS=False, JSON_SORT_KEYS=False)
    if test_config: app.config.update(test_config)
    CORS(app)
    db.init_app(app)
    from . import models
    from .routes import api
    app.register_blueprint(api, url_prefix='/api')
    with app.app_context(): db.create_all()
    return app
