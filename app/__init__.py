from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from .config import Config
from .extensions import db, limiter


def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    limiter.init_app(app)

    # Enable CORS
    if Config.CORS_ALLOWED_ORIGINS == '*':
        CORS(app)
    else:
        CORS(app, origins=Config.CORS_ALLOWED_ORIGINS.split(','))

    # Swagger
    swagger = Swagger(app, template={
        'swagger': '2.0',
        'info': {
            'title': 'Movewiz API',
            'version': '1.0.0',
            'description': 'API for managing events and participants',
        },
    })

    # Register blueprints
    from .routes.api import api_bp
    app.register_blueprint(api_bp)

    return app
