---
sidebar_label: performance_monitoring
---

# Performance Monitoring Middleware

  file_path: `backend/app/core/middleware/performance_monitoring.py`

## Overview

Collects detailed performance metrics per request with minimal overhead.
Captures timing and optional memory deltas, emits observability headers, and
integrates cleanly with external monitoring backends.

## Metrics

- **Timing**: Total request duration (ms)
- **Memory**: RSS delta per request (optional)
- **Logging**: Slow request warnings above a configurable threshold

## Configuration

Keys in `app.core.config.Settings`:

- `performance_monitoring_enabled` (bool)
- `slow_request_threshold` (int, ms)
- `memory_monitoring_enabled` (bool)
- `metrics_export_enabled` (bool)

## Response Headers

- `X-Response-Time`: Duration in milliseconds
- `X-Memory-Delta`: Bytes of RSS delta (when enabled)

## Usage

```python
from app.core.middleware.performance_monitoring import PerformanceMonitoringMiddleware
from app.core.config import settings

app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
```

## PerformanceMonitoringMiddleware

Performance monitoring middleware for request timing and resource tracking.

Provides comprehensive performance monitoring including request timing,
memory usage tracking, and performance metrics collection. The middleware
supports both real-time monitoring and historical performance analysis
with integration capabilities for external monitoring systems.

Monitoring Features:
    * High-precision request timing with nanosecond accuracy
    * Memory usage tracking before and after requests
    * CPU usage monitoring (when available)
    * Slow request detection with configurable thresholds
    * Request concurrency tracking
    * Response size and bandwidth monitoring
    * Performance metrics aggregation
    * Integration hooks for external monitoring systems

Metrics Collected:
    * Request duration (total, processing, waiting)
    * Memory usage (RSS, heap, available)
    * CPU utilization during request processing
    * Request/response sizes for bandwidth analysis
    * Concurrent request counts
    * Error rates and status code distributions
    * Endpoint-specific performance patterns

Performance Analysis:
    * Real-time performance alerting for slow requests
    * Statistical analysis of response times
    * Memory leak detection through usage patterns
    * Bottleneck identification in request processing
    * Performance regression detection
    * Resource usage optimization recommendations

Configuration:
    Monitoring behavior can be configured through settings:
    * performance_monitoring_enabled: Enable/disable monitoring
    * slow_request_threshold: Threshold for slow request alerts
    * memory_monitoring_enabled: Enable memory usage tracking
    * metrics_export_enabled: Enable metrics export to external systems

Integration:
    The middleware can export metrics to monitoring systems:
    * Prometheus metrics export
    * StatsD metrics publishing
    * CloudWatch metrics integration
    * Custom metrics webhooks

Example Metrics:
    ```
    request_duration_seconds{method="POST", endpoint="/v1/text_processing/process"} 0.125
    request_memory_usage_bytes{method="POST", endpoint="/v1/text_processing/process"} 1048576
    slow_requests_total{method="POST", endpoint="/v1/text_processing/process"} 1
    ```

Note:
    Performance monitoring adds minimal overhead but should be configured
    appropriately for high-traffic production environments. Consider
    sampling strategies for very high request volumes.

### __init__()

```python
def __init__(self, app: ASGIApp, settings: Settings):
```

Initialize performance monitoring middleware.

Args:
    app (ASGIApp): The ASGI application to wrap
    settings (Settings): Application settings for monitoring configuration

### dispatch()

```python
async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
```

Process HTTP request with performance monitoring.

Args:
    request (Request): The incoming HTTP request
    call_next (Callable): The next middleware/handler in the chain

Returns:
    Response: The HTTP response with performance headers
