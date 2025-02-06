import pytest
from flask import json
from app.models import Professional, Service, ServiceRequest, ProfessionalDocument, db, Customer, Admin
from app.utils.validation import DocumentValidator
from flask_jwt_extended import create_access_token
import io
from datetime import datetime, timezone
from werkzeug.datastructures import FileStorage

@pytest.fixture
def service(app):
    """Create a test service"""
    with app.app_context():
        service = Service(
            name='Test Service',
            type='cleaning',
            price=100.00,
            time_required='2 hours',
            description='Test service description'
        )
        db.session.add(service)
        db.session.commit()
        
        # Refresh the service to ensure it's bound to the session
        service = db.session.get(Service, service.id)
        return service

@pytest.fixture
def approved_professional(app, service):
    """Create an approved professional"""
    with app.app_context():
        # Get service type from service while in session
        service_type = db.session.get(Service, service.id).type
        
        professional = Professional(
            email='pro@test.com',
            name='Test Professional',
            phone='1234567890',
            service_type=service_type,
            experience='5 years',
            status='approved',
            verified=True,
            available=True,
            active=True
        )
        professional.set_password('password')
        db.session.add(professional)
        db.session.commit()
        
        # Refresh the professional to ensure it's bound to the session
        professional = db.session.get(Professional, professional.id)
        return professional

@pytest.fixture
def professional_token(app, approved_professional):
    """Create a JWT token for professional"""
    with app.app_context():
        return create_access_token(
            identity=approved_professional.email,
            additional_claims={
                'type': 'professional',
                'is_admin': False,
                'verified': True
            }
        )

@pytest.fixture
def customer(app):
    """Create a test customer"""
    with app.app_context():
        customer = Customer(
            email='customer@test.com',
            name='Test Customer',
            phone='1234567890',
            address='123 Customer St',
            pincode='12345',
            status='registered'
        )
        customer.set_password('password')
        db.session.add(customer)
        db.session.commit()
        
        # Refresh the customer to ensure it's bound to the session
        customer = db.session.get(Customer, customer.id)
        return customer

@pytest.fixture
def admin(app):
    """Create a test admin"""
    with app.app_context():
        admin = Admin(
            email='admin@test.com',
            name='Test Admin',
            phone='1234567890'
        )
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        
        # Refresh the admin to ensure it's bound to the session
        admin = db.session.get(Admin, admin.id)
        return admin

@pytest.fixture
def admin_token(app, admin):
    """Create a JWT token for admin"""
    with app.app_context():
        return create_access_token(
            identity=admin.email,
            additional_claims={
                'type': 'admin',
                'is_admin': True
            }
        )

@pytest.fixture
def service_request(app, approved_professional, customer, service):
    """Create a service request"""
    with app.app_context():
        # Get fresh instances from the session
        professional = db.session.get(Professional, approved_professional.id)
        customer = db.session.get(Customer, customer.id)
        service = db.session.get(Service, service.id)
        
        request = ServiceRequest(
            customer_id=customer.id,
            professional_id=professional.id,
            service_id=service.id,
            status='requested',
            request_date=datetime.now(timezone.utc),
            remarks='Test remarks'
        )
        db.session.add(request)
        db.session.commit()
        
        # Refresh the request to ensure it's bound to the session
        request = db.session.get(ServiceRequest, request.id)
        return request

@pytest.fixture
def document_file():
    """Create a test document file"""
    return FileStorage(
        stream=io.BytesIO(b'test content'),
        filename='test.pdf',
        content_type='application/pdf'
    )

def test_get_professionals(client):
    """Test getting list of professionals"""
    response = client.get('/api/professionals')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'items' in data
    assert 'total' in data
    assert 'pages' in data

def test_get_professionals_with_filters(client, approved_professional, service):
    """Test getting professionals with filters"""
    # Test service filter
    response = client.get(f'/api/professionals?service_type={service.type}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) > 0

def test_get_professionals_invalid_filters(client):
    """Test getting professionals with invalid filter parameters"""
    response = client.get('/api/professionals?rating=invalid&experience=abc')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_get_professional_requests(client, professional_token, service_request):
    """Test getting professional's service requests"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    
    # Test all requests
    response = client.get('/api/professionals/requests', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) > 0
    
    # Test by status
    response = client.get('/api/professionals/requests?status=pending', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['items']) > 0

def test_accept_request(client, professional_token, service_request):
    """Test accepting a service request"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    response = client.post(
        f'/api/professionals/requests/{service_request.id}/accept',
        headers=headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'assigned'
    assert data['professional_id'] is not None

def test_reject_request(client, professional_token, service_request):
    """Test rejecting a service request"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    response = client.post(
        f'/api/professionals/requests/{service_request.id}/reject',
        headers=headers
    )
    assert response.status_code == 204

def test_complete_request(client, professional_token, service_request):
    """Test completing a service request"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    
    # First accept the request
    client.post(
        f'/api/professionals/requests/{service_request.id}/accept',
        headers=headers
    )
    
    # Then complete it
    response = client.post(
        f'/api/professionals/requests/{service_request.id}/complete',
        headers=headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'completed'
    assert data['completion_date'] is not None

def test_complete_request_invalid_state(client, professional_token, service_request):
    """Test completing a request that's not in 'accepted' state"""
    with client.application.app_context():
        # Change request status to 'requested'
        request = db.session.get(ServiceRequest, service_request.id)
        request.status = 'requested'
        db.session.commit()

    headers = {'Authorization': f'Bearer {professional_token}'}
    response = client.post(f'/api/professionals/requests/{service_request.id}/complete',
                          headers=headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'status' in data['error']

def test_concurrent_request_accept(client, professional_token, service_request):
    """Test handling concurrent accept requests"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    
    # Simulate request already being accepted
    with client.application.app_context():
        request = db.session.get(ServiceRequest, service_request.id)
        request.status = 'accepted'
        db.session.commit()
    
    response = client.post(f'/api/professionals/requests/{service_request.id}/accept',
                          headers=headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_update_availability(client, professional_token, approved_professional):
    """Test updating professional's availability"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    
    # Test setting to unavailable
    response = client.put(
        '/api/professionals/availability',
        headers=headers,
        json={'available': False}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['available'] is False
    
    # Test setting back to available
    response = client.put(
        '/api/professionals/availability',
        headers=headers,
        json={'available': True}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['available'] is True

def test_update_availability_invalid_data(client, professional_token):
    """Test updating availability with invalid data format"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    data = {
        'availability': 'invalid_format',  # Should be a list of time slots
    }
    response = client.put('/api/professionals/availability', 
                         json=data, headers=headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_get_documents(client, professional_token, approved_professional):
    """Test getting professional's documents"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    response = client.get('/api/professionals/documents', headers=headers)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_upload_document(client, professional_token, document_file):
    """Test uploading a verification document"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    data = {}
    data['document_type'] = 'id_proof'
    data['file'] = (document_file, 'test.pdf')
    response = client.post(
        '/api/professionals/documents',
        headers=headers,
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['document_type'] == 'id_proof'
    assert data['verified'] is False

def test_document_upload_invalid_file(client, professional_token):
    """Test uploading invalid document file"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    data = {
        'document_type': 'certification',
        'file': (io.BytesIO(b'invalid file content'), 'test.exe')  # Invalid file type
    }
    response = client.post('/api/professionals/documents', 
                          data=data, headers=headers)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_verify_document(client, admin_token, professional_token, document_file):
    """Test verifying a professional's document"""
    # First upload a document
    headers = {'Authorization': f'Bearer {professional_token}'}
    data = {}
    data['document_type'] = 'id_proof'
    data['file'] = (document_file, 'test.pdf')
    response = client.post(
        '/api/professionals/documents',
        headers=headers,
        data=data,
        content_type='multipart/form-data'
    )
    document_id = json.loads(response.data)['id']
    
    # Then verify it
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.post(
        f'/api/professionals/documents/{document_id}/verify',
        headers=headers
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['verified'] is True
    assert data['verified_by'] is not None
    assert data['verified_at'] is not None

def test_error_cases(client, professional_token, service_request):
    """Test various error cases"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    
    # Test accepting non-existent request
    response = client.post(
        '/api/professionals/requests/99999/accept',
        headers=headers
    )
    assert response.status_code == 404
    
    # Test accepting already accepted request
    client.post(
        f'/api/professionals/requests/{service_request.id}/accept',
        headers=headers
    )
    response = client.post(
        f'/api/professionals/requests/{service_request.id}/accept',
        headers=headers
    )
    assert response.status_code == 400
    
    # Test completing non-assigned request
    # Create a new request in 'requested' status
    new_request = ServiceRequest(
        service_id=service_request.service_id,
        customer_id=service_request.customer_id,
        professional_id=service_request.professional_id,
        status='requested',
        request_date=service_request.request_date
    )
    db.session.add(new_request)
    db.session.commit()
    
    response = client.post(
        f'/api/professionals/requests/{new_request.id}/complete',
        headers=headers
    )
    assert response.status_code == 400
    
    # Test uploading invalid document type
    data = {
        'document_type': 'invalid_type',
        'file': (document_file, 'test.pdf')
    }
    response = client.post(
        '/api/professionals/documents',
        headers=headers,
        data=data,
        content_type='multipart/form-data'
    )
    assert response.status_code == 400

def test_unauthorized_access(client, service_request):
    """Test accessing endpoints without authentication"""
    endpoints = [
        ('GET', '/api/professionals/requests'),
        ('POST', f'/api/professionals/requests/{service_request.id}/accept'),
        ('POST', f'/api/professionals/requests/{service_request.id}/reject'),
        ('POST', f'/api/professionals/requests/{service_request.id}/complete'),
        ('PUT', '/api/professionals/availability'),
        ('GET', '/api/professionals/documents'),
        ('POST', '/api/professionals/documents')
    ]
    
    for method, endpoint in endpoints:
        response = client.open(endpoint, method=method)
        assert response.status_code == 401
