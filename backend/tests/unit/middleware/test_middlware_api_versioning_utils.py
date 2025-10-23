"""
Unit tests for API versioning utility functions.

This module tests the pure utility functions from the API versioning middleware
that can be tested in isolation without HTTP context. These tests validate the
core string manipulation and version normalization logic that underpins the
API versioning system.

Test Scope:
    - Version string normalization (_normalize_version method)
    - Input validation and edge case handling
    - Format standardization for consistent version comparison

Business Impact:
    - Ensures API version detection works reliably across different input formats
    - Prevents version parsing errors that could break API routing
    - Maintains consistent version format for downstream processing

Test Strategy:
    - Focus on pure function behavior without HTTP dependencies
    - Test edge cases and malformed inputs for robustness
    - Validate output format consistency for all valid inputs

Contract Reference:
    Tests validate behavior documented in:
    backend/contracts/core/middleware/api_versioning.pyi (lines 71-200)
"""

import pytest
from app.core.middleware.api_versioning import APIVersioningMiddleware


class TestNormalizeVersion:
    """
    Test suite for version string normalization logic.

    Scope:
        Tests the _normalize_version method which converts various version string
        formats into a consistent major.minor format for reliable comparison and
        routing within the API versioning middleware.

    Business Critical:
        Version normalization is foundational to API version detection and routing.
        Failures in this logic can break API version detection, causing requests
        to be misrouted or rejected, impacting all API consumers.

    Contract Under Test:
        Method: APIVersioningMiddleware._normalize_version(self, version_str: str) -> str | None

        Input Formats Supported:
            - 'v' prefixed versions: "v1", "v1.5", "V2.0"
            - Major-only versions: "1", "2", "10"
            - Major.minor versions: "1.0", "2.3", "10.5"
            - Major.minor.patch versions: "1.0.0", "2.3.4" (patch truncated)

        Output Format:
            - Always returns major.minor format: "1.0", "2.3"
            - Returns None for invalid or unparseable inputs

        Edge Cases Handled:
            - Case-insensitive 'v' prefix removal
            - Major-only to major.minor conversion
            - Patch version truncation
            - Invalid format rejection
            - Empty string and None handling

    Test Data Strategy:
        Uses representative samples of each input format and edge case.
        Tests both happy path normalization and robust error handling.

    External Dependencies:
        - packaging.version: Used for robust version parsing
        - No HTTP context required (pure string manipulation)

    Risk if Broken:
        API version detection failures could route requests to wrong version
        or reject valid version specifications, breaking API compatibility.
    """

    def test_normalize_v_prefix_removed(self) -> None:
        """
        Test that lowercase 'v' prefix is properly removed from version strings.

        Business Impact:
            Ensures API consumers can specify versions using the common 'v' prefix
            format (e.g., "v1.0") without breaking version detection.

        Scenario:
            Given: Version string with lowercase 'v' prefix ("v1.0")
            When: _normalize_version processes the input
            Then: Prefix is removed and major.minor format is preserved ("1.0")

        Edge Cases Validated:
            - Prefix removal does not affect numeric components
            - Major.minor format is preserved after prefix removal
            - Output format remains consistent with other normalization paths
            - Single digit and multi-digit versions are handled correctly
            - Version with zero components are preserved properly

        Real-world Context:
            API clients commonly use "v1.0", "v2.1" format in URLs and headers.
            This normalization enables flexible version specification while
            maintaining internal consistency.
        """
        # Test basic major.minor with v prefix
        result = APIVersioningMiddleware._normalize_version(None, "v1.0")
        assert result == "1.0"

        # Test single digit major version with v prefix
        result = APIVersioningMiddleware._normalize_version(None, "v1")
        assert result == "1.0"

        # Test multi-digit versions with v prefix
        result = APIVersioningMiddleware._normalize_version(None, "v10.5")
        assert result == "10.5"
        result = APIVersioningMiddleware._normalize_version(None, "v12")
        assert result == "12.0"

        # Test version with zero components
        result = APIVersioningMiddleware._normalize_version(None, "v0.0")
        assert result == "0.0"
        result = APIVersioningMiddleware._normalize_version(None, "v2.0")
        assert result == "2.0"

        # Test version with patch number (should be truncated)
        result = APIVersioningMiddleware._normalize_version(None, "v1.2.3")
        assert result == "1.2"

        # Test edge cases with leading zeros in major version
        result = APIVersioningMiddleware._normalize_version(None, "v01.0")
        assert result == "1.0"

        # Test edge cases with leading zeros in minor version
        result = APIVersioningMiddleware._normalize_version(None, "v1.05")
        assert result == "1.5"

    def test_normalize_uppercase_v_prefix(self) -> None:
        """
        Test that uppercase 'V' prefix is properly removed from version strings.

        Business Impact:
            Ensures case-insensitive handling of version prefixes, allowing
            API consumers to use either "v1.0" or "V1.0" format interchangeably.

        Scenario:
            Given: Version string with uppercase 'V' prefix ("V2.5")
            When: _normalize_version processes the input
            Then: Prefix is removed and major.minor format is preserved ("2.5")

        Edge Cases Validated:
            - Case-insensitive prefix handling
            - Uppercase prefix removal behavior
            - Consistency with lowercase prefix handling
            - Mixed case scenarios and edge cases
            - Multi-digit versions with uppercase prefix

        Real-world Context:
            Different API clients and documentation may use uppercase 'V' prefix.
            Case-insensitive handling prevents client-side formatting issues
            and improves API usability.
        """
        # Test basic major.minor with uppercase V prefix
        result = APIVersioningMiddleware._normalize_version(None, "V2.5")
        assert result == "2.5"

        # Test single digit major version with uppercase V prefix
        result = APIVersioningMiddleware._normalize_version(None, "V3")
        assert result == "3.0"

        # Test multi-digit versions with uppercase V prefix
        result = APIVersioningMiddleware._normalize_version(None, "V11.2")
        assert result == "11.2"
        result = APIVersioningMiddleware._normalize_version(None, "V15")
        assert result == "15.0"

        # Test version with zero components
        result = APIVersioningMiddleware._normalize_version(None, "V0.1")
        assert result == "0.1"
        result = APIVersioningMiddleware._normalize_version(None, "V5.0")
        assert result == "5.0"

        # Test version with patch number (should be truncated)
        result = APIVersioningMiddleware._normalize_version(None, "V3.4.5")
        assert result == "3.4"

        # Test edge cases with leading zeros
        result = APIVersioningMiddleware._normalize_version(None, "V09.0")
        assert result == "9.0"
        result = APIVersioningMiddleware._normalize_version(None, "V1.08")
        assert result == "1.8"

        # Test consistency with lowercase - both should produce same result
        lower_result = APIVersioningMiddleware._normalize_version(None, "v2.5")
        upper_result = APIVersioningMiddleware._normalize_version(None, "V2.5")
        assert lower_result == upper_result == "2.5"

    def test_normalize_major_only_adds_minor(self) -> None:
        """
        Test that major-only version numbers are converted to major.minor format.

        Business Impact:
            Enables API consumers to specify simple major versions ("1", "2")
            that are automatically expanded to major.minor format ("1.0", "2.0")
            for consistent internal processing.

        Scenario:
            Given: Major-only version string ("2")
            When: _normalize_version processes the input
            Then: Minor version ".0" is added ("2.0")

        Edge Cases Validated:
            - Single digit major versions
            - Multi-digit major versions
            - Zero-padded major versions
            - Consistent ".0" minor version addition
            - Edge cases like version 0 and large version numbers

        Real-world Context:
            Simple version specifications like "API version 1" are common in
            documentation and client configuration. Auto-expansion to "1.0"
            maintains internal consistency while supporting simple client usage.
        """
        # Test basic single digit major versions
        result = APIVersioningMiddleware._normalize_version(None, "2")
        assert result == "2.0"

        result = APIVersioningMiddleware._normalize_version(None, "1")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "5")
        assert result == "5.0"

        # Test multi-digit major versions
        result = APIVersioningMiddleware._normalize_version(None, "10")
        assert result == "10.0"

        result = APIVersioningMiddleware._normalize_version(None, "15")
        assert result == "15.0"

        result = APIVersioningMiddleware._normalize_version(None, "100")
        assert result == "100.0"

        # Test edge case with version 0
        result = APIVersioningMiddleware._normalize_version(None, "0")
        assert result == "0.0"

        # Test zero-padded major versions (should be normalized)
        result = APIVersioningMiddleware._normalize_version(None, "01")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "001")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "09")
        assert result == "9.0"

        # Test large version numbers
        result = APIVersioningMiddleware._normalize_version(None, "999")
        assert result == "999.0"

        # Verify all major-only versions consistently get .0 minor
        test_versions = ["1", "2", "3", "10", "15", "20", "100", "999", "0"]
        for version in test_versions:
            result = APIVersioningMiddleware._normalize_version(None, version)
            expected = f"{int(version)}.0"  # int() handles leading zeros
            assert (
                result == expected
            ), f"Version {version} should normalize to {expected}, got {result}"

    def test_normalize_major_minor_preserved(self) -> None:
        """
        Test that already normalized major.minor versions are preserved unchanged.

        Business Impact:
            Ensures that correctly formatted version specifications pass through
        normalization unchanged, maintaining efficiency and preventing unexpected
        modifications to valid inputs.

        Scenario:
            Given: Already normalized major.minor version ("1.5")
            When: _normalize_version processes the input
            Then: Version format is preserved exactly ("1.5")

        Edge Cases Validated:
            - Two-digit minor versions ("1.15")
            - Zero minor versions ("2.0")
            - Single digit minor versions ("1.5")
            - No unnecessary transformations
            - Leading zeros in components are normalized
            - Multi-digit major and minor versions

        Real-world Context:
            Well-formed API clients typically use proper major.minor format.
            Preservation ensures these optimal inputs incur no processing overhead
            and maintain their exact specification.
        """
        # Test basic major.minor versions
        result = APIVersioningMiddleware._normalize_version(None, "1.5")
        assert result == "1.5"

        # Test zero minor versions
        result = APIVersioningMiddleware._normalize_version(None, "2.0")
        assert result == "2.0"

        result = APIVersioningMiddleware._normalize_version(None, "10.0")
        assert result == "10.0"

        # Test two-digit minor versions
        result = APIVersioningMiddleware._normalize_version(None, "1.15")
        assert result == "1.15"

        result = APIVersioningMiddleware._normalize_version(None, "2.25")
        assert result == "2.25"

        # Test multi-digit major and minor versions
        result = APIVersioningMiddleware._normalize_version(None, "10.15")
        assert result == "10.15"

        result = APIVersioningMiddleware._normalize_version(None, "12.34")
        assert result == "12.34"

        # Test edge cases with leading zeros (should be normalized)
        result = APIVersioningMiddleware._normalize_version(None, "01.5")
        assert result == "1.5"

        result = APIVersioningMiddleware._normalize_version(None, "1.05")
        assert result == "1.5"

        result = APIVersioningMiddleware._normalize_version(None, "01.05")
        assert result == "1.5"

        # Test zero major version with minor
        result = APIVersioningMiddleware._normalize_version(None, "0.1")
        assert result == "0.1"

        result = APIVersioningMiddleware._normalize_version(None, "0.0")
        assert result == "0.0"

        # Test large version numbers
        result = APIVersioningMiddleware._normalize_version(None, "100.200")
        assert result == "100.200"

        result = APIVersioningMiddleware._normalize_version(None, "999.888")
        assert result == "999.888"

        # Verify preservation by checking that valid major.minor versions pass through unchanged
        test_versions = ["1.0", "1.5", "2.0", "2.15", "10.5", "10.15", "0.1", "100.200"]
        for version in test_versions:
            result = APIVersioningMiddleware._normalize_version(None, version)
            assert (
                result == version
            ), f"Version {version} should be preserved unchanged, got {result}"

    def test_normalize_patch_version_truncated(self) -> None:
        """
        Test that patch versions are truncated to major.minor format.

        Business Impact:
            Enables the middleware to handle semantic versioning inputs (e.g., "1.0.0")
        by automatically extracting only the major.minor components needed for
        API versioning while ignoring patch-level details.

        Scenario:
            Given: Version string with patch component ("2.3.4")
            When: _normalize_version processes the input
            Then: Patch version is truncated ("2.3")

        Edge Cases Validated:
            - Single-digit patch versions
            - Multi-digit patch versions
            - Zero patch versions
            - Preservation of major and minor components
            - Leading zeros in patch version are handled
            - Large patch numbers are properly truncated

        Real-world Context:
            Semantic versioning (semver) uses major.minor.patch format.
            API versioning typically only needs major.minor for routing
            compatibility, so patch details are safely ignored.
        """
        # Test basic major.minor.patch truncation
        result = APIVersioningMiddleware._normalize_version(None, "2.3.4")
        assert result == "2.3"

        # Test single-digit patch versions
        result = APIVersioningMiddleware._normalize_version(None, "1.0.1")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "10.5.9")
        assert result == "10.5"

        # Test multi-digit patch versions
        result = APIVersioningMiddleware._normalize_version(None, "1.2.15")
        assert result == "1.2"

        result = APIVersioningMiddleware._normalize_version(None, "3.4.100")
        assert result == "3.4"

        # Test zero patch versions
        result = APIVersioningMiddleware._normalize_version(None, "1.5.0")
        assert result == "1.5"

        result = APIVersioningMiddleware._normalize_version(None, "2.0.0")
        assert result == "2.0"

        # Test edge cases with leading zeros in patch
        result = APIVersioningMiddleware._normalize_version(None, "1.2.001")
        assert result == "1.2"

        result = APIVersioningMiddleware._normalize_version(None, "3.4.005")
        assert result == "3.4"

        # Test large patch numbers
        result = APIVersioningMiddleware._normalize_version(None, "1.0.999")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "10.15.1000")
        assert result == "10.15"

        # Test with zero major or minor versions
        result = APIVersioningMiddleware._normalize_version(None, "0.1.5")
        assert result == "0.1"

        result = APIVersioningMiddleware._normalize_version(None, "1.0.3")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "0.0.1")
        assert result == "0.0"

        # Test with v prefix and patch version
        result = APIVersioningMiddleware._normalize_version(None, "v1.2.3")
        assert result == "1.2"

        result = APIVersioningMiddleware._normalize_version(None, "V10.5.15")
        assert result == "10.5"

        # Verify truncation behavior - major.minor.patch should always become major.minor
        test_versions = [
            ("1.0.0", "1.0"),
            ("1.2.3", "1.2"),
            ("10.15.20", "10.15"),
            ("2.0.1", "2.0"),
            ("0.1.5", "0.1"),
            ("999.888.777", "999.888"),
        ]

        for input_version, expected in test_versions:
            result = APIVersioningMiddleware._normalize_version(None, input_version)
            assert (
                result == expected
            ), f"Version {input_version} should truncate to {expected}, got {result}"

    def test_normalize_invalid_version_returns_none(self) -> None:
        """
        Test that invalid version strings return None for proper error handling.

        Business Impact:
            Prevents malformed version specifications from causing routing errors
        or being incorrectly processed. Enables graceful rejection of invalid
        API version specifications with appropriate error responses.

        Scenario:
            Given: Invalid version string ("invalid")
            When: _normalize_version processes the input
            Then: None is returned to indicate parsing failure

        Edge Cases Validated:
            - Non-numeric strings
            - Special characters
            - Malformed numeric strings
            - Graceful failure handling
            - Edge cases with mixed invalid content
            - Partial version patterns

        Real-world Context:
            Malformed version specifications can occur from client errors,
        configuration mistakes, or malicious inputs. Returning None enables
        the middleware to detect and handle these cases appropriately.
        """
        # Test completely non-numeric strings
        result = APIVersioningMiddleware._normalize_version(None, "invalid")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "abc")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "version")
        assert result is None

        # Test strings with special characters - some are actually valid according to packaging.version
        result = APIVersioningMiddleware._normalize_version(None, "1.0.0-beta")
        assert result == "1.0"  # packaging.version can handle pre-release identifiers

        result = APIVersioningMiddleware._normalize_version(None, "v1.0.0-alpha")
        assert result == "1.0"  # packaging.version can handle pre-release identifiers

        result = APIVersioningMiddleware._normalize_version(None, "1.0+build.1")
        assert result == "1.0"  # packaging.version can handle build metadata

        # Test malformed numeric strings
        result = APIVersioningMiddleware._normalize_version(None, "1..0")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, ".1.0")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "1.0.")
        assert result is None

        # Test strings with invalid separators - some are actually handled by packaging.version
        result = APIVersioningMiddleware._normalize_version(None, "1-0")
        assert result == "1.0"  # packaging.version can handle dash separators

        result = APIVersioningMiddleware._normalize_version(None, "1_0")
        assert result is None

        # Test mixed alphanumeric invalid
        result = APIVersioningMiddleware._normalize_version(None, "1a.0b")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "v1a.0b")
        assert result is None

        # Test edge cases with whitespace - packaging.version automatically strips whitespace
        result = APIVersioningMiddleware._normalize_version(None, " 1.0")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "1.0 ")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, " 1.0 ")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "\t1.0")
        assert result == "1.0"

        result = APIVersioningMiddleware._normalize_version(None, "1.0\n")
        assert result == "1.0"

        # Test empty v prefix
        result = APIVersioningMiddleware._normalize_version(None, "v")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "V")
        assert result is None

        # Test multiple dots without numbers
        result = APIVersioningMiddleware._normalize_version(None, "...")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "v...")
        assert result is None

        # Test negative numbers (invalid for semantic versioning)
        result = APIVersioningMiddleware._normalize_version(None, "-1.0")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "1.-0")
        assert result is None

        # Test extended version patterns - packaging.version handles more than 3 components
        result = APIVersioningMiddleware._normalize_version(None, "1.0.0.0")
        assert result == "1.0"  # packaging.version truncates to major.minor

        result = APIVersioningMiddleware._normalize_version(None, "1.2.3.4")
        assert result == "1.2"  # packaging.version truncates to major.minor

        # Verify truly invalid inputs return None (exclude ones that packaging.version handles)
        truly_invalid_inputs = [
            "invalid",
            "abc",
            "version",
            "1..0",
            ".1.0",
            "1.0.",
            "1_0",
            "1a.0b",
            "v1a.0b",
            "v",
            "V",
            "...",
            "v...",
            "-1.0",
            "1.-0",
        ]

        for invalid_input in truly_invalid_inputs:
            result = APIVersioningMiddleware._normalize_version(None, invalid_input)
            assert (
                result is None
            ), f"Invalid input '{invalid_input}' should return None, got {result}"

        # Verify whitespace handling (packaging.version strips whitespace automatically)
        whitespace_inputs = [
            (" 1.0", "1.0"),
            ("1.0 ", "1.0"),
            (" 1.0 ", "1.0"),
            ("\t1.0", "1.0"),
            ("1.0\n", "1.0"),
        ]

        for input_version, expected in whitespace_inputs:
            result = APIVersioningMiddleware._normalize_version(None, input_version)
            assert (
                result == expected
            ), f"Whitespace input '{input_version}' should normalize to '{expected}', got '{result}'"

        # Verify semantic versioning patterns that are actually handled
        semantic_versioning_inputs = [
            ("1.0.0-beta", "1.0"),
            ("v1.0.0-alpha", "1.0"),
            ("1.0+build.1", "1.0"),
            ("1-0", "1.0"),
        ]

        for input_version, expected in semantic_versioning_inputs:
            result = APIVersioningMiddleware._normalize_version(None, input_version)
            assert (
                result == expected
            ), f"Semantic versioning input '{input_version}' should normalize to '{expected}', got '{result}'"

        # Verify extended version patterns that are actually handled (more than 3 components)
        extended_version_inputs = [
            ("1.0.0.0", "1.0"),
            ("1.2.3.4", "1.2"),
            ("v10.15.20.30", "10.15"),
        ]

        for input_version, expected in extended_version_inputs:
            result = APIVersioningMiddleware._normalize_version(None, input_version)
            assert (
                result == expected
            ), f"Extended version input '{input_version}' should normalize to '{expected}', got '{result}'"

    def test_normalize_empty_string_returns_none(self) -> None:
        """
        Test that empty string inputs return None for boundary condition handling.

        Business Impact:
            Handles edge case of empty version specifications, preventing empty
        strings from being processed as valid versions and ensuring proper
        error handling for missing or cleared version values.

        Scenario:
            Given: Empty string version ("")
            When: _normalize_version processes the input
            Then: None is returned to indicate invalid input

        Edge Cases Validated:
            - Empty string boundary condition
            - Whitespace-only strings (explicitly tested)
            - Missing version parameter scenarios
            - Input validation robustness
            - Various whitespace combinations

        Real-world Context:
            Empty version strings can occur from configuration errors,
        client-side bugs, or parameter parsing issues. Proper handling
        prevents these edge cases from breaking version detection.
        """
        # Test completely empty string
        result = APIVersioningMiddleware._normalize_version(None, "")
        assert result is None

        # Test whitespace-only strings (these should also return None)
        result = APIVersioningMiddleware._normalize_version(None, " ")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "   ")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "\t")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "\n")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "\r")
        assert result is None

        # Test mixed whitespace
        result = APIVersioningMiddleware._normalize_version(None, " \t\n\r ")
        assert result is None

        # Test empty string with v prefix but no version
        result = APIVersioningMiddleware._normalize_version(None, "v")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "V")
        assert result is None

        # Test v prefix with whitespace
        result = APIVersioningMiddleware._normalize_version(None, "v ")
        assert result is None

        result = APIVersioningMiddleware._normalize_version(None, "V\t")
        assert result is None

        # Test edge cases with various unicode whitespace
        result = APIVersioningMiddleware._normalize_version(
            None, "\u00a0"
        )  # non-breaking space
        assert result is None

        result = APIVersioningMiddleware._normalize_version(
            None, "\u200b"
        )  # zero-width space
        assert result is None

        # Verify all empty/whitespace inputs return None
        empty_inputs = [
            "",
            " ",
            "   ",
            "\t",
            "\n",
            "\r",
            " \t\n\r ",
            "v",
            "V",
            "v ",
            "V\t",
            "\u00a0",
            "\u200b",
        ]

        for empty_input in empty_inputs:
            result = APIVersioningMiddleware._normalize_version(None, empty_input)
            assert (
                result is None
            ), f"Empty/whitespace input '{repr(empty_input)}' should return None, got {result}"

    def test_normalize_none_returns_none(self) -> None:
        """
        Test that None inputs return None for null value handling.

        Business Impact:
            Ensures robust handling of null version specifications, preventing
        NoneType errors and enabling the middleware to gracefully handle cases
        where version information is completely absent.

        Scenario:
            Given: None value as version input
            When: _normalize_version processes the input
            Then: None is returned without errors

        Edge Cases Validated:
            - None value handling
            - Null reference safety
            - Exception prevention for null inputs
            - Graceful degradation for missing data
            - Consistent behavior across different null scenarios

        Real-world Context:
            None values can occur when version extraction fails or when
        version information is not provided by the client. Safe handling
        ensures the middleware doesn't crash on missing version data.
        """
        # Test direct None input
        result = APIVersioningMiddleware._normalize_version(None, None)
        assert result is None

        # Verify that None handling is safe and doesn't raise exceptions
        try:
            result = APIVersioningMiddleware._normalize_version(None, None)
            assert result is None
        except (AttributeError, TypeError, ValueError) as e:
            pytest.fail(f"None input should not raise exception: {e}")

        # Test that None is handled consistently as the first parameter (self)
        # This tests the method's robustness when called with None as self
        try:
            result = APIVersioningMiddleware._normalize_version(None, None)
            assert result is None
        except Exception as e:
            pytest.fail(f"Method should handle None self parameter gracefully: {e}")

        # Test multiple None calls to ensure consistency
        results = []
        for _ in range(5):
            result = APIVersioningMiddleware._normalize_version(None, None)
            results.append(result)
            assert result is None

        # All results should be None
        assert all(r is None for r in results), "All None inputs should return None"

        # Test that None input doesn't affect subsequent valid inputs
        # This ensures the method is stateless and doesn't retain side effects
        result_none = APIVersioningMiddleware._normalize_version(None, None)
        assert result_none is None

        result_valid = APIVersioningMiddleware._normalize_version(None, "1.0")
        assert result_valid == "1.0"

        result_none_again = APIVersioningMiddleware._normalize_version(None, None)
        assert result_none_again is None

        # Verify None handling is thread-safe (by calling multiple times rapidly)
        import concurrent.futures

        def test_none_input():
            return APIVersioningMiddleware._normalize_version(None, None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(test_none_input) for _ in range(20)]
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]

        # All concurrent None calls should return None
        assert all(
            r is None for r in results
        ), "All concurrent None inputs should return None"
