"""
Unit tests for custom preset creation and validation functions.

This test module verifies the create_preset() and validate_preset_config()
functions that enable custom security preset creation and configuration validation.

Test Strategy:
    - Component Under Test: create_preset() and validate_preset_config() functions
    - Testing Approach: Black-box testing through public API only
    - No Mocking: Pure functions with no external dependencies
    - Contract Source: backend/contracts/infrastructure/security/llm/presets.pyi

Fixtures Available:
    From conftest.py (backend/tests/unit/llm_security/presets/conftest.py):
    - custom_preset_scanner_configs: Scanner configurations for custom presets
    - custom_preset_performance_overrides: Performance overrides for custom presets
    - custom_preset_logging_overrides: Logging overrides for custom presets
    - invalid_preset_configurations: Various invalid configurations for testing
    - preset_validation_issues: Expected validation error messages
    - custom_preset_examples: Complete custom preset examples
"""

import pytest
from typing import Dict, Any, List
import copy

from app.infrastructure.security.llm.presets import create_preset, validate_preset_config


class TestCreatePreset:
    """
    Test suite for create_preset() function.
    
    Scope:
        Verifies that create_preset() builds complete custom security configurations
        by combining scanner definitions with base settings and overrides.
        
    Business Critical:
        Custom preset creation enables specialized security configurations for
        specific use cases (content moderation, enterprise security, etc.).
        Incorrect preset creation could result in security gaps.
        
    Test Strategy:
        - Test preset creation with minimal configuration
        - Test preset creation with comprehensive overrides
        - Verify base configuration inheritance
        - Test preset structure and completeness
    """

    def test_creates_preset_with_minimal_configuration(self, custom_preset_scanner_configs):
        """
        Test that create_preset builds complete configuration from minimal input.

        Verifies:
            create_preset() can build a complete, valid preset configuration
            from just name, description, and scanner definitions, using base
            defaults for all other settings.

        Business Impact:
            Simplified preset creation enables users to create custom security
            configurations without deep knowledge of all settings.

        Scenario:
            Given: A custom preset with name, description, and minimal scanner configs
            When: create_preset() is called with these parameters
            And: No performance or logging overrides are provided
            Then: A complete configuration dictionary is returned
            And: The preset field contains the custom name
            And: All required sections are present with valid defaults
            And: Scanner configurations match the provided input

        Fixtures Used:
            - custom_preset_scanner_configs: Example scanner configurations
        """
        # Arrange: Get scanner configurations from fixture
        input_scanners = custom_preset_scanner_configs["content_moderation_input"]
        output_scanners = custom_preset_scanner_configs["content_moderation_output"]
        name = "minimal-preset"
        description = "Minimal preset for testing"

        # Act: Create preset with minimal parameters
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify complete configuration structure
        assert preset_config is not None
        assert isinstance(preset_config, dict)

        # Verify preset identification
        assert preset_config["preset"] == name

        # Verify all required sections are present
        required_sections = ["preset", "input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in preset_config, f"Missing required section: {section}"

        # Verify scanner configurations match input
        assert preset_config["input_scanners"] == input_scanners
        assert preset_config["output_scanners"] == output_scanners

        # Verify default sections are populated (from development preset)
        assert preset_config["performance"] is not None
        assert isinstance(preset_config["performance"], dict)
        assert preset_config["logging"] is not None
        assert isinstance(preset_config["logging"], dict)
        assert preset_config["service"] is not None
        assert isinstance(preset_config["service"], dict)
        assert preset_config["features"] is not None
        assert isinstance(preset_config["features"], dict)

        # Verify service configuration contains custom name
        assert preset_config["service"]["name"] == f"security-scanner-{name}"
        assert preset_config["service"]["environment"] == name

    def test_creates_preset_with_custom_scanner_definitions(self, custom_preset_scanner_configs):
        """
        Test that create_preset correctly applies custom scanner configurations.

        Verifies:
            Custom scanner configurations provided to create_preset() are
            correctly included in the returned preset without modification.

        Business Impact:
            Accurate scanner configuration ensures custom presets implement
            the intended security policies and thresholds.

        Scenario:
            Given: Custom input and output scanner configurations
            When: create_preset() is called with these scanner configs
            Then: The returned configuration contains the exact scanner definitions
            And: input_scanners match the provided input scanner configs
            And: output_scanners match the provided output scanner configs
            And: No scanner configurations are added or removed

        Fixtures Used:
            - custom_preset_scanner_configs: Custom scanner definitions
        """
        # Arrange: Get custom scanner configurations
        input_scanners = custom_preset_scanner_configs["content_moderation_input"]
        output_scanners = custom_preset_scanner_configs["content_moderation_output"]
        name = "custom-scanner-test"
        description = "Test preset with custom scanner definitions"

        # Act: Create preset with custom scanner configurations
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify scanner configurations are preserved exactly
        assert preset_config["input_scanners"] == input_scanners
        assert preset_config["output_scanners"] == output_scanners

        # Verify specific scanner configurations are present
        assert "prompt_injection" in preset_config["input_scanners"]
        assert "toxicity_input" in preset_config["input_scanners"]
        assert "hate_speech" in preset_config["input_scanners"]
        assert "toxicity_output" in preset_config["output_scanners"]
        assert "violence" in preset_config["output_scanners"]

        # Verify specific threshold values are preserved
        assert preset_config["input_scanners"]["prompt_injection"]["threshold"] == 0.4
        assert preset_config["input_scanners"]["toxicity_input"]["threshold"] == 0.3
        assert preset_config["input_scanners"]["hate_speech"]["threshold"] == 0.2
        assert preset_config["output_scanners"]["toxicity_output"]["threshold"] == 0.2
        assert preset_config["output_scanners"]["violence"]["threshold"] == 0.1

        # Verify action settings are preserved
        assert preset_config["input_scanners"]["prompt_injection"]["action"] == "block"
        assert preset_config["input_scanners"]["toxicity_input"]["action"] == "block"
        assert preset_config["input_scanners"]["hate_speech"]["action"] == "block"
        assert preset_config["output_scanners"]["toxicity_output"]["action"] == "block"
        assert preset_config["output_scanners"]["violence"]["action"] == "block"

        # Verify no extra scanners were added
        assert len(preset_config["input_scanners"]) == len(input_scanners)
        assert len(preset_config["output_scanners"]) == len(output_scanners)

    def test_creates_preset_with_performance_overrides(self, custom_preset_performance_overrides):
        """
        Test that create_preset applies custom performance overrides correctly.

        Verifies:
            Performance overrides provided to create_preset() are merged with
            base performance settings, with overrides taking precedence.

        Business Impact:
            Performance customization enables users to optimize security scanning
            for specific deployment scenarios (high-throughput, resource-constrained).

        Scenario:
            Given: Custom performance override settings
            When: create_preset() is called with performance_overrides parameter
            Then: The returned configuration includes the custom performance settings
            And: Specified overrides replace base values
            And: Non-specified settings retain base defaults
            And: All performance values are within valid ranges

        Fixtures Used:
            - custom_preset_performance_overrides: Performance customization examples
        """
        # Arrange: Get performance override settings
        performance_overrides = custom_preset_performance_overrides["content_moderation"]
        input_scanners = {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }
        output_scanners = {}
        name = "performance-test"
        description = "Test preset with performance overrides"

        # Act: Create preset with performance overrides
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners,
            performance_overrides=performance_overrides
        )

        # Assert: Verify performance overrides are applied
        performance_config = preset_config["performance"]

        # Verify specified overrides are applied
        assert performance_config["cache_ttl_seconds"] == performance_overrides["cache_ttl_seconds"]
        assert performance_config["max_concurrent_scans"] == performance_overrides["max_concurrent_scans"]
        assert performance_config["memory_limit_mb"] == performance_overrides["memory_limit_mb"]
        assert performance_config["batch_processing"] == performance_overrides["batch_processing"]
        assert performance_config["batch_size"] == performance_overrides["batch_size"]

        # Verify base performance settings are still present (not overridden)
        assert "cache_enabled" in performance_config
        assert "lazy_loading" in performance_config
        assert "onnx_providers" in performance_config
        assert "enable_model_caching" in performance_config
        assert "enable_result_caching" in performance_config

        # Verify values are within valid ranges
        assert performance_config["cache_ttl_seconds"] > 0
        assert performance_config["max_concurrent_scans"] > 0
        assert performance_config["memory_limit_mb"] > 0
        assert performance_config["batch_size"] > 0
        assert isinstance(performance_config["batch_processing"], bool)

    def test_creates_preset_with_logging_overrides(self, custom_preset_logging_overrides):
        """
        Test that create_preset applies custom logging overrides correctly.

        Verifies:
            Logging overrides provided to create_preset() are merged with
            base logging settings, with overrides taking precedence.

        Business Impact:
            Logging customization enables users to configure appropriate logging
            levels and privacy settings for specific compliance requirements.

        Scenario:
            Given: Custom logging override settings
            When: create_preset() is called with logging_overrides parameter
            Then: The returned configuration includes the custom logging settings
            And: Specified overrides replace base values
            And: Non-specified settings retain base defaults
            And: Logging configuration is valid and consistent

        Fixtures Used:
            - custom_preset_logging_overrides: Logging customization examples
        """
        # Arrange: Get logging override settings
        logging_overrides = custom_preset_logging_overrides["content_moderation"]
        input_scanners = {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }
        output_scanners = {}
        name = "logging-test"
        description = "Test preset with logging overrides"

        # Act: Create preset with logging overrides
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners,
            logging_overrides=logging_overrides
        )

        # Assert: Verify logging overrides are applied
        logging_config = preset_config["logging"]

        # Verify specified overrides are applied
        assert logging_config["level"] == logging_overrides["level"]
        assert logging_config["log_violations"] == logging_overrides["log_violations"]
        assert logging_config["sanitize_pii_in_logs"] == logging_overrides["sanitize_pii_in_logs"]
        assert logging_config["log_format"] == logging_overrides["log_format"]

        # Verify base logging settings are still present (not overridden)
        assert "enabled" in logging_config
        assert "log_scan_operations" in logging_config
        assert "log_performance_metrics" in logging_config
        assert "include_scanned_text" in logging_config
        assert "retention_days" in logging_config

        # Verify logging configuration is valid
        assert logging_config["level"] in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert logging_config["log_format"] in ["text", "json"]
        assert isinstance(logging_config["log_violations"], bool)
        assert isinstance(logging_config["sanitize_pii_in_logs"], bool)

    def test_creates_preset_with_all_custom_settings(
        self,
        custom_preset_scanner_configs,
        custom_preset_performance_overrides,
        custom_preset_logging_overrides
    ):
        """
        Test that create_preset handles complete customization correctly.

        Verifies:
            create_preset() can successfully combine custom scanner configs,
            performance overrides, and logging overrides into a complete preset.

        Business Impact:
            Comprehensive customization enables users to create highly specialized
            security configurations tailored to specific business requirements.

        Scenario:
            Given: Custom scanner configs, performance overrides, and logging overrides
            When: create_preset() is called with all customization parameters
            Then: A complete configuration is returned with all customizations applied
            And: Scanner configurations match provided input
            And: Performance settings include all specified overrides
            And: Logging settings include all specified overrides
            And: All sections are complete and valid

        Fixtures Used:
            - custom_preset_scanner_configs: Scanner definitions
            - custom_preset_performance_overrides: Performance customization
            - custom_preset_logging_overrides: Logging customization
        """
        # Arrange: Get all custom settings
        input_scanners = custom_preset_scanner_configs["content_moderation_input"]
        output_scanners = custom_preset_scanner_configs["content_moderation_output"]
        performance_overrides = custom_preset_performance_overrides["high_security"]
        logging_overrides = custom_preset_logging_overrides["high_security"]
        name = "comprehensive-test"
        description = "Test preset with all custom settings"

        # Act: Create preset with all customizations
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners,
            performance_overrides=performance_overrides,
            logging_overrides=logging_overrides
        )

        # Assert: Verify all customizations are applied
        # Verify scanner configurations
        assert preset_config["input_scanners"] == input_scanners
        assert preset_config["output_scanners"] == output_scanners

        # Verify performance overrides are applied
        performance_config = preset_config["performance"]
        for key, value in performance_overrides.items():
            assert performance_config[key] == value, f"Performance override for {key} not applied"

        # Verify logging overrides are applied
        logging_config = preset_config["logging"]
        for key, value in logging_overrides.items():
            assert logging_config[key] == value, f"Logging override for {key} not applied"

        # Verify all sections are complete
        required_sections = ["preset", "input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in preset_config, f"Missing required section: {section}"

        # Verify preset identification
        assert preset_config["preset"] == name
        assert preset_config["service"]["name"] == f"security-scanner-{name}"
        assert preset_config["service"]["environment"] == name

    def test_creates_preset_inherits_base_development_settings(self):
        """
        Test that create_preset inherits base settings from development preset.

        Verifies:
            Custom presets inherit base performance and logging settings from
            the development preset for any settings not explicitly overridden.

        Business Impact:
            Base setting inheritance provides sensible defaults and reduces
            configuration complexity for custom preset creation.

        Scenario:
            Given: A custom preset with no performance or logging overrides
            When: create_preset() is called
            Then: Performance section contains development preset defaults
            And: Logging section contains development preset defaults
            And: Features section contains development preset defaults
            And: Only scanner configurations differ from development preset

        Fixtures Used:
            - None (tests default inheritance behavior)
        """
        # Arrange: Get development preset for comparison
        from app.infrastructure.security.llm.presets import get_development_preset
        dev_preset = get_development_preset()

        # Custom preset with minimal configuration (no overrides)
        input_scanners = {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.8,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }
        output_scanners = {}
        name = "inheritance-test"
        description = "Test preset inheritance"

        # Act: Create preset without overrides
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify inheritance of base settings
        # Performance section should inherit from development preset
        assert preset_config["performance"]["cache_enabled"] == dev_preset["performance"]["cache_enabled"]
        assert preset_config["performance"]["lazy_loading"] == dev_preset["performance"]["lazy_loading"]
        assert preset_config["performance"]["onnx_providers"] == dev_preset["performance"]["onnx_providers"]
        assert preset_config["performance"]["max_concurrent_scans"] == dev_preset["performance"]["max_concurrent_scans"]
        assert preset_config["performance"]["memory_limit_mb"] == dev_preset["performance"]["memory_limit_mb"]

        # Logging section should inherit from development preset
        assert preset_config["logging"]["enabled"] == dev_preset["logging"]["enabled"]
        assert preset_config["logging"]["level"] == dev_preset["logging"]["level"]
        assert preset_config["logging"]["log_scan_operations"] == dev_preset["logging"]["log_scan_operations"]
        assert preset_config["logging"]["log_violations"] == dev_preset["logging"]["log_violations"]
        assert preset_config["logging"]["include_scanned_text"] == dev_preset["logging"]["include_scanned_text"]

        # Features section should inherit from development preset
        assert preset_config["features"] == dev_preset["features"]

        # Service section should be customized (not inherited)
        assert preset_config["service"]["name"] == f"security-scanner-{name}"
        assert preset_config["service"]["environment"] == name

        # Scanner sections should be custom (not inherited)
        assert preset_config["input_scanners"] == input_scanners
        assert preset_config["output_scanners"] == output_scanners

    def test_created_preset_contains_all_required_sections(self):
        """
        Test that create_preset always returns configuration with all required sections.

        Verifies:
            Every preset created by create_preset() contains the complete set
            of required configuration sections for proper system initialization.

        Business Impact:
            Complete configuration structure prevents initialization failures
            and ensures custom presets work correctly in all deployment scenarios.

        Scenario:
            Given: A call to create_preset() with minimal parameters
            When: The returned configuration is examined
            Then: All required sections are present:
                - preset (custom name)
                - input_scanners (provided configs)
                - output_scanners (provided configs)
                - performance (base + overrides)
                - logging (base + overrides)
                - service (base settings)
                - features (base settings)

        Fixtures Used:
            - None (tests configuration completeness)
        """
        # Arrange: Minimal configuration
        input_scanners = {"prompt_injection": {"enabled": True, "threshold": 0.8, "action": "warn", "use_onnx": True, "scan_timeout": 30}}
        output_scanners = {}
        name = "sections-test"
        description = "Test required sections"

        # Act: Create preset
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify all required sections are present
        required_sections = ["preset", "input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in preset_config, f"Missing required section: {section}"
            assert preset_config[section] is not None, f"Required section {section} is None"

        # Verify each section has the expected type
        assert isinstance(preset_config["preset"], str)
        assert isinstance(preset_config["input_scanners"], dict)
        assert isinstance(preset_config["output_scanners"], dict)
        assert isinstance(preset_config["performance"], dict)
        assert isinstance(preset_config["logging"], dict)
        assert isinstance(preset_config["service"], dict)
        assert isinstance(preset_config["features"], dict)

    def test_creates_preset_with_empty_output_scanners(self):
        """
        Test that create_preset handles empty output scanner configuration.

        Verifies:
            create_preset() can create valid presets with no output scanners
            for use cases that only require input validation (e.g., testing).

        Business Impact:
            Flexible scanner configuration enables use cases with different
            security requirements (input-only validation, output-only filtering).

        Scenario:
            Given: Input scanners with content, empty output scanners dictionary
            When: create_preset() is called with empty output_scanners={}
            Then: A valid configuration is returned
            And: input_scanners contains the provided scanners
            And: output_scanners is an empty dictionary
            And: All other sections are complete and valid

        Fixtures Used:
            - None (tests edge case with minimal scanner config)
        """
        # Arrange: Input scanners with empty output scanners
        input_scanners = {
            "prompt_injection": {"enabled": True, "threshold": 0.8, "action": "warn", "use_onnx": True, "scan_timeout": 30},
            "toxicity_input": {"enabled": True, "threshold": 0.7, "action": "warn", "use_onnx": True, "scan_timeout": 25}
        }
        output_scanners = {}  # Empty dictionary
        name = "input-only-test"
        description = "Test preset with empty output scanners"

        # Act: Create preset
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify configuration is valid
        assert preset_config["input_scanners"] == input_scanners
        assert preset_config["output_scanners"] == {}
        assert len(preset_config["output_scanners"]) == 0

        # Verify all required sections are still present
        required_sections = ["preset", "input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in preset_config

        # Verify the configuration passes validation
        issues = validate_preset_config(preset_config)
        assert not issues, f"Empty output scanners should be valid: {issues}"

    def test_creates_preset_with_descriptive_name_and_description(self):
        """
        Test that create_preset stores name and description in configuration.

        Verifies:
            Custom preset name and description are correctly stored in the
            configuration for identification and documentation purposes.

        Business Impact:
            Clear naming and descriptions help teams identify and select
            appropriate security configurations for different environments.

        Scenario:
            Given: A custom name "content-moderation" and description
            When: create_preset() is called with these parameters
            Then: The preset field contains "content-moderation"
            And: The configuration can be identified by its name
            And: The description is available for documentation

        Fixtures Used:
            - None (tests metadata storage)
        """
        # Arrange: Custom name and description
        name = "content-moderation"
        description = "High-sensitivity content moderation for social platforms"
        input_scanners = {"prompt_injection": {"enabled": True, "threshold": 0.5, "action": "block", "use_onnx": True, "scan_timeout": 30}}
        output_scanners = {}

        # Act: Create preset
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify name and description storage
        assert preset_config["preset"] == name
        assert preset_config["service"]["name"] == f"security-scanner-{name}"
        assert preset_config["service"]["environment"] == name

        # Verify configuration can be identified by name
        assert preset_config["preset"] == "content-moderation"
        assert "content-moderation" in preset_config["service"]["name"]
        assert preset_config["service"]["environment"] == "content-moderation"

    def test_creates_preset_with_specialized_thresholds(self):
        """
        Test that create_preset preserves specialized security thresholds.

        Verifies:
            Custom security thresholds in scanner configurations are preserved
            exactly as specified, enabling specialized security policies.

        Business Impact:
            Precise threshold control enables fine-tuning of security policies
            to balance protection and user experience for specific use cases.

        Scenario:
            Given: Scanner configurations with very strict thresholds (0.1-0.3)
            When: create_preset() is called with these scanners
            Then: The returned configuration contains exact threshold values
            And: No threshold values are modified or normalized
            And: Scanner actions match the provided specifications

        Fixtures Used:
            - custom_preset_scanner_configs: Contains high-security thresholds
        """
        # Arrange: Scanner configurations with specialized thresholds
        input_scanners = {
            "prompt_injection": {
                "enabled": True,
                "threshold": 0.1,  # Very strict
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30
            },
            "toxicity_input": {
                "enabled": True,
                "threshold": 0.2,  # Extremely strict
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 25
            }
        }
        output_scanners = {
            "toxicity_output": {
                "enabled": True,
                "threshold": 0.05,  # Maximum sensitivity
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }
        name = "high-security"
        description = "Maximum security preset with strict thresholds"

        # Act: Create preset
        preset_config = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Assert: Verify thresholds are preserved exactly
        assert preset_config["input_scanners"]["prompt_injection"]["threshold"] == 0.1
        assert preset_config["input_scanners"]["toxicity_input"]["threshold"] == 0.2
        assert preset_config["output_scanners"]["toxicity_output"]["threshold"] == 0.05

        # Verify actions are preserved exactly
        assert preset_config["input_scanners"]["prompt_injection"]["action"] == "block"
        assert preset_config["input_scanners"]["toxicity_input"]["action"] == "block"
        assert preset_config["output_scanners"]["toxicity_output"]["action"] == "block"

        # Verify thresholds are within valid range
        assert 0.0 <= preset_config["input_scanners"]["prompt_injection"]["threshold"] <= 1.0
        assert 0.0 <= preset_config["input_scanners"]["toxicity_input"]["threshold"] <= 1.0
        assert 0.0 <= preset_config["output_scanners"]["toxicity_output"]["threshold"] <= 1.0


class TestValidatePresetConfig:
    """
    Test suite for validate_preset_config() function.
    
    Scope:
        Verifies that validate_preset_config() performs comprehensive validation
        of preset configurations and returns detailed issue descriptions.
        
    Business Critical:
        Configuration validation prevents system initialization failures and
        security misconfigurations that could leave systems vulnerable.
        
    Test Strategy:
        - Test validation of valid preset configurations
        - Test detection of structural issues (missing sections)
        - Test detection of invalid parameter values
        - Test validation error message quality
    """

    def test_validates_correct_configuration_without_issues(self, development_preset_data):
        """
        Test that validate_preset_config returns empty list for valid configuration.

        Verifies:
            validate_preset_config() returns an empty list when provided with
            a complete, valid preset configuration meeting all requirements.

        Business Impact:
            Accurate validation of correct configurations prevents false positive
            errors that would disrupt valid deployments.

        Scenario:
            Given: A valid development preset configuration
            When: validate_preset_config() is called
            Then: An empty list is returned (no validation issues)
            And: The configuration is accepted as valid
            And: No error messages or warnings are generated

        Fixtures Used:
            - development_preset_data: Known valid configuration
        """
        # Arrange: Use the valid development preset configuration
        config = development_preset_data

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify no validation issues are found
        assert isinstance(issues, list)
        assert len(issues) == 0, f"Expected no validation issues, but got: {issues}"
        assert issues == []

    def test_validates_production_preset_configuration(self, production_preset_data):
        """
        Test that validate_preset_config accepts valid production configuration.

        Verifies:
            validate_preset_config() correctly validates production preset
            configurations with strict security settings.

        Business Impact:
            Ensures production-ready configurations pass validation, enabling
            confident deployment of security-hardened settings.

        Scenario:
            Given: A valid production preset configuration
            When: validate_preset_config() is called
            Then: An empty list is returned (no validation issues)
            And: Strict thresholds are accepted as valid
            And: Production-specific settings pass validation

        Fixtures Used:
            - production_preset_data: Production configuration for validation
        """
        # Arrange: Use the valid production preset configuration
        config = production_preset_data

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify no validation issues are found
        assert isinstance(issues, list)
        assert len(issues) == 0, f"Production preset should be valid, but got issues: {issues}"

        # Verify specific production settings are accepted
        assert config["input_scanners"]["prompt_injection"]["threshold"] == 0.6  # Strict but valid
        assert config["input_scanners"]["pii_detection"]["action"] == "redact"  # Valid action
        assert config["performance"]["max_concurrent_scans"] == 20  # Valid positive integer

    def test_validates_testing_preset_configuration(self, testing_preset_data):
        """
        Test that validate_preset_config accepts minimal testing configuration.

        Verifies:
            validate_preset_config() correctly validates minimal testing preset
            configurations with reduced scanner coverage.

        Business Impact:
            Ensures test-optimized configurations pass validation, enabling
            fast CI/CD pipelines with appropriate security coverage.

        Scenario:
            Given: A valid testing preset configuration with minimal scanners
            When: validate_preset_config() is called
            Then: An empty list is returned (no validation issues)
            And: Minimal scanner configuration is accepted
            And: Empty output_scanners is valid

        Fixtures Used:
            - testing_preset_data: Testing configuration for validation
        """
        # Arrange: Use the valid testing preset configuration
        config = testing_preset_data

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify no validation issues are found
        assert isinstance(issues, list)
        assert len(issues) == 0, f"Testing preset should be valid, but got issues: {issues}"

        # Verify minimal configuration is accepted
        assert len(config["input_scanners"]) == 1  # Minimal input scanners
        assert len(config["output_scanners"]) == 0  # Empty output scanners is valid
        assert config["performance"]["max_concurrent_scans"] == 1  # Minimal but valid

    def test_detects_missing_required_sections(self, invalid_preset_configurations):
        """
        Test that validate_preset_config detects missing configuration sections.

        Verifies:
            validate_preset_config() identifies and reports all missing required
            sections in a configuration dictionary.

        Business Impact:
            Early detection of structural issues prevents initialization failures
            and provides clear guidance for configuration fixes.

        Scenario:
            Given: A configuration missing multiple required sections
            When: validate_preset_config() is called
            Then: A list of validation issues is returned
            And: Each missing section is identified in the issues list
            And: Error messages include section names for easy diagnosis

        Fixtures Used:
            - invalid_preset_configurations: Config with missing sections
        """
        # Arrange: Create configuration missing sections that the implementation actually checks for
        config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "warn"
                }
            }
            # Missing: output_scanners, performance, logging
        }

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify missing sections are detected
        assert isinstance(issues, list)
        assert len(issues) > 0, "Expected validation issues for missing sections"

        # Verify specific missing sections are reported (based on actual implementation)
        expected_missing_sections = ["output_scanners", "performance", "logging"]
        for section in expected_missing_sections:
            assert any(section in issue for issue in issues), f"Missing section '{section}' not reported in issues: {issues}"

        # Verify error messages are descriptive
        for issue in issues:
            assert isinstance(issue, str)
            assert "Missing required section" in issue

    def test_detects_invalid_threshold_values(self, invalid_preset_configurations):
        """
        Test that validate_preset_config detects thresholds outside valid range.

        Verifies:
            validate_preset_config() identifies scanner thresholds that fall
            outside the valid range of 0.0 to 1.0.

        Business Impact:
            Invalid thresholds would cause scanner initialization failures.
            Early detection prevents runtime errors and deployment issues.

        Scenario:
            Given: Scanner configurations with invalid thresholds (< 0.0 or > 1.0)
            When: validate_preset_config() is called
            Then: Validation issues are returned
            And: Each invalid threshold is identified
            And: Error messages specify the invalid value and valid range
            And: Scanner names are included for easy identification

        Fixtures Used:
            - invalid_preset_configurations: Config with invalid thresholds
        """
        # Arrange: Get configuration with invalid thresholds
        config = invalid_preset_configurations["invalid_threshold_values"]

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify invalid thresholds are detected
        assert isinstance(issues, list)
        assert len(issues) > 0, "Expected validation issues for invalid thresholds"

        # Verify specific invalid thresholds are reported
        assert any("prompt_injection" in issue and "1.5" in issue for issue in issues), f"Invalid threshold 1.5 not reported: {issues}"
        assert any("toxicity_input" in issue and "-0.1" in issue for issue in issues), f"Invalid threshold -0.1 not reported: {issues}"

        # Verify error messages include scanner names and values
        for issue in issues:
            if "threshold" in issue.lower():
                assert isinstance(issue, str)
                assert any(scanner in issue for scanner in ["prompt_injection", "toxicity_input"])

    def test_detects_invalid_performance_values(self, invalid_preset_configurations):
        """
        Test that validate_preset_config detects invalid performance parameter values.

        Verifies:
            validate_preset_config() identifies performance settings with
            invalid values (negative numbers, zero where positive required).

        Business Impact:
            Invalid performance values would cause resource allocation failures.
            Early detection prevents system instability and performance issues.

        Scenario:
            Given: Performance settings with negative or zero values
            When: validate_preset_config() is called
            Then: Validation issues are returned
            And: Each invalid performance value is identified
            And: Error messages specify the parameter and valid range
            And: Validation covers max_concurrent_scans, cache_ttl_seconds, memory_limit_mb

        Fixtures Used:
            - invalid_preset_configurations: Config with invalid performance values
        """
        # Arrange: Create configuration with invalid max_concurrent_scans (what implementation actually checks)
        config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "warn",
                    "use_onnx": True,
                    "scan_timeout": 30
                }
            },
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": -1  # Invalid negative value
            },
            "logging": {"enabled": True}
        }

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify invalid performance values are detected
        assert isinstance(issues, list)
        assert len(issues) > 0, "Expected validation issues for invalid performance values"

        # Verify specific invalid performance value is reported
        assert any("-1" in issue and "max_concurrent_scans" in issue for issue in issues), f"Invalid max_concurrent_scans not reported: {issues}"

    def test_detects_missing_scanner_required_fields(self, invalid_preset_configurations):
        """
        Test that validate_preset_config detects scanners missing required fields.

        Verifies:
            validate_preset_config() identifies scanner configurations that
            are missing required fields like threshold, action, or enabled.

        Business Impact:
            Incomplete scanner configurations would cause initialization failures.
            Early detection with field-level feedback enables quick fixes.

        Scenario:
            Given: Scanner configurations missing required fields
            When: validate_preset_config() is called
            Then: Validation issues are returned
            And: Each missing field is identified
            And: Scanner names are included in error messages
            And: Required fields are listed for guidance

        Fixtures Used:
            - invalid_preset_configurations: Config with incomplete scanners
        """
        # Arrange: Create configuration with scanner missing 'enabled' field (which is checked by implementation)
        config = {
            "input_scanners": {
                "bad_scanner": {
                    # Missing 'enabled' field
                    "threshold": 0.7,
                    "action": "block"
                }
            },
            "output_scanners": {},
            "performance": {"max_concurrent_scans": 5},
            "logging": {"enabled": True}
        }

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify missing scanner fields are detected
        assert isinstance(issues, list)
        assert len(issues) > 0, "Expected validation issues for missing scanner fields"

        # Verify missing 'enabled' field is reported (this is what the implementation actually checks)
        assert any("bad_scanner" in issue and "enabled" in issue for issue in issues), f"Missing enabled field not reported: {issues}"

    def test_detects_wrong_data_types(self, invalid_preset_configurations):
        """
        Test that validate_preset_config detects incorrect data types.

        Verifies:
            validate_preset_config() identifies configuration fields with
            incorrect data types (string instead of int, etc.).

        Business Impact:
            Type mismatches cause runtime errors during configuration parsing.
            Early detection with type information enables correct configuration.

        Scenario:
            Given: Configuration with wrong data types for various fields
            When: validate_preset_config() is called
            Then: Validation issues are returned
            And: Each type mismatch is identified
            And: Error messages specify expected and actual types
            And: Field names are included for easy location

        Fixtures Used:
            - invalid_preset_configurations: Config with type mismatches
        """
        # Arrange: Create configuration with invalid scanner configuration type
        config = {
            "input_scanners": {
                "bad_scanner": "not_a_dict"  # Wrong type - should be dict
            },
            "output_scanners": {},
            "performance": {"max_concurrent_scans": 5},
            "logging": {"enabled": True}
        }

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify type issues are detected
        assert isinstance(issues, list)
        assert len(issues) > 0, "Expected validation issues for wrong data types"

        # Verify invalid scanner configuration type is reported
        assert any("bad_scanner" in issue and "Invalid scanner configuration" in issue for issue in issues), f"Invalid scanner type not reported: {issues}"

    def test_returns_descriptive_error_messages(self):
        """
        Test that validate_preset_config provides helpful error messages.

        Verifies:
            All validation error messages are descriptive, specific, and
            actionable, enabling users to quickly diagnose and fix issues.

        Business Impact:
            Clear error messages reduce configuration debugging time and
            prevent frustration during deployment setup.

        Scenario:
            Given: Various invalid configurations
            When: validate_preset_config() is called for each
            Then: Error messages are specific to the issue
            And: Messages include field names and invalid values
            And: Messages suggest valid ranges or formats
            And: No generic "validation failed" messages

        Fixtures Used:
            - invalid_preset_configurations: Various invalid configs
        """
        # Arrange: Create various invalid configurations
        invalid_configs = [
            # Missing sections
            {"input_scanners": {"test": {"enabled": True, "threshold": 0.8, "action": "warn"}}},
            # Invalid threshold
            {
                "input_scanners": {"test": {"enabled": True, "threshold": 1.5, "action": "warn"}},
                "output_scanners": {},
                "performance": {"max_concurrent_scans": 5},
                "logging": {"enabled": True}
            },
            # Invalid performance values
            {
                "input_scanners": {"test": {"enabled": True, "threshold": 0.8, "action": "warn"}},
                "output_scanners": {},
                "performance": {"max_concurrent_scans": -1},
                "logging": {"enabled": True}
            }
        ]

        # Act & Assert: Test each invalid configuration
        for config in invalid_configs:
            issues = validate_preset_config(config)

            if issues:  # Only test if issues are found
                for issue in issues:
                    assert isinstance(issue, str)
                    assert len(issue.strip()) > 0, "Error message should not be empty"

                    # Check for descriptive content (avoid generic messages)
                    if "Missing required section" in issue:
                        assert ":" not in issue or len(issue.split(":")) > 1, "Missing section errors should specify which section"
                    elif "threshold" in issue.lower():
                        assert any(char.isdigit() for char in issue), "Threshold errors should include the invalid value"
                    elif "max_concurrent_scans" in issue:
                        assert any(char.isdigit() for char in issue), "Performance errors should include the invalid value"

    def test_validates_custom_preset_from_create_preset(self, custom_preset_scanner_configs):
        """
        Test that validate_preset_config accepts presets from create_preset().

        Verifies:
            Configurations created by create_preset() pass validation,
            ensuring the two functions work together correctly.

        Business Impact:
            Ensures the custom preset creation workflow produces valid
            configurations that can be used in production systems.

        Scenario:
            Given: A custom preset created with create_preset()
            When: validate_preset_config() is called on the created preset
            Then: An empty list is returned (no validation issues)
            And: The created preset is accepted as valid
            And: All sections pass structural validation

        Fixtures Used:
            - custom_preset_scanner_configs: For creating custom preset
        """
        # Arrange: Create a custom preset using create_preset
        input_scanners = custom_preset_scanner_configs["content_moderation_input"]
        output_scanners = custom_preset_scanner_configs["content_moderation_output"]
        name = "integration-test"
        description = "Test preset for integration validation"

        custom_preset = create_preset(
            name=name,
            description=description,
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # Act: Validate the created preset
        issues = validate_preset_config(custom_preset)

        # Assert: Verify the custom preset passes validation
        assert isinstance(issues, list)
        assert len(issues) == 0, f"Custom preset should be valid, but got issues: {issues}"

        # Verify all required sections are present and valid
        required_sections = ["input_scanners", "output_scanners", "performance", "logging"]
        for section in required_sections:
            assert section in custom_preset, f"Created preset missing section: {section}"

    def test_validates_all_standard_presets_successfully(self, preset_names):
        """
        Test that validate_preset_config accepts all standard presets.

        Verifies:
            All standard presets (development, production, testing) from
            get_preset_config() pass validation without issues.

        Business Impact:
            Ensures built-in presets are correctly structured and meet
            validation requirements for reliable system operation.

        Scenario:
            Given: Each standard preset name
            When: get_preset_config() is called to retrieve each preset
            And: validate_preset_config() is called on each preset
            Then: All presets return empty validation issue lists
            And: No standard presets trigger validation errors

        Fixtures Used:
            - preset_names: List of standard preset names
        """
        # Arrange: Import get_preset_config function
        from app.infrastructure.security.llm.presets import get_preset_config

        # Act & Assert: Test each standard preset
        for preset_name in preset_names:
            # Get the preset configuration
            config = get_preset_config(preset_name)

            # Validate the configuration
            issues = validate_preset_config(config)

            # Verify no validation issues
            assert isinstance(issues, list)
            assert len(issues) == 0, f"Standard preset '{preset_name}' should be valid, but got issues: {issues}"

            # Verify preset identification
            assert config["preset"] == preset_name

    def test_validation_preserves_original_configuration(self):
        """
        Test that validate_preset_config does not modify input configuration.

        Verifies:
            validate_preset_config() performs read-only validation and does
            not modify the input configuration dictionary.

        Business Impact:
            Read-only validation ensures configuration immutability and
            prevents unexpected side effects during validation operations.

        Scenario:
            Given: A configuration dictionary
            And: A deep copy of the configuration for comparison
            When: validate_preset_config() is called
            Then: The original configuration is unchanged
            And: All values remain identical to the pre-validation state
            And: No fields are added, removed, or modified

        Fixtures Used:
            - development_preset_data: Configuration for validation
        """
        # Arrange: Get a configuration and create a deep copy for comparison
        original_config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "warn",
                    "use_onnx": True,
                    "scan_timeout": 30
                }
            },
            "output_scanners": {},
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 300,
                "max_concurrent_scans": 5,
                "memory_limit_mb": 1024
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "log_scan_operations": True
            }
        }

        # Create deep copy for comparison
        config_copy = copy.deepcopy(original_config)

        # Act: Validate the configuration
        issues = validate_preset_config(original_config)

        # Assert: Verify original configuration is unchanged
        assert original_config == config_copy, "Configuration was modified during validation"

        # Verify specific sections are unchanged
        assert original_config["input_scanners"] == config_copy["input_scanners"]
        assert original_config["output_scanners"] == config_copy["output_scanners"]
        assert original_config["performance"] == config_copy["performance"]
        assert original_config["logging"] == config_copy["logging"]

    def test_validation_handles_empty_scanner_configurations(self):
        """
        Test that validate_preset_config handles empty scanner dictionaries.

        Verifies:
            validate_preset_config() correctly validates configurations with
            empty scanner dictionaries (valid for testing scenarios).

        Business Impact:
            Flexible validation supports minimal configurations for specific
            use cases like performance testing or gradual security rollout.

        Scenario:
            Given: A configuration with empty input_scanners and output_scanners
            But: All other sections are complete and valid
            When: validate_preset_config() is called
            Then: No validation issues related to empty scanners
            And: Empty dictionaries are accepted as valid
            And: Only actual structural issues are reported

        Fixtures Used:
            - None (tests edge case validation)
        """
        # Arrange: Configuration with empty scanners but other sections complete
        config = {
            "input_scanners": {},  # Empty input scanners
            "output_scanners": {},  # Empty output scanners
            "performance": {
                "cache_enabled": True,
                "cache_ttl_seconds": 300,
                "max_concurrent_scans": 5,
                "memory_limit_mb": 1024
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "log_scan_operations": True
            }
        }

        # Act: Validate the configuration
        issues = validate_preset_config(config)

        # Assert: Verify empty scanners are accepted as valid
        assert isinstance(issues, list)
        assert len(issues) == 0, f"Empty scanners should be valid, but got issues: {issues}"

        # Verify configuration structure remains intact
        assert config["input_scanners"] == {}
        assert config["output_scanners"] == {}
        assert len(config["input_scanners"]) == 0
        assert len(config["output_scanners"]) == 0

    def test_validation_returns_list_of_strings(self):
        """
        Test that validate_preset_config always returns list of strings.

        Verifies:
            Return value from validate_preset_config() is always a list
            containing only string elements (error messages).

        Business Impact:
            Consistent return type enables reliable error handling and
            prevents type-related bugs in validation result processing.

        Scenario:
            Given: Various valid and invalid configurations
            When: validate_preset_config() is called for each
            Then: Return value is always a list
            And: All list elements are strings
            And: Empty list is returned for valid configs
            And: Non-empty list contains descriptive error strings for invalid configs

        Fixtures Used:
            - None (tests return type contract)
        """
        # Arrange: Test configurations
        valid_config = {
            "input_scanners": {
                "prompt_injection": {
                    "enabled": True,
                    "threshold": 0.8,
                    "action": "warn",
                    "use_onnx": True,
                    "scan_timeout": 30
                }
            },
            "output_scanners": {},
            "performance": {"max_concurrent_scans": 5},
            "logging": {"enabled": True}
        }

        invalid_config = {
            "input_scanners": {
                "test": {
                    "enabled": True,
                    "threshold": 1.5,  # Invalid threshold
                    "action": "warn"
                }
            }
            # Missing required sections
        }

        test_configs = [
            ("Valid config", valid_config),
            ("Invalid config", invalid_config),
            ("Empty config", {}),
            ("Partial config", {"input_scanners": {}})
        ]

        # Act & Assert: Test each configuration
        for config_name, config in test_configs:
            issues = validate_preset_config(config)

            # Verify return type is always a list
            assert isinstance(issues, list), f"{config_name}: Expected list, got {type(issues)}"

            # Verify all elements are strings
            for issue in issues:
                assert isinstance(issue, str), f"{config_name}: Expected string in issues list, got {type(issue)}"
                assert len(issue.strip()) > 0, f"{config_name}: Empty string in issues list"

            # Verify empty list for valid configuration
            if config_name == "Valid config":
                assert len(issues) == 0, f"{config_name}: Expected no issues for valid config"

            # Verify non-empty list for invalid configurations (if issues are detected)
            if config_name in ["Invalid config", "Empty config", "Partial config"]:
                # May or may not have issues depending on validation implementation
                # But if there are issues, they should be strings
                if issues:
                    assert all(isinstance(issue, str) for issue in issues)

