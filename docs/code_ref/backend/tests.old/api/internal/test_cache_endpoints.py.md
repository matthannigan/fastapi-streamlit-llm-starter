---
sidebar_label: test_cache_endpoints
---

# Integration tests for cache API endpoints.

  file_path: `backend/tests.old/api/internal/test_cache_endpoints.py`

Tests the FastAPI endpoints for configuration monitoring including
usage statistics, performance metrics, alerts, and data export.

## TestCacheEndpoints

Test cache-related endpoints.

### auth_headers()

```python
def auth_headers(self):
```

Create authentication headers.

### test_cache_status()

```python
def test_cache_status(self, client: TestClient):
```

Test cache status endpoint.

### test_cache_invalidate()

```python
def test_cache_invalidate(self, client: TestClient):
```

Test cache invalidation endpoint without auth (should fail).

### test_cache_invalidate_empty_pattern()

```python
def test_cache_invalidate_empty_pattern(self, client: TestClient):
```

Test cache invalidation with empty pattern without auth (should fail).

### test_cache_status_with_mock()

```python
def test_cache_status_with_mock(self, client: TestClient):
```

Test cache status with mocked cache stats.

### test_cache_invalidate_with_mock()

```python
def test_cache_invalidate_with_mock(self, client: TestClient, auth_headers):
```

Test cache invalidation with mocked cache.

### test_cache_invalidate_with_auth_success()

```python
def test_cache_invalidate_with_auth_success(self, client: TestClient, auth_headers):
```

Test cache invalidation endpoint with authentication.

### test_cache_invalidate_empty_pattern_with_auth()

```python
def test_cache_invalidate_empty_pattern_with_auth(self, client: TestClient, auth_headers):
```

Test cache invalidation with empty pattern and authentication.

## TestCachePerformanceAPIEndpoint

Comprehensive tests for the cache performance API endpoint with mocked monitor.

### auth_headers()

```python
def auth_headers(self):
```

Create authentication headers.

### test_cache_metrics_endpoint_with_mock_monitor()

```python
def test_cache_metrics_endpoint_with_mock_monitor(self, client_with_mock_monitor, mock_performance_monitor):
```

Test the cache metrics endpoint returns expected data structure.

### test_cache_metrics_endpoint_handles_monitor_none()

```python
def test_cache_metrics_endpoint_handles_monitor_none(self, client):
```

Test endpoint handles case where performance monitor is None.

### test_cache_metrics_endpoint_handles_stats_computation_error()

```python
def test_cache_metrics_endpoint_handles_stats_computation_error(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint handles statistics computation errors.

### test_cache_metrics_endpoint_handles_attribute_error()

```python
def test_cache_metrics_endpoint_handles_attribute_error(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint handles missing performance monitor methods.

### test_cache_metrics_endpoint_handles_unexpected_error()

```python
def test_cache_metrics_endpoint_handles_unexpected_error(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint handles unexpected errors during stats retrieval.

### test_cache_metrics_endpoint_validates_stats_format()

```python
def test_cache_metrics_endpoint_validates_stats_format(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint validates that stats are returned in correct format.

### test_cache_metrics_endpoint_handles_response_validation_error()

```python
def test_cache_metrics_endpoint_handles_response_validation_error(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint handles Pydantic validation errors.

### test_cache_metrics_endpoint_with_optional_fields()

```python
def test_cache_metrics_endpoint_with_optional_fields(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint correctly handles response with optional fields missing.

### test_cache_metrics_endpoint_with_all_optional_fields()

```python
def test_cache_metrics_endpoint_with_all_optional_fields(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint correctly handles response with all optional fields present.

### test_cache_metrics_endpoint_content_type_and_headers()

```python
def test_cache_metrics_endpoint_content_type_and_headers(self, client_with_mock_monitor):
```

Test endpoint returns correct content type and response headers.

### test_cache_metrics_endpoint_with_auth_headers()

```python
def test_cache_metrics_endpoint_with_auth_headers(self, client_with_mock_monitor, auth_headers):
```

Test endpoint works correctly with authentication headers.

### test_cache_metrics_endpoint_performance_with_large_dataset()

```python
def test_cache_metrics_endpoint_performance_with_large_dataset(self, client_with_mock_monitor, mock_performance_monitor):
```

Test endpoint performance with large mock dataset.
