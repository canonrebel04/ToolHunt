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

    # Initialize extensions
    cache.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
