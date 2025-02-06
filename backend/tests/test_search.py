import pytest
from app.models import Service, Professional, User, Admin
from app.extensions import db
from datetime import datetime

def test_search_services_no_filters(client):
    """Test searching services without any filters"""
    # Create test services
    services = [
        Service(name="AC Repair", type="repair", price=100, time_required="2h", description="AC repair service"),
        Service(name="Plumbing", type="plumbing", price=80, time_required="1h", description="Plumbing service"),
        Service(name="House Cleaning", type="cleaning", price=150, time_required="3h", description="Cleaning service")
    ]
    for service in services:
        db.session.add(service)
    db.session.commit()

    # Test search without filters
    response = client.get('/api/search/services')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 3
    assert data['total'] == 3

def test_search_services_with_filters(client):
    """Test searching services with filters"""
    # Create test services
    services = [
        Service(name="AC Repair", type="repair", price=100, time_required="2h", description="AC repair service"),
        Service(name="Plumbing", type="plumbing", price=80, time_required="1h", description="Plumbing service"),
        Service(name="House Cleaning", type="cleaning", price=150, time_required="3h", description="Cleaning service")
    ]
    for service in services:
        db.session.add(service)
    db.session.commit()

    # Test search with text query
    response = client.get('/api/search/services?q=cleaning')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['name'] == "House Cleaning"

    # Test search with price range
    response = client.get('/api/search/services?min_price=90&max_price=120')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['name'] == "AC Repair"

    # Test search with service type
    response = client.get('/api/search/services?type=repair')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['type'] == "repair"

def test_search_professionals_unauthorized(client):
    """Test searching professionals without admin access"""
    response = client.get('/api/search/professionals')
    assert response.status_code == 401  # Unauthorized

def test_search_professionals(client, admin_token, admin):
    """Test searching professionals with admin access"""
    # Create test professionals
    professionals = []
    for i in range(3):
        pro = Professional()
        pro.email = f"pro{i}@test.com"
        pro.name = f"Pro {i}"
        pro.phone = f"123456789{i}"
        pro.type = "professional"
        pro.active = True
        pro.blocked = False
        pro.service_type = "cleaning" if i < 2 else "repair"
        pro.experience = f"{i+1} years"
        pro.status = "pending" if i == 0 else "approved"
        db.session.add(pro)
    db.session.commit()

    headers = {'Authorization': f'Bearer {admin_token}'}

    # Test search without filters
    response = client.get('/api/search/professionals', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 3

    # Test search by name
    response = client.get('/api/search/professionals?q=Pro 1', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['name'] == "Pro 1"

    # Test search by service type
    response = client.get('/api/search/professionals?service_type=cleaning', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 2

    # Test search by status
    response = client.get('/api/search/professionals?status=pending', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 1
    assert data['items'][0]['status'] == "pending"

    # Test search by blocked status
    response = client.get('/api/search/professionals?blocked=false', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['items']) == 3  # All professionals are not blocked
