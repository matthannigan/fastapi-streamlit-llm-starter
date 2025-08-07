"""
Request/Response Compression Middleware

Handles both incoming compressed requests and outgoing response compression
with multiple compression algorithms and intelligent compression decisions.
"""

import gzip
import zlib
import brotli
import logging
from typing import List, Dict, Any, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import io

from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)


class CompressionMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive compression middleware for requests and responses.
    
    Features:
    - Automatic request decompression (gzip, deflate, brotli)
    - Intelligent response compression based on content type and size
    - Configurable compression levels and algorithms
    - Content-type aware compression decisions
    - Performance optimized with size thresholds
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
        if not self.compression_enabled:
            return False
        
        # Check if already compressed
        if response.headers.get('content-encoding'):
            return False
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        
        # Never compress certain types
        for incompressible in self.incompressible_types:
            if content_type.startswith(incompressible):
                return False
        
        # Only compress known compressible types
        compressible = any(
            content_type.startswith(comp_type)
            for comp_type in self.compressible_types
        )
        
        if not compressible:
            return False
        
        # Check size threshold
        content_length = response.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size < self.min_response_size:
                    return False
            except ValueError:
                pass
        
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
    
    async def _decompress_request_body(self, request: Request) -> None:
        """Decompress request body if compressed."""
        content_encoding = request.headers.get('content-encoding', '').lower()
        
        if not content_encoding or content_encoding not in self.decompression_algorithms:
            return
        
        try:
            # Read the entire body
            body = await request.body()
            
            if not body:
                return
            
            # Decompress the body
            decompressor = self.decompression_algorithms[content_encoding]
            decompressed_body = decompressor(body)
            
            # Create a new receive callable with decompressed body
            async def decompressed_receive():
                return {
                    "type": "http.request",
                    "body": decompressed_body,
                    "more_body": False
                }
            
            # Replace the request's receive method
            request._receive = decompressed_receive
            
            # Update Content-Length header
            request.headers.__dict__['_list'] = [
                (name, value) for name, value in request.headers.items()
                if name.lower() not in ['content-encoding', 'content-length']
            ]
            request.headers.__dict__['_list'].append(
                ('content-length', str(len(decompressed_body)))
            )
            
            logger.debug(
                f"Decompressed request body: {content_encoding} "
                f"{len(body)} -> {len(decompressed_body)} bytes"
            )
            
        except Exception as e:
            logger.error(f"Failed to decompress request body ({content_encoding}): {e}")
            raise ValueError(f"Invalid {content_encoding} compressed data")
    
    def _compress_response_body(self, response: Response, algorithm: str) -> Response:
        """Compress response body using specified algorithm."""
        if not hasattr(response, 'body') or not response.body:
            return response
        
        try:
            # Get the compression function
            compressor = self.compression_algorithms[algorithm]
            
            # Compress the body
            original_size = len(response.body)
            compressed_body = compressor(response.body)
            compressed_size = len(compressed_body)
            
            # Only use compression if it actually reduces size
            if compressed_size < original_size:
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
        
        # 1. Handle request decompression
        try:
            await self._decompress_request_body(request)
        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid compressed request body",
                    "error_code": "INVALID_COMPRESSION",
                    "detail": str(e)
                }
            )
        
        # 2. Process the request
        response = await call_next(request)
        
        # 3. Handle response compression
        if self._should_compress_response(response):
            # Parse client's Accept-Encoding header
            accept_encoding = request.headers.get('accept-encoding', '')
            supported_algorithms = self._parse_accept_encoding(accept_encoding)
            
            # Choose the best compression algorithm
            for algorithm in supported_algorithms:
                if algorithm in self.compression_algorithms:
                    response = self._compress_response_body(response, algorithm)
                    break
        
        return response


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
    """Get compression statistics from a response."""
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
    """Configure compression settings with validation."""
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
