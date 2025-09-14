"""
Unified Environment Detection Service

This module provides centralized environment detection capabilities for all backend
infrastructure services, eliminating code duplication and providing consistent
environment classification across cache, resilience, security, and other systems.

## Architecture Position

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Services                     │
├─────────────────────────────────────────────────────────────┤
│  Security Auth  │  Cache Presets  │  Resilience Config      │
│     (NEW)       │   (EXISTING)    │    (EXISTING)           │
├─────────────────────────────────────────────────────────────┤
│           Unified Environment Detection Service             │
│                        (NEW)                                │
├─────────────────────────────────────────────────────────────┤
│              Environment Variables & System                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **Centralized Detection**: Single source of truth for environment classification
- **Confidence Scoring**: Provides confidence levels and reasoning for decisions  
- **Extensible Patterns**: Configurable patterns for custom deployment scenarios
- **Context-Aware**: Supports feature-specific context (AI, security, cache)
- **Fallback Strategies**: Robust fallback detection for edge cases
- **Integration Ready**: Drop-in replacement for existing detection logic

## Usage Examples

```python
# Basic environment detection
detector = EnvironmentDetector()
env_info = detector.detect_environment()
print(f"Environment: {env_info.environment} (confidence: {env_info.confidence})")

# Feature-specific detection
ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

# Integration with existing systems
cache_preset = cache_manager.recommend_preset(env_info.environment)
resilience_preset = resilience_manager.recommend_preset(env_info.environment)
auth_config = security_auth.configure_for_environment(env_info)
```
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, NamedTuple, Set
from enum import Enum
import logging
import os
import re
from pathlib import Path


class Environment(str, Enum):
    """
    Standard environment classifications for application deployment contexts.
    
    Provides consistent environment naming across all backend infrastructure
    services including cache, resilience, security, and monitoring systems.
    
    Values:
        DEVELOPMENT: Local development and testing environments
        TESTING: Automated testing and CI environments
        STAGING: Pre-production environments for integration testing
        PRODUCTION: Live production environments serving real users
        UNKNOWN: Fallback when environment cannot be determined
    
    Examples:
        >>> env = Environment.PRODUCTION
        >>> assert env.value == "production"
        >>> assert str(env) == "production"
    
        >>> # Used in configuration
        >>> if env == Environment.PRODUCTION:
        ...     use_redis_cache = True
    """

    ...


class FeatureContext(str, Enum):
    """
    Feature-specific context for specialized environment detection.
    
    Enables feature-aware environment detection that considers specific
    infrastructure requirements like AI processing, security enforcement,
    or cache optimization when determining appropriate environment settings.
    
    Values:
        AI_ENABLED: Context for AI-powered features requiring model access
        SECURITY_ENFORCEMENT: Context for security-critical features
        CACHE_OPTIMIZATION: Context for cache-intensive operations
        RESILIENCE_STRATEGY: Context for resilience pattern selection
        DEFAULT: Standard environment detection without feature context
    
    Examples:
        >>> # Basic usage
        >>> context = FeatureContext.AI_ENABLED
        >>> assert context.value == "ai_enabled"
    
        >>> # Used with environment detection
        >>> env_info = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
        >>> # May return production environment even in dev if security is enforced
    """

    ...


class EnvironmentSignal(NamedTuple):
    """
    Single environment detection signal with confidence scoring and reasoning.
    
    Represents one piece of evidence used in environment detection, such as
    an environment variable, system indicator, or hostname pattern match.
    Each signal includes confidence scoring to enable weighted decision making.
    
    Attributes:
        source: Detection mechanism that generated this signal (e.g., "env_var", "hostname_pattern")
        value: Raw value that triggered the detection (e.g., "production", "staging.example.com")
        environment: Environment classification this signal indicates
        confidence: Confidence score from 0.0-1.0 for this detection
        reasoning: Human-readable explanation of why this signal indicates the environment
    
    Examples:
        >>> signal = EnvironmentSignal(
        ...     source="ENVIRONMENT",
        ...     value="production",
        ...     environment=Environment.PRODUCTION,
        ...     confidence=0.95,
        ...     reasoning="Explicit environment from ENVIRONMENT=production"
        ... )
        >>> assert signal.confidence > 0.9
        >>> assert signal.environment == Environment.PRODUCTION
    """

    ...


@dataclass
class EnvironmentInfo:
    """
    Comprehensive environment detection result with confidence scoring and metadata.
    
    Contains the final environment determination along with confidence scoring,
    reasoning, and supporting evidence. Includes feature-specific context and
    metadata for advanced use cases like preset selection or security overrides.
    
    Attributes:
        environment: Final determined environment classification
        confidence: Overall confidence score from 0.0-1.0 for the detection
        reasoning: Human-readable explanation of the detection decision
        detected_by: Primary detection mechanism that determined the environment
        feature_context: Feature-specific context used in detection
        additional_signals: All environment signals collected during detection
        metadata: Feature-specific metadata and configuration hints
    
    Usage:
        # Basic environment checking
        env_info = detector.detect_environment()
        if env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.8:
            enable_production_features()
    
        # Feature-aware detection
        ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
        if 'ai_prefix' in ai_env.metadata:
            cache_key_prefix = ai_env.metadata['ai_prefix']
    
        # Debugging detection issues
        print(f"Environment: {env_info}")
        print(f"Reasoning: {env_info.reasoning}")
        for signal in env_info.additional_signals:
            print(f"  - {signal.source}: {signal.reasoning}")
    """

    def __str__(self) -> str:
        ...


@dataclass
class DetectionConfig:
    """
    Configuration for environment detection behavior and patterns.
    
    Controls how the EnvironmentDetector identifies environments through
    environment variables, patterns, indicators, and feature-specific overrides.
    Allows customization of detection logic for different deployment scenarios.
    
    Attributes:
        env_var_precedence: Environment variables checked in priority order
        development_patterns: Regex patterns indicating development environments
        staging_patterns: Regex patterns indicating staging environments
        production_patterns: Regex patterns indicating production environments
        development_indicators: System indicators suggesting development
        production_indicators: System indicators suggesting production
        feature_contexts: Feature-specific configuration overrides
    
    Examples:
        # Custom configuration for specialized deployment
        config = DetectionConfig(
            env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
            production_patterns=[r'.*live.*', r'.*prod.*']
        )
        detector = EnvironmentDetector(config)
    
        # Add custom feature context
        config.feature_contexts[FeatureContext.AI_ENABLED] = {
            'environment_var': 'ENABLE_AI_FEATURES',
            'true_values': ['true', '1', 'enabled']
        }
    """

    ...


class EnvironmentDetector:
    """
    Unified environment detection service for consistent infrastructure configuration.
    
    Provides centralized environment classification across all backend infrastructure
    services including cache, resilience, security, and monitoring systems. Uses
    confidence scoring, feature-specific context, and extensible pattern matching
    to ensure reliable environment detection in diverse deployment scenarios.
    
    Public Methods:
        detect_environment(): Detect environment with optional feature context
        detect_with_context(): Detect environment with specific feature context
        get_environment_summary(): Get comprehensive detection summary with all signals
    
    State Management:
        - Maintains signal cache for performance optimization
        - Thread-safe for concurrent access across infrastructure services
        - Immutable configuration after initialization
    
    Behavior:
        - Collects environment signals from variables, patterns, and system indicators
        - Applies confidence scoring with conflict resolution
        - Supports feature-specific overrides for specialized detection
        - Provides fallback detection when no signals are found
        - Logs detection decisions for debugging and monitoring
    
    Usage:
        # Basic environment detection
        detector = EnvironmentDetector()
        env_info = detector.detect_environment()
    
        if env_info.environment == Environment.PRODUCTION:
            configure_production_services()
        elif env_info.confidence < 0.7:
            logger.warning(f"Low confidence detection: {env_info.reasoning}")
    
        # Feature-aware detection for AI services
        ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
        if ai_env.metadata.get('ai_prefix'):
            cache_prefix = ai_env.metadata['ai_prefix']
    
        # Custom configuration for specialized deployment
        config = DetectionConfig(
            production_patterns=[r'.*live.*', r'.*prod.*'],
            feature_contexts={
                FeatureContext.SECURITY_ENFORCEMENT: {
                    'environment_var': 'FORCE_SECURE_MODE',
                    'production_override': True
                }
            }
        )
        detector = EnvironmentDetector(config)
    
        # Debugging detection issues
        summary = detector.get_environment_summary()
        print(f"Detected: {summary['detected_environment']} ({summary['confidence']:.2f})")
        for signal in summary['all_signals']:
            print(f"  - {signal['source']}: {signal['reasoning']}")
    """

    def __init__(self, config: Optional[DetectionConfig] = None):
        """
        Initialize environment detector with configuration and caching.
        
        Args:
            config: Optional detection configuration with patterns and precedence.
                   Uses DetectionConfig() defaults if not provided.
        
        Behavior:
            - Creates signal cache for performance optimization
            - Validates configuration patterns are well-formed regex
            - Logs initialization for debugging and monitoring
            - Stores immutable configuration for thread safety
        
        Examples:
            >>> # Basic initialization with defaults
            >>> detector = EnvironmentDetector()
            >>> assert detector.config is not None
        
            >>> # Custom configuration
            >>> config = DetectionConfig(
            ...     env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
            ...     production_patterns=[r'.*prod.*', r'.*live.*']
            ... )
            >>> detector = EnvironmentDetector(config)
        """
        ...

    def detect_environment(self, feature_context: FeatureContext = FeatureContext.DEFAULT) -> EnvironmentInfo:
        """
        Detect environment with optional feature-specific context.
        
        Primary entry point for environment detection. Collects signals from
        environment variables, system indicators, and hostname patterns, then
        applies confidence scoring and feature-specific overrides.
        
        Args:
            feature_context: Feature-specific context for specialized detection.
                           Defaults to FeatureContext.DEFAULT for standard detection.
                           Use specific contexts like AI_ENABLED or SECURITY_ENFORCEMENT
                           for feature-aware detection.
        
        Returns:
            EnvironmentInfo containing:
            - environment: Detected Environment enum value
            - confidence: Float from 0.0-1.0 indicating detection confidence
            - reasoning: Human-readable explanation of detection decision
            - detected_by: Primary signal source that determined the environment
            - feature_context: The feature context used in detection
            - additional_signals: All signals collected during detection
            - metadata: Feature-specific metadata and configuration hints
        
        Behavior:
            - Collects environment signals from all configured sources
            - Applies feature-specific context overrides when specified
            - Uses confidence scoring to resolve conflicting signals
            - Returns development environment as fallback when no signals found
            - Caches detection results for performance optimization
            - Logs detection decisions for debugging and monitoring
        
        Examples:
            >>> detector = EnvironmentDetector()
            >>>
            >>> # Basic detection
            >>> env_info = detector.detect_environment()
            >>> assert env_info.environment in Environment
            >>> assert 0.0 <= env_info.confidence <= 1.0
            >>>
            >>> # Feature-aware detection
            >>> ai_env = detector.detect_environment(FeatureContext.AI_ENABLED)
            >>> if ai_env.metadata.get('ai_prefix'):
            ...     cache_key = f"{ai_env.metadata['ai_prefix']}cache-key"
            >>>
            >>> # High confidence check
            >>> if env_info.confidence > 0.8:
            ...     configure_production_features()
            >>> else:
            ...     logger.warning(f"Low confidence: {env_info.reasoning}")
        """
        ...

    def detect_with_context(self, feature_context: FeatureContext) -> EnvironmentInfo:
        """
        Detect environment with specific feature context and specialized logic.
        
        Performs feature-aware environment detection that considers specific
        infrastructure requirements. May override standard detection logic
        based on feature-specific environment variables and configuration.
        
        Args:
            feature_context: Specific feature context for specialized detection.
                           Must be a valid FeatureContext enum value.
                           Different contexts apply different detection rules:
                           - AI_ENABLED: Checks ENABLE_AI_CACHE, may add 'ai-' prefix
                           - SECURITY_ENFORCEMENT: May override to production if ENFORCE_AUTH=true
                           - DEFAULT: Standard detection without feature-specific overrides
        
        Returns:
            EnvironmentInfo with feature-aware detection results containing:
            - environment: Final determined environment (may be overridden by feature context)
            - confidence: Confidence score considering feature-specific signals
            - feature_context: The specific feature context used
            - metadata: Feature-specific configuration hints and overrides
            - additional_signals: All signals including feature-specific ones
        
        Behavior:
            - Collects standard environment detection signals
            - Applies feature-specific environment variable checks
            - May override environment based on feature requirements
            - Adds feature-specific metadata for configuration hints
            - Combines confidence scores from multiple signal sources
            - Logs feature-specific detection decisions
        
        Examples:
            >>> detector = EnvironmentDetector()
            >>>
            >>> # Security enforcement may override to production
            >>> security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
            >>> if security_env.environment == Environment.PRODUCTION:
            ...     enforce_authentication_requirements()
            >>>
            >>> # AI context provides cache prefix hints
            >>> ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)
            >>> cache_prefix = ai_env.metadata.get('ai_prefix', '')
            >>> cache_key = f"{cache_prefix}summarize:{text_hash}"
            >>>
            >>> # Feature-specific confidence assessment
            >>> if ai_env.confidence > 0.9 and 'enable_ai_cache_enabled' in ai_env.metadata:
            ...     use_ai_optimized_cache_settings()
        """
        ...

    def get_environment_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive environment detection summary with all signals and metadata.
        
        Provides detailed information about environment detection including
        all collected signals, confidence scores, and metadata. Useful for
        debugging detection issues and understanding how the environment was determined.
        
        Returns:
            Dictionary containing comprehensive detection information:
            - 'detected_environment': Final environment name as string
            - 'confidence': Overall confidence score (0.0-1.0)
            - 'reasoning': Human-readable explanation of detection decision
            - 'detected_by': Primary detection mechanism
            - 'all_signals': List of all signals with source, value, confidence
            - 'metadata': Feature-specific metadata and configuration hints
        
        Behavior:
            - Performs full environment detection with default context
            - Formats all signals for human-readable output
            - Includes both primary and additional signals
            - Preserves original signal confidence scores
            - Provides structured data for programmatic analysis
        
        Examples:
            >>> detector = EnvironmentDetector()
            >>> summary = detector.get_environment_summary()
            >>>
            >>> # Check detection results
            >>> print(f"Environment: {summary['detected_environment']}")
            >>> print(f"Confidence: {summary['confidence']:.2f}")
            >>> print(f"Reasoning: {summary['reasoning']}")
            >>>
            >>> # Analyze all signals
            >>> for signal in summary['all_signals']:
            ...     print(f"  {signal['source']}: {signal['reasoning']}")
            >>>
            >>> # Debug low confidence detection
            >>> if summary['confidence'] < 0.7:
            ...     logger.warning(f"Low confidence detection: {summary['reasoning']}")
            ...     for signal in summary['all_signals']:
            ...         logger.info(f"Signal: {signal['source']} -> {signal['environment']} ({signal['confidence']})")
        """
        ...


def get_environment_info(feature_context: FeatureContext = FeatureContext.DEFAULT) -> EnvironmentInfo:
    """
    Convenient function to get environment information using the global detector.
    
    Provides easy access to environment detection without needing to create
    an EnvironmentDetector instance. Uses the global environment_detector
    instance with default configuration for consistent detection across the application.
    
    Args:
        feature_context: Feature context for specialized detection logic.
                        Defaults to FeatureContext.DEFAULT for standard detection.
                        Use specific contexts like AI_ENABLED or SECURITY_ENFORCEMENT
                        for feature-aware detection.
    
    Returns:
        EnvironmentInfo containing:
        - environment: Detected Environment enum value
        - confidence: Detection confidence score (0.0-1.0)
        - reasoning: Human-readable explanation of detection
        - feature_context: The feature context used
        - metadata: Feature-specific configuration hints
        - additional_signals: All detection signals collected
    
    Raises:
        ValidationError: If feature_context is not a valid FeatureContext enum value
    
    Behavior:
        - Uses global environment_detector instance for consistent results
        - Performs full environment detection with confidence scoring
        - Applies feature-specific context when specified
        - Caches detection results for performance optimization
        - Thread-safe for concurrent access across services
    
    Examples:
        >>> # Basic environment detection
        >>> env_info = get_environment_info()
        >>> if env_info.environment == Environment.PRODUCTION:
        ...     enable_production_logging()
        >>>
        >>> # Feature-aware detection
        >>> ai_env = get_environment_info(FeatureContext.AI_ENABLED)
        >>> if ai_env.metadata.get('ai_prefix'):
        ...     cache_prefix = ai_env.metadata['ai_prefix']
        >>>
        >>> # Confidence-based decisions
        >>> security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        >>> if security_env.confidence > 0.8:
        ...     enforce_strict_security_policies()
        >>> else:
        ...     logger.warning(f"Uncertain environment detection: {security_env.reasoning}")
    """
    ...


def is_production_environment(feature_context: FeatureContext = FeatureContext.DEFAULT) -> bool:
    """
    Check if running in production environment with confidence threshold.
    
    Convenience function for production environment checks with built-in
    confidence validation. Uses reasonable confidence threshold to avoid
    false positives that could affect production configurations.
    
    Args:
        feature_context: Feature context for specialized detection logic.
                        Defaults to FeatureContext.DEFAULT for standard detection.
                        Use SECURITY_ENFORCEMENT context for stricter production detection.
    
    Returns:
        True if production environment is detected with confidence > 0.60,
        False otherwise. The 0.60 threshold balances reliability with
        sensitivity to avoid false production configurations.
    
    Behavior:
        - Performs environment detection with specified feature context
        - Requires both Environment.PRODUCTION and confidence > 0.60
        - Returns False for uncertain or non-production detections
        - Uses same detection logic as get_environment_info()
    
    Examples:
        >>> # Basic production check
        >>> if is_production_environment():
        ...     configure_production_logging()
        ...     enable_performance_monitoring()
        >>>
        >>> # Security-aware production check
        >>> if is_production_environment(FeatureContext.SECURITY_ENFORCEMENT):
        ...     enforce_authentication_requirements()
        ...     enable_audit_logging()
        >>>
        >>> # Combined with manual confidence check
        >>> env_info = get_environment_info()
        >>> if is_production_environment() and env_info.confidence > 0.9:
        ...     enable_strict_production_features()
    """
    ...


def is_development_environment(feature_context: FeatureContext = FeatureContext.DEFAULT) -> bool:
    """
    Check if running in development environment with confidence threshold.
    
    Convenience function for development environment checks with built-in
    confidence validation. Useful for enabling development-specific features
    like debug logging, hot reloading, or relaxed security settings.
    
    Args:
        feature_context: Feature context for specialized detection logic.
                        Defaults to FeatureContext.DEFAULT for standard detection.
                        Use specific contexts for feature-aware development detection.
    
    Returns:
        True if development environment is detected with confidence > 0.60,
        False otherwise. The 0.60 threshold ensures reasonable confidence
        while allowing for development environment variations.
    
    Behavior:
        - Performs environment detection with specified feature context
        - Requires both Environment.DEVELOPMENT and confidence > 0.60
        - Returns False for uncertain or non-development detections
        - Uses same detection logic as get_environment_info()
    
    Examples:
        >>> # Basic development check
        >>> if is_development_environment():
        ...     enable_debug_logging()
        ...     configure_hot_reloading()
        >>>
        >>> # AI development features
        >>> if is_development_environment(FeatureContext.AI_ENABLED):
        ...     use_development_ai_models()
        ...     enable_ai_debug_logging()
        >>>
        >>> # Development-specific cache settings
        >>> if is_development_environment(FeatureContext.CACHE_OPTIMIZATION):
        ...     use_memory_cache_only()
        ...     set_short_cache_ttls()
    """
    ...
