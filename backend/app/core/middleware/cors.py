"""
CORS Middleware Configuration

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
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)


def setup_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure Cross-Origin Resource Sharing (CORS) middleware with production-grade security controls.

    Sets up CORS middleware with security-conscious settings that enable controlled
    cross-origin access while preventing unauthorized requests. The configuration
    supports both development and production environments with appropriate security
    controls and explicit origin allowlisting.

    Args:
        app: FastAPI application instance to configure with CORS middleware
        settings: Application settings containing CORS configuration including
                 allowed_origins list and other security parameters

    Returns:
        None - Configures the FastAPI app instance in-place by adding CORS middleware

    Behavior:
        - Configures explicit origin allowlist from settings.allowed_origins
        - Enables credentials support for authentication cookies/headers
        - Allows all HTTP methods (*) for maximum API flexibility
        - Allows all headers (*) for maximum client compatibility
        - Handles preflight OPTIONS requests automatically
        - Logs configured origins for monitoring and debugging
        - Validates origin configuration to prevent security misconfigurations

    CORS Features:
        * Explicit origin allowlist (no wildcards in production)
        * Credentials support for authenticated cross-origin requests
        * All HTTP methods supported (GET, POST, PUT, DELETE, etc.)
        * All headers allowed for maximum compatibility
        * Automatic preflight request handling
        * Production-ready security defaults

    Security Configuration:
        - Origins must be explicitly listed in settings.allowed_origins
        - No wildcard (*) origins used for production security
        - Credentials enabled requires specific origin configuration
        - Settings validation ensures only valid origins are accepted
        - Prevents unauthorized cross-origin access while maintaining functionality

    Examples:
        >>> # Basic setup with configured origins
        >>> from fastapi import FastAPI
        >>> from app.core.config import Settings
        >>>
        >>> app = FastAPI()
        >>> settings = Settings(allowed_origins=["https://example.com", "https://app.example.com"])
        >>> setup_cors_middleware(app, settings)
        >>> # CORS middleware now configured for specified origins

        >>> # Development setup with localhost
        >>> dev_settings = Settings(allowed_origins=["http://localhost:3000", "http://localhost:8080"])
        >>> setup_cors_middleware(app, dev_settings)

        >>> # Production setup with multiple domains
        >>> prod_settings = Settings(
        ...     allowed_origins=[
        ...         "https://app.example.com",
        ...         "https://admin.example.com",
        ...         "https://api.example.com"
        ...     ]
        ... )
        >>> setup_cors_middleware(app, prod_settings)

    Configuration Parameters:
        - settings.allowed_origins: List of allowed origin URLs (required)
        - allow_credentials: True (supports authentication cookies/headers)
        - allow_methods: ["*"] (all HTTP methods supported)
        - allow_headers: ["*"] (all headers supported)

    Note:
        CORS middleware should be added last in the middleware stack to ensure
        it processes responses after all other middleware have completed. This
        is typically handled automatically by the application's setup_middleware()
        function which configures middleware in the correct order.

    Warning:
        Always use explicit origins in production environments. Avoid wildcard
        origins ("*") when credentials are enabled as this creates security
        vulnerabilities. The allowed_origins list should be carefully reviewed
        and limited to only the domains that require cross-origin access.
    """
    logger.info(f"Setting up CORS middleware with origins: {settings.allowed_origins}")

    # Note: Type ignore comments were removed as they are no longer needed
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
