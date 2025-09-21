"""
Environment Integration Test Fixtures

This module provides fixtures for environment detection integration testing, including
environment isolation, configuration management, and integration with infrastructure
components like security, cache, and resilience systems.
"""

import pytest
import os
from typing import Dict, List, Optional
from unittest.mock import patch, Mock
from pathlib import Path

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentDetector,
    DetectionConfig,
    get_environment_info,
    is_production_environment,
    is_development_environment
)


@pytest.fixture(scope="function")
def clean_environment():
    """
    Ensure clean environment variables for each test.

    This fixture provides complete environment isolation by backing up the
    original environment, clearing all environment variables that could affect
    environment detection, and restoring the original environment after the test.

    This is critical for environment detection integration tests as environment
    variables are global state that can cause test interference.

    Use Cases:
        - Testing environment detection in controlled conditions
        - Verifying environment-specific behavior
        - Ensuring test isolation between different environment scenarios

    Cleanup:
        Original environment is completely restored after test completion
    """
    # Store original environment
    original_env = dict(os.environ)

    # Clear all environment variables that could affect environment detection
    env_vars_to_clear = [
        'ENVIRONMENT', 'NODE_ENV', 'FLASK_ENV', 'APP_ENV', 'ENV',
        'DEPLOYMENT_ENV', 'DJANGO_SETTINGS_MODULE', 'RAILS_ENV',
        'API_KEY', 'ADDITIONAL_API_KEYS', 'AUTH_MODE',
        'ENABLE_USER_TRACKING', 'ENABLE_REQUEST_LOGGING',
        'ENABLE_AI_CACHE', 'ENFORCE_AUTH', 'DEBUG', 'PRODUCTION',
        'PROD', 'HOSTNAME', 'RATE_LIMITING_ENABLED'
    ]

    for var in env_vars_to_clear:
        os.environ.pop(var, None)

    # Disable rate limiting for testing
    os.environ['RATE_LIMITING_ENABLED'] = 'false'

    # Also clear any files that could be detected as system indicators
    # (Note: In a real test environment, you might want to mock Path.exists())

    yield

    # Restore original environment completely
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def development_environment(clean_environment):
    """
    Set up development environment for integration testing.

    Configures the environment to simulate a development deployment with
    typical development environment variables and system indicators.

    Configuration:
        - ENVIRONMENT=development (highest precedence)
        - No API keys configured
        - Development-specific system indicators

    Use Cases:
        - Testing development-specific behavior
        - Verifying relaxed security in development
        - Testing cache optimization for development
    """
    os.environ['ENVIRONMENT'] = 'development'

    # Reflect changes in runtime settings
    try:
        from app.core.config import settings
        from app.infrastructure.security.auth import api_key_auth
        settings.api_key = os.environ.get('API_KEY', '')
        settings.additional_api_keys = os.environ.get('ADDITIONAL_API_KEYS', '')
        api_key_auth.reload_keys()
    except Exception:
        pass

    yield


@pytest.fixture(scope="function")
def production_environment(clean_environment):
    """
    Set up production environment for integration testing.

    Configures the environment to simulate a production deployment with
    production environment variables and security requirements.

    Configuration:
        - ENVIRONMENT=production (highest precedence)
        - API keys configured and required
        - Production-specific system indicators
        - Security enforcement enabled

    Use Cases:
        - Testing production security enforcement
        - Verifying API key requirements
        - Testing production-specific resilience settings
    """
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['API_KEY'] = 'test-api-key-12345'
    os.environ['ADDITIONAL_API_KEYS'] = 'test-key-2,test-key-3'

    # Reflect changes in runtime settings
    try:
        from app.core.config import settings
        from app.infrastructure.security.auth import api_key_auth
        settings.api_key = os.environ.get('API_KEY', '')
        settings.additional_api_keys = os.environ.get('ADDITIONAL_API_KEYS', '')
        api_key_auth.reload_keys()
    except Exception:
        pass

    yield


@pytest.fixture(scope="function")
def staging_environment(clean_environment):
    """
    Set up staging environment for integration testing.

    Configures the environment to simulate a staging deployment with
    staging environment variables and balanced security.

    Configuration:
        - ENVIRONMENT=staging
        - API keys configured
        - Staging-specific system indicators

    Use Cases:
        - Testing staging-specific behavior
        - Verifying pre-production configurations
        - Testing integration with staging systems
    """
    os.environ['ENVIRONMENT'] = 'staging'
    os.environ['API_KEY'] = 'test-api-key-12345'

    try:
        from app.core.config import settings
        from app.infrastructure.security.auth import api_key_auth
        settings.api_key = os.environ.get('API_KEY', '')
        settings.additional_api_keys = os.environ.get('ADDITIONAL_API_KEYS', '')
        api_key_auth.reload_keys()
    except Exception:
        pass

    yield


@pytest.fixture(scope="function")
def testing_environment(clean_environment):
    """
    Set up testing environment for integration testing.

    Configures the environment to simulate a CI/CD testing environment.

    Configuration:
        - ENVIRONMENT=testing
        - Minimal security requirements
        - Testing-specific optimizations

    Use Cases:
        - Testing CI/CD pipeline behavior
        - Verifying automated test configurations
        - Testing environment detection in test scenarios
    """
    os.environ['ENVIRONMENT'] = 'testing'
    os.environ['CI'] = 'true'  # Common CI indicator

    yield


@pytest.fixture(scope="function")
def environment_with_hostname(clean_environment):
    """
    Set up environment with hostname-based detection.

    Configures environment variables and hostname to test hostname pattern
    matching in environment detection.

    Use Cases:
        - Testing hostname-based environment detection
        - Verifying containerized deployment detection
        - Testing pattern-based environment classification
    """
    os.environ['HOSTNAME'] = 'api-prod-01.example.com'

    yield


@pytest.fixture(scope="function")
def environment_with_system_indicators(clean_environment):
    """
    Set up environment with system indicator files.

    Creates temporary files that serve as system indicators for environment
    detection (e.g., .env, .git, docker-compose files).

    Use Cases:
        - Testing file-based environment detection
        - Verifying development environment indicators
        - Testing system-level environment detection
    """
    # Create temporary files that indicate development environment
    temp_dir = Path.cwd()
    env_file = temp_dir / '.env'
    git_dir = temp_dir / '.git'

    try:
        env_file.touch()
        git_dir.mkdir(exist_ok=True)

        yield

    finally:
        # Cleanup temporary files
        try:
            env_file.unlink(missing_ok=True)
            git_dir.rmdir()
        except OSError:
            pass  # Ignore cleanup errors


@pytest.fixture(scope="function")
def ai_enabled_environment(clean_environment):
    """
    Set up environment with AI features enabled.

    Configures environment for testing AI-specific feature contexts and
    environment detection overrides.

    Configuration:
        - ENABLE_AI_CACHE=true
        - AI-specific feature context testing
        - Cache optimization for AI workloads

    Use Cases:
        - Testing AI feature context detection
        - Verifying AI-specific environment overrides
        - Testing AI-optimized cache settings
    """
    os.environ['ENABLE_AI_CACHE'] = 'true'

    yield


@pytest.fixture(scope="function")
def security_enforcement_environment(clean_environment):
    """
    Set up environment with security enforcement enabled.

    Configures environment for testing security-specific feature contexts
    and production overrides.

    Configuration:
        - ENFORCE_AUTH=true
        - Security enforcement feature context
        - Production security requirements

    Use Cases:
        - Testing security context overrides
        - Verifying security enforcement behavior
        - Testing production security requirements
    """
    os.environ['ENFORCE_AUTH'] = 'true'

    yield


@pytest.fixture(scope="function")
def mock_environment_detector():
    """
    Mock environment detector for controlled testing.

    Provides a mock that can be configured to return specific environment
    information for testing component integration without real environment
    detection logic.

    Use Cases:
        - Testing components that depend on environment detection
        - Isolating component behavior from environment detection logic
        - Testing error scenarios in environment detection
    """
    def mock_get_environment_info(feature_context=FeatureContext.DEFAULT):
        class MockEnvironmentInfo:
            def __init__(self, environment=Environment.DEVELOPMENT, confidence=0.9):
                self.environment = environment
                self.confidence = confidence
                self.reasoning = f"Mocked {environment.value} environment"
                self.detected_by = "mock"
                self.feature_context = feature_context
                self.additional_signals = []
                self.metadata = {}

        return MockEnvironmentInfo()

    with patch('app.core.environment.get_environment_info', side_effect=mock_get_environment_info):
        yield mock_get_environment_info


@pytest.fixture(scope="function")
def mock_production_environment_detector(mock_environment_detector):
    """
    Mock environment detector configured for production environment.

    Pre-configured mock that returns production environment with high
    confidence for testing production-specific behavior.

    Use Cases:
        - Testing production security enforcement
        - Verifying production cache settings
        - Testing production resilience configurations
    """
    def mock_get_environment_info(feature_context=FeatureContext.DEFAULT):
        class MockEnvironmentInfo:
            def __init__(self):
                self.environment = Environment.PRODUCTION
                self.confidence = 0.95
                self.reasoning = "Mocked production environment for testing"
                self.detected_by = "mock"
                self.feature_context = feature_context
                self.additional_signals = []
                self.metadata = {}

        return MockEnvironmentInfo()

    with patch('app.core.environment.get_environment_info', side_effect=mock_get_environment_info):
        yield


@pytest.fixture(scope="function")
def mock_environment_detection_failure():
    """
    Mock environment detector that fails.

    Configured to raise exceptions to test error handling and fallback
    behavior in components that depend on environment detection.

    Use Cases:
        - Testing error handling in environment detection
        - Verifying fallback behavior when detection fails
        - Testing resilience of dependent components
    """
    def mock_get_environment_info(feature_context=FeatureContext.DEFAULT):
        raise Exception("Environment detection service unavailable")

    with patch('app.core.environment.get_environment_info', side_effect=mock_get_environment_info):
        yield


@pytest.fixture(scope="function")
def custom_detection_config():
    """
    Custom detection configuration for testing.

    Provides a DetectionConfig instance with custom patterns and settings
    for testing specialized deployment scenarios.

    Use Cases:
        - Testing custom environment detection patterns
        - Verifying custom environment variable precedence
        - Testing specialized deployment configurations
    """
    config = DetectionConfig(
        env_var_precedence=['CUSTOM_ENV', 'ENVIRONMENT'],
        production_patterns=[r'.*live.*', r'.*prod.*', r'.*production.*'],
        feature_contexts={
            FeatureContext.AI_ENABLED: {
                'environment_var': 'ENABLE_AI_FEATURES',
                'true_values': ['true', '1', 'enabled'],
                'preset_modifier': 'ai-'
            },
            FeatureContext.SECURITY_ENFORCEMENT: {
                'environment_var': 'FORCE_SECURE_MODE',
                'true_values': ['true', '1', 'yes'],
                'production_override': True
            }
        }
    )

    yield config


@pytest.fixture(scope="function")
def environment_detector_with_config(custom_detection_config):
    """
    Environment detector with custom configuration.

    Provides an EnvironmentDetector instance with custom configuration
    for testing specialized detection scenarios.

    Use Cases:
        - Testing custom pattern matching
        - Verifying custom environment variable precedence
        - Testing feature-specific overrides
    """
    detector = EnvironmentDetector(custom_detection_config)

    yield detector


# Convenience fixtures for common testing scenarios

@pytest.fixture(scope="function")
def prod_with_ai_features(clean_environment):
    """Production environment with AI features enabled."""
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['ENABLE_AI_CACHE'] = 'true'
    os.environ['API_KEY'] = 'test-api-key-12345'

    try:
        from app.core.config import settings
        from app.infrastructure.security.auth import api_key_auth
        settings.api_key = os.environ.get('API_KEY', '')
        api_key_auth.reload_keys()
    except Exception:
        pass

    yield


@pytest.fixture(scope="function")
def dev_with_security_enforcement(clean_environment):
    """Development environment with security enforcement enabled."""
    os.environ['ENVIRONMENT'] = 'development'
    os.environ['ENFORCE_AUTH'] = 'true'

    try:
        from app.core.config import settings
        from app.infrastructure.security.auth import api_key_auth
        settings.api_key = os.environ.get('API_KEY', '')
        api_key_auth.reload_keys()
    except Exception:
        pass

    yield


@pytest.fixture(scope="function")
def unknown_environment(clean_environment):
    """Environment with no clear indicators for fallback testing."""
    # Ensure no environment variables are set that would indicate a specific environment
    env_vars_to_clear = [
        'ENVIRONMENT', 'NODE_ENV', 'FLASK_ENV', 'APP_ENV', 'ENV',
        'DEPLOYMENT_ENV', 'DJANGO_SETTINGS_MODULE', 'RAILS_ENV',
        'HOSTNAME', 'CI'
    ]

    for var in env_vars_to_clear:
        os.environ.pop(var, None)

    yield
