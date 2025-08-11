---
sidebar_label: compression
---

# Compression Middleware

  file_path: `backend/app/core/middleware/compression.py`

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
