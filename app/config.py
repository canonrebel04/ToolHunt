import os

"""Configuration classes for the ToolHunt Flask application."""


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
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # SECURITY: Ensure SECRET_KEY is set in production to prevent cookie forgery
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for Flask application")
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300
