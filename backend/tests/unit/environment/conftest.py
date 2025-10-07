"""
Fixtures for environment detection test suite.

This module provides test fixtures for testing the unified environment detection
service. All fixtures focus on external dependencies and test data setup without
exposing internal implementation details of the environment detection module.

Fixture Categories:
    - Basic Configuration: Default and custom DetectionConfig instances
    - Environment Detectors: Pre-configured EnvironmentDetector instances
    - Environment Mocking: Simulated environment variables and system conditions
    - System Mocking: File system, hostname, and system indicator simulation
    - Signal Scenarios: Various combinations of detection signals for testing
    - Error Conditions: Simulated failure scenarios for resilience testing
"""

import pytest
from unittest.mock import Mock, patch
import os
from pathlib import Path

from app.core.environment import (
    DetectionConfig,
    EnvironmentDetector,
    Environment,
    FeatureContext,
    EnvironmentSignal,
    EnvironmentInfo,
)


# =============================================================================
# Configuration Fixtures
# =============================================================================

@pytest.fixture
def custom_detection_config():
    """
    Provides DetectionConfig with modified patterns and precedence for testing.

    Use Cases:
        - Testing custom environment variable precedence
        - Testing specialized deployment naming patterns
        - Testing feature-specific configuration overrides

    Configuration:
        - Custom env_var_precedence with organization-specific variables
        - Modified pattern lists for specialized deployments
        - Feature context overrides for testing scenarios
    """
    return DetectionConfig(
        env_var_precedence=["CUSTOM_ENV", "ENVIRONMENT", "APP_ENV"],
        development_patterns=[r".*dev.*", r".*local.*", r".*test.*", r".*custom-dev.*"],
        staging_patterns=[r".*stage.*", r".*uat.*", r".*custom-stage.*"],
        production_patterns=[r".*prod.*", r".*live.*", r".*custom-prod.*"],
        development_indicators=["DEBUG=true", "CUSTOM_DEV=true", ".env"],
        production_indicators=["DEBUG=false", "CUSTOM_PROD=true", "PRODUCTION=true"],
        feature_contexts={
            FeatureContext.AI_ENABLED: {
                "environment_var": "ENABLE_AI_CACHE",
                "true_values": ["true", "1", "yes"],
                "preset_modifier": "ai-"
            },
            FeatureContext.SECURITY_ENFORCEMENT: {
                "environment_var": "ENFORCE_AUTH",
                "true_values": ["true", "1", "yes"],
                "production_override": True
            }
        }
    )


@pytest.fixture
def custom_precedence_config():
    """
    Provides DetectionConfig with custom environment variable precedence only.

    Use Cases:
        - Testing precedence ordering behavior
        - Testing organization-specific variable priorities
    """
    return DetectionConfig(
        env_var_precedence=["ORG_ENV", "CUSTOM_ENVIRONMENT", "ENVIRONMENT", "NODE_ENV"]
    )


@pytest.fixture
def custom_patterns_config():
    """
    Provides DetectionConfig with custom hostname patterns for specialized deployments.

    Use Cases:
        - Testing custom hostname pattern matching
        - Testing organization-specific naming conventions
    """
    return DetectionConfig(
        development_patterns=[r".*custom-dev.*", r".*org-dev.*"],
        staging_patterns=[r".*custom-stage.*", r".*org-uat.*"],
        production_patterns=[r".*custom-prod.*", r".*org-live.*"]
    )


@pytest.fixture
def custom_feature_config():
    """
    Provides DetectionConfig with custom feature context configuration.

    Use Cases:
        - Testing custom feature-specific detection logic
        - Testing organization-specific feature variables
    """
    return DetectionConfig(
        feature_contexts={
            FeatureContext.AI_ENABLED: {
                "environment_var": "ENABLE_AI_FEATURES",
                "true_values": ["true", "1", "enabled"],
                "preset_modifier": "custom-ai-"
            },
            FeatureContext.CACHE_OPTIMIZATION: {
                "environment_var": "OPTIMIZE_CACHE",
                "true_values": ["true", "1", "enabled"]
            }
        }
    )


@pytest.fixture
def custom_indicators_config():
    """
    Provides DetectionConfig with custom system indicators.

    Use Cases:
        - Testing custom development/production indicators
        - Testing organization-specific deployment markers
    """
    return DetectionConfig(
        development_indicators=["CUSTOM_DEBUG=true", ".custom-env", "DEV_MODE=on"],
        production_indicators=["CUSTOM_DEBUG=false", "PROD_MODE=on", "LIVE=true"]
    )


@pytest.fixture
def invalid_patterns_config():
    """
    Provides DetectionConfig with invalid regex patterns for error testing.

    Use Cases:
        - Testing configuration validation
        - Testing error handling for malformed patterns
    """
    return DetectionConfig(
        development_patterns=[r"[invalid-regex", r".*valid.*"],
        production_patterns=[r")*invalid", r".*valid.*"]
    )


# =============================================================================
# Environment Detector Fixtures
# =============================================================================

@pytest.fixture
def environment_detector():
    """
    Provides EnvironmentDetector instance with default configuration.

    Use Cases:
        - Standard environment detection testing
        - Baseline behavior validation
        - General functionality testing
    """
    return EnvironmentDetector()


# =============================================================================
# Environment Variable Mocking Fixtures
# =============================================================================

@pytest.fixture
def clean_environment():
    """
    Provides clean environment with no detection signals available.

    Use Cases:
        - Testing fallback detection behavior
        - Testing behavior when no environment signals are found

    Environment State:
        - No environment variables set
        - No system indicators present
        - No hostname patterns available
    """
    with patch.dict(os.environ, {}, clear=True), \
         patch("app.core.environment.patterns.Path.exists", return_value=False), \
         patch.dict(os.environ, {"HOSTNAME": ""}, clear=False):
        yield


@pytest.fixture
def mock_environment_conditions():
    """
    Provides various environment variable configurations for testing.

    Use Cases:
        - Testing different environment variable combinations
        - Testing confidence scoring with various signal strengths

    Returns:
        Dictionary with different environment scenarios
    """
    return {
        "production_explicit": {"ENVIRONMENT": "production"},
        "development_explicit": {"ENVIRONMENT": "development"},
        "node_env_prod": {"NODE_ENV": "production"},
        "flask_env_dev": {"FLASK_ENV": "development"},
        "mixed_signals": {"ENVIRONMENT": "production", "NODE_ENV": "development"},
        "common_values": {
            "dev": {"ENVIRONMENT": "dev"},
            "prod": {"ENVIRONMENT": "prod"},
            "test": {"ENVIRONMENT": "test"},
            "staging": {"ENVIRONMENT": "staging"}
        }
    }


@pytest.fixture
def mock_multiple_env_vars():
    """
    Provides environment with multiple conflicting environment variables.

    Use Cases:
        - Testing environment variable precedence
        - Testing conflict resolution logic
    """
    return {
        "ENVIRONMENT": "production",
        "NODE_ENV": "development",
        "FLASK_ENV": "testing",
        "APP_ENV": "staging"
    }


@pytest.fixture
def mock_common_env_values():
    """
    Provides environment variables with common naming conventions.

    Use Cases:
        - Testing mapping of common values to Environment enums
        - Testing compatibility with standard naming
    """
    return [
        ({"ENVIRONMENT": "dev"}, Environment.DEVELOPMENT),
        ({"ENVIRONMENT": "prod"}, Environment.PRODUCTION),
        ({"ENVIRONMENT": "test"}, Environment.TESTING),
        ({"ENVIRONMENT": "staging"}, Environment.STAGING),
        ({"NODE_ENV": "development"}, Environment.DEVELOPMENT),
        ({"NODE_ENV": "production"}, Environment.PRODUCTION)
    ]


@pytest.fixture
def mock_custom_env_vars():
    """
    Provides environment variables matching custom precedence configuration.

    Use Cases:
        - Testing custom environment variable precedence
        - Testing organization-specific variables
    """
    return {
        "ORG_ENV": "production",
        "CUSTOM_ENVIRONMENT": "development",
        "ENVIRONMENT": "testing"
    }


# =============================================================================
# Feature-Specific Environment Fixtures
# =============================================================================

@pytest.fixture
def mock_ai_environment_vars():
    """
    Provides environment variables for AI-specific feature detection.

    Use Cases:
        - Testing AI_ENABLED feature context behavior
        - Testing AI-specific metadata generation
    """
    return {
        "ENVIRONMENT": "development",
        "ENABLE_AI_CACHE": "true",
        "AI_MODEL": "gpt-4"
    }


@pytest.fixture
def mock_security_enforcement_vars():
    """
    Provides environment variables for security enforcement testing.

    Use Cases:
        - Testing SECURITY_ENFORCEMENT context overrides
        - Testing security-driven environment classification
    """
    return {
        "ENVIRONMENT": "development",
        "ENFORCE_AUTH": "true",
        "SECURITY_LEVEL": "high"
    }


@pytest.fixture
def mock_cache_environment_vars():
    """
    Provides environment variables for cache optimization testing.

    Use Cases:
        - Testing CACHE_OPTIMIZATION feature context
        - Testing cache-specific configuration hints
    """
    return {
        "ENVIRONMENT": "production",
        "CACHE_STRATEGY": "redis",
        "CACHE_TTL": "3600"
    }


@pytest.fixture
def mock_resilience_environment_vars():
    """
    Provides environment variables for resilience strategy testing.

    Use Cases:
        - Testing RESILIENCE_STRATEGY feature context
        - Testing resilience-specific metadata generation
    """
    return {
        "ENVIRONMENT": "production",
        "RESILIENCE_PRESET": "production",
        "CIRCUIT_BREAKER_ENABLED": "true"
    }


@pytest.fixture
def mock_feature_environment_vars():
    """
    Provides comprehensive feature-specific environment variables.

    Use Cases:
        - Testing multiple feature contexts together
        - Testing feature-specific metadata collection
    """
    return {
        "ENVIRONMENT": "production",
        "ENABLE_AI_CACHE": "true",
        "ENFORCE_AUTH": "true",
        "CACHE_STRATEGY": "redis",
        "RESILIENCE_PRESET": "production"
    }


@pytest.fixture
def mock_custom_feature_vars():
    """
    Provides environment variables matching custom feature configuration.

    Use Cases:
        - Testing custom feature context configuration
        - Testing organization-specific feature variables
    """
    return {
        "ENVIRONMENT": "development",
        "ENABLE_AI_FEATURES": "enabled",
        "OPTIMIZE_CACHE": "true"
    }


# =============================================================================
# System Indicator Fixtures
# =============================================================================

@pytest.fixture
def mock_debug_flags():
    """
    Provides various DEBUG flag configurations for testing.

    Use Cases:
        - Testing system indicator detection
        - Testing debug flag influence on environment classification
    """
    return [
        ({"DEBUG": "true"}, Environment.DEVELOPMENT),
        ({"DEBUG": "false"}, Environment.PRODUCTION),
        ({"DEBUG": "1"}, Environment.DEVELOPMENT),
        ({"DEBUG": "0"}, Environment.PRODUCTION)
    ]


@pytest.fixture
def mock_file_system():
    """
    Provides mocked file system with various indicator files.

    Use Cases:
        - Testing file-based system indicator detection
        - Testing development/production file presence logic
    """
    def mock_exists(path):
        path_str = str(path)
        # Development indicators
        if path_str in [".env", ".git", "docker-compose.dev.yml"]:
            return True
        # Production indicators would return False
        return False

    with patch("app.core.environment.patterns.Path.exists", side_effect=mock_exists):
        yield


@pytest.fixture
def mock_custom_indicators():
    """
    Provides environment/filesystem with custom system indicators.

    Use Cases:
        - Testing custom system indicator detection
        - Testing organization-specific deployment markers
    """
    env_vars = {
        "CUSTOM_DEBUG": "true",
        "DEV_MODE": "on"
    }

    def mock_exists(path):
        return str(path) in [".custom-env"]

    with patch.dict(os.environ, env_vars), \
         patch("app.core.environment.patterns.Path.exists", side_effect=mock_exists):
        yield


# =============================================================================
# Hostname Pattern Fixtures
# =============================================================================

@pytest.fixture
def mock_hostname_patterns():
    """
    Provides various hostname patterns for testing pattern matching.

    Use Cases:
        - Testing hostname pattern recognition
        - Testing containerized deployment detection
    """
    return [
        ("api-prod-01.example.com", Environment.PRODUCTION),
        ("staging-service.company.com", Environment.STAGING),
        ("dev-api.local", Environment.DEVELOPMENT),
        ("custom-prod-service", Environment.PRODUCTION),
        ("test-runner-123", Environment.TESTING)
    ]


@pytest.fixture
def mock_custom_hostname():
    """
    Provides hostname matching custom pattern configuration.

    Use Cases:
        - Testing custom hostname pattern matching
        - Testing organization-specific naming conventions
    """
    hostnames = [
        "custom-dev-api.org.com",
        "org-uat-service.internal",
        "custom-prod-web.company.com"
    ]
    return hostnames


@pytest.fixture
def mock_problematic_hostname():
    """
    Provides hostname values that could trigger regex issues.

    Use Cases:
        - Testing regex error handling
        - Testing edge cases in pattern matching
    """
    return [
        "hostname-with-[brackets]",
        "service.with.lots.of.dots...",
        "hostname_with_special_chars!@#",
        ""  # Empty hostname
    ]


# =============================================================================
# Signal Collection Fixtures
# =============================================================================

@pytest.fixture
def mock_environment_signal():
    """
    Provides known environment signal for predictable detection testing.

    Use Cases:
        - Testing detection reasoning and source identification
        - Testing signal processing logic
    """
    return EnvironmentSignal(
        source="ENVIRONMENT",
        value="production",
        environment=Environment.PRODUCTION,
        confidence=0.95,
        reasoning="Explicit environment from ENVIRONMENT=production"
    )


@pytest.fixture
def mock_primary_signal():
    """
    Provides primary environment signal with identifiable source.

    Use Cases:
        - Testing detected_by field population
        - Testing primary signal identification
    """
    return EnvironmentSignal(
        source="ENVIRONMENT",
        value="development",
        environment=Environment.DEVELOPMENT,
        confidence=0.95,
        reasoning="Primary signal from ENVIRONMENT variable"
    )


@pytest.fixture
def mock_environment_signals():
    """
    Provides multiple environment signals for comprehensive testing.

    Use Cases:
        - Testing signal collection and summary generation
        - Testing multiple signal processing
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Explicit env var"),
        EnvironmentSignal("hostname_pattern", "prod-api", Environment.PRODUCTION, 0.70, "Hostname pattern"),
        EnvironmentSignal("system_indicator", "DEBUG=false", Environment.PRODUCTION, 0.75, "Debug flag")
    ]


@pytest.fixture
def mock_multiple_signals():
    """
    Provides various types of detection signals for analysis testing.

    Use Cases:
        - Testing signal formatting and analysis
        - Testing comprehensive signal collection
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Environment variable"),
        EnvironmentSignal("NODE_ENV", "production", Environment.PRODUCTION, 0.85, "Node environment"),
        EnvironmentSignal("hostname_pattern", "prod-service", Environment.PRODUCTION, 0.70, "Hostname match"),
        EnvironmentSignal("system_indicator", ".git", Environment.DEVELOPMENT, 0.60, "Git repository detected")
    ]


@pytest.fixture
def mock_mixed_signal_sources():
    """
    Provides signals from various sources with different reliability levels.

    Use Cases:
        - Testing signal confidence scoring
        - Testing source reliability assessment
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "High confidence env var"),
        EnvironmentSignal("hostname_pattern", "prod-api", Environment.PRODUCTION, 0.65, "Medium confidence pattern"),
        EnvironmentSignal("system_indicator", "DEBUG=false", Environment.PRODUCTION, 0.70, "Medium confidence indicator")
    ]


@pytest.fixture
def mock_conflicting_signals():
    """
    Provides contradictory high-confidence signals for conflict testing.

    Use Cases:
        - Testing signal conflict resolution
        - Testing confidence reduction logic
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Explicit production"),
        EnvironmentSignal("NODE_ENV", "development", Environment.DEVELOPMENT, 0.85, "Node development"),
        EnvironmentSignal("hostname_pattern", "dev-service", Environment.DEVELOPMENT, 0.75, "Development hostname")
    ]


@pytest.fixture
def mock_agreeing_signals():
    """
    Provides multiple signals indicating the same environment.

    Use Cases:
        - Testing confidence boosting logic
        - Testing signal agreement assessment
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Environment variable"),
        EnvironmentSignal("hostname_pattern", "prod-api", Environment.PRODUCTION, 0.70, "Production hostname"),
        EnvironmentSignal("system_indicator", "DEBUG=false", Environment.PRODUCTION, 0.75, "Production indicator")
    ]


@pytest.fixture
def mock_mixed_environment_signals():
    """
    Provides combination of base and feature-specific signals.

    Use Cases:
        - Testing feature context signal preservation
        - Testing comprehensive signal collection
    """
    base_signals = [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Base environment"),
        EnvironmentSignal("hostname_pattern", "prod-api", Environment.PRODUCTION, 0.70, "Base hostname")
    ]

    feature_signals = [
        EnvironmentSignal("security_override", "ENFORCE_AUTH=true", Environment.PRODUCTION, 0.90, "Security enforcement")
    ]

    return {"base": base_signals, "feature": feature_signals}


# =============================================================================
# Confidence and Performance Fixtures
# =============================================================================

@pytest.fixture
def mock_confidence_scenarios():
    """
    Provides environment conditions producing different confidence levels.

    Use Cases:
        - Testing confidence threshold logic
        - Testing environment check function behavior
    """
    return [
        # High confidence scenarios
        {
            "env_vars": {"ENVIRONMENT": "production"},
            "expected_confidence": 0.95,
            "expected_environment": Environment.PRODUCTION
        },
        # Medium confidence scenarios
        {
            "env_vars": {"NODE_ENV": "production"},
            "hostname": "prod-api",
            "expected_confidence": 0.75,
            "expected_environment": Environment.PRODUCTION
        },
        # Low confidence scenarios
        {
            "hostname": "ambiguous-service",
            "expected_confidence": 0.45,
            "expected_environment": Environment.DEVELOPMENT  # fallback
        }
    ]


@pytest.fixture
def mock_known_confidence_signals():
    """
    Provides environment signals with predetermined confidence scores.

    Use Cases:
        - Testing confidence score preservation
        - Testing signal confidence analysis
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Highest confidence"),
        EnvironmentSignal("NODE_ENV", "production", Environment.PRODUCTION, 0.85, "High confidence"),
        EnvironmentSignal("hostname_pattern", "prod-api", Environment.PRODUCTION, 0.70, "Medium confidence"),
        EnvironmentSignal("system_indicator", ".git", Environment.DEVELOPMENT, 0.60, "Lower confidence")
    ]


@pytest.fixture
def mock_cacheable_signals():
    """
    Provides stable environment signals suitable for caching testing.

    Use Cases:
        - Testing signal caching performance
        - Testing repeated detection optimization
    """
    return [
        EnvironmentSignal("ENVIRONMENT", "production", Environment.PRODUCTION, 0.95, "Cacheable env var"),
        EnvironmentSignal("hostname_pattern", "stable-prod-api", Environment.PRODUCTION, 0.70, "Cacheable hostname")
    ]


@pytest.fixture
def thread_pool():
    """
    Provides thread pool for concurrent testing.

    Use Cases:
        - Testing thread safety
        - Testing concurrent detection calls
    """
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as executor:
        yield executor


# =============================================================================
# Global Detector Mocking Fixtures
# =============================================================================

@pytest.fixture
def mock_global_detector():
    """
    Provides mocked environment detector instance for context-local hybrid approach.

    Use Cases:
        - Testing module-level convenience functions
        - Testing detector consistency in hybrid mode

    Implementation:
        Patches get_environment_info in both the API module and the main package
        namespace to handle different import patterns in tests.
    """
    mock_detector = Mock(spec=EnvironmentDetector)

    def mock_get_environment_info(feature_context=FeatureContext.DEFAULT):
        """Mock implementation that returns configurable results."""
        result = mock_detector.detect_with_context(feature_context)
        return result

    # Set default return value
    mock_detector.detect_with_context.return_value = EnvironmentInfo(
        environment=Environment.DEVELOPMENT,
        confidence=0.85,
        reasoning="Mocked detection result",
        detected_by="mock_source",
        feature_context=FeatureContext.DEFAULT,
        additional_signals=[],
        metadata={}
    )

    # Patch in both locations to handle re-exports
    with patch("app.core.environment.api.get_environment_info", side_effect=mock_get_environment_info), \
         patch("app.core.environment.get_environment_info", side_effect=mock_get_environment_info):
        yield mock_detector


@pytest.fixture
def mock_feature_detection_results():
    """
    Provides detection results for various feature contexts.

    Use Cases:
        - Testing feature context support in convenience functions
        - Testing feature-specific detection consistency
    """
    results = {
        FeatureContext.DEFAULT: EnvironmentInfo(
            environment=Environment.DEVELOPMENT,
            confidence=0.80,
            reasoning="Default detection",
            detected_by="env_var",
            feature_context=FeatureContext.DEFAULT
        ),
        FeatureContext.AI_ENABLED: EnvironmentInfo(
            environment=Environment.DEVELOPMENT,
            confidence=0.85,
            reasoning="AI-aware detection",
            detected_by="env_var",
            feature_context=FeatureContext.AI_ENABLED,
            metadata={"ai_prefix": "ai-"}
        ),
        FeatureContext.SECURITY_ENFORCEMENT: EnvironmentInfo(
            environment=Environment.PRODUCTION,  # Override to production
            confidence=0.90,
            reasoning="Security enforcement override",
            detected_by="security_override",
            feature_context=FeatureContext.SECURITY_ENFORCEMENT
        )
    }
    return results


# =============================================================================
# Error Condition Fixtures
# =============================================================================

@pytest.fixture
def mock_file_system_errors():
    """
    Provides file system that raises errors on access attempts.

    Use Cases:
        - Testing file system error handling
        - Testing graceful degradation
    """
    # Store original function to avoid recursion
    original_exists = Path.exists

    def mock_exists_with_error(self):
        path_str = str(self)
        # Only raise errors for specific test paths, not pytest internals
        if "restricted" in path_str or path_str in [".env", ".git", "docker-compose.dev.yml"]:
            raise PermissionError("Access denied")
        # Use the original method for all other paths
        return original_exists(self)

    with patch.object(Path, "exists", mock_exists_with_error):
        yield


@pytest.fixture
def mock_env_access_errors():
    """
    Provides environment that raises errors on variable access.

    Use Cases:
        - Testing environment variable access error handling
        - Testing detection resilience
    """
    def mock_getenv_with_error(key, default=None):
        if key == "RESTRICTED_VAR":
            raise PermissionError("Environment access denied")
        return default

    with patch("os.getenv", side_effect=mock_getenv_with_error):
        yield


@pytest.fixture
def mock_error_conditions():
    """
    Provides environment conditions designed to trigger specific errors.

    Use Cases:
        - Testing error message quality
        - Testing error condition handling
    """
    return {
        "file_permission_error": {"restricted_file": ".restricted-env"},
        "env_access_error": {"restricted_var": "RESTRICTED_VAR"},
        "regex_error": {"problematic_hostname": "hostname-with-[invalid-regex]"}
    }


@pytest.fixture
def mock_partial_failure_conditions():
    """
    Provides environment with some detection mechanisms failing.

    Use Cases:
        - Testing partial functionality maintenance
        - Testing detection resilience
    """
    # Environment where file system fails but environment variables work
    env_vars = {"ENVIRONMENT": "production"}

    # Store original function to avoid recursion
    original_exists = Path.exists

    def mock_exists_failing(self):
        path_str = str(self)
        # Fail only for environment detection paths, not pytest internals
        if any(indicator in path_str for indicator in [".env", ".git", "docker-compose", "requirements"]):
            raise OSError("File system unavailable")
        # Use the original method for all other paths (pytest internals)
        return original_exists(self)

    with patch.dict(os.environ, env_vars), \
         patch.object(Path, "exists", mock_exists_failing):
        yield


# =============================================================================
# Logger Mocking Fixtures
# =============================================================================

@pytest.fixture
def mock_logger():
    """
    Provides mocked logger to capture initialization and detection messages.

    Use Cases:
        - Testing logging behavior
        - Validating log message content and levels
    """
    mock_logger = Mock()
    with patch("app.core.environment.detector.logger", mock_logger):
        yield mock_logger
