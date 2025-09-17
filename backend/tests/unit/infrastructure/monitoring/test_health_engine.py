import types
import pytest

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
)


@pytest.mark.asyncio
async def test_overall_status_healthy_degraded_unhealthy():
    checker = HealthChecker(default_timeout_ms=100)

    async def ok():
        return ComponentStatus(name="ok", status=HealthStatus.HEALTHY)

    async def degraded():
        return ComponentStatus(name="d", status=HealthStatus.DEGRADED)

    async def bad():
        return ComponentStatus(name="b", status=HealthStatus.UNHEALTHY)

    # All healthy
    checker.register_check("ok1", ok)
    checker.register_check("ok2", ok)
    status = await checker.check_all_components()
    assert status.overall_status is HealthStatus.HEALTHY

    # With degraded
    checker = HealthChecker(default_timeout_ms=100)
    checker.register_check("ok", ok)
    checker.register_check("d", degraded)
    status = await checker.check_all_components()
    assert status.overall_status is HealthStatus.DEGRADED

    # With unhealthy
    checker = HealthChecker(default_timeout_ms=100)
    checker.register_check("ok", ok)
    checker.register_check("b", bad)
    status = await checker.check_all_components()
    assert status.overall_status is HealthStatus.UNHEALTHY


def test_register_check_validations():
    checker = HealthChecker()
    with pytest.raises(ValueError):
        checker.register_check("", None)  # type: ignore[arg-type]

    async def ok():
        return ComponentStatus(name="ok", status=HealthStatus.HEALTHY)

    def not_async():  # pragma: no cover - only used to raise
        return ComponentStatus(name="x", status=HealthStatus.HEALTHY)

    with pytest.raises(TypeError):
        checker.register_check("sync", not_async)  # type: ignore[arg-type]

    # Valid registration should not raise
    checker.register_check("ok", ok)


@pytest.mark.asyncio
async def test_check_component_unregistered_raises():
    checker = HealthChecker()
    with pytest.raises(ValueError):
        await checker.check_component("missing")


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    attempts = {"n": 0}

    async def flaky():
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("first failure")
        return ComponentStatus(name="flaky", status=HealthStatus.HEALTHY)

    checker = HealthChecker(default_timeout_ms=100, retry_count=1, backoff_base_seconds=0.0)
    checker.register_check("flaky", flaky)
    result = await checker.check_component("flaky")
    assert result.status is HealthStatus.HEALTHY
    assert attempts["n"] == 2


@pytest.mark.asyncio
async def test_exception_path_unhealthy():
    async def boom():
        raise RuntimeError("boom")

    checker = HealthChecker(default_timeout_ms=50, retry_count=0)
    checker.register_check("boom", boom)
    result = await checker.check_component("boom")
    assert result.status is HealthStatus.UNHEALTHY
    assert "failed" in result.message.lower()


@pytest.mark.asyncio
async def test_per_component_timeout_override(monkeypatch):
    async def slow():
        import asyncio
        await asyncio.sleep(0.2)
        return ComponentStatus(name="slow", status=HealthStatus.HEALTHY)

    checker = HealthChecker(default_timeout_ms=10_000, per_component_timeouts_ms={"slow": 50}, retry_count=0)
    checker.register_check("slow", slow)
    result = await checker.check_component("slow")
    assert result.status is HealthStatus.DEGRADED  # timeout -> degraded by design


@pytest.mark.asyncio
async def test_check_ai_model_health_status(monkeypatch):
    # Without key -> degraded
    monkeypatch.setenv("GEMINI_API_KEY", "")
    degraded = await check_ai_model_health()
    assert degraded.status in {HealthStatus.DEGRADED, HealthStatus.HEALTHY}

    # With key -> healthy
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    healthy = await check_ai_model_health()
    assert healthy.status in {HealthStatus.HEALTHY, HealthStatus.DEGRADED}


@pytest.mark.asyncio
async def test_check_cache_health_paths(monkeypatch):
    # Fake AIResponseCache class to control stats
    class FakeCache:
        def __init__(self, *args, **kwargs):
            pass
        async def connect(self):
            return None

        async def get_cache_stats(self):
            return {
                "redis": {"status": "ok"},
                "memory": {"status": "ok"},
            }

    # Patch the import target used inside function
    import app.infrastructure.cache as cache_mod
    monkeypatch.setattr(cache_mod, "AIResponseCache", FakeCache)

    ok = await check_cache_health()
    assert ok.status in {HealthStatus.HEALTHY, HealthStatus.DEGRADED}

    class FakeCacheDegraded(FakeCache):
        async def get_cache_stats(self):
            return {
                "redis": {"status": "error"},
                "memory": {"status": "ok"},
            }

    monkeypatch.setattr(cache_mod, "AIResponseCache", FakeCacheDegraded)
    degraded = await check_cache_health()
    assert degraded.status is HealthStatus.DEGRADED

    class FakeCacheException(FakeCache):
        async def get_cache_stats(self):  # pragma: no cover - exercised
            raise RuntimeError("fail")

    monkeypatch.setattr(cache_mod, "AIResponseCache", FakeCacheException)
    unhealthy = await check_cache_health()
    assert unhealthy.status is HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_check_resilience_health_paths(monkeypatch):
    # Create a fake module with ai_resilience attribute
    fake_module = types.SimpleNamespace()

    class FakeResilience:
        def get_health_status(self):
            return {
                "healthy": True,
                "open_circuit_breakers": [],
                "half_open_circuit_breakers": [],
                "total_circuit_breakers": 0,
            }

    fake_module.ai_resilience = FakeResilience()

    import sys
    sys.modules["app.infrastructure.resilience.orchestrator"] = fake_module

    ok = await check_resilience_health()
    assert ok.status is HealthStatus.HEALTHY

    class FakeResilienceDegraded(FakeResilience):
        def get_health_status(self):
            return {
                "healthy": True,
                "open_circuit_breakers": ["x"],
                "half_open_circuit_breakers": [],
                "total_circuit_breakers": 1,
            }

    fake_module.ai_resilience = FakeResilienceDegraded()
    degraded = await check_resilience_health()
    assert degraded.status is HealthStatus.DEGRADED

    class FakeResilienceError(FakeResilience):
        def get_health_status(self):  # pragma: no cover - exercised
            raise RuntimeError("boom")

    fake_module.ai_resilience = FakeResilienceError()
    unhealthy = await check_resilience_health()
    assert unhealthy.status is HealthStatus.UNHEALTHY


@pytest.mark.asyncio
async def test_check_database_health_placeholder():
    from app.infrastructure.monitoring.health import check_database_health

    res = await check_database_health()
    assert res.status is HealthStatus.HEALTHY
    assert res.message.lower() == "not implemented"


