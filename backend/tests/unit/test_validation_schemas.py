"""
Unit tests for JSON schema validation system.

Tests validation of custom resilience configurations and presets.
"""

import pytest
import json
from unittest.mock import patch

from app.validation_schemas import (
    ResilienceConfigValidator,
    ValidationResult,
    config_validator,
    RESILIENCE_CONFIG_SCHEMA,
    PRESET_SCHEMA
)


class TestValidationResult:
    """Test ValidationResult class."""
    
    def test_validation_result_creation(self):
        """Test creating validation results."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert bool(result) is True
    
    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        errors = ["Field error", "Another error"]
        result = ValidationResult(is_valid=False, errors=errors)
        assert result.is_valid is False
        assert result.errors == errors
        assert bool(result) is False
    
    def test_validation_result_to_dict(self):
        """Test converting validation result to dictionary."""
        warnings = ["Warning message"]
        result = ValidationResult(is_valid=True, warnings=warnings)
        result_dict = result.to_dict()
        
        assert result_dict["is_valid"] is True
        assert result_dict["errors"] == []
        assert result_dict["warnings"] == warnings


class TestResilienceConfigValidator:
    """Test resilience configuration validator."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = ResilienceConfigValidator()
        
        # Should initialize successfully regardless of jsonschema availability
        assert validator is not None
    
    def test_valid_custom_config(self):
        """Test validation of valid custom configuration."""
        valid_config = {
            "retry_attempts": 5,
            "circuit_breaker_threshold": 8,
            "recovery_timeout": 90
        }
        
        result = config_validator.validate_custom_config(valid_config)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_custom_config_with_all_fields(self):
        """Test validation with all possible fields."""
        comprehensive_config = {
            "retry_attempts": 4,
            "circuit_breaker_threshold": 6,
            "recovery_timeout": 120,
            "default_strategy": "balanced",
            "operation_overrides": {
                "summarize": "conservative",
                "sentiment": "aggressive"
            },
            "exponential_multiplier": 1.5,
            "exponential_min": 2.0,
            "exponential_max": 15.0,
            "jitter_enabled": True,
            "jitter_max": 3.0,
            "max_delay_seconds": 180
        }
        
        result = config_validator.validate_custom_config(comprehensive_config)
        assert result.is_valid is True
    
    def test_invalid_retry_attempts(self):
        """Test validation with invalid retry attempts."""
        invalid_configs = [
            {"retry_attempts": 0},  # Too low
            {"retry_attempts": 15}, # Too high
            {"retry_attempts": "invalid"}, # Wrong type
        ]
        
        for config in invalid_configs:
            result = config_validator.validate_custom_config(config)
            assert result.is_valid is False
            assert len(result.errors) > 0
    
    def test_invalid_circuit_breaker_threshold(self):
        """Test validation with invalid circuit breaker threshold."""
        invalid_configs = [
            {"circuit_breaker_threshold": 0},   # Too low
            {"circuit_breaker_threshold": 25},  # Too high
            {"circuit_breaker_threshold": -1},  # Negative
        ]
        
        for config in invalid_configs:
            result = config_validator.validate_custom_config(config)
            assert result.is_valid is False
            assert len(result.errors) > 0
    
    def test_invalid_recovery_timeout(self):
        """Test validation with invalid recovery timeout."""
        invalid_configs = [
            {"recovery_timeout": 5},    # Too low
            {"recovery_timeout": 350},  # Too high
        ]
        
        for config in invalid_configs:
            result = config_validator.validate_custom_config(config)
            assert result.is_valid is False
            assert len(result.errors) > 0
    
    def test_invalid_strategy(self):
        """Test validation with invalid strategy."""
        invalid_config = {
            "default_strategy": "invalid_strategy"
        }
        
        result = config_validator.validate_custom_config(invalid_config)
        assert result.is_valid is False
        # Check for validation error about strategy
        assert any("default_strategy" in error or "enum" in error.lower() or "invalid_strategy" in error 
                  for error in result.errors)
    
    def test_invalid_operation_overrides(self):
        """Test validation with invalid operation overrides."""
        invalid_configs = [
            {
                "operation_overrides": {
                    "invalid_operation": "balanced"  # Invalid operation
                }
            },
            {
                "operation_overrides": {
                    "summarize": "invalid_strategy"  # Invalid strategy
                }
            }
        ]
        
        for config in invalid_configs:
            result = config_validator.validate_custom_config(config)
            assert result.is_valid is False
            assert len(result.errors) > 0
    
    def test_logical_validation_exponential_bounds(self):
        """Test logical validation for exponential bounds."""
        invalid_config = {
            "exponential_min": 10.0,
            "exponential_max": 5.0  # Max less than min
        }
        
        result = config_validator.validate_custom_config(invalid_config)
        assert result.is_valid is False
        assert any("exponential_min" in error for error in result.errors)
    
    def test_warning_for_retry_delay_mismatch(self):
        """Test warning for potential retry/delay mismatch."""
        config = {
            "retry_attempts": 5,
            "max_delay_seconds": 8  # Very short for 5 retries
        }
        
        result = config_validator.validate_custom_config(config)
        # Should be valid but with warnings
        assert result.is_valid is True
        assert len(result.warnings) > 0
        assert any("max_delay_seconds" in warning for warning in result.warnings)
    
    def test_validate_json_string_valid(self):
        """Test validating valid JSON string."""
        valid_json = json.dumps({
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5
        })
        
        result = config_validator.validate_json_string(valid_json)
        assert result.is_valid is True
    
    def test_validate_json_string_invalid_json(self):
        """Test validating invalid JSON string."""
        invalid_json = '{"retry_attempts": 3, "invalid": }'
        
        result = config_validator.validate_json_string(invalid_json)
        assert result.is_valid is False
        assert any("Invalid JSON" in error for error in result.errors)
    
    def test_empty_config_validation(self):
        """Test validation of empty configuration."""
        empty_config = {}
        
        result = config_validator.validate_custom_config(empty_config)
        # Empty config should be invalid (no required fields)
        assert result.is_valid is False


class TestPresetValidation:
    """Test preset validation."""
    
    def test_valid_preset(self):
        """Test validation of valid preset."""
        valid_preset = {
            "name": "Test Preset",
            "description": "A test preset for validation",
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60,
            "default_strategy": "balanced",
            "operation_overrides": {
                "summarize": "conservative"
            },
            "environment_contexts": ["development", "testing"]
        }
        
        result = config_validator.validate_preset(valid_preset)
        assert result.is_valid is True
    
    def test_preset_missing_required_fields(self):
        """Test preset validation with missing required fields."""
        incomplete_preset = {
            "name": "Incomplete Preset",
            "retry_attempts": 3
            # Missing other required fields
        }
        
        result = config_validator.validate_preset(incomplete_preset)
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_preset_logical_validation_warnings(self):
        """Test preset logical validation warnings."""
        preset_with_warning = {
            "name": "Warning Preset",
            "description": "Preset that should generate warnings",
            "retry_attempts": 8,  # High retry attempts
            "circuit_breaker_threshold": 3,  # Low threshold
            "recovery_timeout": 60,
            "default_strategy": "aggressive",
            "operation_overrides": {},
            "environment_contexts": ["production"]  # Aggressive in production
        }
        
        result = config_validator.validate_preset(preset_with_warning)
        assert result.is_valid is True
        assert len(result.warnings) > 0


class TestConfigValidatorIntegration:
    """Test integration with Settings and PresetManager."""
    
    def test_settings_validate_custom_config(self):
        """Test Settings.validate_custom_config method."""
        from app.config import Settings
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config='{"retry_attempts": 5}'
        )
        
        validation_result = settings.validate_custom_config()
        assert validation_result["is_valid"] is True
    
    def test_settings_validate_invalid_custom_config(self):
        """Test Settings validation with invalid custom config."""
        from app.config import Settings
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config='{"retry_attempts": 15}'  # Invalid value
        )
        
        validation_result = settings.validate_custom_config()
        assert validation_result["is_valid"] is False
        assert len(validation_result["errors"]) > 0
    
    def test_settings_validate_external_json(self):
        """Test Settings validation with external JSON string."""
        from app.config import Settings
        
        settings = Settings()
        external_json = '{"circuit_breaker_threshold": 8}'
        
        validation_result = settings.validate_custom_config(external_json)
        assert validation_result["is_valid"] is True


class TestValidationWithoutJsonSchema:
    """Test validation behavior when jsonschema is not available."""
    
    @patch('app.validation_schemas.JSONSCHEMA_AVAILABLE', False)
    def test_basic_validation_fallback(self):
        """Test that basic validation works when jsonschema is unavailable."""
        validator = ResilienceConfigValidator()
        
        # Valid config should pass basic validation
        valid_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60
        }
        
        result = validator.validate_custom_config(valid_config)
        assert result.is_valid is True
        
        # Invalid config should fail basic validation
        invalid_config = {
            "retry_attempts": 15  # Too high
        }
        
        result = validator.validate_custom_config(invalid_config)
        assert result.is_valid is False
    
    @patch('app.validation_schemas.JSONSCHEMA_AVAILABLE', False)
    def test_basic_preset_validation_fallback(self):
        """Test basic preset validation fallback."""
        validator = ResilienceConfigValidator()
        
        # Missing required fields should fail
        incomplete_preset = {
            "name": "Test"
        }
        
        result = validator.validate_preset(incomplete_preset)
        assert result.is_valid is False


class TestValidationSchemas:
    """Test the JSON schema definitions themselves."""
    
    def test_resilience_config_schema_structure(self):
        """Test that the resilience config schema is well-formed."""
        assert "$schema" in RESILIENCE_CONFIG_SCHEMA
        assert "properties" in RESILIENCE_CONFIG_SCHEMA
        assert "retry_attempts" in RESILIENCE_CONFIG_SCHEMA["properties"]
        assert "circuit_breaker_threshold" in RESILIENCE_CONFIG_SCHEMA["properties"]
    
    def test_preset_schema_structure(self):
        """Test that the preset schema is well-formed."""
        assert "$schema" in PRESET_SCHEMA
        assert "properties" in PRESET_SCHEMA
        assert "required" in PRESET_SCHEMA
        assert "name" in PRESET_SCHEMA["required"]
        assert "description" in PRESET_SCHEMA["required"]