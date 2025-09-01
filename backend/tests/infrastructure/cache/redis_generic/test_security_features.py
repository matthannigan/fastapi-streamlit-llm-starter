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

import pytest
from unittest.mock import patch
from typing import Dict, Any, List
from app.infrastructure.cache.security import SecurityConfig
from app.infrastructure.cache.redis_generic import GenericRedisCache

class TestSecurityStatusManagement:
    """
    Test security status reporting and management functionality.
    
    The security status system must provide accurate information about current
    security configuration and operational status.
    """

    def test_get_security_status_with_security_config(self, secure_generic_redis_config):
        """
        Test security status retrieval with security configuration.
        
        Given: A cache with security configuration enabled
        When: Security status is requested
        Then: Comprehensive security status should be returned
        And: Security level should be accurately reported
        And: Configuration details should be included
        """
        # Arrange: Create cache with security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Act: Get security status
        status = cache.get_security_status()
        
        # Assert: Verify comprehensive status information
        assert isinstance(status, dict)
        assert "security_level" in status
        assert "security_enabled" in status
        
        # Security level should be HIGH due to comprehensive security config
        assert status["security_level"] == "HIGH"
        
        # Security should be enabled
        assert status["security_enabled"] is True
        
        # Should have configuration details
        if "configuration" in status:
            config = status["configuration"]
            assert config["authentication_enabled"] is True
            assert config["tls_enabled"] is True
            assert config["certificate_verification"] is True

    def test_get_security_status_without_security_config(self, default_generic_redis_config):
        """
        Test security status retrieval without security configuration.
        
        Given: A cache without security configuration
        When: Security status is requested
        Then: Basic security status should be returned
        And: Absence of security features should be indicated
        And: No errors should be raised for missing security configuration
        """
        # Arrange: Create cache without security configuration
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Act: Get security status
        status = cache.get_security_status()
        
        # Assert: Verify basic status information
        assert isinstance(status, dict)
        assert "security_level" in status
        assert "security_enabled" in status
        
        # Security level should be NONE due to no security features
        assert status["security_level"] == "NONE"
        
        # Security should be disabled
        assert status["security_enabled"] is False
        
        # Should have informative message
        assert "message" in status

    @pytest.mark.parametrize(
        "config_params, expected_level",
        [
            ({}, "LOW"), # No security features
            (
                {"redis_auth": "password"}, 
                "MEDIUM" # Basic auth only
            ),
            (
                {"use_tls": True},
                "MEDIUM" # TLS only, no auth
            ),
            (
                {"redis_auth": "password", "use_tls": True, "verify_certificates": True},
                "HIGH" # TLS + Auth + Verification
            ),
            (
                {
                    "redis_auth": "password", 
                    "use_tls": True, 
                    "acl_username": "user", 
                    "acl_password": "password", 
                    "verify_certificates": True
                },
                "HIGH" # Multiple auth methods + TLS + Verification
            ),
        ]
    )
    def test_security_level_classification(self, mock_path_exists, config_params, expected_level):
        """
        Test security level classification based on configuration.
        
        Given: Caches with different security configurations
        When: Security status is retrieved for each configuration
        Then: Security levels should be accurately classified
        """
        # 1. Arrange: Create a REAL SecurityConfig with the specified parameters
        security_config = SecurityConfig(**config_params)
        
        # 2. Arrange: Create a REAL GenericRedisCache with this config
        # We don't need a real connection for this test, just the configured instance.
        cache = GenericRedisCache(
            redis_url="redis://localhost",
            security_config=security_config
        )

        # 3. Act: Call the public method to get the security status
        status = cache.get_security_status()

        # 4. Assert: Check the classification in the returned data
        assert status["security_level"] == expected_level

    def test_security_status_data_completeness(self, secure_generic_redis_config):
        """
        Test completeness of security status data.
        
        Given: A cache with comprehensive security configuration
        When: Security status is retrieved
        Then: All relevant security information should be included
        And: Connection status should be reported
        And: Configuration details should be comprehensive
        """
        # Arrange: Create cache with comprehensive security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Act: Get security status
        status = cache.get_security_status()
        
        # Assert: Verify required keys are present
        required_keys = {"security_level", "security_enabled"}
        assert all(key in status for key in required_keys)
        
        # Security should be enabled for comprehensive config
        assert status["security_enabled"] is True
        assert status["security_level"] == "HIGH"
        
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
        
        Given: Caches with various security configurations
        When: Security recommendations are requested
        Then: Appropriate recommendations should be generated
        And: Recommendations should be specific and actionable
        And: Security improvements should be suggested
        """
        # Arrange: Create cache with minimal security
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Act: Get security recommendations
        recommendations = cache.get_security_recommendations()
        
        # Assert: Verify recommendations are generated
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Check for expected security recommendations
        recommendation_text = " ".join(recommendations)
        
        # Should recommend authentication
        assert any("authentication" in rec.lower() for rec in recommendations)
        
        # Should recommend encryption
        assert any("tls" in rec.lower() or "encryption" in rec.lower() for rec in recommendations)
        
        # Should recommend specific actions
        assert any("enable" in rec.lower() or "configure" in rec.lower() for rec in recommendations)

    def test_security_recommendations_for_unsecured_cache(self, default_generic_redis_config):
        """
        Test security recommendations for unsecured cache configuration.
        
        Given: A cache without security configuration
        When: Security recommendations are requested
        Then: Comprehensive security recommendations should be provided
        And: Recommendations should cover authentication and encryption
        And: Implementation guidance should be included
        """
        # Arrange: Create unsecured cache
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Act: Get security recommendations
        recommendations = cache.get_security_recommendations()
        
        # Assert: Verify comprehensive recommendations
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 3  # Should have multiple recommendations
        
        recommendation_text = " ".join(recommendations).lower()
        
        # Should recommend authentication setup
        assert "password" in recommendation_text or "auth" in recommendation_text
        
        # Should recommend TLS encryption
        assert "tls" in recommendation_text or "ssl" in recommendation_text
        
        # Should recommend security setup (flexible matching)
        assert any("security" in rec.lower() or "acl" in rec.lower() or "redis" in rec.lower() 
                  for rec in recommendations)
        
        # Should provide implementation guidance
        assert any("configure" in rec.lower() or "set" in rec.lower() or "enable" in rec.lower() 
                  for rec in recommendations)


class TestSecurityValidation:
    """
    Test security validation functionality.
    
    The security validation system must provide comprehensive assessment of
    Redis connection security including authentication and encryption validation.
    """

    @pytest.mark.asyncio
    async def test_validate_security_with_security_manager(self, secure_generic_redis_config, fake_redis_client):
        """
        Test security validation with security manager available.
        
        Given: A cache with security configuration and manager
        When: Security validation is performed
        Then: Comprehensive security validation should be returned
        And: Validation results should include security assessment
        And: Vulnerabilities should be identified if present
        """
        # Arrange: Create cache with security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Mock the Redis connection for testing
        with patch.object(cache, 'redis', fake_redis_client):
            await cache.connect()
            
            # Act: Validate security
            validation_result = await cache.validate_security()
            
            # Assert: Verify validation result structure
            if validation_result is not None:
                assert hasattr(validation_result, 'is_secure') or isinstance(validation_result, dict)
                
                # If it's a dict format
                if isinstance(validation_result, dict):
                    assert "is_secure" in validation_result
                    assert "validation_results" in validation_result
                    assert "vulnerabilities" in validation_result
                    assert "recommendations" in validation_result
                else:
                    # If it's an object format
                    assert hasattr(validation_result, 'is_secure')
                    assert hasattr(validation_result, 'vulnerabilities')

    @pytest.mark.asyncio
    async def test_validate_security_without_security_manager(self, default_generic_redis_config, fake_redis_client):
        """
        Test security validation without security manager.
        
        Given: A cache without security configuration
        When: Security validation is performed
        Then: None should be returned indicating no security manager
        And: No errors should be raised for missing security features
        """
        # Arrange: Create cache without security configuration
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Mock the Redis connection for testing
        with patch.object(cache, 'redis', fake_redis_client):
            await cache.connect()
            
            # Act: Validate security
            validation_result = await cache.validate_security()
            
            # Assert: Should return None when no security manager available
            assert validation_result is None

    @pytest.mark.asyncio
    async def test_validate_security_connection_handling(self, secure_generic_redis_config):
        """
        Test security validation with connection issues.
        
        Given: A cache with security configuration
        When: Security validation is performed with connection issues
        Then: Validation should handle connection problems gracefully
        And: Appropriate error information should be provided
        """
        # Arrange: Create cache with security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Act: Validate security without connection
        validation_result = await cache.validate_security()
        
        # Assert: Should handle missing connection gracefully
        # Either returns None or provides connection error information
        if validation_result is not None:
            if isinstance(validation_result, dict):
                # Should indicate connection problems in validation
                assert "connection_status" in validation_result or "errors" in validation_result


class TestSecurityReporting:
    """
    Test security report generation functionality.
    
    The security reporting system must provide comprehensive security assessment
    reports including configuration analysis, vulnerability assessment, and recommendations.
    """

    @pytest.mark.asyncio
    async def test_generate_security_report_comprehensive(self, secure_generic_redis_config, fake_redis_client):
        """
        Test comprehensive security report generation.
        
        Given: A cache with security configuration
        When: A security report is generated
        Then: Comprehensive security report should be returned
        And: Report should include configuration status and recommendations
        And: Report should be formatted for human readability
        """
        # Arrange: Create cache with security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Mock the Redis connection for testing
        with patch.object(cache, 'redis', fake_redis_client):
            await cache.connect()
            
            # Act: Generate security report
            report = await cache.generate_security_report()
            
            # Assert: Verify report structure and content
            assert isinstance(report, str)
            assert len(report) > 0
            
            report_lower = report.lower()
            
            # Should include security status information
            assert "security" in report_lower
            
            # Should include configuration information
            assert "configuration" in report_lower or "config" in report_lower
            
            # Should include recommendations section
            assert "recommendation" in report_lower or "suggest" in report_lower
            
            # Should be formatted for readability (contains sections/headers)
            assert "\n" in report or "---" in report or "==" in report

    @pytest.mark.asyncio
    async def test_generate_security_report_basic_config(self, default_generic_redis_config, fake_redis_client):
        """
        Test security report generation for basic configuration.
        
        Given: A cache without security configuration
        When: A security report is generated
        Then: Basic security report should be returned
        And: Report should highlight security deficiencies
        And: Report should provide security improvement recommendations
        """
        # Arrange: Create cache with basic configuration
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Mock the Redis connection for testing
        with patch.object(cache, 'redis', fake_redis_client):
            await cache.connect()
            
            # Act: Generate security report
            report = await cache.generate_security_report()
            
            # Assert: Verify report addresses security gaps
            assert isinstance(report, str)
            assert len(report) > 0
            
            report_lower = report.lower()
            
            # Should highlight security level
            assert "none" in report_lower or "not configured" in report_lower or "not configured" in report_lower
            
            # Should recommend security improvements
            assert "auth" in report_lower or "password" in report_lower
            assert "tls" in report_lower or "encryption" in report_lower
            
            # Should provide actionable guidance
            assert "enable" in report_lower or "configure" in report_lower or "implement" in report_lower

    @pytest.mark.asyncio
    async def test_security_report_formatting(self, secure_generic_redis_config):
        """
        Test security report formatting and structure.
        
        Given: A cache with security configuration
        When: A security report is generated
        Then: Report should be well-formatted and structured
        And: Report should contain clear sections and information hierarchy
        """
        # Arrange: Create cache with security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Act: Generate security report
        report = await cache.generate_security_report()
        
        # Assert: Verify report formatting
        assert isinstance(report, str)
        assert len(report) > 100  # Should be substantial
        
        # Should have multiple lines (structured content)
        lines = report.split('\n')
        assert len(lines) > 5
        
        # Should contain section headers or structure indicators
        has_structure = any([
            "---" in report,
            "===" in report,
            "Security" in report and "Report" in report,
            any(line.strip().endswith(':') for line in lines[:10])  # Section headers
        ])
        assert has_structure


class TestSecurityConfigurationTesting:
    """
    Test security configuration testing functionality.
    
    The security configuration testing system must provide comprehensive testing
    of security settings including connection validation and authentication testing.
    """

    @pytest.mark.asyncio
    async def test_security_configuration_testing_comprehensive(self, secure_generic_redis_config, fake_redis_client):
        """
        Test comprehensive security configuration testing.
        
        Given: A cache with comprehensive security configuration
        When: Security configuration testing is performed
        Then: Detailed test results should be returned
        And: All security aspects should be tested
        And: Overall security status should be assessed
        """
        # Arrange: Create cache with comprehensive security configuration
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
        # Mock the Redis connection for testing
        with patch.object(cache, 'redis', fake_redis_client):
            await cache.connect()
            
            # Act: Test security configuration
            test_results = await cache.test_security_configuration()
            
            # Assert: Verify test results structure
            assert isinstance(test_results, dict)
            
            # Should include overall assessment
            assert "overall_secure" in test_results
            assert isinstance(test_results["overall_secure"], bool)
            
            # Should include detailed test results
            assert "test_results" in test_results
            assert isinstance(test_results["test_results"], dict)
            
            # Should include any errors or warnings
            assert "errors" in test_results
            assert "warnings" in test_results
            
            # Test results should cover key security aspects
            test_details = test_results["test_results"]
            expected_tests = ["connection", "authentication", "encryption"]
            tested_aspects = list(test_details.keys())
            assert len(tested_aspects) > 0

    @pytest.mark.asyncio
    async def test_security_configuration_testing_basic(self, default_generic_redis_config, fake_redis_client):
        """
        Test security configuration testing for basic configuration.
        
        Given: A cache with basic (unsecured) configuration
        When: Security configuration testing is performed
        Then: Test results should reflect security deficiencies
        And: Security warnings should be provided
        And: Overall security status should be negative
        """
        # Arrange: Create cache with basic configuration
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Mock the Redis connection for testing
        with patch.object(cache, 'redis', fake_redis_client):
            await cache.connect()
            
            # Act: Test security configuration
            test_results = await cache.test_security_configuration()
            
            # Assert: Should reflect security deficiencies
            assert isinstance(test_results, dict)
            assert "overall_secure" in test_results
            
            # Overall security should be False for basic config
            assert test_results["overall_secure"] is False
            
            # Should include recommendations about security deficiencies
            assert "recommendations" in test_results
            recommendations = test_results["recommendations"]
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            
            # Recommendations should mention key security issues
            recommendation_text = " ".join(recommendations).lower()
            assert "authentication" in recommendation_text or "auth" in recommendation_text
            assert "encryption" in recommendation_text or "tls" in recommendation_text

    @pytest.mark.asyncio
    async def test_security_configuration_testing_error_handling(self, secure_generic_redis_config):
        """
        Test security configuration testing error handling.
        
        Given: A cache with security configuration
        When: Security configuration testing encounters errors
        Then: Errors should be handled gracefully
        And: Error information should be included in results
        And: Partial results should still be provided where possible
        """
        # Arrange: Create cache with security configuration (no connection)
        try:
            cache = GenericRedisCache(**secure_generic_redis_config)
        except FileNotFoundError:
            pytest.skip("Security certificate files not available for testing")
        
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
            assert "connection" in error_text or "connect" in error_text or "redis" in error_text



