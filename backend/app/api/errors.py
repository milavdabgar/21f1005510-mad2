from flask import Blueprint, current_app
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from jwt.exceptions import PyJWTError
from ..models import db
from ..utils.errors import APIError

bp = Blueprint('errors', __name__)

def error_response(status_code, message, details=None):
    """Create a standard error response"""
    response = {'error': message}
    if details:
        response['details'] = details
    return response, status_code

@bp.app_errorhandler(ValidationError)
def handle_validation_error(error):
    """Handle Marshmallow validation errors"""
    return error_response(400, 'Validation failed', error.messages)

@bp.app_errorhandler(400)
def handle_bad_request(error):
    """Handle bad request errors"""
    return error_response(400, str(error.description))

@bp.app_errorhandler(401)
def handle_unauthorized(error):
    """Handle unauthorized access"""
    return error_response(401, 'Authentication required')

@bp.app_errorhandler(403)
def handle_forbidden(error):
    """Handle forbidden access"""
    return error_response(403, 'Access forbidden')

@bp.app_errorhandler(404)
def handle_not_found(error):
    """Handle not found errors"""
    return error_response(404, 'Resource not found')

@bp.app_errorhandler(PyJWTError)
def handle_jwt_error(error):
    """Handle JWT token errors"""
    return error_response(401, 'Invalid authentication token')

@bp.app_errorhandler(IntegrityError)
def handle_integrity_error(error):
    """Handle database integrity errors"""
    db.session.rollback()
    current_app.logger.error(f'Database integrity error: {str(error)}')
    return error_response(409, 'Resource conflict')

@bp.app_errorhandler(SQLAlchemyError)
def handle_database_error(error):
    """Handle database errors"""
    db.session.rollback()
    current_app.logger.error(f'Database error: {str(error)}')
    return error_response(500, 'Database error occurred')

@bp.app_errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    return error_response(error.status_code, error.message, error.details)

@bp.app_errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle unexpected errors"""
    current_app.logger.exception('An unexpected error occurred')
    return error_response(500, 'An unexpected error occurred')
