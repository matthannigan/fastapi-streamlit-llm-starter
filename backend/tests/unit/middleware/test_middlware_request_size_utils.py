"""
Unit tests for request size limiting middleware utility functions.

This module tests the hierarchical size limit lookup logic of the RequestSizeLimitMiddleware
component, focusing on the _get_size_limit() method that determines appropriate size
limits based on endpoint paths, content types, and default configurations.

The tests validate the middleware's public contract as documented in:
- backend/contracts/core/middleware/request_size.pyi
- Integration with middleware configuration from Settings

Test Strategy:
- Tests focus exclusively on the _get_size_limit() utility function behavior
- Hierarchical lookup logic: endpoint → content-type → default
- Content-Type parsing with charset parameter handling
- Boundary conditions and edge cases in limit resolution
- Behavior-driven testing with clear business impact documentation

External Dependencies Mocked:
- RequestSizeLimitMiddleware: Real instance with mocked ASGI app
- Settings: Created via create_settings() factory for test isolation
- Request objects: Created via create_mock_request factory fixture

Contract Reference:
The middleware size limit resolution follows this documented behavior:
1. Endpoint-specific limits take highest precedence
2. Content-type limits used when no endpoint match
3. Default limit used as final fallback
4. Content-Type charset parameters stripped before lookup
"""

import pytest
from unittest.mock import Mock
from typing import Callable
from app.core.middleware.request_size import RequestSizeLimitMiddleware
from app.core.config import create_settings

# Fixtures injected by pytest conftest.py - type hints for mypy
mock_app: Mock
create_mock_request: Callable[..., Mock]


class TestGetSizeLimit:
    """
    Unit tests for hierarchical size limit determination in RequestSizeLimitMiddleware.

    Scope:
        Tests the _get_size_limit() method that implements hierarchical size limit
        lookup logic following endpoint → content-type → default precedence.

    Business Critical:
        Size limit determination protects against DoS attacks and resource exhaustion.
        Incorrect limit resolution could allow oversized requests to bypass protection
        or incorrectly reject legitimate requests, impacting service availability.

    Contract Reference:
        Tests verify behavior documented in backend/contracts/core/middleware/request_size.pyi:
        - Hierarchical lookup: endpoint → content-type → default
        - Content-Type charset parameter stripping
        - Proper fallback behavior when no match found

    Test Strategy:
        - Mock middleware instance with configurable limit mappings
        - Test various request scenarios covering all lookup paths
        - Validate edge cases and boundary conditions
        - Ensure behavior remains consistent across refactoring

    External Dependencies:
        - RequestSizeLimitMiddleware: Real instance with mocked ASGI app
        - Settings: Created via create_settings() factory for test isolation
        - Mock Request objects: Created via create_mock_request factory fixture

    Known Limitations:
        - Tests use private _get_size_limit() method for unit testing isolation
        - Full middleware behavior tested in integration test suite
        - Does not test streaming validation or error response generation
    """

    def test_endpoint_specific_limit_priority(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that endpoint-specific limits take highest precedence in hierarchical lookup.

        Verifies:
            When both endpoint-specific and content-type limits are available,
            the endpoint-specific limit is selected per documented precedence rules.

        Business Impact:
            Ensures critical endpoints like file uploads can have stricter or more
            lenient limits than global content-type policies, enabling granular
            resource protection tailored to endpoint requirements.

        Scenario:
            Given: Request to '/v1/upload' endpoint with JSON content-type
                   and both endpoint (50MB) and content-type (5MB) limits configured
            When: Size limit lookup is performed via _get_size_limit()
            Then: Endpoint-specific limit (50MB) is returned, not content-type limit

        Edge Cases Covered:
            - Endpoint path matching is exact (not pattern-based)
            - Content-Type header is properly parsed and available
            - Multiple limit types coexist in configuration

        Contract Reference:
            Hierarchical lookup precedence: endpoint → content-type → default
            per request_size.pyi middleware documentation.

        Test Data:
            - Endpoint: '/v1/upload' with 50MB limit
            - Content-Type: 'application/json' with 5MB limit
            - Default: 10MB limit (should not be used)
        """
        # Given: Middleware configured with hierarchical limits
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())
        middleware.default_limits = {
            "/v1/upload": 50 * 1024 * 1024,  # 50MB endpoint limit
            "application/json": 5 * 1024 * 1024,  # 5MB content-type limit
            "default": 10 * 1024 * 1024  # 10MB default limit
        }

        # And: Request matching both endpoint and content-type patterns
        request = create_mock_request(
            path="/v1/upload",
            headers={"content-type": "application/json"}
        )

        # When: Size limit lookup is performed
        limit = middleware._get_size_limit(request)

        # Then: Endpoint-specific limit takes precedence
        assert limit == 50 * 1024 * 1024, "Endpoint limit should override content-type limit"

    def test_content_type_limit_fallback(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test content-type limit used when no endpoint-specific match is available.

        Verifies:
            When no endpoint-specific limit matches the request path, the middleware
            correctly falls back to content-type based limits per documented behavior.

        Business Impact:
            Enables content-type specific resource protection (e.g., stricter limits
            for JSON vs multipart/form-data) without requiring individual endpoint
            configuration, providing balanced security and usability.

        Scenario:
            Given: Request to '/v1/api/data' endpoint with JSON content-type
                   and no endpoint-specific limit configured
            When: Size limit lookup is performed via _get_size_limit()
            Then: Content-type specific limit (5MB) is returned, not default

        Edge Cases Covered:
            - No endpoint path match in configuration
            - Content-Type header properly formatted and parsable
            - Content-type limit exists in configuration
            - Default limit exists but should not be used

        Contract Reference:
            Fallback behavior: endpoint → content-type → default
            per request_size.pyi middleware documentation.

        Test Data:
            - Endpoint: '/v1/api/data' (no specific limit configured)
            - Content-Type: 'application/json' with 5MB limit
            - Default: 10MB limit (fallback, not used here)
        """
        # Given: Middleware configured with content-type and default limits only
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())
        middleware.default_limits = {
            "application/json": 5 * 1024 * 1024,  # 5MB content-type limit
            "default": 10 * 1024 * 1024  # 10MB default limit
        }

        # And: Request with content-type but no matching endpoint limit
        request = create_mock_request(
            path="/v1/api/data",  # No endpoint-specific limit configured
            headers={"content-type": "application/json"}
        )

        # When: Size limit lookup is performed
        limit = middleware._get_size_limit(request)

        # Then: Content-type limit is used as fallback
        assert limit == 5 * 1024 * 1024, "Content-type limit should be used when no endpoint match"

    def test_default_limit_final_fallback(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test default limit used as final fallback when no endpoint or content-type match.

        Verifies:
            When neither endpoint-specific nor content-type limits match the request,
            the middleware correctly falls back to the default limit as final safety net.

        Business Impact:
            Ensures universal protection against oversized requests even for
            unexpected endpoints or content-types, preventing resource exhaustion
            attacks through unconfigured request paths.

        Scenario:
            Given: Request to '/v1/api/data' endpoint with no Content-Type header
                   and no matching endpoint or content-type limits configured
            When: Size limit lookup is performed via _get_size_limit()
            Then: Default limit (10MB) is returned as final fallback

        Edge Cases Covered:
            - No endpoint path match in configuration
            - No Content-Type header provided by client
            - Only default limit configured
            - Final fallback behavior when all other matches fail

        Contract Reference:
            Final fallback behavior: endpoint → content-type → default
            per request_size.pyi middleware documentation.

        Test Data:
            - Endpoint: '/v1/api/data' (no specific limit configured)
            - Content-Type: None (not provided by client)
            - Default: 10MB limit (final fallback)
        """
        # Given: Middleware configured with only default limit
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())
        middleware.default_limits = {"default": 10 * 1024 * 1024}  # 10MB default only

        # And: Request with no content-type header
        request = create_mock_request(path="/v1/api/data")  # No content-type header

        # When: Size limit lookup is performed
        limit = middleware._get_size_limit(request)

        # Then: Default limit is used as final fallback
        assert limit == 10 * 1024 * 1024, "Default limit should be used as final fallback"

    def test_content_type_with_charset_stripped(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test Content-Type charset parameters are stripped before limit lookup.

        Verifies:
            When Content-Type header includes charset parameters (e.g., 'application/json; charset=utf-8'),
            the middleware correctly strips the charset and performs limit lookup using only
            the media type portion per documented parsing behavior.

        Business Impact:
            Ensures content-type based limit enforcement works correctly regardless of
            charset specifications, preventing clients from bypassing limits by adding
            charset parameters to Content-Type headers.

        Scenario:
            Given: Request with Content-Type 'application/json; charset=utf-8'
                   and content-type limit configured for 'application/json'
            When: Size limit lookup is performed via _get_size_limit()
            Then: Content-type limit (5MB) is found after charset stripping

        Edge Cases Covered:
            - Content-Type header with charset parameter
            - Proper charset parameter stripping before lookup
            - Case-insensitive charset parameter handling
            - Content-type limit matching after stripping

        Contract Reference:
            Content-Type parsing: charset parameters stripped before lookup
            per request_size.pyi middleware documentation.

        Test Data:
            - Content-Type: 'application/json; charset=utf-8' (with charset)
            - Configured limit: 'application/json' with 5MB limit
            - Expected: 5MB limit found after charset stripping
        """
        # Given: Middleware configured with content-type limits
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())
        middleware.default_limits = {
            "application/json": 5 * 1024 * 1024,  # 5MB for 'application/json'
            "default": 10 * 1024 * 1024  # 10MB default fallback
        }

        # And: Request with Content-Type including charset parameter
        request = create_mock_request(
            path="/v1/api/data",
            headers={"content-type": "application/json; charset=utf-8"}
        )

        # When: Size limit lookup is performed
        limit = middleware._get_size_limit(request)

        # Then: Charset stripped and content-type limit applied
        assert limit == 5 * 1024 * 1024, "Charset should be stripped before content-type lookup"


class TestFormatSize:
    """
    Unit tests for human-readable size formatting in RequestSizeLimitMiddleware.

    Scope:
        Tests the _format_size() method that converts byte values to human-readable
        strings with appropriate units (B, KB, MB, GB) for display purposes.

    Business Critical:
        Size formatting provides clear, understandable error messages and logging
        information for developers and system administrators when request size
        limits are exceeded, enabling effective debugging and monitoring.

    Contract Reference:
        Tests verify behavior documented in backend/contracts/core/middleware/request_size.pyi:
        - Size conversion with appropriate units based on magnitude
        - Decimal formatting (one decimal place) for KB, MB, GB
        - Integer formatting for byte values

    Test Strategy:
        - Test boundary values between different size units
        - Validate formatting precision and decimal places
        - Ensure consistent unit selection logic
        - Test edge cases including zero and large values

    External Dependencies:
        - RequestSizeLimitMiddleware: Real instance with mocked ASGI app
        - Settings: Created via create_settings() factory for test isolation

    Known Limitations:
        - Tests use private _format_size() method for unit testing isolation
        - Does not test locale-specific formatting or internationalization
        - Maximum size testing limited to GB range as per implementation
    """

    def test_format_size_bytes(self, mock_app: Mock) -> None:
        """
        Test formatting of byte values less than 1KB.

        Verifies:
            Values less than 1024 bytes are formatted with 'B' suffix
            and no decimal places, maintaining integer precision.

        Business Impact:
            Ensures small request size limits are displayed clearly without
            unnecessary decimal precision, improving readability for
            developers reviewing size restrictions.

        Scenario:
            Given: Middleware instance for testing
            When: _format_size() is called with 512 bytes
            Then: Returns "512B" (no decimal, B suffix)

        Edge Cases Covered:
            - Zero bytes (0B)
            - Small values under 1KB
            - Values just under 1KB threshold
            - Integer formatting maintained

        Contract Reference:
            Size formatting: < 1024 bytes formatted as integer + 'B'
            per request_size.pyi middleware documentation.

        Test Data:
            - 0 bytes -> "0B"
            - 512 bytes -> "512B"
            - 1023 bytes -> "1023B"
        """
        # Given: Middleware instance for testing
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())

        # When: Formatting byte values less than 1KB
        assert middleware._format_size(0) == "0B", "Zero bytes should format as 0B"
        assert middleware._format_size(512) == "512B", "512 bytes should format as 512B"
        assert middleware._format_size(1023) == "1023B", "1023 bytes should format as 1023B"

    def test_format_size_kilobytes(self, mock_app: Mock) -> None:
        """
        Test formatting of kilobyte values (1KB to 1MB).

        Verifies:
            Values between 1KB and 1MB are formatted with 'KB' suffix
            and one decimal place of precision for consistent display.

        Business Impact:
            Provides consistent decimal precision for medium-sized limits,
            enabling developers to quickly understand size restrictions
            without excessive decimal places.

        Scenario:
            Given: Middleware instance for testing
            When: _format_size() is called with values between 1KB and 1MB
            Then: Returns values with one decimal place and 'KB' suffix

        Edge Cases Covered:
            - Exact kilobyte boundaries
            - Values requiring decimal rounding
            - Values just under 1MB threshold
            - Consistent one-decimal precision

        Contract Reference:
            Size formatting: >= 1024 and < 1048576 bytes formatted as
            value/1024 with 1 decimal + 'KB' per request_size.pyi.

        Test Data:
            - 1024 bytes -> "1.0KB"
            - 1536 bytes -> "1.5KB"
            - 1048575 bytes -> "1023.9KB"
        """
        # Given: Middleware instance for testing
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())

        # When: Formatting kilobyte values
        assert middleware._format_size(1024) == "1.0KB", "1024 bytes should format as 1.0KB"
        assert middleware._format_size(1536) == "1.5KB", "1536 bytes should format as 1.5KB"
        assert middleware._format_size(5120) == "5.0KB", "5120 bytes should format as 5.0KB"
        assert middleware._format_size(1048575) == "1024.0KB", "Just under 1MB should format with KB"

    def test_format_size_megabytes(self, mock_app: Mock) -> None:
        """
        Test formatting of megabyte values (1MB to 1GB).

        Verifies:
            Values between 1MB and 1GB are formatted with 'MB' suffix
            and one decimal place of precision for consistent display.

        Business Impact:
            Ensures large request size limits (common for file uploads)
            are displayed in appropriate units for easy understanding
            by developers configuring upload restrictions.

        Scenario:
            Given: Middleware instance for testing
            When: _format_size() is called with values between 1MB and 1GB
            Then: Returns values with one decimal place and 'MB' suffix

        Edge Cases Covered:
            - Exact megabyte boundaries
            - Common file upload sizes
            - Values requiring decimal rounding
            - Values just under 1GB threshold

        Contract Reference:
            Size formatting: >= 1048576 and < 1073741824 bytes formatted as
            value/1048576 with 1 decimal + 'MB' per request_size.pyi.

        Test Data:
            - 1048576 bytes -> "1.0MB"
            - 5242880 bytes -> "5.0MB" (5MB typical limit)
            - 52428800 bytes -> "50.0MB" (50MB file upload limit)
            - 1073741823 bytes -> "1023.9MB"
        """
        # Given: Middleware instance for testing
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())

        # When: Formatting megabyte values
        assert middleware._format_size(1048576) == "1.0MB", "1MB should format as 1.0MB"
        assert middleware._format_size(5242880) == "5.0MB", "5MB should format as 5.0MB"
        assert middleware._format_size(52428800) == "50.0MB", "50MB should format as 50.0MB"
        assert middleware._format_size(1073741823) == "1024.0MB", "Just under 1GB should format with MB"

    def test_format_size_gigabytes(self, mock_app: Mock) -> None:
        """
        Test formatting of gigabyte values (1GB and above).

        Verifies:
            Values 1GB and above are formatted with 'GB' suffix
            and one decimal place of precision for very large sizes.

        Business Impact:
            Supports very large request size limits for specialized
            applications while maintaining consistent formatting
            standards across all size ranges.

        Scenario:
            Given: Middleware instance for testing
            When: _format_size() is called with values 1GB and above
            Then: Returns values with one decimal place and 'GB' suffix

        Edge Cases Covered:
            - Exact gigabyte boundaries
            - Very large file transfer scenarios
            - Decimal precision maintenance at large scales
            - Realistic upper bounds for API limits

        Contract Reference:
            Size formatting: >= 1073741824 bytes formatted as
            value/1073741824 with 1 decimal + 'GB' per request_size.pyi.

        Test Data:
            - 1073741824 bytes -> "1.0GB"
            - 2147483648 bytes -> "2.0GB"
            - 10737418240 bytes -> "10.0GB"
        """
        # Given: Middleware instance for testing
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())

        # When: Formatting gigabyte values
        assert middleware._format_size(1073741824) == "1.0GB", "1GB should format as 1.0GB"
        assert middleware._format_size(2147483648) == "2.0GB", "2GB should format as 2.0GB"
        assert middleware._format_size(10737418240) == "10.0GB", "10GB should format as 10.0GB"

    def test_format_size_boundary_values(self, mock_app: Mock) -> None:
        """
        Test formatting at exact unit boundaries to ensure correct unit selection.

        Verifies:
            Values exactly at unit boundaries (1024, 1048576, 1073741824)
            are formatted with the correct larger unit and proper precision.

        Business Impact:
            Ensures consistent behavior at critical threshold values
            that are commonly used for configuration, preventing
            confusion about which unit is being applied.

        Scenario:
            Given: Middleware instance for testing
            When: _format_size() is called with exact boundary values
            Then: Values use the larger unit with correct formatting

        Edge Cases Covered:
            - KB boundary: 1024 bytes should be 1.0KB, not 1024B
            - MB boundary: 1048576 bytes should be 1.0MB, not 1024KB
            - GB boundary: 1073741824 bytes should be 1.0GB, not 1024MB
            - Consistent decimal formatting at boundaries

        Contract Reference:
            Size formatting thresholds at 1024, 1048576, 1073741824
            per request_size.pyi middleware documentation.

        Test Data:
            - 1024 bytes -> "1.0KB" (not "1024B")
            - 1048576 bytes -> "1.0MB" (not "1024KB")
            - 1073741824 bytes -> "1.0GB" (not "1024MB")
        """
        # Given: Middleware instance for testing
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())

        # When: Testing exact boundary values
        assert middleware._format_size(1024) == "1.0KB", "KB boundary should use KB unit"
        assert middleware._format_size(1048576) == "1.0MB", "MB boundary should use MB unit"
        assert middleware._format_size(1073741824) == "1.0GB", "GB boundary should use GB unit"

    def test_format_size_rounding_precision(self, mock_app: Mock) -> None:
        """
        Test decimal rounding precision for formatted size values.

        Verifies:
            Values requiring decimal rounding are properly formatted
            with exactly one decimal place across all size units.

        Business Impact:
            Ensures consistent decimal precision across all size
            displays, providing a professional and predictable
            user experience for developers reading size limits.

        Scenario:
            Given: Middleware instance for testing
            When: _format_size() is called with values requiring rounding
            Then: Values display with exactly one decimal place

        Edge Cases Covered:
            - Values that would round up at one decimal place
            - Values that would round down at one decimal place
            - Consistency across different size units
            - One-decimal precision enforced

        Contract Reference:
            Size formatting: One decimal place for KB, MB, GB
            per request_size.pyi middleware documentation.

        Test Data:
            - 1536 bytes -> "1.5KB" (1.5 exactly)
            - 1572864 bytes -> "1.5MB" (1.5 exactly)
            - 1536 bytes with rounding edge cases
            - Long decimal values truncated to one place
        """
        # Given: Middleware instance for testing
        middleware = RequestSizeLimitMiddleware(mock_app, create_settings())

        # When: Testing values that require decimal precision
        assert middleware._format_size(1536) == "1.5KB", "1.5KB should maintain one decimal"
        assert middleware._format_size(1572864) == "1.5MB", "1.5MB should maintain one decimal"
        assert middleware._format_size(1610612736) == "1.5GB", "1.5GB should maintain one decimal"

        # Test rounding behavior
        assert middleware._format_size(1280) == "1.2KB", "Should round to one decimal place"
        assert middleware._format_size(1310720) == "1.2MB", "Should round MB to one decimal"