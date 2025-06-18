"""
Resilience Presets

This module provides predefined configurations (presets) for resilience patterns.
"""

import logging
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict

from .retry import RetryConfig
from .circuit_breaker import CircuitBreakerConfig

logger = logging.getLogger(__name__)


class ResilienceStrategy(str, Enum):
    """Available resilience strategies for different operation types."""
    AGGRESSIVE = "aggressive"      # Fast retries, low tolerance
    BALANCED = "balanced"         # Default strategy
    CONSERVATIVE = "conservative" # Slower retries, high tolerance
    CRITICAL = "critical"         # Maximum retries for critical operations


@dataclass
class ResilienceConfig:
    """Configuration for resilience policies."""
    strategy: ResilienceStrategy = ResilienceStrategy.BALANCED
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker_config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    enable_circuit_breaker: bool = True
    enable_retry: bool = True


def get_default_presets() -> Dict[ResilienceStrategy, ResilienceConfig]:
    """Returns a dictionary of default resilience strategy configurations."""
    return {
        ResilienceStrategy.AGGRESSIVE: ResilienceConfig(
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
        ),
        ResilienceStrategy.BALANCED: ResilienceConfig(
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
        ),
        ResilienceStrategy.CONSERVATIVE: ResilienceConfig(
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
        ),
        ResilienceStrategy.CRITICAL: ResilienceConfig(
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
    }


# Default presets for easy access
DEFAULT_PRESETS = get_default_presets()