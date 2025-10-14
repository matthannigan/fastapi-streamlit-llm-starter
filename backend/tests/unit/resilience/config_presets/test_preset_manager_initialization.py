"""
Test suite for PresetManager initialization and preset loading.

Verifies that the PresetManager correctly loads predefined presets,
initializes validation infrastructure, and prepares for environment detection.
"""

import pytest
from app.infrastructure.resilience.config_presets import PresetManager, PRESETS


class TestPresetManagerInitialization:
    """
    Test suite for PresetManager initialization behavior.
    
    Scope:
        - Constructor behavior and default state
        - Preset loading from PRESETS dictionary
        - Validation infrastructure setup
        - Environment detection preparation
        
    Business Critical:
        Proper initialization ensures reliable preset management and
        environment-aware configuration recommendations in production.
        
    Test Strategy:
        - Verify preset loading completeness
        - Test default state after initialization
        - Validate infrastructure readiness
    """
    
    def test_initialization_loads_all_predefined_presets(self):
        """
        Test that PresetManager loads all presets from PRESETS dictionary.

        Verifies:
            All predefined presets (simple, development, production) are loaded
            and accessible after initialization as documented in Behavior section.

        Business Impact:
            Ensures all documented presets are available for configuration
            selection, preventing missing configuration options.

        Scenario:
            Given: The PRESETS dictionary contains predefined presets
            When: PresetManager is instantiated
            Then: All PRESETS keys are accessible via list_presets()
            And: Each preset can be retrieved via get_preset()
            And: Preset count matches PRESETS dictionary size

        Fixtures Used:
            - None (tests initialization behavior)
        """
        # Given: The PRESETS dictionary contains predefined presets
        expected_presets = set(PRESETS.keys())

        # When: PresetManager is instantiated
        manager = PresetManager()

        # Then: All PRESETS keys are accessible via list_presets()
        loaded_presets = set(manager.list_presets())
        assert loaded_presets == expected_presets, (
            f"Loaded presets {loaded_presets} don't match expected {expected_presets}"
        )

        # And: Each preset can be retrieved via get_preset()
        for preset_name in PRESETS.keys():
            preset = manager.get_preset(preset_name)
            assert preset is not None, f"Failed to retrieve preset '{preset_name}'"
            assert preset.name == PRESETS[preset_name].name

        # And: Preset count matches PRESETS dictionary size
        assert len(manager.list_presets()) == len(PRESETS)
    
    def test_initialization_prepares_validation_infrastructure(self):
        """
        Test that PresetManager sets up validation capabilities.

        Verifies:
            Validation infrastructure is initialized and ready to validate
            preset configurations as documented in Behavior section.

        Business Impact:
            Enables immediate preset validation after initialization
            without additional setup or configuration errors.

        Scenario:
            Given: PresetManager instantiation
            When: validate_preset() is called immediately after init
            Then: Validation executes without initialization errors
            And: Validation logic is functional for valid presets

        Fixtures Used:
            - None (tests validation readiness)
        """
        # Given: PresetManager instantiation
        manager = PresetManager()

        # When: validate_preset() is called immediately after init with a valid preset
        simple_preset = manager.get_preset("simple")

        # Then: Validation executes without initialization errors
        # And: Validation logic is functional for valid presets
        result = manager.validate_preset(simple_preset)
        assert result is True, "Validation should succeed for valid preset"

        # Verify validation works for all predefined presets
        for preset_name in PRESETS.keys():
            preset = manager.get_preset(preset_name)
            is_valid = manager.validate_preset(preset)
            assert is_valid is True, f"Preset '{preset_name}' should be valid"
    
    def test_initialization_prepares_environment_detection_patterns(self):
        """
        Test that PresetManager initializes environment detection capabilities.

        Verifies:
            Environment detection patterns and logic are ready for
            intelligent preset recommendations as documented in Behavior section.

        Business Impact:
            Ensures environment-aware recommendations work immediately
            after initialization for deployment automation.

        Scenario:
            Given: PresetManager instantiation
            When: recommend_preset() is called immediately after init
            Then: Environment detection executes without errors
            And: A valid preset recommendation is returned

        Fixtures Used:
            - None (tests environment detection readiness)
        """
        # Given: PresetManager instantiation
        manager = PresetManager()

        # When: recommend_preset() is called immediately after init
        # This tests auto-detection (no environment parameter)
        recommended_preset = manager.recommend_preset()

        # Then: Environment detection executes without errors
        assert recommended_preset is not None, "recommend_preset() should return a preset name"
        assert isinstance(recommended_preset, str), "recommend_preset() should return a string"
        assert recommended_preset in ["simple", "development", "production"], \
            f"Recommended preset '{recommended_preset}' should be one of the valid presets"

        # And: A valid preset recommendation is returned
        # Test with explicit environment parameter
        explicit_recommendation = manager.recommend_preset("development")
        assert explicit_recommendation == "development", \
            f"Explicit environment 'development' should recommend 'development' preset, got '{explicit_recommendation}'"

        # Test detailed recommendation to ensure full environment detection works
        detailed_recommendation = manager.recommend_preset_with_details("production")
        assert detailed_recommendation.preset_name == "production", \
            f"Detailed recommendation for 'production' should return 'production' preset"
        assert detailed_recommendation.confidence > 0.0, "Confidence should be positive"
        assert isinstance(detailed_recommendation.reasoning, str), "Reasoning should be a string"
        assert len(detailed_recommendation.reasoning) > 0, "Reasoning should not be empty"

        # Test pattern matching with complex environment names
        complex_env_recommendation = manager.recommend_preset_with_details("staging-environment-v2")
        assert complex_env_recommendation.preset_name in ["simple", "development", "production"], \
            "Complex environment names should return valid preset recommendations"
    
    def test_initialization_creates_thread_safe_preset_storage(self):
        """
        Test that PresetManager provides thread-safe preset access.

        Verifies:
            Preset storage supports concurrent access from multiple threads
            as documented in State Management section.

        Business Impact:
            Ensures reliable preset access in multi-threaded application
            environments without race conditions or data corruption.

        Scenario:
            Given: PresetManager instantiation
            When: Multiple threads access presets concurrently
            And: Operations include get_preset() and list_presets()
            Then: All operations complete successfully
            And: No thread-safety exceptions occur
            And: Returned presets are consistent and valid

        Fixtures Used:
            - fake_threading_module: Simulates concurrent access
        """
        import threading
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Given: PresetManager instantiation
        manager = PresetManager()

        # Track results from concurrent operations
        results = []
        errors = []

        def get_preset_worker(preset_name):
            """Worker function that gets a specific preset multiple times."""
            try:
                for _ in range(10):
                    preset = manager.get_preset(preset_name)
                    results.append({
                        'operation': 'get_preset',
                        'preset_name': preset_name,
                        'preset_id': id(preset),  # Track object identity
                        'preset_data': {
                            'name': preset.name,
                            'retry_attempts': preset.retry_attempts,
                            'circuit_breaker_threshold': preset.circuit_breaker_threshold
                        }
                    })
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(f"get_preset error for {preset_name}: {e}")

        def list_presets_worker():
            """Worker function that lists presets multiple times."""
            try:
                for _ in range(10):
                    preset_list = manager.list_presets()
                    results.append({
                        'operation': 'list_presets',
                        'preset_list': sorted(preset_list),  # Sort for consistency
                        'list_length': len(preset_list)
                    })
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append(f"list_presets error: {e}")

        def validate_preset_worker():
            """Worker function that validates presets."""
            try:
                preset_names = ["simple", "development", "production"]
                for preset_name in preset_names:
                    preset = manager.get_preset(preset_name)
                    is_valid = manager.validate_preset(preset)
                    results.append({
                        'operation': 'validate_preset',
                        'preset_name': preset_name,
                        'is_valid': is_valid
                    })
                    time.sleep(0.001)
            except Exception as e:
                errors.append(f"validate_preset error: {e}")

        # When: Multiple threads access presets concurrently
        # Create multiple threads for different operations
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit get_preset operations for different presets
            get_futures = [
                executor.submit(get_preset_worker, preset_name)
                for preset_name in ["simple", "development", "production"]
                for _ in range(3)  # 3 workers per preset
            ]

            # Submit list_presets operations
            list_futures = [
                executor.submit(list_presets_worker)
                for _ in range(5)  # 5 workers listing presets
            ]

            # Submit validate_preset operations
            validate_futures = [
                executor.submit(validate_preset_worker)
                for _ in range(2)  # 2 workers validating presets
            ]

            # Wait for all operations to complete
            all_futures = get_futures + list_futures + validate_futures
            for future in as_completed(all_futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    errors.append(f"Thread execution error: {e}")

        # Then: All operations complete successfully
        assert len(errors) == 0, f"Thread safety errors occurred: {errors}"
        assert len(results) > 0, "No results collected from concurrent operations"

        # And: No thread-safety exceptions occur
        # (This is verified by the empty errors list above)

        # And: Returned presets are consistent and valid
        # Check get_preset results
        get_results = [r for r in results if r['operation'] == 'get_preset']
        assert len(get_results) > 0, "No get_preset results found"

        # Verify all get_preset operations returned valid presets
        for result in get_results:
            assert result['preset_name'] in ["simple", "development", "production"]
            assert result['preset_data']['name'] in ["Simple", "Development", "Production"]
            assert result['preset_data']['retry_attempts'] > 0
            assert result['preset_data']['circuit_breaker_threshold'] > 0

        # Check list_presets results
        list_results = [r for r in results if r['operation'] == 'list_presets']
        assert len(list_results) > 0, "No list_presets results found"

        # Verify all list_presets operations returned consistent results
        expected_presets = {"simple", "development", "production"}
        for result in list_results:
            assert set(result['preset_list']) == expected_presets, \
                f"Inconsistent preset list: {result['preset_list']}"
            assert result['list_length'] == 3, \
                f"Incorrect list length: {result['list_length']}"

        # Check validate_preset results
        validate_results = [r for r in results if r['operation'] == 'validate_preset']
        assert len(validate_results) > 0, "No validate_preset results found"

        # Verify all validate_preset operations returned True (all predefined presets should be valid)
        for result in validate_results:
            assert result['is_valid'] is True, \
                f"Preset {result['preset_name']} should be valid but validation returned False"

        # Verify consistency - same preset objects should have consistent data
        simple_results = [r for r in get_results if r['preset_name'] == 'simple']
        if len(simple_results) > 1:
            first_result = simple_results[0]
            for result in simple_results[1:]:
                assert result['preset_data'] == first_result['preset_data'], \
                    "Simple preset data should be consistent across threads"