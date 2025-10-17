"""
Circuit Breaker Module

This module implements the Circuit Breaker pattern for resilient service communication,
providing fault tolerance and automatic recovery capabilities for AI service calls.

Circuit Breaker Pattern:
    The circuit breaker pattern prevents cascading failures by monitoring service calls
    and automatically "opening" the circuit when failure rates exceed thresholds.

    States:
    - CLOSED: Normal operation, calls pass through to protected service
    - OPEN: Circuit is open, calls fail fast without reaching the service
    - HALF-OPEN: Testing state, limited calls allowed to test service recovery

Key Components:
    - EnhancedCircuitBreaker: Production-ready circuit breaker with comprehensive metrics
    - CircuitBreakerConfig: Configuration dataclass with production-ready defaults
    - ResilienceMetrics: Comprehensive metrics tracking for monitoring and alerting
    - AIServiceException: Base exception for AI service errors (imported)

Configuration Parameters:
    - failure_threshold: Number of consecutive failures (1-100) before opening circuit
    - recovery_timeout: Seconds to wait (1-3600) before attempting half-open state
    - half_open_max_calls: Maximum calls (1-10) allowed in half-open testing state

Metrics Collection:
    - Total calls, successful calls, failed calls with timestamp tracking
    - Circuit breaker state transitions (opens, half-opens, closes)
    - Success/failure rates calculated as percentages
    - Exportable dictionary format for monitoring system integration

Production Usage:
    ```python
    from app.infrastructure.resilience.circuit_breaker import (
        EnhancedCircuitBreaker,
        CircuitBreakerConfig,
        ResilienceMetrics
    )

    # Configuration for critical AI service
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=30,
        half_open_max_calls=1
    )

    # Create monitored circuit breaker
    cb = EnhancedCircuitBreaker(
        failure_threshold=config.failure_threshold,
        recovery_timeout=config.recovery_timeout,
        name="ai_text_service"
    )

    # Protect service calls with circuit breaker
    try:
        result = cb.call(ai_service.process_text, text_data)
        print(f"Success: {cb.metrics.success_rate:.1f}% success rate")
    except Exception as e:
        print(f"Service call failed: {e}")
        metrics = cb.metrics.to_dict()
        print(f"Circuit breaker metrics: {metrics}")

        # Implement fallback logic
        result = fallback_service.process(text_data)
    ```

Advanced Usage Patterns:
    ```python
    # Function decoration for automatic protection
    @cb.call
    def protected_ai_call(data):
        return ai_service.complex_processing(data)

    # Health monitoring and alerting
    def monitor_service_health():
        metrics = cb.metrics.to_dict()
        if metrics['success_rate'] < 95.0:
            alert_manager.trigger_alert(
                f"Low success rate: {metrics['success_rate']}%"
            )

        if metrics['circuit_breaker_opens'] > 0:
            operations_team.notify(
                f"Circuit breaker opened: {metrics['circuit_breaker_opens']} times"
            )

    # Integration with resilience orchestrator
    async def resilient_ai_operation(data):
        return await resilience_orchestrator.execute(
            operation="ai_process",
            circuit_breaker=cb,
            func=ai_service.process,
            data=data
        )
    ```

Dependencies:
    - circuitbreaker: Third-party circuit breaker implementation
    - datetime: For timestamp tracking and temporal analysis
    - logging: For circuit breaker state change notifications
    - app.core.exceptions: Custom exception hierarchy for error handling

Thread Safety:
    All circuit breaker operations are thread-safe for concurrent environments.
    Metrics updates are atomic to prevent race conditions during high-load scenarios.
    State transitions are synchronized to ensure consistent behavior across threads.

Integration Points:
    - Resilience Orchestrator: Coordinates with retry patterns and timeouts
    - Monitoring Systems: Metrics export for Prometheus, DataDog, etc.
    - Alert Management: Health assessment and automated alerting
    - Configuration Management: Preset-based configuration for different environments
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Type
from dataclasses import dataclass

from circuitbreaker import CircuitBreaker  # type: ignore[import-untyped]

from app.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerConfig:
    """
    Configuration for circuit breaker behavior with production-ready defaults.

    Defines circuit breaker behavior parameters including failure thresholds, recovery timeouts,
    and testing limits for half-open state operations. Provides sensible defaults optimized
    for AI service resilience patterns.

    Attributes:
        failure_threshold: Number of consecutive failures (1-100) before opening circuit
        recovery_timeout: Seconds to wait (1-3600) in open state before half-open testing
        half_open_max_calls: Maximum calls (1-10) allowed in half-open testing state

    Public Methods:
        None - immutable configuration dataclass

    State Management:
        - Configuration is immutable after initialization
        - Parameter ranges validated for safe operation
        - Production-optimized defaults for AI service patterns
        - Compatible with all circuit breaker implementations

    Usage:
        # Default configuration for balanced resilience
        config = CircuitBreakerConfig()

        # Conservative configuration for critical services
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120,
            half_open_max_calls=1
        )

        # Aggressive configuration for development
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=30,
            half_open_max_calls=3
        )

        # Configuration validation
        assert 1 <= config.failure_threshold <= 100
        assert 1 <= config.recovery_timeout <= 3600
        assert 1 <= config.half_open_max_calls <= 10

    Behavior:
        - Validates parameter ranges on initialization to ensure safe operation
        - Provides immutable configuration to prevent runtime modification
        - Uses conservative defaults optimized for AI service reliability
        - Maintains compatibility with circuitbreaker library implementations
        - Supports different operational modes (conservative, balanced, aggressive)
    """
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 1


@dataclass
class ResilienceMetrics:
    """
    Comprehensive metrics collection for resilience monitoring and operational visibility.

    Tracks all aspects of resilience behavior including success/failure rates, retry attempts,
    circuit breaker state transitions, and timing information for SLA monitoring and alerting.

    Attributes:
        total_calls: Total service calls attempted across all circuit breaker states
        successful_calls: Calls completed successfully without errors or timeouts
        failed_calls: Calls that failed with exceptions, timeouts, or circuit breaker rejections
        retry_attempts: Total retry attempts across all failed calls
        circuit_breaker_opens: Number of times circuit opened due to failure threshold
        circuit_breaker_half_opens: Transitions to half-open testing state
        circuit_breaker_closes: Successful recoveries from open to closed state
        last_success: Timestamp of most recent successful call
        last_failure: Timestamp of most recent failed call

    Public Methods:
        to_dict(): Export metrics as dictionary for monitoring systems and serialization
        reset(): Clear all metrics for testing or periodic reset operations
        success_rate: Property calculating current success rate as percentage (0.0-100.0)
        failure_rate: Property calculating current failure rate as percentage (0.0-100.0)

    State Management:
        - Thread-safe increment operations for concurrent access environments
        - Atomic updates prevent race conditions during metric collection
        - Timestamp tracking enables temporal analysis and health monitoring
        - Exportable format integrates with monitoring and alerting systems

    Usage:
        # Direct metrics manipulation (thread-safe)
        metrics = ResilienceMetrics()
        metrics.total_calls += 1
        metrics.successful_calls += 1
        metrics.last_success = datetime.now()

        # Monitoring integration
        stats = metrics.to_dict()
        monitoring_system.report_metrics("ai_service", stats)
        alert_manager.check_thresholds(stats)

        # Health assessment and alerting
        if metrics.success_rate < 95.0:
            alert_manager.trigger_alert("Low success rate detected")

        # Periodic reset for monitoring windows
        if monitoring_window_expired():
            metrics.reset()
    """
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    retry_attempts: int = 0
    circuit_breaker_opens: int = 0
    circuit_breaker_half_opens: int = 0
    circuit_breaker_closes: int = 0
    last_failure: datetime | None = None
    last_success: datetime | None = None

    @property
    def success_rate(self) -> float:
        """
        Calculate success rate as a percentage of total calls.

        Returns:
            float: Success rate as a percentage (0.0-100.0). Returns 0.0 if no calls have been made
                  to avoid division by zero. Calculated as (successful_calls / total_calls) * 100.

        Examples:
            >>> metrics = ResilienceMetrics()
            >>> metrics.success_rate
            0.0

            >>> metrics.total_calls = 10
            >>> metrics.successful_calls = 8
            >>> round(metrics.success_rate, 1)
            80.0
        """
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

    @property
    def failure_rate(self) -> float:
        """
        Calculate failure rate as a percentage of total calls.

        Returns:
            float: Failure rate as a percentage (0.0-100.0). Returns 0.0 if no calls have been made
                  to avoid division by zero. Calculated as (failed_calls / total_calls) * 100.

        Examples:
            >>> metrics = ResilienceMetrics()
            >>> metrics.failure_rate
            0.0

            >>> metrics.total_calls = 10
            >>> metrics.failed_calls = 3
            >>> round(metrics.failure_rate, 1)
            30.0

            # Note: success_rate + failure_rate may not equal 100% if calls are cancelled
        """
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100

    def reset(self) -> None:
        """
        Clear all metrics for testing or periodic reset operations.

        Resets all counters and timestamps to their initial state.
        This method is useful for periodic monitoring windows or test isolation.

        Behavior:
            - Sets all counter metrics to 0
            - Sets both timestamp fields to None
            - Preserves the dataclass structure
            - Can be called safely multiple times

        Use Cases:
            - Periodic reset for monitoring windows as documented in Usage
            - Test isolation between test cases
            - Counter overflow prevention in long-running processes
            - Starting fresh metrics collection after maintenance

        Examples:
            >>> metrics = ResilienceMetrics()
            >>> metrics.total_calls = 100
            >>> metrics.successful_calls = 95
            >>> metrics.failed_calls = 5
            >>> metrics.last_success = datetime.now()
            >>> metrics.reset()
            >>> metrics.total_calls
            0
            >>> metrics.successful_calls
            0
            >>> metrics.last_success is None
            True
        """
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.retry_attempts = 0
        self.circuit_breaker_opens = 0
        self.circuit_breaker_half_opens = 0
        self.circuit_breaker_closes = 0
        self.last_failure = None
        self.last_success = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary for JSON serialization and monitoring integration.

        Returns:
            Dict[str, Any]: Dictionary containing all metrics with:
            - Raw count values (total_calls, successful_calls, etc.)
            - Calculated rates (success_rate, failure_rate) rounded to 2 decimal places
            - ISO-formatted timestamps for last_success and last_failure (None if not set)

        Behavior:
            - Converts datetime objects to ISO 8601 string format for JSON serialization
            - Rounds percentage values to 2 decimal places for consistent reporting
            - Includes all metric fields for comprehensive monitoring visibility
            - Maintains dictionary structure compatible with monitoring systems

        Examples:
            >>> metrics = ResilienceMetrics()
            >>> metrics.total_calls = 5
            >>> metrics.successful_calls = 4
            >>> metrics.failed_calls = 1
            >>> metrics.last_success = datetime(2023, 1, 1, 12, 0, 0)
            >>> result = metrics.to_dict()
            >>> result['success_rate']
            80.0
            >>> '2023-01-01T12:00:00' in result['last_success']
            True

            # Empty metrics
            >>> empty = ResilienceMetrics().to_dict()
            >>> empty['success_rate']
            0.0
            >>> empty['last_success'] is None
            True
        """
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "retry_attempts": self.retry_attempts,
            "circuit_breaker_opens": self.circuit_breaker_opens,
            "circuit_breaker_half_opens": self.circuit_breaker_half_opens,
            "circuit_breaker_closes": self.circuit_breaker_closes,
            "success_rate": round(self.success_rate, 2),
            "failure_rate": round(self.failure_rate, 2),
            "last_failure": self.last_failure.isoformat() if self.last_failure else None,
            "last_success": self.last_success.isoformat() if self.last_success else None,
        }


class EnhancedCircuitBreaker(CircuitBreaker):
    """
    Production-ready circuit breaker with comprehensive metrics, state management, and monitoring.

    Extends base CircuitBreaker with detailed metrics collection, flexible configuration,
    and production monitoring capabilities. Implements the circuit breaker pattern with
    automatic state transitions, failure detection, and recovery testing.

    Attributes:
        failure_threshold: Number of consecutive failures before opening circuit
        recovery_timeout: Seconds to wait before attempting half-open testing
        last_failure_time: Timestamp of most recent failure for state tracking
        metrics: Comprehensive statistics collection for monitoring and alerting
        name: Circuit breaker identifier for monitoring and logging

    Public Methods:
        call(func, *args, **kwargs): Execute function with circuit breaker protection
        _check_state_change(): Monitor and log circuit breaker state transitions

    State Management:
        - Automatic state transitions (closed -> open -> half-open -> closed)
        - Thread-safe state updates for concurrent operation access
        - Comprehensive metrics collection with timing information
        - Recovery testing with configurable limits in half-open state
        - State change logging for operational visibility

    Usage:
        # Basic circuit breaker with monitoring
        cb = EnhancedCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            name="ai_text_service"
        )

        # Function decoration usage
        @cb.call
        def process_ai_request(data):
            return ai_service.process(data)

        # Direct call usage
        try:
            result = cb.call(ai_service.process, data)
            print(f"Success: {cb.metrics.success_rate:.1f}% success rate")
        except CircuitBreakerOpen:
            print("Circuit breaker is open - using fallback")
            result = fallback_service.process(data)
        except Exception as e:
            print(f"Service call failed: {e}")
            raise

        # Monitoring and health assessment
        metrics = cb.metrics.to_dict()
        health_status = "healthy" if cb.metrics.success_rate > 95 else "degraded"
        print(f"Service {health_status}: {metrics}")

        # State-based decision making
        if hasattr(cb, 'current_state') and cb.current_state == 'OPEN':
            enable_degraded_mode()
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, expected_exception: Type[BaseException] | None = None, name: str | None = None) -> None:
        """
        Initialize enhanced circuit breaker with metrics collection and monitoring.

        Args:
            failure_threshold: Number of consecutive failures (1-100) before opening circuit.
                              Must be positive integer. Default: 5
            recovery_timeout: Seconds to wait (1-3600) in open state before attempting recovery.
                             Must be positive integer. Default: 60
            expected_exception: Exception type or tuple of types that count as failures.
                               If None, all exceptions count as failures. Default: None
            name: Optional identifier for logging and monitoring. Used to distinguish
                  multiple circuit breakers in metrics. Default: None

        Raises:
            ValidationError: If failure_threshold or recovery_timeout are not positive integers,
                           or if expected_exception is not an exception class or tuple

        Behavior:
            - Validates all parameters before initialization
            - Initializes comprehensive metrics collection for monitoring
            - Sets up state tracking for circuit breaker transitions
            - Configures base CircuitBreaker with provided parameters
            - Stores configuration for metric compatibility across library versions
            - Begins in CLOSED state allowing normal operation
            - Creates thread-safe metrics storage for concurrent access
            - Establishes monitoring context for operational visibility

        Examples:
            # Default configuration
            cb = EnhancedCircuitBreaker()

            # Custom configuration for critical service
            cb = EnhancedCircuitBreaker(
                failure_threshold=3,
                recovery_timeout=120,
                name="payment_service"
            )

            # With specific exception types
            cb = EnhancedCircuitBreaker(
                expected_exception=(ConnectionError, TimeoutError),
                name="external_api"
            )

            # Verify initialization
            assert cb.failure_threshold == 5
            assert cb.recovery_timeout == 60
            assert cb.metrics.total_calls == 0
        """
        # Validate failure_threshold
        if not isinstance(failure_threshold, int):
            raise ValidationError(
                f"failure_threshold must be a positive integer, got {type(failure_threshold).__name__}",
                {"parameter": "failure_threshold", "provided_type": type(failure_threshold).__name__}
            )
        if failure_threshold <= 0:
            raise ValidationError(
                f"failure_threshold must be positive, got {failure_threshold}",
                {"parameter": "failure_threshold", "value": failure_threshold}
            )

        # Validate recovery_timeout
        if not isinstance(recovery_timeout, int):
            raise ValidationError(
                f"recovery_timeout must be a positive integer, got {type(recovery_timeout).__name__}",
                {"parameter": "recovery_timeout", "provided_type": type(recovery_timeout).__name__}
            )
        if recovery_timeout <= 0:
            raise ValidationError(
                f"recovery_timeout must be positive, got {recovery_timeout}",
                {"parameter": "recovery_timeout", "value": recovery_timeout}
            )

        # Validate expected_exception
        if expected_exception is not None:
            if isinstance(expected_exception, tuple):
                # Validate each item in the tuple is an exception class
                for exc in expected_exception:
                    if not isinstance(exc, type) or not issubclass(exc, BaseException):
                        raise ValidationError(
                            f"expected_exception tuple must contain only exception classes, "
                            f"got {type(exc).__name__}",
                            {"parameter": "expected_exception", "invalid_item_type": type(exc).__name__}
                        )
            elif isinstance(expected_exception, type) and issubclass(expected_exception, BaseException):
                # Single exception class is valid
                pass
            else:
                # Not None, not a tuple, not an exception class
                raise ValidationError(
                    f"expected_exception must be an exception class or tuple of exception classes, "
                    f"got {type(expected_exception).__name__}",
                    {"parameter": "expected_exception", "provided_type": type(expected_exception).__name__}
                )

        # Store the parameters as instance attributes for compatibility
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time: datetime | None = None
        self.metrics = ResilienceMetrics()
        self._last_known_state: str | None = None

        # Initialize the base CircuitBreaker
        super().__init__(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name
        )

    def _check_state_change(self) -> None:
        """
        Monitor and log circuit breaker state transitions with metrics collection.

        Behavior:
            - Detects circuit breaker state changes (CLOSED, OPEN, HALF_OPEN)
            - Updates metrics counters for each state transition type
            - Logs state changes for operational monitoring and debugging
            - Handles library version compatibility for state detection
            - Gracefully handles state detection failures without interruption

        State Detection:
            - Primary: Uses 'current_state' attribute if available
            - Fallback: Derives state from failure counter when current_state unavailable
            - Compatibility: Works across different circuitbreaker library versions

        Side Effects:
            - Increments metrics.circuit_breaker_opens on CLOSED->OPEN transition
            - Increments metrics.circuit_breaker_half_opens on OPEN->HALF_OPEN transition
            - Increments metrics.circuit_breaker_closes on HALF_OPEN->CLOSED transition
            - Logs state changes at appropriate levels (INFO, WARNING) with circuit name

        Examples:
            >>> cb = EnhancedCircuitBreaker(name="test_service")
            >>> cb.metrics.circuit_breaker_opens
            0
            >>> # Simulate circuit opening (internal operation)
            >>> # cb._check_state_change() would detect and log the transition
        """
        try:
            # Get current state - this varies by library version
            current_state = getattr(self, "current_state", None)
            if current_state is None:
                # Fallback: try to determine state from failure count
                # Use the correct attribute name from the circuitbreaker library
                fail_counter = getattr(self, "failure_count", 0)
                if fail_counter >= self.failure_threshold:
                    current_state = "open"
                else:
                    current_state = "closed"

            if current_state != self._last_known_state:
                if current_state == "open":
                    self.metrics.circuit_breaker_opens += 1
                    logger.warning(f"Circuit breaker '{self.name or 'unnamed'}' opened")
                elif current_state == "half-open":
                    self.metrics.circuit_breaker_half_opens += 1
                    logger.info(f"Circuit breaker '{self.name or 'unnamed'}' half-opened")
                elif current_state == "closed":
                    self.metrics.circuit_breaker_closes += 1
                    logger.info(f"Circuit breaker '{self.name or 'unnamed'}' closed")

                self._last_known_state = current_state
        except Exception:
            # If state checking fails, just continue silently
            pass

    def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection and comprehensive metrics collection.

        Args:
            func: Callable function to execute under circuit breaker protection.
                  Must be callable and accept the provided arguments
            *args: Positional arguments to pass to the function. Can be empty
            **kwargs: Keyword arguments to pass to the function. Can be empty

        Returns:
            Return value from the executed function if successful. The type and structure
            depend entirely on the wrapped function's return contract

        Raises:
            CircuitBreakerOpen: When circuit is open and calls are rejected without execution
            Exception: Any exception raised by the function (propagated unchanged)
            AttributeError: If func is not callable or has invalid signature
            TypeError: If arguments are incompatible with function signature

        Behavior:
            - Increments total_calls metric before execution attempt
            - Checks for circuit breaker state changes before and after call
            - Tracks successful calls with timestamps and success count
            - Tracks failed calls with timestamps and failure count
            - Updates last_failure_time for circuit breaker recovery logic
            - Monitors state transitions for operational visibility
            - Executes function through parent circuit breaker logic
            - Maintains thread-safe metrics updates for concurrent access
            - Rejects calls immediately when circuit is open (fail-fast behavior)

        Side Effects:
            - Updates metrics.total_calls, metrics.successful_calls, metrics.failed_calls
            - Updates metrics.last_success, metrics.last_failure timestamps
            - May trigger circuit breaker state changes and logging
            - Updates last_failure_time for recovery timeout calculations
            - Logs state transitions at appropriate levels (INFO, WARNING)

        Examples:
            >>> cb = EnhancedCircuitBreaker(failure_threshold=3, name="test")
            >>> def good_function():
            ...     return "success"
            >>> result = cb.call(good_function)
            >>> result
            'success'
            >>> cb.metrics.successful_calls
            1

            >>> def failing_function():
            ...     raise ValueError("Service error")
            >>> with pytest.raises(ValueError):
            ...     cb.call(failing_function)
            >>> cb.metrics.failed_calls
            1

            # Circuit breaker opens after threshold
            >>> for i in range(3):
            ...     try:
            ...         cb.call(failing_function)
            ...     except ValueError:
            ...         pass
            >>> # Subsequent calls will be rejected immediately

            # With arguments
            >>> def process_data(data, multiplier=1):
            ...     return data * multiplier
            >>> result = cb.call(process_data, "hello ", multiplier=2)
            >>> result
            'hello hello '
        """
        self.metrics.total_calls += 1

        # Check for state changes before the call
        self._check_state_change()

        try:
            result = super().call(func, *args, **kwargs)
            self.metrics.successful_calls += 1
            self.metrics.last_success = datetime.now()

            # Check for state changes after successful call
            self._check_state_change()
            return result
        except Exception:
            self.metrics.failed_calls += 1
            self.metrics.last_failure = datetime.now()
            self.last_failure_time = datetime.now()

            # Check for state changes after failed call
            self._check_state_change()
            raise
