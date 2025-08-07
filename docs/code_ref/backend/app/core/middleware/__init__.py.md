---
sidebar_label: __init__
---

# Core Middleware Module - Enhanced

  file_path: `backend/app/core/middleware/__init__.py`

This module provides centralized middleware management for the FastAPI backend application.
All application middleware is consolidated here including CORS configuration, error handling,
logging, security, monitoring, rate limiting, compression, and API versioning middleware to
provide comprehensive production-ready capabilities with clean separation of concerns.

The middleware stack is designed for production use with comprehensive error handling,
security features, monitoring capabilities, and development conveniences. Each middleware
component can be individually configured through the application settings.

## Enhanced Middleware Components

### CORS Middleware

- Cross-Origin Resource Sharing configuration
- Configurable allowed origins, methods, and headers
- Support for credentials and preflight requests
- Production-ready security settings

### Global Exception Handler

- Centralized exception handling for unhandled errors
- Standardized error response format
- Security-conscious error message sanitization
- Comprehensive logging for debugging and monitoring

### Request Logging Middleware

- HTTP request/response logging with performance metrics
- Configurable log levels and detail granularity
- Request ID generation for tracing
- Sensitive data filtering for security

### Security Middleware

- Security headers injection (HSTS, CSP, etc.)
- Input validation and sanitization
- XSS and injection attack prevention
- Enhanced header controls

### Performance Monitoring Middleware

- Request timing and performance metrics
- Memory usage tracking
- Slow request detection and alerting
- Integration with monitoring systems

### Rate Limiting Middleware

- Redis-backed distributed rate limiting
- Per-endpoint and per-user rate limits
- Graceful degradation when Redis unavailable
- Custom rate limit headers and rules

### API Versioning Middleware

- Multiple version detection strategies (URL, headers, query params)
- Version compatibility routing
- Deprecation warnings and sunset dates
- Backward compatibility transformations

### Compression Middleware

- Request decompression (gzip, brotli, deflate)
- Intelligent response compression
- Content-type aware compression decisions
- Streaming compression support

### Request Size Limiting Middleware

- Content-type specific size limits
- Streaming validation for large requests
- Protection against DoS attacks
- Detailed error responses

## Architecture

The enhanced middleware stack follows FastAPI's middleware execution order, with
rate limiting and security middleware running first, followed by versioning,
compression, logging, and monitoring middleware, and finally CORS middleware
for response processing.

### Enhanced Execution Order (Request Processing)

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

## Configuration

All middleware can be configured through the Settings class in app.core.config:

- CORS settings: allowed_origins, cors_credentials, cors_methods
- Logging settings: log_level, request_logging_enabled
- Security settings: security_headers_enabled, max_request_size
- Monitoring settings: performance_monitoring_enabled, slow_request_threshold
- Rate limiting: rate_limiting_enabled, redis_url, custom_rate_limits
- Compression: compression_enabled, compression_level, compression_algorithms
- API versioning: api_versioning_enabled, default_api_version, current_api_version

## Usage

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

## Dependencies

- fastapi: Core web framework and middleware support
- fastapi.middleware.cors: CORS middleware implementation
- app.core.config: Application settings and configuration
- app.core.exceptions: Custom exception hierarchy
- shared.models: Pydantic models for error responses
- redis.asyncio: Redis client for distributed rate limiting
- brotli: Brotli compression support
- packaging: Version parsing and comparison
- logging: Python standard library logging

## Thread Safety

All middleware components are designed to be thread-safe and support
concurrent request processing in production environments with multiple
workers and async request handling.

## Example

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

## Note

This module provides both basic middleware setup (setup_middleware) for
backward compatibility and enhanced middleware setup (setup_enhanced_middleware)
with all advanced features. The enhanced version includes rate limiting,
compression, API versioning, and advanced monitoring capabilities for
production-ready deployments.
