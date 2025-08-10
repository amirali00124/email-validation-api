from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
import redis
import os
import logging

class RateLimiter:
    def __init__(self):
        # Try to connect to Redis, fallback to in-memory storage
        try:
            redis_url = os.environ.get('REDIS_URL')
            if redis_url:
                self.redis_client = redis.from_url(redis_url)
                self.use_redis = True
            else:
                self.use_redis = False
                self.memory_storage = {}
        except Exception as e:
            logging.warning(f"Redis not available, using memory storage: {e}")
            self.use_redis = False
            self.memory_storage = {}
    
    def limit(self, key, limit, window=3600):
        """
        Rate limiting function
        key: unique identifier (e.g., API key or IP)
        limit: number of requests allowed
        window: time window in seconds (default 1 hour)
        """
        now = datetime.utcnow()
        
        if self.use_redis:
            return self._redis_limit(key, limit, window, now)
        else:
            return self._memory_limit(key, limit, window, now)
    
    def _redis_limit(self, key, limit, window, now):
        """Redis-based rate limiting"""
        try:
            pipe = self.redis_client.pipeline()
            window_start = now - timedelta(seconds=window)
            
            # Remove old entries
            pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start.timestamp())
            
            # Count current requests
            pipe.zcard(f"rate_limit:{key}")
            
            # Add current request
            pipe.zadd(f"rate_limit:{key}", {str(now.timestamp()): now.timestamp()})
            
            # Set expiry
            pipe.expire(f"rate_limit:{key}", window)
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            return current_count <= limit, current_count, limit
            
        except Exception as e:
            logging.error(f"Redis rate limiting error: {e}")
            return True, 0, limit  # Allow on error
    
    def _memory_limit(self, key, limit, window, now):
        """Memory-based rate limiting"""
        if key not in self.memory_storage:
            self.memory_storage[key] = []
        
        # Remove old entries
        window_start = now - timedelta(seconds=window)
        self.memory_storage[key] = [
            timestamp for timestamp in self.memory_storage[key]
            if timestamp > window_start
        ]
        
        # Add current request
        self.memory_storage[key].append(now)
        
        current_count = len(self.memory_storage[key])
        return current_count <= limit, current_count, limit

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit_per_hour=100):
    """Decorator for rate limiting endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get identifier (API key or IP)
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            identifier = api_key or request.remote_addr
            
            allowed, current, limit = rate_limiter.limit(
                f"rate_limit:{identifier}", 
                limit_per_hour, 
                3600  # 1 hour window
            )
            
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'current_requests': current,
                    'limit': limit,
                    'reset_time': 3600
                }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
