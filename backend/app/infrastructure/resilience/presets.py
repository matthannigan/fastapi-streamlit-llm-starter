"""
Resilience Configuration Presets and Strategy Management

This module provides a comprehensive system for managing resilience configurations
in AI service applications. It includes:

**Core Components:**
- ResilienceStrategy: Enum defining available resilience strategies (aggressive, balanced, conservative, critical)
- ResilienceConfig: Main configuration class combining retry, circuit breaker, and strategy settings
- ResiliencePreset: Predefined configuration templates for different deployment scenarios
- PresetManager: Advanced manager with validation, environment detection, and recommendation capabilities

**Preset System:**
- Pre-defined presets for common scenarios (simple, development, production)
- Environment-aware preset recommendations with confidence scoring
- Automatic environment detection from system variables and indicators
- Pattern-based environment classification for complex deployment names

**Strategy Configurations:**
- Default strategy presets with optimized retry and circuit breaker parameters
- Operation-specific strategy overrides for fine-grained control
- Validation system for configuration integrity

**Key Features:**
- Simplified configuration through presets instead of manual environment variables
- Intelligent environment detection and preset recommendation
- Comprehensive validation with fallback to basic validation
- Pattern matching for complex environment naming schemes
- Extensible preset system for custom deployment scenarios

**Usage:**
- Use preset_manager.recommend_preset() for automatic environment-based selection
- Access predefined presets via PRESETS dictionary or preset_manager.get_preset()
- Convert presets to full ResilienceConfig objects via to_resilience_config()
- Leverage DEFAULT_PRESETS for direct strategy-based configuration access

This module serves as the central configuration hub for all resilience-related
settings across the application, providing both simplified preset-based configuration
and advanced customization capabilities.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any, NamedTuple
from enum import Enum
import json
import logging
import os
import re

from .retry import RetryConfig
from .circuit_breaker import CircuitBreakerConfig

logger = logging.getLogger(__name__)


class EnvironmentRecommendation(NamedTuple):
    """Environment-based preset recommendation with confidence and reasoning."""
    preset_name: str
    confidence: float  # 0.0 to 1.0
    reasoning: str
    environment_detected: str


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
    default_strategy: ResilienceStrategy
    operation_overrides: Dict[str, ResilienceStrategy]
    environment_contexts: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert preset to dictionary for serialization."""
        return asdict(self)
    
    def to_resilience_config(self) -> ResilienceConfig:
        """Convert preset to resilience configuration object."""
        return ResilienceConfig(
            strategy=self.default_strategy,
            retry_config=RetryConfig(
                max_attempts=self.retry_attempts,
                max_delay_seconds=min(self.retry_attempts * 20, 120),
                exponential_multiplier=1.0 if self.default_strategy == ResilienceStrategy.BALANCED else 
                                     0.5 if self.default_strategy == ResilienceStrategy.AGGRESSIVE else 1.5,
                exponential_min=1.0 if self.default_strategy == ResilienceStrategy.AGGRESSIVE else 2.0,
                exponential_max=5.0 if self.default_strategy == ResilienceStrategy.AGGRESSIVE else 
                              10.0 if self.default_strategy == ResilienceStrategy.BALANCED else 30.0
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
        default_strategy=ResilienceStrategy.BALANCED,
        operation_overrides={},
        environment_contexts=["development", "testing", "staging", "production"]
    ),
    
    "development": ResiliencePreset(
        name="Development",
        description="Fast-fail configuration optimized for development speed",
        retry_attempts=2,
        circuit_breaker_threshold=3,
        recovery_timeout=30,
        default_strategy=ResilienceStrategy.AGGRESSIVE,
        operation_overrides={
            "sentiment": ResilienceStrategy.AGGRESSIVE,  # Fast feedback for UI development
            "qa": ResilienceStrategy.BALANCED           # Reasonable reliability for testing
        },
        environment_contexts=["development", "testing"]
    ),
    
    "production": ResiliencePreset(
        name="Production",
        description="High-reliability configuration for production workloads",
        retry_attempts=5,
        circuit_breaker_threshold=10,
        recovery_timeout=120,
        default_strategy=ResilienceStrategy.CONSERVATIVE,
        operation_overrides={
            "qa": ResilienceStrategy.CRITICAL,          # Maximum reliability for user-facing Q&A
            "sentiment": ResilienceStrategy.AGGRESSIVE, # Can afford faster feedback for sentiment
            "summarize": ResilienceStrategy.CONSERVATIVE, # Important for content processing
            "key_points": ResilienceStrategy.BALANCED,   # Balanced approach for key points
            "questions": ResilienceStrategy.BALANCED     # Balanced approach for questions
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
        try:
            from app.validation_schemas import config_validator
            
            # Convert preset to dict for validation
            preset_dict = preset.to_dict()
            
            # Use JSON schema validation if available
            validation_result = config_validator.validate_preset(preset_dict)
            
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    logger.error(f"Preset validation error: {error}")
                return False
            
            # Log any warnings
            for warning in validation_result.warnings:
                logger.warning(f"Preset validation warning: {warning}")
            
            return True
            
        except ImportError:
            # Fallback to basic validation if validation_schemas not available
            return self._basic_validate_preset(preset)
    
    def _basic_validate_preset(self, preset: ResiliencePreset) -> bool:
        """Basic preset validation without JSON schema."""
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
            if not isinstance(strategy, ResilienceStrategy):
                logger.error(f"Invalid strategy for operation {operation}: {strategy}")
                return False
        
        return True
    
    def recommend_preset(self, environment: Optional[str] = None) -> str:
        """
        Recommend appropriate preset for given environment.
        
        Args:
            environment: Environment name (dev, test, staging, prod, etc.)
            If None, will auto-detect from environment variables
            
        Returns:
            Recommended preset name
        """
        recommendation = self.recommend_preset_with_details(environment)
        return recommendation.preset_name
    
    def recommend_preset_with_details(self, environment: Optional[str] = None) -> EnvironmentRecommendation:
        """
        Get detailed environment-aware preset recommendation.
        
        Args:
            environment: Environment name or None for auto-detection
            
        Returns:
            EnvironmentRecommendation with preset, confidence, and reasoning
        """
        if environment is None:
            return self._auto_detect_environment()
        
        env_lower = environment.lower().strip()
        
        # High-confidence exact matches
        exact_matches = {
            "development": ("development", 0.95, "Exact match for development environment"),
            "dev": ("development", 0.90, "Standard abbreviation for development"),
            "testing": ("development", 0.85, "Testing typically uses development-like settings"),
            "test": ("development", 0.85, "Test environment should fail fast"),
            "staging": ("production", 0.90, "Staging should mirror production settings"),
            "stage": ("production", 0.85, "Stage environment abbreviation"),
            "production": ("production", 0.95, "Exact match for production environment"),
            "prod": ("production", 0.90, "Standard abbreviation for production"),
            "live": ("production", 0.85, "Live environment implies production"),
        }
        
        if env_lower in exact_matches:
            preset, confidence, reasoning = exact_matches[env_lower]
            return EnvironmentRecommendation(
                preset_name=preset,
                confidence=confidence,
                reasoning=reasoning,
                environment_detected=environment
            )
        
        # Pattern-based matching for complex environment names
        preset, confidence, reasoning = self._pattern_match_environment(env_lower)
        
        return EnvironmentRecommendation(
            preset_name=preset,
            confidence=confidence,
            reasoning=reasoning,
            environment_detected=environment
        )
    
    def _auto_detect_environment(self) -> EnvironmentRecommendation:
        """
        Auto-detect environment from environment variables and system context.
        
        Returns:
            EnvironmentRecommendation based on detected environment
        """
        # Check common environment variables
        env_vars_to_check = [
            'ENVIRONMENT',
            'ENV',
            'DEPLOYMENT_ENV',
            'NODE_ENV',
            'RAILS_ENV',
            'DJANGO_SETTINGS_MODULE',
            'FLASK_ENV',
            'APP_ENV'
        ]
        
        detected_env = None
        for var in env_vars_to_check:
            value = os.getenv(var)
            if value:
                detected_env = value
                break
        
        if detected_env:
            logger.info(f"Auto-detected environment from {var}={detected_env}")
            recommendation = self.recommend_preset_with_details(detected_env)
            # Modify to indicate auto-detection
            return EnvironmentRecommendation(
                preset_name=recommendation.preset_name,
                confidence=recommendation.confidence,
                reasoning=recommendation.reasoning,
                environment_detected=f"{detected_env} (auto-detected)"
            )
        
        # Check for development indicators
        host = os.getenv('HOST', '') or ''
        dev_indicators = [
            os.getenv('DEBUG') == 'true',
            os.getenv('DEBUG') == '1',
            os.path.exists('.env'),
            os.path.exists('docker-compose.dev.yml'),
            os.path.exists('.git'),  # Local development
            'localhost' in host,
            '127.0.0.1' in host
        ]
        
        if any(dev_indicators):
            return EnvironmentRecommendation(
                preset_name="development",
                confidence=0.75,
                reasoning="Development indicators detected (DEBUG=true, .env file, localhost, etc.)",
                environment_detected="development (auto-detected)"
            )
        
        # Check for production indicators
        database_url = os.getenv('DATABASE_URL', '') or ''
        prod_indicators = [
            os.getenv('PROD') == 'true',
            os.getenv('PRODUCTION') == 'true',
            os.getenv('DEBUG') == 'false',
            os.getenv('DEBUG') == '0',
            'prod' in host.lower(),
            'production' in database_url.lower()
        ]
        
        if any(prod_indicators):
            return EnvironmentRecommendation(
                preset_name="production",
                confidence=0.70,
                reasoning="Production indicators detected (PROD=true, DEBUG=false, production URLs, etc.)",
                environment_detected="production (auto-detected)"
            )
        
        # Default fallback
        return EnvironmentRecommendation(
            preset_name="simple",
            confidence=0.50,
            reasoning="No clear environment indicators found, using simple preset as safe default",
            environment_detected="unknown (auto-detected)"
        )
    
    def _pattern_match_environment(self, env_str: str) -> tuple[str, float, str]:
        """
        Use pattern matching to classify environment strings.
        
        Args:
            env_str: Environment string to classify
            
        Returns:
            Tuple of (preset_name, confidence, reasoning)
        """
        # Staging patterns (check first to avoid conflicts with other patterns)
        staging_patterns = [
            r'.*stag.*',
            r'.*pre-?prod.*',
            r'.*preprod.*',
            r'.*uat.*',
            r'.*integration.*'
        ]
        
        for pattern in staging_patterns:
            if re.match(pattern, env_str, re.IGNORECASE):
                return ("production", 0.70, f"Environment name '{env_str}' matches staging pattern, using production preset")
        
        # Development patterns
        dev_patterns = [
            r'.*dev.*',
            r'.*local.*',
            r'.*test.*',
            r'.*sandbox.*',
            r'.*demo.*'
        ]
        
        for pattern in dev_patterns:
            if re.match(pattern, env_str, re.IGNORECASE):
                return ("development", 0.75, f"Environment name '{env_str}' matches development pattern")
        
        # Production patterns
        prod_patterns = [
            r'.*prod.*',
            r'.*live.*',
            r'.*release.*',
            r'.*stable.*',
            r'.*main.*',
            r'.*master.*'
        ]
        
        for pattern in prod_patterns:
            if re.match(pattern, env_str, re.IGNORECASE):
                return ("production", 0.75, f"Environment name '{env_str}' matches production pattern")
        
        # Unknown pattern
        return ("simple", 0.40, f"Unknown environment pattern '{env_str}', defaulting to simple preset")
    
    def get_all_presets_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all available presets."""
        summary = {}
        for name in self.presets.keys():
            summary[name] = self.get_preset_details(name)
        return summary


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

# Global preset manager instance
preset_manager = PresetManager()