---
sidebar_label: test_health_check_performance
---

# Performance and stress tests for HealthChecker infrastructure.

  file_path: `backend/tests/performance/test_health_check_performance.py`

## Covers

- Individual health check timeout enforcement
- System aggregation latency (<50ms for fast checks)
- Concurrent requests safety
- Many registered components
- Slow health checks run concurrently (wall time bounded)
- Basic memory stability (no growth across repetitions)
