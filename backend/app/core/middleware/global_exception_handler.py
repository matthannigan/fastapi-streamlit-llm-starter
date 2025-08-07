"""
Global Exception Handler

This module provides centralized exception handling for unhandled application errors.
It ensures consistent, secure error responses while protecting internal implementation
details and providing comprehensive logging for debugging and monitoring.
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
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    get_http_status_for_exception
)
from app.schemas.common import ErrorResponse

# Configure module logger
logger = logging.getLogger(__name__)

# Context variables for request tracking (imported from main middleware module)
request_id_context: ContextVar[str] = ContextVar('request_id', default='')


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
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        Handle FastAPI request validation errors with consistent formatting.
        
        This handler catches Pydantic validation errors that occur during request
        parsing and converts them to the standardized ErrorResponse format. This
        ensures all validation errors (both automatic and custom) follow the same
        response structure.
        
        Args:
            request (Request): The FastAPI request object that failed validation
            exc (RequestValidationError): The Pydantic validation error
        
        Returns:
            JSONResponse: Standardized error response with validation details
        """
        # Get request ID for correlation (if available)
        request_id = getattr(request.state, 'request_id', request_id_context.get('unknown'))
        
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
                'request_id': request_id,
                'method': request.method,
                'url': str(request.url),
                'validation_errors': exc.errors()
            }
        )
        
        # Create standardized error response
        error_response = ErrorResponse(
            error=error_message,
            error_code="VALIDATION_ERROR"
        )
        
        return JSONResponse(
            status_code=422,  # Unprocessable Entity (standard for validation errors)
            content=error_response.dict()
        )
    
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
        elif isinstance(exc, AuthenticationError):
            error_response.error = "Authentication failed"
            error_response.error_code = "AUTHENTICATION_ERROR"
        elif isinstance(exc, AuthorizationError):
            error_response.error = "Access denied"
            error_response.error_code = "AUTHORIZATION_ERROR"
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