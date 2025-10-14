"""
Unit tests for security preset retrieval functions.

This test module verifies the core preset retrieval functionality of the
app.infrastructure.security.llm.presets module, focusing on get_preset_config(),
list_presets(), and get_preset_description() functions.

Test Strategy:
    - Component Under Test: app.infrastructure.security.llm.presets (entire module)
    - Testing Approach: Black-box testing through public API only
    - No Mocking: Module has no external dependencies, pure function testing
    - Contract Source: backend/contracts/infrastructure/security/llm/presets.pyi

Fixtures Available:
    From conftest.py (backend/tests/unit/llm_security/presets/conftest.py):
    - preset_names: List of available preset names
    - preset_descriptions: Dictionary of preset descriptions
    - development_preset_data: Expected development preset structure
    - production_preset_data: Expected production preset structure
    - testing_preset_data: Expected testing preset structure
"""

import pytest
from typing import Dict, Any, List

from app.infrastructure.security.llm.presets import get_preset_config, list_presets, get_preset_description


class TestGetPresetConfig:
    """
    Test suite for get_preset_config() function.
    
    Scope:
        Verifies that get_preset_config() returns complete, valid configuration
        dictionaries for all supported presets per the documented contract.
        
    Business Critical:
        Preset configurations drive security scanner behavior. Incorrect
        configurations could result in security vulnerabilities or system failures.
        
    Test Strategy:
        - Test all valid preset names (development, production, testing)
        - Verify complete configuration structure for each preset
        - Test error handling for invalid preset names
        - Verify configuration immutability and consistency
    """

    def test_returns_development_preset_configuration(self, development_preset_data):
        """
        Test that get_preset_config returns complete development preset configuration.

        Verifies:
            get_preset_config("development") returns a complete configuration dictionary
            with all required sections and development-appropriate settings.

        Business Impact:
            Development preset enables rapid iteration with lenient security settings.
            Incorrect configuration would disrupt developer workflows.

        Scenario:
            Given: A request for the "development" preset
            When: get_preset_config("development") is called
            Then: A complete configuration dictionary is returned
            And: The preset field contains "development"
            And: All required sections are present (input_scanners, output_scanners,
                 performance, logging, service, features)
            And: Development-appropriate settings are configured (lenient thresholds,
                 debug logging, CPU-only execution)

        Fixtures Used:
            - development_preset_data: Expected development preset structure for validation
        """
        # When: get_preset_config("development") is called
        config = get_preset_config("development")

        # Then: A complete configuration dictionary is returned
        assert isinstance(config, dict)

        # And: The preset field contains "development"
        assert config["preset"] == "development"

        # And: All required sections are present
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"
            assert isinstance(config[section], dict), f"Section {section} should be a dictionary"

        # And: Development-appropriate settings are configured
        # Check debug mode is enabled
        assert config["service"]["debug_mode"] is True

        # Check CPU-only execution
        assert "CPUExecutionProvider" in config["performance"]["onnx_providers"]

        # Check lenient thresholds (should be >= 0.8)
        for scanner_name, scanner_config in config["input_scanners"].items():
            assert scanner_config["threshold"] >= 0.8, f"Scanner {scanner_name} should have lenient threshold"
            assert scanner_config["action"] in ["warn", "flag"], f"Scanner {scanner_name} should use non-blocking action"

        # Check debug logging
        assert config["logging"]["level"] == "DEBUG"
        assert config["logging"]["include_scanned_text"] is True

    def test_returns_production_preset_configuration(self, production_preset_data):
        """
        Test that get_preset_config returns complete production preset configuration.

        Verifies:
            get_preset_config("production") returns a complete configuration dictionary
            with strict security settings appropriate for production deployment.

        Business Impact:
            Production preset provides maximum security for live systems handling
            real user data. Configuration errors could expose security vulnerabilities.

        Scenario:
            Given: A request for the "production" preset
            When: get_preset_config("production") is called
            Then: A complete configuration dictionary is returned
            And: The preset field contains "production"
            And: All required sections are present
            And: Production-appropriate settings are configured (strict thresholds,
                 GPU acceleration, secure logging, authentication enabled)

        Fixtures Used:
            - production_preset_data: Expected production preset structure for validation
        """
        # When: get_preset_config("production") is called
        config = get_preset_config("production")

        # Then: A complete configuration dictionary is returned
        assert isinstance(config, dict)

        # And: The preset field contains "production"
        assert config["preset"] == "production"

        # And: All required sections are present
        required_sections = ["input_scanners", "output_scanners", "performance", "logging", "service", "features"]
        for section in required_sections:
            assert section in config, f"Missing required section: {section}"
            assert isinstance(config[section], dict), f"Section {section} should be a dictionary"

        # And: Production-appropriate settings are configured
        # Check strict security thresholds (most should be <= 0.7)
        for scanner_name, scanner_config in config["input_scanners"].items():
            threshold = scanner_config["threshold"]
            # Core security scanners should have strict thresholds
            if scanner_name in ["prompt_injection", "pii_detection"]:
                assert threshold <= 0.7, f"Core security scanner {scanner_name} should have strict threshold <= 0.7, got {threshold}"
            assert scanner_config["action"] in ["block", "redact"], f"Scanner {scanner_name} should use protective action, got {scanner_config['action']}"

        # Check GPU acceleration is available
        onnx_providers = config["performance"]["onnx_providers"]
        assert "CUDAExecutionProvider" in onnx_providers or "CPUExecutionProvider" in onnx_providers

        # Check secure logging
        assert config["logging"]["level"] == "INFO"
        assert config["logging"]["include_scanned_text"] is False  # Privacy protection
        assert config["logging"]["sanitize_pii_in_logs"] is True
        assert config["logging"]["log_format"] == "json"

        # Check authentication and rate limiting
        assert config["service"]["api_key_required"] is True
        assert config["service"]["rate_limit_enabled"] is True
        assert config["service"]["debug_mode"] is False

    def test_returns_testing_preset_configuration(self, testing_preset_data):
        """
        Test that get_preset_config returns complete testing preset configuration.

        Verifies:
            get_preset_config("testing") returns a minimal configuration optimized
            for fast test execution with minimal resource usage.

        Business Impact:
            Testing preset enables fast CI/CD pipelines. Configuration errors
            would slow down development velocity and increase costs.

        Scenario:
            Given: A request for the "testing" preset
            When: get_preset_config("testing") is called
            Then: A minimal configuration dictionary is returned
            And: The preset field contains "testing"
            And: Only essential scanners are enabled (prompt_injection only)
            And: Output scanners are empty for speed
            And: Performance settings are minimal (1 concurrent scan, short TTL)
            And: Logging is disabled for fast execution

        Fixtures Used:
            - testing_preset_data: Expected testing preset structure for validation
        """
        # When: get_preset_config("testing") is called
        config = get_preset_config("testing")

        # Then: A minimal configuration dictionary is returned
        assert isinstance(config, dict)

        # And: The preset field contains "testing"
        assert config["preset"] == "testing"

        # And: Only essential scanners are enabled (prompt_injection only)
        input_scanners = config["input_scanners"]
        assert len(input_scanners) == 1, "Testing preset should have only one input scanner"
        assert "prompt_injection" in input_scanners, "Testing preset should have prompt_injection scanner"
        assert input_scanners["prompt_injection"]["enabled"] is True

        # And: Output scanners are empty for speed
        output_scanners = config["output_scanners"]
        assert len(output_scanners) == 0, "Testing preset should have no output scanners"

        # And: Performance settings are minimal
        performance = config["performance"]
        assert performance["max_concurrent_scans"] == 1, "Testing preset should limit to 1 concurrent scan"
        assert performance["cache_ttl_seconds"] == 1, "Testing preset should have 1-second cache TTL"
        assert performance["memory_limit_mb"] <= 512, "Testing preset should use minimal memory"

        # And: Logging is disabled for fast execution
        logging = config["logging"]
        assert logging["enabled"] is False, "Testing preset should disable logging"
        assert logging["level"] == "ERROR", "Testing preset should use ERROR log level"

    def test_raises_value_error_for_unknown_preset(self):
        """
        Test that get_preset_config raises ValueError for unrecognized preset names.

        Verifies:
            get_preset_config() raises ValueError with helpful error message when
            called with a preset name that doesn't exist in the system.

        Business Impact:
            Clear error messages prevent misconfiguration and guide users toward
            valid preset names, reducing configuration errors in deployment.

        Scenario:
            Given: An invalid preset name "nonexistent_preset"
            When: get_preset_config("nonexistent_preset") is called
            Then: ValueError is raised
            And: The error message contains "Unknown preset"
            And: The error message lists valid preset names for user guidance

        Fixtures Used:
            - None (tests error handling with invalid input)
        """
        # Given: An invalid preset name "nonexistent_preset"
        invalid_preset_name = "nonexistent_preset"

        # When: get_preset_config("nonexistent_preset") is called
        # Then: ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            get_preset_config(invalid_preset_name)

        # And: The error message contains "Unknown preset"
        error_message = str(exc_info.value)
        assert "Unknown preset" in error_message

        # And: The error message lists valid preset names for user guidance
        for valid_preset in ["development", "production", "testing"]:
            assert valid_preset in error_message, f"Error message should mention valid preset: {valid_preset}"

    def test_preset_configuration_contains_all_required_sections(self, preset_names):
        """
        Test that all preset configurations contain required top-level sections.

        Verifies:
            Every preset configuration dictionary contains the complete set of
            required sections per the documented configuration structure.

        Business Impact:
            Missing configuration sections would cause system initialization failures
            and prevent security scanners from functioning properly.

        Scenario:
            Given: Each available preset name (development, production, testing)
            When: get_preset_config() is called for each preset
            Then: The returned configuration contains all required keys:
                - "preset" (preset identifier)
                - "input_scanners" (input validation configs)
                - "output_scanners" (output content configs)
                - "performance" (performance settings)
                - "logging" (logging configuration)
                - "service" (service identification)
                - "features" (feature flags)

        Fixtures Used:
            - preset_names: List of all available preset names to iterate
        """
        # Given: Each available preset name
        required_sections = ["preset", "input_scanners", "output_scanners", "performance", "logging", "service", "features"]

        for preset_name in preset_names:
            # When: get_preset_config() is called for each preset
            config = get_preset_config(preset_name)

            # Then: The returned configuration contains all required keys
            for section in required_sections:
                assert section in config, f"Preset {preset_name} missing required section: {section}"
                # The "preset" field is a string, all others should be dictionaries
                if section == "preset":
                    assert isinstance(config[section], str), f"Section {section} in preset {preset_name} should be a string"
                else:
                    assert isinstance(config[section], dict), f"Section {section} in preset {preset_name} should be a dictionary"

    def test_development_preset_has_lenient_thresholds(self):
        """
        Test that development preset uses lenient security thresholds per contract.

        Verifies:
            Development preset scanner thresholds are configured with high values
            (0.8-0.9) to reduce false positives during development.

        Business Impact:
            Lenient thresholds prevent security scanners from blocking legitimate
            development activities, maintaining developer productivity.

        Scenario:
            Given: The development preset configuration
            When: Scanner threshold values are examined
            Then: All thresholds are >= 0.8 (lenient)
            And: Scanner actions are "warn" or "flag" (non-blocking)
            And: CPU-only execution is configured for easy local setup

        Fixtures Used:
            - None (tests observable configuration values)
        """
        # Given: The development preset configuration
        config = get_preset_config("development")

        # When: Scanner threshold values are examined
        input_scanners = config["input_scanners"]

        # Then: All thresholds are >= 0.8 (lenient)
        for scanner_name, scanner_config in input_scanners.items():
            threshold = scanner_config["threshold"]
            assert threshold >= 0.8, f"Development scanner {scanner_name} should have lenient threshold >= 0.8, got {threshold}"

        # And: Scanner actions are "warn" or "flag" (non-blocking)
        for scanner_name, scanner_config in input_scanners.items():
            action = scanner_config["action"]
            assert action in ["warn", "flag"], f"Development scanner {scanner_name} should use non-blocking action, got {action}"

        # And: CPU-only execution is configured for easy local setup
        onnx_providers = config["performance"]["onnx_providers"]
        assert "CPUExecutionProvider" in onnx_providers, "Development preset should support CPU execution"

    def test_production_preset_has_strict_thresholds(self):
        """
        Test that production preset uses strict security thresholds per contract.

        Verifies:
            Production preset scanner thresholds are configured with low values
            (0.6-0.7) for maximum security protection.

        Business Impact:
            Strict thresholds provide comprehensive security coverage for production
            systems, preventing security incidents and data breaches.

        Scenario:
            Given: The production preset configuration
            When: Scanner threshold values are examined
            Then: All thresholds are <= 0.7 (strict)
            And: Scanner actions are "block" or "redact" (protective)
            And: GPU acceleration is enabled with CPU fallback
            And: Authentication and rate limiting are enabled

        Fixtures Used:
            - None (tests observable configuration values)
        """
        # Given: The production preset configuration
        config = get_preset_config("production")

        # When: Scanner threshold values are examined
        input_scanners = config["input_scanners"]

        # Then: Core security thresholds are <= 0.7 (strict)
        for scanner_name, scanner_config in input_scanners.items():
            threshold = scanner_config["threshold"]
            # Core security scanners should have strict thresholds
            if scanner_name in ["prompt_injection", "pii_detection"]:
                assert threshold <= 0.7, f"Core production scanner {scanner_name} should have strict threshold <= 0.7, got {threshold}"

        # And: Scanner actions are "block" or "redact" (protective)
        for scanner_name, scanner_config in input_scanners.items():
            action = scanner_config["action"]
            assert action in ["block", "redact"], f"Production scanner {scanner_name} should use protective action, got {action}"

        # And: GPU acceleration is enabled with CPU fallback
        onnx_providers = config["performance"]["onnx_providers"]
        assert "CUDAExecutionProvider" in onnx_providers or "CPUExecutionProvider" in onnx_providers, "Production preset should support GPU/CPU execution"

        # And: Authentication and rate limiting are enabled
        assert config["service"]["api_key_required"] is True, "Production preset should require API key"
        assert config["service"]["rate_limit_enabled"] is True, "Production preset should enable rate limiting"

    def test_testing_preset_has_minimal_scanners(self):
        """
        Test that testing preset enables only essential scanners per contract.

        Verifies:
            Testing preset configuration includes only prompt_injection scanner
            for input validation and no output scanners for maximum speed.

        Business Impact:
            Minimal scanner configuration enables fast test execution in CI/CD
            pipelines, reducing costs and improving developer feedback loops.

        Scenario:
            Given: The testing preset configuration
            When: Scanner configurations are examined
            Then: Only one input scanner is enabled (prompt_injection)
            And: Output scanners dictionary is empty
            And: Performance settings minimize resource usage (1 concurrent scan)
            And: Cache TTL is very short (1 second) for test isolation

        Fixtures Used:
            - None (tests observable configuration values)
        """
        # Given: The testing preset configuration
        config = get_preset_config("testing")

        # When: Scanner configurations are examined
        input_scanners = config["input_scanners"]
        output_scanners = config["output_scanners"]

        # Then: Only one input scanner is enabled (prompt_injection)
        assert len(input_scanners) == 1, f"Testing preset should have exactly 1 input scanner, got {len(input_scanners)}"
        assert "prompt_injection" in input_scanners, "Testing preset should have prompt_injection scanner"
        assert input_scanners["prompt_injection"]["enabled"] is True, "prompt_injection scanner should be enabled"

        # And: Output scanners dictionary is empty
        assert len(output_scanners) == 0, "Testing preset should have no output scanners"

        # And: Performance settings minimize resource usage
        performance = config["performance"]
        assert performance["max_concurrent_scans"] == 1, "Testing preset should limit to 1 concurrent scan"
        assert performance["cache_ttl_seconds"] == 1, "Testing preset should have 1-second cache TTL"
        assert performance["memory_limit_mb"] <= 512, "Testing preset should use minimal memory"

    def test_preset_configuration_is_consistent_across_calls(self):
        """
        Test that get_preset_config returns consistent configuration for same preset.

        Verifies:
            Multiple calls to get_preset_config() with the same preset name return
            identical configuration dictionaries for reliability and predictability.

        Business Impact:
            Configuration consistency ensures predictable system behavior and
            prevents configuration drift during runtime.

        Scenario:
            Given: A valid preset name "development"
            When: get_preset_config("development") is called multiple times
            Then: All returned configurations are identical
            And: Configuration values match across all calls
            And: No unexpected variation occurs between calls

        Fixtures Used:
            - None (tests consistency of function behavior)
        """
        # Given: A valid preset name "development"
        preset_name = "development"

        # When: get_preset_config("development") is called multiple times
        configs = []
        for i in range(3):
            config = get_preset_config(preset_name)
            configs.append(config)

        # Then: All returned configurations are identical
        for i in range(1, len(configs)):
            assert configs[0] == configs[i], f"Configuration {i} differs from first configuration"

        # And: Configuration values match across all calls
        first_config = configs[0]
        for config in configs[1:]:
            assert config["preset"] == first_config["preset"]
            assert config["input_scanners"] == first_config["input_scanners"]
            assert config["output_scanners"] == first_config["output_scanners"]
            assert config["performance"] == first_config["performance"]
            assert config["logging"] == first_config["logging"]
            assert config["service"] == first_config["service"]
            assert config["features"] == first_config["features"]

    def test_preset_input_scanners_are_properly_structured(self, preset_names):
        """
        Test that input scanner configurations follow the expected structure.

        Verifies:
            Each input scanner configuration contains required fields (enabled,
            threshold, action, scan_timeout) with appropriate data types.

        Business Impact:
            Proper scanner structure prevents initialization failures and ensures
            security scanners can be instantiated and configured correctly.

        Scenario:
            Given: A preset configuration from get_preset_config()
            When: Input scanner configurations are examined
            Then: Each scanner has an "enabled" boolean field
            And: Each scanner has a "threshold" float field (0.0-1.0)
            And: Each scanner has an "action" string field
            And: Each scanner has a "scan_timeout" integer field
            And: All values are within valid ranges

        Fixtures Used:
            - preset_names: List of preset names to test all configurations
        """
        # Given: Preset configurations from get_preset_config()
        for preset_name in preset_names:
            config = get_preset_config(preset_name)
            input_scanners = config["input_scanners"]

            # When: Input scanner configurations are examined
            for scanner_name, scanner_config in input_scanners.items():
                # Then: Each scanner has an "enabled" boolean field
                assert "enabled" in scanner_config, f"Scanner {scanner_name} in preset {preset_name} missing 'enabled' field"
                assert isinstance(scanner_config["enabled"], bool), f"Scanner {scanner_name} 'enabled' should be boolean"

                # And: Each scanner has a "threshold" float field (0.0-1.0)
                assert "threshold" in scanner_config, f"Scanner {scanner_name} in preset {preset_name} missing 'threshold' field"
                threshold = scanner_config["threshold"]
                assert isinstance(threshold, (int, float)), f"Scanner {scanner_name} 'threshold' should be numeric"
                assert 0.0 <= threshold <= 1.0, f"Scanner {scanner_name} threshold {threshold} should be between 0.0 and 1.0"

                # And: Each scanner has an "action" string field
                assert "action" in scanner_config, f"Scanner {scanner_name} in preset {preset_name} missing 'action' field"
                assert isinstance(scanner_config["action"], str), f"Scanner {scanner_name} 'action' should be string"
                assert scanner_config["action"] in ["warn", "flag", "block", "redact"], f"Scanner {scanner_name} action should be valid"

                # And: Each scanner has a "scan_timeout" integer field
                assert "scan_timeout" in scanner_config, f"Scanner {scanner_name} in preset {preset_name} missing 'scan_timeout' field"
                timeout = scanner_config["scan_timeout"]
                assert isinstance(timeout, int), f"Scanner {scanner_name} 'scan_timeout' should be integer"
                assert timeout > 0, f"Scanner {scanner_name} scan_timeout {timeout} should be positive"

    def test_preset_performance_settings_are_valid(self, preset_names):
        """
        Test that performance settings contain valid values and types.

        Verifies:
            Performance section contains required fields with appropriate data types
            and values within valid operational ranges.

        Business Impact:
            Valid performance settings prevent resource exhaustion and ensure
            efficient system operation under load.

        Scenario:
            Given: A preset configuration from get_preset_config()
            When: Performance section is examined
            Then: "max_concurrent_scans" is a positive integer
            And: "cache_ttl_seconds" is a positive integer
            And: "onnx_providers" is a non-empty list of strings
            And: All values are within reasonable operational ranges

        Fixtures Used:
            - preset_names: List of preset names to test all configurations
        """
        # Given: Preset configurations from get_preset_config()
        for preset_name in preset_names:
            config = get_preset_config(preset_name)
            performance = config["performance"]

            # When: Performance section is examined

            # Then: "max_concurrent_scans" is a positive integer
            assert "max_concurrent_scans" in performance, f"Preset {preset_name} missing max_concurrent_scans"
            max_scans = performance["max_concurrent_scans"]
            assert isinstance(max_scans, int), f"Preset {preset_name} max_concurrent_scans should be integer"
            assert max_scans > 0, f"Preset {preset_name} max_concurrent_scans should be positive, got {max_scans}"

            # And: "cache_ttl_seconds" is a positive integer
            assert "cache_ttl_seconds" in performance, f"Preset {preset_name} missing cache_ttl_seconds"
            cache_ttl = performance["cache_ttl_seconds"]
            assert isinstance(cache_ttl, int), f"Preset {preset_name} cache_ttl_seconds should be integer"
            assert cache_ttl > 0, f"Preset {preset_name} cache_ttl_seconds should be positive, got {cache_ttl}"

            # And: "onnx_providers" is a non-empty list of strings
            assert "onnx_providers" in performance, f"Preset {preset_name} missing onnx_providers"
            providers = performance["onnx_providers"]
            assert isinstance(providers, list), f"Preset {preset_name} onnx_providers should be list"
            assert len(providers) > 0, f"Preset {preset_name} onnx_providers should not be empty"
            for provider in providers:
                assert isinstance(provider, str), f"Preset {preset_name} onnx provider should be string, got {type(provider)}"

            # And: All values are within reasonable operational ranges
            # Test preset should have minimal values
            if preset_name == "testing":
                assert max_scans <= 5, f"Testing preset should have low max_concurrent_scans, got {max_scans}"
                assert cache_ttl <= 10, f"Testing preset should have short cache_ttl_seconds, got {cache_ttl}"
            # Production preset should have higher values
            elif preset_name == "production":
                assert max_scans >= 10, f"Production preset should have high max_concurrent_scans, got {max_scans}"
                assert cache_ttl >= 3600, f"Production preset should have long cache_ttl_seconds, got {cache_ttl}"


class TestListPresets:
    """
    Test suite for list_presets() function.
    
    Scope:
        Verifies that list_presets() returns the complete catalog of available
        preset names in a consistent, predictable format.
        
    Business Critical:
        Preset discovery enables dynamic configuration and validation of user
        selections. Missing or incorrect preset names would prevent valid
        configurations from being used.
        
    Test Strategy:
        - Verify complete preset catalog is returned
        - Test return value consistency across calls
        - Verify no unexpected or invalid preset names are included
    """

    def test_returns_complete_list_of_available_presets(self, preset_names):
        """
        Test that list_presets returns all available preset names.

        Verifies:
            list_presets() returns a list containing all valid preset names
            that can be used with get_preset_config().

        Business Impact:
            Complete preset listing enables users to discover all available
            configuration options for their deployment needs.

        Scenario:
            Given: The presets module is imported
            When: list_presets() is called
            Then: A list is returned
            And: The list contains exactly 3 preset names
            And: The list contains "development"
            And: The list contains "production"
            And: The list contains "testing"

        Fixtures Used:
            - preset_names: Expected preset names for validation
        """
        # Given: The presets module is imported
        # When: list_presets() is called
        result = list_presets()

        # Then: A list is returned
        assert isinstance(result, list), "list_presets() should return a list"

        # And: The list contains exactly 3 preset names
        assert len(result) == 3, f"list_presets() should return exactly 3 presets, got {len(result)}"

        # And: The list contains all expected preset names
        for preset_name in preset_names:
            assert preset_name in result, f"list_presets() should contain '{preset_name}'"

    def test_returns_list_in_consistent_order(self):
        """
        Test that list_presets returns presets in consistent order across calls.

        Verifies:
            The order of preset names in the returned list is consistent across
            multiple calls, enabling predictable behavior in UI and automation.

        Business Impact:
            Consistent ordering provides better user experience and enables
            reliable automated configuration selection.

        Scenario:
            Given: list_presets() has been called multiple times
            When: The returned lists are compared
            Then: All lists are in identical order
            And: The order is always ['development', 'production', 'testing']

        Fixtures Used:
            - None (tests consistency of function behavior)
        """
        # Given: list_presets() has been called multiple times
        lists = []
        for i in range(3):
            preset_list = list_presets()
            lists.append(preset_list)

        # When: The returned lists are compared
        # Then: All lists are in identical order
        for i in range(1, len(lists)):
            assert lists[0] == lists[i], f"List {i} has different order than first list: {lists[0]} vs {lists[i]}"

        # And: The order is always ['development', 'production', 'testing']
        expected_order = ['development', 'production', 'testing']
        assert lists[0] == expected_order, f"Expected order {expected_order}, got {lists[0]}"

    def test_returns_new_list_instance_each_call(self):
        """
        Test that list_presets returns a new list instance on each call.

        Verifies:
            Each call to list_presets() returns a new list instance rather than
            a shared mutable reference, ensuring no shared state between callers.

        Business Impact:
            Separate list instances prevent accidental mutations from affecting
            other parts of the system, maintaining data integrity.

        Scenario:
            Given: list_presets() is called twice
            When: The returned list instances are compared
            Then: The instances are not the same object (different memory addresses)
            And: Modifying one list does not affect the other
            And: Both lists contain identical values

        Fixtures Used:
            - None (tests object identity and immutability guarantees)
        """
        # Given: list_presets() is called twice
        list1 = list_presets()
        list2 = list_presets()

        # When: The returned list instances are compared
        # Then: The instances are not the same object (different memory addresses)
        assert list1 is not list2, "list_presets() should return new list instance each call"

        # And: Both lists contain identical values
        assert list1 == list2, "Both lists should contain identical values"

        # And: Modifying one list does not affect the other
        list1.append("test_value")
        assert "test_value" not in list2, "Modifying list1 should not affect list2"
        assert len(list2) == len(list1) - 1, "list2 should remain unchanged"

    def test_all_returned_preset_names_are_valid(self):
        """
        Test that all preset names from list_presets work with get_preset_config.

        Verifies:
            Every preset name returned by list_presets() is a valid input for
            get_preset_config() and results in successful configuration retrieval.

        Business Impact:
            Ensures preset discovery and retrieval are synchronized, preventing
            errors when users select presets from the available list.

        Scenario:
            Given: The list of preset names from list_presets()
            When: get_preset_config() is called with each preset name
            Then: No ValueError is raised for any preset name
            And: A valid configuration dictionary is returned for each
            And: Each configuration's preset field matches the requested name

        Fixtures Used:
            - None (tests integration between list_presets and get_preset_config)
        """
        # Given: The list of preset names from list_presets()
        preset_names = list_presets()

        # When: get_preset_config() is called with each preset name
        for preset_name in preset_names:
            # Then: No ValueError is raised for any preset name
            try:
                config = get_preset_config(preset_name)
            except ValueError:
                pytest.fail(f"get_preset_config() should not raise ValueError for valid preset: {preset_name}")

            # And: A valid configuration dictionary is returned for each
            assert isinstance(config, dict), f"Config for {preset_name} should be a dictionary"
            assert "preset" in config, f"Config for {preset_name} should have 'preset' field"

            # And: Each configuration's preset field matches the requested name
            assert config["preset"] == preset_name, f"Config preset field should match requested name {preset_name}"

    def test_returned_list_contains_only_strings(self):
        """
        Test that list_presets returns a list containing only string elements.

        Verifies:
            All elements in the preset names list are strings, ensuring type
            consistency for downstream processing.

        Business Impact:
            Type consistency prevents runtime errors when preset names are used
            in string operations or passed to get_preset_config().

        Scenario:
            Given: The list returned from list_presets()
            When: The type of each element is checked
            Then: All elements are instances of str
            And: No None or other types are present in the list

        Fixtures Used:
            - None (tests return type guarantees)
        """
        # Given: The list returned from list_presets()
        preset_list = list_presets()

        # When: The type of each element is checked
        for i, element in enumerate(preset_list):
            # Then: All elements are instances of str
            assert isinstance(element, str), f"Element {i} should be string, got {type(element)}"
            # And: No None or other types are present in the list
            assert element is not None, f"Element {i} should not be None"

        # Additional validation: ensure all elements are non-empty strings
        for i, element in enumerate(preset_list):
            assert len(element.strip()) > 0, f"Element {i} should not be empty string"


class TestGetPresetDescription:
    """
    Test suite for get_preset_description() function.
    
    Scope:
        Verifies that get_preset_description() returns human-readable descriptions
        for all valid presets and handles invalid preset names gracefully.
        
    Business Critical:
        Preset descriptions help users understand configuration options and make
        informed choices for their deployment scenarios.
        
    Test Strategy:
        - Test descriptions for all valid presets
        - Verify description content is helpful and accurate
        - Test graceful handling of unknown preset names
    """

    def test_returns_description_for_development_preset(self, preset_descriptions):
        """
        Test that get_preset_description returns appropriate description for development.

        Verifies:
            get_preset_description("development") returns a human-readable description
            explaining the development preset's purpose and characteristics.

        Business Impact:
            Clear descriptions help developers select appropriate security
            configurations for their local development environments.

        Scenario:
            Given: A request for development preset description
            When: get_preset_description("development") is called
            Then: A non-empty string is returned
            And: The description contains "development" keyword
            And: The description mentions "lenient" or "fast iteration"
            And: The description matches expected development preset description

        Fixtures Used:
            - preset_descriptions: Expected preset descriptions for validation
        """
        # Given: A request for development preset description
        preset_name = "development"

        # When: get_preset_description("development") is called
        description = get_preset_description(preset_name)

        # Then: A non-empty string is returned
        assert isinstance(description, str), "Description should be a string"
        assert len(description.strip()) > 0, "Description should not be empty"

        # And: The description contains "development" keyword
        assert "development" in description.lower(), "Description should mention 'development'"

        # And: The description mentions "lenient" or "fast iteration"
        description_lower = description.lower()
        assert ("lenient" in description_lower or
                "fast iteration" in description_lower or
                "development" in description_lower), "Description should mention lenient settings or fast iteration"

        # And: The description matches expected development preset description
        expected_description = preset_descriptions.get("development")
        assert description == expected_description, f"Description should match expected: {expected_description}"

    def test_returns_description_for_production_preset(self, preset_descriptions):
        """
        Test that get_preset_description returns appropriate description for production.

        Verifies:
            get_preset_description("production") returns a human-readable description
            explaining the production preset's security focus and deployment context.

        Business Impact:
            Clear descriptions help teams select appropriate security configurations
            for production deployments with real user data.

        Scenario:
            Given: A request for production preset description
            When: get_preset_description("production") is called
            Then: A non-empty string is returned
            And: The description contains "production" keyword
            And: The description mentions "strict" or "security"
            And: The description matches expected production preset description

        Fixtures Used:
            - preset_descriptions: Expected preset descriptions for validation
        """
        # Given: A request for production preset description
        preset_name = "production"

        # When: get_preset_description("production") is called
        description = get_preset_description(preset_name)

        # Then: A non-empty string is returned
        assert isinstance(description, str), "Description should be a string"
        assert len(description.strip()) > 0, "Description should not be empty"

        # And: The description contains "production" keyword
        assert "production" in description.lower(), "Description should mention 'production'"

        # And: The description mentions "strict" or "security"
        description_lower = description.lower()
        assert ("strict" in description_lower or
                "security" in description_lower), "Description should mention strict settings or security"

        # And: The description matches expected production preset description
        expected_description = preset_descriptions.get("production")
        assert description == expected_description, f"Description should match expected: {expected_description}"

    def test_returns_description_for_testing_preset(self, preset_descriptions):
        """
        Test that get_preset_description returns appropriate description for testing.

        Verifies:
            get_preset_description("testing") returns a human-readable description
            explaining the testing preset's performance focus and CI/CD optimization.

        Business Impact:
            Clear descriptions help teams configure appropriate security settings
            for automated testing environments and CI/CD pipelines.

        Scenario:
            Given: A request for testing preset description
            When: get_preset_description("testing") is called
            Then: A non-empty string is returned
            And: The description contains "testing" keyword
            And: The description mentions "minimal" or "fast execution"
            And: The description matches expected testing preset description

        Fixtures Used:
            - preset_descriptions: Expected preset descriptions for validation
        """
        # Given: A request for testing preset description
        preset_name = "testing"

        # When: get_preset_description("testing") is called
        description = get_preset_description(preset_name)

        # Then: A non-empty string is returned
        assert isinstance(description, str), "Description should be a string"
        assert len(description.strip()) > 0, "Description should not be empty"

        # And: The description contains "testing" keyword
        assert "testing" in description.lower(), "Description should mention 'testing'"

        # And: The description mentions "minimal" or "fast execution"
        description_lower = description.lower()
        assert ("minimal" in description_lower or
                "fast execution" in description_lower or
                "testing" in description_lower), "Description should mention minimal scanners or fast execution"

        # And: The description matches expected testing preset description
        expected_description = preset_descriptions.get("testing")
        assert description == expected_description, f"Description should match expected: {expected_description}"

    def test_returns_unknown_preset_message_for_invalid_names(self):
        """
        Test that get_preset_description handles unknown preset names gracefully.

        Verifies:
            get_preset_description() returns "Unknown preset" fallback message
            when called with a preset name that doesn't exist in the system.

        Business Impact:
            Graceful handling prevents runtime errors and provides clear feedback
            when preset names are mistyped or outdated.

        Scenario:
            Given: An invalid preset name "nonexistent_preset"
            When: get_preset_description("nonexistent_preset") is called
            Then: The string "Unknown preset" is returned
            And: No exception is raised
            And: The function completes successfully

        Fixtures Used:
            - None (tests error handling with invalid input)
        """
        # Given: An invalid preset name "nonexistent_preset"
        invalid_preset_name = "nonexistent_preset"

        # When: get_preset_description("nonexistent_preset") is called
        # Then: The string "Unknown preset" is returned
        result = get_preset_description(invalid_preset_name)
        assert result == "Unknown preset", f"Expected 'Unknown preset', got '{result}'"

        # And: No exception is raised
        # The function call above completes without exception

        # And: The function completes successfully
        assert isinstance(result, str), "Should return a string"
        assert len(result) > 0, "Should return non-empty string"

    def test_descriptions_are_helpful_and_informative(self, preset_names):
        """
        Test that preset descriptions contain useful information for users.

        Verifies:
            All preset descriptions are substantive, informative strings that
            explain the preset's purpose rather than being empty or generic.

        Business Impact:
            Helpful descriptions enable users to make informed configuration
            decisions without consulting extensive documentation.

        Scenario:
            Given: Each available preset name
            When: get_preset_description() is called for each preset
            Then: Each description is a non-empty string
            And: Each description is at least 20 characters long
            And: Each description mentions the preset name or its purpose
            And: Each description is unique (not duplicated across presets)

        Fixtures Used:
            - preset_names: List of preset names to iterate
        """
        # Given: Each available preset name
        descriptions = []

        # When: get_preset_description() is called for each preset
        for preset_name in preset_names:
            description = get_preset_description(preset_name)
            descriptions.append((preset_name, description))

            # Then: Each description is a non-empty string
            assert isinstance(description, str), f"Description for {preset_name} should be string"
            assert len(description.strip()) > 0, f"Description for {preset_name} should not be empty"

            # And: Each description is at least 20 characters long
            assert len(description) >= 20, f"Description for {preset_name} should be at least 20 characters: '{description}'"

            # And: Each description mentions the preset name or its purpose
            description_lower = description.lower()
            assert preset_name.lower() in description_lower, f"Description for {preset_name} should mention the preset name"

        # And: Each description is unique (not duplicated across presets)
        description_texts = [desc for _, desc in descriptions]
        unique_descriptions = set(description_texts)
        assert len(description_texts) == len(unique_descriptions), "All preset descriptions should be unique"

    def test_descriptions_match_preset_purposes(self):
        """
        Test that preset descriptions accurately reflect preset characteristics.

        Verifies:
            Preset descriptions accurately describe the security level, use case,
            and key characteristics of each preset configuration.

        Business Impact:
            Accurate descriptions prevent misconfiguration by clearly communicating
            the trade-offs and intended use cases for each preset.

        Scenario:
            Given: Development preset description
            When: The description content is analyzed
            Then: The description indicates lenient/development usage

            Given: Production preset description
            When: The description content is analyzed
            Then: The description indicates strict/production security

            Given: Testing preset description
            When: The description content is analyzed
            Then: The description indicates minimal/fast testing focus

        Fixtures Used:
            - None (tests semantic content of descriptions)
        """
        # Given: Development preset description
        dev_description = get_preset_description("development")
        # When: The description content is analyzed
        # Then: The description indicates lenient/development usage
        dev_lower = dev_description.lower()
        assert ("lenient" in dev_lower or
                "development" in dev_lower or
                "fast iteration" in dev_lower), "Development description should mention lenient settings or fast iteration"

        # Given: Production preset description
        prod_description = get_preset_description("production")
        # When: The description content is analyzed
        # Then: The description indicates strict/production security
        prod_lower = prod_description.lower()
        assert ("strict" in prod_lower or
                "security" in prod_lower or
                "production" in prod_lower), "Production description should mention strict security or production deployment"

        # Given: Testing preset description
        test_description = get_preset_description("testing")
        # When: The description content is analyzed
        # Then: The description indicates minimal/fast testing focus
        test_lower = test_description.lower()
        assert ("minimal" in test_lower or
                "fast execution" in test_lower or
                "testing" in test_lower), "Testing description should mention minimal scanners or fast execution"

        # Additional verification: ensure descriptions are clearly distinguishable
        descriptions = [dev_description, prod_description, test_description]
        unique_descriptions = set(descriptions)
        assert len(descriptions) == len(unique_descriptions), "All preset descriptions should be clearly distinguishable"

