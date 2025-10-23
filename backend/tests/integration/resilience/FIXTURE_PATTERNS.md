# Resilience Integration Test Fixture Patterns Guide

## Overview

This document provides comprehensive guidance on fixture patterns and best practices for resilience integration testing. It captures the lessons learned from fixing critical test issues and provides actionable patterns to ensure reliable, maintainable tests.

**Context**: The patterns in this guide were developed through fixing 10 critical test issues identified in `TEST_FIXES.md`. These issues caused test failures, flaky behavior, and maintenance problems due to violations of the App Factory Pattern and improper fixture timing.

## Table of Contents

1. [Critical Foundation Patterns](#critical-foundation-patterns)
2. [App Factory Pattern Compliance](#app-factory-pattern-compliance)
3. [Fixture Timing Patterns](#fixture-timing-patterns)
4. [Environment Variable Testing](#environment-variable-testing)
5. [Authentication Testing Patterns](#authentication-testing-patterns)
6. [Service Factory Patterns](#service-factory-patterns)
7. [Common Violations and Solutions](#common-violations-and-solutions)
8. [Test Isolation Guarantees](#test-isolation-guarantees)
9. [Choosing the Right Fixture](#choosing-the-right-fixture)
10. [Migration Checklist](#migration-checklist)

---

## Critical Foundation Patterns

### Pattern 1: Environment → Settings → App Creation Order

**This is the most critical pattern - violations caused Blocker Issue #1**

```python
# ✅ CORRECT: Follow this exact order
@pytest.fixture
def reliable_test_client(monkeypatch):
    # Step 1: Set environment variables FIRST
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-key-12345")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")

    # Step 2: Create settings AFTER environment is set
    settings = create_settings()  # Picks up environment variables

    # Step 3: Create app WITH the settings
    app = create_app(settings_obj=settings)
    return TestClient(app)

# ❌ CRITICAL BUG: Never do this
@pytest.fixture
def broken_test_client(monkeypatch):
    # WRONG: Create app with current environment
    app = create_app()  # Uses existing environment

    # WRONG: Set environment AFTER app already created
    monkeypatch.setenv("ENVIRONMENT", "staging")  # Too late! App won't see this

    return TestClient(app)  # App has wrong configuration
```

**Why This Matters**:
- Settings objects cache environment variables at creation time
- Apps cache settings at initialization time
- Changes after creation are ignored, causing wrong test behavior
- This was the root cause of Issue #1 (Blocker) in TEST_FIXES.md

### Pattern 2: Always Use monkeypatch for Environment Variables

**This prevents test pollution that causes flaky tests**

```python
# ✅ CORRECT: Always use monkeypatch
def test_production_config(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-prod-key")

    app = create_app()  # Picks up production environment
    client = TestClient(app)

    response = client.get("/v1/health")
    assert response.status_code == 200

# ❌ NEVER: Direct environment modification
import os

def test_broken_config():
    os.environ["ENVIRONMENT"] = "production"  # POLLUTION! Persists forever
    # This change affects ALL subsequent tests
```

**Why This Matters**:
- Direct `os.environ` changes persist after test completion
- Causes tests to become order-dependent (flaky)
- Parallel execution fails because workers inherit polluted state
- Manual cleanup is error-prone and often forgotten

---

## App Factory Pattern Compliance

### Pattern 3: Function Scope for Test Isolation

```python
# ✅ CORRECT: Function scope ensures fresh instances
@pytest.fixture(scope="function")
def isolated_test_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    app = create_app()
    return TestClient(app)

# ❌ AVOID: Module scope can cause shared state issues
@pytest.fixture(scope="module")
def shared_test_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    app = create_app()
    return TestClient(app)  # Shared across all tests in module
```

### Pattern 4: Fresh Settings Instances

```python
# ✅ CORRECT: Create fresh settings for each test
@pytest.fixture(scope="function")
def test_settings(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    return create_settings()  # Fresh instance

# ✅ CORRECT: Use settings in app creation
@pytest.fixture
def test_client(test_settings):
    app = create_app(settings_obj=test_settings)
    return TestClient(app)
```

### Pattern 5: Custom Configuration Testing

```python
@pytest.fixture
def custom_resilience_client(monkeypatch):
    # Configure custom resilience settings
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("RESILIENCE_PRESET", "custom")
    monkeypatch.setenv("RESILIENCE_CUSTOM_CONFIG", json.dumps({
        "circuit_breaker_threshold": 3,
        "retry_attempts": 5,
        "timeout_ms": 1000
    }))

    app = create_app()
    return TestClient(app)

def test_custom_resilience_behavior(custom_resilience_client):
    # Test with custom resilience configuration
    response = custom_resilience_client.post("/internal/resilience/test-failure")
    assert response.status_code == 200
    assert response.json()["circuit_breaker_threshold"] == 3
```

---

## Fixture Timing Patterns

### Pattern 6: Mocks Applied Before Service Initialization

**This solves Issues #3-#8 (Critical) from TEST_FIXES.md**

```python
# ✅ CORRECT: Mock applied before service creation
@pytest.fixture
async def service_with_mock_ai(settings):
    # Apply mock BEFORE service creation
    with patch("app.services.text_processor.Agent") as mock_class:
        # Configure mock instance
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Create service WITH mock already active
        service = TextProcessorService(settings=settings)
        yield service  # Service uses mock during __init__

# ❌ VIOLATION: Mock applied after service creation
@pytest.fixture
async def broken_service(settings):
    # WRONG: Service creates real Agent immediately
    service = TextProcessorService(settings=settings)

    # Mock applied AFTER service already has Agent
    with patch("app.services.text_processor.Agent"):
        yield service  # Service still uses real Agent!
```

### Pattern 7: Service Factory for Different Mock Behaviors

```python
# Factory fixture for failing AI service
@pytest.fixture
async def service_with_failing_ai(settings):
    with patch("app.services.text_processor.Agent") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.run.side_effect = ConnectionError("AI service down")
        mock_class.return_value = mock_instance

        service = TextProcessorService(settings=settings)
        yield service

# Factory fixture for flaky AI service
@pytest.fixture
async def service_with_flaky_ai(settings):
    with patch("app.services.text_processor.Agent") as mock_class:
        mock_instance = AsyncMock()
        # Fail twice, then succeed
        mock_instance.run.side_effect = [
            ConnectionError("First failure"),
            ConnectionError("Second failure"),
            "Success on third try"
        ]
        mock_class.return_value = mock_instance

        service = TextProcessorService(settings=settings)
        yield service

# Usage
async def test_circuit_breaker_activation(service_with_failing_ai):
    # Service already has failing AI configured
    for attempt in range(5):
        with pytest.raises(ConnectionError):
            await service.process_text("test")

    # Verify circuit breaker opened
    assert service.resilience.circuit_breaker.is_open()

async def test_retry_behavior(service_with_flaky_ai):
    # Service will fail twice, then succeed
    result = await service.process_text("test")
    assert result == "Success on third try"
    assert service.resilience.metrics["retries"] == 2
```

---

## Environment Variable Testing

### Pattern 8: Environment Override Testing

```python
def test_environment_detection(monkeypatch):
    """Test environment auto-detection with different configurations."""

    # Test development environment
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "true")
    app = create_app()

    response = TestClient(app).get("/internal/resilience/environment")
    assert response.json()["environment"] == "development"

def test_production_environment_detection(monkeypatch):
    """Test production environment detection."""

    # Set production indicators
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "prod-key-12345")
    monkeypatch.delenv("DEBUG", raising=False)

    app = create_app()
    response = TestClient(app).get("/internal/resilience/environment")
    assert response.json()["environment"] == "production"
```

### Pattern 9: Environment Variable Removal

```python
def test_missing_api_key_behavior(monkeypatch):
    """Test behavior when required environment variables are missing."""

    # Remove required variable
    monkeypatch.delenv("API_KEY", raising=False)

    # Should raise ConfigurationError
    with pytest.raises(ConfigurationError) as exc_info:
        app = create_app()

    assert "API_KEY" in str(exc_info.value)
    assert "required" in str(exc_info.value).lower()
```

### Pattern 10: Environment Cleanup in Tests

```python
def test_environment_isolation(monkeypatch):
    """Test that environment changes don't affect other tests."""

    # Set specific environment for this test
    monkeypatch.setenv("CUSTOM_VAR", "test-value")

    app = create_app()
    client = TestClient(app)

    # Test with custom environment
    response = client.get("/v1/config")
    assert response.json()["custom_var"] == "test-value"

    # monkeypatch automatically cleans up after test
    # No manual cleanup needed!
```

---

## Authentication Testing Patterns

### Pattern 11: Multiple Authentication States

```python
# Authenticated client fixture
@pytest.fixture
def authenticated_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "valid-test-key-12345")

    app = create_app()
    # Add authentication headers
    client = TestClient(app)
    client.headers.update({
        "Authorization": "Bearer valid-test-key-12345",
        "Content-Type": "application/json"
    })
    return client

# Unauthenticated client fixture
@pytest.fixture
def unauthenticated_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "valid-test-key-12345")  # App needs this for startup

    app = create_app()
    # No authentication headers added
    return TestClient(app)

# Invalid authentication client fixture
@pytest.fixture
def invalid_auth_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "valid-test-key-12345")

    app = create_app()
    client = TestClient(app)
    client.headers.update({
        "Authorization": "Bearer invalid-key-99999",
        "Content-Type": "application/json"
    })
    return client
```

### Pattern 12: Authentication Testing

```python
def test_endpoint_authentication(authenticated_client, unauthenticated_client, invalid_auth_client):
    """Test that endpoints properly enforce authentication."""

    # Test unauthenticated request fails
    response = unauthenticated_client.get("/v1/protected")
    assert response.status_code == 401

    # Test invalid authentication fails
    response = invalid_auth_client.get("/v1/protected")
    assert response.status_code == 401

    # Test authenticated request succeeds
    response = authenticated_client.get("/v1/protected")
    assert response.status_code == 200
```

---

## Service Factory Patterns

### Pattern 13: Service with Pre-Configured Dependencies

```python
@pytest.fixture
async def text_processor_with_controlled_ai(settings):
    """TextProcessorService with fully controlled AI behavior."""

    with patch("app.services.text_processor.Agent") as mock_class:
        # Create configurable mock
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Create service with mock already in place
        service = TextProcessorService(settings=settings)

        # Provide mock instance for test configuration
        service.ai_mock = mock_instance  # Allow tests to configure behavior

        yield service

async def test_text_processing_success(text_processor_with_controlled_ai):
    """Test successful text processing with controlled AI."""

    # Configure AI response
    text_processor_with_controlled_ai.ai_mock.run.return_value = AsyncMock(
        output="Processed text successfully"
    )

    result = await text_processor_with_controlled_ai.process_text("test input")
    assert result.output == "Processed text successfully"

async def test_text_processing_failure(text_processor_with_controlled_ai):
    """Test text processing failure handling."""

    # Configure AI failure
    text_processor_with_controlled_ai.ai_mock.run.side_effect = ConnectionError("AI down")

    with pytest.raises(ConnectionError):
        await text_processor_with_controlled_ai.process_text("test input")
```

### Pattern 14: Service with Real Dependencies

```python
@pytest.fixture
async def service_with_real_dependencies():
    """Service with real infrastructure dependencies for integration testing."""

    # Use real cache and resilience orchestrator
    from app.infrastructure.cache.memory import InMemoryCache
    from app.infrastructure.resilience.orchestrator import AIServiceResilience
    from app.core.config import create_settings

    settings = create_settings()
    cache = InMemoryCache()
    orchestrator = AIServiceResilience(settings=settings)

    service = TextProcessorService(
        settings=settings,
        cache=cache,
        ai_resilience=orchestrator
    )

    try:
        yield service
    finally:
        # Cleanup real dependencies
        if hasattr(orchestrator, 'cleanup'):
            await orchestrator.cleanup()
```

---

## Common Violations and Solutions

### Violation 1: Environment Set After App Creation

**Problem**: Test modifies environment variables AFTER app/settings already created

**Example of Violation**:
```python
def test_broken_environment_detection(monkeypatch):
    app = create_app()  # App created with existing environment

    monkeypatch.setenv("ENVIRONMENT", "staging")  # TOO LATE!

    response = TestClient(app).get("/internal/resilience/environment")
    # App still reports old environment!
```

**Solution**:
```python
def test_correct_environment_detection(monkeypatch):
    # Set environment FIRST
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.setenv("DEPLOYMENT_STAGE", "staging")

    # Create app AFTER environment setup
    app = create_app()

    response = TestClient(app).get("/internal/resilience/environment")
    assert response.json()["environment"] == "staging"
```

### Violation 2: Mocks Applied After Service Initialization

**Problem**: Service creates real dependencies before mocks are applied

**Example of Violation**:
```python
@pytest.fixture
async def broken_service_with_mock():
    service = TextProcessorService()  # Real Agent created here

    with patch("app.services.text_processor.Agent"):
        yield service  # Service still uses real Agent!
```

**Solution**:
```python
@pytest.fixture
async def service_with_mock():
    # Apply mock BEFORE service creation
    with patch("app.services.text_processor.Agent"):
        service = TextProcessorService()  # Uses mock Agent
        yield service
```

### Violation 3: Only Authenticated Test Client Available

**Problem**: No way to test unauthenticated request scenarios

**Solution**: Create multiple client fixtures (see Pattern 11)

### Violation 4: Using os.environ Instead of monkeypatch

**Problem**: Direct environment modification causes test pollution

**Solution**: Always use monkeypatch.setenv() (see Pattern 2)

---

## Test Isolation Guarantees

### What These Patterns Guarantee

1. **Function Scope**: All fixtures use function scope for fresh instances
2. **App Factory Pattern**: Fresh FastAPI apps created per test
3. **Monkeypatch Cleanup**: Environment changes automatically restored
4. **Service Factories**: Fresh services with configured dependencies
5. **No Shared State**: Each test gets isolated infrastructure

### Verification Checklist

For each test, verify:

- [ ] Environment variables set with `monkeypatch.setenv()`
- [ ] Environment set BEFORE app/settings creation
- [ ] App created with `create_app()` (not module import)
- [ ] Mocks applied BEFORE service initialization
- [ ] Fixture scope is "function" (not module or session)
- [ ] No direct `os.environ` modifications
- [ ] No shared state between tests

---

## Choosing the Right Fixture

### Decision Guide

#### Use Factory Fixtures (text_processor_with_*) When:
- Testing AI service failure scenarios
- Testing circuit breaker activation
- Testing retry behavior with controlled failures
- Any test requiring specific mock behavior during service initialization
- Testing resilience patterns under controlled conditions

#### Use Regular Client Fixtures (resilience_test_client) When:
- Testing API endpoints with standard configuration
- Testing authentication patterns
- Testing configuration management
- General integration testing without specific service mocking
- Testing end-to-end request flows

#### Use Unauthenticated Client Fixtures When:
- Testing authentication requirements
- Testing authorization failures
- Testing security boundaries
- Validating endpoint protection
- Testing error handling for missing authentication

#### Use Production Client Fixtures When:
- Testing production-specific behavior
- Validating production configuration
- Testing performance with production settings
- End-to-end validation with production-like setup

### Fixture Selection Flowchart

```
Need to test AI service behavior?
├─ Yes → Use factory fixture (text_processor_with_*)
│   ├─ Need failures? → text_processor_with_failing_ai
│   ├─ Need retries? → text_processor_with_flaky_ai
│   └─ Need success? → text_processor_with_mock_ai
└─ No → Need authentication testing?
    ├─ Yes → Use auth fixtures (authenticated/unauthenticated)
    └─ No → Use standard client (resilience_test_client)
```

---

## Migration Checklist

### For Existing Tests

1. **Check Environment Variable Usage**:
   - [ ] Replace `os.environ` with `monkeypatch.setenv()`
   - [ ] Ensure environment set BEFORE app creation
   - [ ] Remove manual environment cleanup code

2. **Verify App Creation Pattern**:
   - [ ] Replace module-level app import with `create_app()`
   - [ ] Create app in fixture or test (not at module level)
   - [ ] Use function scope for fixtures

3. **Fix Service Mocking**:
   - [ ] Apply mocks BEFORE service creation
   - [ ] Use factory fixtures for complex mock scenarios
   - [ ] Avoid mocks applied after service initialization

4. **Add Authentication Variants**:
   - [ ] Create unauthenticated client fixture if needed
   - [ ] Create invalid auth client fixture if needed
   - [ ] Test both authenticated and unauthenticated scenarios

5. **Update Fixture Scope**:
   - [ ] Change module/session scope to function scope
   - [ ] Ensure fresh instances per test
   - [ ] Remove shared state between tests

### Verification Steps

1. **Run Tests in Random Order**:
   ```bash
   pytest --random-order -v
   ```

2. **Run Tests in Parallel**:
   ```bash
   pytest -n auto -v
   ```

3. **Check for Test Pollution**:
   ```bash
   pytest -v --tb=short
   ```

4. **Verify Environment Isolation**:
   - Run individual test: Should pass
   - Run full suite: All tests should pass
   - Run multiple times: Results should be consistent

---

## Conclusion

These patterns were developed through real-world experience fixing critical test failures. They ensure:

- **Reliable Tests**: No flaky behavior due to shared state
- **Proper Isolation**: Each test runs in completely isolated environment
- **Maintainable Code**: Clear patterns that are easy to follow
- **Comprehensive Coverage**: Ability to test all scenarios including failures

Following these patterns will prevent the issues identified in `TEST_FIXES.md` and ensure your resilience integration tests are reliable, maintainable, and comprehensive.

Remember: The order of operations matters more than the specific implementation. Environment → Settings → App → Service is the critical sequence that must be followed.