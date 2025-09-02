---
sidebar_label: test_health_check_performance
---

# Performance and stress tests for HealthChecker infrastructure.

  file_path: `backend/tests/performance/test_health_check_performance.py`

Covers:
- Individual health check timeout enforcement
- System aggregation latency (<50ms for fast checks)
- Concurrent requests safety
- Many registered components
- Slow health checks run concurrently (wall time bounded)
- Basic memory stability (no growth across repetitions)

## test_individual_timeout_enforced()

```python
async def test_individual_timeout_enforced() -> None:
```

A component that exceeds its timeout returns DEGRADED with timeout message.

## test_system_aggregation_fast_under_50ms()

```python
async def test_system_aggregation_fast_under_50ms() -> None:
```

Fast checks should aggregate well under the 50ms target.

## test_concurrent_requests_are_safe()

```python
async def test_concurrent_requests_are_safe() -> None:
```

Multiple concurrent invocations should succeed without interference.

## test_many_components_complete_quickly()

```python
async def test_many_components_complete_quickly() -> None:
```

Registering many components should still complete promptly.

## test_slow_checks_run_concurrently()

```python
async def test_slow_checks_run_concurrently() -> None:
```

Total wall time should approximate the slowest check, not the sum (concurrency).

## test_per_component_timeout_override()

```python
async def test_per_component_timeout_override() -> None:
```

Per-component timeout overrides should be respected.

## test_memory_stability_under_repetition()

```python
async def test_memory_stability_under_repetition() -> None:
```

Basic memory stability check: repeated runs should not grow memory significantly.

Note: This is a heuristic sanity check, not a precise leak detector. Marked as slow and
excluded by default per pytest.ini.
