import pytest
from unittest.mock import patch
import os
import sys

# Add the parent directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Settings, settings

class TestSettings:
    """Test the Settings configuration class."""
    
    def test_default_values(self):
        """Test configuration values (including .env file loading)."""
        # Test the actual behavior which includes .env file loading
        test_settings = Settings()
        
        # These values come from .env file or defaults
        assert test_settings.api_base_url in ["http://backend:8000", "http://localhost:8000"]  # Could be either depending on .env
        assert test_settings.page_title == "AI Text Processor"
        assert test_settings.page_icon == "🤖"
        assert test_settings.layout == "wide"
        # show_debug_info and max_text_length depend on .env file, so test they exist
        assert isinstance(test_settings.show_debug_info, bool)
        assert isinstance(test_settings.max_text_length, int)
        assert test_settings.max_text_length > 0
    
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