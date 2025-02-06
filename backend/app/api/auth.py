from flask import Blueprint, request, jsonify, current_app, abort
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, get_jwt
from app.models import User, Customer, Professional, Admin, db, ProfessionalDocument
from ..schemas import (UserSchema, CustomerSchema, ProfessionalSchema, AdminSchema,
                      block_user_schema, professionals_list_schema, users_search_schema,
                      user_search_params_schema)
from ..utils.errors import error_wrapper, APIError, ValidationAPIError, AuthorizationError, ForbiddenError
from ..utils.validation import DocumentValidator, UserValidator
from ..utils.response import APIResponse
from marshmallow import ValidationError

bp = Blueprint('auth', __name__)

# Initialize schemas
user_schema = UserSchema()
customer_schema = CustomerSchema()
professional_schema = ProfessionalSchema()
admin_schema = AdminSchema()

USER_SCHEMAS = {
    'customer': customer_schema,
    'professional': professional_schema,
    'admin': admin_schema
}

USER_MODELS = {
    'customer': Customer,
    'professional': Professional,
    'admin': Admin
}

def create_user_response(user, access_token=None):
    """Create standardized user response"""
    response = {
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'phone': user.phone,
            'type': user.__class__.__name__.lower()
        }
    }
    
    # Add professional specific fields
    if isinstance(user, Professional):
        response['user'].update({
            'service_type': user.service_type,
            'experience': user.experience,
            'status': user.status,
            'id_proof_path': user.id_proof_path,
            'certification_path': user.certification_path
        })
        if user.status == 'pending':
            response['message'] = 'Please wait for admin approval'
    
    if access_token:
        response['access_token'] = access_token
    
    return response

def create_error_response(message, status_code, details=None):
    """Create standardized error response"""
    response = {
        'message': message,
        'status': status_code
    }
    if details:
        response['details'] = details
    return jsonify(response), status_code

@bp.route('/register', methods=['POST'])
@error_wrapper
def register():
    """Register a new user"""
    try:
        # Check if request is multipart form data
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        
        # Get data based on content type
        if is_multipart:
            data = request.form.to_dict()
            id_proof = request.files.get('id_proof')
            certification = request.files.get('certification')
        else:
            data = request.get_json()
            id_proof = certification = None
            
        # Get and validate user type
        user_type = data.get('type', 'customer').lower()
        UserValidator.validate_user_type(user_type)
        
        # Check for professional documents first
        if user_type == 'professional':
            if not id_proof or not certification:
                return jsonify({'message': 'Documents required for professional registration'}), 400
            DocumentValidator.validate_professional_docs(id_proof, certification)
        
        # Validate registration data
        UserValidator.validate_registration_data(data, user_type)
        
        # Validate email uniqueness
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 400
        
        # Create user based on type
        if user_type == 'professional':
            user = Professional()
        elif user_type == 'customer':
            user = Customer()
        else:
            return jsonify({'message': 'Invalid user type'}), 400
        
        # Set common fields
        user.email = data['email']
        user.name = data['name']
        user.phone = data['phone']
        user.set_password(data['password'])
        
        # Set type-specific fields
        if user_type == 'customer':
            user.address = data['address']
            user.pincode = data['pincode']
        elif user_type == 'professional':
            user.service_type = data['service_type']
            user.experience = data['experience']
            
            # Save user first to get the ID
            db.session.add(user)
            db.session.commit()
            
            # Save documents and create document entries
            id_proof_path = DocumentValidator.save_document(id_proof, user.id, 'id_proof')
            certification_path = DocumentValidator.save_document(certification, user.id, 'certification')
            
            # Set paths in professional record
            user.id_proof_path = id_proof_path
            user.certification_path = certification_path
            user.status = 'pending'
            
            # Create document entries in professional_document table
            id_proof_doc = ProfessionalDocument(
                professional_id=user.id,
                document_type='id_proof',
                file_path=id_proof_path
            )
            certification_doc = ProfessionalDocument(
                professional_id=user.id,
                document_type='certification',
                file_path=certification_path
            )
            
            # Add documents to session
            db.session.add(id_proof_doc)
            db.session.add(certification_doc)
        
        # Save user (for customers or final save for professionals)
        if user_type == 'customer':
            db.session.add(user)
        db.session.commit()
        
        # Generate access token for non-professional users
        access_token = None
        if user_type != 'professional':
            access_token = create_access_token(identity=user.email)
        
        # Create response
        response_data = create_user_response(user, access_token)
        return jsonify(response_data), 201
        
    except ValidationAPIError as e:
        return jsonify(e.errors), 400
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred'}), 500

@bp.route('/login', methods=['POST'])
@error_wrapper
def login():
    """Login user and return access token"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400
        
        # Query for the specific user type
        user = User.query.filter_by(email=email).first()
        
        if not user:
            raise APIError('Invalid email or password', 401)
            
        if not user.check_password(password):
            raise APIError('Invalid email or password', 401)
            
        if not user.active:
            raise APIError('Account is blocked', 401)
            
        # For professionals, check registration status
        if isinstance(user, Professional):
            if user.status == 'pending':
                return jsonify({'message': 'Your account is pending admin approval'}), 403
            elif user.status == 'rejected':
                return jsonify({'message': 'Your registration has been rejected'}), 403
            elif user.status != 'approved':
                return jsonify({'message': 'Your account status is invalid'}), 403
        
        # Create access token and response
        access_token = create_access_token(identity=user.email)
        response_data = create_user_response(user, access_token)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred'}), 500

@bp.route('/profile', methods=['GET'])
@jwt_required()
@error_wrapper
def get_profile():
    """Get user profile"""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first_or_404()
    return jsonify(create_user_response(user))

@bp.route('/profile', methods=['PUT'])
@jwt_required()
@error_wrapper
def update_profile():
    """Update user profile"""
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first_or_404()
    
    data = request.get_json()
    
    # Only allow updating non-sensitive fields
    allowed_fields = {'name', 'phone'}
    if user.type.lower() == 'professional':
        allowed_fields.update({'experience', 'service_type'})
    
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    try:
        # Update user fields
        for key, value in update_data.items():
            setattr(user, key, value)
    
        db.session.commit()
        return jsonify(create_user_response(user))
        
    except ValidationError as err:
        db.session.rollback()
        raise ValidationAPIError(err.messages)
    except Exception as e:
        db.session.rollback()
        raise

@bp.route('/admin/professionals', methods=['GET'])
@jwt_required()
@error_wrapper
def list_professionals():
    """List all professionals with their verification status"""
    if not get_jwt()['is_admin']:
        raise AuthorizationError("Admin access required")
    
    professionals = Professional.query.all()
    return jsonify(professionals_list_schema.dump(professionals))

@bp.route('/admin/professionals/<int:id>/approve', methods=['POST'])
@jwt_required()
@error_wrapper
def approve_professional(id):
    """Approve a professional's registration"""
    if not get_jwt()['is_admin']:
        raise AuthorizationError("Admin access required")
    
    professional = db.session.get(Professional, id)
    if not professional:
        abort(404, description="Professional not found")
    
    try:
        professional.approve(get_jwt()['sub'])
        db.session.commit()
        return jsonify({'message': 'Professional approved successfully'})
    except Exception as e:
        db.session.rollback()
        raise

@bp.route('/admin/professionals/<int:id>/reject', methods=['POST'])
@jwt_required()
@error_wrapper
def reject_professional(id):
    """Reject a professional's registration"""
    if not get_jwt()['is_admin']:
        raise AuthorizationError("Admin access required")
    
    try:
        data = block_user_schema.load(request.get_json())
        professional = db.session.get(Professional, id)
        if not professional:
            abort(404, description="Professional not found")
        professional.reject(get_jwt()['sub'], data.get('reason'))
        return jsonify({'message': 'Professional rejected successfully'})
    except ValidationError as err:
        raise ValidationAPIError(err.messages)

@bp.route('/admin/users/search', methods=['GET'])
@jwt_required()
@error_wrapper
def search_users():
    """Search users by email, name, or phone"""
    if not get_jwt()['is_admin']:
        raise AuthorizationError("Admin access required")
    
    try:
        params = user_search_params_schema.load(request.args)
        users_query = User.query
        
        if params.get('type'):
            users_query = users_query.filter(User.type == params['type'])
        
        if params.get('q'):
            users_query = users_query.filter(
                db.or_(
                    User.email.ilike(f'%{params["q"]}%'),
                    User.name.ilike(f'%{params["q"]}%'),
                    User.phone.ilike(f'%{params["q"]}%')
                )
            )
        
        users = users_query.all()
        return jsonify(users_search_schema.dump(users))
    except ValidationError as err:
        raise ValidationAPIError(err.messages)
