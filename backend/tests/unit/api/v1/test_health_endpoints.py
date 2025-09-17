import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_public_health_endpoint_smoke(client):
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in ["healthy", "degraded", "unhealthy"]
    assert "ai_model_available" in data


def test_public_health_endpoint_redirect(client):
    # The /health utility should redirect to /v1/health
    resp = client.get("/health", follow_redirects=False)
    assert resp.status_code in [301, 302]
    assert resp.headers.get("Location") == "/v1/health"


