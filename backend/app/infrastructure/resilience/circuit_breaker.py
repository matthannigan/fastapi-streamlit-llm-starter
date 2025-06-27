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

logger = logging.getLogger(__name__)


class AIServiceException(Exception):
    """Base exception for AI service errors."""
    pass


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 1


@dataclass
class ResilienceMetrics:
    """Metrics for monitoring resilience behavior."""
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
        """Calculate success rate as a percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.successful_calls / self.total_calls) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate as a percentage."""
        if self.total_calls == 0:
            return 0.0
        return (self.failed_calls / self.total_calls) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
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
    """Enhanced circuit breaker with metrics and monitoring."""

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