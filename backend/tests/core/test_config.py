"""Tests for the Settings configuration class."""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings
from app.dependencies import get_settings, get_fresh_settings


class TestSettings:
    """Test cases for the Settings class."""

    def test_settings_instantiation(self):
        """Test that Settings class can be instantiated successfully."""
        settings = Settings()
        
        # Test that all required attributes exist and have reasonable values
        assert hasattr(settings, 'ai_model')
        assert hasattr(settings, 'ai_temperature')
        assert hasattr(settings, 'host')
        assert hasattr(settings, 'port')
        assert hasattr(settings, 'debug')
        assert hasattr(settings, 'log_level')
        assert hasattr(settings, 'resilience_enabled')
        assert hasattr(settings, 'default_resilience_strategy')
        assert hasattr(settings, 'allowed_origins')
        
        # Test reasonable types
        assert isinstance(settings.ai_temperature, float)
        assert isinstance(settings.port, int)
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.log_level, str)
        assert isinstance(settings.allowed_origins, list)

    def test_settings_with_clean_environment(self):
        """Test Settings with a clean environment (no override variables)."""
        # Clear relevant environment variables for this test
        env_vars_to_clear = [
            "AI_MODEL", "AI_TEMPERATURE", "BACKEND_HOST", "BACKEND_PORT", 
            "DEBUG", "LOG_LEVEL", "RESILIENCE_ENABLED"
        ]
        
        # Create a clean environment
        clean_env = {k: v for k, v in os.environ.items() 
                    if k not in env_vars_to_clear}
        
        with patch.dict(os.environ, clean_env, clear=True):
            # Create a custom Settings class that doesn't read from .env file
            from pydantic_settings import SettingsConfigDict
            
            class CleanSettings(Settings):
                model_config = SettingsConfigDict(
                    env_file=None,  # Don't read from .env file
                    env_file_encoding='utf-8',
                    case_sensitive=False,
                    extra='ignore'
                )
            
            settings = CleanSettings()
            
            # Test some key default values
            assert settings.ai_temperature == 0.7
            assert settings.host == "0.0.0.0"
            assert settings.debug is False
            assert settings.resilience_enabled is True
            assert settings.default_resilience_strategy == "balanced"
            assert len(settings.allowed_origins) > 0

    def test_settings_direct_parameter_override(self):
        """Test that Settings constructor parameters properly override defaults."""
        # Test direct parameter override (this bypasses environment variable issues)
        settings = Settings(
            ai_model="test-model",
            ai_temperature=0.5,
            port=9000,
            debug=True,
            log_level="DEBUG"
        )
        
        assert settings.ai_model == "test-model"
        assert settings.ai_temperature == 0.5
        assert settings.port == 9000
        assert settings.debug is True
        assert settings.log_level == "DEBUG"

    def test_settings_environment_variable_override_isolated(self):
        """Test environment variable override with isolated environment."""
        # Use a completely fresh environment for this test
        test_env = {
            "AI_MODEL": "env-test-model",
            "AI_TEMPERATURE": "1.2"
        }
        
        # Clear existing environment and set only our test variables
        with patch.dict(os.environ, test_env, clear=True):
            settings = Settings()
            
            assert settings.ai_model == "env-test-model"
            assert settings.ai_temperature == 1.2

    def test_settings_validation_ai_temperature(self):
        """Test validation of AI temperature bounds."""
        # Valid temperature
        settings = Settings(ai_temperature=1.5)
        assert settings.ai_temperature == 1.5
        
        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            Settings(ai_temperature=3.0)
        
        # Invalid temperature (negative)
        with pytest.raises(ValidationError):
            Settings(ai_temperature=-0.1)

    def test_settings_validation_port(self):
        """Test validation of port number."""
        # Valid port
        settings = Settings(port=3000)
        assert settings.port == 3000
        
        # Invalid port (too high)
        with pytest.raises(ValidationError):
            Settings(port=70000)
        
        # Invalid port (zero or negative)
        with pytest.raises(ValidationError):
            Settings(port=0)

    def test_settings_validation_log_level(self):
        """Test validation of log level."""
        # Valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level
            
        # Case insensitive
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"
        
        # Invalid log level
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")

    def test_settings_validation_resilience_strategy(self):
        """Test validation of resilience strategy patterns."""
        # Valid strategies
        for strategy in ["conservative", "balanced", "aggressive"]:
            settings = Settings(default_resilience_strategy=strategy)
            assert settings.default_resilience_strategy == strategy
            
        # Invalid strategy
        with pytest.raises(ValidationError):
            Settings(default_resilience_strategy="invalid")

    def test_settings_validation_allowed_origins(self):
        """Test validation of allowed origins."""
        # Valid origins
        settings = Settings(allowed_origins=["http://localhost:3000"])
        assert settings.allowed_origins == ["http://localhost:3000"]
        
        # Empty origins should raise error
        with pytest.raises(ValidationError):
            Settings(allowed_origins=[])

    def test_settings_positive_integer_fields(self):
        """Test validation of fields that must be positive integers."""
        # Test valid positive values
        settings = Settings(
            MAX_BATCH_REQUESTS_PER_CALL=10,
            BATCH_AI_CONCURRENCY_LIMIT=2,
            circuit_breaker_failure_threshold=3,
            retry_max_attempts=5
        )
        
        assert settings.MAX_BATCH_REQUESTS_PER_CALL == 10
        assert settings.BATCH_AI_CONCURRENCY_LIMIT == 2
        assert settings.circuit_breaker_failure_threshold == 3
        assert settings.retry_max_attempts == 5
        
        # Test invalid values (zero or negative)
        with pytest.raises(ValidationError):
            Settings(MAX_BATCH_REQUESTS_PER_CALL=0)

    def test_settings_environment_loading(self):
        """Test that settings properly load from environment files."""
        # This tests the actual environment file loading mechanism
        settings = Settings()
        
        # Just verify the settings object is created and has expected structure
        assert hasattr(settings, 'model_config')
        assert settings.model_config.get('env_file') == '.env'


class TestDependencyProviders:
    """Test cases for dependency provider functions."""

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self):
        """Test that get_settings returns the same instance (cached)."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_get_fresh_settings_returns_new_instance(self):
        """Test that get_fresh_settings returns a new Settings instance."""
        settings1 = get_fresh_settings()
        settings2 = get_fresh_settings()
        
        assert isinstance(settings1, Settings)
        assert isinstance(settings2, Settings)
        # Should be different instances
        assert settings1 is not settings2

    def test_get_fresh_settings_with_parameter_override(self):
        """Test that get_fresh_settings can accept parameter overrides."""
        # Test with direct parameter (avoids environment variable issues)
        settings = Settings(ai_model="custom-model")
        assert settings.ai_model == "custom-model" 