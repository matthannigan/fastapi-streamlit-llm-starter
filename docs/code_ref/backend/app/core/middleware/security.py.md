---
sidebar_label: security
---

# Security Middleware

  file_path: `backend/app/core/middleware/security.py`

## Overview

Adds essential HTTP security headers and performs lightweight request
validations to provide a strong baseline for API hardening. Designed to work
in tandem with upstream protections like WAF and rate limiting.

## Headers

## Automatically configures

- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`
- `Content-Security-Policy` (strict for APIs, relaxed for docs)
- `Referrer-Policy`
- `Permissions-Policy`

## Validation

- Enforces `Content-Length` limits
- Caps total request header count
- Applies URL length and basic pattern checks (lightweight)

## Configuration

From `app.core.config.Settings`:

- `security_headers_enabled` (bool)
- `max_request_size` (int)
- `max_headers_count` (int)
- `csp_policy` (optional override for API CSP)

## Usage

```python
from app.core.middleware.security import SecurityMiddleware
from app.core.config import settings

app.add_middleware(SecurityMiddleware, settings=settings)
```
