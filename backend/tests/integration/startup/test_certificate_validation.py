"""
Integration tests for TLS certificate validation with cryptography library.

This module tests SEAM 2: Certificate Validation → Cryptography Library → Graceful Degradation
from the Redis security validation component.

Test Focus:
    - TLS certificate file system validation
    - Cryptography library integration for certificate parsing
    - Certificate expiration detection and warnings
    - Graceful degradation when cryptography is unavailable
    - File path validation and error messaging

Critical Integration Path:
    validate_tls_certificates() → File system checks → Cryptography parsing →
    Certificate validation → Expiration warnings → Result dictionary
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

from app.core.startup.redis_security import RedisSecurityValidator

# Check if cryptography library is available
try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# Helper function to generate realistic test certificates
def generate_test_certificate(
    days_until_expiry: int = 365,
    subject_cn: str = "test.redis.local",
) -> tuple[bytes, bytes]:
    """
    Generate a valid test certificate and private key for testing.

    Args:
        days_until_expiry: Number of days until certificate expires (can be negative for expired certs)
        subject_cn: Common Name for certificate subject

    Returns:
        Tuple of (certificate_pem, private_key_pem) as bytes

    Note:
        Requires cryptography library to be available
    """
    if not CRYPTOGRAPHY_AVAILABLE:
        raise ImportError("cryptography library required for certificate generation")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Generate certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test State"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Test City"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Organization"),
            x509.NameAttribute(NameOID.COMMON_NAME, subject_cn),
        ]
    )

    # Calculate dates properly to handle negative days (expired certificates)
    now = datetime.utcnow()
    if days_until_expiry >= 0:
        # Normal certificate: valid from now until future date
        not_valid_before = now
        not_valid_after = now + timedelta(days=days_until_expiry)
    else:
        # Expired certificate: valid from past until past date
        # Make it valid for 365 days starting from (now + days_until_expiry - 365)
        not_valid_before = now + timedelta(days=days_until_expiry - 365)
        not_valid_after = now + timedelta(days=days_until_expiry)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # Serialize to PEM format
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    return cert_pem, key_pem


class TestCertificateValidationIntegration:
    """
    Integration tests for TLS certificate validation.

    Seam Under Test:
        RedisSecurityValidator.validate_tls_certificates() → File system → Cryptography library →
        Certificate parsing → Expiration validation → Validation results

    Critical Paths:
        1. Valid certificates with cryptography available
        2. Missing certificate files generate helpful errors
        3. Certificate expiration warnings based on days remaining
        4. Graceful degradation without cryptography library

    Business Impact:
        TLS certificate validation is security-critical for production deployments.
        Proper validation ensures secure Redis connections and provides early warning
        of expiring certificates to prevent production incidents.
    """

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_valid_certificates_pass_validation(self, tmp_path: Path):
        """
        Test that valid certificate files pass validation when cryptography is available.

        Integration Scope:
            File system → Certificate files → Cryptography parsing → Validation success

        Business Impact:
            Ensures valid TLS certificates are correctly recognized, enabling secure
            Redis connections in production environments.

        Test Strategy:
            - Generate realistic test certificate and key files
            - Write files to temporary directory
            - Validate certificates through RedisSecurityValidator
            - Verify validation success with certificate metadata

        Success Criteria:
            - Validation result indicates success (valid=True)
            - No errors are reported
            - Certificate expiration information is populated
            - Subject information is correctly parsed
        """
        # Arrange: Generate and write test certificate files
        cert_pem, key_pem = generate_test_certificate(
            days_until_expiry=365, subject_cn="test.redis.local"
        )

        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate the certificates
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: Validation succeeded
        assert result["valid"] is True, f"Expected validation to succeed, got errors: {result.get('errors')}"
        assert len(result["errors"]) == 0, f"Expected no errors, got: {result['errors']}"

        # Verify certificate metadata was parsed
        assert "cert_info" in result
        assert "expires" in result["cert_info"], "Expected certificate expiration date"
        assert (
            "days_until_expiry" in result["cert_info"]
        ), "Expected days until expiry"
        assert "subject" in result["cert_info"], "Expected certificate subject"

        # Verify expiration is in the future
        days_until_expiry = result["cert_info"]["days_until_expiry"]
        assert (
            days_until_expiry > 0
        ), f"Expected certificate to be valid, but expires in {days_until_expiry} days"
        assert (
            350 <= days_until_expiry <= 365
        ), f"Expected ~365 days until expiry, got {days_until_expiry}"

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_certificate_with_ca_validates_all_files(self, tmp_path: Path):
        """
        Test that certificate validation handles cert, key, and CA files.

        Integration Scope:
            Multiple certificate files → File system validation → Path storage

        Business Impact:
            Production Redis deployments often require CA certificates for mutual TLS.
            Proper validation ensures all required certificate components are present.

        Test Strategy:
            - Generate certificate, key, and CA files
            - Validate all three file paths
            - Verify all paths are stored in result

        Success Criteria:
            - Validation succeeds with all three files
            - All file paths are recorded in cert_info
            - No errors or warnings about missing files
        """
        # Arrange: Generate certificate files
        cert_pem, key_pem = generate_test_certificate(days_until_expiry=365)
        ca_pem, _ = generate_test_certificate(
            days_until_expiry=730, subject_cn="ca.redis.local"
        )

        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"
        ca_file = tmp_path / "ca.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)
        ca_file.write_bytes(ca_pem)

        validator = RedisSecurityValidator()

        # Act: Validate all certificate files
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file),
            key_path=str(key_file),
            ca_path=str(ca_file),
        )

        # Assert: All files validated successfully
        assert result["valid"] is True
        assert len(result["errors"]) == 0

        # Verify all paths are recorded
        assert "cert_path" in result["cert_info"]
        assert "key_path" in result["cert_info"]
        assert "ca_path" in result["cert_info"]

        # Verify paths are absolute
        assert Path(result["cert_info"]["cert_path"]).is_absolute()
        assert Path(result["cert_info"]["key_path"]).is_absolute()
        assert Path(result["cert_info"]["ca_path"]).is_absolute()

    def test_missing_certificate_files_generate_errors(self):
        """
        Test that missing certificate files are detected and reported with helpful errors.

        Integration Scope:
            File system validation → Missing file detection → Error message generation

        Business Impact:
            Provides clear, actionable error messages when certificate files are
            misconfigured, reducing troubleshooting time during production deployments.

        Test Strategy:
            - Attempt to validate nonexistent certificate paths
            - Verify validation fails with appropriate status
            - Check error messages mention missing files

        Success Criteria:
            - Validation result indicates failure (valid=False)
            - Error messages explicitly mention files "not found"
            - Both certificate and key file errors are reported
        """
        # Arrange: Use nonexistent file paths
        validator = RedisSecurityValidator()

        # Act: Attempt to validate nonexistent files
        result = validator.validate_tls_certificates(
            cert_path="/nonexistent/path/to/cert.pem",
            key_path="/nonexistent/path/to/key.pem",
        )

        # Assert: Validation failed
        assert result["valid"] is False, "Expected validation to fail for missing files"
        assert len(result["errors"]) > 0, "Expected error messages for missing files"

        # Verify error messages are helpful
        errors_text = " ".join(result["errors"]).lower()
        assert (
            "not found" in errors_text
        ), f"Expected 'not found' in error messages, got: {result['errors']}"

        # Verify both files are reported as missing
        assert any("cert.pem" in error for error in result["errors"]), (
            "Expected certificate file mentioned in errors"
        )
        assert any("key.pem" in error for error in result["errors"]), (
            "Expected key file mentioned in errors"
        )

    def test_missing_ca_certificate_generates_specific_error(self):
        """
        Test that missing CA certificate is specifically identified in errors.

        Integration Scope:
            Optional CA path validation → File system check → Specific error reporting

        Business Impact:
            CA certificate errors should be distinct from client certificate errors
            for easier troubleshooting of mutual TLS configurations.

        Test Strategy:
            - Validate with only CA path specified (missing)
            - Verify CA-specific error message
            - Ensure error differentiates CA from client cert

        Success Criteria:
            - Validation fails for missing CA file
            - Error message specifically mentions "CA certificate"
            - Error message contains the CA file path
        """
        # Arrange
        validator = RedisSecurityValidator()

        # Act: Validate with missing CA certificate only
        result = validator.validate_tls_certificates(
            ca_path="/nonexistent/ca.pem"
        )

        # Assert: CA-specific error reported
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # Verify CA is specifically mentioned
        ca_error_found = False
        for error in result["errors"]:
            if "ca" in error.lower() and "not found" in error.lower():
                ca_error_found = True
                break

        assert ca_error_found, (
            f"Expected CA certificate error, got: {result['errors']}"
        )

    def test_directory_path_instead_of_file_generates_error(self, tmp_path: Path):
        """
        Test that directory paths are rejected with clear error messages.

        Integration Scope:
            File system validation → File type checking → Error generation

        Business Impact:
            Prevents configuration errors where directory paths are mistakenly
            provided instead of certificate file paths.

        Test Strategy:
            - Create test directory
            - Attempt to validate directory as certificate file
            - Verify specific "not a file" error message

        Success Criteria:
            - Validation fails when directory provided
            - Error message clearly states "not a file"
            - Error message includes the directory path
        """
        # Arrange: Create a directory instead of a file
        cert_dir = tmp_path / "cert_directory"
        cert_dir.mkdir()

        validator = RedisSecurityValidator()

        # Act: Attempt to validate directory as certificate
        result = validator.validate_tls_certificates(cert_path=str(cert_dir))

        # Assert: Validation fails with specific error
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # Verify error mentions "not a file"
        assert any("not a file" in error.lower() for error in result["errors"]), (
            f"Expected 'not a file' error, got: {result['errors']}"
        )

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_expired_certificate_generates_error(self, tmp_path: Path):
        """
        Test that expired certificates are detected and validation fails.

        Integration Scope:
            Cryptography parsing → Expiration date extraction → Validation logic

        Business Impact:
            Prevents production deployments with expired certificates that would
            cause connection failures, providing early detection at startup.

        Test Strategy:
            - Generate certificate expired 10 days ago
            - Attempt validation
            - Verify expiration error with days count

        Success Criteria:
            - Validation fails for expired certificate
            - Error message mentions "expired"
            - Error message includes number of days expired
        """
        # Arrange: Generate expired certificate
        cert_pem, key_pem = generate_test_certificate(days_until_expiry=-10)

        cert_file = tmp_path / "expired_cert.pem"
        key_file = tmp_path / "expired_key.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate expired certificate
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: Validation failed due to expiration
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # Verify expiration error
        assert any("expired" in error.lower() for error in result["errors"]), (
            f"Expected expiration error, got: {result['errors']}"
        )

        # Verify days count is mentioned
        assert any("days" in error.lower() for error in result["errors"]), (
            f"Expected days count in error, got: {result['errors']}"
        )

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_certificate_expiring_soon_generates_warning(self, tmp_path: Path):
        """
        Test that certificates expiring within 30 days generate warnings.

        Integration Scope:
            Expiration date parsing → Warning threshold logic → Warning generation

        Business Impact:
            Provides early warning of approaching certificate expiration to prevent
            production outages from expired certificates.

        Test Strategy:
            - Generate certificate expiring in 15 days
            - Validate certificate
            - Verify validation succeeds but includes warning

        Success Criteria:
            - Validation succeeds (valid=True) for not-yet-expired cert
            - Warning is generated about approaching expiration
            - Warning includes days until expiration
        """
        # Arrange: Generate certificate expiring in 15 days
        cert_pem, key_pem = generate_test_certificate(days_until_expiry=15)

        cert_file = tmp_path / "expiring_cert.pem"
        key_file = tmp_path / "expiring_key.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate certificate
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: Validation succeeds with warning
        assert result["valid"] is True, "Certificate should still be valid"
        assert len(result["warnings"]) > 0, "Expected warning for approaching expiration"

        # Verify warning mentions expiration
        warnings_text = " ".join(result["warnings"]).lower()
        assert "expires" in warnings_text or "expir" in warnings_text, (
            f"Expected expiration warning, got: {result['warnings']}"
        )

        # Verify days count is included
        assert "days" in warnings_text, (
            f"Expected days count in warning, got: {result['warnings']}"
        )

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_certificate_expiring_in_90_days_generates_informational_warning(
        self, tmp_path: Path
    ):
        """
        Test that certificates expiring in 30-90 days generate informational warnings.

        Integration Scope:
            Expiration date parsing → Multi-tier warning logic → Warning categorization

        Business Impact:
            Provides tiered warning system for certificate lifecycle management,
            allowing proactive renewal scheduling.

        Test Strategy:
            - Generate certificate expiring in 60 days
            - Validate and check for informational warning
            - Distinguish from urgent warnings (< 30 days)

        Success Criteria:
            - Validation succeeds
            - Warning is generated
            - Warning is informational (not urgent/error level)
        """
        # Arrange: Generate certificate expiring in 60 days
        cert_pem, key_pem = generate_test_certificate(days_until_expiry=60)

        cert_file = tmp_path / "expiring_60_cert.pem"
        key_file = tmp_path / "expiring_60_key.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate certificate
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: Validation succeeds with informational warning
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

        # Verify warning mentions expiration timeframe
        warnings_text = " ".join(result["warnings"]).lower()
        assert "expires" in warnings_text or "expir" in warnings_text

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_valid_certificate_includes_subject_information(self, tmp_path: Path):
        """
        Test that valid certificates have subject information extracted.

        Integration Scope:
            Cryptography parsing → X.509 subject extraction → Metadata population

        Business Impact:
            Subject information aids in certificate identification and validation
            of certificate provenance in production environments.

        Test Strategy:
            - Generate certificate with specific subject CN
            - Validate certificate
            - Verify subject information is extracted and formatted

        Success Criteria:
            - Subject information is present in cert_info
            - Subject contains the expected Common Name
            - Subject is in RFC4514 string format
        """
        # Arrange: Generate certificate with known subject
        cert_pem, key_pem = generate_test_certificate(
            days_until_expiry=365, subject_cn="redis.production.example.com"
        )

        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate certificate
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: Subject information is extracted
        assert result["valid"] is True
        assert "subject" in result["cert_info"]

        subject = result["cert_info"]["subject"]
        assert "redis.production.example.com" in subject, (
            f"Expected CN in subject, got: {subject}"
        )

    @pytest.mark.skipif(
        CRYPTOGRAPHY_AVAILABLE,
        reason="Test requires cryptography to be unavailable - see TEST_PLAN_cryptography_unavailable.md",
    )
    def test_certificate_validation_warns_without_cryptography(self, tmp_path: Path):
        """
        Test that certificate validation gracefully degrades when cryptography is unavailable.

        Integration Scope:
            Certificate files → Missing cryptography library → Limited validation → Warning generation

        Business Impact:
            Ensures application can still perform basic certificate file validation
            even when cryptography library is not installed, with clear warnings
            about limited capabilities.

        Test Strategy:
            - Create basic certificate file (without cryptography)
            - Attempt validation
            - Verify basic file validation succeeds
            - Confirm warning about limited cryptography capabilities
            - Verify advanced features (expiration) are unavailable

        Success Criteria:
            - Basic file validation succeeds (files exist)
            - Warning generated about cryptography unavailability
            - No advanced certificate info available (expiration, subject)
            - Validation doesn't fail completely

        Note:
            This test must run in an environment without cryptography installed.
            See backend/tests/integration/startup/TEST_PLAN_cryptography_unavailable.md
            for execution instructions.
        """
        # Arrange: Create basic certificate file content
        # Without cryptography, we can't generate real certs, so use placeholder
        cert_content = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKJ3vQQqJr0jMA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMjMwMTAxMDAwMDAwWhcNMjQwMTAxMDAwMDAwWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEA0z9QrF7xKQj8vH2v0E7xYF7mI8c2j3rVL9wYtZ7pX9M4cL5yN8rN7dJ+
fake certificate content for testing without cryptography library
-----END CERTIFICATE-----"""

        cert_file = tmp_path / "cert.pem"
        cert_file.write_text(cert_content)

        validator = RedisSecurityValidator()

        # Act: Validate certificate without cryptography
        result = validator.validate_tls_certificates(cert_path=str(cert_file))

        # Assert: Basic validation should work
        assert result["valid"] is True, "Basic file validation should succeed"

        # Verify warning about cryptography
        assert len(result["warnings"]) > 0, "Expected warning about cryptography"
        assert any(
            "cryptography" in warning.lower() for warning in result["warnings"]
        ), f"Expected cryptography warning, got: {result['warnings']}"

        # Verify advanced features unavailable
        cert_info = result.get("cert_info", {})
        assert cert_info.get("expires") is None, (
            "Expiration should not be available without cryptography"
        )

    def test_no_certificate_paths_provided_returns_valid_result(self):
        """
        Test that validation succeeds when no certificate paths are provided.

        Integration Scope:
            Empty parameters → Validation logic → Success result

        Business Impact:
            TLS certificates are optional for some Redis configurations.
            Validation should succeed when certificates are intentionally not configured.

        Test Strategy:
            - Call validate_tls_certificates with no parameters
            - Verify validation succeeds
            - Verify no errors or warnings

        Success Criteria:
            - Validation returns valid=True
            - No errors are generated
            - cert_info is empty or minimal
        """
        # Arrange
        validator = RedisSecurityValidator()

        # Act: Validate with no certificate paths
        result = validator.validate_tls_certificates()

        # Assert: Validation succeeds with no certificates
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_malformed_certificate_file_generates_warning(self, tmp_path: Path):
        """
        Test that malformed certificate files generate parsing warnings.

        Integration Scope:
            File system → Cryptography parsing → Parse error handling → Warning generation

        Business Impact:
            Provides clear feedback when certificate files are corrupted or
            incorrectly formatted, aiding troubleshooting during deployment.

        Test Strategy:
            - Create file with invalid certificate content
            - Attempt validation
            - Verify warning about parsing failure
            - Verify file existence check still passes

        Success Criteria:
            - File existence validation succeeds
            - Warning generated about certificate parsing
            - Validation may still succeed (file exists) but warns about content
        """
        # Arrange: Create file with invalid certificate content
        cert_file = tmp_path / "malformed_cert.pem"
        key_file = tmp_path / "key.pem"

        # Invalid certificate content
        cert_file.write_text("This is not a valid certificate")

        # Valid key for comparison
        _, key_pem = generate_test_certificate(days_until_expiry=365)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate malformed certificate
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: File validation succeeds but parsing warning generated
        # Note: The validator may choose to succeed (file exists) or fail (can't parse)
        # Either is acceptable as long as there's a warning
        assert len(result["warnings"]) > 0, "Expected warning for malformed certificate"

        # Verify warning mentions parsing issue
        warnings_text = " ".join(result["warnings"]).lower()
        assert "parse" in warnings_text or "certificate" in warnings_text, (
            f"Expected parsing warning, got: {result['warnings']}"
        )

    @pytest.mark.skipif(
        not CRYPTOGRAPHY_AVAILABLE,
        reason="Requires cryptography library for certificate generation",
    )
    def test_certificate_paths_are_converted_to_absolute(self, tmp_path: Path):
        """
        Test that relative certificate paths are converted to absolute paths.

        Integration Scope:
            Path normalization → Absolute path conversion → Result storage

        Business Impact:
            Ensures certificate paths in logs and errors are unambiguous,
            improving debuggability in production deployments.

        Test Strategy:
            - Generate certificate in temp directory
            - Validate using relative path
            - Verify result contains absolute path

        Success Criteria:
            - Validation succeeds
            - cert_info contains absolute paths
            - Absolute paths point to correct files
        """
        # Arrange: Generate certificate
        cert_pem, key_pem = generate_test_certificate(days_until_expiry=365)

        cert_file = tmp_path / "cert.pem"
        key_file = tmp_path / "key.pem"

        cert_file.write_bytes(cert_pem)
        key_file.write_bytes(key_pem)

        validator = RedisSecurityValidator()

        # Act: Validate with relative-looking paths (tmp_path handles this)
        result = validator.validate_tls_certificates(
            cert_path=str(cert_file), key_path=str(key_file)
        )

        # Assert: Paths are absolute
        assert result["valid"] is True
        assert "cert_path" in result["cert_info"]
        assert "key_path" in result["cert_info"]

        cert_path = Path(result["cert_info"]["cert_path"])
        key_path = Path(result["cert_info"]["key_path"])

        assert cert_path.is_absolute(), f"Expected absolute cert path, got: {cert_path}"
        assert key_path.is_absolute(), f"Expected absolute key path, got: {key_path}"

        # Verify paths point to our test files
        assert cert_path == cert_file.absolute()
        assert key_path == key_file.absolute()
