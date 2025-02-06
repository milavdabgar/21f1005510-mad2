from functools import wraps
from flask import request, jsonify, abort
from marshmallow import ValidationError
from ..models import db
from .errors import APIError

def paginate_query(query, schema, **kwargs):
    """Paginate a SQLAlchemy query and return serialized results"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    # Log query before pagination
    print(f"SQL Query before pagination: {query}")
    
    paginated = query.paginate(page=page, per_page=per_page)
    
    # Log pagination results
    print(f"Pagination results - Total: {paginated.total}, Pages: {paginated.pages}, Items: {len(paginated.items)}")
    
    # Serialize and log items
    serialized_items = schema.dump(paginated.items, **kwargs)
    print(f"Serialized {len(serialized_items)} items")
    
    return {
        'items': serialized_items,
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': page,
        'per_page': per_page,
        'has_next': paginated.has_next,
        'has_prev': paginated.has_prev
    }

def validate_schema(schema_cls):
    """Decorator to validate request data against a schema"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                schema = schema_cls()
                json_data = request.get_json() or {}
                print(f"Validating data: {json_data}")  
                try:
                    data = schema.load(json_data)
                    print(f"Validation successful, loaded data: {data}")  
                except ValidationError as err:
                    print(f"Validation error: {err.messages}")  
                    raise APIError(str(err.messages), 400)
                return f(*args, data=data, **kwargs)
            except Exception as e:
                print(f"Unexpected error: {str(e)}")  
                raise APIError(str(e), 400)
        return wrapper
    return decorator

def get_or_404(model_cls, id):
    """Get a model instance by ID or return 404"""
    instance = db.session.get(model_cls, id)
    if instance is None:
        raise APIError(f"{model_cls.__name__} not found", 404)
    return instance

def crud_resource(model_cls, schema_cls, identifier='id'):
    """Create CRUD endpoints for a resource"""
    def get_list():
        query = model_cls.query
        return paginate_query(query, schema_cls(many=True))
    
    def get_one(id):
        item = get_or_404(model_cls, id)
        return schema_cls().dump(item)
    
    def create():
        schema = schema_cls()
        data = schema.load(request.get_json())
        db.session.add(data)
        db.session.commit()
        return schema.dump(data), 201
    
    def update(id):
        item = get_or_404(model_cls, id)
        schema = schema_cls()
        data = schema.load(request.get_json(), instance=item, partial=True)
        db.session.commit()
        return schema.dump(data)
    
    def delete(id):
        item = get_or_404(model_cls, id)
        db.session.delete(item)
        db.session.commit()
        return '', 204
    
    return {
        'get_list': get_list,
        'get_one': get_one,
        'create': create,
        'update': update,
        'delete': delete
    }

def filter_query(query, model, **filters):
    """Apply filters to a SQLAlchemy query"""
    for field, value in filters.items():
        if value is not None and hasattr(model, field):
            if isinstance(value, (list, tuple)):
                query = query.filter(getattr(model, field).in_(value))
            else:
                query = query.filter(getattr(model, field) == value)
    return query

def validate_request_status(request, professional_id, expected_status=None):
    """Validate service request status and ownership
    
    Args:
        request: ServiceRequest instance
        professional_id: ID of the professional
        expected_status: Expected status of the request, if any
        
    Raises:
        APIError: If validation fails
    """
    if not request:
        raise APIError("Service request not found", 404)
    
    if request.professional_id != professional_id:
        raise APIError("Unauthorized access", 403)
        
    if expected_status and request.status != expected_status:
        raise APIError(f"Service request must be in '{expected_status}' status", 400)
