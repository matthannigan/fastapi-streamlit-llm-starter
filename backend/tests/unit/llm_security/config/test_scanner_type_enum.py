"""
Test suite for ScannerType enumeration.

Tests verify ScannerType enum values and categorization according to the
public contract defined in config.pyi.
"""

import pytest


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
        pass

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
        pass

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
        pass

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
        pass


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
        pass

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
        pass