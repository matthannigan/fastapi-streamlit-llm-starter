---
sidebar_label: test_resilience_performance_endpoints
---

# Integration tests for resilience performance benchmark API endpoints.

  file_path: `backend/tests.old/integration/api/internal/test_resilience_performance_endpoints.py`

Tests the FastAPI endpoints for running performance benchmarks,
getting performance reports, and accessing performance metrics.

## TestPerformanceBenchmarkEndpoints

Test performance benchmark API endpoints.

### client()

```python
def client(self):
```

Create test client.

### auth_headers()

```python
def auth_headers(self):
```

Create authentication headers.

### test_get_performance_thresholds()

```python
def test_get_performance_thresholds(self, client):
```

Test getting performance thresholds endpoint.

### test_run_performance_benchmark_unauthorized()

```python
def test_run_performance_benchmark_unauthorized(self, client):
```

Test running benchmark without authentication.

### test_run_performance_benchmark_authorized()

```python
def test_run_performance_benchmark_authorized(self, client, auth_headers):
```

Test running performance benchmark with authentication.

### test_run_custom_performance_benchmark()

```python
def test_run_custom_performance_benchmark(self, client, auth_headers):
```

Test running custom performance benchmark.

### test_run_custom_benchmark_invalid_operation()

```python
def test_run_custom_benchmark_invalid_operation(self, client, auth_headers):
```

Test running custom benchmark with invalid operation.

### test_get_performance_report_json()

```python
def test_get_performance_report_json(self, client, auth_headers):
```

Test getting performance report in JSON format.

### test_get_performance_report_text()

```python
def test_get_performance_report_text(self, client, auth_headers):
```

Test getting performance report in text format.

### test_get_performance_history()

```python
def test_get_performance_history(self, client, auth_headers):
```

Test getting performance history.

### test_comprehensive_benchmark_performance_validation()

```python
def test_comprehensive_benchmark_performance_validation(self, client, auth_headers):
```

Test comprehensive benchmark to validate actual performance.

## TestPerformanceBenchmarkErrorHandling

Test error handling in performance benchmark endpoints.

### client()

```python
def client(self):
```

Create test client.

### auth_headers()

```python
def auth_headers(self):
```

Create authentication headers.

### test_benchmark_with_service_error()

```python
def test_benchmark_with_service_error(self, client, auth_headers):
```

Test benchmark handling when underlying services fail.

### test_performance_report_with_no_data()

```python
def test_performance_report_with_no_data(self, client, auth_headers):
```

Test performance report when no benchmark data exists.

## TestPerformanceBenchmarkIntegration

Test integration of performance benchmarks with configuration system.

### client()

```python
def client(self):
```

Create test client.

### auth_headers()

```python
def auth_headers(self):
```

Create authentication headers.

### test_benchmark_reflects_actual_configuration_performance()

```python
def test_benchmark_reflects_actual_configuration_performance(self, client, auth_headers):
```

Test that benchmarks reflect actual configuration loading performance.

### test_benchmark_validation_matches_real_validation()

```python
def test_benchmark_validation_matches_real_validation(self, client, auth_headers):
```

Test that validation benchmarks match real validation performance.
