from flask import jsonify
from app.extensions import jwt
from app.models import User

@jwt.user_identity_loader
def user_identity_lookup(user_email):
    """Convert user email to JWT identity"""
    return user_email

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    """Load user from database using JWT identity"""
    identity = jwt_data["sub"]
    return User.query.filter_by(email=identity).first()

@jwt.additional_claims_loader
def add_claims_to_access_token(identity):
    """Add user type and admin status to JWT claims"""
    user = User.query.filter_by(email=identity).first()
    if user:
        return {
            "type": user.type.lower(),
            "is_admin": user.type.lower() == 'admin'
        }
    return {}

@jwt.token_verification_failed_loader
def token_verification_failed_callback(jwt_header, jwt_payload):
    """Handle invalid token"""
    return jsonify({
        'error': 'Invalid token',
        'message': 'Token signature verification failed'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    """Handle malformed token"""
    return jsonify({
        'error': 'Invalid token',
        'message': 'Token is malformed or invalid'
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Handle expired token"""
    return jsonify({
        'error': 'Token expired',
        'message': 'The token has expired'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error_string):
    """Handle missing token"""
    return jsonify({
        'error': 'Authorization required',
        'message': 'Token is missing'
    }), 401
