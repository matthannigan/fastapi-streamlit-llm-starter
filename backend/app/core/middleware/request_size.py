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

# Configure module logger
logger = logging.getLogger(__name__)


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
        super().__init__(app)
        self.settings = settings

        # Methods that can have request bodies
        self.body_methods = {'POST', 'PUT', 'PATCH'}

        # Default size limits (in bytes) - fallback values
        default_limits = {
            # Global default
            'default': 10 * 1024 * 1024,  # 10MB

            # Content-type specific limits
            'application/json': 5 * 1024 * 1024,      # 5MB for JSON
            'text/plain': 1 * 1024 * 1024,            # 1MB for text
            'multipart/form-data': 50 * 1024 * 1024,  # 50MB for files
            'application/octet-stream': 100 * 1024 * 1024,  # 100MB for binary

            # Endpoint specific limits
            '/v1/text_processing/process': 2 * 1024 * 1024,      # 2MB
            '/v1/text_processing/batch_process': 20 * 1024 * 1024,  # 20MB
            '/v1/text_processing/upload': 50 * 1024 * 1024,  # 50MB
        }

        # Use custom settings if provided, otherwise use defaults
        custom_limits = getattr(settings, 'request_size_limits', {})
        if custom_limits:
            self.default_limits = custom_limits.copy()
        else:
            self.default_limits = default_limits.copy()
    
    def _get_size_limit(self, request: Request) -> int:
        """
        Determine the appropriate size limit for the current request using hierarchical lookup.

        Args:
            request (Request): The HTTP request object containing URL path and content-type headers

        Returns:
            int: Size limit in bytes for the request based on endpoint and content-type configuration

        Behavior:
            - Checks for endpoint-specific limits first (highest priority)
            - Falls back to content-type specific limits
            - Uses global default limit as final fallback
            - Returns limit in bytes for direct comparison with request sizes
        """
        # Check endpoint-specific limits first
        endpoint_limit = self.default_limits.get(request.url.path)
        if endpoint_limit:
            return endpoint_limit

        # Check content-type specific limits
        content_type = request.headers.get('content-type', '').split(';')[0].strip()
        content_type_limit = self.default_limits.get(content_type)
        if content_type_limit:
            return content_type_limit

        # Use default limit
        return self.default_limits['default']
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Convert size in bytes to human-readable format with appropriate units.

        Args:
            size_bytes (int): Size in bytes to format for display

        Returns:
            str: Human-readable size string with appropriate unit (B, KB, MB, GB)

        Behavior:
            - Uses bytes for values less than 1KB
            - Uses kilobytes with one decimal place for values less than 1MB
            - Uses megabytes with one decimal place for values less than 1GB
            - Uses gigabytes with one decimal place for larger values
        """
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"  # noqa: E231
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"  # noqa: E231
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"  # noqa: E231
    
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
        # Skip size checking for methods without bodies
        if request.method not in self.body_methods:
            return await call_next(request)
        
        # Get size limit for this request
        size_limit = self._get_size_limit(request)
        
        # Check Content-Length header first (if present)
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                declared_size = int(content_length)
                if declared_size > size_limit:
                    logger.warning(
                        f"Request size {self._format_size(declared_size)} exceeds limit "
                        f"{self._format_size(size_limit)} for {request.url.path}"
                    )
                    
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": "Request too large",
                            "error_code": "REQUEST_TOO_LARGE",
                            "max_size": self._format_size(size_limit),
                            "received_size": self._format_size(declared_size),
                            "endpoint": request.url.path
                        },
                        headers={
                            "X-Max-Request-Size": str(size_limit),
                            "X-Request-Size-Limit": self._format_size(size_limit)
                        }
                    )
            except ValueError:
                # Invalid Content-Length header
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "Invalid Content-Length header",
                        "error_code": "INVALID_CONTENT_LENGTH"
                    }
                )
        
        # For streaming requests or requests without Content-Length,
        # we need to validate during body reading
        original_receive = request.receive
        body_size = 0
        
        async def size_limiting_receive():
            nonlocal body_size
            message = await original_receive()
            
            if message["type"] == "http.request":
                body_chunk = message.get("body", b"")
                body_size += len(body_chunk)
                
                if body_size > size_limit:
                    # Raise app-level error for uniform handling
                    raise RequestTooLargeError(
                        f"Request body size {body_size} exceeds limit {size_limit}"
                    )
            
            return message
        
        # Replace the receive callable
        request._receive = size_limiting_receive
        
        try:
            response = await call_next(request)
            
            # Add informational headers about size limits
            response.headers["X-Max-Request-Size"] = str(size_limit)
            response.headers["X-Request-Size-Limit"] = self._format_size(size_limit)
            
            return response
            
        except RequestTooLargeError as e:
            logger.warning(f"Streaming request too large: {e}")
            
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error": "Request too large",
                    "error_code": "REQUEST_TOO_LARGE",
                    "max_size": self._format_size(size_limit),
                    "endpoint": request.url.path
                },
                headers={
                    "X-Max-Request-Size": str(size_limit),
                    "X-Request-Size-Limit": self._format_size(size_limit)
                }
            )


class RequestTooLargeException(Exception):
    """Deprecated. Use RequestTooLargeError from app.core.exceptions instead."""
    pass


# Alternative ASGI-level implementation for even better performance
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
        self.app = app
        self.max_size = max_size

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
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check if this is a method that can have a body
        method = scope.get("method", "GET")
        if method not in {"POST", "PUT", "PATCH"}:
            await self.app(scope, receive, send)
            return
        
        # Check Content-Length header
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        
        if content_length:
            try:
                size = int(content_length.decode())
                if size > self.max_size:
                    # Send 413 response
                    await send({
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [
                            [b"content-type", b"application/json"],
                            [b"x-max-request-size", str(self.max_size).encode()],
                        ],
                    })
                    await send({
                        "type": "http.response.body",
                        "body": b'{"error": "Request too large", "error_code": "REQUEST_TOO_LARGE"}',
                    })
                    return
            except (ValueError, UnicodeDecodeError):
                # Invalid Content-Length
                await send({
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Invalid Content-Length", "error_code": "INVALID_CONTENT_LENGTH"}',
                })
                return
        
        # For streaming validation, wrap the receive callable
        body_size = 0
        
        async def size_limiting_receive():
            nonlocal body_size
            message = await receive()
            
            if message["type"] == "http.request":
                body = message.get("body", b"")
                body_size += len(body)
                
                if body_size > self.max_size:
                    # Let the global handler or upstream middleware handle it
                    raise RequestTooLargeError("Request too large")
            
            return message
        
        response_started = False
        
        async def intercept_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)
        
        try:
            await self.app(scope, size_limiting_receive, intercept_send)
        except Exception as e:
            # Only send error response if we haven't started sending a response yet
            if not response_started:
                await send({
                    "type": "http.response.start",
                    "status": 413,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"x-max-request-size", str(self.max_size).encode()],
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Request too large", "error_code": "REQUEST_TOO_LARGE"}',
                })
