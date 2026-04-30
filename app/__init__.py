from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import db, limiter, session


def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)
    app.secret_key = Config.SESSION_SECRET

    # Enable CORS for all origins (backend-only, front end plugged later)
    CORS(app)

    # Init extensions
    db.init_app(app)
    limiter.init_app(app)
    session.init_app(app)

    # Register blueprints
    from .routes.api import api_bp
    app.register_blueprint(api_bp)

    return app
