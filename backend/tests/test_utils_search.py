"""Tests for the search utility functions"""

import pytest
from app.utils.search import Search, memoize
from app.models import Service, Professional, User
from app.extensions import db, redis_client
from werkzeug.security import generate_password_hash
import json

@pytest.fixture
def setup_test_data(app):
    """Setup test data for search tests"""
    with app.app_context():
        # Create test services
        services = [
            Service(name="AC Repair", type="repair", price=100, time_required="2h",
                   description="AC repair service"),
            Service(name="Plumbing", type="plumbing", price=80, time_required="1h",
                   description="Plumbing service"),
            Service(name="House Cleaning", type="cleaning", price=150, time_required="3h",
                   description="Cleaning service")
        ]
        for service in services:
            db.session.add(service)

        # Create test professionals
        users = [
            Professional(
                email="pro1@test.com",
                password_hash=generate_password_hash("password"),
                name="John Doe",
                type="professional",
                experience="5 years",
                service_type="repair",
                status="approved",
                verified=True,
                available=True
            ),
            Professional(
                email="pro2@test.com",
                password_hash=generate_password_hash("password"),
                name="Jane Smith",
                type="professional",
                experience="3 years",
                service_type="plumbing",
                status="approved",
                verified=True,
                available=True
            )
        ]
        for user in users:
            db.session.add(user)
        db.session.commit()
        yield
        # Cleanup
        db.session.query(Service).delete()
        db.session.query(Professional).delete()
        db.session.query(User).delete()
        db.session.commit()

def test_service_filter(app, setup_test_data):
    """Test service-based filtering"""
    with app.app_context():
        # Test service type filter
        query = Professional.query
        filtered = Search._apply_service_filter(query, "repair")
        assert filtered.count() == 1
        assert filtered.first().service_type == "repair"

        # Test availability filter
        filtered = Search._apply_availability_filter(query)
        assert filtered.count() == 2
        assert all(p.available for p in filtered.all())

        # Test verification filter
        filtered = Search._apply_verification_filter(query)
        assert filtered.count() == 2
        assert all(p.verified for p in filtered.all())

def test_search_services_with_query(app, setup_test_data):
    """Test searching services with query parameter"""
    with app.app_context():
        # Test exact match
        results = Search.search_services(query="AC Repair")
        assert len(results) == 1
        assert results[0]['name'] == "AC Repair"
        assert results[0]['price'] == 100

        # Test partial match
        results = Search.search_services(query="repair")
        assert len(results) == 1
        assert results[0]['name'] == "AC Repair"

        # Test no match
        results = Search.search_services(query="invalid")
        assert len(results) == 0

def test_search_services_with_filters(app, setup_test_data):
    """Test searching services with various filters"""
    with app.app_context():
        # Test type filter
        results = Search.search_services(type="repair")
        assert len(results) == 1
        assert results[0]['name'] == "AC Repair"

        # Test price range filter
        results = Search.search_services(min_price=100)
        assert len(results) == 2  # AC Repair (100) and House Cleaning (150)
        assert all(s['price'] >= 100 for s in results)

        # Test combined filters
        results = Search.search_services(type="cleaning", min_price=100)
        assert len(results) == 1
        assert results[0]['name'] == "House Cleaning"
        assert results[0]['price'] == 150

def test_memoize_decorator(app):
    """Test memoization decorator"""
    with app.app_context():
        call_count = 0

        @memoize(timeout=10)
        def test_function(arg):
            nonlocal call_count
            call_count += 1
            return {'result': arg}

        # First call - should hit the function
        result1 = test_function('test')
        assert call_count == 1
        assert result1['result'] == 'test'

        # Second call - should use cache
        result2 = test_function('test')
        assert call_count == 1  # Count shouldn't increase
        assert result2['result'] == 'test'

        # Different argument - should hit the function
        result3 = test_function('different')
        assert call_count == 2
        assert result3['result'] == 'different'

def test_search_professionals_with_filters(app, setup_test_data):
    """Test searching professionals with various filters"""
    with app.app_context():
        # Test experience filter
        results = Search.search_professionals(min_experience=4)
        assert len(results) == 1
        assert int(results[0]['experience'].split()[0]) >= 4

        # Test service type filter
        results = Search.search_professionals(service_type="repair")
        assert len(results) == 1
        assert results[0]['service_type'] == "repair"

        # Test availability filter
        results = Search.search_professionals(available_only=True)
        assert len(results) == 2
        assert all(p['available'] for p in results)

        # Test verification filter
        results = Search.search_professionals(verified_only=True)
        assert len(results) == 2
        assert all(p['verified'] for p in results)

def test_extract_years():
    """Test experience year extraction"""
    assert Search._extract_years("5 years") == 5
    assert Search._extract_years("invalid") == 0
    assert Search._extract_years("") == 0
    assert Search._extract_years("10+ years") == 10

def test_search_services_error_handling(app, setup_test_data):
    """Test error handling in service search"""
    with app.app_context():
        # Test invalid price filter
        results = Search.search_services(min_price="invalid")
        assert len(results) == 3  # Should ignore invalid filter

        # Test non-existent type
        results = Search.search_services(type="nonexistent")
        assert len(results) == 0

def test_search_professionals_combined_filters(app, setup_test_data):
    """Test searching professionals with multiple filters"""
    with app.app_context():
        # Test combining multiple filters
        results = Search.search_professionals(
            service_type="repair",
            verified_only=True,
            available_only=True
        )
        assert len(results) == 1
        assert results[0]['service_type'] == "repair"
        assert results[0]['verified'] is True
        assert results[0]['available'] is True

        # Test with query and filters
        results = Search.search_professionals(
            query="John",
            service_type="repair",
            min_experience=3
        )
        assert len(results) == 1
        assert "John" in results[0]['name']

        # Test with no results
        results = Search.search_professionals(
            service_type="nonexistent",
            verified_only=True
        )
        assert len(results) == 0

def test_search_professionals_error_handling(app, setup_test_data):
    """Test error handling in professional search"""
    with app.app_context():
        # Test with invalid experience
        results = Search.search_professionals(min_experience="invalid")
        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)

        # Test with empty query
        results = Search.search_professionals(query="")
        assert isinstance(results, list)
