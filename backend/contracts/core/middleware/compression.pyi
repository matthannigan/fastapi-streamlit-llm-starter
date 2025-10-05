"""
Compression Middleware

## Overview

Production-grade middleware for handling compressed HTTP traffic. It supports
automatic request decompression and intelligent response compression using
multiple algorithms with content-aware decisions and size thresholds.

## Features

- **Request decompression**: Supports `gzip`, `deflate`, and `br` (Brotli)
- **Response compression**: Chooses the best algorithm from client
  `Accept-Encoding` preferences
- **Content-aware decisions**: Skips images, archives, and already-compressed
  media; prioritizes text and JSON payloads
- **Size thresholds**: Only compresses responses larger than a configurable
  minimum
- **Streaming support**: Optional ASGI-level streaming compression for large
  responses
- **Safety**: Falls back gracefully if a compression backend fails

## Configuration

Configured via `app.core.config.Settings` (see `backend/app/core/config.py`):

- `compression_enabled` (bool): Master toggle
- `compression_min_size` (int): Minimum size in bytes to compress (default 1024)
- `compression_level` (int): 1-9 quality/CPU tradeoff (default 6)
- `compression_algorithms` (list[str]): Preferred order, e.g. `['br','gzip','deflate']`
- `streaming_compression_enabled` (bool): Enable ASGI streaming middleware

## Headers

- Request: `Content-Encoding` is honored for decompression
- Response: Sets `Content-Encoding`, `Content-Length`, and adds
  `X-Original-Size` and `X-Compression-Ratio` for observability

## Usage

```python
from app.core.middleware.compression import CompressionMiddleware
from app.core.config import settings

app.add_middleware(CompressionMiddleware, settings=settings)
```

## Dependencies

- `fastapi`, `starlette`
- `brotli`, `gzip`, `zlib`

## Notes

Compression is applied only when it reduces payload size. Media types that are
usually already compressed are excluded to avoid wasted CPU cycles.
"""

import gzip
import zlib
import brotli
import logging
from typing import List, Dict, Any, Callable, cast
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import io
from app.core.config import Settings
from app.core.exceptions import ValidationError


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Production-grade compression middleware with intelligent content-aware response compression and automatic request decompression.
    
    Provides comprehensive HTTP traffic compression with multiple algorithm support,
    content-type awareness, size thresholds, and graceful fallback mechanisms.
    Optimizes bandwidth usage while maintaining performance through intelligent
    compression decisions and streaming support for large responses.
    
    Attributes:
        settings (Settings): Application settings containing compression configuration
        min_response_size (int): Minimum response size in bytes to consider compression
        compression_level (int): Compression quality level (1-9, higher = better compression but slower)
        compression_enabled (bool): Master toggle for compression functionality
        compressible_types (set): Content types that should be compressed
        incompressible_types (set): Content types that should never be compressed
        compression_algorithms (dict): Available compression algorithms with their implementations
        decompression_algorithms (dict): Available decompression algorithms with their implementations
    
    Public Methods:
        dispatch(): Main middleware entry point for response compression processing
        __call__(): ASGI interface for request decompression and response handling
    
    State Management:
        - Compression decisions are stateless per request
        - Content-type preferences are pre-computed for performance
        - Algorithm availability is determined at initialization
        - Thread-safe through request-scoped processing
    
    Usage:
        # Basic setup with default settings
        from app.core.middleware.compression import CompressionMiddleware
        from app.core.config import settings
    
        app.add_middleware(CompressionMiddleware, settings=settings)
    
        # Configuration via settings:
        # compression_enabled = True
        # compression_min_size = 1024  # 1KB minimum
        # compression_level = 6        # 1-9 quality level
        # compression_algorithms = ['br', 'gzip', 'deflate']
    
        # Requests with compressed bodies are automatically decompressed:
        # POST /api/data with Content-Encoding: gzip → decompressed before reaching endpoint
    
        # Responses are compressed based on content type and size:
        # JSON responses > 1KB → compressed with client's preferred algorithm
    
    Compression Strategy:
        The middleware uses intelligent compression decisions:
        1. Checks if compression is enabled and response isn't already compressed
        2. Evaluates content type against compressible/incompressible lists
        3. Applies size thresholds (default: responses > 1KB)
        4. Selects best algorithm from client's Accept-Encoding header
        5. Only uses compression if it reduces payload size
    
    Algorithm Support:
        - Brotli (br): Best compression ratio, modern browser support
        - Gzip: Good compatibility, moderate compression
        - Deflate: Basic compression, universal support
        - Graceful fallback when preferred algorithm fails
    
    Response Headers Added:
        Content-Encoding: Compression algorithm used (br, gzip, deflate)
        Content-Length: Updated compressed payload size
        X-Original-Size: Original uncompressed payload size
        X-Compression-Ratio: Compression efficiency as decimal (0.0-1.0)
    
    Request Handling:
        - Automatically decompresses request bodies with Content-Encoding header
        - Supports gzip, deflate, and brotli request compression
        - Returns structured error for invalid compressed data
        - Updates Content-Length header after decompression
    
    Note:
        Compression is only applied when it reduces payload size. The middleware
        skips compression for images, videos, archives, and other content types
        that are typically already compressed to avoid wasting CPU cycles.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process request with compression handling.
        """
        ...

    async def __call__(self, scope, receive, send):
        """
        ASGI interface for handling request decompression.
        """
        ...


class StreamingCompressionMiddleware:
    """
    ASGI-level streaming compression middleware for large responses.
    
    This middleware compresses responses as they're being streamed,
    which is more memory-efficient for large responses.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def __call__(self, scope, receive, send):
        ...


class CompressionSettings:
    """
    Compression middleware configuration settings.
    """

    ...


def get_compression_stats(response: Response) -> Dict[str, Any]:
    """
    Extract compression statistics from a response processed by CompressionMiddleware.
    
    Analyzes response headers to determine compression effectiveness and provides
    detailed metrics for monitoring and optimization purposes.
    
    Args:
        response: FastAPI Response object that has been processed by
                 CompressionMiddleware with compression headers
    
    Returns:
        Dictionary containing compression statistics:
        - compressed (bool): Whether the response was compressed
        - algorithm (str): Compression algorithm used (br, gzip, deflate) or None
        - original_size (str): Original uncompressed size from X-Original-Size header
        - compressed_size (str): Final compressed size from Content-Length header
        - compression_ratio (str): Compression efficiency ratio from X-Compression-Ratio
        - savings_bytes (int): Bytes saved through compression (calculated)
        - savings_percent (float): Percentage savings through compression (calculated)
    
    Behavior:
            - Reads compression-related headers from the response
            - Calculates byte and percentage savings when size information available
            - Returns None or empty values for missing compression headers
            - Handles parsing errors gracefully for malformed header values
            - Provides consistent data structure for monitoring and analytics
    
        Examples:
            >>> # Compressed response
            >>> stats = get_compression_stats(compressed_response)
            >>> stats['compressed']
            True
            >>> stats['algorithm']
            'gzip'
            >>> stats['savings_bytes']
            512
    
            >>> # Uncompressed response
            >>> stats = get_compression_stats(uncompressed_response)
            >>> stats['compressed']
            False
            >>> stats['algorithm']
            None
    
            >>> # Response with detailed metrics
            >>> stats = get_compression_stats(response_with_headers)
            >>> stats['savings_percent']
            75.0
    """
    ...


def configure_compression_settings(settings: Settings) -> Dict[str, Any]:
    """
    Validate and configure compression settings with safe defaults and constraints.
    
    Processes raw compression settings from the application configuration,
    applies validation rules, enforces safe limits, and provides a clean
    configuration dictionary ready for use by compression middleware.
    
    Args:
        settings: Settings object containing compression configuration attributes
                 including compression_enabled, compression_min_size, compression_level,
                 and compression_algorithms
    
    Returns:
        Dictionary containing validated compression configuration:
        - enabled (bool): Whether compression is enabled
        - min_size (int): Minimum response size for compression (minimum 512 bytes)
        - level (int): Compression level (1-9, clamped to valid range)
        - algorithms (List[str]): Validated list of compression algorithms
    
    Behavior:
            - Applies safe minimum and maximum limits to all settings
            - Validates compression algorithms against supported options
            - Provides fallback to gzip if no valid algorithms are configured
            - Clamps compression level to valid range (1-9)
            - Ensures minimum size threshold prevents compressing tiny responses
            - Maintains backward compatibility with existing configuration patterns
    
        Examples:
            >>> # Valid configuration
            >>> config = configure_compression_settings(valid_settings)
            >>> config['enabled']
            True
            >>> config['level']
            6
            >>> 'gzip' in config['algorithms']
            True
    
            >>> # Configuration with invalid values
            >>> config = configure_compression_settings(settings_with_invalid_values)
            >>> config['level']  # Clamped to valid range
            9
            >>> config['min_size']  # Applied minimum threshold
            512
    
            >>> # Empty algorithms fallback
            >>> config = configure_compression_settings(settings_with_no_algorithms)
            >>> config['algorithms']
            ['gzip']
    """
    ...
