---
sidebar_label: test_performance_monitoring_middleware
---

# Comprehensive tests for Performance Monitoring middleware.

  file_path: `backend/tests.old/unit/core/middleware/test_performance_monitoring_middleware.py`

Tests cover request timing, memory monitoring, slow request detection,
performance headers, and metrics collection.

## TestPerformanceMonitoringMiddleware

Test Performance Monitoring middleware functionality.

### settings()

```python
def settings(self):
```

Test settings with performance monitoring configuration.

### app()

```python
def app(self, settings):
```

FastAPI app with performance monitoring middleware.

### test_middleware_initialization()

```python
def test_middleware_initialization(self, settings):
```

Test middleware initialization with settings.

### test_middleware_initialization_defaults()

```python
def test_middleware_initialization_defaults(self):
```

Test middleware initialization with default values.

### test_performance_headers_added()

```python
def test_performance_headers_added(self, app):
```

Test that performance headers are added to responses.

### test_memory_monitoring_headers()

```python
def test_memory_monitoring_headers(self, mock_psutil_process, app):
```

Test memory monitoring headers when enabled.

### test_memory_monitoring_disabled()

```python
def test_memory_monitoring_disabled(self, mock_psutil_process):
```

Test when memory monitoring is disabled.

### test_memory_monitoring_exception_handling()

```python
def test_memory_monitoring_exception_handling(self, mock_psutil_process, app):
```

Test graceful handling of psutil exceptions.

### test_slow_request_detection()

```python
def test_slow_request_detection(self, mock_logger, app):
```

Test slow request detection and logging.

### test_fast_request_debug_logging()

```python
def test_fast_request_debug_logging(self, mock_logger, app):
```

Test debug logging for fast requests.

### test_request_id_integration()

```python
def test_request_id_integration(self, app):
```

Test integration with request ID from request logging.

### test_error_request_performance_logging()

```python
def test_error_request_performance_logging(self, mock_logger, app):
```

Test performance logging for failed requests.

### test_performance_logging_extra_data()

```python
def test_performance_logging_extra_data(self, mock_logger, app):
```

Test that performance logs include structured extra data.

### test_memory_delta_logging()

```python
def test_memory_delta_logging(self, mock_logger, mock_psutil_process, app):
```

Test memory delta inclusion in performance logs.

### test_response_time_accuracy()

```python
def test_response_time_accuracy(self, app):
```

Test response time measurement accuracy.

### test_different_http_methods()

```python
def test_different_http_methods(self, app):
```

Test performance monitoring across different HTTP methods.

### test_slow_request_threshold_boundary()

```python
def test_slow_request_threshold_boundary(self, mock_logger):
```

Test slow request detection at threshold boundary.

### test_concurrent_requests_performance()

```python
def test_concurrent_requests_performance(self, app):
```

Test performance monitoring with concurrent requests.

### test_performance_header_format_validation()

```python
def test_performance_header_format_validation(self, app):
```

Test that performance headers have correct format.

### test_memory_delta_calculation()

```python
def test_memory_delta_calculation(self, mock_psutil_process, app):
```

Test memory delta calculation logic.
