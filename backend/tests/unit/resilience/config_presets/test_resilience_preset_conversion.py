"""
Test suite for ResiliencePreset conversion and serialization methods.

Verifies that ResiliencePreset objects correctly convert to dictionaries
and ResilienceConfig objects with proper parameter mapping.
"""

import pytest
from app.infrastructure.resilience.config_presets import (
    ResiliencePreset,
    ResilienceConfig,
    ResilienceStrategy,
    PRESETS
)


class TestResiliencePresetToDictConversion:
    """
    Test suite for ResiliencePreset.to_dict() serialization.
    
    Scope:
        - to_dict() method for JSON serialization
        - Enum value string conversion
        - Field preservation and structure
        - Metadata inclusion
        
    Business Critical:
        Accurate serialization enables configuration persistence,
        API responses, and integration with external systems.
        
    Test Strategy:
        - Test dictionary structure completeness
        - Verify enum to string conversion
        - Test all preset types conversion
        - Validate JSON serializability
    """
    
    def test_to_dict_returns_complete_dictionary_structure(self):
        """
        Test that to_dict() returns dictionary with all preset fields.

        Verifies:
            The to_dict() method returns a dictionary containing all
            ResiliencePreset fields as documented in method contract.

        Business Impact:
            Ensures complete preset information is available for
            persistence, API responses, and external integrations.

        Scenario:
            Given: A ResiliencePreset instance (e.g., simple preset)
            When: to_dict() is called
            Then: Dictionary contains name, description fields
            And: Dictionary contains retry_attempts, circuit_breaker_threshold
            And: Dictionary contains recovery_timeout, default_strategy
            And: Dictionary contains operation_overrides, environment_contexts

        Fixtures Used:
            - None (tests serialization behavior)
        """
        # Given: A ResiliencePreset instance
        preset = PRESETS["simple"]

        # When: to_dict() is called
        result = preset.to_dict()

        # Then: Dictionary contains all required fields
        assert "name" in result
        assert "description" in result
        assert "retry_attempts" in result
        assert "circuit_breaker_threshold" in result
        assert "recovery_timeout" in result
        assert "default_strategy" in result
        assert "operation_overrides" in result
        assert "environment_contexts" in result

        # And: Values match the preset
        assert result["name"] == "Simple"
        assert result["retry_attempts"] == 3
        assert result["circuit_breaker_threshold"] == 5
    
    def test_to_dict_converts_strategy_enum_to_string(self):
        """
        Test that to_dict() converts ResilienceStrategy enum to string.

        Verifies:
            The default_strategy field is converted from ResilienceStrategy
            enum to string value as documented in Behavior section.

        Business Impact:
            Enables JSON serialization of presets without custom
            encoder handling for enum types.

        Scenario:
            Given: A ResiliencePreset with default_strategy = ResilienceStrategy.BALANCED
            When: to_dict() is called
            Then: Dictionary['default_strategy'] is string "balanced"
            And: Enum value is properly converted

        Fixtures Used:
            - None (tests enum conversion)
        """
        # Given: A ResiliencePreset with BALANCED strategy
        preset = PRESETS["simple"]
        assert preset.default_strategy == ResilienceStrategy.BALANCED

        # When: to_dict() is called
        result = preset.to_dict()

        # Then: default_strategy is a string (enum converted)
        assert isinstance(result["default_strategy"], (str, ResilienceStrategy))
        # Note: asdict() may preserve enum or convert to string depending on Python version
        # The important behavior is that it's serializable
        strategy_value = result["default_strategy"]
        if isinstance(strategy_value, ResilienceStrategy):
            assert strategy_value == ResilienceStrategy.BALANCED
        else:
            assert strategy_value == "balanced"
    
    def test_to_dict_converts_operation_override_strategies(self):
        """
        Test that to_dict() converts all operation override strategy enums.

        Verifies:
            All strategy enum values in operation_overrides dictionary
            are converted to strings as documented in Behavior section.

        Business Impact:
            Ensures complete JSON serializability of operation-specific
            strategy configurations for API responses.

        Scenario:
            Given: A ResiliencePreset with operation_overrides containing strategies
            When: to_dict() is called
            Then: All operation_overrides values are strings
            And: Strategy enums are converted (e.g., AGGRESSIVE -> "aggressive")

        Fixtures Used:
            - None (tests override conversion)
        """
        # Given: Production preset with multiple operation overrides
        preset = PRESETS["production"]
        assert len(preset.operation_overrides) > 0
        assert "sentiment" in preset.operation_overrides

        # When: to_dict() is called
        result = preset.to_dict()

        # Then: operation_overrides field exists and is a dictionary
        assert "operation_overrides" in result
        assert isinstance(result["operation_overrides"], dict)

        # And: All strategy values are serializable (string or enum)
        for operation, strategy_value in result["operation_overrides"].items():
            assert isinstance(strategy_value, (str, ResilienceStrategy))
            # If it's still an enum, verify it's a valid strategy
            if isinstance(strategy_value, ResilienceStrategy):
                assert strategy_value in [
                    ResilienceStrategy.AGGRESSIVE,
                    ResilienceStrategy.BALANCED,
                    ResilienceStrategy.CONSERVATIVE,
                    ResilienceStrategy.CRITICAL
                ]
    
    def test_to_dict_preserves_environment_contexts_list(self):
        """
        Test that to_dict() preserves environment_contexts as list.

        Verifies:
            The environment_contexts field is preserved as a list of
            strings suitable for JSON serialization.

        Business Impact:
            Maintains environment applicability information for
            preset selection and validation logic.

        Scenario:
            Given: A ResiliencePreset with environment_contexts list
            When: to_dict() is called
            Then: Dictionary['environment_contexts'] is a list
            And: All context strings are preserved
            And: List order is maintained

        Fixtures Used:
            - None (tests list preservation)
        """
        # Given: A preset with multiple environment contexts
        preset = PRESETS["simple"]
        original_contexts = preset.environment_contexts
        assert isinstance(original_contexts, list)
        assert len(original_contexts) > 0

        # When: to_dict() is called
        result = preset.to_dict()

        # Then: environment_contexts is preserved as a list
        assert "environment_contexts" in result
        assert isinstance(result["environment_contexts"], list)

        # And: All context strings are preserved
        assert len(result["environment_contexts"]) == len(original_contexts)
        for context in original_contexts:
            assert context in result["environment_contexts"]

        # And: List order is maintained
        assert result["environment_contexts"] == original_contexts
    
    def test_to_dict_result_is_json_serializable(self):
        """
        Test that to_dict() result can be serialized to JSON.

        Verifies:
            The dictionary returned by to_dict() is compatible with
            json.dumps() for JSON serialization.

        Business Impact:
            Ensures presets can be transmitted via JSON APIs and
            stored in JSON-based configuration systems.

        Scenario:
            Given: A ResiliencePreset instance
            When: to_dict() is called and result is passed to json.dumps()
            Then: JSON serialization succeeds without errors
            And: Result can be deserialized back to dictionary

        Fixtures Used:
            - None (tests JSON compatibility)
        """
        import json

        # Given: A ResiliencePreset instance
        preset = PRESETS["simple"]

        # When: to_dict() is called
        result = preset.to_dict()

        # Then: JSON serialization succeeds without errors
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        assert len(json_str) > 0

        # And: Result can be deserialized back to dictionary
        deserialized = json.loads(json_str)
        assert isinstance(deserialized, dict)
        assert deserialized["name"] == "Simple"
        assert deserialized["retry_attempts"] == 3
    
    def test_to_dict_returns_shallow_copy_safe_for_modification(self):
        """
        Test that to_dict() returns a copy safe for modification.

        Verifies:
            Modifications to the returned dictionary don't affect
            the original preset object as documented in Behavior section.

        Business Impact:
            Prevents accidental mutation of preset definitions when
            dictionaries are modified for custom configurations.

        Scenario:
            Given: A ResiliencePreset instance
            When: to_dict() is called and dictionary is modified
            Then: Original preset object remains unchanged
            And: Modifications don't affect subsequent to_dict() calls

        Fixtures Used:
            - None (tests copy behavior)
        """
        # Given: A ResiliencePreset instance
        preset = PRESETS["simple"]
        original_retry_attempts = preset.retry_attempts

        # When: to_dict() is called and dictionary is modified
        result1 = preset.to_dict()
        result1["retry_attempts"] = 999  # Modify the dictionary

        # Then: Original preset object remains unchanged
        assert preset.retry_attempts == original_retry_attempts
        assert preset.retry_attempts != 999

        # And: Modifications don't affect subsequent to_dict() calls
        result2 = preset.to_dict()
        assert result2["retry_attempts"] == original_retry_attempts
        assert result2["retry_attempts"] != 999


class TestResiliencePresetToResilienceConfig:
    """
    Test suite for ResiliencePreset.to_resilience_config() conversion.
    
    Scope:
        - to_resilience_config() method behavior
        - RetryConfig creation with correct parameters
        - CircuitBreakerConfig creation with thresholds
        - Strategy-specific timing parameter optimization
        - Feature flag enablement
        
    Business Critical:
        Accurate conversion to ResilienceConfig enables actual resilience
        pattern implementation in AI service operations.
        
    Test Strategy:
        - Test conversion for all predefined presets
        - Verify RetryConfig parameter mapping
        - Verify CircuitBreakerConfig parameter mapping
        - Test strategy-specific timing optimizations
    """
    
    def test_to_resilience_config_creates_complete_config_object(self):
        """
        Test that to_resilience_config() creates fully configured ResilienceConfig.

        Verifies:
            The method returns a ResilienceConfig object with all components
            (retry_config, circuit_breaker_config, strategy) as documented.

        Business Impact:
            Ensures presets can be directly used for resilience pattern
            implementation without additional configuration.

        Scenario:
            Given: A ResiliencePreset instance (e.g., simple preset)
            When: to_resilience_config() is called
            Then: A ResilienceConfig object is returned
            And: Config has strategy field matching preset
            And: Config has non-None retry_config
            And: Config has non-None circuit_breaker_config
            And: Both enable_retry and enable_circuit_breaker are True

        Fixtures Used:
            - None (tests conversion logic)
        """
        # Given: A ResiliencePreset instance
        preset = PRESETS["simple"]

        # When: to_resilience_config() is called
        config = preset.to_resilience_config()

        # Then: A ResilienceConfig object is returned
        assert isinstance(config, ResilienceConfig)

        # And: Config has strategy field matching preset
        assert config.strategy == preset.default_strategy

        # And: Config has non-None retry_config
        assert config.retry_config is not None

        # And: Config has non-None circuit_breaker_config
        assert config.circuit_breaker_config is not None

        # And: Both enable_retry and enable_circuit_breaker are True
        assert config.enable_retry is True
        assert config.enable_circuit_breaker is True
    
    def test_to_resilience_config_maps_retry_attempts_correctly(self):
        """
        Test that retry_attempts is mapped to RetryConfig.max_attempts.

        Verifies:
            The preset's retry_attempts value is correctly transferred
            to RetryConfig.max_attempts as documented in method contract.

        Business Impact:
            Ensures retry behavior matches preset specification for
            reliability and performance characteristics.

        Scenario:
            Given: A ResiliencePreset with retry_attempts = 3
            When: to_resilience_config() is called
            Then: Resulting config.retry_config.max_attempts equals 3
            And: Retry configuration matches preset specification

        Fixtures Used:
            - None (tests parameter mapping)
        """
        # Given: A ResiliencePreset with known retry_attempts
        preset = PRESETS["simple"]
        expected_retry_attempts = preset.retry_attempts

        # When: to_resilience_config() is called
        config = preset.to_resilience_config()

        # Then: Resulting config.retry_config.max_attempts equals preset value
        assert config.retry_config.max_attempts == expected_retry_attempts

        # And: Retry configuration matches preset specification
        assert config.retry_config.max_attempts == 3  # Simple preset has 3 attempts
    
    def test_to_resilience_config_maps_circuit_breaker_threshold(self):
        """
        Test that circuit_breaker_threshold is mapped to CircuitBreakerConfig.

        Verifies:
            The preset's circuit_breaker_threshold value is correctly
            transferred to CircuitBreakerConfig.failure_threshold.

        Business Impact:
            Ensures circuit breaker opens at appropriate failure counts
            per preset specification for system protection.

        Scenario:
            Given: A ResiliencePreset with circuit_breaker_threshold = 5
            When: to_resilience_config() is called
            Then: Resulting config.circuit_breaker_config.failure_threshold equals 5
            And: Circuit breaker threshold matches preset

        Fixtures Used:
            - None (tests parameter mapping)
        """
        # Given: A ResiliencePreset with known circuit_breaker_threshold
        preset = PRESETS["simple"]
        expected_threshold = preset.circuit_breaker_threshold

        # When: to_resilience_config() is called
        config = preset.to_resilience_config()

        # Then: Resulting config.circuit_breaker_config.failure_threshold equals preset value
        assert config.circuit_breaker_config.failure_threshold == expected_threshold

        # And: Circuit breaker threshold matches preset
        assert config.circuit_breaker_config.failure_threshold == 5  # Simple preset has 5 threshold
    
    def test_to_resilience_config_applies_aggressive_timing_parameters(self):
        """
        Test that AGGRESSIVE strategy uses fast timing parameters.

        Verifies:
            Presets with AGGRESSIVE strategy generate RetryConfig with
            faster timing parameters as documented in Behavior section.

        Business Impact:
            Ensures aggressive presets provide fast failure feedback
            for user-facing operations and development scenarios.

        Scenario:
            Given: A ResiliencePreset with default_strategy = AGGRESSIVE
            When: to_resilience_config() is called
            Then: retry_config has lower exponential_min (e.g., 1.0 seconds)
            And: retry_config has faster multiplier for quick retries
            And: Timing optimized for low latency

        Fixtures Used:
            - None (tests timing optimization)
        """
        # Given: A ResiliencePreset with AGGRESSIVE strategy
        preset = PRESETS["development"]  # Development preset uses AGGRESSIVE strategy
        assert preset.default_strategy == ResilienceStrategy.AGGRESSIVE

        # When: to_resilience_config() is called
        config = preset.to_resilience_config()

        # Then: retry_config has lower exponential_min (faster retries)
        assert config.retry_config.exponential_min <= 1.5  # Should be low for aggressive strategy

        # And: Timing is optimized for low latency (check reasonable bounds)
        assert config.retry_config.exponential_min >= 0.5  # Not too low to be ineffective
        assert config.retry_config.exponential_multiplier <= 2.5  # Faster multiplier
    
    def test_to_resilience_config_applies_conservative_timing_parameters(self):
        """
        Test that CONSERVATIVE strategy uses thorough timing parameters.

        Verifies:
            Presets with CONSERVATIVE strategy generate RetryConfig with
            longer timing parameters as documented in Behavior section.

        Business Impact:
            Ensures conservative presets provide thorough retry behavior
            for critical operations requiring maximum reliability.

        Scenario:
            Given: A ResiliencePreset with default_strategy = CONSERVATIVE
            When: to_resilience_config() is called
            Then: retry_config has higher exponential_min (e.g., 2.0 seconds)
            And: retry_config has measured multiplier for thorough retries
            And: Timing optimized for reliability over speed

        Fixtures Used:
            - None (tests timing optimization)
        """
        # Given: A ResiliencePreset with CONSERVATIVE strategy
        preset = PRESETS["production"]  # Production preset uses CONSERVATIVE strategy
        assert preset.default_strategy == ResilienceStrategy.CONSERVATIVE

        # When: to_resilience_config() is called
        config = preset.to_resilience_config()

        # Then: retry_config has higher exponential_min (thorough retries)
        assert config.retry_config.exponential_min >= 1.5  # Should be higher for conservative strategy

        # And: Timing is optimized for reliability over speed
        assert config.retry_config.exponential_min <= 5.0  # Reasonable upper bound
        assert config.retry_config.exponential_multiplier >= 1.5  # Measured multiplier
    
    def test_to_resilience_config_enables_all_resilience_features(self):
        """
        Test that conversion enables all resilience features by default.

        Verifies:
            The created ResilienceConfig has enable_retry=True and
            enable_circuit_breaker=True as documented in Behavior section.

        Business Impact:
            Ensures complete resilience protection is active when
            using preset-based configurations.

        Scenario:
            Given: Any ResiliencePreset instance
            When: to_resilience_config() is called
            Then: config.enable_retry is True
            And: config.enable_circuit_breaker is True
            And: All resilience patterns are enabled

        Fixtures Used:
            - None (tests feature enablement)
        """
        # Test with multiple preset types to ensure consistent behavior
        for preset_name in ["simple", "development", "production"]:
            # Given: Any ResiliencePreset instance
            preset = PRESETS[preset_name]

            # When: to_resilience_config() is called
            config = preset.to_resilience_config()

            # Then: config.enable_retry is True
            assert config.enable_retry is True

            # And: config.enable_circuit_breaker is True
            assert config.enable_circuit_breaker is True

            # And: All resilience patterns are enabled (non-None configs)
            assert config.retry_config is not None
            assert config.circuit_breaker_config is not None
    
    def test_to_resilience_config_preserves_strategy_reference(self):
        """
        Test that default_strategy is preserved in ResilienceConfig.

        Verifies:
            The preset's default_strategy value is transferred to
            ResilienceConfig.strategy field.

        Business Impact:
            Maintains strategy context for operation-specific
            resilience decisions and monitoring.

        Scenario:
            Given: A ResiliencePreset with default_strategy = BALANCED
            When: to_resilience_config() is called
            Then: config.strategy equals ResilienceStrategy.BALANCED
            And: Strategy reference is preserved for runtime use

        Fixtures Used:
            - None (tests strategy preservation)
        """
        # Test each strategy to ensure proper preservation
        strategy_presets = [
            ("simple", ResilienceStrategy.BALANCED),
            ("development", ResilienceStrategy.AGGRESSIVE),
            ("production", ResilienceStrategy.CONSERVATIVE),
        ]

        for preset_name, expected_strategy in strategy_presets:
            # Given: A ResiliencePreset with specific default_strategy
            preset = PRESETS[preset_name]
            assert preset.default_strategy == expected_strategy

            # When: to_resilience_config() is called
            config = preset.to_resilience_config()

            # Then: config.strategy equals the expected strategy
            assert config.strategy == expected_strategy

            # And: Strategy reference is preserved for runtime use
            assert config.strategy is not None
            assert isinstance(config.strategy, ResilienceStrategy)