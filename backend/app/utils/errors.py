from flask import jsonify
from marshmallow import ValidationError
from functools import wraps

class APIError(Exception):
    """Custom API Error class"""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

def get_status_text(status_code):
    """Get HTTP status text for a status code"""
    status_texts = {
        200: 'OK',
        201: 'Created',
        204: 'No Content',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        409: 'Conflict',
        500: 'Internal Server Error'
    }
    return status_texts.get(status_code, 'Unknown')

class ValidationAPIError(APIError):
    """Validation error class"""
    def __init__(self, messages):
        super().__init__('Validation failed', 400)
        self.messages = messages

class AuthorizationError(APIError):
    """Authorization Error - Used for authentication failures (wrong credentials)"""
    def __init__(self, message='Invalid credentials'):
        super().__init__(message, 401)

class ForbiddenError(APIError):
    """Forbidden Error - Used for authorization failures (insufficient permissions)"""
    def __init__(self, message='Access forbidden'):
        super().__init__(message, 403)

class ResourceNotFoundError(APIError):
    """Resource Not Found"""
    def __init__(self, message='Resource not found'):
        super().__init__(message, 404)

def handle_api_error(error):
    """Handle API errors"""
    response = {
        'error': str(error),
        'message': str(error),
        'status': error.status_code,
        'status_text': get_status_text(error.status_code)
    }
    return jsonify(response), error.status_code

def handle_validation_error(error):
    """Handle Marshmallow validation errors"""
    return handle_api_error(ValidationAPIError(error.messages))

def handle_not_found_error(error):
    """Handle 404 errors"""
    return handle_api_error(ResourceNotFoundError())

def handle_generic_error(error):
    """Handle generic errors"""
    response = {
        'error': str(error),
        'message': 'Internal server error',
        'status': 500,
        'status_text': 'Internal Server Error'
    }
    return jsonify(response), 500

def init_error_handlers(app):
    """Initialize error handlers"""
    app.register_error_handler(APIError, handle_api_error)
    app.register_error_handler(ValidationError, handle_validation_error)
    app.register_error_handler(404, handle_not_found_error)
    app.register_error_handler(Exception, handle_generic_error)

def error_wrapper(f):
    """Wrapper to handle API errors"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            response = {
                'error': str(e),
                'message': str(e),
                'status': e.status_code,
                'status_text': get_status_text(e.status_code)
            }
            if isinstance(e, ValidationAPIError):
                response['messages'] = e.messages
            return jsonify(response), e.status_code
        except ValidationError as err:
            error = ValidationAPIError(err.messages)
            response = {
                'error': str(error),
                'message': str(error),
                'status': error.status_code,
                'status_text': get_status_text(error.status_code),
                'messages': error.messages
            }
            return jsonify(response), error.status_code
        except Exception as e:
            response = {
                'error': str(e),
                'message': 'Internal server error',
                'status': 500,
                'status_text': 'Internal Server Error'
            }
            return jsonify(response), 500
    return wrapped

@error_wrapper
def error_response(status_code, message, details=None):
    """Create error response"""
    error = APIError(message, status_code)
    return handle_api_error(error)
