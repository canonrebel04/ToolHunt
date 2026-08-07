"""ToolHunt Flask application factory."""

import logging
import os
from flask import Flask
from app.extensions import cache


def create_app(config_class=None):
    """Create and configure the Flask application.

    Parameters
    ----------
    config_class : class, optional
        Configuration class to use (e.g. TestingConfig, ProductionConfig).
        Falls back to app.config.Config if not provided.

    Returns
    -------
    Flask
        Configured Flask application instance.
    """
    # Configure structured logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Determine the project root (one level above this package)
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    app = Flask(
        __name__,
        template_folder=os.path.join(_root, 'templates'),
        static_folder=os.path.join(_root, 'static'),
    )

    if config_class is None:
        from app.config import Config
        config_class = Config

    app.config.from_object(config_class)

    # SECURITY: Ensure that production environments explicitly set the secret key.
    # We validate here rather than in ProductionConfig to avoid import-time crashes during tests/dev.
    if app.debug is False and app.config.get('TESTING') is False and app.config.get('SECRET_KEY') == 'default-insecure-dev-key':
        raise ValueError("SECRET_KEY environment variable is not set for production!")

    # Initialize extensions
    cache.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
