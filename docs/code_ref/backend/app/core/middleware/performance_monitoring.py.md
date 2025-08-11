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
