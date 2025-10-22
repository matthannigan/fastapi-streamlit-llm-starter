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
    - real_text_processor_service: Real TextProcessorService with resilience integration
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

See Also:
    - backend/CLAUDE.md - App Factory Pattern guide
    - docs/guides/testing/INTEGRATION_TESTS.md - Integration testing philosophy
    - backend/tests/integration/README.md - Integration test patterns
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
    if hasattr(orchestrator, 'reset'):
        await orchestrator.reset()
    if hasattr(orchestrator, 'cleanup'):
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
# Service Fixtures with Real Dependencies
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
    if hasattr(service, 'initialize'):
        await service.initialize()

    yield service

    # Cleanup after test
    if hasattr(service, 'cleanup'):
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
    with patch('app.services.text_processor.Agent') as mock_class:
        # Create mock instance
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Set default successful behavior
        mock_instance.run.return_value = "AI response generated successfully"
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
    with patch('app.services.text_processor.Agent') as mock_class:
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
    with patch('app.services.text_processor.Agent') as mock_class:
        mock_instance = AsyncMock()
        mock_class.return_value = mock_instance

        # Configure intermittent failures (fail twice, then succeed)
        mock_instance.run.side_effect = [
            ConnectionError("Intermittent failure 1"),
            ConnectionError("Intermittent failure 2"),
            "Success after retries"
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