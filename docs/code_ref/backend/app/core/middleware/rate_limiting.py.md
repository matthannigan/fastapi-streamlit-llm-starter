---
sidebar_label: rate_limiting
---

# Rate Limiting Middleware (Redis-enabled)

  file_path: `backend/app/core/middleware/rate_limiting.py`

## Overview

Production-ready rate limiting with multiple strategies and optional Redis for
distributed enforcement. Provides granular controls per endpoint category and
graceful local fallbacks when Redis is unavailable.

## Features

- **Strategies**: Sliding window, fixed window, and token-bucket style behavior
- **Distributed**: Uses Redis when available; falls back to local in-memory
- **Granularity**: Per-endpoint classes (e.g., `health`, `auth`, `api_heavy`)
- **Headers**: Emits `X-RateLimit-*` and `Retry-After` on limit exceedance
- **Resilience**: Continues operating with local limiter if Redis errors occur

## Configuration

Provided via `app.core.config.Settings`:

- `rate_limiting_enabled` (bool): Master toggle
- `rate_limits` (dict): Rule set per classification (requests/window)
- `rate_limiting_skip_health` (bool): Bypass for health checks
- `redis_url` (str|None): Enable Redis-backed distributed limits when set

## Identification

Client identity is derived in priority order: API key, user ID, then client IP
(`X-Forwarded-For` or `X-Real-IP`, or connection address).

## Usage

```python
from app.core.middleware.rate_limiting import RateLimitMiddleware
from app.core.config import settings

app.add_middleware(RateLimitMiddleware, settings=settings)
```
