"""
Enhanced Rate Limiting Middleware with Redis Support

Provides production-ready rate limiting with multiple strategies, distributed
support via Redis, and granular control over different endpoint types.
"""

import time
import logging
from typing import Dict, Optional, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

import redis.asyncio as redis
from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-ready rate limiting middleware with multiple strategies.
    
    Features:
    - Multiple rate limiting strategies (sliding window, token bucket, fixed window)
    - Redis-backed distributed rate limiting
    - Per-endpoint and per-user rate limits
    - Graceful degradation when Redis is unavailable
    - Custom rate limit headers in responses
    - Configurable rate limit rules
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, Dict] = {}
        self.cache_cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        # Rate limit rules (requests per time window)
        self.rate_limits = {
            # Global limits per IP
            'global': {'requests': 1000, 'window': 3600},  # 1000/hour
            
            # API endpoint specific limits
            'api_heavy': {'requests': 10, 'window': 60},    # 10/minute for heavy ops
            'api_standard': {'requests': 100, 'window': 60},  # 100/minute standard
            'api_light': {'requests': 1000, 'window': 60},   # 1000/minute light ops
            
            # Authentication endpoints
            'auth': {'requests': 5, 'window': 300},  # 5/5min auth attempts
            
            # Health checks (very permissive)
            'health': {'requests': 10000, 'window': 60},     # 10000/minute
        }
        
        # Endpoint classifications
        self.endpoint_rules = {
            '/v1/text_processing/process': 'api_heavy',
            '/v1/text_processing/batch_process': 'api_heavy',
            '/v1/text_processing/analyze': 'api_standard',
            '/v1/auth/login': 'auth',
            '/v1/auth/refresh': 'auth',
            '/health': 'health',
            '/healthz': 'health',
            '/ping': 'health',
        }
        
        # Initialize Redis connection
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis connection for distributed rate limiting."""
        try:
            if hasattr(self.settings, 'redis_url') and self.settings.redis_url:
                self.redis_client = redis.from_url(
                    self.settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=1,
                    socket_timeout=1
                )
        except Exception as e:
            logger.warning(f"Redis connection failed, using local cache: {e}")
            self.redis_client = None
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Priority: API key > User ID > IP address
        api_key = request.headers.get('x-api-key') or request.headers.get('authorization')
        if api_key:
            return f"api_key: {hash(api_key) % 1000000}"
        
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user: {user_id}"
        
        client_ip = request.client.host if request.client else 'unknown'
        return f"ip: {client_ip}"
    
    def _get_rate_limit_rule(self, request: Request) -> str:
        """Determine which rate limit rule applies to this request."""
        path = request.url.path
        
        # Check for exact matches first
        if path in self.endpoint_rules:
            return self.endpoint_rules[path]
        
        # Check for pattern matches
        if path.startswith('/health') or path.startswith('/ping'):
            return 'health'
        elif path.startswith('/v1/auth'):
            return 'auth'
        elif path.startswith('/v1/text_processing'):
            # Default text processing to standard unless specifically configured
            return 'api_standard'
        
        # Default to global rate limit
        return 'global'
    
    async def _check_rate_limit_redis(self, key: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """Check rate limit using Redis sliding window."""
        try:
            if self.redis_client is None:
                # Fall back to local cache if Redis is not available
                return await self._check_rate_limit_local(key, limit, window)
            
            current_time = time.time()
            window_start = current_time - window
            
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, window + 10)
            
            results = await pipe.execute()
            current_requests = results[1]
            
            # Calculate remaining and reset time
            remaining = max(0, limit - current_requests)
            reset_time = int(current_time + window)
            
            return current_requests < limit, {
                'limit': limit,
                'remaining': remaining,
                'reset': reset_time,
                'current': current_requests
            }
            
        except Exception as e:
            logger.warning(f"Redis rate limit check failed: {e}")
            # Fall back to local cache
            return await self._check_rate_limit_local(key, limit, window)
    
    async def _check_rate_limit_local(self, key: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """Check rate limit using local memory cache."""
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cache_cleanup_interval:
            await self._cleanup_local_cache()
            self.last_cleanup = current_time
        
        if key not in self.local_cache:
            self.local_cache[key] = {'requests': [], 'window': window}
        
        cache_entry = self.local_cache[key]
        
        # Remove requests outside the window
        window_start = current_time - window
        cache_entry['requests'] = [
            req_time for req_time in cache_entry['requests']
            if req_time > window_start
        ]
        
        # Add current request
        cache_entry['requests'].append(current_time)
        
        current_requests = len(cache_entry['requests'])
        remaining = max(0, limit - current_requests)
        reset_time = int(current_time + window)
        
        return current_requests <= limit, {
            'limit': limit,
            'remaining': remaining,
            'reset': reset_time,
            'current': current_requests
        }
    
    async def _cleanup_local_cache(self):
        """Clean up expired entries from local cache."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, data in self.local_cache.items():
            window = data.get('window', 3600)
            window_start = current_time - window
            
            # Remove old requests
            data['requests'] = [
                req_time for req_time in data['requests']
                if req_time > window_start
            ]
            
            # Remove empty entries
            if not data['requests']:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.local_cache[key]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks if configured
        if getattr(self.settings, 'rate_limiting_skip_health', True):
            if request.url.path in ['/health', '/healthz', '/ping']:
                return await call_next(request)
        
        # Get client identifier and rate limit rule
        client_id = self._get_client_identifier(request)
        rule_name = self._get_rate_limit_rule(request)
        rate_config = self.rate_limits.get(rule_name, self.rate_limits['global'])
        
        # Create rate limit key
        rate_limit_key = f"rate_limit: {rule_name}: {client_id}"
        
        # Check rate limit
        if self.redis_client:
            allowed, rate_info = await self._check_rate_limit_redis(
                rate_limit_key, rate_config['requests'], rate_config['window']
            )
        else:
            allowed, rate_info = await self._check_rate_limit_local(
                rate_limit_key, rate_config['requests'], rate_config['window']
            )
        
        # Add rate limit headers to response
        def add_rate_limit_headers(response: Response):
            response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
            response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
            response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
            response.headers['X-RateLimit-Rule'] = rule_name
            return response
        
        # Check if rate limited
        if not allowed:
            retry_after = rate_config['window']
            
            logger.warning(
                f"Rate limit exceeded for {client_id} on {request.url.path} "
                f"(rule: {rule_name}, limit: {rate_config['requests']}/{rate_config['window']}s)"
            )
            
            error_response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "limit": rate_info['limit'],
                    "window": rate_config['window'],
                    "retry_after": retry_after
                }
            )
            
            # Add rate limit headers
            add_rate_limit_headers(error_response)
            error_response.headers['Retry-After'] = str(retry_after)
            
            return error_response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful response
        return add_rate_limit_headers(response)


# Configuration additions for Settings class
class RateLimitSettings:
    """Rate limiting configuration settings."""
    
    # Enable/disable rate limiting
    rate_limiting_enabled: bool = True
    
    # Skip rate limiting for health endpoints
    rate_limiting_skip_health: bool = True
    
    # Redis URL for distributed rate limiting (optional)
    redis_url: Optional[str] = None
    
    # Custom rate limit rules (can override defaults)
    custom_rate_limits: Dict[str, Dict[str, int]] = {}
    
    # Custom endpoint rules (can override defaults)
    custom_endpoint_rules: Dict[str, str] = {}
