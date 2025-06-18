"""
Resilience Infrastructure Service

Re-exports the resilience components including circuit breaker, retry logic,
presets, and the main orchestrator for ease of use.
"""

# Core components
from .circuit_breaker import (
    AIServiceException,
    CircuitBreakerConfig,
    ResilienceMetrics,
    EnhancedCircuitBreaker
)

from .retry import (
    RetryConfig,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    classify_exception,
    should_retry_on_exception
)

from .presets import (
    ResilienceStrategy,
    ResilienceConfig,
    get_default_presets,
    DEFAULT_PRESETS
)

from .orchestrator import (
    AIServiceResilience,
    ai_resilience,
    with_operation_resilience,
    with_aggressive_resilience,
    with_balanced_resilience,
    with_conservative_resilience,
    with_critical_resilience
)

# Bridge resilience presets from their old location for backward compatibility
try:
    from ...resilience_presets import preset_manager, PRESETS
except ImportError:
    # If old resilience_presets module doesn't exist, create placeholder
    preset_manager = None
    PRESETS = DEFAULT_PRESETS

__all__ = [
    # Core exceptions
    "AIServiceException",
    "TransientAIError", 
    "PermanentAIError",
    "RateLimitError",
    "ServiceUnavailableError",
    
    # Configuration classes
    "RetryConfig",
    "CircuitBreakerConfig", 
    "ResilienceConfig",
    "ResilienceStrategy",
    
    # Core components
    "EnhancedCircuitBreaker",
    "ResilienceMetrics",
    "AIServiceResilience",
    
    # Utility functions
    "classify_exception",
    "should_retry_on_exception",
    "get_default_presets",
    
    # Presets and defaults
    "DEFAULT_PRESETS",
    
    # Global instance and decorators
    "ai_resilience",
    "with_operation_resilience",
    "with_aggressive_resilience",
    "with_balanced_resilience", 
    "with_conservative_resilience",
    "with_critical_resilience",
    
    # Backward compatibility
    "preset_manager",
    "PRESETS"
]
