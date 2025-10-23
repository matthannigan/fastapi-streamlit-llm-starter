"""
Integration test fixtures for resilience testing.

This module provides fixtures for testing resilience infrastructure integration with
AI services, cache systems, and circuit breakers. All fixtures follow the App Factory Pattern
for proper test isolation and use high-fidelity fakes for infrastructure dependencies.

Key Fixtures:
    - resilience_test_client: HTTP client with isolated app configured for resilience testing
    - resilience_test_settings: Real Settings with resilience test configuration
    - ai_resilience_orchestrator: Real AIServiceResilience for integration testing
    - preset_manager_with_env_detection: Real PresetManager with environment detection
    - real_text_processor_service: Real TextProcessorService with resilience integration (legacy)
    - text_processor_with_mock_ai: TextProcessorService with mock AI agent (recommended)
    - text_processor_with_failing_ai: TextProcessorService with failing AI agent
    - text_processor_with_flaky_ai: TextProcessorService with flaky AI agent
    - mock_ai_service: Mock AI service for testing resilience under failures
    - real_performance_benchmarker: Real PerformanceBenchmarker for SLA validation

Shared Fixtures (from backend/tests/integration/conftest.py):
    - fakeredis_client: In-memory Redis simulation
    - authenticated_headers: Valid API authentication
    - integration_client: Pre-configured test client

Usage:
    Test files in this directory automatically have access to all fixtures
    defined here and in parent conftest.py files.

    ```python
    def test_circuit_breaker_integration(resilience_test_client, ai_resilience_orchestrator):
        response = resilience_test_client.post("/internal/resilience/test")
        assert response.status_code == 200
    ```

Critical Patterns:
    - Always use monkeypatch.setenv() for environment variables
    - Set environment BEFORE creating app/settings
    - Use function scope for test isolation
    - Use high-fidelity fakes (fakeredis) over mocks
    - Test real infrastructure behavior, not mocks

Factory Fixture Pattern (Solves Timing Issues):
    - Use text_processor_with_* fixtures for proper AI service mocking
    - These fixtures apply mocks BEFORE service initialization (solves timing issues)
    - Avoid legacy real_text_processor_service for AI service testing
    - Factory pattern ensures mocks are in place when service creates Agent instance

Fixture Timing Solutions:
    - OLD: real_text_processor_service + mock_ai_service (timing issue - mocks applied after service init)
    - NEW: text_processor_with_mock_ai (timing fixed - mocks applied during service init)
    - See TEST_FIXES.md "Pattern 2: Fixture Timing Issues" for details

See Also:
    - backend/CLAUDE.md - App Factory Pattern guide
    - docs/guides/testing/INTEGRATION_TESTS.md - Integration testing philosophy
    - backend/tests/integration/README.md - Integration test patterns
    - backend/tests/integration/resilience/FIXTURE_PATTERNS.md - Comprehensive fixture patterns guide
    - backend/tests/integration/resilience/TEST_FIXES.md - Pattern violations and solutions

===============================================================================
## APP FACTORY PATTERN COMPLIANCE (CRITICAL)

This conftest.py demonstrates PROPER App Factory Pattern usage. These patterns
solve the critical violations identified in TEST_FIXES.md and ensure reliable,
isolated tests.

## PATTERN 1: Environment Setup → Settings Creation → App Creation

### ✅ CORRECT: Environment Set Before App Creation
```python
@pytest.fixture
def correct_test_client(monkeypatch):
    # Step 1: Set environment variables FIRST
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-key-12345")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")

    # Step 2: Create settings AFTER environment is set
    settings = create_settings()  # Picks up environment variables

    # Step 3: Create app WITH the settings
    app = create_app(settings_obj=settings)
    return TestClient(app)
```

### ❌ VIOLATION: Environment Set After App Creation (CRITICAL BUG)
```python
# NEVER DO THIS - This was Issue #1 in TEST_FIXES.md
@pytest.fixture
def broken_test_client(monkeypatch):
    # WRONG: Create app with current environment
    app = create_app()  # Uses existing environment

    # WRONG: Set environment AFTER app already created
    monkeypatch.setenv("ENVIRONMENT", "staging")  # Too late! App won't see this

    return TestClient(app)  # App has wrong configuration
```

## PATTERN 2: Fixture Timing for Service Mocking

### ✅ CORRECT: Mocks Applied Before Service Initialization
```python
# Use factory fixtures that create services WITH mocks already in place
@pytest.fixture
async def text_processor_with_mock_ai(settings):
    # Apply mock BEFORE service creation
    with patch("app.services.text_processor.Agent") as mock_class:
        # Configure mock
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Create service WITH mock already active
        service = TextProcessorService(settings=settings)
        yield service  # Service uses mock during __init__
```

### ❌ VIOLATION: Mocks Applied After Service Initialization
```python
# NEVER DO THIS - This caused Issues #3-#8 in TEST_FIXES.md
@pytest.fixture
async def broken_text_processor(settings):
    # WRONG: Create service with real Agent
    service = TextProcessorService(settings=settings)  # Agent created here

    # Mock applied AFTER service already has Agent instance
    # Service won't use the mock!
    with patch("app.services.text_processor.Agent"):
        yield service  # Too late!
```

## PATTERN 3: Environment Variable Testing (MANDATORY)

### ✅ CORRECT: Always Use monkeypatch.setenv()
```python
def test_environment_configuration(monkeypatch):
    # ✅ Use monkeypatch for ALL environment variable modifications
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-prod-key")

    # Create app AFTER environment setup
    app = create_app()
    client = TestClient(app)

    # Test with correct configuration
    response = client.get("/v1/health")
    assert response.status_code == 200
```

### ❌ VIOLATION: Never Use os.environ Directly
```python
# NEVER DO THIS - Causes permanent test pollution
import os

def test_broken_environment():
    os.environ["ENVIRONMENT"] = "production"  # Pollutes ALL subsequent tests!
    # This change persists and causes flaky tests
```

## PATTERN 4: Authentication Testing Variants

### ✅ CORRECT: Multiple Client Fixtures for Different Auth States
```python
# For testing authenticated requests
@pytest.fixture
def authenticated_client(monkeypatch):
    monkeypatch.setenv("API_KEY", "valid-key-12345")
    app = create_app()
    return TestClient(app)

# For testing unauthenticated requests
@pytest.fixture
def unauthenticated_client(monkeypatch):
    monkeypatch.setenv("API_KEY", "valid-key-12345")  # App needs key for startup
    app = create_app()
    return TestClient(app)  # No auth headers auto-added

def test_authentication_required(authenticated_client, unauthenticated_client):
    # Test unauthenticated request fails
    response = unauthenticated_client.get("/v1/protected")
    assert response.status_code == 401

    # Test authenticated request succeeds
    response = authenticated_client.get("/v1/protected")
    assert response.status_code == 200
```

## PATTERN 5: Complex Service Factory Fixtures

### ✅ CORRECT: Service Factories with Pre-Configured Dependencies
```python
@pytest.fixture
async def service_with_failing_dependency(settings):
    # Apply failing mock BEFORE service creation
    with patch("app.external.Service") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.run.side_effect = ConnectionError("Service down")
        mock_class.return_value = mock_instance

        # Service picks up failing dependency during initialization
        service = MyService(settings=settings)
        yield service  # Service has failing dependency from the start

async def test_circuit_breaker_activation(service_with_failing_dependency):
    # Service already has failing dependency configured
    for attempt in range(5):
        with pytest.raises(ConnectionError):
            await service.do_operation()

    # Verify circuit breaker opened due to failures
    assert service.circuit_breaker.is_open()
```

## COMMON VIOLATIONS AND SOLUTIONS

### Violation 1: Setting Environment After App Creation
**Issue**: Test modifies environment variables AFTER app/settings already created
**Solution**: Always follow environment → settings → app order
**Reference**: TEST_FIXES.md Issue #1 (Blocker)

### Violation 2: Mocks Applied After Service Initialization
**Issue**: Service creates real dependencies before mocks are applied
**Solution**: Use factory fixtures that apply mocks before service creation
**Reference**: TEST_FIXES.md Issues #3-#8 (Critical)

### Violation 3: Only Authenticated Test Client Available
**Issue**: No way to test unauthenticated request scenarios
**Solution**: Create multiple client fixtures for different auth states
**Reference**: TEST_FIXES.md Issue #2 (Critical)

### Violation 4: Using os.environ Instead of monkeypatch
**Issue**: Direct environment modification causes test pollution
**Solution**: ALWAYS use monkeypatch.setenv() for environment variables
**Reference**: backend/CLAUDE.md "Environment Variable Testing Patterns"

## FIXTURE CHOICE GUIDE

### When to Use Factory Fixtures (text_processor_with_*)
- Testing AI service failure scenarios
- Testing circuit breaker activation
- Testing retry behavior with controlled failures
- Any test requiring specific mock behavior during service initialization

### When to Use Regular Client Fixtures (resilience_test_client)
- Testing API endpoints with standard configuration
- Testing authentication patterns
- Testing configuration management
- General integration testing without specific service mocking

### When to Use Unauthenticated Client Fixtures
- Testing authentication requirements
- Testing authorization failures
- Testing security boundaries
- Validating endpoint protection

## ISOLATION GUARANTEES

This conftest.py provides complete test isolation through:

1. **Function Scope**: All fixtures use function scope for fresh instances
2. **App Factory Pattern**: Fresh FastAPI apps created per test
3. **Monkeypatch Cleanup**: Environment changes automatically restored
4. **Service Factories**: Fresh services with configured dependencies
5. **No Shared State**: Each test gets isolated infrastructure

These patterns eliminate the flaky tests caused by shared state and timing issues
identified in TEST_FIXES.md.

===============================================================================
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Generator, AsyncGenerator

from app.main import create_app
from app.core.config import create_settings
from app.core.config import Settings


# =============================================================================
# App Factory Pattern Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def resilience_test_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    """
    Real Settings instance for resilience integration tests.

    Provides actual Settings object with resilience-appropriate configuration
    that can be used to initialize services and verify resilience behavior.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        Settings: Fresh settings instance from current environment

    Note:
        - Uses factory pattern to pick up current environment
        - Modify via monkeypatch BEFORE calling this fixture
        - Settings validation rules are fully applied
        - Resilience presets configured for testing scenarios
    """
    # Set resilience test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-resilience-key-12345")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")
    monkeypatch.setenv("CACHE_PRESET", "development")

    # AI service configuration for testing
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key-for-resilience")

    # Create fresh settings from current environment
    return create_settings()


@pytest.fixture(scope="function")
def resilience_test_client(monkeypatch: pytest.MonkeyPatch, resilience_test_settings: Settings) -> TestClient:
    """
    Test client for resilience integration tests with isolated app instance.

    Uses App Factory Pattern to create fresh FastAPI app that picks up
    current environment variables set via monkeypatch.

    Args:
        monkeypatch: Pytest fixture for environment configuration
        resilience_test_settings: Real Settings with resilience configuration

    Returns:
        TestClient: HTTP client with fresh app instance

    Note:
        - Environment must be set BEFORE calling this fixture
        - Each test gets completely isolated app instance
        - Settings are loaded fresh from current environment
        - Resilience features are enabled for testing
    """
    # Set resilience-specific environment
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-resilience-key-12345")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")

    # Create fresh app AFTER environment is configured
    app = create_app(settings_obj=resilience_test_settings)
    return TestClient(app)


@pytest.fixture(scope="function")
def resilience_production_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client with production resilience configuration.

    Creates isolated app with production resilience settings for testing
    production-grade resilience behavior.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client configured for production resilience testing
    """
    # Set production environment
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-prod-resilience-key")
    monkeypatch.setenv("RESILIENCE_PRESET", "production")
    monkeypatch.setenv("CACHE_PRESET", "production")

    # Create app with production settings
    app = create_app()
    return TestClient(app)


@pytest.fixture(scope="function")
def unauthenticated_resilience_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client for resilience integration tests WITHOUT API authentication in headers.

    Creates isolated FastAPI app with API key configured in environment but
    TestClient that does NOT automatically include authentication headers,
    enabling testing of authentication failure scenarios.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client without automatic auth headers for testing auth failures

    Note:
        - Environment has API key configured for app startup
        - TestClient does NOT automatically include auth headers
        - Each test gets completely isolated app instance
        - Resilience features are enabled for testing
        - Use this fixture to test that endpoints properly reject unauthenticated requests
    """
    # Set resilience-specific environment with API key for app startup
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-resilience-unauth-key-54321")  # Valid for startup
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")
    # Force authentication requirement even in testing environment
    monkeypatch.setenv("ENFORCE_AUTH", "true")

    # Create fresh app AFTER environment is configured
    app = create_app()

    # Create TestClient without default headers - this will NOT automatically include auth
    return TestClient(app)


@pytest.fixture
def resilience_invalid_api_key_headers() -> Dict[str, str]:
    """
    Headers with invalid API key for resilience authentication testing.

    Returns:
        dict: HTTP headers with clearly invalid authentication

    Note:
        - Uses invalid API key that will fail authentication
        - Includes headers required for resilience endpoints
        - Tests authentication failure scenarios
    """
    return {
        "Authorization": "Bearer invalid-resilience-api-key-99999",
        "Content-Type": "application/json",
        "X-Test-Scenario": "resilience-auth-testing"
    }


@pytest.fixture
def resilience_missing_auth_headers() -> Dict[str, str]:
    """
    Headers without any authentication for resilience testing.

    Returns:
        dict: HTTP headers without authentication for testing missing auth

    Note:
        - No Authorization header included
        - Includes Content-Type for proper request formatting
        - Tests missing authentication scenarios
    """
    return {
        "Content-Type": "application/json",
        "X-Test-Scenario": "resilience-missing-auth"
    }


# =============================================================================
# High-Fidelity Infrastructure Fixtures
# =============================================================================

@pytest.fixture
async def ai_resilience_orchestrator(resilience_test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    Real AIServiceResilience for integration testing.

    Provides actual resilience orchestrator implementation with real configuration,
    enabling realistic integration testing of AI service resilience patterns.

    Args:
        resilience_test_settings: Real Settings with test configuration

    Yields:
        AIServiceResilience: Fully initialized resilience orchestrator

    Note:
        - Uses real resilience orchestrator implementation (not mocked)
        - Configuration from real Settings object
        - Tests actual resilience behavior, not mocks
        - Cleanup happens automatically after test
    """
    from app.infrastructure.resilience.orchestrator import AIServiceResilience

    # Initialize orchestrator with real settings
    orchestrator = AIServiceResilience(settings=resilience_test_settings)

    yield orchestrator

    # Cleanup after test
    if hasattr(orchestrator, "reset"):
        await orchestrator.reset()
    if hasattr(orchestrator, "cleanup"):
        await orchestrator.cleanup()


@pytest.fixture
def preset_manager_with_env_detection() -> Any:
    """
    Real PresetManager with environment detection for integration testing.

    Provides actual PresetManager implementation to test real preset loading,
    environment detection, and configuration validation behavior.

    Returns:
        PresetManager: Configured preset manager with environment detection

    Note:
        - Uses real PresetManager implementation (not mocked)
        - Tests actual preset management behavior
        - Environment detection is fully functional
    """
    from app.infrastructure.resilience.config_presets import PresetManager

    return PresetManager()


@pytest.fixture
def real_performance_benchmarker() -> Any:
    """
    Real ConfigurationPerformanceBenchmark for SLA validation integration testing.

    Provides actual ConfigurationPerformanceBenchmark implementation to test real
    performance monitoring, benchmark collection, and SLA validation.

    Returns:
        ConfigurationPerformanceBenchmark: Configured performance benchmarker

    Note:
        - Uses real performance benchmarker implementation
        - Tests actual performance monitoring behavior
        - Benchmark collection and SLA validation are functional
    """
    from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

    return ConfigurationPerformanceBenchmark()


@pytest.fixture
def config_validator_with_rate_limiting() -> Any:
    """
    ResilienceConfigValidator with real rate limiting for integration testing.

    Provides actual configuration validator with rate limiting enabled to test
    real validation behavior, rate limiting, and configuration management.

    Returns:
        ResilienceConfigValidator: Configured validator with rate limiting

    Note:
        - Uses real validator implementation (not mocked)
        - Rate limiting is fully functional (built into the validator)
        - Tests actual configuration validation behavior
    """
    from app.infrastructure.resilience.config_validator import ResilienceConfigValidator  # type: ignore

    return ResilienceConfigValidator()


@pytest.fixture
def concurrent_executor() -> Generator[ThreadPoolExecutor, None, None]:
    """
    Concurrent execution helper for load testing integration scenarios.

    Provides ThreadPoolExecutor for testing concurrent resilience patterns,
    load balancing, and performance under concurrent load.

    Yields:
        ThreadPoolExecutor: Configured executor for concurrent testing

    Note:
        - Executor is configured with reasonable defaults for testing
        - Automatic shutdown after test prevents resource leaks
        - Enables testing of concurrent resilience patterns
    """
    executor = ThreadPoolExecutor(max_workers=10)

    yield executor

    # Ensure proper shutdown
    executor.shutdown(wait=True)


# =============================================================================
# Service Factory Fixtures with Pre-Configured Mocks
# =============================================================================

@pytest.fixture
async def text_processor_with_mock_ai(resilience_test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    TextProcessorService factory fixture with standard mock AI agent pre-configured.

    This fixture solves the fixture timing issue by creating the TextProcessorService
    with the AI mock already applied during service initialization, ensuring the mock
    is in place BEFORE the service creates its Agent instance.

    IMPROVED (Issues #9-#10): Enhanced mock with operation-specific responses to support
    comprehensive testing including sentiment analysis performance validation.

    Args:
        resilience_test_settings: Real Settings with test configuration

    Yields:
        TextProcessorService: Service instance with mock AI agent configured

    Usage:
        ```python
        async def test_with_mock_ai(text_processor_with_mock_ai):
            # Service already has mock AI configured
            response = await text_processor_with_mock_ai.process_text(request)
            assert response.result is not None
        ```

    Mock Behavior (Issues #9-#10 Fix):
        - Default response: "AI response generated successfully" (for summarize, etc.)
        - Sentiment analysis: Returns JSON with sentiment, confidence, explanation
        - Operation detection: Mock analyzes prompt content for "sentiment" keywords
        - Proper JSON structure: Ensures SentimentResult validation passes

    Note:
        - Mock AI agent returns successful responses by default
        - Solves "Pattern 2: Fixture Timing Issues" from TEST_FIXES.md
        - Mock is applied during service __init__, not after
        - Uses real resilience orchestrator and memory cache
        - Enhanced to support performance testing across different operation types
    """
    from app.services.text_processor import TextProcessorService
    from app.infrastructure.cache.memory import InMemoryCache

    # Apply mock BEFORE service creation
    with patch("app.services.text_processor.Agent") as mock_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Set default successful behavior with operation-specific responses
        # Define operation-specific responses based on the prompt
        def mock_run_side_effect(prompt, **kwargs):
            response = AsyncMock()
            # Check if this is a sentiment analysis request
            if "sentiment" in str(prompt).lower() or "feeling" in str(prompt).lower():
                response.output = '{"sentiment": "positive", "confidence": 0.85, "explanation": "Text contains positive language and optimistic tone"}'
            else:
                response.output = "AI response generated successfully"
            return response

        mock_instance.run.side_effect = mock_run_side_effect
        mock_instance.is_available.return_value = True

        # Create resilience orchestrator and cache
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        cache = InMemoryCache()
        # Disable cache to force AI service calls
        cache.enabled = False
        ai_resilience = AIServiceResilience(settings=resilience_test_settings)

        # Create service WITH MOCK already in place
        service = TextProcessorService(
            settings=resilience_test_settings,
            cache=cache,
            ai_resilience=ai_resilience
        )

        # Initialize service
        if hasattr(service, "initialize"):
            await service.initialize()

        yield service

        # Cleanup
        if hasattr(service, "cleanup"):
            await service.cleanup()
        if hasattr(ai_resilience, "cleanup"):
            await ai_resilience.cleanup()


@pytest.fixture
async def text_processor_with_failing_ai(resilience_test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    TextProcessorService factory fixture with failing mock AI agent pre-configured.

    This fixture creates a TextProcessorService with an AI mock that consistently
    fails, enabling testing of circuit breaker activation, retry patterns, and
    graceful degradation behavior.

    Args:
        resilience_test_settings: Real Settings with test configuration

    Yields:
        TextProcessorService: Service instance with failing AI agent configured

    Usage:
        ```python
        async def test_circuit_breaker_activation(text_processor_with_failing_ai):
            # AI service will consistently fail
            with pytest.raises(ConnectionError):
                await text_processor_with_failing_ai.process_text(request)

            # Verify circuit breaker opened
            assert service.resilience.circuit_breaker.is_open()
        ```

    Note:
        - AI mock raises ConnectionError consistently
        - Tests failure handling and recovery patterns
        - Useful for testing circuit breaker and retry logic
        - Mock applied during service initialization
    """
    from app.services.text_processor import TextProcessorService
    from app.infrastructure.cache.memory import InMemoryCache

    # Apply mock BEFORE service creation
    with patch("app.services.text_processor.Agent") as mock_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Configure consistent failures
        mock_instance.run.side_effect = ConnectionError("AI service unavailable")
        mock_instance.is_available.return_value = False

        # Create resilience orchestrator and cache
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        cache = InMemoryCache()
        ai_resilience = AIServiceResilience(settings=resilience_test_settings)

        # Create service WITH FAILING MOCK already in place
        service = TextProcessorService(
            settings=resilience_test_settings,
            cache=cache,
            ai_resilience=ai_resilience
        )

        # Initialize service
        if hasattr(service, "initialize"):
            await service.initialize()

        yield service

        # Cleanup
        if hasattr(service, "cleanup"):
            await service.cleanup()
        if hasattr(ai_resilience, "cleanup"):
            await ai_resilience.cleanup()


@pytest.fixture
async def text_processor_with_flaky_ai(resilience_test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    TextProcessorService factory fixture with flaky mock AI agent pre-configured.

    This fixture creates a TextProcessorService with an AI mock that fails intermittently,
    enabling testing of retry patterns, circuit breaker recovery, and resilience under
    unstable conditions.

    Args:
        resilience_test_settings: Real Settings with test configuration

    Yields:
        TextProcessorService: Service instance with flaky AI agent configured

    Usage:
        ```python
        async def test_retry_with_flaky_service(text_processor_with_flaky_ai):
            # Service fails 2 times, then succeeds
            response = await text_processor_with_flaky_ai.process_text(request)
            assert response.result is not None

            # Verify retries happened
            assert service.resilience.metrics["retries"] > 0
        ```

    Note:
        - Default behavior: fails 2 times, then succeeds
        - Override side_effect for custom failure patterns
        - Tests retry logic and circuit breaker recovery
        - Mock applied during service initialization
    """
    from app.services.text_processor import TextProcessorService
    from app.infrastructure.cache.memory import InMemoryCache

    # Apply mock BEFORE service creation
    with patch("app.services.text_processor.Agent") as mock_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Configure intermittent failures (fail twice, then succeed)
        mock_response = AsyncMock()
        mock_response.output = "Success after retries"
        mock_instance.run.side_effect = [
            ConnectionError("Intermittent failure 1"),
            ConnectionError("Intermittent failure 2"),
            mock_response
        ]
        mock_instance.is_available.return_value = True

        # Create resilience orchestrator and cache
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        cache = InMemoryCache()
        ai_resilience = AIServiceResilience(settings=resilience_test_settings)

        # Create service WITH FLAKY MOCK already in place
        service = TextProcessorService(
            settings=resilience_test_settings,
            cache=cache,
            ai_resilience=ai_resilience
        )

        # Initialize service
        if hasattr(service, "initialize"):
            await service.initialize()

        yield service

        # Cleanup
        if hasattr(service, "cleanup"):
            await service.cleanup()
        if hasattr(ai_resilience, "cleanup"):
            await ai_resilience.cleanup()


# =============================================================================
# Service Fixtures with Real Dependencies (Legacy - Keep for compatibility)
# =============================================================================

@pytest.fixture
async def real_text_processor_service(ai_resilience_orchestrator: Any, resilience_test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    Real TextProcessorService with resilience integration for testing.

    Provides actual TextProcessorService implementation with real resilience
    orchestrator, enabling testing of complete service integration with resilience patterns.

    Args:
        ai_resilience_orchestrator: Real resilience orchestrator fixture
        resilience_test_settings: Real Settings with test configuration

    Yields:
        TextProcessorService: Fully initialized service with resilience integration

    Note:
        - Uses real TextProcessorService implementation (not mocked)
        - Resilience integration is fully functional
        - Tests actual service behavior with resilience patterns
        - Cleanup happens automatically after test

    DEPRECATED: Use factory fixtures (text_processor_with_mock_ai, etc.) for
    proper AI service mocking. This fixture has timing issues with mocks.
    """
    from app.services.text_processor import TextProcessorService

    # Import cache for service initialization
    from app.infrastructure.cache.memory import InMemoryCache

    # Initialize service with real resilience orchestrator and memory cache
    cache = InMemoryCache()
    service = TextProcessorService(
        settings=resilience_test_settings,
        cache=cache,
        ai_resilience=ai_resilience_orchestrator
    )

    # Perform any required initialization
    if hasattr(service, "initialize"):
        await service.initialize()

    yield service

    # Cleanup after test
    if hasattr(service, "cleanup"):
        await service.cleanup()


# =============================================================================
# Mock Fixtures for External Dependencies
# =============================================================================

@pytest.fixture
def mock_ai_service() -> Generator[AsyncMock, None, None]:
    """
    Mock AI service for testing resilience under controlled failure conditions.

    Provides configurable mock AI service that can simulate various failure scenarios
    to test circuit breakers, retries, and graceful degradation patterns.

    Yields:
        AsyncMock: Configured mock AI service with default behavior

    Usage:
        ```python
        def test_circuit_breaker_with_failures(mock_ai_service):
            # Simulate AI service failures
            mock_ai_service.run.side_effect = ConnectionError("AI service down")

            # Test resilience behavior
            result = service.process_with_resilience()

            # Verify graceful degradation
            assert result is not None
            assert "fallback" in result.status
        ```

    Note:
        - Default behavior returns successful responses
        - Override side_effect or return_value in tests for specific scenarios
        - Mock is reset between tests (function scope)
        - Use AsyncMock for async AI service operations
    """
    with patch("app.services.text_processor.Agent") as mock_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Set default successful behavior
        # Create mock response object with .output attribute (as expected by TextProcessorService)
        mock_response = AsyncMock()
        mock_response.output = "AI response generated successfully"
        mock_instance.run.return_value = mock_response
        mock_instance.is_available.return_value = True

        yield mock_instance


@pytest.fixture
def failing_ai_service() -> Generator[AsyncMock, None, None]:
    """
    AI service mock that simulates consistent failures for resilience testing.

    Provides mock AI service that raises exceptions to test circuit breaker
    activation, retry patterns, and graceful degradation behavior.

    Yields:
        AsyncMock: Mock AI service configured to raise exceptions

    Usage:
        ```python
        def test_circuit_breaker_activation(failing_ai_service):
            # AI service will raise ConnectionError
            with pytest.raises(ConnectionError):
                service.call_ai_service()

            # Verify circuit breaker activated
            assert service.resilience.circuit_breaker.is_open()
        ```

    Note:
        - Configured to raise ConnectionError consistently
        - Tests failure handling and recovery patterns
        - Useful for testing circuit breaker and retry logic
    """
    with patch("app.services.text_processor.Agent") as mock_class:
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Configure consistent failures
        mock_instance.run.side_effect = ConnectionError("AI service unavailable")
        mock_instance.is_available.return_value = False

        yield mock_instance


@pytest.fixture
def flaky_ai_service() -> Generator[AsyncMock, None, None]:
    """
    AI service mock that simulates intermittent failures for resilience testing.

    Provides mock AI service that fails intermittently to test retry patterns,
    circuit breaker recovery, and resilience under unstable conditions.

    Yields:
        AsyncMock: Mock AI service configured for intermittent failures

    Usage:
        ```python
        def test_retry_with_flaky_service(flaky_ai_service):
            # Service fails 2 times, then succeeds
            flaky_ai_service.run.side_effect = [
                ConnectionError("First failure"),
                ConnectionError("Second failure"),
                "Success on third try"
            ]

            # Test retry logic
            result = service.process_with_retry()
            assert result == "Success on third try"
        ```

    Note:
        - Default behavior: fails 2 times, then succeeds
        - Override side_effect for custom failure patterns
        - Tests retry logic and circuit breaker recovery
    """
    with patch("app.services.text_processor.Agent") as mock_class:
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Configure intermittent failures (fail twice, then succeed)
        mock_response = AsyncMock()
        mock_response.output = "Success after retries"
        mock_instance.run.side_effect = [
            ConnectionError("Intermittent failure 1"),
            ConnectionError("Intermittent failure 2"),
            mock_response
        ]
        mock_instance.is_available.return_value = True

        yield mock_instance


# =============================================================================
# Test Data Fixtures for Resilience Testing
# =============================================================================

@pytest.fixture
def sample_resilience_test_data() -> Dict[str, Any]:
    """
    Sample test data for resilience integration testing scenarios.

    Provides realistic test data that represents typical inputs for testing
    resilience patterns with AI services and text processing.

    Returns:
        dict: Sample test data with various scenarios

    Note:
        - Data represents realistic AI service inputs
        - Includes edge cases for resilience testing
        - Modify in tests for specific scenarios
    """
    return {
        "simple_request": {
            "text": "This is a simple test request for AI processing.",
            "operation": "summarize",
            "expected_length": 50
        },
        "complex_request": {
            "text": "This is a much longer and more complex text that requires significant processing time and resources from the AI service. It contains multiple sentences and various linguistic patterns that might challenge the system.",
            "operation": "analyze",
            "expected_length": 200
        },
        "timeout_prone_request": {
            "text": "A" * 10000,  # Very long text that might cause timeouts
            "operation": "deep_analysis",
            "expected_length": 500
        },
        "edge_case_request": {
            "text": "",  # Empty text
            "operation": "summarize",
            "expected_length": 0
        }
    }


@pytest.fixture
def resilience_test_scenarios() -> Dict[str, Any]:
    """
    Predefined resilience test scenarios for integration testing.

    Provides common test scenarios that exercise different resilience patterns
    and failure modes to validate comprehensive resilience behavior.

    Returns:
        dict: Dictionary of test scenarios with configurations

    Usage:
        ```python
        def test_circuit_breaker_scenarios(resilience_test_scenarios):
            for scenario_name, config in resilience_test_scenarios.items():
                # Test each resilience scenario
                result = service.handle_request(config)
                assert result.status == config["expected_status"]
        ```
    """
    return {
        "circuit_breaker_open": {
            "failure_type": "connection_error",
            "expected_status": "degraded",
            "expected_behavior": "circuit_breaker_open"
        },
        "retry_success": {
            "failure_type": "temporary_failure",
            "expected_status": "success",
            "expected_behavior": "retry_success"
        },
        "timeout_handling": {
            "failure_type": "timeout",
            "expected_status": "timeout",
            "expected_behavior": "graceful_timeout"
        },
        "graceful_degradation": {
            "failure_type": "complete_failure",
            "expected_status": "fallback",
            "expected_behavior": "graceful_degradation"
        },
        "performance_degradation": {
            "failure_type": "slow_response",
            "expected_status": "slow_but_success",
            "expected_behavior": "performance_warning"
        }
    }


# =============================================================================
# Authentication Fixtures for Resilience Testing
# =============================================================================

@pytest.fixture
def resilience_auth_headers() -> Dict[str, str]:
    """
    Authentication headers specific to resilience testing scenarios.

    Returns:
        dict: HTTP headers with resilience-specific authentication

    Note:
        - Uses resilience-specific API key
        - Includes headers required for resilience endpoints
    """
    return {
        "Authorization": "Bearer test-resilience-key-12345",
        "Content-Type": "application/json",
        "X-Test-Scenario": "resilience-testing"
    }


@pytest.fixture
def resilience_admin_headers() -> Dict[str, str]:
    """
    Admin-level authentication headers for resilience management endpoints.

    Returns:
        dict: HTTP headers with admin authentication for resilience management

    Note:
        - Uses admin-level API key for resilience management
        - Includes headers required for administrative operations
    """
    return {
        "Authorization": "Bearer admin-resilience-key-67890",
        "Content-Type": "application/json",
        "X-Admin-Operation": "resilience-management"
    }
