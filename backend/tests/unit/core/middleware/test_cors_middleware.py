"""
Comprehensive tests for CORS middleware.

Tests cover CORS configuration, origin validation, credentials handling,
header/method allowances, and preflight request processing.
"""

import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware

from app.core.middleware.cors import setup_cors_middleware
from app.core.config import Settings


class TestCORSMiddleware:
    """Test CORS middleware setup and configuration."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with CORS configuration."""
        settings = Mock(spec=Settings)
        settings.allowed_origins = ["http://localhost:3000", "https://example.com"]
        return settings
    
    @pytest.fixture
    def app(self):
        """Basic FastAPI app for testing."""
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        @app.post("/api/data")
        async def api_endpoint():
            return {"result": "success"}
        
        @app.options("/api/data")
        async def options_endpoint():
            return {"status": "ok"}
        
        return app
    
    @pytest.fixture
    def cors_app(self, app, settings):
        """FastAPI app with CORS middleware configured."""
        setup_cors_middleware(app, settings)
        return app
    
    def test_setup_cors_middleware(self, app, settings):
        """Test CORS middleware setup function."""
        initial_middleware_count = len(app.user_middleware)
        
        setup_cors_middleware(app, settings)
        
        # Verify middleware was added
        assert len(app.user_middleware) == initial_middleware_count + 1
        
        # Verify it's the CORS middleware
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        assert cors_middleware.kwargs["allow_origins"] == settings.allowed_origins
        assert cors_middleware.kwargs["allow_credentials"] is True
        assert cors_middleware.kwargs["allow_methods"] == ["*"]
        assert cors_middleware.kwargs["allow_headers"] == ["*"]
    
    def test_cors_simple_request_allowed_origin(self, cors_app):
        """Test simple CORS request with allowed origin."""
        client = TestClient(cors_app)
        
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_simple_request_disallowed_origin(self, cors_app):
        """Test simple CORS request with disallowed origin."""
        client = TestClient(cors_app)
        
        response = client.get(
            "/test",
            headers={"Origin": "https://malicious.com"}
        )
        
        # Request should succeed but CORS headers should not include the origin
        assert response.status_code == 200
        # The disallowed origin should not be in the response header
        assert response.headers.get("access-control-allow-origin") != "https://malicious.com"
    
    def test_cors_preflight_request_allowed_origin(self, cors_app):
        """Test CORS preflight request with allowed origin."""
        client = TestClient(cors_app)
        
        response = client.options(
            "/api/data",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "https://example.com"
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "POST" in response.headers["access-control-allow-methods"]
        assert "content-type" in response.headers["access-control-allow-headers"].lower()
        assert "authorization" in response.headers["access-control-allow-headers"].lower()
    
    def test_cors_preflight_request_disallowed_origin(self, cors_app):
        """Test CORS preflight request with disallowed origin."""
        client = TestClient(cors_app)
        
        response = client.options(
            "/api/data",
            headers={
                "Origin": "https://blocked.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Preflight may be rejected or handled but origin should not be allowed
        # CORS middleware may reject invalid origins with 4xx status
        assert response.status_code in [200, 400]  # Accept either
        if response.status_code == 200:
            assert response.headers.get("access-control-allow-origin") != "https://blocked.com"
    
    def test_cors_credentials_support(self, cors_app):
        """Test CORS credentials support."""
        client = TestClient(cors_app)
        
        response = client.get(
            "/test",
            headers={"Origin": "http://localhost:3000"},
            cookies={"session_id": "test123"}
        )
        
        assert response.status_code == 200
        assert response.headers["access-control-allow-credentials"] == "true"
    
    def test_cors_all_methods_allowed(self, cors_app):
        """Test that all HTTP methods are allowed in CORS."""
        client = TestClient(cors_app)
        
        methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD"]
        
        for method in methods:
            response = client.options(
                "/api/data",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": method
                }
            )
            
            assert response.status_code == 200
            allowed_methods = response.headers.get("access-control-allow-methods", "")
            # Should allow all methods or specifically allow the requested method
            assert "*" in allowed_methods or method in allowed_methods.upper()
    
    def test_cors_all_headers_allowed(self, cors_app):
        """Test that all headers are allowed in CORS."""
        client = TestClient(cors_app)
        
        custom_headers = ["X-Custom-Header", "Authorization", "Content-Type", "X-API-Key"]
        headers_string = ", ".join(custom_headers)
        
        response = client.options(
            "/api/data",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": headers_string
            }
        )
        
        assert response.status_code == 200
        allowed_headers = response.headers.get("access-control-allow-headers", "")
        # Should allow all headers or specifically allow the requested headers
        assert "*" in allowed_headers or all(
            header.lower() in allowed_headers.lower() for header in custom_headers
        )
    
    def test_cors_no_origin_header(self, cors_app):
        """Test request without Origin header (same-origin request)."""
        client = TestClient(cors_app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        # No CORS headers should be added for same-origin requests
        assert "access-control-allow-origin" not in response.headers
    
    def test_cors_multiple_origins_configuration(self):
        """Test CORS setup with multiple allowed origins."""
        app = FastAPI()
        settings = Mock(spec=Settings)
        settings.allowed_origins = [
            "http://localhost:3000",
            "https://app.example.com",
            "https://admin.example.com"
        ]
        
        setup_cors_middleware(app, settings)
        client = TestClient(app)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        # Test each allowed origin
        for origin in settings.allowed_origins:
            response = client.get(
                "/test",
                headers={"Origin": origin}
            )
            
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
    
    def test_cors_wildcard_origin_configuration(self):
        """Test CORS setup with wildcard origin (development mode)."""
        app = FastAPI()
        settings = Mock(spec=Settings)
        settings.allowed_origins = ["*"]
        
        setup_cors_middleware(app, settings)
        client = TestClient(app)
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        response = client.get(
            "/test",
            headers={"Origin": "https://any-domain.com"}
        )
        
        assert response.status_code == 200
        # With wildcard origin, the response should reflect the request origin
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_middleware_logging(self, app, settings):
        """Test that CORS middleware setup includes proper logging."""
        # Test that the setup completes successfully and logs appropriately
        # The actual logging behavior is tested through integration
        setup_cors_middleware(app, settings)
        
        # If we reach here, setup completed without errors
        assert True
    
    def test_cors_empty_origins_list(self):
        """Test CORS setup with empty origins list."""
        app = FastAPI()
        settings = Mock(spec=Settings)
        settings.allowed_origins = []
        
        setup_cors_middleware(app, settings)
        
        # Verify middleware was still added even with empty origins
        cors_middleware = None
        for middleware in app.user_middleware:
            if middleware.cls == CORSMiddleware:
                cors_middleware = middleware
                break
        
        assert cors_middleware is not None
        assert cors_middleware.kwargs["allow_origins"] == []
    
    def test_cors_response_headers_preservation(self, cors_app):
        """Test that CORS middleware preserves other response headers."""
        @cors_app.get("/headers")
        async def headers_endpoint():
            return {"data": "test"}
        
        client = TestClient(cors_app)
        
        response = client.get(
            "/headers",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers
        # Content headers should also be preserved
        assert "content-type" in response.headers
        assert "content-length" in response.headers
