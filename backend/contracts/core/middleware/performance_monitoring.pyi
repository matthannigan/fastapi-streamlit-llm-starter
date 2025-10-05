"""
Performance Monitoring Middleware

## Overview

Collects detailed performance metrics per request with minimal overhead.
Captures timing and optional memory deltas, emits observability headers, and
integrates cleanly with external monitoring backends.

## Metrics

- **Timing**: Total request duration (ms)
- **Memory**: RSS delta per request (optional)
- **Logging**: Slow request warnings above a configurable threshold

## Configuration

Keys in `app.core.config.Settings`:

- `performance_monitoring_enabled` (bool)
- `slow_request_threshold` (int, ms)
- `memory_monitoring_enabled` (bool)
- `metrics_export_enabled` (bool)

## Response Headers

- `X-Response-Time`: Duration in milliseconds
- `X-Memory-Delta`: Bytes of RSS delta (when enabled)

## Usage

```python
from app.core.middleware.performance_monitoring import PerformanceMonitoringMiddleware
from app.core.config import settings

app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
```
"""

import logging
import time
from typing import Callable, Any
from starlette.types import ASGIApp
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import Settings


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Production-ready performance monitoring middleware for request timing and resource tracking.
    
    Provides comprehensive performance monitoring including high-precision request timing,
    memory usage tracking, slow request detection, and performance metrics collection.
    The middleware supports both real-time monitoring and historical performance analysis
    with configurable thresholds and graceful degradation when monitoring tools are unavailable.
    
    Attributes:
        settings (Settings): Application configuration for monitoring behavior
        slow_request_threshold (int): Threshold in milliseconds for slow request alerts
        memory_monitoring_enabled (bool): Whether to track memory usage deltas per request
    
    Public Methods:
        dispatch(request, call_next): Processes HTTP requests with performance monitoring
    
    State Management:
        - Thread-safe: Uses per-request state tracking without shared mutable state
        - Lightweight: Minimal performance overhead with optimized timing calculations
        - Graceful degradation: Continues operating when memory monitoring tools unavailable
        - Non-blocking: All monitoring operations are asynchronous and non-intrusive
    
    Usage:
        # Basic setup with default settings
        from app.core.middleware.performance_monitoring import PerformanceMonitoringMiddleware
        from app.core.config import create_settings
    
        settings = create_settings()
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
    
        # Configuration via settings
        settings.slow_request_threshold = 2000  # 2 second slow request threshold
        settings.memory_monitoring_enabled = True
    
    Monitoring Features:
        - High-precision request timing using perf_counter() with millisecond accuracy
        - Memory usage tracking before and after requests (RSS delta calculation)
        - Slow request detection with configurable threshold alerts
        - Performance metrics logging with request correlation IDs
        - Response headers injection for client-side performance monitoring
        - Error handling for monitoring tool failures without affecting requests
    
    Response Headers:
        - X-Response-Time: Request duration in milliseconds (e.g., "125.50ms")
        - X-Memory-Delta: Memory usage change in bytes (e.g., "1048576B")
    
    Configuration:
        Monitoring behavior controlled by application settings:
        - performance_monitoring_enabled: Global enable/disable toggle
        - slow_request_threshold: Threshold in milliseconds for slow request alerts
        - memory_monitoring_enabled: Whether to track memory usage per request
        - metrics_export_enabled: Enable external monitoring system integration
    
    Examples:
        >>> # Middleware automatically tracks all requests
        >>> # Fast endpoint response
        >>> response.headers['X-Response-Time']  # "25.75ms"
        >>> response.headers['X-Memory-Delta']   # "524288B"
        >>>
        >>> # Slow endpoint triggers warning logs
        >>> # Logs: "Slow request detected: POST /v1/process 2150.5ms [req_id: abc123]"
        >>> response.headers['X-Response-Time']  # "2150.50ms"
    
    Performance Characteristics:
        - Overhead: < 1ms additional latency per request
        - Memory: Minimal additional memory usage for timing data
        - Threading: No shared state, fully thread-safe
        - Compatibility: Works with all ASGI applications and middleware stacks
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize performance monitoring middleware with configuration.
        
        Creates middleware instance with performance tracking capabilities configured
        from application settings. Sets up thresholds for slow request detection,
        memory monitoring configuration, and other monitoring parameters.
        
        Args:
            app (ASGIApp): The ASGI application to wrap with performance monitoring
            settings (Settings): Application settings containing monitoring configuration:
                               - slow_request_threshold: milliseconds threshold for alerts
                               - memory_monitoring_enabled: boolean to enable memory tracking
                               - performance_monitoring_enabled: global enable/disable
        
        Returns:
            None: Constructor initializes middleware instance in-place
        
        Raises:
            ConfigurationError: If settings contain invalid monitoring configuration values
        
        Behavior:
            - Extracts monitoring configuration from provided settings
            - Sets default values for missing configuration options
            - Validates configuration parameter ranges and types
            - Prepares monitoring infrastructure for request processing
            - Configures memory monitoring tools if enabled
            - Sets up slow request detection thresholds
        
        Examples:
            >>> from fastapi import FastAPI
            >>> from app.core.config import create_settings
            >>> from app.core.middleware.performance_monitoring import PerformanceMonitoringMiddleware
            >>>
            >>> app = FastAPI()
            >>> settings = create_settings()
            >>> settings.slow_request_threshold = 1000  # 1 second threshold
            >>> settings.memory_monitoring_enabled = True
            >>>
            >>> middleware = PerformanceMonitoringMiddleware(app, settings)
            >>> app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        """
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with comprehensive performance monitoring.
        
        Wraps request processing with timing, memory tracking, and performance metrics
        collection. Monitors the complete request lifecycle from start to response,
        including memory usage changes, slow request detection, and performance logging.
        
        Args:
            request (Request): The incoming HTTP request to monitor
            call_next (Callable[[Request], Any]): The next middleware/handler in the ASGI chain
        
        Returns:
            Response: The HTTP response with performance monitoring headers added:
                     - X-Response-Time: Duration in milliseconds (e.g., "125.50ms")
                     - X-Memory-Delta: Memory usage change in bytes (e.g., "1048576B")
        
        Raises:
            None: This method always returns a Response, re-raising any exceptions
                  after logging performance metrics for failed requests
        
        Behavior:
            - Records request start time using high-precision perf_counter()
            - Captures initial memory usage if memory monitoring is enabled
            - Processes request through the ASGI chain via call_next
            - Calculates request duration and memory delta after response
            - Adds performance headers to response for client-side monitoring
            - Logs performance metrics with request correlation IDs
            - Detects and logs slow requests above the configured threshold
            - Handles memory monitoring tool failures gracefully
            - Logs performance data even when requests fail with exceptions
        
        Performance Monitoring:
            - Timing: Uses time.perf_counter() for nanosecond precision
            - Memory: Tracks RSS (Resident Set Size) memory deltas
            - Logging: Structured logging with request context for monitoring systems
            - Headers: Injects standardized headers for client-side performance analysis
            - Thresholds: Configurable slow request detection with warning logs
        
        Error Handling:
            - Memory monitoring failures don't affect request processing
            - Performance metrics logged for both successful and failed requests
            - Exceptions re-raised after performance logging to preserve error flow
            - Monitoring tool availability checked and handled gracefully
        
        Examples:
            >>> # Fast request processing
            >>> response = await middleware.dispatch(request, call_next)
            >>> response.headers['X-Response-Time']    # "25.75ms"
            >>> response.headers['X-Memory-Delta']     # "524288B"
            >>>
            >>> # Slow request triggers warning log
            >>> # Log entry: "Slow request detected: POST /api/process 2150.5ms [req_id: abc123]"
            >>> response.headers['X-Response-Time']    # "2150.50ms"
            >>>
            >>> # Request failure still logged for performance analysis
            >>> # Log entry: "Performance (failed): POST /api/process 1250.2m ValueError [req_id: def456]"
            >>> # Exception still raised to caller
        
        Configuration Impact:
            - slow_request_threshold: Determines which requests trigger slow request warnings
            - memory_monitoring_enabled: Controls whether memory deltas are tracked and reported
            - performance_monitoring_enabled: Global toggle for all monitoring features
        """
        ...
