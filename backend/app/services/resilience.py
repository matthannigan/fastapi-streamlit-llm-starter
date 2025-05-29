"""
Enhanced resilience service for AI operations using tenacity and circuitbreaker.

This module provides:
- Configurable retry strategies with exponential backoff
- Circuit breaker pattern for AI service protection
- Operation-specific resilience policies
- Comprehensive monitoring and metrics
- Integration with existing caching and logging systems
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field

import httpx
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
from circuitbreaker import CircuitBreaker, CircuitBreakerMonitor

from app.config import settings

logger = logging.getLogger(__name__)


class ResilienceStrategy(str, Enum):
    """Available resilience strategies for different operation types."""
    AGGRESSIVE = "aggressive"      # Fast retries, low tolerance
    BALANCED = "balanced"         # Default strategy
    CONSERVATIVE = "conservative" # Slower retries, high tolerance
    CRITICAL = "critical"         # Maximum retries for critical operations


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    max_delay_seconds: int = 60
    exponential_multiplier: float = 1.0
    exponential_min: float = 2.0
    exponential_max: float = 10.0
    jitter: bool = True
    jitter_max: float = 2.0


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    half_open_max_calls: int = 1


@dataclass
class ResilienceConfig:
    """Configuration for resilience policies."""
    strategy: ResilienceStrategy = ResilienceStrategy.BALANCED
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker_config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    enable_circuit_breaker: bool = True
    enable_retry: bool = True


class AIServiceException(Exception):
    """Base exception for AI service errors."""
    pass


class TransientAIError(AIServiceException):
    """Transient AI service error that should be retried."""
    pass


class PermanentAIError(AIServiceException):
    """Permanent AI service error that should not be retried."""
    pass


class RateLimitError(TransientAIError):
    """Rate limit exceeded error."""
    pass


class ServiceUnavailableError(TransientAIError):
    """AI service temporarily unavailable."""
    pass


def classify_exception(exc: Exception) -> bool:
    """
    Classify whether an exception should trigger retries.
    
    Returns True if the exception is transient and should be retried.
    """
    # Network and connection errors (should retry)
    if isinstance(exc, (
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError,
        TransientAIError,
        RateLimitError,
        ServiceUnavailableError
    )):
        return True
    
    # HTTP errors that should be retried
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        # Retry on server errors and rate limits
        if status_code in (429, 500, 502, 503, 504):
            return True
        # Don't retry on client errors
        if 400 <= status_code < 500:
            return False
    
    # Permanent errors (should not retry)
    if isinstance(exc, (
        PermanentAIError,
        ValueError,
        TypeError,
        AttributeError
    )):
        return False
    
    # Default: retry on unknown exceptions (conservative approach)
    return True


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
            "last_success": self.last_success.isoformat() if self.last_success else None
        }


class EnhancedCircuitBreaker(CircuitBreaker):
    """Enhanced circuit breaker with metrics and monitoring."""
    
    def __init__(self, *args, **kwargs):
        self.metrics = ResilienceMetrics()
        super().__init__(*args, **kwargs)
    
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
            raise
    
    def _update_state(self, state):
        """Override state updates to track circuit breaker events."""
        old_state = self._state
        super()._update_state(state)
        
        # Track state transitions
        if old_state != self._state:
            if self._state == 'open':
                self.metrics.circuit_breaker_opens += 1
                logger.warning(f"Circuit breaker opened for {self._name}")
            elif self._state == 'half-open':
                self.metrics.circuit_breaker_half_opens += 1
                logger.info(f"Circuit breaker half-opened for {self._name}")
            elif self._state == 'closed':
                self.metrics.circuit_breaker_closes += 1
                logger.info(f"Circuit breaker closed for {self._name}")


class AIServiceResilience:
    """
    Comprehensive resilience service for AI operations.
    
    Provides retry logic, circuit breaker pattern, and monitoring
    for AI service calls with configurable strategies.
    """
    
    def __init__(self):
        """Initialize the resilience service with default configurations."""
        self.metrics: Dict[str, ResilienceMetrics] = {}
        self.circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}
        self.configs: Dict[str, ResilienceConfig] = {}
        
        # Load default configurations
        self._load_default_configs()
        
        logger.info("AI Service Resilience initialized")
    
    def _load_default_configs(self):
        """Load default resilience configurations for different strategies."""
        
        # Aggressive strategy: Fast retries, low tolerance
        self.configs[ResilienceStrategy.AGGRESSIVE] = ResilienceConfig(
            strategy=ResilienceStrategy.AGGRESSIVE,
            retry_config=RetryConfig(
                max_attempts=2,
                max_delay_seconds=10,
                exponential_multiplier=0.5,
                exponential_min=1.0,
                exponential_max=5.0
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30
            )
        )
        
        # Balanced strategy: Default settings
        self.configs[ResilienceStrategy.BALANCED] = ResilienceConfig(
            strategy=ResilienceStrategy.BALANCED,
            retry_config=RetryConfig(
                max_attempts=3,
                max_delay_seconds=30,
                exponential_multiplier=1.0,
                exponential_min=2.0,
                exponential_max=10.0
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60
            )
        )
        
        # Conservative strategy: Slower retries, high tolerance
        self.configs[ResilienceStrategy.CONSERVATIVE] = ResilienceConfig(
            strategy=ResilienceStrategy.CONSERVATIVE,
            retry_config=RetryConfig(
                max_attempts=5,
                max_delay_seconds=120,
                exponential_multiplier=2.0,
                exponential_min=4.0,
                exponential_max=30.0
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=8,
                recovery_timeout=120
            )
        )
        
        # Critical strategy: Maximum retries
        self.configs[ResilienceStrategy.CRITICAL] = ResilienceConfig(
            strategy=ResilienceStrategy.CRITICAL,
            retry_config=RetryConfig(
                max_attempts=7,
                max_delay_seconds=300,
                exponential_multiplier=1.5,
                exponential_min=3.0,
                exponential_max=60.0,
                jitter_max=5.0
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=10,
                recovery_timeout=300
            )
        )
    
    def get_or_create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> EnhancedCircuitBreaker:
        """Get or create a circuit breaker for the given operation."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = EnhancedCircuitBreaker(
                failure_threshold=config.failure_threshold,
                recovery_timeout=config.recovery_timeout,
                expected_exception=classify_exception,
                name=name
            )
            logger.info(f"Created circuit breaker for operation: {name}")
        
        return self.circuit_breakers[name]
    
    def get_metrics(self, operation_name: str) -> ResilienceMetrics:
        """Get metrics for a specific operation."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = ResilienceMetrics()
        return self.metrics[operation_name]
    
    def custom_before_sleep(self, operation_name: str):
        """Custom before_sleep callback that tracks retry metrics."""
        def callback(retry_state):
            metrics = self.get_metrics(operation_name)
            metrics.retry_attempts += 1
            
            logger.warning(
                f"Retrying {operation_name} (attempt {retry_state.attempt_number}) "
                f"after {retry_state.outcome.exception()} - "
                f"waiting {retry_state.next_action.sleep} seconds"
            )
        return callback
    
    def with_resilience(
        self,
        operation_name: str,
        strategy: Union[ResilienceStrategy, str] = ResilienceStrategy.BALANCED,
        custom_config: Optional[ResilienceConfig] = None,
        fallback: Optional[Callable] = None
    ):
        """
        Decorator that adds comprehensive resilience to AI calls.
        
        Args:
            operation_name: Name of the operation for monitoring
            strategy: Resilience strategy to use
            custom_config: Custom configuration (overrides strategy)
            fallback: Function to call when circuit breaker is open
        """
        def decorator(func: Callable) -> Callable:
            # Get configuration
            if custom_config:
                config = custom_config
            else:
                if isinstance(strategy, str):
                    strategy_enum = ResilienceStrategy(strategy)
                else:
                    strategy_enum = strategy
                config = self.configs[strategy_enum]
            
            # Get or create circuit breaker
            circuit_breaker = None
            if config.enable_circuit_breaker:
                circuit_breaker = self.get_or_create_circuit_breaker(
                    operation_name, 
                    config.circuit_breaker_config
                )
            
            # Build retry decorator
            retry_decorator = None
            if config.enable_retry:
                retry_config = config.retry_config
                
                # Build wait strategy
                wait_strategy = wait_exponential(
                    multiplier=retry_config.exponential_multiplier,
                    min=retry_config.exponential_min,
                    max=retry_config.exponential_max
                )
                
                # Add jitter if enabled
                if retry_config.jitter:
                    wait_strategy = wait_strategy + wait_random(0, retry_config.jitter_max)
                
                # Build stop strategy
                stop_strategy = (
                    stop_after_attempt(retry_config.max_attempts) |
                    stop_after_delay(retry_config.max_delay_seconds)
                )
                
                retry_decorator = retry(
                    stop=stop_strategy,
                    wait=wait_strategy,
                    retry=classify_exception,
                    before_sleep=self.custom_before_sleep(operation_name),
                    reraise=True
                )
            
            async def wrapper(*args, **kwargs):
                metrics = self.get_metrics(operation_name)
                start_time = time.time()
                
                try:
                    logger.debug(f"Starting {operation_name} with strategy {config.strategy}")
                    
                    # Apply circuit breaker if enabled
                    if circuit_breaker:
                        # Check if circuit breaker is open
                        if circuit_breaker.current_state == 'open':
                            if fallback:
                                logger.warning(f"Circuit breaker open for {operation_name}, using fallback")
                                return await fallback(*args, **kwargs)
                            else:
                                raise ServiceUnavailableError(
                                    f"Service {operation_name} is currently unavailable (circuit breaker open)"
                                )
                        
                        # Wrap function with circuit breaker
                        if config.enable_retry and retry_decorator:
                            decorated_func = circuit_breaker(retry_decorator(func))
                        else:
                            decorated_func = circuit_breaker(func)
                    else:
                        # Just use retry if circuit breaker is disabled
                        if config.enable_retry and retry_decorator:
                            decorated_func = retry_decorator(func)
                        else:
                            decorated_func = func
                    
                    # Execute the decorated function
                    result = await decorated_func(*args, **kwargs)
                    
                    # Update metrics on success
                    metrics.successful_calls += 1
                    metrics.last_success = datetime.now()
                    
                    duration = time.time() - start_time
                    logger.debug(f"Successfully completed {operation_name} in {duration:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    # Update metrics on failure
                    metrics.failed_calls += 1
                    metrics.last_failure = datetime.now()
                    
                    duration = time.time() - start_time
                    logger.error(f"Failed {operation_name} after {duration:.2f}s: {str(e)}")
                    
                    # Re-raise the exception
                    raise
                finally:
                    metrics.total_calls += 1
            
            return wrapper
        return decorator
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all operations."""
        all_metrics = {}
        
        # Operation metrics
        for operation_name, metrics in self.metrics.items():
            all_metrics[operation_name] = metrics.to_dict()
        
        # Circuit breaker states
        circuit_breaker_states = {}
        for name, cb in self.circuit_breakers.items():
            circuit_breaker_states[name] = {
                "state": cb.current_state,
                "failure_count": cb.failure_count,
                "last_failure_time": cb.last_failure_time,
                "metrics": cb.metrics.to_dict() if hasattr(cb, 'metrics') else {}
            }
        
        return {
            "operations": all_metrics,
            "circuit_breakers": circuit_breaker_states,
            "summary": {
                "total_operations": len(self.metrics),
                "total_circuit_breakers": len(self.circuit_breakers),
                "open_circuit_breakers": len([
                    cb for cb in self.circuit_breakers.values() 
                    if cb.current_state == 'open'
                ])
            }
        }
    
    def reset_metrics(self, operation_name: Optional[str] = None):
        """Reset metrics for a specific operation or all operations."""
        if operation_name:
            if operation_name in self.metrics:
                self.metrics[operation_name] = ResilienceMetrics()
                logger.info(f"Reset metrics for operation: {operation_name}")
        else:
            self.metrics.clear()
            logger.info("Reset all operation metrics")
    
    def is_healthy(self) -> bool:
        """Check if the resilience service is healthy."""
        open_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if cb.current_state == 'open'
        ]
        
        if open_breakers:
            logger.warning(f"Unhealthy: Circuit breakers open for: {open_breakers}")
            return False
        
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get detailed health status."""
        open_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if cb.current_state == 'open'
        ]
        
        half_open_breakers = [
            name for name, cb in self.circuit_breakers.items()
            if cb.current_state == 'half-open'
        ]
        
        return {
            "healthy": len(open_breakers) == 0,
            "open_circuit_breakers": open_breakers,
            "half_open_circuit_breakers": half_open_breakers,
            "total_circuit_breakers": len(self.circuit_breakers),
            "operations_monitored": list(self.metrics.keys())
        }


# Global resilience instance
ai_resilience = AIServiceResilience()

# Convenience decorators for common strategies
def with_aggressive_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Decorator for aggressive resilience strategy."""
    return ai_resilience.with_resilience(
        operation_name, 
        ResilienceStrategy.AGGRESSIVE, 
        fallback=fallback
    )

def with_balanced_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Decorator for balanced resilience strategy."""
    return ai_resilience.with_resilience(
        operation_name, 
        ResilienceStrategy.BALANCED, 
        fallback=fallback
    )

def with_conservative_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Decorator for conservative resilience strategy."""
    return ai_resilience.with_resilience(
        operation_name, 
        ResilienceStrategy.CONSERVATIVE, 
        fallback=fallback
    )

def with_critical_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Decorator for critical resilience strategy."""
    return ai_resilience.with_resilience(
        operation_name, 
        ResilienceStrategy.CRITICAL, 
        fallback=fallback
    )
