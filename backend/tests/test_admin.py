import pytest
from app.models import User, Professional, Service, ServiceRequest, Customer, Admin
from app.extensions import db
from flask_jwt_extended import create_access_token

@pytest.fixture
def auth_headers(app, session):
    """Create authentication headers for admin user."""
    with app.app_context():
        admin = Admin.query.filter_by(email='admin@test.com').first()
        if not admin:
            admin = Admin(
                email='admin@test.com',
                name='Test Admin',
                active=True,
                type='admin'
            )
            admin.set_password('testpassword')
            session.add(admin)
            session.commit()
            session.refresh(admin)
        
        token = create_access_token(
            identity=admin.email,
            additional_claims={'type': 'admin', 'is_admin': True}
        )
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

@pytest.fixture
def sample_users(app, session):
    """Create sample users for testing."""
    users = []
    with app.app_context():
        # Clear existing users except admin
        User.query.filter(User.type != 'admin').delete()
        session.commit()
        
        # Create a customer
        customer = Customer(
            email='customer@test.com',
            name='Test Customer',
            phone='1234567890',
            type='customer',
            status='registered'
        )
        customer.set_password('testpassword')
        users.append(customer)
        
        # Create a professional
        professional = Professional(
            email='professional@test.com',
            name='Test Professional',
            phone='0987654321',
            type='professional',
            status='pending',
            service_type='cleaning',
            experience=5,
            verified=False
        )
        professional.set_password('testpassword')
        users.append(professional)
        
        session.add_all(users)
        session.commit()
        for user in users:
            session.refresh(user)
        
        return users

def test_get_users(client, session, auth_headers, sample_users):
    """Test getting all users."""
    response = client.get('/api/admin/users', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) >= 2  # At least customer and professional

def test_get_users_with_filters(client, session, auth_headers, sample_users):
    """Test getting users with status and type filters."""
    # Test blocked status
    response = client.get('/api/admin/users?status=blocked', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(user['blocked'] for user in data['items'])

    # Test active status
    response = client.get('/api/admin/users?status=active', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(user['active'] for user in data['items'])

    # Test type filter
    response = client.get('/api/admin/users?type=professional', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(user['user_type'] == 'professional' for user in data['items'])

    # Test combined filters
    response = client.get('/api/admin/users?type=professional&status=active', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(user['user_type'] == 'professional' and user['active'] for user in data['items'])

def test_update_user_status(client, session, auth_headers, sample_users):
    """Test updating user's status."""
    professional = User.query.filter_by(email='professional@test.com').first()
    
    response = client.put(
        f'/api/admin/users/{professional.id}/status',
        json={'status': 'blocked'},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'blocked'
    
    # Verify in database
    updated_user = db.session.get(User, professional.id)
    assert updated_user.status == 'blocked'

def test_update_user_status_invalid(client, session, auth_headers, sample_users):
    """Test updating user's status with invalid status."""
    professional = User.query.filter_by(email='professional@test.com').first()
    
    response = client.put(
        f'/api/admin/users/{professional.id}/status',
        json={'status': 'invalid_status'},
        headers=auth_headers
    )
    assert response.status_code == 400

def test_get_professionals(client, session, auth_headers, sample_users):
    """Test getting all professionals with filters."""
    response = client.get('/api/admin/professionals', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1  # One professional in sample data
    
    # Test status filter
    response = client.get('/api/admin/professionals?status=pending', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(pro['status'] == 'pending' for pro in data['items'])

def test_get_customers(client, session, auth_headers, sample_users):
    """Test getting all customers with filters."""
    response = client.get('/api/admin/customers', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1  # One customer in sample data
    
    # Test status filter
    response = client.get('/api/admin/customers?status=registered', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert all(cust['status'] == 'registered' for cust in data['items'])

def test_verify_professional(client, session, auth_headers, sample_users):
    """Test verifying a professional's account."""
    professional = User.query.filter_by(email='professional@test.com').first()
    
    response = client.post(
        f'/api/admin/professionals/{professional.id}/verify',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['verified'] == True
    
    # Verify in database
    updated_professional = db.session.get(Professional, professional.id)
    assert updated_professional.verified == True
    assert updated_professional.status == 'approved'

def test_verify_nonexistent_professional(client, session, auth_headers):
    """Test verifying a non-existent professional."""
    response = client.post(
        '/api/admin/professionals/99999/verify',
        headers=auth_headers
    )
    assert response.status_code == 404

def test_get_dashboard_stats(client, session, auth_headers, sample_users):
    """Test getting admin dashboard statistics."""
    response = client.get('/api/admin/dashboard/stats', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    
    # Check required fields
    assert 'total_users' in data
    assert 'total_professionals' in data
    assert 'total_customers' in data
    assert 'recent_users' in data
    assert 'recent_professionals' in data
    assert 'recent_customers' in data
    assert 'total_requests' in data
    assert 'recent_requests' in data
    assert 'pending_requests' in data
    assert 'completed_requests' in data
    
    # Verify counts
    assert data['total_users'] >= 2  # At least our sample users
    assert data['total_professionals'] >= 1  # One professional
    assert data['total_customers'] >= 1  # One customer
