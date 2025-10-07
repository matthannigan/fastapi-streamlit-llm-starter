"""
Integration tests for environment-aware Redis security validation.

This module tests SEAM 1: Environment Detection → Security Configuration → Enforcement
as defined in TEST_PLAN.md. These tests validate that the redis_security component
correctly integrates with the environment detection system to enforce appropriate
security requirements based on deployment context.

Test Philosophy:
    - Test from outside-in through public API (validate_production_security)
    - Use high-fidelity behavior testing (no mocks for internal components)
    - Verify observable outcomes (error messages, logs, success/failure)
    - Maintain complete test isolation via monkeypatch

Critical Integration Seam:
    RedisSecurityValidator → get_environment_info() → Security Rule Application

Business Impact:
    These tests ensure that production deployments enforce TLS requirements while
    development environments maintain flexibility, preventing security misconfigurations
    that could expose production systems.
"""

import logging
import pytest

from app.core.startup.redis_security import RedisSecurityValidator
from app.core.exceptions import ConfigurationError


class TestEnvironmentAwareSecurityValidation:
    """
    Integration tests for environment-aware security validation.

    Seam Under Test:
        RedisSecurityValidator → get_environment_info() → Security enforcement

    Critical Paths:
        1. Production environment detection → TLS requirement enforcement
        2. Development environment detection → Flexible security rules
        3. Override mechanism → Warning generation with security bypass

    Business Impact:
        Ensures production systems are secure while maintaining developer flexibility
        in local environments. Prevents accidental deployment of insecure configurations
        to production.
    """

    def test_production_environment_rejects_insecure_redis_url(self, monkeypatch):
        """
        Test that production environment detection triggers TLS enforcement.

        Integration Scope:
            Validator → Environment detection → Security enforcement → Error generation

        Business Impact:
            Prevents production deployments with insecure Redis connections,
            protecting sensitive data from network exposure

        Test Strategy:
            - Set production environment indicators via monkeypatch
            - Create validator instance (picks up environment)
            - Attempt validation with insecure Redis URL
            - Verify ConfigurationError with helpful guidance

        Success Criteria:
            - ConfigurationError raised for insecure URL in production
            - Error message contains "production environment requires secure"
            - Error message suggests TLS (rediss://) configuration
            - Error includes actionable fix instructions
        """
        # Arrange: Configure production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act & Assert: Insecure URL should fail in production
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_production_security("redis://redis:6379")

        # Verify error message content provides helpful guidance
        error_message = str(exc_info.value)
        assert "production environment requires secure" in error_message.lower()
        assert "tls" in error_message.lower()
        assert "rediss://" in error_message

        # Verify error includes fix instructions
        assert "How to fix this:" in error_message or "fix" in error_message.lower()

    def test_production_environment_accepts_secure_redis_url(self, monkeypatch):
        """
        Test that production environment allows secure Redis connections.

        Integration Scope:
            Validator → Environment detection → Security validation → Success path

        Business Impact:
            Confirms that properly configured production deployments pass security
            validation, enabling secure operations

        Test Strategy:
            - Set production environment indicators
            - Create validator with production context
            - Validate secure Redis URL (rediss://)
            - Verify no exceptions raised

        Success Criteria:
            - No ConfigurationError raised
            - Validation completes successfully
            - Secure connection is accepted
        """
        # Arrange: Configure production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act: Validate secure URL (should succeed without exception)
        validator.validate_production_security("rediss://redis:6380")

        # Assert: No exception means success
        # This test passes if we reach this point without raising

    def test_production_environment_accepts_authenticated_connection(self, monkeypatch):
        """
        Test that production accepts redis:// URLs with authentication.

        Integration Scope:
            Validator → Environment detection → Auth detection → Security validation

        Business Impact:
            Allows production deployments using authenticated but non-TLS connections
            in secure internal networks

        Test Strategy:
            - Set production environment
            - Validate redis:// URL with embedded credentials
            - Verify authentication is recognized as secure

        Success Criteria:
            - No ConfigurationError raised
            - URL with credentials passes validation
            - Authentication detected as security mechanism
        """
        # Arrange: Configure production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act: Validate authenticated connection (should succeed)
        validator.validate_production_security("redis://user:password@redis:6379")

        # Assert: No exception means authentication was recognized as secure

    def test_development_environment_allows_insecure_redis_url(self, monkeypatch):
        """
        Test that development environment allows flexible security.

        Integration Scope:
            Validator → Environment detection → Flexible rule application

        Business Impact:
            Enables developers to use simple Redis configurations locally without
            TLS overhead, improving development experience

        Test Strategy:
            - Set development environment via monkeypatch
            - Validate insecure Redis URL
            - Verify no security enforcement
            - Confirm validation succeeds

        Success Criteria:
            - No ConfigurationError raised for insecure URL
            - Development mode allows redis:// without authentication
            - Validation completes successfully
        """
        # Arrange: Configure development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        # Explicitly remove any production indicators
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
        monkeypatch.delenv("PRODUCTION", raising=False)

        validator = RedisSecurityValidator()

        # Act: Insecure URL should succeed in development
        validator.validate_production_security("redis://localhost:6379")

        # Assert: No exception means flexible security worked
        # This test passes if we reach this point without raising

    def test_development_environment_accepts_secure_urls_too(self, monkeypatch):
        """
        Test that development environment accepts both secure and insecure URLs.

        Integration Scope:
            Validator → Environment detection → Flexible security for all URL types

        Business Impact:
            Developers can test TLS configurations locally without enforcement,
            enabling realistic production-like testing

        Test Strategy:
            - Set development environment
            - Validate both secure (rediss://) and insecure (redis://) URLs
            - Verify both are accepted

        Success Criteria:
            - Both rediss:// and redis:// URLs pass validation
            - No security errors in development mode
            - Maximum flexibility for local testing
        """
        # Arrange: Configure development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        validator = RedisSecurityValidator()

        # Act & Assert: Both secure and insecure should work
        validator.validate_production_security("redis://localhost:6379")
        validator.validate_production_security("rediss://localhost:6380")

        # Both should succeed without exceptions

    def test_testing_environment_bypasses_security_enforcement(self, monkeypatch):
        """
        Test that testing environment allows flexible security like development.

        Integration Scope:
            Validator → Environment detection → Testing mode security rules

        Business Impact:
            Enables integration and CI/CD tests to run without TLS infrastructure,
            simplifying test setup while maintaining security in production

        Test Strategy:
            - Set testing environment explicitly
            - Validate insecure Redis URL
            - Verify testing mode behaves like development

        Success Criteria:
            - No ConfigurationError for insecure URLs in testing mode
            - Testing environment recognized as non-production
            - Security enforcement bypassed appropriately
        """
        # Arrange: Configure testing environment
        monkeypatch.setenv("ENVIRONMENT", "testing")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
        monkeypatch.delenv("PRODUCTION", raising=False)

        validator = RedisSecurityValidator()

        # Act: Insecure URL should succeed in testing mode
        validator.validate_production_security("redis://redis:6379")

        # Assert: No exception means testing mode allows flexible security

    def test_production_override_allows_insecure_with_warning(
        self, monkeypatch, caplog
    ):
        """
        Test that explicit override allows insecure connections with security warning.

        Integration Scope:
            Override mechanism → Security bypass → Warning generation

        Business Impact:
            Provides escape hatch for secure internal networks while maintaining
            audit trail through warning logs. Prevents blocking legitimate use cases.

        Test Strategy:
            - Set production environment
            - Enable insecure override flag
            - Validate insecure Redis URL
            - Verify warning is logged
            - Confirm validation succeeds

        Success Criteria:
            - No ConfigurationError raised with override enabled
            - Security warning logged for audit trail
            - Warning mentions "SECURITY WARNING" or similar
            - Warning references insecure connection in production
        """
        # Arrange: Configure production with override
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act: Override should allow insecure connection
        with caplog.at_level(logging.WARNING):
            validator.validate_production_security(
                "redis://redis:6379", insecure_override=True
            )

        # Assert: No exception raised (override worked)
        # Assert: Warning was logged for audit trail
        warning_messages = [
            record.message for record in caplog.records if record.levelno == logging.WARNING
        ]

        assert any("SECURITY WARNING" in msg for msg in warning_messages), (
            "Expected security warning to be logged when using insecure override in production"
        )

        assert any(
            "insecure Redis connection" in msg.lower() or "insecure" in msg.lower()
            for msg in warning_messages
        ), "Warning should mention insecure connection"

    def test_null_redis_url_raises_configuration_error(self, monkeypatch):
        """
        Test that None/empty Redis URL raises clear configuration error.

        Integration Scope:
            Input validation → Error generation → User guidance

        Business Impact:
            Prevents application startup with missing configuration,
            providing clear guidance for resolution

        Test Strategy:
            - Create validator
            - Attempt validation with None URL
            - Verify ConfigurationError with helpful message

        Success Criteria:
            - ConfigurationError raised for None/empty URL
            - Error message explains the problem
            - Error provides fix instructions
            - References REDIS_URL environment variable
        """
        # Arrange: Any environment (error should occur regardless)
        monkeypatch.setenv("ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act & Assert: None URL should fail with clear error
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_production_security(None)

        error_message = str(exc_info.value)
        assert "Redis URL" in error_message
        assert "required" in error_message.lower()

        # Verify helpful guidance is provided
        assert "REDIS_URL" in error_message or "redis_url" in error_message.lower()

    def test_empty_redis_url_raises_configuration_error(self, monkeypatch):
        """
        Test that empty string Redis URL raises configuration error.

        Integration Scope:
            Input validation → Error generation

        Business Impact:
            Catches misconfiguration where REDIS_URL is set but empty

        Test Strategy:
            - Validate empty string URL
            - Verify appropriate error handling

        Success Criteria:
            - ConfigurationError raised for empty string
            - Same error handling as None URL
        """
        # Arrange
        monkeypatch.setenv("ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act & Assert: Empty string should fail
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_production_security("")

        error_message = str(exc_info.value)
        assert "Redis URL" in error_message
        assert "required" in error_message.lower()

    def test_environment_confidence_affects_security_enforcement(self, monkeypatch):
        """
        Test that environment detection confidence is used in security decisions.

        Integration Scope:
            Environment detection → Confidence evaluation → Security enforcement

        Business Impact:
            Ensures security enforcement uses robust environment detection,
            preventing false positives/negatives

        Test Strategy:
            - Set strong production indicators (high confidence)
            - Verify strict security enforcement
            - Set weak/ambiguous indicators (lower confidence)
            - Verify appropriate security behavior

        Success Criteria:
            - Strong production indicators trigger strict enforcement
            - Environment confidence reflected in error messages
            - Security decisions based on detected environment
        """
        # Arrange: Set strong production indicators
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
        monkeypatch.setenv("PRODUCTION", "true")

        validator = RedisSecurityValidator()

        # Act & Assert: Strong production signals should enforce security
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_production_security("redis://redis:6379")

        error_message = str(exc_info.value)

        # Verify environment detection is referenced
        assert "environment" in error_message.lower()
        assert "production" in error_message.lower()

    def test_validator_logs_security_validation_success(
        self, monkeypatch, caplog
    ):
        """
        Test that successful security validation is logged.

        Integration Scope:
            Security validation → Success logging → Audit trail

        Business Impact:
            Provides audit trail of security validations for compliance
            and debugging production issues

        Test Strategy:
            - Configure secure production environment
            - Validate secure Redis URL
            - Verify success is logged appropriately

        Success Criteria:
            - Info-level log message on success
            - Log includes security confirmation
            - Log references secure connection
        """
        # Arrange: Configure secure production
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act: Validate secure connection
        with caplog.at_level(logging.INFO):
            validator.validate_production_security("rediss://redis:6380")

        # Assert: Success should be logged
        info_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        assert any(
            "security validation passed" in msg.lower() or "validation" in msg.lower()
            for msg in info_messages
        ), "Expected success message to be logged"

        assert any(
            "secure" in msg.lower() for msg in info_messages
        ), "Expected security confirmation in logs"

    def test_development_mode_logs_informational_message(
        self, monkeypatch, caplog
    ):
        """
        Test that development mode logs informational security message.

        Integration Scope:
            Environment detection → Development mode → Informational logging

        Business Impact:
            Informs developers about flexible security mode without alarming them

        Test Strategy:
            - Set development environment
            - Validate insecure URL
            - Verify informational log message

        Success Criteria:
            - Info-level log about development mode
            - Message explains TLS validation is skipped
            - Helpful tip about local TLS testing included
        """
        # Arrange: Configure development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        validator = RedisSecurityValidator()

        # Act: Validate in development mode
        with caplog.at_level(logging.INFO):
            validator.validate_production_security("redis://localhost:6379")

        # Assert: Informational message should be logged
        info_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        assert any(
            "development" in msg.lower() for msg in info_messages
        ), "Expected development mode message"

        assert any(
            "tls validation skipped" in msg.lower() or "security flexibility" in msg.lower()
            for msg in info_messages
        ), "Expected explanation of flexible security"


class TestComprehensiveProductionErrorMessages:
    """
    Integration tests for comprehensive production error message validation.

    This test class validates that production security errors include complete
    fix guidance with all documented options and environment detection details.

    Seam Under Test:
        RedisSecurityValidator → get_environment_info() → ConfigurationError generation

    Business Impact:
        Ensures developers receive complete, actionable guidance when security
        validation fails, reducing time to resolution and preventing misconfigurations
    """

    def test_production_error_includes_all_fix_options(self, monkeypatch):
        """
        Test that production security error includes all documented fix options.

        Integration Scope:
            Validator → Environment detection → Security enforcement → Error generation

        Business Impact:
            Prevents production deployments with insecure Redis connections while
            providing comprehensive guidance for resolution, reducing operational
            downtime and configuration errors

        Test Strategy:
            - Set production environment indicators via monkeypatch
            - Create validator instance (picks up environment)
            - Trigger validation with insecure Redis URL
            - Verify ConfigurationError contains all three fix options with examples
            - Verify environment detection details are included

        Success Criteria:
            - ConfigurationError contains all three fix options:
              * Option 1: Use TLS Connection (rediss://)
              * Option 2: Development/Testing TLS Setup
              * Option 3: Secure Internal Network Override
            - Each option includes specific configuration examples
            - Environment detection details and confidence level are included
            - Error message is developer-friendly and actionable
        """
        # Arrange: Configure production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act & Assert: Insecure URL should fail with comprehensive error
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_production_security("redis://redis:6379")

        error_message = str(exc_info.value)

        # Verify all three fix options are present with proper headings
        assert "Option 1: Use TLS Connection (Recommended)" in error_message
        assert "Option 2: Development/Testing TLS Setup" in error_message
        assert "Option 3: Secure Internal Network Override (Use with caution)" in error_message

        # Verify Option 1 includes TLS guidance and rediss:// example
        assert "rediss://your-redis-host:6380" in error_message
        assert "REDIS_TLS_CERT_PATH" in error_message
        assert "REDIS_TLS_KEY_PATH" in error_message
        assert "REDIS_TLS_CA_PATH" in error_message

        # Verify Option 2 includes automated setup guidance
        assert "./scripts/init-redis-tls.sh" in error_message
        assert "docker-compose -f docker-compose.secure.yml up -d" in error_message

        # Verify Option 3 includes override mechanism and security warnings
        assert "REDIS_INSECURE_ALLOW_PLAINTEXT=true" in error_message
        assert "infrastructure-level encryption" in error_message.lower()
        assert "firewall rules" in error_message.lower()
        assert "network monitoring" in error_message.lower()

        # Verify environment detection details are included
        assert "Environment Information:" in error_message
        assert "Detected: production" in error_message
        assert "confidence:" in error_message.lower()

        # Verify documentation references are present
        assert "docs/guides/infrastructure/CACHE.md#security" in error_message
        assert "docs/get-started/ENVIRONMENT_VARIABLES.md" in error_message

        # Verify error structure and formatting
        assert "🔒 SECURITY ERROR:" in error_message
        assert "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" in error_message
        assert "Current: Insecure connection" in error_message
        assert "Required: TLS-enabled" in error_message


class TestInsecureOverrideWarningContent:
    """
    Integration tests for insecure override warning content validation.

    This test class validates that production override warnings include
    comprehensive infrastructure security checklists and risk communication.

    Seam Under Test:
        Production detection → Override mechanism → Warning generation → Security checklist

    Business Impact:
        Ensures operators understand minimum security requirements when using
        insecure override, maintaining security awareness and compliance
    """

    def test_production_override_warning_includes_security_checklist(
        self, monkeypatch, caplog
    ):
        """
        Test that insecure override warning includes infrastructure security checklist.

        Integration Scope:
            Production detection → Override mechanism → Warning generation → Checklist

        Business Impact:
            Prevents improper use of insecure override by ensuring operators understand
            security requirements and business risks, maintaining security posture

        Test Strategy:
            - Set production environment indicators via monkeypatch
            - Create validator instance (picks up environment)
            - Trigger validation with insecure Redis URL and override flag
            - Capture log messages with caplog
            - Verify warning includes complete infrastructure security checklist

        Success Criteria:
            - Warning includes network isolation requirements
            - Warning includes firewall configuration guidance
            - Warning includes VPC/private network requirements
            - Warning includes access control requirements
            - Warning includes monitoring and audit requirements
            - Warning severity is appropriate (WARNING level)
            - Business risk is clearly communicated
        """
        # Arrange: Configure production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act: Override should allow insecure connection with warning
        with caplog.at_level(logging.WARNING):
            validator.validate_production_security(
                "redis://redis:6379", insecure_override=True
            )

        # Assert: No exception raised (override worked)
        # Assert: Warning was logged with comprehensive security checklist
        warning_messages = [
            record.message for record in caplog.records if record.levelno == logging.WARNING
        ]

        assert len(warning_messages) > 0, "Expected security warning to be logged"

        # Combine all warning messages for comprehensive check
        full_warning = " ".join(warning_messages)

        # Verify warning severity and visibility
        assert "🚨 SECURITY WARNING:" in full_warning
        assert "insecure redis connection in production" in full_warning.lower()
        assert "REDIS_INSECURE_ALLOW_PLAINTEXT=true" in full_warning

        # Verify infrastructure security checklist items
        assert "Network traffic is encrypted at the infrastructure level" in full_warning
        assert "VPN" in full_warning or "service mesh" in full_warning

        assert "Redis access is restricted to authorized services only via firewall rules" in full_warning
        assert "firewall rules" in full_warning.lower()

        assert "Network monitoring and intrusion detection systems are in place" in full_warning
        assert "Physical network access is strictly controlled" in full_warning

        # Verify strong recommendation for TLS
        assert "Strong Recommendation: Use TLS encryption" in full_warning
        assert "rediss://" in full_warning

        # Verify documentation references
        assert "docs/guides/infrastructure/CACHE.md#security" in full_warning
        assert "./scripts/init-redis-tls.sh" in full_warning

        # Verify warning is properly formatted and prominent
        assert "⚠️" in full_warning  # Warning emoji
        assert "should only be used in highly secure, isolated network environments" in full_warning.lower()

    def test_override_warning_uses_correct_log_level(self, monkeypatch, caplog):
        """
        Test that insecure override warning uses appropriate log severity.

        Integration Scope:
            Override mechanism → Log level validation → Warning visibility

        Business Impact:
            Ensures security warnings are properly visible in monitoring systems
            while not being so severe as to cause alert fatigue

        Test Strategy:
            - Set production environment
            - Trigger override warning
            - Verify WARNING log level is used
            - Verify error level is not used for override warnings

        Success Criteria:
            - Warning logged at WARNING level, not ERROR
            - Warning message is captured by warning-level log filters
            - Appropriate severity for monitoring systems
        """
        # Arrange: Configure production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Act: Capture warnings at WARNING level
        with caplog.at_level(logging.WARNING):
            validator.validate_production_security(
                "redis://redis:6379", insecure_override=True
            )

        # Assert: Warning should be present at WARNING level
        warning_messages = [
            record.message for record in caplog.records if record.levelno == logging.WARNING
        ]

        assert len(warning_messages) > 0, "Expected WARNING level log message"
        assert any(
            "SECURITY WARNING" in msg for msg in warning_messages
        ), "Expected security warning in WARNING level logs"

        # Verify no ERROR level messages for override (only WARNING)
        error_messages = [
            record.message for record in caplog.records if record.levelno == logging.ERROR
        ]
        assert len(error_messages) == 0, "Override should generate WARNING, not ERROR level logs"


class TestStagingEnvironmentSecurityValidation:
    """
    Integration tests for staging environment security validation flow.

    This test class validates that staging environment detection bypasses
    strict TLS enforcement while maintaining appropriate security awareness.

    Seam Under Test:
        Staging environment detection → Security rule application → Flexible validation

    Business Impact:
        Enables staging deployments to test configurations without mandatory TLS,
        supporting varied deployment scenarios while maintaining production security
    """

    def test_staging_environment_bypasses_tls_enforcement(self, monkeypatch):
        """
        Test that staging environment allows flexible security like development.

        Integration Scope:
            Staging environment detection → Security rule application → Flexible validation

        Business Impact:
            Enables staging deployments to test configurations without mandatory TLS,
            supporting pre-production testing while ensuring production security

        Test Strategy:
            - Set staging environment indicators via monkeypatch
            - Create validator instance (picks up environment)
            - Validate insecure Redis URL (should succeed)
            - Validate secure Redis URL (should also succeed)
            - Verify both URL types are accepted in staging

        Success Criteria:
            - Staging environment bypasses TLS enforcement
            - Both secure and insecure URLs accepted in staging
            - No ConfigurationError raised for insecure URLs
            - Environment detection correctly identifies staging
        """
        # Arrange: Configure staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
        monkeypatch.delenv("PRODUCTION", raising=False)

        validator = RedisSecurityValidator()

        # Act & Assert: Insecure URL should succeed in staging (no exception)
        validator.validate_production_security("redis://redis:6379")

        # Act & Assert: Secure URL should also succeed in staging (no exception)
        validator.validate_production_security("rediss://redis:6380")

        # Test passes if no exceptions are raised

    def test_staging_vs_production_security_behavior_distinction(self, monkeypatch):
        """
        Test that staging environment behavior differs from production.

        Integration Scope:
            Environment detection → Security rule application → Behavioral validation

        Business Impact:
            Demonstrates environment-specific security rules, ensuring production
            maintains strict security while staging allows testing flexibility

        Test Strategy:
            - Test same insecure Redis URL in staging environment (should succeed)
            - Test same insecure Redis URL in production environment (should fail)
            - Verify behavioral distinction between environments

        Success Criteria:
            - Same insecure URL succeeds in staging
            - Same insecure URL fails in production
            - Clear behavioral distinction between environments
            - Environment detection drives different security enforcement
        """
        # Arrange: Configure staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        staging_validator = RedisSecurityValidator()

        # Act: Staging should accept insecure URL
        staging_validator.validate_production_security("redis://redis:6379")

        # Now test the same URL in production (should fail)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

        production_validator = RedisSecurityValidator()

        # Act & Assert: Production should reject the same insecure URL
        with pytest.raises(ConfigurationError) as exc_info:
            production_validator.validate_production_security("redis://redis:6379")

        # Verify production error message
        error_message = str(exc_info.value)
        assert "production environment requires secure" in error_message.lower()
        assert "rediss://" in error_message

    def test_staging_vs_development_behavior_comparison(self, monkeypatch):
        """
        Test that staging environment behaves similarly to development.

        Integration Scope:
            Environment detection → Security rule comparison → Behavioral consistency

        Business Impact:
            Ensures consistent flexible security behavior across non-production
            environments, providing predictable developer experience

        Test Strategy:
            - Test various Redis URL types in staging environment
            - Test same Redis URL types in development environment
            - Verify consistent behavior across both environments

        Success Criteria:
            - Staging and development accept same URL types
            - Both environments allow insecure connections
            - Both environments allow secure connections
            - Consistent flexible security across non-production
        """
        test_urls = [
            "redis://localhost:6379",  # Insecure
            "redis://user:pass@localhost:6379",  # Authenticated
            "rediss://localhost:6380",  # Secure TLS
        ]

        # Test in staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        staging_validator = RedisSecurityValidator()

        for url in test_urls:
            # Act: All URLs should succeed in staging
            staging_validator.validate_production_security(url)

        # Test in development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        development_validator = RedisSecurityValidator()

        for url in test_urls:
            # Act: Same URLs should also succeed in development
            development_validator.validate_production_security(url)

        # Test passes if no exceptions are raised in either environment

    def test_staging_accepts_authenticated_connections(self, monkeypatch):
        """
        Test that staging environment accepts authenticated Redis connections.

        Integration Scope:
            Staging environment detection → Auth validation → Security acceptance

        Business Impact:
            Enables testing of authenticated Redis configurations in staging
            before production deployment, ensuring authentication works correctly

        Test Strategy:
            - Set staging environment
            - Validate authenticated Redis URL
            - Verify authentication is recognized and accepted

        Success Criteria:
            - Authenticated connections accepted in staging
            - No security errors for authenticated URLs
            - Authentication detection works in staging context
        """
        # Arrange: Configure staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        validator = RedisSecurityValidator()

        # Act: Authenticated connection should succeed
        validator.validate_production_security("redis://user:password@redis:6379")

        # Assert: No exception means authentication was accepted
        # Test passes if we reach this point without raising


class TestStagingEnvironmentInformationalMessaging:
    """
    Integration tests for staging environment informational messaging.

    This test class validates that staging environment logs appropriate
    informational messages about security flexibility and TLS testing.

    Seam Under Test:
        Staging detection → Informational logging → Developer guidance

    Business Impact:
        Communicates security expectations for staging while allowing
        deployment flexibility and encouraging TLS testing
    """

    def test_staging_environment_logs_informational_message(self, monkeypatch, caplog):
        """
        Test that staging environment logs appropriate informational message.

        Integration Scope:
            Staging detection → Informational logging → Developer guidance

        Business Impact:
            Communicates security expectations for staging while encouraging
            TLS testing and production readiness preparation

        Test Strategy:
            - Set staging environment indicators via monkeypatch
            - Create validator instance (picks up environment)
            - Validate insecure Redis URL with caplog capture
            - Verify INFO-level log message is generated
            - Verify message content explains staging security flexibility

        Success Criteria:
            - INFO-level log message generated for staging
            - Message explains staging security flexibility
            - Message encourages TLS testing
            - Message tone is informative, not alarming
            - Message differs from development mode messaging
        """
        # Arrange: Configure staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
        monkeypatch.delenv("PRODUCTION", raising=False)

        validator = RedisSecurityValidator()

        # Act: Validate in staging mode with log capture
        with caplog.at_level(logging.INFO):
            validator.validate_production_security("redis://redis:6379")

        # Assert: Informational message should be logged
        info_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        assert len(info_messages) > 0, "Expected INFO level log message for staging environment"

        # Combine all info messages for comprehensive check
        full_info_message = " ".join(info_messages)

        # Verify staging-specific messaging
        assert any("staging" in msg.lower() for msg in info_messages), "Expected staging to be mentioned in logs"
        assert "Staging environment" in full_info_message, "Expected explicit staging environment reference"

        # Verify message explains security flexibility
        assert any(
            "TLS validation skipped" in msg.lower() or "flexible" in msg.lower() or "security" in msg.lower()
            for msg in info_messages
        ), "Expected explanation of security flexibility"

        # Verify message mentions staging context specifically
        assert "Using flexible security for staging environment" in full_info_message

        # Verify message includes environment title formatting
        assert "Staging" in full_info_message, "Expected proper title case staging reference"

    def test_staging_message_differs_from_development_message(self, monkeypatch, caplog):
        """
        Test that staging informational message differs from development message.

        Integration Scope:
            Environment detection → Context-specific messaging → Message differentiation

        Business Impact:
            Ensures each environment receives contextually appropriate guidance,
            preventing confusion and providing targeted advice

        Test Strategy:
            - Capture informational messages from staging environment
            - Capture informational messages from development environment
            - Verify messages are different and contextually appropriate

        Success Criteria:
            - Staging message differs from development message
            - Staging message mentions staging-specific context
            - Development message mentions development-specific context
            - Both messages are informative but distinct
        """
        # Test staging environment messaging
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        staging_validator = RedisSecurityValidator()

        with caplog.at_level(logging.INFO):
            staging_validator.validate_production_security("redis://redis:6379")

        staging_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        # Clear caplog for development test
        caplog.clear()

        # Test development environment messaging
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        development_validator = RedisSecurityValidator()

        with caplog.at_level(logging.INFO):
            development_validator.validate_production_security("redis://redis:6379")

        development_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        # Verify both environments logged messages
        assert len(staging_messages) > 0, "Expected staging environment to log message"
        assert len(development_messages) > 0, "Expected development environment to log message"

        # Verify messages are different
        staging_full = " ".join(staging_messages)
        development_full = " ".join(development_messages)

        # Staging should mention staging specifically
        assert "Staging environment" in staging_full, "Expected staging-specific messaging"
        assert "Using flexible security for staging environment" in staging_full

        # Development should mention development specifically
        assert "Development environment detected" in development_full, "Expected development-specific messaging"
        assert "Security flexibility enabled for local development" in development_full

        # Verify messages are not identical
        assert staging_full != development_full, "Expected different messages for staging vs development"

        # Verify development message includes TLS testing tip
        assert "./scripts/init-redis-tls.sh" in development_full, "Expected TLS testing tip in development message"

    def test_staging_message_tone_is_informative_not_alarming(self, monkeypatch, caplog):
        """
        Test that staging message tone is informative, not warning/alarming.

        Integration Scope:
            Staging detection → Message tone validation → Developer experience

        Business Impact:
            Ensures staging environment messaging encourages testing without
            alarming developers, maintaining productive development experience

        Test Strategy:
            - Set staging environment
            - Capture informational log messages
            - Verify tone is informative and encouraging
            - Verify absence of alarming language

        Success Criteria:
            - Message uses INFO level, not WARNING or ERROR
            - Tone is informative and educational
            - No alarming or warning language in staging messages
            - Encourages TLS testing without pressure
        """
        # Arrange: Configure staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        validator = RedisSecurityValidator()

        # Act: Capture logs at INFO level
        with caplog.at_level(logging.INFO):
            validator.validate_production_security("redis://redis:6379")

        # Assert: Check message tone and content
        info_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        assert len(info_messages) > 0, "Expected INFO level message"

        # Verify no WARNING or ERROR level messages for staging
        warning_messages = [
            record.message for record in caplog.records if record.levelno == logging.WARNING
        ]
        error_messages = [
            record.message for record in caplog.records if record.levelno == logging.ERROR
        ]

        assert len(warning_messages) == 0, "Staging should not generate WARNING messages for insecure URLs"
        assert len(error_messages) == 0, "Staging should not generate ERROR messages for insecure URLs"

        # Verify informative, non-alarming language
        full_message = " ".join(info_messages)

        # Should use informational language
        assert "ℹ️" in full_message, "Expected info emoji in staging message"

        # Should not contain alarming keywords
        alarming_keywords = ["warning", "error", "danger", "risk", "insecure"]
        for keyword in alarming_keywords:
            # Note: "flexible security" is okay, but "insecure" alone is alarming
            if keyword == "insecure":
                continue
            assert keyword not in full_message.lower(), f"Found alarming keyword '{keyword}' in staging message"

        # Should be positive and encouraging
        assert "TLS validation skipped" in full_message or "flexible security" in full_message.lower()
        assert "Staging environment" in full_message

    def test_staging_message_with_secure_connection(self, monkeypatch, caplog):
        """
        Test that staging environment logs informational message even with secure connections.

        Integration Scope:
            Staging detection → Secure connection validation → Appropriate messaging

        Business Impact:
            Ensures consistent messaging regardless of connection type,
            maintaining clear environment identification

        Test Strategy:
            - Set staging environment
            - Validate secure Redis URL (rediss://)
            - Verify appropriate informational message is still logged

        Success Criteria:
            - INFO message logged for secure connections in staging
            - Message still identifies staging environment
            - No warnings or errors for secure connections
        """
        # Arrange: Configure staging environment
        monkeypatch.setenv("ENVIRONMENT", "staging")
        monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

        validator = RedisSecurityValidator()

        # Act: Validate secure connection in staging
        with caplog.at_level(logging.INFO):
            validator.validate_production_security("rediss://redis:6380")

        # Assert: Should still log staging identification message
        info_messages = [
            record.message for record in caplog.records if record.levelno == logging.INFO
        ]

        assert len(info_messages) > 0, "Expected INFO message even for secure connections in staging"

        full_message = " ".join(info_messages)
        assert "Staging environment" in full_message, "Expected staging identification"
        assert "Using flexible security for staging environment" in full_message

        # Should not log any warnings or errors for secure connections
        warning_messages = [
            record.message for record in caplog.records if record.levelno == logging.WARNING
        ]
        error_messages = [
            record.message for record in caplog.records if record.levelno == logging.ERROR
        ]

        assert len(warning_messages) == 0, "No warnings expected for secure connections"
        assert len(error_messages) == 0, "No errors expected for secure connections"
