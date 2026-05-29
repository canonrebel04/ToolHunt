"""Configuration classes for the ToolHunt Flask application."""

import os


class Config:
    """Base configuration."""
    SECRET_KEY = 'dev'
    TESTING = False
    CACHE_TYPE = 'SimpleCache'  # In-memory cache, no Redis needed
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes


class TestingConfig(Config):
    """Configuration used during test runs."""
    TESTING = True
    CACHE_TYPE = 'SimpleCache'


class ProductionConfig(Config):
    """Configuration for production deployments."""
    # Ensure SECRET_KEY is set in the environment to avoid hardcoding credentials.
    # We use .get() so we don't crash at import time in local development.
    # Flask will still refuse to start/use sessions securely if this resolves to None.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300
