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
    Enhanced request size limiting with streaming validation.
    
    Features:
    - Per-endpoint size limits
    - Content-type specific limits
    - Streaming request body validation
    - Protection against DoS attacks
    - Detailed error responses
    - Configurable size limits
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
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
        """Determine the appropriate size limit for this request."""
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
        """Format size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"  # noqa: E231
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f}MB"  # noqa: E231
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"  # noqa: E231
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Process request with size validation."""
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
    ASGI-level request size limiting for maximum performance.
    
    This implementation works at the ASGI level for better performance
    and more granular control over request processing.
    """
    
    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):
        self.app = app
        self.max_size = max_size
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
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
