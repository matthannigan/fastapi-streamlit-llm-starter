"""
Test suite for ScannerType enumeration.

Tests verify ScannerType enum values and categorization according to the
public contract defined in config.pyi.
"""

import pytest
from app.infrastructure.security.llm.config import ScannerType


class TestScannerTypeEnumValues:
    """Test ScannerType enum member existence and values."""

    def test_scanner_type_has_input_scanner_members(self):
        """
        Test that ScannerType enum includes all documented input scanner types.

        Verifies:
            ScannerType enum contains PROMPT_INJECTION, TOXICITY_INPUT, PII_DETECTION,
            MALICIOUS_URL, and SUSPICIOUS_PATTERN per contract's Input Scanners section.

        Business Impact:
            Ensures all input security scanner types are available for configuration
            and security processing.

        Scenario:
            Given: ScannerType enum imported.
            When: Input scanner attributes are accessed.
            Then: All five input scanner types exist with correct values.

        Fixtures Used:
            None - tests enum definition directly.
        """
        # Verify all input scanner types exist as enum members
        assert hasattr(ScannerType, 'PROMPT_INJECTION')
        assert hasattr(ScannerType, 'TOXICITY_INPUT')
        assert hasattr(ScannerType, 'PII_DETECTION')
        assert hasattr(ScannerType, 'MALICIOUS_URL')
        assert hasattr(ScannerType, 'SUSPICIOUS_PATTERN')

        # Verify they have the expected string values
        assert ScannerType.PROMPT_INJECTION.value == "prompt_injection"
        assert ScannerType.TOXICITY_INPUT.value == "toxicity_input"
        assert ScannerType.PII_DETECTION.value == "pii_detection"
        assert ScannerType.MALICIOUS_URL.value == "malicious_url"
        assert ScannerType.SUSPICIOUS_PATTERN.value == "suspicious_pattern"

    def test_scanner_type_has_output_scanner_members(self):
        """
        Test that ScannerType enum includes all documented output scanner types.

        Verifies:
            ScannerType enum contains TOXICITY_OUTPUT, BIAS_DETECTION, HARMFUL_CONTENT,
            FACTUALITY_CHECK, and SENTIMENT_ANALYSIS per contract's Output Scanners section.

        Business Impact:
            Ensures all output safety scanner types are available for AI response
            validation and safety checking.

        Scenario:
            Given: ScannerType enum imported.
            When: Output scanner attributes are accessed.
            Then: All five output scanner types exist with correct values.

        Fixtures Used:
            None - tests enum definition directly.
        """
        # Verify all output scanner types exist as enum members
        assert hasattr(ScannerType, 'TOXICITY_OUTPUT')
        assert hasattr(ScannerType, 'BIAS_DETECTION')
        assert hasattr(ScannerType, 'HARMFUL_CONTENT')
        assert hasattr(ScannerType, 'FACTUALITY_CHECK')
        assert hasattr(ScannerType, 'SENTIMENT_ANALYSIS')

        # Verify they have the expected string values
        assert ScannerType.TOXICITY_OUTPUT.value == "toxicity_output"
        assert ScannerType.BIAS_DETECTION.value == "bias_detection"
        assert ScannerType.HARMFUL_CONTENT.value == "harmful_content"
        assert ScannerType.FACTUALITY_CHECK.value == "factuality_check"
        assert ScannerType.SENTIMENT_ANALYSIS.value == "sentiment_analysis"

    def test_scanner_type_enum_members_are_strings(self):
        """
        Test that ScannerType enum values are string type.

        Verifies:
            ScannerType inherits from str, Enum per contract's class declaration.

        Business Impact:
            Ensures scanner types can be used as strings for configuration keys
            and dictionary lookups.

        Scenario:
            Given: Any ScannerType enum member.
            When: Type is checked.
            Then: Member is instance of str.

        Fixtures Used:
            None - tests enum type characteristics.
        """
        # Test that enum members are instances of str
        assert isinstance(ScannerType.PROMPT_INJECTION, str)
        assert isinstance(ScannerType.TOXICITY_INPUT, str)
        assert isinstance(ScannerType.BIAS_DETECTION, str)
        assert isinstance(ScannerType.SENTIMENT_ANALYSIS, str)

        # Test that they can be used as strings directly
        # Note: ScannerType inherits from str, so the enum member itself is the string value
        scanner_str = ScannerType.PROMPT_INJECTION
        assert scanner_str == "prompt_injection"
        assert isinstance(scanner_str, str)

    def test_scanner_type_values_match_expected_strings(self):
        """
        Test that ScannerType enum string values match expected naming convention.

        Verifies:
            ScannerType string values use snake_case format (e.g., "prompt_injection")
            for consistency in configuration files.

        Business Impact:
            Ensures consistent scanner type naming across configuration files and
            code for maintainability.

        Scenario:
            Given: ScannerType enum members.
            When: String values are accessed.
            Then: Values use snake_case format matching member names.

        Fixtures Used:
            None - tests enum value formatting.
        """
        # Test that all enum values follow snake_case convention
        all_scanner_types = list(ScannerType)

        for scanner_type in all_scanner_types:
            value = scanner_type.value
            # Should be lowercase with underscores
            assert value.islower(), f"ScannerType value '{value}' should be lowercase"
            assert '_' in value or value.isalpha(), f"ScannerType value '{value}' should use snake_case format"

            # Should not contain uppercase letters, spaces, or special characters except underscores
            assert not any(c.isupper() for c in value), f"ScannerType value '{value}' should not contain uppercase letters"
            assert ' ' not in value, f"ScannerType value '{value}' should not contain spaces"
            assert all(c.isalnum() or c == '_' for c in value), f"ScannerType value '{value}' should only contain alphanumeric characters and underscores"


class TestScannerTypeUsagePatterns:
    """Test ScannerType enum usage in typical scenarios."""

    def test_scanner_type_can_be_used_as_dictionary_key(self, scanner_type):
        """
        Test that ScannerType members can serve as dictionary keys.

        Verifies:
            ScannerType enums are hashable and usable as dictionary keys for
            scanner configuration storage.

        Business Impact:
            Enables using scanner types as keys in configuration dictionaries
            for organized scanner settings.

        Scenario:
            Given: Dictionary with ScannerType keys.
            When: Values are stored and retrieved using ScannerType members.
            Then: Dictionary operations work correctly with enum keys.

        Fixtures Used:
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Use real ScannerType enum members as dictionary keys
        scanner_configs = {
            ScannerType.PROMPT_INJECTION: {"enabled": True, "threshold": 0.7},
            ScannerType.TOXICITY_INPUT: {"enabled": True, "threshold": 0.8},
            ScannerType.PII_DETECTION: {"enabled": False, "threshold": 0.6},
        }

        # Test that values can be retrieved using enum keys
        prompt_config = scanner_configs[ScannerType.PROMPT_INJECTION]
        assert prompt_config["enabled"] == True
        assert prompt_config["threshold"] == 0.7

        # Test that dictionary operations work correctly
        assert ScannerType.TOXICITY_INPUT in scanner_configs
        assert ScannerType.BIAS_DETECTION not in scanner_configs

        # Test adding new entries
        scanner_configs[ScannerType.BIAS_DETECTION] = {"enabled": True, "threshold": 0.9}
        assert ScannerType.BIAS_DETECTION in scanner_configs
        assert scanner_configs[ScannerType.BIAS_DETECTION]["threshold"] == 0.9

        # Test iteration over dictionary
        keys = list(scanner_configs.keys())
        assert ScannerType.PROMPT_INJECTION in keys
        assert ScannerType.TOXICITY_INPUT in keys

    def test_scanner_type_comparison_with_string_values(self, scanner_type):
        """
        Test that ScannerType members can be compared with string values.

        Verifies:
            ScannerType string inheritance allows comparison with plain strings
            for configuration parsing.

        Business Impact:
            Enables flexible configuration parsing where string values from YAML
            can be compared with enum members.

        Scenario:
            Given: ScannerType member and equivalent string value.
            When: Comparison is performed.
            Then: Enum member equals corresponding string value.

        Fixtures Used:
            - scanner_type: Fixture providing MockScannerType instance.
        """
        # Test that ScannerType enum members can be compared with their string values
        assert ScannerType.PROMPT_INJECTION == "prompt_injection"
        assert ScannerType.TOXICITY_INPUT == "toxicity_input"
        assert ScannerType.BIAS_DETECTION == "bias_detection"
        assert ScannerType.SENTIMENT_ANALYSIS == "sentiment_analysis"

        # Test that comparison works both ways
        assert "prompt_injection" == ScannerType.PROMPT_INJECTION
        assert "pii_detection" == ScannerType.PII_DETECTION

        # Test that different values are not equal
        assert ScannerType.PROMPT_INJECTION != "toxicity_input"
        assert ScannerType.BIAS_DETECTION != "prompt_injection"
        assert ScannerType.HARMFUL_CONTENT != "bias_detection"

        # Test that comparison works in conditional statements
        scanner_name = "toxicity_output"
        if scanner_name == ScannerType.TOXICITY_OUTPUT:
            comparison_works = True
        else:
            comparison_works = False
        assert comparison_works

        # Test with a list of scanner types for configuration parsing
        allowed_scanners = [ScannerType.PROMPT_INJECTION, ScannerType.TOXICITY_INPUT]
        config_scanner = "prompt_injection"
        assert config_scanner in allowed_scanners