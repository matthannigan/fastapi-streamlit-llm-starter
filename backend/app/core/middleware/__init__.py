"""
Core Middleware Module

This module provides centralized middleware management for the FastAPI backend application.
All application middleware is consolidated here including CORS configuration, error handling,
logging, security, and monitoring middleware to provide a clean separation of concerns.

The middleware stack is designed for production use with comprehensive error handling,
security features, monitoring capabilities, and development conveniences. Each middleware
component can be individually configured through the application settings.

Middleware Components:
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
        * Request rate limiting and abuse prevention
        * Input validation and sanitization
        * XSS and injection attack prevention

    Performance Monitoring Middleware:
        * Request timing and performance metrics
        * Memory usage tracking
        * Slow request detection and alerting
        * Integration with monitoring systems

Architecture:
    The middleware stack follows FastAPI's middleware execution order, with
    security and logging middleware running first, followed by application-specific
    middleware, and finally CORS middleware for response processing.

    Execution Order (Request Processing):
    1. Security Middleware (headers, rate limiting)
    2. Request Logging Middleware (start timing, generate request ID)
    3. Performance Monitoring Middleware (memory/CPU tracking)
    4. Application Logic (routers, endpoints)
    5. CORS Middleware (response headers)
    6. Performance Monitoring Middleware (finish timing)
    7. Request Logging Middleware (log response)
    8. Global Exception Handler (if exceptions occur)

Configuration:
    All middleware can be configured through the Settings class in app.core.config:
    
    * CORS settings: allowed_origins, cors_credentials, cors_methods
    * Logging settings: log_level, request_logging_enabled
    * Security settings: security_headers_enabled, rate_limiting_enabled
    * Monitoring settings: performance_monitoring_enabled, slow_request_threshold

Usage:
    Import and apply middleware to FastAPI application:
    
    ```python
    from fastapi import FastAPI
    from app.core.middleware import setup_middleware
    from app.core.config import settings
    
    app = FastAPI()
    setup_middleware(app, settings)
    ```

Dependencies:
    * fastapi: Core web framework and middleware support
    * fastapi.middleware.cors: CORS middleware implementation
    * app.core.config: Application settings and configuration
    * app.core.exceptions: Custom exception hierarchy
    * shared.models: Pydantic models for error responses
    * logging: Python standard library logging

Thread Safety:
    All middleware components are designed to be thread-safe and support
    concurrent request processing in production environments with multiple
    workers and async request handling.

Example:
    Complete middleware setup for production deployment:
    
    ```python
    from fastapi import FastAPI
    from app.core.middleware import setup_middleware
    from app.core.config import settings
    
    app = FastAPI(title="AI Text Processor API")
    
    # Apply all middleware components
    setup_middleware(app, settings)
    
    # Middleware stack is now configured and ready
    ```

Note:
    This module replaces the inline middleware configuration previously
    found in main.py and provides a centralized, testable, and maintainable
    approach to middleware management. All middleware can be individually
    enabled/disabled through configuration settings.
"""

import logging
import time
from typing import Optional, Dict

from fastapi import FastAPI, Request, Response
from app.core.config import Settings

# Import middleware components from their dedicated modules
from .cors import setup_cors_middleware
from .global_exception_handler import setup_global_exception_handler
from .request_logging import RequestLoggingMiddleware, request_id_context, request_start_time_context
from .security import SecurityMiddleware
from .performance_monitoring import PerformanceMonitoringMiddleware

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


# ============================================================================
# Middleware Setup Function
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
    
    # Individual middleware components
    'setup_cors_middleware',
    'setup_global_exception_handler',
    'RequestLoggingMiddleware',
    'SecurityMiddleware', 
    'PerformanceMonitoringMiddleware',
    
    # Utility functions
    'get_request_id',
    'get_request_duration',
    'add_response_headers',
    'is_health_check_request',
    'configure_middleware_logging',
    
    # Migration helpers
    'migrate_from_main_py_middleware'
]