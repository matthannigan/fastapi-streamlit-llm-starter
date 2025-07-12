"""
Unit tests for resilience preset system.

Tests preset loading, validation, conversion, and integration with Settings class.
"""

import pytest
import json
import os
from unittest.mock import patch

from app.core.config import Settings
from app.infrastructure.resilience.config_presets import (
    ResilienceStrategy, 
    ResilienceConfig,
    ResiliencePreset, 
    PresetManager, 
    PRESETS,
    preset_manager
)


class TestResiliencePreset:
    """Test ResiliencePreset data model."""
    
    def test_preset_creation(self):
        """Test creating a resilience preset."""
        preset = ResiliencePreset(
            name="Test",
            description="Test preset",
            retry_attempts=3,
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={"qa": ResilienceStrategy.CRITICAL},
            environment_contexts=["test"]
        )
        
        assert preset.name == "Test"
        assert preset.retry_attempts == 3
        assert preset.default_strategy == ResilienceStrategy.BALANCED
        assert preset.operation_overrides["qa"] == ResilienceStrategy.CRITICAL
    
    def test_preset_to_dict(self):
        """Test converting preset to dictionary."""
        preset = PRESETS["simple"]
        preset_dict = preset.to_dict()
        
        assert isinstance(preset_dict, dict)
        assert preset_dict["name"] == "Simple"
        assert preset_dict["retry_attempts"] == 3
        assert preset_dict["default_strategy"] == ResilienceStrategy.BALANCED
    
    def test_preset_to_resilience_config(self):
        """Test converting preset to ResilienceConfig."""
        preset = PRESETS["simple"]
        config = preset.to_resilience_config()
        
        assert isinstance(config, ResilienceConfig)
        assert config.retry_config.max_attempts == 3
        assert config.circuit_breaker_config.failure_threshold == 5
        assert config.strategy == ResilienceStrategy.BALANCED


class TestPresetManager:
    """Test PresetManager functionality."""
    
    def test_preset_manager_initialization(self):
        """Test preset manager initialization."""
        manager = PresetManager()
        assert len(manager.presets) == 3
        assert "simple" in manager.presets
        assert "development" in manager.presets
        assert "production" in manager.presets
    
    def test_get_preset_valid(self):
        """Test getting a valid preset."""
        manager = PresetManager()
        preset = manager.get_preset("simple")
        
        assert preset.name == "Simple"
        assert preset.retry_attempts == 3
        assert preset.circuit_breaker_threshold == 5
    
    def test_get_preset_invalid(self):
        """Test getting an invalid preset raises ValueError."""
        manager = PresetManager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.get_preset("invalid")
        
        assert "Unknown preset 'invalid'" in str(exc_info.value)
        assert "Available presets" in str(exc_info.value)
    
    def test_list_presets(self):
        """Test listing all preset names."""
        manager = PresetManager()
        presets = manager.list_presets()
        
        assert len(presets) == 3
        assert "simple" in presets
        assert "development" in presets
        assert "production" in presets
    
    def test_get_preset_details(self):
        """Test getting detailed preset information."""
        manager = PresetManager()
        details = manager.get_preset_details("development")
        
        assert details["name"] == "Development"
        assert details["description"] == "Fast-fail configuration optimized for development speed"
        assert details["configuration"]["retry_attempts"] == 2
        assert details["configuration"]["default_strategy"] == "aggressive"
        assert "development" in details["environment_contexts"]
    
    def test_validate_preset_valid(self):
        """Test validating a valid preset."""
        manager = PresetManager()
        preset = PRESETS["simple"]
        
        assert manager.validate_preset(preset) is True
    
    def test_validate_preset_invalid_retry_attempts(self):
        """Test validating preset with invalid retry attempts."""
        manager = PresetManager()
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Invalid preset",
            retry_attempts=15,  # Invalid: > 10
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["test"]
        )
        
        assert manager.validate_preset(invalid_preset) is False
    
    def test_validate_preset_invalid_circuit_breaker_threshold(self):
        """Test validating preset with invalid circuit breaker threshold."""
        manager = PresetManager()
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Invalid preset",
            retry_attempts=3,
            circuit_breaker_threshold=25,  # Invalid: > 20
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["test"]
        )
        
        assert manager.validate_preset(invalid_preset) is False
    
    def test_validate_preset_invalid_recovery_timeout(self):
        """Test validating preset with invalid recovery timeout."""
        manager = PresetManager()
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Invalid preset",
            retry_attempts=3,
            circuit_breaker_threshold=5,
            recovery_timeout=5,  # Invalid: < 10
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["test"]
        )
        
        assert manager.validate_preset(invalid_preset) is False
    
    @pytest.mark.parametrize("environment,expected", [
        ("development", "development"),
        ("dev", "development"),
        ("testing", "development"),
        ("test", "development"),
        ("staging", "production"),
        ("stage", "production"),
        ("production", "production"),
        ("prod", "production"),
        ("unknown", "simple")
    ])
    def test_recommend_preset(self, environment, expected):
        """Test preset recommendations for different environments."""
        manager = PresetManager()
        recommendation = manager.recommend_preset(environment)
        assert recommendation == expected
    
    def test_get_all_presets_summary(self):
        """Test getting summary of all presets."""
        manager = PresetManager()
        summary = manager.get_all_presets_summary()
        
        assert len(summary) == 3
        assert "simple" in summary
        assert "development" in summary
        assert "production" in summary
        
        # Check structure of summary
        simple_summary = summary["simple"]
        assert "name" in simple_summary
        assert "description" in simple_summary
        assert "configuration" in simple_summary
        assert "environment_contexts" in simple_summary


class TestPresetDefinitions:
    """Test the predefined presets match specifications."""
    
    def test_simple_preset_specification(self):
        """Test simple preset matches PRD specification."""
        preset = PRESETS["simple"]
        
        assert preset.name == "Simple"
        assert preset.retry_attempts == 3
        assert preset.circuit_breaker_threshold == 5
        assert preset.recovery_timeout == 60
        assert preset.default_strategy == ResilienceStrategy.BALANCED
        assert preset.operation_overrides == {}
        assert "development" in preset.environment_contexts
        assert "production" in preset.environment_contexts
    
    def test_development_preset_specification(self):
        """Test development preset matches PRD specification."""
        preset = PRESETS["development"]
        
        assert preset.name == "Development"
        assert preset.retry_attempts == 2
        assert preset.circuit_breaker_threshold == 3
        assert preset.recovery_timeout == 30
        assert preset.default_strategy == ResilienceStrategy.AGGRESSIVE
        assert preset.operation_overrides["sentiment"] == ResilienceStrategy.AGGRESSIVE
        assert preset.operation_overrides["qa"] == ResilienceStrategy.BALANCED
        assert "development" in preset.environment_contexts
        assert "testing" in preset.environment_contexts
    
    def test_production_preset_specification(self):
        """Test production preset matches PRD specification."""
        preset = PRESETS["production"]
        
        assert preset.name == "Production"
        assert preset.retry_attempts == 5
        assert preset.circuit_breaker_threshold == 10
        assert preset.recovery_timeout == 120
        assert preset.default_strategy == ResilienceStrategy.CONSERVATIVE
        assert preset.operation_overrides["qa"] == ResilienceStrategy.CRITICAL
        assert preset.operation_overrides["sentiment"] == ResilienceStrategy.AGGRESSIVE
        assert preset.operation_overrides["summarize"] == ResilienceStrategy.CONSERVATIVE
        assert "production" in preset.environment_contexts
        assert "staging" in preset.environment_contexts


class TestSettingsIntegration:
    """Test Settings class integration with preset system."""
    
    def test_default_resilience_preset(self):
        """Test default resilience preset setting."""
        settings = Settings()
        assert settings.resilience_preset == "simple"
    
    def test_resilience_preset_validation_valid(self):
        """Test valid resilience preset passes validation."""
        # This should not raise an exception
        settings = Settings(resilience_preset="development")
        assert settings.resilience_preset == "development"
    
    def test_resilience_preset_validation_invalid(self):
        """Test invalid resilience preset fails validation."""
        with pytest.raises(ValueError) as exc_info:
            Settings(resilience_preset="invalid")
        
        assert "Invalid resilience_preset 'invalid'" in str(exc_info.value)
    
    def test_has_legacy_resilience_config_false(self):
        """Test detecting no legacy config when using presets."""
        settings = Settings(resilience_preset="simple")
        assert settings._has_legacy_resilience_config() is False
    
    @patch.dict(os.environ, {
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10",
        "RETRY_MAX_ATTEMPTS": "5"
    })
    def test_has_legacy_resilience_config_true_env_vars(self):
        """Test detecting legacy config from environment variables."""
        settings = Settings()
        assert settings._has_legacy_resilience_config() is True
    
    def test_has_legacy_resilience_config_true_modified_defaults(self):
        """Test detecting legacy config from modified default values."""
        settings = Settings(
            circuit_breaker_failure_threshold=10,  # Changed from default of 5
            resilience_preset="simple"
        )
        assert settings._has_legacy_resilience_config() is True
    
    def test_get_resilience_config_preset(self):
        """Test getting resilience config from preset."""
        settings = Settings(resilience_preset="development")
        config = settings.get_resilience_config()
        
        assert isinstance(config, ResilienceConfig)
        assert config.retry_config.max_attempts == 2
        assert config.circuit_breaker_config.failure_threshold == 3
        assert config.strategy == ResilienceStrategy.AGGRESSIVE
    
    @patch.dict(os.environ, {
        "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8",
        "RETRY_MAX_ATTEMPTS": "4",
        "DEFAULT_RESILIENCE_STRATEGY": "conservative"
    })
    def test_get_resilience_config_legacy(self):
        """Test getting resilience config from legacy settings."""
        settings = Settings()
        config = settings.get_resilience_config()
        
        assert isinstance(config, ResilienceConfig)
        assert config.retry_config.max_attempts == 4
        assert config.circuit_breaker_config.failure_threshold == 8
        assert config.strategy == ResilienceStrategy.CONSERVATIVE
    
    def test_get_resilience_config_with_custom_overrides(self):
        """Test getting resilience config with custom JSON overrides."""
        custom_config = json.dumps({
            "retry_attempts": 7,
            "circuit_breaker_threshold": 12
        })
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=custom_config
        )
        config = settings.get_resilience_config()
        
        assert config.retry_config.max_attempts == 7
        assert config.circuit_breaker_config.failure_threshold == 12
    
    def test_get_resilience_config_invalid_custom_json(self):
        """Test handling invalid JSON in custom config."""
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config="invalid json"
        )
        
        # Should fall back to preset without custom config
        config = settings.get_resilience_config()
        assert config.retry_config.max_attempts == 3  # Simple preset default
    
    def test_get_resilience_config_fallback_on_error(self):
        """Test fallback to simple preset on error."""
        # Mock the preset_manager import inside the method - use the correct import path
        with patch('app.infrastructure.resilience.preset_manager') as mock_manager:
            # First call (production preset) fails, second call (simple fallback) succeeds
            simple_preset = PRESETS["simple"]
            mock_manager.get_preset.side_effect = [Exception("Test error"), simple_preset]
            
            settings = Settings(resilience_preset="production")
            config = settings.get_resilience_config()
            
            # Should fall back to simple preset
            assert config.retry_config.max_attempts == 3
    
    @pytest.mark.parametrize("operation,expected_legacy,expected_preset", [
        ("summarize", "balanced", "conservative"),  # Production preset has conservative default
        ("sentiment", "aggressive", "aggressive"),
        ("qa", "conservative", "critical"),
        ("unknown", "balanced", "conservative")  # Production preset has conservative default
    ])
    def test_get_operation_strategy(self, operation, expected_legacy, expected_preset):
        """Test getting operation-specific strategies."""
        # Test with preset configuration (production has overrides)
        settings = Settings(resilience_preset="production")
        strategy = settings.get_operation_strategy(operation)
        assert strategy == expected_preset
        
        # Test with legacy configuration
        with patch.object(settings, '_has_legacy_resilience_config', return_value=True):
            if operation != "unknown":
                strategy = settings.get_operation_strategy(operation)
                assert strategy == expected_legacy
    
    def test_get_operation_strategy_fallback(self):
        """Test operation strategy fallback on error."""
        settings = Settings()
        
        # Mock the preset_manager import inside the method - use the correct import path
        with patch('app.infrastructure.resilience.preset_manager') as mock_manager:
            mock_manager.get_preset.side_effect = Exception("Test error")
            
            strategy = settings.get_operation_strategy("summarize")
            assert strategy == "balanced"  # Safe fallback


class TestGlobalPresetManager:
    """Test the global preset manager instance."""
    
    def test_global_preset_manager_available(self):
        """Test global preset manager is available."""
        assert preset_manager is not None
        assert isinstance(preset_manager, PresetManager)
        assert len(preset_manager.presets) == 3
    
    def test_global_preset_manager_functionality(self):
        """Test global preset manager functionality."""
        # Should work the same as a new instance
        preset = preset_manager.get_preset("simple")
        assert preset.name == "Simple"
        
        presets = preset_manager.list_presets()
        assert len(presets) == 3