from sqlalchemy import or_, and_, func
from sqlalchemy.orm import aliased
from ..models import User, Professional, Service, ServiceRequest, Customer
from ..extensions import redis_client, db
from functools import wraps
import json

def memoize(timeout=300):
    """Memoization decorator using Redis cache"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create a unique cache key based on function name and arguments
            key = f"memoize:{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get cached result
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Get fresh result
            result = f(*args, **kwargs)
            
            # Cache the result
            redis_client.setex(key, timeout, json.dumps(result))
            
            return result
        return decorated_function
    return decorator

class Search:
    @staticmethod
    def _apply_location_filter(query, model, location):
        """Apply location-based filtering"""
        if not location:
            return query
        
        return query.filter(
            or_(
                model.city.ilike(f'%{location}%'),
                model.state.ilike(f'%{location}%'),
                model.pin_code == location
            )
        )
    
    @staticmethod
    def _apply_service_filter(query, service_type):
        """Apply service type filtering"""
        if not service_type:
            return query
        
        return query.filter(Professional.service_type == service_type)
    
    @staticmethod
    def _apply_availability_filter(query):
        """Apply availability filtering"""
        return query.filter(Professional.available.is_(True))
    
    @staticmethod
    def _apply_verification_filter(query):
        """Apply verification filtering"""
        return query.filter(Professional.verified.is_(True))
    
    @staticmethod
    def _extract_years(experience):
        """Extract the number of years from experience string"""
        if not experience:
            return 0
        try:
            # Extract first number from string, handling "X+" format
            years = experience.split()[0].rstrip('+')
            return int(years)
        except (ValueError, IndexError):
            return 0

    @staticmethod
    def _safe_cast(value, type_, default=None):
        """Safely cast a value to a type"""
        try:
            return type_(value)
        except (ValueError, TypeError):
            return default

    @staticmethod
    @memoize(timeout=300)
    def search_services(query=None, **filters):
        """Search services with caching"""
        base_query = Service.query
        
        if query:
            search_term = f'%{query}%'
            base_query = base_query.filter(
                Service.name.ilike(search_term)
            )
        
        if type_ := filters.get('type'):
            base_query = base_query.filter(Service.type == type_)
        
        if min_price := Search._safe_cast(filters.get('min_price'), float):
            base_query = base_query.filter(Service.price >= min_price)
        
        # Execute query and return results as list of dicts
        results = base_query.all()
        return [{
            'id': s.id,
            'name': s.name,
            'type': s.type,
            'price': s.price
        } for s in results]
    
    @staticmethod
    @memoize(timeout=300)
    def search_professionals(query=None, **filters):
        """Search professionals with caching"""
        # Use aliased to prevent ambiguous column names
        user_alias = aliased(User)
        
        # Start with Professional query and select specific columns
        base_query = db.session.query(
            Professional.id,
            Professional.experience,
            Professional.service_type,
            Professional.verified,
            Professional.available,
            user_alias.name,
            user_alias.email
        ).join(
            user_alias, Professional.id == user_alias.id
        )
        
        if query:
            search_term = f'%{query}%'
            base_query = base_query.filter(
                or_(
                    user_alias.name.ilike(search_term),
                    user_alias.email.ilike(search_term)
                )
            )
        
        if service_type := filters.get('service_type'):
            base_query = base_query.filter(Professional.service_type == service_type)
        
        if filters.get('available_only'):
            base_query = base_query.filter(Professional.available.is_(True))
        
        if filters.get('verified_only'):
            base_query = base_query.filter(Professional.verified.is_(True))
        
        # Execute query and return results as list of dicts
        results = base_query.all()
        
        # Filter by experience in Python since SQLite doesn't support regexp_replace
        if min_experience := Search._safe_cast(filters.get('min_experience'), int):
            results = [r for r in results if Search._extract_years(r[1]) >= min_experience]
        
        return [{
            'id': r[0],
            'name': r[5],
            'email': r[6],
            'experience': r[1],
            'service_type': r[2],
            'verified': r[3],
            'available': r[4]
        } for r in results]
    
    @staticmethod
    def get_recommended_professionals(service_id, location=None, limit=5):
        """Get recommended professionals based on ratings and availability"""
        base_query = Professional.query.filter(
            and_(
                Professional.service_id == service_id,
                Professional.is_verified.is_(True),
                Professional.is_available.is_(True)
            )
        )
        
        if location:
            base_query = Search._apply_location_filter(base_query, Professional, location)
        
        return base_query.join(ServiceRequest).group_by(Professional.id).order_by(
            func.avg(ServiceRequest.rating).desc()
        ).limit(limit).all()
    
    @staticmethod
    @memoize(timeout=300)
    def search_service_requests(**filters):
        """Search service requests with filters"""
        query = ServiceRequest.query
        
        # Apply customer_id filter
        if customer_id := filters.get('customer_id'):
            query = query.filter(ServiceRequest.customer_id == customer_id)
            
        # Apply status filter
        if status := filters.get('status'):
            query = query.filter(ServiceRequest.status == status)
            
        # Apply date filters
        if start_date := filters.get('start_date'):
            query = query.filter(ServiceRequest.request_date >= start_date)
            
        if end_date := filters.get('end_date'):
            query = query.filter(ServiceRequest.request_date <= end_date)
        
        return query
