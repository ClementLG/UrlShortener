import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my_precious_secret_key')
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///urls.db')
    # --- Rate Limiting ---
    # See https://flask-limiter.readthedocs.io/en/stable/ for details.
    # Default rate limit for all routes.
    RATELIMIT_DEFAULT = "100 per day;20 per hour"

    # Rate limit for the redirection route (<short_code>).
    RATELIMIT_REDIRECT = "10/minute"

    # Rate limit for the API route (/api/urls).
    RATELIMIT_API = "5/minute"

    # Strategy can be 'fixed-window', 'moving-window', etc.
    RATELIMIT_STRATEGY = 'moving-window'

    # Storage backend for rate limits. 'memory://' is for local development.
    # For production, consider using Redis: 'redis://localhost:6379/0'
    RATELIMIT_STORAGE_URL = "memory://"
    LOG_FILE = 'logs/app.log'
    LOG_LEVEL = 'INFO'

class ProductionConfig(Config):
    """Production configuration."""
    FLASK_ENV = 'production'
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///prod_urls.db')

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE_URI = 'sqlite:///:memory:'

config_by_name = dict(
    production=ProductionConfig,
    development=DevelopmentConfig,
    testing=TestingConfig
)