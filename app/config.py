import os

"""Configuration classes for the ToolHunt Flask application."""


class Config:
    """Base configuration."""
    SECRET_KEY = 'dev'
    TESTING = False
    CACHE_TYPE = 'SimpleCache'  # In-memory cache, no Redis needed
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # Limit request body to 1MB to prevent DoS
    # Configures whether the app is behind a reverse proxy (e.g. Nginx, Docker)
    USE_PROXY_FIX = os.environ.get('USE_PROXY_FIX', 'false').lower() == 'true'


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
