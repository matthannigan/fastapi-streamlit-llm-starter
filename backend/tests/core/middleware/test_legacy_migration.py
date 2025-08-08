"""
Tests for legacy middleware migration.
"""
from unittest.mock import Mock, patch
from fastapi import FastAPI
from app.core.config import Settings
from app.core.middleware import migrate_from_main_py_middleware


class TestLegacyMigration:
    """Test legacy middleware migration functionality."""

    def test_migrate_from_main_py_middleware(self):
        """Test migration from main.py style middleware."""
        app = FastAPI()
        settings = Mock(spec=Settings)
        settings.allowed_origins = ["*"]

        with patch('app.core.middleware.logger') as mock_logger, \
             patch('app.core.middleware.setup_cors_middleware') as mock_cors, \
             patch('app.core.middleware.setup_global_exception_handler') as mock_exception:

            migrate_from_main_py_middleware(app, settings)

            # Should log warning about legacy migration
            mock_logger.warning.assert_called_once()

            # Should set up basic middleware
            mock_cors.assert_called_once_with(app, settings)
            mock_exception.assert_called_once_with(app, settings)

            # Should log completion
            mock_logger.info.assert_called_with("Legacy middleware migration complete")
