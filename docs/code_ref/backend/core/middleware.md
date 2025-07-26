# Core Middleware Module

This module provides centralized middleware management for the FastAPI backend application.
All application middleware is consolidated here including CORS configuration, error handling,
logging, security, and monitoring middleware to provide a clean separation of concerns.

The middleware stack is designed for production use with comprehensive error handling,
security features, monitoring capabilities, and development conveniences. Each middleware
component can be individually configured through the application settings.

## Middleware Components

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
- Request rate limiting and abuse prevention
- Input validation and sanitization
- XSS and injection attack prevention

### Performance Monitoring Middleware

- Request timing and performance metrics
- Memory usage tracking
- Slow request detection and alerting
- Integration with monitoring systems

## Architecture

The middleware stack follows FastAPI's middleware execution order, with
security and logging middleware running first, followed by application-specific
middleware, and finally CORS middleware for response processing.

### Execution Order (Request Processing)

1. Security Middleware (headers, rate limiting)
2. Request Logging Middleware (start timing, generate request ID)
3. Performance Monitoring Middleware (memory/CPU tracking)
4. Application Logic (routers, endpoints)
5. CORS Middleware (response headers)
6. Performance Monitoring Middleware (finish timing)
7. Request Logging Middleware (log response)
8. Global Exception Handler (if exceptions occur)

## Configuration

All middleware can be configured through the Settings class in app.core.config:

- CORS settings: allowed_origins, cors_credentials, cors_methods
- Logging settings: log_level, request_logging_enabled
- Security settings: security_headers_enabled, rate_limiting_enabled
- Monitoring settings: performance_monitoring_enabled, slow_request_threshold

## Usage

Import and apply middleware to FastAPI application:

```python
from fastapi import FastAPI
from app.core.middleware import setup_middleware
from app.core.config import settings

app = FastAPI()
setup_middleware(app, settings)
```

## Dependencies

- fastapi: Core web framework and middleware support
- fastapi.middleware.cors: CORS middleware implementation
- app.core.config: Application settings and configuration
- app.core.exceptions: Custom exception hierarchy
- shared.models: Pydantic models for error responses
- logging: Python standard library logging

## Thread Safety

All middleware components are designed to be thread-safe and support
concurrent request processing in production environments with multiple
workers and async request handling.

## Example

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

## Note

This module replaces the inline middleware configuration previously
found in main.py and provides a centralized, testable, and maintainable
approach to middleware management. All middleware can be individually
enabled/disabled through configuration settings.
