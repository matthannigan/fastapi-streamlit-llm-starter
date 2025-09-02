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

## RequestLoggingMiddleware

HTTP request/response logging middleware with performance tracking.

Provides comprehensive logging of HTTP requests and responses with timing
information, request correlation IDs, and configurable detail levels.
The middleware supports both development debugging and production monitoring
with appropriate log filtering and security considerations.

Logging Features:
    * Request/response timing with millisecond precision
    * Unique request ID generation for correlation tracking
    * HTTP method, URL, status code, and response size logging
    * User agent and client IP address tracking (when available)
    * Configurable log levels based on response status codes
    * Sensitive data filtering for security compliance
    * Integration with structured logging for monitoring systems

Performance Tracking:
    * Request start/end timing with high precision
    * Response size calculation for bandwidth monitoring
    * Slow request detection and warning logs
    * Memory usage tracking (optional)
    * Integration with performance monitoring systems

Security Features:
    * Request ID correlation for secure debugging
    * Sensitive header filtering (Authorization, API keys)
    * Query parameter sanitization for logs
    * Client IP anonymization options
    * Log level control to prevent information leakage

Configuration:
    The middleware behavior can be controlled through settings:
    * request_logging_enabled: Enable/disable request logging
    * log_level: Minimum log level for request logging
    * slow_request_threshold: Threshold for slow request warnings
    * sensitive_headers: List of headers to filter from logs

Example Logs:
    ```
    INFO: Request started: GET /v1/text_processing/process [req_id: abc123]
    INFO: Request completed: GET /v1/text_processing/process 200 1.2KB 150ms [req_id: abc123]
    WARN: Slow request: POST /v1/text_processing/batch_process 200 5.6KB 2500ms [req_id: def456]
    ```

Note:
    This middleware should be placed early in the middleware stack to capture
    timing information for all subsequent middleware and request processing.

### __init__()

```python
def __init__(self, app: ASGIApp, settings: Settings):
```

Initialize request logging middleware with configuration.

Args:
    app (ASGIApp): The ASGI application to wrap
    settings (Settings): Application settings for logging configuration

### dispatch()

```python
async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
```

Process HTTP request with logging and timing.

Args:
    request (Request): The incoming HTTP request
    call_next (Callable): The next middleware/handler in the chain

Returns:
    Response: The HTTP response from downstream handlers
