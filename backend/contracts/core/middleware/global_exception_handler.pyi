"""
Global Exception Handler

## Overview

Centralized, security-conscious exception handling for the FastAPI application.
Provides standardized JSON error responses, consistent HTTP status mapping,
structured logging with request correlation for observability, and comprehensive
security header preservation to maintain security posture on all error responses.

## Responsibilities

- **Consistency**: Uniform error payloads via `app.schemas.common.ErrorResponse`
- **Security**: Sanitized messages; no internal details leaked to clients
- **Security Headers**: Preserves security headers on all error responses
- **Mapping**: Stable HTTP status codes by exception category
- **Observability**: Correlated logs using request IDs

## HTTP Status Mapping

- `ApplicationError` -> 400 Bad Request (validation, business logic errors)
- `InfrastructureError` -> 502 Bad Gateway (external service failures)
- `TransientAIError` -> 503 Service Unavailable (temporary AI issues)
- `PermanentAIError` -> 502 Bad Gateway (permanent AI issues)
- `RateLimitError` -> 429 Too Many Requests (rate limit exceeded)
- `RequestTooLargeError` -> 413 Payload Too Large (request size validation)
- `RequestValidationError` -> 422 Unprocessable Entity (Pydantic validation)
- All other exceptions -> 500 Internal Server Error

## Security Header Preservation

All exception handlers preserve security headers to maintain the application's
security posture even when errors occur after middleware processing:

- **X-Content-Type-Options**: `nosniff` (always added) - Prevents MIME type sniffing attacks
- **X-Frame-Options**: `DENY` (when enabled) - Prevents clickjacking attacks
- **Strict-Transport-Security**: `max-age=31536000; includeSubDomains` (when enabled) - Enforces HTTPS
- **Referrer-Policy**: `strict-origin-when-cross-origin` (when enabled) - Controls referrer information

Security headers are controlled by the `security_headers_enabled` setting and are
applied to all error responses including validation errors, API versioning errors,
and general application exceptions.

## Special Cases

Maintains compatibility for API versioning errors by returning a specific
payload and headers (`X-API-Supported-Versions`, `X-API-Current-Version`)
with security header preservation.

## Usage

```python
from app.core.middleware.global_exception_handler import setup_global_exception_handler
from app.core.config import settings

setup_global_exception_handler(app, settings)
```

## Important Architecture Note

This module implements centralized exception handling using FastAPI's
@app.exception_handler() decorator system, NOT Starlette middleware.

While located in the middleware directory and functioning like middleware,
this uses FastAPI's exception handler system rather than Starlette's
BaseHTTPMiddleware. This means:

- It catches exceptions AFTER middleware processing
- It doesn't appear in app.middleware_stack
- It's configured via @app.exception_handler() decorators
- It runs when middleware or application code raises unhandled exceptions

This is architecturally correct for error handling but differs from
traditional middleware implementation patterns. The security header preservation
ensures that security posture is maintained even when exceptions bypass
normal middleware processing.
"""

import logging
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import Settings
from app.core.exceptions import ApplicationError, ValidationError, AuthenticationError, AuthorizationError, ConfigurationError, BusinessLogicError, InfrastructureError, TransientAIError, PermanentAIError, RateLimitError, RequestTooLargeError, get_http_status_for_exception
from app.schemas.common import ErrorResponse


def setup_global_exception_handler(app: FastAPI, settings: Settings) -> None:
    """
    Configure global exception handling with security header preservation for unhandled application errors.
    
    Sets up comprehensive exception handlers that catch all unhandled exceptions
    across the FastAPI application and return consistent, secure error responses
    with security header preservation. The handler ensures clients receive
    predictable error responses while protecting internal implementation details
    and maintaining security posture even when exceptions occur after middleware processing.
    
    Args:
        app (FastAPI): The FastAPI application instance to configure with exception handlers
        settings (Settings): Application settings that influence error handling behavior,
                            including security header configuration
    
    Returns:
        None: This function configures the app in-place and returns nothing
    
    Raises:
        ConfigurationError: If the app instance is invalid or settings are malformed
    
    Behavior:
        - Registers RequestValidationError handler for Pydantic validation errors (HTTP 422)
        - Registers global Exception handler for all uncaught exceptions
        - Logs full exception details server-side with request context for debugging
        - Maps exception types to appropriate HTTP status codes including rate limiting and request size validation
        - Generates secure, user-friendly error messages that don't expose internals
        - Preserves request correlation IDs for debugging and monitoring
        - Returns standardized ErrorResponse format for all error types
        - Handles special cases like API versioning errors with custom responses
        - Ensures the application never returns unhandled exceptions to clients
        - Preserves security headers on all error responses to maintain security posture
        - Always adds X-Content-Type-Options: nosniff header for MIME type protection
        - Conditionally adds enhanced security headers when security_headers_enabled is True
    
    HTTP Status Code Mapping:
        - ApplicationError -> 400 Bad Request (validation, business logic errors)
        - InfrastructureError -> 502 Bad Gateway (external service failures)
        - TransientAIError -> 503 Service Unavailable (temporary AI issues)
        - PermanentAIError -> 502 Bad Gateway (permanent AI issues)
        - RateLimitError -> 429 Too Many Requests (rate limit exceeded)
        - RequestTooLargeError -> 413 Payload Too Large (request size validation)
        - RequestValidationError -> 422 Unprocessable Entity (Pydantic validation)
        - All other exceptions -> 500 Internal Server Error
    
    Security Features:
        - Generic error messages prevent information disclosure attacks
        - Full exception details logged server-side only
        - No stack traces or internal paths exposed to clients
        - Request correlation IDs enable secure debugging without exposing data
        - Security header preservation maintains security posture on all error responses
        - X-Content-Type-Options: nosniff prevents MIME type sniffing attacks
        - Enhanced security headers when security_headers_enabled is True:
          * X-Frame-Options: DENY prevents clickjacking attacks
          * Strict-Transport-Security enforces HTTPS with HSTS
          * Referrer-Policy controls referrer information leakage
    
    Examples:
        >>> from fastapi import FastAPI
        >>> from app.core.config import create_settings
        >>> from app.core.middleware.global_exception_handler import setup_global_exception_handler
        >>>
        >>> # Basic setup
        >>> app = FastAPI()
        >>> settings = create_settings()
        >>> setup_global_exception_handler(app, settings)
        >>>
        >>> # All unhandled exceptions now return standardized JSON responses
        >>> # including rate limiting and request size validation errors
        >>> # instead of HTML error pages or unstructured errors
    
    Example Response Format:
        ```json
        {
            "success": false,
            "error": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": "2025-07-12T12:34:56.789012"
        }
        ```
    
    Example Validation Error Response:
        ```json
        {
            "success": false,
            "error": "Invalid request data: field_name: field is required",
            "error_code": "VALIDATION_ERROR",
            "timestamp": "2025-07-12T12:34:56.789012"
        }
        ```
    
    Example Rate Limit Error Response:
        ```json
        {
            "success": false,
            "error": "Rate limit exceeded",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "timestamp": "2025-07-12T12:34:56.789012"
        }
        ```
    
    Example Request Too Large Error Response:
        ```json
        {
            "success": false,
            "error": "Request too large",
            "error_code": "REQUEST_TOO_LARGE",
            "timestamp": "2025-07-12T12:34:56.789012"
        }
        ```
    """
    ...
