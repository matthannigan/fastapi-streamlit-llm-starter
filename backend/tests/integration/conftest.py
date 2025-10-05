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


@pytest.fixture(scope="module")
def production_environment_integration():
    """Set up production environment with API keys for integration tests."""
    # Set production environment with test API keys
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['API_KEY'] = 'test-api-key-12345'
    os.environ['ADDITIONAL_API_KEYS'] = 'test-key-2,test-key-3'

    yield

    # Cleanup after tests
    os.environ.pop('ENVIRONMENT', None)
    os.environ.pop('API_KEY', None)
    os.environ.pop('ADDITIONAL_API_KEYS', None)


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
