---
sidebar_label: request_size
---

# Request Size Limiting Middleware

  file_path: `backend/app/core/middleware/request_size.py`

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
