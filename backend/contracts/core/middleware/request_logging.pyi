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
        ...

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
        ...
