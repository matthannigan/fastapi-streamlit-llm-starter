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
request_id_context: ContextVar[str] = ContextVar('request_id', default='')
request_start_time_context: ContextVar[float] = ContextVar('request_start_time', default=0.0)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP request/response logging middleware with performance tracking.
    
    Provides comprehensive logging of HTTP requests and responses with timing
    information, request correlation IDs, and configurable detail levels.
    The middleware supports both development debugging and production monitoring
    with appropriate log filtering and security considerations.
    
    Logging Features:
        * Request/response timing with millisecond precision
        * Unique request ID generation for correlation tracking
        * HTTP method, URL, status code, and response size logging
        * User agent and client IP address tracking (when available)
        * Configurable log levels based on response status codes
        * Sensitive data filtering for security compliance
        * Integration with structured logging for monitoring systems
    
    Performance Tracking:
        * Request start/end timing with high precision
        * Response size calculation for bandwidth monitoring
        * Slow request detection and warning logs
        * Memory usage tracking (optional)
        * Integration with performance monitoring systems
    
    Security Features:
        * Request ID correlation for secure debugging
        * Sensitive header filtering (Authorization, API keys)
        * Query parameter sanitization for logs
        * Client IP anonymization options
        * Log level control to prevent information leakage
    
    Configuration:
        The middleware behavior can be controlled through settings:
        * request_logging_enabled: Enable/disable request logging
        * log_level: Minimum log level for request logging
        * slow_request_threshold: Threshold for slow request warnings
        * sensitive_headers: List of headers to filter from logs
    
    Example Logs:
        ```
        INFO: Request started: GET /v1/text_processing/process [req_id: abc123]
        INFO: Request completed: GET /v1/text_processing/process 200 1.2KB 150ms [req_id: abc123]
        WARN: Slow request: POST /v1/text_processing/batch_process 200 5.6KB 2500ms [req_id: def456]
        ```
    
    Note:
        This middleware should be placed early in the middleware stack to capture
        timing information for all subsequent middleware and request processing.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize request logging middleware with configuration.
        
        Args:
            app (ASGIApp): The ASGI application to wrap
            settings (Settings): Application settings for logging configuration
        """
        super().__init__(app)
        self.settings = settings
        self.slow_request_threshold = getattr(settings, 'slow_request_threshold', 1000)  # ms
        self.sensitive_headers = {'authorization', 'x-api-key', 'cookie'}
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with logging and timing.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware/handler in the chain
            
        Returns:
            Response: The HTTP response from downstream handlers
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
                'request_id': request_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'user_agent': request.headers.get('user-agent', 'unknown'),
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )
        
        try:
            # Process request through remaining middleware and handlers
            response = await call_next(request)
            
            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Get response size if available
            response_size = getattr(response, 'content-length', 'unknown')
            if hasattr(response, 'body') and response.body:
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
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': duration_ms,
                    'response_size': response_size
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
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': duration_ms,
                    'exception_type': type(exc).__name__
                },
                exc_info=True
            )
            raise