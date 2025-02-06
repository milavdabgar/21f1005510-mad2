import redis
from flask import current_app
import json
from functools import wraps

redis_client = redis.Redis.from_url('redis://localhost:6379/0')

def cache_key(*args, **kwargs):
    """Generate a cache key from arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)

def cache(timeout=300):
    """Cache decorator for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f"{f.__name__}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Get fresh data
            data = f(*args, **kwargs)
            
            # Cache the data
            redis_client.setex(key, timeout, json.dumps(data))
            
            return data
        return decorated_function
    return decorator

def user_cache(timeout=300):
    """Cache decorator for user-specific routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_jwt_extended import get_jwt_identity
            
            # Include user identity in cache key
            user_id = get_jwt_identity()
            key = f"{f.__name__}:{user_id}:{cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            
            # Get fresh data
            data = f(*args, **kwargs)
            
            # Cache the data
            redis_client.setex(key, timeout, json.dumps(data))
            
            return data
        return decorated_function
    return decorator

def invalidate_cache(pattern):
    """Invalidate cache keys matching pattern"""
    for key in redis_client.scan_iter(pattern):
        redis_client.delete(key)
