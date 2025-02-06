import pytest
from datetime import datetime, timedelta, timezone
from app.models import ServiceRequest, Service, Professional, Customer
from app.utils.stats import Statistics

def create_service_request(session, service, customer, professional=None, status="requested", rating=None):
    """Helper function to create a service request"""
    request = ServiceRequest(
        service=service,
        customer=customer,
        professional=professional,
        status=status,
        rating=rating,
        request_date=datetime.now(timezone.utc)
    )
    session.add(request)
    session.commit()
    return request

def test_admin_stats_unauthorized(client):
    """Test admin stats endpoint without auth"""
    response = client.get('/api/stats/admin')
    assert response.status_code == 401

def test_admin_stats(client, session, admin_token, service, customer, approved_professional):
    """Test admin stats endpoint"""
    # Create some test data
    create_service_request(session, service, customer, approved_professional, "completed", 5)
    create_service_request(session, service, customer, approved_professional, "completed", 4)
    create_service_request(session, service, customer, None, "requested")
    
    headers = {'Authorization': f'Bearer {admin_token}'}
    print(f"Admin Token: {admin_token}")  # Debugging statement
    response = client.get('/api/stats/admin', headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debugging statement
    assert response.status_code == 200
    
    data = response.json
    assert 'services' in data
    assert 'professionals' in data
    assert 'customers' in data
    
    # Check service stats
    services = data['services']
    assert services['total_requests'] == 3
    assert services['rated_requests'] == 2
    assert services['avg_rating'] > 0
    assert 'status_breakdown' in services
    assert services['status_breakdown']['completed'] == 2
    assert services['status_breakdown']['requested'] == 1
    
    # Check professional stats
    pros = data['professionals']
    assert pros['total'] == 1
    assert pros['total_requests'] == 3  # Include all requests
    assert pros['avg_rating'] > 0
    assert pros['total_earnings'] == 2 * service.price
    
    # Check customer stats
    customers = data['customers']
    assert customers['total_requests'] == 3
    assert customers['completed_requests'] == 2
    assert customers['rating_rate'] > 0

def test_professional_stats_unauthorized(client):
    """Test professional stats endpoint without auth"""
    response = client.get('/api/stats/professional')
    assert response.status_code == 401

def test_professional_stats(client, session, professional_token, service, customer, approved_professional):
    """Test professional stats endpoint"""
    # Create test data with various statuses and ratings
    create_service_request(session, service, customer, approved_professional, "completed", 5)
    create_service_request(session, service, customer, approved_professional, "completed", 4)
    create_service_request(session, service, customer, approved_professional, "cancelled")
    create_service_request(session, service, customer, approved_professional, "requested")
    
    headers = {'Authorization': f'Bearer {professional_token}'}
    print(f"Professional Token: {professional_token}")  # Debugging statement
    response = client.get('/api/stats/professional', headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debugging statement
    assert response.status_code == 200
    
    data = response.json
    assert data['total_requests'] == 4  # Include all requests
    assert data['rated_requests'] == 2
    assert data['avg_rating'] == 4.5
    assert data['total_earnings'] == 2 * service.price
    assert data['completion_rate'] == 50.0  # 2 completed out of 4 total

def test_professional_stats_no_data(client, professional_token):
    """Test professional stats endpoint with no data"""
    headers = {'Authorization': f'Bearer {professional_token}'}
    print(f"Professional Token: {professional_token}")  # Debugging statement
    response = client.get('/api/stats/professional', headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debugging statement
    assert response.status_code == 200
    
    data = response.json
    assert data['total_requests'] == 0
    assert data['rated_requests'] == 0
    assert data['avg_rating'] == 0
    assert data['total_earnings'] == 0
    assert data['completion_rate'] == 0

def test_customer_stats_unauthorized(client):
    """Test customer stats endpoint without auth"""
    response = client.get('/api/stats/customer')
    assert response.status_code == 401

def test_customer_stats(client, session, customer_token, service, customer, approved_professional):
    """Test customer stats endpoint"""
    # Create test data
    create_service_request(session, service, customer, approved_professional, "completed", 5)
    create_service_request(session, service, customer, approved_professional, "completed", None)
    create_service_request(session, service, customer, None, "requested")
    
    headers = {'Authorization': f'Bearer {customer_token}'}
    print(f"Customer Token: {customer_token}")  # Debugging statement
    response = client.get('/api/stats/customer', headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debugging statement
    assert response.status_code == 200
    
    data = response.json
    assert 'total_requests' in data
    assert 'status_counts' in data
    
    # Check request summary
    status_counts = data['status_counts']
    assert status_counts['completed'] == 2
    assert status_counts['requested'] == 1
    
    # Check spending and rating rate
    assert data['total_spending'] == 2 * service.price
    assert data['rating_rate'] > 0

def test_customer_stats_no_data(client, customer_token):
    """Test customer stats endpoint with no data"""
    headers = {'Authorization': f'Bearer {customer_token}'}
    print(f"Customer Token: {customer_token}")  # Debugging statement
    response = client.get('/api/stats/customer', headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debugging statement
    assert response.status_code == 200
    
    data = response.json
    assert 'total_requests' in data
    assert data['total_requests'] == 0
    assert 'status_counts' in data
    assert data['status_counts'] == {}
    assert data['total_spending'] == 0
    assert data['rating_rate'] == 0

def test_stats_with_old_data(client, session, admin_token, service, customer, approved_professional):
    """Test that old data is filtered out"""
    # Create an old request (31 days ago)
    old_request = ServiceRequest(
        service=service,
        customer=customer,
        professional=approved_professional,
        status="completed",
        rating=5,
        request_date=datetime.now(timezone.utc) - timedelta(days=31)
    )
    session.add(old_request)
    
    # Create a recent request
    create_service_request(session, service, customer, approved_professional, "completed", 4)
    session.commit()
    
    # Test admin stats
    headers = {'Authorization': f'Bearer {admin_token}'}
    print(f"Admin Token: {admin_token}")  # Debugging statement
    response = client.get('/api/stats/admin', headers=headers)
    print(f"Response Status Code: {response.status_code}")  # Debugging statement
    assert response.status_code == 200
    data = response.json
    
    # Should only count recent request
    assert data['services']['total_requests'] == 1
    assert data['professionals']['total_requests'] == 1
    assert data['customers']['total_requests'] == 1
