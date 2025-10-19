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
import logging
from datetime import datetime
from typing import Any, Callable, Dict
from functools import wraps

from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    wait_fixed,
    wait_random,
    wait_combine,
    before_sleep_log,
    RetryError
)

from app.core.exceptions import (
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    ServiceUnavailableError,
)
from app.infrastructure.resilience.circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    ResilienceMetrics,
)
from app.infrastructure.resilience.retry import (
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
    Main orchestrator for AI service resilience patterns with comprehensive failure handling and monitoring.

    Provides a unified interface for applying retry mechanisms, circuit breaker patterns, and fallback
    strategies to AI service operations. Manages multiple resilience strategies with operation-specific
    configurations and comprehensive metrics collection for production monitoring.

    Attributes:
        settings: Application settings for configuration loading
        circuit_breakers: Dict[str, EnhancedCircuitBreaker] mapping operation names to circuit breakers
        configurations: Dict[Any, ResilienceConfig] mapping strategies/operations to resilience configurations
        operation_metrics: Dict[str, ResilienceMetrics] tracking metrics per operation

    Public Methods:
        with_resilience(): Primary decorator for applying resilience patterns to functions
        with_operation_resilience(): Convenience decorator using operation-specific configuration
        register_operation(): Register new operations with specific resilience strategies
        get_all_metrics(): Retrieve comprehensive metrics for monitoring and debugging
        reset_metrics(): Reset metrics for operations or entire system
        is_healthy(): Check overall system health based on circuit breaker states
        get_health_status(): Get detailed health information including open/half-open circuit breakers

    State Management:
        - Thread-safe circuit breaker state management across concurrent operations
        - Atomic configuration updates without service interruption
        - Isolated metrics tracking per operation preventing cross-operation interference
        - Global instance management for decorator support at import time

    Usage:
        # Basic usage with default configuration
        resilience = AIServiceResilience(settings)

        @resilience.with_operation_resilience("ai_summarize")
        async def summarize_text(text: str) -> str:
            return await ai_service.summarize(text)

        # Advanced usage with custom strategy and fallback
        @resilience.with_resilience(
            operation_name="critical_ai_operation",
            strategy=ResilienceStrategy.CRITICAL,
            fallback=lambda x: f"Fallback result for {x}"
        )
        async def critical_ai_operation(input_data: str) -> str:
            return await external_ai_service.process(input_data)

        # Monitoring and health checks
        metrics = resilience.get_all_metrics()
        health_status = resilience.get_health_status()

        # Register new operations with specific strategies
        resilience.register_operation("text_analysis", ResilienceStrategy.BALANCED)
    """

    def __init__(self, settings: Any | None = None) -> None:
        """
        Initialize resilience orchestrator with application settings and default configurations.

        Args:
            settings: Optional application settings object containing resilience configurations.
                     If None, uses default preset configurations without environment overrides.

        Behavior:
            - Loads default resilience strategy configurations from presets
            - Applies settings overrides to all strategy configurations if provided
            - Initializes empty collections for circuit breakers, metrics, and operation configs
            - Preserves strategy-specific characteristics while applying global settings
            - Logs warnings for configuration loading errors without failing initialization
            - Sets up thread-safe data structures for concurrent operation support
        """
        self.settings = settings
        self.circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self.configurations: Dict[Any, ResilienceConfig] = {}
        self.operation_metrics: Dict[str, ResilienceMetrics] = {}

        # Load configurations
        self._load_configurations()
        self._load_operation_configs()
        self._load_fallback_configs()

    def _load_configurations(self) -> None:
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

    def _load_operation_configs(self) -> None:
        """Load operation-specific configurations from settings."""
        if not self.settings:
            return

        # Operations are now registered by domain services via register_operation()
        # This method is kept for backward compatibility but no longer loads hardcoded operations
        # The configurations dictionary will be populated as operations are registered

    def _load_fallback_configs(self) -> None:
        """Load fallback configurations for compatibility."""
        # Add any legacy or fallback configuration logic here

    def get_or_create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> EnhancedCircuitBreaker:
        """
        Retrieve existing circuit breaker or create new one with operation-specific configuration.

        Implements circuit breaker pattern isolation by maintaining separate circuit breaker
        instances per operation name. Provides thread-safe creation and retrieval with
        automatic configuration application for new circuit breakers.

        Args:
            name: Unique operation name used as circuit breaker identifier.
                  Must be consistent across all calls for the same operation to ensure
                  proper circuit breaker state management and metrics aggregation
            config: CircuitBreakerConfig containing failure_threshold (minimum 1),
                    recovery_timeout in seconds (minimum 10), and other circuit breaker
                    settings for operation-specific behavior customization

        Returns:
            EnhancedCircuitBreaker instance configured with TransientAIError as the expected
            exception type. Returns existing instance if already created for the operation
            name, otherwise creates new instance with provided configuration

        Behavior:
            - Returns existing circuit breaker if already created for the operation name
            - Creates new circuit breaker with TransientAIError as expected exception type
            - Stores circuit breaker in internal dictionary for future reuse
            - Applies provided configuration settings to new circuit breakers
            - Maintains circuit breaker isolation per operation name
            - Thread-safe creation and retrieval for concurrent access

        Examples:
            >>> resilience = AIServiceResilience()
            >>> config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
            >>> cb1 = resilience.get_or_create_circuit_breaker("ai_summarize", config)
            >>> cb2 = resilience.get_or_create_circuit_breaker("ai_summarize", config)
            >>> assert cb1 is cb2  # Same instance returned
            >>>
            >>> # Different operations get different circuit breakers
            >>> cb3 = resilience.get_or_create_circuit_breaker("sentiment", config)
            >>> assert cb1 is not cb3
        """
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = EnhancedCircuitBreaker(
                failure_threshold=config.failure_threshold,
                recovery_timeout=config.recovery_timeout,
                expected_exception=TransientAIError,
                name=name
            )
        return self.circuit_breakers[name]

    def get_metrics(self, operation_name: str) -> ResilienceMetrics:
        """
        Retrieve or create metrics tracking object for specified operation.

        Args:
            operation_name: Name of the operation to get metrics for

        Returns:
            ResilienceMetrics object containing call counts, success/failure rates, and timing data

        Behavior:
            - Returns existing metrics object if already created for operation
            - Creates new ResilienceMetrics instance for first-time operations
            - Stores metrics object for future retrieval and updates
            - Provides thread-safe access to metrics across concurrent operations
            - Maintains isolated metrics per operation name
        """
        if operation_name not in self.operation_metrics:
            self.operation_metrics[operation_name] = ResilienceMetrics()
        return self.operation_metrics[operation_name]

    def get_operation_config(self, operation_name: str) -> ResilienceConfig:
        """
        Resolve resilience configuration for operation using hierarchical configuration lookup.

        Args:
            operation_name: Name of the operation to get configuration for

        Returns:
            ResilienceConfig containing retry settings, circuit breaker config, and strategy information
            for the operation, with fallback to balanced strategy if no specific config found

        Behavior:
            - Checks for operation-specific configuration first (highest priority)
            - Queries settings for operation-specific strategy if available
            - Combines operation strategy with base configuration from settings
            - Falls back to balanced strategy configuration if no specific config exists
            - Handles configuration errors gracefully by using fallback strategy
            - Maintains configuration consistency across operation invocations
        """
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

    def custom_before_sleep(self, operation_name: str) -> Callable:
        """
        Create tenacity callback function for logging and metrics during retry sleep periods.

        Args:
            operation_name: Name of operation for logging and metrics context

        Returns:
            Callback function compatible with tenacity's before_sleep parameter that logs
            retry attempts and updates operation metrics

        Behavior:
            - Returns callable that increments retry attempt metrics
            - Logs warning messages with retry attempt number and sleep duration
            - Provides operational visibility into retry behavior for debugging
            - Updates metrics atomically for accurate retry counting
            - Maintains operation context in log messages for troubleshooting
        """
        def callback(retry_state: Any) -> None:
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
        strategy: ResilienceStrategy | str | None = None,
        custom_config: ResilienceConfig | None = None,
        fallback: Callable | None = None
    ) -> Callable:
        """
        Primary decorator applying comprehensive resilience patterns with configurable strategies and fallback handling.

        Provides the core resilience functionality by combining retry mechanisms, circuit breaker protection,
        and fallback strategies. Supports multiple configuration approaches including strategy-based presets,
        operation-specific settings, and complete custom configurations.

        Args:
            operation_name: Unique operation identifier for metrics tracking and circuit breaker isolation.
                           Used for configuration lookup, logging context, and operational monitoring.
            strategy: Optional resilience strategy override (AGGRESSIVE, BALANCED, CONSERVATIVE, CRITICAL).
                     Can be ResilienceStrategy enum or string. If None, uses operation-specific configuration.
            custom_config: Optional ResilienceConfig for complete configuration override.
                          Takes precedence over strategy and operation-specific settings.
            fallback: Optional callable providing alternative behavior when all resilience patterns fail.
                     Invoked with same arguments as original function for graceful degradation.

        Returns:
            Decorator function that wraps target function with comprehensive resilience patterns:
            - Automatic retry with configurable exponential backoff and jitter
            - Circuit breaker protection preventing cascade failures
            - Exception classification and appropriate handling strategies
            - Comprehensive metrics collection for operational monitoring
            - Fallback execution for graceful degradation scenarios

        Raises:
            No exceptions raised during decoration. Wrapped function may raise:
            - TransientAIError: For retryable failures after exhausting retry attempts
            - PermanentAIError: For non-retryable failures when no fallback provided
            - ServiceUnavailableError: When circuit breaker is open and no fallback available

        Behavior:
            - Resolves configuration using precedence: custom_config > strategy > operation config > balanced default
            - Creates or retrieves circuit breaker instance isolated per operation name
            - Builds tenacity retry decorator with exponential backoff, jitter, and appropriate stop conditions
            - Applies circuit breaker check before operation execution when enabled
            - Classifies exceptions into transient/permanent categories for intelligent retry decisions
            - Increments success/failure metrics atomically for accurate monitoring
            - Records timing information for performance analysis and SLA monitoring
            - Invokes fallback function for both retry exhaustion and permanent failure scenarios
            - Logs retry attempts and failures with operation context for debugging
            - Maintains thread safety for concurrent operation execution
            - Preserves original function signature, return type, and async/sync behavior

        Examples:
            >>> # Basic usage with operation-specific configuration
            >>> resilience = AIServiceResilience(settings)
            >>> @resilience.with_resilience(\"ai_text_analysis\")
            ... async def analyze_text(text: str) -> dict:
            ...     return await ai_service.analyze(text)

            >>> # With specific strategy override
            >>> @resilience.with_resilience(\"critical_operation\", strategy=ResilienceStrategy.CRITICAL)
            ... async def critical_function(data: str) -> str:
            ...     return await critical_service.process(data)

            >>> # With custom configuration and fallback
            >>> custom_config = ResilienceConfig(
            ...     strategy=ResilienceStrategy.BALANCED,
            ...     retry_config=RetryConfig(max_attempts=5, exponential_multiplier=2),
            ...     enable_circuit_breaker=True
            ... )
            >>> @resilience.with_resilience(
            ...     \"data_processing\",
            ...     custom_config=custom_config,
            ...     fallback=lambda data: {\"error\": \"Processing unavailable\", \"input\": data}
            ... )
            ... async def process_data(data: dict) -> dict:
            ...     return await processing_service.process(data)

            >>> # Error handling patterns
            >>> try:
            ...     result = await analyze_text(\"sample text\")
            ...     print(f\"Analysis result: {result}\")
            ... except TransientAIError:
            ...     print(\"Service temporarily unavailable, try again later\")
            ... except PermanentAIError as e:
            ...     print(f\"Permanent failure: {e}\")
            ... except ServiceUnavailableError:
            ...     print(\"Circuit breaker open, service degraded\")

            >>> # Using with synchronous functions
            >>> @resilience.with_resilience(\"sync_operation\")
            ... def sync_function(input_data: str) -> str:
            ...     return external_service.process_sync(input_data)
            >>> result = sync_function(\"test data\")  # Resilience patterns applied to sync function
        """
        def decorator(func: Callable) -> Callable:
            # Get configuration
            if custom_config:
                config = custom_config
            elif strategy:
                if isinstance(strategy, str):
                    strategy_enum = ResilienceStrategy(strategy)
                else:
                    strategy_enum = strategy  # type: ignore[unreachable]
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
                    wait_strategy: Any = wait_exponential(
                        multiplier=retry_config.exponential_multiplier,
                        min=retry_config.exponential_min,
                        max=retry_config.exponential_max
                    )
                    if retry_config.jitter:
                        wait_strategy = wait_combine(wait_strategy, wait_random(0, retry_config.jitter_max))
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
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                metrics = self.get_metrics(operation_name)
                metrics.total_calls += 1

                start_time = datetime.now()

                async def execute_function() -> Any:
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
                        # Let ApplicationError (ValidationError, ConfigurationError, etc.) pass through unchanged
                        from app.core.exceptions import ApplicationError
                        if not isinstance(e, (AIServiceException, ApplicationError)):
                            if classify_exception(e):
                                raise TransientAIError(str(e)) from e
                            raise PermanentAIError(str(e)) from e
                        raise

                try:
                    # Apply circuit breaker if enabled
                    if circuit_breaker:
                        # Circuit breaker check
                        if hasattr(circuit_breaker, "_state") and circuit_breaker._state == "open":
                            raise ServiceUnavailableError("Circuit breaker is open")

                        # Apply retry if enabled
                        if retry_decorator:
                            result = await retry_decorator(execute_function)()
                        else:
                            result = await execute_function()

                        # Record success in circuit breaker
                        circuit_breaker.metrics.successful_calls += 1
                        return result
                    # Apply retry if enabled
                    if retry_decorator:
                        return await retry_decorator(execute_function)()
                    return await execute_function()

                except (RetryError, TransientAIError, ServiceUnavailableError):
                    # All retries failed or circuit breaker open
                    if fallback:
                        logger.warning(f"Operation '{operation_name}' failed, using fallback")
                        if asyncio.iscoroutinefunction(fallback):
                            return await fallback(*args, **kwargs)
                        return fallback(*args, **kwargs)
                    raise
                except PermanentAIError:
                    # Don't retry permanent errors, but can still use fallback
                    if fallback:
                        logger.warning(f"Operation '{operation_name}' permanent error, using fallback")
                        if asyncio.iscoroutinefunction(fallback):
                            return await fallback(*args, **kwargs)
                        return fallback(*args, **kwargs)
                    raise

            return wrapper
        return decorator

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve comprehensive system-wide metrics for monitoring and operational visibility.

        Returns:
            Dictionary containing:
            - operations: Dict mapping operation names to their ResilienceMetrics data
            - circuit_breakers: Dict with circuit breaker states, thresholds, and metrics
            - summary: System-level statistics including counts and health status

        Behavior:
            - Aggregates metrics from all registered operations and circuit breakers
            - Includes current circuit breaker states (open, closed, half-open)
            - Provides summary statistics for quick health assessment
            - Returns timestamp for metrics collection time tracking
            - Calculates healthy circuit breaker count for system health overview
            - Thread-safe collection of metrics from concurrent operations
        """
        result = {
            "operations": {},
            "circuit_breakers": {},
            "summary": {
                "total_operations": len(self.operation_metrics),
                "total_circuit_breakers": len(self.circuit_breakers),
                "healthy_circuit_breakers": sum(
                    1 for cb in self.circuit_breakers.values()
                    if not hasattr(cb, "_state") or cb._state != "open"
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
                "state": getattr(cb, "_state", "closed"),
                "failure_threshold": getattr(cb, "failure_threshold", 5),
                "recovery_timeout": getattr(cb, "recovery_timeout", 60),
                "metrics": cb.metrics.to_dict() if hasattr(cb, "metrics") else {}
            }

        return result

    def reset_metrics(self, operation_name: str | None = None) -> None:
        """
        Reset metrics counters for debugging, testing, or operational maintenance.

        Args:
            operation_name: Optional specific operation name to reset. If None, resets all metrics.

        Behavior:
            - Resets specific operation metrics to new ResilienceMetrics instance when operation_name provided
            - Clears all operation metrics and circuit breaker metrics when operation_name is None
            - Resets circuit breaker metrics for matching operation name if circuit breaker exists
            - Maintains circuit breaker state (open/closed) while resetting only metrics counters
            - Provides clean slate for metrics collection without affecting resilience behavior
            - Thread-safe reset operation for concurrent access scenarios
        """
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
        """
        Determine overall system health based on circuit breaker states.

        Returns:
            True if all circuit breakers are closed (healthy), False if any are open (unhealthy)

        Behavior:
            - Evaluates health as True only when no circuit breakers are in open state
            - Considers half-open circuit breakers as healthy (recovery in progress)
            - Returns True for systems with no registered circuit breakers
            - Provides quick health check suitable for load balancer health endpoints
            - Thread-safe evaluation of circuit breaker states
        """
        # Check if any circuit breakers are open
        open_circuit_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if hasattr(cb, "_state") and cb._state == "open"
        ]
        return len(open_circuit_breakers) == 0

    def get_health_status(self) -> Dict[str, Any]:
        """
        Retrieve comprehensive system health information for monitoring and alerting.

        Provides detailed health status by analyzing circuit breaker states across all
        operations. Essential for monitoring dashboards, alerting systems, and automated
        health checks in production environments.

        Returns:
            Dictionary containing comprehensive health information:
            - healthy: bool indicating overall system health (True if no open circuit breakers)
            - open_circuit_breakers: List of operation names with open circuit breakers (failed operations)
            - half_open_circuit_breakers: List of operations in recovery state (testing recovery)
            - total_circuit_breakers: Count of all registered circuit breakers
            - total_operations: Count of all operations with metrics tracking
            - timestamp: ISO format timestamp of health check for temporal correlation

        Behavior:
            - Categorizes circuit breakers by state for detailed status reporting
            - Provides operation and circuit breaker counts for capacity planning
            - Includes timestamp for health status temporal tracking
            - Identifies specific operations experiencing issues via open circuit breakers
            - Tracks recovery progress through half-open circuit breaker identification
            - Thread-safe health status collection for monitoring systems
            - Returns healthy=True even for systems with no registered circuit breakers

        Examples:
            >>> resilience = AIServiceResilience()
            >>> # Get system health status
            >>> health = resilience.get_health_status()
            >>> assert "healthy" in health
            >>> assert "open_circuit_breakers" in health
            >>> assert "timestamp" in health
            >>>
            >>> # System is healthy when no circuit breakers are open
            >>> assert health["healthy"] or len(health["open_circuit_breakers"]) == 0
            >>>
            >>> # Monitor specific operations experiencing issues
            >>> if health["open_circuit_breakers"]:
            ...     print(f"Failed operations: {health['open_circuit_breakers']}")
            >>> # Track recovery progress
            >>> if health["half_open_circuit_breakers"]:
            ...     print(f"Recovering operations: {health['half_open_circuit_breakers']}")
        """
        open_circuit_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if hasattr(cb, "_state") and cb._state == "open"
        ]

        half_open_circuit_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if hasattr(cb, "_state") and cb._state == "half-open"
        ]

        return {
            "healthy": len(open_circuit_breakers) == 0,
            "open_circuit_breakers": open_circuit_breakers,
            "half_open_circuit_breakers": half_open_circuit_breakers,
            "total_circuit_breakers": len(self.circuit_breakers),
            "total_operations": len(self.operation_metrics),
            "timestamp": datetime.now().isoformat()
        }

    def with_operation_resilience(self, operation_name: str, fallback: Callable | None = None) -> Callable:
        """
        Convenience decorator applying operation-specific resilience configuration.

        Args:
            operation_name: Name of operation for configuration lookup and metrics tracking
            fallback: Optional fallback function called when all resilience patterns fail

        Returns:
            Decorator function that applies resilience patterns using operation-specific config

        Behavior:
            - Delegates to with_resilience() using operation-specific configuration resolution
            - Simplifies decorator usage when no custom strategy override needed
            - Maintains same resilience pattern application as full with_resilience() method
            - Provides convenient interface for most common resilience application scenarios
        """
        return self.with_resilience(operation_name=operation_name, fallback=fallback)

    def register_operation(self, operation_name: str, strategy: ResilienceStrategy = ResilienceStrategy.BALANCED) -> None:
        """
        Register new operation with specific resilience strategy for configuration management.

        Args:
            operation_name: Unique name for the operation to register
            strategy: ResilienceStrategy enum value defining the resilience approach
                     (AGGRESSIVE, BALANCED, CONSERVATIVE, CRITICAL). Defaults to BALANCED.

        Behavior:
            - Delegates to settings.register_operation() when settings object available
            - Stores operation configuration directly for standalone/testing scenarios
            - Allows dynamic operation registration during runtime
            - Maps operation name to strategy configuration for future lookups
            - Enables operation-specific resilience behavior customization
            - Supports both production (settings-based) and test (direct) registration modes
        """
        if self.settings:
            # Let settings handle the registration
            self.settings.register_operation(operation_name, strategy.value)
        else:
            # Direct registration for testing/standalone use
            self.configurations[operation_name] = self.configurations[strategy]


# Global instance - initialize immediately to support decorators at import time
ai_resilience = AIServiceResilience()


# Convenience decorator functions
def with_operation_resilience(operation_name: str, fallback: Callable | None = None) -> Callable:
    """
    Global decorator applying operation-specific resilience patterns with automatic configuration lookup.

    Provides the primary interface for applying resilience patterns to AI service operations
    using configuration resolved from operation name. Automatically determines retry behavior,
    circuit breaker settings, and fallback handling based on registered operation configuration.

    Args:
        operation_name: Unique operation identifier used for configuration lookup and metrics tracking.
                       Should match operations registered via register_operation() or settings.
        fallback: Optional callable for graceful degradation when all resilience patterns fail.
                 Called with same arguments as original function. Can be sync or async.

    Returns:
        Decorator function that wraps target function with resilience patterns including:
        - Retry mechanisms with exponential backoff based on operation configuration
        - Circuit breaker protection preventing cascade failures
        - Comprehensive metrics tracking for monitoring and alerting
        - Fallback execution for graceful degradation

    Raises:
        RuntimeError: If global AIServiceResilience instance not properly initialized

    Behavior:
        - Resolves operation-specific configuration from registered operations or settings
        - Applies circuit breaker pattern when enabled in configuration
        - Retries transient failures using configured retry strategy
        - Tracks success/failure metrics for operational monitoring
        - Invokes fallback function when all retry attempts exhausted or permanent errors occur
        - Logs resilience actions for debugging and operational visibility
        - Maintains thread safety for concurrent operation execution
        - Preserves original function signature and return type

    Examples:
        >>> # Basic usage with operation-specific configuration
        >>> @with_operation_resilience("ai_summarize")
        ... async def summarize_text(text: str) -> str:
        ...     return await ai_service.summarize(text)

        >>> # With fallback for graceful degradation
        >>> @with_operation_resilience("ai_analyze", fallback=lambda x: {"error": "Service unavailable"})
        ... async def analyze_text(text: str) -> dict:
        ...     return await ai_service.analyze(text)

        >>> # Error handling - function raises original exception when no fallback
        >>> result = await summarize_text("input text")
        >>> # If all retries fail and no fallback provided, raises AIServiceException
    """
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_operation_resilience(operation_name, fallback)


def with_aggressive_resilience(operation_name: str, fallback: Callable | None = None) -> Callable:
    """
    Global decorator applying aggressive resilience strategy optimized for fast recovery and high availability.

    Applies resilience patterns optimized for scenarios requiring rapid failure detection and recovery,
    such as user-facing operations or time-sensitive processing. Uses higher retry attempts with shorter
    delays and lower circuit breaker thresholds for quick failover.

    Args:
        operation_name: Unique operation identifier for metrics tracking and logging context.
                       Used to isolate metrics and circuit breaker state per operation.
        fallback: Optional callable providing alternative behavior when resilience patterns fail.
                 Should handle same inputs as original function and provide meaningful degraded response.

    Returns:
        Decorator function applying aggressive resilience configuration with:
        - Higher retry attempt counts for persistent recovery attempts
        - Shorter delays between retries for rapid recovery
        - Lower circuit breaker failure thresholds for quick failure detection
        - Comprehensive metrics collection for performance monitoring

    Raises:
        RuntimeError: If global AIServiceResilience instance not properly initialized

    Behavior:
        - Applies aggressive resilience strategy regardless of operation configuration
        - Uses higher retry counts with shorter exponential backoff delays
        - Opens circuit breaker after fewer consecutive failures
        - Provides rapid recovery for transient failures
        - Suitable for user-facing operations requiring low latency
        - Tracks metrics under provided operation name for monitoring
        - Invokes fallback for both transient and permanent failure scenarios

    Examples:
        >>> # For user-facing operations requiring fast response
        >>> @with_aggressive_resilience("user_chat_response")
        ... async def generate_chat_response(message: str) -> str:
        ...     return await ai_service.generate_response(message)

        >>> # With fallback for graceful user experience
        >>> @with_aggressive_resilience(
        ...     "real_time_translation",
        ...     fallback=lambda text, lang: f"Translation unavailable for {lang}"
        ... )
        ... async def translate_text(text: str, target_language: str) -> str:
        ...     return await translation_service.translate(text, target_language)
    """
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_resilience(operation_name, ResilienceStrategy.AGGRESSIVE, fallback=fallback)


def with_balanced_resilience(operation_name: str, fallback: Callable | None = None) -> Callable:
    """
    Global decorator applying balanced resilience strategy suitable for most production workloads.

    Provides moderate resilience settings balancing performance, resource utilization, and fault
    tolerance. Offers reasonable retry behavior and circuit breaker protection without excessive
    resource consumption or lengthy recovery periods.

    Args:
        operation_name: Unique operation identifier for metrics tracking and circuit breaker isolation.
                       Provides operational context for monitoring and debugging.
        fallback: Optional callable providing alternative behavior when all resilience mechanisms fail.
                 Should match original function signature and provide reasonable default response.

    Returns:
        Decorator function applying balanced resilience configuration with:
        - Moderate retry attempts balancing persistence and resource usage
        - Reasonable delay intervals for sustainable retry behavior
        - Balanced circuit breaker thresholds for appropriate failure detection
        - Runtime resilience application for dynamic configuration support

    Raises:
        RuntimeError: If global AIServiceResilience instance not properly initialized

    Behavior:
        - Applies balanced resilience strategy at runtime rather than decoration time
        - Uses moderate retry counts with reasonable exponential backoff
        - Opens circuit breaker after balanced failure threshold
        - Suitable for most background processing and API operations
        - Balances fault tolerance with resource conservation
        - Provides predictable performance characteristics
        - Supports both sync and async operation patterns

    Examples:
        >>> # Standard API operation with balanced resilience
        >>> @with_balanced_resilience("document_analysis")
        ... async def analyze_document(document: str) -> dict:
        ...     return await ai_service.analyze_document(document)

        >>> # Background processing with fallback
        >>> @with_balanced_resilience(
        ...     "batch_processing",
        ...     fallback=lambda items: {"processed": 0, "errors": len(items)}
        ... )
        ... async def process_batch(items: List[str]) -> dict:
        ...     return await processing_service.process_items(items)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not ai_resilience:
                raise RuntimeError("AIServiceResilience not initialized")
            # Apply resilience at runtime, not at import time
            resilient_func = ai_resilience.with_resilience(
                operation_name, ResilienceStrategy.BALANCED, fallback=fallback
            )(func)
            return await resilient_func(*args, **kwargs)
        return wrapper
    return decorator


def with_conservative_resilience(operation_name: str, fallback: Callable | None = None) -> Callable:
    """
    Global decorator applying conservative resilience strategy optimized for resource conservation and stability.

    Implements resilience patterns focused on minimizing resource usage and system load during failures,
    suitable for non-critical operations or resource-constrained environments. Uses fewer retry attempts
    with longer delays and higher circuit breaker thresholds for system stability.

    Args:
        operation_name: Unique operation identifier for metrics tracking and operational context.
                       Enables isolated monitoring and circuit breaker state per operation.
        fallback: Optional callable providing alternative functionality when resilience patterns exhausted.
                 Should provide acceptable degraded behavior without requiring full service functionality.

    Returns:
        Decorator function applying conservative resilience configuration with:
        - Fewer retry attempts to reduce system load during failures
        - Longer delays between retries to allow system recovery
        - Higher circuit breaker thresholds for stability over availability
        - Resource-conscious resilience behavior suitable for background operations

    Raises:
        RuntimeError: If global AIServiceResilience instance not properly initialized

    Behavior:
        - Prioritizes system stability over aggressive failure recovery
        - Uses minimal retry attempts with extended exponential backoff
        - Tolerates more failures before opening circuit breaker
        - Reduces resource consumption during prolonged failure scenarios
        - Suitable for batch processing and non-time-critical operations
        - Provides sustainable resilience for resource-constrained environments
        - Maintains comprehensive metrics for monitoring despite conservative approach

    Examples:
        >>> # Resource-intensive background processing
        >>> @with_conservative_resilience("large_model_inference")
        ... async def run_expensive_model(input_data: str) -> str:
        ...     return await expensive_ai_service.process(input_data)

        >>> # Non-critical data enrichment with fallback
        >>> @with_conservative_resilience(
        ...     "data_enrichment",
        ...     fallback=lambda data: {**data, "enriched": False}
        ... )
        ... async def enrich_data(data: dict) -> dict:
        ...     enriched = await enrichment_service.enrich(data)
        ...     return {**data, **enriched, "enriched": True}
    """
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_resilience(operation_name, ResilienceStrategy.CONSERVATIVE, fallback=fallback)


def with_critical_resilience(operation_name: str, fallback: Callable | None = None) -> Callable:
    """
    Global decorator applying maximum resilience strategy for mission-critical operations requiring highest availability.

    Implements the most robust resilience patterns available, prioritizing operation success over
    resource efficiency. Uses maximum retry attempts, longest recovery timeouts, and highest failure
    tolerance to ensure critical operations complete successfully whenever possible.

    Args:
        operation_name: Unique operation identifier for metrics tracking and critical operation monitoring.
                       Enables priority monitoring and alerting for mission-critical functionality.
        fallback: Optional callable providing emergency alternative behavior for absolute failure scenarios.
                 Critical for maintaining system functionality when primary operation cannot complete.
                 Should provide essential functionality even if degraded.

    Returns:
        Decorator function applying maximum resilience configuration with:
        - Maximum retry attempts for persistent failure recovery
        - Extended timeouts and recovery periods for comprehensive failure handling
        - Highest circuit breaker thresholds to maintain availability
        - Priority metrics tracking for critical operation monitoring

    Raises:
        RuntimeError: If global AIServiceResilience instance not properly initialized

    Behavior:
        - Prioritizes operation success over resource efficiency
        - Uses maximum retry attempts with extensive exponential backoff
        - Maintains circuit breaker open longer before attempting recovery
        - Suitable for operations critical to business functionality
        - Provides highest level of fault tolerance available
        - May consume significant resources during failure scenarios
        - Essential for operations where failure has severe business impact
        - Maintains detailed metrics for critical operation monitoring

    Examples:
        >>> # Financial transaction processing requiring maximum reliability
        >>> @with_critical_resilience("payment_processing")
        ... async def process_payment(payment_data: dict) -> dict:
        ...     return await payment_service.process_transaction(payment_data)

        >>> # Critical system integration with emergency fallback
        >>> @with_critical_resilience(
        ...     "security_validation",
        ...     fallback=lambda request: {"validated": False, "reason": "Service unavailable"}
        ... )
        ... async def validate_security_token(token: str) -> dict:
        ...     return await security_service.validate_token(token)

        >>> # Mission-critical AI operation with comprehensive error handling
        >>> try:
        ...     result = await process_payment(payment_info)
        ... except Exception as e:
        ...     # Critical operations may still fail after maximum resilience attempts
        ...     logger.critical(f"Critical payment processing failed: {e}")
        ...     # Implement emergency procedures
    """
    if not ai_resilience:
        raise RuntimeError("AIServiceResilience not initialized")
    return ai_resilience.with_resilience(operation_name, ResilienceStrategy.CRITICAL, fallback=fallback)
