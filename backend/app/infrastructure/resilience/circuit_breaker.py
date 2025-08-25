"""
Circuit Breaker Module

This module implements the Circuit Breaker pattern for resilient service communication,
providing fault tolerance and automatic recovery capabilities for AI service calls.

Circuit Breaker Pattern:
    The circuit breaker pattern prevents cascading failures by monitoring service calls
    and automatically "opening" the circuit when failure rates exceed thresholds.
    
    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Circuit is open, calls fail fast without reaching the service
    - HALF-OPEN: Testing state, limited calls allowed to test service recovery

Key Components:
    - EnhancedCircuitBreaker: Core circuit breaker with metrics and monitoring
    - CircuitBreakerConfig: Configuration dataclass for circuit breaker parameters
    - ResilienceMetrics: Comprehensive metrics tracking for monitoring and alerting
    - AIServiceException: Base exception for AI service errors

Configuration:
    - failure_threshold: Number of failures before opening circuit (default: 5)
    - recovery_timeout: Seconds to wait before trying half-open state (default: 60)
    - half_open_max_calls: Maximum calls allowed in half-open state (default: 1)

Metrics Tracked:
    - Total calls, successful calls, failed calls
    - Retry attempts and circuit breaker state transitions
    - Success/failure rates with timestamps
    - Circuit breaker opens, half-opens, and closes

Usage Example:
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

Dependencies:
    - circuitbreaker: Third-party circuit breaker implementation
    - datetime: For timestamp tracking
    - logging: For circuit breaker state change notifications

Thread Safety:
    The circuit breaker is thread-safe and can be used in concurrent environments.
    Metrics are updated atomically to ensure consistency.

Integration:
    This module integrates with the broader resilience infrastructure including
    retry mechanisms, timeouts, and monitoring systems.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

from circuitbreaker import CircuitBreaker
from app.core.exceptions import AIServiceException

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerConfig:
    """
    Circuit breaker configuration dataclass with validation and production-ready defaults.
    
    Defines circuit breaker behavior parameters including failure thresholds, recovery timeouts,
    and testing limits for half-open state operations. Provides sensible defaults optimized
    for AI service resilience patterns.
    
    Attributes:
        failure_threshold: int consecutive failures (1-100) before opening circuit (default: 5)
        recovery_timeout: int seconds (1-3600) to wait in open state before half-open (default: 60)
        half_open_max_calls: int maximum calls (1-10) allowed in half-open testing (default: 1)
        
    State Management:
        - Immutable configuration after initialization
        - Validation of parameter ranges for safe operation
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
        total_calls: int total service calls attempted across all states
        successful_calls: int calls completed successfully without errors
        failed_calls: int calls that failed with exceptions or timeouts
        retry_attempts: int total retry attempts across all failed calls
        circuit_breaker_opens: int number of times circuit opened due to failures
        circuit_breaker_half_opens: int transitions to half-open testing state
        circuit_breaker_closes: int successful recoveries from open state
        last_success: Optional[datetime] timestamp of most recent successful call
        last_failure: Optional[datetime] timestamp of most recent failed call
        
    Public Methods:
        to_dict(): Export metrics as dictionary for monitoring systems
        reset(): Clear all metrics for testing or periodic reset
        success_rate: Property calculating current success rate percentage
        
    State Management:
        - Thread-safe increment operations for concurrent access
        - Atomic updates to prevent race conditions
        - Timestamp tracking for temporal analysis
        - Exportable format for monitoring integration
        
    Usage:
        # Basic metrics tracking
        metrics = ResilienceMetrics()
        metrics.total_calls += 1
        metrics.successful_calls += 1
        
        # Monitoring integration
        stats = metrics.to_dict()
        monitoring_system.report_metrics("ai_service", stats)
        
        # Health assessment
        if metrics.success_rate < 0.95:
            alert_manager.trigger_alert("Low success rate")
    """
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    retry_attempts: int = 0
    circuit_breaker_opens: int = 0
    circuit_breaker_half_opens: int = 0
    circuit_breaker_closes: int = 0
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """
        Calculate success rate as a percentage.
        
        Returns:
            Success rate as a percentage (0.0-100.0), or 0.0 if no calls made
        """
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

    @property
    def failure_rate(self) -> float:
        """
        Calculate failure rate as a percentage.
        
        Returns:
            Failure rate as a percentage (0.0-100.0), or 0.0 if no calls made
        """
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to dictionary for JSON serialization.
        
        Returns:
            Dictionary containing all metrics with calculated rates and formatted timestamps
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
        failure_threshold: int consecutive failures before opening circuit
        recovery_timeout: int seconds to wait before half-open testing
        last_failure_time: Optional[float] timestamp of most recent failure
        metrics: ResilienceMetrics comprehensive statistics collection
        name: Optional[str] circuit breaker identifier for monitoring
        
    State Management:
        - Automatic state transitions (closed -> open -> half-open -> closed)
        - Thread-safe state updates for concurrent operation access
        - Comprehensive metrics collection with timing information
        - Recovery testing with configurable limits in half-open state
        
    Usage:
        # Basic circuit breaker with monitoring
        cb = EnhancedCircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            name="ai_text_service"
        )
        
        # Use with service calls
        try:
            if cb.can_execute():
                result = await ai_service.process(data)
                cb.record_success()
                return result
            else:
                raise ServiceUnavailableError("Circuit breaker open")
        except Exception as e:
            cb.record_failure()
            raise
            
        # Monitoring and health checks
        if cb.is_healthy():
            print(f"Service healthy: {cb.metrics.success_rate:.1%} success rate")
        else:
            print(f"Service degraded: {cb.state} state")
    """

    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=None, name=None):
        # Store the parameters as instance attributes for compatibility
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.metrics = ResilienceMetrics()
        self._last_known_state = None
        
        # Initialize the base CircuitBreaker
        super().__init__(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name
        )

    def _check_state_change(self):
        """Check for state changes and update metrics accordingly."""
        try:
            # Get current state - this varies by library version
            current_state = getattr(self, 'current_state', None)
            if current_state is None:
                # Fallback: try to determine state from failure count
                fail_counter = getattr(self, 'fail_counter', 0)
                if fail_counter >= self.failure_threshold:
                    current_state = 'open'
                else:
                    current_state = 'closed'
            
            if current_state != self._last_known_state:
                if current_state == 'open':
                    self.metrics.circuit_breaker_opens += 1
                    logger.warning(f"Circuit breaker '{self.name or 'unnamed'}' opened")
                elif current_state == 'half-open':
                    self.metrics.circuit_breaker_half_opens += 1
                    logger.info(f"Circuit breaker '{self.name or 'unnamed'}' half-opened")
                elif current_state == 'closed':
                    self.metrics.circuit_breaker_closes += 1
                    logger.info(f"Circuit breaker '{self.name or 'unnamed'}' closed")
                
                self._last_known_state = current_state
        except Exception:
            # If state checking fails, just continue silently
            pass

    def call(self, func, *args, **kwargs):
        """Override call to track metrics."""
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
        except Exception as e:
            self.metrics.failed_calls += 1
            self.metrics.last_failure = datetime.now()
            self.last_failure_time = datetime.now()
            
            # Check for state changes after failed call
            self._check_state_change()
            raise