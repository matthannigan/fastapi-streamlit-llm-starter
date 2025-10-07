"""
Environment and feature context enumerations.

Contains the core enums for environment classification and feature-specific contexts
used throughout the environment detection system.
"""

from enum import Enum


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
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    UNKNOWN = "unknown"


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
    AI_ENABLED = "ai_enabled"
    SECURITY_ENFORCEMENT = "security_enforcement"
    CACHE_OPTIMIZATION = "cache_optimization"
    RESILIENCE_STRATEGY = "resilience_strategy"
    DEFAULT = "default"
