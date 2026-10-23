import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load local environment variables from .env file
load_dotenv(BASE_DIR / '.env')

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'road-transport-expert-system-secure-key-2025')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'database' / 'transportation.db'))
    RULES_PATH = os.environ.get('RULES_PATH', str(BASE_DIR / 'knowledge_base' / 'transportation_rules.json'))
    AI_API_KEY = os.environ.get('AI_API_KEY') or os.environ.get('GEMINI_API_KEY', '')
    GEMINI_API_KEY = AI_API_KEY
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
