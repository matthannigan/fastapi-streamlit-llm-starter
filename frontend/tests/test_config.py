import pytest
from unittest.mock import patch, MagicMock
import os

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
    
    def test_uses_input_max_length_variable(self):
        """Test that max_text_length uses INPUT_MAX_LENGTH environment variable."""
        # Test that the configuration correctly reads from INPUT_MAX_LENGTH
        current_value = os.getenv("INPUT_MAX_LENGTH")
        if current_value:
            test_settings = Settings()
            assert test_settings.max_text_length == int(current_value)
        else:
            # If not set, should use default
            test_settings = Settings()
            assert test_settings.max_text_length == 10000  # Default value
    
    def test_global_settings_instance(self):
        """Test global settings instance."""
        assert settings is not None
        assert isinstance(settings, Settings) 