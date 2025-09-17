"""
Integration tests for core middleware functionality.
"""
import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware import (
    setup_cors_middleware,
    setup_global_exception_handler
)
from app.core.config import Settings


class TestMiddlewareIntegration:
    """Integration tests for core middleware functionality."""

    @pytest.fixture
    def middleware_app(self):
        """App with core middleware for integration testing."""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "ok"}

        # Basic settings for core middleware
        settings = Mock(spec=Settings)
        settings.security_headers_enabled = False  # Disable to avoid mocking issues
        settings.request_logging_enabled = False   # Disable to avoid mocking issues
        settings.performance_monitoring_enabled = False  # Disable to avoid mocking issues
        settings.allowed_origins = ["*"]
        settings.log_level = "INFO"

        # Only setup basic CORS and exception handling without complex middleware
        setup_cors_middleware(app, settings)
        setup_global_exception_handler(app, settings)

        return app

    def test_middleware_app_basic_functionality(self, middleware_app):
        """Test basic functionality with middleware stack."""
        client = TestClient(middleware_app)

        response = client.get("/test")
        assert response.status_code == 200
        assert response.json()["message"] == "test"

    def test_health_check_endpoint(self, middleware_app):
        """Test health check endpoint with middleware."""
        client = TestClient(middleware_app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
