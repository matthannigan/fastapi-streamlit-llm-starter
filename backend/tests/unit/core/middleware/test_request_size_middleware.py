"""
Comprehensive tests for Request Size Limiting Middleware

Tests cover content-length validation, streaming size limits, endpoint-specific limits,
content-type limits, and DoS protection features.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.middleware.request_size import (
    RequestSizeLimitMiddleware,
    RequestTooLargeException,
    ASGIRequestSizeLimitMiddleware
)
from app.core.config import Settings


class TestRequestSizeLimitMiddleware:
    """Test the main request size limiting middleware."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with size limiting configuration."""
        settings = Mock(spec=Settings)
        settings.request_size_limits = {
            'default': 5 * 1024 * 1024,  # 5MB default
            'application/json': 2 * 1024 * 1024,  # 2MB for JSON
            '/v1/text_processing/process': 1 * 1024 * 1024,  # 1MB for text processing
            '/v1/upload': 10 * 1024 * 1024,  # 10MB for uploads
        }
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI test app with request size limiting middleware."""
        app = FastAPI()
        
        @app.post("/v1/text_processing/process")
        async def text_processing(request: Request):
            body = await request.body()
            return {"processed_size": len(body)}
        
        @app.post("/v1/upload")
        async def upload_file(request: Request):
            body = await request.body()
            return {"uploaded_size": len(body)}
        
        @app.post("/api/data")
        async def process_data(request: Request):
            body = await request.body()
            return {"data_size": len(body)}
        
        @app.get("/health")
        async def health_check():
            return {"status": "ok"}
        
        app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with custom settings."""
        app = FastAPI()
        middleware = RequestSizeLimitMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.default_limits['default'] == 5 * 1024 * 1024
        assert middleware.default_limits['application/json'] == 2 * 1024 * 1024
        assert middleware.default_limits['/v1/text_processing/process'] == 1 * 1024 * 1024
        assert 'POST' in middleware.body_methods
        assert 'PUT' in middleware.body_methods
        assert 'PATCH' in middleware.body_methods
    
    def test_get_size_limit_endpoint_specific(self, app, settings):
        """Test endpoint-specific size limit retrieval."""
        middleware = RequestSizeLimitMiddleware(app.user_middleware[0].cls, settings)
        
        # Mock request for text processing endpoint
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/v1/text_processing/process"
        request.headers = {}
        
        limit = middleware._get_size_limit(request)
        assert limit == 1 * 1024 * 1024  # 1MB
    
    def test_get_size_limit_content_type_specific(self, app, settings):
        """Test content-type specific size limit retrieval."""
        middleware = RequestSizeLimitMiddleware(app.user_middleware[0].cls, settings)
        
        # Mock request with JSON content type
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/generic"
        request.headers = {"content-type": "application/json; charset=utf-8"}
        
        limit = middleware._get_size_limit(request)
        assert limit == 2 * 1024 * 1024  # 2MB for JSON
    
    def test_get_size_limit_default_fallback(self, app, settings):
        """Test fallback to default size limit."""
        middleware = RequestSizeLimitMiddleware(app.user_middleware[0].cls, settings)
        
        # Mock request with unknown endpoint and content type
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/unknown/endpoint"
        request.headers = {"content-type": "text/plain"}
        
        limit = middleware._get_size_limit(request)
        assert limit == 5 * 1024 * 1024  # 5MB default
    
    def test_format_size_human_readable(self, app, settings):
        """Test human-readable size formatting."""
        middleware = RequestSizeLimitMiddleware(app.user_middleware[0].cls, settings)
        
        assert middleware._format_size(512) == "512B"
        assert middleware._format_size(1536) == "1.5KB"
        assert middleware._format_size(2 * 1024 * 1024) == "2.0MB"
        assert middleware._format_size(3 * 1024 * 1024 * 1024) == "3.0GB"
    
    def test_skip_size_check_for_get_requests(self, app):
        """Test that GET requests skip size checking."""
        client = TestClient(app)
        
        # GET request should always pass regardless of size limits
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_content_length_header_validation_pass(self, app):
        """Test passing content-length validation."""
        client = TestClient(app)
        
        # Small request within limit (text processing endpoint has 1MB limit)
        small_data = b"x" * 1000  # 1KB
        response = client.post(
            "/v1/text_processing/process",
            content=small_data,
            headers={"Content-Length": str(len(small_data))}
        )
        
        assert response.status_code == 200
        assert response.json()["processed_size"] == len(small_data)
    
    def test_content_length_header_validation_fail(self, app):
        """Test failing content-length validation."""
        client = TestClient(app)
        
        # Large declared size exceeding limit
        large_size = 2 * 1024 * 1024  # 2MB, exceeds 1MB limit for text processing
        
        response = client.post(
            "/v1/text_processing/process",
            content=b"small actual data",
            headers={"Content-Length": str(large_size)}
        )
        
        assert response.status_code == 413
        data = response.json()
        assert data["error_code"] == "REQUEST_TOO_LARGE"
        assert "max_size" in data
        assert "received_size" in data
        assert "endpoint" in data
    
    def test_invalid_content_length_header(self, app):
        """Test handling of invalid Content-Length header."""
        client = TestClient(app)
        
        response = client.post(
            "/v1/text_processing/process",
            content=b"test data",
            headers={"Content-Length": "invalid"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_CONTENT_LENGTH"
    
    def test_streaming_size_validation_pass(self, app):
        """Test streaming size validation that passes."""
        client = TestClient(app)
        
        # Data within upload limit (10MB)
        data_size = 1024 * 1024  # 1MB
        test_data = b"x" * data_size
        
        response = client.post("/v1/upload", content=test_data)
        assert response.status_code == 200
        assert response.json()["uploaded_size"] == data_size
    
    def test_streaming_size_validation_fail(self, app):
        """Test streaming size validation that fails."""
        client = TestClient(app)
        
        # Create large data exceeding limit
        # Text processing endpoint has 1MB limit
        large_data = b"x" * (2 * 1024 * 1024)  # 2MB
        
        response = client.post("/v1/text_processing/process", content=large_data)
        assert response.status_code == 413
        
        data = response.json()
        assert data["error_code"] == "REQUEST_TOO_LARGE"
        assert "max_size" in data
    
    def test_response_headers_include_size_info(self, app):
        """Test that successful responses include size limit information."""
        client = TestClient(app)
        
        response = client.post("/v1/upload", content=b"test data")
        assert response.status_code == 200
        
        assert "X-Max-Request-Size" in response.headers
        assert "X-Request-Size-Limit" in response.headers
    
    def test_different_limits_per_endpoint(self, app):
        """Test different size limits for different endpoints."""
        client = TestClient(app)
        
        # Text processing has 1MB limit
        data_1mb = b"x" * (1024 * 1024)
        response = client.post("/v1/text_processing/process", content=data_1mb)
        assert response.status_code == 200
        
        # Slightly over 1MB should fail for text processing
        data_over_1mb = b"x" * (1024 * 1024 + 1000)
        response = client.post("/v1/text_processing/process", content=data_over_1mb)
        assert response.status_code == 413
        
        # But same data should pass for upload endpoint (10MB limit)
        response = client.post("/v1/upload", content=data_over_1mb)
        assert response.status_code == 200
    
    def test_content_type_specific_limits(self, app):
        """Test content-type specific size limits."""
        client = TestClient(app)
        
        # 2.1MB data (exceeds 2MB JSON limit, within 5MB default)
        data_2mb = b"x" * (2 * 1024 * 1024 + 1024)  # 2MB + 1KB
        
        # Should fail with JSON content type (2MB limit)
        response = client.post(
            "/api/data",
            content=data_2mb,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 413
        
        # Should pass with plain text content type (5MB default limit)
        response = client.post(
            "/api/data", 
            content=data_2mb,
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code == 200


class TestRequestTooLargeException:
    """Test custom exception for request size violations."""
    
    def test_exception_creation(self):
        """Test creating RequestTooLargeException."""
        message = "Request exceeds size limit"
        exception = RequestTooLargeException(message)
        
        assert str(exception) == message
        assert isinstance(exception, Exception)


class TestASGIRequestSizeLimitMiddleware:
    """Test ASGI-level request size limiting middleware."""
    
    @pytest.fixture
    def asgi_app(self):
        """Simple ASGI app for testing."""
        async def app(scope, receive, send):
            if scope["type"] == "http":
                # Consume the request body to trigger size validation
                while True:
                    message = await receive()
                    if message["type"] == "http.request":
                        if not message.get("more_body", False):
                            break
                    elif message["type"] == "http.disconnect":
                        break
                
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": b'{"message": "success"}',
                })
        return app
    
    @pytest.fixture
    def asgi_middleware(self, asgi_app):
        """ASGI middleware with size limits."""
        return ASGIRequestSizeLimitMiddleware(asgi_app, max_size=1024)  # 1KB limit
    
    @pytest.mark.asyncio
    async def test_asgi_middleware_non_http_passthrough(self, asgi_middleware):
        """Test ASGI middleware passes through non-HTTP requests."""
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()
        
        await asgi_middleware(scope, receive, send)
        # Should pass through to underlying app
    
    @pytest.mark.asyncio
    async def test_asgi_middleware_get_method_passthrough(self, asgi_middleware):
        """Test ASGI middleware passes through GET requests."""
        scope = {
            "type": "http",
            "method": "GET",
            "headers": []
        }
        
        # Mock receive to return proper ASGI messages for GET request
        receive_call_count = 0
        async def mock_receive():
            nonlocal receive_call_count
            receive_call_count += 1
            if receive_call_count == 1:
                return {
                    "type": "http.request",
                    "body": b"",
                    "more_body": False
                }
            return {"type": "http.disconnect"}
        
        send = AsyncMock()
        
        await asgi_middleware(scope, mock_receive, send)
        # Should pass through to underlying app
        send.assert_called()  # Verify the app was called and sent responses
    
    @pytest.mark.asyncio
    async def test_asgi_middleware_content_length_check_pass(self, asgi_middleware):
        """Test ASGI middleware content-length validation passes."""
        scope = {
            "type": "http",
            "method": "POST",
            "headers": [[b"content-length", b"512"]]  # Within 1KB limit
        }
        
        # Mock receive to return proper ASGI messages for POST request
        receive_call_count = 0
        async def mock_receive():
            nonlocal receive_call_count
            receive_call_count += 1
            if receive_call_count == 1:
                return {
                    "type": "http.request",
                    "body": b"x" * 512,  # 512 bytes as declared
                    "more_body": False
                }
            return {"type": "http.disconnect"}
        
        send = AsyncMock()
        
        await asgi_middleware(scope, mock_receive, send)
        # Should pass through to underlying app
        send.assert_called()  # Verify the app was called and sent responses
    
    @pytest.mark.asyncio
    async def test_asgi_middleware_content_length_check_fail(self, asgi_middleware):
        """Test ASGI middleware content-length validation fails."""
        scope = {
            "type": "http",
            "method": "POST",
            "headers": [[b"content-length", b"2048"]]  # Exceeds 1KB limit
        }
        receive = AsyncMock()
        send = AsyncMock()
        
        await asgi_middleware(scope, receive, send)
        
        # Should have sent 413 response
        send.assert_any_call({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                [b"content-type", b"application/json"],
                [b"x-max-request-size", b"1024"],
            ],
        })
    
    @pytest.mark.asyncio
    async def test_asgi_middleware_invalid_content_length(self, asgi_middleware):
        """Test ASGI middleware handles invalid content-length."""
        scope = {
            "type": "http",
            "method": "POST",
            "headers": [[b"content-length", b"invalid"]]
        }
        receive = AsyncMock()
        send = AsyncMock()
        
        await asgi_middleware(scope, receive, send)
        
        # Should have sent 400 response
        send.assert_any_call({
            "type": "http.response.start",
            "status": 400,
            "headers": [[b"content-type", b"application/json"]],
        })
    
    @pytest.mark.asyncio
    async def test_asgi_middleware_streaming_validation(self, asgi_middleware):
        """Test ASGI middleware streaming size validation."""
        scope = {
            "type": "http",
            "method": "POST",
            "headers": []
        }
        
        # Mock receive that returns large chunks
        chunk_size = 512
        num_chunks = 3  # Total 1536 bytes, exceeds 1024 limit
        
        async def mock_receive():
            mock_receive.call_count = getattr(mock_receive, 'call_count', 0) + 1
            if mock_receive.call_count <= num_chunks:
                return {
                    "type": "http.request",
                    "body": b"x" * chunk_size,
                    "more_body": mock_receive.call_count < num_chunks
                }
            return {"type": "http.disconnect"}
        
        send = AsyncMock()
        
        # Should trigger size violation during streaming
        await asgi_middleware(scope, mock_receive, send)
        
        # Should send error response
        error_calls = [call for call in send.call_args_list 
                      if call[0][0].get("status") == 413]
        assert len(error_calls) > 0


class TestRequestSizeIntegration:
    """Integration tests for request size limiting."""
    
    @pytest.fixture
    def integration_app(self):
        """App with comprehensive size limits for integration testing."""
        app = FastAPI()
        
        @app.post("/api/small")
        async def small_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body), "endpoint": "small"}
        
        @app.post("/api/medium")
        async def medium_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body), "endpoint": "medium"}
        
        @app.post("/api/large")
        async def large_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body), "endpoint": "large"}
        
        # Configure different limits for testing
        settings = Mock(spec=Settings)
        settings.request_size_limits = {
            'default': 1024,  # 1KB default (small for testing)
            '/api/small': 512,  # 512B for small endpoint
            '/api/medium': 2048,  # 2KB for medium endpoint  
            '/api/large': 4096,  # 4KB for large endpoint
            'application/json': 800,  # 800B for JSON
            'text/plain': 1500,  # 1.5KB for text
        }
        
        app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
        return app
    
    def test_progressive_size_limits(self, integration_app):
        """Test different endpoints with progressive size limits."""
        client = TestClient(integration_app)
        
        # Small data (400B) - should work for all endpoints
        small_data = b"x" * 400
        
        response = client.post("/api/small", content=small_data)
        assert response.status_code == 200
        
        response = client.post("/api/medium", content=small_data)
        assert response.status_code == 200
        
        response = client.post("/api/large", content=small_data)
        assert response.status_code == 200
        
        # Medium data (1KB) - should fail for small, work for medium/large
        medium_data = b"x" * 1024
        
        response = client.post("/api/small", content=medium_data)
        assert response.status_code == 413
        
        response = client.post("/api/medium", content=medium_data)
        assert response.status_code == 200
        
        response = client.post("/api/large", content=medium_data)
        assert response.status_code == 200
        
        # Large data (3KB) - should fail for small/medium, work for large
        large_data = b"x" * 3072
        
        response = client.post("/api/small", content=large_data)
        assert response.status_code == 413
        
        response = client.post("/api/medium", content=large_data)
        assert response.status_code == 413
        
        response = client.post("/api/large", content=large_data)
        assert response.status_code == 200
    
    def test_content_type_precedence_over_endpoint(self, integration_app):
        """Test that endpoint limits take precedence over content-type limits."""
        client = TestClient(integration_app)
        
        # 1KB data - exceeds JSON limit (800B) but within medium endpoint limit (2KB)
        data = b"x" * 1024
        
        # Endpoint limit should take precedence
        response = client.post(
            "/api/medium",
            content=data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # For endpoint without specific limit, content-type limit applies
        response = client.post(
            "/api/small",  # 512B limit
            content=data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 413
    
    def test_error_response_details(self, integration_app):
        """Test detailed error responses for size violations."""
        client = TestClient(integration_app)
        
        # Exceed limit for small endpoint
        large_data = b"x" * 1024
        response = client.post("/api/small", content=large_data)
        
        assert response.status_code == 413
        data = response.json()
        
        # Check error response structure
        assert data["error"] == "Request too large"
        assert data["error_code"] == "REQUEST_TOO_LARGE"
        assert data["endpoint"] == "/api/small"
        assert "max_size" in data
        assert "received_size" in data
        
        # Check headers
        assert "X-Max-Request-Size" in response.headers
        assert "X-Request-Size-Limit" in response.headers
    
    @pytest.mark.slow
    def test_concurrent_size_validation(self, integration_app):
        """Test size validation under concurrent load."""
        import concurrent.futures
        import threading
        
        client = TestClient(integration_app)
        results = []
        
        def make_request(size, endpoint):
            data = b"x" * size
            try:
                response = client.post(f"/api/{endpoint}", content=data)
                return response.status_code
            except Exception as e:
                return str(e)
        
        # Test concurrent requests with different sizes
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            # Mix of requests within and exceeding limits
            test_cases = [
                (300, "small"),   # Within limit
                (600, "small"),   # Exceeds limit
                (1500, "medium"), # Within limit
                (3000, "medium"), # Exceeds limit
                (2000, "large"),  # Within limit
                (5000, "large"),  # Exceeds limit
            ] * 5  # Run each case 5 times
            
            for size, endpoint in test_cases:
                future = executor.submit(make_request, size, endpoint)
                futures.append((future, size, endpoint))
            
            # Collect results
            for future, size, endpoint in futures:
                status_code = future.result()
                results.append((status_code, size, endpoint))
        
        # Analyze results
        success_count = sum(1 for status, _, _ in results if status == 200)
        error_count = sum(1 for status, _, _ in results if status == 413)
        
        assert success_count > 0, "No requests succeeded"
        assert error_count > 0, "No requests were properly rejected"
        
        # Verify that smaller requests generally succeeded
        small_successes = sum(1 for status, size, endpoint in results 
                             if status == 200 and size <= 400)
        assert small_successes > 0, "Small requests should succeed"


@pytest.mark.slow
class TestRequestSizePerformance:
    """Performance tests for request size limiting middleware."""
    
    @pytest.fixture
    def performance_app(self):
        """App configured for performance testing."""
        app = FastAPI()
        
        @app.post("/perf/test")
        async def performance_endpoint(request: Request):
            body = await request.body()
            return {"processed": len(body)}
        
        settings = Mock(spec=Settings)
        settings.request_size_limits = {
            'default': 10 * 1024 * 1024,  # 10MB limit for performance testing
        }
        
        app.add_middleware(RequestSizeLimitMiddleware, settings=settings)
        return app
    
    def test_size_validation_performance_overhead(self, performance_app):
        """Test performance overhead of size validation."""
        import time
        
        client = TestClient(performance_app)
        test_data = b"x" * 1024  # 1KB test data
        
        # Measure request processing time
        start_time = time.time()
        for _ in range(100):
            response = client.post("/perf/test", content=test_data)
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_request = total_time / 100
        
        # Size validation should add minimal overhead
        assert avg_time_per_request < 0.01, f"Average time per request: {avg_time_per_request:.3f}s"
    
    def test_large_request_processing_time(self, performance_app):
        """Test processing time for large requests within limits."""
        import time
        
        client = TestClient(performance_app)
        
        # Test with different data sizes
        sizes = [1024, 10*1024, 100*1024, 1024*1024]  # 1KB to 1MB
        
        for size in sizes:
            test_data = b"x" * size
            
            start_time = time.time()
            response = client.post("/perf/test", content=test_data)
            end_time = time.time()
            
            assert response.status_code == 200
            processing_time = end_time - start_time
            
            # Processing time should scale reasonably with size
            time_per_byte = processing_time / size
            assert time_per_byte < 0.00001, f"Processing too slow for {size} bytes: {time_per_byte:.8f}s/byte"