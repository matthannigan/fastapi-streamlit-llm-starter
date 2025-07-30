# Core Exceptions Module

  file_path: `backend/app/core/exceptions.py`

This module defines the complete exception hierarchy for the backend application.
All custom exceptions are organized here to provide a clear understanding of
error types and their relationships.

## Exception Hierarchy

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

## Usage Examples

--------------

## Basic usage

from app.core.exceptions import ValidationError, AIServiceException

if not data:
raise ValidationError("Input data is required")

## Resilience patterns

from app.core.exceptions import TransientAIError, PermanentAIError

try:
result = ai_service_call()

### except TransientAIError

# Retry logic
pass

### except PermanentAIError

# Don't retry, handle permanently
pass

## Error classification

from app.core.exceptions import classify_ai_exception

try:
risky_operation()
except Exception as e:
if classify_ai_exception(e):
# This is retryable
retry_operation()

## Integration Notes

-----------------
- All exceptions include optional context data for debugging
- Exception types are designed to work with circuit breakers and retry logic
- HTTP status code mapping is provided for API error responses
- Logging integration with structured error data
