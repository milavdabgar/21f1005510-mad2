from flask import Flask
from app.config import DevelopmentConfig
from app.extensions import db, jwt, migrate, cors, ma
from datetime import timedelta
from flask_cors import CORS
from celery import Celery

# Initialize Celery
celery = Celery(__name__,
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0')

__all__ = ['create_app', 'celery', 'db']

def create_app(config_class=DevelopmentConfig):    
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure CORS
    app.config['CORS_HEADERS'] = 'Content-Type'
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": "*",
            "supports_credentials": True
        }
    })

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        task_track_started=True,
        task_always_eager=False,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        include=['app.jobs']
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    # Initialize Redis configuration
    app.config['REDIS_URL'] = 'redis://localhost:6379/0'

    # Set JWT configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

    # Import JWT callbacks and error handlers
    from app import auth  # This sets up all JWT callbacks
    from flask_jwt_extended.exceptions import JWTExtendedException
    from app.utils.errors import AuthorizationError, error_response

    @jwt.unauthorized_loader
    def handle_unauthorized_error(_err):
        return error_response(401, "Missing or invalid authorization token")

    @jwt.invalid_token_loader
    def handle_invalid_token_error(_err):
        return error_response(401, "Invalid authorization token")

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(_err):
        return error_response(401, "Authorization error")

    @app.errorhandler(AuthorizationError)
    def handle_auth_error(err):
        return error_response(401, str(err))

    # Register blueprints
    from app.api import auth, services, professionals, customers, admin, errors, stats, search
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(services.bp, url_prefix='/api/services')
    app.register_blueprint(professionals.bp, url_prefix='/api/professionals')
    app.register_blueprint(customers.bp, url_prefix='/api/customers')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    app.register_blueprint(stats.bp, url_prefix='/api')
    app.register_blueprint(search.bp, url_prefix='/api')
    app.register_blueprint(errors.bp)  # No prefix for error handlers

    # Create database tables
    with app.app_context():
        # Only drop and recreate tables in development
        if app.debug and not app.testing:
            db.drop_all()
            db.create_all()
            
            # Create sample data if running in development
            from app.sample_data import create_sample_data
            create_sample_data()

    return app
