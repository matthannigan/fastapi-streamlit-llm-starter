"""
Resilience Infrastructure Integration Test Fixtures

This module provides comprehensive fixtures for testing the resilience infrastructure
integration points, including AI service resilience orchestration, circuit breaker
patterns, retry mechanisms, and configuration management.

Following the integration testing philosophy:
- Test behavior from the outside-in through API boundaries
- Use high-fidelity fakes (fakeredis) for infrastructure components
- Focus on observable outcomes rather than implementation details
- Verify component collaboration and seam integration

Key Components:
- AIServiceResilience: Main orchestrator for AI service resilience patterns
- EnhancedCircuitBreaker: Circuit breaker implementation with metrics
- Configuration management: Preset-based configuration with environment detection
- Exception classification: Smart retry decision logic
- Health monitoring: System health checks and recovery mechanisms

Fixtures provided:
- resilience_service: Configured AIServiceResilience instance
- circuit_breaker: EnhancedCircuitBreaker with test configuration
- fake_redis_cache: fakeredis-based cache for testing cache integration
- unreliable_ai_service: Mock AI service that can simulate failures
- resilience_config: Test configuration presets for different scenarios
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Callable, Optional

import fakeredis.aioredis

from app.core.config import Settings
from app.core.exceptions import (
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError
)
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    ResilienceMetrics
)
from app.infrastructure.resilience.retry import RetryConfig
from app.infrastructure.resilience.config_presets import (
    ResilienceConfig,
    ResilienceStrategy,
    get_default_presets
)
from app.infrastructure.cache import GenericRedisCache


@pytest.fixture(scope="session")
def resilience_test_settings():
    """Session-scoped settings for resilience integration tests."""
    return Settings(
        environment="testing",
        api_key="test-api-key-12345",
        additional_api_keys="test-key-2,test-key-3",
        resilience_preset="balanced",
        enable_circuit_breaker=True,
        enable_retry=True,
        max_retry_attempts=3,
        circuit_breaker_failure_threshold=5,
        circuit_breaker_recovery_timeout=60
    )


@pytest.fixture
def fake_redis_cache():
    """
    Provides a high-fidelity fake Redis cache for integration testing.

    This fixture creates a fakeredis instance that behaves identically to
    real Redis for testing cache integration with resilience patterns.
    
    Following the "hot-swap" pattern from cache integration tests, this creates
    a real GenericRedisCache instance and replaces its Redis client with a
    FakeRedis client for testing without external dependencies.

    Business Impact:
        Ensures cache operations are tested with realistic behavior
        without requiring a running Redis server for tests.

    Test Strategy:
        - Uses fakeredis.aioredis.FakeRedis for async Redis simulation
        - Hot-swaps Redis client in GenericRedisCache for testing
        - Provides same interface as real Redis cache implementation
        - Enables testing of cache + resilience pattern integration
        - Uses test database 15 for isolation (consistent with factory patterns)
    """
    # Create a real GenericRedisCache instance with test-appropriate configuration
    cache = GenericRedisCache(
        redis_url="redis://localhost:6379/15",  # URL for interface consistency, database 15 for test isolation
        default_ttl=3600,  # Standard test TTL
        enable_l1_cache=False,  # Test pure Redis behavior without L1 cache interference
        l1_cache_size=0,  # Disable L1 cache for focused Redis testing
        compression_threshold=1000,  # Standard compression threshold
        compression_level=6,  # Balanced compression
        fail_on_connection_error=False  # Allow graceful operation during testing
    )
    
    # Hot-swap the Redis client with FakeRedis for testing
    # This provides Redis-compatible behavior without requiring an external Redis server
    cache.redis = fakeredis.aioredis.FakeRedis(
        decode_responses=False,  # Consistent with real Redis client configuration
        connection_pool=None  # Use default connection handling
    )
    
    return cache


@pytest.fixture
def circuit_breaker():
    """
    Provides a configured EnhancedCircuitBreaker for integration testing.

    This fixture creates a circuit breaker with test-appropriate settings
    for verifying circuit breaker behavior in integration scenarios.

    Business Impact:
        Tests circuit breaker protection of failing services
        Validates automatic recovery mechanisms

    Test Strategy:
        - Configurable failure thresholds for different test scenarios
        - Recovery timeout settings appropriate for testing
        - Metrics collection enabled for validation
    """
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        half_open_max_calls=1
    )

    return EnhancedCircuitBreaker(
        failure_threshold=config.failure_threshold,
        recovery_timeout=config.recovery_timeout,
        name="test_circuit_breaker"
    )


@pytest.fixture
def resilience_service(resilience_test_settings):
    """
    Provides a configured AIServiceResilience instance for integration testing.

    This fixture creates the main resilience orchestrator with test settings
    and proper configuration for comprehensive integration testing.

    Integration Scope:
        AIServiceResilience → Circuit Breaker → Retry Logic → Configuration

    Business Impact:
        Core resilience functionality that affects user experience
        during AI service outages and failures

    Test Strategy:
        - Uses realistic test settings with balanced configuration
        - Enables both circuit breaker and retry functionality
        - Provides comprehensive metrics for validation
        - Thread-safe for concurrent test execution
    """
    return AIServiceResilience(resilience_test_settings)


@pytest.fixture
def unreliable_ai_service():
    """
    Provides a mock AI service that can simulate various failure scenarios.

    This fixture creates a controllable AI service mock that can be configured
    to succeed, fail temporarily, or fail permanently for testing different
    resilience scenarios.

    Business Impact:
        Enables testing of resilience patterns against realistic failure modes
        Validates proper error classification and handling

    Test Strategy:
        - Configurable failure patterns for different test scenarios
        - Supports both transient and permanent error simulation
        - Enables testing of fallback mechanisms
        - Provides realistic response patterns
    """
    class UnreliableAIService:
        """Mock AI service with configurable failure modes."""

        def __init__(self):
            self.call_count = 0
            self.failure_mode = "success"  # success, transient_failure, permanent_failure
            self.success_after_attempts = 0

        def set_failure_mode(self, mode: str, success_after: int = 0):
            """Configure the failure mode for subsequent calls."""
            self.failure_mode = mode
            self.success_after_attempts = success_after

        async def process(self, text: str) -> Dict[str, Any]:
            """Mock AI service call with configurable failure behavior."""
            self.call_count += 1

            if self.failure_mode == "transient_failure":
                if self.call_count <= self.success_after_attempts:
                    raise TransientAIError(f"Service temporarily unavailable (attempt {self.call_count})")
                else:
                    return {"result": f"Processed: {text}"}

            elif self.failure_mode == "permanent_failure":
                raise PermanentAIError("Service permanently unavailable")

            elif self.failure_mode == "rate_limit":
                raise RateLimitError("Rate limit exceeded")

            elif self.failure_mode == "service_unavailable":
                raise ServiceUnavailableError("Service is currently unavailable")

            else:  # success mode
                return {"result": f"Processed: {text}"}

        async def fail_fast(self) -> Dict[str, Any]:
            """Service that fails immediately without retry possibility."""
            raise PermanentAIError("This service always fails")

        async def succeed_after_delay(self, text: str, delay: float = 0.1) -> Dict[str, Any]:
            """Service that succeeds but takes time (for timeout testing)."""
            await asyncio.sleep(delay)
            return {"result": f"Delayed processing: {text}"}

    return UnreliableAIService()


@pytest.fixture
def resilience_config():
    """
    Provides test resilience configurations for different scenarios.

    This fixture provides pre-configured ResilienceConfig instances
    for testing different resilience strategies and configurations.

    Business Impact:
        Enables testing of different resilience behaviors
        Validates configuration-based strategy selection

    Test Strategy:
        - Covers all resilience strategies (aggressive, balanced, conservative, critical)
        - Provides custom configurations for edge case testing
        - Enables testing of configuration override scenarios
    """
    # Get default presets
    presets = get_default_presets()

    configs = {
        "aggressive": presets[ResilienceStrategy.AGGRESSIVE],
        "balanced": presets[ResilienceStrategy.BALANCED],
        "conservative": presets[ResilienceStrategy.CONSERVATIVE],
        "critical": presets[ResilienceStrategy.CRITICAL],
    }

    # Add custom configurations for edge cases
    configs["no_retry"] = ResilienceConfig(
        strategy=ResilienceStrategy.CONSERVATIVE,
        retry_config=RetryConfig(max_attempts=1),
        enable_retry=False
    )

    configs["no_circuit_breaker"] = ResilienceConfig(
        strategy=ResilienceStrategy.BALANCED,
        enable_circuit_breaker=False,
        enable_retry=True
    )

    configs["custom"] = ResilienceConfig(
        strategy=ResilienceStrategy.BALANCED,
        retry_config=RetryConfig(max_attempts=5, max_delay_seconds=120),
        circuit_breaker_config=CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=30
        )
    )

    return configs


@pytest.fixture
def mock_environment_variables():
    """
    Provides environment variable mocking utilities for configuration testing.

    This fixture provides utilities for testing environment-based configuration
    loading and preset selection.

    Business Impact:
        Enables testing of environment-specific resilience behavior
        Validates configuration loading from environment variables

    Test Strategy:
        - Provides clean environment variable setup/teardown
        - Enables testing of different environment scenarios
        - Supports testing of invalid configuration scenarios
    """
    original_env = {}

    def set_env_vars(env_dict: Dict[str, str]):
        """Set environment variables, saving originals for cleanup."""
        for key, value in env_dict.items():
            if key in os.environ:
                original_env[key] = os.environ[key]
            os.environ[key] = value

    def cleanup():
        """Restore original environment variables."""
        for key in original_env:
            os.environ[key] = original_env[key]
        # Remove variables that weren't originally set
        for key in list(os.environ.keys()):
            if key.startswith("TEST_") or key.startswith("RESILIENCE_"):
                os.environ.pop(key, None)

    return {
        "set": set_env_vars,
        "cleanup": cleanup
    }


@pytest.fixture
def performance_monitoring():
    """
    Provides performance monitoring utilities for resilience testing.

    This fixture provides utilities for measuring performance of resilience
    operations and validating performance requirements.

    Business Impact:
        Enables validation of performance requirements (<100ms config loading)
        Supports performance regression detection

    Test Strategy:
        - Provides timing utilities for operation measurement
        - Enables performance threshold validation
        - Supports concurrent operation testing
    """
    class PerformanceMonitor:
        """Utility for monitoring resilience operation performance."""

        def __init__(self):
            self.measurements = {}

        async def measure_operation(self, operation_name: str, operation_func: Callable) -> float:
            """Measure the execution time of a resilience operation."""
            start_time = asyncio.get_event_loop().time()

            try:
                await operation_func()
            except Exception:
                pass  # We still want to measure failed operations

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time

            if operation_name not in self.measurements:
                self.measurements[operation_name] = []

            self.measurements[operation_name].append(duration)
            return duration

        def get_average_duration(self, operation_name: str) -> float:
            """Get average duration for an operation."""
            if operation_name not in self.measurements or not self.measurements[operation_name]:
                return 0.0

            return sum(self.measurements[operation_name]) / len(self.measurements[operation_name])

        def validate_threshold(self, operation_name: str, threshold_seconds: float) -> bool:
            """Validate that operation meets performance threshold."""
            avg_duration = self.get_average_duration(operation_name)
            return avg_duration < threshold_seconds

    return PerformanceMonitor()


@pytest.fixture
def resilience_health_monitor():
    """
    Provides health monitoring utilities for resilience system testing.

    This fixture provides utilities for monitoring system health and
    validating health check functionality.

    Business Impact:
        Enables testing of health monitoring and alerting systems
        Validates system recovery and health reporting

    Test Strategy:
        - Provides health status collection from multiple components
        - Enables testing of health check endpoints
        - Supports validation of health status transitions
    """
    class HealthMonitor:
        """Utility for monitoring resilience system health."""

        def __init__(self):
            self.health_checks = []

        def record_health_check(self, component_name: str, is_healthy: bool, details: Optional[Dict] = None):
            """Record a health check result."""
            self.health_checks.append({
                "component": component_name,
                "healthy": is_healthy,
                "details": details or {},
                "timestamp": asyncio.get_event_loop().time()
            })

        def get_component_health(self, component_name: str) -> bool:
            """Get the latest health status for a component."""
            for check in reversed(self.health_checks):
                if check["component"] == component_name:
                    return check["healthy"]
            return True  # Default to healthy if no checks recorded

        def get_overall_health(self) -> bool:
            """Get overall system health based on all recorded checks."""
            if not self.health_checks:
                return True

            return all(check["healthy"] for check in self.health_checks)

        def get_health_summary(self) -> Dict[str, Any]:
            """Get comprehensive health summary."""
            if not self.health_checks:
                return {"overall_healthy": True, "components": {}}

            components = {}
            for check in self.health_checks:
                component = check["component"]
                if component not in components:
                    components[component] = []
                components[component].append(check["healthy"])

            component_health = {
                component: all(statuses) for component, statuses in components.items()
            }

            return {
                "overall_healthy": all(component_health.values()),
                "components": component_health,
                "total_checks": len(self.health_checks)
            }

    return HealthMonitor()


@pytest.fixture
def concurrent_test_utils():
    """
    Provides utilities for testing concurrent resilience operations.

    This fixture provides utilities for testing thread safety and
    concurrent operation handling in the resilience system.

    Business Impact:
        Enables validation of thread-safe resilience operations
        Tests system behavior under concurrent load

    Test Strategy:
        - Provides concurrent operation execution utilities
        - Enables testing of race condition scenarios
        - Supports load testing of resilience patterns
    """
    class ConcurrentTestUtils:
        """Utilities for testing concurrent resilience operations."""

        def __init__(self):
            self.concurrent_results = []

        async def run_concurrent_operations(self, operation_func: Callable, concurrency: int = 5) -> list:
            """Run multiple operations concurrently and collect results."""
            tasks = []
            for i in range(concurrency):
                task = asyncio.create_task(operation_func(i))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            self.concurrent_results.extend(results)
            return results

        def get_success_count(self) -> int:
            """Get count of successful operations."""
            return len([r for r in self.concurrent_results if not isinstance(r, Exception)])

        def get_failure_count(self) -> int:
            """Get count of failed operations."""
            return len([r for r in self.concurrent_results if isinstance(r, Exception)])

        def clear_results(self):
            """Clear concurrent test results."""
            self.concurrent_results.clear()

    return ConcurrentTestUtils()


@pytest.fixture
def exception_simulation():
    """
    Provides utilities for simulating different types of exceptions.

    This fixture provides utilities for testing exception handling and
    classification in the resilience system.

    Business Impact:
        Enables testing of exception classification logic
        Validates proper retry/fallback behavior for different error types

    Test Strategy:
        - Provides controlled exception generation
        - Enables testing of exception classification
        - Supports testing of error handling patterns
    """
    class ExceptionSimulator:
        """Utility for simulating different types of exceptions."""

        def create_transient_error(self, message: str = "Temporary service error") -> TransientAIError:
            """Create a transient error that should be retried."""
            return TransientAIError(message)

        def create_permanent_error(self, message: str = "Permanent service error") -> PermanentAIError:
            """Create a permanent error that should not be retried."""
            return PermanentAIError(message)

        def create_rate_limit_error(self, message: str = "Rate limit exceeded") -> RateLimitError:
            """Create a rate limit error requiring backoff."""
            return RateLimitError(message)

        def create_service_unavailable_error(self, message: str = "Service unavailable") -> ServiceUnavailableError:
            """Create a service unavailable error."""
            return ServiceUnavailableError(message)

        def create_custom_ai_error(self, message: str, transient: bool = True) -> AIServiceException:
            """Create a custom AI service exception."""
            if transient:
                return TransientAIError(message)
            else:
                return PermanentAIError(message)

    return ExceptionSimulator()


@pytest.fixture(autouse=True)
def cleanup_environment_after_test(mock_environment_variables):
    """Automatically cleanup environment variables after each test."""
    yield
    mock_environment_variables["cleanup"]()


@pytest.fixture(autouse=True)
def reset_resilience_state():
    """Reset resilience system state between tests."""
    # Reset any global state if needed
    yield

    # Clean up after test
    try:
        # Reset circuit breaker states if needed
        pass
    except Exception:
        pass  # Ignore cleanup errors
