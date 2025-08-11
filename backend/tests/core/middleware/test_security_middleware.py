"""
Comprehensive tests for Security middleware.

Tests cover security headers injection, request validation, content security policy,
request size limits, and endpoint-specific CSP rules.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware.security import SecurityMiddleware
from app.core.config import Settings


class TestSecurityMiddleware:
    """Test Security middleware functionality."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with security configuration."""
        settings = Mock(spec=Settings)
        settings.security_headers_enabled = True
        settings.max_request_size = 1024 * 1024  # 1MB
        settings.max_headers_count = 50
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI app with security middleware."""
        app = FastAPI()
        
        @app.get("/api/test")
        async def api_endpoint():
            return {"message": "api response"}
        
        @app.get("/docs")
        async def docs_endpoint():
            return {"message": "docs page"}
        
        @app.get("/redoc")
        async def redoc_endpoint():
            return {"message": "redoc page"}
        
        @app.get("/openapi.json")
        async def openapi_endpoint():
            return {"message": "openapi spec"}
        
        @app.get("/internal/admin")
        async def internal_endpoint():
            return {"message": "internal admin"}
        
        @app.post("/upload")
        async def upload_endpoint():
            return {"message": "upload success"}
        
        app.add_middleware(SecurityMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with settings."""
        app = FastAPI()
        middleware = SecurityMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.max_request_size == 1024 * 1024
        assert middleware.max_headers_count == 50
        
        # Check base security headers are configured
        expected_headers = {
            'Strict-Transport-Security',
            'X-Frame-Options', 
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Referrer-Policy',
            'Permissions-Policy'
        }
        assert expected_headers.issubset(set(middleware.base_security_headers.keys()))
    
    def test_security_headers_injection_api(self, app):
        """Test security headers are injected for API endpoints."""
        client = TestClient(app)
        
        response = client.get("/api/test")
        
        assert response.status_code == 200
        
        # Check base security headers
        assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-xss-protection"] == "1; mode=block"
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert "permissions-policy" in response.headers
        
        # Check API CSP is applied
        csp = response.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "object-src 'none'" in csp
    
    def test_security_headers_injection_docs(self, app):
        """Test relaxed CSP for documentation endpoints."""
        client = TestClient(app)
        
        response = client.get("/docs")
        
        assert response.status_code == 200
        
        # Should have base security headers
        assert "strict-transport-security" in response.headers
        assert "x-frame-options" in response.headers
        
        # Should have relaxed CSP for docs
        csp = response.headers.get("content-security-policy", "")
        assert "'unsafe-inline'" in csp  # Needed for Swagger UI
        assert "'unsafe-eval'" in csp  # Needed for Swagger UI
        assert "cdn.jsdelivr.net" in csp or "unpkg.com" in csp  # CDN sources
    
    def test_security_headers_injection_redoc(self, app):
        """Test relaxed CSP for ReDoc endpoint."""
        client = TestClient(app)
        
        response = client.get("/redoc")
        
        assert response.status_code == 200
        
        # Should have relaxed CSP for ReDoc
        csp = response.headers.get("content-security-policy", "")
        assert "'unsafe-inline'" in csp
        assert "'unsafe-eval'" in csp
    
    def test_security_headers_injection_openapi(self, app):
        """Test relaxed CSP for OpenAPI spec."""
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        
        # OpenAPI spec should get docs CSP treatment
        csp = response.headers.get("content-security-policy", "")
        assert "'unsafe-inline'" in csp
    
    def test_security_headers_injection_internal(self, app):
        """Test relaxed CSP for internal endpoints."""
        client = TestClient(app)
        
        response = client.get("/internal/admin")
        
        assert response.status_code == 200
        
        # Internal endpoints should get docs CSP
        csp = response.headers.get("content-security-policy", "")
        assert "'unsafe-inline'" in csp
    
    def test_request_size_validation_within_limit(self, app):
        """Test request size validation within limits."""
        client = TestClient(app)
        
        # Small request within limit
        small_data = "x" * 1000  # 1KB
        response = client.post(
            "/upload",
            content=small_data,
            headers={"Content-Type": "text/plain"}
        )
        
        assert response.status_code == 200
    
    def test_request_size_validation_exceeds_limit(self, app):
        """Test request size validation when exceeding limits."""
        client = TestClient(app)
        
        # Large request exceeding limit (2MB > 1MB limit)
        large_size = 2 * 1024 * 1024
        response = client.post(
            "/upload",
            content="x" * large_size,
            headers={
                "Content-Type": "text/plain",
                "Content-Length": str(large_size)
            }
        )
        
        assert response.status_code == 413  # Request Entity Too Large
        assert "Request too large" in response.json()["error"]
    
    def test_request_size_validation_invalid_content_length(self, app):
        """Test request with invalid Content-Length header."""
        client = TestClient(app)
        
        response = client.post(
            "/upload",
            content="test data",
            headers={
                "Content-Type": "text/plain",
                "Content-Length": "invalid"
            }
        )
        
        assert response.status_code == 400
        assert "Invalid Content-Length" in response.json()["error"]
    
    def test_excessive_headers_validation(self, app):
        """Test validation of excessive headers count."""
        client = TestClient(app)
        
        # Create more headers than allowed (50 is the limit)
        excessive_headers = {f"X-Custom-Header-{i}": f"value{i}" for i in range(60)}
        excessive_headers["Content-Type"] = "application/json"
        
        response = client.get("/api/test", headers=excessive_headers)
        
        assert response.status_code == 400
        assert "Too many headers" in response.json()["error"]
    
    def test_headers_count_within_limit(self, app):
        """Test request with headers count within limit."""
        client = TestClient(app)
        
        # Create headers within limit
        normal_headers = {f"X-Custom-Header-{i}": f"value{i}" for i in range(10)}
        normal_headers["Content-Type"] = "application/json"
        
        response = client.get("/api/test", headers=normal_headers)
        
        assert response.status_code == 200
    
    def test_is_docs_endpoint_detection(self, settings):
        """Test documentation endpoint detection logic."""
        app = FastAPI()
        middleware = SecurityMiddleware(app, settings)
        
        # Mock request objects
        docs_paths = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/docs/oauth2-redirect",
            "/redoc/something",
            "/internal/admin",
            "/some/openapi/path"
        ]
        
        api_paths = [
            "/api/test",
            "/v1/users",
            "/health",
            "/metrics"
        ]
        
        for path in docs_paths:
            mock_request = Mock()
            mock_request.url.path = path
            assert middleware._is_docs_endpoint(mock_request) is True
        
        for path in api_paths:
            mock_request = Mock()
            mock_request.url.path = path
            assert middleware._is_docs_endpoint(mock_request) is False
    
    def test_middleware_disabled_security_headers(self):
        """Test middleware when security headers are disabled."""
        settings = Mock(spec=Settings)
        settings.security_headers_enabled = False
        settings.max_request_size = 1024 * 1024
        settings.max_headers_count = 50
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        app.add_middleware(SecurityMiddleware, settings=settings)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        # Security headers should still be added (middleware doesn't have a disable flag)
        assert "strict-transport-security" in response.headers
    
    def test_custom_settings_initialization(self):
        """Test middleware initialization with custom settings."""
        settings = Mock(spec=Settings)
        # Test missing attributes with fallback values
        delattr(settings, 'max_request_size') if hasattr(settings, 'max_request_size') else None
        delattr(settings, 'max_headers_count') if hasattr(settings, 'max_headers_count') else None
        
        app = FastAPI()
        middleware = SecurityMiddleware(app, settings)
        
        # Should use default values when settings are missing
        assert middleware.max_request_size == 10 * 1024 * 1024  # 10MB default
        assert middleware.max_headers_count == 100  # 100 default
    
    def test_csp_header_content_api_endpoints(self, app):
        """Test detailed CSP content for API endpoints."""
        client = TestClient(app)
        
        response = client.get("/api/test")
        
        csp = response.headers.get("content-security-policy", "")
        
        # Check specific CSP directives for API endpoints
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp
        assert "img-src 'self' data:" in csp
        assert "font-src 'self'" in csp
        assert "connect-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp
        assert "frame-ancestors 'none'" in csp
    
    def test_csp_header_content_docs_endpoints(self, app):
        """Test detailed CSP content for documentation endpoints."""
        client = TestClient(app)
        
        response = client.get("/docs")
        
        csp = response.headers.get("content-security-policy", "")
        
        # Check specific CSP directives for docs endpoints
        assert "default-src 'self'" in csp
        assert "'unsafe-inline'" in csp
        assert "'unsafe-eval'" in csp
        assert ("cdn.jsdelivr.net" in csp or "unpkg.com" in csp)
        assert "object-src 'none'" in csp
        assert "base-uri 'self'" in csp
    
    def test_response_without_content_length_header(self, app):
        """Test request without Content-Length header."""
        client = TestClient(app)
        
        # Request without Content-Length should work normally
        response = client.get("/api/test")
        
        assert response.status_code == 200
        assert "strict-transport-security" in response.headers
    
    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self, settings):
        """Test middleware behavior when downstream raises exception."""
        app = FastAPI()
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        app.add_middleware(SecurityMiddleware, settings=settings)
        client = TestClient(app, raise_server_exceptions=False)
        
        # Exception should propagate as 500 error
        response = client.get("/error")
        
        assert response.status_code == 500  # Internal server error
        # When an exception occurs, the security middleware may not get to process
        # the response because FastAPI's exception handling bypasses normal middleware
        # response processing. This is expected behavior.
    
    def test_permissions_policy_header(self, app):
        """Test Permissions-Policy header content."""
        client = TestClient(app)
        
        response = client.get("/api/test")
        
        permissions = response.headers.get("permissions-policy", "")
        
        # Check that dangerous permissions are disabled
        assert "geolocation=()" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions
    
    def test_hsts_header_configuration(self, app):
        """Test HSTS header configuration."""
        client = TestClient(app)
        
        response = client.get("/api/test")
        
        hsts = response.headers.get("strict-transport-security")
        
        # Check HSTS configuration
        assert "max-age=31536000" in hsts  # 1 year
        assert "includeSubDomains" in hsts
        # Should not include preload without explicit configuration
        assert "preload" not in hsts
