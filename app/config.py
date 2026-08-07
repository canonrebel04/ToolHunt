import os

"""Configuration classes for the ToolHunt Flask application."""


class Config:
    """Base configuration."""
    # SECURITY: Using environment variable for secret key with insecure fallback for local dev.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-insecure-dev-key')
    TESTING = False
    CACHE_TYPE = 'SimpleCache'  # In-memory cache, no Redis needed
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes


class TestingConfig(Config):
    """Configuration used during test runs."""
    TESTING = True
    CACHE_TYPE = 'SimpleCache'


class ProductionConfig(Config):
    """Configuration for production deployments."""
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300
