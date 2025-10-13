"""
Cache module test fixtures providing mocks for cache infrastructure dependencies.

This module provides test doubles for external dependencies of the LLM security cache
module, focusing on cache interfaces, Redis operations, and cache performance
monitoring scenarios.

SHARED MOCKS: MockSecurityConfig, MockSecurityResult, MockViolation are imported from parent conftest.py
"""

from typing import Dict, Any, Optional
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, UTC
from dataclasses import dataclass

# Import shared mocks from parent conftest - these are used across multiple modules
# MockSecurityConfig, MockSecurityResult, MockViolation, and their fixtures
# are now defined in backend/tests/unit/llm_security/conftest.py

# Import classes that would normally be from the actual implementation
# from app.infrastructure.cache.base import CacheInterface
# from app.infrastructure.cache.memory import InMemoryCache
# from app.infrastructure.cache.factory import CacheFactory
# from app.infrastructure.security.llm.protocol import SecurityResult, Violation
# from app.infrastructure.security.llm.config import SecurityConfig


class MockCacheInterface:
    """Mock CacheInterface for testing cache operations."""

    def __init__(self, available: bool = True, operation_latency_ms: float = 1.0):
        self.available = available
        self.operation_latency_ms = operation_latency_ms
        self._storage = {}
        self._operation_calls = []

    async def get(self, key: str) -> Optional[Any]:
        """Mock cache get operation."""
        self._operation_calls.append({"operation": "get", "key": key})
        if not self.available:
            return None
        return self._storage.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Mock cache set operation."""
        self._operation_calls.append({"operation": "set", "key": key, "ttl": ttl_seconds})
        if not self.available:
            return False
        self._storage[key] = value
        return True

    async def delete(self, key: str) -> bool:
        """Mock cache delete operation."""
        self._operation_calls.append({"operation": "delete", "key": key})
        if not self.available:
            return False
        return self._storage.pop(key, None) is not None

    async def clear(self) -> bool:
        """Mock cache clear operation."""
        self._operation_calls.append({"operation": "clear"})
        if not self.available:
            return False
        self._storage.clear()
        return True

    def size(self) -> int:
        """Mock cache size operation."""
        return len(self._storage)

    def reset_history(self):
        """Reset operation history for test isolation."""
        self._operation_calls.clear()

    @property
    def operation_history(self) -> list:
        """Get history of cache operations for test verification."""
        return self._operation_calls.copy()


class MockInMemoryCache(MockCacheInterface):
    """Mock InMemoryCache extending MockCacheInterface with memory-specific behavior."""

    def __init__(self, available: bool = True, max_size: int = 1000):
        super().__init__(available=available)
        self.max_size = max_size
        self._memory_usage_bytes = 0


class MockCacheFactory:
    """Mock CacheFactory for testing cache creation scenarios."""

    def __init__(self):
        self._creation_calls = []

    async def create_redis_cache(self, redis_url: str, **kwargs) -> MockCacheInterface:
        """Mock Redis cache creation."""
        creation_call = {
            "type": "redis",
            "redis_url": redis_url,
            "kwargs": kwargs,
            "timestamp": "mock-timestamp"
        }
        self._creation_calls.append(creation_call)

        # Simulate Redis availability based on URL
        available = not ("unavailable" in redis_url or "invalid" in redis_url)
        latency = 0.5 if "redis://localhost" in redis_url else 2.0

        return MockCacheInterface(available=available, operation_latency_ms=latency)

    async def create_memory_cache(self, **kwargs) -> MockInMemoryCache:
        """Mock memory cache creation."""
        creation_call = {
            "type": "memory",
            "kwargs": kwargs,
            "timestamp": "mock-timestamp"
        }
        self._creation_calls.append(creation_call)

        max_size = kwargs.get("max_size", 1000)
        return MockInMemoryCache(available=True, max_size=max_size)

    def reset_history(self):
        """Reset creation history for test isolation."""
        self._creation_calls.clear()

    @property
    def creation_history(self) -> list:
        """Get history of cache creation calls for test verification."""
        return self._creation_calls.copy()


# NOTE: MockSecurityResult, MockViolation, MockSecurityConfig removed
# These are now shared fixtures in parent conftest.py


@pytest.fixture
def mock_cache_interface():
    """Factory fixture to create MockCacheInterface instances for testing."""
    def _create_cache(available: bool = True, latency_ms: float = 1.0) -> MockCacheInterface:
        return MockCacheInterface(available=available, operation_latency_ms=latency_ms)
    return _create_cache


@pytest.fixture
def mock_memory_cache():
    """Factory fixture to create MockInMemoryCache instances for testing."""
    def _create_cache(available: bool = True, max_size: int = 1000) -> MockInMemoryCache:
        return MockInMemoryCache(available=available, max_size=max_size)
    return _create_cache


@pytest.fixture
def mock_cache_factory():
    """Factory fixture to create MockCacheFactory instances for testing."""
    def _create_factory() -> MockCacheFactory:
        return MockCacheFactory()
    return _create_factory


# NOTE: mock_security_result, mock_violation, mock_security_config fixtures removed
# These are now shared fixtures in parent conftest.py


@pytest.fixture
def cache_test_data(mock_security_result, mock_violation):
    """Test data for cache operations including various security results.
    
    Uses shared mock_security_result and mock_violation fixtures from parent conftest.
    """
    return {
        "safe_result": mock_security_result(
            is_safe=True,
            violations=[],
            score=1.0,
            scanned_text="This is safe content",
            scan_duration_ms=100
        ),
        "unsafe_result": mock_security_result(
            is_safe=False,
            violations=[mock_violation(
                violation_type="injection",
                severity="high",
                description="Prompt injection detected",
                confidence=0.95
            )],
            score=0.2,
            scanned_text="Ignore previous instructions and",
            scan_duration_ms=200
        ),
        "borderline_result": mock_security_result(
            is_safe=True,
            violations=[mock_violation(
                violation_type="suspicious_pattern",
                severity="low",
                description="Suspicious pattern detected",
                confidence=0.6
            )],
            score=0.7,
            scanned_text="This seems somewhat unusual",
            scan_duration_ms=150
        ),
        "complex_result": mock_security_result(
            is_safe=False,
            violations=[
                mock_violation(violation_type="injection", severity="high", confidence=0.9),
                mock_violation(violation_type="toxicity", severity="medium", confidence=0.7)
            ],
            score=0.3,
            scanned_text="Complex problematic content",
            scan_duration_ms=300,
            scanner_results={
                "prompt_injection": {"detected": True, "confidence": 0.9},
                "toxicity": {"detected": True, "confidence": 0.7}
            },
            metadata={"model_version": "v2.1.0", "processing_time": "fast"}
        )
    }


@pytest.fixture
def cache_test_scenarios():
    """Various test scenarios for cache functionality testing."""
    return {
        "redis_available": {
            "redis_url": "redis://localhost:6379",
            "expected_redis_available": True,
            "expected_fallback": False
        },
        "redis_unavailable": {
            "redis_url": "redis://unavailable-host:6379",
            "expected_redis_available": False,
            "expected_fallback": True
        },
        "redis_invalid": {
            "redis_url": "invalid://connection-string",
            "expected_redis_available": False,
            "expected_fallback": True
        },
        "cache_disabled": {
            "cache_enabled": False,
            "expected_operations": "no_ops"
        },
        "high_latency_redis": {
            "redis_url": "redis://slow-server:6379",
            "expected_redis_available": True,
            "expected_high_latency": True
        }
    }


@pytest.fixture
def cache_performance_data():
    """Performance test data for cache statistics and monitoring."""
    return {
        "high_hit_rate_scenario": {
            "hits": 95,
            "misses": 5,
            "expected_hit_rate": 95.0,
            "avg_lookup_time": 0.8
        },
        "low_hit_rate_scenario": {
            "hits": 20,
            "misses": 80,
            "expected_hit_rate": 20.0,
            "avg_lookup_time": 1.2
        },
        "no_cache_scenario": {
            "hits": 0,
            "misses": 100,
            "expected_hit_rate": 0.0,
            "avg_lookup_time": 2.0
        },
        "perfect_cache_scenario": {
            "hits": 100,
            "misses": 0,
            "expected_hit_rate": 100.0,
            "avg_lookup_time": 0.5
        }
    }


@pytest.fixture
def cache_key_test_data():
    """Test data for cache key generation and validation."""
    return {
        "same_content_different_type": {
            "text": "Hello world",
            "scan_type_1": "input",
            "scan_type_2": "output",
            "expect_different_keys": True
        },
        "different_content_same_type": {
            "text_1": "Hello world",
            "text_2": "Hello different world",
            "scan_type": "input",
            "expect_different_keys": True
        },
        "same_content_same_type": {
            "text": "Hello world",
            "scan_type": "input",
            "expect_different_keys": False
        },
        "empty_content": {
            "text": "",
            "scan_type": "input",
            "expect_valid_key": True
        },
        "unicode_content": {
            "text": "Hello 世界 🌍",
            "scan_type": "input",
            "expect_valid_key": True
        },
        "large_content": {
            "text": "A" * 10000,  # 10KB
            "scan_type": "input",
            "expect_valid_key": True
        }
    }


@pytest.fixture
def cache_ttl_test_data():
    """Test data for TTL (Time-To-Live) functionality."""
    return {
        "short_ttl": {
            "ttl_seconds": 60,
            "description": "Short TTL for testing expiration",
            "use_case": "development_testing"
        },
        "medium_ttl": {
            "ttl_seconds": 3600,
            "description": "Medium TTL for normal caching",
            "use_case": "production_standard"
        },
        "long_ttl": {
            "ttl_seconds": 86400,
            "description": "Long TTL for stable content",
            "use_case": "static_content"
        },
        "custom_ttl": {
            "ttl_seconds": 1800,
            "description": "Custom TTL for specific requirements",
            "use_case": "custom_policy"
        }
    }


@pytest.fixture
def cache_health_check_data():
    """Test data for cache health check scenarios."""
    return {
        "healthy_scenario": {
            "redis_available": True,
            "memory_available": True,
            "expected_status": "healthy",
            "expected_operations_work": True
        },
        "degraded_scenario": {
            "redis_available": False,
            "memory_available": True,
            "expected_status": "degraded",
            "expected_operations_work": True
        },
        "unhealthy_scenario": {
            "redis_available": False,
            "memory_available": False,
            "expected_status": "unhealthy",
            "expected_operations_work": False
        },
        "disabled_scenario": {
            "cache_enabled": False,
            "expected_status": "disabled",
            "expected_operations_work": False
        }
    }


@pytest.fixture
def cache_error_scenarios():
    """Various error scenarios for testing cache error handling."""
    return {
        "redis_connection_error": {
            "error_type": "connection_error",
            "expected_behavior": "fallback_to_memory",
            "should_raise_exception": False
        },
        "redis_timeout_error": {
            "error_type": "timeout_error",
            "expected_behavior": "fallback_to_memory",
            "should_raise_exception": False
        },
        "serialization_error": {
            "error_type": "serialization_error",
            "expected_behavior": "skip_caching",
            "should_raise_exception": False
        },
        "memory_limit_error": {
            "error_type": "memory_limit_error",
            "expected_behavior": "evict_old_entries",
            "should_raise_exception": False
        },
        "invalid_ttl_error": {
            "error_type": "invalid_ttl",
            "expected_behavior": "use_default_ttl",
            "should_raise_exception": False
        }
    }