"""
Health check infrastructure test fixtures providing dependencies for unit testing.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the health monitoring component from systems outside its boundary.

Dependencies covered:
- Settings configuration (Real import from conftest.py)
- Cache service (Fake)
- Resilience orchestrator (Fake)
- AI configuration (via Settings)
- Time utilities (Real imports)
- Asyncio utilities (Real imports)
- Logging (Real imports)
"""

import pytest
from typing import Dict, Any, List, Optional
from unittest.mock import AsyncMock


class FakeCacheService:
    """
    Fake cache service for testing health check behavior.

    Provides a lightweight, in-memory cache implementation that simulates
    the AIResponseCache interface without requiring Redis or complex setup.

    Behavior:
        - Stateful: Maintains operational status that can be controlled by tests
        - Supports get_cache_stats() method for health checks
        - Can simulate healthy, degraded, and failed states
        - No actual caching logic - pure test double

    State Control:
        - status: "healthy", "degraded", or "failed"
        - redis_available: Controls Redis availability simulation
        - memory_available: Controls memory cache availability simulation

    Usage:
        # Healthy cache with Redis
        cache = FakeCacheService()
        stats = await cache.get_cache_stats()
        assert stats["redis"]["status"] == "ok"

        # Degraded cache (Redis down, memory fallback)
        cache = FakeCacheService(redis_available=False)
        stats = await cache.get_cache_stats()
        assert stats["redis"]["status"] == "error"
        assert stats["memory"]["status"] == "ok"

        # Failed cache (both Redis and memory unavailable)
        cache = FakeCacheService(redis_available=False, memory_available=False)
        stats = await cache.get_cache_stats()
        assert "error" in stats
    """

    def __init__(
        self,
        redis_available: bool = True,
        memory_available: bool = True,
        connect_should_fail: bool = False
    ):
        """
        Initialize fake cache service with configurable availability.

        Args:
            redis_available: Whether Redis should be available (default: True)
            memory_available: Whether memory cache should be available (default: True)
            connect_should_fail: Whether connect() should raise exception (default: False)
        """
        self.redis_available = redis_available
        self.memory_available = memory_available
        self.connect_should_fail = connect_should_fail
        self.connected = False

    async def connect(self):
        """
        Simulate cache connection with optional failure.

        Raises:
            ConnectionError: When connect_should_fail is True
        """
        if self.connect_should_fail:
            # Update state to reflect Redis becoming unavailable due to connection failure
            self.redis_available = False
            raise ConnectionError("Simulated cache connection failure")
        self.connected = True

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Return cache statistics for health monitoring.

        Returns:
            Dict containing redis and memory cache status information
        """
        if not self.redis_available and not self.memory_available:
            return {
                "error": "Both Redis and memory cache unavailable",
                "redis": {"status": "error"},
                "memory": {"status": "unavailable"}
            }

        return {
            "redis": {
                "status": "ok" if self.redis_available else "error",
                "connection": "active" if self.redis_available else "failed"
            },
            "memory": {
                "status": "ok" if self.memory_available else "unavailable",
                "entries": 42 if self.memory_available else 0
            }
        }


class FakeResilienceOrchestrator:
    """
    Fake resilience orchestrator for testing health check behavior.

    Provides a lightweight orchestrator implementation that simulates circuit
    breaker states and resilience system health without actual resilience logic.

    Behavior:
        - Stateful: Maintains circuit breaker states that can be controlled
        - Supports get_health_status() method for health checks
        - Can simulate healthy, degraded (open breakers), and failed states
        - No actual resilience logic - pure test double

    State Control:
        - healthy: Overall resilience system health status
        - open_breakers: List of open circuit breaker names
        - half_open_breakers: List of half-open circuit breaker names
        - total_breakers: Total number of circuit breakers

    Usage:
        # Healthy resilience system (all breakers closed)
        orchestrator = FakeResilienceOrchestrator()
        health = orchestrator.get_health_status()
        assert health["healthy"] is True
        assert len(health["open_circuit_breakers"]) == 0

        # Degraded resilience (some breakers open)
        orchestrator = FakeResilienceOrchestrator(
            open_breakers=["ai_service", "external_api"]
        )
        health = orchestrator.get_health_status()
        assert health["healthy"] is False
        assert "ai_service" in health["open_circuit_breakers"]

        # Failed resilience system
        orchestrator = FakeResilienceOrchestrator(should_fail=True)
        with pytest.raises(RuntimeError):
            orchestrator.get_health_status()
    """

    def __init__(
        self,
        healthy: bool = True,
        open_breakers: Optional[List[str]] = None,
        half_open_breakers: Optional[List[str]] = None,
        total_breakers: int = 3,
        should_fail: bool = False
    ):
        """
        Initialize fake resilience orchestrator with configurable state.

        Args:
            healthy: Overall resilience system health (default: True)
            open_breakers: List of open circuit breaker names (default: empty)
            half_open_breakers: List of half-open circuit breaker names (default: empty)
            total_breakers: Total number of circuit breakers (default: 3)
            should_fail: Whether get_health_status() should raise exception (default: False)
        """
        self.healthy = healthy
        self.open_breakers = open_breakers or []
        self.half_open_breakers = half_open_breakers or []
        self.total_breakers = total_breakers
        self.should_fail = should_fail

    def get_health_status(self) -> Dict[str, Any]:
        """
        Return resilience system health status for monitoring.

        Returns:
            Dict containing circuit breaker states and health information

        Raises:
            RuntimeError: When should_fail is True
        """
        if self.should_fail:
            raise RuntimeError("Simulated resilience system failure")

        return {
            "healthy": self.healthy and len(self.open_breakers) == 0,
            "open_circuit_breakers": self.open_breakers,
            "half_open_circuit_breakers": self.half_open_breakers,
            "total_circuit_breakers": self.total_breakers
        }


@pytest.fixture
def fake_cache_service():
    """
    Provides a fake cache service for health check testing.

    Returns FakeCacheService instance with healthy default configuration:
    - Redis available and operational
    - Memory cache available and operational
    - Connection succeeds

    Use Cases:
        - Testing healthy cache scenarios
        - Testing cache health check integration
        - Testing cache stats retrieval

    Test Customization:
        def test_degraded_cache(fake_cache_service):
            fake_cache_service.redis_available = False
            # Test will see degraded cache behavior
            status = await check_cache_health(fake_cache_service)
            assert status.status == HealthStatus.DEGRADED
    """
    return FakeCacheService()


@pytest.fixture
def fake_cache_service_redis_down():
    """
    Provides fake cache service with Redis unavailable (memory fallback).

    Pre-configured for testing degraded cache scenarios where Redis is down
    but memory cache provides fallback functionality.

    Returns:
        FakeCacheService with redis_available=False, memory_available=True

    Use Cases:
        - Testing degraded cache health status
        - Testing cache fallback behavior
        - Testing health check with partial cache availability
    """
    return FakeCacheService(redis_available=False, memory_available=True)


@pytest.fixture
def fake_cache_service_completely_down():
    """
    Provides fake cache service with both Redis and memory unavailable.

    Pre-configured for testing complete cache failure scenarios where
    both Redis and memory cache are unavailable.

    Returns:
        FakeCacheService with redis_available=False, memory_available=False

    Use Cases:
        - Testing unhealthy cache status
        - Testing cache health check failure handling
        - Testing complete cache unavailability scenarios
    """
    return FakeCacheService(redis_available=False, memory_available=False)


@pytest.fixture
def fake_cache_service_connection_fails():
    """
    Provides fake cache service where connection attempt fails.

    Pre-configured for testing scenarios where cache service connection
    raises an exception during initialization.

    Returns:
        FakeCacheService with connect_should_fail=True

    Use Cases:
        - Testing connection failure handling
        - Testing health check error recovery
        - Testing cache initialization failures
    """
    return FakeCacheService(connect_should_fail=True)


@pytest.fixture
def fake_resilience_orchestrator():
    """
    Provides a fake resilience orchestrator for health check testing.

    Returns FakeResilienceOrchestrator instance with healthy default configuration:
    - All circuit breakers closed
    - No open or half-open breakers
    - System marked as healthy

    Use Cases:
        - Testing healthy resilience scenarios
        - Testing resilience health check integration
        - Testing circuit breaker status retrieval

    Test Customization:
        def test_open_breakers(fake_resilience_orchestrator):
            fake_resilience_orchestrator.open_breakers = ["ai_service"]
            # Test will see degraded resilience behavior
            status = await check_resilience_health()
            assert status.status == HealthStatus.DEGRADED
    """
    return FakeResilienceOrchestrator()


@pytest.fixture
def fake_resilience_orchestrator_with_open_breakers():
    """
    Provides fake resilience orchestrator with open circuit breakers.

    Pre-configured for testing degraded resilience scenarios where
    some circuit breakers are open due to service failures.

    Returns:
        FakeResilienceOrchestrator with open_breakers=["ai_service", "cache"]

    Use Cases:
        - Testing degraded resilience health status
        - Testing open circuit breaker detection
        - Testing resilience degradation scenarios
    """
    return FakeResilienceOrchestrator(
        healthy=False,
        open_breakers=["ai_service", "cache"]
    )


@pytest.fixture
def fake_resilience_orchestrator_recovering():
    """
    Provides fake resilience orchestrator in recovery state.

    Pre-configured for testing resilience recovery scenarios where
    circuit breakers are transitioning from open to closed state.

    Returns:
        FakeResilienceOrchestrator with half_open_breakers=["ai_service"]

    Use Cases:
        - Testing circuit breaker recovery
        - Testing half-open state monitoring
        - Testing resilience recovery scenarios
    """
    return FakeResilienceOrchestrator(
        healthy=True,
        half_open_breakers=["ai_service"]
    )


@pytest.fixture
def fake_resilience_orchestrator_failed():
    """
    Provides fake resilience orchestrator that raises exceptions.

    Pre-configured for testing resilience system failure scenarios where
    the orchestrator itself is unavailable or failing.

    Returns:
        FakeResilienceOrchestrator with should_fail=True

    Use Cases:
        - Testing resilience infrastructure failures
        - Testing unhealthy resilience status
        - Testing exception handling in health checks
    """
    return FakeResilienceOrchestrator(should_fail=True)


# Settings fixture is imported from parent conftest.py (backend/tests/unit/conftest.py)
# Available fixtures from parent:
# - test_settings: Real Settings instance with test configuration
# - development_settings: Settings with development preset
# - production_settings: Settings with production preset

# Standard library imports are real and don't need fixtures:
# - asyncio (for timeout, sleep, gather)
# - time (for perf_counter, time)
# - logging (for logger)
# - dataclasses (for dataclass)
# - enum (for Enum)
# - typing (for type hints)