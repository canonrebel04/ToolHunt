import os

"""Configuration classes for the ToolHunt Flask application."""


class Config:
    """Base configuration."""
    # SECURITY: Use environment variable for SECRET_KEY with a static non-production fallback
    SECRET_KEY = os.environ.get('SECRET_KEY', 'local-dev-not-for-production')
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
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300
