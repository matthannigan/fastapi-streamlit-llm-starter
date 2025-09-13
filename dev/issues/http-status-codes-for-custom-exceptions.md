# HTTP Status Codes for Custom Exceptions

**Issue**: Custom exceptions in FastAPI dependency injection are not properly converted to HTTP status codes

**Status**: ✅ **RESOLVED** for AuthenticationError, documented for comprehensive future implementation

**Date**: September 11, 2025

## Problem Statement

When custom exceptions (like `AuthenticationError`) are raised within FastAPI dependency injection functions, they bypass the global exception handler and cause several issues:

1. **Unhandled 500 errors** instead of proper HTTP status codes
2. **Middleware conflicts** with "response already started" errors
3. **Inconsistent error responses** across the application
4. **Poor debugging experience** with confusing stack traces

### Root Cause Analysis

FastAPI handles dependency injection exceptions at a different level in the execution chain than route handler exceptions. This means:

- **Global exception handlers** don't catch dependency errors
- **Middleware stack** processes exceptions before they reach global handlers
- **Custom exceptions** get wrapped in FastAPI's internal exception handling

## Solution Implemented

### HTTPException Wrapper Pattern

We implemented an **HTTPException wrapper** that converts custom exceptions to FastAPI-native `HTTPException` objects:

```python
# app/infrastructure/security/auth.py
async def verify_api_key_http(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Dependency wrapper that converts AuthenticationError to HTTPException.
    
    This wrapper catches AuthenticationError exceptions from verify_api_key and
    converts them to HTTPException which FastAPI handles more gracefully with
    the middleware stack, avoiding "response already started" conflicts.
    """
    try:
        return await verify_api_key(credentials)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(exc), "context": exc.context},
            headers={"WWW-Authenticate": "Bearer"}
        )
```

### Implementation Changes

1. **Created wrapper dependency** `verify_api_key_http` that catches `AuthenticationError`
2. **Updated endpoint dependencies** to use the wrapper instead of direct dependency
3. **Added proper exports** in the security module `__init__.py`
4. **Updated test expectations** to expect `401` instead of `403` (correct HTTP semantics)

### Results

- ✅ **No more 500 errors** - All authentication failures return `401 Unauthorized`
- ✅ **No middleware conflicts** - Clean HTTP responses without "response already started"
- ✅ **Proper error structure** - Consistent error format with context preservation
- ✅ **Better debugging** - Clear request logging with correct status codes

## Comprehensive Future Implementation Strategies

### Strategy 1: Individual Exception Wrappers (Recommended)

Create specific wrapper dependencies for each exception type that needs HTTP conversion.

**Pros:**
- **Explicit control** over each exception type
- **Easy to customize** HTTP status and response format per exception
- **No performance impact** on non-failing requests
- **Clear separation** between business logic and HTTP concerns

**Cons:**
- **Code duplication** if many exceptions need wrappers
- **Manual maintenance** when adding new exception types

**Implementation:**

```python
# Create wrappers for different exception types
async def validate_input_http(data: dict = Depends(validate_input)):
    try:
        return await validate_input(data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": str(exc), "context": exc.context}
        )

async def check_authorization_http(user: str = Depends(check_authorization)):
    try:
        return await check_authorization(user)
    except AuthorizationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"message": str(exc), "context": exc.context}
        )
```

### Strategy 2: Decorator Pattern

Create a decorator that automatically wraps dependency functions.

**Implementation:**

```python
def http_exception_handler(*exception_mappings):
    """
    Decorator that converts custom exceptions to HTTPException.
    
    Usage:
        @http_exception_handler(
            (AuthenticationError, status.HTTP_401_UNAUTHORIZED),
            (ValidationError, status.HTTP_400_BAD_REQUEST)
        )
        async def my_dependency():
            # dependency logic here
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                for exception_type, status_code in exception_mappings:
                    if isinstance(exc, exception_type):
                        raise HTTPException(
                            status_code=status_code,
                            detail={"message": str(exc), "context": getattr(exc, 'context', {})}
                        )
                raise  # Re-raise if not handled
        return wrapper
    return decorator

# Usage:
@http_exception_handler(
    (AuthenticationError, status.HTTP_401_UNAUTHORIZED),
    (ValidationError, status.HTTP_400_BAD_REQUEST)
)
async def verify_user(credentials = Depends(security)):
    # dependency logic
    pass
```

### Strategy 3: Enhanced Global Exception Handler

Modify the global exception handler to better handle dependency injection exceptions.

**Implementation:**

```python
# In global_exception_handler.py
@app.exception_handler(Exception)
async def enhanced_global_exception_handler(request: Request, exc: Exception):
    """Enhanced handler that catches dependency injection exceptions."""
    
    # Check if this is a dependency injection context
    if hasattr(request.state, 'dependency_context'):
        # Handle dependency exceptions specially
        return handle_dependency_exception(request, exc)
    
    # Normal global exception handling
    return await handle_normal_exception(request, exc)

# Middleware to mark dependency context
class DependencyContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Mark when we're in dependency resolution
        if is_dependency_resolution_phase():
            request.state.dependency_context = True
        
        response = await call_next(request)
        return response
```

### Strategy 4: Custom FastAPI Exception Handler Registration

Register specific handlers for custom exceptions at the FastAPI level.

**Implementation:**

```python
def register_custom_exception_handlers(app: FastAPI):
    """Register FastAPI exception handlers for custom exceptions."""
    
    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request, exc):
        return JSONResponse(
            status_code=401,
            content={"message": str(exc), "context": exc.context}
        )
    
    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc), "context": exc.context}
        )
    
    @app.exception_handler(AuthorizationError)
    async def authorization_exception_handler(request, exc):
        return JSONResponse(
            status_code=403,
            content={"message": str(exc), "context": exc.context}
        )

# In app setup:
app = FastAPI()
register_custom_exception_handlers(app)
```

## Recommended Implementation Plan

### Phase 1: Immediate (Current State)
- ✅ **AuthenticationError wrapper** implemented and working
- ✅ **Test expectations updated** to match HTTP standards
- ✅ **Documentation complete** with solution patterns

### Phase 2: Common Exception Types
Based on usage patterns, implement wrappers for:
1. **ValidationError** → `400 Bad Request`
2. **AuthorizationError** → `403 Forbidden`  
3. **ConfigurationError** → `500 Internal Server Error`
4. **BusinessLogicError** → `422 Unprocessable Entity`

### Phase 3: Systematic Approach
Choose and implement one of the comprehensive strategies:
- **Recommended**: Strategy 1 (Individual Wrappers) for explicit control
- **Alternative**: Strategy 2 (Decorator Pattern) for DRY principle
- **Advanced**: Strategy 4 (FastAPI Handlers) for framework integration

### Phase 4: Validation and Testing
1. **Audit all endpoints** to identify custom exception usage
2. **Update test suites** to expect correct HTTP status codes
3. **Performance testing** to ensure no regression
4. **Documentation updates** for new patterns

## Best Practices

### HTTP Status Code Standards
- **400 Bad Request** - Invalid input/validation errors
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Valid authentication but insufficient permissions
- **422 Unprocessable Entity** - Business logic violations
- **500 Internal Server Error** - Configuration or infrastructure errors

### Error Response Format
Maintain consistent error response structure:
```json
{
    "message": "Human-readable error description",
    "context": {
        "error_code": "SPECIFIC_ERROR_CODE",
        "field": "validation_field",
        "additional": "debugging_info"
    }
}
```

### Testing Considerations
- **Test both success and failure paths** for all dependencies
- **Verify correct HTTP status codes** in integration tests
- **Check error response structure** for consistency
- **Validate middleware compatibility** with new patterns

## Monitoring and Observability

### Metrics to Track
- **Exception conversion rates** (custom exceptions → HTTP responses)
- **Status code distribution** (401, 403, 400, etc.)
- **Response time impact** of wrapper dependencies
- **Error rate trends** by exception type

### Logging Enhancements
```python
# Enhanced logging in wrappers
logger.warning(
    f"Authentication failed for {request.url}: {exc}",
    extra={
        'exception_type': type(exc).__name__,
        'status_code': 401,
        'conversion_method': 'http_wrapper',
        'context': getattr(exc, 'context', {})
    }
)
```

## Migration Guide

### For Existing Dependencies
1. **Identify custom exception usage** in dependency functions
2. **Create wrapper dependencies** using the established pattern
3. **Update endpoint imports** to use wrapper dependencies
4. **Update test expectations** for correct HTTP status codes
5. **Validate behavior** in integration tests

### For New Development
1. **Use wrapper dependencies** from the start for any custom exceptions
2. **Follow HTTP status code standards** when defining exception mappings
3. **Include context preservation** for debugging
4. **Write tests** that verify HTTP status codes, not just exception types

## Conclusion

The **HTTPException wrapper pattern** provides an effective, maintainable solution for converting custom exceptions to proper HTTP responses in FastAPI dependency injection. This approach:

- **Resolves immediate issues** with authentication error handling
- **Provides clear patterns** for future exception types
- **Maintains separation of concerns** between business logic and HTTP responses
- **Preserves debugging information** while providing clean client responses
- **Scales incrementally** as new exception types are added

The solution successfully transforms a complex middleware/exception handler conflict into a clean, testable, and maintainable pattern that can be applied across the entire application.