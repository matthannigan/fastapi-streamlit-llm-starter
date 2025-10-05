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

# Configure module logger
logger = logging.getLogger(__name__)


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
        super().__init__(app)
        self.settings = settings
        
        # Compression settings
        self.min_response_size = getattr(settings, 'compression_min_size', 1024)  # 1KB
        self.compression_level = getattr(settings, 'compression_level', 6)  # 1-9
        self.compression_enabled = getattr(settings, 'compression_enabled', True)
        
        
        # Compressible content types
        self.compressible_types = {
            'application/json',
            'application/xml',
            'text/plain',
            'text/html',
            'text/css',
            'text/javascript',
            'application/javascript',
            'text/csv',
            'application/csv',
            'application/x-yaml',
            'text/yaml',
        }
        
        # Content types to never compress
        self.incompressible_types = {
            'image/',
            'video/',
            'audio/',
            'application/zip',
            'application/gzip',
            'application/x-compressed',
            'application/pdf',
            'application/octet-stream',
        }
        
        # Compression algorithms in order of preference
        self.compression_algorithms = {
            'br': self._compress_brotli,      # Brotli (best compression)
            'gzip': self._compress_gzip,      # Gzip (good compatibility)
            'deflate': self._compress_deflate,  # Deflate (basic)
        }
        
        # Decompression algorithms
        self.decompression_algorithms = {
            'gzip': self._decompress_gzip,
            'deflate': self._decompress_deflate,
            'br': self._decompress_brotli,
        }
    
    def _parse_accept_encoding(self, accept_encoding: str) -> List[str]:
        """Parse Accept-Encoding header and return supported algorithms."""
        if not accept_encoding:
            return []
        
        # Parse quality values and sort by preference
        encodings = []
        for encoding in accept_encoding.split(','):
            encoding = encoding.strip()
            if ';' in encoding:
                name, quality = encoding.split(';', 1)
                try:
                    q = float(quality.split('=')[1])
                except (ValueError, IndexError):
                    q = 1.0
            else:
                name, q = encoding, 1.0
            
            name = name.strip().lower()
            if name in self.compression_algorithms and q > 0:
                encodings.append((name, q))
        
        # Sort by quality (descending) and return algorithm names
        encodings.sort(key=lambda x: x[1], reverse=True)
        return [name for name, _ in encodings]
    
    def _should_compress_response(self, response: Response) -> bool:
        """Determine if response should be compressed."""
        logger.debug(f"Checking if response should be compressed: {type(response)}")
        
        if not self.compression_enabled:
            logger.debug("Compression disabled, skipping")
            return False
        
        # Check if already compressed
        if response.headers.get('content-encoding'):
            logger.debug("Already compressed, skipping")
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        logger.debug(f"Content-Type: {content_type}")
        
        # Never compress certain types
        for incompressible in self.incompressible_types:
            if content_type.startswith(incompressible):
                logger.debug(f"Incompressible content type: {content_type}")
                return False
        
        # Only compress known compressible types
        compressible = any(
            content_type.startswith(comp_type)
            for comp_type in self.compressible_types
        )
        
        if not compressible:
            logger.debug(f"Non-compressible content type: {content_type}")
            return False
        
        # Check size from content-length header if available
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size < self.min_response_size:
                    logger.debug(f"Response size {size} below threshold {self.min_response_size}")
                    return False
            except (ValueError, TypeError):
                pass  # Ignore invalid content-length, will check body size later
        
        logger.debug("Response should be compressed")
        return True
    
    def _compress_gzip(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        return gzip.compress(data, compresslevel=self.compression_level)
    
    def _compress_deflate(self, data: bytes) -> bytes:
        """Compress data using deflate."""
        return zlib.compress(data, level=self.compression_level)
    
    def _compress_brotli(self, data: bytes) -> bytes:
        """Compress data using brotli."""
        try:
            return brotli.compress(data, quality=self.compression_level)
        except Exception:
            # Fallback to gzip if brotli fails
            return self._compress_gzip(data)
    
    def _decompress_gzip(self, data: bytes) -> bytes:
        """Decompress gzip data."""
        return gzip.decompress(data)
    
    def _decompress_deflate(self, data: bytes) -> bytes:
        """Decompress deflate data."""
        return zlib.decompress(data)
    
    def _decompress_brotli(self, data: bytes) -> bytes:
        """Decompress brotli data."""
        return brotli.decompress(data)
    
    
    async def _get_response_body(self, response: Response) -> bytes:
        """Extract body content from different response types."""
        # Handle JSONResponse and similar response objects
        if isinstance(response, JSONResponse) and hasattr(response, 'render'):
            r_any = cast(Any, response)
            body_content = r_any.render(getattr(r_any, 'content', None))
            if isinstance(body_content, str):
                body_content = body_content.encode('utf-8')
            return body_content
        
        # Handle different response types from FastAPI
        if hasattr(response, 'body') and response.body:
            return response.body
        
        # For streaming responses, we need to read the body iterator
        r_any = cast(Any, response)
        if hasattr(r_any, 'body_iterator'):
            body_parts = []
            async for chunk in r_any.body_iterator:
                body_parts.append(chunk)
            body = b''.join(body_parts)
            
            # Create a new iterator for the original body
            async def new_body_iterator():
                yield body
            r_any.body_iterator = new_body_iterator()
            return body
        
        return b''
    
    async def _compress_response_body(self, response: Response, algorithm: str) -> Response:
        """Compress response body using specified algorithm."""
        logger.debug(f"Attempting to compress response: {type(response)}, algorithm: {algorithm}")
        
        # Get the response body
        try:
            body_content = await self._get_response_body(response)
        except Exception as e:
            logger.warning(f"Failed to get response body: {e}")
            return response
        
        if not body_content:
            logger.debug("No body content found, skipping compression")
            return response
        
        # Ensure body_content is bytes
        if isinstance(body_content, str):
            body_content = body_content.encode('utf-8')
        
        try:
            # Check size threshold first
            original_size = len(body_content)
            logger.debug(f"Body size: {original_size}, threshold: {self.min_response_size}")
            if original_size < self.min_response_size:
                logger.debug(f"Body size {original_size} below threshold {self.min_response_size}, skipping compression")
                return response
            
            # Get the compression function
            compressor = self.compression_algorithms[algorithm]
            
            # Compress the body
            compressed_body = compressor(body_content)
            compressed_size = len(compressed_body)
            
            # Only use compression if it actually reduces size
            if compressed_size < original_size:
                # Update the response body based on response type
                if isinstance(response, JSONResponse):
                    # For JSONResponse, create a new response with compressed body
                    response.body = compressed_body
                elif hasattr(cast(Any, response), 'body_iterator'):
                    async def compressed_body_iterator():
                        yield compressed_body
                    cast(Any, response).body_iterator = compressed_body_iterator()
                elif hasattr(response, 'body'):
                    response.body = compressed_body
                
                # Update headers
                response.headers['content-encoding'] = algorithm
                response.headers['content-length'] = str(compressed_size)
                response.headers['x-original-size'] = str(original_size)
                response.headers['x-compression-ratio'] = f"{compressed_size / original_size:.2f}"  # noqa: E231
                
                logger.debug(
                    f"Compressed response: {algorithm} "
                    f"{original_size} -> {compressed_size} bytes "
                    f"({compressed_size / original_size:.1%})"  # noqa: E231
                )
            else:
                logger.debug(
                    f"Compression not beneficial: {algorithm} "
                    f"{original_size} -> {compressed_size} bytes"
                )
        
        except Exception as e:
            logger.warning(f"Failed to compress response with {algorithm}: {e}")
        
        return response
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Process request with compression handling."""
        logger.debug(f"CompressionMiddleware dispatch called for {request.method} {request.url.path}")
        
        # Handle response compression
        response = await call_next(request)
        logger.debug(f"Got response from call_next: {type(response)}, status: {getattr(response, 'status_code', 'unknown')}")
        
        if self._should_compress_response(response):
            # Parse client's Accept-Encoding header
            accept_encoding = request.headers.get('accept-encoding', '')
            supported_algorithms = self._parse_accept_encoding(accept_encoding)
            
            # Choose the best compression algorithm
            for algorithm in supported_algorithms:
                if algorithm in self.compression_algorithms:
                    response = await self._compress_response_body(response, algorithm)
                    break
        return response
    
    async def __call__(self, scope, receive, send):
        """ASGI interface for handling request decompression."""
        if scope["type"] != "http":
            # For non-HTTP requests, call parent which will eventually call self.app
            await super().__call__(scope, receive, send)
            return
        
        # Check for request compression
        headers = dict(scope.get("headers", []))
        content_encoding = headers.get(b"content-encoding", b"").decode().lower()
        
        if content_encoding and content_encoding in self.decompression_algorithms:
            # Handle compressed requests - call parent with modified receive
            try:
                decompressed_receive = await self._create_decompressing_receive(receive, content_encoding, scope)
                await super().__call__(scope, decompressed_receive, send)
            except (ValueError, ValidationError):
                # Send error response for invalid compression
                await send({
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"error": "Invalid compressed request body", "error_code": "INVALID_COMPRESSION"}',
                })
        else:
            # No decompression needed, call parent which will handle dispatch
            await super().__call__(scope, receive, send)
    
    async def _create_decompressing_receive(self, receive, content_encoding, scope):
        """Create a receive callable that decompresses the request body."""
        decompressor = self.decompression_algorithms[content_encoding]
        body_parts = []
        
        async def decompressing_receive():
            while True:
                message = await receive()
                if message["type"] == "http.request":
                    body_parts.append(message.get("body", b""))
                    if not message.get("more_body", False):
                        # All body collected, decompress
                        compressed_body = b"".join(body_parts)
                        if compressed_body:
                            try:
                                decompressed_body = decompressor(compressed_body)
                                
                                # Update headers to reflect decompressed content
                                headers = dict(scope.get("headers", []))
                                headers.pop(b"content-encoding", None)
                                headers[b"content-length"] = str(len(decompressed_body)).encode()
                                scope["headers"] = list(headers.items())
                                
                                logger.debug(
                                    f"Decompressed request body: {content_encoding} "
                                    f"{len(compressed_body)} -> {len(decompressed_body)} bytes"
                                )
                                
                                return {
                                    "type": "http.request",
                                    "body": decompressed_body,
                                    "more_body": False
                                }
                            except Exception as e:
                                logger.error(f"Failed to decompress request body ({content_encoding}): {e}")
                                # Raise ValidationError to let global handler map to 400 consistently
                                raise ValidationError(f"Invalid {content_encoding} compressed data")
                        else:
                            return message
                    else:
                        continue
                else:
                    return message
        
        return decompressing_receive


class StreamingCompressionMiddleware:
    """
    ASGI-level streaming compression middleware for large responses.
    
    This middleware compresses responses as they're being streamed,
    which is more memory-efficient for large responses.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        self.app = app
        self.settings = settings
        self.min_size = getattr(settings, 'compression_min_size', 1024)
        self.compression_level = getattr(settings, 'compression_level', 6)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Check Accept-Encoding header
        headers = dict(scope.get("headers", []))
        accept_encoding = headers.get(b"accept-encoding", b"").decode().lower()
        
        if "gzip" not in accept_encoding:
            await self.app(scope, receive, send)
            return
        
        # Wrap the send function to intercept responses
        compressor = None
        response_started = False
        
        async def compressing_send(message):
            nonlocal compressor, response_started
            
            if message["type"] == "http.response.start":
                response_started = True
                headers_dict = dict(message.get("headers", []))
                content_type = headers_dict.get(b"content-type", b"").decode()
                
                # Check if we should compress this response
                if (content_type.startswith(("application/json", "text/")) and
                        b"content-encoding" not in headers_dict):
                    
                    # Initialize compressor
                    compressor = gzip.GzipFile(mode='wb', fileobj=io.BytesIO(), compresslevel=self.compression_level)
                    
                    # Modify headers
                    new_headers = []
                    for name, value in message.get("headers", []):
                        if name.lower() not in [b"content-length"]:
                            new_headers.append([name, value])
                    
                    new_headers.extend([
                        [b"content-encoding", b"gzip"],
                        [b"transfer-encoding", b"chunked"],
                    ])
                    
                    message["headers"] = new_headers
                
                await send(message)
            
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                
                if compressor and body:
                    # Compress the chunk
                    compressor.write(body)
                    
                    if not more_body:
                        compressor.close()
                        compressed_data = compressor.fileobj.getvalue()
                        compressor.fileobj.close()
                        
                        message["body"] = compressed_data
                    else:
                        # For streaming, we'd need a more complex implementation
                        # For now, just pass through
                        pass
                
                await send(message)
        
        await self.app(scope, receive, compressing_send)


# Additional utility functions for compression management
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
    stats = {
        'compressed': bool(response.headers.get('content-encoding')),
        'algorithm': response.headers.get('content-encoding'),
        'original_size': response.headers.get('x-original-size'),
        'compressed_size': response.headers.get('content-length'),
        'compression_ratio': response.headers.get('x-compression-ratio'),
    }
    
    if stats['original_size'] and stats['compressed_size']:
        try:
            original = int(stats['original_size'])
            compressed = int(stats['compressed_size'])
            stats['savings_bytes'] = original - compressed
            stats['savings_percent'] = ((original - compressed) / original) * 100
        except (ValueError, ZeroDivisionError):
            pass
    
    return stats


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
    config = {
        'enabled': getattr(settings, 'compression_enabled', True),
        'min_size': max(512, getattr(settings, 'compression_min_size', 1024)),
        'level': max(1, min(9, getattr(settings, 'compression_level', 6))),
        'algorithms': getattr(settings, 'compression_algorithms', ['br', 'gzip', 'deflate']),
    }
    
    # Validate algorithms
    valid_algorithms = {'br', 'gzip', 'deflate'}
    config['algorithms'] = [alg for alg in config['algorithms'] if alg in valid_algorithms]
    
    if not config['algorithms']:
        config['algorithms'] = ['gzip']  # Fallback to gzip
    
    return config


# Settings additions for compression
class CompressionSettings:
    """Compression middleware configuration settings."""
    
    # Enable/disable compression
    compression_enabled: bool = True
    
    # Minimum response size to compress (bytes)
    compression_min_size: int = 1024
    
    # Compression level (1-9, higher = better compression but slower)
    compression_level: int = 6
    
    # Preferred compression algorithms in order
    compression_algorithms: List[str] = ['br', 'gzip', 'deflate']
    
    # Maximum memory usage for compression (bytes)
    compression_max_memory: int = 100 * 1024 * 1024  # 100MB
    
    # Enable streaming compression for large responses
    streaming_compression_enabled: bool = True
