import pytest
from unittest.mock import patch
import os

from frontend.app.config import Settings, settings

class TestSettings:
    """Test the Settings configuration class."""
    
    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            test_settings = Settings()
            
            assert test_settings.api_base_url == "http://backend:8000"
            assert test_settings.page_title == "AI Text Processor"
            assert test_settings.page_icon == "🤖"
            assert test_settings.layout == "wide"
            assert test_settings.show_debug_info is False
            assert test_settings.max_text_length == 10000
    
    def test_environment_override(self):
        """Test environment variable overrides."""
        env_vars = {
            "API_BASE_URL": "http://localhost:8000",
            "SHOW_DEBUG_INFO": "true",
            "MAX_TEXT_LENGTH": "5000"
        }
        
        with patch.dict(os.environ, env_vars):
            test_settings = Settings()
            
            assert test_settings.api_base_url == "http://localhost:8000"
            assert test_settings.show_debug_info is True
            assert test_settings.max_text_length == 5000
    
    def test_global_settings_instance(self):
        """Test global settings instance."""
        assert settings is not None
        assert isinstance(settings, Settings) 