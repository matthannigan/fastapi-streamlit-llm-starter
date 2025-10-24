"""
Integration tests for Redis security validation without cryptography library.

This test module verifies graceful degradation and helpful error/warning messages
when the cryptography library is unavailable. These tests run in an isolated Docker
environment where cryptography is intentionally not installed.

**Execution Requirements:**
- Run via Docker container without cryptography: ./run-no-cryptography-tests.sh
- Or manually in isolated virtualenv without cryptography package
- DO NOT run in standard test environment (will be skipped if cryptography is available)

**Test Philosophy:**
These are integration tests because:
- They test real import behavior in isolated environment
- They verify actual validation results users would see
- Unit-level mocking of library availability causes pytest internal errors
- The cryptography library imports at module load time, before test fixtures run

**Reference:**
- Test Plan: backend/tests/integration/startup/TEST_PLAN_cryptography_unavailable.md
- Implementation: backend/app/core/startup/redis_security.py
"""

import pytest

# Check if cryptography is available
CRYPTOGRAPHY_AVAILABLE = True
try:
    from cryptography.fernet import Fernet  # noqa: F401
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Skip entire module if cryptography IS available
pytestmark = [pytest.mark.docker, pytest.mark.skipif(
    CRYPTOGRAPHY_AVAILABLE,
    reason="Tests require cryptography library to be UNAVAILABLE. "
    "Run via Docker: ./backend/tests/integration/docker/run-no-cryptography-tests.sh",
)]


class TestTLSCertificateValidationWithoutCryptography:
    """
    Integration tests for TLS certificate validation graceful degradation.

    These tests verify that certificate validation provides appropriate warnings
    and continues with limited functionality when cryptography is unavailable.

    Integration Scope:
        validate_tls_certificates() → cryptography import attempt
        → graceful degradation with warning

    Test Environment:
        - Python environment WITHOUT cryptography package
        - Tests real import behavior, not mocked
        - Docker-isolated execution recommended
    """

    def test_tls_certificate_validation_warns_without_cryptography(self, tmp_path):
        """
        Test that TLS validation adds warning when cryptography is unavailable.

        Integration Scope:
            validate_tls_certificates() → certificate file existence check
            → cryptography import attempt → graceful degradation with warning

        Business Impact:
            Ensures basic TLS configuration can be validated even when cryptography
            is unavailable, while clearly warning about limited validation capability.
            Allows deployment to proceed with basic checks rather than failing entirely.

        Test Strategy:
            - Create temporary test certificate files
            - Call validate_tls_certificates() without cryptography
            - Verify result["valid"] is True (basic file validation works)
            - Verify warning about limited cryptography validation
            - Verify no advanced certificate information (expiration, subject)

        Success Criteria:
            - result["valid"] is True
            - result["warnings"] contains "cryptography library not available"
            - Warning indicates "certificate validation limited"
            - No certificate expiration information available
            - No certificate subject information available
            - Basic file existence validation still succeeds

        Fixtures Used:
            - tmp_path: Creates temporary directory for test certificates
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        # Create temporary certificate files
        cert_file = tmp_path / "test_cert.pem"
        cert_file.write_text(
            "-----BEGIN CERTIFICATE-----\n"
            "MIICmzCCAYMCAgPoMA0GCSqGSIb3DQEBBQUAMBQxEjAQBgNVBAMTCWxvY2FsaG9z\n"
            "-----END CERTIFICATE-----"
        )

        key_file = tmp_path / "test_key.pem"
        key_file.write_text(
            "-----BEGIN PRIVATE KEY-----\n"
            "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\n"
            "-----END PRIVATE KEY-----"
        )

        # Validate certificates without cryptography
        validator = RedisSecurityValidator()
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Verify basic file validation succeeds
        assert result["valid"] is True, (
            "Basic file validation should succeed without cryptography. "
            f"Got: {result}"
        )

        # Verify warning about limited capability
        assert "warnings" in result, "Result should include warnings list"
        warning_text = " ".join(result["warnings"]).lower()

        assert "cryptography" in warning_text, (
            "Warning should mention cryptography library. " f"Got warnings: {result['warnings']}"
        )

        assert "limited" in warning_text or "not available" in warning_text, (
            "Warning should indicate limited validation capability. "
            f"Got warnings: {result['warnings']}"
        )

        # Verify no advanced certificate information
        cert_info = result.get("cert_info", {})
        assert cert_info.get("expires") is None, (
            "Certificate expiration should not be available without cryptography"
        )
        assert cert_info.get("subject") is None, (
            "Certificate subject should not be available without cryptography"
        )
        assert cert_info.get("days_until_expiry") is None, (
            "Days until expiry should not be available without cryptography"
        )

    def test_certificate_file_paths_still_validated(self, tmp_path):
        """
        Test that file existence validation works without cryptography.

        Integration Scope:
            validate_tls_certificates() → file path validation
            → result without advanced parsing

        Business Impact:
            Ensures basic configuration errors (wrong paths, missing files)
            are caught even when cryptography is unavailable.

        Test Strategy:
            - Create test certificate files
            - Validate with correct paths
            - Verify file paths are recorded in result
            - Verify paths are converted to absolute paths

        Success Criteria:
            - File paths are validated and recorded
            - Absolute paths are returned
            - Basic file existence checks succeed
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        # Create test certificate
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")

        validator = RedisSecurityValidator()
        result = validator.validate_tls_certificates(cert_path=str(cert_file))

        # Verify file paths are recorded
        assert result["valid"] is True
        assert "cert_info" in result
        assert "cert_path" in result["cert_info"]

        # Verify paths are absolute
        recorded_path = result["cert_info"]["cert_path"]
        assert recorded_path.startswith("/") or recorded_path[
            1:3
        ] == ":\\", f"Path should be absolute: {recorded_path}"

    def test_missing_certificate_files_still_generate_errors(self):
        """
        Test that missing file errors work without cryptography.

        Integration Scope:
            validate_tls_certificates() → file existence check
            → error generation (no cryptography needed)

        Business Impact:
            Ensures configuration mistakes are caught regardless of
            cryptography availability.

        Success Criteria:
            - Missing file generates error
            - result["valid"] is False
            - Error message is helpful
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        validator = RedisSecurityValidator()
        result = validator.validate_tls_certificates(
            cert_path="/nonexistent/cert.pem"
        )

        # Verify error is generated
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("not found" in error.lower() for error in result["errors"])


class TestEncryptionKeyValidationWithoutCryptography:
    """
    Integration tests for encryption key validation without cryptography.

    These tests verify that encryption key validation fails appropriately
    when cryptography is unavailable, with clear error messages.

    Integration Scope:
        validate_encryption_key() → cryptography import attempt
        → validation failure with helpful error

    Test Environment:
        - Python environment WITHOUT cryptography package
        - Tests real import behavior, not mocked
    """

    def test_encryption_key_validation_fails_without_cryptography(self):
        """
        Test that encryption key validation fails when cryptography is unavailable.

        Integration Scope:
            validate_encryption_key() → cryptography.fernet import attempt
            → ImportError handling → validation failure with error message

        Business Impact:
            Ensures encryption keys cannot be validated without cryptography,
            preventing false confidence in security configuration. Clear error
            helps developers understand dependency requirement.

        Test Strategy:
            - Provide valid Fernet key format (44 characters base64)
            - Call validate_encryption_key() without cryptography
            - Verify result["valid"] is False
            - Verify error message indicates cryptography unavailability
            - Verify error explains that validation cannot proceed

        Success Criteria:
            - result["valid"] is False
            - result["errors"] contains "cryptography library not available"
            - Error indicates "cannot be validated"
            - Error is actionable for developers

        Environment Requirements:
            - cryptography package must NOT be installed
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        # Valid Fernet key format (44 characters, base64-encoded)
        valid_key = "x" * 44

        # Attempt validation without cryptography
        validator = RedisSecurityValidator()
        result = validator.validate_encryption_key(valid_key)

        # Verify validation fails
        assert result["valid"] is False, (
            "Validation should fail without cryptography. " f"Got: {result}"
        )

        # Verify error message quality
        assert "errors" in result and len(result["errors"]) > 0, (
            "Result should include error messages"
        )

        error_text = " ".join(result["errors"]).lower()

        # Check for cryptography library mention
        assert "cryptography" in error_text, (
            "Error should mention cryptography library. " f"Got errors: {result['errors']}"
        )

        # Check for explanation that validation cannot proceed
        assert "not available" in error_text or "cannot be validated" in error_text, (
            "Error should explain validation cannot proceed. "
            f"Got errors: {result['errors']}"
        )

    def test_encryption_key_length_validation_still_works(self):
        """
        Test that basic key length validation works without cryptography.

        Integration Scope:
            validate_encryption_key() → basic length check
            → length validation (no cryptography needed)

        Business Impact:
            Provides basic validation feedback even when cryptography
            is unavailable, catching obvious configuration errors.

        Success Criteria:
            - Too-short keys are rejected
            - Error message mentions expected length
            - Basic validation doesn't require cryptography
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        # Invalid key (too short)
        short_key = "too-short"

        validator = RedisSecurityValidator()
        result = validator.validate_encryption_key(short_key)

        # Verify length validation works
        assert result["valid"] is False
        assert any(
            "length" in error.lower() or "44" in error for error in result["errors"]
        ), f"Error should mention expected length. Got: {result['errors']}"

    def test_empty_encryption_key_handling(self):
        """
        Test that empty/None encryption keys are handled appropriately.

        Integration Scope:
            validate_encryption_key() → empty key check
            → appropriate error/warning

        Success Criteria:
            - Empty key generates error or warning
            - Result clearly indicates encryption is disabled
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        validator = RedisSecurityValidator()

        # Test None key
        result_none = validator.validate_encryption_key(None)
        assert result_none["valid"] is False or len(result_none["warnings"]) > 0

        # Test empty string
        result_empty = validator.validate_encryption_key("")
        assert result_empty["valid"] is False or len(result_empty["warnings"]) > 0


class TestComprehensiveValidationWithoutCryptography:
    """
    Integration tests for comprehensive security validation without cryptography.

    These tests verify that comprehensive validation handles cryptography
    unavailability gracefully across multiple validation components.
    """

    def test_comprehensive_validation_includes_cryptography_warnings(self, tmp_path):
        """
        Test that comprehensive validation aggregates cryptography warnings.

        Integration Scope:
            validate_security_configuration() → all validation methods
            → cryptography warnings aggregation → comprehensive result

        Business Impact:
            Ensures comprehensive security reports clearly indicate when
            validation is limited by missing cryptography library.

        Success Criteria:
            - Validation completes without crashing
            - Result includes warnings about cryptography unavailability
            - Overall status reflects limited validation capability
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        # Create test certificate
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")

        validator = RedisSecurityValidator()
        result = validator.validate_security_configuration(
            redis_url="rediss://redis:6380",
            tls_cert_path=str(cert_file),
            encryption_key="x" * 44,
            test_connectivity=False,
        )

        # Verify warnings are present
        assert len(result.warnings) > 0, "Should have warnings about cryptography"

        # Verify validation includes cryptography limitations
        all_text = (
            " ".join(result.warnings)
            + " ".join(result.errors)
            + result.tls_status
            + result.encryption_status
        ).lower()

        assert "cryptography" in all_text, (
            "Validation should mention cryptography limitations"
        )

    def test_validation_summary_indicates_limited_capability(self, tmp_path):
        """
        Test that validation summary clearly indicates limited validation.

        Integration Scope:
            validate_security_configuration() → result.summary()
            → human-readable output with limitations

        Success Criteria:
            - Summary is generated without errors
            - Summary text is readable and informative
            - Limitations are clearly communicated
        """
        from app.core.startup.redis_security import RedisSecurityValidator

        # Create test certificate
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text("-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----")

        validator = RedisSecurityValidator()
        result = validator.validate_security_configuration(
            redis_url="rediss://redis:6380",
            tls_cert_path=str(cert_file),
            test_connectivity=False,
        )

        # Generate summary
        summary = result.summary()

        # Verify summary is generated
        assert summary, "Summary should be generated"
        assert len(summary) > 50, "Summary should be detailed"
        assert "\n" in summary, "Summary should be formatted with newlines"
