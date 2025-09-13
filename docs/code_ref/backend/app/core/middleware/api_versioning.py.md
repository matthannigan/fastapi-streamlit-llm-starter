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

## APIVersioningMiddleware

Comprehensive API versioning middleware with multiple strategies.

Features:
- URL path versioning (/v1/, /v2/)
- Header-based versioning (API-Version, Accept headers)
- Query parameter versioning (?version=1.0)
- Version deprecation warnings
- Backward compatibility routing
- Minimum/maximum version enforcement

### __init__()

```python
def __init__(self, app: ASGIApp, settings: Settings):
```

### dispatch()

```python
async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
```

Process request with API versioning.

## VersionCompatibilityMiddleware

Middleware for handling backward compatibility transformations.

This middleware can transform requests and responses to maintain
compatibility between different API versions.

### __init__()

```python
def __init__(self, app: ASGIApp, settings: Settings):
```

### dispatch()

```python
async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
```

Apply version compatibility transformations.

## APIVersioningSettings

API versioning configuration settings.

## APIVersionNotSupported

Exception raised when an unsupported API version is requested.

### __init__()

```python
def __init__(self, message: str, requested_version: str, supported_versions: list[str], current_version: str):
```

## get_api_version()

```python
def get_api_version(request: Request) -> str:
```

Get the API version for the current request.

## is_version_deprecated()

```python
def is_version_deprecated(request: Request) -> bool:
```

Check if the current API version is deprecated.

## get_version_sunset_date()

```python
def get_version_sunset_date(request: Request) -> Optional[str]:
```

Get the sunset date for the current API version.

## extract_version_from_url()

```python
def extract_version_from_url(path: str) -> Optional[str]:
```

Extract version from URL path (e.g., /v1/users -> 1.0).

## extract_version_from_header()

```python
def extract_version_from_header(request: Request, header_name: str) -> Optional[str]:
```

Extract version from request header.

## extract_version_from_accept()

```python
def extract_version_from_accept(request: Request) -> Optional[str]:
```

Extract version from Accept header (e.g., application/vnd.api+json;version=2.0).

## validate_api_version()

```python
def validate_api_version(version_str: str, supported_versions: list) -> bool:
```

Validate if the given version is supported.

## rewrite_path_for_version()

```python
def rewrite_path_for_version(path: str, target_version: str) -> str:
```

Rewrite path to include version prefix.

## add_version_headers()

```python
def add_version_headers(response: Response, current_version: str, supported_versions: list, header_name: str = 'X-API-Version') -> None:
```

Add version information to response headers.
