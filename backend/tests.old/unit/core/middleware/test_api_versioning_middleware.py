"""
Comprehensive tests for API Versioning Middleware

Tests cover version detection, path rewriting, header handling,
content negotiation, and backward compatibility features.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.core.middleware.api_versioning import (
    APIVersioningMiddleware,
    extract_version_from_url,
    extract_version_from_header,
    extract_version_from_accept,
    validate_api_version,
    rewrite_path_for_version,
    add_version_headers,
    APIVersionNotSupported
)
from app.core.config import Settings


class TestAPIVersioningMiddleware:
    """Test the main API versioning middleware."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with versioning configuration."""
        settings = Mock(spec=Settings)
        settings.api_versioning_enabled = True
        settings.api_default_version = "1.0"
        settings.api_supported_versions = ["1.0", "1.1", "2.0"]
        settings.api_version_header = "X-API-Version"
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI test app with versioning middleware."""
        app = FastAPI()
        
        # Version-specific endpoints
        @app.get("/v1/users")
        async def users_v1():
            return {"version": "1.0", "users": []}
        
        @app.get("/v2/users")
        async def users_v2():
            return {"version": "2.0", "users": [], "metadata": {}}
        
        @app.get("/users")
        async def users_unversioned():
            return {"version": "default", "users": []}
        
        @app.get("/health")
        async def health_check():
            return {"status": "ok"}
        
        app.add_middleware(APIVersioningMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with different configurations."""
        app = FastAPI()
        middleware = APIVersioningMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.enabled == True
        assert middleware.default_version == "1.0"
        assert "1.0" in middleware.supported_versions
        assert "2.0" in middleware.supported_versions
        assert middleware.version_header == "X-API-Version"
    
    def test_disabled_middleware(self):
        """Test middleware when versioning is disabled."""
        settings = Mock(spec=Settings)
        settings.api_versioning_enabled = False
        
        app = FastAPI()
        middleware = APIVersioningMiddleware(app, settings)
        
        assert middleware.enabled == False
    
    def test_version_detection_from_url(self, app):
        """Test version detection from URL path."""
        client = TestClient(app)
        
        response = client.get("/v1/users")
        assert response.status_code == 200
        assert response.json()["version"] == "1.0"
        
        response = client.get("/v2/users")  
        assert response.status_code == 200
        assert response.json()["version"] == "2.0"
    
    def test_version_detection_from_header(self, app):
        """Test version detection from request headers."""
        client = TestClient(app)
        
        # Test with version header
        response = client.get("/users", headers={"X-API-Version": "2.0"})
        assert response.status_code == 200
        # Should be rewritten to /v2/users
        
        # Test with custom header
        response = client.get("/users", headers={"API-Version": "1.1"})
        assert response.status_code == 200
    
    def test_version_detection_from_accept_header(self, app):
        """Test version detection from Accept header."""
        client = TestClient(app)
        
        # Test content negotiation with version
        response = client.get("/users", headers={
            "Accept": "application/vnd.api+json;version=2.0"
        })
        assert response.status_code == 200
    
    def test_default_version_fallback(self, app):
        """Test fallback to default version."""
        client = TestClient(app)
        
        response = client.get("/users")
        assert response.status_code == 200
        # Should use default version
    
    def test_unsupported_version_error(self, app):
        """Test error handling for unsupported versions."""
        client = TestClient(app)
        
        response = client.get("/users", headers={"X-API-Version": "3.0"})
        assert response.status_code == 400
        
        data = response.json()
        assert data["error_code"] == "API_VERSION_NOT_SUPPORTED"
        assert "3.0" in data["detail"]
        assert "supported_versions" in data
    
    def test_version_headers_in_response(self, app):
        """Test that version information is added to response headers."""
        client = TestClient(app)
        
        response = client.get("/v1/users")
        assert response.status_code == 200
        
        # Check version headers
        assert "X-API-Version" in response.headers
        assert "X-API-Supported-Versions" in response.headers
        assert response.headers["X-API-Version"] == "1.0"
    
    def test_health_check_bypass(self, app):
        """Test that health checks bypass version processing."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        # Health checks shouldn't be modified by versioning
    
    def test_version_precedence_order(self, app):
        """Test version detection precedence (URL > Header > Accept > Default)."""
        client = TestClient(app)
        
        # URL version should take precedence over header
        response = client.get("/v1/users", headers={"X-API-Version": "2.0"})
        assert response.status_code == 200
        # Should use v1 from URL, not v2 from header


class TestVersionExtractionFunctions:
    """Test individual version extraction functions."""
    
    def test_extract_version_from_url_valid(self):
        """Test URL version extraction with valid versions."""
        assert extract_version_from_url("/v1/users") == "1.0"
        assert extract_version_from_url("/v2/products/123") == "2.0"
        assert extract_version_from_url("/v1.1/orders") == "1.1"
        assert extract_version_from_url("/v10/items") == "10.0"
    
    def test_extract_version_from_url_invalid(self):
        """Test URL version extraction with invalid formats."""
        assert extract_version_from_url("/users") is None
        assert extract_version_from_url("/version1/users") is None
        assert extract_version_from_url("/v/users") is None
        assert extract_version_from_url("") is None
    
    def test_extract_version_from_header_standard(self):
        """Test header version extraction with standard headers."""
        request = Mock(spec=Request)
        
        # Test X-API-Version header
        request.headers = {"x-api-version": "2.0"}
        assert extract_version_from_header(request, "X-API-Version") == "2.0"
        
        # Test API-Version header
        request.headers = {"api-version": "1.1"}
        assert extract_version_from_header(request, "API-Version") == "1.1"
        
        # Test case insensitive
        request.headers = {"X-API-VERSION": "2.5"}
        assert extract_version_from_header(request, "x-api-version") == "2.5"
    
    def test_extract_version_from_header_missing(self):
        """Test header version extraction when header is missing."""
        request = Mock(spec=Request)
        request.headers = {}
        
        assert extract_version_from_header(request, "X-API-Version") is None
    
    def test_extract_version_from_accept_header(self):
        """Test version extraction from Accept header content negotiation."""
        request = Mock(spec=Request)
        
        # Test standard vendor media type with version
        request.headers = {"accept": "application/vnd.api+json;version=2.0"}
        assert extract_version_from_accept(request) == "2.0"
        
        # Test with multiple parameters
        request.headers = {"accept": "application/vnd.api+json;charset=utf-8;version=1.5"}
        assert extract_version_from_accept(request) == "1.5"
        
        # Test with spaces
        request.headers = {"accept": "application/vnd.api+json; version=3.0"}
        assert extract_version_from_accept(request) == "3.0"
    
    def test_extract_version_from_accept_header_no_version(self):
        """Test Accept header without version parameter."""
        request = Mock(spec=Request)
        
        request.headers = {"accept": "application/json"}
        assert extract_version_from_accept(request) is None
        
        request.headers = {"accept": "application/vnd.api+json"}
        assert extract_version_from_accept(request) is None
    
    def test_validate_api_version_valid(self):
        """Test API version validation with valid versions."""
        supported = ["1.0", "1.1", "2.0", "2.5"]
        
        assert validate_api_version("1.0", supported) == True
        assert validate_api_version("2.5", supported) == True
        assert validate_api_version("1.1", supported) == True
    
    def test_validate_api_version_invalid(self):
        """Test API version validation with invalid versions."""
        supported = ["1.0", "1.1", "2.0"]
        
        assert validate_api_version("3.0", supported) == False
        assert validate_api_version("0.9", supported) == False
        assert validate_api_version("invalid", supported) == False
        assert validate_api_version("", supported) == False
        assert validate_api_version(None, supported) == False


class TestPathRewriting:
    """Test path rewriting functionality."""
    
    def test_rewrite_path_for_version_add_prefix(self):
        """Test adding version prefix to unversioned paths."""
        assert rewrite_path_for_version("/users", "1.0") == "/v1/users"
        assert rewrite_path_for_version("/products/123", "2.0") == "/v2/products/123"
        assert rewrite_path_for_version("/orders", "1.5") == "/v1.5/orders"
    
    def test_rewrite_path_for_version_update_existing(self):
        """Test updating existing version prefix."""
        assert rewrite_path_for_version("/v1/users", "2.0") == "/v2/users"
        assert rewrite_path_for_version("/v1.0/products", "1.5") == "/v1.5/products"
        assert rewrite_path_for_version("/v2/orders/123", "1.0") == "/v1/orders/123"
    
    def test_rewrite_path_for_version_no_change_needed(self):
        """Test when path already has correct version."""
        assert rewrite_path_for_version("/v1/users", "1.0") == "/v1/users"
        assert rewrite_path_for_version("/v2/products", "2.0") == "/v2/products"
        assert rewrite_path_for_version("/v1.5/orders", "1.5") == "/v1.5/orders"
    
    def test_rewrite_path_for_version_edge_cases(self):
        """Test path rewriting edge cases."""
        # Root path
        assert rewrite_path_for_version("/", "1.0") == "/v1"
        
        # Path with query parameters (should preserve)
        assert rewrite_path_for_version("/users?limit=10", "2.0") == "/v2/users?limit=10"
        
        # Path with fragments (should preserve)
        assert rewrite_path_for_version("/users#section", "1.0") == "/v1/users#section"


class TestVersionHeaders:
    """Test version header handling."""
    
    def test_add_version_headers_basic(self):
        """Test adding basic version headers to response."""
        response = Mock(spec=JSONResponse)
        response.headers = {}
        
        supported_versions = ["1.0", "1.1", "2.0"]
        add_version_headers(response, "1.0", supported_versions)
        
        assert response.headers["X-API-Version"] == "1.0"
        assert "1.0" in response.headers["X-API-Supported-Versions"]
        assert "2.0" in response.headers["X-API-Supported-Versions"]
    
    def test_add_version_headers_custom_header_name(self):
        """Test adding version headers with custom header name."""
        response = Mock(spec=JSONResponse)
        response.headers = {}
        
        supported_versions = ["1.0", "2.0"]
        add_version_headers(response, "2.0", supported_versions, "API-Version")
        
        assert response.headers["API-Version"] == "2.0"
        assert response.headers["X-API-Supported-Versions"] == "1.0, 2.0"
    
    def test_add_version_headers_preserve_existing(self):
        """Test that existing headers are preserved."""
        response = Mock(spec=JSONResponse)
        response.headers = {"Content-Type": "application/json"}
        
        supported_versions = ["1.0"]
        add_version_headers(response, "1.0", supported_versions)
        
        assert response.headers["Content-Type"] == "application/json"
        assert response.headers["X-API-Version"] == "1.0"


class TestVersioningIntegration:
    """Integration tests for API versioning middleware."""
    
    @pytest.fixture
    def complex_app(self):
        """App with complex versioning scenarios."""
        app = FastAPI()
        
        # Multiple versions of same endpoint
        @app.get("/v1/users/{user_id}")
        async def get_user_v1(user_id: int):
            return {
                "version": "1.0",
                "user_id": user_id,
                "name": "John Doe"
            }
        
        @app.get("/v2/users/{user_id}")
        async def get_user_v2(user_id: int):
            return {
                "version": "2.0", 
                "user_id": user_id,
                "name": "John Doe",
                "email": "john@example.com",
                "metadata": {"created": "2023-01-01"}
            }
        
        # Unversioned endpoint that should get versioned
        @app.post("/orders")
        async def create_order():
            return {"order_id": 123, "status": "created"}
        
        # Version-specific POST endpoints
        @app.post("/v1/orders")
        async def create_order_v1():
            return {"version": "1.0", "order_id": 123}
        
        @app.post("/v2/orders")
        async def create_order_v2():
            return {"version": "2.0", "order_id": 123, "tracking": "abc123"}
        
        # Settings with multiple supported versions
        settings = Mock(spec=Settings)
        settings.api_versioning_enabled = True
        settings.api_default_version = "1.0"
        settings.api_supported_versions = ["1.0", "1.1", "2.0"]
        settings.api_version_header = "X-API-Version"
        
        app.add_middleware(APIVersioningMiddleware, settings=settings)
        return app
    
    def test_version_routing_get_requests(self, complex_app):
        """Test version-based routing for GET requests."""
        client = TestClient(complex_app)
        
        # Test v1 endpoint
        response = client.get("/v1/users/123")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"
        assert "email" not in data  # v1 doesn't have email
        
        # Test v2 endpoint  
        response = client.get("/v2/users/123")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0"
        assert "email" in data  # v2 has email
        assert "metadata" in data  # v2 has metadata
    
    def test_version_routing_post_requests(self, complex_app):
        """Test version-based routing for POST requests."""
        client = TestClient(complex_app)
        
        # Test unversioned POST with version header
        response = client.post("/orders", headers={"X-API-Version": "2.0"})
        assert response.status_code == 200
        # Should be routed to v2 endpoint
        
        # Test explicit v1 POST
        response = client.post("/v1/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"
        assert "tracking" not in data
        
        # Test explicit v2 POST
        response = client.post("/v2/orders") 
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0"
        assert "tracking" in data
    
    def test_content_negotiation_versioning(self, complex_app):
        """Test content negotiation with version parameters."""
        client = TestClient(complex_app)
        
        # Test Accept header with version
        response = client.get("/users/123", headers={
            "Accept": "application/vnd.api+json;version=2.0"
        })
        assert response.status_code == 200
        # Should route to v2 endpoint
    
    def test_version_precedence_complex(self, complex_app):
        """Test version precedence in complex scenarios."""
        client = TestClient(complex_app)
        
        # URL version should override header version
        response = client.get("/v1/users/123", headers={
            "X-API-Version": "2.0",
            "Accept": "application/vnd.api+json;version=2.0"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"  # Should use URL version (v1)
    
    def test_error_responses_include_version_info(self, complex_app):
        """Test that error responses include version information."""
        client = TestClient(complex_app)
        
        # Test unsupported version
        response = client.get("/users/123", headers={"X-API-Version": "9.0"})
        assert response.status_code == 400
        
        data = response.json()
        assert "supported_versions" in data
        assert "1.0" in data["supported_versions"]
        assert "2.0" in data["supported_versions"]


@pytest.mark.slow
class TestVersioningPerformance:
    """Performance tests for API versioning middleware."""
    
    @pytest.fixture
    def performance_app(self):
        """App configured for performance testing."""
        app = FastAPI()
        
        @app.get("/v1/test")
        async def test_v1():
            return {"version": "1.0"}
        
        @app.get("/v2/test")
        async def test_v2():
            return {"version": "2.0"}
        
        settings = Mock(spec=Settings)
        settings.api_versioning_enabled = True
        settings.api_default_version = "1.0"
        settings.api_supported_versions = ["1.0", "1.1", "2.0"]
        settings.api_version_header = "X-API-Version"
        
        app.add_middleware(APIVersioningMiddleware, settings=settings)
        return app
    
    def test_versioning_performance_overhead(self, performance_app):
        """Test performance overhead of versioning middleware."""
        import time
        
        client = TestClient(performance_app)
        
        # Measure response time with versioning
        start_time = time.time()
        for _ in range(100):
            response = client.get("/v1/test")
            assert response.status_code == 200
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_request = total_time / 100
        
        # Versioning should add minimal overhead (< 5ms per request)
        assert avg_time_per_request < 0.005, f"Average time per request: {avg_time_per_request:.3f}s"
    
    def test_version_detection_performance(self):
        """Test performance of version detection functions."""
        import time
        
        # Test URL version extraction performance
        start_time = time.time()
        for _ in range(10000):
            extract_version_from_url("/v2/users/123/orders")
        end_time = time.time()
        
        extraction_time = end_time - start_time
        assert extraction_time < 1.0, f"URL extraction took too long: {extraction_time:.3f}s"