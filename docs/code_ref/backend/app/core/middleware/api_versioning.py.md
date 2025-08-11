---
sidebar_label: api_versioning
---

# API Versioning Middleware

  file_path: `backend/app/core/middleware/api_versioning.py`

## Overview

Robust API version detection and routing with support for URL prefix, headers,
query parameters, and Accept media types. Adds response headers with current
and supported versions, and can perform compatibility transformations.

Now includes a safe-by-default exemption for internal routes mounted at `/internal/*`
so that administrative endpoints are not rewritten with public API version prefixes.

## Detection Strategies

- **Path**: `/v1/`, `/v2/`, `/v1.5/`
- **Headers**: `X-API-Version`, `API-Version`, or custom via settings
- **Query**: `?version=1.0` or `?api_version=1.0`
- **Accept**: `application/vnd.api+json;version=2.0`

## Behavior

- Writes detected version and method to `request.state`
- Rejects unsupported versions with a stable JSON payload and
`X-API-Supported-Versions`/`X-API-Current-Version` headers
- Optionally rewrites paths to the expected version prefix
- Skips versioning for health-check paths (e.g., `/health`, `/readiness`)
- Skips versioning for internal API paths (e.g., `/internal/resilience/health`) to
prevent unintended rewrites like `/v1/internal/resilience/health`

## Configuration

Configured via `app.core.config.Settings` and helper settings in this module:

- `api_versioning_enabled`, `default_api_version`, `current_api_version`
- `min_api_version`, `max_api_version`, `api_supported_versions`
- `api_version_compatibility_enabled`, `api_version_header`
- `api_versioning_skip_internal` (bool, default: True)
- When True, requests whose path is `/internal` or starts with `/internal/`
bypass version detection and path rewriting

## Examples

```text
Request:  GET /internal/resilience/health
Before:   (could be rewritten to /v1/internal/resilience/health)
After:    Versioning bypassed; remains /internal/resilience/health
```

## Usage

```python
from app.core.middleware.api_versioning import APIVersioningMiddleware
from app.core.config import settings

app.add_middleware(APIVersioningMiddleware, settings=settings)
```
