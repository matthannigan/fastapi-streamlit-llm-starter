---
sidebar_label: cors
---

# CORS Middleware Configuration

  file_path: `backend/app/core/middleware/cors.py`

## Overview

Configures Cross-Origin Resource Sharing (CORS) for the FastAPI application to
allow controlled cross-origin access while maintaining production-grade
security. Uses explicit origin allowlists from settings.

## Behavior

- Allows credentials and all methods/headers by default
- Restricts origins to `settings.allowed_origins`
- Should be added last in the stack to properly process responses

## Usage

```python
from app.core.middleware.cors import setup_cors_middleware
from app.core.config import settings

setup_cors_middleware(app, settings)
```
