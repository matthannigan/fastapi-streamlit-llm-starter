"""
Custom test assertions for enhanced testing.

This module provides custom assertion helpers that extend pytest
capabilities for domain-specific testing scenarios.
"""
import pytest
from typing import Any, Dict, List


def assert_valid_response_structure(response_data: Dict[str, Any], required_fields: List[str]):
    """Assert that a response has the required structure."""
    assert isinstance(response_data, dict), "Response must be a dictionary"
    
    for field in required_fields:
        assert field in response_data, f"Required field '{field}' missing from response"


def assert_cache_hit_rate(hits: int, total: int, min_rate: float = 0.8):
    """Assert that cache hit rate meets minimum threshold."""
    rate = hits / total if total > 0 else 0
    assert rate >= min_rate, f"Cache hit rate {rate:.2%} below minimum {min_rate:.2%}"


def assert_response_time_within_limits(duration: float, max_duration: float = 1.0):
    """Assert that response time is within acceptable limits."""
    assert duration <= max_duration, f"Response time {duration:.3f}s exceeds limit {max_duration:.3f}s"


def assert_valid_api_key_format(api_key: str):
    """Assert that API key has valid format."""
    assert isinstance(api_key, str), "API key must be a string"
    assert len(api_key) >= 10, "API key must be at least 10 characters"
    assert api_key.strip() == api_key, "API key must not have leading/trailing whitespace"
