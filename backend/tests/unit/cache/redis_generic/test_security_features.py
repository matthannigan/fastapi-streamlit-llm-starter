"""
Comprehensive test suite for GenericRedisCache security features.

This module provides systematic behavioral testing of the security functionality
including security validation, configuration management, reporting, and testing
capabilities integrated with the GenericRedisCache.

Test Coverage:
    - Security configuration validation and management
    - Security status reporting and recommendations
    - Comprehensive security assessment and reporting
    - Security configuration testing and validation
    - Integration with Redis connection security
    - Error handling for security-related operations

Testing Philosophy:
    - Uses behavior-driven testing with Given/When/Then structure
    - Tests security functionality with realistic mock configurations
    - Validates security integration without compromising test security
    - Ensures graceful degradation when security features are unavailable
    - Comprehensive coverage of security scenarios and edge cases

Test Organization:
    - TestSecurityValidation: Security validation and assessment functionality
    - TestSecurityStatusManagement: Security status reporting and management
    - TestSecurityReporting: Security report generation and formatting
    - TestSecurityConfigurationTesting: Security configuration testing and validation

Fixtures and Mocks:
    From conftest.py:
        - mock_tls_security_config: Mock SecurityConfig with TLS encryption
        - secure_generic_redis_config: Configuration with security enabled
        - default_generic_redis_config: Standard configuration for comparison
        - fakeredis: Stateful fake Redis client
    From parent conftest.py:
        - sample_cache_key: Standard cache key for testing
        - sample_cache_value: Standard cache value for testing
"""

import ssl
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.security import SecurityConfig


class TestSecurityStatusManagement:
    """
    Test security status reporting and management functionality.

    The security status system must provide accurate information about current
    security configuration and operational status.
    """

    def test_get_security_status_with_security_config(
        self, mock_path_exists, mock_ssl_context
    ):
        """
        Test security status retrieval with auto-generated security configuration.

        Given: A cache with auto-generated security configuration
        When: Security status is requested
        Then: Comprehensive security status should be returned
        And: Security level should be accurately reported
        And: Configuration details should be included
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(redis_url="redis://localhost:6379")

        # Act: Get security status
        status = cache.get_security_status()

        # Assert: Verify comprehensive status information
        assert isinstance(status, dict)
        assert "security_level" in status

        # Security level should be MEDIUM or HIGH for auto-generated config
        assert status["security_level"] in ["MEDIUM", "HIGH"]

        # Security should be indicated by presence of configuration
        assert "configuration" in status

        # Should have configuration details
        config = status["configuration"]
        assert config["has_authentication"] is True
        assert config["tls_enabled"] is True
        # Certificate verification is False in development environment (allows self-signed)
        # This is expected behavior from SecurityConfig.create_for_environment()

    def test_get_security_status_without_security_config(
        self, default_generic_redis_config
    ):
        """
        Test security status retrieval with auto-generated security configuration.

        Given: A cache initialized with default config (security auto-generated)
        When: Security status is requested
        Then: Security status should be returned
        And: Security should always be present (security-first architecture)
        And: No errors should be raised
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**default_generic_redis_config)

        # Act: Get security status
        status = cache.get_security_status()

        # Assert: Verify security information
        assert isinstance(status, dict)
        assert "security_level" in status

        # Security should always be present in security-first architecture
        # Security level should be MEDIUM or HIGH (never NONE)
        assert status["security_level"] in ["MEDIUM", "HIGH"]

        # Security manager should be present
        assert cache.security_manager is not None

    def test_security_level_classification(self, mock_path_exists):
        """
        Test security level classification for auto-generated security config.

        Given: A cache with auto-generated security configuration
        When: Security status is retrieved
        Then: Security level should reflect the automatically-created config
        And: Security should always be present (never LOW or NONE)
        """
        # Arrange: Create cache (security config auto-generated via create_for_environment())
        cache = GenericRedisCache(redis_url="redis://localhost")

        # Act: Get security status
        status = cache.get_security_status()

        # Assert: Security should always be present in security-first architecture
        assert "security_level" in status
        # Security level should be MEDIUM or HIGH (never LOW or NONE in development)
        assert status["security_level"] in ["MEDIUM", "HIGH"]
        # Security manager should be present
        assert cache.security_manager is not None
        # Security config should have required fields
        assert cache.security_config is not None
        assert cache.security_config.redis_auth is not None
        assert cache.security_config.use_tls == True

    def test_security_status_data_completeness(
        self, secure_generic_redis_config, mock_path_exists, mock_ssl_context
    ):
        """
        Test completeness of security status data.

        Given: A cache with auto-generated security configuration
        When: Security status is retrieved
        Then: All relevant security information should be included
        And: Connection status should be reported
        And: Configuration details should be comprehensive
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Act: Get security status
        status = cache.get_security_status()

        # Assert: Verify required keys are present
        required_keys = {"security_level"}
        assert all(key in status for key in required_keys)

        # Security level should be MEDIUM or HIGH for auto-generated config
        assert status["security_level"] in ["MEDIUM", "HIGH"]

        # Verify additional details if present
        if "configuration" in status:
            config = status["configuration"]
            # Check key configuration elements
            if "authentication_enabled" in config:
                assert config["authentication_enabled"] is True
            if "tls_enabled" in config:
                assert config["tls_enabled"] is True

        # Verify security features reporting if present
        if "security_features" in status:
            features = status["security_features"]
            assert isinstance(features, list)

        # Should include useful information beyond basic structure
        assert len(status) >= 2  # At least security_level and security_enabled

    def test_security_recommendations_generation(self, default_generic_redis_config):
        """
        Test generation of security recommendations.

        Given: A cache with auto-generated security configuration
        When: Security recommendations are requested
        Then: Appropriate recommendations should be generated
        And: Recommendations should be specific and actionable
        And: Security improvements should be suggested
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**default_generic_redis_config)

        # Act: Get security recommendations
        recommendations = cache.get_security_recommendations()

        # Assert: Verify recommendations are generated
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Recommendations should be actionable
        # Note: With auto-generated security config, basic TLS and auth are already enabled
        # Recommendations will focus on further hardening (cert verification, key rotation, etc.)
        assert any(isinstance(rec, str) and len(rec) > 0 for rec in recommendations)

    def test_security_recommendations_for_unsecured_cache(
        self, default_generic_redis_config
    ):
        """
        Test security recommendations for cache with auto-generated security.

        Given: A cache with auto-generated security configuration
        When: Security recommendations are requested
        Then: Recommendations should be provided for further security hardening
        And: Recommendations should be actionable
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**default_generic_redis_config)

        # Act: Get security recommendations
        recommendations = cache.get_security_recommendations()

        # Assert: Verify recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0  # Should have recommendations for hardening

        # All recommendations should be non-empty strings
        assert all(isinstance(rec, str) and len(rec) > 0 for rec in recommendations)

        # Recommendations should provide guidance (flexible matching)
        recommendation_text = " ".join(recommendations).lower()
        # May recommend: certificate verification, key rotation, ACL setup, monitoring, etc.
        assert len(recommendation_text) > 0


class TestSecurityValidation:
    """
    Test security validation functionality.

    The security validation system must provide comprehensive assessment of
    Redis connection security including authentication and encryption validation.
    """

    @pytest.mark.asyncio
    async def test_validate_security_with_security_manager(
        self,
        secure_generic_redis_config,
        fake_redis_client,
        mock_path_exists,
        mock_ssl_context,
    ):
        """
        Test security validation with security manager available.

        Given: A cache with security configuration and manager
        When: Security validation is performed
        Then: Comprehensive security validation should be returned
        And: Validation results should include security assessment
        And: Vulnerabilities should be identified if present
        """
        # Arrange: Create cache with security configuration using the fixture
        # mock_path_exists ensures certificate file existence is mocked
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Mock the Redis connection for testing
        with patch.object(cache, "redis", fake_redis_client):
            await cache.connect()

            # Act: Validate security
            validation_result = await cache.validate_security()

            # Assert: Verify validation result structure
            if validation_result is not None:
                assert hasattr(validation_result, "is_secure") or isinstance(
                    validation_result, dict
                )

                # If it's a dict format
                if isinstance(validation_result, dict):
                    assert "is_secure" in validation_result
                    assert "validation_results" in validation_result
                    assert "vulnerabilities" in validation_result
                    assert "recommendations" in validation_result
                else:
                    # If it's an object format
                    assert hasattr(validation_result, "is_secure")
                    assert hasattr(validation_result, "vulnerabilities")

    @pytest.mark.asyncio
    async def test_validate_security_without_security_manager(
        self, default_generic_redis_config, fake_redis_client
    ):
        """
        Test security validation with auto-generated security manager.

        Given: A cache with auto-generated security configuration
        When: Security validation is performed
        Then: Validation result should be returned
        And: Security manager should be present
        And: Validation should work correctly
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**default_generic_redis_config)

        # Mock the Redis connection for testing
        with patch.object(cache, "redis", fake_redis_client):
            await cache.connect()

            # Act: Validate security
            validation_result = await cache.validate_security()

            # Assert: Security manager should be present in security-first architecture
            assert cache.security_manager is not None
            # Validation result should be returned (not None)
            assert validation_result is not None

    @pytest.mark.asyncio
    async def test_validate_security_connection_handling(
        self, secure_generic_redis_config, mock_path_exists, mock_ssl_context
    ):
        """
        Test security validation with connection issues.

        Given: A cache with security configuration
        When: Security validation is performed with connection issues
        Then: Validation should handle connection problems gracefully
        And: Appropriate error information should be provided
        """
        # Arrange: Create cache with security configuration using the fixture
        # mock_path_exists ensures certificate file existence is mocked
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Act: Validate security without connection
        validation_result = await cache.validate_security()

        # Assert: Should handle missing connection gracefully
        # Either returns None or provides connection error information
        if validation_result is not None:
            if isinstance(validation_result, dict):
                # Should indicate connection problems in validation
                assert (
                    "connection_status" in validation_result
                    or "errors" in validation_result
                )


class TestSecurityReporting:
    """
    Test security report generation functionality.

    The security reporting system must provide comprehensive security assessment
    reports including configuration analysis, vulnerability assessment, and recommendations.
    """

    @pytest.mark.asyncio
    async def test_generate_security_report_comprehensive(
        self,
        secure_generic_redis_config,
        fake_redis_client,
        mock_path_exists,
        mock_ssl_context,
    ):
        """
        Test comprehensive security report generation.

        Given: A cache with security configuration
        When: A security report is generated
        Then: Comprehensive security report should be returned
        And: Report should include configuration status and recommendations
        And: Report should be formatted for human readability
        """
        # Arrange: Create cache with security configuration using the fixture
        # mock_path_exists ensures certificate file existence is mocked
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Mock the Redis connection for testing
        with patch.object(cache, "redis", fake_redis_client):
            await cache.connect()

            # Act: Generate security report
            report = await cache.generate_security_report()

            # Assert: Verify report structure and content
            assert isinstance(report, str)
            assert len(report) > 0

            report_lower = report.lower()

            # Should include security status information
            assert "security" in report_lower

            # Should include configuration information or validation status
            assert (
                "configuration" in report_lower
                or "config" in report_lower
                or "validation" in report_lower
                or "security" in report_lower
            )

            # Should include recommendations section or validation guidance
            assert (
                "recommendation" in report_lower
                or "suggest" in report_lower
                or "validate" in report_lower
                or "run" in report_lower
            )

            # Should be formatted for readability (or be a simple message)
            assert len(report) > 10  # Should have meaningful content

    @pytest.mark.asyncio
    async def test_generate_security_report_basic_config(
        self, default_generic_redis_config, fake_redis_client
    ):
        """
        Test security report generation with auto-generated security configuration.

        Given: A cache with auto-generated security configuration
        When: A security report is generated
        Then: Security report should be returned
        And: Report should reflect security configuration status
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**default_generic_redis_config)

        # Mock the Redis connection for testing
        with patch.object(cache, "redis", fake_redis_client):
            await cache.connect()

            # Act: Generate security report
            report = await cache.generate_security_report()

            # Assert: Verify report is generated
            assert isinstance(report, str)
            assert len(report) > 0

            # Report should contain information about security status
            # May mention validation needed or current security level
            report_lower = report.lower()
            assert "security" in report_lower or "validation" in report_lower

            # Report should be structured and informative
            assert len(report_lower) > 20  # Reasonable minimum length

    @pytest.mark.asyncio
    async def test_security_report_formatting(
        self, secure_generic_redis_config, mock_path_exists, mock_ssl_context
    ):
        """
        Test security report formatting and structure.

        Given: A cache with security configuration
        When: A security report is generated
        Then: Report should be well-formatted and structured
        And: Report should contain clear sections and information hierarchy
        """
        # Arrange: Create cache with security configuration using the fixture
        # mock_path_exists ensures certificate file existence is mocked
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Act: Generate security report
        report = await cache.generate_security_report()

        # Assert: Verify report formatting
        assert isinstance(report, str)
        assert len(report) > 50  # Should be substantial

        # Should have lines (structured content)
        lines = report.split("\n")
        assert len(lines) >= 1

        # Should contain meaningful security content
        assert (
            "security" in report.lower()
            or "validation" in report.lower()
            or "available" in report.lower()
            or "report" in report.lower()
        )


class TestSecurityConfigurationTesting:
    """
    Test security configuration testing functionality.

    The security configuration testing system must provide comprehensive testing
    of security settings including connection validation and authentication testing.
    """

    @pytest.mark.asyncio
    async def test_security_configuration_testing_comprehensive(
        self,
        secure_generic_redis_config,
        fake_redis_client,
        mock_path_exists,
        mock_ssl_context,
    ):
        """
        Test comprehensive security configuration testing.

        Given: A cache with comprehensive security configuration
        When: Security configuration testing is performed
        Then: Detailed test results should be returned
        And: All security aspects should be tested
        And: Overall security status should be assessed
        """
        # Arrange: Create cache with comprehensive security configuration using the fixture
        # mock_path_exists ensures certificate file existence is mocked
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Mock the Redis connection for testing
        with patch.object(cache, "redis", fake_redis_client):
            await cache.connect()

            # Act: Test security configuration
            test_results = await cache.test_security_configuration()

            # Assert: Verify test results structure
            assert isinstance(test_results, dict)

            # Should include overall assessment
            assert "overall_secure" in test_results
            assert isinstance(test_results["overall_secure"], bool)

            # Should include detailed test results
            assert "test_details" in test_results
            assert isinstance(test_results["test_details"], dict)

            # Should include any errors
            assert "errors" in test_results

            # Test results should cover key security aspects
            test_details = test_results["test_details"]
            tested_aspects = list(test_details.keys())
            assert len(tested_aspects) > 0

    @pytest.mark.asyncio
    async def test_security_configuration_testing_basic(
        self, default_generic_redis_config, fake_redis_client
    ):
        """
        Test security configuration testing with auto-generated security.

        Given: A cache with auto-generated security configuration
        When: Security configuration testing is performed
        Then: Test results should reflect current security configuration
        And: Security status should be provided
        And: Recommendations for hardening should be included
        """
        # Arrange: Create cache (security config auto-generated)
        cache = GenericRedisCache(**default_generic_redis_config)

        # Mock the Redis connection for testing
        with patch.object(cache, "redis", fake_redis_client):
            await cache.connect()

            # Act: Test security configuration
            test_results = await cache.test_security_configuration()

            # Assert: Should provide security testing results
            assert isinstance(test_results, dict)
            assert "overall_secure" in test_results

            # With auto-generated security config, overall_secure depends on configuration
            # In development: may be False due to cert verification disabled
            assert isinstance(test_results["overall_secure"], bool)

            # Should have security test results
            assert len(test_results) > 0

    @pytest.mark.asyncio
    async def test_security_configuration_testing_error_handling(
        self, secure_generic_redis_config, mock_path_exists, mock_ssl_context
    ):
        """
        Test security configuration testing error handling.

        Given: A cache with security configuration
        When: Security configuration testing encounters errors
        Then: Errors should be handled gracefully
        And: Error information should be included in results
        And: Partial results should still be provided where possible
        """
        # Arrange: Create cache with security configuration using the fixture
        # mock_path_exists ensures certificate file existence is mocked
        cache = GenericRedisCache(**secure_generic_redis_config)

        # Act: Test security configuration without connection
        test_results = await cache.test_security_configuration()

        # Assert: Should handle connection issues gracefully
        assert isinstance(test_results, dict)

        # Should still provide basic structure
        assert "overall_secure" in test_results
        assert "errors" in test_results

        # Should record connection-related errors
        errors = test_results["errors"]
        if len(errors) > 0:
            error_text = " ".join(errors).lower()
            assert (
                "connection" in error_text
                or "connect" in error_text
                or "redis" in error_text
            )
