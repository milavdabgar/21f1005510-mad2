from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..models import Service, Professional, ServiceRequest, db
from ..schemas import ServiceSchema, ProfessionalSchema, ServiceRequestSchema
from ..utils.errors import error_wrapper, APIError, ValidationError
from ..utils.auth import admin_required, RoleBasedAccess
from ..utils.api import paginate_query
from ..utils.cache import cache, invalidate_cache
import logging
from functools import wraps
from sqlalchemy import func

logger = logging.getLogger(__name__)
bp = Blueprint('services', __name__)

# Constants
CACHE_TIMEOUT = 300  # 5 minutes
SERVICE_ENDPOINTS = ['/services', '/services/']

def validate_service_data(data, partial=False):
    """Validate service data with schema"""
    if not data:
        raise APIError("No input data provided", 400)
    
    # Convert type to lowercase if present
    if 'type' in data:
        data['type'] = data['type'].lower()
    
    schema = ServiceSchema(partial=partial)
    errors = schema.validate(data)
    if errors:
        raise ValidationError(errors)
    return schema

def invalidate_service_cache():
    """Invalidate all service-related cache"""
    for endpoint in SERVICE_ENDPOINTS:
        invalidate_cache(endpoint)
        invalidate_cache(f"{endpoint}/")
        invalidate_cache(f"{endpoint}?*")

def get_or_404(model_cls, id):
    """Get model instance by id or return 404"""
    instance = db.session.get(model_cls, id)
    if not instance:
        raise APIError(f"{model_cls.__name__} not found", 404)
    return instance

@bp.route('/', methods=['GET'])
@error_wrapper
def get_services():
    """Get all services with optional filtering"""
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
        return jsonify(schema.dump(services))
    except Exception as e:
        logger.error(f"Error fetching services: {str(e)}")
        return jsonify({"error": "Error fetching services"}), 500

@bp.route('/<int:service_id>/', methods=['GET'])
@error_wrapper
@cache(timeout=CACHE_TIMEOUT)
def get_service(service_id):
    """Get service details"""
    service = get_or_404(Service, service_id)
    return ServiceSchema().dump(service)

@bp.route('/<int:service_id>/professionals/', methods=['GET'])
@error_wrapper
def get_service_professionals(service_id):
    """Get professionals offering a service"""
    service = get_or_404(Service, service_id)
    verified_only = request.args.get('verified_only', type=bool, default=True)
    location = request.args.get('location')
    
    query = Professional.query.filter_by(service_type=service.type)
    if verified_only:
        query = query.filter_by(verified=True)
    if location:
        query = query.filter_by(location=location)
    
    return paginate_query(query, ProfessionalSchema(many=True))

@bp.route('/<int:service_id>/requests/', methods=['GET'])
@jwt_required()
@error_wrapper
def get_service_requests(service_id):
    """Get service requests for a service"""
    service = get_or_404(Service, service_id)
    if not RoleBasedAccess.can_view_service_requests(service_id):
        raise APIError('Unauthorized access', 403)
    
    query = ServiceRequest.query.filter_by(service_id=service_id)
    if status := request.args.get('status'):
        query = query.filter_by(status=status)
    
    return paginate_query(query, ServiceRequestSchema(many=True))

@bp.route('/categories/', methods=['GET'])
@error_wrapper
@jwt_required()
def list_service_categories():
    """Get all available service categories"""
    try:
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
    except Exception as e:
        logger.error(f"Error fetching service categories: {str(e)}")
        raise APIError("Error fetching service categories", 500)

@bp.route('/', methods=['POST'])
@jwt_required()
@admin_required()
@error_wrapper
def create_service():
    """Create a new service"""
    try:
        data = request.get_json()
        schema = validate_service_data(data)
        
        service = Service(**data)
        db.session.add(service)
        db.session.commit()
        
        invalidate_service_cache()
        return schema.dump(service), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating service: {str(e)}")
        raise APIError(str(e), 400)

@bp.route('/<int:service_id>/', methods=['PUT'])
@error_wrapper
@jwt_required()
@admin_required()
def update_service(service_id):
    """Update service details"""
    service = get_or_404(Service, service_id)
    data = request.get_json()

    # Only allow updating specific fields
    allowed_fields = ['name', 'type', 'price', 'time_required', 'description']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    # Validate data
    schema = validate_service_data(update_data, partial=True)
    
    try:
        # Update service
        for key, value in update_data.items():
            setattr(service, key, value)
        db.session.commit()
        invalidate_service_cache()
        
        return ServiceSchema().dump(service)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating service {service_id}: {str(e)}")
        raise APIError(str(e), 500)

@bp.route('/<int:service_id>/', methods=['DELETE'])
@jwt_required()
@admin_required()
@error_wrapper
def delete_service(service_id):
    """Delete a service"""
    service = get_or_404(Service, service_id)
    
    # Check if service has any requests
    service_requests = ServiceRequest.query.filter_by(service_id=service_id).first()
    if service_requests:
        raise APIError("Cannot delete service as it has existing service requests. Archive the service instead.", 400)
    
    try:
        service.delete()
        invalidate_service_cache()
        return '', 204
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting service {service_id}: {str(e)}")
        raise APIError(str(e), 500)
