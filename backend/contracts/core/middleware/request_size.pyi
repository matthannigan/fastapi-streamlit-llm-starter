"""
Request Size Limiting Middleware

## Overview

Protects the API by enforcing configurable request body size limits with
streaming validation. Supports per-endpoint and content-type specific limits
to mitigate abuse and accidental oversized uploads.

## Features

- **Per-endpoint limits**: Configure strict caps on heavy routes
- **Content-type limits**: Different ceilings for JSON, multipart, etc.
- **Streaming enforcement**: Validates as body chunks arrive (no buffering)
- **Clear errors**: Returns 413 with informative headers and fields

## Configuration

Provided via `app.core.config.Settings`:

- `request_size_limiting_enabled` (bool): Master toggle
- `request_size_limits` (dict): Map of endpoint or content-type to byte limit
- `max_request_size` (int): Global default limit

## Usage

```python
from app.core.middleware.request_size import RequestSizeLimitMiddleware
from app.core.config import settings

app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
```
"""

import logging
from typing import Callable, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from app.core.config import Settings
from app.core.exceptions import RequestTooLargeError


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced request size limiting with streaming validation.
    
    Features:
    - Per-endpoint size limits
    - Content-type specific limits
    - Streaming request body validation
    - Protection against DoS attacks
    - Detailed error responses
    - Configurable size limits
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process request with size validation.
        """
        ...


class RequestTooLargeException(Exception):
    """
    Deprecated. Use RequestTooLargeError from app.core.exceptions instead.
    """

    ...


class ASGIRequestSizeLimitMiddleware:
    """
    ASGI-level request size limiting for maximum performance.
    
    This implementation works at the ASGI level for better performance
    and more granular control over request processing.
    """

    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):
        ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        ...
