"""
Integration test fixtures for middleware testing.

This module provides fixtures for testing middleware integration with
dependencies including Redis (via fakeredis), rate limiting, compression,
security headers, and performance monitoring. All fixtures follow the
App Factory Pattern for proper test isolation.

Key Fixtures:
    - test_client: HTTP client with isolated app instance
    - test_settings: Real Settings with test configuration
    - client_minimal_middleware: Test client with selective middleware disabled
    - client_with_fakeredis_rate_limit: Test client with Redis-backed rate limiting
    - failing_redis_connection: Mock Redis failures for resilience testing
    - large_payload_generator: Generate large payloads for size limit testing
    - performance_monitor: Timing utility for performance validation

Shared Fixtures (from backend/tests/integration/conftest.py):
    - fakeredis_client: In-memory Redis simulation
    - authenticated_headers: Valid API authentication
    - integration_client: Pre-configured test client
    - async_integration_client: Async HTTP client
    - production_environment_integration: Production environment setup

Usage:
    Test files in this directory automatically have access to all fixtures
    defined here and in parent conftest.py files.

    ```python
    def test_middleware_integration(test_client, authenticated_headers):
        response = test_client.get("/v1/health", headers=authenticated_headers)
        assert response.status_code == 200
    ```

Critical Patterns:
    - Always use monkeypatch.setenv() for environment variables
    - Set environment BEFORE creating app/settings
    - Use function scope for test isolation
    - Use high-fidelity fakes (fakeredis) over mocks

See Also:
    - backend/CLAUDE.md - App Factory Pattern guide
    - docs/guides/testing/INTEGRATION_TESTS.md - Integration testing philosophy
    - backend/tests/integration/README.md - Integration test patterns
"""
import pytest
import time
from typing import Any, AsyncGenerator, Callable, Generator
from unittest.mock import AsyncMock, Mock

from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import create_settings
from app.api.v1.deps import get_text_processor
from app.services.text_processor import TextProcessorService
from app.schemas import TextProcessingResponse

# =============================================================================
# App Factory Pattern Fixtures (Critical for Test Isolation)
# =============================================================================

@pytest.fixture(scope="function")
def test_settings(monkeypatch: pytest.MonkeyPatch) -> Any:
    """
    Real Settings instance for middleware integration tests.

    Provides actual Settings object with test-appropriate configuration
    that can be used to initialize services and verify behavior.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        Settings: Fresh settings instance from current environment

    Note:
        - Uses factory pattern to pick up current environment
        - Modify via monkeypatch BEFORE calling this fixture
        - Settings validation rules are fully applied
    """
    # Set test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("CACHE_PRESET", "disabled")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")  # Disable for isolation testing

    # Create fresh settings from current environment
    return create_settings()


@pytest.fixture(scope="function")
def test_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client for middleware integration tests with isolated app instance.

    Uses App Factory Pattern to create fresh FastAPI app that picks up
    current environment variables set via monkeypatch.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client with fresh app instance

    Note:
        - Environment must be set BEFORE calling this fixture
        - Each test gets completely isolated app instance
        - Settings are loaded fresh from current environment
    """
    # Set default test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")  # Disable for clean testing
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")  # For AI service initialization

    # Create fresh app AFTER environment is configured
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def test_client_with_logging(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client with request logging enabled for testing logging middleware.

    Creates isolated app with request logging configured for testing
    middleware integration scenarios.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client configured with logging enabled
    """
    # Set test configuration with logging enabled
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")  # For AI service initialization
    monkeypatch.setenv("REQUEST_LOGGING_ENABLED", "true")
    monkeypatch.setenv("PERFORMANCE_MONITORING_ENABLED", "true")

    # Create fresh app with logging configuration
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


# =============================================================================
# Middleware-Specific Test Client Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def client_minimal_middleware(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    TestClient with selective middleware disabled for isolation testing.

    Use to isolate specific middleware behavior by disabling others.
    Enables focused testing of individual middleware components.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client with minimal middleware stack

    Note:
        - Disables rate limiting and compression for clean testing
        - Keeps performance monitoring and request logging for validation
        - Each test gets fresh app instance (function scope)
    """
    # Set test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")
    monkeypatch.setenv("COMPRESSION_ENABLED", "false")
    monkeypatch.setenv("PERFORMANCE_MONITORING_ENABLED", "true")
    monkeypatch.setenv("REQUEST_LOGGING_ENABLED", "true")

    # Create fresh app with selective middleware
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def client_with_fakeredis_rate_limit(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    TestClient with Redis-backed rate limiting using fakeredis.

    Simulates distributed rate limiting without requiring real Redis.
    Enables testing of rate limiting middleware behavior in isolation.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client with Redis-backed rate limiting

    Note:
        - Redirects Redis connections to fakeredis instance
        - Enables rate limiting with distributed counters
        - Each test gets fresh Redis instance (function scope)
        - No network calls - all operations in-memory
    """
    import fakeredis.aioredis as fredis
    import redis.asyncio as redis

    # Create fake Redis instance
    fake_redis = fredis.FakeRedis(decode_responses=False)

    # Redirect Redis.from_url to fakeredis instance
    monkeypatch.setattr(redis.Redis, 'from_url', lambda url, **kw: fake_redis)

    # Set test configuration for rate limiting
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("RATE_LIMITING_ENABLED", "true")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("RATE_LIMIT_REDIS_KEY_PREFIX", "test_rate_limit:")

    # Create fresh app with rate limiting configuration
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def client_with_compression(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    TestClient with compression middleware enabled for testing compression behavior.

    Creates isolated app with compression configured for testing compression
    middleware integration scenarios.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client configured with compression enabled

    Note:
        - Enables compression with low threshold for easy testing
        - Each test gets fresh app instance (function scope)
    """
    # Set test configuration with compression enabled
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("COMPRESSION_ENABLED", "true")
    monkeypatch.setenv("COMPRESSION_THRESHOLD", "100")  # Low threshold for testing

    # Create fresh app with compression configuration
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="function")
def authenticated_test_client_with_logging(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client with logging enabled and valid authentication headers.

    Provides authenticated test client for testing middleware behavior
    that requires authentication without coupling to authentication testing.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client with authentication headers and logging enabled

    Note:
        - Includes valid API key headers automatically
        - Configures body logging environment variables
        - Uses function scope for test isolation
        - Creates fresh app using create_app()
        - Returns TestClient with automatic authentication header injection
    """
    # Set test configuration with logging enabled
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")  # For AI service initialization
    monkeypatch.setenv("REQUEST_LOGGING_ENABLED", "true")
    monkeypatch.setenv("PERFORMANCE_MONITORING_ENABLED", "true")
    monkeypatch.setenv("LOG_REQUEST_BODIES", "true")   # Enable body logging
    monkeypatch.setenv("LOG_RESPONSE_BODIES", "true")  # Enable response logging

    # Create fresh app with logging configuration
    app = create_app()

    # Create client with default authentication headers
    client = TestClient(app, raise_server_exceptions=False)

    # Monkey-patch client to include auth headers automatically
    original_request = client.request
    def request_with_auth(*args, **kwargs):
        if 'headers' not in kwargs or kwargs['headers'] is None:
            kwargs['headers'] = {}
        elif kwargs['headers'] is None:
            kwargs['headers'] = {}

        # Normalize headers to lowercase for case-insensitive comparison
        headers_lower = {k.lower(): v for k, v in kwargs['headers'].items()} if kwargs['headers'] else {}

        if 'authorization' not in headers_lower:
            kwargs['headers']['Authorization'] = 'Bearer test-api-key-12345'
        return original_request(*args, **kwargs)

    client.request = request_with_auth
    return client


@pytest.fixture(scope="function")
def client_with_security_headers(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    TestClient with security headers middleware enabled for testing security behavior.

    Creates isolated app with security headers configured for testing
    security middleware integration scenarios.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        TestClient: HTTP client configured with security headers enabled

    Note:
        - Enables security headers for testing
        - Each test gets fresh app instance (function scope)
    """
    # Set test configuration with security enabled
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("SECURITY_ENABLED", "true")

    # Create fresh app with security configuration
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


# =============================================================================
# Mock and Failure Simulation Fixtures
# =============================================================================

@pytest.fixture
def failing_redis_connection(monkeypatch: pytest.MonkeyPatch) -> bool:
    """
    Force Redis connection errors to validate local fallback behavior.

    Simulates Redis outage for graceful degradation testing of rate limiting
    middleware and other Redis-dependent components.

    Args:
        monkeypatch: Pytest fixture for mocking Redis operations

    Returns:
        bool: Marker indicating fixture is active

    Note:
        - Causes all Redis operations to raise ConnectionError
        - Tests can verify graceful degradation behavior
        - Mock is automatically cleaned up after test
    """
    def _raise_connection_error(*args: Any, **kwargs: Any) -> None:
        """Simulate Redis connection failure."""
        raise ConnectionError('Simulated Redis failure for testing')

    # Mock Redis async methods to raise connection errors
    monkeypatch.setattr('redis.asyncio.Redis.incr', _raise_connection_error, raising=True)
    monkeypatch.setattr('redis.asyncio.Redis.get', _raise_connection_error, raising=True)
    monkeypatch.setattr('redis.asyncio.Redis.set', _raise_connection_error, raising=True)
    monkeypatch.setattr('redis.asyncio.Redis.expire', _raise_connection_error, raising=True)

    return True  # Fixture marker to indicate it's active


@pytest.fixture
def mock_rate_limit_storage() -> Mock:
    """
    Mock rate limit storage for testing rate limiting middleware behavior.

    Provides controlled mock responses for testing rate limiting scenarios
    without requiring Redis or external storage.

    Returns:
        Mock: Configured mock with default rate limiting behavior

    Usage:
        ```python
        def test_rate_limit_exceeded(mock_rate_limit_storage):
            # Configure mock to simulate limit exceeded
            mock_rate_limit_storage.get.return_value = "10"
            mock_rate_limit_storage.incr.return_value = 11

            # Test rate limiting behavior
            response = client.get("/api/endpoint")
            assert response.status_code == 429
        ```

    Note:
        - Default behavior returns successful responses (under limit)
        - Override return_value or side_effect in tests for specific scenarios
        - Mock is reset between tests (function scope)
    """
    mock = Mock()

    # Set default behavior (under rate limit)
    mock.get.return_value = None  # No existing requests
    mock.incr.return_value = 1    # First request
    mock.expire.return_value = True

    return mock


@pytest.fixture
def slow_performance_monitor() -> AsyncMock:
    """
    Mock performance monitor that simulates slow operations for testing timeout scenarios.

    Provides controlled slow responses for testing performance monitoring
    middleware behavior under various timing conditions.

    Returns:
        AsyncMock: Mock configured with slow default behavior

    Usage:
        ```python
        def test_performance_timeout(slow_performance_monitor):
            # Configure mock to be slow
            slow_performance_monitor.record_request.side_effect = asyncio.sleep(0.1)

            # Test performance monitoring behavior with slow operations
            response = client.get("/api/endpoint")
            assert response.status_code == 200
        ```

    Note:
        - Default behavior simulates normal timing
        - Override side_effect in tests for specific timing scenarios
        - Mock is reset between tests (function scope)
    """
    mock = AsyncMock()

    # Set default behavior (normal timing)
    mock.record_request.return_value = {"duration_ms": 10.0, "status": "success"}
    mock.get_metrics.return_value = {"avg_duration_ms": 15.0, "request_count": 100}

    return mock


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_small_response() -> dict:
    """
    Sample small response for compression threshold testing.

    Provides realistic small response data that falls below compression
    threshold for testing compression middleware behavior.

    Returns:
        dict: Sample response data with small payload

    Note:
        - Data is small enough to bypass compression threshold
        - Valid JSON structure for API responses
        - Modify in tests for specific scenarios
    """
    return {
        "message": "Hello, World!",
        "status": "success",
        "data": {"id": 1, "name": "test"}
    }


@pytest.fixture
def sample_large_response() -> dict:
    """
    Sample large response for compression activation testing.

    Provides realistic large response data that exceeds compression
    threshold for testing compression middleware behavior.

    Returns:
        dict: Sample response data with large payload

    Note:
        - Data is large enough to trigger compression
        - Valid JSON structure for API responses
        - Modify in tests for specific scenarios
    """
    # Generate enough data to exceed typical compression thresholds
    large_data = []
    for i in range(100):
        large_data.append({
            "id": i,
            "name": f"item_{i}",
            "description": "A" * 50,  # Pad with characters
            "metadata": {"key": f"value_{i}", "extra": "B" * 20}
        })

    return {
        "message": "Large response data",
        "status": "success",
        "count": len(large_data),
        "data": large_data
    }


@pytest.fixture
def large_payload_generator() -> Callable[[int], Generator[bytes, None, None]]:
    """
    Generate large payloads without consuming memory.

    Returns function that yields chunks for streaming tests and
    request size limiting middleware validation.

    Returns:
        Callable: Function that generates large payloads as chunks

    Usage:
        ```python
        def test_large_payload_handling(large_payload_generator):
            # Generate 5MB payload
            generator = large_payload_generator(5)
            chunks = list(generator)

            # Test request size limiting behavior
            response = client.post("/api/upload", data=b''.join(chunks))
            assert response.status_code in [200, 413]  # 413 = Payload Too Large
        ```

    Note:
        - Generator yields 1KB chunks to control memory usage
        - Size parameter is in MB for easy configuration
        - Each chunk is exactly 1024 bytes
        - Useful for testing request size limiting middleware
    """
    def generator(size_mb: int) -> Generator[bytes, None, None]:
        """
        Generate large payload chunks.

        Args:
            size_mb: Size of payload to generate in megabytes

        Yields:
            bytes: 1KB chunks of data
        """
        chunk = b"x" * 1024  # 1KB chunk
        for _ in range(size_mb * 1024):
            yield chunk

    return generator


@pytest.fixture
def sample_api_request_data() -> dict:
    """
    Sample API request data for middleware testing.

    Provides realistic request data for testing various middleware
    components including validation, logging, and security.

    Returns:
        dict: Sample API request data

    Note:
        - Contains typical API request fields
        - Valid structure for JSON requests
        - Modify in tests for specific scenarios
    """
    return {
        "text": "Sample text for processing",
        "options": {
            "language": "en",
            "format": "json",
            "include_metadata": True
        },
        "metadata": {
            "source": "test",
            "priority": "normal",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }


# =============================================================================
# Performance Monitoring Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def performance_monitor() -> Any:
    """
    Performance monitoring for testing middleware timing and metrics.

    Provides timing utilities for measuring middleware performance,
    compression effects, and request processing efficiency.

    Returns:
        PerformanceMonitor: Object with start(), stop(), and elapsed_ms property

    Note:
        - Simple implementation for basic timing measurements
        - Each test gets fresh instance (function scope)
        - Useful for validating performance characteristics

    Usage:
        ```python
        def test_middleware_performance(performance_monitor):
            performance_monitor.start()

            # Execute middleware operation
            response = client.get("/api/endpoint")

            performance_monitor.stop()
            assert performance_monitor.elapsed_ms < 1000  # Under 1 second
        ```

    See Also:
        - backend/tests/integration/text_processor/conftest.py:604-650 for similar implementation
    """
    class PerformanceMonitor:
        def __init__(self) -> None:
            self.start_time: float | None = None
            self.end_time: float | None = None

        def start(self) -> None:
            """Start timing measurement."""
            self.start_time = time.perf_counter()

        def stop(self) -> None:
            """Stop timing measurement."""
            self.end_time = time.perf_counter()

        @property
        def elapsed_ms(self) -> float | None:
            """Get elapsed time in milliseconds."""
            if self.start_time is not None and self.end_time is not None:
                return (self.end_time - self.start_time) * 1000
            return None

        def reset(self) -> None:
            """Reset timing measurements."""
            self.start_time = None
            self.end_time = None

    return PerformanceMonitor()


# =============================================================================
# Middleware Service Fixtures
# =============================================================================

@pytest.fixture
def rate_limiting_service(test_settings: Any) -> Any:
    """
    Real rate limiting service for integration testing.

    Provides actual rate limiting implementation with test configuration,
    enabling validation of rate limiting middleware behavior.

    Args:
        test_settings: Real Settings with test configuration

    Returns:
        RateLimitingService: Configured rate limiting service

    Note:
        - Uses real rate limiting implementation (not mocked)
        - Configuration from real Settings object
        - Tests actual rate limiting behavior, not mocks
    """
    from app.infrastructure.resilience.rate_limiting import RateLimitingService  # type: ignore

    # Create service with real settings
    service = RateLimitingService(settings=test_settings)
    return service


@pytest.fixture
def compression_service(test_settings: Any) -> Any:
    """
    Real compression service for integration testing.

    Provides actual compression implementation with test configuration,
    enabling validation of compression middleware behavior.

    Args:
        test_settings: Real Settings with test configuration

    Returns:
        CompressionService: Configured compression service

    Note:
        - Uses real compression implementation (not mocked)
        - Configuration from real Settings object
        - Tests actual compression behavior, not mocks
    """
    from app.infrastructure.compression import CompressionService  # type: ignore

    # Create service with real settings
    service = CompressionService(settings=test_settings)
    return service


# =============================================================================
# Authentication Fixtures (Reuse from Shared Fixtures)
# =============================================================================

@pytest.fixture
def middleware_auth_headers() -> dict:
    """
    Authentication headers specific to middleware testing.

    Returns:
        dict: HTTP headers with middleware-specific authentication

    Note:
        - Uses test API key configured for middleware tests
        - Includes content type for JSON requests
        - Can be modified in tests for specific auth scenarios
    """
    return {
        "Authorization": "Bearer test-api-key-12345",
        "Content-Type": "application/json",
        "X-Test-Client": "middleware-integration-test"
    }


@pytest.fixture
def invalid_middleware_auth_headers() -> dict:
    """
    Invalid authentication headers for middleware authentication testing.

    Returns:
        dict: HTTP headers with invalid authentication for testing failure scenarios

    Note:
        - Uses invalid API key for testing authentication middleware
        - Maintains proper format for valid request structure
        - Useful for testing authentication failure handling
    """
    return {
        "Authorization": "Bearer invalid-middleware-key-12345",
        "Content-Type": "application/json",
        "X-Test-Client": "middleware-integration-test"
    }


# =============================================================================
# Exception Handler Test Fixtures
# =============================================================================

@pytest.fixture(scope="function")
def app_with_exception_test_endpoints(monkeypatch: pytest.MonkeyPatch) -> Any:
    """
    App with test endpoints for exception handler testing.

    Provides FastAPI app instance with pre-registered test endpoints that
    raise specific exception types for testing global exception handler
    integration with middleware stack.

    Args:
        monkeypatch: Pytest fixture for environment configuration

    Returns:
        FastAPI: App instance with exception test endpoints pre-registered

    Note:
        - Uses App Factory Pattern for proper test isolation
        - All exception types from app.core.exceptions are tested
        - Each endpoint raises a specific exception type
        - Environment configured for testing
        - Each test gets fresh app instance (function scope)

    Usage:
        ```python
        def test_exception_handler(app_with_exception_test_endpoints):
            app = app_with_exception_test_endpoints
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/test/validation-error")
            assert response.status_code == 400
        ```
    """
    from app.core.exceptions import (
        ValidationError, AuthenticationError, AuthorizationError,
        ConfigurationError, InfrastructureError, BusinessLogicError,
        RateLimitError, RequestTooLargeError
    )

    # Configure environment for testing
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")

    # Create app using factory pattern
    app = create_app()

    # Register test endpoints that raise specific exceptions
    @app.get("/test/validation-error")
    async def validation_error_endpoint() -> None:
        """Test endpoint that raises ValidationError."""
        raise ValidationError("Invalid input data", {"field": "email"})

    @app.get("/test/authentication-error")
    async def authentication_error_endpoint() -> None:
        """Test endpoint that raises AuthenticationError."""
        raise AuthenticationError("Invalid credentials")

    @app.get("/test/authorization-error")
    async def authorization_error_endpoint() -> None:
        """Test endpoint that raises AuthorizationError."""
        raise AuthorizationError("Insufficient permissions")

    @app.get("/test/configuration-error")
    async def configuration_error_endpoint() -> None:
        """Test endpoint that raises ConfigurationError."""
        raise ConfigurationError("Invalid configuration")

    @app.get("/test/infrastructure-error")
    async def infrastructure_error_endpoint() -> None:
        """Test endpoint that raises InfrastructureError."""
        raise InfrastructureError("Database connection failed")

    @app.get("/test/business-logic-error")
    async def business_logic_error_endpoint() -> None:
        """Test endpoint that raises BusinessLogicError."""
        raise BusinessLogicError("Business rule violated")

    @app.get("/test/rate-limit-error")
    async def rate_limit_error_endpoint() -> None:
        """Test endpoint that raises RateLimitError."""
        raise RateLimitError("Rate limit exceeded")

    @app.get("/test/request-too-large-error")
    async def request_too_large_error_endpoint() -> None:
        """Test endpoint that raises RequestTooLargeError."""
        raise RequestTooLargeError("Request size too large")

    @app.get("/test/generic-exception")
    async def generic_exception_endpoint() -> None:
        """Test endpoint that raises generic Exception."""
        raise Exception("Unexpected error")

    @app.get("/test/value-error")
    async def value_error_endpoint() -> None:
        """Test endpoint that raises ValueError."""
        raise ValueError("Invalid value")

    @app.get("/test/type-error")
    async def type_error_endpoint() -> None:
        """Test endpoint that raises TypeError."""
        raise TypeError("Type mismatch")

    @app.get("/test/key-error")
    async def key_error_endpoint() -> None:
        """Test endpoint that raises KeyError."""
        raise KeyError("Missing key")

    @app.get("/test/attribute-error")
    async def attribute_error_endpoint() -> None:
        """Test endpoint that raises AttributeError."""
        raise AttributeError("Missing attribute")

    @app.get("/test/import-error")
    async def import_error_endpoint() -> None:
        """Test endpoint that raises ImportError."""
        raise ImportError("Module not found")

    @app.get("/test/connection-error")
    async def connection_error_endpoint() -> None:
        """Test endpoint that raises ConnectionError."""
        raise ConnectionError("Connection failed")

    @app.get("/test/timeout-error")
    async def timeout_error_endpoint() -> None:
        """Test endpoint that raises TimeoutError."""
        raise TimeoutError("Operation timed out")

    @app.get("/test/runtime-error")
    async def runtime_error_endpoint() -> None:
        """Test endpoint that raises RuntimeError."""
        raise RuntimeError("Runtime error occurred")

    return app


@pytest.fixture(scope="function")
def exception_test_client(app_with_exception_test_endpoints: Any) -> TestClient:
    """
    Test client with exception test endpoints for global exception handler testing.

    Creates HTTP client with app that has pre-registered exception test
    endpoints, enabling proper testing of global exception handler
    integration with middleware stack.

    Args:
        app_with_exception_test_endpoints: App with exception test endpoints

    Returns:
        TestClient: HTTP client configured for exception handler testing

    Note:
        - Uses app from exception_test_endpoints fixture
        - All endpoints raise specific exceptions for testing
        - Client can test error responses, headers, and logging
        - Each test gets fresh client (function scope)

    Usage:
        ```python
        def test_exception_handler_integration(exception_test_client):
            response = exception_test_client.get("/test/validation-error")
            assert response.status_code == 400
            assert "error" in response.json()
        ```
    """
    return TestClient(app_with_exception_test_endpoints, raise_server_exceptions=False)


# =============================================================================
  # AI Service Mock Fixture
  # =============================================================================

@pytest.fixture(scope="function")
def mock_text_processor() -> AsyncMock:
    """Mock text processor service for middleware tests.

    Middleware integration tests should test middleware behavior,
    not AI service functionality. This fixture mocks the TextProcessorService
    to return successful responses without requiring real AI service.

    Returns:
        AsyncMock: Mocked text processor service instance with process_text method

    Note:
        - Returns AsyncMock with process_text method configured
        - Use with app.dependency_overrides to replace real service
        - Automatically returns proper TextProcessingResponse objects
    """
    mock_service = AsyncMock(spec=TextProcessorService)

    # Mock the process_text method to return successful response
    async def mock_process_text(request):
        return TextProcessingResponse(
            result="mocked summary",
            operation=request.operation,
            metadata={"processing_time": 0.01, "cached": False},
            cache_hit=False
        )

    mock_service.process_text = AsyncMock(side_effect=mock_process_text)

    return mock_service


@pytest.fixture(scope="function")
def test_client_with_mocked_ai_service(mock_text_processor):
    """Create test client with mocked AI service for middleware tests.

    This fixture creates a fresh FastAPI app instance with the TextProcessorService
    dependency overridden to return our mock. This ensures middleware tests don't
    require real AI service connectivity.

    Args:
        mock_text_processor: Mocked text processor service fixture

    Returns:
        TestClient: FastAPI test client with mocked dependencies

    Note:
        - Overrides get_text_processor dependency with mock
        - Cleans up dependency overrides after test completes
        - Each test gets isolated app instance with fresh configuration
    """
    # Create fresh app instance
    app = create_app()

    # Override the dependency to return our mock
    app.dependency_overrides[get_text_processor] = lambda: mock_text_processor

    yield TestClient(app)

    # Cleanup: Clear dependency overrides
    app.dependency_overrides.clear()
