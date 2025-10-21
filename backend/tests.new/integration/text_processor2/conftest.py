"""
Fixtures for text_processor + cache integration tests.

Follows patterns from backend/tests/integration/cache/conftest.py
while leveraging shared fixtures from backend/tests/integration/conftest.py.

This file provides integration test infrastructure for validating
the collaboration between TextProcessorService and AIResponseCache.
"""

import pytest
import fakeredis.aioredis
from cryptography.fernet import Fernet
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.services.text_processor import TextProcessorService

# =============================================================================
# Serial Execution (if needed for shared state)
# =============================================================================

# Uncomment if tests share state or have timing dependencies:
# def pytest_collection_modifyitems(items):
#     """Force text_processor integration tests to run serially."""
#     for item in items:
#         item.add_marker(pytest.mark.xdist_group(name="text_processor_serial"))


# =============================================================================
# Settings Fixtures
# =============================================================================

@pytest.fixture
def test_settings(monkeypatch):
    """
    Real Settings instance with test configuration for integration testing.

    Provides a Settings instance loaded from test configuration, enabling tests
    to verify actual configuration loading, validation, and environment detection.

    This fixture follows the monkeypatch pattern (not direct os.environ manipulation)
    to ensure proper test isolation and cleanup.

    Args:
        monkeypatch: Pytest fixture for environment variable manipulation

    Returns:
        Settings: Real Settings instance with test configuration

    Note:
        This is the same fixture pattern as cache/conftest.py test_settings.
        Duplicated here to avoid cross-directory fixture dependencies.
    """
    from app.core.config import Settings

    # Set test environment variables using monkeypatch (proper pattern)
    test_env = {
        "GEMINI_API_KEY": "test-gemini-api-key-12345",
        "API_KEY": "test-api-key-12345",
        "CACHE_PRESET": "development",
        "RESILIENCE_PRESET": "simple",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    # Create real Settings instance
    # monkeypatch automatically restores environment after test
    return Settings()


# =============================================================================
# Cache Infrastructure Fixtures
# =============================================================================

@pytest.fixture(scope="function")
async def fakeredis_client():
    """
    FakeRedis client for integration testing.

    Provides in-memory Redis simulation without Docker overhead.
    Follows pattern from cache integration tests but uses fakeredis
    instead of real Redis container for faster execution.

    Note:
        This fixture is also available in shared integration/conftest.py.
        Defined here for clarity and to avoid import dependencies.

    Returns:
        FakeRedis: Async-compatible fake Redis client

    Note:
        decode_responses=False matches production Redis behavior
    """
    return fakeredis.aioredis.FakeRedis(decode_responses=False)


@pytest.fixture(scope="function")
async def ai_response_cache(fakeredis_client, monkeypatch):
    """
    Real AIResponseCache backed by fakeredis for integration testing.

    Follows cache integration test patterns:
    - Uses proper Fernet key generation (like secure_redis_cache)
    - Uses monkeypatch for environment variables (best practice)
    - Proper cleanup in try/finally block
    - Tests real production code with realistic infrastructure

    Differences from cache/conftest.py secure_redis_cache:
    - Uses fakeredis instead of secure Redis container
    - Simplified encryption (can be enabled if needed)
    - Function-scoped instead of session-scoped

    Integration Scope:
        Tests collaboration between TextProcessorService and AIResponseCache
        using production cache code with simulated Redis backend.

    Args:
        fakeredis_client: FakeRedis client fixture
        monkeypatch: Pytest fixture for environment variable manipulation

    Yields:
        AIResponseCache: Connected cache instance with full features

    Note:
        Encryption disabled by default for simplicity.
        See UPGRADE_UNIT_TESTS.md Phase 4 for encryption options if needed.
    """
    # Generate proper encryption key (following cache integration pattern)
    # This ensures encryption infrastructure works even if we disable it
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)

    cache = AIResponseCache(
        redis_client=fakeredis_client,
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        enable_monitoring=True,
        enable_encryption=False,  # Simplified for testing (see Phase 4)
    )

    # Skip connect() - fakeredis_client is already connected
    # await cache.connect()

    try:
        yield cache
    finally:
        # Proper cleanup following cache integration pattern
        try:
            await cache.clear()
            # await cache.disconnect()  # Skip disconnect for fakeredis
        except Exception as e:
            print(f"Warning: Cache cleanup failed: {e}")


@pytest.fixture(scope="function")
async def ai_response_cache_with_data(fakeredis_client, monkeypatch):
    """
    Pre-populated AIResponseCache for testing cache hit scenarios.

    Follows pattern from unit tests' fake_cache_with_hit but uses
    real AIResponseCache to test production cache behavior.

    Args:
        fakeredis_client: FakeRedis client fixture
        monkeypatch: Pytest fixture for environment variable manipulation

    Yields:
        AIResponseCache: Connected cache instance with sample data

    Pre-populated Data:
        - Operation: "summarize"
        - Text: "Sample text for testing"
        - Options: {"max_length": 100}
        - Cached result: "Cached summary of sample text content"
        - TTL: 7200 seconds

    Usage:
        ```python
        async def test_cache_hit(ai_response_cache_with_data):
            # Cache already contains summarization result
            result = await ai_response_cache_with_data.get(cache_key)
            assert result is not None
        ```
    """
    # Generate proper encryption key
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)

    cache = AIResponseCache(
        redis_client=fakeredis_client,
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        enable_monitoring=True,
        enable_encryption=False,
    )

    # Skip connect() - fakeredis_client is already connected
    # await cache.connect()

    # Pre-populate with sample data
    cache_key = cache.build_key(
        text="Sample text for testing",
        operation="summarize",
        options={"max_length": 100}
    )

    await cache.set(
        cache_key,
        {
            "result": "Cached summary of sample text content",
            "operation": "summarize",
            "cache_hit": True,
            "processing_time": 0.01,  # Minimal time for cache hit
        },
        ttl=7200
    )

    try:
        yield cache
    finally:
        try:
            await cache.clear()
            # await cache.disconnect()  # Skip disconnect for fakeredis
        except Exception as e:
            print(f"Warning: Cache cleanup failed: {e}")


@pytest.fixture(scope="function")
async def integration_text_processor(test_settings, ai_response_cache):
    """
    TextProcessorService with real cache for integration testing.

    Leverages:
    - test_settings from cache/conftest.py
    - ai_response_cache from this conftest.py

    Integration Scope:
        TextProcessorService + AIResponseCache + PydanticAI Agent collaboration

    Args:
        test_settings: Settings instance from cache fixtures
        ai_response_cache: Real cache instance backed by fakeredis

    Returns:
        TextProcessorService: Service instance configured for integration testing

    Note:
        This fixture combines real service logic with real cache infrastructure
        to test actual integration behavior, not mocked interfaces.
    """
    return TextProcessorService(
        settings=test_settings,
        cache=ai_response_cache,
    )


# =============================================================================
# Test Data Fixtures (optional)
# =============================================================================

@pytest.fixture
def sample_processing_request():
    """
    Standard text processing request for integration testing.

    Provides consistent test data for integration tests validating
    the complete flow from request to cached response.

    Returns:
        ProcessingRequest: Sample request with common operation

    Usage:
        ```python
        async def test_cache_integration(integration_text_processor, sample_processing_request):
            response = await integration_text_processor.process_text(sample_processing_request)
            assert response.cache_hit is False  # First call
        ```
    """
    from app.schemas import ProcessingRequest
    return ProcessingRequest(
        text="Sample text for processing",
        operation="summarize"
    )


# =============================================================================
# Mock Fixtures (for integration tests without AI API calls)
# =============================================================================

@pytest.fixture
def mock_pydantic_agent():
    """
    Mock PydanticAI Agent for testing without AI API keys.

    This mock allows integration tests to focus on cache behavior
    without requiring actual AI service calls. The tests validate
    cache integration, not AI integration.

    Returns:
        Mock: Mock Agent with run() method that returns structured response

    Default Behavior:
        - run() returns successful AI response
        - Tracks call count for verification
        - Can be customized per test

    Usage:
        ```python
        async def test_with_mock_agent(mock_pydantic_agent):
            # Customize response
            mock_pydantic_agent.run.return_value = Mock(
                data="Custom AI result",
                cost=Mock(request_tokens=5, response_tokens=10)
            )

            # Use in test
            processor = TextProcessorService(settings, cache)
            response = await processor.process_text(request)

            # Verify mock was called
            mock_pydantic_agent.run.assert_called_once()
        ```

    Note:
        For true end-to-end AI integration, create separate E2E tests
        with real AI agents using manual test markers and API keys.
    """
    from unittest.mock import AsyncMock, Mock

    mock_agent = Mock()
    mock_agent.run = AsyncMock()

    # Default response structure matching PydanticAI
    mock_agent.run.return_value = Mock(
        data="AI processed result",
        cost=Mock(request_tokens=10, response_tokens=20)
    )

    return mock_agent


@pytest.fixture
def fake_prompt_sanitizer():
    """
    Fake PromptSanitizer for tracking sanitization calls in integration tests.

    Provides a simple pass-through sanitizer that tracks whether sanitization
    was called, useful for verifying the service calls sanitization.

    Returns:
        Mock: Mock sanitizer with tracking

    Behavior:
        - sanitize() returns input unchanged (pass-through)
        - Tracks whether sanitize() was called
        - Can verify call count and arguments

    Usage:
        ```python
        async def test_sanitization(fake_prompt_sanitizer):
            processor = TextProcessorService(
                settings,
                cache,
                prompt_sanitizer=fake_prompt_sanitizer
            )

            await processor.process_text(request)

            # Verify sanitization was called
            fake_prompt_sanitizer.sanitize.assert_called_once()
        ```

    Note:
        For production integration tests, consider using real PromptSanitizer
        since it has no external dependencies. This mock is provided for
        backward compatibility with unit tests.
    """
    from unittest.mock import Mock

    sanitizer = Mock()
    sanitizer.sanitize = Mock(side_effect=lambda text: text)  # Pass-through
    sanitizer.sanitize_called = False

    def track_sanitize(text):
        sanitizer.sanitize_called = True
        return text

    sanitizer.sanitize.side_effect = track_sanitize
    return sanitizer
