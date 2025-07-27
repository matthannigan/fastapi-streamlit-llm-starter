"""
Core Exceptions Module

This module defines the complete exception hierarchy for the backend application.
All custom exceptions are organized here to provide a clear understanding of
error types and their relationships.

Exception Hierarchy:
-------------------
Exception
├── ApplicationError (Base for all application-specific errors)
│   ├── ValidationError (Input validation failures)
│   ├── AuthenticationError (Authentication failures - missing/invalid credentials)
│   ├── AuthorizationError (Authorization failures - insufficient permissions)
│   ├── ConfigurationError (Configuration-related errors)
│   └── BusinessLogicError (Domain/business rule violations)
└── InfrastructureError (Base for infrastructure-related errors)
    └── AIServiceException (Base for AI service errors)
        ├── TransientAIError (Temporary AI service errors - should retry)
        │   ├── RateLimitError (Rate limiting errors)
        │   └── ServiceUnavailableError (Service temporarily unavailable)
        └── PermanentAIError (Permanent AI service errors - don't retry)

Usage Examples:
--------------
Basic usage:
    from app.core.exceptions import ValidationError, AIServiceException
    
    if not data:
        raise ValidationError("Input data is required")

Resilience patterns:
    from app.core.exceptions import TransientAIError, PermanentAIError
    
    try:
        result = ai_service_call()
    except TransientAIError:
        # Retry logic
        pass
    except PermanentAIError:
        # Don't retry, handle permanently
        pass

Error classification:
    from app.core.exceptions import classify_ai_exception
    
    try:
        risky_operation()
    except Exception as e:
        if classify_ai_exception(e):
            # This is retryable
            retry_operation()

Integration Notes:
-----------------
- All exceptions include optional context data for debugging
- Exception types are designed to work with circuit breakers and retry logic
- HTTP status code mapping is provided for API error responses
- Logging integration with structured error data
"""

from typing import Any, Dict, Optional
import httpx


# ============================================================================
# Base Application Exceptions
# ============================================================================

class ApplicationError(Exception):
    """
    Base exception for all application-specific errors.
    
    This should be used for errors that originate from business logic,
    validation, or other application-level concerns.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message


class ValidationError(ApplicationError):
    """
    Raised when input validation fails.
    
    Use this for user input validation, schema validation,
    or any data format/content validation errors.
    """
    pass


class ConfigurationError(ApplicationError):
    """
    Raised when there are configuration-related errors.
    
    Use this for missing environment variables, invalid configuration
    values, or configuration parsing errors.
    """
    pass


class BusinessLogicError(ApplicationError):
    """
    Raised when business rules or domain logic constraints are violated.
    
    Use this for domain-specific errors that represent violations of
    business rules rather than technical failures.
    """
    pass


class AuthenticationError(ApplicationError):
    """
    Raised when authentication fails.
    
    Use this when a user fails to provide valid credentials, such as:
    - Missing API key
    - Invalid API key
    - Malformed authentication headers
    - Expired tokens
    """
    pass


class AuthorizationError(ApplicationError):
    """
    Raised when authorization fails.
    
    Use this when an authenticated user lacks permission for a resource:
    - Insufficient privileges for an endpoint
    - Access denied to specific resources
    - Role-based access control violations
    - Resource ownership violations
    """
    pass


# ============================================================================
# Infrastructure Exceptions
# ============================================================================

class InfrastructureError(Exception):
    """
    Base exception for infrastructure-related errors.
    
    This should be used for errors that originate from external systems,
    network issues, database problems, or other infrastructure concerns.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if self.context:
            return f"{self.message} (Context: {self.context})"
        return self.message


# ============================================================================
# AI Service Exception Hierarchy
# ============================================================================

class AIServiceException(InfrastructureError):
    """
    Base exception for AI service errors.
    
    This is the root of the AI service exception hierarchy and should be
    used for any errors related to AI service interactions.
    """
    pass


class TransientAIError(AIServiceException):
    """
    Transient AI service error that should be retried.
    
    Use this for temporary failures that are likely to resolve themselves
    with retry attempts, such as network hiccups, temporary service overload,
    or rate limiting that will reset.
    """
    pass


class PermanentAIError(AIServiceException):
    """
    Permanent AI service error that should not be retried.
    
    Use this for errors that indicate a fundamental problem that won't
    be resolved by retrying, such as invalid API keys, malformed requests,
    or service deprecation.
    """
    pass


class RateLimitError(TransientAIError):
    """
    Rate limit exceeded error.
    
    Raised when the AI service indicates that the rate limit has been
    exceeded. This is a transient error that should be retried with
    appropriate backoff.
    """
    pass


class ServiceUnavailableError(TransientAIError):
    """
    AI service temporarily unavailable.
    
    Raised when the AI service is temporarily down or unreachable.
    This is a transient error that should be retried.
    """
    pass


# ============================================================================
# Exception Classification Utilities
# ============================================================================

def classify_ai_exception(exc: Exception) -> bool:
    """
    Classify whether an AI-related exception should trigger retries.
    
    Args:
        exc: The exception to classify
        
    Returns:
        True if the exception is transient and should be retried,
        False if it's permanent and should not be retried
    """
    # Network and connection errors (should retry)
    if isinstance(exc, (
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError,
        TransientAIError,
        RateLimitError,
        ServiceUnavailableError
    )):
        return True

    # HTTP errors that should be retried
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        # Retry on server errors and rate limits
        if status_code in (429, 500, 502, 503, 504):
            return True
        # Don't retry on client errors
        if 400 <= status_code < 500:
            return False

    # Permanent errors (should not retry)
    if isinstance(exc, (
        PermanentAIError,
        ValidationError,
        ConfigurationError,
        ValueError,
        TypeError,
        AttributeError
    )):
        return False

    # Default: retry on unknown exceptions (conservative approach)
    return True


def get_http_status_for_exception(exc: Exception) -> int:
    """
    Map exceptions to appropriate HTTP status codes for API responses.
    
    Args:
        exc: The exception to map
        
    Returns:
        Appropriate HTTP status code
    """
    if isinstance(exc, ValidationError):
        return 400  # Bad Request
    elif isinstance(exc, AuthenticationError):
        return 401  # Unauthorized
    elif isinstance(exc, AuthorizationError):
        return 403  # Forbidden
    elif isinstance(exc, ConfigurationError):
        return 500  # Internal Server Error
    elif isinstance(exc, BusinessLogicError):
        return 422  # Unprocessable Entity
    elif isinstance(exc, RateLimitError):
        return 429  # Too Many Requests
    elif isinstance(exc, ServiceUnavailableError):
        return 503  # Service Unavailable
    elif isinstance(exc, PermanentAIError):
        return 502  # Bad Gateway
    elif isinstance(exc, TransientAIError):
        return 503  # Service Unavailable
    elif isinstance(exc, AIServiceException):
        return 502  # Bad Gateway
    elif isinstance(exc, InfrastructureError):
        return 500  # Internal Server Error
    elif isinstance(exc, ApplicationError):
        return 400  # Bad Request
    else:
        return 500  # Internal Server Error


# ============================================================================
# Backwards Compatibility Aliases
# ============================================================================

# For smooth migration, maintain aliases to the old locations
# These can be removed in a future version once all imports are updated

__all__ = [
    # Base exceptions
    "ApplicationError",
    "ValidationError", 
    "AuthenticationError",
    "AuthorizationError",
    "ConfigurationError",
    "BusinessLogicError",
    "InfrastructureError",
    
    # AI service exceptions
    "AIServiceException",
    "TransientAIError",
    "PermanentAIError", 
    "RateLimitError",
    "ServiceUnavailableError",
    
    # Utility functions
    "classify_ai_exception",
    "get_http_status_for_exception",
]
