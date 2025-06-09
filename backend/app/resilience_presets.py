"""
Resilience configuration presets for simplified AI service configuration.

This module provides a simplified approach to configuring resilience settings
by offering pre-defined presets instead of requiring manual configuration 
of 47+ environment variables.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class StrategyType(str, Enum):
    """Available resilience strategies."""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced" 
    CONSERVATIVE = "conservative"
    CRITICAL = "critical"


@dataclass
class ResiliencePreset:
    """
    Predefined resilience configuration preset.
    
    Encapsulates retry, circuit breaker, and strategy settings
    for different deployment scenarios.
    """
    name: str
    description: str
    retry_attempts: int
    circuit_breaker_threshold: int
    recovery_timeout: int
    default_strategy: StrategyType
    operation_overrides: Dict[str, StrategyType]
    environment_contexts: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization."""
        return asdict(self)
    
    def to_resilience_config(self) -> 'ResilienceConfig':
        """Convert preset to resilience configuration object."""
        from app.services.resilience import ResilienceConfig, RetryConfig, CircuitBreakerConfig
        
        return ResilienceConfig(
            strategy=self.default_strategy,
            retry_config=RetryConfig(
                max_attempts=self.retry_attempts,
                max_delay_seconds=min(self.retry_attempts * 20, 120),
                exponential_multiplier=1.0 if self.default_strategy == StrategyType.BALANCED else 
                                     0.5 if self.default_strategy == StrategyType.AGGRESSIVE else 1.5,
                exponential_min=1.0 if self.default_strategy == StrategyType.AGGRESSIVE else 2.0,
                exponential_max=5.0 if self.default_strategy == StrategyType.AGGRESSIVE else 
                              10.0 if self.default_strategy == StrategyType.BALANCED else 30.0
            ),
            circuit_breaker_config=CircuitBreakerConfig(
                failure_threshold=self.circuit_breaker_threshold,
                recovery_timeout=self.recovery_timeout
            )
        )


# Preset definitions based on PRD specifications
PRESETS = {
    "simple": ResiliencePreset(
        name="Simple",
        description="Balanced configuration suitable for most use cases",
        retry_attempts=3,
        circuit_breaker_threshold=5,
        recovery_timeout=60,
        default_strategy=StrategyType.BALANCED,
        operation_overrides={},
        environment_contexts=["development", "testing", "staging", "production"]
    ),
    
    "development": ResiliencePreset(
        name="Development",
        description="Fast-fail configuration optimized for development speed",
        retry_attempts=2,
        circuit_breaker_threshold=3,
        recovery_timeout=30,
        default_strategy=StrategyType.AGGRESSIVE,
        operation_overrides={
            "sentiment": StrategyType.AGGRESSIVE,  # Fast feedback for UI development
            "qa": StrategyType.BALANCED           # Reasonable reliability for testing
        },
        environment_contexts=["development", "testing"]
    ),
    
    "production": ResiliencePreset(
        name="Production",
        description="High-reliability configuration for production workloads",
        retry_attempts=5,
        circuit_breaker_threshold=10,
        recovery_timeout=120,
        default_strategy=StrategyType.CONSERVATIVE,
        operation_overrides={
            "qa": StrategyType.CRITICAL,          # Maximum reliability for user-facing Q&A
            "sentiment": StrategyType.AGGRESSIVE, # Can afford faster feedback for sentiment
            "summarize": StrategyType.CONSERVATIVE, # Important for content processing
            "key_points": StrategyType.BALANCED,   # Balanced approach for key points
            "questions": StrategyType.BALANCED     # Balanced approach for questions
        },
        environment_contexts=["production", "staging"]
    )
}


class PresetManager:
    """
    Manager for resilience presets with validation and recommendation capabilities.
    """
    
    def __init__(self):
        """Initialize preset manager with default presets."""
        self.presets = PRESETS.copy()
        logger.info(f"Initialized PresetManager with {len(self.presets)} presets")
    
    def get_preset(self, name: str) -> ResiliencePreset:
        """
        Get preset by name with validation.
        
        Args:
            name: Preset name (simple, development, production)
            
        Returns:
            ResiliencePreset object
            
        Raises:
            ValueError: If preset name is not found
        """
        if name not in self.presets:
            available = list(self.presets.keys())
            raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
        return self.presets[name]
    
    def list_presets(self) -> List[str]:
        """Get list of available preset names."""
        return list(self.presets.keys())
    
    def get_preset_details(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a preset."""
        preset = self.get_preset(name)
        return {
            "name": preset.name,
            "description": preset.description,
            "configuration": {
                "retry_attempts": preset.retry_attempts,
                "circuit_breaker_threshold": preset.circuit_breaker_threshold,
                "recovery_timeout": preset.recovery_timeout,
                "default_strategy": preset.default_strategy.value,
                "operation_overrides": {k: v.value for k, v in preset.operation_overrides.items()}
            },
            "environment_contexts": preset.environment_contexts
        }
    
    def validate_preset(self, preset: ResiliencePreset) -> bool:
        """
        Validate preset configuration values.
        
        Args:
            preset: Preset to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Validate retry attempts
        if preset.retry_attempts < 1 or preset.retry_attempts > 10:
            logger.error(f"Invalid retry_attempts: {preset.retry_attempts} (must be 1-10)")
            return False
        
        # Validate circuit breaker threshold
        if preset.circuit_breaker_threshold < 1 or preset.circuit_breaker_threshold > 20:
            logger.error(f"Invalid circuit_breaker_threshold: {preset.circuit_breaker_threshold} (must be 1-20)")
            return False
        
        # Validate recovery timeout
        if preset.recovery_timeout < 10 or preset.recovery_timeout > 300:
            logger.error(f"Invalid recovery_timeout: {preset.recovery_timeout} (must be 10-300)")
            return False
        
        # Validate operation overrides contain valid strategies
        for operation, strategy in preset.operation_overrides.items():
            if not isinstance(strategy, StrategyType):
                logger.error(f"Invalid strategy for operation {operation}: {strategy}")
                return False
        
        return True
    
    def recommend_preset(self, environment: str) -> str:
        """
        Recommend appropriate preset for given environment.
        
        Args:
            environment: Environment name (dev, test, staging, prod, etc.)
            
        Returns:
            Recommended preset name
        """
        env_lower = environment.lower()
        
        # Environment-to-preset mapping
        recommendations = {
            "development": "development",
            "dev": "development",
            "testing": "development", 
            "test": "development",
            "staging": "production",
            "stage": "production",
            "production": "production",
            "prod": "production"
        }
        
        recommended = recommendations.get(env_lower, "simple")
        logger.info(f"Recommended preset '{recommended}' for environment '{environment}'")
        return recommended
    
    def get_all_presets_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all available presets."""
        summary = {}
        for name in self.presets.keys():
            summary[name] = self.get_preset_details(name)
        return summary


# Global preset manager instance
preset_manager = PresetManager()