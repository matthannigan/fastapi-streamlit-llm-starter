"""
Performance and stress tests for HealthChecker infrastructure.

Covers:
- Individual health check timeout enforcement
- System aggregation latency (<50ms for fast checks)
- Concurrent requests safety
- Many registered components
- Slow health checks run concurrently (wall time bounded)
- Basic memory stability (no growth across repetitions)
"""

from __future__ import annotations

import asyncio
import time
import tracemalloc
from typing import Awaitable, Callable

import pytest

from app.infrastructure.monitoring.health import (
    ComponentStatus,
    HealthChecker,
    HealthStatus,
)


def _make_fast_check(name: str) -> Callable[[], Awaitable[ComponentStatus]]:
    async def _check() -> ComponentStatus:
        start = time.perf_counter()
        # no-op, immediate healthy
        return ComponentStatus(
            name=name,
            status=HealthStatus.HEALTHY,
            message="ok",
            response_time_ms=(time.perf_counter() - start) * 1000.0,
        )

    return _check


def _make_slow_check(name: str, sleep_ms: int) -> Callable[[], Awaitable[ComponentStatus]]:
    async def _check() -> ComponentStatus:
        start = time.perf_counter()
        await asyncio.sleep(sleep_ms / 1000.0)
        return ComponentStatus(
            name=name,
            status=HealthStatus.HEALTHY,
            message="ok",
            response_time_ms=(time.perf_counter() - start) * 1000.0,
        )

    return _check


@pytest.mark.asyncio
async def test_individual_timeout_enforced() -> None:
    """A component that exceeds its timeout returns DEGRADED with timeout message."""
    checker = HealthChecker(default_timeout_ms=10, retry_count=0)
    checker.register_check("too_slow", _make_slow_check("too_slow", sleep_ms=100))

    status = await checker.check_component("too_slow")
    assert status.status is HealthStatus.DEGRADED
    assert "timed out" in status.message.lower()
    assert status.response_time_ms >= 10


@pytest.mark.asyncio
async def test_system_aggregation_fast_under_50ms() -> None:
    """Fast checks should aggregate well under the 50ms target."""
    checker = HealthChecker(default_timeout_ms=500, retry_count=0)
    for i in range(5):
        checker.register_check(f"fast_{i}", _make_fast_check(f"fast_{i}"))

    t0 = time.perf_counter()
    result = await checker.check_all_components()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert result.overall_status is HealthStatus.HEALTHY
    # Target is <50ms; allow a small buffer for CI variance
    assert elapsed_ms < 50.0, f"Aggregation took {elapsed_ms:.2f}ms, expected < 50ms"


@pytest.mark.asyncio
async def test_concurrent_requests_are_safe() -> None:
    """Multiple concurrent invocations should succeed without interference."""
    checker = HealthChecker(default_timeout_ms=500, retry_count=0)
    for i in range(3):
        checker.register_check(f"fast_{i}", _make_fast_check(f"fast_{i}"))

    async def _one_round() -> HealthStatus:
        res = await checker.check_all_components()
        return res.overall_status

    rounds = 10
    statuses = await asyncio.gather(*[_one_round() for _ in range(rounds)])
    assert all(s is HealthStatus.HEALTHY for s in statuses)


@pytest.mark.asyncio
async def test_many_components_complete_quickly() -> None:
    """Registering many components should still complete promptly."""
    checker = HealthChecker(default_timeout_ms=1000, retry_count=0)
    for i in range(100):
        checker.register_check(f"c{i}", _make_fast_check(f"c{i}"))

    t0 = time.perf_counter()
    res = await checker.check_all_components()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert len(res.components) == 100
    assert res.overall_status is HealthStatus.HEALTHY
    # Heuristic bound to keep this test quick on CI
    assert elapsed_ms < 200.0


@pytest.mark.asyncio
async def test_slow_checks_run_concurrently() -> None:
    """Total wall time should approximate the slowest check, not the sum (concurrency)."""
    checker = HealthChecker(default_timeout_ms=1000, retry_count=0)
    for i in range(5):
        checker.register_check(f"slow_{i}", _make_slow_check(f"slow_{i}", sleep_ms=100))

    t0 = time.perf_counter()
    await checker.check_all_components()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # If run sequentially: ~500ms; with concurrency we expect close to 100ms
    assert elapsed_ms < 300.0, f"Expected concurrent behavior (<300ms), got {elapsed_ms:.2f}ms"


@pytest.mark.asyncio
async def test_per_component_timeout_override() -> None:
    """Per-component timeout overrides should be respected."""
    checker = HealthChecker(
        default_timeout_ms=500,
        per_component_timeouts_ms={"slow_exact": 50},
        retry_count=0,
    )
    checker.register_check("slow_exact", _make_slow_check("slow_exact", sleep_ms=200))

    status = await checker.check_component("slow_exact")
    assert status.status is HealthStatus.DEGRADED
    assert "timed out" in status.message.lower()
    assert status.response_time_ms >= 50


@pytest.mark.slow
@pytest.mark.asyncio
async def test_memory_stability_under_repetition() -> None:
    """Basic memory stability check: repeated runs should not grow memory significantly.

    Note: This is a heuristic sanity check, not a precise leak detector. Marked as slow and
    excluded by default per pytest.ini.
    """
    checker = HealthChecker(default_timeout_ms=500, retry_count=0)
    for i in range(10):
        checker.register_check(f"fast_{i}", _make_fast_check(f"fast_{i}"))

    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    # Run several rounds
    for _ in range(100):
        await checker.check_all_components()

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Compute memory difference in bytes (heuristic threshold: < 1MB growth)
    stats = snapshot_after.compare_to(snapshot_before, "filename")
    total_diff = sum(s.size_diff for s in stats)

    # Registry size should remain constant
    assert len(checker._checks) == 10  # noqa: SLF001 (intentional test of internal stability)

    assert total_diff < 1_000_000, f"Memory grew by {total_diff} bytes (>1MB)"
