---
sidebar_label: request_logging
---

# Request Logging Middleware

  file_path: `backend/app/core/middleware/request_logging.py`

## Overview

Structured HTTP request/response logging with correlation IDs and timing.
Balances developer ergonomics and production safety by filtering sensitive
fields and supporting slow-request alerts.

## Capabilities

- **Correlation**: Per-request UUID propagated via contextvars
- **Timing**: Millisecond latency for each request
- **Details**: Method, path, status, response size; user agent and client IP
- **Security**: Sanitizes sensitive headers and query params

## Configuration

From `app.core.config.Settings`:

- `request_logging_enabled` (bool)
- `log_level` (str)
- `slow_request_threshold` (ms)

## Usage

```python
from app.core.middleware.request_logging import RequestLoggingMiddleware
from app.core.config import settings

app.add_middleware(RequestLoggingMiddleware, settings=settings)
```
