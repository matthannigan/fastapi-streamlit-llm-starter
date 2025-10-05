"""
Request Size Limiting Middleware

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
"""

import logging
from typing import Callable, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from app.core.config import Settings
from app.core.exceptions import RequestTooLargeError


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    HTTP request size limiting middleware with per-endpoint and content-type validation.
    
    Provides protection against DoS attacks and resource exhaustion by enforcing configurable
    request body size limits with streaming validation. Supports per-endpoint limits,
    content-type specific ceilings, and graceful error responses with detailed diagnostics.
    
    Attributes:
        settings (Settings): Application configuration object containing size limit preferences
        body_methods (set): HTTP methods that can contain request bodies requiring size validation
        default_limits (dict): Hierarchical size limit configuration for endpoints, content-types, and defaults
    
    Public Methods:
        dispatch(): Processes HTTP requests with comprehensive size validation and limiting
    
    State Management:
        - Stateless middleware with no persistent state between requests
        - Uses request receive callable wrapping for streaming validation
        - Maintains size limit configuration in memory from settings initialization
        - Tracks per-request body size during streaming validation
    
    Usage:
        # Basic middleware registration
        from app.core.middleware.request_size import RequestSizeLimitMiddleware
        from app.core.config import settings
    
        app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
    
        # Configuration via settings.request_size_limits
        # {
        #     'default': 10485760,  # 10MB
        #     'application/json': 5242880,  # 5MB for JSON
        #     '/v1/upload': 52428800  # 50MB for upload endpoint
        # }
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize request size limiting middleware with hierarchical limit configuration.
        
        Args:
            app (ASGIApp): The ASGI application to wrap with size validation functionality
            settings (Settings): Application settings containing size limit configuration:
                - request_size_limits (dict): Custom size limits for endpoints and content-types
                - max_request_size (int): Global default size limit in bytes
                - request_size_limiting_enabled (bool): Master switch for size limiting
        
        Behavior:
            - Configures HTTP methods that support request bodies (POST, PUT, PATCH)
            - Sets up hierarchical size limit defaults for different content types and endpoints
            - Merges custom limits from settings with default configuration
            - Prepares size limit lookup tables for efficient request validation
            - Initializes middleware chain with the wrapped ASGI application
        """
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with comprehensive size validation and DoS protection.
        
        Args:
            request (Request): The incoming HTTP request object with headers and body data
            call_next (Callable[[Request], Any]): The next middleware or route handler in the ASGI chain
        
        Returns:
            Response: HTTP response with size limit headers added, or error response if size exceeded
        
        Raises:
            RequestTooLargeError: When streaming request body exceeds configured size limits
        
        Behavior:
            - Skips size validation for HTTP methods that don't support request bodies
            - Determines appropriate size limit using hierarchical endpoint/content-type lookup
            - Validates Content-Length header immediately when present for fast rejection
            - Wraps request receive callable for streaming validation of chunked requests
            - Returns detailed error responses with size information and limit headers
            - Adds informational size limit headers to successful responses
            - Logs size limit violations for monitoring and debugging
            - Handles invalid Content-Length headers with appropriate error responses
        
        Examples:
            # Content-Length validation (fast path)
            # Request with Content-Length: 15000000 exceeds 10MB limit
            # Returns 413 with error details and limit headers
        
            # Streaming validation (chunked requests)
            # Monitors body chunks during receive() calls
            # Raises RequestTooLargeError when cumulative size exceeds limit
        
            # Successful request with limit headers
            # Response headers: X-Max-Request-Size: 10485760, X-Request-Size-Limit: 10.0MB
        """
        ...


class RequestTooLargeException(Exception):
    """
    Deprecated. Use RequestTooLargeError from app.core.exceptions instead.
    """

    ...


class ASGIRequestSizeLimitMiddleware:
    """
    High-performance ASGI-level request size limiting middleware.
    
    Alternative implementation that operates at the ASGI protocol level for maximum
    performance and granular control over request processing. Bypasses FastAPI middleware
    overhead for optimal throughput in high-load scenarios.
    
    Attributes:
        app (ASGIApp): The ASGI application to wrap with size validation
        max_size (int): Maximum request body size in bytes for all requests
    
    Public Methods:
        __call__(): ASGI application callable that processes requests with size validation
    
    State Management:
        - Stateless ASGI middleware with no persistent state between requests
        - Operates at protocol level for minimal overhead
        - Uses raw ASGI scope, receive, and send interfaces
        - Tracks per-request body size during streaming validation
    
    Usage:
        # Direct ASGI application wrapping
        from app.core.middleware.request_size import ASGIRequestSizeLimitMiddleware
    
        app = ASGIRequestSizeLimitMiddleware(
            your_asgi_app,
            max_size=10 * 1024 * 1024  # 10MB limit
        )
    
        # Integration with FastAPI
        # app = FastAPI()
        # sized_app = ASGIRequestSizeLimitMiddleware(app, max_size=10485760)
    """

    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):
        """
        Initialize ASGI-level size limiting middleware with maximum size configuration.
        
        Args:
            app (ASGIApp): The ASGI application to wrap with size validation functionality
            max_size (int): Maximum request body size in bytes (default: 10MB)
        
        Behavior:
            - Stores ASGI application reference for request processing
            - Configures global size limit for all HTTP requests
            - Prepares for protocol-level request interception and validation
            - Initializes middleware for high-performance request processing
        """
        ...

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """
        Process ASGI request with protocol-level size validation and DoS protection.
        
        Args:
            scope (Scope): ASGI connection scope containing connection metadata
            receive (Receive): ASGI receive callable for incoming message processing
            send (Send): ASGI send callable for outgoing message transmission
        
        Returns:
            None: Processes request asynchronously and sends responses directly
        
        Behavior:
            - Validates request type (HTTP only) and passes through non-HTTP requests
            - Checks HTTP method and skips validation for methods without request bodies
            - Validates Content-Length header immediately when present for fast rejection
            - Wraps receive callable for streaming validation of chunked transfer encoding
            - Sends 413 responses directly for oversized requests
            - Sends 400 responses for invalid Content-Length headers
            - Handles streaming validation with RequestTooLargeError for chunked requests
            - Provides minimal overhead validation for maximum performance
        """
        ...
