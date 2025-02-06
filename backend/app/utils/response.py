"""Utility functions for standardizing API responses"""

class APIResponse:
    @staticmethod
    def success(data=None, message=None, status_code=200):
        """Create a success response"""
        response = {}
        if data is not None:
            response.update(data)
        if message:
            response['message'] = message
        return response, status_code

    @staticmethod
    def error(message, code=400, details=None):
        """Create an error response"""
        response = {
            'message': message,
            'code': code
        }
        if details:
            response['details'] = details
        return response, code
