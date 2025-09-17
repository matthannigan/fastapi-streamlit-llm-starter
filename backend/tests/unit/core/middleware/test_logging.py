"""
Tests for middleware logging.
"""
import logging
from unittest.mock import Mock, patch
from app.core.config import Settings
from app.core.middleware import configure_middleware_logging


class TestMiddlewareLogging:
    """Test middleware logging configuration."""

    def test_configure_middleware_logging(self):
        """Test middleware logging configuration."""
        settings = Mock(spec=Settings)
        settings.log_level = "DEBUG"

        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_handler_class:

            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            mock_logger.handlers = []  # No existing handlers

            mock_handler = Mock()
            mock_handler_class.return_value = mock_handler

            configure_middleware_logging(settings)

            # Should configure multiple middleware loggers
            assert mock_get_logger.call_count >= 3

            # Should set log level
            mock_logger.setLevel.assert_called_with(logging.DEBUG)

    def test_configure_middleware_logging_existing_handlers(self):
        """Test middleware logging when handlers already exist."""
        settings = Mock(spec=Settings)
        settings.log_level = "INFO"

        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_logger.handlers = [Mock()]  # Existing handler
            mock_get_logger.return_value = mock_logger

            configure_middleware_logging(settings)

            # Should still set log level
            mock_logger.setLevel.assert_called_with(logging.INFO)
            # But shouldn't add new handlers
            mock_logger.addHandler.assert_not_called()
