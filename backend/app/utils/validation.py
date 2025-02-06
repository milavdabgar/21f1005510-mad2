"""Validation utilities for the application"""
from werkzeug.utils import secure_filename
import os
from flask import current_app
from .errors import ValidationAPIError, APIError

class DocumentValidator:
    """Validator for document uploads"""
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    @staticmethod
    def validate_professional_docs(id_proof, certification):
        """Validate professional documents"""
        if not id_proof or not certification:
            raise ValidationAPIError({'documents': 'Both ID proof and certification documents are required'})
        
        if not (DocumentValidator.is_valid_extension(id_proof.filename) and 
                DocumentValidator.is_valid_extension(certification.filename)):
            raise ValidationAPIError({'documents': 'Only PDF, JPG, JPEG, and PNG files are allowed'})
    
    @staticmethod
    def is_valid_extension(filename):
        """Check if file has an allowed extension"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in DocumentValidator.ALLOWED_EXTENSIONS

    @staticmethod
    def save_document(file, user_id, doc_type):
        """Save uploaded document and return path"""
        if not file:
            return None
        
        try:
            filename = secure_filename(f"{user_id}_{doc_type}_{file.filename}")
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
            os.makedirs(upload_dir, exist_ok=True)
            
            path = os.path.join(upload_dir, filename)
            file.save(path)
            return path
        except Exception as e:
            current_app.logger.error(f"Error saving document: {str(e)}")
            raise APIError(f"Error saving document: {str(e)}", 500)

class UserValidator:
    """Validator for user-related operations"""
    
    @staticmethod
    def validate_user_type(user_type):
        """Validate user type"""
        valid_types = {'customer', 'professional', 'admin'}
        if user_type.lower() not in valid_types:
            raise ValidationAPIError({'user_type': 'Invalid user type. Must be one of: customer, professional, admin'})
    
    @staticmethod
    def validate_registration_data(data, user_type):
        """Validate user registration data"""
        errors = []
        
        # Check required fields for all users
        required_fields = {'email', 'password', 'name', 'phone'}
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Additional fields for professionals
        if user_type == 'professional':
            professional_fields = {'service_type', 'experience'}
            missing_fields = [field for field in professional_fields if not data.get(field)]
            if missing_fields:
                errors.append(f"Missing required professional fields: {', '.join(missing_fields)}")
        
        # Additional fields for customers
        elif user_type == 'customer':
            customer_fields = {'address', 'pincode'}
            missing_fields = [field for field in customer_fields if not data.get(field)]
            if missing_fields:
                errors.append(f"Missing required customer fields: {', '.join(missing_fields)}")
        
        if errors:
            raise ValidationAPIError({'message': ' '.join(errors)})
    
    @staticmethod
    def validate_email_unique(User, email):
        """Validate email is not already registered"""
        if User.query.filter_by(email=email).first():
            raise ValidationAPIError({'message': 'Email already registered'})
