from app.infrastructure.monitoring.health import (
    HealthStatus,
    ComponentStatus,
    SystemHealthStatus,
)


def test_health_status_enum_values():
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"


def test_component_status_defaults():
    cs = ComponentStatus(name="x", status=HealthStatus.HEALTHY)
    assert cs.message == ""
    assert isinstance(cs.response_time_ms, float)
    assert cs.metadata is None


def test_system_health_status_structure():
    cs = ComponentStatus(name="x", status=HealthStatus.HEALTHY)
    shs = SystemHealthStatus(overall_status=HealthStatus.HEALTHY, components=[cs], timestamp=0.0)
    assert shs.overall_status is HealthStatus.HEALTHY
    assert len(shs.components) == 1

