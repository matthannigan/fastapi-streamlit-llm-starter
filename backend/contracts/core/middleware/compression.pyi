"""
Compression Middleware

## Overview

Production-grade middleware for handling compressed HTTP traffic. It supports
automatic request decompression and intelligent response compression using
multiple algorithms with content-aware decisions and size thresholds.

## Features

- **Request decompression**: Supports `gzip`, `deflate`, and `br` (Brotli)
- **Response compression**: Chooses the best algorithm from client
  `Accept-Encoding` preferences
- **Content-aware decisions**: Skips images, archives, and already-compressed
  media; prioritizes text and JSON payloads
- **Size thresholds**: Only compresses responses larger than a configurable
  minimum
- **Streaming support**: Optional ASGI-level streaming compression for large
  responses
- **Safety**: Falls back gracefully if a compression backend fails

## Configuration

Configured via `app.core.config.Settings` (see `backend/app/core/config.py`):

- `compression_enabled` (bool): Master toggle
- `compression_min_size` (int): Minimum size in bytes to compress (default 1024)
- `compression_level` (int): 1-9 quality/CPU tradeoff (default 6)
- `compression_algorithms` (list[str]): Preferred order, e.g. `['br','gzip','deflate']`
- `streaming_compression_enabled` (bool): Enable ASGI streaming middleware

## Headers

- Request: `Content-Encoding` is honored for decompression
- Response: Sets `Content-Encoding`, `Content-Length`, and adds
  `X-Original-Size` and `X-Compression-Ratio` for observability

## Usage

```python
from app.core.middleware.compression import CompressionMiddleware
from app.core.config import settings

app.add_middleware(CompressionMiddleware, settings=settings)
```

## Dependencies

- `fastapi`, `starlette`
- `brotli`, `gzip`, `zlib`

## Notes

Compression is applied only when it reduces payload size. Media types that are
usually already compressed are excluded to avoid wasted CPU cycles.
"""

import gzip
import zlib
import brotli
import logging
from typing import List, Dict, Any, Callable, cast
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import io
from app.core.config import Settings
from app.core.exceptions import ValidationError


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive compression middleware for requests and responses.
    
    Features:
    - Automatic request decompression (gzip, deflate, brotli)
    - Intelligent response compression based on content type and size
    - Configurable compression levels and algorithms
    - Content-type aware compression decisions
    - Performance optimized with size thresholds
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process request with compression handling.
        """
        ...

    async def __call__(self, scope, receive, send):
        """
        ASGI interface for handling request decompression.
        """
        ...


class StreamingCompressionMiddleware:
    """
    ASGI-level streaming compression middleware for large responses.
    
    This middleware compresses responses as they're being streamed,
    which is more memory-efficient for large responses.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def __call__(self, scope, receive, send):
        ...


class CompressionSettings:
    """
    Compression middleware configuration settings.
    """

    ...


def get_compression_stats(response: Response) -> Dict[str, Any]:
    """
    Get compression statistics from a response.
    """
    ...


def configure_compression_settings(settings: Settings) -> Dict[str, Any]:
    """
    Configure compression settings with validation.
    """
    ...
