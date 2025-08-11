"""
Tests for the main middleware setup function.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import FastAPI

from app.core.middleware import setup_middleware
from app.core.config import Settings


class TestMiddlewareSetup:
    """Test the main middleware setup function."""

    @pytest.fixture
    def settings(self):
        """Test settings with all middleware enabled."""
        settings = Mock(spec=Settings)
        settings.security_headers_enabled = True
        settings.request_logging_enabled = True
        settings.performance_monitoring_enabled = True
        settings.allowed_origins = ["*"]
        settings.log_level = "INFO"
        return settings

    @pytest.fixture
    def app(self):
        """Basic FastAPI app for testing."""
        return FastAPI(title="Test App")

    def test_setup_middleware_all_enabled(self, app, settings):
        """Test middleware setup with all components enabled."""
        with patch('app.core.middleware.logger') as mock_logger:
            setup_middleware(app, settings)

            # Verify all middleware setup logging
            assert mock_logger.info.call_count >= 4  # Multiple setup log calls

            # Verify middleware were added to app
            assert len(app.user_middleware) > 0

    def test_setup_middleware_selective_disable(self, app):
        """Test middleware setup with some components disabled."""
        settings = Mock(spec=Settings)
        settings.security_headers_enabled = False
        settings.request_logging_enabled = True
        settings.performance_monitoring_enabled = False
        settings.allowed_origins = ["http://localhost:3000"]

        with patch('app.core.middleware.logger') as mock_logger:
            setup_middleware(app, settings)

            # Should still have some middleware but not all
            mock_logger.info.assert_called()

    def test_setup_middleware_enhanced_components(self, app):
        """Test setup with enhanced middleware components."""
        settings = Mock(spec=Settings)

        # Enhanced middleware settings
        settings.security_headers_enabled = True
        settings.request_logging_enabled = True
        settings.performance_monitoring_enabled = True
        settings.allowed_origins = ["*"]

        # Enhanced middleware specific settings
        settings.rate_limiting_enabled = True
        settings.api_versioning_enabled = True
        settings.compression_enabled = True
        settings.request_size_limits = {}

        with patch('app.core.middleware.logger'):
            setup_middleware(app, settings)

            # Should have middleware stack configured
            assert len(app.user_middleware) > 0
