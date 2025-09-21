"""
Authentication Integration Test Fixtures

This module provides fixtures for authentication integration testing, including
environment-aware configuration, API key setup, and test clients with different
authentication scenarios.
"""

import pytest
import os
from typing import Dict, List, Optional
from unittest.mock import patch, Mock

from app.core.environment import Environment, FeatureContext


@pytest.fixture(scope="function")
def clean_environment():
    """Ensure clean environment variables for each test."""
    # Store original environment
    original_env = dict(os.environ)

    # Clear auth-related environment variables (except API keys for integration tests)
    auth_vars = [
        'AUTH_MODE',
        'ENABLE_USER_TRACKING', 'ENABLE_REQUEST_LOGGING',
        'ENVIRONMENT'
    ]

    for var in auth_vars:
        os.environ.pop(var, None)

    # Disable rate limiting for testing
    os.environ['RATE_LIMITING_ENABLED'] = 'false'

    # Preserve API_KEY and ADDITIONAL_API_KEYS for integration tests
    # These are loaded from .env file and needed for authentication testing

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def clean_environment_no_keys():
    """Ensure clean environment variables for each test with no API keys."""
    # Store original environment
    original_env = dict(os.environ)

    # Clear all auth-related environment variables including API keys
    auth_vars = [
        'AUTH_MODE',
        'ENABLE_USER_TRACKING', 'ENABLE_REQUEST_LOGGING',
        'ENVIRONMENT',
        'API_KEY',
        'ADDITIONAL_API_KEYS'
    ]

    for var in auth_vars:
        os.environ.pop(var, None)

    # Disable rate limiting for testing
    os.environ['RATE_LIMITING_ENABLED'] = 'false'

    # Reset global auth instance to have no keys
    try:
        from app.infrastructure.security.auth import api_key_auth, auth_config
        # Create fresh auth instance with no keys
        auth_config = type(auth_config)()
        api_key_auth = type(api_key_auth)(auth_config)
        # Reload to pick up the clean environment
        api_key_auth.reload_keys()
    except Exception:
        pass

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="function")
def development_environment(clean_environment):
    """Set up development environment (no API keys)."""
    os.environ.pop('API_KEY', None)
    os.environ.pop('ADDITIONAL_API_KEYS', None)
    os.environ['ENVIRONMENT'] = 'development'
    # Reflect changes in runtime settings and auth
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
    """Set up production environment with API keys."""
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['API_KEY'] = 'test-api-key-12345'
    os.environ['ADDITIONAL_API_KEYS'] = 'test-key-2,test-key-3'
    # Reflect in runtime settings
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
    """Set up staging environment with API keys."""
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
def advanced_auth_config(clean_environment):
    """Set up advanced authentication configuration."""
    os.environ['AUTH_MODE'] = 'advanced'
    os.environ['ENABLE_USER_TRACKING'] = 'true'
    os.environ['ENABLE_REQUEST_LOGGING'] = 'true'
    yield


@pytest.fixture(scope="function")
def single_api_key_config(clean_environment):
    """Set up configuration with single API key."""
    os.environ['API_KEY'] = 'single-test-key-12345'
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
def multiple_api_keys_config(clean_environment):
    """Set up configuration with multiple API keys."""
    os.environ['API_KEY'] = 'primary-test-key-12345'
    os.environ['ADDITIONAL_API_KEYS'] = 'secondary-key-67890,tertiary-key-abcdef'
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
def reload_auth_keys_after_multi(multiple_api_keys_config):
    """Reload global auth keys after setting multiple key environment variables."""
    # Import here to avoid circular import issues
    from app.infrastructure.security.auth import api_key_auth
    from app.core.config import settings

    # Sync runtime settings with env changes so reload picks them up
    settings.api_key = os.environ.get('API_KEY', '')
    settings.additional_api_keys = os.environ.get('ADDITIONAL_API_KEYS', '')

    api_key_auth.reload_keys()
    yield


@pytest.fixture(scope="function")
def reload_auth_keys_after_clear(development_environment):
    """Ensure no keys are configured and reload global auth keys (development mode)."""
    from app.infrastructure.security.auth import api_key_auth
    from app.core.config import settings

    # After development_environment cleared keys, reflect in runtime settings
    settings.api_key = os.environ.get('API_KEY', '')
    settings.additional_api_keys = os.environ.get('ADDITIONAL_API_KEYS', '')

    api_key_auth.reload_keys()
    yield


@pytest.fixture(scope="function")
def mock_environment_detection():
    """Mock environment detection for controlled testing."""
    def mock_get_environment_info(feature_context):
        class MockEnvironmentInfo:
            def __init__(self, environment, confidence=0.9):
                self.environment = environment
                self.confidence = confidence
                self.reasoning = f"Mocked {environment.value} environment"

        # Default to development unless specified otherwise
        return MockEnvironmentInfo(Environment.DEVELOPMENT, 0.9)

    with patch('app.infrastructure.security.auth.get_environment_info', side_effect=mock_get_environment_info):
        yield mock_get_environment_info


@pytest.fixture(scope="function")
def mock_production_environment_detection(mock_environment_detection):
    """Mock environment detection to return production environment."""
    def mock_get_environment_info(feature_context):
        class MockEnvironmentInfo:
            def __init__(self):
                self.environment = Environment.PRODUCTION
                self.confidence = 0.95
                self.reasoning = "Mocked production environment for testing"

        return MockEnvironmentInfo()

    with patch('app.infrastructure.security.auth.get_environment_info', side_effect=mock_get_environment_info):
        yield


@pytest.fixture(scope="function")
def mock_environment_detection_failure():
    """Mock environment detection to fail."""
    def mock_get_environment_info(feature_context):
        raise Exception("Environment detection service unavailable")

    with patch('app.infrastructure.security.auth.get_environment_info', side_effect=mock_get_environment_info):
        yield


@pytest.fixture
def valid_api_key_headers():
    """Headers with valid API key for authenticated requests."""
    return {
        "Authorization": "Bearer test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_api_key_headers():
    """Headers with invalid API key for testing authentication failures."""
    return {
        "Authorization": "Bearer invalid-api-key-99999",
        "Content-Type": "application/json"
    }


@pytest.fixture
def x_api_key_headers():
    """Headers using X-API-Key instead of Authorization Bearer."""
    return {
        "X-API-Key": "test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def malformed_auth_headers():
    """Headers with malformed authentication."""
    return {
        "Authorization": "Invalid-Format test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def missing_auth_headers():
    """Headers without any authentication."""
    return {"Content-Type": "application/json"}


@pytest.fixture(scope="function")
def auth_system_with_keys():
    """Create a fresh auth system with configured API keys."""
    # Import here to avoid circular imports
    from app.infrastructure.security.auth import APIKeyAuth, AuthConfig

    # Create fresh config and auth instances
    config = AuthConfig()
    auth_system = APIKeyAuth(config)

    # Configure test keys
    auth_system.api_keys.update({'test-key-1', 'test-key-2', 'test-key-3'})

    return auth_system


@pytest.fixture(scope="function")
def auth_system_without_keys():
    """Create a fresh auth system without API keys (development mode)."""
    # Import here to avoid circular imports
    from app.infrastructure.security.auth import APIKeyAuth, AuthConfig

    # Create fresh config and auth instances
    config = AuthConfig()
    auth_system = APIKeyAuth(config)

    # Clear any keys that might have been set
    auth_system.api_keys.clear()

    return auth_system
