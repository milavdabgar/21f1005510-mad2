from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from ..models import Professional, Service, ServiceRequest, ProfessionalDocument, Admin, db
from ..schemas import (ProfessionalSchema, ServiceSchema, ServiceRequestSchema, ProfessionalDocumentSchema)
from ..utils.errors import error_wrapper, APIError
from ..utils.auth import professional_required, admin_required
from ..utils.api import (paginate_query, get_or_404, validate_request_status)
from ..utils.search import Search
from ..utils.stats import Statistics
from ..utils.cache import cache, invalidate_cache, user_cache
from datetime import datetime, timezone
import logging
import os
from flask import current_app

bp = Blueprint('professionals', __name__)
logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 300

# Constants for request statuses
REQUEST_STATUSES = {
    'new': [ServiceRequest.STATUS_ASSIGNED],  # New requests are only assigned ones
    'active': [ServiceRequest.STATUS_ACCEPTED],  # Active requests are accepted ones
    'completed': [ServiceRequest.STATUS_COMPLETED, ServiceRequest.STATUS_CLOSED],  # History shows completed and closed
    'all': [
        ServiceRequest.STATUS_REQUESTED,
        ServiceRequest.STATUS_ASSIGNED,
        ServiceRequest.STATUS_ACCEPTED,
        ServiceRequest.STATUS_REJECTED,
        ServiceRequest.STATUS_COMPLETED,
        ServiceRequest.STATUS_CLOSED
    ]
}

def utc_now():
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def get_current_professional():
    """Get current professional from JWT token"""
    email = get_jwt_identity()
    professional = Professional.query.filter_by(email=email).first()
    if not professional:
        raise APIError('Professional not found', 404)
    if not professional.active:
        raise APIError('Account is inactive', 403)
    return professional

def get_verified_professional():
    """Get current professional from JWT token and verify status"""
    professional = get_current_professional()
    if not professional.verified:
        raise APIError('Account not verified', 403)
    return professional

@bp.route('', methods=['GET'])
@error_wrapper
@cache(timeout=CACHE_TIMEOUT)
@jwt_required(optional=True)
def get_professionals():
    """Get all professionals with basic filtering"""
    # Get query parameters
    service_type = request.args.get('service_type')
    rating = request.args.get('rating')
    experience = request.args.get('experience')
    available = request.args.get('available', type=bool)

    # Start with base query
    query = Professional.query.filter_by(verified=True)

    # Apply filters
    if service_type:
        query = query.filter(Professional.service_type == service_type)
    if rating:
        try:
            rating = float(rating)
            query = query.filter(Professional.rating >= rating)
        except ValueError:
            raise APIError("Invalid rating value", 400)
    if experience:
        try:
            experience = int(experience)
            query = query.filter(Professional.experience >= experience)
        except ValueError:
            raise APIError("Invalid experience value", 400)
    if available is not None:
        query = query.filter_by(available=available)

    # Get paginated results
    schema = ProfessionalSchema(many=True)
    return paginate_query(query, schema)

@bp.route('/requests', methods=['GET'])
@jwt_required()
@professional_required()
@error_wrapper
def get_requests():
    """Get professional's service requests"""
    try:
        professional = get_current_professional()
        status = request.args.get('status')
        
        logger.debug(f"Getting requests for professional {professional.id} with status filter: {status}")

        # Start with base query
        query = (ServiceRequest.query
                .filter_by(professional_id=professional.id)
                .order_by(ServiceRequest.request_date.desc()))

        # Apply status filter if provided
        if status:
            if isinstance(status, str):
                status = [status]
            valid_statuses = []
            for s in status:
                if s in REQUEST_STATUSES:
                    valid_statuses.extend(REQUEST_STATUSES[s])
                else:
                    valid_statuses.append(s)
            logger.debug(f"Filtering by statuses: {valid_statuses}")
            query = query.filter(ServiceRequest.status.in_(valid_statuses))

        # Log the SQL query being executed
        logger.debug(f"SQL Query: {query}")
        
        # Get paginated results
        schema = ServiceRequestSchema(many=True)
        return paginate_query(query, schema)
        
    except Exception as e:
        logger.error(f"Error getting requests: {str(e)}")
        if isinstance(e, APIError):
            raise e
        raise APIError("Error getting requests", 500)

@bp.route('/requests/<int:request_id>/accept', methods=['POST'])
@jwt_required()
@professional_required()
@error_wrapper
def accept_request(request_id):
    """Accept a service request"""
    try:
        professional = get_current_professional()
        request = get_or_404(ServiceRequest, request_id)
        
        # Validate request status - should be 'assigned' to accept
        validate_request_status(request, professional.id, ServiceRequest.STATUS_ASSIGNED)
        
        # Update request status to accepted
        request.status = ServiceRequest.STATUS_ACCEPTED
        request.assigned_at = utc_now()
        
        # Update professional's availability and current request
        professional.available = False
        professional.current_request = request_id
        
        db.session.commit()
        
        # Return updated request
        schema = ServiceRequestSchema()
        return schema.dump(request), 200
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, APIError):
            raise e
        logger.error(f"Error accepting request: {str(e)}")
        raise APIError("Error accepting request", 500)

@bp.route('/requests/<int:request_id>/reject', methods=['POST'])
@jwt_required()
@professional_required()
@error_wrapper
def reject_request(request_id):
    """Reject a service request"""
    try:
        professional = get_current_professional()
        request = get_or_404(ServiceRequest, request_id)
        
        # Validate request status - should be 'assigned' to reject
        validate_request_status(request, professional.id, ServiceRequest.STATUS_ASSIGNED)
        
        # Update request status to rejected
        request.status = ServiceRequest.STATUS_REJECTED
        request.rejected_at = utc_now()
        
        # Update professional's availability
        professional.available = True
        professional.current_request = None
        
        db.session.commit()
        
        # Return updated request
        schema = ServiceRequestSchema()
        return schema.dump(request), 200
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, APIError):
            raise e
        logger.error(f"Error rejecting request: {str(e)}")
        raise APIError("Error rejecting request", 500)

@bp.route('/requests/<int:request_id>/complete', methods=['POST'])
@jwt_required()
@professional_required()
@error_wrapper
def complete_request(request_id):
    """Complete a service request"""
    try:
        professional = get_current_professional()
        request = get_or_404(ServiceRequest, request_id)
        
        # Validate request status - must be 'accepted' to complete
        validate_request_status(request, professional.id, ServiceRequest.STATUS_ACCEPTED)
        
        # Update request status
        request.status = ServiceRequest.STATUS_COMPLETED
        request.completion_date = utc_now()
        
        # Update professional's availability
        professional.available = True
        professional.current_request = None
        
        db.session.commit()
        
        # Return updated request
        schema = ServiceRequestSchema()
        return schema.dump(request), 200
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, APIError):
            raise e
        logger.error(f"Error completing request: {str(e)}")
        raise APIError("Error completing request", 500)

@bp.route('/availability', methods=['PUT'])
@jwt_required()
@professional_required()
@error_wrapper
def update_availability():
    """Update professional's availability"""
    try:
        professional = get_current_professional()
        data = request.get_json()

        if not isinstance(data.get('available'), bool):
            raise APIError("Invalid availability value", 400)

        professional.available = data['available']
        db.session.commit()

        # Invalidate cache
        invalidate_cache('get_professionals')

        schema = ProfessionalSchema()
        return schema.dump(professional)
    except APIError as e:
        raise
    except Exception as e:
        logger.error(f"Error in update_availability: {str(e)}")
        raise APIError("Internal server error", 500)

@bp.route('/documents', methods=['GET'])
@jwt_required()
@professional_required()
@error_wrapper
@user_cache(timeout=CACHE_TIMEOUT)
def get_documents():
    """Get professional's verification documents"""
    try:
        professional = get_current_professional()
        documents = ProfessionalDocument.query.filter_by(professional_id=professional.id).all()
        schema = ProfessionalDocumentSchema(many=True)
        return schema.dump(documents)
    except Exception as e:
        logger.error(f"Error in get_documents: {str(e)}")
        raise APIError("Internal server error", 500)

@bp.route('/documents', methods=['POST'])
@jwt_required()
@professional_required()
@error_wrapper
def upload_document():
    """Upload a verification document"""
    if 'file' not in request.files:
        raise APIError("No file uploaded", 400)
    
    file = request.files['file']
    if not file.filename:
        raise APIError("No file selected", 400)

    # Validate file type
    allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg'}
    if not '.' in file.filename or \
       file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        raise APIError("Invalid file type. Allowed types: pdf, png, jpg, jpeg", 400)

    # Validate document type
    document_type = request.form.get('document_type')
    if not document_type or document_type not in ['id_proof', 'certification', 'license']:
        raise APIError("Invalid document type", 400)

    professional = get_current_professional()
    
    try:
        # Create document record
        document = ProfessionalDocument(
            professional_id=professional.id,
            document_type=document_type,
            file_path='',  # Will be updated after saving file
            verified=False
        )
        
        # Save document first to get ID
        db.session.add(document)
        db.session.flush()
        
        # Get project root directory (one level up from app)
        project_root = os.path.dirname(current_app.root_path)
        
        # Ensure upload directory exists for this professional
        upload_dir = os.path.join(project_root, 'uploads', str(professional.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file with relative path for storage
        filename = f"{document.id}_{document_type}_{file.filename}"
        file_path = os.path.join('uploads', str(professional.id), filename)
        absolute_path = os.path.join(project_root, file_path)
        
        # Save the file using absolute path but store relative path
        file.save(absolute_path)
        document.file_path = file_path
        
        # Commit changes
        db.session.commit()
        
        # Return created document
        schema = ProfessionalDocumentSchema()
        result = schema.dump(document)
        if not 'id' in result:
            result['id'] = document.id
        return result, 201
        
    except Exception as e:
        logger.error(f"Error saving document: {str(e)}")
        db.session.rollback()
        raise APIError("Error saving document", 500)  

@bp.route('/documents/<int:document_id>/verify', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def verify_document(document_id):
    """Verify a professional's document (Admin only)"""
    try:
        document = db.session.get(ProfessionalDocument, document_id)
        if not document:
            raise APIError("Document not found", 404)
        
        # Check if already verified
        if document.verified:
            raise APIError("Document is already verified", 400)
            
        # Validate document type
        if document.document_type not in {'id_proof', 'certification', 'license'}:
            raise APIError("Invalid document type", 400)
        
        # Get admin user
        admin_email = get_jwt_identity()
        admin = Admin.query.filter_by(email=admin_email).first()
        if not admin:
            raise APIError("Admin not found", 404)
        
        # Update document status
        document.verified = True
        document.verified_by = admin.id
        document.verified_at = utc_now()
        
        # Check if all documents are verified
        professional = document.professional
        if professional:
            required_docs = {'id_proof', 'certification', 'license'}
            verified_docs = {doc.document_type for doc in professional.documents if doc.verified}
            
            if required_docs.issubset(verified_docs):
                professional.verified = True
                professional.verified_at = utc_now()
                professional.verified_by = admin.id
                professional.status = 'approved'
        
        db.session.commit()
        
        # Return updated document
        schema = ProfessionalDocumentSchema()
        result = schema.dump(document)
        if not 'id' in result:
            result['id'] = document.id
        return result, 200
        
    except APIError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error verifying document: {str(e)}")
        raise APIError("Error verifying document", 500)

@bp.route('/profile', methods=['GET'])
@jwt_required()
@professional_required()
@error_wrapper
@user_cache(timeout=CACHE_TIMEOUT)
def get_profile():
    """Get professional profile"""
    professional = get_current_professional()
    schema = ProfessionalSchema()
    return schema.dump(professional)

@bp.route('/profile', methods=['PUT'])
@jwt_required()
@professional_required()
@error_wrapper
def update_profile():
    """Update professional profile"""
    professional = get_verified_professional()  # Only verified professionals can update
    data = request.get_json()
    
    # Update professional-specific fields
    allowed_fields = {'experience', 'service_type', 'available'}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    try:
        # Update fields
        for key, value in update_data.items():
            setattr(professional, key, value)
        
        db.session.commit()
        invalidate_cache('get_profile')
        return ProfessionalSchema().dump(professional)
        
    except Exception as e:
        db.session.rollback()
        raise APIError(str(e), 400)

def init_app(app):
    """Initialize professional blueprint with app"""
    # Register error handlers at application level
    @app.errorhandler(401)
    def handle_401(e):
        return {"error": "Unauthorized access"}, 401

    @app.errorhandler(404)
    def handle_404(e):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(Exception)
    def handle_error(e):
        if isinstance(e, APIError):
            return {"error": str(e)}, e.status_code
        logger.error(f"Unhandled error: {str(e)}")
        return {"error": "Internal server error"}, 500

    # Register blueprint
    app.register_blueprint(bp, url_prefix='/api/professionals')
