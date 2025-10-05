"""
Rate Limiting Middleware (Redis-enabled)

## Overview

Production-ready rate limiting with multiple strategies and optional Redis for
distributed enforcement. Provides granular controls per endpoint category and
graceful local fallbacks when Redis is unavailable.

## Features

- **Strategies**: Sliding window, fixed window, and token-bucket style behavior
- **Distributed**: Uses Redis when available; falls back to local in-memory
- **Granularity**: Per-endpoint classes (e.g., `health`, `auth`, `api_heavy`)
- **Headers**: Emits `X-RateLimit-*` and `Retry-After` on limit exceedance
- **Resilience**: Continues operating with local limiter if Redis errors occur

## Configuration

Provided via `app.core.config.Settings`:

- `rate_limiting_enabled` (bool): Master toggle
- `rate_limits` (dict): Rule set per classification (requests/window)
- `rate_limiting_skip_health` (bool): Bypass for health checks
- `redis_url` (str|None): Enable Redis-backed distributed limits when set

## Identification

Client identity is derived in priority order: API key, user ID, then client IP
(`X-Forwarded-For` or `X-Real-IP`, or connection address).

## Usage

```python
from app.core.middleware.rate_limiting import RateLimitMiddleware
from app.core.config import settings

app.add_middleware(RateLimitMiddleware, settings=settings)
```
"""

import time
import logging
from typing import Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, status
from fastapi.responses import JSONResponse
import redis.asyncio as redis
from redis.exceptions import RedisError
from app.core.config import Settings
from app.core.exceptions import RateLimitError


class RateLimitExceeded(RateLimitError):
    """
    Deprecated alias. Prefer using RateLimitError from app.core.exceptions.
    """

    def __init__(self, message: str, retry_after: int = 60):
        ...


class RedisRateLimiter:
    """
    Redis-backed distributed rate limiter for multi-instance applications.
    
    Provides distributed rate limiting using Redis as a shared counter store. Supports
    multiple application instances with consistent rate limiting across all nodes.
    Implements sliding window behavior with automatic key expiration and graceful error
    handling for Redis connectivity issues.
    
    Attributes:
        redis_client (redis.Redis): Redis client instance for distributed storage
        requests_per_minute (int): Maximum allowed requests per time window
        window_seconds (int): Time window duration in seconds for rate limiting
    
    State Management:
        - Distributed: All rate limit state stored in Redis for consistency
        - Automatic cleanup: Redis TTL automatically expires old rate limit keys
        - Atomic operations: Uses Redis pipelines for atomic counter increments
        - Connection resilience: Handles Redis errors gracefully with fallback
    
    Usage:
        >>> import redis.asyncio as redis
        >>> from app.core.middleware.rate_limiting import RedisRateLimiter
        >>>
        >>> redis_client = redis.from_url("redis://localhost:6379")
        >>> limiter = RedisRateLimiter(redis_client, requests_per_minute=100, window_seconds=60)
        >>>
        >>> # Check rate limit
        >>> if await limiter.is_allowed("user_123"):
        ...     # Process request
        ... else:
        ...     # Reject with 429 Too Many Requests
        ...     pass
    
    Performance Characteristics:
        - Network latency: One Redis roundtrip per request check
        - Memory usage: Minimal client-side memory, Redis stores counters
        - Scalability: Linear scaling with Redis cluster support
        - Consistency: Strong consistency across all application instances
    """

    def __init__(self, redis_client: redis.Redis, requests_per_minute: int = 60, window_seconds: int = 60):
        """
        Initialize Redis-based distributed rate limiter.
        
        Creates rate limiter instance that uses Redis for distributed counter storage.
        Configures request limits and time windows for rate limiting behavior.
        
        Args:
            redis_client (redis.Redis): Redis client instance with async support
            requests_per_minute (int): Maximum requests allowed per time window (1-10000)
            window_seconds (int): Time window duration in seconds (1-3600)
        
        Returns:
            None: Constructor initializes limiter instance in-place
        
        Raises:
            ConfigurationError: If parameters are outside valid ranges
            RedisError: If Redis client is not properly configured
        
        Behavior:
            - Stores configuration for rate limiting calculations
            - Validates parameter ranges for safety
            - Prepares Redis client for distributed operations
            - Sets up default values for rate limiting behavior
        
        Examples:
            >>> redis_client = redis.from_url("redis://localhost:6379")
            >>> limiter = RedisRateLimiter(redis_client, 100, 60)
            >>> # Allow 100 requests per 60 second window
        """
        ...

    async def is_allowed(self, key: str, weight: int = 1) -> bool:
        """
        Check if request is allowed under rate limit using distributed Redis storage.
        
        Implements distributed rate limiting by incrementing counters in Redis and checking
        against configured limits. Uses atomic operations to ensure consistency across
        multiple application instances. Automatically handles key expiration for sliding
        window behavior.
        
        Args:
            key (str): Unique identifier for rate limiting (e.g., client ID or IP)
            weight (int): Request weight/cost (default: 1). Higher weights consume more limit
        
        Returns:
            bool: True if request is allowed under rate limit, False if limit exceeded
        
        Raises:
            RedisError: If Redis operations fail (triggers fallback to local limiting)
            ValueError: If key is empty or weight is negative
        
        Behavior:
            - Creates Redis key with rate_limit: prefix for the given identifier
            - Uses Redis pipeline for atomic increment and TTL operations
            - Sets TTL on new keys to implement sliding window behavior
            - Returns True if incremented count stays within allowed limit
            - Raises RedisError on connection issues to trigger fallback limiter
            - Logs warnings for Redis operation failures
        
        Sliding Window Implementation:
            - Each request increments counter for client key
            - Keys automatically expire after window_seconds
            - Counter represents requests in current window
            - New window starts when key expires and counter resets
        
        Error Handling:
            - Redis connection errors trigger fallback to local limiter
            - Invalid parameters raise ValueError immediately
            - All Redis operations logged with appropriate error levels
        
        Examples:
            >>> limiter = RedisRateLimiter(redis_client, 10, 60)
            >>> # First request always allowed
            >>> await limiter.is_allowed("user_123")
            True
            >>>
            >>> # Subsequent requests until limit reached
            >>> for i in range(9):
            ...     assert await limiter.is_allowed("user_123") == True
            >>>
            >>> # Request exceeding limit
            >>> await limiter.is_allowed("user_123")
            False
            >>>
            >>> # Different client has separate limit
            >>> await limiter.is_allowed("user_456")
            True
        
        Performance:
            - Single Redis roundtrip for increment and TTL check
            - Automatic key expiration prevents memory buildup
            - Atomic operations prevent race conditions
            - Connection pooling reduces overhead for high traffic
        """
        ...


class LocalRateLimiter:
    """
    Local in-memory rate limiter for single-instance applications or Redis fallback.
    
    Provides in-memory rate limiting for development environments or as a fallback when
    Redis is unavailable. Implements sliding window behavior with automatic cleanup of
    expired client data to prevent memory leaks. Thread-safe for basic usage patterns.
    
    Attributes:
        requests_per_minute (int): Maximum allowed requests per time window
        window_seconds (int): Time window duration in seconds for rate limiting
        clients (dict): In-memory storage for client request timestamps
        cleanup_interval (int): Seconds between automatic cleanup runs
        last_cleanup (float): Timestamp of last cleanup operation
    
    State Management:
        - Local storage: All rate limit state stored in memory
        - Automatic cleanup: Removes expired client entries to prevent memory leaks
        - Thread-safety: Basic safety for concurrent requests within single process
        - Memory efficient: Periodic cleanup prevents unbounded memory growth
    
    Usage:
        >>> from app.core.middleware.rate_limiting import LocalRateLimiter
        >>>
        >>> limiter = LocalRateLimiter(requests_per_minute=10, window_seconds=60)
        >>>
        >>> # Check rate limit for client
        >>> if limiter.is_allowed("client_123"):
        ...     # Process request
        ... else:
        ...     # Reject with 429 Too Many Requests
        ...     pass
    
    Performance Characteristics:
        - Memory usage: O(n) where n is number of active clients in window
        - CPU usage: O(1) per request with periodic O(n) cleanup
        - Latency: Sub-millisecond with no network overhead
        - Scalability: Limited to single process, perfect for development
    
    Limitations:
        - Not distributed: Each instance maintains separate rate limits
        - Memory bounds: Requires periodic cleanup for long-running processes
        - Process restarts: All rate limit data lost on restart
        - Best for: Development, testing, or Redis fallback scenarios
    """

    def __init__(self, requests_per_minute: int = 60, window_seconds: int = 60):
        """
        Initialize local in-memory rate limiter.
        
        Creates rate limiter instance that stores client request data in memory.
        Configures request limits, time windows, and cleanup behavior for memory management.
        
        Args:
            requests_per_minute (int): Maximum requests allowed per time window (1-10000)
            window_seconds (int): Time window duration in seconds (1-3600)
        
        Returns:
            None: Constructor initializes limiter instance in-place
        
        Raises:
            ConfigurationError: If parameters are outside valid ranges
        
        Behavior:
            - Stores configuration for rate limiting calculations
            - Initializes client tracking dictionary
            - Sets up automatic cleanup interval for memory management
            - Records initialization timestamp for cleanup scheduling
        
        Examples:
            >>> limiter = LocalRateLimiter(100, 60)
            >>> # Allow 100 requests per 60 second window per client
        """
        ...

    def is_allowed(self, key: str, weight: int = 1) -> bool:
        """
        Check if request is allowed under rate limit using local in-memory storage.
        
        Implements sliding window rate limiting using in-memory storage of request timestamps.
        Automatically removes expired entries and periodically cleans up inactive clients
        to prevent memory leaks. Handles edge cases like mocked time in test environments.
        
        Args:
            key (str): Unique identifier for rate limiting (e.g., client ID or IP)
            weight (int): Request weight/cost (default: 1). Currently always 1
        
        Returns:
            bool: True if request is allowed under rate limit, False if limit exceeded
        
        Raises:
            ValueError: If key is empty or weight is invalid
        
        Behavior:
            - Performs periodic cleanup of expired client entries
            - Removes old request timestamps outside the sliding window
            - Allows request if current count is below limit
            - Tracks new request timestamp for subsequent checks
            - Handles mocked time gracefully in test environments
            - Prevents memory leaks through automatic cleanup
        
        Sliding Window Implementation:
            - Stores timestamps of recent requests per client
            - Removes timestamps older than window_seconds
            - Counts remaining requests to determine current usage
            - Allows request if count + weight <= requests_per_minute
        
        Memory Management:
            - Automatic cleanup every 5 minutes (cleanup_interval)
            - Removes clients with no recent requests
            - Filters out invalid timestamp data
            - Handles test environment time mocking gracefully
        
        Error Handling:
            - Invalid parameters raise ValueError immediately
            - Time-related errors handled gracefully for test compatibility
            - Corrupted client data cleaned up automatically
        
        Examples:
            >>> limiter = LocalRateLimiter(5, 60)  # 5 requests per minute
            >>> # First 5 requests allowed
            >>> for i in range(5):
            ...     assert limiter.is_allowed("client_123") == True
            >>>
            >>> # 6th request denied
            >>> limiter.is_allowed("client_123")
            False
            >>>
            >>> # Different client has separate limit
            >>> limiter.is_allowed("client_456")
            True
            >>>
            >>> # After window expires, requests allowed again
            >>> # (in real scenario, would wait 60+ seconds)
        
        Performance:
            - O(1) average case for request checking
            - O(n) cleanup cost distributed over time
            - Memory usage proportional to active clients
            - No network latency or external dependencies
        """
        ...


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Production-ready rate limiting middleware with Redis-backed distributed limiting and graceful fallback.
    
    Provides comprehensive rate limiting for FastAPI applications with support for multiple rate
    limiting strategies, per-endpoint configuration, and distributed Redis-based limiting with
    automatic fallback to local in-memory limiting. Designed for high-traffic production
    environments with configurable policies and monitoring capabilities.
    
    Attributes:
        settings (Settings): Application configuration containing rate limit settings
        enabled (bool): Global toggle for rate limiting functionality
        requests_per_minute (int): Default request limit per time window
        burst_size (int): Maximum requests allowed in burst scenarios
        window_seconds (int): Default time window for rate limiting
        rate_limits (dict): Configuration rules per endpoint classification
        redis_client (Optional[redis.Redis]): Redis client for distributed limiting
        redis_rate_limiter (Optional[RedisRateLimiter]): Redis limiter instance
    
    Public Methods:
        dispatch(request, call_next): Processes HTTP requests with rate limiting
        _get_rate_limit_rule(request): Determines applicable rate limit rule for request
        _check_rate_limit(client_id, rule_name): Checks if request exceeds limits
    
    State Management:
        - Distributed: Redis storage for multi-instance consistency when available
        - Fallback: Local in-memory storage when Redis unavailable
        - Automatic cleanup: Prevents memory leaks in local storage
        - Graceful degradation: Continues operating during Redis connectivity issues
        - Thread-safe: Safe for concurrent request processing
    
    Usage:
        # Basic setup with default configuration
        from app.core.middleware.rate_limiting import RateLimitMiddleware
        from app.core.config import create_settings
    
        app = FastAPI()
        settings = create_settings()
        app.add_middleware(RateLimitMiddleware, settings=settings)
    
        # Configuration via settings
        settings.rate_limits = {
            'api_heavy': {'requests': 10, 'window': 60},
            'auth': {'requests': 5, 'window': 300},
            'standard': {'requests': 100, 'window': 60}
        }
    
    Rate Limiting Features:
        - Distributed limiting: Redis-backed for multi-instance consistency
        - Per-endpoint rules: Different limits for different endpoint types
        - Client identification: API key, user ID, or IP-based identification
        - Graceful fallback: Local limiting when Redis unavailable
        - Configurable policies: Custom rules per endpoint classification
        - Monitoring headers: X-RateLimit-* headers for client visibility
        - Health check bypass: Optional skipping for health endpoints
    
    Response Headers:
        - X-RateLimit-Limit: Maximum requests allowed in current window
        - X-RateLimit-Remaining: Requests remaining in current window
        - X-RateLimit-Window: Time window duration in seconds
        - X-RateLimit-Reset: Timestamp when window resets
        - X-RateLimit-Rule: Name of rate limit rule applied
        - Retry-After: Seconds to wait before retry (on 429 responses)
    
    Configuration Options:
        - rate_limiting_enabled: Global enable/disable toggle
        - rate_limits: Dictionary of rules per endpoint classification
        - rate_limiting_skip_health: Skip limiting for health check endpoints
        - redis_url: Redis connection URL for distributed limiting
        - rate_limit_requests_per_minute: Default request limit
        - rate_limit_burst_size: Maximum burst request count
        - rate_limit_window_seconds: Default time window duration
    
    Performance Characteristics:
        - Redis mode: One network roundtrip per request check
        - Local mode: O(1) memory operations with periodic cleanup
        - Memory usage: Proportional to active clients in local mode
        - Scalability: Linear scaling with Redis cluster support
        - Overhead: < 1ms additional latency per request
    
    Examples:
        >>> # Rate limited response headers
        >>> response.headers.get('X-RateLimit-Limit')     # "100"
        >>> response.headers.get('X-RateLimit-Remaining') # "95"
        >>> response.headers.get('X-RateLimit-Window')    # "60"
        >>> response.headers.get('X-RateLimit-Rule')      # "standard"
        >>>
        >>> # Rate exceeded response
        >>> response = client.post('/api/limited')
        >>> response.status_code                           # 429
        >>> response.headers.get('Retry-After')           # "60"
        >>> response.json()['error_code']                  # "RATE_LIMIT_EXCEEDED"
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        """
        ...


class RateLimitSettings:
    """
    Rate limiting configuration settings.
    """

    ...


def get_client_identifier(request: Request) -> str:
    """
    Extract unique client identifier for rate limiting from request headers and metadata.
    
    Determines client identity using a priority hierarchy to enable accurate rate limiting
    across different authentication methods and client types. Supports API key authentication,
    user-based identification, and IP-based fallback identification for anonymous clients.
    
    Args:
        request (Request): The FastAPI request object containing headers and state information
    
    Returns:
        str: Unique client identifier string prefixed by identification method:
             - "api_key: {key}" for API key authenticated requests
             - "user: {user_id}" for authenticated user requests
             - "ip: {ip_address}" for IP-based identification as fallback
    
    Behavior:
        - Priority 1: API key from 'x-api-key' or 'authorization' headers
        - Priority 2: User ID from request.state.user_id (when available and not mocked)
        - Priority 3: IP address from 'x-forwarded-for' header (first IP in chain)
        - Priority 4: IP address from 'x-real-ip' header
        - Priority 5: Connection IP address as final fallback
        - Handles mocked user IDs in test environments gracefully
        - Extracts first IP from comma-separated X-Forwarded-For header values
        - Preserves identification method in returned string for debugging
    
    Examples:
        >>> # API key authenticated request
        >>> request.headers = {'x-api-key': 'sk-1234567890'}
        >>> get_client_identifier(request)
        'api_key: sk-1234567890'
    
        >>> # Authenticated user request
        >>> request.state.user_id = 'user_12345'
        >>> get_client_identifier(request)
        'user: user_12345'
    
        >>> # Request with proxy forwarding
        >>> request.headers = {'x-forwarded-for': '192.168.1.100, 10.0.0.1'}
        >>> get_client_identifier(request)
        'ip: 192.168.1.100'
    
        >>> # Direct IP connection
        >>> request.client.host = '192.168.1.200'
        >>> get_client_identifier(request)
        'ip: 192.168.1.200'
    """
    ...


def get_endpoint_classification(request: Request) -> str:
    """
    Classify endpoint for rate limiting based on request path and business logic.
    
    Maps request paths to rate limiting categories to apply appropriate rate limit rules.
    This function can be extended to implement business-specific rate limiting strategies
    such as tier-based limits, resource-cost-based classification, or user-role-based limits.
    
    Args:
        request (Request): The FastAPI request object containing path information
    
    Returns:
        str: Rate limiting classification string that determines which rule set applies:
             - "health" for health check endpoints
             - "critical" for high-impact processing endpoints
             - "monitoring" for internal monitoring endpoints
             - "auth" for authentication endpoints
             - "standard" for all other endpoints
    
    Behavior:
        - Maps specific endpoints to predefined classifications
        - Uses pattern matching for endpoint categories
        - Provides logical fallback to "standard" classification
        - Enables different rate limits for different endpoint types
        - Supports business-specific customizations through function extension
    
    Endpoint Classifications:
        - Health checks: /health, /healthz, /ping, /status
        - Critical processing: /v1/text_processing/process, /v1/text_processing/batch_process
        - Monitoring: /internal/* endpoints
        - Authentication: /v1/auth/* endpoints
        - Standard: All other endpoints
    
    Extension Examples:
        # Tier-based classification
        if request.state.user_tier == 'premium':
            return 'premium_high'
    
        # Resource-cost-based classification
        if 'file_upload' in request.path:
            return 'resource_heavy'
    
        # User-role-based classification
        if request.state.user_role == 'admin':
            return 'admin_unlimited'
    
    Examples:
        >>> # Health check endpoint
        >>> request.url.path = '/health'
        >>> get_endpoint_classification(request)
        'health'
    
        >>> # Text processing endpoint
        >>> request.url.path = '/v1/text_processing/process'
        >>> get_endpoint_classification(request)
        'critical'
    
        >>> # Authentication endpoint
        >>> request.url.path = '/v1/auth/login'
        >>> get_endpoint_classification(request)
        'auth'
    
        >>> # Standard API endpoint
        >>> request.url.path = '/v1/data/list'
        >>> get_endpoint_classification(request)
        'standard'
    """
    ...
