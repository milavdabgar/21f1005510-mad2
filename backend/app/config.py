import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base config."""
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    DEBUG = os.environ.get('DEBUG', False)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///app.db')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')
    # Get JWT expiration and clean any potential whitespace
    jwt_expires_raw = os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '3600').strip()
    try:
        # Try to convert to int, fallback to 3600 if any error occurs
        jwt_expires_seconds = int(jwt_expires_raw.split('#')[0].strip())
    except (ValueError, AttributeError):
        jwt_expires_seconds = 3600
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=jwt_expires_seconds)
    
    # Upload Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads'))
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'pdf,jpg,jpeg,png,doc,docx').split(','))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Redis config
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/1'
    
    # CORS config
    CORS_HEADERS = 'Content-Type'

    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Mail Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', False).lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@scarlett.com')
    
    # Frontend Configuration
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:8080')

class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True
    ENV = 'development'

class TestConfig(Config):
    """Test config."""
    TESTING = True
    DEBUG = False
    ENV = 'testing'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_uploads')
    
    # Redis configuration
    REDIS_URL = 'redis://localhost:6379/1'  # Use a different database for testing
    
    # Test Celery configuration (using memory broker)
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'memory://'
    
    # Test mail configuration (using dummy SMTP server)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 2525
    MAIL_USE_TLS = False

class ProductionConfig(Config):
    """Production config."""
    DEBUG = False
    ENV = 'production'
    
    # Override with production-specific settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True

# Dictionary for environment-based configuration selection
config = {
    'development': DevelopmentConfig,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
