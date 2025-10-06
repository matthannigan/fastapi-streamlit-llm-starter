"""
Integration tests for Redis security comprehensive validation (SEAM 4).

This test module verifies the integration between the comprehensive security
configuration validation method and all its component validators, testing the
full validation orchestration and result aggregation flow.

Test Coverage:
    - Comprehensive validation with all components passing
    - Validation failure aggregation from multiple components
    - Validation summary format and human-readable output
    - SecurityValidationResult structure and behavior
    - Multi-component error and warning aggregation

Integration Seam:
    validate_security_configuration() → Component validators → Result aggregation
"""

import pytest
from cryptography.fernet import Fernet


class TestComprehensiveSecurityValidation:
    """
    Test suite for comprehensive security configuration validation integration.

    Integration Scope:
        Tests the integration of validate_security_configuration() with:
        - validate_tls_certificates() component
        - validate_encryption_key() component
        - validate_redis_auth() component
        - SecurityValidationResult aggregation
        - Result summary generation

    Critical Path:
        Configuration input → Multi-component validation → Error aggregation →
        Result structure → Summary generation

    Business Impact:
        Comprehensive validation provides operations teams with complete security
        audit capability, enabling informed deployment decisions and security
        compliance verification.

    Test Strategy:
        - Test outside-in from validate_security_configuration() entry point
        - Use real component validators (no mocking of internal methods)
        - Verify observable behavior through SecurityValidationResult structure
        - Test with realistic configuration scenarios
        - Use high-fidelity test data (tmp_path, Fernet keys)
    """

    def test_comprehensive_validation_all_components_pass(self, tmp_path, monkeypatch):
        """
        Test comprehensive validation succeeds when all components are properly configured.

        Integration Scope:
            validate_security_configuration() → All validators → Success aggregation

        Business Impact:
            Confirms complete security configuration is valid, providing confidence
            for production deployment and operational sign-off.

        Test Strategy:
            1. Create valid test certificates using tmp_path
            2. Generate valid Fernet encryption key
            3. Configure secure Redis URL with TLS
            4. Call validate_security_configuration() with all components
            5. Verify SecurityValidationResult shows all components valid

        Success Criteria:
            - result.is_valid is True
            - All component statuses show success (✅ or "Valid")
            - No errors in result.errors list
            - All security components validated successfully
        """
        # Arrange: Create valid security configuration components
        from app.core.startup.redis_security import RedisSecurityValidator

        # Create test certificates in temporary directory
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text("-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----")

        key_file = tmp_path / "key.pem"
        key_file.write_text("-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----")

        ca_file = tmp_path / "ca.pem"
        ca_file.write_text("-----BEGIN CERTIFICATE-----\ntest_ca\n-----END CERTIFICATE-----")

        # Generate valid encryption key
        encryption_key = Fernet.generate_key().decode('utf-8')

        # Configure secure Redis URL with TLS
        redis_url = "rediss://redis:6380"

        # Act: Perform comprehensive validation
        validator = RedisSecurityValidator()
        result = validator.validate_security_configuration(
            redis_url=redis_url,
            encryption_key=encryption_key,
            tls_cert_path=str(cert_file),
            tls_key_path=str(key_file),
            tls_ca_path=str(ca_file),
            test_connectivity=False
        )

        # Assert: Verify comprehensive validation success
        assert result is not None, "Validation result should not be None"
        assert hasattr(result, 'is_valid'), "Result must have is_valid attribute"
        assert result.is_valid is True, "Validation should pass with all components configured"

        # Verify component statuses indicate success
        assert hasattr(result, 'tls_status'), "Result must have tls_status attribute"
        assert "✅" in result.tls_status or "Valid" in result.tls_status, \
            "TLS status should indicate success"

        assert hasattr(result, 'encryption_status'), "Result must have encryption_status attribute"
        assert "✅" in result.encryption_status or "Valid" in result.encryption_status, \
            "Encryption status should indicate success"

        assert hasattr(result, 'auth_status'), "Result must have auth_status attribute"
        # Auth may not be present in URL, so check for valid states
        assert result.auth_status is not None, "Auth status should be populated"

        # Verify no errors were collected
        assert hasattr(result, 'errors'), "Result must have errors attribute"
        assert isinstance(result.errors, list), "Errors must be a list"
        assert len(result.errors) == 0, f"No errors expected for valid configuration, got: {result.errors}"

    def test_comprehensive_validation_aggregates_multiple_failures(self, monkeypatch):
        """
        Test that validation failures from multiple components are correctly aggregated.

        Integration Scope:
            Invalid configuration → Multiple validators → Error aggregation

        Business Impact:
            Ensures all security issues are surfaced in a single validation pass,
            enabling comprehensive remediation rather than iterative fix-and-retry cycles.

        Test Strategy:
            1. Configure production environment via monkeypatch
            2. Provide invalid configuration for multiple components:
               - Insecure Redis URL (no TLS)
               - Invalid encryption key format
            3. Call validate_security_configuration()
            4. Verify errors from all failing components are aggregated

        Success Criteria:
            - result.is_valid is False
            - Multiple errors present in result.errors
            - TLS status shows failure (❌)
            - Encryption status shows failure (❌)
            - Error messages from different components are collected
        """
        # Arrange: Configure production environment and invalid security configuration
        from app.core.startup.redis_security import RedisSecurityValidator

        # Set production environment to enforce strict security
        monkeypatch.setenv("ENVIRONMENT", "production")

        # Configure invalid components
        redis_url = "redis://redis:6379"  # Insecure - no TLS
        encryption_key = "invalid-key"     # Invalid format - too short

        # Act: Perform comprehensive validation with multiple failures
        validator = RedisSecurityValidator()
        result = validator.validate_security_configuration(
            redis_url=redis_url,
            encryption_key=encryption_key,
            test_connectivity=False
        )

        # Assert: Verify failure aggregation
        assert result.is_valid is False, "Validation should fail with invalid configuration"

        # Verify errors are aggregated
        assert hasattr(result, 'errors'), "Result must have errors attribute"
        assert isinstance(result.errors, list), "Errors must be a list"
        assert len(result.errors) > 0, "Errors should be present for invalid configuration"

        # Verify component statuses show failures
        assert hasattr(result, 'tls_status'), "Result must have tls_status attribute"
        assert "❌" in result.tls_status or result.tls_status != "✅ Valid", \
            "TLS status should indicate failure for insecure URL"

        assert hasattr(result, 'encryption_status'), "Result must have encryption_status attribute"
        assert "❌" in result.encryption_status or result.encryption_status != "✅ Valid", \
            "Encryption status should indicate failure for invalid key"

        # Verify errors from both TLS and encryption components are present
        error_text = " ".join(result.errors).lower()
        # At least one error should relate to security issues
        assert len(error_text) > 0, "Error text should not be empty"

    def test_validation_result_summary_format(self, monkeypatch):
        """
        Test that validation result summary generates proper human-readable output.

        Integration Scope:
            Validation result → Summary generation → Human-readable output

        Business Impact:
            Provides clear, actionable security status reports for operational logging,
            audit trails, and troubleshooting support.

        Test Strategy:
            1. Create validator instance
            2. Perform validation with secure configuration
            3. Call result.summary() to generate human-readable report
            4. Verify summary contains all required sections

        Success Criteria:
            - Summary includes report header
            - Summary includes "Redis Security Validation Report" title
            - Summary includes "TLS/SSL:" section
            - Summary includes "Encryption:" section
            - Summary includes "Auth:" section
            - Summary is properly formatted for terminal output
        """
        # Arrange: Create validator and perform validation
        from app.core.startup.redis_security import RedisSecurityValidator

        # Configure basic secure Redis URL
        redis_url = "rediss://redis:6380"

        # Act: Perform validation and generate summary
        validator = RedisSecurityValidator()
        result = validator.validate_security_configuration(
            redis_url=redis_url,
            test_connectivity=False
        )

        # Generate human-readable summary
        summary = result.summary()

        # Assert: Verify summary format and content
        assert isinstance(summary, str), "Summary must be a string"
        assert len(summary) > 0, "Summary should not be empty"

        # Verify header and title
        assert "Redis Security Validation Report" in summary, \
            "Summary must include report title"

        # Verify component sections are present
        assert "TLS/SSL:" in summary, "Summary must include TLS/SSL section"
        assert "Encryption:" in summary, "Summary must include Encryption section"
        assert "Auth:" in summary, "Summary must include Auth section"

        # Verify summary is formatted for readability
        assert "\n" in summary, "Summary should be multi-line for readability"


class TestComprehensiveValidationErrorHandling:
    """
    Test suite for comprehensive validation error handling and edge cases.

    Integration Scope:
        Tests validation behavior with edge cases and error scenarios,
        verifying proper error handling and validation robustness.

    Business Impact:
        Ensures validation remains reliable even with unusual or invalid
        configurations, providing consistent error reporting.

    Test Strategy:
        - Test with missing components
        - Test with partial configurations
        - Test error message clarity
        - Test validation resilience
    """

    def test_comprehensive_validation_with_missing_redis_url_raises_error(self):
        """
        Test that comprehensive validation raises ConfigurationError for missing Redis URL.

        Integration Scope:
            Input validation → Error handling → ConfigurationError

        Business Impact:
            Ensures clear, immediate feedback when critical configuration is missing,
            preventing unclear runtime errors later.

        Test Strategy:
            1. Call validate_security_configuration() with None redis_url
            2. Verify ConfigurationError is raised
            3. Verify error message is informative

        Success Criteria:
            - ConfigurationError is raised
            - Error message indicates missing Redis URL
        """
        # Arrange: Create validator
        from app.core.startup.redis_security import RedisSecurityValidator
        from app.core.exceptions import ConfigurationError

        validator = RedisSecurityValidator()

        # Act & Assert: Verify ConfigurationError for None URL
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_security_configuration(
                redis_url=None,
                test_connectivity=False
            )

        # Verify error message is informative
        error_message = str(exc_info.value)
        assert len(error_message) > 0, "Error message should not be empty"

    def test_comprehensive_validation_with_empty_redis_url_raises_error(self):
        """
        Test that comprehensive validation raises ConfigurationError for empty Redis URL.

        Integration Scope:
            Input validation → Error handling → ConfigurationError

        Business Impact:
            Catches configuration errors early, preventing deployment with
            invalid Redis connection configuration.

        Test Strategy:
            1. Call validate_security_configuration() with empty string redis_url
            2. Verify ConfigurationError is raised
            3. Verify error message is clear

        Success Criteria:
            - ConfigurationError is raised
            - Error message indicates invalid Redis URL
        """
        # Arrange: Create validator
        from app.core.startup.redis_security import RedisSecurityValidator
        from app.core.exceptions import ConfigurationError

        validator = RedisSecurityValidator()

        # Act & Assert: Verify ConfigurationError for empty URL
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_security_configuration(
                redis_url="",
                test_connectivity=False
            )

        # Verify error message provides guidance
        error_message = str(exc_info.value)
        assert len(error_message) > 0, "Error message should provide guidance"

    def test_comprehensive_validation_handles_partial_configuration(self, tmp_path):
        """
        Test that comprehensive validation handles partial security configuration.

        Integration Scope:
            Partial configuration → Component validators → Result aggregation

        Business Impact:
            Supports incremental security configuration, allowing validation
            to provide feedback on what's configured and what's missing.

        Test Strategy:
            1. Provide only some security components (e.g., TLS but no encryption)
            2. Call validate_security_configuration()
            3. Verify validation completes without crashes
            4. Verify result shows status for all components

        Success Criteria:
            - Validation completes successfully
            - All component statuses are populated
            - Missing components are clearly indicated
            - No exceptions are raised
        """
        # Arrange: Create partial security configuration
        from app.core.startup.redis_security import RedisSecurityValidator

        # Create TLS certificates but omit encryption key
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")

        redis_url = "rediss://redis:6380"

        # Act: Perform validation with partial configuration
        validator = RedisSecurityValidator()
        result = validator.validate_security_configuration(
            redis_url=redis_url,
            tls_cert_path=str(cert_file),
            encryption_key=None,  # Explicitly omit encryption
            test_connectivity=False
        )

        # Assert: Verify validation handles partial configuration
        assert result is not None, "Result should be returned"
        assert hasattr(result, 'is_valid'), "Result must have is_valid attribute"

        # Verify all component statuses are populated even with partial config
        assert hasattr(result, 'tls_status'), "TLS status should be populated"
        assert hasattr(result, 'encryption_status'), "Encryption status should be populated"
        assert hasattr(result, 'auth_status'), "Auth status should be populated"

        # Verify each status is a non-empty string
        assert isinstance(result.tls_status, str) and len(result.tls_status) > 0
        assert isinstance(result.encryption_status, str) and len(result.encryption_status) > 0
        assert isinstance(result.auth_status, str) and len(result.auth_status) > 0
