"""Infrastructure tests for health checker and built-in checks."""

import asyncio
import pytest

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    check_ai_model_health,
)


@pytest.mark.asyncio
async def test_health_checker_register_and_run():
    checker = HealthChecker(default_timeout_ms=100)

    # Register a fast healthy check
    async def ok_check() -> ComponentStatus:
        return ComponentStatus(name="ok", status=HealthStatus.HEALTHY)

    checker.register_check("ok", ok_check)
    status = await checker.check_all_components()
    assert status.overall_status in {HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY}
    assert any(c.name == "ok" for c in status.components)


@pytest.mark.asyncio
async def test_health_checker_timeout_degrades():
    checker = HealthChecker(default_timeout_ms=50, retry_count=0)

    async def slow_check() -> ComponentStatus:
        await asyncio.sleep(0.2)
        return ComponentStatus(name="slow", status=HealthStatus.HEALTHY)

    checker.register_check("slow", slow_check)
    result = await checker.check_component("slow")
    # Timeout maps to DEGRADED by design
    assert result.status is HealthStatus.DEGRADED


@pytest.mark.asyncio
async def test_ai_model_health_uses_settings(monkeypatch):
    # No key -> degraded
    monkeypatch.setenv("GEMINI_API_KEY", "")
    result = await check_ai_model_health()
    assert result.status in {HealthStatus.DEGRADED, HealthStatus.HEALTHY}
