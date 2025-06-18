"""
Retry Module

This file provides the logic for request retries, including configurable
strategies, custom exception types, and exception classification for
determining whether a failed operation should be attempted again.
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
from .circuit_breaker import AIServiceException


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