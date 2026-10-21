"""ToolHunt Flask application factory."""

import logging
import os

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

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

    # SECURITY: Ensure SECRET_KEY is set in production to prevent cookie forgery
    if not app.debug and not app.config.get('TESTING') and not app.config.get('SECRET_KEY'):
        raise ValueError("No SECRET_KEY set for Flask application")

    # SECURITY: Trust reverse proxy headers securely, but only when configured.
    # Blindly trusting proxy headers without a real proxy introduces an IP spoofing vulnerability.
    if app.config.get('USE_PROXY_FIX'):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize extensions
    cache.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
