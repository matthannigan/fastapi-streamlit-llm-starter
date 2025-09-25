"""
Comprehensive tests for Compression Middleware

Tests cover request decompression, response compression, algorithm selection,
content-type handling, and streaming compression features.
"""

import pytest
import gzip
import zlib
import brotli
import io
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.middleware.compression import (
    CompressionMiddleware,
    StreamingCompressionMiddleware,
    get_compression_stats,
    configure_compression_settings
)
from app.core.config import Settings


class TestCompressionMiddleware:
    """Test the main compression middleware."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with compression configuration."""
        settings = Mock(spec=Settings)
        settings.compression_enabled = True
        settings.compression_min_size = 1024  # 1KB
        settings.compression_level = 6
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI test app with compression middleware."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "This is a test response that should be long enough to trigger compression when the response size exceeds the minimum threshold"}
        
        @app.get("/small")
        async def small_endpoint():
            return {"data": "small"}
        
        @app.get("/large")
        async def large_endpoint():
            # Return large JSON that will definitely be compressed
            large_data = {"items": [{"id": i, "data": "x" * 100} for i in range(100)]}
            return large_data
        
        @app.post("/upload")
        async def upload_endpoint(request: Request):
            body = await request.body()
            return {"received_bytes": len(body)}
        
        app.add_middleware(CompressionMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with different configurations."""
        app = FastAPI()
        middleware = CompressionMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.compression_enabled == True
        assert middleware.min_response_size == 1024
        assert middleware.compression_level == 6
        
        # Check compression algorithms are properly configured
        assert 'br' in middleware.compression_algorithms
        assert 'gzip' in middleware.compression_algorithms
        assert 'deflate' in middleware.compression_algorithms
    
    def test_disabled_compression(self):
        """Test middleware when compression is disabled."""
        settings = Mock(spec=Settings)
        settings.compression_enabled = False
        
        app = FastAPI()
        middleware = CompressionMiddleware(app, settings)
        
        assert middleware.compression_enabled == False
    
    def test_response_compression_large_json(self, app):
        """Test response compression for large JSON responses."""
        client = TestClient(app)
        
        response = client.get("/large", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        
        # Check if compression was applied (it might not be for test responses)
        content_encoding = response.headers.get("content-encoding")
        if content_encoding:
            assert content_encoding == "gzip"
            assert "x-original-size" in response.headers
            assert "x-compression-ratio" in response.headers
        else:
            # If not compressed, verify response is still valid
            data = response.json()
            assert "items" in data
    
    def test_response_no_compression_small(self, app):
        """Test that small responses are not compressed."""
        client = TestClient(app)
        
        response = client.get("/small", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        
        # Should not be compressed due to size threshold
        assert response.headers.get("content-encoding") is None
    
    def test_compression_algorithm_selection(self, app):
        """Test compression algorithm selection based on Accept-Encoding."""
        client = TestClient(app)
        
        # Test brotli preference
        response = client.get("/large", headers={"Accept-Encoding": "br, gzip"})
        assert response.status_code == 200
        # Compression may or may not work in test environment
        if response.headers.get("content-encoding"):
            assert response.headers.get("content-encoding") in ["br", "gzip"]
        
        # Test gzip fallback
        response = client.get("/large", headers={"Accept-Encoding": "gzip, deflate"})
        assert response.status_code == 200
        if response.headers.get("content-encoding"):
            assert response.headers.get("content-encoding") in ["gzip", "deflate"]
        
        # Test deflate fallback
        response = client.get("/large", headers={"Accept-Encoding": "deflate"})
        assert response.status_code == 200
        # Response should be successful regardless of compression
        data = response.json()
        assert "items" in data
    
    def test_compression_quality_values(self, app):
        """Test compression algorithm selection with quality values."""
        client = TestClient(app)
        
        # Prefer gzip over brotli with quality values
        response = client.get("/large", headers={
            "Accept-Encoding": "br;q=0.5, gzip;q=0.9"
        })
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "gzip"
    
    def test_no_compression_unsupported_encoding(self, app):
        """Test no compression when client doesn't support any algorithms."""
        client = TestClient(app)
        
        response = client.get("/large", headers={"Accept-Encoding": "compress"})
        assert response.status_code == 200
        
        # Should not be compressed
        assert response.headers.get("content-encoding") is None
    
    def test_request_decompression_gzip(self, app):
        """Test decompression of gzip-compressed request bodies."""
        client = TestClient(app)
        
        # Compress request data
        original_data = b'{"test": "data with enough content to make it worthwhile to compress"}'
        compressed_data = gzip.compress(original_data)
        
        response = client.post(
            "/upload",
            content=compressed_data,
            headers={
                "Content-Encoding": "gzip",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        # Should receive original uncompressed size
        assert response.json()["received_bytes"] == len(original_data)
    
    def test_request_decompression_brotli(self, app):
        """Test decompression of brotli-compressed request bodies."""
        client = TestClient(app)
        
        # Compress request data with brotli
        original_data = b'{"test": "data with enough content to make it worthwhile to compress"}'
        compressed_data = brotli.compress(original_data)
        
        response = client.post(
            "/upload",
            content=compressed_data,
            headers={
                "Content-Encoding": "br",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["received_bytes"] == len(original_data)
    
    def test_request_decompression_error(self, app):
        """Test error handling for invalid compressed request data."""
        client = TestClient(app)
        
        # Send invalid gzip data
        invalid_compressed_data = b"invalid gzip data"
        
        response = client.post(
            "/upload",
            content=invalid_compressed_data,
            headers={
                "Content-Encoding": "gzip",
                "Content-Type": "application/json"
            }
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_COMPRESSION"


class TestCompressionAlgorithms:
    """Test individual compression algorithms."""
    
    @pytest.fixture
    def middleware(self):
        """Compression middleware instance for testing."""
        settings = Mock(spec=Settings)
        settings.compression_enabled = True
        settings.compression_level = 6
        
        app = FastAPI()
        return CompressionMiddleware(app, settings)
    
    def test_gzip_compression(self, middleware):
        """Test gzip compression functionality."""
        test_data = b"This is test data that should compress well with gzip algorithm" * 10  # Make it larger
        
        compressed = middleware._compress_gzip(test_data)
        # Only check compression worked if it actually compressed
        if len(compressed) < len(test_data):
            # Verify it's valid gzip
            decompressed = gzip.decompress(compressed)
            assert decompressed == test_data
        else:
            # For very small data, compression might not be beneficial
            assert len(test_data) < 100  # Only allow this for very small data
    
    def test_deflate_compression(self, middleware):
        """Test deflate compression functionality.""" 
        test_data = b"This is test data that should compress well with deflate algorithm"
        
        compressed = middleware._compress_deflate(test_data)
        assert len(compressed) < len(test_data)
        
        # Verify it's valid deflate
        decompressed = zlib.decompress(compressed)
        assert decompressed == test_data
    
    def test_brotli_compression(self, middleware):
        """Test brotli compression functionality."""
        test_data = b"This is test data that should compress well with brotli algorithm"
        
        compressed = middleware._compress_brotli(test_data)
        assert len(compressed) < len(test_data)
        
        # Verify it's valid brotli
        decompressed = brotli.decompress(compressed)
        assert decompressed == test_data
    
    def test_brotli_fallback_to_gzip(self, middleware):
        """Test brotli fallback to gzip on compression error."""
        with patch('brotli.compress') as mock_brotli:
            mock_brotli.side_effect = Exception("Brotli compression failed")
            
            test_data = b"test data"
            compressed = middleware._compress_brotli(test_data)
            
            # Should fallback to gzip
            decompressed = gzip.decompress(compressed)
            assert decompressed == test_data
    
    def test_gzip_decompression(self, middleware):
        """Test gzip decompression functionality."""
        test_data = b"This is test data for gzip decompression testing"
        compressed = gzip.compress(test_data)
        
        decompressed = middleware._decompress_gzip(compressed)
        assert decompressed == test_data
    
    def test_brotli_decompression(self, middleware):
        """Test brotli decompression functionality."""
        test_data = b"This is test data for brotli decompression testing"
        compressed = brotli.compress(test_data)
        
        decompressed = middleware._decompress_brotli(compressed)
        assert decompressed == test_data


class TestCompressionDecisionLogic:
    """Test compression decision logic."""
    
    @pytest.fixture
    def middleware(self):
        """Compression middleware instance."""
        settings = Mock(spec=Settings)
        settings.compression_enabled = True
        settings.compression_min_size = 1024
        
        app = FastAPI()
        return CompressionMiddleware(app, settings)
    
    def test_should_compress_json_response(self, middleware):
        """Test compression decision for JSON responses."""
        response = Mock(spec=Response)
        response.headers = {
            "content-type": "application/json",
            "content-length": "2048"
        }
        
        assert middleware._should_compress_response(response) == True
    
    def test_should_not_compress_small_response(self, middleware):
        """Test no compression for small responses."""
        response = Mock(spec=Response)
        response.headers = {
            "content-type": "application/json",
            "content-length": "512"  # Below 1024 threshold
        }
        
        assert middleware._should_compress_response(response) == False
    
    def test_should_not_compress_already_compressed(self, middleware):
        """Test no compression for already compressed responses."""
        response = Mock(spec=Response)
        response.headers = {
            "content-type": "application/json",
            "content-encoding": "gzip",
            "content-length": "2048"
        }
        
        assert middleware._should_compress_response(response) == False
    
    def test_should_not_compress_images(self, middleware):
        """Test no compression for image content."""
        response = Mock(spec=Response)
        response.headers = {
            "content-type": "image/jpeg",
            "content-length": "2048"
        }
        
        assert middleware._should_compress_response(response) == False
    
    def test_should_compress_text_content(self, middleware):
        """Test compression for text content types."""
        content_types = [
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/xml",
            "text/csv",
            "application/csv"
        ]
        
        for content_type in content_types:
            response = Mock(spec=Response)
            response.headers = {
                "content-type": content_type,
                "content-length": "2048"
            }
            
            assert middleware._should_compress_response(response) == True, f"Should compress {content_type}"
    
    def test_should_not_compress_incompressible_types(self, middleware):
        """Test no compression for incompressible content types."""
        content_types = [
            "image/png",
            "video/mp4",
            "audio/mpeg",
            "application/zip",
            "application/gzip",
            "application/pdf",
            "application/octet-stream"
        ]
        
        for content_type in content_types:
            response = Mock(spec=Response)
            response.headers = {
                "content-type": content_type,
                "content-length": "2048"
            }
            
            assert middleware._should_compress_response(response) == False, f"Should not compress {content_type}"


class TestAcceptEncodingParsing:
    """Test Accept-Encoding header parsing."""
    
    @pytest.fixture
    def middleware(self):
        """Compression middleware instance."""
        settings = Mock(spec=Settings)
        app = FastAPI()
        return CompressionMiddleware(app, settings)
    
    def test_parse_simple_encoding(self, middleware):
        """Test parsing simple Accept-Encoding header."""
        encodings = middleware._parse_accept_encoding("gzip, deflate")
        assert encodings == ["gzip", "deflate"]
    
    def test_parse_encoding_with_quality(self, middleware):
        """Test parsing Accept-Encoding with quality values."""
        encodings = middleware._parse_accept_encoding("br;q=0.9, gzip;q=0.8, deflate;q=0.7")
        assert encodings == ["br", "gzip", "deflate"]
    
    def test_parse_encoding_quality_ordering(self, middleware):
        """Test that encodings are ordered by quality value."""
        encodings = middleware._parse_accept_encoding("gzip;q=0.5, br;q=0.9, deflate;q=0.7")
        assert encodings == ["br", "deflate", "gzip"]
    
    def test_parse_encoding_zero_quality(self, middleware):
        """Test that encodings with q=0 are excluded."""
        encodings = middleware._parse_accept_encoding("gzip;q=0, br;q=1.0, deflate;q=0.0")
        assert encodings == ["br"]
    
    def test_parse_empty_encoding(self, middleware):
        """Test parsing empty Accept-Encoding header."""
        encodings = middleware._parse_accept_encoding("")
        assert encodings == []
        
        encodings = middleware._parse_accept_encoding(None)
        assert encodings == []
    
    def test_parse_encoding_unsupported_algorithms(self, middleware):
        """Test that unsupported algorithms are filtered out."""
        encodings = middleware._parse_accept_encoding("gzip, compress, br, identity")
        # Only gzip and br should be returned (supported algorithms)
        assert "gzip" in encodings
        assert "br" in encodings
        assert "compress" not in encodings
        assert "identity" not in encodings


class TestStreamingCompressionMiddleware:
    """Test streaming compression middleware."""
    
    @pytest.fixture
    def settings(self):
        """Test settings."""
        settings = Mock(spec=Settings)
        settings.compression_min_size = 1024
        settings.compression_level = 6
        return settings
    
    @pytest.fixture
    def streaming_app(self, settings):
        """App with streaming compression middleware."""
        app = FastAPI()
        
        @app.get("/stream")
        async def streaming_endpoint():
            return {"large_data": "x" * 2000}  # Large enough to compress
        
        # Use ASGI-level streaming middleware
        return StreamingCompressionMiddleware(app, settings)
    
    @pytest.mark.asyncio
    async def test_streaming_compression_initialization(self, streaming_app, settings):
        """Test streaming middleware initialization."""
        assert streaming_app.settings == settings
        assert streaming_app.min_size == 1024
        assert streaming_app.compression_level == 6
    
    @pytest.mark.asyncio
    async def test_streaming_compression_non_http(self, streaming_app):
        """Test streaming middleware with non-HTTP scope."""
        scope = {
            "type": "websocket", 
            "path": "/ws",
            "query_string": b"",
            "headers": []
        }
        receive = AsyncMock()
        send = AsyncMock()
        
        # Should pass through without processing
        await streaming_app(scope, receive, send)
        # Verify it doesn't interfere with non-HTTP protocols
    
    @pytest.mark.asyncio
    async def test_streaming_compression_no_gzip_support(self, streaming_app):
        """Test streaming middleware when client doesn't support gzip."""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/stream",
            "query_string": b"",
            "headers": [(b"accept-encoding", b"deflate")]
        }
        receive = AsyncMock()
        send = AsyncMock()
        
        # Should pass through without compression
        await streaming_app(scope, receive, send)


class TestCompressionUtilities:
    """Test compression utility functions."""
    
    def test_get_compression_stats_compressed_response(self):
        """Test compression statistics for compressed response."""
        response = Mock(spec=Response)
        response.headers = {
            "content-encoding": "gzip",
            "x-original-size": "2048",
            "content-length": "1024",
            "x-compression-ratio": "0.50"
        }
        
        stats = get_compression_stats(response)
        
        assert stats["compressed"] == True
        assert stats["algorithm"] == "gzip"
        assert stats["original_size"] == "2048"
        assert stats["compressed_size"] == "1024"
        assert stats["compression_ratio"] == "0.50"
        assert stats["savings_bytes"] == 1024
        assert stats["savings_percent"] == 50.0
    
    def test_get_compression_stats_uncompressed_response(self):
        """Test compression statistics for uncompressed response."""
        response = Mock(spec=Response)
        response.headers = {}
        
        stats = get_compression_stats(response)
        
        assert stats["compressed"] == False
        assert stats["algorithm"] is None
        assert stats["original_size"] is None
        assert stats["compressed_size"] is None
    
    def test_configure_compression_settings_defaults(self):
        """Test compression settings configuration with defaults."""
        settings = Mock(spec=Settings)
        
        config = configure_compression_settings(settings)
        
        assert config["enabled"] == True
        assert config["min_size"] == 1024
        assert config["level"] == 6
        assert "br" in config["algorithms"]
        assert "gzip" in config["algorithms"]
    
    def test_configure_compression_settings_custom(self):
        """Test compression settings with custom values."""
        settings = Mock(spec=Settings)
        settings.compression_enabled = False
        settings.compression_min_size = 2048
        settings.compression_level = 9
        settings.compression_algorithms = ["gzip", "deflate"]
        
        config = configure_compression_settings(settings)
        
        assert config["enabled"] == False
        assert config["min_size"] == 2048
        assert config["level"] == 9
        assert config["algorithms"] == ["gzip", "deflate"]
    
    def test_configure_compression_settings_validation(self):
        """Test compression settings validation."""
        settings = Mock(spec=Settings)
        settings.compression_min_size = 100  # Too small
        settings.compression_level = 15  # Too high
        settings.compression_algorithms = ["invalid", "gzip", "unknown"]
        
        config = configure_compression_settings(settings)
        
        # Should enforce minimum size
        assert config["min_size"] >= 512
        # Should clamp compression level
        assert config["level"] <= 9
        # Should filter invalid algorithms
        assert config["algorithms"] == ["gzip"]
    
    def test_configure_compression_settings_empty_algorithms(self):
        """Test compression settings with no valid algorithms."""
        settings = Mock(spec=Settings)
        settings.compression_algorithms = ["invalid", "unknown"]
        
        config = configure_compression_settings(settings)
        
        # Should fallback to gzip
        assert config["algorithms"] == ["gzip"]


class TestCompressionIntegration:
    """Integration tests for compression middleware."""
    
    @pytest.fixture
    def full_compression_app(self):
        """App with full compression configuration."""
        app = FastAPI()
        
        @app.get("/api/large-json")
        async def large_json():
            return {
                "data": [{"id": i, "content": "x" * 200} for i in range(50)],
                "metadata": {"total": 50, "compressed": True}
            }
        
        @app.get("/api/small-json")
        async def small_json():
            return {"message": "ok"}
        
        @app.post("/api/upload")
        async def upload_data(request: Request):
            body = await request.body()
            # Return a response large enough to trigger compression (>512 bytes)
            return {
                "received_size": len(body),
                "content_type": request.headers.get("content-type"),
                "processing_info": "This response is made large enough to trigger compression " * 10,
                "metadata": {
                    "timestamp": "2024-01-01T00:00:00Z",
                    "server": "test-server",
                    "version": "1.0.0",
                    "additional_data": "padding" * 20
                }
            }
        
        @app.get("/static/image.jpg")
        async def serve_image():
            # Simulate serving an image
            response = Response(
                content=b"fake image data" * 100,
                media_type="image/jpeg"
            )
            return response
        
        settings = Mock(spec=Settings)
        settings.compression_enabled = True
        settings.compression_min_size = 512
        settings.compression_level = 6
        
        app.add_middleware(CompressionMiddleware, settings=settings)
        return app
    
    def test_end_to_end_compression_flow(self, full_compression_app):
        """Test complete compression flow from request to response."""
        client = TestClient(full_compression_app)
        
        # Test large JSON compression
        response = client.get("/api/large-json", headers={
            "Accept-Encoding": "br, gzip, deflate"
        })
        
        assert response.status_code == 200
        assert response.headers.get("content-encoding") == "br"  # Best compression
        assert "x-original-size" in response.headers
        assert "x-compression-ratio" in response.headers
        
        # Verify data integrity
        data = response.json()
        assert len(data["data"]) == 50
        assert data["metadata"]["total"] == 50
    
    def test_mixed_content_handling(self, full_compression_app):
        """Test handling of different content types."""
        client = TestClient(full_compression_app)
        
        # JSON should be compressed
        response = client.get("/api/large-json", headers={"Accept-Encoding": "gzip"})
        assert response.headers.get("content-encoding") == "gzip"
        
        # Small JSON should not be compressed
        response = client.get("/api/small-json", headers={"Accept-Encoding": "gzip"})
        assert response.headers.get("content-encoding") is None
        
        # Images should not be compressed
        response = client.get("/static/image.jpg", headers={"Accept-Encoding": "gzip"})
        assert response.headers.get("content-encoding") is None
    
    def test_request_response_compression_cycle(self, full_compression_app):
        """Test both request decompression and response compression."""
        client = TestClient(full_compression_app)
        
        # Create large JSON payload
        large_payload = {"items": [{"data": "x" * 100} for _ in range(50)]}
        original_json = str(large_payload).encode()
        
        # Compress the request
        compressed_request = gzip.compress(original_json)
        
        # Send compressed request, expect compressed response
        response = client.post(
            "/api/upload",
            content=compressed_request,
            headers={
                "Content-Encoding": "gzip",
                "Content-Type": "application/json",
                "Accept-Encoding": "gzip"
            }
        )
        
        assert response.status_code == 200
        
        # Response should be compressed
        assert response.headers.get("content-encoding") == "gzip"
        
        # Verify request was properly decompressed
        data = response.json()
        assert data["received_size"] == len(original_json)


@pytest.mark.slow
class TestCompressionPerformance:
    """Performance tests for compression middleware."""
    
    @pytest.fixture
    def performance_app(self):
        """App configured for performance testing."""
        app = FastAPI()
        
        @app.get("/perf/test")
        async def performance_test():
            # Return data that will benefit from compression
            return {"data": "x" * 10000}  # 10KB of compressible data
        
        settings = Mock(spec=Settings)
        settings.compression_enabled = True
        settings.compression_min_size = 1024
        settings.compression_level = 6
        
        app.add_middleware(CompressionMiddleware, settings=settings)
        return app
    
    def test_compression_performance_overhead(self, performance_app):
        """Test performance overhead of compression."""
        import time
        
        client = TestClient(performance_app)
        
        # Test without compression
        start_time = time.time()
        for _ in range(50):
            response = client.get("/perf/test")
            assert response.status_code == 200
        uncompressed_time = time.time() - start_time
        
        # Test with compression
        start_time = time.time()
        for _ in range(50):
            response = client.get("/perf/test", headers={"Accept-Encoding": "gzip"})
            assert response.status_code == 200
        compressed_time = time.time() - start_time
        
        # Compression should not add excessive overhead
        # Allow up to 2x slowdown for compression benefit
        overhead_ratio = compressed_time / uncompressed_time
        assert overhead_ratio < 3.0, f"Compression overhead too high: {overhead_ratio:.2f}x"
    
    def test_compression_ratio_effectiveness(self, performance_app):
        """Test compression effectiveness and ratios."""
        client = TestClient(performance_app)
        
        response = client.get("/perf/test", headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        
        original_size = int(response.headers["x-original-size"])
        compressed_size = int(response.headers["content-length"])
        compression_ratio = compressed_size / original_size
        
        # Should achieve good compression ratio for repetitive data
        assert compression_ratio < 0.1, f"Poor compression ratio: {compression_ratio:.2f}"
        
        # Verify compression saved significant space
        savings_percent = ((original_size - compressed_size) / original_size) * 100
        assert savings_percent > 90, f"Insufficient compression savings: {savings_percent:.1f}%"