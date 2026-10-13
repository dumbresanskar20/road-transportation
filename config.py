import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'road-transport-expert-system-secure-key-2025')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'database' / 'transportation.db'))
    RULES_PATH = os.environ.get('RULES_PATH', str(BASE_DIR / 'knowledge_base' / 'transportation_rules.json'))
    TESTING = False
    DEBUG = False

class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = False
    DATABASE_PATH = ':memory:'

class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
