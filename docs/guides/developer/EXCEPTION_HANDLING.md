---
sidebar_label: Exception Handling
---

# Exception Handling Guide

This guide provides comprehensive documentation for custom error handling in the FastAPI backend, including the exception hierarchy, middleware integration, and best practices for implementing robust error handling in your applications.

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Exception Hierarchy](#-exception-hierarchy)
3. [Exception Categories](#-exception-categories)
4. [Global Exception Handler](#-global-exception-handler)
5. [Exception Classification](#-exception-classification)
6. [HTTP Status Code Mapping](#-http-status-code-mapping)
7. [Usage Patterns](#-usage-patterns)
8. [Testing Exception Handling](#-testing-exception-handling)
9. [Best Practices](#-best-practices)
10. [Integration with Infrastructure](#-integration-with-infrastructure)
11. [Troubleshooting](#-troubleshooting)

## 🎯 Overview

The FastAPI backend implements a comprehensive exception handling system designed to provide:

- **Consistent Error Responses**: Standardized error format across all API endpoints
- **Security-Conscious Messaging**: Error messages that don't expose internal details
- **Resilience Integration**: Exception classification for retry and circuit breaker logic
- **Comprehensive Logging**: Full error context for debugging and monitoring
- **HTTP Compliance**: Appropriate status codes for different error types

### Key Components

```
app/core/exceptions.py      # Exception hierarchy definitions
app/core/middleware.py      # Global exception handler
app/schemas/common.py       # Error response models
```

## 📊 Exception Hierarchy

The backend uses a hierarchical exception system that separates application concerns from infrastructure concerns:

```
Exception
├── ApplicationError (Base for all application-specific errors)
│   ├── ValidationError (Input validation failures)
│   ├── AuthenticationError (Authentication failures)
│   ├── AuthorizationError (Authorization failures)
│   ├── ConfigurationError (Configuration-related errors)
│   └── BusinessLogicError (Domain/business rule violations)
└── InfrastructureError (Base for infrastructure-related errors)
    └── AIServiceException (Base for AI service errors)
        ├── TransientAIError (Temporary AI service errors - should retry)
        │   ├── RateLimitError (Rate limiting errors)
        │   └── ServiceUnavailableError (Service temporarily unavailable)
        └── PermanentAIError (Permanent AI service errors - don't retry)
```

### Design Principles

1. **Clear Separation**: Application vs Infrastructure error boundaries
2. **Retry Classification**: Transient vs Permanent error distinction
3. **Security Focus**: No sensitive information in error messages
4. **Extensibility**: Easy to add domain-specific exceptions

## 🏗️ Exception Categories

### Application Errors

Application errors represent issues with business logic, validation, or user interactions:

#### ValidationError
```python
from app.core.exceptions import ValidationError

# Input validation failures
if not request.text.strip():
    raise ValidationError("Text cannot be empty")

# Schema validation failures  
if len(request.text) > MAX_TEXT_LENGTH:
    raise ValidationError(f"Text exceeds maximum length of {MAX_TEXT_LENGTH}")
```

#### AuthenticationError
```python
from app.core.exceptions import AuthenticationError

# Missing credentials
if not api_key:
    raise AuthenticationError("API key is required")

# Invalid credentials
if not verify_api_key(api_key):
    raise AuthenticationError("Invalid API key")
```

#### AuthorizationError
```python
from app.core.exceptions import AuthorizationError

# Insufficient permissions
if not user.has_permission("admin"):
    raise AuthorizationError("Admin access required")

# Resource access denied
if not user.can_access_resource(resource_id):
    raise AuthorizationError("Access denied to resource")
```

#### BusinessLogicError
```python
from app.core.exceptions import BusinessLogicError

# Domain rule violations
if account.balance < transaction.amount:
    raise BusinessLogicError("Insufficient funds for transaction")

# Workflow constraints
if order.status == "completed":
    raise BusinessLogicError("Cannot modify completed order")
```

#### ConfigurationError
```python
from app.core.exceptions import ConfigurationError

# Missing required configuration
if not settings.gemini_api_key:
    raise ConfigurationError("GEMINI_API_KEY environment variable is required")

# Invalid configuration values
if settings.max_retries < 0:
    raise ConfigurationError("max_retries must be non-negative")
```

### Infrastructure Errors

Infrastructure errors represent issues with external systems, network, or technical components:

#### AIServiceException Hierarchy
```python
from app.core.exceptions import (
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError
)

# Temporary service issues (retry recommended)
try:
    response = await ai_service.process(text)
except httpx.TimeoutException:
    raise ServiceUnavailableError("AI service timeout")

# Rate limiting (retry with backoff)
if response.status_code == 429:
    raise RateLimitError("Rate limit exceeded")

# Permanent service issues (don't retry)
if response.status_code == 401:
    raise PermanentAIError("Invalid AI service credentials")
```

#### InfrastructureError
```python
from app.core.exceptions import InfrastructureError

# Database connection issues
try:
    await database.connect()
except ConnectionError:
    raise InfrastructureError("Database connection failed")

# External service errors
if not redis_client.ping():
    raise InfrastructureError("Redis cache unavailable")
```

## 🛡️ Global Exception Handler

The global exception handler in `app/core/middleware.py` provides centralized error processing:

### Handler Features

- **Request Correlation**: Links errors to specific request IDs for tracing
- **Comprehensive Logging**: Logs full exception details with context
- **Secure Responses**: Returns user-safe error messages
- **Status Code Mapping**: Automatic HTTP status code assignment
- **Structured Format**: Consistent `ErrorResponse` model

### Handler Implementation

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled application errors."""
    
    # Get request correlation ID
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Log full exception with context
    logger.error(
        f"Unhandled exception in request {request_id}: {str(exc)}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'exception_type': type(exc).__name__
        },
        exc_info=True
    )
    
    # Determine HTTP status and create response
    http_status = get_http_status_for_exception(exc)
    error_response = ErrorResponse(error="Internal server error", error_code="INTERNAL_ERROR")
    
    return JSONResponse(status_code=http_status, content=error_response.dict())
```

### Validation Error Handler

FastAPI request validation errors are handled separately:

```python
@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI request validation errors."""
    
    # Extract validation details
    error_details = []
    for error in exc.errors():
        field_name = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(f"{field_name}: {error['msg']}")
    
    # Create user-friendly error message
    error_message = "Invalid request data"
    if error_details:
        error_message = f"Invalid request data: {error_details[0]}"
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(error=error_message, error_code="VALIDATION_ERROR").dict()
    )
```

## 🔍 Exception Classification

The `classify_ai_exception` utility determines whether exceptions should trigger retry logic:

### Classification Logic

```python
from app.core.exceptions import classify_ai_exception

def classify_ai_exception(exc: Exception) -> bool:
    """Classify whether an exception should trigger retries."""
    
    # Transient errors (should retry)
    if isinstance(exc, (
        httpx.ConnectError,
        httpx.TimeoutException,
        TransientAIError,
        RateLimitError,
        ServiceUnavailableError
    )):
        return True
    
    # HTTP errors with retryable status codes
    if isinstance(exc, httpx.HTTPStatusError):
        # Server errors and rate limits are retryable
        if exc.response.status_code in (429, 500, 502, 503, 504):
            return True
        # Client errors are not retryable
        if 400 <= exc.response.status_code < 500:
            return False
    
    # Permanent errors (should not retry)
    if isinstance(exc, (
        PermanentAIError,
        ValidationError,
        ConfigurationError
    )):
        return False
    
    # Default: retry on unknown exceptions (conservative approach)
    return True
```

### Usage in Resilience Patterns

```python
from app.core.exceptions import classify_ai_exception

async def resilient_ai_call(operation):
    """Example of using exception classification in retry logic."""
    max_attempts = 3
    
    for attempt in range(max_attempts):
        try:
            return await ai_service.call(operation)
        except Exception as e:
            if not classify_ai_exception(e) or attempt == max_attempts - 1:
                # Don't retry permanent errors or on final attempt
                raise
            # Wait before retry
            await asyncio.sleep(2 ** attempt)
```

## 📊 HTTP Status Code Mapping

The `get_http_status_for_exception` function maps exceptions to HTTP status codes:

### Status Code Rules

| Exception Type | HTTP Status | Code | Rationale |
|----------------|------------|------|-----------|
| `ValidationError` | 400 | Bad Request | Client input error |
| `AuthenticationError` | 401 | Unauthorized | Missing/invalid credentials |
| `AuthorizationError` | 403 | Forbidden | Insufficient permissions |
| `BusinessLogicError` | 422 | Unprocessable Entity | Business rule violation |
| `ConfigurationError` | 500 | Internal Server Error | Server configuration issue |
| `RateLimitError` | 429 | Too Many Requests | Rate limiting |
| `ServiceUnavailableError` | 503 | Service Unavailable | Temporary service issue |
| `PermanentAIError` | 502 | Bad Gateway | Permanent external service error |
| `TransientAIError` | 503 | Service Unavailable | Temporary external service error |
| `InfrastructureError` | 500 | Internal Server Error | Infrastructure failure |
| `ApplicationError` | 400 | Bad Request | Generic application error |
| Unknown exceptions | 500 | Internal Server Error | Safety fallback |

### Custom Status Code Mapping

```python
from app.core.exceptions import get_http_status_for_exception

# Example usage in custom error handling
try:
    result = await some_operation()
except Exception as e:
    status_code = get_http_status_for_exception(e)
    return JSONResponse(
        status_code=status_code,
        content={"error": "Operation failed"}
    )
```

## 💻 Usage Patterns

### Basic Exception Handling in Services

```python
from app.core.exceptions import ValidationError, InfrastructureError

class TextProcessorService:
    async def process_text(self, text: str) -> str:
        """Process text with comprehensive error handling."""
        try:
            # Input validation
            if not text.strip():
                raise ValidationError("Text cannot be empty")
            
            if len(text) > self.max_length:
                raise ValidationError(f"Text exceeds maximum length of {self.max_length}")
            
            # Process with external service
            result = await self.ai_service.process(text)
            
            return result
            
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except httpx.TimeoutException:
            # Convert to infrastructure error
            raise InfrastructureError("AI service timeout")
        except Exception as e:
            # Log and convert unknown errors
            logger.error(f"Unexpected error in text processing: {e}")
            raise InfrastructureError("Text processing failed")
```

### Exception Handling in API Endpoints

```python
from fastapi import HTTPException
from app.core.exceptions import ValidationError, BusinessLogicError

@router.post("/process")
async def process_text(request: TextProcessingRequest):
    """API endpoint with exception handling."""
    try:
        # Validate request
        if not request.text:
            raise ValidationError("Text is required")
        
        # Process request
        result = await text_processor.process(request)
        
        return TextProcessingResponse(success=True, result=result)
        
    except ValidationError as e:
        # Validation errors become 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    except BusinessLogicError as e:
        # Business logic errors become 422 Unprocessable Entity
        raise HTTPException(status_code=422, detail=str(e))
    # Note: Other exceptions are handled by global exception handler
```

### Exception Context and Debugging

```python
from app.core.exceptions import ApplicationError

# Adding context to exceptions for debugging
try:
    user_data = await fetch_user_data(user_id)
except DatabaseError as e:
    raise ApplicationError(
        message="Failed to fetch user data",
        context={
            "user_id": user_id,
            "operation": "fetch_user_data",
            "original_error": str(e)
        }
    )
```

### Resilience Integration

```python
from app.core.exceptions import TransientAIError, PermanentAIError
from app.infrastructure.resilience import circuit_breaker, with_retry

@circuit_breaker(failure_threshold=5)
@with_retry(max_attempts=3)
async def ai_operation(text: str):
    """AI operation with resilience patterns."""
    try:
        response = await ai_service.process(text)
        return response
    except httpx.TimeoutException:
        # Timeout is transient - circuit breaker and retry will handle
        raise TransientAIError("AI service timeout")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            # Authentication error is permanent - stop retrying
            raise PermanentAIError("Invalid AI service credentials")
        elif e.response.status_code >= 500:
            # Server error is transient - retry
            raise TransientAIError(f"AI service error: {e.response.status_code}")
        else:
            # Client error is permanent - don't retry
            raise PermanentAIError(f"AI request error: {e.response.status_code}")
```

## 🧪 Testing Exception Handling

### Unit Testing Exceptions

```python
import pytest
from app.core.exceptions import ValidationError, InfrastructureError
from app.services.text_processor import TextProcessorService

class TestTextProcessorExceptions:
    """Test exception handling in text processor service."""
    
    async def test_validation_error_empty_text(self):
        """Test ValidationError for empty text."""
        service = TextProcessorService()
        
        with pytest.raises(ValidationError, match="Text cannot be empty"):
            await service.process_text("")
    
    async def test_validation_error_text_too_long(self):
        """Test ValidationError for text exceeding maximum length."""
        service = TextProcessorService()
        long_text = "x" * (service.max_length + 1)
        
        with pytest.raises(ValidationError, match="Text exceeds maximum length"):
            await service.process_text(long_text)
    
    @patch('app.services.text_processor.ai_service')
    async def test_infrastructure_error_timeout(self, mock_ai_service):
        """Test InfrastructureError for AI service timeout."""
        mock_ai_service.process.side_effect = httpx.TimeoutException("Timeout")
        service = TextProcessorService()
        
        with pytest.raises(InfrastructureError, match="AI service timeout"):
            await service.process_text("test text")
```

### API Testing with Exception Handling

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAPIExceptionHandling:
    """Test API exception handling."""
    
    def test_validation_error_returns_400(self):
        """Test that validation errors return 400 status."""
        response = client.post("/v1/text_processing/process", json={
            "text": "",  # Empty text should trigger ValidationError
            "operation": "summarize"
        })
        
        assert response.status_code == 400
        assert "Text cannot be empty" in response.json()["error"]
    
    def test_authentication_error_returns_401(self):
        """Test that authentication errors return 401 status."""
        response = client.post("/v1/text_processing/process", json={
            "text": "test text",
            "operation": "summarize"
        })  # No API key provided
        
        assert response.status_code == 401
        assert "Authentication failed" in response.json()["error"]
    
    @patch('app.services.text_processor.ai_service')
    def test_infrastructure_error_returns_500(self, mock_ai_service):
        """Test that infrastructure errors return 500 status."""
        mock_ai_service.process.side_effect = Exception("Database connection failed")
        
        response = client.post("/v1/text_processing/process", 
                             json={"text": "test", "operation": "summarize"},
                             headers={"X-API-Key": "test-key"})
        
        assert response.status_code == 500
        assert "Internal server error" in response.json()["error"]
```

### Exception Classification Testing

```python
import pytest
from app.core.exceptions import classify_ai_exception, TransientAIError, PermanentAIError

class TestExceptionClassification:
    """Test exception classification for resilience patterns."""
    
    def test_transient_errors_are_retryable(self):
        """Test that transient errors are classified as retryable."""
        transient_errors = [
            TransientAIError("Service temporarily unavailable"),
            httpx.TimeoutException("Request timeout"),
            httpx.ConnectError("Connection failed")
        ]
        
        for error in transient_errors:
            assert classify_ai_exception(error) is True
    
    def test_permanent_errors_are_not_retryable(self):
        """Test that permanent errors are not retryable."""
        permanent_errors = [
            PermanentAIError("Invalid API key"),
            ValidationError("Invalid input"),
            ConfigurationError("Missing configuration")
        ]
        
        for error in permanent_errors:
            assert classify_ai_exception(error) is False
    
    def test_http_status_code_classification(self):
        """Test HTTP status code classification."""
        # Create mock response for HTTPStatusError
        mock_response = Mock()
        
        # Server errors should be retryable
        mock_response.status_code = 503
        server_error = httpx.HTTPStatusError("Service unavailable", response=mock_response)
        assert classify_ai_exception(server_error) is True
        
        # Client errors should not be retryable
        mock_response.status_code = 400
        client_error = httpx.HTTPStatusError("Bad request", response=mock_response)
        assert classify_ai_exception(client_error) is False
```

## 📝 Best Practices

### Exception Hierarchy Guidelines

1. **Use Specific Exceptions**: Choose the most specific exception type for better error handling
2. **Include Context**: Add relevant context information for debugging
3. **Consistent Messaging**: Use clear, user-friendly error messages
4. **Security Awareness**: Never expose sensitive information in error messages

```python
# ✅ Good: Specific exception with context
raise ValidationError(
    "Invalid email format",
    context={"email": user_input, "field": "email"}
)

# ❌ Bad: Generic exception without context
raise Exception("Something went wrong")
```

### Infrastructure Resilience Exception Patterns

**Broad Exception Handling for Infrastructure Resilience:**

The cache infrastructure demonstrates a resilience-first approach where `except Exception:` is appropriate for graceful degradation:

```python
# ✅ Infrastructure Pattern: Broad handling for resilience
class CacheFactory:
    @staticmethod
    async def create_ai_cache() -> CacheInterface:
        try:
            ai_cache = AIResponseCache(redis_url=settings.REDIS_URL)
            if await ai_cache.connect():
                return ai_cache
        except Exception:
            # Infrastructure failures shouldn't break the application
            logger.warning("Redis unavailable, falling back to memory cache")
            
        return InMemoryCache(default_ttl=300)
```

**Key Principles for Infrastructure Exception Handling:**

1. **Resilience Over Precision**: Infrastructure failures should not cascade to application failures
2. **Graceful Degradation**: Always provide fallback mechanisms when possible
3. **Comprehensive Logging**: Log all details server-side for debugging while continuing operation
4. **Operational Awareness**: Use monitoring to track infrastructure exception patterns

**When NOT to use broad exception handling:**

```python
# ❌ Bad: Broad handling in business logic
async def transfer_money(from_account: str, to_account: str, amount: float):
    try:
        # Complex business logic
        result = await banking_service.transfer(from_account, to_account, amount)
        return result
    except Exception:
        # This hides important business logic errors!
        logger.error("Transfer failed")
        return {"status": "error"}

# ✅ Good: Specific handling in business logic
async def transfer_money(from_account: str, to_account: str, amount: float):
    try:
        result = await banking_service.transfer(from_account, to_account, amount)
        return result
    except InsufficientFundsError as e:
        raise BusinessLogicError(f"Insufficient funds: {e}")
    except AccountNotFoundError as e:
        raise ValidationError(f"Invalid account: {e}")
    except BankingServiceError as e:
        raise InfrastructureError(f"Banking service unavailable: {e}")
```

### Error Handling Patterns

1. **Fail Fast**: Validate inputs early and raise appropriate exceptions
2. **Transform Exceptions**: Convert infrastructure exceptions to application exceptions at boundaries
3. **Log Appropriately**: Log detailed information server-side, return safe messages to clients
4. **Use Type Hints**: Include exception types in function signatures for clarity

```python
# ✅ Good: Clear exception handling with transformation
async def process_user_request(request: UserRequest) -> UserResponse:
    """Process user request with proper exception handling."""
    try:
        # Validate early
        if not request.user_id:
            raise ValidationError("User ID is required")
        
        # Call infrastructure service
        user_data = await user_service.get_user(request.user_id)
        
        return UserResponse(data=user_data)
        
    except DatabaseConnectionError as e:
        # Transform infrastructure error to application error
        logger.error(f"Database error for user {request.user_id}: {e}")
        raise InfrastructureError("Unable to retrieve user data")
    except ValidationError:
        # Re-raise validation errors as-is
        raise
```

### Resilience Integration

1. **Use Exception Classification**: Leverage `classify_ai_exception` for retry logic
2. **Appropriate Exception Types**: Use `TransientAIError` vs `PermanentAIError` correctly
3. **Circuit Breaker Integration**: Let circuit breakers handle exception patterns
4. **Graceful Degradation**: Provide fallback responses when possible

```python
# ✅ Good: Resilience-aware exception handling
@circuit_breaker(failure_threshold=5)
async def ai_text_analysis(text: str) -> AnalysisResult:
    """AI analysis with resilience patterns."""
    try:
        result = await external_ai_service.analyze(text)
        return AnalysisResult.from_api_response(result)
    except httpx.TimeoutException:
        # Timeout is transient - let circuit breaker handle
        raise TransientAIError("Analysis service timeout")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # Rate limit is transient
            raise RateLimitError("Analysis rate limit exceeded")
        elif e.response.status_code >= 500:
            # Server error is transient
            raise TransientAIError(f"Analysis service error: {e.response.status_code}")
        else:
            # Client error is permanent
            raise PermanentAIError(f"Analysis request error: {e.response.status_code}")
```

### Testing Guidelines

1. **Test All Exception Paths**: Ensure every exception type is tested
2. **Mock External Dependencies**: Use mocks to trigger specific exception scenarios
3. **Test Status Code Mapping**: Verify HTTP status codes are correct
4. **Test Context Preservation**: Ensure error context is properly handled

## 🔧 Integration with Infrastructure

### Cache Service Integration

The cache infrastructure uses a specific exception handling pattern that prioritizes **graceful degradation** over strict exception typing. This approach ensures the application continues operating even when Redis becomes unavailable.

#### Cache Fallback Pattern

```python
class CacheFactory:
    @staticmethod
    async def create_ai_cache() -> CacheInterface:
        """Create AI cache with graceful fallback to memory cache."""
        try:
            ai_cache = AIResponseCache(redis_url=settings.REDIS_URL)
            if await ai_cache.connect():
                return ai_cache
        except Exception:
            # Broad exception handling for maximum resilience
            logger.warning("Redis unavailable, falling back to memory cache")
            
        return InMemoryCache(default_ttl=300)  # 5-minute fallback TTL
```

#### Infrastructure Exception Handling Guidelines

**When to use broad `except Exception:` handling:**

1. **Graceful Degradation**: When system should continue operating despite infrastructure failures
2. **Fallback Scenarios**: When alternative implementations are available
3. **Non-Critical Operations**: When failure doesn't impact core functionality

```python
# ✅ Appropriate: Graceful degradation in cache operations
async def get_cached_value(self, key: str) -> Optional[Any]:
    """Get value from cache with graceful degradation."""
    try:
        return await self.redis.get(key)
    except Exception:
        # Redis errors shouldn't break the application
        logger.warning("Cache unavailable, operation continuing without cache")
        return None

# ✅ Appropriate: Connection establishment with fallback
async def connect_to_redis(self) -> bool:
    """Connect to Redis with fallback handling."""
    try:
        await self.redis.ping()
        logger.info("Connected to Redis successfully")
        return True
    except Exception as e:
        logger.warning(f"Redis connection failed: {e} - caching disabled")
        self.redis = None
        return False
```

**When to use specific exception handling:**

1. **Business Logic**: When different error types require different responses
2. **User-Facing Operations**: When users need specific error information
3. **Critical Paths**: When errors indicate serious system problems

```python
# ✅ Appropriate: Specific handling for business operations
async def process_user_data(self, user_id: str) -> UserData:
    """Process user data with specific error handling."""
    try:
        user = await self.database.get_user(user_id)
        return self.transform_user_data(user)
    except UserNotFoundError:
        raise ValidationError(f"User {user_id} not found")
    except DatabaseConnectionError:
        raise InfrastructureError("Database temporarily unavailable")
    except ValidationError:
        # Re-raise validation errors as-is
        raise
```

#### Cache Infrastructure Exception Patterns

The cache infrastructure implements the following exception handling strategy:

```python
class AIResponseCache:
    async def get(self, key: str) -> Optional[Any]:
        """Get cache value with comprehensive error handling."""
        try:
            # Attempt Redis operation
            cached_data = await self.redis.get(key)
            if cached_data:
                return json.loads(cached_data.decode('utf-8'))
            return None
        except Exception as e:
            # Log the specific error but don't expose details
            logger.warning(f"Cache get error for key {key}: {e}")
            return None  # Graceful degradation - act as cache miss
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set cache value with error resilience."""
        try:
            cache_data = json.dumps(value).encode('utf-8')
            await self.redis.setex(key, ttl or self.default_ttl, cache_data)
        except Exception as e:
            # Cache write failures are non-critical
            logger.warning(f"Cache set error for key {key}: {e}")
            # Continue execution - cache miss on next read
```

#### Monitoring Infrastructure Exceptions

When using broad exception handling, implement comprehensive monitoring:

```python
class MonitoringMiddleware:
    def track_infrastructure_exceptions(self, operation: str, exception: Exception):
        """Track infrastructure exceptions for operational awareness."""
        
        # Log detailed error information
        logger.warning(
            f"Infrastructure exception in {operation}",
            extra={
                "operation": operation,
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "stack_trace": traceback.format_exc()
            }
        )
        
        # Update metrics for monitoring
        self.metrics.increment(f'infrastructure.exceptions.{operation}')
        self.metrics.increment(f'infrastructure.exceptions.type.{type(exception).__name__}')
```

### Resilience Service Integration

```python
from app.core.exceptions import classify_ai_exception

class ResilienceOrchestrator:
    async def execute_with_resilience(self, operation, strategy):
        """Execute operation with resilience patterns."""
        circuit_breaker = self.get_circuit_breaker(operation)
        
        for attempt in range(strategy.max_retries):
            try:
                return await circuit_breaker.call(operation)
            except Exception as e:
                if not classify_ai_exception(e):
                    # Permanent error - don't retry
                    raise
                if attempt == strategy.max_retries - 1:
                    # Final attempt - raise the error
                    raise
                # Wait before retry
                await asyncio.sleep(strategy.get_delay(attempt))
```

### Monitoring Integration

```python
from app.core.exceptions import ApplicationError, InfrastructureError

class MonitoringMiddleware:
    async def process_request(self, request, call_next):
        """Monitor requests with exception tracking."""
        try:
            response = await call_next(request)
            # Track successful requests
            self.metrics.increment('requests.success')
            return response
        except ApplicationError as e:
            # Track application errors
            self.metrics.increment('requests.application_error')
            self.metrics.increment(f'requests.error.{type(e).__name__}')
            raise
        except InfrastructureError as e:
            # Track infrastructure errors
            self.metrics.increment('requests.infrastructure_error')
            self.metrics.increment(f'requests.error.{type(e).__name__}')
            raise
```

## 🔧 Troubleshooting

### Common Issues

#### Exception Not Being Caught by Global Handler

**Problem**: Custom exceptions are not being processed by the global exception handler.

**Solution**: Ensure exceptions inherit from the correct base classes:

```python
# ✅ Correct: Inherits from ApplicationError
class CustomValidationError(ValidationError):
    pass

# ❌ Incorrect: Doesn't inherit from hierarchy
class CustomError(Exception):
    pass
```

#### Incorrect HTTP Status Codes

**Problem**: API returns wrong HTTP status codes for certain exceptions.

**Solution**: Check exception type hierarchy and status code mapping:

```python
# Verify exception inheritance
from app.core.exceptions import get_http_status_for_exception

# Test status code mapping
exception = ValidationError("Test error")
status_code = get_http_status_for_exception(exception)
assert status_code == 400
```

#### Missing Exception Context in Logs

**Problem**: Exception logs don't contain enough context for debugging.

**Solution**: Include relevant context when raising exceptions:

```python
# ✅ Good: Include context
try:
    result = await external_service.call(data)
except ServiceError as e:
    raise InfrastructureError(
        "External service failed",
        context={
            "service": "external_service",
            "data_id": data.id,
            "original_error": str(e)
        }
    )
```

#### Retry Logic Not Working

**Problem**: Resilience patterns are not retrying when expected.

**Solution**: Verify exception classification:

```python
from app.core.exceptions import classify_ai_exception

# Test exception classification
exception = ServiceUnavailableError("Service down")
should_retry = classify_ai_exception(exception)
assert should_retry is True
```

### Infrastructure Exception Debugging

**When broad `except Exception:` is used in infrastructure (like cache operations):**

1. **Check Application Logs**: Infrastructure exceptions are logged with full context
2. **Monitor Fallback Behavior**: Verify fallback mechanisms activate correctly
3. **Track Exception Patterns**: Use monitoring to identify recurring infrastructure issues
4. **Test Graceful Degradation**: Ensure application continues operating despite infrastructure failures

```python
# Debug infrastructure exceptions
import logging
logging.basicConfig(level=logging.WARNING)

# Test cache fallback behavior
cache_factory = CacheFactory()
cache = await cache_factory.create_ai_cache()
# Check logs for "Redis unavailable, falling back to memory cache"

# Verify cache operations work with fallback
result = await cache.get("test_key")  # Should work with memory cache
```

### Debugging Exception Flow

1. **Check Exception Type**: Verify the exception inherits from the correct base class
2. **Verify Classification**: Test with `classify_ai_exception` for resilience integration
3. **Check Status Mapping**: Test with `get_http_status_for_exception` for HTTP codes
4. **Review Logs**: Check both application logs and middleware logs for complete context
5. **Test Error Responses**: Verify client receives expected error format
6. **Test Infrastructure Fallbacks**: Ensure graceful degradation works as expected

### Performance Considerations

1. **Exception Creation Cost**: Custom exceptions with context have minimal overhead
2. **Logging Performance**: Structured logging with context is efficient
3. **Global Handler Impact**: Global exception handler adds minimal latency
4. **Classification Efficiency**: Exception classification is fast for common types
5. **Infrastructure Resilience**: Broad exception handling in infrastructure has negligible performance impact

## 📚 Related Documentation

### Prerequisites
- **[Code Standards](./CODE_STANDARDS.md)**: Coding patterns and architectural guidelines
- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Understanding service boundaries for exception handling

### Related Topics
- **[Testing Guide](./TESTING.md)**: Comprehensive testing patterns including exception testing
- **[Authentication Guide](./AUTHENTICATION.md)**: Authentication and authorization error handling
- **[Resilience Guide](../infrastructure/RESILIENCE.md)**: Integration with circuit breakers and retry logic
- **[Monitoring Guide](../infrastructure/MONITORING.md)**: Error tracking and alerting

### Next Steps
- **[API Documentation](../application/API.md)**: Implementing robust API endpoints with proper exception handling
- **[Security Guide](../infrastructure/SECURITY.md)**: Security-conscious error handling and information disclosure prevention