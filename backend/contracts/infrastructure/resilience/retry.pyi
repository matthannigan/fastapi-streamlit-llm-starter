"""
Retry Module - Resilient Request Retry Logic

This module provides a comprehensive retry mechanism for handling transient failures
in AI service requests and other network operations. It implements intelligent
exception classification, configurable retry strategies, and seamless integration
with the Tenacity retry library.

Key Components:
--------------
1. RetryConfig: Dataclass for configuring retry behavior including:
   - Maximum retry attempts and delay limits
   - Exponential backoff parameters with multipliers
   - Jitter configuration to prevent thundering herd effects

2. Exception Hierarchy: Custom exception types for proper error classification:
   - TransientAIError: Temporary errors that should be retried
   - PermanentAIError: Permanent errors that should not be retried
   - RateLimitError: Rate limiting errors requiring backoff
   - ServiceUnavailableError: Temporary service unavailability

3. Exception Classification: Smart logic to determine retry eligibility:
   - Network/connection errors: Always retry
   - HTTP status codes: Retry on 429, 5xx; skip on 4xx client errors
   - Custom AI errors: Based on error type classification
   - Unknown exceptions: Conservative retry approach

4. Tenacity Integration: Compatible functions for use with Tenacity decorators:
   - should_retry_on_exception(): Determines retry based on exception type
   - classify_exception(): Core classification logic for any exception

Usage Examples:
--------------
Basic configuration:
    config = RetryConfig(
        max_attempts=5,
        max_delay_seconds=120,
        exponential_multiplier=2.0,
        jitter=True
    )

With Tenacity decorator:
    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(
        retry=should_retry_on_exception,
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_exponential(multiplier=config.exponential_multiplier)
    )
    async def make_ai_request():
        # Your AI service call here
        pass

Exception classification:
    try:
        # Some operation that might fail
        result = await risky_operation()
    except Exception as e:
        if classify_exception(e):
            # This is a transient error, safe to retry
            await retry_operation()
        else:
            # Permanent error, don't retry
            raise

Tenacity integration examples:
    from tenacity import retry, stop_after_attempt, wait_exponential

    # Basic resilient operation
    @retry(
        retry=should_retry_on_exception,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1.0, min=2.0, max=10.0)
    )
    async def make_ai_request():
        # Your AI service call here
        return await ai_service.process()

    # Advanced configuration with custom retry policy
    config = RetryConfig(max_attempts=5, exponential_multiplier=2.0)

    @retry(
        retry=should_retry_on_exception,
        stop=stop_after_attempt(config.max_attempts),
        wait=wait_exponential(
            multiplier=config.exponential_multiplier,
            min=config.exponential_min,
            max=config.exponential_max
        )
    )
    async def critical_operation():
        # High-priority operation with aggressive retry
        return await mission_critical_service()

Integration Notes:
-----------------
- Works seamlessly with circuit breaker patterns and other resilience components
- Imports shared exceptions from core.exceptions for consistency across the system
- Designed for async/await patterns but fully compatible with synchronous code
- Follows fail-fast principles for permanent errors while being resilient to transients
- Integrates with monitoring and observability systems through structured logging
- Compatible with dependency injection and configuration management patterns

The module emphasizes intelligent retry decisions over blind retry attempts,
helping to reduce unnecessary load on failing services while maximizing
success rates for recoverable failures. All components include comprehensive
docstrings with usage examples and behavior specifications.
"""

from dataclasses import dataclass
from typing import Any
from app.core.exceptions import classify_ai_exception


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior with exponential backoff and jitter to prevent thundering herd effects.
    
    Provides comprehensive retry parameters for resilient service communication, including attempt limits,
    exponential backoff configuration, and jitter settings. Optimized for AI service patterns with
    production-ready defaults that balance resilience with resource efficiency.
    
    Attributes:
        max_attempts: Maximum number of retry attempts before giving up (1-20, default: 3)
        max_delay_seconds: Maximum delay between retries to cap exponential growth (1-3600, default: 60)
        exponential_multiplier: Multiplier for exponential backoff calculation (0.1-10.0, default: 1.0)
        exponential_min: Minimum delay for exponential backoff in seconds (0.1-60.0, default: 2.0)
        exponential_max: Maximum delay for exponential backoff in seconds (1.0-3600.0, default: 10.0)
        jitter: Whether to add random jitter to prevent synchronized retries (default: True)
        jitter_max: Maximum jitter to add to delays in seconds (0.1-60.0, default: 2.0)
    
    Public Methods:
        validate(): Validates all configuration parameters are within acceptable ranges
        to_dict(): Converts configuration to dictionary format for serialization
    
    State Management:
        - Immutable after initialization - create new instance for different configurations
        - Parameter validation occurs during initialization
        - Thread-safe for read operations across multiple threads
        - Compatible with Tenacity retry library decorators
        - Designed for use with dependency injection patterns
    
    Usage:
        # Default configuration suitable for most scenarios
        config = RetryConfig()
    
        # Aggressive retry for critical AI operations
        critical_config = RetryConfig(
            max_attempts=5,
            max_delay_seconds=120,
            exponential_multiplier=2.0,
            jitter_max=5.0
        )
    
        # Conservative retry for expensive operations
        conservative_config = RetryConfig(
            max_attempts=2,
            max_delay_seconds=30,
            exponential_multiplier=0.5,
            jitter=False
        )
    
        # Integration with Tenacity decorators
        from tenacity import retry, stop_after_attempt, wait_exponential
    
        @retry(
            stop=stop_after_attempt(config.max_attempts),
            wait=wait_exponential(
                multiplier=config.exponential_multiplier,
                min=config.exponential_min,
                max=config.exponential_max
            ),
            retry=should_retry_on_exception
        )
        async def resilient_ai_call():
            # AI service operation that may need retries
            return await ai_service.process_request()
    
        # Configuration validation for safety
        try:
            config = RetryConfig(max_attempts=25)  # Invalid: exceeds limit
        except ValidationError as e:
            print(f"Invalid configuration: {e}")
    """

    ...


def classify_exception(exc: Exception) -> bool:
    """
    Classify whether an exception represents a transient failure that should trigger retries.
    
    Determines if the given exception is recoverable through retry attempts based on exception type,
    error characteristics, and domain-specific classification rules. Focuses on identifying
    transient failures (network issues, rate limits, temporary service unavailability) versus
    permanent failures (authentication errors, invalid requests).
    
    Args:
        exc: Exception instance to classify for retry eligibility. Can be any exception type
            including HTTP errors, network failures, or custom AI service exceptions.
    
    Returns:
        bool: True if the exception represents a transient failure that should be retried,
        False if the exception is permanent and should not be retried.
    
    Behavior:
        - Delegates to centralized classify_ai_exception function for consistency
        - Classifies HTTP status codes: 429 (rate limit) and 5xx (server errors) as retryable
        - Treats network/connection errors as transient and retryable
        - Identifies custom TransientAIError instances as retryable
        - Rejects PermanentAIError, 4xx client errors, and authentication failures
        - Uses conservative retry approach for unknown exception types
        - Maintains consistency across all resilience components
    
    Examples:
        >>> # Transient network error - should retry
        >>> import httpx
        >>> exc = httpx.ConnectError("Connection timeout")
        >>> assert classify_exception(exc) == True
    
        >>> # Rate limit error - should retry
        >>> from app.core.exceptions import RateLimitError
        >>> exc = RateLimitError("Rate limit exceeded")
        >>> assert classify_exception(exc) == True
    
        >>> # Permanent authentication error - should not retry
        >>> from app.core.exceptions import PermanentAIError
        >>> exc = PermanentAIError("Invalid API key")
        >>> assert classify_exception(exc) == False
    
        >>> # HTTP client error - should not retry
        >>> exc = httpx.HTTPStatusError("Bad Request", request=None, response=None)
        >>> assert classify_exception(exc) == False
    
        >>> # Unknown exception - conservative approach
        >>> exc = ValueError("Unexpected error")
        >>> result = classify_exception(exc)  # Returns False for unknown types
    """
    ...


def should_retry_on_exception(retry_state: Any) -> bool:
    """
    Tenacity-compatible retry predicate that determines if an exception should trigger a retry attempt.
    
    Extracts exception information from Tenacity's retry state object and applies intelligent
    classification logic to determine retry eligibility. Designed to work with Tenacity's
    @retry decorator as the retry parameter.
    
    Args:
        retry_state: Tenacity RetryCallState object containing:
            - outcome: Future or result object with exception information
            - attempt_number: Current retry attempt number (1-based)
            - start_time: Timestamp when retry attempt began
            - action: Callable that triggered the exception
    
    Returns:
        bool: True if the exception from the retry state should trigger another retry attempt,
        False if the exception is permanent and retrying should stop.
    
    Raises:
        AttributeError: If retry_state object doesn't have expected attributes
        TypeError: If retry_state is None or not a valid RetryCallState
    
    Behavior:
        - Safely extracts exception from retry_state.outcome when available
        - Handles failed outcomes by retrieving the underlying exception
        - Returns False for successful outcomes (no retry needed)
        - Delegates exception classification to classify_exception function
        - Maintains compatibility with Tenacity's retry mechanism
        - Gracefully handles malformed retry_state objects
        - Logs retry decisions for monitoring and debugging
    
    Examples:
        >>> # Usage with Tenacity retry decorator
        >>> from tenacity import retry, stop_after_attempt
        >>>
        >>> @retry(
        ...     stop=stop_after_attempt(3),
        ...     retry=should_retry_on_exception
        ... )
        >>> async def resilient_api_call():
        ...     # Function that may fail with transient errors
        ...     return await external_service_request()
    
        >>> # Direct testing with mock retry state
        >>> from unittest.mock import Mock
        >>> mock_state = Mock()
        >>> mock_state.outcome.failed = True
        >>> mock_state.outcome.exception.return_value = ValueError("test")
        >>> result = should_retry_on_exception(mock_state)
    
        >>> # Integration with custom retry strategies
        >>> from tenacity import RetryError, Retrying, stop_after_attempt
        >>>
        >>> for attempt in Retrying(
        ...     stop=stop_after_attempt(3),
        ...     retry=should_retry_on_exception
        ... ):
        ...     with attempt:
        ...         result = risky_operation()
    """
    ...
