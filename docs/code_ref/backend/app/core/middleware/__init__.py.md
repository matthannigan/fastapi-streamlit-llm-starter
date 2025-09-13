---
sidebar_label: __init__
---

# Core Middleware Infrastructure Package

  file_path: `backend/app/core/middleware/__init__.py`

This package provides comprehensive middleware management for the FastAPI backend application,
implementing a production-ready middleware stack with security, monitoring, performance optimization,
and operational capabilities. The middleware architecture follows best practices for API security,
observability, and resilience patterns.

## Package Architecture

The middleware system follows a layered architecture designed for maximum security,
performance, and operational visibility:

### Security Layer
- **Security Middleware**: Essential HTTP security headers and request validation
- **CORS Middleware**: Cross-origin resource sharing with configurable policies
- **Rate Limiting**: Redis-backed distributed rate limiting with graceful degradation
- **Request Size Limiting**: DoS protection through request size validation

### Monitoring & Observability Layer
- **Request Logging**: Comprehensive HTTP request/response logging with correlation IDs
- **Performance Monitoring**: Resource tracking, timing analysis, and slow request detection
- **Global Exception Handling**: Centralized error handling with structured responses
- **Health Check Integration**: Middleware health validation and status reporting

### Performance Optimization Layer
- **Compression Middleware**: Intelligent request/response compression with multiple algorithms
- **API Versioning**: Version detection, routing, and backward compatibility
- **Request Optimization**: Efficient request processing and resource management

## Core Middleware Components

### Security Middleware (`security.py`)
Comprehensive security hardening with HTTP security headers:
- **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options protection
- **Input Validation**: Request header validation and sanitization
- **DoS Protection**: Request size limits and header count restrictions
- **XSS Protection**: Cross-site scripting prevention and content type validation
- **API Security**: Production-ready security policies for API endpoints

### Request Logging Middleware (`request_logging.py`)
Structured logging system with correlation tracking:
- **Correlation IDs**: Unique request identifiers for distributed tracing
- **Performance Metrics**: Request timing, response size, and status code tracking
- **Sensitive Data Filtering**: Automatic filtering of sensitive information
- **Health Check Optimization**: Reduced logging noise for monitoring requests
- **Structured Logging**: JSON-formatted logs for monitoring system integration

### Performance Monitoring Middleware (`performance_monitoring.py`)
Real-time performance tracking and alerting:
- **Resource Monitoring**: Memory usage, CPU utilization, and request concurrency
- **Slow Request Detection**: Configurable thresholds for performance alerting
- **Response Time Analysis**: Detailed timing breakdown with percentile calculations
- **Memory Leak Detection**: Memory usage pattern analysis and alerting
- **Integration Ready**: Prometheus, StatsD, and custom monitoring system support

### Rate Limiting Middleware (`rate_limiting.py`)
Distributed rate limiting with Redis backend:
- **Per-Endpoint Limits**: Configurable rate limits per API endpoint
- **Per-User Limits**: User-specific rate limiting with authentication integration
- **Sliding Window**: Advanced rate limiting algorithms with burst support
- **Redis Integration**: Distributed rate limiting across multiple application instances
- **Graceful Degradation**: Local fallback when Redis is unavailable

### Compression Middleware (`compression.py`)
Intelligent compression for improved performance:
- **Multi-Algorithm Support**: Brotli, gzip, and deflate compression
- **Content-Type Awareness**: Intelligent compression decisions based on content type
- **Streaming Compression**: Efficient compression for large responses
- **Compression Analytics**: Compression ratio tracking and optimization metrics
- **Dynamic Configuration**: Runtime compression configuration and tuning

### API Versioning Middleware (`api_versioning.py`)
Comprehensive API version management:
- **Multiple Detection Methods**: URL, header, and query parameter version detection
- **Backward Compatibility**: Automatic transformation between API versions
- **Deprecation Management**: Version sunset dates and deprecation warnings
- **Version Analytics**: Usage tracking and migration planning support
- **Compatibility Layer**: Seamless migration support for client applications

## Middleware Execution Architecture

### LIFO Execution Order
FastAPI middleware follows Last-In-First-Out execution order. The middleware stack
is designed to optimize security, performance, and monitoring:

```
Request Processing Flow:
1. CORS Middleware (preflight handling, added last, runs first)
2. Performance Monitoring (establish timing context)
3. Request Logging (correlation ID generation)
4. Compression Middleware (request decompression)
5. Version Compatibility (API version transformation)
6. API Versioning (version detection and routing)
7. Security Middleware (security validation and headers)
8. Request Size Limiting (DoS protection)
9. Rate Limiting (abuse prevention, added first, runs last)
10. Application Logic (route handlers and business logic)
11. Global Exception Handler (error handling, not true middleware)

Response Processing Flow (reverse order):
Rate Limiting → Request Size → Security → Versioning → Compression → Logging → Monitoring → CORS
```

### Integration Patterns

#### Infrastructure Service Integration
```python
from app.core.middleware import setup_middleware
from app.core.config import settings
from app.infrastructure.cache import get_cache_service
from app.infrastructure.monitoring import HealthChecker

# Middleware with infrastructure integration
app = FastAPI()
setup_middleware(app, settings)

# Cache integration for rate limiting
cache_service = get_cache_service()
rate_limit_middleware = RateLimitMiddleware(cache_service=cache_service)
```

#### Configuration-Driven Setup
```python
from app.core.middleware import setup_enhanced_middleware, validate_middleware_configuration

# Validate configuration before setup
issues = validate_middleware_configuration(settings)
if issues:
    for issue in issues:
        logger.warning(f"Middleware config issue: {issue}")

# Setup with validated configuration
setup_enhanced_middleware(app, settings)
```

#### Production Optimization
```python
from app.core.middleware import setup_production_middleware

# Production-optimized middleware stack
setup_production_middleware(app, settings)

# Includes:
# - Performance optimization
# - Security hardening
# - Monitoring integration
# - Health check endpoints
```

## Configuration Architecture

### Environment-Specific Configuration
- **Development**: Enhanced logging, relaxed security, debugging features
- **Testing**: Isolated configuration, mock integrations, fast execution
- **Production**: Security hardening, performance optimization, full monitoring

### Feature Toggles
```python
# Security configuration
security_headers_enabled: bool = True
max_request_size: int = 10 * 1024 * 1024  # 10MB
max_headers_count: int = 100

# Performance configuration
performance_monitoring_enabled: bool = True
slow_request_threshold: int = 1000  # milliseconds
memory_monitoring_enabled: bool = True

# Rate limiting configuration
rate_limiting_enabled: bool = True
redis_url: str = "redis://localhost:6379"
custom_rate_limits: Dict[str, Dict[str, int]] = {}

# Compression configuration
compression_enabled: bool = True
compression_min_size: int = 1024  # 1KB
compression_algorithms: List[str] = ['br', 'gzip', 'deflate']

# API versioning configuration
api_versioning_enabled: bool = True
default_api_version: str = "1.0"
version_compatibility_enabled: bool = False
```

## Usage Patterns

### Basic Middleware Setup
```python
from fastapi import FastAPI
from app.core.middleware import setup_middleware
from app.core.config import settings

app = FastAPI()

# Basic production-ready middleware stack
setup_middleware(app, settings)

# Provides:
# - Security headers
# - Request logging
# - Performance monitoring
# - Global exception handling
# - CORS configuration
```

### Enhanced Middleware Stack
```python
from app.core.middleware import setup_enhanced_middleware

app = FastAPI()

# Full-featured middleware stack
setup_enhanced_middleware(app, settings)

# Additional features:
# - Rate limiting
# - Request compression
# - API versioning
# - Advanced monitoring
# - Request size limiting
```

### Production Deployment
```python
from app.core.middleware import setup_production_middleware

app = FastAPI(title="Production API")

# Production-optimized setup
setup_production_middleware(app, settings)

# Includes:
# - Configuration validation
# - Performance optimization
# - Health check endpoints
# - Monitoring integration
# - Security hardening
```

### Custom Middleware Configuration
```python
from app.core.middleware import (
    SecurityMiddleware,
    RateLimitMiddleware,
    CompressionMiddleware
)

app = FastAPI()

# Custom middleware configuration
app.add_middleware(
    RateLimitMiddleware,
    settings=settings,
    custom_limits={
        "POST /api/v1/process": {"requests": 10, "period": 60},
        "GET /api/v1/status": {"requests": 100, "period": 60}
    }
)

app.add_middleware(SecurityMiddleware, settings=settings)
app.add_middleware(CompressionMiddleware, settings=settings)
```

## Performance Characteristics

### Middleware Overhead
- **Security Middleware**: < 0.5ms per request
- **Request Logging**: < 1ms per request (with filtering)
- **Performance Monitoring**: < 0.2ms per request
- **Rate Limiting**: < 2ms per request (Redis-backed)
- **Compression**: Variable (depends on content size and algorithm)
- **Total Overhead**: < 5ms for full enhanced stack

### Memory Usage
- **Base Middleware Stack**: < 1MB additional memory
- **Rate Limiting Cache**: Configurable (Redis-backed by default)
- **Compression Buffers**: Streaming design minimizes memory usage
- **Monitoring Data**: Circular buffers with configurable retention

### Scalability
- **Concurrent Requests**: Supports thousands of concurrent requests
- **Multiple Workers**: Full support for multi-worker deployments
- **Distributed Operation**: Redis-backed rate limiting across instances
- **Resource Management**: Proper cleanup and resource management

## Security Features

### Defense in Depth
- **Input Validation**: Request size, header count, and content validation
- **Security Headers**: Comprehensive HTTP security header implementation
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Error Handling**: Secure error responses without information disclosure

### Security Headers
```python
# Automatically configured security headers:
{
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}
```

### Threat Mitigation
- **XSS Protection**: Content-type validation and security headers
- **CSRF Protection**: SameSite cookie policies and origin validation
- **DoS Protection**: Request size limits and rate limiting
- **Information Disclosure**: Sanitized error responses and structured logging

## Monitoring & Observability

### Request Correlation
```python
from app.core.middleware import get_request_id, get_request_duration

@app.get("/api/endpoint")
async def my_endpoint(request: Request):
    request_id = get_request_id(request)
    duration = get_request_duration(request)
    
    logger.info(f"Processing request {request_id}, duration: {duration}ms")
    return {"request_id": request_id}
```

### Health Monitoring
```python
from app.core.middleware import create_middleware_health_check

# Built-in health check for middleware stack
health_check = create_middleware_health_check()

@app.get("/health/middleware")
async def middleware_health(request: Request):
    return await health_check(request)
```

### Performance Analytics
```python
from app.core.middleware import get_middleware_stats

# Middleware performance statistics
stats = get_middleware_stats(app)
# Returns: middleware count, enabled features, configuration
```

## Testing Support

### Middleware Testing
```python
from app.core.middleware import validate_middleware_configuration

# Configuration validation
issues = validate_middleware_configuration(settings)
assert len(issues) == 0, f"Configuration issues: {issues}"

# Health check testing
health_check = create_middleware_health_check()
result = await health_check(mock_request)
assert result["status"] == "healthy"
```

### Mock Integration
```python
# Test configuration for isolated testing
test_settings = Settings(
    rate_limiting_enabled=False,
    security_headers_enabled=True,
    performance_monitoring_enabled=False,
    request_logging_enabled=True
)

setup_middleware(test_app, test_settings)
```

## Migration & Compatibility

### Legacy Support
```python
from app.core.middleware import migrate_from_main_py_middleware

# Migration helper for applications moving from main.py middleware
migrate_from_main_py_middleware(app, settings)
```

### Gradual Migration
- **Backward Compatibility**: All existing configurations continue to work
- **Feature Flags**: Individual middleware components can be enabled/disabled
- **Configuration Migration**: Automatic migration from legacy configurations
- **Documentation**: Comprehensive migration guides and examples

## EnhancedMiddlewareSettings

Enhanced middleware configuration settings.

This class extends the base Settings with configuration options
for all the enhanced middleware components.

## setup_middleware()

```python
def setup_middleware(app: FastAPI, settings: Settings) -> None:
```

Configure comprehensive middleware stack for production-ready FastAPI application.

This function establishes a complete middleware infrastructure providing security, monitoring,
performance optimization, and operational visibility. The middleware stack is designed
following security best practices and production deployment requirements.

Args:
    app: FastAPI application instance to configure with middleware stack
    settings: Application settings containing middleware configuration options
        and feature toggles for individual middleware components

Behavior:
    - Applies middleware in optimal execution order for security and performance
    - Enables/disables middleware components based on settings configuration
    - Configures production-ready security headers and CORS policies
    - Establishes request correlation and performance tracking infrastructure
    - Sets up centralized exception handling with structured error responses
    - Integrates with application logging and monitoring systems
    - Provides graceful degradation when optional components fail
    
Middleware Stack Order (LIFO Execution):
    Due to FastAPI's Last-In-First-Out middleware execution, the setup order
    is reverse of the actual execution order:
    
    Setup Order → Execution Order:
    1. Security Middleware → Runs 4th (request validation)
    2. Request Logging → Runs 3rd (correlation ID generation)  
    3. Performance Monitoring → Runs 2nd (timing context)
    4. Global Exception Handler → Catches all exceptions
    5. CORS Middleware → Runs 1st (preflight handling)

Configuration Integration:
    Uses the following settings for middleware behavior control:
    - `security_headers_enabled`: Enable HTTP security headers (default: True)
    - `request_logging_enabled`: Enable request/response logging (default: True)
    - `performance_monitoring_enabled`: Enable performance tracking (default: True)
    - `allowed_origins`: CORS allowed origins list
    - `log_level`: Logging verbosity for middleware components

Examples:
    >>> # Basic middleware setup
    >>> from fastapi import FastAPI
    >>> from app.core.middleware import setup_middleware
    >>> from app.core.config import settings
    >>> 
    >>> app = FastAPI()
    >>> setup_middleware(app, settings)
    >>> # Production-ready middleware stack is now active

    >>> # Custom configuration example
    >>> custom_settings = Settings(
    ...     security_headers_enabled=True,
    ...     performance_monitoring_enabled=True,
    ...     request_logging_enabled=False,  # Disable for high-traffic endpoints
    ...     allowed_origins=["https://mydomain.com"]
    ... )
    >>> setup_middleware(app, custom_settings)

    >>> # Development configuration
    >>> dev_settings = Settings(
    ...     security_headers_enabled=False,  # Relaxed for development
    ...     performance_monitoring_enabled=True,
    ...     request_logging_enabled=True,
    ...     log_level="DEBUG"
    ... )
    >>> setup_middleware(app, dev_settings)

Production Features:
    - **Security Headers**: HSTS, CSP, X-Frame-Options, anti-XSS protection
    - **Request Correlation**: Unique request IDs for distributed tracing
    - **Performance Metrics**: Response times, resource usage, slow request detection
    - **Error Handling**: Consistent error responses without information disclosure
    - **CORS Configuration**: Production-ready cross-origin resource sharing
    - **Health Check Integration**: Middleware health validation endpoints

Security Considerations:
    - Security middleware validates requests before processing
    - Error responses are sanitized to prevent information disclosure
    - CORS policies are enforced for cross-origin request protection
    - Request logging filters sensitive data automatically
    - Security headers provide defense-in-depth protection

Performance Characteristics:
    - Total middleware overhead: < 2ms per request for basic stack
    - Memory overhead: < 500KB additional memory usage
    - Async-first design for optimal concurrency support
    - Minimal CPU overhead with efficient request processing
    - Graceful degradation when optional components are unavailable

Monitoring Integration:
    - Request correlation IDs for distributed tracing
    - Performance metrics collection for monitoring systems
    - Structured logging with JSON format for log aggregation
    - Health check endpoints for operational monitoring
    - Error tracking with proper exception classification

## setup_enhanced_middleware()

```python
def setup_enhanced_middleware(app: FastAPI, settings: Settings) -> None:
```

Configure enhanced middleware stack with all available components.

Enhanced Middleware Execution Order (LIFO - Last-In, First-Out):
The middleware added last executes first. Here's the actual execution order:

1. **CORS Middleware**: Handle preflight requests (added last, runs first)
2. **Performance Monitoring**: Track performance metrics
3. **Request Logging Middleware**: Log requests with correlation IDs
4. **Compression Middleware**: Handle request/response compression
5. **Version Compatibility Middleware**: Transform between versions (if enabled)
6. **API Versioning Middleware**: Handle version detection and routing
7. **Security Middleware**: Security headers and validation
8. **Request Size Limiting**: Prevent large request DoS attacks
9. **Rate Limiting Middleware**: Protect against abuse (added first, runs last)
10. **Application Logic**: Your route handlers
11. **Global Exception Handler**: Catch any unhandled exceptions (not true middleware)

Note: Due to FastAPI's LIFO middleware execution, the order above reflects
the actual request processing order, not the setup order in this function.

Args:
    app (FastAPI): The FastAPI application instance
    settings (Settings): Application settings with middleware configuration

## get_request_id()

```python
def get_request_id(request: Request) -> str:
```

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

## get_request_duration()

```python
def get_request_duration(_request: Request) -> Optional[float]:
```

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

## add_response_headers()

```python
def add_response_headers(response: Response, headers: Dict[str, str]) -> None:
```

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

## is_health_check_request()

```python
def is_health_check_request(request: Request) -> bool:
```

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

## configure_middleware_logging()

```python
def configure_middleware_logging(settings: Settings) -> None:
```

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

## get_middleware_stats()

```python
def get_middleware_stats(app: FastAPI) -> Dict[str, Any]:
```

Get statistics and information about configured middleware.

Returns:
    Dict containing middleware configuration and runtime stats

## validate_middleware_configuration()

```python
def validate_middleware_configuration(settings: Settings) -> List[str]:
```

Validate middleware configuration and return any warnings or errors.

Args:
    settings: Application settings to validate

Returns:
    List of validation warnings/errors

## create_middleware_health_check()

```python
def create_middleware_health_check() -> Callable:
```

Create a health check function that validates middleware status.

Returns:
    Async function that can be used as a health check endpoint

## optimize_middleware_stack()

```python
def optimize_middleware_stack(app: FastAPI, settings: Settings) -> None:
```

Optimize middleware stack for production performance.

Args:
    app: FastAPI application instance
    settings: Application settings

## setup_middleware_monitoring()

```python
def setup_middleware_monitoring(app: FastAPI, settings: Settings) -> None:
```

Set up monitoring and analytics for middleware performance.

Args:
    app: FastAPI application instance
    settings: Application settings

## setup_production_middleware()

```python
def setup_production_middleware(app: FastAPI, settings: Settings) -> None:
```

Set up middleware stack optimized for production use.

This function configures the middleware stack with production-optimized
settings and includes all security, performance, and monitoring features.

Args:
    app: FastAPI application instance
    settings: Application settings

## migrate_from_main_py_middleware()

```python
def migrate_from_main_py_middleware(app: FastAPI, settings: Settings) -> None:
```

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
