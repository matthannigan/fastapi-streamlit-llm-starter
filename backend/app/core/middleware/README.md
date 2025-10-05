---
sidebar_label: middleware
---

# Core Middleware Infrastructure

This directory provides a comprehensive middleware infrastructure for FastAPI applications, implementing production-ready components that handle cross-cutting concerns including security, monitoring, performance optimization, and operational capabilities. The middleware architecture follows best practices for API security, observability, and resilience patterns.

## Directory Structure

```
middleware/
├── __init__.py                     # Module exports and setup functions
├── security.py                     # HTTP security headers and request validation
├── cors.py                         # Cross-origin resource sharing configuration
├── rate_limiting.py               # Distributed rate limiting with Redis fallback
├── request_size.py                # Request size limiting and DoS protection
├── compression.py                 # Intelligent compression with streaming support
├── api_versioning.py              # Multi-strategy API version management
├── request_logging.py             # Structured logging with correlation tracking
├── performance_monitoring.py     # High-precision performance tracking
├── global_exception_handler.py    # Centralized error handling and response formatting
└── README.md                      # This documentation file
```

## Core Architecture

### Layered Middleware Architecture

The middleware infrastructure follows a **layered security architecture** with clear separation of concerns:

1. **Security Layer**: HTTP security headers, CORS policies, rate limiting, and request validation
2. **Monitoring & Observability Layer**: Request logging, performance monitoring, and health tracking
3. **Performance Optimization Layer**: Compression, API versioning, and request optimization
4. **Exception Handling Layer**: Centralized error handling with secure response formatting

### Execution Order (LIFO - Last-In, First-Out)

FastAPI middleware executes in reverse order of registration. The middleware stack is optimized for security and performance:

```
Request Processing Flow:
1. CORS Middleware (preflight handling, added last, runs first)
2. Performance Monitoring (establish timing context)
3. Request Logging (correlation ID generation)
4. Compression Middleware (request decompression)
5. API Versioning (version detection and routing)
6. Security Middleware (security validation and headers)
7. Request Size Limiting (DoS protection)
8. Rate Limiting (abuse prevention, added first, runs last)
9. Application Logic (route handlers and business logic)
10. Global Exception Handler (error handling, not true middleware)

Response Processing Flow (reverse order):
Rate Limiting → Request Size → Security → Versioning → Compression → Logging → Monitoring → CORS
```

## Core Components Comparison

### Security Middleware (`security.py`)

**Purpose:** Production-grade security hardening with comprehensive HTTP security headers and request validation.

**Key Features:**
- ✅ **Security Headers**: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- ✅ **Request Validation**: Content-Length validation, header count limits, and request size enforcement
- ✅ **DoS Protection**: Configurable maximum request sizes and header count restrictions with 413 responses
- ✅ **XSS Protection**: Content-Type validation and XSS prevention headers
- ✅ **Endpoint-Aware CSP**: Strict CSP for API endpoints, relaxed policies for documentation endpoints

**Configuration:**
```python
# Security middleware configuration
security_headers_enabled = True          # Master toggle for security headers
max_request_size = 10 * 1024 * 1024      # 10MB maximum request size
max_headers_count = 100                  # Maximum headers per request
csp_policy = None                        # Optional custom CSP override
```

**Response Headers Applied:**
```python
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

**Best For:**
- Production API deployments requiring security hardening
- Applications needing comprehensive HTTP security header implementation
- Systems requiring DoS protection through request validation
- Multi-tier applications with different security policies for APIs vs documentation

### Rate Limiting Middleware (`rate_limiting.py`)

**Purpose:** Enterprise-grade distributed rate limiting with intelligent fallback and comprehensive endpoint classification.

**Key Features:**
- ✅ **Per-Endpoint Classification**: Automatic categorization (health, auth, critical, standard, monitoring)
- ✅ **Multi-Strategy Rate Limiting**: Sliding window, fixed window, and token-bucket style behavior
- ✅ **Redis Integration**: Distributed rate limiting across multiple application instances
- ✅ **Client Identification**: Priority hierarchy using API keys, user IDs, and IP addresses
- ✅ **Graceful Fallback**: Local in-memory rate limiting with automatic cleanup when Redis unavailable

**Configuration:**
```python
# Rate limiting configuration
rate_limiting_enabled = True         # Master toggle for rate limiting
redis_url = "redis://localhost:6379" # Redis connection for distributed limiting
rate_limits = {
    'health': {'requests': 1000, 'window': 60},     # Lenient for health checks
    'auth': {'requests': 5, 'window': 300},        # Strict for authentication
    'standard': {'requests': 100, 'window': 60},    # Standard for general APIs
    'api_heavy': {'requests': 10, 'window': 60}    # Conservative for heavy operations
}
```

**Client Identification Priority:**
1. **API Key**: From `X-API-Key` or `Authorization` headers (highest priority)
2. **User ID**: From `request.state.user_id` (when available)
3. **IP Address**: From `X-Forwarded-For`, `X-Real-IP`, or connection IP (fallback)

**Response Headers:**
- `X-RateLimit-Limit`: Maximum requests allowed in current window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Window`: Time window duration in seconds
- `X-RateLimit-Rule`: Name of rate limit rule applied
- `Retry-After`: Seconds to wait before retry (on 429 responses)

### Compression Middleware (`compression.py`)

**Purpose:** Intelligent multi-algorithm compression with content-aware decisions and streaming support.

**Key Features:**
- ✅ **Multi-Algorithm Support**: Brotli (br), gzip, and deflate with automatic client preference selection
- ✅ **Content-Aware Decisions**: Intelligent compression based on content-type with size thresholds
- ✅ **Streaming Architecture**: ASGI-level streaming compression for large responses
- ✅ **Request Decompression**: Automatic handling of compressed request bodies
- ✅ **Performance Analytics**: Compression ratio tracking and optimization metrics

**Configuration:**
```python
# Compression configuration
compression_enabled = True               # Master toggle for compression
compression_min_size = 1024              # 1KB minimum size for compression
compression_level = 6                    # 1-9 quality/CPU tradeoff
compression_algorithms = ['br', 'gzip', 'deflate']  # Preferred algorithm order
streaming_compression_enabled = True     # Enable ASGI streaming compression
```

**Algorithm Selection Priority:**
1. **Brotli (br)**: Best compression ratio, modern browser support
2. **gzip**: Good compatibility, moderate compression
3. **deflate**: Basic compression, universal support

**Content-Type Handling:**
- **Compressed**: `text/*`, `application/json`, `application/xml`, `application/javascript`
- **Not Compressed**: `image/*`, `video/*`, `application/zip`, already compressed content

**Response Headers Added:**
- `Content-Encoding`: Compression algorithm used (br, gzip, deflate)
- `X-Original-Size`: Original uncompressed payload size
- `X-Compression-Ratio`: Compression efficiency as decimal (0.0-1.0)

### API Versioning Middleware (`api_versioning.py`)

**Purpose:** Comprehensive API version management with multi-strategy detection and internal API bypass.

**Key Features:**
- ✅ **Multi-Strategy Detection**: Path prefix, headers, query parameters, and Accept media types
- ✅ **Internal API Bypass**: Safe-by-default exemption for `/internal/*` routes
- ✅ **Backward Compatibility**: Intelligent version matching and deprecation management
- ✅ **Response Headers**: Comprehensive version information headers
- ✅ **Configuration Management**: Environment-based version configuration with validation

**Detection Strategy Priority:**
1. **Path-based**: `/v1/`, `/v2/`, `/v1.5/` URL patterns
2. **Header-based**: `X-API-Version`, `API-Version` headers
3. **Query parameter**: `?version=1.0` or `?api_version=1.0`
4. **Accept header**: `application/vnd.api+json;version=1.0`
5. **Default version**: Fallback when no version detected

**Internal API Bypass:**
Requests to `/internal/*` automatically bypass versioning to prevent unintended rewrites like `/v1/internal/resilience/health`.

**Response Headers:**
- `X-API-Version`: The API version used for processing
- `X-API-Version-Detection`: Strategy used for version detection
- `X-API-Supported-Versions`: Comma-separated list of supported versions
- `X-API-Current-Version`: The latest/current API version
- `Deprecation`: Set to 'true' for deprecated versions
- `Sunset`: Sunset date for deprecated versions

### Request Logging Middleware (`request_logging.py`)

**Purpose:** Structured logging system with comprehensive correlation tracking and security-conscious filtering.

**Key Features:**
- ✅ **Correlation IDs**: Unique 8-character request identifiers using contextvars for thread safety
- ✅ **Performance Metrics**: Millisecond-precision timing, response size tracking, and status code analytics
- ✅ **Sensitive Data Filtering**: Automatic filtering of authorization headers, API keys, and sensitive parameters
- ✅ **Health Check Optimization**: Reduced logging verbosity for health endpoints and monitoring probes
- ✅ **Structured Logging**: JSON-formatted logs with request metadata for monitoring system integration

**Correlation ID System:**
- Generated once per request using UUID8
- Stored in both `request.state.request_id` and contextvars
- Available throughout the request lifecycle for distributed tracing
- Propagated to downstream services via headers

**Sensitive Data Filtering:**
Automatically filters these headers from logs:
- `authorization`, `x-api-key`, `x-auth-token`
- `cookie`, `set-cookie`
- Passwords and tokens in query parameters

**Log Format Examples:**
```json
// Request started
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Request started: GET /api/health [req_id: abc12345]",
  "request_id": "abc12345",
  "method": "GET",
  "path": "/api/health",
  "user_agent": "curl/7.68.0"
}

// Request completed
{
  "timestamp": "2025-01-15T10:30:45.156Z",
  "level": "INFO",
  "message": "Request completed: GET /api/health 200 156B 45.2ms [req_id: abc12345]",
  "request_id": "abc12345",
  "status_code": 200,
  "response_size": 156,
  "duration_ms": 45.2
}
```

### Performance Monitoring Middleware (`performance_monitoring.py`)

**Purpose:** High-precision performance tracking with configurable alerting and resource monitoring.

**Key Features:**
- ✅ **Resource Monitoring**: RSS memory delta tracking, request timing with perf_counter() precision
- ✅ **Slow Request Detection**: Configurable thresholds with structured warning logs
- ✅ **Response Headers**: Performance headers for client-side monitoring
- ✅ **Graceful Degradation**: Continues operating when memory monitoring tools unavailable
- ✅ **Production Optimized**: <1ms overhead with configurable monitoring features

**Configuration:**
```python
# Performance monitoring configuration
performance_monitoring_enabled = True    # Master toggle for monitoring
slow_request_threshold = 1000             # 1 second threshold for slow requests
memory_monitoring_enabled = True         # Track memory usage changes
metrics_export_enabled = False            # Enable external monitoring integration
```

**Response Headers Added:**
- `X-Response-Time`: Request duration in milliseconds (e.g., "125.50ms")
- `X-Memory-Delta`: Memory usage change in bytes (e.g., "1048576B")

**Slow Request Detection:**
Requests exceeding `slow_request_threshold` trigger warning logs:
```
WARN: Slow request detected: POST /api/process 2150.5ms [req_id: abc123]
```

**Memory Monitoring:**
Tracks RSS (Resident Set Size) memory changes before and after request processing:
- Positive values indicate increased memory usage
- Negative values indicate memory cleanup
- Automatic graceful degradation when memory tools unavailable

### Request Size Limiting Middleware (`request_size.py`)

**Purpose:** DoS protection through streaming request size validation with per-content-type limits.

**Key Features:**
- ✅ **Per-Content-Type Limits**: Different size ceilings for JSON, multipart, and other content types
- ✅ **Streaming Validation**: Validates as body chunks arrive (no buffering required)
- ✅ **Hierarchical Configuration**: Endpoint-specific, content-type, and global default limits
- ✅ **Clear Error Responses**: Informative 413 responses with size information headers

**Configuration:**
```python
# Request size limiting configuration
request_size_limiting_enabled = True     # Master toggle for size limiting
request_size_limits = {
    'default': 10 * 1024 * 1024,         # 10MB default limit
    'application/json': 5 * 1024 * 1024,  # 5MB for JSON
    'multipart/form-data': 50 * 1024 * 1024  # 50MB for file uploads
}
```

**Response Headers Added:**
- `X-Max-Request-Size`: Maximum allowed size in bytes
- `X-Request-Size-Limit`: Human-readable size limit (e.g., "10.0MB")

**Error Response Format (413):**
```json
{
  "success": false,
  "error": "Request entity too large",
  "error_code": "REQUEST_TOO_LARGE",
  "details": {
    "actual_size": 15728640,
    "max_size": 10485760,
    "max_size_human": "10.0MB"
  }
}
```

### Global Exception Handler (`global_exception_handler.py`)

**Purpose:** Centralized error handling with structured responses and secure error sanitization.

**Key Features:**
- ✅ **Structured Error Responses**: Consistent JSON error format across all exceptions
- ✅ **Security Filtering**: Sanitized messages prevent information disclosure
- ✅ **HTTP Status Mapping**: Intelligent status code mapping by exception category
- ✅ **Request Correlation**: Preserves request IDs in error responses for debugging

**Important Architecture Note:**
This module uses FastAPI's `@app.exception_handler()` decorator system, NOT Starlette middleware. It catches exceptions after middleware processing but serves the same architectural purpose.

**HTTP Status Code Mapping:**
- `ApplicationError` → 400 Bad Request
- `InfrastructureError` → 502 Bad Gateway
- `TransientAIError` → 503 Service Unavailable
- `PermanentAIError` → 502 Bad Gateway
- `RequestValidationError` → 422 Unprocessable Entity
- All other exceptions → 500 Internal Server Error

**Error Response Format:**
```json
{
  "success": false,
  "error": "Internal server error",
  "error_code": "INTERNAL_ERROR",
  "timestamp": "2025-01-15T10:30:45.789012",
  "request_id": "abc12345"  // Included when available
}
```

### CORS Middleware (`cors.py`)

**Purpose:** Cross-origin resource sharing with configurable policies and explicit origin allowlisting.

**Key Features:**
- ✅ **Explicit Origin Allowlisting**: No wildcard origins in production for security
- ✅ **Credentials Support**: Supports authentication cookies and headers in CORS requests
- ✅ **Preflight Handling**: Automatic OPTIONS request handling for CORS preflight
- ✅ **Production Security**: Secure defaults with configurable origin policies

**Configuration:**
```python
# CORS configuration
allowed_origins = [
    "https://app.example.com",
    "https://admin.example.com"
]  # Explicit origin list (no wildcards in production)
```

**CORS Headers Applied:**
- `Access-Control-Allow-Origin`: Configured allowed origins
- `Access-Control-Allow-Methods`: All HTTP methods ("*")
- `Access-Control-Allow-Headers`: All headers ("*")
- `Access-Control-Allow-Credentials`: True (supports cookies/auth)

## Quick Start Guide

### Environment Setup

Set up middleware configuration using environment variables:

```bash
# Security configuration
export SECURITY_HEADERS_ENABLED=true
export MAX_REQUEST_SIZE=10485760      # 10MB
export MAX_HEADERS_COUNT=100

# Rate limiting configuration
export RATE_LIMITING_ENABLED=true
export REDIS_URL=redis://localhost:6379

# Compression configuration
export COMPRESSION_ENABLED=true
export COMPRESSION_LEVEL=6
export COMPRESSION_ALGORITHDS='["br", "gzip", "deflate"]'

# API versioning configuration
export API_VERSIONING_ENABLED=true
export DEFAULT_API_VERSION=1.0
export CURRENT_API_VERSION=1.0

# Performance monitoring configuration
export PERFORMANCE_MONITORING_ENABLED=true
export SLOW_REQUEST_THRESHOLD=1000    # 1 second
export MEMORY_MONITORING_ENABLED=true
```

### Basic Middleware Setup

```python
from fastapi import FastAPI
from app.core.middleware import setup_middleware
from app.core.config import settings

app = FastAPI()

# Basic production-ready middleware stack
setup_middleware(app, settings)

# Provides:
# - Security headers and validation
# - Request logging with correlation IDs
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
# - Rate limiting (Redis-backed with local fallback)
# - Request compression (multi-algorithm)
# - API versioning (multi-strategy detection)
# - Request size limiting (DoS protection)
# - Advanced monitoring
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

## Configuration Management

### Environment-Specific Configuration

The middleware system supports **environment-based configuration** with appropriate defaults:

#### Development Configuration
```bash
# Development middleware settings
export SECURITY_HEADERS_ENABLED=true
export RATE_LIMITING_ENABLED=true
export COMPRESSION_ENABLED=true
export API_VERSIONING_ENABLED=true
export PERFORMANCE_MONITORING_ENABLED=true
export REQUEST_LOGGING_ENABLED=true
export MEMORY_MONITORING_ENABLED=true
export LOG_LEVEL=DEBUG
```

#### Production Configuration
```bash
# Production middleware settings
export SECURITY_HEADERS_ENABLED=true
export RATE_LIMITING_ENABLED=true
export COMPRESSION_ENABLED=true
export API_VERSIONING_ENABLED=true
export PERFORMANCE_MONITORING_ENABLED=true
export REQUEST_LOGGING_ENABLED=true
export MEMORY_MONITORING_ENABLED=false  # Reduce overhead
export LOG_LEVEL=INFO
```

### Configuration Validation

```python
from app.core.middleware import validate_middleware_configuration

# Validate configuration before setup
issues = validate_middleware_configuration(settings)
if issues:
    for issue in issues:
        logger.warning(f"Middleware config issue: {issue}")
else:
    logger.info("Middleware configuration validated successfully")
```

## Integration Patterns

### Custom Middleware Development

#### Adding Custom Middleware
```python
# custom_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from app.core.config import Settings

class CustomBusinessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.enabled = getattr(settings, 'custom_middleware_enabled', True)

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # Custom business logic here
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Add custom headers
        response.headers["X-Custom-Process-Time"] = str(process_time)
        return response
```

#### Integration with Middleware Stack
```python
# In app/core/middleware/__init__.py
from .custom_middleware import CustomBusinessMiddleware

def setup_enhanced_middleware(app: FastAPI, settings: Settings) -> None:
    # ... existing middleware setup ...

    # Add custom middleware in appropriate position
    custom_enabled = getattr(settings, 'custom_middleware_enabled', False)
    if custom_enabled:
        app.add_middleware(CustomBusinessMiddleware, settings=settings)
        logger.info("Custom business middleware enabled")
```

### Request Correlation in Application Code

```python
from app.core.middleware import get_request_id, get_request_duration
from fastapi import Request

@app.get("/api/endpoint")
async def my_endpoint(request: Request):
    request_id = get_request_id(request)
    duration = get_request_duration(request)

    logger.info(f"Processing request {request_id}, duration: {duration}ms")
    return {
        "request_id": request_id,
        "processing_time_ms": duration
    }
```

### Health Check Integration

```python
from app.core.middleware import create_middleware_health_check

# Built-in health check for middleware stack
health_check = create_middleware_health_check()

@app.get("/health/middleware")
async def middleware_health(request: Request):
    """Middleware health check endpoint."""
    return await health_check(request)

@app.get("/internal/middleware/stats")
async def middleware_stats():
    """Middleware statistics endpoint."""
    from app.core.middleware import get_middleware_stats
    return get_middleware_stats(app)
```

## Performance Characteristics

### Middleware Overhead Analysis

| Component | Overhead per Request | Memory Impact | Key Optimizations |
|-----------|-------------------|--------------|-------------------|
| **Security Middleware** | < 0.5ms | < 100KB | Header validation optimization |
| **Request Logging** | < 1ms | < 200KB | Efficient correlation ID generation |
| **Performance Monitoring** | < 0.2ms | < 50KB | perf_counter() precision timing |
| **Rate Limiting** | < 2ms | Variable | Redis pipelining, local fallback |
| **Compression** | Variable | Streaming | Content-type awareness |
| **API Versioning** | < 0.3ms | < 100KB | Efficient version detection |
| **Total Enhanced Stack** | < 5ms | < 1MB | Optimized execution order |

### Scalability Characteristics

#### Concurrent Request Handling
- **Thread Safety**: All middleware components are thread-safe using contextvars
- **Async Support**: Fully async implementation for optimal concurrency
- **Memory Management**: Streaming design minimizes memory usage
- **Resource Cleanup**: Automatic cleanup of temporary resources

#### Distributed Operation Support
- **Redis Integration**: Rate limiting operates across multiple instances
- **Request Correlation**: Correlation IDs work across service boundaries
- **Configuration Consistency**: Environment-based configuration ensures consistency
- **Health Monitoring**: Distributed health check support

### Performance Optimization Tips

1. **Choose Appropriate Features**: Enable only needed middleware components
2. **Configure Thresholds Wisely**: Set appropriate size limits and monitoring thresholds
3. **Use Redis for Rate Limiting**: Enable Redis for distributed rate limiting in production
4. **Optimize Compression**: Use appropriate compression levels and size thresholds
5. **Monitor Performance**: Regular monitoring of middleware performance impact

## Security Considerations

### Defense in Depth Strategy

The middleware stack implements **defense in depth** with multiple security layers:

#### Input Validation Layer
- Request size limits prevent DoS attacks
- Header count validation prevents header-based attacks
- Content-Length validation prevents malformed requests

#### Security Headers Layer
- HSTS prevents downgrade attacks
- CSP prevents XSS and code injection
- X-Frame-Options prevents clickjacking
- X-Content-Type-Options prevents MIME sniffing

#### Rate Limiting Layer
- Per-endpoint classification provides appropriate protection levels
- Distributed rate limiting prevents coordinated attacks
- Graceful fallback ensures continued protection during Redis outages

#### Error Handling Layer
- Sanitized error responses prevent information disclosure
- Consistent error format prevents attacker reconnaissance
- Request correlation enables security incident analysis

### Security Configuration Best Practices

```bash
# Production security configuration
export SECURITY_HEADERS_ENABLED=true
export MAX_REQUEST_SIZE=10485760      # 10MB limit
export MAX_HEADERS_COUNT=100          # Prevent header flooding
export RATE_LIMITING_ENABLED=true
export COMPRESSION_ENABLED=true
export LOG_SENSITIVE_DATA=false      # Don't log sensitive data
```

### Threat Mitigation Coverage

| Threat | Mitigation | Middleware Component |
|--------|------------|-------------------|
| **DoS Attacks** | Request size limits, rate limiting | Security, Rate Limiting |
| **XSS Attacks** | CSP headers, content-type validation | Security |
| **CSRF Attacks** | SameSite cookies, origin validation | Security, CORS |
| **Information Disclosure** | Sanitized error responses | Global Exception Handler |
| **Brute Force** | Rate limiting per endpoint | Rate Limiting |
| **Injection Attacks** | Input validation, security headers | Security |

## Monitoring & Observability

### Request Correlation System

The middleware system provides comprehensive request correlation:

```python
# Correlation ID is available throughout the request lifecycle
request_id = get_request_id(request)  # From middleware context

# Available in logs for distributed tracing
logger.info(f"Processing {request_id}")

# Included in error responses for debugging
# Error responses automatically include request_id when available
```

### Performance Monitoring Integration

```python
# Performance headers are automatically added to responses
# X-Response-Time: 125.50ms
# X-Memory-Delta: 1048576B

# Slow requests trigger warning logs
# WARN: Slow request detected: POST /api/process 2150.5ms [req_id: abc123]

# Performance metrics available for monitoring systems
stats = get_middleware_stats(app)
```

### Health Check Endpoints

```bash
# Overall middleware health
curl -s http://localhost:8000/health/middleware | jq '.'

# Detailed middleware statistics
curl -s http://localhost:8000/internal/middleware/stats | jq '.'

# Component-specific health
curl -s http://localhost:8000/internal/middleware/health | jq '.middleware'
```

### Monitoring Integration Points

The middleware system provides multiple integration points for monitoring:

#### Prometheus Metrics (Future Enhancement)
```python
# Metrics that could be exported:
# - middleware_request_duration_seconds
# - middleware_request_size_bytes
# - middleware_rate_limit_hits_total
# - middleware_compression_ratio
```

#### Structured Logging Integration
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "INFO",
  "message": "Request completed: GET /api/health 200 156B 45.2ms [req_id: abc12345]",
  "request_id": "abc12345",
  "method": "GET",
  "path": "/api/health",
  "status_code": 200,
  "response_size": 156,
  "duration_ms": 45.2,
  "middleware_stack": ["cors", "performance_monitoring", "request_logging", "security", "global_exception_handler"]
}
```

## Testing & Validation

### Middleware Testing Patterns

#### Unit Testing Individual Middleware
```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import create_settings

def test_security_middleware_headers():
    """Test security middleware adds expected headers."""
    settings = create_settings()
    settings.security_headers_enabled = True

    app = create_app(settings_obj=settings)
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert "strict-transport-security" in response.headers
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers
```

#### Integration Testing Middleware Stack
```python
def test_middleware_execution_order():
    """Test middleware components execute in correct order."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    # Verify correlation ID from request logging
    assert "x-request-id" in response.headers

    # Verify performance timing from performance monitoring
    assert "x-response-time" in response.headers

    # Verify security headers from security middleware
    assert "x-content-type-options" in response.headers
```

#### Configuration Validation Testing
```python
def test_middleware_configuration_validation():
    """Test configuration validation identifies issues."""
    from app.core.middleware import validate_middleware_configuration
    from app.core.config import Settings

    settings = Settings(
        compression_enabled=True,
        compression_level=15  # Invalid level > 9
    )

    issues = validate_middleware_configuration(settings)
    assert any("compression level" in issue.lower() for issue in issues)
```

### Load Testing Middleware

```python
# Test middleware performance under load
def test_middleware_load_performance():
    """Test middleware stack handles concurrent requests efficiently."""
    import asyncio
    import aiohttp

    async def make_request(session, url):
        async with session.get(url) as response:
            return await response.text()

    async def run_load_test():
        connector = aiohttp.TCPConnector(limit=100)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [make_request(session, "http://localhost:8000/health")
                    for _ in range(1000)]
            results = await asyncio.gather(*tasks)
            return len(results)

    # Verify all requests complete successfully
    success_count = asyncio.run(run_load_test())
    assert success_count == 1000
```

## Troubleshooting & Common Issues

### Debugging Middleware Configuration

#### Configuration Validation
```bash
# Check middleware configuration
curl -s http://localhost:8000/internal/middleware/validate-config | jq '.'

# Get configuration warnings
curl -s http://localhost:8000/internal/middleware/config-warnings | jq '.'
```

#### Middleware Health Status
```bash
# Overall middleware health
curl -s http://localhost:8000/internal/middleware/health | jq '.status'

# Component-specific health
curl -s http://localhost:8000/internal/middleware/health | jq '.middleware'
```

### Common Issues and Solutions

#### Issue: CORS Headers Not Applied
**Symptoms:** CORS preflight requests fail, cross-origin requests blocked
**Diagnosis:**
```bash
curl -X OPTIONS -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST" \
  -v http://localhost:8000/api/endpoint
```
**Solutions:**
- Verify `allowed_origins` configuration includes the requesting origin
- Check that CORS middleware is registered last in the stack
- Ensure request doesn't bypass middleware stack

#### Issue: Rate Limiting Not Working
**Symptoms:** Requests not being rate limited, excessive requests allowed
**Diagnosis:**
```bash
# Check rate limiting status
curl -s http://localhost:8000/internal/middleware/stats | jq '.enabled_features'

# Test rate limit headers
curl -I -H "X-API-Key: test-key" http://localhost:8000/api/endpoint
```
**Solutions:**
- Verify Redis connection if using distributed rate limiting
- Check that `rate_limiting_enabled` is true
- Verify client identification hierarchy (API key > user ID > IP)

#### Issue: Compression Not Applied
**Symptoms:** Responses not compressed despite Accept-Encoding header
**Diagnosis:**
```bash
curl -H "Accept-Encoding: gzip, br" -I http://localhost:8000/api/endpoint
```
**Solutions:**
- Verify response size exceeds `compression_min_size`
- Check content-type is in compressible list
- Verify `compression_enabled` is true
- Check that response isn't already compressed

#### Issue: High Memory Usage
**Symptoms:** Memory usage increasing over time
**Diagnosis:**
```bash
# Monitor memory usage
curl -s http://localhost:8000/internal/monitoring/memory-analysis

# Check middleware memory impact
curl -s http://localhost:8000/internal/middleware/memory-breakdown
```
**Solutions:**
- Disable memory monitoring in production (`memory_monitoring_enabled=false`)
- Reduce retention periods for monitoring data
- Optimize compression settings for memory efficiency

#### Issue: Performance Degradation
**Symptoms:** Increased response times after middleware deployment
**Diagnosis:**
```bash
# Check middleware performance impact
curl -s http://localhost:8000/internal/middleware/performance-impact

# Monitor response times
curl -s http://localhost:8000/internal/monitoring/response-time-breakdown
```
**Solutions:**
- Profile individual middleware performance
- Disable non-essential middleware components
- Optimize configuration thresholds
- Consider ASGI-level middleware for performance-critical components

### Advanced Debugging

#### Middleware Debug Mode
```bash
# Enable detailed middleware logging
export MIDDLEWARE_DEBUG_MODE=true
export LOG_LEVEL=DEBUG

# Enable performance profiling
export MIDDLEWARE_PERFORMANCE_PROFILING=true

# Restart with debug configuration
docker-compose restart backend
```

#### Request Tracing
```bash
# Enable detailed request tracing
curl -H "X-Debug-Trace: true" -v http://localhost:8000/health

# Get detailed execution trace
curl -s http://localhost:8000/internal/middleware/request-trace?request_id=<request_id>
```

## Migration & Compatibility

### Legacy Support

The middleware system provides **backward compatibility** for existing applications:

#### Migration from Inline Middleware
```python
# Old approach (inline in main.py)
# app.add_middleware(CORSMiddleware, ...)
# @app.exception_handler(Exception)
# async def global_exception_handler(request, exc): ...

# New approach (middleware module)
from app.core.middleware import setup_middleware
setup_middleware(app, settings)
```

#### Configuration Migration
```python
# Legacy environment variables continue to work
export CORS_ORIGINS=["https://example.com"]
export RATE_LIMIT_ENABLED=true

# New enhanced configuration options available
export RATE_LIMITING_ENABLED=true      # New naming
export RATE_LIMITING_SKIP_HEALTH=true   # New feature
```

### Gradual Migration Strategy

#### Phase 1: Basic Migration
```python
# Replace basic middleware setup
from app.core.middleware import setup_middleware
setup_middleware(app, settings)
```

#### Phase 2: Enhanced Features
```python
# Enable enhanced middleware features
from app.core.middleware import setup_enhanced_middleware
setup_enhanced_middleware(app, settings)
```

#### Phase 3: Production Optimization
```python
# Full production setup
from app.core.middleware import setup_production_middleware
setup_production_middleware(app, settings)
```

## Best Practices

### Middleware Configuration Best Practices

1. **Environment-Specific Configuration**: Use different settings for development, staging, and production
2. **Feature Toggles**: Enable/disable individual middleware components based on needs
3. **Configuration Validation**: Always validate configuration before application startup
4. **Monitoring Integration**: Integrate middleware metrics with your monitoring system
5. **Security-First**: Always enable security middleware in production environments

### Performance Optimization Best Practices

1. **Selective Enablement**: Only enable middleware components that are needed
2. **Appropriate Thresholds**: Set size limits and monitoring thresholds appropriately
3. **Redis Integration**: Use Redis for distributed rate limiting in multi-instance deployments
4. **Compression Tuning**: Balance compression level vs CPU usage based on content
5. **Regular Monitoring**: Monitor middleware performance impact and optimize accordingly

### Security Best Practices

1. **Defense in Depth**: Enable multiple security layers for comprehensive protection
2. **Regular Updates**: Keep middleware components updated with security patches
3. **Configuration Review**: Regularly review and audit middleware security configurations
4. **Rate Limiting**: Use appropriate rate limits for different endpoint types
5. **Error Handling**: Ensure error responses don't leak sensitive information

### Operational Excellence Best Practices

1. **Health Monitoring**: Implement comprehensive health checks for all middleware components
2. **Structured Logging**: Use structured logging with correlation IDs for debugging
3. **Performance Baselines**: Establish and monitor performance baselines for middleware
4. **Incident Response**: Document procedures for common middleware issues
5. **Configuration Management**: Version control all middleware configurations

---

This middleware infrastructure provides a production-ready, comprehensive solution for handling cross-cutting concerns in FastAPI applications. It combines industry-standard patterns with intelligent configuration management to ensure robust, scalable, and secure middleware operations with comprehensive monitoring, security features, and operational excellence.