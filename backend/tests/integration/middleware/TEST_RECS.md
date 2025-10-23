# Middleware Testing Recommendations

## Overview

This document outlines the unique characteristics and recommended approaches for testing middleware components, contrasting them with infrastructure components like resilience patterns.

## 🔑 Key Differences in Testing Middleware

### 1. **Request/Response Lifecycle Testing** (Middleware-Specific)

**Middleware operates at the ASGI/HTTP boundary**, intercepting the entire request/response cycle:

```python
# ✅ Middleware tests must verify BOTH request AND response phases
def test_security_middleware_adds_headers(client):
    """Test security middleware injects headers on response."""
    response = client.get("/v1/health")

    # Test response phase (headers added)
    assert "Strict-Transport-Security" in response.headers
    assert "X-Frame-Options" in response.headers

# ✅ Middleware tests verify request modification
def test_logging_middleware_sets_correlation_id(client):
    """Test logging middleware sets request ID in state."""
    # This requires integration test - can't easily unit test
    response = client.get("/v1/health")
    # Middleware should have set request.state.request_id
```

**Resilience infrastructure** operates at the service call level, not HTTP:

```python
# Resilience tests focus on retry/circuit breaker logic
def test_circuit_breaker_opens_after_threshold():
    """Test circuit breaker state transitions."""
    breaker = CircuitBreaker(failure_threshold=3)

    # Test state transitions, not HTTP layer
    for _ in range(3):
        breaker.record_failure()

    assert breaker.state == CircuitBreakerState.OPEN
```

### 2. **Middleware Execution Order is Critical** (LIFO)

Middleware has **Last-In-First-Out** execution order, which is critical for testing:

```python
# ❌ BAD: Testing single middleware in isolation misses ordering issues
def test_security_middleware_alone():
    # This won't catch if logging middleware needs to run first
    pass

# ✅ GOOD: Integration tests verify correct middleware ordering
def test_middleware_execution_order(client):
    """
    Test middleware stack executes in correct order.

    Critical order:
    1. CORS (runs first, added last)
    2. Performance Monitoring
    3. Request Logging (sets correlation ID)
    4. Security (uses correlation ID for logging)
    """
    response = client.get("/v1/health")

    # Security headers should be present (Security middleware ran)
    assert "X-Frame-Options" in response.headers

    # Request ID should have been generated (Logging middleware ran first)
    # This tests implicit ordering dependency
```

**Resilience patterns** don't have order dependencies:

```python
# Resilience tests are order-independent
def test_retry_with_circuit_breaker():
    # Order doesn't matter - just behavior
    pass
```

### 3. **Side Effects and State Management** (Middleware-Heavy)

Middleware **heavily uses side effects** that must be tested:

```python
# ✅ Test contextvars usage (thread-safe state)
def test_request_logging_sets_contextvar(client):
    """Test logging middleware sets correlation ID in contextvar."""
    from app.core.middleware.request_logging import request_id_context

    # Before request
    assert request_id_context.get(None) is None

    # Make request
    client.get("/v1/health")

    # After request, contextvar should have been set during processing
    # (May need custom endpoint that captures this)

# ✅ Test request.state modification
def test_middleware_sets_request_state(client):
    """Test middleware populates request.state correctly."""
    # Requires integration test with actual endpoint that checks state
    pass

# ✅ Test response header injection
def test_middleware_adds_response_headers(client):
    """Test middleware injects security headers."""
    response = client.get("/v1/health")
    assert "X-Response-Time" in response.headers  # Performance middleware
    assert "Strict-Transport-Security" in response.headers  # Security middleware
```

**Resilience patterns** have simpler state:

```python
# Simpler state testing
def test_circuit_breaker_state_tracking():
    breaker = CircuitBreaker()
    assert breaker.failure_count == 0
    breaker.record_failure()
    assert breaker.failure_count == 1
```

### 4. **Integration vs Unit Test Balance Differs**

**Middleware testing** requires MORE integration tests:

```python
# Unit tests for middleware are LIMITED - mainly config/setup
def test_security_middleware_initialization():
    """Unit test: middleware configures correctly."""
    from app.core.middleware.security import SecurityMiddleware
    middleware = SecurityMiddleware(mock_app, settings)
    assert middleware.max_request_size == settings.max_request_size

# ✅ Integration tests are PRIMARY for middleware
@pytest.fixture
def app_with_middleware():
    """Create app with full middleware stack."""
    app = create_app()
    return app

def test_security_headers_integration(app_with_middleware):
    """Integration: test security headers in real request flow."""
    client = TestClient(app_with_middleware)
    response = client.get("/v1/health")

    # Test actual HTTP behavior
    assert response.status_code == 200
    assert "Strict-Transport-Security" in response.headers
```

**Resilience infrastructure** can be unit tested extensively:

```python
# 90%+ unit test coverage achievable
def test_retry_logic_unit():
    """Unit test retry logic in isolation."""
    retry_policy = RetryPolicy(max_attempts=3)
    # Test logic without HTTP layer
```

### 5. **Testing Pattern: The TestClient is Essential**

**Middleware requires TestClient** for meaningful tests:

```python
# ✅ REQUIRED: Use TestClient for middleware tests
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_cors_middleware(client):
    """Test CORS middleware with actual HTTP requests."""
    response = client.options(
        "/v1/health",
        headers={"Origin": "https://example.com"}
    )
    assert "Access-Control-Allow-Origin" in response.headers

def test_request_size_limiting_middleware(client):
    """Test request size middleware rejects large payloads."""
    large_body = "x" * (11 * 1024 * 1024)  # 11MB
    response = client.post("/v1/text_processing/process", data=large_body)
    assert response.status_code == 413  # Request Entity Too Large
```

**Resilience tests** can use simple function calls:

```python
# Direct function testing works fine
def test_exponential_backoff():
    delays = calculate_backoff_delays(max_attempts=3)
    assert delays == [1, 2, 4]  # No HTTP needed
```

### 6. **Specific Middleware Testing Challenges**

#### a) Testing Middleware Interactions

```python
def test_logging_and_performance_middleware_interaction(client):
    """Test logging middleware uses correlation ID from logging middleware."""
    response = client.get("/v1/health")

    # Both middlewares should have run
    # Request logging set correlation ID
    # Performance monitoring used it for timing logs
    assert response.status_code == 200
```

#### b) Testing ASGI-Level Behavior

```python
def test_compression_middleware_streams_response(client):
    """Test compression middleware handles streaming responses."""
    response = client.get(
        "/v1/large-response",
        headers={"Accept-Encoding": "gzip"}
    )
    assert response.headers.get("Content-Encoding") == "gzip"
```

#### c) Testing Environment-Specific Behavior

```python
def test_security_middleware_production_mode(monkeypatch):
    """Test security middleware stricter in production."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    app = create_app()
    client = TestClient(app)

    response = client.get("/internal/docs")
    # Internal docs disabled in production
    assert response.status_code == 404
```

## 📋 Testing Middleware: Recommended Approach

### Unit Tests (20-30% of middleware tests)

```python
# Test middleware initialization and configuration
def test_middleware_configuration():
    """Test middleware reads settings correctly."""
    settings = Settings(max_request_size=5000000)
    middleware = SecurityMiddleware(mock_app, settings)
    assert middleware.max_request_size == 5000000

# Test helper functions
def test_is_docs_endpoint_detection():
    """Test docs endpoint detection logic."""
    from app.core.middleware.security import SecurityMiddleware
    # Test helper methods
```

### Integration Tests (70-80% of middleware tests)

```python
# Test middleware behavior in real request flow
def test_full_middleware_stack(client):
    """Test complete middleware stack integration."""
    response = client.post(
        "/v1/text_processing/process",
        json={"text": "test", "operation": "summarize"},
        headers={"Authorization": "Bearer test-key"}
    )

    # Verify multiple middleware components worked
    assert response.status_code == 200
    assert "X-Response-Time" in response.headers  # Performance
    assert "X-Frame-Options" in response.headers  # Security
    assert "X-Request-ID" in response.headers  # Logging
```

## 🎯 Summary: Key Testing Differences

| Aspect | Middleware Testing | Resilience Testing |
|--------|-------------------|-------------------|
| **Primary Test Type** | Integration (70-80%) | Unit (80-90%) |
| **Test Scope** | HTTP request/response cycle | Service call behavior |
| **Execution Order** | Critical (LIFO) | Not applicable |
| **Side Effects** | Heavy (headers, state, logs) | Minimal |
| **TestClient Required** | Yes, essential | No |
| **State Management** | Contextvars, request.state | Simple instance variables |
| **Contract Source** | ASGI spec + HTTP behavior | Docstrings only |
| **Observable Outcomes** | HTTP responses, headers, status | Return values, exceptions |

**Bottom line**: Middleware testing requires **more integration testing** because middleware behavior is fundamentally about **HTTP request/response transformation** and **execution order**, while resilience infrastructure can be largely unit tested because it's about **pure logic and state transitions**.

## Recommended Testing Strategy for Middleware

### Phase 1: Unit Tests (Configuration and Helpers)

1. **Middleware Initialization**
   - Test settings are properly loaded
   - Test configuration validation
   - Test default values
   - Test error handling for invalid config

2. **Helper Functions**
   - Test utility functions (e.g., `_is_docs_endpoint()`)
   - Test data filtering/sanitization logic
   - Test pure functions that don't require HTTP context

### Phase 2: Integration Tests (Primary Coverage)

1. **Individual Middleware Behavior**
   - Test each middleware component's HTTP behavior
   - Test request validation and rejection
   - Test response header injection
   - Test side effects (logging, state management)

2. **Middleware Stack Integration**
   - Test middleware execution order
   - Test middleware interactions
   - Test cumulative effect of multiple middlewares
   - Test error propagation through stack

3. **Environment-Specific Behavior**
   - Test development vs production differences
   - Test feature toggles
   - Test configuration overrides

4. **Edge Cases and Error Handling**
   - Test oversized requests
   - Test malformed requests
   - Test missing headers
   - Test exception handling

## Testing Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Over-Mocking Middleware

```python
# ❌ BAD: Mocking defeats the purpose of middleware testing
def test_security_middleware_with_mocks(mocker):
    mock_call_next = mocker.Mock(return_value=Response())
    middleware = SecurityMiddleware(mock_app, settings)
    # This doesn't test actual HTTP behavior
```

### ❌ Anti-Pattern 2: Testing Implementation Details

```python
# ❌ BAD: Testing internal state instead of observable behavior
def test_middleware_internal_state():
    middleware = SecurityMiddleware(mock_app, settings)
    # Don't test internal attributes
    assert middleware._internal_counter == 0
```

### ❌ Anti-Pattern 3: Ignoring Execution Order

```python
# ❌ BAD: Testing middleware in isolation when order matters
def test_security_middleware_alone():
    # Misses the fact that logging middleware must run first
    pass
```

## ✅ Best Practices

1. **Use TestClient for all integration tests**
2. **Test observable HTTP behavior (status codes, headers, body)**
3. **Test middleware interactions and execution order**
4. **Use monkeypatch for environment variable testing**
5. **Test both success and error paths**
6. **Verify side effects (logs, state, contextvars)**
7. **Test with realistic request scenarios**
8. **Document middleware dependencies in test docstrings**

## See Also

- **Testing Philosophy**: `docs/guides/testing/TESTING.md`
- **Integration Testing Guide**: `docs/guides/testing/INTEGRATION_TESTS.md`
- **Unit Testing Guide**: `docs/guides/testing/UNIT_TESTS.md`
- **Middleware Contracts**: `backend/contracts/core/middleware/*.pyi`
- **App Factory Pattern**: `backend/CLAUDE.md` - "App Factory Pattern" section
