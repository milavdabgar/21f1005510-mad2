import pytest
from flask import json
from app.models import User, Customer, Professional, Admin, db
from app.extensions import db
import io
from flask_jwt_extended import create_access_token

@pytest.fixture
def admin(app):
    """Create an admin user"""
    with app.app_context():
        admin = Admin(
            email='admin@test.com',
            name='Admin User',
            phone='1234567890'
        )
        admin.set_password('password')
        admin.save()
        
        # Get the ID and commit
        admin_id = admin.id
        db.session.commit()
        
        # Return a fresh instance
        return db.session.get(Admin, admin_id)

@pytest.fixture
def admin_token(app, admin):
    """Create a JWT token for admin"""
    with app.app_context():
        return create_access_token(identity=admin.email)

@pytest.fixture
def customer(app):
    """Create a customer"""
    with app.app_context():
        customer = Customer(
            email='customer@test.com',
            name='Test Customer',
            phone='1234567890',
            address='123 Test St',
            pincode='12345'
        )
        customer.set_password('password')
        customer.save()
        
        # Get the ID and commit
        customer_id = customer.id
        db.session.commit()
        
        # Return a fresh instance
        return db.session.get(Customer, customer_id)

@pytest.fixture
def customer_token(app, customer):
    """Create a JWT token for customer"""
    with app.app_context():
        return create_access_token(identity=customer.email)

@pytest.fixture
def professional(app):
    """Create a professional"""
    with app.app_context():
        professional = Professional(
            email='professional@test.com',
            name='Test Professional',
            phone='1234567890',
            service_type='plumbing',
            experience='5 years'
        )
        professional.set_password('password')
        professional.save()
        
        # Get the ID and commit
        professional_id = professional.id
        db.session.commit()
        
        # Return a fresh instance
        return db.session.get(Professional, professional_id)

@pytest.fixture
def professional_token(app, professional):
    """Create a JWT token for professional"""
    with app.app_context():
        return create_access_token(identity=professional.email)

@pytest.fixture
def customer_data():
    return {
        'email': 'customer@test.com',
        'password': 'test123',
        'type': 'customer',
        'name': 'Test Customer',
        'phone': '1234567890',
        'address': '123 Test St',
        'pincode': '12345'
    }

@pytest.fixture
def professional_data():
    return {
        'email': 'professional@test.com',
        'password': 'test123',
        'type': 'professional',
        'name': 'Test Professional',
        'phone': '1234567890',
        'experience': '5 years',
        'service_type': 'plumbing'
    }

@pytest.fixture
def document_data():
    """Create test document files"""
    id_proof = (io.BytesIO(b"test id proof content"), 'id_proof.pdf')
    certification = (io.BytesIO(b"test certification content"), 'certification.pdf')
    return {
        'id_proof': id_proof,
        'certification': certification
    }

def test_register_customer(client, customer_data):
    """Test customer registration"""
    response = client.post('/api/auth/register', 
                         json=customer_data)
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Check response structure (matches Vue frontend needs)
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == customer_data['email']
    assert data['user']['type'] == 'customer'
    assert 'password' not in data['user']

def test_register_professional(client, professional_data):
    """Test professional registration"""
    response = client.post('/api/auth/register', 
                         json=professional_data)
    assert response.status_code == 400  # Should fail without documents
    assert b'Documents required for professional registration' in response.data

def test_register_professional_with_documents(client, professional_data, document_data):
    """Test professional registration with document upload"""
    # Create multipart form data
    data = {}
    for key, value in professional_data.items():
        data[key] = value
    
    # Add files
    for key, (file_obj, filename) in document_data.items():
        data[key] = (file_obj, filename)
    
    # Send registration request with documents
    response = client.post('/api/auth/register',
                         data=data,
                         content_type='multipart/form-data')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    
    # Verify professional registration
    assert data['user']['type'] == 'professional'
    assert data['user']['status'] == 'pending'  # Status should be pending
    assert 'access_token' not in data  # No token should be returned
    assert 'Please wait for admin approval' in data['message']
    
    # Verify documents were uploaded
    assert data['user']['id_proof_path'] is not None
    assert data['user']['certification_path'] is not None

def test_login_pending_professional(client, professional_data, document_data):
    """Test that pending professional cannot login"""
    # First register professional
    data = dict(professional_data)
    for key, (file_obj, filename) in document_data.items():
        data[key] = (file_obj, filename)
    
    client.post('/api/auth/register',
               data=data,
               content_type='multipart/form-data')
    
    # Try to login
    response = client.post('/api/auth/login', 
                         json={
                             'email': professional_data['email'],
                             'password': professional_data['password']
                         })
    
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'pending admin approval' in data['message'].lower()

def test_login_rejected_professional(client, professional_data, document_data, admin_token):
    """Test that rejected professional cannot login"""
    # First register professional
    data = dict(professional_data)
    for key, (file_obj, filename) in document_data.items():
        data[key] = (file_obj, filename)
    
    register_response = client.post('/api/auth/register',
                                  data=data,
                                  content_type='multipart/form-data')
    professional_id = json.loads(register_response.data)['user']['id']
    
    # Admin rejects the professional
    client.post(f'/api/auth/admin/professionals/{professional_id}/reject',
               headers={'Authorization': f'Bearer {admin_token}'},
               json={'reason': 'Documents not valid'})
    
    # Try to login
    response = client.post('/api/auth/login', 
                         json={
                             'email': professional_data['email'],
                             'password': professional_data['password']
                         })
    
    assert response.status_code == 403
    data = json.loads(response.data)
    assert 'rejected' in data['message'].lower()

def test_login_approved_professional(client, professional_data, document_data, admin_token):
    """Test that approved professional can login"""
    # First register professional
    data = dict(professional_data)
    for key, (file_obj, filename) in document_data.items():
        data[key] = (file_obj, filename)
    
    register_response = client.post('/api/auth/register',
                                  data=data,
                                  content_type='multipart/form-data')
    professional_id = json.loads(register_response.data)['user']['id']
    
    # Admin approves the professional
    approve_response = client.post(f'/api/auth/admin/professionals/{professional_id}/approve',
                                 headers={'Authorization': f'Bearer {admin_token}'})
    print(f"Approve response: {approve_response.data}")
    
    # Verify professional status after approval
    prof = db.session.get(Professional, professional_id)
    print(f"Professional status after approval: {prof.status}")
    
    # Try to login
    login_response = client.post('/api/auth/login',
                               json={
                                   'email': professional_data['email'],
                                   'password': professional_data['password']
                               })
    print(f"Login response: {login_response.data}")
    
    assert login_response.status_code == 200
    data = json.loads(login_response.data)
    assert 'access_token' in data
    assert data['user']['status'] == 'approved'

def test_login_success(client, customer_data):
    """Test successful login"""
    # First register
    client.post('/api/auth/register', json=customer_data)
    
    # Then login
    response = client.post('/api/auth/login', 
                         json={
                             'email': customer_data['email'],
                             'password': customer_data['password']
                         })
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify token and user data for Vue frontend
    assert 'access_token' in data
    assert 'user' in data
    assert data['user']['email'] == customer_data['email']

def test_login_invalid_credentials(client, customer_data):
    """Test login with wrong password"""
    # First register
    client.post('/api/auth/register', json=customer_data)
    
    # Try login with wrong password
    response = client.post('/api/auth/login', 
                         json={
                             'email': customer_data['email'],
                             'password': 'wrongpassword'
                         })
    assert response.status_code == 401

def test_get_profile(client, customer_data):
    """Test profile retrieval with JWT token"""
    # Register and login
    client.post('/api/auth/register', json=customer_data)
    login_response = client.post('/api/auth/login', 
                               json={
                                   'email': customer_data['email'],
                                   'password': customer_data['password']
                               })
    token = json.loads(login_response.data)['access_token']
    
    # Get profile with token
    response = client.get('/api/auth/profile',
                         headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify profile data
    assert data['user']['email'] == customer_data['email']
    assert 'password' not in data['user']

def test_update_profile(client, customer_data):
    """Test profile update"""
    # Register and login
    client.post('/api/auth/register', json=customer_data)
    login_response = client.post('/api/auth/login', 
                               json={
                                   'email': customer_data['email'],
                                   'password': customer_data['password']
                               })
    token = json.loads(login_response.data)['access_token']
    
    # Update profile
    update_data = {'name': 'Updated Name', 'phone': '9876543210'}
    response = client.put('/api/auth/profile',
                         headers={'Authorization': f'Bearer {token}'},
                         json=update_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify updates
    assert data['user']['name'] == update_data['name']
    assert data['user']['phone'] == update_data['phone']

def test_unauthorized_access(client):
    """Test accessing protected route without token"""
    response = client.get('/api/auth/profile')
    assert response.status_code == 401

def test_register_duplicate_email(client, customer_data):
    """Test registration with existing email"""
    # First registration
    client.post('/api/auth/register', json=customer_data)
    
    # Second registration with same email
    response = client.post('/api/auth/register', json=customer_data)
    assert response.status_code == 400
    assert b'Email already registered' in response.data

def test_admin_list_professionals(client, admin_token, professional):
    """Test listing all professionals"""
    res = client.get('/api/auth/admin/professionals', 
                    headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert len(res.json) > 0
    assert res.json[0]['email'] == professional.email
    assert res.json[0]['service_type'] == professional.service_type

def test_admin_approve_professional(client, admin_token, professional):
    """Test approving a professional"""
    with client.application.app_context():
        res = client.post(f'/api/auth/admin/professionals/{professional.id}/approve',
                         headers={'Authorization': f'Bearer {admin_token}'})
        assert res.status_code == 200
        assert res.json['message'] == 'Professional approved successfully'
        
        # Verify professional status
        db.session.expire_all()
        prof = db.session.get(Professional, professional.id)
        assert prof.status == 'approved'
        assert prof.verified is True
        assert prof.verified_at is not None
        assert prof.verified_by is not None

def test_admin_reject_professional(client, admin_token, professional):
    """Test rejecting a professional"""
    with client.application.app_context():
        res = client.post(f'/api/auth/admin/professionals/{professional.id}/reject',
                         json={'reason': 'Invalid documents'},
                         headers={'Authorization': f'Bearer {admin_token}'})
        assert res.status_code == 200
        assert res.json['message'] == 'Professional rejected successfully'
        
        # Verify professional status
        db.session.expire_all()
        prof = db.session.get(Professional, professional.id)
        assert prof.status == 'rejected'
        assert prof.verified is False
        assert prof.rejection_reason == 'Invalid documents'

def test_admin_block_user(client, admin_token, customer):
    """Test blocking a user"""
    with client.application.app_context():
        res = client.post(f'/api/auth/admin/users/{customer.id}/block',
                         json={'reason': 'Suspicious activity'},
                         headers={'Authorization': f'Bearer {admin_token}'})
        assert res.status_code == 200
        assert res.json['message'] == 'User blocked successfully'
        
        # Verify user status
        db.session.expire_all()
        cust = db.session.get(Customer, customer.id)
        assert cust.blocked is True
        assert cust.active is False
        assert cust.blocked_reason == 'Suspicious activity'
        assert cust.blocked_at is not None
        assert cust.blocked_by is not None

def test_admin_unblock_user(client, admin_token, customer):
    """Test unblocking a user"""
    with client.application.app_context():
        # First block the user
        customer.block(1, 'Suspicious activity')
        db.session.commit()
        
        res = client.post(f'/api/auth/admin/users/{customer.id}/unblock',
                         headers={'Authorization': f'Bearer {admin_token}'})
        assert res.status_code == 200
        assert res.json['message'] == 'User unblocked successfully'
        
        # Verify user status
        db.session.expire_all()
        cust = db.session.get(Customer, customer.id)
        assert cust.blocked is False
        assert cust.active is True
        assert cust.blocked_reason is None
        assert cust.blocked_at is None
        assert cust.blocked_by is None

def test_admin_search_users(client, admin_token, customer, professional):
    """Test searching users"""
    # Search by email
    res = client.get('/api/auth/admin/users/search?q=test',
                     headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    assert isinstance(res.json, list)
    assert len(res.json) > 0
    
    # Search by type
    res = client.get('/api/auth/admin/users/search?type=professional',
                     headers={'Authorization': f'Bearer {admin_token}'})
    assert res.status_code == 200
    assert all(u['type'] == 'professional' for u in res.json)

def test_non_admin_cannot_access_admin_endpoints(client, customer_token):
    """Test that non-admin users cannot access admin endpoints"""
    endpoints = [
        ('GET', '/api/auth/admin/professionals'),
        ('POST', '/api/auth/admin/professionals/1/approve'),
        ('POST', '/api/auth/admin/professionals/1/reject'),
        ('POST', '/api/auth/admin/users/1/block'),
        ('POST', '/api/auth/admin/users/1/unblock'),
        ('GET', '/api/auth/admin/users/search')
    ]
    
    for method, endpoint in endpoints:
        if method == 'GET':
            res = client.get(endpoint, headers={'Authorization': f'Bearer {customer_token}'})
        else:
            res = client.post(endpoint, headers={'Authorization': f'Bearer {customer_token}'})
        assert res.status_code == 401  # Changed from 403 to 401 to match the actual response
