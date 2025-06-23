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

Integration Notes:
-----------------
- Works seamlessly with circuit breaker patterns
- Imports shared exceptions to maintain consistency across resilience components
- Designed for async/await patterns but compatible with synchronous code
- Follows fail-fast principles for permanent errors while being resilient to transients

The module emphasizes intelligent retry decisions over blind retry attempts,
helping to reduce unnecessary load on failing services while maximizing
success rates for recoverable failures.
"""

from dataclasses import dataclass
import httpx


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    max_delay_seconds: int = 60
    exponential_multiplier: float = 1.0
    exponential_min: float = 2.0
    exponential_max: float = 10.0
    jitter: bool = True
    jitter_max: float = 2.0


# Import shared exceptions from circuit_breaker module to avoid duplication
from app.infrastructure.resilience.circuit_breaker import AIServiceException


class TransientAIError(AIServiceException):
    """Transient AI service error that should be retried."""
    pass


class PermanentAIError(AIServiceException):
    """Permanent AI service error that should not be retried."""
    pass


class RateLimitError(TransientAIError):
    """Rate limit exceeded error."""
    pass


class ServiceUnavailableError(TransientAIError):
    """AI service temporarily unavailable."""
    pass


def classify_exception(exc: Exception) -> bool:
    """
    Classify whether an exception should trigger retries.

    Returns True if the exception is transient and should be retried.
    """
    # Network and connection errors (should retry)
    if isinstance(exc, (
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError,
        TransientAIError,
        RateLimitError,
        ServiceUnavailableError
    )):
        return True

    # HTTP errors that should be retried
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        # Retry on server errors and rate limits
        if status_code in (429, 500, 502, 503, 504):
            return True
        # Don't retry on client errors
        if 400 <= status_code < 500:
            return False

    # Permanent errors (should not retry)
    if isinstance(exc, (
        PermanentAIError,
        ValueError,
        TypeError,
        AttributeError
    )):
        return False

    # Default: retry on unknown exceptions (conservative approach)
    return True


def should_retry_on_exception(retry_state) -> bool:
    """
    Tenacity-compatible function to determine if an exception should trigger a retry.

    Args:
        retry_state: Tenacity retry state object containing exception information

    Returns:
        True if the exception should trigger a retry
    """
    if hasattr(retry_state, 'outcome') and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        return classify_exception(exception)
    return False