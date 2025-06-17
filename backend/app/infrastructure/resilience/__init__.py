"""
Resilience Infrastructure Service

Re-exports the primary resilience service, strategy enums, presets,
and individual decorators for ease of use.
"""

# Bridge resilience logic from its old location in 'services'.
from ...services.resilience import (
    ai_resilience,
    ResilienceStrategy,
    ServiceUnavailableError,
    TransientAIError,
    PermanentAIError,
    with_operation_resilience,
    with_aggressive_resilience,
    with_balanced_resilience,
    with_conservative_resilience,
    with_critical_resilience
)

# Bridge resilience presets from their old location.
from ...resilience_presets import preset_manager, PRESETS

__all__ = [
    "ai_resilience",
    "ResilienceStrategy",
    "ServiceUnavailableError",
    "TransientAIError",
    "PermanentAIError",
    "with_operation_resilience",
    "with_aggressive_resilience",
    "with_balanced_resilience",
    "with_conservative_resilience",
    "with_critical_resilience",
    "preset_manager",
    "PRESETS"
]
