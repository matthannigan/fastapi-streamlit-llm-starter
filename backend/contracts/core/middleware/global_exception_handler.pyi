"""
Global Exception Handler

## Overview

Centralized, security-conscious exception handling for the FastAPI application.
Provides standardized JSON error responses, consistent HTTP status mapping, and
structured logging with request correlation for observability.

## Responsibilities

- **Consistency**: Uniform error payloads via `app.schemas.common.ErrorResponse`
- **Security**: Sanitized messages; no internal details leaked to clients
- **Mapping**: Stable HTTP status codes by exception category
- **Observability**: Correlated logs using request IDs

## HTTP Status Mapping

- `ApplicationError` → 400
- `InfrastructureError` → 502
- `TransientAIError` → 503
- `PermanentAIError` → 502
- Other uncaught exceptions → 500

## Special Cases

Maintains compatibility for API versioning errors by returning a specific
payload and headers (`X-API-Supported-Versions`, `X-API-Current-Version`).

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
traditional middleware implementation patterns.
"""

import logging
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import Settings
from app.core.exceptions import ApplicationError, ValidationError, AuthenticationError, AuthorizationError, ConfigurationError, BusinessLogicError, InfrastructureError, TransientAIError, PermanentAIError, get_http_status_for_exception
from app.schemas.common import ErrorResponse


def setup_global_exception_handler(app: FastAPI, settings: Settings) -> None:
    """
    Configure global exception handling for unhandled application errors.
    
    Sets up comprehensive exception handlers that catch all unhandled exceptions
    across the FastAPI application and return consistent, secure error responses.
    The handler ensures clients receive predictable error responses while protecting
    internal implementation details and sensitive information.
    
    Args:
        app (FastAPI): The FastAPI application instance to configure with exception handlers
        settings (Settings): Application settings that influence error handling behavior
    
    Returns:
        None: This function configures the app in-place and returns nothing
    
    Raises:
        ConfigurationError: If the app instance is invalid or settings are malformed
    
    Behavior:
        - Registers RequestValidationError handler for Pydantic validation errors (HTTP 422)
        - Registers global Exception handler for all uncaught exceptions
        - Logs full exception details server-side with request context for debugging
        - Maps exception types to appropriate HTTP status codes
        - Generates secure, user-friendly error messages that don't expose internals
        - Preserves request correlation IDs for debugging and monitoring
        - Returns standardized ErrorResponse format for all error types
        - Handles special cases like API versioning errors with custom responses
        - Ensures the application never returns unhandled exceptions to clients
    
    HTTP Status Code Mapping:
        - ApplicationError -> 400 Bad Request (validation, business logic errors)
        - InfrastructureError -> 502 Bad Gateway (external service failures)
        - TransientAIError -> 503 Service Unavailable (temporary AI issues)
        - PermanentAIError -> 502 Bad Gateway (permanent AI issues)
        - RequestValidationError -> 422 Unprocessable Entity (Pydantic validation)
        - All other exceptions -> 500 Internal Server Error
    
    Security Features:
        - Generic error messages prevent information disclosure attacks
        - Full exception details logged server-side only
        - No stack traces or internal paths exposed to clients
        - Request correlation IDs enable secure debugging without exposing data
    
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
    """
    ...
