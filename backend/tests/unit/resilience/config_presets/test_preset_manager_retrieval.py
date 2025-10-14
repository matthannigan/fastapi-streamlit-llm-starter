"""
Test suite for PresetManager preset retrieval and information access.

Verifies that the PresetManager correctly retrieves presets by name,
lists available presets, and provides detailed preset information.
"""

import pytest
from app.infrastructure.resilience.config_presets import PresetManager, ResiliencePreset


class TestPresetManagerRetrieval:
    """
    Test suite for preset retrieval operations.
    
    Scope:
        - get_preset() method for retrieving presets by name
        - list_presets() method for listing available presets
        - get_preset_details() method for detailed information
        - Error handling for invalid preset names
        
    Business Critical:
        Accurate preset retrieval is fundamental for configuration management,
        enabling applications to access correct resilience settings.
        
    Test Strategy:
        - Test successful retrieval of all predefined presets
        - Verify list_presets() completeness and accuracy
        - Test detailed information access
        - Validate error handling for invalid names
    """
    
    def test_get_preset_returns_simple_preset(self):
        """
        Test that get_preset() retrieves the 'simple' preset successfully.

        Verifies:
            The get_preset() method returns a valid ResiliencePreset object
            when called with 'simple' preset name as documented in method contract.

        Business Impact:
            Ensures the fundamental 'simple' preset is accessible for
            applications requiring balanced default configuration.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset("simple") is called
            Then: A ResiliencePreset object is returned
            And: Preset name is "Simple"
            And: Preset has expected retry_attempts and circuit_breaker_threshold
            And: Preset default_strategy is ResilienceStrategy.BALANCED

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: An initialized PresetManager instance
        from app.infrastructure.resilience.config_presets import ResilienceStrategy
        manager = PresetManager()

        # When: get_preset("simple") is called
        result = manager.get_preset("simple")

        # Then: A ResiliencePreset object is returned
        assert isinstance(result, ResiliencePreset)

        # And: Preset name is "Simple"
        assert result.name == "Simple"

        # And: Preset has expected retry_attempts and circuit_breaker_threshold
        assert result.retry_attempts == 3
        assert result.circuit_breaker_threshold == 5
        assert result.recovery_timeout == 60

        # And: Preset default_strategy is ResilienceStrategy.BALANCED
        assert result.default_strategy == ResilienceStrategy.BALANCED
    
    def test_get_preset_returns_development_preset(self):
        """
        Test that get_preset() retrieves the 'development' preset successfully.

        Verifies:
            The get_preset() method returns the development preset with
            fast-fail characteristics as documented in PRESETS definition.

        Business Impact:
            Ensures development-optimized configuration is available for
            rapid iteration and debugging workflows.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset("development") is called
            Then: A ResiliencePreset object is returned
            And: Preset name is "Development"
            And: Preset has aggressive strategy for fast failures
            And: Preset retry_attempts is lower than production

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: An initialized PresetManager instance
        from app.infrastructure.resilience.config_presets import ResilienceStrategy
        manager = PresetManager()

        # When: get_preset("development") is called
        result = manager.get_preset("development")

        # Then: A ResiliencePreset object is returned
        assert isinstance(result, ResiliencePreset)

        # And: Preset name is "Development"
        assert result.name == "Development"

        # And: Preset has aggressive strategy for fast failures
        assert result.default_strategy == ResilienceStrategy.AGGRESSIVE

        # And: Preset retry_attempts is lower than production
        assert result.retry_attempts == 2
        assert result.circuit_breaker_threshold == 3
        assert result.recovery_timeout == 30
    
    def test_get_preset_returns_production_preset(self):
        """
        Test that get_preset() retrieves the 'production' preset successfully.

        Verifies:
            The get_preset() method returns the production preset with
            high-reliability characteristics as documented in PRESETS definition.

        Business Impact:
            Ensures production-grade configuration with maximum reliability
            is accessible for critical production deployments.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset("production") is called
            Then: A ResiliencePreset object is returned
            And: Preset name is "Production"
            And: Preset has conservative strategy for reliability
            And: Preset retry_attempts is higher than development
            And: Preset includes operation-specific overrides

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: An initialized PresetManager instance
        from app.infrastructure.resilience.config_presets import ResilienceStrategy
        manager = PresetManager()

        # When: get_preset("production") is called
        result = manager.get_preset("production")

        # Then: A ResiliencePreset object is returned
        assert isinstance(result, ResiliencePreset)

        # And: Preset name is "Production"
        assert result.name == "Production"

        # And: Preset has conservative strategy for reliability
        assert result.default_strategy == ResilienceStrategy.CONSERVATIVE

        # And: Preset retry_attempts is higher than development
        assert result.retry_attempts == 5
        assert result.circuit_breaker_threshold == 10
        assert result.recovery_timeout == 120

        # And: Preset includes operation-specific overrides
        assert len(result.operation_overrides) > 0
        assert "qa" in result.operation_overrides
        assert result.operation_overrides["qa"] == ResilienceStrategy.CRITICAL
    
    def test_get_preset_with_invalid_name_raises_value_error(self):
        """
        Test that get_preset() raises ValueError for invalid preset name.

        Verifies:
            The get_preset() method raises ValueError when called with
            a preset name that doesn't exist as documented in Raises section.

        Business Impact:
            Prevents silent failures from typos or configuration errors,
            ensuring configuration problems are caught early.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset("nonexistent_preset") is called
            Then: ValueError is raised
            And: Error message indicates preset was not found
            And: Error message lists available preset names

        Fixtures Used:
            - None (tests error handling)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When/Then: get_preset("nonexistent_preset") is called, ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            manager.get_preset("nonexistent_preset")

        # And: Error message indicates preset was not found
        error_message = str(exc_info.value)
        assert "nonexistent_preset" in error_message
        assert "Unknown preset" in error_message

        # And: Error message lists available preset names
        assert "Available presets" in error_message
        assert "simple" in error_message
        assert "development" in error_message
        assert "production" in error_message
    
    def test_get_preset_with_empty_name_raises_value_error(self):
        """
        Test that get_preset() raises ValueError for empty string.

        Verifies:
            The get_preset() method validates input and raises ValueError
            for empty or whitespace-only preset names.

        Business Impact:
            Ensures robust input validation preventing invalid configuration
            access and improving error diagnostics.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset("") is called with empty string
            Then: ValueError is raised
            And: Error message indicates invalid preset name

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When/Then: get_preset("") is called with empty string, ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            manager.get_preset("")

        # And: Error message indicates invalid preset name
        error_message = str(exc_info.value)
        assert "Unknown preset" in error_message or "Invalid preset name" in error_message
        assert "Available presets" in error_message
    
    def test_list_presets_returns_all_available_preset_names(self):
        """
        Test that list_presets() returns complete list of preset names.

        Verifies:
            The list_presets() method returns a list containing all available
            preset names (simple, development, production) as documented in
            return contract.

        Business Impact:
            Enables applications to discover available configurations
            dynamically for UI selection or validation purposes.

        Scenario:
            Given: An initialized PresetManager instance
            When: list_presets() is called
            Then: A list of strings is returned
            And: List contains "simple", "development", and "production"
            And: List length matches the number of PRESETS entries
            And: No duplicate names are present

        Fixtures Used:
            - None (tests list operation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: list_presets() is called
        result = manager.list_presets()

        # Then: A list of strings is returned
        assert isinstance(result, list)
        assert all(isinstance(name, str) for name in result)

        # And: List contains "simple", "development", and "production"
        expected_presets = ["simple", "development", "production"]
        for preset in expected_presets:
            assert preset in result

        # And: List length matches the number of PRESETS entries
        assert len(result) == 3

        # And: No duplicate names are present
        assert len(result) == len(set(result))
    
    def test_list_presets_returns_consistent_results(self):
        """
        Test that list_presets() returns consistent results across calls.

        Verifies:
            The list_presets() method returns the same preset names
            on multiple invocations, ensuring consistency.

        Business Impact:
            Ensures reliable preset discovery for applications that
            cache or repeatedly query available presets.

        Scenario:
            Given: An initialized PresetManager instance
            When: list_presets() is called multiple times
            Then: All calls return identical preset name lists
            And: Order of names is consistent

        Fixtures Used:
            - None (tests consistency)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: list_presets() is called multiple times
        result1 = manager.list_presets()
        result2 = manager.list_presets()
        result3 = manager.list_presets()

        # Then: All calls return identical preset name lists
        assert result1 == result2 == result3

        # And: Order of names is consistent
        # (Since we're comparing lists directly, order matters)
        assert result1 is not None
        assert len(result1) > 0
    
    def test_get_preset_details_returns_comprehensive_information(self):
        """
        Test that get_preset_details() returns complete preset information.

        Verifies:
            The get_preset_details() method returns a dictionary containing
            all preset configuration details as documented in return contract.

        Business Impact:
            Provides detailed configuration information for monitoring,
            debugging, and administrative interfaces.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset_details("production") is called
            Then: A dictionary is returned with preset configuration
            And: Dictionary contains name, description, and all settings
            And: Dictionary includes operation_overrides mapping
            And: Dictionary includes environment_contexts list

        Fixtures Used:
            - None (tests information access)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: get_preset_details("production") is called
        result = manager.get_preset_details("production")

        # Then: A dictionary is returned with preset configuration
        assert isinstance(result, dict)

        # And: Dictionary contains name, description, and all settings
        assert "name" in result
        assert "description" in result
        assert "configuration" in result
        assert "environment_contexts" in result

        # Verify the basic fields
        assert result["name"] == "Production"
        assert isinstance(result["description"], str)
        assert len(result["description"]) > 0

        # And: Dictionary includes operation_overrides mapping
        config = result["configuration"]
        assert "operation_overrides" in config
        assert isinstance(config["operation_overrides"], dict)
        assert len(config["operation_overrides"]) > 0

        # And: Dictionary includes environment_contexts list
        assert isinstance(result["environment_contexts"], list)
        assert len(result["environment_contexts"]) > 0

        # Verify other configuration fields
        assert "retry_attempts" in config
        assert "circuit_breaker_threshold" in config
        assert "recovery_timeout" in config
        assert "default_strategy" in config
    
    def test_get_preset_details_with_invalid_name_raises_value_error(self):
        """
        Test that get_preset_details() raises ValueError for invalid name.

        Verifies:
            The get_preset_details() method validates preset name and
            raises ValueError for non-existent presets.

        Business Impact:
            Ensures robust error handling when requesting details for
            invalid configurations, improving error diagnostics.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_preset_details("invalid_preset") is called
            Then: ValueError is raised
            And: Error message indicates preset not found

        Fixtures Used:
            - None (tests error handling)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When/Then: get_preset_details("invalid_preset") is called, ValueError is raised
        with pytest.raises(ValueError) as exc_info:
            manager.get_preset_details("invalid_preset")

        # And: Error message indicates preset not found
        error_message = str(exc_info.value)
        assert "invalid_preset" in error_message
        assert "Unknown preset" in error_message


class TestPresetManagerSummary:
    """
    Test suite for get_all_presets_summary() comprehensive preset information.
    
    Scope:
        - get_all_presets_summary() aggregation behavior
        - Completeness of returned information
        - Data structure format and consistency
        
    Business Critical:
        Summary information enables administrative dashboards and
        configuration management tools to display all available options.
    """
    
    def test_get_all_presets_summary_returns_all_presets(self):
        """
        Test that get_all_presets_summary() includes all available presets.

        Verifies:
            The method returns a dictionary mapping all preset names to
            their detailed configuration as documented in return contract.

        Business Impact:
            Provides single-call access to all preset information for
            administrative interfaces and configuration documentation.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_all_presets_summary() is called
            Then: A dictionary is returned with entries for all presets
            And: Dictionary keys match list_presets() output
            And: Each entry contains complete preset details
            And: All presets have consistent information structure

        Fixtures Used:
            - None (tests summary aggregation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: get_all_presets_summary() is called
        result = manager.get_all_presets_summary()

        # Then: A dictionary is returned with entries for all presets
        assert isinstance(result, dict)

        # And: Dictionary keys match list_presets() output
        preset_list = manager.list_presets()
        assert set(result.keys()) == set(preset_list)

        # And: Each entry contains complete preset details
        for preset_name, preset_details in result.items():
            assert isinstance(preset_details, dict)
            assert "name" in preset_details
            assert "description" in preset_details
            assert "configuration" in preset_details
            assert "environment_contexts" in preset_details

        # And: All presets have consistent information structure
        expected_keys = {"name", "description", "configuration", "environment_contexts"}
        for preset_details in result.values():
            assert set(preset_details.keys()) == expected_keys
    
    def test_get_all_presets_summary_includes_detailed_configuration(self):
        """
        Test that each preset in summary contains complete configuration.

        Verifies:
            Each preset entry in the summary contains all configuration
            fields including name, description, settings, and contexts.

        Business Impact:
            Ensures administrative tools have complete information for
            all presets without requiring individual detail queries.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_all_presets_summary() is called
            Then: Each preset entry contains name and description fields
            And: Each entry includes retry_attempts and circuit_breaker_threshold
            And: Each entry includes default_strategy and operation_overrides
            And: Each entry includes environment_contexts list

        Fixtures Used:
            - None (tests data completeness)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: get_all_presets_summary() is called
        result = manager.get_all_presets_summary()

        # Then: Each preset entry contains name and description fields
        for preset_name, preset_details in result.items():
            assert "name" in preset_details
            assert "description" in preset_details
            assert isinstance(preset_details["name"], str)
            assert isinstance(preset_details["description"], str)
            assert len(preset_details["name"]) > 0
            assert len(preset_details["description"]) > 0

            # And: Each entry includes retry_attempts and circuit_breaker_threshold
            config = preset_details["configuration"]
            assert "retry_attempts" in config
            assert "circuit_breaker_threshold" in config
            assert isinstance(config["retry_attempts"], int)
            assert isinstance(config["circuit_breaker_threshold"], int)
            assert config["retry_attempts"] > 0
            assert config["circuit_breaker_threshold"] > 0

            # And: Each entry includes default_strategy and operation_overrides
            assert "default_strategy" in config
            assert "operation_overrides" in config
            assert isinstance(config["default_strategy"], str)
            assert isinstance(config["operation_overrides"], dict)

            # And: Each entry includes environment_contexts list
            assert "environment_contexts" in preset_details
            assert isinstance(preset_details["environment_contexts"], list)
            assert len(preset_details["environment_contexts"]) > 0
    
    def test_get_all_presets_summary_returns_consistent_structure(self):
        """
        Test that all preset entries have consistent data structure.

        Verifies:
            All preset entries in the summary follow the same structure
            and field naming conventions for parsing consistency.

        Business Impact:
            Enables reliable programmatic processing of preset information
            without special-case handling for different presets.

        Scenario:
            Given: An initialized PresetManager instance
            When: get_all_presets_summary() is called
            Then: All preset entries have identical field names
            And: Field types are consistent across all presets
            And: Data structure is suitable for JSON serialization

        Fixtures Used:
            - None (tests structural consistency)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # When: get_all_presets_summary() is called
        result = manager.get_all_presets_summary()

        # Then: All preset entries have identical field names
        if len(result) > 1:
            # Get the first preset as reference
            first_preset = next(iter(result.values()))
            expected_top_level_keys = set(first_preset.keys())
            expected_config_keys = set(first_preset["configuration"].keys())

            # Verify all presets have same structure
            for preset_details in result.values():
                assert set(preset_details.keys()) == expected_top_level_keys
                assert set(preset_details["configuration"].keys()) == expected_config_keys

        # And: Field types are consistent across all presets
        for preset_details in result.values():
            # Top-level field types
            assert isinstance(preset_details["name"], str)
            assert isinstance(preset_details["description"], str)
            assert isinstance(preset_details["configuration"], dict)
            assert isinstance(preset_details["environment_contexts"], list)

            # Configuration field types
            config = preset_details["configuration"]
            assert isinstance(config["retry_attempts"], int)
            assert isinstance(config["circuit_breaker_threshold"], int)
            assert isinstance(config["recovery_timeout"], int)
            assert isinstance(config["default_strategy"], str)
            assert isinstance(config["operation_overrides"], dict)

        # And: Data structure is suitable for JSON serialization
        # Test that it can be serialized to JSON (basic check for JSON-serializable types)
        import json
        try:
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
            assert len(json_str) > 0
        except (TypeError, ValueError) as e:
            pytest.fail(f"Summary result is not JSON serializable: {e}")