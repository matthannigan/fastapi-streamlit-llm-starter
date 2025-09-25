"""
Shared fixtures for authentication integration tests.

Provides environment manipulation, test client setup, and authentication
configuration for testing authentication system integration.
"""

import pytest
import os
from fastapi.testclient import TestClient
from app.main import app


def reload_auth_system():
    """
    Force authentication system to reload configuration and keys.

    Must be called after environment variables are modified to ensure
    the authentication system picks up the changes.
    """
    from app.infrastructure.security.auth import api_key_auth, auth_config
    from app.core.config import settings

    # Reload the global settings to pick up environment variable changes
    # This forces Pydantic to re-read environment variables
    settings.__init__()

    # Reload the auth configuration to pick up environment variable changes
    auth_config.__init__()

    # Reload the API keys to pick up environment variable changes
    api_key_auth.reload_keys()


@pytest.fixture
def client():
    """
    FastAPI test client for authentication integration testing.
    
    Provides real HTTP client that exercises complete FastAPI middleware
    stack including authentication dependencies and exception handling.
    
    Use Cases:
        - Testing complete HTTP authentication flows
        - Validating HTTP response codes and headers
        - Testing middleware integration and compatibility
    """
    return TestClient(app)


@pytest.fixture
def clean_environment(monkeypatch):
    """
    Clean environment fixture that removes all auth-related variables.
    
    Ensures test isolation by clearing authentication configuration
    before each test, preventing environment variable pollution.
    
    Cleanup Actions:
        - Removes API_KEY and ADDITIONAL_API_KEYS
        - Clears AUTH_MODE and tracking settings
        - Resets ENVIRONMENT variable
    """
    auth_vars = [
        "API_KEY", "ADDITIONAL_API_KEYS", "AUTH_MODE",
        "ENABLE_USER_TRACKING", "ENABLE_REQUEST_LOGGING", "ENVIRONMENT"
    ]

    for var in auth_vars:
        monkeypatch.delenv(var, raising=False)

    yield monkeypatch


@pytest.fixture
def production_environment(clean_environment):
    """
    Configure production environment for testing production security enforcement.
    
    Sets up environment variables that trigger production security mode
    with API key requirements and strict validation.
    
    Configuration:
        - ENVIRONMENT=production (triggers production security)
        - API_KEY=test-production-key (primary key)
        - ADDITIONAL_API_KEYS=test-secondary-key (additional keys)
    """
    clean_environment.setenv("ENVIRONMENT", "production")
    clean_environment.setenv("API_KEY", "test-production-key")
    clean_environment.setenv("ADDITIONAL_API_KEYS", "test-secondary-key")

    # Reload authentication system after setting environment variables
    reload_auth_system()

    return clean_environment


@pytest.fixture
def development_environment(clean_environment):
    """
    Configure development environment for testing development mode behavior.
    
    Sets up environment that triggers development mode with optional
    authentication and appropriate warnings.
    
    Configuration:
        - ENVIRONMENT=development (triggers development mode)
        - No API keys configured (enables development mode)
    """
    clean_environment.setenv("ENVIRONMENT", "development")

    # Reload authentication system after setting environment variables
    reload_auth_system()

    return clean_environment


@pytest.fixture
def development_with_keys_environment(clean_environment):
    """
    Configure development environment with API keys for mixed-mode testing.
    
    Tests scenario where development environment has API keys configured,
    ensuring authentication still works but with development-appropriate behavior.
    
    Configuration:
        - ENVIRONMENT=development
        - API_KEY=test-dev-key (development key)
    """
    clean_environment.setenv("ENVIRONMENT", "development")
    clean_environment.setenv("API_KEY", "test-dev-key")

    # Reload authentication system after setting environment variables
    reload_auth_system()

    return clean_environment


@pytest.fixture
def multiple_api_keys_environment(clean_environment):
    """
    Configure environment with multiple API keys for key management testing.
    
    Tests multi-key authentication scenarios including primary key,
    additional keys, and whitespace handling.
    
    Configuration:
        - Primary key via API_KEY
        - Multiple additional keys via ADDITIONAL_API_KEYS
        - Keys with various formatting (whitespace testing)
    """
    clean_environment.setenv("API_KEY", "primary-key-12345")
    clean_environment.setenv("ADDITIONAL_API_KEYS", " secondary-key-67890 , tertiary-key-11111 ")

    # Reload authentication system after setting environment variables
    reload_auth_system()

    return clean_environment


@pytest.fixture
def auth_headers_valid():
    """
    Generate valid authentication headers for testing.
    
    Returns:
        Dict with Authorization header using Bearer token format
    """
    return {"Authorization": "Bearer test-production-key"}


@pytest.fixture
def auth_headers_invalid():
    """
    Generate invalid authentication headers for testing.
    
    Returns:
        Dict with Authorization header using invalid API key
    """
    return {"Authorization": "Bearer invalid-key-99999"}


@pytest.fixture
def auth_headers_secondary():
    """
    Generate authentication headers using secondary API key.
    
    Returns:
        Dict with Authorization header using secondary key from ADDITIONAL_API_KEYS
    """
    return {"Authorization": "Bearer test-secondary-key"}
