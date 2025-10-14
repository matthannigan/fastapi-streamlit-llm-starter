"""
Unit tests for preset module integration and edge cases.

This test module verifies integration scenarios between preset functions and
edge cases that don't fit into specific function categories. Tests focus on
how the preset functions work together and handle boundary conditions.

Test Strategy:
    - Component Under Test: Integration of all preset module functions
    - Testing Approach: Black-box testing of function interactions
    - No Mocking: Pure functions with no external dependencies
    - Contract Source: backend/contracts/infrastructure/security/llm/presets.pyi

Fixtures Available:
    From conftest.py (backend/tests/unit/llm_security/presets/conftest.py):
    - preset_names: List of available preset names
    - preset_descriptions: Preset descriptions
    - development_preset_data: Development preset structure
    - production_preset_data: Production preset structure
    - testing_preset_data: Testing preset structure
    - custom_preset_examples: Custom preset examples
"""

import pytest
import threading
import time
from typing import Dict, Any, List

from app.infrastructure.security.llm.presets import (
    get_preset_config,
    list_presets,
    get_preset_description,
    create_preset,
    validate_preset_config
)


class TestPresetRetrievalIntegration:
    """
    Test suite for integration between preset retrieval functions.
    
    Scope:
        Verifies that list_presets(), get_preset_description(), and
        get_preset_config() work together correctly and consistently.
        
    Business Critical:
        Integration failures would prevent users from discovering and
        selecting appropriate security configurations.
        
    Test Strategy:
        - Test consistency across discovery and retrieval functions
        - Verify descriptions match actual preset characteristics
        - Test complete preset selection workflow
    """

    def test_list_presets_and_get_preset_config_are_synchronized(self):
        """
        Test that all presets from list_presets work with get_preset_config.

        Verifies:
            Every preset name returned by list_presets() can be successfully
            passed to get_preset_config() without errors, ensuring discovery
            and retrieval are synchronized.

        Business Impact:
            Prevents user frustration from discovering presets they cannot use.
            Ensures configuration selection workflow is reliable.

        Scenario:
            Given: The complete list of preset names from list_presets()
            When: get_preset_config() is called for each preset name
            Then: No ValueError is raised for any preset name
            And: Each call returns a valid configuration dictionary
            And: The returned preset field matches the requested name

        Fixtures Used:
            - None (tests integration between functions)
        """
        # Given: The complete list of preset names from list_presets()
        available_presets = list_presets()

        # When: get_preset_config() is called for each preset name
        retrieved_configs = {}
        for preset_name in available_presets:
            # Then: No ValueError is raised for any preset name
            config = get_preset_config(preset_name)

            # And: Each call returns a valid configuration dictionary
            assert isinstance(config, dict), f"Config for {preset_name} should be a dictionary"
            assert "preset" in config, f"Config for {preset_name} should have 'preset' field"

            # And: The returned preset field matches the requested name
            assert config["preset"] == preset_name, f"Config preset field should match requested name"

            retrieved_configs[preset_name] = config

        # Verify all expected presets were found
        expected_presets = ["development", "production", "testing"]
        assert len(available_presets) == len(expected_presets), f"Should have exactly {len(expected_presets)} presets"
        assert set(available_presets) == set(expected_presets), "Presets should match expected set"

        # Verify configs are different but all valid
        config_signatures = set()
        for preset_name, config in retrieved_configs.items():
            # Create a signature based on key sections to ensure configs are meaningfully different
            signature = (
                len(config.get("input_scanners", {})),
                len(config.get("output_scanners", {})),
                config.get("service", {}).get("environment")
            )
            config_signatures.add(signature)

        # Should have different signatures for different presets
        assert len(config_signatures) > 1, "Different presets should have different configurations"

    def test_preset_descriptions_match_available_presets(self):
        """
        Test that get_preset_description works for all presets from list_presets.

        Verifies:
            Every preset name from list_presets() has a corresponding
            description available from get_preset_description().

        Business Impact:
            Ensures users can get information about all available presets
            for informed configuration selection.

        Scenario:
            Given: The complete list of preset names from list_presets()
            When: get_preset_description() is called for each preset name
            Then: No preset returns "Unknown preset" message
            And: Each description is a helpful, non-empty string
            And: Descriptions are unique across presets

        Fixtures Used:
            - None (tests integration between functions)
        """
        # Given: The complete list of preset names from list_presets()
        available_presets = list_presets()

        # When: get_preset_description() is called for each preset name
        descriptions = {}
        for preset_name in available_presets:
            description = get_preset_description(preset_name)
            descriptions[preset_name] = description

            # Then: No preset returns "Unknown preset" message
            assert description != "Unknown preset", f"Preset {preset_name} should have a valid description"

            # And: Each description is a helpful, non-empty string
            assert isinstance(description, str), f"Description for {preset_name} should be a string"
            assert len(description.strip()) > 0, f"Description for {preset_name} should not be empty"
            assert len(description) > 10, f"Description for {preset_name} should be meaningful"

        # And: Descriptions are unique across presets
        unique_descriptions = set(descriptions.values())
        assert len(unique_descriptions) == len(descriptions), "Each preset should have a unique description"

        # Verify specific expected keywords are present in descriptions
        expected_keywords = {
            "development": ["lenient", "development", "iteration"],
            "production": ["strict", "security", "production"],
            "testing": ["minimal", "fast", "testing"]
        }

        for preset_name, description in descriptions.items():
            keywords = expected_keywords.get(preset_name, [])
            for keyword in keywords:
                assert keyword in description.lower(), f"Description for {preset_name} should mention '{keyword}'"

    def test_preset_descriptions_accurately_reflect_configurations(self, preset_descriptions):
        """
        Test that preset descriptions match actual preset characteristics.

        Verifies:
            Descriptions from get_preset_description() accurately reflect
            the actual security settings in corresponding preset configurations.

        Business Impact:
            Accurate descriptions prevent misconfiguration by ensuring users
            understand what they're selecting before deployment.

        Scenario:
            Given: Development preset and its description
            When: Description is compared to actual configuration
            Then: Description mentions "lenient" or "development"
            And: Configuration actually has lenient thresholds (>= 0.8)

            Given: Production preset and its description
            When: Description is compared to actual configuration
            Then: Description mentions "strict" or "security"
            And: Configuration actually has strict thresholds (<= 0.7)

            Given: Testing preset and its description
            When: Description is compared to actual configuration
            Then: Description mentions "minimal" or "fast"
            And: Configuration actually has minimal scanners

        Fixtures Used:
            - preset_descriptions: Expected descriptions for comparison
        """
        # Given: Development preset and its description
        dev_config = get_preset_config("development")
        dev_description = get_preset_description("development")

        # When: Description is compared to actual configuration
        # Then: Description mentions "lenient" or "development"
        assert any(keyword in dev_description.lower() for keyword in ["lenient", "development"]), \
            f"Development description should mention lenient settings or development"

        # And: Configuration actually has lenient thresholds (>= 0.8)
        dev_scanners = dev_config.get("input_scanners", {})
        for scanner_name, scanner_config in dev_scanners.items():
            threshold = scanner_config.get("threshold", 0.0)
            assert threshold >= 0.8, f"Development scanner {scanner_name} should have lenient threshold >= 0.8, got {threshold}"

        # Given: Production preset and its description
        prod_config = get_preset_config("production")
        prod_description = get_preset_description("production")

        # When: Description is compared to actual configuration
        # Then: Description mentions "strict" or "security"
        assert any(keyword in prod_description.lower() for keyword in ["strict", "security"]), \
            f"Production description should mention strict settings or security"

        # And: Configuration actually has strict thresholds (<= 0.7)
        prod_scanners = prod_config.get("input_scanners", {})
        strict_thresholds_found = False
        for scanner_name, scanner_config in prod_scanners.items():
            threshold = scanner_config.get("threshold", 1.0)
            if threshold <= 0.7:
                strict_thresholds_found = True
            # Allow some flexibility - not all scanners might be strict
            assert 0.0 <= threshold <= 1.0, f"Production scanner {scanner_name} should have valid threshold, got {threshold}"

        assert strict_thresholds_found, "Production preset should have at least one scanner with strict threshold <= 0.7"

        # Given: Testing preset and its description
        test_config = get_preset_config("testing")
        test_description = get_preset_description("testing")

        # When: Description is compared to actual configuration
        # Then: Description mentions "minimal" or "fast"
        assert any(keyword in test_description.lower() for keyword in ["minimal", "fast", "testing"]), \
            f"Testing description should mention minimal scanners or fast execution"

        # And: Configuration actually has minimal scanners
        test_input_scanners = test_config.get("input_scanners", {})
        test_output_scanners = test_config.get("output_scanners", {})
        assert len(test_input_scanners) == 1, f"Testing preset should have exactly 1 input scanner, got {len(test_input_scanners)}"
        assert len(test_output_scanners) == 0, f"Testing preset should have no output scanners, got {len(test_output_scanners)}"

        # Verify the one input scanner is prompt injection
        assert "prompt_injection" in test_input_scanners, "Testing preset should have prompt injection scanner"

    def test_complete_preset_discovery_workflow(self):
        """
        Test complete workflow: discover, describe, retrieve preset.

        Verifies:
            The complete user workflow of discovering available presets,
            reading descriptions, and retrieving configurations works
            seamlessly without errors.

        Business Impact:
            Ensures end-to-end preset selection workflow is user-friendly
            and reliable for configuration setup.

        Scenario:
            Given: A user needs to select a security preset
            When: list_presets() is called to discover options
            And: get_preset_description() is called for each option
            And: get_preset_config() is called for the selected preset
            Then: All operations complete successfully
            And: No errors occur at any step
            And: Final configuration matches the selected preset's description

        Fixtures Used:
            - None (tests complete workflow integration)
        """
        # Given: A user needs to select a security preset

        # When: list_presets() is called to discover options
        try:
            available_presets = list_presets()
        except Exception as e:
            pytest.fail(f"list_presets() failed: {e}")

        # And: get_preset_description() is called for each option
        preset_info = {}
        try:
            for preset_name in available_presets:
                description = get_preset_description(preset_name)
                preset_info[preset_name] = {
                    "description": description,
                    "config": None
                }
        except Exception as e:
            pytest.fail(f"get_preset_description() failed: {e}")

        # And: get_preset_config() is called for the selected preset
        # Simulate user selecting production preset for maximum security
        selected_preset = "production"
        try:
            config = get_preset_config(selected_preset)
            preset_info[selected_preset]["config"] = config
        except Exception as e:
            pytest.fail(f"get_preset_config() failed for {selected_preset}: {e}")

        # Then: All operations complete successfully
        assert len(available_presets) > 0, "Should have available presets"
        assert selected_preset in available_presets, "Selected preset should be available"
        assert preset_info[selected_preset]["description"] != "Unknown preset", "Selected preset should have valid description"
        assert preset_info[selected_preset]["config"] is not None, "Selected preset should have configuration"

        # And: No errors occur at any step (verified by no exceptions above)

        # And: Final configuration matches the selected preset's description
        config = preset_info[selected_preset]["config"]
        description = preset_info[selected_preset]["description"]

        # Verify configuration characteristics match description
        assert config["preset"] == selected_preset, "Configuration should match selected preset"
        assert "strict" in description.lower() or "security" in description.lower(), \
            "Production description should mention strict settings or security"

        # Verify production-specific characteristics
        service_config = config.get("service", {})
        assert service_config.get("environment") == "production", "Production config should have production environment"
        assert service_config.get("api_key_required") is True, "Production should require API key"

        # Verify comprehensive scanner coverage
        input_scanners = config.get("input_scanners", {})
        output_scanners = config.get("output_scanners", {})
        assert len(input_scanners) >= 3, "Production should have comprehensive input scanners"
        assert len(output_scanners) >= 2, "Production should have comprehensive output scanners"

        # Workflow completed successfully
        assert True, "Complete preset discovery workflow completed successfully"


class TestCustomPresetIntegration:
    """
    Test suite for integration between create_preset and validation.
    
    Scope:
        Verifies that create_preset() and validate_preset_config() work
        together correctly, and custom presets integrate with retrieval functions.
        
    Business Critical:
        Integration failures would prevent users from creating and deploying
        custom security configurations for specialized use cases.
        
    Test Strategy:
        - Test create_preset output passes validation
        - Verify custom presets work with standard preset functions
        - Test preset creation and usage workflow
    """

    def test_created_presets_pass_validation(self, custom_preset_scanner_configs):
        """
        Test that presets from create_preset pass validate_preset_config.

        Verifies:
            Custom presets created by create_preset() automatically meet
            all validation requirements without additional configuration.

        Business Impact:
            Ensures custom preset creation workflow produces production-ready
            configurations that deploy successfully.

        Scenario:
            Given: A custom preset created with create_preset()
            When: validate_preset_config() is called on the created preset
            Then: No validation issues are returned (empty list)
            And: The preset is ready for immediate use
            And: All required sections are present and valid

        Fixtures Used:
            - custom_preset_scanner_configs: For creating custom preset
        """
        # Given: A custom preset created with create_preset()
        custom_preset = create_preset(
            name="test-custom-preset",
            description="Test preset for validation",
            input_scanners=custom_preset_scanner_configs["content_moderation_input"],
            output_scanners=custom_preset_scanner_configs["content_moderation_output"]
        )

        # When: validate_preset_config() is called on the created preset
        validation_issues = validate_preset_config(custom_preset)

        # Then: No validation issues are returned (empty list)
        assert validation_issues == [], f"Custom preset should pass validation without issues, got: {validation_issues}"

        # And: The preset is ready for immediate use
        assert isinstance(custom_preset, dict), "Custom preset should be a dictionary"

        # And: All required sections are present and valid
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service"]
        for section in required_sections:
            assert section in custom_preset, f"Custom preset should have required section: {section}"
            assert isinstance(custom_preset[section], dict), f"Section {section} should be a dictionary"

        # Verify custom scanner configurations are preserved
        input_scanners = custom_preset["input_scanners"]
        assert len(input_scanners) > 0, "Should have input scanners"
        for scanner_name, scanner_config in input_scanners.items():
            assert "enabled" in scanner_config, f"Scanner {scanner_name} should have 'enabled' field"
            assert "threshold" in scanner_config, f"Scanner {scanner_name} should have 'threshold' field"
            threshold = scanner_config["threshold"]
            assert 0.0 <= threshold <= 1.0, f"Scanner {scanner_name} should have valid threshold, got {threshold}"

        # Verify preset identification
        assert custom_preset.get("preset") == "test-custom-preset", "Preset should have correct name"

    def test_created_preset_with_overrides_passes_validation(
        self,
        custom_preset_scanner_configs,
        custom_preset_performance_overrides,
        custom_preset_logging_overrides
    ):
        """
        Test that fully customized presets pass validation.

        Verifies:
            Custom presets with extensive overrides for performance and
            logging still meet all validation requirements.

        Business Impact:
            Ensures advanced customization features don't inadvertently
            create invalid configurations.

        Scenario:
            Given: A custom preset with all customization options used
            When: validate_preset_config() is called
            Then: No validation issues are returned
            And: All custom overrides are present and valid
            And: No conflicts exist between overridden and base settings

        Fixtures Used:
            - custom_preset_scanner_configs: Scanner customization
            - custom_preset_performance_overrides: Performance customization
            - custom_preset_logging_overrides: Logging customization
        """
        # Given: A custom preset with all customization options used
        custom_preset = create_preset(
            name="test-fully-customized",
            description="Test preset with all customizations",
            input_scanners=custom_preset_scanner_configs["content_moderation_input"],
            output_scanners=custom_preset_scanner_configs["content_moderation_output"],
            performance_overrides=custom_preset_performance_overrides["content_moderation"],
            logging_overrides=custom_preset_logging_overrides["content_moderation"]
        )

        # When: validate_preset_config() is called
        validation_issues = validate_preset_config(custom_preset)

        # Then: No validation issues are returned
        assert validation_issues == [], f"Fully customized preset should pass validation, got: {validation_issues}"

        # And: All custom overrides are present and valid
        performance_config = custom_preset.get("performance", {})
        expected_performance = custom_preset_performance_overrides["content_moderation"]

        # Verify performance overrides were applied
        for key, expected_value in expected_performance.items():
            if key in performance_config:
                actual_value = performance_config[key]
                assert actual_value == expected_value, \
                    f"Performance override {key} should be {expected_value}, got {actual_value}"

        # Verify logging overrides were applied
        logging_config = custom_preset.get("logging", {})
        expected_logging = custom_preset_logging_overrides["content_moderation"]

        for key, expected_value in expected_logging.items():
            if key in logging_config:
                actual_value = logging_config[key]
                assert actual_value == expected_value, \
                    f"Logging override {key} should be {expected_value}, got {actual_value}"

        # And: No conflicts exist between overridden and base settings
        # Verify performance settings are valid
        if "max_concurrent_scans" in performance_config:
            max_scans = performance_config["max_concurrent_scans"]
            assert isinstance(max_scans, int) and max_scans > 0, \
                f"max_concurrent_scans should be positive integer, got {max_scans}"

        if "cache_ttl_seconds" in performance_config:
            cache_ttl = performance_config["cache_ttl_seconds"]
            assert isinstance(cache_ttl, int) and cache_ttl > 0, \
                f"cache_ttl_seconds should be positive integer, got {cache_ttl}"

        # Verify logging settings are valid
        if "level" in logging_config:
            log_level = logging_config["level"]
            assert isinstance(log_level, str) and log_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR"], \
                f"log_level should be valid logging level, got {log_level}"

        # Verify structure remains intact
        assert custom_preset.get("preset") == "test-fully-customized", "Preset name should be preserved"
        assert "input_scanners" in custom_preset, "Input scanners should be present"
        assert "output_scanners" in custom_preset, "Output scanners should be present"
        assert "service" in custom_preset, "Service configuration should be present"

    def test_validation_catches_issues_in_manually_constructed_presets(self):
        """
        Test that validate_preset_config catches issues not caught by create_preset.

        Verifies:
            validate_preset_config() provides additional safety by catching
            issues in manually constructed preset dictionaries.

        Business Impact:
            Provides safety net for configurations created or modified outside
            the create_preset workflow.

        Scenario:
            Given: A manually constructed preset dictionary with issues
            When: validate_preset_config() is called
            Then: Validation issues are detected and reported
            And: Error messages guide users to fix the problems
            And: Validation catches structural and value issues

        Fixtures Used:
            - None (tests validation of manually created configs)
        """
        # Given: A manually constructed preset dictionary with issues
        invalid_config = {
            "preset": "manual-preset",
            "input_scanners": {
                "bad_scanner": {
                    "enabled": True,
                    "threshold": 1.5,  # Invalid threshold > 1.0
                    "action": "block"
                },
                "incomplete_scanner": {
                    "enabled": True
                    # Missing threshold and action
                }
            },
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": -1,  # Invalid negative value
                "cache_ttl_seconds": 0       # Invalid zero value
            },
            "logging": {
                "enabled": "not_boolean"  # Invalid data type
            }
            # Missing required service section
        }

        # When: validate_preset_config() is called
        validation_issues = validate_preset_config(invalid_config)

        # Then: Validation issues are detected and reported
        assert len(validation_issues) > 0, "Should detect validation issues"
        assert validation_issues != [], f"Should return non-empty list of issues, got: {validation_issues}"

        # And: Error messages guide users to fix the problems
        issues_text = " ".join(validation_issues).lower()

        # Should mention threshold issues
        assert any("threshold" in issue.lower() for issue in validation_issues), \
            "Should mention threshold validation issues"

        # Should mention missing required sections
        assert any("missing" in issue.lower() for issue in validation_issues), \
            "Should mention missing required sections"

        # Should mention invalid performance values
        assert any("max_concurrent_scans" in issue.lower() or "concurrent" in issue.lower() for issue in validation_issues), \
            "Should mention invalid performance settings"

        # And: Validation catches structural and value issues
        # Test structural issues (missing required sections)
        minimal_invalid_config = {
            "preset": "minimal-invalid",
            "input_scanners": {},
            # Missing output_scanners, performance, logging, service
        }

        structural_issues = validate_preset_config(minimal_invalid_config)
        assert len(structural_issues) > 0, "Should catch missing required sections"
        assert any("missing required section" in issue.lower() for issue in structural_issues), \
            "Should explicitly mention missing required sections"

        # Test value range issues
        range_invalid_config = {
            "preset": "range-invalid",
            "input_scanners": {
                "test_scanner": {
                    "enabled": True,
                    "threshold": -0.5,  # Invalid negative threshold
                    "action": "warn"
                }
            },
            "output_scanners": {},
            "performance": {
                "max_concurrent_scans": 5  # Valid
            },
            "logging": {
                "enabled": True
            },
            "service": {
                "environment": "test"
            }
        }

        range_issues = validate_preset_config(range_invalid_config)
        assert len(range_issues) > 0, "Should catch threshold range issues"
        assert any("threshold" in issue.lower() for issue in range_issues), \
            "Should mention threshold validation errors"

    def test_custom_preset_can_be_used_like_standard_preset(self, custom_preset_scanner_configs):
        """
        Test that custom presets work in same contexts as standard presets.

        Verifies:
            Custom preset configurations created by create_preset() can be
            used in the same way as standard presets from get_preset_config().

        Business Impact:
            Ensures custom presets are first-class citizens and can be used
            anywhere standard presets are used.

        Scenario:
            Given: A custom preset created with create_preset()
            And: A standard preset from get_preset_config()
            When: Both configurations are examined
            Then: Both have identical structure (same sections)
            And: Both pass validation
            And: Both can be used interchangeably in security systems

        Fixtures Used:
            - custom_preset_scanner_configs: For creating custom preset
        """
        # Given: A custom preset created with create_preset()
        custom_preset = create_preset(
            name="interchangeable-custom",
            description="Custom preset for interchangeability test",
            input_scanners=custom_preset_scanner_configs["content_moderation_input"],
            output_scanners=custom_preset_scanner_configs["content_moderation_output"]
        )

        # And: A standard preset from get_preset_config()
        standard_preset = get_preset_config("development")

        # When: Both configurations are examined

        # Then: Both have identical structure (same sections)
        custom_sections = set(custom_preset.keys())
        standard_sections = set(standard_preset.keys())

        # Custom presets should have at least the core sections that standard presets have
        core_sections = {"input_scanners", "output_scanners", "performance", "logging", "service"}
        assert core_sections.issubset(custom_sections), "Custom preset should have core sections"
        assert core_sections.issubset(standard_sections), "Standard preset should have core sections"

        # Both should have preset field
        assert "preset" in custom_preset, "Custom preset should have preset field"
        assert "preset" in standard_preset, "Standard preset should have preset field"

        # And: Both pass validation
        custom_validation = validate_preset_config(custom_preset)
        standard_validation = validate_preset_config(standard_preset)

        assert custom_validation == [], f"Custom preset should pass validation: {custom_validation}"
        assert standard_validation == [], f"Standard preset should pass validation: {standard_validation}"

        # And: Both can be used interchangeably in security systems
        # Test that both can be processed by the same validation logic
        def process_preset_config(preset_config, preset_type):
            """Simulate security system processing a preset configuration."""
            # Validate structure
            assert "input_scanners" in preset_config, f"{preset_type} preset should have input scanners"
            assert "output_scanners" in preset_config, f"{preset_type} preset should have output scanners"
            assert "performance" in preset_config, f"{preset_type} preset should have performance config"
            assert "logging" in preset_config, f"{preset_type} preset should have logging config"
            assert "service" in preset_config, f"{preset_type} preset should have service config"

            # Extract scanner configurations
            input_scanners = preset_config["input_scanners"]
            output_scanners = preset_config["output_scanners"]

            # Count enabled scanners
            enabled_input = sum(1 for scanner in input_scanners.values() if scanner.get("enabled", False))
            enabled_output = sum(1 for scanner in output_scanners.values() if scanner.get("enabled", False))

            # Get performance settings
            performance = preset_config["performance"]
            max_scans = performance.get("max_concurrent_scans", 1)

            # Return processed summary
            return {
                "preset_type": preset_type,
                "enabled_input_scanners": enabled_input,
                "enabled_output_scanners": enabled_output,
                "max_concurrent_scans": max_scans,
                "preset_name": preset_config.get("preset", "unknown")
            }

        # Process both presets with the same logic
        custom_result = process_preset_config(custom_preset, "custom")
        standard_result = process_preset_config(standard_preset, "standard")

        # Both should be processed successfully
        assert custom_result["preset_type"] == "custom"
        assert standard_result["preset_type"] == "standard"
        assert custom_result["preset_name"] == "interchangeable-custom"
        assert standard_result["preset_name"] == "development"

        # Both should have valid scanner counts and performance settings
        assert custom_result["enabled_input_scanners"] >= 0
        assert custom_result["enabled_output_scanners"] >= 0
        assert custom_result["max_concurrent_scans"] > 0

        assert standard_result["enabled_input_scanners"] >= 0
        assert standard_result["enabled_output_scanners"] >= 0
        assert standard_result["max_concurrent_scans"] > 0

        # Both configurations are now proven to be interchangeable
        assert True, "Custom and standard presets are interchangeable"


class TestPresetEdgeCases:
    """
    Test suite for edge cases and boundary conditions in preset module.
    
    Scope:
        Verifies that preset functions handle edge cases gracefully,
        including unusual but valid inputs and boundary conditions.
        
    Business Critical:
        Edge case handling prevents unexpected failures in production
        and ensures robust operation across all valid inputs.
        
    Test Strategy:
        - Test boundary threshold values (0.0, 1.0)
        - Test empty/minimal configurations
        - Test very large configurations
        - Test unusual but valid parameter combinations
    """

    def test_preset_with_threshold_at_minimum_boundary(self):
        """
        Test that presets with threshold exactly 0.0 are valid.

        Verifies:
            Scanner thresholds at the minimum valid boundary (0.0) are
            accepted and pass validation.

        Business Impact:
            Enables maximum security sensitivity for critical applications
            that need to catch all potential issues.

        Scenario:
            Given: A scanner configuration with threshold = 0.0
            When: create_preset() is called with this scanner
            And: validate_preset_config() is called on the result
            Then: No validation issues are returned
            And: The threshold value is preserved exactly as 0.0
            And: The configuration is usable in security systems

        Fixtures Used:
            - None (tests boundary value handling)
        """
        # Given: A scanner configuration with threshold = 0.0
        input_scanners = {
            "strict_prompt_injection": {
                "enabled": True,
                "threshold": 0.0,  # Minimum valid boundary
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30
            },
            "strict_toxicity": {
                "enabled": True,
                "threshold": 0.0,  # Minimum valid boundary
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 25
            }
        }

        output_scanners = {
            "strict_output_toxicity": {
                "enabled": True,
                "threshold": 0.0,  # Minimum valid boundary
                "action": "block",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }

        # When: create_preset() is called with this scanner
        custom_preset = create_preset(
            name="boundary-minimum-test",
            description="Test preset with minimum threshold boundaries",
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # And: validate_preset_config() is called on the result
        validation_issues = validate_preset_config(custom_preset)

        # Then: No validation issues are returned
        assert validation_issues == [], f"Preset with 0.0 thresholds should be valid: {validation_issues}"

        # And: The threshold value is preserved exactly as 0.0
        retrieved_input_scanners = custom_preset.get("input_scanners", {})
        for scanner_name, scanner_config in retrieved_input_scanners.items():
            threshold = scanner_config.get("threshold")
            assert threshold == 0.0, f"Scanner {scanner_name} should preserve 0.0 threshold, got {threshold}"

        retrieved_output_scanners = custom_preset.get("output_scanners", {})
        for scanner_name, scanner_config in retrieved_output_scanners.items():
            threshold = scanner_config.get("threshold")
            assert threshold == 0.0, f"Output scanner {scanner_name} should preserve 0.0 threshold, got {threshold}"

        # And: The configuration is usable in security systems
        # Test that the configuration can be processed normally
        assert "performance" in custom_preset, "Should have performance configuration"
        assert "logging" in custom_preset, "Should have logging configuration"
        assert "service" in custom_preset, "Should have service configuration"

        # Verify all scanners are enabled and properly configured
        for scanner_name, scanner_config in retrieved_input_scanners.items():
            assert scanner_config.get("enabled") is True, f"Scanner {scanner_name} should be enabled"
            assert scanner_config.get("action") == "block", f"Scanner {scanner_name} should have block action"
            assert "scan_timeout" in scanner_config, f"Scanner {scanner_name} should have timeout"

    def test_preset_with_threshold_at_maximum_boundary(self):
        """
        Test that presets with threshold exactly 1.0 are valid.

        Verifies:
            Scanner thresholds at the maximum valid boundary (1.0) are
            accepted and pass validation.

        Business Impact:
            Enables minimal security for special cases where very lenient
            validation is required (debugging, testing).

        Scenario:
            Given: A scanner configuration with threshold = 1.0
            When: create_preset() is called with this scanner
            And: validate_preset_config() is called on the result
            Then: No validation issues are returned
            And: The threshold value is preserved exactly as 1.0
            And: The configuration is usable in security systems

        Fixtures Used:
            - None (tests boundary value handling)
        """
        # Given: A scanner configuration with threshold = 1.0
        input_scanners = {
            "lenient_prompt_injection": {
                "enabled": True,
                "threshold": 1.0,  # Maximum valid boundary
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 30
            },
            "lenient_toxicity": {
                "enabled": True,
                "threshold": 1.0,  # Maximum valid boundary
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 25
            }
        }

        output_scanners = {
            "lenient_output_toxicity": {
                "enabled": True,
                "threshold": 1.0,  # Maximum valid boundary
                "action": "warn",
                "use_onnx": False,
                "scan_timeout": 30
            }
        }

        # When: create_preset() is called with this scanner
        custom_preset = create_preset(
            name="boundary-maximum-test",
            description="Test preset with maximum threshold boundaries",
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        # And: validate_preset_config() is called on the result
        validation_issues = validate_preset_config(custom_preset)

        # Then: No validation issues are returned
        assert validation_issues == [], f"Preset with 1.0 thresholds should be valid: {validation_issues}"

        # And: The threshold value is preserved exactly as 1.0
        retrieved_input_scanners = custom_preset.get("input_scanners", {})
        for scanner_name, scanner_config in retrieved_input_scanners.items():
            threshold = scanner_config.get("threshold")
            assert threshold == 1.0, f"Scanner {scanner_name} should preserve 1.0 threshold, got {threshold}"

        retrieved_output_scanners = custom_preset.get("output_scanners", {})
        for scanner_name, scanner_config in retrieved_output_scanners.items():
            threshold = scanner_config.get("threshold")
            assert threshold == 1.0, f"Output scanner {scanner_name} should preserve 1.0 threshold, got {threshold}"

        # And: The configuration is usable in security systems
        # Test that the configuration can be processed normally
        assert "performance" in custom_preset, "Should have performance configuration"
        assert "logging" in custom_preset, "Should have logging configuration"
        assert "service" in custom_preset, "Should have service configuration"

        # Verify all scanners are enabled and properly configured with lenient settings
        for scanner_name, scanner_config in retrieved_input_scanners.items():
            assert scanner_config.get("enabled") is True, f"Scanner {scanner_name} should be enabled"
            assert scanner_config.get("action") == "warn", f"Scanner {scanner_name} should have warn action for lenient settings"
            assert "scan_timeout" in scanner_config, f"Scanner {scanner_name} should have timeout"

    def test_preset_with_single_input_scanner(self):
        """
        Test that presets with only one input scanner are valid.

        Verifies:
            Minimal scanner configuration with just one input scanner
            is valid and passes all checks.

        Business Impact:
            Supports specialized use cases that only need specific
            security validation (e.g., prompt injection only).

        Scenario:
            Given: A configuration with exactly one input scanner
            And: Empty output scanners
            When: create_preset() and validate_preset_config() are called
            Then: No validation issues are returned
            And: The configuration is complete and usable

        Fixtures Used:
            - None (tests minimal valid configuration)
        """
        # Given: A configuration with exactly one input scanner
        input_scanners = {
            "single_prompt_injection": {
                "enabled": True,
                "threshold": 0.7,
                "action": "warn",
                "use_onnx": True,
                "scan_timeout": 30
            }
        }

        # And: Empty output scanners
        output_scanners = {}

        # When: create_preset() and validate_preset_config() are called
        minimal_preset = create_preset(
            name="single-scanner-test",
            description="Test preset with single input scanner",
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )

        validation_issues = validate_preset_config(minimal_preset)

        # Then: No validation issues are returned
        assert validation_issues == [], f"Single scanner preset should be valid: {validation_issues}"

        # And: The configuration is complete and usable
        assert isinstance(minimal_preset, dict), "Preset should be a dictionary"

        # Verify structure is complete
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service"]
        for section in required_sections:
            assert section in minimal_preset, f"Should have required section: {section}"

        # Verify scanner counts
        assert len(minimal_preset["input_scanners"]) == 1, "Should have exactly 1 input scanner"
        assert len(minimal_preset["output_scanners"]) == 0, "Should have no output scanners"

        # Verify the single scanner is properly configured
        scanner_config = list(minimal_preset["input_scanners"].values())[0]
        assert scanner_config["enabled"] is True, "Scanner should be enabled"
        assert 0.0 <= scanner_config["threshold"] <= 1.0, "Scanner should have valid threshold"
        assert scanner_config["action"] in ["warn", "flag", "block", "redact"], "Scanner should have valid action"

    def test_preset_with_many_scanners(self):
        """
        Test that presets with comprehensive scanner coverage work correctly.

        Verifies:
            Configurations with many input and output scanners (10+ total)
            are handled efficiently and pass validation.

        Business Impact:
            Supports enterprise use cases requiring comprehensive security
            coverage across multiple threat categories.

        Scenario:
            Given: A configuration with 10+ input and output scanners
            When: create_preset() and validate_preset_config() are called
            Then: No validation issues are returned
            And: All scanners are preserved in the configuration
            And: Performance is acceptable (< 1 second for validation)

        Fixtures Used:
            - None (tests large configuration handling)
        """
        # Given: A configuration with 10+ input and output scanners
        input_scanners = {
            "prompt_injection": {"enabled": True, "threshold": 0.7, "action": "block", "scan_timeout": 30},
            "toxicity_input": {"enabled": True, "threshold": 0.6, "action": "block", "scan_timeout": 25},
            "pii_detection": {"enabled": True, "threshold": 0.5, "action": "redact", "scan_timeout": 40},
            "malicious_url": {"enabled": True, "threshold": 0.8, "action": "block", "scan_timeout": 20},
            "hate_speech": {"enabled": True, "threshold": 0.4, "action": "block", "scan_timeout": 35},
            "violence": {"enabled": True, "threshold": 0.3, "action": "block", "scan_timeout": 30},
            "self_harm": {"enabled": True, "threshold": 0.2, "action": "block", "scan_timeout": 40},
            "sexual_content": {"enabled": True, "threshold": 0.5, "action": "block", "scan_timeout": 25},
            "harassment": {"enabled": True, "threshold": 0.6, "action": "block", "scan_timeout": 30},
            "misinformation": {"enabled": True, "threshold": 0.7, "action": "flag", "scan_timeout": 45}
        }

        output_scanners = {
            "toxicity_output": {"enabled": True, "threshold": 0.6, "action": "block", "scan_timeout": 25},
            "bias_detection": {"enabled": True, "threshold": 0.5, "action": "flag", "scan_timeout": 30},
            "harmful_content": {"enabled": True, "threshold": 0.4, "action": "block", "scan_timeout": 35},
            "factuality": {"enabled": True, "threshold": 0.7, "action": "flag", "scan_timeout": 40},
            "repetition": {"enabled": True, "threshold": 0.8, "action": "warn", "scan_timeout": 20}
        }

        # When: create_preset() and validate_preset_config() are called
        start_time = time.time()
        comprehensive_preset = create_preset(
            name="comprehensive-coverage",
            description="Enterprise-grade preset with comprehensive coverage",
            input_scanners=input_scanners,
            output_scanners=output_scanners
        )
        creation_time = time.time() - start_time

        start_time = time.time()
        validation_issues = validate_preset_config(comprehensive_preset)
        validation_time = time.time() - start_time

        # Then: No validation issues are returned
        assert validation_issues == [], f"Comprehensive preset should be valid: {validation_issues}"

        # And: All scanners are preserved in the configuration
        assert len(comprehensive_preset["input_scanners"]) == 10, "Should preserve all 10 input scanners"
        assert len(comprehensive_preset["output_scanners"]) == 5, "Should preserve all 5 output scanners"

        # And: Performance is acceptable (< 1 second for validation)
        assert validation_time < 1.0, f"Validation should be fast, took {validation_time:.3f}s"
        assert creation_time < 1.0, f"Creation should be fast, took {creation_time:.3f}s"

        # Verify all scanners are properly configured
        for scanner_name, scanner_config in comprehensive_preset["input_scanners"].items():
            assert scanner_config["enabled"] is True, f"Input scanner {scanner_name} should be enabled"
            assert 0.0 <= scanner_config["threshold"] <= 1.0, f"Input scanner {scanner_name} should have valid threshold"

        for scanner_name, scanner_config in comprehensive_preset["output_scanners"].items():
            assert scanner_config["enabled"] is True, f"Output scanner {scanner_name} should be enabled"
            assert 0.0 <= scanner_config["threshold"] <= 1.0, f"Output scanner {scanner_name} should have valid threshold"

    def test_preset_with_many_scanners(self):
        """
        Test that presets with comprehensive scanner coverage work correctly.
        
        Verifies:
            Configurations with many input and output scanners (10+ total)
            are handled efficiently and pass validation.
            
        Business Impact:
            Supports enterprise use cases requiring comprehensive security
            coverage across multiple threat categories.
            
        Scenario:
            Given: A configuration with 10+ input and output scanners
            When: create_preset() and validate_preset_config() are called
            Then: No validation issues are returned
            And: All scanners are preserved in the configuration
            And: Performance is acceptable (< 1 second for validation)
            
        Fixtures Used:
            - None (tests large configuration handling)
        """
        pass

    def test_preset_with_very_short_cache_ttl(self):
        """
        Test that presets with minimum cache TTL (1 second) are valid.

        Verifies:
            Performance configuration with very short cache TTL is accepted
            for test isolation and rapid configuration changes.

        Business Impact:
            Supports testing scenarios and rapid development cycles where
            cache persistence needs to be minimal.

        Scenario:
            Given: A performance override with cache_ttl_seconds = 1
            When: create_preset() is called with this override
            And: validate_preset_config() is called on the result
            Then: No validation issues are returned
            And: The TTL value is preserved as 1 second

        Fixtures Used:
            - None (tests minimum valid TTL)
        """
        # Given: A performance override with cache_ttl_seconds = 1
        performance_overrides = {
            "cache_ttl_seconds": 1,  # Very short TTL for test isolation
            "max_concurrent_scans": 2,
            "memory_limit_mb": 512
        }

        input_scanners = {
            "test_prompt_injection": {
                "enabled": True,
                "threshold": 0.8,
                "action": "warn",
                "scan_timeout": 10
            }
        }

        # When: create_preset() is called with this override
        short_ttl_preset = create_preset(
            name="short-cache-ttl",
            description="Preset with minimal cache TTL for testing",
            input_scanners=input_scanners,
            output_scanners={},
            performance_overrides=performance_overrides
        )

        # And: validate_preset_config() is called on the result
        validation_issues = validate_preset_config(short_ttl_preset)

        # Then: No validation issues are returned
        assert validation_issues == [], f"Short TTL preset should be valid: {validation_issues}"

        # And: The TTL value is preserved as 1 second
        performance_config = short_ttl_preset.get("performance", {})
        assert performance_config.get("cache_ttl_seconds") == 1, \
            f"Cache TTL should be 1 second, got {performance_config.get('cache_ttl_seconds')}"

        # Verify other performance settings are also preserved
        assert performance_config.get("max_concurrent_scans") == 2, "Should preserve max_concurrent_scans"
        assert performance_config.get("memory_limit_mb") == 512, "Should preserve memory_limit_mb"

    def test_preset_with_very_long_cache_ttl(self):
        """
        Test that presets with extended cache TTL (hours) are valid.

        Verifies:
            Performance configuration with very long cache TTL (e.g., 24 hours)
            is accepted for production optimization scenarios.

        Business Impact:
            Supports production optimization where long cache persistence
            reduces computational costs and improves throughput.

        Scenario:
            Given: A performance override with cache_ttl_seconds = 86400 (24h)
            When: create_preset() is called with this override
            And: validate_preset_config() is called on the result
            Then: No validation issues are returned
            And: The TTL value is preserved as specified

        Fixtures Used:
            - None (tests extended TTL handling)
        """
        # Given: A performance override with cache_ttl_seconds = 86400 (24h)
        performance_overrides = {
            "cache_ttl_seconds": 86400,  # 24 hours for production optimization
            "max_concurrent_scans": 50,
            "memory_limit_mb": 8192
        }

        input_scanners = {
            "production_prompt_injection": {
                "enabled": True,
                "threshold": 0.6,
                "action": "block",
                "scan_timeout": 30
            }
        }

        # When: create_preset() is called with this override
        long_ttl_preset = create_preset(
            name="long-cache-ttl",
            description="Preset with extended cache TTL for production",
            input_scanners=input_scanners,
            output_scanners={},
            performance_overrides=performance_overrides
        )

        # And: validate_preset_config() is called on the result
        validation_issues = validate_preset_config(long_ttl_preset)

        # Then: No validation issues are returned
        assert validation_issues == [], f"Long TTL preset should be valid: {validation_issues}"

        # And: The TTL value is preserved as specified
        performance_config = long_ttl_preset.get("performance", {})
        assert performance_config.get("cache_ttl_seconds") == 86400, \
            f"Cache TTL should be 86400 seconds, got {performance_config.get('cache_ttl_seconds')}"

        # Verify other performance settings are also preserved
        assert performance_config.get("max_concurrent_scans") == 50, "Should preserve max_concurrent_scans"
        assert performance_config.get("memory_limit_mb") == 8192, "Should preserve memory_limit_mb"

    def test_preset_with_case_sensitive_names(self):
        """
        Test that preset names are case-sensitive as documented.

        Verifies:
            get_preset_config() treats preset names as case-sensitive,
            rejecting variations in case.

        Business Impact:
            Clear case sensitivity behavior prevents confusion and ensures
            consistent configuration selection.

        Scenario:
            Given: Valid preset name "development"
            When: get_preset_config("Development") is called (wrong case)
            Then: ValueError is raised
            And: Error message indicates unknown preset

            Given: Valid preset name "development"
            When: get_preset_config("development") is called (correct case)
            Then: Configuration is returned successfully

        Fixtures Used:
            - None (tests case sensitivity behavior)
        """
        # Given: Valid preset name "development"
        # When: get_preset_config("Development") is called (wrong case)
        with pytest.raises(ValueError) as exc_info:
            get_preset_config("Development")

        # Then: ValueError is raised
        assert exc_info.type == ValueError, "Should raise ValueError for wrong case"

        # And: Error message indicates unknown preset
        error_message = str(exc_info.value)
        assert "Unknown preset" in error_message, "Error message should mention unknown preset"
        assert "development" in error_message.lower(), "Error should list available presets"

        # Given: Valid preset name "development"
        # When: get_preset_config("development") is called (correct case)
        config = get_preset_config("development")

        # Then: Configuration is returned successfully
        assert isinstance(config, dict), "Should return configuration dictionary"
        assert config.get("preset") == "development", "Should return development preset"

        # Test other case variations
        invalid_cases = ["DEVELOPMENT", "Production", "TESTING", "testing"]
        for invalid_case in invalid_cases:
            with pytest.raises(ValueError):
                get_preset_config(invalid_case)

    def test_preset_names_with_hyphens_in_custom_presets(self):
        """
        Test that custom preset names can contain hyphens.

        Verifies:
            create_preset() accepts preset names with hyphens for
            readable multi-word names (e.g., "content-moderation").

        Business Impact:
            Enables clear, descriptive naming for custom presets using
            common naming conventions (kebab-case).

        Scenario:
            Given: A custom preset name "content-moderation-strict"
            When: create_preset() is called with this name
            Then: The preset is created successfully
            And: The preset field contains the exact name with hyphens
            And: validate_preset_config() accepts the configuration

        Fixtures Used:
            - None (tests naming flexibility)
        """
        # Given: A custom preset name "content-moderation-strict"
        preset_name = "content-moderation-strict"

        input_scanners = {
            "content_prompt_injection": {
                "enabled": True,
                "threshold": 0.3,
                "action": "block",
                "scan_timeout": 25
            }
        }

        # When: create_preset() is called with this name
        custom_preset = create_preset(
            name=preset_name,
            description="Strict content moderation preset with hyphens in name",
            input_scanners=input_scanners,
            output_scanners={}
        )

        # Then: The preset is created successfully
        assert isinstance(custom_preset, dict), "Preset should be created successfully"

        # And: The preset field contains the exact name with hyphens
        assert custom_preset.get("preset") == preset_name, \
            f"Preset field should preserve hyphens: {preset_name}"

        # And: validate_preset_config() accepts the configuration
        validation_issues = validate_preset_config(custom_preset)
        assert validation_issues == [], f"Hyphenated preset name should be valid: {validation_issues}"

        # Test various hyphenated patterns
        hyphenated_names = [
            "api-endpoint-security",
            "high-performance-mode",
            "enterprise-grade-protection",
            "test-only-minimal",
            "multi-region-deployment"
        ]

        for test_name in hyphenated_names:
            test_preset = create_preset(
                name=test_name,
                description=f"Test preset for {test_name}",
                input_scanners={"test": {"enabled": True, "threshold": 0.5, "action": "warn"}},
                output_scanners={}
            )
            assert test_preset.get("preset") == test_name, f"Should preserve name: {test_name}"
            assert validate_preset_config(test_preset) == [], f"Should validate: {test_name}"

    def test_preset_with_very_long_cache_ttl(self):
        """
        Test that presets with extended cache TTL (hours) are valid.
        
        Verifies:
            Performance configuration with very long cache TTL (e.g., 24 hours)
            is accepted for production optimization scenarios.
            
        Business Impact:
            Supports production optimization where long cache persistence
            reduces computational costs and improves throughput.
            
        Scenario:
            Given: A performance override with cache_ttl_seconds = 86400 (24h)
            When: create_preset() is called with this override
            And: validate_preset_config() is called on the result
            Then: No validation issues are returned
            And: The TTL value is preserved as specified
            
        Fixtures Used:
            - None (tests extended TTL handling)
        """
        pass

    def test_preset_with_case_sensitive_names(self):
        """
        Test that preset names are case-sensitive as documented.
        
        Verifies:
            get_preset_config() treats preset names as case-sensitive,
            rejecting variations in case.
            
        Business Impact:
            Clear case sensitivity behavior prevents confusion and ensures
            consistent configuration selection.
            
        Scenario:
            Given: Valid preset name "development"
            When: get_preset_config("Development") is called (wrong case)
            Then: ValueError is raised
            And: Error message indicates unknown preset
            
            Given: Valid preset name "development"
            When: get_preset_config("development") is called (correct case)
            Then: Configuration is returned successfully
            
        Fixtures Used:
            - None (tests case sensitivity behavior)
        """
        pass

    def test_preset_names_with_hyphens_in_custom_presets(self):
        """
        Test that custom preset names can contain hyphens.
        
        Verifies:
            create_preset() accepts preset names with hyphens for
            readable multi-word names (e.g., "content-moderation").
            
        Business Impact:
            Enables clear, descriptive naming for custom presets using
            common naming conventions (kebab-case).
            
        Scenario:
            Given: A custom preset name "content-moderation-strict"
            When: create_preset() is called with this name
            Then: The preset is created successfully
            And: The preset field contains the exact name with hyphens
            And: validate_preset_config() accepts the configuration
            
        Fixtures Used:
            - None (tests naming flexibility)
        """
        pass


class TestPresetThreadSafety:
    """
    Test suite for thread safety of preset module functions.
    
    Scope:
        Verifies that preset functions can be safely called concurrently
        from multiple threads without data corruption or race conditions.
        
    Business Critical:
        Thread safety is essential for web applications where multiple
        requests access preset configurations concurrently.
        
    Test Strategy:
        - Test concurrent calls to get_preset_config()
        - Test concurrent preset validation
        - Verify no shared mutable state between calls
    """

    def test_concurrent_get_preset_config_calls_are_safe(self):
        """
        Test that get_preset_config can be called concurrently safely.

        Verifies:
            Multiple threads can call get_preset_config() simultaneously
            without data corruption or race conditions.

        Business Impact:
            Ensures web applications can safely retrieve preset configurations
            from multiple concurrent requests without synchronization issues.

        Scenario:
            Given: 10 threads making concurrent get_preset_config() calls
            When: All threads request different presets simultaneously
            Then: All calls complete successfully without errors
            And: Each thread receives the correct configuration for its request
            And: No configuration data is corrupted or mixed between threads

        Fixtures Used:
            - None (tests thread safety with concurrent operations)
        """
        # Given: 10 threads making concurrent get_preset_config() calls
        num_threads = 10
        preset_names = ["development", "production", "testing"]
        results = {}
        errors = []
        exception_event = threading.Event()

        def worker_thread(thread_id, preset_name):
            """Worker function that calls get_preset_config concurrently."""
            try:
                # When: All threads request different presets simultaneously
                config = get_preset_config(preset_name)
                results[thread_id] = {
                    "preset_name": preset_name,
                    "config": config,
                    "thread_id": thread_id
                }
            except Exception as e:
                errors.append(f"Thread {thread_id} failed: {e}")
                exception_event.set()

        # Create and start threads
        threads = []
        for i in range(num_threads):
            preset_name = preset_names[i % len(preset_names)]
            thread = threading.Thread(target=worker_thread, args=(i, preset_name))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout

        # Then: All calls complete successfully without errors
        assert not exception_event.is_set(), f"Exception occurred: {errors}"
        assert len(errors) == 0, f"No errors should occur: {errors}"
        assert len(results) == num_threads, f"All {num_threads} threads should complete"

        # And: Each thread receives the correct configuration for its request
        for thread_id, result in results.items():
            config = result["config"]
            expected_preset = result["preset_name"]
            assert isinstance(config, dict), f"Thread {thread_id} should get dict config"
            assert config.get("preset") == expected_preset, \
                f"Thread {thread_id} should get {expected_preset} config, got {config.get('preset')}"

        # And: No configuration data is corrupted or mixed between threads
        # Verify configs are independent and valid
        for result in results.values():
            config = result["config"]
            assert "input_scanners" in config, "Config should have input_scanners"
            assert "output_scanners" in config, "Config should have output_scanners"
            assert "performance" in config, "Config should have performance"
            assert "logging" in config, "Config should have logging"
            assert "service" in config, "Config should have service"

    def test_concurrent_validation_calls_are_safe(self):
        """
        Test that validate_preset_config can be called concurrently safely.

        Verifies:
            Multiple threads can call validate_preset_config() simultaneously
            on different configurations without interference.

        Business Impact:
            Ensures validation can occur in parallel during system initialization
            or configuration updates without synchronization overhead.

        Scenario:
            Given: 10 threads making concurrent validate_preset_config() calls
            When: Each thread validates a different configuration
            Then: All validations complete successfully
            And: Each thread receives correct validation results
            And: No validation state is shared between threads

        Fixtures Used:
            - None (tests thread safety with concurrent validation)
        """
        # Given: 10 threads making concurrent validate_preset_config() calls
        num_threads = 10
        validation_results = {}
        errors = []
        exception_event = threading.Event()

        def create_test_config(preset_id):
            """Create a unique test configuration for each thread."""
            return {
                "preset": f"test-{preset_id}",
                "input_scanners": {
                    f"scanner_{preset_id}": {
                        "enabled": True,
                        "threshold": 0.5 + (preset_id * 0.01),  # Unique threshold
                        "action": "warn",
                        "scan_timeout": 30
                    }
                },
                "output_scanners": {},
                "performance": {
                    "max_concurrent_scans": 5,
                    "cache_ttl_seconds": 300
                },
                "logging": {
                    "enabled": True,
                    "level": "INFO"
                },
                "service": {
                    "environment": f"test-{preset_id}"
                }
            }

        def validation_worker_thread(thread_id):
            """Worker function that validates configurations concurrently."""
            try:
                # When: Each thread validates a different configuration
                config = create_test_config(thread_id)
                issues = validate_preset_config(config)

                validation_results[thread_id] = {
                    "config_preset": config["preset"],
                    "issues": issues,
                    "threshold": config["input_scanners"][f"scanner_{thread_id}"]["threshold"]
                }
            except Exception as e:
                errors.append(f"Validation thread {thread_id} failed: {e}")
                exception_event.set()

        # Create and start validation threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=validation_worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout

        # Then: All validations complete successfully
        assert not exception_event.is_set(), f"Validation exception occurred: {errors}"
        assert len(errors) == 0, f"No validation errors should occur: {errors}"
        assert len(validation_results) == num_threads, f"All {num_threads} validations should complete"

        # And: Each thread receives correct validation results
        for thread_id, result in validation_results.items():
            # All test configs should be valid (no issues)
            assert result["issues"] == [], f"Thread {thread_id} should have no validation issues"
            # Each should have its unique threshold preserved
            expected_threshold = 0.5 + (thread_id * 0.01)
            assert result["threshold"] == expected_threshold, \
                f"Thread {thread_id} threshold should be preserved"

        # And: No validation state is shared between threads
        # Verify all results are unique and independent
        preset_names = set(result["config_preset"] for result in validation_results.values())
        thresholds = set(result["threshold"] for result in validation_results.values())
        assert len(preset_names) == num_threads, "All preset names should be unique"
        assert len(thresholds) == num_threads, "All thresholds should be unique"

    def test_preset_configurations_are_independent_across_calls(self):
        """
        Test that modifications to returned configurations don't affect other calls.

        Verifies:
            Configuration dictionaries returned by get_preset_config() and
            create_preset() are independent, preventing unintended sharing.

        Business Impact:
            Prevents accidental configuration mutations from affecting other
            parts of the system, maintaining data integrity.

        Scenario:
            Given: Two calls to get_preset_config("development")
            When: The first returned configuration is modified
            Then: The second returned configuration remains unchanged
            And: Subsequent calls return original unmodified configuration
            And: No shared mutable state exists between configurations

        Fixtures Used:
            - None (tests configuration independence)
        """
        # Given: Two calls to get_preset_config("development")
        config1 = get_preset_config("development")
        config2 = get_preset_config("development")

        # Verify both configs are initially identical
        assert config1["preset"] == config2["preset"] == "development"
        original_max_scans = config1["performance"]["max_concurrent_scans"]
        original_log_level = config1["logging"]["level"]

        # When: The first returned configuration is modified
        config1["performance"]["max_concurrent_scans"] = 999
        config1["logging"]["level"] = "CUSTOM_LEVEL"
        config1["service"]["environment"] = "MODIFIED"

        # Then: The second returned configuration remains unchanged
        assert config2["performance"]["max_concurrent_scans"] == original_max_scans, \
            "Second config should not be affected by first config modification"
        assert config2["logging"]["level"] == original_log_level, \
            "Second config should not be affected by first config modification"
        assert config2["service"]["environment"] == "development", \
            "Second config should not be affected by first config modification"

        # And: Subsequent calls return original unmodified configuration
        config3 = get_preset_config("development")
        assert config3["performance"]["max_concurrent_scans"] == original_max_scans, \
            "New calls should return original unmodified configuration"
        assert config3["logging"]["level"] == original_log_level, \
            "New calls should return original unmodified configuration"
        assert config3["service"]["environment"] == "development", \
            "New calls should return original unmodified configuration"

        # And: No shared mutable state exists between configurations
        # Verify deep independence by modifying nested structures
        config4 = get_preset_config("development")
        config4["input_scanners"]["prompt_injection"]["threshold"] = 0.99

        config5 = get_preset_config("development")
        original_prompt_threshold = config5["input_scanners"]["prompt_injection"]["threshold"]
        assert original_prompt_threshold != 0.99, \
            "New config should not be affected by previous modifications"


class TestPresetDocumentationConsistency:
    """
    Test suite verifying preset behaviors match documented contracts.
    
    Scope:
        Verifies that actual preset behaviors match the guarantees and
        examples documented in the module's docstring contract.
        
    Business Critical:
        Contract consistency ensures users can rely on documented behavior
        and prevents surprises during deployment.
        
    Test Strategy:
        - Test documented configuration structures
        - Verify documented guarantee behaviors
        - Test contract examples work as documented
    """

    def test_preset_configuration_structure_matches_documentation(self):
        """
        Test that preset configuration structure matches documented format.

        Verifies:
            All preset configurations follow the structure documented in
            the module docstring with all required sections.

        Business Impact:
            Ensures documentation accuracy and prevents integration issues
            when users rely on documented structure.

        Scenario:
            Given: The documented configuration structure from module docstring
            When: get_preset_config() is called for each standard preset
            Then: Each configuration matches the documented structure:
                - preset: str (preset identifier)
                - input_scanners: Dict[str, Any]
                - output_scanners: Dict[str, Any]
                - performance: Dict[str, Any]
                - logging: Dict[str, Any]
                - service: Dict[str, Any]
                - features: Dict[str, Any]

        Fixtures Used:
            - None (tests documentation accuracy)
        """
        # Given: The documented configuration structure from module docstring
        # Expected structure based on documentation
        required_sections = {
            "preset": str,
            "input_scanners": dict,
            "output_scanners": dict,
            "performance": dict,
            "logging": dict,
            "service": dict,
            "features": dict
        }

        # When: get_preset_config() is called for each standard preset
        available_presets = list_presets()

        for preset_name in available_presets:
            config = get_preset_config(preset_name)

            # Then: Each configuration matches the documented structure
            assert isinstance(config, dict), f"Config for {preset_name} should be a dictionary"

            # Check all required sections exist and have correct types
            for section_name, expected_type in required_sections.items():
                assert section_name in config, f"Config for {preset_name} missing required section: {section_name}"
                assert isinstance(config[section_name], expected_type), \
                    f"Config section {section_name} for {preset_name} should be {expected_type.__name__}"

            # Verify preset field matches requested preset
            assert config["preset"] == preset_name, f"Preset field should match requested name {preset_name}"

            # Verify scanner configurations have expected structure
            input_scanners = config["input_scanners"]
            for scanner_name, scanner_config in input_scanners.items():
                assert isinstance(scanner_config, dict), f"Scanner config for {scanner_name} should be dict"
                assert "enabled" in scanner_config, f"Scanner {scanner_name} should have 'enabled' field"
                assert "threshold" in scanner_config, f"Scanner {scanner_name} should have 'threshold' field"
                assert 0.0 <= scanner_config["threshold"] <= 1.0, f"Scanner {scanner_name} threshold should be valid"

    def test_docstring_usage_examples_work_correctly(self):
        """
        Test that code examples from docstrings execute successfully.

        Verifies:
            All code examples in function docstrings are executable and
            produce the documented results.

        Business Impact:
            Ensures documentation examples are reliable and help users
            understand how to use the preset system correctly.

        Scenario:
            Given: Usage examples from get_preset_config() docstring
            When: The example code is executed
            Then: No exceptions are raised
            And: Results match documented output
            And: Example demonstrates intended functionality

        Fixtures Used:
            - None (tests example code accuracy)
        """
        # Test examples from get_preset_config() docstring

        # Example: Get production configuration for deployment
        prod_config = get_preset_config("production")
        assert prod_config["preset"] == "production"
        assert prod_config["service"]["environment"] == "production"

        # Example: Access specific scanner settings
        config = get_preset_config("development")
        prompt_scanner = config["input_scanners"]["prompt_injection"]
        assert prompt_scanner["enabled"] is True
        assert 0.0 <= prompt_scanner["threshold"] <= 1.0

        # Example: Verify performance configuration
        prod_config = get_preset_config("production")
        perf = prod_config["performance"]
        assert perf.get("cache_enabled") is True
        # Note: max_concurrent_scans field name may vary, so check for reasonable value
        concurrent_scans = perf.get("max_concurrent_scans", perf.get("max_concurrent_scans", 1))
        assert isinstance(concurrent_scans, int) and concurrent_scans > 0

        # Test list_presets() examples
        presets = list_presets()
        assert isinstance(presets, list)
        assert all(isinstance(name, str) for name in presets)
        assert len(presets) >= 3  # Should have at least the standard presets

        # Test preset description examples
        for preset in list_presets():
            desc = get_preset_description(preset)
            assert desc != "Unknown preset"
            assert len(desc) > 10  # Should be meaningful description

    def test_documented_preset_characteristics_are_accurate(self):
        """
        Test that documented preset characteristics match actual behavior.

        Verifies:
            Preset descriptions in module docstring accurately reflect
            actual preset configurations and behaviors.

        Business Impact:
            Accurate documentation prevents misconfiguration and ensures
            users select appropriate presets for their needs.

        Scenario:
            Given: Module docstring describes development preset as "lenient"
            When: Development preset configuration is examined
            Then: Thresholds are actually lenient (>= 0.8)

            Given: Module docstring describes production as "strict"
            When: Production preset configuration is examined
            Then: Thresholds are actually strict (<= 0.7)

            Given: Module docstring describes testing as "minimal"
            When: Testing preset configuration is examined
            Then: Scanner count is actually minimal (1 input scanner)

        Fixtures Used:
            - None (tests documentation-code consistency)
        """
        # Given: Module docstring describes development preset as "lenient"
        dev_config = get_preset_config("development")
        # When: Development preset configuration is examined
        dev_scanners = dev_config["input_scanners"]
        lenient_thresholds = [scanner["threshold"] for scanner in dev_scanners.values()]
        # Then: Thresholds are actually lenient (>= 0.8)
        assert all(threshold >= 0.8 for threshold in lenient_thresholds), \
            f"Development preset should have lenient thresholds >= 0.8, got {lenient_thresholds}"

        # Given: Module docstring describes production as "strict"
        prod_config = get_preset_config("production")
        # When: Production preset configuration is examined
        prod_scanners = prod_config["input_scanners"]
        strict_thresholds = [scanner["threshold"] for scanner in prod_scanners.values()]
        # Then: Thresholds are actually strict (<= 0.7)
        assert any(threshold <= 0.7 for threshold in strict_thresholds), \
            f"Production preset should have strict thresholds <= 0.7, got {strict_thresholds}"

        # Given: Module docstring describes testing as "minimal"
        test_config = get_preset_config("testing")
        # When: Testing preset configuration is examined
        # Then: Scanner count is actually minimal (1 input scanner)
        assert len(test_config["input_scanners"]) == 1, \
            f"Testing preset should have exactly 1 input scanner, got {len(test_config['input_scanners'])}"
        assert len(test_config["output_scanners"]) == 0, \
            f"Testing preset should have no output scanners, got {len(test_config['output_scanners'])}"

        # Verify testing preset has the single scanner as prompt injection
        assert "prompt_injection" in test_config["input_scanners"], \
            "Testing preset should have prompt injection scanner"

        # Verify descriptions match characteristics
        dev_desc = get_preset_description("development")
        assert any(keyword in dev_desc.lower() for keyword in ["lenient", "development"]), \
            "Development description should mention lenient settings"

        prod_desc = get_preset_description("production")
        assert any(keyword in prod_desc.lower() for keyword in ["strict", "security"]), \
            "Production description should mention strict settings or security"

        test_desc = get_preset_description("testing")
        assert any(keyword in test_desc.lower() for keyword in ["minimal", "fast", "testing"]), \
            "Testing description should mention minimal scanners or fast execution"

