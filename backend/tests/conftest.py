import pytest
from app import create_app
from app.extensions import db, init_redis, redis_client
from app.config import TestConfig
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_jwt_extended import create_access_token
from datetime import timedelta
from app.models import Professional, Customer, Admin, Service

@pytest.fixture(autouse=True)
def clear_redis():
    """Clear Redis before each test."""
    redis_client.flushdb()

@pytest.fixture
def app():
    """Create application for the tests."""
    app = create_app(TestConfig)
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def session(app):
    """Create a new database session for a test."""
    with app.app_context():
        # Initialize Redis
        init_redis(app)
        # Create tables
        db.create_all()
        # Create a new session for test
        yield db.session
        # Clean up
        db.session.remove()
        db.drop_all()

@pytest.fixture
def admin(session):
    """Create test admin user"""
    admin = Admin(
        email='admin@test.com',
        name='Test Admin',
        active=True
    )
    admin.set_password('password')
    session.add(admin)
    session.commit()
    return admin

@pytest.fixture
def customer(session):
    """Create test customer"""
    customer = Customer(
        email='customer@test.com',
        name='Test Customer',
        phone='1234567890',
        active=True
    )
    customer.set_password('password')
    session.add(customer)
    session.commit()
    return customer

@pytest.fixture
def approved_professional(session):
    """Create approved professional"""
    professional = Professional(
        email='professional@test.com',
        name='Test Professional',
        phone='1234567890',
        service_type='cleaning',
        experience='5 years',
        status='approved',
        verified=True,
        available=True,
        active=True
    )
    professional.set_password('password')
    session.add(professional)
    session.commit()
    return professional

@pytest.fixture
def service(session):
    """Create test service"""
    service = Service(
        name='Test Service',
        type='cleaning',
        price=100.0,
        time_required='2 hours',
        description='Test service description'
    )
    session.add(service)
    session.commit()
    return service

@pytest.fixture
def admin_token(app, admin):
    """Create admin JWT token"""
    with app.app_context():
        token = create_access_token(
            identity=admin.email,
            additional_claims={'type': 'admin', 'is_admin': True},
            expires_delta=timedelta(hours=1)
        )
        return token

@pytest.fixture
def professional_token(app, approved_professional):
    """Create professional JWT token"""
    with app.app_context():
        token = create_access_token(
            identity=approved_professional.email,
            additional_claims={'type': 'professional'},
            expires_delta=timedelta(hours=1)
        )
        return token

@pytest.fixture
def customer_token(app, customer):
    """Create customer JWT token"""
    with app.app_context():
        token = create_access_token(
            identity=customer.email,
            additional_claims={'type': 'customer'},
            expires_delta=timedelta(hours=1)
        )
        return token
