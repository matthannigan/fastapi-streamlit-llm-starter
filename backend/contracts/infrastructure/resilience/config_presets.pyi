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
from app.infrastructure.resilience.retry import RetryConfig
from app.infrastructure.resilience.circuit_breaker import CircuitBreakerConfig

PRESETS = {'simple': ResiliencePreset(name='Simple', description='Balanced configuration suitable for most use cases', retry_attempts=3, circuit_breaker_threshold=5, recovery_timeout=60, default_strategy=ResilienceStrategy.BALANCED, operation_overrides={}, environment_contexts=['development', 'testing', 'staging', 'production']), 'development': ResiliencePreset(name='Development', description='Fast-fail configuration optimized for development speed', retry_attempts=2, circuit_breaker_threshold=3, recovery_timeout=30, default_strategy=ResilienceStrategy.AGGRESSIVE, operation_overrides={'sentiment': ResilienceStrategy.AGGRESSIVE, 'qa': ResilienceStrategy.BALANCED}, environment_contexts=['development', 'testing']), 'production': ResiliencePreset(name='Production', description='High-reliability configuration for production workloads', retry_attempts=5, circuit_breaker_threshold=10, recovery_timeout=120, default_strategy=ResilienceStrategy.CONSERVATIVE, operation_overrides={'qa': ResilienceStrategy.CRITICAL, 'sentiment': ResilienceStrategy.AGGRESSIVE, 'summarize': ResilienceStrategy.CONSERVATIVE, 'key_points': ResilienceStrategy.BALANCED, 'questions': ResilienceStrategy.BALANCED}, environment_contexts=['production', 'staging'])}

DEFAULT_PRESETS = get_default_presets()


class EnvironmentRecommendation(NamedTuple):
    """
    Environment-based preset recommendation with confidence and reasoning.
    """

    ...


class ResilienceStrategy(str, Enum):
    """
    Resilience strategy enumeration defining optimized patterns for different operation criticality levels.
    
    Provides predefined strategy configurations that automatically optimize retry attempts,
    circuit breaker thresholds, and timeout values based on operation requirements and
    acceptable latency/reliability trade-offs.
    
    Values:
        AGGRESSIVE: Fast retries (3 attempts), low circuit breaker thresholds (3 failures)
                   for user-facing operations requiring quick response
        BALANCED: Moderate retries (3 attempts), balanced thresholds (5 failures)
                 for standard API operations and background processing
        CONSERVATIVE: Minimal retries (2 attempts), high thresholds (10 failures)
                     for resource-intensive operations and batch processing
        CRITICAL: Maximum retries (5 attempts), highest thresholds (15 failures)
                 for mission-critical operations requiring highest reliability
                 
    Behavior:
        - String enum supporting serialization and direct comparison
        - Each strategy maps to specific retry and circuit breaker configurations
        - Strategies balance latency, reliability, and resource consumption
        - Enables consistent resilience patterns across different services
        
    Examples:
        >>> strategy = ResilienceStrategy.BALANCED
        >>> config = DEFAULT_PRESETS[strategy]
        >>> print(f"Max attempts: {config.retry_config.max_attempts}")
        
        >>> # Strategy selection based on operation criticality
        >>> if operation_type == "user_facing":
        ...     strategy = ResilienceStrategy.AGGRESSIVE
        >>> elif operation_type == "critical":
        ...     strategy = ResilienceStrategy.CRITICAL
        >>> else:
        ...     strategy = ResilienceStrategy.BALANCED
    """

    ...


@dataclass
class ResilienceConfig:
    """
    Comprehensive resilience configuration with retry mechanisms, circuit breakers, and strategy management.
    
    Provides complete configuration for resilience patterns including retry behavior,
    circuit breaker policies, and feature toggles. Integrates with strategy-based presets
    while supporting custom configuration overrides for specific requirements.
    
    Attributes:
        strategy: ResilienceStrategy enum defining the overall resilience approach
        retry_config: RetryConfig with exponential backoff and jitter settings
        circuit_breaker_config: CircuitBreakerConfig with failure thresholds and recovery
        enable_circuit_breaker: bool to enable/disable circuit breaker functionality
        enable_retry: bool to enable/disable retry mechanisms
        
    State Management:
        - Immutable configuration after creation for consistent behavior
        - Strategy-based defaults with override capabilities
        - Comprehensive validation ensuring configuration integrity
        - Thread-safe access for concurrent resilience operations
        
    Usage:
        # Strategy-based configuration
        config = ResilienceConfig(strategy=ResilienceStrategy.CRITICAL)
        
        # Custom configuration with overrides
        config = ResilienceConfig(
            strategy=ResilienceStrategy.BALANCED,
            retry_config=RetryConfig(max_attempts=5),
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=3)
        )
        
        # Feature-specific configuration
        config = ResilienceConfig(
            strategy=ResilienceStrategy.CONSERVATIVE,
            enable_circuit_breaker=False,  # Retry-only mode
            enable_retry=True
        )
        
        # Integration with orchestrator
        orchestrator = AIServiceResilience()
        @orchestrator.with_resilience("ai_operation", custom_config=config)
        async def ai_operation():
            return await ai_service.process()
    """

    ...


@dataclass
class ResiliencePreset:
    """
    Predefined resilience configuration preset for different deployment scenarios.
    
    Encapsulates retry, circuit breaker, and strategy settings optimized for specific
    deployment contexts and operational requirements. Provides templates for common
    resilience patterns while allowing customization through operation overrides.
    
    Attributes:
        name: Human-readable name for the preset (e.g., "Production", "Development")
        description: Detailed description of the preset's purpose and characteristics
        retry_attempts: Number of retry attempts for failed operations (1-10)
        circuit_breaker_threshold: Failure count before circuit breaker opens (1-20)
        recovery_timeout: Seconds to wait before circuit breaker recovery attempts (10-600)
        default_strategy: Default ResilienceStrategy for general operations
        operation_overrides: Dictionary mapping operation names to specific strategies
        environment_contexts: List of environments where this preset is appropriate
    
    Public Methods:
        to_dict(): Convert preset to dictionary for JSON serialization
        to_resilience_config(): Convert preset to full ResilienceConfig object
    
    State Management:
        - Immutable dataclass ensuring configuration consistency
        - Automatic conversion strategies for different configuration formats
        - Environment-aware context matching for preset selection
        - Operation-specific granularity through strategy overrides
    
    Usage:
        # Access production preset
        prod_preset = PRESETS["production"]
        print(f"Production preset: {prod_preset.name}")
        print(f"Description: {prod_preset.description}")
    
        # Convert to configuration object
        config = prod_preset.to_resilience_config()
        print(f"Strategy: {config.strategy}")
        print(f"Retry attempts: {config.retry_config.max_attempts}")
    
        # Check operation overrides
        if "sentiment" in prod_preset.operation_overrides:
            sentiment_strategy = prod_preset.operation_overrides["sentiment"]
            print(f"Sentiment analysis uses {sentiment_strategy} strategy")
    
        # Environment context validation
        if "production" in prod_preset.environment_contexts:
            print("Preset suitable for production environment")
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert preset to dictionary for JSON serialization and export.
        
        Returns:
            Dict[str, Any]: Dictionary representation with:
            - All preset fields as key-value pairs
            - ResilienceStrategy enum values converted to strings
            - Maintained structure for configuration analysis
            - Suitable for persistence and transmission
        
        Behavior:
            - Converts ResilienceStrategy enum values to string representations
            - Preserves all metadata for analysis and reconstruction
            - Returns shallow copy safe for modification
            - Maintains compatibility with configuration management systems
        
        Examples:
            >>> preset = PRESETS["production"]
            >>> serialized = preset.to_dict()
            >>> serialized['name']
            'Production'
            >>> serialized['default_strategy']
            'conservative'
            >>> 'sentiment' in serialized['operation_overrides']
            True
        """
        ...

    def to_resilience_config(self) -> ResilienceConfig:
        """
        Convert preset to full ResilienceConfig object with optimized parameters.
        
        Returns:
            ResilienceConfig: Complete configuration object with:
            - Strategy-based retry configuration with exponential backoff
            - Circuit breaker configuration with appropriate thresholds
            - Optimized timing parameters for the preset's operational context
            - All feature flags enabled for comprehensive resilience
        
        Behavior:
            - Creates RetryConfig with strategy-specific exponential backoff parameters
            - Sets circuit breaker thresholds based on preset failure tolerance
            - Configures timing parameters (multipliers, min/max delays) by strategy
            - Uses aggressive timing for AGGRESSIVE strategy (faster retries)
            - Uses conservative timing for CONSERVATIVE strategy (slower, thorough retries)
            - Enables all resilience features for complete protection
        
        Examples:
            >>> preset = PRESETS["production"]
            >>> config = preset.to_resilience_config()
            >>> config.strategy
            <ResilienceStrategy.CONSERVATIVE: 'conservative'>
            >>> config.retry_config.max_attempts
            5
            >>> config.circuit_breaker_config.failure_threshold
            10
        
            >>> # Strategy affects timing parameters
            >>> aggressive_preset = PRESETS["development"]
            >>> aggro_config = aggressive_preset.to_resilience_config()
            >>> aggro_config.retry_config.exponential_min
            1.0  # Faster retries for development
        """
        ...


class PresetManager:
    """
    Comprehensive manager for resilience presets with validation, recommendation, and environment detection.
    
    Provides intelligent preset management including validation against configuration schemas,
    environment-aware preset recommendations, pattern-based environment classification,
    and detailed preset information for operational monitoring and debugging.
    
    Attributes:
        presets: Dictionary mapping preset names to ResiliencePreset objects
    
    Public Methods:
        get_preset(): Retrieve preset by name with validation
        list_presets(): Get list of available preset names
        get_preset_details(): Get comprehensive preset information
        validate_preset(): Validate preset configuration against rules
        recommend_preset(): Get environment-aware preset recommendation
        recommend_preset_with_details(): Get detailed recommendation with reasoning
        get_all_presets_summary(): Get summary of all available presets
    
    State Management:
        - Thread-safe preset access for concurrent operations
        - Comprehensive validation ensuring configuration integrity
        - Environment detection with confidence scoring
        - Pattern-based matching for complex deployment scenarios
        - Integration with unified environment detection service
    
    Usage:
        # Initialize manager
        manager = PresetManager()
    
        # Get recommended preset for current environment
        recommended = manager.recommend_preset()
        print(f"Recommended preset: {recommended}")
    
        # Get detailed recommendation with reasoning
        details = manager.recommend_preset_with_details("staging")
        print(f"Preset: {details.preset_name}")
        print(f"Confidence: {details.confidence:.2f}")
        print(f"Reasoning: {details.reasoning}")
    
        # Access specific preset
        prod_preset = manager.get_preset("production")
        config = prod_preset.to_resilience_config()
    
        # Validate custom preset
        is_valid = manager.validate_preset(custom_preset)
        if not is_valid:
            print("Preset validation failed")
    
        # Get all preset information
        all_presets = manager.get_all_presets_summary()
        for name, details in all_presets.items():
            print(f"{name}: {details['description']}")
    """

    def __init__(self):
        """
        Initialize preset manager with default presets and validation capabilities.
        
        Behavior:
            - Loads all predefined presets from PRESETS dictionary
            - Sets up validation infrastructure for configuration checking
            - Prepares environment detection patterns for intelligent recommendations
            - Initializes logging for operational monitoring
            - Creates thread-safe preset storage for concurrent access
        
        Examples:
            # Basic initialization
            manager = PresetManager()
        
            # Verify presets loaded
            preset_names = manager.list_presets()
            print(f"Loaded {len(preset_names)} presets: {preset_names}")
        
            # Access preset immediately
            simple_preset = manager.get_preset("simple")
            print(f"Simple preset: {simple_preset.description}")
        """
        ...

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
        ...

    def list_presets(self) -> List[str]:
        """
        Get list of available preset names.
        
        Returns:
            List of preset names (e.g., ["simple", "development", "production"])
        """
        ...

    def get_preset_details(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific preset.
        
        Args:
            name: Preset name to get details for
            
        Returns:
            Dictionary containing preset configuration details, description, and context
        """
        ...

    def validate_preset(self, preset: ResiliencePreset) -> bool:
        """
        Validate preset configuration values.
        
        Args:
            preset: Preset to validate
            
        Returns:
            True if valid, False otherwise
        """
        ...

    def recommend_preset(self, environment: Optional[str] = None) -> str:
        """
        Recommend appropriate preset for given environment.
        
        Args:
            environment: Environment name (dev, test, staging, prod, etc.)
            If None, will auto-detect from environment variables
            
        Returns:
            Recommended preset name
        """
        ...

    def recommend_preset_with_details(self, environment: Optional[str] = None) -> EnvironmentRecommendation:
        """
        Get detailed environment-aware preset recommendation with confidence scoring and reasoning.
        
        Args:
            environment: Environment name (dev, test, staging, prod, etc.) or None for auto-detection.
                       Case-insensitive, accepts full names or common abbreviations.
                       If None, uses unified environment detection service. Default: None
        
        Returns:
            EnvironmentRecommendation containing:
            - preset_name: Recommended preset name (simple, development, production)
            - confidence: Confidence score (0.0-1.0) indicating recommendation certainty
            - reasoning: Human-readable explanation of the recommendation logic
            - environment_detected: The environment that was identified or provided
        
        Behavior:
            - Uses high-confidence exact matching for common environment names
            - Applies pattern-based matching for complex environment naming schemes
            - Integrates with unified environment detection service for auto-detection
            - Provides confidence scoring based on evidence strength
            - Returns detailed reasoning for operational transparency
            - Falls back to 'simple' preset for unknown environments with low confidence
            - Maintains consistency with existing environment classification patterns
        
        Raises:
            ImportError: If unified environment detection service is unavailable
        
        Examples:
            # Direct environment specification
            result = manager.recommend_preset_with_details("production")
            print(f"Recommended: {result.preset_name}")
            print(f"Confidence: {result.confidence:.2f}")
            print(f"Reasoning: {result.reasoning}")
        
            # Auto-detection
            result = manager.recommend_preset_with_details()
            if result.confidence > 0.8:
                print(f"High confidence recommendation: {result.preset_name}")
            else:
                print(f"Low confidence ({result.confidence:.2f}), consider manual selection")
        
            # Complex environment names
            result = manager.recommend_preset_with_details("staging-environment-v2")
            print(f"Pattern matched: {result.environment_detected}")
            print(f"Recommended preset: {result.preset_name}")
        
            # Abbreviations
            result = manager.recommend_preset_with_details("dev")
            print(f"Abbreviation resolved: {result.preset_name}")
        """
        ...

    def get_all_presets_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary of all available presets with their detailed information.
        
        Returns:
            Dictionary mapping preset names to their detailed configuration information
        """
        ...


def get_default_presets() -> Dict[ResilienceStrategy, ResilienceConfig]:
    """
    Returns a dictionary of default resilience strategy configurations.
    
    Creates pre-configured ResilienceConfig objects for each available strategy
    (aggressive, balanced, conservative, critical) with optimized settings for
    different operational requirements.
    
    Returns:
        Dictionary mapping ResilienceStrategy enum values to configured ResilienceConfig objects
    """
    ...
