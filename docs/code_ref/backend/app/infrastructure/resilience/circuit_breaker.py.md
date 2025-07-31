---
sidebar_label: circuit_breaker
---

# Circuit Breaker Module

  file_path: `backend/app/infrastructure/resilience/circuit_breaker.py`

This module implements the Circuit Breaker pattern for resilient service communication,
providing fault tolerance and automatic recovery capabilities for AI service calls.

## Circuit Breaker Pattern

The circuit breaker pattern prevents cascading failures by monitoring service calls
and automatically "opening" the circuit when failure rates exceed thresholds.

### States

- `CLOSED`: Normal operation, calls pass through
- `OPEN`: Circuit is open, calls fail fast without reaching the service
- HALF-OPEN: Testing state, limited calls allowed to test service recovery

## Key Components

- EnhancedCircuitBreaker: Core circuit breaker with metrics and monitoring
- CircuitBreakerConfig: Configuration dataclass for circuit breaker parameters
- ResilienceMetrics: Comprehensive metrics tracking for monitoring and alerting
- AIServiceException: Base exception for AI service errors

## Configuration

- failure_threshold: Number of failures before opening circuit (default: 5)
- recovery_timeout: Seconds to wait before trying half-open state (default: 60)
- half_open_max_calls: Maximum calls allowed in half-open state (default: 1)

## Metrics Tracked

- Total calls, successful calls, failed calls
- Retry attempts and circuit breaker state transitions
- Success/failure rates with timestamps
- Circuit breaker opens, half-opens, and closes

## Usage Example

```python
from app.infrastructure.resilience.circuit_breaker import (
EnhancedCircuitBreaker,
CircuitBreakerConfig
)

# Create circuit breaker with custom config
config = CircuitBreakerConfig(
failure_threshold=3,
recovery_timeout=30
)

cb = EnhancedCircuitBreaker(
failure_threshold=config.failure_threshold,
recovery_timeout=config.recovery_timeout,
name="ai_service"
)

# Use circuit breaker to protect service calls
try:
result = cb.call(ai_service_function, param1, param2)
print(f"Success rate: {cb.metrics.success_rate}%")
except Exception as e:
print(f"Service call failed: {e}")
print(f"Circuit breaker metrics: {cb.metrics.to_dict()}")
```

## Dependencies

- circuitbreaker: Third-party circuit breaker implementation
- datetime: For timestamp tracking
- logging: For circuit breaker state change notifications

## Thread Safety

The circuit breaker is thread-safe and can be used in concurrent environments.
Metrics are updated atomically to ensure consistency.

## Integration

This module integrates with the broader resilience infrastructure including
retry mechanisms, timeouts, and monitoring systems.
