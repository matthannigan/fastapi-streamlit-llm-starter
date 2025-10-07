"""
Module-level convenience functions.

Contains the detector instance (global or context-local depending on environment)
and convenience functions for easy access to environment detection functionality
without needing to create detector instances.

Hybrid Architecture:
    - Production: Uses global singleton for zero overhead
    - Tests: Uses context-local storage for automatic test isolation
"""

import sys
import os
import contextvars

from .enums import Environment, FeatureContext
from .models import EnvironmentInfo
from .detector import EnvironmentDetector

# Detect pytest at import time (same pattern as config.py)
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))

if _IS_PYTEST:
    # Testing: Use context-local storage for automatic test isolation
    # Each test context gets its own detector instance that doesn't pollute other tests
    _detector_context = contextvars.ContextVar('environment_detector', default=None)
    environment_detector = None  # No global instance in tests
else:
    # Production: Use global singleton for zero overhead
    # Single shared instance across all requests for optimal performance
    environment_detector = EnvironmentDetector()
    _detector_context = None


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
        - Production: Uses global environment_detector instance for zero overhead
        - Tests: Uses context-local detector instance for automatic test isolation
        - Performs full environment detection with confidence scoring
        - Applies feature-specific context when specified
        - Thread-safe for concurrent access across services
        - Test contexts automatically isolated - no manual cache management needed

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
    if _IS_PYTEST:
        # Test mode: Get or create context-local detector instance
        # Each test context gets its own detector that doesn't pollute other tests
        detector = _detector_context.get()
        if detector is None:
            # Lazy initialization per context
            detector = EnvironmentDetector()
            _detector_context.set(detector)
        return detector.detect_with_context(feature_context)
    else:
        # Production mode: Use global singleton for optimal performance
        return environment_detector.detect_with_context(feature_context)


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
    env_info = get_environment_info(feature_context)
    return env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.60


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
    env_info = get_environment_info(feature_context)
    return env_info.environment == Environment.DEVELOPMENT and env_info.confidence > 0.60
