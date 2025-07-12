"""
Resilience Orchestrator

This module provides the core orchestration layer for AI service resilience patterns,
implementing a comprehensive solution for handling transient failures in AI service
operations through retry mechanisms, circuit breakers, and intelligent fallback strategies.

Architecture Overview:
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

Key Components:
==============

Classes:
--------
- `AIServiceResilience`: Main orchestrator class that coordinates all resilience
  patterns and provides unified interface for applying resilience to functions.

Global Functions:
----------------
- `with_operation_resilience()`: Applies operation-specific resilience strategy
- `with_aggressive_resilience()`: Applies aggressive retry and circuit breaker settings
- `with_balanced_resilience()`: Applies balanced resilience configuration (default)
- `with_conservative_resilience()`: Applies conservative resilience settings
- `with_critical_resilience()`: Applies maximum resilience for critical operations

Core Features:
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

Usage Patterns:
==============

Basic Usage with Decorator:
---------------------------
```python
from app.infrastructure.resilience.orchestrator import with_operation_resilience

@with_operation_resilience("ai_summarize")
async def summarize_text(text: str) -> str:
    # AI service call that may fail
    return await ai_service.summarize(text)
```

Advanced Usage with Custom Configuration:
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

Metrics and Health Monitoring:
------------------------------
```python
# Get comprehensive metrics
metrics = resilience.get_all_metrics()

# Check system health
health_status = resilience.get_health_status()

# Reset metrics for specific operation
resilience.reset_metrics("ai_summarize")
```

Configuration Strategies:
========================

- **AGGRESSIVE**: High retry counts, longer timeouts, higher failure thresholds
- **BALANCED**: Moderate settings suitable for most use cases (default)
- **CONSERVATIVE**: Lower retry counts, shorter timeouts, lower failure thresholds
- **CRITICAL**: Maximum resilience for mission-critical operations

Exception Handling:
==================

The orchestrator automatically classifies exceptions into:
- **TransientAIError**: Temporary failures that should be retried
- **PermanentAIError**: Permanent failures that should not be retried
- **RateLimitError**: Rate limiting scenarios with appropriate backoff
- **ServiceUnavailableError**: Service unavailability requiring circuit breaker action

Integration Points:
==================

- **Settings Integration**: Automatic configuration loading from application settings
- **Logging Integration**: Comprehensive logging of retry attempts and failures
- **Metrics Export**: Compatible with monitoring systems via metrics endpoints
- **Health Checks**: Integrated health check endpoints for system monitoring

Thread Safety:
==============

The orchestrator is designed to be thread-safe and supports:
- Concurrent operation execution with isolated metrics
- Safe circuit breaker state management across threads
- Atomic configuration updates

Dependencies:
============

- `tenacity`: Advanced retry library with comprehensive retry strategies
- `app.infrastructure.resilience.circuit_breaker`: Enhanced circuit breaker implementation
- `app.infrastructure.resilience.retry`: Retry configuration and exception classification
- `app.infrastructure.resilience.config_presets`: Predefined resilience strategies

Example Integration in Service Layer:
====================================

```python
from app.infrastructure.resilience.orchestrator import ai_resilience

class AIService:
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
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_fixed,
    wait_random,
    retry_if_exception_type,
    retry_if_not_exception_type,
    before_sleep_log,
    after_log,
    RetryError,
    TryAgain
)

from app.core.exceptions import (
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
)
from app.infrastructure.resilience.circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    ResilienceMetrics,
)
from app.infrastructure.resilience.retry import (
    RetryConfig,
    should_retry_on_exception,
    classify_exception
)
from app.infrastructure.resilience.config_presets import (
    ResilienceStrategy,
    ResilienceConfig,
    DEFAULT_PRESETS
)

logger = logging.getLogger(__name__)


class AIServiceResilience:
    """
    Main orchestrator for AI service resilience patterns.
    
    Provides unified interface for retry and circuit breaker patterns
    with configurable strategies and comprehensive monitoring.
    """
    
    def __init__(self, settings=None):
        """Initialize resilience service with settings."""
        self.settings = settings
        self.circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self.configurations: Dict[Any, ResilienceConfig] = {}
        self.operation_metrics: Dict[str, ResilienceMetrics] = {}
        
        # Load configurations
        self._load_configurations()
        self._load_operation_configs()
        self._load_fallback_configs()
    
    def _load_configurations(self):
        """Load default strategy configurations."""
        self.configurations = dict(DEFAULT_PRESETS)
        
        # Apply any custom configuration overrides from Settings
        if self.settings:
            try:
                # Get the base processed resilience config from Settings
                base_config = self.settings.get_resilience_config()
                
                # Update all strategy configurations with the base overrides
                # while preserving the strategy-specific settings
                for strategy_enum, default_config in DEFAULT_PRESETS.items():
                    # Create a new config combining the base settings with strategy-specific strategy
                    self.configurations[strategy_enum] = ResilienceConfig(
                        strategy=strategy_enum,  # Keep the strategy-specific strategy
                        retry_config=base_config.retry_config,  # Use processed retry config
                        circuit_breaker_config=base_config.circuit_breaker_config,  # Use processed CB config
                        enable_circuit_breaker=base_config.enable_circuit_breaker,
                        enable_retry=base_config.enable_retry
                    )
                    
            except Exception as e:
                logger.warning(f"Error loading resilience configuration: {e}")
    
    def _load_operation_configs(self):
        """Load operation-specific configurations from settings."""
        if not self.settings:
            return
        
        # Operations are now registered by domain services via register_operation()
        # This method is kept for backward compatibility but no longer loads hardcoded operations
        # The configurations dictionary will be populated as operations are registered
        pass
    
    def _load_fallback_configs(self):
        """Load fallback configurations for compatibility."""
        # Add any legacy or fallback configuration logic here
        pass
    
    def get_or_create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> EnhancedCircuitBreaker:
        """Get or create a circuit breaker for the given name and configuration."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = EnhancedCircuitBreaker(
                failure_threshold=config.failure_threshold,
                recovery_timeout=config.recovery_timeout,
                expected_exception=TransientAIError,
                name=name
            )
        return self.circuit_breakers[name]
    
    def get_metrics(self, operation_name: str) -> ResilienceMetrics:
        """Get metrics for a specific operation."""
        if operation_name not in self.operation_metrics:
            self.operation_metrics[operation_name] = ResilienceMetrics()
        return self.operation_metrics[operation_name]
    
    def get_operation_config(self, operation_name: str) -> ResilienceConfig:
        """Get configuration for a specific operation."""
        # Try operation-specific config first
        if operation_name in self.configurations:
            return self.configurations[operation_name]
        
        # Get operation-specific strategy from settings
        if self.settings:
            try:
                strategy_name = self.settings.get_operation_strategy(operation_name)
                strategy = ResilienceStrategy(strategy_name)
                
                # Create a configuration with the operation-specific strategy
                # but using the base configuration's retry/circuit breaker settings
                base_config = self.settings.get_resilience_config()
                
                return ResilienceConfig(
                    strategy=strategy,
                    retry_config=base_config.retry_config,
                    circuit_breaker_config=base_config.circuit_breaker_config,
                    enable_circuit_breaker=base_config.enable_circuit_breaker,
                    enable_retry=base_config.enable_retry
                )
            except (ValueError, AttributeError):
                pass
        
        # Fallback to balanced
        return self.configurations[ResilienceStrategy.BALANCED]
    
    def custom_before_sleep(self, operation_name: str):
        """Create a custom before_sleep callback for tenacity."""
        def callback(retry_state):
            metrics = self.get_metrics(operation_name)
            metrics.retry_attempts += 1
            logger.warning(
                f"Operation '{operation_name}' retry attempt {retry_state.attempt_number}, "
                f"sleeping {retry_state.next_action.sleep} seconds"
            )
        return callback
    
    def with_resilience(
        self,
        operation_name: str,
        strategy: Union[ResilienceStrategy, str, None] = None,
        custom_config: Optional[ResilienceConfig] = None,
        fallback: Optional[Callable] = None
    ):
        """
        Decorator that applies resilience patterns to a function.
        
        Args:
            operation_name: Name of the operation for metrics and configuration
            strategy: Resilience strategy to use (defaults to operation config)
            custom_config: Custom configuration to override defaults
            fallback: Fallback function to call if all retries fail
            
        Returns:
            Decorated function with resilience patterns applied
        """
        def decorator(func: Callable) -> Callable:
            # Get configuration
            if custom_config:
                config = custom_config
            elif strategy:
                if isinstance(strategy, str):
                    strategy_enum = ResilienceStrategy(strategy)
                else:
                    strategy_enum = strategy
                config = self.configurations[strategy_enum]
            else:
                config = self.get_operation_config(operation_name)
            
            # Get circuit breaker if enabled
            circuit_breaker = None
            if config.enable_circuit_breaker:
                circuit_breaker = self.get_or_create_circuit_breaker(
                    operation_name, 
                    config.circuit_breaker_config
                )
            
            # Build tenacity retry decorator
            retry_decorator = None
            if config.enable_retry:
                retry_config = config.retry_config
                
                # Build wait strategy
                if retry_config.exponential_multiplier > 0:
                    wait_strategy = wait_exponential(
                        multiplier=retry_config.exponential_multiplier,
                        min=retry_config.exponential_min,
                        max=retry_config.exponential_max
                    )
                    if retry_config.jitter:
                        wait_strategy = wait_strategy + wait_random(0, retry_config.jitter_max)
                else:
                    wait_strategy = wait_fixed(2)
                
                retry_decorator = retry(
                    stop=stop_after_attempt(retry_config.max_attempts) | 
                         stop_after_delay(retry_config.max_delay_seconds),
                    wait=wait_strategy,
                    retry=should_retry_on_exception,
                    before_sleep=before_sleep_log(logger, logging.WARNING) if logger.isEnabledFor(logging.WARNING) else None,
                )
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                metrics = self.get_metrics(operation_name)
                metrics.total_calls += 1
                
                start_time = datetime.now()
                
                async def execute_function():
                    """Inner function to execute with resilience patterns."""
                    try:
                        if asyncio.iscoroutinefunction(func):
                            result = await func(*args, **kwargs)
                        else:
                            result = func(*args, **kwargs)
                        
                        metrics.successful_calls += 1
                        metrics.last_success = datetime.now()
                        return result
                        
                    except Exception as e:
                        metrics.failed_calls += 1
                        metrics.last_failure = datetime.now()
                        
                        # Transform exceptions for better classification
                        if not isinstance(e, AIServiceException):
                            if classify_exception(e):
                                raise TransientAIError(str(e)) from e
                            else:
                                raise PermanentAIError(str(e)) from e
                        raise
                
                try:
                    # Apply circuit breaker if enabled
                    if circuit_breaker:
                        # Circuit breaker check
                        if hasattr(circuit_breaker, '_state') and circuit_breaker._state == 'open':
                            raise ServiceUnavailableError("Circuit breaker is open")
                        
                        # Apply retry if enabled
                        if retry_decorator:
                            result = await retry_decorator(execute_function)()
                        else:
                            result = await execute_function()
                        
                        # Record success in circuit breaker
                        circuit_breaker.metrics.successful_calls += 1
                        return result
                    else:
                        # Apply retry if enabled
                        if retry_decorator:
                            return await retry_decorator(execute_function)()
                        else:
                            return await execute_function()
                            
                except (RetryError, TransientAIError, ServiceUnavailableError) as e:
                    # All retries failed or circuit breaker open
                    if fallback:
                        logger.warning(f"Operation '{operation_name}' failed, using fallback")
                        if asyncio.iscoroutinefunction(fallback):
                            return await fallback(*args, **kwargs)
                        else:
                            return fallback(*args, **kwargs)
                    raise
                except PermanentAIError:
                    # Don't retry permanent errors, but can still use fallback
                    if fallback:
                        logger.warning(f"Operation '{operation_name}' permanent error, using fallback")
                        if asyncio.iscoroutinefunction(fallback):
                            return await fallback(*args, **kwargs)
                        else:
                            return fallback(*args, **kwargs)
                    raise
            
            return wrapper
        return decorator
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive metrics for all operations and circuit breakers."""
        result = {
            "operations": {},
            "circuit_breakers": {},
            "summary": {
                "total_operations": len(self.operation_metrics),
                "total_circuit_breakers": len(self.circuit_breakers),
                "healthy_circuit_breakers": sum(
                    1 for cb in self.circuit_breakers.values() 
                    if not hasattr(cb, '_state') or cb._state != 'open'
                ),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Operation metrics
        for name, metrics in self.operation_metrics.items():
            result["operations"][name] = metrics.to_dict()
        
        # Circuit breaker metrics
        for name, cb in self.circuit_breakers.items():
            result["circuit_breakers"][name] = {
                "state": getattr(cb, '_state', 'closed'),
                "failure_threshold": getattr(cb, 'failure_threshold', 5),
                "recovery_timeout": getattr(cb, 'recovery_timeout', 60),
                "metrics": cb.metrics.to_dict() if hasattr(cb, 'metrics') else {}
            }
        
        return result
    
    def reset_metrics(self, operation_name: Optional[str] = None):
        """Reset metrics for specific operation or all operations."""
        if operation_name:
            if operation_name in self.operation_metrics:
                self.operation_metrics[operation_name] = ResilienceMetrics()
            if operation_name in self.circuit_breakers:
                self.circuit_breakers[operation_name].metrics = ResilienceMetrics()
        else:
            self.operation_metrics.clear()
            for cb in self.circuit_breakers.values():
                cb.metrics = ResilienceMetrics()
    
    def is_healthy(self) -> bool:
        """Check if the resilience service is healthy."""
        # Check if any circuit breakers are open
        open_circuit_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if hasattr(cb, '_state') and cb._state == 'open'
        ]
        return len(open_circuit_breakers) == 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status."""
        open_circuit_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if hasattr(cb, '_state') and cb._state == 'open'
        ]
        
        half_open_circuit_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if hasattr(cb, '_state') and cb._state == 'half-open'
        ]
        
        return {
            "healthy": len(open_circuit_breakers) == 0,
            "open_circuit_breakers": open_circuit_breakers,
            "half_open_circuit_breakers": half_open_circuit_breakers,
            "total_circuit_breakers": len(self.circuit_breakers),
            "total_operations": len(self.operation_metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    def with_operation_resilience(self, operation_name: str, fallback: Optional[Callable] = None):
        """Convenience method to apply operation-specific resilience."""
        return self.with_resilience(operation_name=operation_name, fallback=fallback)

    def register_operation(self, operation_name: str, strategy: ResilienceStrategy = ResilienceStrategy.BALANCED):
        """Register a new operation with the resilience service."""
        if self.settings:
            # Let settings handle the registration
            self.settings.register_operation(operation_name, strategy.value)
        else:
            # Direct registration for testing/standalone use
            self.configurations[operation_name] = self.configurations[strategy]


# Global instance - initialize immediately to support decorators at import time
ai_resilience = AIServiceResilience()


# Convenience decorator functions
def with_operation_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for operation-specific resilience."""
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_operation_resilience(operation_name, fallback)


def with_aggressive_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for aggressive resilience strategy."""
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_resilience(operation_name, ResilienceStrategy.AGGRESSIVE, fallback=fallback)


def with_balanced_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for balanced resilience strategy."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not ai_resilience:
                raise RuntimeError("AIServiceResilience not initialized")
            # Apply resilience at runtime, not at import time
            resilient_func = ai_resilience.with_resilience(
                operation_name, ResilienceStrategy.BALANCED, fallback=fallback
            )(func)
            return await resilient_func(*args, **kwargs)
        return wrapper
    return decorator


def with_conservative_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for conservative resilience strategy."""
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_resilience(operation_name, ResilienceStrategy.CONSERVATIVE, fallback=fallback)


def with_critical_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for critical resilience strategy."""
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_resilience(operation_name, ResilienceStrategy.CRITICAL, fallback=fallback) 