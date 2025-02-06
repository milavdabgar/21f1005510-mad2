import json
import pytest
from app.models import Service, Admin, db
from app.utils.auth import create_access_token
from app.extensions import db
from flask_jwt_extended import create_access_token

@pytest.fixture
def auth_headers(app):
    """Create authentication headers for admin user."""
    with app.app_context():
        # Create an admin user if not exists
        admin = Admin.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = Admin(
                email='admin@test.com',
                name='Test Admin',
                active=True,
                type='admin'
            )
            admin.set_password('testpassword')
            db.session.add(admin)
            db.session.commit()
            db.session.refresh(admin)
        
        # Create access token with admin email as identity
        token = create_access_token(
            identity=admin.email,  # Use email as identity
            additional_claims={
                'type': 'admin',
                'is_admin': True
            }
        )
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

@pytest.fixture
def sample_services(app):
    """Create sample services for testing."""
    services = []
    with app.app_context():
        # Clear existing services
        Service.query.delete()
        db.session.commit()
        
        # Create services
        services = [
            Service(
                name='House Cleaning',
                description='Professional house cleaning services',
                type='cleaning',
                price=100.0,
                time_required='2 hours'
            ),
            Service(
                name='Plumbing',
                description='Expert plumbing services',
                type='maintenance',
                price=150.0,
                time_required='1-3 hours'
            ),
            Service(
                name='Gardening',
                description='Professional gardening and landscaping',
                type='outdoor',
                price=200.0,
                time_required='4 hours'
            )
        ]
        
        # Add and commit services
        for service in services:
            db.session.add(service)
        db.session.commit()
        
        # Get fresh instances
        service_ids = [s.id for s in services]
        db.session.expunge_all()
        services = [db.session.get(Service, id) for id in service_ids]
        
        yield services
        
        # Cleanup
        Service.query.delete()
        db.session.commit()

def test_get_services(client, sample_services):
    """Test getting all services."""
    response = client.get('/api/services/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data
    assert len(data['items']) == 3
    assert data['total'] == 3
    assert data['page'] == 1
    assert data['per_page'] == 10

def test_get_services_with_filters(client, sample_services):
    """Test getting services with filters."""
    # Test type filter
    response = client.get('/api/services/?type=cleaning')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data
    assert len(data['items']) == 1
    assert data['items'][0]['type'] == 'cleaning'
    assert data['total'] == 1

def test_get_single_service(client, sample_services):
    """Test getting a single service."""
    service_id = sample_services[0].id
    response = client.get(f'/api/services/{service_id}/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['name'] == 'House Cleaning'
    assert data['type'] == 'cleaning'
    assert data['price'] == 100.0
    assert data['time_required'] == '2 hours'

def test_get_nonexistent_service(client):
    """Test getting a service that doesn't exist."""
    response = client.get('/api/services/999/')
    assert response.status_code == 404

def test_create_service_as_admin(client, auth_headers):
    """Test creating a new service as admin."""
    service_data = {
        'name': 'Electrical Services',
        'description': 'Professional electrical repairs and installations',
        'type': 'maintenance',
        'price': 175.0,
        'time_required': '2-4 hours'
    }
    
    response = client.post(
        '/api/services/',
        data=json.dumps(service_data),
        headers=auth_headers
    )
    assert response.status_code == 201
    
    data = json.loads(response.data)
    assert data['name'] == service_data['name']
    assert data['type'] == service_data['type']
    assert float(data['price']) == float(service_data['price'])
    assert data['time_required'] == service_data['time_required']
    
    # Verify service was created in database
    service = Service.query.filter_by(name=service_data['name']).first()
    assert service is not None
    assert service.description == service_data['description']

def test_create_service_without_auth(client):
    """Test creating a service without authentication."""
    service_data = {
        'name': 'Test Service',
        'description': 'Test Description',
        'type': 'test',
        'price': 100.0,
        'time_required': '1 hour'
    }
    
    response = client.post(
        '/api/services/',
        data=json.dumps(service_data),
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 401

def test_update_service(client, auth_headers, sample_services):
    """Test updating a service."""
    service_id = sample_services[0].id
    update_data = {
        'name': 'Updated House Cleaning',
        'description': 'Updated description',
        'price': 125.0,
        'time_required': '2-3 hours'
    }
    
    response = client.put(
        f'/api/services/{service_id}/',
        data=json.dumps(update_data),
        headers=auth_headers
    )
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['name'] == update_data['name']
    assert data['description'] == update_data['description']
    assert float(data['price']) == float(update_data['price'])
    assert data['time_required'] == update_data['time_required']
    
    # Verify the update in database
    service = db.session.get(Service, service_id)
    assert service.name == update_data['name']
    assert service.description == update_data['description']
    assert service.price == update_data['price']
    assert service.time_required == update_data['time_required']

def test_delete_service(client, auth_headers, sample_services):
    """Test deleting a service."""
    service_id = sample_services[0].id
    response = client.delete(f'/api/services/{service_id}/', headers=auth_headers)
    assert response.status_code == 204
    
    # Verify the service is deleted
    service = db.session.get(Service, service_id)
    assert service is None

def test_delete_nonexistent_service(client, auth_headers):
    """Test deleting a service that doesn't exist."""
    response = client.delete('/api/services/999/', headers=auth_headers)
    assert response.status_code == 404

def test_get_service_professionals(client, sample_services):
    """Test getting professionals for a service."""
    service_id = sample_services[0].id
    response = client.get(f'/api/services/{service_id}/professionals/')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data

def test_get_service_requests(client, auth_headers, sample_services):
    """Test getting service requests for a service."""
    service_id = sample_services[0].id
    response = client.get(f'/api/services/{service_id}/requests/', headers=auth_headers)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
