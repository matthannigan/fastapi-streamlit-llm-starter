"""
Integration-specific fixtures for testing.
"""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture(scope="module")
def integration_app():
    """Application instance for integration testing."""
    return app


@pytest.fixture(scope="module")
def integration_client(integration_app):
    """HTTP client for integration testing."""
    return TestClient(integration_app)


@pytest.fixture(scope="module")
async def async_integration_client(integration_app):
    """Async HTTP client for integration testing."""
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
