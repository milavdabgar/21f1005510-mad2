"""Tests for the response utility functions"""

import pytest
from app.utils.response import APIResponse

def test_success_response_with_data():
    """Test success response with data"""
    data = {'key': 'value'}
    response, status_code = APIResponse.success(data=data)
    assert status_code == 200
    assert 'key' in response
    assert response['key'] == 'value'

def test_success_response_with_message():
    """Test success response with message"""
    message = "Operation successful"
    response, status_code = APIResponse.success(message=message)
    assert status_code == 200
    assert 'message' in response
    assert response['message'] == message

def test_success_response_with_custom_status():
    """Test success response with custom status code"""
    data = {'key': 'value'}
    response, status_code = APIResponse.success(data=data, status_code=201)
    assert status_code == 201
    assert 'key' in response
    assert response['key'] == 'value'

def test_success_response_with_data_and_message():
    """Test success response with both data and message"""
    data = {'key': 'value'}
    message = "Operation successful"
    response, status_code = APIResponse.success(data=data, message=message)
    assert status_code == 200
    assert 'key' in response
    assert 'message' in response
    assert response['key'] == 'value'
    assert response['message'] == message

def test_error_response_basic():
    """Test basic error response"""
    message = "Operation failed"
    response, status_code = APIResponse.error(message)
    assert status_code == 400
    assert response['message'] == message
    assert response['code'] == 400

def test_error_response_with_custom_code():
    """Test error response with custom status code"""
    message = "Not found"
    response, status_code = APIResponse.error(message, code=404)
    assert status_code == 404
    assert response['message'] == message
    assert response['code'] == 404

def test_error_response_with_details():
    """Test error response with additional details"""
    message = "Validation failed"
    details = {'field': 'name', 'error': 'Required field'}
    response, status_code = APIResponse.error(message, details=details)
    assert status_code == 400
    assert response['message'] == message
    assert response['code'] == 400
    assert 'details' in response
    assert response['details'] == details
