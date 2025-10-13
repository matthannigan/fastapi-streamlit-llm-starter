"""
Test suite for Security Configuration Presets.

This module provides comprehensive testing for the preset system,
including preset loading, validation, and customization.

## Test Coverage

### Preset Loading Tests
- Development preset loading and validation
- Production preset loading and validation
- Testing preset loading and validation
- Invalid preset name handling

### Preset Configuration Tests
- Scanner configuration validation
- Performance settings validation
- Logging configuration validation
- Service configuration validation

### Custom Preset Tests
- Custom preset creation
- Custom preset validation
- Preset customization functionality

### Integration Tests
- Preset integration with configuration loader
- Preset application with overrides
- Preset error handling

## Test Categories

- **Unit Tests**: Individual preset functionality
- **Integration Tests**: Preset system integration
- **Validation Tests**: Configuration validation
- **Error Handling Tests**: Robustness and error recovery
"""

import pytest

from app.infrastructure.security.llm.presets import (
    get_preset_config,
    list_presets,
    get_preset_description,
    get_development_preset,
    get_production_preset,
    get_testing_preset,
    create_preset,
    validate_preset_config
)
from app.infrastructure.security.llm.config import SecurityConfig, ScannerType, ViolationAction


class TestPresetLoading:
    """Test cases for preset loading functionality."""

    def test_get_development_preset(self) -> None:
        """Test loading development preset."""
        config = get_development_preset()

        # Check basic structure
        assert isinstance(config, dict)
        assert config["preset"] == "development"

        # Check required sections
        assert "input_scanners" in config
        assert "output_scanners" in config
        assert "performance" in config
        assert "logging" in config
        assert "service" in config
        assert "features" in config

        # Check service configuration
        assert config["service"]["name"] == "security-scanner-dev"
        assert config["service"]["environment"] == "development"
        assert config["service"]["debug_mode"] is True

        # Check scanner configurations
        assert "prompt_injection" in config["input_scanners"]
        assert "toxicity_input" in config["input_scanners"]
        assert "pii_detection" in config["input_scanners"]
        assert "toxicity_output" in config["output_scanners"]
        assert "bias_detection" in config["output_scanners"]

        # Check development-specific settings
        assert config["input_scanners"]["prompt_injection"]["threshold"] == 0.9
        assert config["input_scanners"]["prompt_injection"]["action"] == "warn"
        assert config["logging"]["level"] == "DEBUG"
        assert config["logging"]["include_scanned_text"] is True

    def test_get_production_preset(self) -> None:
        """Test loading production preset."""
        config = get_production_preset()

        # Check basic structure
        assert isinstance(config, dict)
        assert config["preset"] == "production"

        # Check service configuration
        assert config["service"]["name"] == "security-scanner"
        assert config["service"]["environment"] == "production"
        assert config["service"]["debug_mode"] is False
        assert config["service"]["api_key_required"] is True
        assert config["service"]["rate_limit_enabled"] is True

        # Check scanner configurations
        assert "prompt_injection" in config["input_scanners"]
        assert "toxicity_input" in config["input_scanners"]
        assert "pii_detection" in config["input_scanners"]
        assert "malicious_url" in config["input_scanners"]  # Enabled in production
        assert "toxicity_output" in config["output_scanners"]
        assert "bias_detection" in config["output_scanners"]
        assert "harmful_content" in config["output_scanners"]  # Enabled in production

        # Check production-specific settings
        assert config["input_scanners"]["prompt_injection"]["threshold"] == 0.6
        assert config["input_scanners"]["prompt_injection"]["action"] == "block"
        assert config["logging"]["level"] == "INFO"
        assert config["logging"]["include_scanned_text"] is False
        assert config["logging"]["sanitize_pii_in_logs"] is True

        # Check performance settings
        assert config["performance"]["cache_ttl_seconds"] == 7200
        assert config["performance"]["max_concurrent_scans"] == 20
        assert config["performance"]["enable_model_caching"] is True
        assert config["performance"]["enable_result_caching"] is True

    def test_get_testing_preset(self) -> None:
        """Test loading testing preset."""
        config = get_testing_preset()

        # Check basic structure
        assert isinstance(config, dict)
        assert config["preset"] == "testing"

        # Check service configuration
        assert config["service"]["name"] == "security-scanner-test"
        assert config["service"]["environment"] == "testing"
        assert config["service"]["debug_mode"] is True
        assert config["service"]["api_key_required"] is False
        assert config["service"]["rate_limit_enabled"] is False

        # Check minimal scanner configuration
        assert "prompt_injection" in config["input_scanners"]
        assert len(config["input_scanners"]) == 1  # Only prompt injection
        assert len(config["output_scanners"]) == 0  # No output scanners

        # Check testing-specific settings
        assert config["input_scanners"]["prompt_injection"]["threshold"] == 0.95
        assert config["input_scanners"]["prompt_injection"]["use_onnx"] is False
        assert config["input_scanners"]["prompt_injection"]["scan_timeout"] == 5

        # Check performance settings
        assert config["performance"]["cache_ttl_seconds"] == 1
        assert config["performance"]["max_concurrent_scans"] == 1
        assert config["performance"]["enable_model_caching"] is False
        assert config["performance"]["enable_result_caching"] is False

        # Check logging settings
        assert config["logging"]["enabled"] is False
        assert config["logging"]["level"] == "ERROR"

    def test_get_preset_config_function(self) -> None:
        """Test get_preset_config function with all presets."""
        # Test development preset
        dev_config = get_preset_config("development")
        assert dev_config["preset"] == "development"
        assert dev_config["service"]["environment"] == "development"

        # Test production preset
        prod_config = get_preset_config("production")
        assert prod_config["preset"] == "production"
        assert prod_config["service"]["environment"] == "production"

        # Test testing preset
        test_config = get_preset_config("testing")
        assert test_config["preset"] == "testing"
        assert test_config["service"]["environment"] == "testing"

    def test_get_preset_config_invalid_name(self) -> None:
        """Test get_preset_config with invalid preset name."""
        with pytest.raises(ValueError) as exc_info:
            get_preset_config("invalid_preset")

        assert "Unknown preset: invalid_preset" in str(exc_info.value)
        assert "Available presets: ['development', 'production', 'testing']" in str(exc_info.value)

    def test_list_presets(self) -> None:
        """Test list_presets function."""
        presets = list_presets()
        assert isinstance(presets, list)
        assert len(presets) == 3
        assert "development" in presets
        assert "production" in presets
        assert "testing" in presets

    def test_get_preset_description(self) -> None:
        """Test get_preset_description function."""
        # Test valid presets
        dev_desc = get_preset_description("development")
        assert "Development preset" in dev_desc
        assert "lenient settings" in dev_desc

        prod_desc = get_preset_description("production")
        assert "Production preset" in prod_desc
        assert "strict security" in prod_desc

        test_desc = get_preset_description("testing")
        assert "Testing preset" in test_desc
        assert "minimal scanners" in test_desc

        # Test invalid preset
        invalid_desc = get_preset_description("invalid")
        assert invalid_desc == "Unknown preset"


class TestPresetValidation:
    """Test cases for preset validation functionality."""

    def test_validate_development_preset(self) -> None:
        """Test validation of development preset."""
        config = get_development_preset()
        issues = validate_preset_config(config)
        assert len(issues) == 0, f"Development preset validation issues: {issues}"

    def test_validate_production_preset(self) -> None:
        """Test validation of production preset."""
        config = get_production_preset()
        issues = validate_preset_config(config)
        assert len(issues) == 0, f"Production preset validation issues: {issues}"

    def test_validate_testing_preset(self) -> None:
        """Test validation of testing preset."""
        config = get_testing_preset()
        issues = validate_preset_config(config)
        assert len(issues) == 0, f"Testing preset validation issues: {issues}"

    def test_validate_missing_sections(self) -> None:
        """Test validation with missing required sections."""
        invalid_config = {
            "preset": "invalid"
            # Missing required sections
        }

        issues = validate_preset_config(invalid_config)
        assert len(issues) >= 4  # At least 4 missing sections
        assert any("Missing required section: input_scanners" in issue for issue in issues)
        assert any("Missing required section: output_scanners" in issue for issue in issues)
        assert any("Missing required section: performance" in issue for issue in issues)
        assert any("Missing required section: logging" in issue for issue in issues)

    def test_validate_invalid_scanner_config(self) -> None:
        """Test validation with invalid scanner configurations."""
        invalid_config = {
            "input_scanners": {
                "prompt_injection": {
                    # Missing required fields
                    "invalid_field": "value"
                },
                "toxicity_input": "not_a_dict"  # Invalid type
            },
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": 10
            },
            "logging": {
                "enabled": True
            }
        }

        issues = validate_preset_config(invalid_config)
        assert len(issues) >= 3  # At least 3 issues
        assert any("Missing 'enabled' field for scanner prompt_injection" in issue for issue in issues)
        assert any("Invalid scanner configuration for toxicity_input" in issue for issue in issues)

    def test_validate_invalid_threshold_values(self) -> None:
        """Test validation with invalid threshold values."""
        invalid_config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 1.5,  # Invalid (> 1.0)
                    "action": "block"
                },
                "toxicity_input": {
                    "enabled": True,
                    "threshold": -0.1,  # Invalid (< 0.0)
                    "action": "block"
                },
                "pii_detection": {
                    "enabled": True,
                    "threshold": "not_a_number",  # Invalid type
                    "action": "block"
                }
            },
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": 10
            },
            "logging": {
                "enabled": True
            }
        }

        issues = validate_preset_config(invalid_config)
        assert len(issues) >= 3  # At least 3 threshold issues
        assert any("Invalid threshold for scanner prompt_injection: 1.5" in issue for issue in issues)
        assert any("Invalid threshold for scanner toxicity_input: -0.1" in issue for issue in issues)
        assert any("Invalid threshold for scanner pii_detection" in issue for issue in issues)

    def test_validate_invalid_performance_config(self) -> None:
        """Test validation with invalid performance configuration."""
        invalid_config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block"
                }
            },
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": 0  # Invalid (< 1)
            },
            "logging": {
                "enabled": True
            }
        }

        issues = validate_preset_config(invalid_config)
        assert len(issues) >= 1
        assert any("Invalid max_concurrent_scans: 0" in issue for issue in issues)


class TestCustomPresetCreation:
    """Test cases for custom preset creation functionality."""

    def test_create_custom_preset(self) -> None:
        """Test creating a custom preset."""
        input_scanners = {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "block"
            }
        }

        output_scanners = {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.8,
                "action": "warn"
            }
        }

        performance_overrides = {
            "max_concurrent_scans": 15
        }

        custom_preset = create_preset(
            name="custom",
            description="Custom security preset for testing",
            input_scanners=input_scanners,
            output_scanners=output_scanners,
            performance_overrides=performance_overrides
        )

        # Check basic structure
        assert custom_preset["preset"] == "custom"
        assert "input_scanners" in custom_preset
        assert "output_scanners" in custom_preset
        assert "performance" in custom_preset
        assert "logging" in custom_preset
        assert "service" in custom_preset

        # Check custom configurations were applied
        assert custom_preset["input_scanners"]["prompt_injection"]["threshold"] == 0.7
        assert custom_preset["output_scanners"]["toxicity_output"]["action"] == "warn"
        assert custom_preset["performance"]["max_concurrent_scans"] == 15

        # Check service configuration
        assert custom_preset["service"]["name"] == "security-scanner-custom"
        assert custom_preset["service"]["environment"] == "custom"

    def test_create_custom_preset_minimal(self) -> None:
        """Test creating a custom preset with minimal configuration."""
        input_scanners = {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.8,
                "action": "block"
            }
        }

        custom_preset = create_preset(
            name="minimal",
            description="Minimal custom preset",
            input_scanners=input_scanners,
            output_scanners={}
        )

        # Check basic structure
        assert custom_preset["preset"] == "minimal"
        assert len(custom_preset["input_scanners"]) == 1
        assert len(custom_preset["output_scanners"]) == 0

        # Check that default configurations were merged
        assert "performance" in custom_preset
        assert "logging" in custom_preset
        assert custom_preset["performance"]["cache_enabled"] is True

    def test_validate_custom_preset(self) -> None:
        """Test validation of custom preset."""
        custom_preset = create_preset(
            name="test_custom",
            description="Test custom preset",
            input_scanners={
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "block"
                }
            },
            output_scanners={}
        )

        issues = validate_preset_config(custom_preset)
        assert len(issues) == 0, f"Custom preset validation issues: {issues}"


class TestPresetIntegration:
    """Test cases for preset integration with other components."""

    def test_preset_config_conversion(self) -> None:
        """Test conversion of preset config to SecurityConfig."""
        # Get development preset
        preset_config = get_development_preset()

        # Convert to SecurityConfig using from_dict
        security_config = SecurityConfig.from_dict(preset_config)

        # Check conversion worked
        assert isinstance(security_config, SecurityConfig)
        assert security_config.environment == "development"
        assert security_config.debug_mode is True
        assert len(security_config.scanners) > 0

        # Check specific scanner
        prompt_injection = security_config.get_scanner_config(ScannerType.PROMPT_INJECTION)
        assert prompt_injection is not None
        assert prompt_injection.enabled is True
        assert prompt_injection.threshold == 0.9
        assert prompt_injection.action == ViolationAction.WARN

    def test_production_preset_config_conversion(self) -> None:
        """Test conversion of production preset to SecurityConfig."""
        preset_config = get_production_preset()
        security_config = SecurityConfig.from_dict(preset_config)

        assert isinstance(security_config, SecurityConfig)
        assert security_config.environment == "production"
        assert security_config.debug_mode is False

        # Check that more scanners are enabled in production
        enabled_scanners = security_config.get_enabled_scanners()
        assert len(enabled_scanners) >= 5  # Should have more than development

    def test_testing_preset_config_conversion(self) -> None:
        """Test conversion of testing preset to SecurityConfig."""
        preset_config = get_testing_preset()
        security_config = SecurityConfig.from_dict(preset_config)

        assert isinstance(security_config, SecurityConfig)
        assert security_config.environment == "testing"

        # Check that minimal scanners are enabled
        enabled_scanners = security_config.get_enabled_scanners()
        assert len(enabled_scanners) == 1  # Only prompt injection

    def test_preset_feature_flags(self) -> None:
        """Test preset feature flags."""
        dev_config = get_development_preset()
        prod_config = get_production_preset()
        test_config = get_testing_preset()

        # Development should have experimental features enabled
        assert dev_config["features"]["experimental_scanners"] is True
        assert dev_config["features"]["custom_scanner_support"] is True

        # Production should have conservative feature set
        assert prod_config["features"]["experimental_scanners"] is False
        assert prod_config["features"]["custom_scanner_support"] is False
        assert prod_config["features"]["advanced_analytics"] is True

        # Testing should have minimal features
        assert test_config["features"]["experimental_scanners"] is False
        assert test_config["features"]["advanced_analytics"] is False

    def test_preset_performance_characteristics(self) -> None:
        """Test performance characteristics of different presets."""
        dev_config = get_development_preset()
        prod_config = get_production_preset()
        test_config = get_testing_preset()

        # Development should have moderate performance settings
        assert 1 <= dev_config["performance"]["max_concurrent_scans"] <= 10
        assert dev_config["performance"]["cache_ttl_seconds"] >= 300

        # Production should have high performance settings
        assert prod_config["performance"]["max_concurrent_scans"] >= 15
        assert prod_config["performance"]["cache_ttl_seconds"] >= 3600
        assert prod_config["performance"]["enable_model_caching"] is True

        # Testing should have minimal performance settings
        assert test_config["performance"]["max_concurrent_scans"] == 1
        assert test_config["performance"]["cache_ttl_seconds"] <= 5
        assert test_config["performance"]["enable_model_caching"] is False


class TestPresetComparison:
    """Test cases for comparing different presets."""

    def test_development_vs_production_differences(self) -> None:
        """Test differences between development and production presets."""
        dev_config = get_development_preset()
        prod_config = get_production_preset()

        # Security settings should be stricter in production
        dev_threshold = dev_config["input_scanners"]["prompt_injection"]["threshold"]
        prod_threshold = prod_config["input_scanners"]["prompt_injection"]["threshold"]
        assert prod_threshold < dev_threshold  # Lower threshold = more sensitive

        # Actions should be more restrictive in production
        dev_action = dev_config["input_scanners"]["prompt_injection"]["action"]
        prod_action = prod_config["input_scanners"]["prompt_injection"]["action"]
        assert dev_action == "warn"
        assert prod_action == "block"

        # Production should have more scanners enabled
        assert len(prod_config["input_scanners"]) > len(dev_config["input_scanners"])
        assert len(prod_config["output_scanners"]) > len(dev_config["output_scanners"])

        # Logging should be more secure in production
        assert dev_config["logging"]["include_scanned_text"] is True
        assert prod_config["logging"]["include_scanned_text"] is False
        assert prod_config["logging"]["sanitize_pii_in_logs"] is True

    def test_testing_vs_other_presets(self) -> None:
        """Test differences between testing and other presets."""
        test_config = get_testing_preset()
        dev_config = get_development_preset()
        prod_config = get_production_preset()

        # Testing should have minimal scanners
        assert len(test_config["input_scanners"]) < len(dev_config["input_scanners"])
        assert len(test_config["input_scanners"]) < len(prod_config["input_scanners"])
        assert len(test_config["output_scanners"]) == 0

        # Testing should have minimal performance settings
        assert test_config["performance"]["max_concurrent_scans"] == 1
        assert dev_config["performance"]["max_concurrent_scans"] > 1
        assert prod_config["performance"]["max_concurrent_scans"] > 1

        # Testing should have minimal logging
        assert test_config["logging"]["enabled"] is False
        assert dev_config["logging"]["enabled"] is True
        assert prod_config["logging"]["enabled"] is True

    def test_preset_threshold_progression(self) -> None:
        """Test threshold progression across presets."""
        dev_config = get_development_preset()
        prod_config = get_production_preset()
        test_config = get_testing_preset()

        # Prompt injection thresholds
        test_threshold = test_config["input_scanners"]["prompt_injection"]["threshold"]
        dev_threshold = dev_config["input_scanners"]["prompt_injection"]["threshold"]
        prod_threshold = prod_config["input_scanners"]["prompt_injection"]["threshold"]

        # Testing should be most lenient (highest threshold)
        # Development should be moderately lenient
        # Production should be most strict (lowest threshold)
        assert test_threshold >= dev_threshold >= prod_threshold

        # Verify numeric values
        assert test_threshold == 0.95
        assert dev_threshold == 0.9
        assert prod_threshold == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
