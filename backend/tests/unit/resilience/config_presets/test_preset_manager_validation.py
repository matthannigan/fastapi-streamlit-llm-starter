"""
Test suite for PresetManager preset validation functionality.

Verifies that the PresetManager correctly validates preset configurations
against defined rules and constraints.
"""

import pytest
from app.infrastructure.resilience.config_presets import (
    PresetManager,
    ResiliencePreset,
    ResilienceStrategy
)


class TestPresetManagerValidation:
    """
    Test suite for validate_preset() method behavior.
    
    Scope:
        - validate_preset() for valid preset configurations
        - Validation of retry_attempts boundaries
        - Validation of circuit_breaker_threshold boundaries
        - Validation of recovery_timeout boundaries
        - Validation of strategy enum values
        - Validation of operation_overrides structure
        
    Business Critical:
        Preset validation ensures only safe, well-formed configurations
        are accepted, preventing runtime errors and misconfigurations.
        
    Test Strategy:
        - Test validation of all predefined presets
        - Test boundary conditions for numeric parameters
        - Test validation of enum values
        - Test rejection of invalid configurations
    """
    
    def test_validate_preset_accepts_valid_simple_preset(self):
        """
        Test that validate_preset() accepts the predefined simple preset.

        Verifies:
            The validate_preset() method returns True for the well-formed
            'simple' preset as documented in method contract.

        Business Impact:
            Confirms baseline preset validation works correctly,
            ensuring fundamental configuration validation is reliable.

        Scenario:
            Given: An initialized PresetManager instance
            And: The predefined 'simple' preset object
            When: validate_preset(simple_preset) is called
            Then: Method returns True
            And: No validation errors are logged

        Fixtures Used:
            - None (tests validation logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: The predefined 'simple' preset object
        simple_preset = manager.get_preset("simple")

        # When: validate_preset(simple_preset) is called
        result = manager.validate_preset(simple_preset)

        # Then: Method returns True
        assert result is True
    
    def test_validate_preset_accepts_valid_development_preset(self):
        """
        Test that validate_preset() accepts the predefined development preset.

        Verifies:
            The validate_preset() method returns True for the 'development'
            preset with its aggressive strategy configuration.

        Business Impact:
            Ensures development-optimized presets pass validation,
            enabling proper fast-fail configurations.

        Scenario:
            Given: An initialized PresetManager instance
            And: The predefined 'development' preset object
            When: validate_preset(development_preset) is called
            Then: Method returns True
            And: Operation overrides are validated correctly

        Fixtures Used:
            - None (tests validation logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: The predefined 'development' preset object
        development_preset = manager.get_preset("development")

        # When: validate_preset(development_preset) is called
        result = manager.validate_preset(development_preset)

        # Then: Method returns True
        assert result is True
    
    def test_validate_preset_accepts_valid_production_preset(self):
        """
        Test that validate_preset() accepts the predefined production preset.

        Verifies:
            The validate_preset() method returns True for the 'production'
            preset with its conservative strategy and operation overrides.

        Business Impact:
            Ensures production-grade presets pass validation with
            all operation-specific strategy overrides.

        Scenario:
            Given: An initialized PresetManager instance
            And: The predefined 'production' preset object
            When: validate_preset(production_preset) is called
            Then: Method returns True
            And: Complex operation_overrides mapping is validated

        Fixtures Used:
            - None (tests validation logic)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: The predefined 'production' preset object
        production_preset = manager.get_preset("production")

        # When: validate_preset(production_preset) is called
        result = manager.validate_preset(production_preset)

        # Then: Method returns True
        assert result is True
    
    def test_validate_preset_rejects_negative_retry_attempts(self):
        """
        Test that validate_preset() rejects preset with negative retry_attempts.

        Verifies:
            The validate_preset() method returns False when retry_attempts
            is below the documented minimum (1) as per validation rules.

        Business Impact:
            Prevents invalid retry configurations that would cause
            runtime errors or unexpected behavior.

        Scenario:
            Given: An initialized PresetManager instance
            And: A custom preset with retry_attempts = -1
            When: validate_preset(invalid_preset) is called
            Then: Method returns False
            And: Validation rejects negative retry value

        Fixtures Used:
            - None (tests boundary validation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A custom preset with retry_attempts = -1
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Preset with negative retry attempts",
            retry_attempts=-1,  # Invalid: below minimum
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["testing"]
        )

        # When: validate_preset(invalid_preset) is called
        result = manager.validate_preset(invalid_preset)

        # Then: Method returns False
        assert result is False
    
    def test_validate_preset_rejects_excessive_retry_attempts(self):
        """
        Test that validate_preset() rejects preset with retry_attempts above maximum.

        Verifies:
            The validate_preset() method returns False when retry_attempts
            exceeds the documented maximum (10) as per validation rules.

        Business Impact:
            Prevents excessive retry configurations that could cause
            unacceptable latency or resource consumption.

        Scenario:
            Given: An initialized PresetManager instance
            And: A custom preset with retry_attempts = 100
            When: validate_preset(invalid_preset) is called
            Then: Method returns False
            And: Validation rejects excessive retry value

        Fixtures Used:
            - None (tests boundary validation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A custom preset with retry_attempts = 100
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Preset with excessive retry attempts",
            retry_attempts=100,  # Invalid: above maximum
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["testing"]
        )

        # When: validate_preset(invalid_preset) is called
        result = manager.validate_preset(invalid_preset)

        # Then: Method returns False
        assert result is False
    
    def test_validate_preset_rejects_invalid_circuit_breaker_threshold(self):
        """
        Test that validate_preset() rejects invalid circuit_breaker_threshold.

        Verifies:
            The validate_preset() method returns False when circuit_breaker_threshold
            is outside the documented range (1-20) as per validation rules.

        Business Impact:
            Prevents invalid circuit breaker configurations that could
            cause premature circuit opening or ineffective failure detection.

        Scenario:
            Given: An initialized PresetManager instance
            And: A custom preset with circuit_breaker_threshold = 0
            When: validate_preset(invalid_preset) is called
            Then: Method returns False
            And: Validation rejects invalid threshold

        Fixtures Used:
            - None (tests boundary validation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A custom preset with circuit_breaker_threshold = 0
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Preset with invalid circuit breaker threshold",
            retry_attempts=3,
            circuit_breaker_threshold=0,  # Invalid: below minimum
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["testing"]
        )

        # When: validate_preset(invalid_preset) is called
        result = manager.validate_preset(invalid_preset)

        # Then: Method returns False
        assert result is False
    
    def test_validate_preset_rejects_invalid_recovery_timeout(self):
        """
        Test that validate_preset() rejects invalid recovery_timeout values.

        Verifies:
            The validate_preset() method returns False when recovery_timeout
            is outside the documented range (10-300 seconds) as per validation rules.

        Business Impact:
            Prevents invalid timeout configurations that could cause
            excessively slow recovery or premature retry attempts.

        Scenario:
            Given: An initialized PresetManager instance
            And: A custom preset with recovery_timeout = 5 (below minimum)
            When: validate_preset(invalid_preset) is called
            Then: Method returns False
            And: Validation rejects timeout below minimum

        Fixtures Used:
            - None (tests boundary validation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A custom preset with recovery_timeout = 5 (below minimum)
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Preset with invalid recovery timeout",
            retry_attempts=3,
            circuit_breaker_threshold=5,
            recovery_timeout=5,  # Invalid: below minimum
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["testing"]
        )

        # When: validate_preset(invalid_preset) is called
        result = manager.validate_preset(invalid_preset)

        # Then: Method returns False
        assert result is False
    
    def test_validate_preset_validates_operation_overrides_strategies(self):
        """
        Test that validate_preset() validates all operation override strategy values.

        Verifies:
            The validate_preset() method checks that all values in
            operation_overrides are valid ResilienceStrategy enum values.

        Business Impact:
            Ensures operation-specific strategy overrides are valid,
            preventing runtime errors during operation-specific configuration.

        Scenario:
            Given: An initialized PresetManager instance
            And: A preset with operation_overrides containing invalid strategy
            When: validate_preset(invalid_preset) is called
            Then: Method returns False
            And: Validation rejects invalid override strategy

        Fixtures Used:
            - None (tests override validation)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A preset with operation_overrides containing invalid strategy
        # Create a valid preset first, then modify operation_overrides to include invalid strategy
        invalid_preset = ResiliencePreset(
            name="Invalid",
            description="Preset with invalid operation override strategy",
            retry_attempts=3,
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={"sentiment": ResilienceStrategy.AGGRESSIVE},
            environment_contexts=["testing"]
        )

        # Modify operation_overrides to include an invalid strategy value
        # This bypasses dataclass type checking to test validation logic
        invalid_preset.operation_overrides["sentiment"] = "invalid_strategy"  # type: ignore

        # When: validate_preset(invalid_preset) is called
        result = manager.validate_preset(invalid_preset)

        # Then: Method returns False
        assert result is False
    
    def test_validate_preset_accepts_empty_operation_overrides(self):
        """
        Test that validate_preset() accepts preset with empty operation_overrides.

        Verifies:
            The validate_preset() method accepts presets where
            operation_overrides is an empty dictionary (using default_strategy only).

        Business Impact:
            Enables simple preset configurations that use only default
            strategy without operation-specific overrides.

        Scenario:
            Given: An initialized PresetManager instance
            And: A valid preset with operation_overrides = {}
            When: validate_preset(preset) is called
            Then: Method returns True
            And: Empty overrides are considered valid

        Fixtures Used:
            - None (tests empty overrides handling)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A valid preset with operation_overrides = {}
        valid_preset = ResiliencePreset(
            name="Simple",
            description="Preset with empty operation overrides",
            retry_attempts=3,
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},  # Empty dictionary
            environment_contexts=["testing"]
        )

        # When: validate_preset(preset) is called
        result = manager.validate_preset(valid_preset)

        # Then: Method returns True
        assert result is True


class TestPresetManagerValidationEdgeCases:
    """
    Test suite for edge cases in preset validation.
    
    Scope:
        - Boundary value validation
        - Special character handling in preset names
        - Empty or None field validation
        - Complex operation_overrides structures
        
    Business Critical:
        Robust edge case handling prevents unexpected validation
        failures and ensures reliable configuration management.
    """
    
    def test_validate_preset_with_minimum_valid_retry_attempts(self):
        """
        Test that validate_preset() accepts retry_attempts at minimum boundary (1).

        Verifies:
            The validate_preset() method accepts retry_attempts = 1
            as the documented minimum valid value.

        Business Impact:
            Enables minimal retry configurations for fast-fail scenarios
            while maintaining valid configuration structure.

        Scenario:
            Given: An initialized PresetManager instance
            And: A preset with retry_attempts = 1 (documented minimum)
            When: validate_preset(preset) is called
            Then: Method returns True
            And: Minimum boundary is accepted

        Fixtures Used:
            - None (tests boundary condition)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A preset with retry_attempts = 1 (documented minimum)
        boundary_preset = ResiliencePreset(
            name="Boundary Min",
            description="Preset with minimum valid retry attempts",
            retry_attempts=1,  # Minimum valid value
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["testing"]
        )

        # When: validate_preset(preset) is called
        result = manager.validate_preset(boundary_preset)

        # Then: Method returns True
        assert result is True
    
    def test_validate_preset_with_maximum_valid_retry_attempts(self):
        """
        Test that validate_preset() accepts retry_attempts at maximum boundary (10).

        Verifies:
            The validate_preset() method accepts retry_attempts = 10
            as the documented maximum valid value.

        Business Impact:
            Enables maximum retry configurations for critical operations
            requiring highest reliability.

        Scenario:
            Given: An initialized PresetManager instance
            And: A preset with retry_attempts = 10 (documented maximum)
            When: validate_preset(preset) is called
            Then: Method returns True
            And: Maximum boundary is accepted

        Fixtures Used:
            - None (tests boundary condition)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A preset with retry_attempts = 10 (documented maximum)
        boundary_preset = ResiliencePreset(
            name="Boundary Max",
            description="Preset with maximum valid retry attempts",
            retry_attempts=10,  # Maximum valid value
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={},
            environment_contexts=["testing"]
        )

        # When: validate_preset(preset) is called
        result = manager.validate_preset(boundary_preset)

        # Then: Method returns True
        assert result is True
    
    def test_validate_preset_with_all_operation_types_in_overrides(self):
        """
        Test that validate_preset() handles operation_overrides with all operation types.

        Verifies:
            The validate_preset() method correctly validates operation_overrides
            containing all documented operation types (summarize, sentiment, etc.).

        Business Impact:
            Ensures comprehensive operation-specific configuration is
            properly validated for complex resilience requirements.

        Scenario:
            Given: An initialized PresetManager instance
            And: A preset with overrides for all operations (summarize, sentiment, qa, key_points, questions)
            When: validate_preset(preset) is called
            Then: Method returns True
            And: All operation overrides are validated correctly

        Fixtures Used:
            - None (tests comprehensive overrides)
        """
        # Given: An initialized PresetManager instance
        manager = PresetManager()

        # And: A preset with overrides for all operations (summarize, sentiment, qa, key_points, questions)
        comprehensive_preset = ResiliencePreset(
            name="Comprehensive",
            description="Preset with all operation types in overrides",
            retry_attempts=3,
            circuit_breaker_threshold=5,
            recovery_timeout=60,
            default_strategy=ResilienceStrategy.BALANCED,
            operation_overrides={
                "summarize": ResilienceStrategy.CONSERVATIVE,
                "sentiment": ResilienceStrategy.AGGRESSIVE,
                "qa": ResilienceStrategy.CRITICAL,
                "key_points": ResilienceStrategy.BALANCED,
                "questions": ResilienceStrategy.BALANCED
            },
            environment_contexts=["testing"]
        )

        # When: validate_preset(preset) is called
        result = manager.validate_preset(comprehensive_preset)

        # Then: Method returns True
        assert result is True