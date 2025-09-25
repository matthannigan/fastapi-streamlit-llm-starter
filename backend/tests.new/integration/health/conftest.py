"""
Pytest fixtures for health monitoring integration tests.

This module provides fixtures for testing health monitoring system integration
with cache services, resilience patterns, AI services, and monitoring APIs.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from fakeredis import FakeStrictRedis

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    SystemHealthStatus,
    HealthCheckError,
    HealthCheckTimeoutError,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
    check_database_health,
)
from app.infrastructure.cache import AIResponseCache, CachePerformanceMonitor
from app.core.config import Settings


@pytest.fixture
def health_checker():
    """Create a basic HealthChecker instance for testing."""
    return HealthChecker(
        default_timeout_ms=2000,
        per_component_timeouts_ms={},
        retry_count=1,
        backoff_base_seconds=0.1,
    )


@pytest.fixture
def health_checker_with_custom_timeouts():
    """Create a HealthChecker with custom component-specific timeouts."""
    return HealthChecker(
        default_timeout_ms=5000,
        per_component_timeouts_ms={
            "slow_component": 10000,
            "fast_component": 500,
        },
        retry_count=2,
        backoff_base_seconds=0.2,
    )


@pytest.fixture
def mock_cache_service():
    """Mock AIResponseCache for health check testing."""
    mock_cache = AsyncMock(spec=AIResponseCache)
    mock_cache.connect = AsyncMock()
    mock_cache.get_cache_stats = AsyncMock(return_value={
        "redis": {"status": "connected"},
        "memory": {"status": "available"},
        "total_keys": 10,
        "memory_usage_mb": 5.0
    })
    return mock_cache


@pytest.fixture
def fake_redis_cache():
    """Create AIResponseCache with FakeStrictRedis for integration testing."""
    fake_redis = FakeStrictRedis(decode_responses=True)
    cache = AIResponseCache(
        redis_url="redis://localhost:6379",  # fakeredis will use this
        default_ttl=3600,
        text_hash_threshold=1000,
        memory_cache_size=100,
        performance_monitor=Mock(spec=CachePerformanceMonitor),
        text_size_tiers={
            "small": 500,
            "medium": 5000,
            "large": 50000,
        },
    )
    # Patch the redis connection to use fakeredis
    cache.redis = fake_redis
    return cache


@pytest.fixture
def mock_resilience_service():
    """Mock resilience service for health check testing."""
    mock_resilience = Mock()
    mock_resilience.get_health_status.return_value = {
        "healthy": True,
        "open_circuit_breakers": [],
        "half_open_circuit_breakers": [],
        "total_circuit_breakers": 5,
        "operations": {"retry": {"success": 100, "failure": 5}}
    }
    mock_resilience.get_all_metrics.return_value = {
        "circuit_breakers": {"test_cb": {"state": "closed"}},
        "operations": {"retry": {"success": 100, "failure": 5}}
    }
    return mock_resilience


@pytest.fixture
def mock_unhealthy_resilience_service():
    """Mock resilience service with unhealthy status for testing."""
    mock_resilience = Mock()
    mock_resilience.get_health_status.return_value = {
        "healthy": False,
        "open_circuit_breakers": ["test_cb"],
        "half_open_circuit_breakers": [],
        "total_circuit_breakers": 5,
        "operations": {"retry": {"success": 10, "failure": 50}}
    }
    return mock_resilience


@pytest.fixture
def mock_ai_service():
    """Mock AI service for health check testing."""
    mock_service = Mock()
    mock_service.health_check.return_value = "healthy"
    return mock_service


@pytest.fixture
def settings_with_gemini_key():
    """Settings instance with valid Gemini API key."""
    return Settings(
        gemini_api_key="test-gemini-api-key-12345",
        api_key="test-api-key-12345",
        ai_model="gemini-2.0-flash-exp",
        ai_temperature=0.7,
        host="0.0.0.0",
        port=8000,
        debug=False,
        log_level="INFO",
        resilience_enabled=True,
        default_resilience_strategy="balanced",
        resilience_preset="simple",
        allowed_origins=["http://localhost:3000"],
    )


@pytest.fixture
def settings_without_gemini_key():
    """Settings instance without Gemini API key."""
    return Settings(
        gemini_api_key="",  # Empty key to simulate missing API key
        api_key="test-api-key-12345",
        ai_model="gemini-2.0-flash-exp",
        ai_temperature=0.7,
        host="0.0.0.0",
        port=8000,
        debug=False,
        log_level="INFO",
        resilience_enabled=True,
        default_resilience_strategy="balanced",
        resilience_preset="simple",
        allowed_origins=["http://localhost:3000"],
    )


@pytest.fixture
def mock_database_connection():
    """Mock database connection for health check testing."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    return mock_conn


@pytest.fixture
def failing_health_check():
    """Health check function that always fails."""
    async def fail_check():
        raise HealthCheckError("Simulated failure for testing")
    return fail_check


@pytest.fixture
def timeout_health_check():
    """Health check function that always times out."""
    async def timeout_check():
        await asyncio.sleep(5)  # Longer than typical timeout
        return ComponentStatus("timeout_test", HealthStatus.HEALTHY)
    return timeout_check


@pytest.fixture
def degraded_health_check():
    """Health check function that returns degraded status."""
    async def degraded_check():
        return ComponentStatus("degraded_test", HealthStatus.DEGRADED, "Service degraded")
    return degraded_check


@pytest.fixture
def slow_health_check():
    """Health check function that takes time but succeeds."""
    async def slow_check():
        await asyncio.sleep(0.1)  # 100ms delay
        return ComponentStatus("slow_test", HealthStatus.HEALTHY, "Slow but healthy")
    return slow_check


@pytest.fixture
def performance_monitor():
    """Create a CachePerformanceMonitor instance for testing."""
    return CachePerformanceMonitor(
        retention_hours=1,
        max_measurements=100,  # Smaller for testing
        memory_warning_threshold_bytes=10 * 1024 * 1024,  # 10MB for testing
        memory_critical_threshold_bytes=20 * 1024 * 1024   # 20MB for testing
    )


@pytest.fixture
def sample_health_check():
    """Sample health check function for testing registration."""
    async def sample_check():
        return ComponentStatus("sample", HealthStatus.HEALTHY, "Sample check working")
    return sample_check
