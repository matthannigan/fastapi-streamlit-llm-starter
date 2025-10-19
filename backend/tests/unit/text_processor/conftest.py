"""
Text Processor Service test fixtures providing dependencies for testing.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the text_processor component from systems outside its boundary.

Dependencies covered:
- Settings configuration (reuse from parent conftest)
- Cache service (Fake - stateful in-memory cache)
- PromptSanitizer (Fake - tracks sanitization calls)
- ResponseValidator (Mock - complex validation logic)
- AI Resilience Orchestrator (Mock - external singleton)
- PydanticAI Agent (Mock - external library)
"""

import pytest
from unittest.mock import Mock, AsyncMock, create_autospec
from typing import Any, Dict, Optional


# =============================================================================
# Fake Cache Service (Stateful In-Memory Implementation)
# =============================================================================


class FakeCache:
    """
    Fake in-memory cache implementation for testing text processor caching behavior.

    Provides a lightweight, stateful cache that simulates AIResponseCache and InMemoryCache
    interfaces without requiring Redis or complex initialization. Enables testing cache-first
    strategies, TTL management, and cache hit/miss scenarios.

    State Management:
        - Uses dictionary for in-memory storage
        - Tracks cache hits and misses for testing
        - Supports TTL parameter (stored but not enforced for simplicity)
        - Fully stateful - modifications persist across method calls

    Behavior:
        - get(): Returns cached value if exists, None otherwise
        - set(): Stores value with optional TTL
        - delete(): Removes value from cache
        - clear(): Clears all cached values
        - build_cache_key(): Builds cache keys from request parameters

    Use Cases:
        - Testing cache-first processing strategy
        - Testing cache hit/miss behavior
        - Testing cache key generation logic
        - Testing operation-specific TTL handling
        - Verifying cached responses are used correctly

    Test Customization:
        def test_with_cached_response(fake_cache):
            # Pre-populate cache for testing cache hits
            fake_cache._data["test_key"] = {"result": "cached summary"}
            
            # Test will retrieve cached response
            processor = TextProcessorService(settings, fake_cache)
            response = await processor.process_text(request)
            assert response.cache_hit is True
    """

    def __init__(self):
        """Initialize fake cache with empty storage and metrics."""
        self._data: Dict[str, Any] = {}
        self._ttls: Dict[str, int] = {}
        self._hit_count = 0
        self._miss_count = 0

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache by key.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if exists, None otherwise

        Behavior:
            - Tracks cache hits and misses for testing
            - Does not enforce TTL expiration (simplified for testing)
        """
        if key in self._data:
            self._hit_count += 1
            return self._data[key]
        self._miss_count += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (stored but not enforced)

        Behavior:
            - Stores value in internal dictionary
            - Records TTL for testing verification
            - Overwrites existing values
        """
        self._data[key] = value
        if ttl is not None:
            self._ttls[key] = ttl

    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key to delete

        Behavior:
            - Removes key from storage if exists
            - Removes associated TTL if exists
            - No error if key doesn't exist
        """
        self._data.pop(key, None)
        self._ttls.pop(key, None)

    async def clear(self) -> None:
        """
        Clear all values from cache.

        Behavior:
            - Removes all stored values
            - Removes all TTL records
            - Resets hit/miss counters
        """
        self._data.clear()
        self._ttls.clear()
        self._hit_count = 0
        self._miss_count = 0

    def build_cache_key(
        self,
        text: str,
        operation: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build cache key from request parameters.

        Args:
            text: Input text
            operation: Processing operation name
            options: Optional processing options

        Returns:
            Cache key string

        Behavior:
            - Simulates AIResponseCache.build_cache_key() interface
            - Uses simple string concatenation for testing
            - Includes options in key for uniqueness
        """
        options_str = str(sorted(options.items())) if options else ""
        return f"{operation}:{hash(text)}:{options_str}"

    # Alias for consistency with real cache interface
    def build_key(self, text: str, operation: str, options: Dict[str, Any]) -> str:
        """Alias for build_cache_key to match real cache interface."""
        return self.build_cache_key(text, operation, options)

    def get_hit_count(self) -> int:
        """Get number of cache hits (for testing verification)."""
        return self._hit_count

    def get_miss_count(self) -> int:
        """Get number of cache misses (for testing verification)."""
        return self._miss_count

    def get_stored_ttl(self, key: str) -> Optional[int]:
        """Get stored TTL for key (for testing verification)."""
        return self._ttls.get(key)

    async def get_all_keys(self) -> list:
        """Get all cache keys for testing verification."""
        return list(self._data.keys())


@pytest.fixture
def fake_cache():
    """
    Provides fake in-memory cache service for text processor testing.

    Returns a FakeCache instance with empty storage, enabling tests to verify
    caching behavior without requiring Redis or complex cache infrastructure.

    Default Behavior:
        - Empty cache (all lookups miss initially)
        - Stateful - stores values across operations
        - TTL tracking enabled (but not enforced)
        - Metrics tracking for verification

    Use Cases:
        - Testing cache-first processing strategy
        - Testing cache miss fallback to AI processing
        - Testing cache key generation
        - Testing TTL assignment per operation
        - Verifying cache storage after successful processing

    Test Customization:
        def test_cache_hit_scenario(fake_cache):
            # Pre-populate cache with response
            await fake_cache.set(
                "summarize:12345:",
                {"result": "Cached summary"}
            )
            
            # Test uses cached response instead of AI
            processor = TextProcessorService(settings, fake_cache)
            response = await processor.process_text(request)
            assert response.cache_hit is True
            assert fake_cache.get_hit_count() == 1

    Examples:
        >>> # Test cache miss scenario
        >>> cache = fake_cache()
        >>> result = await cache.get("nonexistent_key")
        >>> assert result is None
        >>> assert cache.get_miss_count() == 1

        >>> # Test cache storage
        >>> await cache.set("test_key", {"data": "value"}, ttl=3600)
        >>> assert await cache.get("test_key") == {"data": "value"}
        >>> assert cache.get_stored_ttl("test_key") == 3600
    """
    return FakeCache()


# =============================================================================
# Fake PromptSanitizer (Stateful Sanitization Tracker)
# =============================================================================


class FakePromptSanitizer:
    """
    Fake prompt sanitizer for testing input sanitization behavior.

    Provides a lightweight sanitizer that tracks sanitization calls without
    performing actual security validation. Enables testing that inputs are
    properly sanitized before AI processing.

    State Management:
        - Tracks all sanitization calls
        - Records sanitized inputs for verification
        - Configurable to simulate injection detection
        - Fully stateful across method calls

    Behavior:
        - sanitize_input(): Returns sanitized version of input
        - sanitize_options(): Returns sanitized options dictionary
        - is_injection_detected: Flag to simulate injection detection
        - get_sanitization_calls(): Returns list of all calls for verification

    Use Cases:
        - Testing input sanitization before AI processing
        - Testing options sanitization
        - Testing injection detection handling
        - Verifying sanitization is called for all operations
        - Testing error handling when injection detected

    Test Customization:
        def test_rejects_injection(fake_prompt_sanitizer):
            # Configure to detect injection
            fake_prompt_sanitizer.is_injection_detected = True
            
            # Test should handle injection detection
            processor = TextProcessorService(settings, cache, fake_prompt_sanitizer)
            with pytest.raises(ValidationError):
                await processor.process_text(malicious_request)
    """

    def __init__(self):
        """Initialize fake sanitizer with empty call tracking."""
        self._sanitization_calls = []
        self._is_injection_detected = False

    def sanitize_input(self, text: str) -> str:
        """
        Sanitize input text and track the call.

        Args:
            text: Input text to sanitize

        Returns:
            Sanitized text (unchanged in fake implementation)

        Behavior:
            - Records call for testing verification
            - Returns input unchanged (no actual sanitization)
            - Simulates injection detection if configured
        """
        self._sanitization_calls.append(("text", text))
        if self._is_injection_detected:
            # In real implementation, this would raise an exception
            # For fake, we just track the call
            pass
        return text

    def sanitize_options(self, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Sanitize options dictionary and track the call.

        Args:
            options: Options dictionary to sanitize

        Returns:
            Sanitized options (unchanged in fake implementation)

        Behavior:
            - Records call for testing verification
            - Returns options unchanged or empty dict if None
        """
        result = options if options is not None else {}
        self._sanitization_calls.append(("options", result))
        return result

    def get_sanitization_calls(self) -> list:
        """Get list of all sanitization calls (for testing verification)."""
        return self._sanitization_calls

    @property
    def is_injection_detected(self) -> bool:
        """Get injection detection flag."""
        return self._is_injection_detected

    @is_injection_detected.setter
    def is_injection_detected(self, value: bool):
        """Set injection detection flag for testing."""
        self._is_injection_detected = value


@pytest.fixture
def fake_prompt_sanitizer():
    """
    Provides fake prompt sanitizer for text processor testing.

    Returns a FakePromptSanitizer instance that tracks sanitization calls
    without performing actual security validation, enabling tests to verify
    proper input sanitization behavior.

    Default Behavior:
        - No injection detected (happy path)
        - All inputs pass through unchanged
        - Call tracking enabled for verification
        - Stateful - tracks all calls during test

    Use Cases:
        - Testing input sanitization before AI calls
        - Testing options sanitization
        - Testing injection detection handling
        - Verifying sanitization is called for all operations
        - Testing error paths when injection detected

    Test Customization:
        def test_sanitizes_all_inputs(fake_prompt_sanitizer):
            processor = TextProcessorService(settings, cache, fake_prompt_sanitizer)
            await processor.process_text(request)
            
            # Verify sanitization was called
            calls = fake_prompt_sanitizer.get_sanitization_calls()
            assert len(calls) > 0
            assert ("text", request.text) in calls

    Examples:
        >>> # Test sanitization tracking
        >>> sanitizer = fake_prompt_sanitizer()
        >>> sanitizer.sanitize_input("test text")
        'test text'
        >>> calls = sanitizer.get_sanitization_calls()
        >>> assert ("text", "test text") in calls

        >>> # Test injection detection configuration
        >>> sanitizer.is_injection_detected = True
        >>> # Now tests can verify injection handling
    """
    return FakePromptSanitizer()


# =============================================================================
# Mock ResponseValidator (Complex Validation Logic)
# =============================================================================


@pytest.fixture
def mock_response_validator():
    """
    Provides spec'd mock for ResponseValidator from app.services.response_validator.

    Creates a mock of the ResponseValidator class with default behavior for
    successful validation. Tests can reconfigure to simulate validation failures,
    security issues, or quality problems.

    Default Behavior:
        - validate_response(): Returns True (validation passes)
        - is_safe_response(): Returns True (no security issues)
        - All validation methods are async mocks

    Customization:
        Individual tests can configure the mock to simulate different validation
        scenarios (failures, security issues, quality problems).

    Use Cases:
        - Testing response validation after AI processing
        - Testing validation failure handling
        - Testing security issue detection
        - Verifying validation is called for all operations
        - Testing error handling when validation fails

    Test Customization:
        def test_handles_validation_failure(mock_response_validator):
            # Configure mock to fail validation
            mock_response_validator.validate_response = AsyncMock(return_value=False)
            mock_response_validator.get_validation_error = Mock(
                return_value="Response contains harmful content"
            )
            
            # Test should handle validation failure
            processor = TextProcessorService(settings, cache, validator=mock_response_validator)
            with pytest.raises(ValidationError):
                await processor.process_text(request)

    Examples:
        >>> # Default behavior (validation passes)
        >>> result = await mock_response_validator.validate_response(response)
        >>> assert result is True

        >>> # Configure to fail validation
        >>> mock_response_validator.validate_response = AsyncMock(return_value=False)
        >>> result = await mock_response_validator.validate_response(response)
        >>> assert result is False

    Note:
        This is an external dependency to text_processor (different service),
        so mocking is appropriate. The validator has complex logic that we
        don't want to test as part of text processor unit tests.
    """
    from app.services.response_validator import ResponseValidator
    
    mock = create_autospec(ResponseValidator, instance=True)

    # Configure default happy path behavior
    # validate() method returns the validated string (passthrough on success)
    mock.validate = Mock(side_effect=lambda text, *args, **kwargs: text)
    mock.validate_response = AsyncMock(return_value=True)
    mock.is_safe_response = AsyncMock(return_value=True)
    mock.get_validation_error = Mock(return_value=None)

    return mock


# =============================================================================
# Mock AI Resilience Orchestrator (External Singleton)
# =============================================================================


@pytest.fixture
def mock_ai_resilience():
    """
    Provides spec'd mock for AI resilience orchestrator singleton.

    Creates a mock of the global ai_resilience orchestrator from
    app.infrastructure.resilience, enabling tests to verify resilience
    patterns are applied without actually executing circuit breakers,
    retries, or fallback logic.

    Default Behavior:
        - register_operation(): No-op registration
        - get_health_status(): Returns healthy status
        - get_metrics(): Returns empty metrics
        - Circuit breaker methods available for configuration

    Customization:
        Tests can configure circuit breaker states, retry behavior,
        and fallback responses to simulate different resilience scenarios.

    Use Cases:
        - Testing operation registration with resilience service
        - Testing resilience strategy application
        - Testing circuit breaker integration
        - Testing fallback response handling
        - Verifying resilience patterns are used

    Test Customization:
        def test_applies_balanced_resilience(mock_ai_resilience):
            processor = TextProcessorService(settings, cache)
            
            # Verify balanced resilience registered for summarize
            mock_ai_resilience.register_operation.assert_any_call(
                operation_name="summarize",
                strategy="balanced"
            )

    Examples:
        >>> # Verify operation registration
        >>> processor = TextProcessorService(settings, cache)
        >>> mock_ai_resilience.register_operation.assert_called()

        >>> # Configure circuit breaker state
        >>> mock_ai_resilience.is_circuit_open = Mock(return_value=True)
        >>> # Tests can now verify open circuit handling

    Note:
        ai_resilience is a global singleton orchestrator from infrastructure.
        Mocking is appropriate as it's a system boundary and we don't want
        to test actual resilience execution in text processor unit tests.
    """
    mock = Mock()
    
    # Configure default methods
    mock.register_operation = Mock()
    mock.get_health_status = Mock(return_value={"status": "healthy"})
    mock.get_metrics = Mock(return_value={})
    mock.is_circuit_open = Mock(return_value=False)
    mock.record_success = Mock()
    mock.record_failure = Mock()
    
    return mock


# =============================================================================
# Mock PydanticAI Agent (External Library)
# =============================================================================


@pytest.fixture
def mock_pydantic_agent():
    """
    Provides spec'd mock for PydanticAI Agent from pydantic_ai library.

    Creates a mock of the Agent class with configurable run_sync method
    for testing AI processing without making actual API calls to Gemini.

    Default Behavior:
        - run_sync(): Returns configurable mock response
        - Configuration can be set per test for different responses
        - Async methods available as AsyncMock

    Customization:
        Tests configure return values for different operations (summarize,
        sentiment, key_points, questions, QA).

    Use Cases:
        - Testing AI processing logic without API calls
        - Testing different AI response formats
        - Testing error handling from AI failures
        - Testing timeout and rate limit scenarios
        - Verifying proper prompt construction

    Test Customization:
        def test_summarize_operation(mock_pydantic_agent):
            # Configure agent to return summary
            mock_response = Mock()
            mock_response.data = "This is a test summary"
            mock_pydantic_agent.run_sync = AsyncMock(return_value=mock_response)
            
            # Test processes with mocked AI response
            processor = TextProcessorService(settings, cache)
            response = await processor.process_text(summarize_request)
            assert response.result == "This is a test summary"

    Examples:
        >>> # Configure for summarize operation
        >>> mock_response = Mock(data="Test summary")
        >>> mock_pydantic_agent.run_sync = AsyncMock(return_value=mock_response)

        >>> # Configure for sentiment operation
        >>> mock_sentiment = Mock(sentiment="positive", confidence=0.95)
        >>> mock_response = Mock(data=mock_sentiment)
        >>> mock_pydantic_agent.run_sync = AsyncMock(return_value=mock_response)

    Note:
        PydanticAI Agent is an external library (system boundary), so mocking
        is appropriate. We don't want to test pydantic_ai's functionality or
        make actual API calls in unit tests.
    """
    from pydantic_ai import Agent
    
    mock = create_autospec(Agent, instance=True)
    
    # Configure default async method
    mock.run = AsyncMock()

    # Configure response structure (tests can override)
    default_response = Mock()
    default_response.output = Mock()
    default_response.output.strip.return_value = "Default AI response"
    default_response.data = "Default AI response"
    mock.run.return_value = default_response
    
    return mock


# =============================================================================
# Convenience Fixtures for Common Test Scenarios
# =============================================================================


@pytest.fixture
def fake_cache_with_hit(fake_cache):
    """
    Pre-configured fake cache with cached response for testing cache hits.

    Provides a cache instance with a pre-populated summarize response,
    useful for testing cache-first strategy and cache hit scenarios.

    Returns:
        FakeCache with cached summarize response

    Use Cases:
        - Testing cache hit behavior
        - Testing cache_hit=True in response
        - Testing processing time with cache hits
        - Verifying AI is not called when cache hits
    """
    # Pre-populate with a typical cached response that matches our test request
    import asyncio

    # Calculate the cache key that will match our test request
    test_text = "Sample text for testing"
    test_operation = "summarize"
    test_options = {"max_length": 100}
    cache_key = fake_cache.build_cache_key(test_text, test_operation, test_options)

    asyncio.run(fake_cache.set(
        cache_key,
        {
            "operation": "summarize",
            "result": "Cached summary of sample text content",
            "cache_hit": False,  # Original response wasn't from cache
            "processing_time": 0.01,  # Fast processing time for cache hit test
            "metadata": {"word_count": 100}
        },
        ttl=7200
    ))
    return fake_cache


@pytest.fixture
def mock_response_validator_with_failure(mock_response_validator):
    """
    Pre-configured mock validator that fails validation.

    Provides a ResponseValidator mock configured to fail validation,
    useful for testing validation failure handling.

    Returns:
        Mock configured to:
        - validate() raises ValueError (validation failure)
        - validate_response() returns False
        - get_validation_error() returns error message

    Use Cases:
        - Testing validation failure handling
        - Testing error responses when validation fails
        - Testing validation error logging
    """
    # Configure validate() to raise ValueError (this is what production code catches)
    mock_response_validator.validate = Mock(
        side_effect=ValueError("Response validation failed: harmful content detected")
    )
    mock_response_validator.validate_response = AsyncMock(return_value=False)
    mock_response_validator.get_validation_error = Mock(
        return_value="Response validation failed: harmful content detected"
    )
    return mock_response_validator


@pytest.fixture
def mock_ai_resilience_with_open_circuit(mock_ai_resilience):
    """
    Pre-configured mock resilience orchestrator with open circuit breaker.

    Provides an ai_resilience mock configured with open circuit breaker,
    useful for testing circuit breaker behavior and fallback responses.

    Returns:
        Mock configured with:
        - is_circuit_open() returns True
        - Simulates circuit breaker open state

    Use Cases:
        - Testing circuit breaker open behavior
        - Testing fallback response generation
        - Testing service degradation handling
        - Testing circuit breaker state logging
    """
    mock_ai_resilience.is_circuit_open = Mock(return_value=True)
    return mock_ai_resilience

