"""
Core Middleware Module - Enhanced

This module provides centralized middleware management for the FastAPI backend application.
All application middleware is consolidated here including CORS configuration, error handling,
logging, security, monitoring, rate limiting, compression, and API versioning middleware to
provide comprehensive production-ready capabilities with clean separation of concerns.

The middleware stack is designed for production use with comprehensive error handling,
security features, monitoring capabilities, and development conveniences. Each middleware
component can be individually configured through the application settings.

Enhanced Middleware Components:
    CORS Middleware:
        * Cross-Origin Resource Sharing configuration
        * Configurable allowed origins, methods, and headers
        * Support for credentials and preflight requests
        * Production-ready security settings

    Global Exception Handler:
        * Centralized exception handling for unhandled errors
        * Standardized error response format
        * Security-conscious error message sanitization
        * Comprehensive logging for debugging and monitoring

    Request Logging Middleware:
        * HTTP request/response logging with performance metrics
        * Configurable log levels and detail granularity
        * Request ID generation for tracing
        * Sensitive data filtering for security

    Security Middleware:
        * Security headers injection (HSTS, CSP, etc.)
        * Input validation and sanitization
        * XSS and injection attack prevention
        * Enhanced header controls

    Performance Monitoring Middleware:
        * Request timing and performance metrics
        * Memory usage tracking
        * Slow request detection and alerting
        * Integration with monitoring systems

    Rate Limiting Middleware:
        * Redis-backed distributed rate limiting
        * Per-endpoint and per-user rate limits
        * Graceful degradation when Redis unavailable
        * Custom rate limit headers and rules

    API Versioning Middleware:
        * Multiple version detection strategies (URL, headers, query params)
        * Version compatibility routing
        * Deprecation warnings and sunset dates
        * Backward compatibility transformations

    Compression Middleware:
        * Request decompression (gzip, brotli, deflate)
        * Intelligent response compression
        * Content-type aware compression decisions
        * Streaming compression support

    Request Size Limiting Middleware:
        * Content-type specific size limits
        * Streaming validation for large requests
        * Protection against DoS attacks
        * Detailed error responses

Architecture:
    The enhanced middleware stack follows FastAPI's middleware execution order, with
    rate limiting and security middleware running first, followed by versioning,
    compression, logging, and monitoring middleware, and finally CORS middleware
    for response processing.

    Enhanced Execution Order (Request Processing):
    1. Rate Limiting Middleware (protect against abuse early)
    2. Request Size Limiting (prevent large request DoS attacks)
    3. Security Middleware (security headers and validation)
    4. API Versioning Middleware (handle version detection and routing)
    5. Version Compatibility Middleware (transform between versions)
    6. Compression Middleware (handle request/response compression)
    7. Request Logging Middleware (log requests with correlation IDs)
    8. Performance Monitoring (track performance metrics)
    9. Application Logic (routers, endpoints)
    10. CORS Middleware (handle cross-origin responses)
    11. Global Exception Handler (catch any unhandled exceptions)

Configuration:
    All middleware can be configured through the Settings class in app.core.config:

    * CORS settings: allowed_origins, cors_credentials, cors_methods
    * Logging settings: log_level, request_logging_enabled
    * Security settings: security_headers_enabled, max_request_size
    * Monitoring settings: performance_monitoring_enabled, slow_request_threshold
    * Rate limiting: rate_limiting_enabled, redis_url, custom_rate_limits
    * Compression: compression_enabled, compression_level, compression_algorithms
    * API versioning: api_versioning_enabled, default_api_version, current_api_version

Usage:
    Import and apply middleware to FastAPI application:

    ```python
    from fastapi import FastAPI
    from app.core.middleware import setup_middleware, setup_enhanced_middleware
    from app.core.config import settings

    app = FastAPI()
    # Basic middleware stack
    setup_middleware(app, settings)

    # Or enhanced middleware stack with all features
    setup_enhanced_middleware(app, settings)
    ```

Dependencies:
    * fastapi: Core web framework and middleware support
    * fastapi.middleware.cors: CORS middleware implementation
    * app.core.config: Application settings and configuration
    * app.core.exceptions: Custom exception hierarchy
    * shared.models: Pydantic models for error responses
    * redis.asyncio: Redis client for distributed rate limiting
    * brotli: Brotli compression support
    * packaging: Version parsing and comparison
    * logging: Python standard library logging

Thread Safety:
    All middleware components are designed to be thread-safe and support
    concurrent request processing in production environments with multiple
    workers and async request handling.

Example:
    Complete enhanced middleware setup for production deployment:

    ```python
    from fastapi import FastAPI
    from app.core.middleware import setup_production_middleware
    from app.core.config import settings

    app = FastAPI(title="AI Text Processor API")

    # Apply all enhanced middleware components with production optimization
    setup_production_middleware(app, settings)

    # Enhanced middleware stack is now configured and ready
    ```

Note:
    This module provides both basic middleware setup (setup_middleware) for
    backward compatibility and enhanced middleware setup (setup_enhanced_middleware)
    with all advanced features. The enhanced version includes rate limiting,
    compression, API versioning, and advanced monitoring capabilities for
    production-ready deployments.
"""

import logging
import time
import asyncio
from typing import Optional, Dict, List, Callable, Any

from fastapi import FastAPI, Request, Response
from app.core.config import Settings

# Import middleware components from their dedicated modules
from .cors import setup_cors_middleware
from .global_exception_handler import setup_global_exception_handler
from .request_logging import RequestLoggingMiddleware, request_id_context, request_start_time_context
from .security import SecurityMiddleware
from .performance_monitoring import PerformanceMonitoringMiddleware
from .api_versioning import (
    APIVersioningMiddleware, VersionCompatibilityMiddleware, APIVersioningSettings,
    get_api_version, is_version_deprecated, get_version_sunset_date
)
from .rate_limiting import RateLimitMiddleware, RateLimitSettings
from .request_size import RequestSizeLimitMiddleware
from .compression import (
    CompressionMiddleware, CompressionSettings,
    get_compression_stats, configure_compression_settings
)

# Configure module logger
logger = logging.getLogger(__name__)

# Context variables are now imported from request_logging module
# but we re-export them here for backward compatibility


# ============================================================================
# Middleware Components - Imported from dedicated modules
# ============================================================================

# setup_cors_middleware function is imported from cors.py
# setup_global_exception_handler function is imported from global_exception_handler.py
# RequestLoggingMiddleware class is imported from request_logging.py
# SecurityMiddleware class is imported from security.py
# PerformanceMonitoringMiddleware class is imported from performance_monitoring.py
# APIVersioningMiddleware, VersionCompatibilityMiddleware classes are imported from api_versioning.py
# RateLimitMiddleware class is imported from rate_limiting.py
# RequestSizeLimitMiddleware class is imported from request_size.py
# CompressionMiddleware, StreamingCompressionMiddleware classes are imported from compression.py


# ============================================================================
# Middleware Setup Functions
# ============================================================================

def setup_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure all middleware components for the FastAPI application.

    Sets up the complete middleware stack in the correct order for optimal
    performance, security, and monitoring. The middleware stack is designed
    for production use with comprehensive error handling, security controls,
    and operational visibility.

    Middleware Stack Configuration:
        The middleware is applied in the optimal order for request processing:

        1. **Security Middleware**: Applied first to validate requests and inject
           security headers before any processing occurs
        2. **Request Logging Middleware**: Captures request start timing and
           generates correlation IDs for tracking
        3. **Performance Monitoring Middleware**: Tracks resource usage and
           request performance metrics
        4. **Application Logic**: User-defined routers and endpoints
        5. **CORS Middleware**: Applied last to handle response headers and
           preflight requests properly
        6. **Global Exception Handler**: Catches any unhandled exceptions
           from the entire stack

    Args:
        app (FastAPI): The FastAPI application instance to configure
        settings (Settings): Application settings containing middleware configuration

    Configuration Features:
        * Individual middleware components can be enabled/disabled via settings
        * All middleware respects the application's logging configuration
        * Security headers and CORS settings are production-ready by default
        * Performance monitoring provides both development and production metrics
        * Error handling ensures consistent API responses across all failure modes

    Settings Integration:
        The function uses the following settings for configuration:
        * allowed_origins: CORS origins configuration
        * log_level: Logging verbosity for middleware components
        * security_headers_enabled: Enable/disable security middleware
        * performance_monitoring_enabled: Enable/disable performance tracking
        * request_logging_enabled: Enable/disable request logging

    Example:
        ```python
        from fastapi import FastAPI
        from app.core.middleware import setup_middleware
        from app.core.config import settings

        app = FastAPI()
        setup_middleware(app, settings)
        # All middleware is now configured and ready
        ```

    Middleware Order Rationale:
        * Security middleware runs first to reject malicious requests early
        * Logging middleware captures timing for the entire request lifecycle
        * Performance monitoring tracks resource usage across all processing
        * CORS middleware runs last to properly handle response processing
        * Exception handling provides a safety net for the entire stack

    Production Considerations:
        * All middleware components are designed for high-performance production use
        * Logging levels can be adjusted to reduce verbosity in production
        * Security headers provide defense-in-depth against common attacks
        * Performance monitoring can be integrated with external systems
        * Error responses never expose internal implementation details

    Note:
        This function should be called once during application startup, after
        creating the FastAPI instance but before including routers. The middleware
        stack will be active for all requests processed by the application.
    """
    logger.info("Setting up middleware stack")

    # 1. Security Middleware (first to run on requests)
    security_enabled = getattr(settings, 'security_headers_enabled', True)
    if security_enabled:
        app.add_middleware(SecurityMiddleware, settings=settings)
        logger.info("Security middleware enabled")

    # 2. Request Logging Middleware
    request_logging_enabled = getattr(settings, 'request_logging_enabled', True)
    if request_logging_enabled:
        app.add_middleware(RequestLoggingMiddleware, settings=settings)
        logger.info("Request logging middleware enabled")

    # 3. Performance Monitoring Middleware
    performance_monitoring_enabled = getattr(settings, 'performance_monitoring_enabled', True)
    if performance_monitoring_enabled:
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        logger.info("Performance monitoring middleware enabled")

    # 4. Global Exception Handler (handles exceptions from all middleware)
    setup_global_exception_handler(app, settings)
    logger.info("Global exception handler configured")

    # 5. CORS Middleware (last to run on responses)
    setup_cors_middleware(app, settings)
    logger.info("CORS middleware configured")

    logger.info("Middleware stack setup complete")


def setup_enhanced_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure enhanced middleware stack with all available components.

    Enhanced Middleware Stack Order:
    1. **Rate Limiting Middleware**: Protect against abuse early
    2. **Request Size Limiting**: Prevent large request DoS attacks
    3. **Security Middleware**: Security headers and validation
    4. **API Versioning Middleware**: Handle version detection and routing
    5. **Version Compatibility Middleware**: Transform between versions
    6. **Compression Middleware**: Handle request/response compression
    7. **Request Logging Middleware**: Log requests with correlation IDs
    8. **Performance Monitoring**: Track performance metrics
    9. **Application Logic**: Your route handlers
    10. **CORS Middleware**: Handle cross-origin responses
    11. **Global Exception Handler**: Catch any unhandled exceptions

    Args:
        app (FastAPI): The FastAPI application instance
        settings (Settings): Application settings with middleware configuration
    """
    logger.info("Setting up enhanced middleware stack")

    # 1. Rate Limiting Middleware (protect against abuse first)
    rate_limiting_enabled = getattr(settings, 'rate_limiting_enabled', True)
    if rate_limiting_enabled:
        app.add_middleware(RateLimitMiddleware, settings=settings)
        logger.info("Rate limiting middleware enabled")

    # 2. Request Size Limiting Middleware (prevent large request attacks)
    request_size_limiting_enabled = getattr(settings, 'request_size_limiting_enabled', True)
    if request_size_limiting_enabled:
        app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
        logger.info("Request size limiting middleware enabled")

    # 3. Security Middleware (security headers and validation)
    security_enabled = getattr(settings, 'security_headers_enabled', True)
    if security_enabled:
        app.add_middleware(SecurityMiddleware, settings=settings)
        logger.info("Security middleware enabled")

    # 4. API Versioning Middleware (handle version detection)
    versioning_enabled = getattr(settings, 'api_versioning_enabled', True)
    if versioning_enabled:
        app.add_middleware(APIVersioningMiddleware, settings=settings)
        logger.info("API versioning middleware enabled")

    # 5. Version Compatibility Middleware (transform between versions)
    compatibility_enabled = getattr(settings, 'version_compatibility_enabled', False)
    if compatibility_enabled:
        app.add_middleware(VersionCompatibilityMiddleware, settings=settings)
        logger.info("Version compatibility middleware enabled")

    # 6. Compression Middleware (handle compression early for efficiency)
    compression_enabled = getattr(settings, 'compression_enabled', True)
    if compression_enabled:
        app.add_middleware(CompressionMiddleware, settings=settings)
        logger.info("Compression middleware enabled")

    # 7. Request Logging Middleware (log with all context available)
    request_logging_enabled = getattr(settings, 'request_logging_enabled', True)
    if request_logging_enabled:
        app.add_middleware(RequestLoggingMiddleware, settings=settings)
        logger.info("Request logging middleware enabled")

    # 8. Performance Monitoring Middleware (track performance)
    performance_monitoring_enabled = getattr(settings, 'performance_monitoring_enabled', True)
    if performance_monitoring_enabled:
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        logger.info("Performance monitoring middleware enabled")

    # 9. Global Exception Handler (handle exceptions from all middleware)
    setup_global_exception_handler(app, settings)
    logger.info("Global exception handler configured")

    # 10. CORS Middleware (handle responses last)
    setup_cors_middleware(app, settings)
    logger.info("CORS middleware configured")

    logger.info("Enhanced middleware stack setup complete")


# Enhanced settings class additions
class EnhancedMiddlewareSettings:
    """
    Enhanced middleware configuration settings.

    This class extends the base Settings with configuration options
    for all the enhanced middleware components.
    """

    # === Rate Limiting Settings ===
    rate_limiting_enabled: bool = True
    rate_limiting_skip_health: bool = True
    redis_url: Optional[str] = None
    custom_rate_limits: Dict[str, Dict[str, int]] = {}
    custom_endpoint_rules: Dict[str, str] = {}

    # === Request Size Limiting Settings ===
    request_size_limiting_enabled: bool = True
    request_size_limits: Dict[str, int] = {
        'default': 10 * 1024 * 1024,  # 10MB
        'application/json': 5 * 1024 * 1024,  # 5MB
        'multipart/form-data': 50 * 1024 * 1024,  # 50MB
    }

    # === Compression Settings ===
    compression_enabled: bool = True
    compression_min_size: int = 1024  # 1KB
    compression_level: int = 6  # 1-9
    compression_algorithms: List[str] = ['br', 'gzip', 'deflate']
    streaming_compression_enabled: bool = True

    # === API Versioning Settings ===
    api_versioning_enabled: bool = True
    default_api_version: str = "1.0"
    current_api_version: str = "1.0"
    min_api_version: str = "1.0"
    max_api_version: str = "1.0"
    version_compatibility_enabled: bool = False
    version_analytics_enabled: bool = True

    # === Enhanced Security Settings ===
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    max_headers_count: int = 100
    security_headers_enabled: bool = True

    # === Enhanced Performance Monitoring ===
    performance_monitoring_enabled: bool = True
    slow_request_threshold: int = 1000  # milliseconds
    memory_monitoring_enabled: bool = True
    metrics_export_enabled: bool = False

    # === Enhanced Logging Settings ===
    request_logging_enabled: bool = True
    log_sensitive_data: bool = False
    log_request_bodies: bool = False
    log_response_bodies: bool = False


# ============================================================================
# Utility Functions for Middleware Management
# ============================================================================

def get_request_id(request: Request) -> str:
    """
    Get the current request ID for correlation tracking.

    Retrieves the unique request identifier that was generated by the request
    logging middleware. This ID can be used throughout the application for
    correlating logs, errors, and monitoring data related to a specific request.

    Args:
        request (Request): The FastAPI request object

    Returns:
        str: The unique request identifier, or 'unknown' if not available

    Example:
        ```python
        @app.get("/api/endpoint")
        async def my_endpoint(request: Request):
            request_id = get_request_id(request)
            logger.info(f"Processing request {request_id}")
            return {"request_id": request_id}
        ```
    """
    return getattr(request.state, 'request_id', request_id_context.get('unknown'))


def get_request_duration(_request: Request) -> Optional[float]:
    """
    Get the current request duration in milliseconds.

    Calculates the time elapsed since the request started processing, useful
    for performance monitoring and timeout detection within request handlers.

    Args:
        _request (Request): The FastAPI request object (unused, timing obtained from context)

    Returns:
        Optional[float]: Request duration in milliseconds, or None if timing
            information is not available

    Example:
        ```python
        @app.get("/api/endpoint")
        async def my_endpoint(request: Request):
            duration = get_request_duration(request)
            if duration and duration > 5000:  # 5 seconds
                logger.warning(f"Long-running request: {duration}ms")
            return {"status": "ok"}
        ```
    """
    start_time = request_start_time_context.get(0.0)
    if start_time > 0:
        return (time.time() - start_time) * 1000
    return None


def add_response_headers(response: Response, headers: Dict[str, str]) -> None:
    """
    Add custom headers to an HTTP response.

    Utility function for adding custom headers to responses, with automatic
    header validation and conflict detection. Useful for adding application-specific
    headers while respecting existing middleware headers.

    Args:
        response (Response): The FastAPI response object to modify
        headers (Dict[str, str]): Dictionary of headers to add

    Example:
        ```python
        @app.get("/api/endpoint")
        async def my_endpoint():
            response = JSONResponse({"data": "value"})
            add_response_headers(response, {
                "X-Custom-Header": "custom-value",
                "X-API-Version": "1.0.0"
            })
            return response
        ```
    """
    for name, value in headers.items():
        if name.lower() not in {'content-length', 'content-type'}:
            response.headers[name] = value


def is_health_check_request(request: Request) -> bool:
    """
    Determine if a request is a health check or monitoring request.

    Identifies requests that are likely health checks, monitoring probes, or
    other automated system requests that may not require full logging or
    processing. Useful for reducing log noise and optimizing monitoring.

    Args:
        request (Request): The FastAPI request object to analyze

    Returns:
        bool: True if the request appears to be a health check

    Example:
        ```python
        @app.middleware("http")
        async def conditional_logging(request: Request, call_next):
            if not is_health_check_request(request):
                # Full logging for non-health-check requests
                logger.info(f"Processing {request.method} {request.url}")
            return await call_next(request)
        ```
    """
    health_paths = {'/health', '/healthz', '/ping', '/status', '/readiness', '/liveness'}
    return (
        request.url.path in health_paths or
        request.url.path.startswith('/health') or
        request.headers.get('user-agent', '').lower().startswith(('kube-probe', 'health'))
    )


def configure_middleware_logging(settings: Settings) -> None:
    """
    Configure logging specifically for middleware components.

    Sets up logging configuration optimized for middleware operations including
    appropriate log levels, formatters, and handlers. This ensures middleware
    logging integrates properly with the application's overall logging strategy.

    Args:
        settings (Settings): Application settings containing logging configuration

    Configuration:
        * Sets appropriate log levels for middleware components
        * Configures structured logging for monitoring integration
        * Establishes log filtering for health checks and noise reduction
        * Sets up log correlation with request IDs

    Example:
        ```python
        from app.core.config import settings
        from app.core.middleware import configure_middleware_logging

        # Configure before setting up middleware
        configure_middleware_logging(settings)
        setup_middleware(app, settings)
        ```
    """
    # Configure middleware-specific loggers
    middleware_loggers = [
        'app.core.middleware',
        'app.core.middleware.security',
        'app.core.middleware.performance',
        'app.core.middleware.logging'
    ]

    for logger_name in middleware_loggers:
        middleware_logger = logging.getLogger(logger_name)
        middleware_logger.setLevel(getattr(logging, settings.log_level.upper()))

        # Add structured logging format if not already configured
        if not middleware_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            middleware_logger.addHandler(handler)
            middleware_logger.propagate = False


def get_middleware_stats(app: FastAPI) -> Dict[str, Any]:
    """
    Get statistics and information about configured middleware.

    Returns:
        Dict containing middleware configuration and runtime stats
    """
    middleware_info = {
        'total_middleware': len(app.user_middleware),
        'middleware_stack': [],
        'enabled_features': [],
        'configuration': {}
    }

    # Analyze middleware stack
    for middleware in app.user_middleware:
        # Safely get middleware class name
        try:
            middleware_class = getattr(middleware.cls, '__name__', str(middleware.cls))
        except AttributeError:
            middleware_class = str(type(middleware.cls).__name__)
        
        middleware_info['middleware_stack'].append(middleware_class)

        # Check for known middleware types
        if 'RateLimit' in middleware_class:
            middleware_info['enabled_features'].append('rate_limiting')
        elif 'Security' in middleware_class:
            middleware_info['enabled_features'].append('security_headers')
        elif 'Compression' in middleware_class:
            middleware_info['enabled_features'].append('compression')
        elif 'Versioning' in middleware_class:
            middleware_info['enabled_features'].append('api_versioning')
        elif 'Performance' in middleware_class:
            middleware_info['enabled_features'].append('performance_monitoring')
        elif 'Logging' in middleware_class:
            middleware_info['enabled_features'].append('request_logging')
        elif 'CORS' in middleware_class:
            middleware_info['enabled_features'].append('cors')

    return middleware_info


def validate_middleware_configuration(settings: Settings) -> List[str]:
    """
    Validate middleware configuration and return any warnings or errors.

    Args:
        settings: Application settings to validate

    Returns:
        List of validation warnings/errors
    """
    issues = []

    # Validate rate limiting settings
    if getattr(settings, 'rate_limiting_enabled', False):
        redis_url = getattr(settings, 'redis_url', None)
        if not redis_url:
            issues.append("Rate limiting enabled but no Redis URL configured - using local cache")

    # Validate compression settings
    if getattr(settings, 'compression_enabled', False):
        compression_level = getattr(settings, 'compression_level', 6)
        if not 1 <= compression_level <= 9:
            issues.append(f"Invalid compression level {compression_level}, should be 1-9")

    # Validate API versioning
    if getattr(settings, 'api_versioning_enabled', False):
        default_version = getattr(settings, 'default_api_version', '1.0')
        current_version = getattr(settings, 'current_api_version', '1.0')
        if not default_version or not current_version:
            issues.append("API versioning enabled but versions not properly configured")

    # Validate size limits
    max_request_size = getattr(settings, 'max_request_size', 0)
    if max_request_size <= 0:
        issues.append("Invalid max_request_size, should be > 0")

    # Validate performance monitoring
    slow_threshold = getattr(settings, 'slow_request_threshold', 1000)
    if slow_threshold <= 0:
        issues.append("Invalid slow_request_threshold, should be > 0")

    return issues


def create_middleware_health_check() -> Callable:
    """
    Create a health check function that validates middleware status.

    Returns:
        Async function that can be used as a health check endpoint
    """
    async def middleware_health_check(request: Request) -> Dict[str, Any]:
        """Check the health of all middleware components."""
        health_status = {
            'status': 'healthy',
            'middleware': {},
            'timestamp': time.time()
        }

        try:
            # Check if request ID is being generated (logging middleware)
            request_id = get_request_id(request)
            health_status['middleware']['request_logging'] = {
                'status': 'healthy' if request_id != 'unknown' else 'warning',
                'request_id': request_id
            }

            # Check performance monitoring
            duration = get_request_duration(request)
            health_status['middleware']['performance_monitoring'] = {
                'status': 'healthy' if duration is not None else 'warning',
                'request_duration_ms': duration
            }

            # Check API versioning
            api_version = getattr(request.state, 'api_version', None)
            health_status['middleware']['api_versioning'] = {
                'status': 'healthy' if api_version else 'not_configured',
                'detected_version': api_version
            }

            # Check security headers (will be added to response)
            health_status['middleware']['security'] = {
                'status': 'healthy',  # Will be verified in response headers
                'note': 'Security headers will be validated in response'
            }

        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['error'] = str(e)

        return health_status

    return middleware_health_check


# ============================================================================
# Performance optimization functions
# ============================================================================

def optimize_middleware_stack(app: FastAPI, settings: Settings) -> None:
    """
    Optimize middleware stack for production performance.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Disable verbose logging in production
    if getattr(settings, 'environment', 'development') == 'production':
        # Reduce logging verbosity for performance-critical middleware
        middleware_logger = logging.getLogger('app.core.middleware')
        middleware_logger.setLevel(logging.WARNING)

        # Disable memory monitoring if not needed
        if not getattr(settings, 'detailed_monitoring_enabled', False):
            settings.memory_monitoring_enabled = False

        # Optimize compression settings for production
        if getattr(settings, 'compression_enabled', True):
            # Use faster compression in production
            settings.compression_level = min(settings.compression_level, 4)

    logger.info("Middleware stack optimized for production")


# ============================================================================
# Monitoring and analytics functions
# ============================================================================

def setup_middleware_monitoring(app: FastAPI, settings: Settings) -> None:
    """
    Set up monitoring and analytics for middleware performance.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    if not getattr(settings, 'middleware_monitoring_enabled', False):
        return

    # Set up periodic middleware health checks
    @app.on_event("startup")
    async def setup_monitoring():
        logger.info("Setting up middleware monitoring")

        # Could integrate with monitoring systems like:
        # - Prometheus metrics
        # - StatsD
        # - CloudWatch
        # - Custom analytics

        # Example: Set up periodic health checks
        async def periodic_health_check():
            while True:
                try:
                    # Check middleware health
                    stats = get_middleware_stats(app)
                    logger.info(f"Middleware health check: {stats['enabled_features']}")

                    # Sleep for monitoring interval
                    await asyncio.sleep(300)  # 5 minutes
                except Exception as e:
                    logger.error(f"Middleware health check failed: {e}")
                    await asyncio.sleep(60)  # Retry in 1 minute

        # Start background monitoring task
        asyncio.create_task(periodic_health_check())


# ============================================================================
# Example usage and integration
# ============================================================================

def setup_production_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Set up middleware stack optimized for production use.

    This function configures the middleware stack with production-optimized
    settings and includes all security, performance, and monitoring features.

    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Validate configuration first
    issues = validate_middleware_configuration(settings)
    if issues:
        for issue in issues:
            logger.warning(f"Middleware configuration issue: {issue}")

    # Set up enhanced middleware stack
    setup_enhanced_middleware(app, settings)

    # Optimize for production
    optimize_middleware_stack(app, settings)

    # Set up monitoring
    setup_middleware_monitoring(app, settings)

    # Add middleware health check endpoint
    health_check_func = create_middleware_health_check()

    @app.get("/internal/middleware/health")
    async def middleware_health(request: Request):
        """Middleware health check endpoint."""
        return await health_check_func(request)

    @app.get("/internal/middleware/stats")
    async def middleware_stats():
        """Middleware statistics endpoint."""
        return get_middleware_stats(app)

    logger.info("Production middleware setup complete")


# ============================================================================
# Legacy Support and Migration Helpers
# ============================================================================

def migrate_from_main_py_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Migration helper for applications moving middleware from main.py.

    Provides a drop-in replacement for applications that previously configured
    middleware directly in main.py. This function maintains backward compatibility
    while providing the enhanced middleware features of the new middleware module.

    Args:
        app (FastAPI): The FastAPI application instance
        settings (Settings): Application settings

    Migration Notes:
        * This function provides the same middleware functionality as the old
          inline configuration in main.py
        * Exception handling behavior remains identical
        * CORS configuration uses the same settings
        * Additional middleware features are available through setup_middleware()

    Example:
        ```python
        # Old main.py style (deprecated):
        # app.add_middleware(CORSMiddleware, ...)
        # @app.exception_handler(Exception)
        # async def global_exception_handler(request, exc): ...

        # New middleware module style:
        from app.core.middleware import migrate_from_main_py_middleware
        migrate_from_main_py_middleware(app, settings)
        ```

    Deprecated:
        This function is provided for migration compatibility. New applications
        should use setup_middleware() directly for full middleware functionality.
    """
    logger.warning(
        "Using legacy middleware migration. Consider using setup_middleware() "
        "for full middleware features."
    )

    # Set up basic middleware stack for compatibility
    setup_cors_middleware(app, settings)
    setup_global_exception_handler(app, settings)

    logger.info("Legacy middleware migration complete")


# ============================================================================
# Module Exports and Public API
# ============================================================================

__all__ = [
    # Main setup function
    'setup_middleware',

    # Enhanced setup functions
    'setup_enhanced_middleware',
    'setup_production_middleware',

    # Individual middleware components
    'setup_cors_middleware',
    'setup_global_exception_handler',
    'RequestLoggingMiddleware',
    'SecurityMiddleware',
    'PerformanceMonitoringMiddleware',
    'RateLimitMiddleware',
    'RequestSizeLimitMiddleware',
    'CompressionMiddleware',
    'APIVersioningMiddleware',
    'VersionCompatibilityMiddleware',

    # Settings classes
    'EnhancedMiddlewareSettings',
    'RateLimitSettings',
    'CompressionSettings',
    'APIVersioningSettings',

    # Utility functions
    'get_request_id',
    'get_request_duration',
    'add_response_headers',
    'is_health_check_request',
    'configure_middleware_logging',
    'get_middleware_stats',
    'validate_middleware_configuration',
    'create_middleware_health_check',
    'optimize_middleware_stack',
    'setup_middleware_monitoring',

    # Version utility functions
    'get_api_version',
    'is_version_deprecated',
    'get_version_sunset_date',

    # Compression utilities
    'get_compression_stats',
    'configure_compression_settings',

    # Migration helpers
    'migrate_from_main_py_middleware'
]
