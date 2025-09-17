"""
Tests for enhanced middleware compatibility.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI

from app.core.middleware import setup_middleware
from app.core.config import Settings


class TestEnhancedMiddlewareCompatibility:
    """Test compatibility between core and enhanced middleware."""

    def test_enhanced_middleware_imports(self):
        """Test that enhanced middleware components can be imported."""
        try:
            from app.core.middleware.rate_limiting import RateLimitMiddleware
            from app.core.middleware.api_versioning import APIVersioningMiddleware
            from app.core.middleware.compression import CompressionMiddleware
            from app.core.middleware.request_size import RequestSizeLimitMiddleware

            # All imports should succeed
            assert RateLimitMiddleware is not None
            assert APIVersioningMiddleware is not None
            assert CompressionMiddleware is not None
            assert RequestSizeLimitMiddleware is not None

        except ImportError as e:
            pytest.fail(f"Enhanced middleware import failed: {e}")

    def test_enhanced_middleware_in_setup(self):
        """Test that enhanced middleware can be integrated with setup_middleware."""
        app = FastAPI()

        # Mock enhanced middleware settings
        settings = Mock(spec=Settings)
        settings.security_headers_enabled = True
        settings.request_logging_enabled = True
        settings.performance_monitoring_enabled = True
        settings.allowed_origins = ["*"]

        # Enhanced middleware settings
        settings.rate_limiting_enabled = True
        settings.api_versioning_enabled = True
        settings.compression_enabled = True

        with patch('app.core.middleware.SecurityMiddleware'), \
             patch('app.core.middleware.RequestLoggingMiddleware'), \
             patch('app.core.middleware.PerformanceMonitoringMiddleware'):

            # Should not raise any errors
            setup_middleware(app, settings)

            # Middleware should be configured
            assert len(app.user_middleware) > 0
