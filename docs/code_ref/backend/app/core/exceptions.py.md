---
sidebar_label: exceptions
---

# Core Exceptions Module

  file_path: `backend/app/core/exceptions.py`

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

## ApplicationError

Base exception for all application-specific errors within the business logic layer.

This exception serves as the foundation for all errors that originate from business logic,
validation, authentication, authorization, and other application-level concerns. It provides
structured error handling with contextual information for debugging and monitoring.

Attributes:
    message: Human-readable error description
    context: Optional dictionary containing additional error context and debugging information

Behavior:
    - Preserves original error message in structured format
    - Maintains optional context dictionary for debugging information
    - Provides string representation that includes context when available
    - Supports serialization for API error responses
    - Integrates with monitoring systems for error tracking
    
Examples:
    >>> # Basic error without context
    >>> error = ApplicationError("User validation failed")
    >>> str(error)
    'User validation failed'
    
    >>> # Error with debugging context
    >>> error = ApplicationError("Invalid input", {"field": "email", "value": "invalid@"})
    >>> str(error)
    'Invalid input (Context: {'field': 'email', 'value': 'invalid@'})'
    
    >>> # Usage in application code
    >>> if not user_data.get("email"):
    ...     raise ApplicationError(
    ...         "Email is required", 
    ...         {"user_id": user_data.get("id"), "provided_fields": list(user_data.keys())}
    ...     )

### __init__()

```python
def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
```

Initialize ApplicationError with message and optional context.

Args:
    message: Human-readable error description for display and logging
    context: Optional dictionary with additional debugging information,
            error metadata, or relevant state data

Behavior:
    - Sets up exception inheritance chain properly
    - Stores message and context for later access
    - Ensures context is always a dictionary (empty if None provided)
    - Prepares error for integration with logging and monitoring systems

### __str__()

```python
def __str__(self) -> str:
```

Generate string representation of the error including context if available.

Returns:
    String representation with context appended if context exists
    
Behavior:
    - Returns plain message if no context provided
    - Appends context information in readable format when available
    - Ensures consistent string formatting across all application errors
    - Supports debugging by including relevant context data

## ValidationError

Raised when input validation fails across the application layer.

This exception should be used for all forms of data validation failures including
user input validation, schema validation, business rule validation, and data
format/content validation errors. It provides clear error classification for
client-side error handling and debugging.

Behavior:
    - Maps to HTTP 400 (Bad Request) status code automatically
    - Provides structured validation error information
    - Supports field-specific error reporting through context
    - Integrates with API error response formatting
    - Enables client-side validation error handling
    
Examples:
    >>> # Basic validation error
    >>> raise ValidationError("Email format is invalid")
    
    >>> # Field-specific validation with context
    >>> raise ValidationError(
    ...     "Invalid email format", 
    ...     {"field": "email", "value": "user@invalid", "expected_format": "user@domain.com"}
    ... )
    
    >>> # Multiple field validation error
    >>> raise ValidationError(
    ...     "Multiple fields failed validation",
    ...     {
    ...         "failed_fields": ["email", "phone"], 
    ...         "errors": {"email": "Invalid format", "phone": "Required"}
    ...     }
    ... )
    
    >>> # Schema validation error
    >>> raise ValidationError(
    ...     "Request schema validation failed",
    ...     {"schema": "TextProcessingRequest", "missing_fields": ["text", "operation"]}
    ... )

## ConfigurationError

Raised when there are configuration-related errors.

Use this for missing environment variables, invalid configuration
values, or configuration parsing errors.

## BusinessLogicError

Raised when business rules or domain logic constraints are violated.

Use this for domain-specific errors that represent violations of
business rules rather than technical failures.

## AuthenticationError

Raised when authentication fails.

Use this when a user fails to provide valid credentials, such as:
- Missing API key
- Invalid API key
- Malformed authentication headers
- Expired tokens

## AuthorizationError

Raised when authorization fails.

Use this when an authenticated user lacks permission for a resource:
- Insufficient privileges for an endpoint
- Access denied to specific resources
- Role-based access control violations
- Resource ownership violations

## RequestTooLargeError

Raised when the incoming request exceeds configured size limits.

## InfrastructureError

Base exception for infrastructure-related errors.

This should be used for errors that originate from external systems,
network issues, database problems, or other infrastructure concerns.

### __init__()

```python
def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
```

### __str__()

```python
def __str__(self) -> str:
```

## AIServiceException

Base exception for AI service errors.

This is the root of the AI service exception hierarchy and should be
used for any errors related to AI service interactions.

## TransientAIError

Transient AI service error that should be retried.

Use this for temporary failures that are likely to resolve themselves
with retry attempts, such as network hiccups, temporary service overload,
or rate limiting that will reset.

## PermanentAIError

Permanent AI service error that should not be retried.

Use this for errors that indicate a fundamental problem that won't
be resolved by retrying, such as invalid API keys, malformed requests,
or service deprecation.

## RateLimitError

Rate limit exceeded error.

Raised when the AI service indicates that the rate limit has been
exceeded. This is a transient error that should be retried with
appropriate backoff.

### __init__()

```python
def __init__(self, message: str, retry_after: int = 60, context: Optional[Dict[str, Any]] = None):
```

## ServiceUnavailableError

AI service temporarily unavailable.

Raised when the AI service is temporarily down or unreachable.
This is a transient error that should be retried.

## classify_ai_exception()

```python
def classify_ai_exception(exc: Exception) -> bool:
```

Classify whether an AI-related exception should trigger retry attempts in resilience patterns.

This function provides intelligent exception classification for the resilience system,
enabling automatic retry logic for transient failures while avoiding retries for
permanent errors that will not resolve with additional attempts.

Args:
    exc: The exception instance to classify for retry eligibility.
        Supports both custom application exceptions and standard Python/HTTP exceptions.
    
Returns:
    True if the exception represents a transient failure that should be retried,
    False if it represents a permanent failure that should not be retried.
    
Behavior:
    - Classifies network and connection errors as transient (should retry)
    - Treats HTTP 5xx and 429 status codes as transient failures
    - Classifies HTTP 4xx client errors as permanent (should not retry)
    - Treats validation and configuration errors as permanent failures
    - Applies conservative approach: unknown exceptions default to retryable
    - Supports both httpx and requests library exception types
    - Integrates with circuit breaker pattern for failure threshold tracking
    
Examples:
    >>> # Network error (should retry)
    >>> import httpx
    >>> error = httpx.ConnectError("Connection failed")
    >>> assert classify_ai_exception(error) == True
    
    >>> # Rate limit error (should retry with backoff)
    >>> rate_error = RateLimitError("Rate limit exceeded", retry_after=60)
    >>> assert classify_ai_exception(rate_error) == True
    
    >>> # Validation error (should not retry)
    >>> validation_error = ValidationError("Invalid API key format")
    >>> assert classify_ai_exception(validation_error) == False
    
    >>> # HTTP server error (should retry)
    >>> server_error = httpx.HTTPStatusError("Server error", request=None, response=Mock(status_code=503))
    >>> assert classify_ai_exception(server_error) == True
    
    >>> # HTTP client error (should not retry)
    >>> client_error = httpx.HTTPStatusError("Bad request", request=None, response=Mock(status_code=400))
    >>> assert classify_ai_exception(client_error) == False

## get_http_status_for_exception()

```python
def get_http_status_for_exception(exc: Exception) -> int:
```

Map application and infrastructure exceptions to appropriate HTTP status codes for API responses.

This function provides consistent HTTP status code mapping across the entire application,
ensuring that API clients receive semantically correct status codes based on the type
of error that occurred. It supports both custom application exceptions and standard
Python exceptions.

Args:
    exc: The exception instance to map to an HTTP status code.
        Supports all custom application exceptions, infrastructure exceptions,
        and common Python standard library exceptions.
    
Returns:
    Appropriate HTTP status code (int) between 400-599 based on exception type.
    Returns 500 (Internal Server Error) for unknown exception types.
    
Behavior:
    - Maps validation errors to 400 (Bad Request) for client input issues
    - Maps authentication errors to 401 (Unauthorized) for missing/invalid credentials
    - Maps authorization errors to 403 (Forbidden) for insufficient permissions
    - Maps rate limit errors to 429 (Too Many Requests) with retry-after semantics
    - Maps service unavailable errors to 503 for temporary outages
    - Maps configuration errors to 500 for server-side configuration issues
    - Provides consistent error response structure across all API endpoints
    - Supports custom exception hierarchy for domain-specific error mapping
    
Examples:
    >>> # Validation error mapping
    >>> error = ValidationError("Invalid email format")
    >>> assert get_http_status_for_exception(error) == 400
    
    >>> # Authentication error mapping
    >>> auth_error = AuthenticationError("Invalid API key")
    >>> assert get_http_status_for_exception(auth_error) == 401
    
    >>> # Rate limit error mapping
    >>> rate_error = RateLimitError("Rate limit exceeded", retry_after=60)
    >>> assert get_http_status_for_exception(rate_error) == 429
    
    >>> # Service unavailable mapping
    >>> service_error = ServiceUnavailableError("AI service temporarily down")
    >>> assert get_http_status_for_exception(service_error) == 503
    
    >>> # Unknown exception mapping
    >>> unknown_error = Exception("Unexpected error")
    >>> assert get_http_status_for_exception(unknown_error) == 500
