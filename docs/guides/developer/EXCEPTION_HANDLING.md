# Exception Handling Guide

This guide explains the comprehensive custom exception handling system implemented across the FastAPI backend, providing consistent error handling, improved debugging capabilities, and enhanced resilience integration.

## Overview

The FastAPI backend uses a custom exception hierarchy instead of FastAPI's `HTTPException` to provide:

- **Consistent Error Handling**: Unified exception types across all API endpoints
- **Rich Context Data**: Structured debugging information without exposing sensitive data
- **Resilience Integration**: Exception classification for proper retry logic and circuit breaker behavior
- **Better Observability**: Enhanced logging and monitoring with structured error data

## Custom Exception Hierarchy

### Base Exceptions

```python
from app.core.exceptions import (
    ValidationError,
    BusinessLogicError,
    InfrastructureError,
    AuthenticationError,
    AuthorizationError
)
```

#### `ValidationError` (400 Bad Request)
Used for input validation failures, schema validation errors, and configuration format issues.

**Examples:**
- Invalid JSON format in request body
- Missing required fields
- Parameter validation failures
- Configuration format errors

**Usage:**
```python
raise ValidationError(
    "Invalid configuration format",
    context={
        "endpoint": "config_validation",
        "config_type": "resilience_config",
        "validation_errors": ["missing field: retry_attempts"]
    }
)
```

#### `BusinessLogicError` (422 Unprocessable Entity)
Used for business rule violations, resource not found errors, and domain-specific constraint violations.

**Examples:**
- Template not found
- Circuit breaker doesn't exist
- Operation not allowed in current state
- Business rule violations

**Usage:**
```python
raise BusinessLogicError(
    "Template not found",
    context={
        "endpoint": "get_template",
        "template_name": template_name,
        "available_templates": ["simple", "development", "production"]
    }
)
```

#### `InfrastructureError` (500 Internal Server Error)
Used for system errors, service failures, external service issues, and infrastructure problems.

**Examples:**
- Database connection failures
- Redis connectivity issues
- AI service unavailable
- Circuit breaker failures
- Performance monitoring errors

**Usage:**
```python
raise InfrastructureError(
    "Cache operation failed - Redis unavailable",
    context={
        "endpoint": "cache_operation",
        "cache_operation": "get",
        "redis_status": "connection_failed",
        "fallback_used": True,
        "operation_duration_ms": 150
    }
)
```

#### `AuthenticationError` (401 Unauthorized)
Used for authentication failures (handled by infrastructure security services).

#### `AuthorizationError` (403 Forbidden)
Used for authorization failures (handled by infrastructure security services).

## Context Data Standards

All custom exceptions should include rich context data for debugging and monitoring:

### Required Context Fields
- `endpoint`: The API endpoint name
- `operation`: The specific operation being performed
- `request_id`: Unique request identifier (when available)

### Optional Context Fields
- `error_details`: Detailed error information
- `resource_id`: Resource identifiers
- `performance_metrics`: Timing and performance data
- `service_status`: Service availability information
- `timestamp`: Error occurrence timestamp

### Context Data Example
```python
context = {
    "endpoint": "run_performance_benchmark",
    "operation": "comprehensive_benchmark",
    "request_id": "abc12345",
    "iterations": 50,
    "duration_ms": 1250,
    "error_details": "Service timeout exceeded",
    "timestamp": "2025-01-04T12:30:45.123Z"
}
```

## Implementation Patterns

### 1. Basic Exception Handling
```python
from app.core.exceptions import ValidationError, InfrastructureError

@router.post("/process")
async def process_request(request: ProcessRequest):
    try:
        # Validate input
        if not request.data:
            raise ValidationError(
                "Request data is required",
                context={
                    "endpoint": "process_request",
                    "operation": "validation"
                }
            )
        
        # Process request
        result = await service.process(request)
        return result
        
    except (ValidationError, BusinessLogicError, InfrastructureError):
        # Re-raise custom exceptions - handled by global exception handler
        raise
    except ValueError as e:
        # Convert standard exceptions to custom exceptions
        raise ValidationError(
            str(e),
            context={
                "endpoint": "process_request",
                "operation": "data_processing",
                "error_details": str(e)
            }
        )
    except Exception as e:
        # Convert unexpected exceptions to InfrastructureError
        raise InfrastructureError(
            "Unexpected processing error",
            context={
                "endpoint": "process_request",
                "operation": "processing",
                "error_details": str(e)
            }
        )
```

### 2. Resilience-Specific Patterns
```python
# Circuit breaker exceptions
raise InfrastructureError(
    "Circuit breaker open - service unavailable",
    context={
        "circuit_breaker": breaker_name,
        "failure_count": failure_count,
        "state": "OPEN",
        "next_attempt": next_attempt_time,
        "operation": operation_name
    }
)

# Performance benchmark exceptions
raise InfrastructureError(
    "Performance benchmark execution failed",
    context={
        "benchmark_type": "comprehensive",
        "duration_ms": execution_time,
        "memory_usage": memory_stats,
        "failure_reason": failure_details
    }
)
```

### 3. Cache-Specific Patterns
```python
# Cache operation exceptions
raise InfrastructureError(
    "Cache operation failed - Redis unavailable",
    context={
        "cache_operation": "get",
        "cache_key": sanitized_key,
        "redis_status": "connection_failed",
        "fallback_used": memory_cache_fallback,
        "operation_duration_ms": operation_time
    }
)
```

## API Endpoint Documentation

### Docstring Patterns
All API endpoints should document their custom exceptions in docstrings:

```python
@router.post("/validate")
async def validate_config(request: ConfigRequest):
    """Validate configuration data.
    
    Args:
        request: Configuration validation request
        
    Returns:
        ValidationResponse: Validation results
        
    Raises:
        ValidationError: If configuration format is invalid
        InfrastructureError: If validation process fails due to system issues
        BusinessLogicError: If configuration violates business rules
    """
```

### OpenAPI Response Documentation
```python
@router.post("/process", 
             responses={
                 400: {"model": ErrorResponse, "description": "Validation Error"},
                 422: {"model": ErrorResponse, "description": "Business Logic Error"},
                 500: {"model": ErrorResponse, "description": "Infrastructure Error"},
                 502: {"model": ErrorResponse, "description": "AI Service Error"},
                 503: {"model": ErrorResponse, "description": "Service Unavailable"}
             })
```

## Global Exception Handler Integration

The custom exceptions are automatically converted to appropriate HTTP responses by the global exception handler in `app.core.middleware`:

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Custom exceptions are mapped to appropriate HTTP status codes
    status_code = get_http_status_for_exception(exc)
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=str(exc),
            error_code=exc.__class__.__name__
        ).dict()
    )
```

### HTTP Status Code Mapping
- `ValidationError` → 400 Bad Request
- `AuthenticationError` → 401 Unauthorized
- `AuthorizationError` → 403 Forbidden
- `BusinessLogicError` → 422 Unprocessable Entity
- `InfrastructureError` → 500 Internal Server Error
- `RateLimitError` → 429 Too Many Requests
- `ServiceUnavailableError` → 503 Service Unavailable

## Exception Classification for Resilience

The `classify_ai_exception()` utility function determines whether exceptions should trigger retry logic:

```python
from app.core.exceptions import classify_ai_exception

try:
    result = await risky_operation()
except Exception as e:
    if classify_ai_exception(e):
        # This is a transient error - retry is appropriate
        await retry_operation()
    else:
        # This is a permanent error - don't retry
        handle_permanent_error(e)
```

### Transient Exceptions (Retry Allowed)
- `TransientAIError`
- `RateLimitError`
- `ServiceUnavailableError`
- Network errors (ConnectError, TimeoutException)
- HTTP 429, 500, 502, 503, 504 errors

### Permanent Exceptions (No Retry)
- `PermanentAIError`
- `ValidationError`
- `ConfigurationError`
- `ValueError`, `TypeError`, `AttributeError`
- HTTP 400-499 errors (except 429)

## Best Practices

### 1. Exception Type Selection
- **ValidationError**: User input problems, format issues
- **BusinessLogicError**: Domain rule violations, resource not found
- **InfrastructureError**: System failures, service unavailable

### 2. Context Data Guidelines
- Always include `endpoint` and `operation`
- Include `request_id` when available from request state
- Add relevant debugging information without sensitive data
- Use consistent key naming across endpoints

### 3. Error Message Guidelines
- Write clear, user-friendly error messages
- Avoid exposing internal implementation details
- Include actionable information when possible
- Keep messages concise but informative

### 4. Testing Exception Handling
```python
@pytest.mark.asyncio
async def test_validation_error_handling():
    with pytest.raises(ValidationError) as exc_info:
        await process_invalid_request()
    
    assert "Invalid configuration format" in str(exc_info.value)
    assert exc_info.value.context["endpoint"] == "process_request"
```

## Migration from HTTPException

When migrating from `HTTPException` to custom exceptions:

1. **Update imports:**
   ```python
   # Remove
   from fastapi import HTTPException
   
   # Add
   from app.core.exceptions import ValidationError, InfrastructureError, BusinessLogicError
   ```

2. **Convert raises:**
   ```python
   # Old
   raise HTTPException(status_code=400, detail="Invalid input")
   
   # New
   raise ValidationError(
       "Invalid input",
       context={
           "endpoint": "endpoint_name",
           "operation": "validation"
       }
   )
   ```

3. **Update docstrings:**
   ```python
   # Old
   """
   Raises:
       HTTPException: 400 Bad Request if input is invalid
   """
   
   # New
   """
   Raises:
       ValidationError: If input validation fails
   """
   ```

## Monitoring and Observability

The custom exception system enhances monitoring through:

### Structured Logging
All exceptions include structured context data for logging:
```python
logger.error(
    f"Processing failed: {str(exc)}",
    extra={
        "exception_type": exc.__class__.__name__,
        "context": exc.context,
        "request_id": request_id
    }
)
```

### Metrics Collection
Exception types and context data can be used for metrics:
- Error rate by exception type
- Service health based on InfrastructureError frequency
- Validation error patterns for API improvement

### Alerting
Structured exceptions enable targeted alerting:
- Critical alerts for InfrastructureError spikes
- Warning alerts for ValidationError patterns
- Business logic alerts for BusinessLogicError trends

This comprehensive exception handling system provides a solid foundation for building reliable, observable, and maintainable FastAPI applications with proper error handling throughout the entire application stack.