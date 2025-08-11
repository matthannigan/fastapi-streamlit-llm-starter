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

**Important Note:** CORS IS true middleware. It uses FastAPI's standard `app.add_middleware(CORSMiddleware, ...)` function which integrates with Starlette's middleware system and follows the LIFO (Last-In, First-Out) execution order like all other middleware components. CORS middleware is added last in the setup process, which means it processes requests early and responses late in the middleware stack, allowing it to properly handle preflight requests and add appropriate CORS headers to all responses. We store it in `/backend/app/core/middleware/` along with other middleware for architectural consistency and unified middleware management.
