from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from celery import Celery
from redis import Redis
from flask import current_app

# Initialize extensions without app to avoid circular dependencies
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()
cors = CORS()
celery = Celery('app')
ma = Marshmallow()
redis_client = Redis()

def init_celery(app=None):
    """Initialize Celery with Flask app context"""
    if app:
        celery.conf.update(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND'],
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC'
        )

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
    return celery

def init_redis(app):
    """Initialize Redis with app configuration"""
    global redis_client
    redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
    redis_client = Redis.from_url(redis_url)
    return redis_client
