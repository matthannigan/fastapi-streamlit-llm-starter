"""
Integration-specific fixtures for testing.
"""
import pytest
import os
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Disable rate limiting during integration tests
os.environ['RATE_LIMITING_ENABLED'] = 'false'

from app.main import create_app


@pytest.fixture(autouse=True)
def setup_testing_environment_for_all_integration_tests(monkeypatch):
    """
    Set ENVIRONMENT='testing' and reset environment detector cache for ALL integration tests.

    This prevents SecurityConfig from defaulting to production-level security
    which requires TLS certificates that don't exist in test environments.

    Also clears the global environment_detector cache to prevent stale detection
    from previous tests affecting current test.

    Applied to ALL integration tests (auth, cache, environment, health, startup).
    Individual tests can override by setting different ENVIRONMENT values.
    """
    # Reset the global environment detector cache before each test
    from app.core.environment.api import environment_detector
    environment_detector.reset_cache()

    # Set default testing environment
    monkeypatch.setenv("ENVIRONMENT", "testing")

    yield

    # Reset cache after test to ensure clean state
    environment_detector.reset_cache()


@pytest.fixture(scope="function")
def production_environment_integration(monkeypatch):
    """
    Set up production environment with API keys for integration tests.

    Uses monkeypatch for proper cleanup after each test (function scope).
    This prevents environment pollution that was causing flaky tests.
    """
    # Set production environment with test API keys using monkeypatch
    monkeypatch.setenv('ENVIRONMENT', 'production')
    monkeypatch.setenv('API_KEY', 'test-api-key-12345')
    monkeypatch.setenv('ADDITIONAL_API_KEYS', 'test-key-2,test-key-3')

    yield

    # monkeypatch automatically cleans up after test


@pytest.fixture(scope="function")
def integration_app():
    """
    Fresh application instance for integration testing.

    Uses app factory pattern to ensure complete test isolation.
    Each test gets a fresh app instance that picks up current
    environment variables without any cached state.
    """
    return create_app()


@pytest.fixture(scope="function")
def integration_client(integration_app, production_environment_integration):
    """
    HTTP client for integration testing with production environment setup.

    Uses function scope to ensure each test gets a fresh client with a fresh
    app instance, providing complete test isolation.
    """
    return TestClient(integration_app)


@pytest.fixture(scope="function")
async def async_integration_client(integration_app):
    """
    Async HTTP client for integration testing.

    Uses function scope to ensure each test gets a fresh client with a fresh
    app instance, providing complete test isolation.
    """
    async with AsyncClient(
        transport=ASGITransport(app=integration_app),
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def authenticated_headers():
    """Headers with valid authentication for integration tests."""
    return {
        "Authorization": "Bearer test-api-key-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def invalid_api_key_headers():
    """Headers with invalid API key for integration tests."""
    return {
        "Authorization": "Bearer invalid-api-key-12345",
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
