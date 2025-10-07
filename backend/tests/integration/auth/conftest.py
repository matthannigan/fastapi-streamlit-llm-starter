"""
Shared fixtures for authentication integration tests.

Provides environment manipulation, test client setup, and authentication
configuration for testing authentication system integration.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    """
    FastAPI test client for authentication integration testing.

    Provides real HTTP client that exercises complete FastAPI middleware
    stack including authentication dependencies and exception handling.

    Uses app factory pattern to ensure complete test isolation - each test
    gets a fresh app instance that picks up current environment variables
    without any cached state from previous tests.

    Note: This creates a client with default environment. For specific
    environment testing, use environment-specific fixtures or set
    environment variables in your test methods.

    Use Cases:
        - Testing complete HTTP authentication flows
        - Validating HTTP response codes and headers
        - Testing middleware integration and compatibility
    """
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def production_client(production_environment):
    """
    Test client with production environment pre-configured.

    This fixture ensures the production environment is set up before
    creating the app, so the app picks up the correct environment
    variables from the start.

    Use Cases:
        - Testing production-specific authentication behavior
        - Validating API key requirements in production
        - Testing security enforcement scenarios
    """
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def development_client(development_environment):
    """
    Test client with development environment pre-configured.

    Use Cases:
        - Testing development mode behavior
        - Validating relaxed security in development
        - Testing optional authentication scenarios
    """
    with TestClient(create_app()) as test_client:
        yield test_client


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
        - Clears cached settings to ensure fresh configuration
    """
    auth_vars = [
        "API_KEY", "ADDITIONAL_API_KEYS", "AUTH_MODE",
        "ENABLE_USER_TRACKING", "ENABLE_REQUEST_LOGGING", "ENVIRONMENT"
    ]

    for var in auth_vars:
        monkeypatch.delenv(var, raising=False)

    # Clear the LRU cache for get_settings to ensure fresh settings are created
    from app.dependencies import get_settings
    get_settings.cache_clear()

    yield monkeypatch

    # Clear again after the test to prevent pollution to next test
    get_settings.cache_clear()


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

    return clean_environment


@pytest.fixture
def development_with_keys_client(development_with_keys_environment):
    """
    Test client with development environment and API keys pre-configured.

    Use Cases:
        - Testing development mode with authentication enabled
        - Validating mixed development scenarios
    """
    with TestClient(create_app()) as test_client:
        yield test_client


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

    return clean_environment


@pytest.fixture
def multiple_api_keys_client(multiple_api_keys_environment):
    """
    Test client with multiple API keys pre-configured.

    Use Cases:
        - Testing multi-key authentication scenarios
        - Validating additional API keys handling
    """
    with TestClient(create_app()) as test_client:
        yield test_client


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
