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
    """
    Configuration for retry behavior with exponential backoff and jitter.
    
    Attributes:
        max_attempts: Maximum number of retry attempts
        max_delay_seconds: Maximum delay between retries in seconds
        exponential_multiplier: Multiplier for exponential backoff calculation
        exponential_min: Minimum delay for exponential backoff in seconds
        exponential_max: Maximum delay for exponential backoff in seconds
        jitter: Whether to add random jitter to prevent thundering herd
        jitter_max: Maximum jitter value to add to delays in seconds
    """
    max_attempts: int = 3
    max_delay_seconds: int = 60
    exponential_multiplier: float = 1.0
    exponential_min: float = 2.0
    exponential_max: float = 10.0
    jitter: bool = True
    jitter_max: float = 2.0


# Import all AI service exceptions from centralized location
from app.core.exceptions import (
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    classify_ai_exception,
)


def classify_exception(exc: Exception) -> bool:
    """
    Classify whether an exception should trigger retries.

    Returns True if the exception is transient and should be retried.
    
    Note: This function is now a wrapper around the centralized
    classify_ai_exception function in core.exceptions.
    """
    return classify_ai_exception(exc)


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