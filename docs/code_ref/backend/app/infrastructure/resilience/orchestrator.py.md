---
sidebar_label: orchestrator
---

# Resilience Orchestrator

  file_path: `backend/app/infrastructure/resilience/orchestrator.py`

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

## AIServiceResilience

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

### __init__()

```python
def __init__(self, settings = None):
```

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

### get_or_create_circuit_breaker()

```python
def get_or_create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> EnhancedCircuitBreaker:
```

Retrieve existing circuit breaker or create new one for operation with specified configuration.

Args:
    name: Unique operation name used as circuit breaker identifier
    config: CircuitBreakerConfig containing failure_threshold, recovery_timeout settings
    
Returns:
    EnhancedCircuitBreaker instance configured for the operation, either existing or newly created
    
Behavior:
    - Returns existing circuit breaker if already created for the operation name
    - Creates new circuit breaker with TransientAIError as expected exception type
    - Stores circuit breaker in internal dictionary for future reuse
    - Applies provided configuration settings to new circuit breakers
    - Maintains circuit breaker isolation per operation name
    - Thread-safe creation and retrieval for concurrent access

### get_metrics()

```python
def get_metrics(self, operation_name: str) -> ResilienceMetrics:
```

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

### get_operation_config()

```python
def get_operation_config(self, operation_name: str) -> ResilienceConfig:
```

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

### custom_before_sleep()

```python
def custom_before_sleep(self, operation_name: str):
```

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

### with_resilience()

```python
def with_resilience(self, operation_name: str, strategy: Union[ResilienceStrategy, str, None] = None, custom_config: Optional[ResilienceConfig] = None, fallback: Optional[Callable] = None):
```

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
    >>> @resilience.with_resilience("ai_text_analysis")
    ... async def analyze_text(text: str) -> dict:
    ...     return await ai_service.analyze(text)
    
    >>> # With specific strategy override
    >>> @resilience.with_resilience("critical_operation", strategy=ResilienceStrategy.CRITICAL)
    ... async def critical_function(data: str) -> str:
    ...     return await critical_service.process(data)
    
    >>> # With custom configuration and fallback
    >>> custom_config = ResilienceConfig(
    ...     strategy=ResilienceStrategy.BALANCED,
    ...     retry_config=RetryConfig(max_attempts=5, exponential_multiplier=2),
    ...     enable_circuit_breaker=True
    ... )
    >>> @resilience.with_resilience(
    ...     "data_processing",
    ...     custom_config=custom_config,
    ...     fallback=lambda data: {"error": "Processing unavailable", "input": data}
    ... )
    ... async def process_data(data: dict) -> dict:
    ...     return await processing_service.process(data)
    
    >>> # Error handling patterns
    >>> try:
    ...     result = await analyze_text("sample text")
    ...     print(f"Analysis result: {result}")
    ... except TransientAIError:
    ...     print("Service temporarily unavailable, try again later")
    ... except PermanentAIError as e:
    ...     print(f"Permanent failure: {e}")
    ... except ServiceUnavailableError:
    ...     print("Circuit breaker open, service degraded")
    
    >>> # Using with synchronous functions
    >>> @resilience.with_resilience("sync_operation")
    ... def sync_function(input_data: str) -> str:
    ...     return external_service.process_sync(input_data)
    >>> result = sync_function("test data")  # Resilience patterns applied to sync function

### get_all_metrics()

```python
def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
```

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

### reset_metrics()

```python
def reset_metrics(self, operation_name: Optional[str] = None):
```

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

### is_healthy()

```python
def is_healthy(self) -> bool:
```

Determine overall system health based on circuit breaker states.

Returns:
    True if all circuit breakers are closed (healthy), False if any are open (unhealthy)
    
Behavior:
    - Evaluates health as True only when no circuit breakers are in open state
    - Considers half-open circuit breakers as healthy (recovery in progress)
    - Returns True for systems with no registered circuit breakers
    - Provides quick health check suitable for load balancer health endpoints
    - Thread-safe evaluation of circuit breaker states

### get_health_status()

```python
def get_health_status(self) -> Dict[str, Any]:
```

Retrieve comprehensive health information for detailed system monitoring.

Returns:
    Dictionary containing:
    - healthy: bool indicating overall system health
    - open_circuit_breakers: List of operation names with open circuit breakers
    - half_open_circuit_breakers: List of operations in recovery state
    - total_circuit_breakers: Count of all registered circuit breakers
    - total_operations: Count of all operations with metrics
    - timestamp: ISO format timestamp of health check
    
Behavior:
    - Categorizes circuit breakers by state for detailed status reporting
    - Provides operation and circuit breaker counts for capacity planning
    - Includes timestamp for health status temporal tracking
    - Identifies specific operations experiencing issues via open circuit breakers
    - Tracks recovery progress through half-open circuit breaker identification
    - Thread-safe health status collection for monitoring systems

### with_operation_resilience()

```python
def with_operation_resilience(self, operation_name: str, fallback: Optional[Callable] = None):
```

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

### register_operation()

```python
def register_operation(self, operation_name: str, strategy: ResilienceStrategy = ResilienceStrategy.BALANCED):
```

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

## with_operation_resilience()

```python
def with_operation_resilience(operation_name: str, fallback: Optional[Callable] = None):
```

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

## with_aggressive_resilience()

```python
def with_aggressive_resilience(operation_name: str, fallback: Optional[Callable] = None):
```

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

## with_balanced_resilience()

```python
def with_balanced_resilience(operation_name: str, fallback: Optional[Callable] = None):
```

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

## with_conservative_resilience()

```python
def with_conservative_resilience(operation_name: str, fallback: Optional[Callable] = None):
```

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

## with_critical_resilience()

```python
def with_critical_resilience(operation_name: str, fallback: Optional[Callable] = None):
```

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
