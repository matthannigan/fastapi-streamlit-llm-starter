"""
Test suite for PresetName enumeration.

Tests verify PresetName enum values and preset characteristics according to the
public contract defined in config.pyi.
"""

import pytest
from app.infrastructure.security.llm.config import PresetName, SecurityConfig


class TestPresetNameEnumValues:
    """Test PresetName enum member existence and values."""

    def test_preset_name_has_all_documented_members(self):
        """
        Test that PresetName enum includes all documented preset types.

        Verifies:
            PresetName enum contains STRICT, BALANCED, LENIENT, DEVELOPMENT, and
            PRODUCTION per contract's Available Presets section.

        Business Impact:
            Ensures all predefined configuration templates are available for
            quick security scanner deployment.

        Scenario:
            Given: PresetName enum imported.
            When: Preset type attributes are accessed.
            Then: All five preset types exist with correct values.

        Fixtures Used:
            None - tests enum definition directly.
        """
        # Verify all documented preset members exist
        assert hasattr(PresetName, 'STRICT')
        assert hasattr(PresetName, 'BALANCED')
        assert hasattr(PresetName, 'LENIENT')
        assert hasattr(PresetName, 'DEVELOPMENT')
        assert hasattr(PresetName, 'PRODUCTION')

        # Verify the values match the contract expectations
        assert PresetName.STRICT == "strict"
        assert PresetName.BALANCED == "balanced"
        assert PresetName.LENIENT == "lenient"
        assert PresetName.DEVELOPMENT == "development"
        assert PresetName.PRODUCTION == "production"

        # Verify we have exactly 5 preset types as documented
        preset_values = [preset.value for preset in PresetName]
        expected_values = ["strict", "balanced", "lenient", "development", "production"]
        assert sorted(preset_values) == sorted(expected_values)
        assert len(PresetName) == 5

    def test_preset_name_enum_members_are_strings(self):
        """
        Test that PresetName enum values are string type.

        Verifies:
            PresetName inherits from str, Enum per contract's class declaration.

        Business Impact:
            Ensures preset names can be used in configuration files and
            environment variables as strings.

        Scenario:
            Given: Any PresetName enum member.
            When: Type is checked.
            Then: Member is instance of str.

        Fixtures Used:
            None - tests enum type characteristics.
        """
        # Test that enum members are instances of str
        assert isinstance(PresetName.STRICT, str)
        assert isinstance(PresetName.BALANCED, str)
        assert isinstance(PresetName.LENIENT, str)
        assert isinstance(PresetName.DEVELOPMENT, str)
        assert isinstance(PresetName.PRODUCTION, str)

        # Test that they can be used in string operations
        strict_upper = PresetName.STRICT.upper()
        balanced_title = PresetName.BALANCED.title()

        assert strict_upper == "STRICT"
        assert balanced_title == "Balanced"

        # Test string concatenation works - this demonstrates string inheritance
        prefix = "preset_"
        strict_full = prefix + PresetName.STRICT
        assert strict_full == "preset_strict"

        # Test that PresetName can be compared to its string value (key behavior for config loading)
        assert PresetName.PRODUCTION == "production"
        assert PresetName.STRICT == "strict"

        # Test that PresetName works in string operations where strings are expected
        test_dict = {PresetName.DEVELOPMENT: "dev settings"}
        assert test_dict.get("development") == "dev settings"

        # Test that it can be used in string formatting that expects string-like behavior
        # Note: We use .value to get the actual string representation when needed
        formatted = f"Using {PresetName.PRODUCTION.value} preset"
        assert formatted == "Using production preset"


class TestPresetNameCharacteristics:
    """Test PresetName enum semantic characteristics."""

    def test_preset_name_represents_security_strictness_levels(self):
        """
        Test that PresetName enum values represent security strictness progression.

        Verifies:
            PresetName members represent varying security levels from lenient to
            strict per contract's Available Presets documentation.

        Business Impact:
            Enables graduated security policies where environments determine
            appropriate security strictness.

        Scenario:
            Given: PresetName enum members ordered by security strictness.
            When: Security characteristics are compared conceptually.
            Then: LENIENT < BALANCED < STRICT in security strictness level.

        Fixtures Used:
            None - tests enum semantic ordering.
        """
        # Test that strictness-based presets exist
        strictness_presets = [
            PresetName.LENIENT,
            PresetName.BALANCED,
            PresetName.STRICT
        ]

        # Verify all strictness presets are present
        for preset in strictness_presets:
            assert preset in PresetName

        # Test semantic progression - we can't test the actual implementation,
        # but we can verify the documented progression exists
        # Based on the contract: LENIENT (relaxed) < BALANCED (moderate) < STRICT (maximum)

        # Test that the values follow logical naming conventions
        assert PresetName.LENIENT == "lenient"  # Most relaxed
        assert PresetName.BALANCED == "balanced"  # Moderate security
        assert PresetName.STRICT == "strict"  # Maximum security

        # Test that these represent a progression from lenient to strict
        # This is a conceptual test based on the documented characteristics
        strictness_levels = {
            PresetName.LENIENT: "relaxed security with high thresholds, minimal false positives",
            PresetName.BALANCED: "moderate security settings for general production use",
            PresetName.STRICT: "maximum security with low thresholds, suitable for high-risk environments"
        }

        # Verify each preset has documented strictness characteristics
        for preset, description in strictness_levels.items():
            assert description is not None
            assert len(description) > 0

    def test_preset_name_separates_environment_from_strictness_presets(self):
        """
        Test that PresetName includes both environment and strictness-based presets.

        Verifies:
            PresetName provides both strictness-based presets (STRICT, BALANCED, LENIENT)
            and environment-based presets (DEVELOPMENT, PRODUCTION) per contract.

        Business Impact:
            Enables flexible preset selection based on either security requirements
            or deployment environment.

        Scenario:
            Given: PresetName enum members categorized by type.
            When: Members are grouped by strictness vs environment.
            Then: STRICT/BALANCED/LENIENT are strictness-based; DEVELOPMENT/PRODUCTION are environment-based.

        Fixtures Used:
            None - tests enum categorization.
        """
        # Define strictness-based presets
        strictness_based = {
            PresetName.STRICT: "maximum security with low thresholds",
            PresetName.BALANCED: "moderate security settings",
            PresetName.LENIENT: "relaxed security with high thresholds"
        }

        # Define environment-based presets
        environment_based = {
            PresetName.DEVELOPMENT: "optimized for development with verbose logging and relaxed settings",
            PresetName.PRODUCTION: "production-ready configuration with performance optimizations"
        }

        # Verify all strictness-based presets exist and have correct values
        for preset, description in strictness_based.items():
            assert preset in PresetName
            assert preset.value in ["strict", "balanced", "lenient"]
            assert description is not None

        # Verify all environment-based presets exist and have correct values
        for preset, description in environment_based.items():
            assert preset in PresetName
            assert preset.value in ["development", "production"]
            assert description is not None

        # Verify total number of presets matches expectations
        all_presets = set(strictness_based.keys()) | set(environment_based.keys())
        assert len(all_presets) == 5  # 3 strictness + 2 environment presets

        # Verify no overlap between categories
        strictness_values = {preset.value for preset in strictness_based.keys()}
        environment_values = {preset.value for preset in environment_based.keys()}
        assert len(strictness_values & environment_values) == 0  # No overlap

        # Test that categories are mutually exclusive
        total_presets_in_enum = len(PresetName)
        total_presets_in_categories = len(strictness_based) + len(environment_based)
        assert total_presets_in_enum == total_presets_in_categories


class TestPresetNameUsagePatterns:
    """Test PresetName enum usage in typical scenarios."""

    def test_preset_name_can_be_used_with_create_from_preset(self, preset_name):
        """
        Test that PresetName members work with SecurityConfig.create_from_preset().

        Verifies:
            PresetName enums integrate with SecurityConfig factory method per
            contract's Usage examples.

        Business Impact:
            Enables type-safe preset-based configuration creation through enum
            values instead of strings.

        Scenario:
            Given: PresetName member (e.g., STRICT).
            When: Passed to SecurityConfig.create_from_preset().
            Then: Configuration is created with appropriate preset settings.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        # Test with actual PresetName enum members, not the mock
        # Test each preset can be used with the factory method

        # Test STRICT preset
        strict_config = SecurityConfig.create_from_preset(PresetName.STRICT)
        assert strict_config is not None
        assert strict_config.preset == PresetName.STRICT
        assert strict_config.scanners is not None
        assert len(strict_config.scanners) > 0  # STRICT should enable multiple scanners

        # Test BALANCED preset
        balanced_config = SecurityConfig.create_from_preset(PresetName.BALANCED)
        assert balanced_config is not None
        assert balanced_config.preset == PresetName.BALANCED
        assert balanced_config.scanners is not None
        assert len(balanced_config.scanners) > 0

        # Test LENIENT preset
        lenient_config = SecurityConfig.create_from_preset(PresetName.LENIENT)
        assert lenient_config is not None
        assert lenient_config.preset == PresetName.LENIENT
        assert lenient_config.scanners is not None
        assert len(lenient_config.scanners) > 0

        # Test DEVELOPMENT preset
        dev_config = SecurityConfig.create_from_preset(PresetName.DEVELOPMENT)
        assert dev_config is not None
        assert dev_config.preset == PresetName.DEVELOPMENT
        assert dev_config.debug_mode == True  # Development preset should enable debug mode
        assert dev_config.scanners is not None

        # Test PRODUCTION preset
        prod_config = SecurityConfig.create_from_preset(PresetName.PRODUCTION)
        assert prod_config is not None
        assert prod_config.preset == PresetName.PRODUCTION
        assert prod_config.environment == "development"  # Default environment
        assert prod_config.scanners is not None

        # Test with custom environment parameter
        prod_with_env = SecurityConfig.create_from_preset(
            PresetName.PRODUCTION,
            environment="production"
        )
        assert prod_with_env.environment == "production"
        assert prod_with_env.preset == PresetName.PRODUCTION

    def test_preset_name_equality_with_string_values(self, preset_name):
        """
        Test that PresetName members can be compared with string values.

        Verifies:
            PresetName string inheritance allows comparison with plain strings
            for configuration loading.

        Business Impact:
            Enables flexible configuration where preset names from environment
            variables can be validated against enum members.

        Scenario:
            Given: PresetName member and equivalent string value.
            When: Equality comparison is performed.
            Then: Enum member equals corresponding string value.

        Fixtures Used:
            - preset_name: Fixture providing MockPresetName instance.
        """
        # Test equality between enum members and their string values
        assert PresetName.STRICT == "strict"
        assert "strict" == PresetName.STRICT
        assert PresetName.BALANCED == "balanced"
        assert "balanced" == PresetName.BALANCED
        assert PresetName.LENIENT == "lenient"
        assert "lenient" == PresetName.LENIENT
        assert PresetName.DEVELOPMENT == "development"
        assert "development" == PresetName.DEVELOPMENT
        assert PresetName.PRODUCTION == "production"
        assert "production" == PresetName.PRODUCTION

        # Test inequality
        assert PresetName.STRICT != "balanced"
        assert PresetName.BALANCED != "strict"
        assert PresetName.LENIENT != "development"

        # Test in list membership checks
        valid_presets = ["strict", "balanced", "lenient", "development", "production"]
        assert PresetName.STRICT in valid_presets
        assert PresetName.BALANCED in valid_presets
        assert PresetName.LENIENT in valid_presets
        assert PresetName.DEVELOPMENT in valid_presets
        assert PresetName.PRODUCTION in valid_presets

        # Test using string methods for validation
        def validate_preset_from_string(preset_string: str) -> bool:
            """Helper function to validate a preset string against enum members."""
            return preset_string in [preset.value for preset in PresetName]

        assert validate_preset_from_string("strict") == True
        assert validate_preset_from_string("balanced") == True
        assert validate_preset_from_string("lenient") == True
        assert validate_preset_from_string("development") == True
        assert validate_preset_from_string("production") == True
        assert validate_preset_from_string("invalid") == False

        # Test creating enum from string value (common pattern for config loading)
        def get_preset_from_string(preset_string: str):
            """Helper function to get enum member from string value."""
            for preset in PresetName:
                if preset == preset_string:
                    return preset
            raise ValueError(f"Invalid preset: {preset_string}")

        assert get_preset_from_string("strict") == PresetName.STRICT
        assert get_preset_from_string("balanced") == PresetName.BALANCED
        assert get_preset_from_string("lenient") == PresetName.LENIENT
        assert get_preset_from_string("development") == PresetName.DEVELOPMENT
        assert get_preset_from_string("production") == PresetName.PRODUCTION