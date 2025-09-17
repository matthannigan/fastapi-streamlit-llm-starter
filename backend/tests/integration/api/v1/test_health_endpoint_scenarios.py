import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_all_components_healthy(monkeypatch, client):
    async def fake_check_all():
        from app.infrastructure.monitoring.health import (
            SystemHealthStatus, ComponentStatus, HealthStatus
        )
        comps = [
            ComponentStatus(name="ai_model", status=HealthStatus.HEALTHY),
            ComponentStatus(name="cache", status=HealthStatus.HEALTHY),
            ComponentStatus(name="resilience", status=HealthStatus.HEALTHY),
        ]
        return SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=comps, timestamp=0.0)

    # Patch the dependency's instance method
    from app.dependencies import get_health_checker
    checker = get_health_checker()
    monkeypatch.setattr(checker, "check_all_components", fake_check_all)

    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["ai_model_available"] is True
    assert data["cache_healthy"] is True
    assert data["resilience_healthy"] is True


def test_health_degraded_when_component_degraded(monkeypatch, client):
    async def fake_check_all():
        from app.infrastructure.monitoring.health import (
            SystemHealthStatus, ComponentStatus, HealthStatus
        )
        comps = [
            ComponentStatus(name="ai_model", status=HealthStatus.HEALTHY),
            ComponentStatus(name="cache", status=HealthStatus.DEGRADED),
            ComponentStatus(name="resilience", status=HealthStatus.HEALTHY),
        ]
        return SystemHealthStatus(overall_status=HealthStatus.DEGRADED, components=comps, timestamp=0.0)

    from app.dependencies import get_health_checker
    checker = get_health_checker()
    monkeypatch.setattr(checker, "check_all_components", fake_check_all)

    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["cache_healthy"] is False


def test_health_endpoint_graceful_failure(monkeypatch, client):
    async def boom():
        raise RuntimeError("test failure")

    from app.dependencies import get_health_checker
    checker = get_health_checker()
    monkeypatch.setattr(checker, "check_all_components", boom)

    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    # resilience_healthy and cache_healthy should be None in degraded fallback
    assert data["resilience_healthy"] is None
    assert data["cache_healthy"] is None


def test_health_endpoint_failed_components(monkeypatch, client):
    """When components fail (unhealthy), endpoint should not 500 and should degrade."""
    async def fake_check_all():
        from app.infrastructure.monitoring.health import (
            SystemHealthStatus, ComponentStatus, HealthStatus
        )
        comps = [
            ComponentStatus(name="ai_model", status=HealthStatus.UNHEALTHY, message="AI down"),
            ComponentStatus(name="cache", status=HealthStatus.UNHEALTHY, message="Cache down"),
        ]
        return SystemHealthStatus(overall_status=HealthStatus.UNHEALTHY, components=comps, timestamp=0.0)

    from app.dependencies import get_health_checker
    checker = get_health_checker()
    monkeypatch.setattr(checker, "check_all_components", fake_check_all)

    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    # Backward-compat mapping uses 'degraded' for non-healthy
    assert data["status"] in ["degraded", "unhealthy"]


