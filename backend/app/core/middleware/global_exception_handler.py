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
from app.core.exceptions import (
    ApplicationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    BusinessLogicError,
    InfrastructureError,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    RequestTooLargeError,
    get_http_status_for_exception
)
from app.schemas.common import ErrorResponse

# Configure module logger
logger = logging.getLogger(__name__)

# Context variables for request tracking (imported from main middleware module)
request_id_context: ContextVar[str] = ContextVar("request_id", default="")


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

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle FastAPI request validation errors with consistent formatting and security headers.

        Catches Pydantic validation errors that occur during request parsing and converts
        them to the standardized ErrorResponse format with security header preservation.
        This ensures all validation errors (both automatic and custom) follow the same
        response structure with proper HTTP status codes, detailed logging, and security
        protection even when validation failures occur after middleware processing.

        Args:
            request (Request): The FastAPI request object that failed validation
            exc (RequestValidationError): The Pydantic validation error containing
                                         field-level validation details

        Returns:
            JSONResponse: Standardized error response with HTTP 422 status code,
                         validation details in ErrorResponse format, and security headers

        Raises:
            None: This handler always returns a proper JSONResponse without raising

        Behavior:
            - Extracts request ID from request state for correlation logging
            - Processes all validation errors from the Pydantic exception
            - Formats field names and error messages for user feedback
            - Logs validation errors with full context for monitoring
            - Returns first validation error as user message, logs all details
            - Creates ErrorResponse with VALIDATION_ERROR error code
            - Returns HTTP 422 Unprocessable Entity status code
            - Preserves security headers on validation errors to maintain security posture
            - Always adds X-Content-Type-Options: nosniff header for MIME type protection
            - Conditionally adds enhanced security headers when security_headers_enabled is True

        Security Features:
            - X-Content-Type-Options: nosniff (always added) prevents MIME type sniffing attacks
            - X-Frame-Options: DENY (when enabled) prevents clickjacking attacks
            - Strict-Transport-Security: max-age=31536000; includeSubDomains (when enabled) enforces HTTPS
            - Referrer-Policy: strict-origin-when-cross-origin (when enabled) controls referrer information

        Examples:
            >>> # Request with missing required field triggers this handler
            >>> response = await handler(request, RequestValidationError(errors=[
            ...     {'loc': ('body', 'required_field'), 'msg': 'field required', 'type': 'value_error.missing'}
            ... ]))
            >>> assert response.status_code == 422
            >>> assert "required_field: field required" in response.json()['error']
            >>> assert response.headers["X-Content-Type-Options"] == "nosniff"

        Example Response:
            ```json
            {
                "success": false,
                "error": "Invalid request data: required_field: field required",
                "error_code": "VALIDATION_ERROR",
                "timestamp": "2025-07-12T12:34:56.789012"
            }
            ```

        Example Security Headers (when enabled):
            ```
            X-Content-Type-Options: nosniff
            X-Frame-Options: DENY
            Strict-Transport-Security: max-age=31536000; includeSubDomains
            Referrer-Policy: strict-origin-when-cross-origin
            ```
        """
        # Get request ID for correlation (if available)
        request_id = getattr(request.state, "request_id", request_id_context.get("unknown"))

        # Extract validation error details
        error_details = []
        for error in exc.errors():
            field_name = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field_name}: {error['msg']}")

        error_message = "Invalid request data"
        if error_details:
            # Include first error for user feedback, log all details
            error_message = f"Invalid request data: {error_details[0]}"

        # Log the validation error with context
        logger.warning(
            f"Request validation error in request {request_id}: {'; '.join(error_details)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "validation_errors": exc.errors()
            }
        )

        # Create standardized error response
        error_response = ErrorResponse(
            error=error_message,
            error_code="VALIDATION_ERROR"
        )

        response = JSONResponse(
            status_code=422,  # Unprocessable Entity (standard for validation errors)
            content=error_response.dict()
        )

        # Add security headers to validation error responses to ensure they are preserved
        # when validation errors occur after middleware processing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Add additional security headers if security headers are enabled
        if hasattr(settings, 'security_headers_enabled') and settings.security_headers_enabled:
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Global exception handler for unhandled application errors with security header preservation.

        Catches all unhandled exceptions, logs them appropriately, and returns
        standardized error responses with security header preservation to protect
        internal implementation details while providing useful information for debugging
        and monitoring. This is the ultimate fallback handler that ensures the application
        never returns unstructured error responses to clients and maintains security
        posture even when exceptions occur after middleware processing.

        Args:
            request (Request): The FastAPI request object that triggered the exception
            exc (Exception): The unhandled exception that was raised during processing
                           from middleware, application code, or dependencies

        Returns:
            JSONResponse: Standardized error response with appropriate HTTP status code,
                         ErrorResponse format, and security headers

        Raises:
            None: This handler always returns a proper JSONResponse without raising

        Behavior:
            - Extracts request ID from request state for correlation logging
            - Logs full exception details with traceback for debugging
            - Maps exception types to appropriate HTTP status codes
            - Generates secure error messages that don't expose internal details
            - Handles special cases like API versioning errors with custom responses
            - Preserves error context when provided in ApplicationError
            - Returns structured ErrorResponse with appropriate error codes
            - Maintains security by never exposing stack traces to clients
            - Preserves security headers on all error responses to maintain security posture
            - Always adds X-Content-Type-Options: nosniff header for MIME type protection
            - Conditionally adds enhanced security headers when security_headers_enabled is True

        Security Features:
            - X-Content-Type-Options: nosniff (always added) prevents MIME type sniffing attacks
            - X-Frame-Options: DENY (when enabled) prevents clickjacking attacks
            - Strict-Transport-Security: max-age=31536000; includeSubDomains (when enabled) enforces HTTPS
            - Referrer-Policy: strict-origin-when-cross-origin (when enabled) controls referrer information
            - Security headers are preserved on all error responses, maintaining security posture

        Exception Mapping:
            - ValidationError/BusinessLogicError -> 400 with VALIDATION_ERROR
            - AuthenticationError -> 401 with AUTHENTICATION_ERROR
            - AuthorizationError -> 403 with AUTHORIZATION_ERROR
            - ConfigurationError -> 400 with CONFIGURATION_ERROR
            - RateLimitError -> 429 with RATE_LIMIT_EXCEEDED
            - RequestTooLargeError -> 413 with REQUEST_TOO_LARGE
            - TransientAIError -> 503 with SERVICE_UNAVAILABLE
            - PermanentAIError -> 502 with AI_SERVICE_ERROR
            - InfrastructureError -> 502 with INFRASTRUCTURE_ERROR
            - ApplicationError -> 400 with context-aware error details
            - All other exceptions -> 500 with INTERNAL_ERROR

        Examples:
            >>> # Infrastructure service failure
            >>> response = await handler(request, InfrastructureError("Database connection failed"))
            >>> assert response.status_code == 502
            >>> assert response.json()['error_code'] == "INFRASTRUCTURE_ERROR"
            >>> assert response.headers["X-Content-Type-Options"] == "nosniff"

            >>> # Rate limit exceeded
            >>> response = await handler(request, RateLimitError("Too many requests"))
            >>> assert response.status_code == 429
            >>> assert response.json()['error_code'] == "RATE_LIMIT_EXCEEDED"

            >>> # Request too large
            >>> response = await handler(request, RequestTooLargeError("Payload exceeds limit"))
            >>> assert response.status_code == 413
            >>> assert response.json()['error_code'] == "REQUEST_TOO_LARGE"

            >>> # Application error with context
            >>> app_error = ApplicationError("Invalid input", context={'field': 'email'})
            >>> response = await handler(request, app_error)
            >>> assert response.status_code == 400
            >>> assert 'email' in response.json().get('details', {})

        Example Response:
            ```json
            {
                "success": false,
                "error": "External service error",
                "error_code": "INFRASTRUCTURE_ERROR",
                "timestamp": "2025-07-12T12:34:56.789012",
                "details": {"service": "database", "operation": "connection"}
            }
            ```

        Example Security Headers (when enabled):
            ```
            X-Content-Type-Options: nosniff
            X-Frame-Options: DENY
            Strict-Transport-Security: max-age=31536000; includeSubDomains
            Referrer-Policy: strict-origin-when-cross-origin
            ```

        Notes:
            Security headers are preserved on all error responses to ensure that the
            application maintains its security posture even when exceptions occur
            after middleware processing has completed. This prevents security header
            stripping that could otherwise expose clients to security risks.
        """
        # Get request ID for correlation (if available)
        request_id = getattr(request.state, "request_id", request_id_context.get("unknown"))

        # Log the full exception with context
        logger.error(
            f"Unhandled exception in request {request_id}: {exc!s}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "exception_type": type(exc).__name__,
                "exception_module": type(exc).__module__
            },
            exc_info=True
        )

        # Determine HTTP status code based on exception type
        http_status = get_http_status_for_exception(exc)

        # Special-case known ApplicationError contexts that require custom payloads
        if isinstance(exc, ApplicationError):
            context = getattr(exc, "context", {}) or {}
            # Preserve API versioning error response shape used in tests and clients
            if context.get("error_code") == "API_VERSION_NOT_SUPPORTED":
                headers = {
                    "X-API-Supported-Versions": ", ".join(context.get("supported_versions", [])),
                    "X-API-Current-Version": context.get("current_version", ""),
                    # Add security headers to API versioning error responses
                    "X-Content-Type-Options": "nosniff"
                }

                # Add additional security headers if security headers are enabled
                if hasattr(settings, 'security_headers_enabled') and settings.security_headers_enabled:
                    headers["X-Frame-Options"] = "DENY"
                    headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

                content = {
                    "error": "Unsupported API version",
                    "error_code": "API_VERSION_NOT_SUPPORTED",
                    "requested_version": context.get("requested_version"),
                    "supported_versions": context.get("supported_versions", []),
                    "current_version": context.get("current_version"),
                    "detail": str(exc)
                }
                return JSONResponse(status_code=400, content=content, headers=headers)

        # Create standardized error response
        error_response = ErrorResponse(
            error="Internal server error",
            error_code="INTERNAL_ERROR"
        )

        # Customize error message based on exception type for better UX
        if isinstance(exc, (ValidationError, BusinessLogicError)):
            error_response.error = "Invalid request data"
            error_response.error_code = "VALIDATION_ERROR"
        elif isinstance(exc, AuthenticationError):
            error_response.error = "Authentication failed"
            error_response.error_code = "AUTHENTICATION_ERROR"
        elif isinstance(exc, AuthorizationError):
            error_response.error = "Access denied"
            error_response.error_code = "AUTHORIZATION_ERROR"
        elif isinstance(exc, ConfigurationError):
            error_response.error = "Service configuration error"
            error_response.error_code = "CONFIGURATION_ERROR"
        elif isinstance(exc, RateLimitError):
            error_response.error = "Rate limit exceeded"
            error_response.error_code = "RATE_LIMIT_EXCEEDED"
        elif isinstance(exc, RequestTooLargeError):
            error_response.error = "Request too large"
            error_response.error_code = "REQUEST_TOO_LARGE"
        elif isinstance(exc, TransientAIError):
            error_response.error = "AI service temporarily unavailable"
            error_response.error_code = "SERVICE_UNAVAILABLE"
        elif isinstance(exc, PermanentAIError):
            error_response.error = "AI service error"
            error_response.error_code = "AI_SERVICE_ERROR"
        elif isinstance(exc, InfrastructureError):
            error_response.error = "External service error"
            error_response.error_code = "INFRASTRUCTURE_ERROR"
        elif isinstance(exc, ApplicationError):
            # Prefer error_code provided in context when available
            context = getattr(exc, "context", {}) or {}
            if "error_code" in context:
                error_response.error_code = str(context["error_code"])
            error_response.error = str(exc) or "Invalid request data"
            # Propagate context as details for debugging
            error_response.details = context if context else None

        response = JSONResponse(
            status_code=http_status,
            content=error_response.dict()
        )

        # Add security headers to error responses to ensure they are preserved
        # when exceptions occur after middleware processing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Add additional security headers if security headers are enabled
        if hasattr(settings, 'security_headers_enabled') and settings.security_headers_enabled:
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response
