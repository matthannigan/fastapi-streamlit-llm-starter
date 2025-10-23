# Resilience Integration Test Suite

## Overview

This directory contains comprehensive integration tests for the resilience infrastructure. The test suite validates that resilience patterns work correctly with real dependencies, external services, and under various failure conditions.

## Purpose and Scope

### What This Test Suite Validates

1. **Real Resilience Behavior**: Tests use actual circuit breaker and retry libraries, not mocks
2. **Integration Points**: Validates seams between components (API → Orchestrator → Circuit Breaker → AI Service)
3. **Configuration Management**: Ensures environment detection and preset loading work end-to-end
4. **Failure Scenarios**: Tests real failure conditions and recovery patterns
5. **Performance Integration**: Validates that resilience patterns meet performance targets

### What This Test Suite Does NOT Cover

- **Unit Tests**: Individual component testing is handled by unit test suites
- **E2E Tests**: Full application testing with real external services is handled separately
- **Load Testing**: Performance under extreme load is handled by dedicated performance tests

## Architecture

### Test Organization

```
backend/tests/integration/resilience/
├── README.md                           # This file - test suite overview
├── TEST_PLAN.md                        # Comprehensive test plan with seam analysis
├── TEST_FIXES.md                       # Analysis of test issues and solutions
├── FIXTURE_PATTERNS.md                 # Comprehensive fixture patterns guide
├── conftest.py                         # Shared fixtures with App Factory Pattern
├── test_api_resilience_orchestrator_integration.py     # API → Resilience integration
├── test_config_environment_integration.py              # Configuration & environment detection
├── test_text_processing_resilience_integration.py     # Service → Resilience patterns
├── test_performance_benchmarks_integration.py          # Performance validation
├── test_config_security_integration.py                # Security & validation
└── test_library_integration.py                        # Third-party library integration
```

### Key Architectural Concepts

#### App Factory Pattern (Critical)
All tests use the App Factory Pattern to ensure proper test isolation:

```python
# ✅ CORRECT: Environment → Settings → App
@pytest.fixture
def test_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-key-12345")

    settings = create_settings()  # Picks up environment
    app = create_app(settings_obj=settings)  # Fresh app
    return TestClient(app)
```

#### High-Fidelity Testing
Tests use real infrastructure components rather than mocks:

- **Real Circuit Breaker Library**: Actual `circuitbreaker` library behavior
- **Real Retry Library**: Actual `tenacity` retry behavior
- **Real Configuration**: Actual settings and environment detection
- **Real Service Integration**: Actual TextProcessorService with resilience decorators

#### Service Factory Pattern
For complex mock scenarios, use factory fixtures that apply mocks before service initialization:

```python
@pytest.fixture
async def text_processor_with_failing_ai(settings):
    with patch("app.services.text_processor.Agent") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.run.side_effect = ConnectionError("AI down")
        mock_class.return_value = mock_instance

        service = TextProcessorService(settings=settings)  # Uses mock
        yield service
```

## Getting Started

### Prerequisites

1. **Virtual Environment**: Ensure `.venv` is activated in project root
2. **Dependencies**: All test dependencies installed via `make install`
3. **Environment**: Basic test environment configured automatically

### Running Tests

#### Quick Start
```bash
# From project root
make test-backend-infra-resilience

# From backend directory
../.venv/bin/python -m pytest tests/integration/resilience/ -v
```

#### Specific Test Categories
```bash
# API integration tests
pytest tests/integration/resilience/test_api_resilience_orchestrator_integration.py -v

# Configuration tests
pytest tests/integration/resilience/test_config_environment_integration.py -v

# Performance tests
pytest tests/integration/resilience/test_performance_benchmarks_integration.py -v
```

#### Running with Coverage
```bash
pytest tests/integration/resilience/ --cov=app.infrastructure.resilience --cov-report=term
```

### Common Issues and Solutions

#### Issue: Tests Fail with Environment Errors
**Solution**: Ensure you're using `monkeypatch.setenv()` not `os.environ`
```python
# ✅ Correct
def test_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")

# ❌ Wrong - causes test pollution
def test_environment():
    os.environ["ENVIRONMENT"] = "testing"
```

#### Issue: Tests Pass Individually but Fail in Suite
**Solution**: Check for shared state and use function scope fixtures
```python
# ✅ Correct: Function scope
@pytest.fixture(scope="function")
def test_client():
    return TestClient(create_app())

# ❌ Wrong: Module scope can cause shared state
@pytest.fixture(scope="module")
def test_client():
    return TestClient(create_app())
```

#### Issue: Mock Not Applied to Service
**Solution**: Use factory fixtures that apply mocks before service creation
```python
# ✅ Correct: Mock before service creation
@pytest.fixture
async def service_with_mock():
    with patch("app.services.text_processor.Agent"):
        service = TextProcessorService()  # Uses mock
        yield service

# ❌ Wrong: Mock after service creation
@pytest.fixture
async def service_with_mock():
    service = TextProcessorService()  # Real service created
    with patch("app.services.text_processor.Agent"):
        yield service  # Mock never applied
```

## Test Patterns

### Pattern 1: Basic API Integration
```python
def test_resilience_endpoint_returns_metrics(resilience_test_client):
    """Test that resilience endpoints return real metrics."""

    response = resilience_test_client.get("/internal/resilience/status")
    assert response.status_code == 200

    data = response.json()
    assert "circuit_breakers" in data
    assert "metrics" in data
```

### Pattern 2: Environment Configuration Testing
```python
def test_environment_detection_with_custom_env(monkeypatch):
    """Test environment detection with custom environment variables."""

    # Set environment before app creation
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "prod-key-12345")

    app = create_app()
    client = TestClient(app)

    response = client.get("/internal/resilience/environment")
    assert response.json()["environment"] == "production"
```

### Pattern 3: Failure Scenario Testing
```python
async def test_circuit_breaker_opens_on_failures(text_processor_with_failing_ai):
    """Test that circuit breaker opens on repeated failures."""

    # Trigger multiple failures
    for attempt in range(5):
        with pytest.raises(ConnectionError):
            await text_processor_with_failing_ai.process_text("test")

    # Verify circuit breaker opened
    assert text_processor_with_failing_ai.resilience.circuit_breaker.is_open()
```

### Pattern 4: Performance Validation
```python
def test_configuration_loading_performance(real_performance_benchmarker):
    """Test that configuration loading meets performance targets."""

    with real_performance_benchmarker.measure_operation("config_load") as metrics:
        # Load configuration
        from app.infrastructure.resilience.config_presets import PresetManager
        manager = PresetManager()
        presets = manager.load_all_presets()

    # Validate performance
    assert metrics.duration_ms < 10.0  # Should load in <10ms
    assert len(presets) > 0
```

### Pattern 5: Authentication Testing
```python
def test_authentication_required(resilience_test_client, unauthenticated_resilience_client):
    """Test that resilience endpoints require authentication."""

    # Authenticated request should work
    response = resilience_test_client.get("/internal/resilience/status")
    assert response.status_code == 200

    # Unauthenticated request should fail
    response = unauthenticated_resilience_client.get("/internal/resilience/status")
    assert response.status_code == 401
```

## Fixtures Guide

### Core Fixtures

#### `resilience_test_client`
**Purpose**: Standard HTTP client with resilience configuration
**Use When**: Testing API endpoints with normal configuration
**Example**:
```python
def test_api_endpoint(resilience_test_client):
    response = resilience_test_client.get("/internal/resilience/status")
    assert response.status_code == 200
```

#### `resilience_test_settings`
**Purpose**: Real Settings instance with test configuration
**Use When**: Tests need access to settings object
**Example**:
```python
def test_settings_configuration(resilience_test_settings):
    assert resilience_test_settings.resilience_preset == "simple"
    assert resilience_test_settings.environment == "testing"
```

#### `ai_resilience_orchestrator`
**Purpose**: Real resilience orchestrator for integration testing
**Use When**: Testing resilience behavior directly
**Example**:
```python
async def test_resilience_orchestrator(ai_resilience_orchestrator):
    # Test orchestrator functionality
    breaker = ai_resilience_orchestrator.get_or_create_circuit_breaker("test_operation")
    assert breaker is not None
```

### Service Factory Fixtures

#### `text_processor_with_mock_ai`
**Purpose**: TextProcessorService with mock AI agent
**Use When**: Testing service behavior with controlled AI responses
**Example**:
```python
async def test_text_processing_success(text_processor_with_mock_ai):
    result = await text_processor_with_mock_ai.process_text("test")
    assert result.output == "AI response generated successfully"
```

#### `text_processor_with_failing_ai`
**Purpose**: TextProcessorService with failing AI agent
**Use When**: Testing circuit breaker activation and failure handling
**Example**:
```python
async def test_circuit_breaker_activation(text_processor_with_failing_ai):
    with pytest.raises(ConnectionError):
        await text_processor_with_failing_ai.process_text("test")

    assert text_processor_with_failing_ai.resilience.circuit_breaker.is_open()
```

#### `text_processor_with_flaky_ai`
**Purpose**: TextProcessorService with intermittently failing AI agent
**Use When**: Testing retry behavior and recovery patterns
**Example**:
```python
async def test_retry_behavior(text_processor_with_flaky_ai):
    # Service fails twice, then succeeds
    result = await text_processor_with_flaky_ai.process_text("test")
    assert result.output == "Success after retries"
```

### Authentication Fixtures

#### `unauthenticated_resilience_client`
**Purpose**: Test client without authentication headers
**Use When**: Testing authentication failure scenarios
**Example**:
```python
def test_unauthenticated_access_fails(unauthenticated_resilience_client):
    response = unauthenticated_resilience_client.get("/internal/resilience/status")
    assert response.status_code == 401
```

#### `resilience_invalid_api_key_headers`
**Purpose**: Headers with invalid API key
**Use When**: Testing invalid authentication scenarios
**Example**:
```python
def test_invalid_api_key_fails(resilience_test_client, resilience_invalid_api_key_headers):
    response = resilience_test_client.get("/internal/resilience/status",
                                        headers=resilience_invalid_api_key_headers)
    assert response.status_code == 401
```

## Best Practices

### 1. Always Use App Factory Pattern
```python
# ✅ Correct
@pytest.fixture
def test_client(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    app = create_app()
    return TestClient(app)

# ❌ Wrong
from app.main import app  # Module-level import
test_client = TestClient(app)
```

### 2. Use monkeypatch for Environment Variables
```python
# ✅ Correct
def test_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")

# ❌ Wrong
import os
def test_environment():
    os.environ["ENVIRONMENT"] = "production"
```

### 3. Apply Mocks Before Service Creation
```python
# ✅ Correct
@pytest.fixture
async def service_with_mock():
    with patch("app.services.text_processor.Agent"):
        service = TextProcessorService()
        yield service

# ❌ Wrong
@pytest.fixture
async def service_with_mock():
    service = TextProcessorService()
    with patch("app.services.text_processor.Agent"):
        yield service
```

### 4. Use Function Scope for Fixtures
```python
# ✅ Correct
@pytest.fixture(scope="function")
def test_client():
    return TestClient(create_app())

# ❌ Wrong (can cause shared state)
@pytest.fixture(scope="module")
def test_client():
    return TestClient(create_app())
```

### 5. Test Observable Behavior
```python
# ✅ Correct: Test API response
def test_api_returns_401_for_unauthenticated(unauthenticated_client):
    response = unauthenticated_client.get("/internal/resilience/status")
    assert response.status_code == 401

# ❌ Wrong: Test internal state
def test_circuit_breaker_state(service):
    assert service.circuit_breaker.state == "closed"  # Implementation detail
```

## Troubleshooting

### Common Test Failures

#### "Environment not detected correctly"
**Cause**: Environment set after app creation
**Solution**: Set environment variables BEFORE creating app
```python
def test_environment_detection(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")  # Set FIRST
    app = create_app()  # Create app AFTER
```

#### "Mock not applied to service"
**Cause**: Mock applied after service initialization
**Solution**: Use factory fixtures that apply mocks before service creation
```python
@pytest.fixture
async def service_with_mock():
    with patch("app.services.text_processor.Agent"):  # Apply FIRST
        service = TextProcessorService()  # Create service AFTER
        yield service
```

#### "Tests pass individually but fail in suite"
**Cause**: Shared state between tests
**Solution**: Use function scope fixtures and proper cleanup
```python
@pytest.fixture(scope="function")  # Ensure function scope
def isolated_client():
    return TestClient(create_app())
```

#### "Authentication test fails unexpectedly"
**Cause**: Using wrong client fixture
**Solution**: Use appropriate client fixture for test scenario
```python
def test_auth_failure(unauthenticated_client):  # Use unauthenticated fixture
    response = unauthenticated_client.get("/protected")
    assert response.status_code == 401
```

### Debugging Tips

1. **Check Fixture Order**: Ensure environment is set before app creation
2. **Verify Mock Application**: Ensure mocks are applied before service initialization
3. **Use Function Scope**: Avoid shared state between tests
4. **Check Import Order**: Import app factories, not module-level apps
5. **Validate Environment**: Use monkeypatch, not direct environment modification

## Contributing

### Adding New Tests

1. **Follow App Factory Pattern**: Always use `create_app()` in fixtures
2. **Use Proper Fixtures**: Choose appropriate fixtures for test scenario
3. **Test Observable Behavior**: Focus on external behavior, not internal state
4. **Include Documentation**: Add docstrings explaining test purpose and business impact
5. **Update Documentation**: Update TEST_PLAN.md if adding new test categories

### Test Review Checklist

- [ ] Uses `monkeypatch.setenv()` for environment variables
- [ ] Sets environment BEFORE app creation
- [ ] Uses function scope for fixtures
- [ ] Tests observable behavior, not implementation
- [ ] Has clear docstring with business impact
- [ ] Follows existing patterns in the codebase

## References

- **Comprehensive Guide**: `FIXTURE_PATTERNS.md` - Detailed fixture patterns
- **Issue Analysis**: `TEST_FIXES.md` - Analysis of common test issues
- **Test Plan**: `TEST_PLAN.md` - Comprehensive test plan and seam analysis
- **App Factory Pattern**: `backend/CLAUDE.md` - App Factory Pattern guide
- **Integration Testing**: `docs/guides/testing/TESTING.md` - General integration testing guidance