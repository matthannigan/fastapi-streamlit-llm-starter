---
sidebar_label: retry
---

# Retry Module - Resilient Request Retry Logic

  file_path: `backend/app/infrastructure/resilience/retry.py`

This module provides a comprehensive retry mechanism for handling transient failures
in AI service requests and other network operations. It implements intelligent
exception classification, configurable retry strategies, and seamless integration
with the Tenacity retry library.

## Key Components

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

## Usage Examples

--------------

## Basic configuration

config = RetryConfig(
max_attempts=5,
max_delay_seconds=120,
exponential_multiplier=2.0,
jitter=True
)

## With Tenacity decorator

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
retry=should_retry_on_exception,
stop=stop_after_attempt(config.max_attempts),
wait=wait_exponential(multiplier=config.exponential_multiplier)
)
async def make_ai_request():
# Your AI service call here
pass

## Exception classification

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

## Integration Notes

-----------------
- Works seamlessly with circuit breaker patterns
- Imports shared exceptions to maintain consistency across resilience components
- Designed for async/await patterns but compatible with synchronous code
- Follows fail-fast principles for permanent errors while being resilient to transients

The module emphasizes intelligent retry decisions over blind retry attempts,
helping to reduce unnecessary load on failing services while maximizing
success rates for recoverable failures.
