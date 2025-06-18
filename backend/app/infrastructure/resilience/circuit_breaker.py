"""
Circuit Breaker Module

This file contains the core components for implementing the circuit breaker pattern,
including an enhanced circuit breaker with metrics tracking.
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

        # Initialize the base CircuitBreaker
        super().__init__(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=name
        )

    def call(self, func, *args, **kwargs):
        """Override call to track metrics."""
        self.metrics.total_calls += 1

        try:
            result = super().call(func, *args, **kwargs)
            self.metrics.successful_calls += 1
            self.metrics.last_success = datetime.now()
            return result
        except Exception as e:
            self.metrics.failed_calls += 1
            self.metrics.last_failure = datetime.now()
            self.last_failure_time = datetime.now()
            raise

    def _update_state(self, state):
        """Override state updates to track circuit breaker events."""
        old_state = getattr(self, '_state', None)
        super()._update_state(state)

        # Track state transitions
        if old_state != getattr(self, '_state', None):
            if getattr(self, '_state', None) == 'open':
                self.metrics.circuit_breaker_opens += 1
                logger.warning(f"Circuit breaker opened")
            elif getattr(self, '_state', None) == 'half-open':
                self.metrics.circuit_breaker_half_opens += 1
                logger.info(f"Circuit breaker half-opened")
            elif getattr(self, '_state', None) == 'closed':
                self.metrics.circuit_breaker_closes += 1
                logger.info(f"Circuit breaker closed")