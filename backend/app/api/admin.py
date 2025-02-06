from flask import Blueprint, request, jsonify, current_app, send_from_directory
from app.models import User, Professional, Service, ServiceRequest, Customer, Admin, ProfessionalDocument
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..schemas import (
    UserSchema, CustomerSchema, ProfessionalSchema, ServiceSchema,
    ServiceRequestSchema, AdminSchema, ProfessionalDocumentSchema
)
from app.extensions import db
from app.utils.auth import admin_required, user_required
from app.utils.errors import APIError, error_wrapper, ValidationAPIError, ResourceNotFoundError
from app.utils.api import paginate_query, filter_query
from datetime import datetime, timedelta
import pytz
import os
from app.utils.cache import user_cache
from sqlalchemy import func

bp = Blueprint('admin', __name__)

def init_upload_dir(state):
    """Create upload directory if it doesn't exist"""
    app = state.app
    uploads_dir = os.path.join(app.root_path, 'uploads', 'documents')
    os.makedirs(uploads_dir, exist_ok=True)

bp.record(init_upload_dir)

@bp.route('/users/<int:user_id>/status', methods=['PUT', 'OPTIONS'])
def update_user_status(user_id):
    """Update user's active status"""
    if request.method == 'OPTIONS':
        return '', 200
        
    @jwt_required()
    @admin_required()
    @error_wrapper
    def handle_request():
        try:
            user = db.session.get(User, user_id)
            if not user:
                raise APIError('User not found', 404)

            data = request.get_json()
            if not data or 'active' not in data:
                raise APIError('Active status is required', 400)
                
            if data['active']:
                user.unblock()
            else:
                user.block()
                
            return jsonify({
                'active': user.active,
                'message': f'User {"unblocked" if user.active else "blocked"} successfully'
            }), 200
        except Exception as e:
            current_app.logger.error(f"Error updating user status: {str(e)}")
            db.session.rollback()
            raise APIError(f'Failed to update user status: {str(e)}', 500)
            
    return handle_request()

@bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
def get_users():
    """Get all users with filters"""
    status = request.args.get('status')
    type = request.args.get('type')  # professional, customer, admin

    query = User.query

    # Filter by status if provided
    if status:
        if status == 'blocked':
            query = query.filter_by(active=False)
        elif status == 'active':
            query = query.filter_by(active=True)
        elif status == 'pending':
            # For professionals only
            query = query.join(Professional).filter(Professional.status == 'pending')
        elif status == 'approved':
            # For professionals only
            query = query.join(Professional).filter(Professional.status == 'approved')
        else:
            raise APIError('Invalid status', 400)

    if type:
        if type not in ['professional', 'customer', 'admin']:
            raise APIError('Invalid user type', 400)
        query = query.filter_by(type=type)

    query = apply_search_filter(query, User)
    return paginate_query(query, UserSchema(many=True))

@bp.route('/professionals', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
def get_professionals():
    """Get all professionals with filters"""
    query = Professional.query

    # Apply filters
    filters = {
        'status': request.args.get('status', 'approved'),  # Default to approved professionals
        'available': request.args.get('available', type=bool),
        'service_id': request.args.get('service_id', type=int),
        'verified': request.args.get('verified', True)  # Default to verified professionals
    }
    
    # Apply non-None filters
    for key, value in filters.items():
        if value is not None:
            query = query.filter_by(**{key: value})

    query = apply_search_filter(query, Professional)
    return paginate_query(query, ProfessionalSchema(many=True))

@bp.route('/customers', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
def get_customers():
    """Get all customers with filters"""
    query = Customer.query

    if status := request.args.get('status'):
        query = query.filter_by(status=status)

    query = apply_search_filter(query, Customer)
    return paginate_query(query, CustomerSchema(many=True))

@bp.route('/professionals/<int:professional_id>/verify', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def verify_professional(professional_id):
    """Verify a professional's account after document verification"""
    data = request.json
    approved = data.get('approved', True)
    comment = data.get('comment', '')

    professional = Professional.query.filter_by(id=professional_id).first()
    if not professional:
        raise APIError('Professional not found', 404)

    # Get admin user
    admin_email = get_jwt_identity()
    admin = Admin.query.filter_by(email=admin_email).first()
    if not admin:
        raise APIError('Admin not found', 404)

    # Update professional and their documents
    if approved:
        professional.status = 'approved'
        professional.verified_at = datetime.now(pytz.utc)
        professional.verified_by = admin.id

        # Update all documents
        documents = ProfessionalDocument.query.filter_by(professional_id=professional_id).all()
        for doc in documents:
            doc.verified = True
            doc.verified_at = datetime.now(pytz.utc)
            doc.verified_by = admin.id
            doc.verification_comment = comment if comment else 'Approved by admin'
    else:
        professional.status = 'rejected'
        professional.verified_at = None
        professional.verified_by = None
        professional.rejection_reason = comment

        # Update all documents
        documents = ProfessionalDocument.query.filter_by(professional_id=professional_id).all()
        for doc in documents:
            doc.verified = False
            doc.verified_at = None
            doc.verified_by = None
            doc.verification_comment = comment if comment else 'Rejected by admin'

    db.session.commit()

    return {'success': True, 'message': 'Professional verification status updated'}

@bp.route('/requests/<int:request_id>/assign', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def assign_request(request_id):
    try:
        data = request.get_json()
    except Exception as e:
        raise APIError('Invalid JSON data', 400)
    
    if not data:
        raise APIError('No data provided', 400)
    
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    professional_id = data.get('professional_id')
    
    if not professional_id:
        raise APIError('Professional ID is required', 400)
        
    professional = Professional.query.get_or_404(professional_id)
        
    if not professional.available:
        raise APIError('Professional is not available', 400)
        
    # Allow assignment for both requested and rejected status
    if service_request.status not in [ServiceRequest.STATUS_REQUESTED, ServiceRequest.STATUS_REJECTED]:
        raise APIError('Request must be in requested or rejected state', 400)
        
    # For rejected requests, we need to clear the previous assignment first
    if service_request.status == ServiceRequest.STATUS_REJECTED:
        # If the previous professional is still assigned to this request, mark them as available
        if service_request.professional and service_request.professional.current_request == request_id:
            service_request.professional.current_request = None
            service_request.professional.available = True
            service_request.status = ServiceRequest.STATUS_ASSIGNED
    # For new requests, check if it's already assigned
    elif service_request.professional_id:
        raise APIError('Request is already assigned', 400)
        
    service_request.professional_id = professional_id
    service_request.status = ServiceRequest.STATUS_ASSIGNED
    professional.current_request = request_id
    professional.available = False
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise APIError('Failed to save changes', 500)

    result = ServiceRequestSchema().dump(service_request)
    return result

@bp.route('/requests/<int:request_id>/unassign', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def unassign_request(request_id):
    """Unassign a professional from a service request"""
    service_request = ServiceRequest.query.get_or_404(request_id)
    
    if not service_request.professional_id:
        raise APIError('Request is not assigned to any professional', 400)
        
    if service_request.status != 'assigned':
        raise APIError('Request is not in assigned state', 400)
    
    # Get the professional before we remove the reference
    professional = Professional.query.get(service_request.professional_id)
    if professional:
        professional.current_request = None
        professional.available = True
    
    service_request.professional_id = None
    service_request.status = 'requested'
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise APIError('Failed to save changes', 500)

    return ServiceRequestSchema().dump(service_request)

@bp.route('/requests', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
def get_requests():
    """Get all service requests with filters"""
    filters = {
        'status': request.args.get('status'),
        'customer_id': request.args.get('customer_id', type=int),
        'professional_id': request.args.get('professional_id', type=int),
        'service_id': request.args.get('service_id', type=int)
    }
    
    query = ServiceRequest.query
    filtered_query = filter_query(query, ServiceRequest, **{k: v for k, v in filters.items() if v is not None})
    return paginate_query(filtered_query, ServiceRequestSchema(many=True))

@bp.route('/professionals/<int:professional_id>/documents', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
def get_professional_documents(professional_id):
    """Get professional's verification documents"""
    professional = Professional.query.filter_by(id=professional_id).first()
    if not professional:
        raise APIError('Professional not found', 404)

    # Return the documents
    documents = []
    
    # Get documents from ProfessionalDocument model
    professional_docs = ProfessionalDocument.query.filter_by(professional_id=professional_id).all()
    
    for doc in professional_docs:
        documents.append({
            'id': doc.id,
            'name': doc.document_type.replace('_', ' ').title(),
            'type': doc.document_type,
            'url': doc.file_path,
            'verified': doc.verified,
            'verified_at': doc.verified_at.isoformat() if doc.verified_at else None
        })
    
    return jsonify(documents)

@bp.route('/documents/<path:filepath>', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
def get_document_file(filepath):
    """Serve document files"""
    try:
        # Extract professional ID from the path (uploads/professional_id/filename)
        parts = filepath.split('/')
        if len(parts) != 2:
            raise APIError("Invalid file path", 400)
            
        professional_id = parts[0]
        filename = parts[1]
        
        # Ensure no path traversal
        if '..' in filepath or filepath.startswith('/'):
            raise APIError("Invalid filepath", 400)
            
        # Get project root directory (one level up from app)
        project_root = os.path.dirname(current_app.root_path)
            
        # Documents are stored in uploads/professional_id directory
        uploads_dir = os.path.join(project_root, 'uploads', professional_id)
        file_path = os.path.join(uploads_dir, filename)
        
        if not os.path.exists(file_path):
            current_app.logger.error(f"File not found at path: {file_path}")
            raise APIError("File not found", 404)
            
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
    except Exception as e:
        current_app.logger.error(f"Error serving file {filepath}: {str(e)}")
        raise APIError("File not found", 404)

@bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@admin_required()
@error_wrapper
@user_cache(timeout=300)
def get_dashboard_stats():
    """Get admin dashboard statistics"""
    # Get date range from query params
    days = int(request.args.get('days', 30))
    end_date = datetime.now(pytz.utc)
    start_date = end_date - timedelta(days=days)

    # Total users count
    total_users = User.query.count()
    total_professionals = Professional.query.count()
    total_customers = Customer.query.count()

    # Recent activity counts
    recent_users = User.query.filter(User.created_at >= start_date).count()
    recent_professionals = Professional.query.filter(Professional.created_at >= start_date).count()
    recent_customers = Customer.query.filter(Customer.created_at >= start_date).count()

    # Service requests stats
    total_requests = ServiceRequest.query.count()
    recent_requests = ServiceRequest.query.filter(ServiceRequest.request_date >= start_date).count()
    pending_requests = ServiceRequest.query.filter_by(status='pending').count()
    completed_requests = ServiceRequest.query.filter_by(status='completed').count()

    return {
        'total_users': total_users,
        'total_professionals': total_professionals,
        'total_customers': total_customers,
        'recent_users': recent_users,
        'recent_professionals': recent_professionals,
        'recent_customers': recent_customers,
        'total_requests': total_requests,
        'recent_requests': recent_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests
    }

@bp.route('/export/service-requests', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def export_service_requests():
    """Trigger export of service requests to CSV"""
    current_user = get_jwt_identity()
    admin = Admin.query.get(current_user)
    
    if not admin or not admin.email:
        return jsonify({'message': 'Admin email not found'}), 400
    
    from app.jobs import export_service_requests
    task = export_service_requests.delay(admin.id)
    
    return jsonify({
        'message': 'Export started. You will receive the CSV file via email.',
        'task_id': str(task.id)
    }), 202

@bp.route('/export/service-requests/<int:prof_id>', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def export_service_requests_prof(prof_id):
    """Trigger export of service requests to CSV for a specific professional"""
    professional = Professional.query.get(prof_id)
    if not professional:
        return jsonify({'message': 'Professional not found'}), 404
    
    from app.jobs import export_service_requests as export_task
    task = export_task.delay(prof_id)
    
    return jsonify({
        'message': f'Export started for professional {professional.name}. The file will be sent via email.',
        'task_id': str(task.id)
    }), 202

@bp.route('/services', methods=['GET'])
@error_wrapper
@admin_required()
def get_admin_services():
    """Get all services with pagination for admin"""
    try:
        query = Service.query

        # Search by name or description
        search = request.args.get('search')
        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(
                db.or_(
                    func.lower(Service.name).like(search_term),
                    func.lower(Service.description).like(search_term),
                    func.lower(Service.type).like(search_term)
                )
            )

        # Filter by type if provided
        service_type = request.args.get('type')
        if service_type:
            query = query.filter(func.lower(Service.type) == service_type.lower())

        # Filter by price range
        min_price = request.args.get('minPrice')
        max_price = request.args.get('maxPrice')
        if min_price:
            query = query.filter(Service.price >= float(min_price))
        if max_price:
            query = query.filter(Service.price <= float(max_price))

        # Sort by different criteria
        sort_by = request.args.get('sortBy', 'name')
        if sort_by == 'price_low':
            query = query.order_by(Service.price.asc())
        elif sort_by == 'price_high':
            query = query.order_by(Service.price.desc())
        else:  # default to name
            query = query.order_by(Service.name.asc())

        services = query.all()
        schema = ServiceSchema(many=True)
        result = schema.dump(services)
        return jsonify({
            "items": result,
            "total": len(result)
        })
    except Exception as e:
        logger.error(f"Error fetching admin services: {str(e)}")
        return jsonify({"error": "Error fetching services"}), 500

def apply_search_filter(query, model):
    """Apply search filter to query if search parameter exists"""
    if search := request.args.get('q'):
        return query.filter(
            model.name.ilike(f'%{search}%') |
            model.email.ilike(f'%{search}%')
        )
    return query
