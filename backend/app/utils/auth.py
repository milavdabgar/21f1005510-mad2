from functools import wraps
from flask import jsonify, request, abort
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_identity, get_jwt,
    create_access_token, create_refresh_token
)
from ..models import User, Professional, Customer, Admin
from .errors import AuthorizationError
from ..extensions import db

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    
    # First try to get from claims
    user_type = claims.get('type', '').lower()
    
    # Then try to get from database
    if user_type == 'admin':
        user = Admin.query.get(user_id)
    elif user_type == 'professional':
        user = Professional.query.get(user_id)
    elif user_type == 'customer':
        user = Customer.query.get(user_id)
    else:
        # Fallback to checking all types
        user = Admin.query.get(user_id)
        if not user:
            user = Professional.query.get(user_id) or Customer.query.get(user_id)
    
    return user

def admin_required():
    """Decorator to check if user is admin"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin'):
                raise AuthorizationError('Admin access required')
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def professional_required():
    """Decorator to check if user is professional"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('type', '').lower() != 'professional':
                raise AuthorizationError('Professional access required')
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def customer_required():
    """Decorator to check if user is customer"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('type', '').lower() != 'customer':
                raise AuthorizationError('Customer access required')
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def user_required():
    """Decorator to check if user is authenticated"""
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if not user:
                raise AuthorizationError('Authentication required')
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def generate_tokens(user):
    """Generate access and refresh tokens"""
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'role': user.role
        }
    }

def verify_user_access(model, user_id):
    """Verify user has access to resource"""
    verify_jwt_in_request()
    claims = get_jwt()
    
    if claims.get('is_admin'):
        return True
    
    resource = db.session.get(model, user_id)
    return resource and resource.user_id == get_jwt_identity()

class RoleBasedAccess:
    """Role-based access control"""
    @staticmethod
    def can_view_service_requests(service_id):
        verify_jwt_in_request()
        claims = get_jwt()
        user_id = get_jwt_identity()
        
        if claims.get('is_admin'):
            return True
        
        if claims.get('type', '').lower() == 'professional':
            professional = db.session.get(Professional, user_id)
            return professional and professional.service_type == service_id
        
        return False
    
    @staticmethod
    def can_manage_service():
        verify_jwt_in_request()
        claims = get_jwt()
        return claims.get('is_admin', False)
    
    @staticmethod
    def can_verify_professional():
        user = get_current_user()
        return user and user.role == 'admin'
