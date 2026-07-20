"""Configuration classes for the ToolHunt Flask application."""


import os
import secrets

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
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
