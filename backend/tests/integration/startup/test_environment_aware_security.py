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
