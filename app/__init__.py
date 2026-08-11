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

    # SECURITY: Ensure a secure SECRET_KEY is set in production without falling back to a default
    if not app.debug and not app.config.get('TESTING') and (not app.config.get('SECRET_KEY') or app.config.get('SECRET_KEY') == 'dev'):
        raise ValueError("A secure SECRET_KEY must be set in production environments")

    # Initialize extensions
    cache.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
