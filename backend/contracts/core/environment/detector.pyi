"""
Main environment detection implementation.

Contains the core EnvironmentDetector class that orchestrates environment detection
using signals from various sources and applies confidence scoring.
"""

import logging
from typing import Optional, Dict, Any
from .enums import FeatureContext
from .models import DetectionConfig, EnvironmentInfo, EnvironmentSignal
from .patterns import collect_detection_signals
from .feature_contexts import apply_feature_context, determine_environment


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

    def reset_cache(self) -> None:
        """
        Clear all cached signals for test isolation.
        
        This method is primarily used in testing to ensure fresh environment
        detection between tests. It clears the internal signal cache to prevent
        stale detections from affecting subsequent test runs.
        
        Behavior:
            - Clears all cached environment signals
            - Next detection will perform fresh signal collection
            - Safe to call multiple times
            - No effect on detection configuration
        
        Examples:
            >>> detector = EnvironmentDetector()
            >>> detector.detect_environment()  # Caches detection
            >>> detector.reset_cache()  # Clear cache
            >>> detector.detect_environment()  # Fresh detection
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
