"""
Health monitoring integration test fixtures and configuration.

Provides comprehensive test fixtures for health monitoring integration tests,
including environment manipulation, service configuration, and test utilities
that support the testing philosophy outlined in the TEST_PLAN.md.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    SystemHealthStatus,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
)
from app.dependencies import get_health_checker, get_cache_service
from app.core.config import settings


@pytest.fixture(scope="function")
def health_client():
    """
    FastAPI test client for health endpoint integration testing.

    Provides a fresh TestClient instance for each test function to ensure
    test isolation and prevent state leakage between tests. Uses the real
    FastAPI application with all middleware and dependency injection intact.

    Returns:
        TestClient: Configured test client ready for HTTP requests to health endpoints
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def health_checker():
    """
    Fresh health checker instance for isolated testing.

    Creates a new HealthChecker instance for each test function to ensure
    complete test isolation. This prevents test interference from cached
    health check results or component registration state.

    Returns:
        HealthChecker: Fresh health checker with standard configuration
    """
    checker = HealthChecker(
        default_timeout_ms=2000,
        per_component_timeouts_ms={},
        retry_count=1,
        backoff_base_seconds=0.1,
    )
    checker.register_check("ai_model", check_ai_model_health)
    checker.register_check("cache", check_cache_health)
    checker.register_check("resilience", check_resilience_health)
    return checker


@pytest.fixture(scope="function")
def mock_cache_service():
    """
    Mock cache service for testing cache health integration.

    Provides a configurable mock cache service that can simulate various
    cache states (healthy, degraded, unhealthy) for testing different
    scenarios without requiring actual Redis infrastructure.

    Returns:
        AsyncMock: Configurable mock cache service with get_cache_stats method
    """
    mock_service = AsyncMock()

    # Default healthy state
    mock_service.get_cache_stats.return_value = {
        "redis": {"status": "ok"},
        "memory": {"status": "ok"},
        "error": None,
    }

    return mock_service


@pytest.fixture(scope="function")
def mock_resilience_orchestrator():
    """
    Mock resilience orchestrator for testing resilience health integration.

    Provides a configurable mock resilience service that can simulate different
    circuit breaker states and health conditions for testing resilience monitoring.

    Returns:
        MagicMock: Configurable mock resilience orchestrator with get_health_status method
    """
    mock_orchestrator = MagicMock()

    # Default healthy state - all circuits closed
    mock_orchestrator.get_health_status.return_value = {
        "healthy": True,
        "open_circuit_breakers": [],
        "half_open_circuit_breakers": [],
        "total_circuit_breakers": 3,
    }

    return mock_orchestrator


@pytest.fixture(scope="function")
def healthy_environment(monkeypatch):
    """
    Configure environment for all components to be healthy.

    Sets up environment variables and configuration to ensure all health
    checks report healthy status. This provides a baseline for testing
    optimal system behavior.

    Args:
        monkeypatch: pytest monkeypatch fixture for environment manipulation
    """
    # Ensure AI service is configured
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-for-health-checks")

    # Configure cache for healthy operation
    monkeypatch.setenv("CACHE_PRESET", "development")

    # Configure resilience for healthy operation
    monkeypatch.setenv("RESILIENCE_PRESET", "development")

    # Clear any potential error states
    monkeypatch.delenv("RESILIENCE_CUSTOM_CONFIG", raising=False)


@pytest.fixture(scope="function")
def degraded_ai_environment(monkeypatch):
    """
    Configure environment with AI service degraded.

    Removes AI API key configuration to simulate AI service unavailability
    while keeping other components healthy. Tests system behavior when
    AI functionality is degraded.

    Args:
        monkeypatch: pytest monkeypatch fixture for environment manipulation
    """
    # Remove AI configuration to trigger degraded state
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Keep other components healthy
    monkeypatch.setenv("CACHE_PRESET", "development")
    monkeypatch.setenv("RESILIENCE_PRESET", "development")


@pytest.fixture(scope="function")
def unhealthy_resilience_environment(monkeypatch):
    """
    Configure environment with resilience system unhealthy.

    Sets invalid resilience configuration to simulate resilience infrastructure
    failures while keeping other components operational. Tests system behavior
    when resilience protection is compromised.

    Args:
        monkeypatch: pytest monkeypatch fixture for environment manipulation
    """
    # Configure invalid resilience settings
    monkeypatch.setenv("RESILIENCE_PRESET", "invalid_preset_name")
    monkeypatch.setenv("RESILIENCE_CUSTOM_CONFIG", "{invalid json")

    # Keep AI and cache healthy
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-for-health-checks")
    monkeypatch.setenv("CACHE_PRESET", "development")


@pytest.fixture(scope="function")
def cache_only_environment(monkeypatch):
    """
    Configure environment for cache-only operation (Redis unavailable).

    Simulates Redis unavailability by configuring minimal cache preset,
    forcing the system to operate with memory-only caching. Tests graceful
    degradation behavior when primary cache backend is unavailable.

    Args:
        monkeypatch: pytest monkeypatch fixture for environment manipulation
    """
    # Configure memory-only cache
    monkeypatch.setenv("CACHE_PRESET", "minimal")

    # Keep other components healthy
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key-for-health-checks")
    monkeypatch.setenv("RESILIENCE_PRESET", "development")


@pytest.fixture
async def performance_time_tracker():
    """
    Utility for tracking response times in performance tests.

    Provides a context manager and utility functions for measuring
    and validating response times in health check performance tests.

    Yields:
        dict: Performance tracking utilities with start_time, end_time, and duration methods
    """
    timing_data = {
        "start_time": None,
        "end_time": None,
        "measurements": []
    }

    class TimeTracker:
        def start_measurement(self):
            """Start a new timing measurement."""
            timing_data["start_time"] = time.perf_counter()

        def end_measurement(self) -> float:
            """End current timing measurement and return duration in milliseconds."""
            if timing_data["start_time"] is None:
                raise ValueError("Must call start_measurement() first")

            timing_data["end_time"] = time.perf_counter()
            duration_ms = (timing_data["end_time"] - timing_data["start_time"]) * 1000.0
            timing_data["measurements"].append(duration_ms)
            timing_data["start_time"] = None
            timing_data["end_time"] = None
            return duration_ms

        def get_average_time(self) -> float:
            """Get average of all recorded measurements in milliseconds."""
            if not timing_data["measurements"]:
                return 0.0
            return sum(timing_data["measurements"]) / len(timing_data["measurements"])

        def get_max_time(self) -> float:
            """Get maximum recorded measurement in milliseconds."""
            if not timing_data["measurements"]:
                return 0.0
            return max(timing_data["measurements"])

        def reset_measurements(self):
            """Clear all recorded measurements."""
            timing_data["measurements"].clear()

    yield TimeTracker()


@pytest.fixture
def circuit_breaker_state_factory():
    """
    Factory for creating different circuit breaker states for testing.

    Provides a utility function to create mock resilience orchestrator
    responses with various circuit breaker configurations (all closed,
    some open, half-open states, etc.) for comprehensive resilience
    health testing.

    Returns:
        callable: Function that creates circuit breaker state dictionaries
    """
    def create_circuit_breaker_state(
        healthy: bool = True,
        open_breakers: Optional[list] = None,
        half_open_breakers: Optional[list] = None,
        total_breakers: int = 3
    ) -> Dict[str, Any]:
        """
        Create a circuit breaker state dictionary for testing.

        Args:
            healthy: Overall health status of resilience system
            open_breakers: List of open circuit breaker names
            half_open_breakers: List of half-open circuit breaker names
            total_breakers: Total number of circuit breakers

        Returns:
            Dict: Circuit breaker state dictionary in expected format
        """
        return {
            "healthy": healthy,
            "open_circuit_breakers": open_breakers or [],
            "half_open_circuit_breakers": half_open_breakers or [],
            "total_circuit_breakers": total_breakers,
        }

    return create_circuit_breaker_state


@pytest.fixture
def component_status_factory():
    """
    Factory for creating ComponentStatus objects for testing.

    Provides a utility function to create standardized ComponentStatus
    objects with various configurations for testing health check
    aggregation logic and status determination.

    Returns:
        callable: Function that creates ComponentStatus objects
    """
    def create_component_status(
        name: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        message: str = "",
        response_time_ms: float = 10.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ComponentStatus:
        """
        Create a ComponentStatus object for testing.

        Args:
            name: Component name identifier
            status: Health status of the component
            message: Status message or error details
            response_time_ms: Health check execution time in milliseconds
            metadata: Optional component-specific metadata

        Returns:
            ComponentStatus: Configured component status object
        """
        return ComponentStatus(
            name=name,
            status=status,
            message=message,
            response_time_ms=response_time_ms,
            metadata=metadata or {}
        )

    return create_component_status