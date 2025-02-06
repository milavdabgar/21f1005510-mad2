import pytest
from app.models import Customer, Service, ServiceRequest
from datetime import datetime, timezone
from flask_jwt_extended import create_access_token

@pytest.fixture
def customer(session):
    """Create a test customer."""
    customer = Customer(
        email='test@scarlett.com',
        name='Test Customer',
        phone='1234567890',
        address='123 Test St',
        pincode='12345'
    )
    session.add(customer)
    session.commit()
    return customer

@pytest.fixture
def other_customer(session):
    """Create another test customer."""
    customer = Customer(
        email='other@scarlett.com',
        name='Other Customer',
        phone='9876543210',
        address='456 Test St',
        pincode='54321'
    )
    session.add(customer)
    session.commit()
    return customer

@pytest.fixture
def auth_headers(customer):
    """Create authentication headers."""
    token = create_access_token(identity=customer.email)
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def service(session):
    """Create a test service."""
    service = Service(
        name='Test Service',
        description='Test Description',
        type='general',
        price=100.0,
        time_required='1 hour'
    )
    session.add(service)
    session.commit()
    return service

def test_get_profile(client, customer, auth_headers):
    """Test getting customer profile."""
    response = client.get('/api/customers/profile', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['user']['email'] == customer.email
    assert data['user']['name'] == customer.name
    assert data['user']['phone'] == customer.phone
    assert data['address'] == customer.address
    assert data['pincode'] == customer.pincode

def test_update_profile(client, customer, auth_headers):
    """Test updating customer profile."""
    update_data = {
        'name': 'Updated Name',
        'phone': '5555555555',
        'address': 'Updated Address',
        'pincode': '54321'
    }
    response = client.put('/api/customers/profile',
                         json=update_data,
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == update_data['name']
    assert data['phone'] == update_data['phone']
    assert data['address'] == update_data['address']
    assert data['pincode'] == update_data['pincode']

def test_get_services(client, service, auth_headers):
    """Test getting available services."""
    response = client.get('/api/customers/services', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['name'] == service.name
    assert data['items'][0]['description'] == service.description
    assert float(data['items'][0]['price']) == service.price

def test_create_request(client, customer, service, auth_headers):
    """Test creating a service request."""
    request_data = {
        'service_id': service.id,
        'remarks': 'Test request'
    }
    response = client.post('/api/customers/requests', 
                          json=request_data,
                          headers=auth_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data['service']['id'] == service.id
    assert data['status'] == 'requested'
    assert data['remarks'] == request_data['remarks']

def test_get_request(client, customer, service, auth_headers, session):
    """Test getting a specific service request."""
    # Create a service request first
    request = ServiceRequest(
        service_id=service.id,
        customer_id=customer.id,
        request_date=datetime.now(timezone.utc),
        remarks='Test request'
    )
    session.add(request)
    session.commit()

    response = client.get(f'/api/customers/requests/{request.id}',
                         headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['id'] == request.id
    assert data['service']['id'] == service.id
    assert data['status'] == request.status

def test_cancel_request(client, customer, service, auth_headers, session):
    """Test canceling a service request."""
    # Create a service request first
    request = ServiceRequest(
        service_id=service.id,
        customer_id=customer.id,
        request_date=datetime.now(timezone.utc),
        remarks='Test request'
    )
    session.add(request)
    session.commit()

    response = client.post(f'/api/customers/requests/{request.id}/cancel',
                          headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'cancelled'

def test_get_stats(client, customer, service, auth_headers, session):
    """Test getting customer statistics."""
    # Create some service requests with different statuses
    for status in ['completed', 'requested', 'cancelled']:
        request = ServiceRequest(
            service_id=service.id,
            customer_id=customer.id,
            request_date=datetime.now(timezone.utc),
            status=status
        )
        session.add(request)
    session.commit()

    response = client.get('/api/customers/dashboard/stats', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_requests' in data
    assert 'pending_requests' in data
    assert 'completed_requests' in data
    assert 'cancelled_requests' in data

def test_get_service_categories(client, auth_headers, app):
    """Test getting service categories for customers"""
    # Add test services with different types
    with app.app_context():
        from app.models import Service, db
        services = [
            Service(
                name='House Cleaning',
                type='cleaning',
                description='Professional house cleaning service',
                price=100.00,
                time_required='2 hours'
            ),
            Service(
                name='Electrical Repair',
                type='electrical',
                description='Professional electrical repair service',
                price=150.00,
                time_required='1 hour'
            )
        ]
        db.session.add_all(services)
        db.session.commit()

    response = client.get('/api/customers/services/categories', headers=auth_headers)
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'items' in data
    assert 'total' in data
    assert isinstance(data['items'], list)
    assert len(data['items']) > 0
    
    # Check category structure
    category = data['items'][0]
    assert 'type' in category
    assert 'name' in category
    assert 'description' in category
    assert category['name'].endswith('Services')
    
    # Total should match items length
    assert data['total'] == len(data['items'])

    # Cleanup test data
    with app.app_context():
        db.session.query(Service).delete()
        db.session.commit()
