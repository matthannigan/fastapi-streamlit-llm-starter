---
sidebar_label: conftest
---

# Resilience Infrastructure Integration Test Fixtures

  file_path: `backend/tests.new/integration/resilience/conftest.py`

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

## resilience_test_settings()

```python
def resilience_test_settings():
```

Session-scoped settings for resilience integration tests.

## fake_redis_cache()

```python
def fake_redis_cache():
```

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

## circuit_breaker()

```python
def circuit_breaker():
```

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

## resilience_service()

```python
def resilience_service(resilience_test_settings):
```

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

## unreliable_ai_service()

```python
def unreliable_ai_service():
```

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

## resilience_config()

```python
def resilience_config():
```

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

## mock_environment_variables()

```python
def mock_environment_variables():
```

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

## performance_monitoring()

```python
def performance_monitoring():
```

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

## resilience_health_monitor()

```python
def resilience_health_monitor():
```

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

## concurrent_test_utils()

```python
def concurrent_test_utils():
```

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

## exception_simulation()

```python
def exception_simulation():
```

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

## cleanup_environment_after_test()

```python
def cleanup_environment_after_test(mock_environment_variables):
```

Automatically cleanup environment variables after each test.

## reset_resilience_state()

```python
def reset_resilience_state():
```

Reset resilience system state between tests.
