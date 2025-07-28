# Resilience Orchestrator

  file_path: `backend/app/infrastructure/resilience/orchestrator.py`

This module provides the core orchestration layer for AI service resilience patterns,
implementing a comprehensive solution for handling transient failures in AI service
operations through retry mechanisms, circuit breakers, and intelligent fallback strategies.

## Architecture Overview

=====================

The Resilience Orchestrator follows a layered architecture pattern:

1. **Orchestration Layer (AIServiceResilience)**: Main coordinator that manages
resilience strategies, configurations, and applies patterns to operations.

2. **Pattern Layer**: Individual resilience patterns (retry, circuit breaker)
with their own configuration and state management.

3. **Metrics Layer**: Comprehensive monitoring and health tracking for all
resilience operations and circuit breaker states.

4. **Configuration Layer**: Strategy-based configuration system supporting
multiple predefined strategies and custom configurations.

## Key Components

==============

## Classes

--------
- `AIServiceResilience`: Main orchestrator class that coordinates all resilience
patterns and provides unified interface for applying resilience to functions.

## Global Functions

----------------
- `with_operation_resilience()`: Applies operation-specific resilience strategy
- `with_aggressive_resilience()`: Applies aggressive retry and circuit breaker settings
- `with_balanced_resilience()`: Applies balanced resilience configuration (default)
- `with_conservative_resilience()`: Applies conservative resilience settings
- `with_critical_resilience()`: Applies maximum resilience for critical operations

## Core Features

=============

1. **Retry Patterns**:
- Exponential backoff with jitter
- Fixed delay strategies
- Configurable stop conditions (max attempts, max delay)
- Exception classification for intelligent retry decisions

2. **Circuit Breaker Patterns**:
- Automatic failure detection and service protection
- Configurable failure thresholds and recovery timeouts
- State management (closed, open, half-open)
- Per-operation circuit breaker isolation

3. **Configuration Management**:
- Strategy-based configuration (aggressive, balanced, conservative, critical)
- Operation-specific configuration overrides
- Runtime configuration updates via JSON
- Backward compatibility with legacy configurations

4. **Monitoring & Metrics**:
- Comprehensive operation metrics (success/failure rates, response times)
- Circuit breaker state and health monitoring
- Aggregated system health status
- Per-operation performance tracking

5. **Fallback Mechanisms**:
- Configurable fallback functions for failed operations
- Automatic fallback invocation on permanent failures
- Support for both sync and async fallback functions

## Usage Patterns

==============

## Basic Usage with Decorator

---------------------------
```python
from app.infrastructure.resilience.orchestrator import with_operation_resilience

@with_operation_resilience("ai_summarize")
async def summarize_text(text: str) -> str:
# AI service call that may fail
return await ai_service.summarize(text)
```

## Advanced Usage with Custom Configuration

-----------------------------------------
```python
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.config_presets import ResilienceStrategy

resilience = AIServiceResilience()

@resilience.with_resilience(
operation_name="critical_ai_operation",
strategy=ResilienceStrategy.CRITICAL,
fallback=lambda x: f"Fallback result for {x}"
)
async def critical_ai_operation(input_data: str) -> str:
return await external_ai_service.process(input_data)
```

## Metrics and Health Monitoring

------------------------------
```python
# Get comprehensive metrics
metrics = resilience.get_all_metrics()

# Check system health
health_status = resilience.get_health_status()

# Reset metrics for specific operation
resilience.reset_metrics("ai_summarize")
```

## Configuration Strategies

========================

- **AGGRESSIVE**: High retry counts, longer timeouts, higher failure thresholds
- **BALANCED**: Moderate settings suitable for most use cases (default)
- **CONSERVATIVE**: Lower retry counts, shorter timeouts, lower failure thresholds
- **CRITICAL**: Maximum resilience for mission-critical operations

## Exception Handling

==================

The orchestrator automatically classifies exceptions into:
- **TransientAIError**: Temporary failures that should be retried
- **PermanentAIError**: Permanent failures that should not be retried
- **RateLimitError**: Rate limiting scenarios with appropriate backoff
- **ServiceUnavailableError**: Service unavailability requiring circuit breaker action

## Integration Points

==================

- **Settings Integration**: Automatic configuration loading from application settings
- **Logging Integration**: Comprehensive logging of retry attempts and failures
- **Metrics Export**: Compatible with monitoring systems via metrics endpoints
- **Health Checks**: Integrated health check endpoints for system monitoring

## Thread Safety

==============

The orchestrator is designed to be thread-safe and supports:
- Concurrent operation execution with isolated metrics
- Safe circuit breaker state management across threads
- Atomic configuration updates

## Dependencies

============

- `tenacity`: Advanced retry library with comprehensive retry strategies
- `app.infrastructure.resilience.circuit_breaker`: Enhanced circuit breaker implementation
- `app.infrastructure.resilience.retry`: Retry configuration and exception classification
- `app.infrastructure.resilience.config_presets`: Predefined resilience strategies

## Example Integration in Service Layer

====================================

```python
from app.infrastructure.resilience.orchestrator import ai_resilience

## class AIService

def __init__(self):
# Initialize resilience with application settings
global ai_resilience
ai_resilience = AIServiceResilience(settings)

@ai_resilience.with_operation_resilience("text_processing")
async def process_text(self, text: str) -> dict:
# Implementation with automatic resilience patterns applied
pass
```

This module serves as the primary entry point for applying resilience patterns
to AI service operations, providing a production-ready solution for handling
the inherent unreliability of external AI services and network operations.
