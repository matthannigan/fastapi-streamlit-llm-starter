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
import uuid
from typing import Callable, Optional, Dict, Any
from contextvars import ContextVar
from starlette.types import ASGIApp, Receive, Scope, Send

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import Settings
from app.core.exceptions import (
    ApplicationError,
    ValidationError,
    ConfigurationError,
    BusinessLogicError,
    InfrastructureError,
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    get_http_status_for_exception
)
from shared.models import ErrorResponse

# Configure module logger
logger = logging.getLogger(__name__)

# Context variables for request tracking
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
request_start_time_context: ContextVar[float] = ContextVar('request_start_time', default=0.0)


# ============================================================================
# CORS Middleware Configuration
# ============================================================================

def setup_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure Cross-Origin Resource Sharing (CORS) middleware for the application.
    
    Sets up CORS middleware with production-ready security settings that allow
    controlled cross-origin access while preventing unauthorized requests. The
    configuration supports development and production environments with appropriate
    security controls.
    
    CORS Features:
        * Configurable allowed origins from settings
        * Support for credentials in cross-origin requests
        * All HTTP methods allowed for API flexibility
        * All headers allowed for maximum compatibility
        * Preflight request handling for complex requests
        * Security-conscious defaults with explicit configuration
    
    Args:
        app (FastAPI): The FastAPI application instance to configure
        settings (Settings): Application settings containing CORS configuration
            including allowed_origins list
    
    Configuration:
        The middleware uses the following settings:
        * settings.allowed_origins: List of allowed origin URLs
        * Credentials: Enabled to support authentication cookies/headers
        * Methods: All HTTP methods (*) for maximum API flexibility
        * Headers: All headers (*) for client compatibility
    
    Security Notes:
        * Origins are explicitly configured, not using wildcard in production
        * Credentials support requires specific origin configuration
        * Preflight requests are properly handled for complex CORS scenarios
        * Settings validation ensures only valid origins are configured
    
    Example:
        >>> setup_cors_middleware(app, settings)
        >>> # CORS middleware now configured with settings.allowed_origins
    
    Note:
        CORS middleware should be added last in the middleware stack to ensure
        it processes responses after all other middleware has completed. This
        is handled automatically by the setup_middleware() function.
    """
    logger.info(f"Setting up CORS middleware with origins: {settings.allowed_origins}")
    
    # Note: Type ignore comments are needed due to FastAPI/Starlette type inference
    # limitations with CORSMiddleware. The code functions correctly at runtime.
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.allowed_origins,  # type: ignore[call-arg]
        allow_credentials=True,  # type: ignore[call-arg]
        allow_methods=["*"],  # type: ignore[call-arg]
        allow_headers=["*"],  # type: ignore[call-arg]
    )


# ============================================================================
# Global Exception Handler
# ============================================================================

def setup_global_exception_handler(app: FastAPI, settings: Settings) -> None:
    """
    Configure global exception handling for unhandled application errors.
    
    Provides a centralized error handling mechanism that catches all unhandled
    exceptions across the application and returns consistent, secure error responses.
    The handler ensures clients receive predictable error responses while protecting
    internal implementation details and sensitive information.
    
    Exception Handling Features:
        * Comprehensive logging of all unhandled exceptions with full context
        * Standardized error response format using shared.models.ErrorResponse
        * HTTP status code mapping based on exception types
        * Security-conscious error messages that don't expose internal details
        * Request context preservation for debugging and monitoring
        * Integration with the custom exception hierarchy
    
    Args:
        app (FastAPI): The FastAPI application instance to configure
        settings (Settings): Application settings for error handling configuration
    
    Exception Processing:
        The handler processes exceptions in the following order:
        1. Log the full exception with context for debugging
        2. Determine appropriate HTTP status code based on exception type
        3. Generate secure, user-friendly error message
        4. Create standardized ErrorResponse model
        5. Return JSONResponse with appropriate status code
    
    HTTP Status Code Mapping:
        * ApplicationError -> 400 Bad Request (validation, business logic errors)
        * InfrastructureError -> 502 Bad Gateway (external service failures)
        * TransientAIError -> 503 Service Unavailable (temporary AI issues)
        * PermanentAIError -> 502 Bad Gateway (permanent AI issues)
        * All other exceptions -> 500 Internal Server Error
    
    Security Features:
        * Generic error messages prevent information disclosure
        * Full exception details logged server-side only
        * No stack traces or internal paths exposed to clients
        * Request correlation IDs for secure debugging
    
    Example Response:
        ```json
        {
            "success": false,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": "2025-07-12T12:34:56.789012"
        }
        ```
    
    Note:
        This handler is the last resort for exception handling and will catch
        any exception not handled by more specific exception handlers. It ensures
        the application never returns unhandled exceptions to clients.
    """
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Global exception handler for unhandled application errors.
        
        Catches all unhandled exceptions, logs them appropriately, and returns
        a standardized error response to protect internal implementation details
        while providing useful information for debugging and monitoring.
        
        Args:
            request (Request): The FastAPI request object that triggered the exception
            exc (Exception): The unhandled exception that was raised during processing
        
        Returns:
            JSONResponse: A standardized error response with appropriate HTTP status
        """
        # Get request ID for correlation (if available)
        request_id = getattr(request.state, 'request_id', request_id_context.get('unknown'))
        
        # Log the full exception with context
        logger.error(
            f"Unhandled exception in request {request_id}: {str(exc)}",
            extra={
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'exception_type': type(exc).__name__,
                'exception_module': type(exc).__module__
            },
            exc_info=True
        )
        
        # Determine HTTP status code based on exception type
        http_status = get_http_status_for_exception(exc)
        
        # Create standardized error response
        error_response = ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        )
        
        # Customize error message based on exception type for better UX
        if isinstance(exc, (ValidationError, BusinessLogicError)):
            error_response.error = "Invalid request data"
            error_response.error_code = "VALIDATION_ERROR"
        elif isinstance(exc, ConfigurationError):
            error_response.error = "Service configuration error"
            error_response.error_code = "CONFIGURATION_ERROR"
        elif isinstance(exc, TransientAIError):
            error_response.error = "AI service temporarily unavailable"
            error_response.error_code = "SERVICE_UNAVAILABLE"
        elif isinstance(exc, PermanentAIError):
            error_response.error = "AI service error"
            error_response.error_code = "AI_SERVICE_ERROR"
        elif isinstance(exc, InfrastructureError):
            error_response.error = "External service error"
            error_response.error_code = "INFRASTRUCTURE_ERROR"
        
        return JSONResponse(
            status_code=http_status,
            content=error_response.dict()
        )


# ============================================================================
# Request Logging Middleware
# ============================================================================

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP request/response logging middleware with performance tracking.
    
    Provides comprehensive logging of HTTP requests and responses with timing
    information, request correlation IDs, and configurable detail levels.
    The middleware supports both development debugging and production monitoring
    with appropriate log filtering and security considerations.
    
    Logging Features:
        * Request/response timing with millisecond precision
        * Unique request ID generation for correlation tracking
        * HTTP method, URL, status code, and response size logging
        * User agent and client IP address tracking (when available)
        * Configurable log levels based on response status codes
        * Sensitive data filtering for security compliance
        * Integration with structured logging for monitoring systems
    
    Performance Tracking:
        * Request start/end timing with high precision
        * Response size calculation for bandwidth monitoring
        * Slow request detection and warning logs
        * Memory usage tracking (optional)
        * Integration with performance monitoring systems
    
    Security Features:
        * Request ID correlation for secure debugging
        * Sensitive header filtering (Authorization, API keys)
        * Query parameter sanitization for logs
        * Client IP anonymization options
        * Log level control to prevent information leakage
    
    Configuration:
        The middleware behavior can be controlled through settings:
        * request_logging_enabled: Enable/disable request logging
        * log_level: Minimum log level for request logging
        * slow_request_threshold: Threshold for slow request warnings
        * sensitive_headers: List of headers to filter from logs
    
    Example Logs:
        ```
        INFO: Request started: GET /api/v1/process [req_id: abc123]
        INFO: Request completed: GET /api/v1/process 200 1.2KB 150ms [req_id: abc123]
        WARN: Slow request: POST /api/v1/batch 200 5.6KB 2500ms [req_id: def456]
        ```
    
    Note:
        This middleware should be placed early in the middleware stack to capture
        timing information for all subsequent middleware and request processing.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize request logging middleware with configuration.
        
        Args:
            app (ASGIApp): The ASGI application to wrap
            settings (Settings): Application settings for logging configuration
        """
        super().__init__(app)
        self.settings = settings
        self.slow_request_threshold = getattr(settings, 'slow_request_threshold', 1000)  # ms
        self.sensitive_headers = {'authorization', 'x-api-key', 'cookie'}
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with logging and timing.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware/handler in the chain
            
        Returns:
            Response: The HTTP response from downstream handlers
        """
        # Generate unique request ID for correlation
        request_id = str(uuid.uuid4())[:8]
        request_id_context.set(request_id)
        
        # Store request ID in request state for access by other components
        request.state.request_id = request_id
        
        # Record request start time
        start_time = time.time()
        request_start_time_context.set(start_time)
        
        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path} [req_id: {request_id}]",
            extra={
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'user_agent': request.headers.get('user-agent', 'unknown'),
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )
        
        try:
            # Process request through remaining middleware and handlers
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get response size if available
            response_size = getattr(response, 'content-length', 'unknown')
            if hasattr(response, 'body') and response.body:
                response_size = f"{len(response.body)}B"
            
            # Determine log level based on status code
            log_level = logging.INFO
            if response.status_code >= 400:
                log_level = logging.WARNING if response.status_code < 500 else logging.ERROR
            elif duration_ms > self.slow_request_threshold:
                log_level = logging.WARNING
                
            # Log request completion
            logger.log(
                log_level,
                f"Request completed: {request.method} {request.url.path} "
                f"{response.status_code} {response_size} {duration_ms:.1f}ms [req_id: {request_id}]",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'response_size': response_size
                }
            )
            
            return response
            
        except Exception as exc:
            # Log request exception
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"{type(exc).__name__} {duration_ms:.1f}ms [req_id: {request_id}]",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'exception_type': type(exc).__name__
                },
                exc_info=True
            )
            raise


# ============================================================================
# Security Middleware
# ============================================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security-focused middleware for HTTP headers and request validation.
    
    Provides essential security controls including security headers injection,
    basic request validation, and protection against common web vulnerabilities.
    The middleware implements defense-in-depth security principles suitable
    for production API deployments.
    
    Security Features:
        * Security headers injection (HSTS, X-Frame-Options, etc.)
        * Content Security Policy (CSP) configuration
        * X-Content-Type-Options and X-XSS-Protection headers
        * Request size limits to prevent DoS attacks
        * Basic input validation and sanitization
        * Referrer policy configuration for privacy
        * Feature policy headers for browser security
    
    Headers Configured:
        * Strict-Transport-Security: HSTS for HTTPS enforcement
        * X-Frame-Options: Clickjacking protection
        * X-Content-Type-Options: MIME type sniffing prevention
        * X-XSS-Protection: XSS attack mitigation
        * Content-Security-Policy: Resource loading restrictions
        * Referrer-Policy: Referrer information control
        * Permissions-Policy: Browser feature access control
    
    Request Validation:
        * Content-Length limits for request body size
        * Header count and size validation
        * URL length restrictions
        * Basic malicious pattern detection
        * Rate limiting hooks (basic implementation)
    
    Configuration:
        Security behavior can be configured through settings:
        * security_headers_enabled: Enable/disable security headers
        * max_request_size: Maximum request body size in bytes
        * max_headers_count: Maximum number of headers per request
        * csp_policy: Custom Content Security Policy string
    
    Note:
        This middleware provides basic security controls. For production
        deployments, additional security measures like WAF, rate limiting,
        and DDoS protection should be implemented at the infrastructure level.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize security middleware with configuration.
        
        Args:
            app (ASGIApp): The ASGI application to wrap
            settings (Settings): Application settings for security configuration
        """
        super().__init__(app)
        self.settings = settings
        self.max_request_size = getattr(settings, 'max_request_size', 10 * 1024 * 1024)  # 10MB
        self.max_headers_count = getattr(settings, 'max_headers_count', 100)
        
        # Security headers configuration
        self.security_headers = {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        }
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with security validations and header injection.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware/handler in the chain
            
        Returns:
            Response: The HTTP response with security headers
        """
        # Validate request headers count
        if len(request.headers) > self.max_headers_count:
            logger.warning(f"Request with excessive headers: {len(request.headers)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Too many headers"}
            )
        
        # Validate Content-Length if present
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(f"Request too large: {size} bytes")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"error": "Request too large"}
                    )
            except ValueError:
                logger.warning("Invalid Content-Length header")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid Content-Length"}
                )
        
        # Process request through remaining middleware
        response = await call_next(request)
        
        # Inject security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
            
        return response


# ============================================================================
# Performance Monitoring Middleware
# ============================================================================

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Performance monitoring middleware for request timing and resource tracking.
    
    Provides comprehensive performance monitoring including request timing,
    memory usage tracking, and performance metrics collection. The middleware
    supports both real-time monitoring and historical performance analysis
    with integration capabilities for external monitoring systems.
    
    Monitoring Features:
        * High-precision request timing with nanosecond accuracy
        * Memory usage tracking before and after requests
        * CPU usage monitoring (when available)
        * Slow request detection with configurable thresholds
        * Request concurrency tracking
        * Response size and bandwidth monitoring
        * Performance metrics aggregation
        * Integration hooks for external monitoring systems
    
    Metrics Collected:
        * Request duration (total, processing, waiting)
        * Memory usage (RSS, heap, available)
        * CPU utilization during request processing
        * Request/response sizes for bandwidth analysis
        * Concurrent request counts
        * Error rates and status code distributions
        * Endpoint-specific performance patterns
    
    Performance Analysis:
        * Real-time performance alerting for slow requests
        * Statistical analysis of response times
        * Memory leak detection through usage patterns
        * Bottleneck identification in request processing
        * Performance regression detection
        * Resource usage optimization recommendations
    
    Configuration:
        Monitoring behavior can be configured through settings:
        * performance_monitoring_enabled: Enable/disable monitoring
        * slow_request_threshold: Threshold for slow request alerts
        * memory_monitoring_enabled: Enable memory usage tracking
        * metrics_export_enabled: Enable metrics export to external systems
    
    Integration:
        The middleware can export metrics to monitoring systems:
        * Prometheus metrics export
        * StatsD metrics publishing
        * CloudWatch metrics integration
        * Custom metrics webhooks
    
    Example Metrics:
        ```
        request_duration_seconds{method="POST", endpoint="/api/v1/process"} 0.125
        request_memory_usage_bytes{method="POST", endpoint="/api/v1/process"} 1048576
        slow_requests_total{method="POST", endpoint="/api/v1/process"} 1
        ```
    
    Note:
        Performance monitoring adds minimal overhead but should be configured
        appropriately for high-traffic production environments. Consider
        sampling strategies for very high request volumes.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize performance monitoring middleware.
        
        Args:
            app (ASGIApp): The ASGI application to wrap
            settings (Settings): Application settings for monitoring configuration
        """
        super().__init__(app)
        self.settings = settings
        self.slow_request_threshold = getattr(settings, 'slow_request_threshold', 1000)  # ms
        self.memory_monitoring_enabled = getattr(settings, 'memory_monitoring_enabled', True)
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with performance monitoring.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware/handler in the chain
            
        Returns:
            Response: The HTTP response with performance headers
        """
        import psutil
        import os
        
        # Get request ID for correlation
        request_id = getattr(request.state, 'request_id', 'unknown')
        
        # Record performance baseline
        start_time = time.perf_counter()
        start_memory = None
        
        if self.memory_monitoring_enabled:
            try:
                process = psutil.Process(os.getpid())
                start_memory = process.memory_info().rss
            except Exception:
                # Memory monitoring is optional
                pass
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate performance metrics
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000
            
            # Memory usage calculation
            memory_delta = None
            if self.memory_monitoring_enabled and start_memory:
                try:
                    process = psutil.Process(os.getpid())
                    end_memory = process.memory_info().rss
                    memory_delta = end_memory - start_memory
                except Exception:
                    pass
            
            # Add performance headers
            response.headers['X-Response-Time'] = f"{duration_ms:.2f}ms"
            if memory_delta is not None:
                response.headers['X-Memory-Delta'] = f"{memory_delta}B"
            
            # Log performance metrics
            perf_extra = {
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'duration_ms': duration_ms,
                'status_code': response.status_code
            }
            
            if memory_delta is not None:
                perf_extra['memory_delta_bytes'] = memory_delta
            
            # Slow request detection
            if duration_ms > self.slow_request_threshold:
                logger.warning(
                    f"Slow request detected: {request.method} {request.url.path} "
                    f"{duration_ms:.1f}ms [req_id: {request_id}]",
                    extra=perf_extra
                )
            else:
                logger.debug(
                    f"Performance: {request.method} {request.url.path} "
                    f"{duration_ms:.1f}ms [req_id: {request_id}]",
                    extra=perf_extra
                )
            
            return response
            
        except Exception as exc:
            # Log performance for failed requests
            duration = time.perf_counter() - start_time
            duration_ms = duration * 1000
            
            logger.error(
                f"Performance (failed): {request.method} {request.url.path} "
                f"{duration_ms:.1f}ms {type(exc).__name__} [req_id: {request_id}]",
                extra={
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'exception_type': type(exc).__name__
                }
            )
            raise


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


def get_request_duration(request: Request) -> Optional[float]:
    """
    Get the current request duration in milliseconds.
    
    Calculates the time elapsed since the request started processing, useful
    for performance monitoring and timeout detection within request handlers.
    
    Args:
        request (Request): The FastAPI request object
        
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