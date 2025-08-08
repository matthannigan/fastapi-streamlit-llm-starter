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
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)


def setup_cors_middleware(app: FastAPI, settings: Settings) -> None:
    """
    Configure Cross-Origin Resource Sharing (CORS) middleware for the application.
    
    Sets up CORS middleware with production-ready security settings that allow
    controlled cross-origin access while preventing unauthorized requests. The
    configuration supports development and production environments with appropriate
    security controls.
    
    CORS Features:
        * Configurable allowed origins from settings
        * Support for credentials in cross-origin requests
        * All HTTP methods allowed for API flexibility
        * All headers allowed for maximum compatibility
        * Preflight request handling for complex requests
        * Security-conscious defaults with explicit configuration
    
    Args:
        app (FastAPI): The FastAPI application instance to configure
        settings (Settings): Application settings containing CORS configuration
            including allowed_origins list
    
    Configuration:
        The middleware uses the following settings:
        * settings.allowed_origins: List of allowed origin URLs
        * Credentials: Enabled to support authentication cookies/headers
        * Methods: All HTTP methods (*) for maximum API flexibility
        * Headers: All headers (*) for client compatibility
    
    Security Notes:
        * Origins are explicitly configured, not using wildcard in production
        * Credentials support requires specific origin configuration
        * Preflight requests are properly handled for complex CORS scenarios
        * Settings validation ensures only valid origins are configured
    
    Example:
        >>> setup_cors_middleware(app, settings)
        >>> # CORS middleware now configured with settings.allowed_origins
    
    Note:
        CORS middleware should be added last in the middleware stack to ensure
        it processes responses after all other middleware has completed. This
        is handled automatically by the setup_middleware() function.
    """
    logger.info(f"Setting up CORS middleware with origins: {settings.allowed_origins}")
    
    # Note: Type ignore comments are needed due to FastAPI/Starlette type inference
    # limitations with CORSMiddleware. The code functions correctly at runtime.
    app.add_middleware(
        CORSMiddleware,  # type: ignore[arg-type]
        allow_origins=settings.allowed_origins,  # type: ignore[call-arg]
        allow_credentials=True,  # type: ignore[call-arg]
        allow_methods=["*"],  # type: ignore[call-arg]
        allow_headers=["*"],  # type: ignore[call-arg]
    )