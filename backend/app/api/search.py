from flask import Blueprint, request
from sqlalchemy import or_
from flask_jwt_extended import jwt_required, get_jwt
from app.models import Service, Professional, User
from app.schemas import ServiceSchema, ProfessionalSchema
from app.cache import cache
from app.utils.errors import APIError

bp = Blueprint('search', __name__)

@bp.route('/search/services', methods=['GET'])
@cache(timeout=300)  # Cache for 5 minutes
def search_services():
    """Search services with filtering based on name and type"""
    # Get search parameters
    search_query = request.args.get('q', '')
    service_type = request.args.get('type')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    # Start with base query
    query = Service.query

    # Apply text search if provided
    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(or_(
            Service.name.ilike(pattern),
            Service.description.ilike(pattern)
        ))

    # Filter by service type
    if service_type:
        query = query.filter(Service.type == service_type.lower())

    # Apply price filters
    if min_price is not None:
        query = query.filter(Service.price >= min_price)
    if max_price is not None:
        query = query.filter(Service.price <= max_price)

    # Order by name
    query = query.order_by(Service.name)

    # Paginate results
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    pagination = query.paginate(page=page, per_page=per_page)

    # Serialize results
    schema = ServiceSchema(many=True)
    return {
        'items': schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    }

@bp.route('/search/professionals', methods=['GET'])
@jwt_required()  # Only admin can search professionals
def search_professionals():
    """Search professionals for admin to block/unblock/review"""
    # Verify admin access
    claims = get_jwt()
    if not claims.get('is_admin'):
        return {'error': 'Unauthorized access'}, 401

    # Get search parameters
    search_query = request.args.get('q', '')
    service_type = request.args.get('service_type')
    status = request.args.get('status')  # For filtering by verification/approval status
    blocked_str = request.args.get('blocked', None)  # Get as string first
    blocked = None if blocked_str is None else blocked_str.lower() == 'true'  # Convert to boolean

    # Start with base query
    query = Professional.query

    # Apply text search if provided
    if search_query:
        pattern = f"%{search_query}%"
        query = query.filter(or_(
            Professional.name.ilike(pattern),
            Professional.email.ilike(pattern),
            Professional.phone.ilike(pattern)
        ))

    # Filter by service type
    if service_type:
        query = query.filter(Professional.service_type == service_type.lower())

    # Filter by professional status
    if status:
        query = query.filter(Professional.status == status)

    # Filter by blocked status
    if blocked is not None:
        query = query.filter(Professional.blocked == blocked)  # Ensure proper boolean conversion

    # Order by name
    query = query.order_by(Professional.name)

    # Paginate results
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    pagination = query.paginate(page=page, per_page=per_page)

    # Serialize results
    schema = ProfessionalSchema(many=True)
    return {
        'items': schema.dump(pagination.items),
        'total': pagination.total,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    }
