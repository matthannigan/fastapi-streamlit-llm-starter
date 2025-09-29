"""
Infrastructure-specific fixtures for testing.
"""
import pytest
from unittest.mock import patch
import hashlib
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional


@pytest.fixture
def mock_infrastructure_config():
    """Mock configuration for infrastructure components."""
    return {
        "cache_enabled": True,
        "resilience_enabled": True,
        "monitoring_enabled": True
    }

# =============================================================================
# Mock Settings Fixtures
# =============================================================================

@pytest.fixture
def test_settings():
    """
    Real Settings instance with test configuration for testing actual configuration behavior.
    
    Provides a Settings instance loaded from test configuration, enabling tests
    to verify actual configuration loading, validation, and environment detection
    instead of using hardcoded mock values.
    
    This fixture represents behavior-driven testing where we test the actual
    Settings class functionality rather than mocking its behavior.
    """
    import tempfile
    import json
    import os
    from app.core.config import Settings
    
    # Create test configuration with realistic values
    test_config = {
        "gemini_api_key": "test-gemini-api-key-12345",
        "ai_model": "gemini-2.0-flash-exp", 
        "ai_temperature": 0.7,
        "host": "0.0.0.0",
        "port": 8000,
        "api_key": "test-api-key-12345",
        "additional_api_keys": "key1,key2,key3",
        "debug": False,
        "log_level": "INFO",
        "cache_preset": "development",
        "resilience_preset": "simple",
        "health_check_timeout_ms": 2000
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        config_file = f.name
    
    try:
        # Create Settings instance with test config
        # Override environment variables to ensure test isolation
        test_env = {
            "GEMINI_API_KEY": "test-gemini-api-key-12345",
            "API_KEY": "test-api-key-12345",
            "CACHE_PRESET": "development",
            "RESILIENCE_PRESET": "simple"
        }
        
        # Temporarily set test environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        # Create real Settings instance
        settings = Settings()
        
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        
        return settings
        
    finally:
        # Clean up temporary config file
        os.unlink(config_file)


@pytest.fixture
def development_settings():
    """
    Real Settings instance configured for development environment testing.
    
    Provides Settings with development preset for testing development-specific behavior.
    """
    import os
    
    # Set development environment variables
    test_env = {
        "GEMINI_API_KEY": "test-dev-api-key",
        "API_KEY": "test-dev-api-key", 
        "CACHE_PRESET": "development",
        "RESILIENCE_PRESET": "development",
        "DEBUG": "true"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
        
    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture  
def production_settings():
    """
    Real Settings instance configured for production environment testing.
    
    Provides Settings with production preset for testing production-specific behavior.
    """
    import os
    
    # Set production environment variables
    test_env = {
        "GEMINI_API_KEY": "test-prod-api-key",
        "API_KEY": "test-prod-api-key",
        "CACHE_PRESET": "production", 
        "RESILIENCE_PRESET": "production",
        "DEBUG": "false"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
        
    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
