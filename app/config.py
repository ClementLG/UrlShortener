import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'my_precious_secret_key')
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///urls.db')
    RATELIMIT_DEFAULT = "200/day;50/hour;10/minute"
    RATELIMIT_STRATEGY = 'moving-window'
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