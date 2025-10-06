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
    Set ENVIRONMENT='testing' for ALL integration tests.

    This prevents SecurityConfig from defaulting to production-level security
    which requires TLS certificates that don't exist in test environments.

    Test isolation is automatic via context-local environment detection.
    Each test context gets its own detector instance with no shared state.

    Applied to ALL integration tests (auth, cache, environment, health, startup).
    Individual tests can override by setting different ENVIRONMENT values.
    """
    # Set default testing environment
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "true")
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "gL/jVnZqgV5uKb/hYq1Jb3d8cZ5fJg6nO8r/d3gH2wA=")

    yield


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
