import pytest
from unittest.mock import Mock
from app.core.config import create_settings
from app.core.middleware import validate_middleware_configuration


class TestValidateMiddlewareConfiguration:
    """
    Test suite for middleware configuration validation logic.

    Scope:
        - Configuration validation for all middleware components
        - Detection of misconfigurations and inconsistent settings
        - Warning generation for potentially problematic configurations
        - Validation of middleware interdependencies and requirements

    Business Critical:
        Configuration validation prevents runtime failures and security vulnerabilities
        that could result from improper middleware setup. Early detection of issues
        ensures system reliability and prevents production incidents.

    Test Strategy:
        - Unit tests focus on validate_middleware_configuration function behavior
        - Configuration scenarios cover common misconfigurations
        - Warning verification for each middleware component
        - Edge case testing for boundary conditions and invalid values

    Public Contract Under Test:
        validate_middleware_configuration(settings: Settings) -> List[str]

        Returns list of configuration warnings/errors:
        - Empty list indicates valid configuration
        - Non-empty list contains descriptive warning messages
        - Warnings highlight potential operational issues
        - Covers all middleware component interdependencies

    External Dependencies:
        - Settings object from app.core.config (real instance, not mocked)
        - No external service dependencies (pure validation function)

    Known Limitations:
        - Does not test actual middleware behavior with invalid configurations
        - Warning message content may evolve over time
        - Configuration validation is static (no runtime context)

    Related Tests:
        - Integration tests verify middleware behavior with various configurations
        - Component-specific middleware tests validate individual middleware setup
    """
    
    def test_rate_limiting_enabled_without_redis_url_warns(self) -> None:
        """
        Test that rate limiting enabled without Redis URL generates appropriate warning.

        Verifies:
            Configuration validation detects missing Redis URL for distributed rate limiting
            and generates warning about fallback to local cache behavior

        Business Impact:
            Prevents silent degradation of rate limiting functionality in production.
            Distributed rate limiting requires Redis for multi-instance coordination.
            Local fallback provides only single-instance protection.

        Scenario:
            Given: Rate limiting is enabled but Redis URL is not configured
            When: Configuration validation is performed
            Then: Warning is generated indicating local cache fallback usage

        Edge Cases Covered:
            - Missing Redis URL configuration
            - Rate limiting enabled flag check
            - Warning message clarity about fallback behavior

        Contract Reference:
            validate_middleware_configuration() should return warnings for
            configurations that may cause operational issues or reduced functionality
        """
        # Given: Rate limiting enabled without Redis URL
        settings = create_settings()
        settings.rate_limiting_enabled = True
        settings.redis_url = ""  # Empty string triggers "not configured" condition

        # When: Configuration validation is performed
        issues = validate_middleware_configuration(settings)

        # Then: Warning generated about local cache fallback
        assert len(issues) >= 1
        rate_limiting_issues = [issue for issue in issues if "rate limiting" in issue.lower() and "redis" in issue.lower()]
        assert len(rate_limiting_issues) >= 1
        assert "local cache" in rate_limiting_issues[0].lower()

        # Additional verification: Ensure the warning message is descriptive
        warning_message = rate_limiting_issues[0]
        assert "enabled" in warning_message.lower()
        assert "configured" in warning_message.lower()
    
    def test_invalid_compression_level_warns(self) -> None:
        """
        Test that invalid compression level generates appropriate validation warning.

        Verifies:
            Configuration validation detects compression level outside valid range
            and generates warning about potential compression failures

        Business Impact:
            Prevents runtime compression errors that could cause request failures.
            Invalid compression levels may cause middleware exceptions or unexpected
            behavior in response compression processing.

        Scenario:
            Given: Compression is enabled with invalid compression level (10, outside 1-9 range)
            When: Configuration validation is performed
            Then: Warning is generated indicating compression level issue

        Edge Cases Covered:
            - Compression level above maximum (9)
            - Compression level below minimum (1)
            - Compression middleware enabled flag interaction
            - Warning message specificity for compression configuration

        Contract Reference:
            validate_middleware_configuration() should validate numeric parameter
            ranges and warn about values that may cause component failures
        """
        # Since the Settings model has Pydantic validation (ge=1, le=9) that prevents
        # setting invalid compression_level values directly, we need to test the function
        # with a mock settings object that can have invalid values

        # Test Case 1: Mock settings with compression level above maximum (9)
        mock_settings = Mock()
        mock_settings.compression_enabled = True
        mock_settings.compression_level = 10  # Invalid (range: 1-9)
        # Set default values for other settings to prevent Mock objects in getattr calls
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.rate_limiting_enabled = False
        mock_settings.api_versioning_enabled = False
        mock_settings.default_api_version = "1.0"
        mock_settings.current_api_version = "1.0"
        mock_settings.max_request_size = 1024
        mock_settings.slow_request_threshold = 1000

        issues = validate_middleware_configuration(mock_settings)

        compression_issues = [issue for issue in issues if "compression level" in issue.lower()]
        assert len(compression_issues) >= 1
        assert "10" in compression_issues[0]
        assert "1-9" in compression_issues[0]

        # Test Case 2: Mock settings with compression level below minimum (1)
        mock_settings.compression_level = 0  # Invalid (range: 1-9)

        issues = validate_middleware_configuration(mock_settings)

        compression_issues = [issue for issue in issues if "compression level" in issue.lower()]
        assert len(compression_issues) >= 1
        assert "0" in compression_issues[0]
        assert "1-9" in compression_issues[0]

        # Test Case 3: Mock settings with valid compression level should not generate warning
        mock_settings.compression_level = 6  # Valid (range: 1-9)

        issues = validate_middleware_configuration(mock_settings)

        compression_issues = [issue for issue in issues if "compression level" in issue.lower()]
        assert len(compression_issues) == 0

        # Test Case 4: Mock settings with compression disabled should not validate level
        mock_settings.compression_enabled = False
        mock_settings.compression_level = 15  # Would be invalid if enabled

        issues = validate_middleware_configuration(mock_settings)

        compression_issues = [issue for issue in issues if "compression level" in issue.lower()]
        assert len(compression_issues) == 0

        # Test Case 5: Test with real Settings object (should always be valid due to Pydantic constraints)
        real_settings = create_settings()
        real_settings.compression_enabled = True
        # Settings model prevents setting invalid compression_level
        # This tests that valid real settings don't generate warnings
        issues = validate_middleware_configuration(real_settings)
        compression_issues = [issue for issue in issues if "compression level" in issue.lower()]
        assert len(compression_issues) == 0
    
    def test_api_versioning_missing_versions_warns(self) -> None:
        """
        Test that API versioning enabled without proper version configuration generates warning.

        Verifies:
            Configuration validation detects missing or invalid API version settings
            when API versioning middleware is enabled and generates appropriate warnings

        Business Impact:
            Prevents API versioning middleware failures that could break routing
            or cause inconsistent version handling across API endpoints.

        Scenario:
            Given: API versioning is enabled but default and current version are empty strings
            When: Configuration validation is performed
            Then: Warning is generated about improper version configuration

        Edge Cases Covered:
            - Missing default API version configuration
            - Missing current API version configuration
            - API versioning middleware enabled flag interaction
            - Version configuration completeness validation

        Contract Reference:
            validate_middleware_configuration() should verify that enabled middleware
            components have all required configuration parameters properly set
        """
        # Test Case 1: Both versions are empty strings
        settings = create_settings()
        settings.api_versioning_enabled = True
        settings.default_api_version = ""
        settings.current_api_version = ""

        issues = validate_middleware_configuration(settings)

        versioning_issues = [issue for issue in issues if "versioning" in issue.lower() and "configured" in issue.lower()]
        assert len(versioning_issues) >= 1
        assert "enabled" in versioning_issues[0].lower()

        # Test Case 2: Default version is empty, current version is set
        settings.default_api_version = ""
        settings.current_api_version = "1.0"

        issues = validate_middleware_configuration(settings)

        versioning_issues = [issue for issue in issues if "versioning" in issue.lower() and "configured" in issue.lower()]
        assert len(versioning_issues) >= 1

        # Test Case 3: Current version is empty, default version is set
        settings.default_api_version = "1.0"
        settings.current_api_version = ""

        issues = validate_middleware_configuration(settings)

        versioning_issues = [issue for issue in issues if "versioning" in issue.lower() and "configured" in issue.lower()]
        assert len(versioning_issues) >= 1

        # Test Case 4: Both versions are properly set - should not generate warning
        settings.default_api_version = "1.0"
        settings.current_api_version = "1.0"

        issues = validate_middleware_configuration(settings)

        versioning_issues = [issue for issue in issues if "versioning" in issue.lower() and "configured" in issue.lower()]
        assert len(versioning_issues) == 0

        # Test Case 5: API versioning disabled should not validate versions
        settings.api_versioning_enabled = False
        settings.default_api_version = ""
        settings.current_api_version = ""

        issues = validate_middleware_configuration(settings)

        versioning_issues = [issue for issue in issues if "versioning" in issue.lower() and "configured" in issue.lower()]
        assert len(versioning_issues) == 0
    
    def test_invalid_max_request_size_warns(self) -> None:
        """
        Test that invalid maximum request size generates appropriate validation warning.

        Verifies:
            Configuration validation detects invalid max_request_size values
            that could cause request processing failures or security issues

        Business Impact:
            Prevents request size middleware failures and potential security vulnerabilities.
            Invalid size limits could cause DoS vulnerabilities or legitimate request rejections.

        Scenario:
            Given: max_request_size is set to 0 (invalid - no requests allowed)
            When: Configuration validation is performed
            Then: Warning is generated about invalid request size configuration

        Edge Cases Covered:
            - Zero request size (blocks all requests)
            - Negative request size values
            - Request size boundary validation
            - Security implications of improper size limits

        Contract Reference:
            validate_middleware_configuration() should validate security-related
            parameters and warn about values that may cause security or operational issues
        """
        # Since the Settings model has Pydantic validation (gt=0) that prevents
        # setting invalid max_request_size values directly, we need to test the function
        # with a mock settings object that can have invalid values

        # Test Case 1: Mock settings with zero request size (blocks all requests)
        mock_settings = Mock()
        mock_settings.max_request_size = 0  # Invalid
        # Set default values for other settings to prevent Mock objects in getattr calls
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.rate_limiting_enabled = False
        mock_settings.compression_enabled = False
        mock_settings.compression_level = 6
        mock_settings.api_versioning_enabled = False
        mock_settings.default_api_version = "1.0"
        mock_settings.current_api_version = "1.0"
        mock_settings.slow_request_threshold = 1000

        issues = validate_middleware_configuration(mock_settings)

        size_issues = [issue for issue in issues if "max_request_size" in issue.lower()]
        assert len(size_issues) >= 1
        assert ">" in size_issues[0]  # Should mention "should be > 0"

        # Test Case 2: Mock settings with negative request size (physically impossible)
        mock_settings.max_request_size = -1000  # Invalid

        issues = validate_middleware_configuration(mock_settings)

        size_issues = [issue for issue in issues if "max_request_size" in issue.lower()]
        assert len(size_issues) >= 1
        assert ">" in size_issues[0]  # Should mention "should be > 0"

        # Test Case 3: Mock settings with valid request size should not generate warning
        mock_settings.max_request_size = 10 * 1024 * 1024  # 10MB, valid

        issues = validate_middleware_configuration(mock_settings)

        size_issues = [issue for issue in issues if "max_request_size" in issue.lower()]
        assert len(size_issues) == 0

        # Test Case 4: Mock settings with very small but positive size should be valid
        mock_settings.max_request_size = 1  # 1 byte, technically valid

        issues = validate_middleware_configuration(mock_settings)

        size_issues = [issue for issue in issues if "max_request_size" in issue.lower()]
        assert len(size_issues) == 0

        # Test Case 5: Test with real Settings object (should always be valid due to Pydantic constraints)
        real_settings = create_settings()
        # Settings model prevents setting invalid max_request_size
        # This tests that valid real settings don't generate warnings
        issues = validate_middleware_configuration(real_settings)
        size_issues = [issue for issue in issues if "max_request_size" in issue.lower()]
        assert len(size_issues) == 0
    
    def test_invalid_slow_request_threshold_warns(self) -> None:
        """
        Test that invalid slow request threshold generates appropriate validation warning.

        Verifies:
            Configuration validation detects invalid slow_request_threshold values
            that could cause performance monitoring issues or incorrect alerting

        Business Impact:
            Prevents performance monitoring middleware failures and ensures accurate
            slow request detection for operational visibility and alerting.

        Scenario:
            Given: slow_request_threshold is set to negative value (-100ms, invalid)
            When: Configuration validation is performed
            Then: Warning is generated about invalid performance threshold configuration

        Edge Cases Covered:
            - Negative threshold values (physically impossible)
            - Zero threshold values (too sensitive)
            - Performance monitoring parameter validation
            - Alerting system configuration integrity

        Contract Reference:
            validate_middleware_configuration() should validate performance monitoring
            parameters and warn about values that may cause incorrect operational metrics
        """
        # Since the Settings model has Pydantic validation (gt=0) that prevents
        # setting invalid slow_request_threshold values directly, we need to test the function
        # with a mock settings object that can have invalid values

        # Test Case 1: Mock settings with negative threshold value (physically impossible)
        mock_settings = Mock()
        mock_settings.slow_request_threshold = -100  # Invalid
        # Set default values for other settings to prevent Mock objects in getattr calls
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.rate_limiting_enabled = False
        mock_settings.compression_enabled = False
        mock_settings.compression_level = 6
        mock_settings.api_versioning_enabled = False
        mock_settings.default_api_version = "1.0"
        mock_settings.current_api_version = "1.0"
        mock_settings.max_request_size = 1024

        issues = validate_middleware_configuration(mock_settings)

        threshold_issues = [issue for issue in issues if "slow_request_threshold" in issue.lower()]
        assert len(threshold_issues) >= 1
        assert ">" in threshold_issues[0]  # Should mention "should be > 0"

        # Test Case 2: Mock settings with zero threshold value (too sensitive)
        mock_settings.slow_request_threshold = 0  # Invalid

        issues = validate_middleware_configuration(mock_settings)

        threshold_issues = [issue for issue in issues if "slow_request_threshold" in issue.lower()]
        assert len(threshold_issues) >= 1
        assert ">" in threshold_issues[0]  # Should mention "should be > 0"

        # Test Case 3: Mock settings with valid threshold should not generate warning
        mock_settings.slow_request_threshold = 1000  # 1 second, valid

        issues = validate_middleware_configuration(mock_settings)

        threshold_issues = [issue for issue in issues if "slow_request_threshold" in issue.lower()]
        assert len(threshold_issues) == 0

        # Test Case 4: Mock settings with very small but positive threshold should be valid
        mock_settings.slow_request_threshold = 1  # 1ms, technically valid

        issues = validate_middleware_configuration(mock_settings)

        threshold_issues = [issue for issue in issues if "slow_request_threshold" in issue.lower()]
        assert len(threshold_issues) == 0

        # Test Case 5: Test with real Settings object (should always be valid due to Pydantic constraints)
        real_settings = create_settings()
        # Settings model prevents setting invalid slow_request_threshold
        # This tests that valid real settings don't generate warnings
        issues = validate_middleware_configuration(real_settings)
        threshold_issues = [issue for issue in issues if "slow_request_threshold" in issue.lower()]
        assert len(threshold_issues) == 0
    
    def test_valid_configuration_returns_no_issues(self) -> None:
        """
        Test that valid middleware configuration returns empty issues list.

        Verifies:
            Configuration validation passes without warnings for properly
            configured middleware settings using default valid values

        Business Impact:
            Confirms that default and properly configured middleware setups
            are recognized as valid, ensuring smooth production deployment
            without false-positive configuration warnings.

        Scenario:
            Given: Settings object with default valid configuration values
            When: Configuration validation is performed
            Then: No warnings or errors are generated (empty issues list)

        Edge Cases Covered:
            - Default configuration validation
            - All middleware components properly configured
            - No conflicting or invalid parameter values
            - Complete configuration coverage validation

        Contract Reference:
            validate_middleware_configuration() should return empty list
            when configuration is valid and no operational issues are detected
        """
        # Test Case 1: Default valid configuration should pass validation
        settings = create_settings()  # All valid defaults

        issues = validate_middleware_configuration(settings)

        assert len(issues) == 0

        # Test Case 2: Explicitly valid configuration with all features enabled
        settings.rate_limiting_enabled = True
        settings.redis_url = "redis://localhost:6379"
        settings.compression_enabled = True
        settings.compression_level = 6  # Valid (1-9)
        settings.api_versioning_enabled = True
        settings.default_api_version = "1.0"
        settings.current_api_version = "1.0"
        settings.max_request_size = 10 * 1024 * 1024  # 10MB
        settings.slow_request_threshold = 1000  # 1 second

        issues = validate_middleware_configuration(settings)

        assert len(issues) == 0

        # Test Case 3: Valid configuration with features disabled
        settings.rate_limiting_enabled = False
        settings.compression_enabled = False
        settings.api_versioning_enabled = False

        issues = validate_middleware_configuration(settings)

        assert len(issues) == 0

        # Test Case 4: Valid boundary values
        settings.compression_enabled = True
        settings.compression_level = 1  # Minimum valid
        settings.max_request_size = 1  # Minimum valid
        settings.slow_request_threshold = 1  # Minimum valid

        issues = validate_middleware_configuration(settings)

        assert len(issues) == 0

        # Test Case 5: Valid maximum values
        settings.compression_level = 9  # Maximum valid
        settings.max_request_size = 100 * 1024 * 1024  # 100MB
        settings.slow_request_threshold = 60000  # 1 minute

        issues = validate_middleware_configuration(settings)

        assert len(issues) == 0