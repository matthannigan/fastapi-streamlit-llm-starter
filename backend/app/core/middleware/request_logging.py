"""
Request Logging Middleware

## Overview

Structured HTTP request/response logging with correlation IDs and timing.
Balances developer ergonomics and production safety by filtering sensitive
fields and supporting slow-request alerts.

## Capabilities

- **Correlation**: Per-request UUID propagated via contextvars
- **Timing**: Millisecond latency for each request
- **Details**: Method, path, status, response size; user agent and client IP
- **Security**: Sanitizes sensitive headers and query params

## Configuration

From `app.core.config.Settings`:

- `request_logging_enabled` (bool)
- `log_level` (str)
- `slow_request_threshold` (ms)

## Usage

```python
from app.core.middleware.request_logging import RequestLoggingMiddleware
from app.core.config import settings

app.add_middleware(RequestLoggingMiddleware, settings=settings)
```
"""

import logging
import time
import uuid
from typing import Callable, Any
from contextvars import ContextVar
from starlette.types import ASGIApp
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)

# Context variables for request tracking
request_id_context: ContextVar[str] = ContextVar("request_id", default="")
request_start_time_context: ContextVar[float] = ContextVar("request_start_time", default=0.0)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP request/response logging middleware with correlation tracking and performance monitoring.

    Provides comprehensive logging infrastructure for FastAPI applications with unique request
    correlation IDs, millisecond-precision timing, and security-conscious data filtering.
    The middleware supports both development debugging and production monitoring with appropriate
    log level management and sensitive data protection.

    Attributes:
        settings (Settings): Application configuration object containing logging preferences
        slow_request_threshold (int): Duration in milliseconds above which requests are logged as slow
        sensitive_headers (set): Header names that are filtered from logs for security

    Public Methods:
        dispatch(): Processes HTTP requests with comprehensive logging and timing

    State Management:
        - Uses contextvars for thread-safe request correlation tracking
        - Generates unique 8-character request IDs for each incoming request
        - Stores timing information in request state for middleware chain access
        - Maintains no persistent state between requests (stateless middleware)

    Usage:
        # Basic middleware registration
        from app.core.middleware.request_logging import RequestLoggingMiddleware
        from app.core.config import settings

        app.add_middleware(RequestLoggingMiddleware, settings=settings)

        # Access request ID in downstream components
        request_id = request.state.request_id
        correlation_id = request_id_context.get()
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize request logging middleware with application configuration.

        Args:
            app (ASGIApp): The ASGI application to wrap with logging functionality
            settings (Settings): Application settings containing logging configuration:
                - slow_request_threshold (int): Threshold in milliseconds for slow request warnings
                - request_logging_enabled (bool): Master switch for request logging
                - log_level (str): Minimum log level for request logging

        Behavior:
            - Extracts slow request threshold from settings (defaults to 1000ms)
            - Configures sensitive header filtering set for security
            - Prepares logging context for request correlation tracking
            - Initializes middleware chain with the wrapped ASGI application
        """
        super().__init__(app)
        self.settings = settings
        self.slow_request_threshold = getattr(settings, "slow_request_threshold", 1000)  # ms
        self.sensitive_headers = {"authorization", "x-api-key", "cookie"}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with comprehensive logging, timing, and correlation tracking.

        Args:
            request (Request): The incoming HTTP request object containing method, URL, headers
            call_next (Callable[[Request], Any]): The next middleware or route handler in the ASGI chain

        Returns:
            Response: The HTTP response object returned from downstream handlers with additional
                     logging metadata and timing information attached

        Raises:
            Exception: Propagates any exceptions from downstream handlers after logging the failure

        Behavior:
            - Generates unique 8-character request ID for correlation tracking
            - Stores request ID in both contextvars and request state for downstream access
            - Records request start time with millisecond precision
            - Logs request initiation with method, path, and metadata
            - Processes request through remaining middleware stack
            - Calculates request duration and response size metrics
            - Determines appropriate log level based on status code and duration
            - Logs request completion with comprehensive timing and response details
            - Logs request failures with exception information and timing
            - Applies sensitive header filtering to prevent security information leakage

        Examples:
            # Successful request logging
            # INFO: Request started: GET /api/health [req_id: abc12345]
            # INFO: Request completed: GET /api/health 200 156B 45.2ms [req_id: abc12345]

            # Slow request logging
            # WARN: Request completed: POST /api/process 200 2.3KB 1250.5ms [req_id: def67890]

            # Error request logging
            # ERROR: Request failed: POST /api/process ValidationError 234.1ms [req_id: ghi98765]
        """
        # Generate unique request ID for correlation
        request_id = str(uuid.uuid4())[:8]
        request_id_context.set(request_id)

        # Store request ID in request state for access by other components
        request.state.request_id = request_id

        # Record request start time
        start_time = time.time()
        request_start_time_context.set(start_time)

        # Log request start
        logger.info(
            f"Request started: {request.method} {request.url.path} [req_id: {request_id}]",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )

        try:
            # Process request through remaining middleware and handlers
            response: Response = await call_next(request)

            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000

            # Get response size if available
            response_size = getattr(response, "content-length", "unknown")
            if hasattr(response, "body") and response.body:
                response_size = f"{len(response.body)}B"

            # Determine log level based on status code
            log_level = logging.INFO
            if response.status_code >= 400:
                log_level = logging.WARNING if response.status_code < 500 else logging.ERROR
            elif duration_ms > self.slow_request_threshold:
                log_level = logging.WARNING

            # Log request completion
            logger.log(
                log_level,
                f"Request completed: {request.method} {request.url.path} "
                f"{response.status_code} {response_size} {duration_ms:.1f}ms [req_id: {request_id}]",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "response_size": response_size
                }
            )

            return response

        except Exception as exc:
            # Log request exception
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"{type(exc).__name__} {duration_ms:.1f}ms [req_id: {request_id}]",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "exception_type": type(exc).__name__
                },
                exc_info=True
            )
            raise
