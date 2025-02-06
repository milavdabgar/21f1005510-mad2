from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from ..models import Customer, Service, ServiceRequest, db, User, Professional
from ..schemas import (CustomerSchema, CustomerProfileSchema, ServiceSchema, ServiceRequestSchema,
                    CreateServiceRequestSchema)
from ..utils.errors import error_wrapper, APIError
from ..utils.auth import customer_required
from ..utils.api import paginate_query, validate_schema, get_or_404
from ..utils.search import Search
from ..utils.stats import Statistics
from ..utils.cache import cache, invalidate_cache, user_cache
from datetime import datetime, timezone
import logging

bp = Blueprint('customers', __name__)

def get_current_customer():
    """Get current customer from JWT token"""
    email = get_jwt_identity()
    customer = Customer.query.filter_by(email=email).first()
    if not customer:
        raise APIError('Customer not found', 404)
    if not customer.active:
        raise APIError('Account is inactive', 403)
    return customer

def get_customer_request(request_id, customer_id):
    """Get and validate customer's service request"""
    request = ServiceRequest.query.filter_by(id=request_id).first()
    if not request:
        raise APIError('Service request not found', 404)
    if request.customer_id != customer_id:
        raise APIError('Unauthorized access', 403)
    return request

def validate_request_status(request, allowed_statuses):
    """Validate service request status"""
    if request.status not in allowed_statuses:
        raise APIError(f'Cannot perform action on request in {request.status} status', 400)

# Profile Management
@bp.route('/profile', methods=['GET'])
@jwt_required()
@customer_required()
@error_wrapper
@user_cache(timeout=300)
def get_profile():
    """Get customer profile"""
    customer = get_current_customer()
    return {
        'user': CustomerSchema().dump(customer),
        'address': customer.address,
        'pincode': customer.pincode
    }

@bp.route('/profile', methods=['PUT'])
@jwt_required()
@customer_required()
@error_wrapper
@validate_schema(CustomerProfileSchema)
def update_profile(data):
    """Update customer profile"""
    customer = get_current_customer()
    
    # Update fields
    for key, value in data.items():
        if hasattr(customer, key):
            setattr(customer, key, value)
    
    db.session.commit()
    invalidate_cache('get_profile')
    return CustomerSchema().dump(customer)

# Service Discovery
@bp.route('/services', methods=['GET'])
@jwt_required()
@customer_required()
@error_wrapper
def list_services():
    """List available services with optional filtering"""
    filters = {
        'type': request.args.get('type'),
        'search': request.args.get('search'),
        'min_price': request.args.get('min_price', type=float),
        'max_price': request.args.get('max_price', type=float),
        'location': request.args.get('location')
    }
    
    query = Service.query
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        query = query.filter(
            or_(
                Service.name.ilike(search_term),
                Service.description.ilike(search_term)
            )
        )
    
    if filters.get('type'):
        query = query.filter(Service.type == filters['type'])
    
    if filters.get('min_price'):
        query = query.filter(Service.price >= filters['min_price'])
    
    if filters.get('max_price'):
        query = query.filter(Service.price <= filters['max_price'])
    
    return paginate_query(query, ServiceSchema(many=True))

@bp.route('/services/categories', methods=['GET'])
@jwt_required()
@customer_required()
@error_wrapper
def list_service_categories():
    """Get all available service categories for customers"""
    categories = db.session.query(Service.type).distinct().all()
    
    # Format categories with name and description
    formatted_categories = {
        'items': [
            {
                'type': type_name,
                'name': type_name.capitalize() + ' Services',
                'description': f'Professional {type_name} services for your needs'
            } for (type_name,) in categories
        ],
        'total': len(categories)
    }
    
    return jsonify(formatted_categories)

@bp.route('/requests', methods=['GET'])
@jwt_required()
@customer_required()
@error_wrapper
def list_requests():
    """List customer's service requests"""
    try:
        customer = get_current_customer()
        filters = {
            'status': request.args.get('status'),
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'customer_id': customer.id
        }
        
        # Build base query
        query = ServiceRequest.query.filter_by(customer_id=customer.id)
        
        # Apply filters
        if filters.get('status'):
            query = query.filter(ServiceRequest.status == filters['status'])
            
        if filters.get('start_date'):
            query = query.filter(ServiceRequest.request_date >= filters['start_date'])
            
        if filters.get('end_date'):
            query = query.filter(ServiceRequest.request_date <= filters['end_date'])
        
        # Add ordering
        query = query.order_by(ServiceRequest.request_date.desc())
        
        # Return paginated results
        return paginate_query(query, ServiceRequestSchema(many=True))
        
    except Exception as e:
        current_app.logger.error(f"Error in list_requests: {str(e)}")
        raise APIError("Error retrieving service requests", 500)

@bp.route('/requests', methods=['POST'])
@jwt_required()
@customer_required()
@error_wrapper
@validate_schema(CreateServiceRequestSchema)
def create_request(data):
    """Create a new service request"""
    customer = get_current_customer()
    service = db.session.get(Service, data['service_id'])
    if not service:
        raise APIError('Service not found', 404)
    
    service_request = ServiceRequest(
        service_id=service.id,
        customer_id=customer.id,
        remarks=data.get('remarks', ''),
        request_date=datetime.now()
    )
    db.session.add(service_request)
    db.session.commit()

    # Invalidate stats cache
    invalidate_cache('get_stats*')

    return ServiceRequestSchema().dump(service_request), 201

@bp.route('/requests/<int:request_id>', methods=['GET'])
@jwt_required()
@customer_required()
@error_wrapper
def get_request(request_id):
    """Get service request details"""
    customer = get_current_customer()
    request = get_customer_request(request_id, customer.id)
    return ServiceRequestSchema().dump(request)

@bp.route('/requests/<int:request_id>/cancel', methods=['POST'])
@jwt_required()
@customer_required()
@error_wrapper
def cancel_request(request_id):
    """Cancel a service request"""
    customer = get_current_customer()
    request = get_customer_request(request_id, customer.id)
    validate_request_status(request, ['requested', 'assigned'])
    
    request.status = 'cancelled'
    db.session.commit()

    # Invalidate stats cache
    invalidate_cache('get_stats*')

    return ServiceRequestSchema().dump(request)

@bp.route('/requests/<int:request_id>/complete', methods=['POST'])
@jwt_required()
@customer_required()
@error_wrapper
def complete_request(request_id):
    """Mark a service request as completed"""
    customer = get_current_customer()
    request = get_customer_request(request_id, customer.id)
    validate_request_status(request, ['in_progress'])
    
    request.status = 'completed'
    request.completion_date = datetime.now()
    db.session.commit()

    # Invalidate stats cache
    invalidate_cache('get_stats*')

    return ServiceRequestSchema().dump(request)

@bp.route('/requests/<int:request_id>/rate', methods=['POST'])
@jwt_required()
def rate_request(request_id):
    try:
        # Get current user ID from JWT token
        current_user_email = get_jwt_identity()
        current_app.logger.info(f"Current user email from token: {current_user_email}")
        
        # First get the user, then get the customer
        user = User.query.filter_by(email=current_user_email).first()
        if not user:
            current_app.logger.error(f"User not found for email: {current_user_email}")
            return jsonify({'error': 'User not found'}), 404
            
        customer = Customer.query.get(user.id)
        if not customer:
            current_app.logger.error(f"Customer not found for user ID: {user.id}")
            return jsonify({'error': 'Customer not found'}), 404

        # Get service request
        service_request = ServiceRequest.query.get_or_404(request_id)
        if service_request.customer_id != customer.id:
            return jsonify({'error': 'Unauthorized'}), 403

        if service_request.status != 'completed':
            return jsonify({'error': 'Can only rate completed requests'}), 400

        # Get rating data from request body using Flask request object
        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data in request")
            return jsonify({'error': 'No rating data provided'}), 400

        rating = data.get('rating')
        remarks = data.get('remarks', '')

        if not rating or not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return jsonify({'error': 'Invalid rating. Must be between 1 and 5'}), 400

        # Update service request with rating and change status
        service_request.rating = rating
        service_request.remarks = remarks
        service_request.status = 'closed'
        db.session.commit()

        return jsonify({
            'message': 'Rating submitted successfully',
            'request': {
                'id': service_request.id,
                'status': service_request.status,
                'rating': service_request.rating,
                'remarks': service_request.remarks
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error in rate_request: {str(e)}')
        return jsonify({'error': 'Failed to submit rating'}), 500

@bp.route('/requests/<int:request_id>/close', methods=['POST'])
@jwt_required()
@customer_required()
@error_wrapper
def close_request(request_id):
    """Close a service request after rating"""
    try:
        customer = get_current_customer()
        request = get_or_404(ServiceRequest, request_id)
        
        # Validate that this request belongs to the customer
        if request.customer_id != customer.id:
            raise APIError("Not authorized to close this request", 403)
            
        # Validate request status - must be 'completed' to close
        if request.status != ServiceRequest.STATUS_COMPLETED:
            raise APIError("Request must be completed before closing", 400)
            
        # Get rating data
        data = request.get_json()
        if not data or 'rating' not in data:
            raise APIError("Rating is required", 400)
            
        rating = data.get('rating')
        if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            raise APIError("Rating must be between 1 and 5", 400)
            
        # Update request
        request.status = ServiceRequest.STATUS_CLOSED
        request.rating = rating
        request.closed_at = datetime.now(timezone.utc)
        
        # Update professional's availability and current request if not already updated
        if request.professional_id:
            professional = Professional.query.get(request.professional_id)
            if professional and not professional.available:
                professional.available = True
                professional.current_request = None
        
        db.session.commit()
        
        schema = ServiceRequestSchema()
        return schema.dump(request), 200
        
    except Exception as e:
        db.session.rollback()
        if isinstance(e, APIError):
            raise e
        logger.error(f"Error closing request: {str(e)}")
        raise APIError("Error closing request", 500)

@bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@customer_required()
@error_wrapper
@user_cache(timeout=300)
def get_stats():
    """Get customer dashboard statistics"""
    customer = get_current_customer()
    days = request.args.get('days', 30, type=int)
    stats = Statistics.get_customer_stats(customer.id, days)
    
    # Transform stats to match expected format
    status_counts = stats['status_counts']
    return {
        'total_requests': stats['total_requests'],
        'pending_requests': status_counts.get('requested', 0),
        'completed_requests': status_counts.get('completed', 0),
        'cancelled_requests': status_counts.get('cancelled', 0),
        'total_spending': stats['total_spending'],
        'rating_rate': stats['rating_rate']
    }
