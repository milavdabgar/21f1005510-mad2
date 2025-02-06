from functools import wraps
from flask import request
from app.extensions import redis_client
import json

def cache(timeout=300):
    """Simple cache decorator for GET requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            # Use request path and query parameters as cache key
            key = request.path
            if request.query_string:
                key = f"{key}?{request.query_string.decode('utf-8')}"
            
            # Try to get cached response
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Get fresh response
            response = f(*args, **kwargs)
            
            # Cache the response
            redis_client.setex(key, timeout, json.dumps(response))
            
            return response
        return decorated_function
    return decorator

def invalidate_cache(key):
    """Invalidate a specific cache key and all its query parameter variants"""
    # Delete the base key
    redis_client.delete(key)
    
    # Delete all keys that start with this path
    pattern = f"{key}?*"
    for k in redis_client.scan_iter(pattern):
        redis_client.delete(k)
