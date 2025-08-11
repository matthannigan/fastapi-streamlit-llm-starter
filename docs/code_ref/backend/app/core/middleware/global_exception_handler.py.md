---
sidebar_label: global_exception_handler
---

# Global Exception Handler

  file_path: `backend/app/core/middleware/global_exception_handler.py`

## Overview

Centralized, security-conscious exception handling for the FastAPI application.
Provides standardized JSON error responses, consistent HTTP status mapping, and
structured logging with request correlation for observability.

## Responsibilities

- **Consistency**: Uniform error payloads via `app.schemas.common.ErrorResponse`
- **Security**: Sanitized messages; no internal details leaked to clients
- **Mapping**: Stable HTTP status codes by exception category
- **Observability**: Correlated logs using request IDs

## HTTP Status Mapping

- `ApplicationError` → 400
- `InfrastructureError` → 502
- `TransientAIError` → 503
- `PermanentAIError` → 502
- Other uncaught exceptions → 500

## Special Cases

Maintains compatibility for API versioning errors by returning a specific
payload and headers (`X-API-Supported-Versions`, `X-API-Current-Version`).

## Usage

```python
from app.core.middleware.global_exception_handler import setup_global_exception_handler
from app.core.config import settings

setup_global_exception_handler(app, settings)
```

## Important Architecture Note

This module implements centralized exception handling using FastAPI's
@app.exception_handler() decorator system, NOT Starlette middleware.

While located in the middleware directory and functioning like middleware,
this uses FastAPI's exception handler system rather than Starlette's
BaseHTTPMiddleware. This means:

- It catches exceptions AFTER middleware processing
- It doesn't appear in app.middleware_stack
- It's configured via @app.exception_handler() decorators
- It runs when middleware or application code raises unhandled exceptions

This is architecturally correct for error handling but differs from
traditional middleware implementation patterns.
