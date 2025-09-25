---
sidebar_label: test_monitoring_endpoints
---

# Tests for monitoring endpoints.

  file_path: `backend/tests.old/integration/api/internal/test_monitoring_endpoints.py`

Tests the monitoring health endpoint that checks the health of monitoring
subsystems including cache performance monitoring, cache service monitoring,
and resilience metrics collection.

## TestMonitoringHealthEndpoint

Test the /monitoring/health endpoint.

### auth_headers()

```python
def auth_headers(self):
```

Create authentication headers.

### test_monitoring_health_success()

```python
def test_monitoring_health_success(self, client: TestClient):
```

Test monitoring health endpoint returns healthy status when all components work.

### test_monitoring_health_with_auth()

```python
def test_monitoring_health_with_auth(self, client: TestClient, auth_headers):
```

Test monitoring health endpoint works with authentication.

### test_monitoring_health_cache_performance_monitor_failure()

```python
def test_monitoring_health_cache_performance_monitor_failure(self, client: TestClient):
```

Test monitoring health when cache performance monitor fails.

### test_monitoring_health_cache_service_monitoring_failure()

```python
def test_monitoring_health_cache_service_monitoring_failure(self, client: TestClient):
```

Test monitoring health when cache service monitoring fails.

### test_monitoring_health_resilience_monitoring_failure()

```python
def test_monitoring_health_resilience_monitoring_failure(self, client: TestClient):
```

Test monitoring health when resilience monitoring fails.

### test_monitoring_health_multiple_component_failures()

```python
def test_monitoring_health_multiple_component_failures(self, client: TestClient):
```

Test monitoring health when multiple components fail.

### test_monitoring_health_complete_failure()

```python
def test_monitoring_health_complete_failure(self, client: TestClient):
```

Test monitoring health when all components fail but endpoint still responds gracefully.

### test_monitoring_health_no_recent_cache_data()

```python
def test_monitoring_health_no_recent_cache_data(self, client: TestClient):
```

Test monitoring health when there's no recent cache performance data.

### test_monitoring_health_resilience_stats_partial_data()

```python
def test_monitoring_health_resilience_stats_partial_data(self, client: TestClient):
```

Test monitoring health when resilience stats have partial data.

### test_monitoring_health_invalid_auth_still_works()

```python
def test_monitoring_health_invalid_auth_still_works(self, client: TestClient):
```

Test monitoring health endpoint behavior with invalid auth.

### test_monitoring_health_no_auth_works()

```python
def test_monitoring_health_no_auth_works(self, client: TestClient):
```

Test monitoring health endpoint works with no auth headers (optional auth).

### test_monitoring_health_response_structure_complete()

```python
def test_monitoring_health_response_structure_complete(self, client: TestClient):
```

Test monitoring health endpoint returns complete expected structure.
