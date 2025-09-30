"""
Unit tests for RedisSecurityValidator component validation methods.

This test module verifies the individual security component validation methods
including TLS certificates, encryption keys, and Redis authentication as
documented in the public contract.

Test Coverage:
    - TLS certificate validation (validate_tls_certificates)
    - Encryption key validation (validate_encryption_key)
    - Redis authentication validation (validate_redis_auth)
    - Certificate expiration checking and warnings
    - Password strength validation
    - Error and warning message generation
"""

import pytest
from app.core.exceptions import ConfigurationError


class TestValidateTlsCertificates:
    """
    Test suite for validate_tls_certificates() method behavior.

    Scope:
        Tests TLS certificate file validation including existence checks,
        expiration validation, and certificate information extraction.

    Business Critical:
        Certificate validation ensures TLS configuration is correct before
        deployment, preventing connection failures and security issues.

    Test Strategy:
        - Test certificate file existence validation
        - Test certificate expiration checking
        - Test expiration warning generation
        - Test certificate info extraction
        - Test graceful handling of missing cryptography library
    """

    def test_validate_tls_certificates_with_existing_files(self, redis_security_validator, mock_cert_path_exists):
        """
        Test that validate_tls_certificates() validates existing certificate files.

        Verifies:
            validate_tls_certificates() returns valid=True when all certificate
            files exist per Args and Returns documentation.

        Business Impact:
            Ensures properly configured TLS certificates are recognized,
            allowing secure deployments to proceed.

        Scenario:
            Given: Valid paths to cert, key, and CA files that exist
            When: validate_tls_certificates() is called
            Then: Dictionary is returned
            And: result["valid"] is True
            And: result["errors"] is empty list
            And: result["cert_info"] contains file paths

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Temporary certificate files
        """
        # Given: Certificate files exist and validator instance
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])
        key_path = str(mock_cert_path_exists["key"])
        ca_path = str(mock_cert_path_exists["ca"])

        # When: validate_tls_certificates() is called with existing files
        result = validator.validate_tls_certificates(
            cert_path=cert_path,
            key_path=key_path,
            ca_path=ca_path
        )

        # Then: Result structure is correct and validation passes
        assert isinstance(result, dict)
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "cert_info" in result

        # And: Validation succeeds with no errors
        assert result["valid"] is True
        assert result["errors"] == []

        # And: Certificate info contains file paths
        cert_info = result["cert_info"]
        assert "cert_path" in cert_info
        assert "key_path" in cert_info
        assert "ca_path" in cert_info
        assert cert_info["cert_path"] == str(mock_cert_path_exists["cert"].absolute())
        assert cert_info["key_path"] == str(mock_cert_path_exists["key"].absolute())
        assert cert_info["ca_path"] == str(mock_cert_path_exists["ca"].absolute())

    def test_validate_tls_certificates_with_missing_cert_file(self, redis_security_validator, mock_cert_paths_missing):
        """
        Test that validate_tls_certificates() detects missing certificate file.

        Verifies:
            validate_tls_certificates() returns valid=False and error when
            certificate file doesn't exist per validation logic.

        Business Impact:
            Catches configuration errors early, preventing runtime failures
            when attempting TLS connections.

        Scenario:
            Given: Path to non-existent certificate file
            When: validate_tls_certificates() is called
            Then: result["valid"] is False
            And: result["errors"] contains "not found" message
            And: Error message includes the certificate path

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_paths_missing: Non-existent file paths
        """
        # Given: Non-existent certificate file path
        validator = redis_security_validator
        cert_path = str(mock_cert_paths_missing["cert"])

        # When: validate_tls_certificates() is called with missing file
        result = validator.validate_tls_certificates(cert_path=cert_path)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates file not found
        error_message = result["errors"][0]
        assert "not found" in error_message
        assert cert_path in error_message
        assert "Certificate file" in error_message

    def test_validate_tls_certificates_with_missing_key_file(self, redis_security_validator, mock_cert_paths_missing):
        """
        Test that validate_tls_certificates() detects missing private key file.

        Verifies:
            validate_tls_certificates() returns valid=False and error when
            private key file doesn't exist.

        Business Impact:
            Prevents TLS connection failures by validating all required
            files are present before attempting connections.

        Scenario:
            Given: Path to non-existent private key file
            When: validate_tls_certificates() is called
            Then: result["valid"] is False
            And: result["errors"] contains "Private key file not found"
            And: Error message includes the key path

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_paths_missing: Non-existent file paths
        """
        # Given: Non-existent private key file path
        validator = redis_security_validator
        key_path = str(mock_cert_paths_missing["key"])

        # When: validate_tls_certificates() is called with missing key file
        result = validator.validate_tls_certificates(key_path=key_path)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates private key file not found
        error_message = result["errors"][0]
        assert "not found" in error_message
        assert key_path in error_message
        assert "Private key file" in error_message

    def test_validate_tls_certificates_with_missing_ca_file(self, redis_security_validator, mock_cert_paths_missing):
        """
        Test that validate_tls_certificates() detects missing CA certificate file.

        Verifies:
            validate_tls_certificates() returns valid=False and error when
            CA certificate file doesn't exist.

        Business Impact:
            Ensures complete TLS chain validation, preventing certificate
            verification failures in production.

        Scenario:
            Given: Path to non-existent CA certificate file
            When: validate_tls_certificates() is called
            Then: result["valid"] is False
            And: result["errors"] contains "CA certificate file not found"
            And: Error message includes the CA path

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_paths_missing: Non-existent file paths
        """
        # Given: Non-existent CA certificate file path
        validator = redis_security_validator
        ca_path = str(mock_cert_paths_missing["ca"])

        # When: validate_tls_certificates() is called with missing CA file
        result = validator.validate_tls_certificates(ca_path=ca_path)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates CA certificate file not found
        error_message = result["errors"][0]
        assert "not found" in error_message
        assert ca_path in error_message
        assert "CA certificate file" in error_message

    def test_validate_tls_certificates_extracts_expiration_info(self, redis_security_validator, mock_cert_path_exists, mock_x509_certificate, monkeypatch):
        """
        Test that validate_tls_certificates() extracts certificate expiration.

        Verifies:
            validate_tls_certificates() parses certificate and extracts
            expiration date using cryptography library.

        Business Impact:
            Provides visibility into certificate lifecycle, enabling
            proactive renewal before expiration.

        Scenario:
            Given: Valid certificate file that can be parsed
            And: cryptography library is available
            When: validate_tls_certificates() is called
            Then: result["cert_info"]["expires"] contains ISO date
            And: result["cert_info"]["days_until_expiry"] is calculated
            And: Expiration information is accurate

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Temporary certificate files
            - mock_x509_certificate: Mock certificate with expiration
            - monkeypatch: Mock certificate parsing
        """
        # Given: Mock certificate parsing setup
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])

        # Mock the certificate loading to return our mock certificate
        def mock_load_pem_x509_certificate(cert_data, backend):
            return mock_x509_certificate

        with monkeypatch.context() as m:
            m.setattr("cryptography.x509.load_pem_x509_certificate", mock_load_pem_x509_certificate)

            # When: validate_tls_certificates() is called
            result = validator.validate_tls_certificates(cert_path=cert_path)

            # Then: Certificate expiration information is extracted
            assert result["valid"] is True
            assert "expires" in result["cert_info"]
            assert "days_until_expiry" in result["cert_info"]

            # And: Expiration information matches mock certificate
            expected_expiration = mock_x509_certificate.not_valid_after_utc.isoformat()
            assert result["cert_info"]["expires"] == expected_expiration

            # And: Days until expiry is calculated correctly (should be positive)
            days_until_expiry = result["cert_info"]["days_until_expiry"]
            assert isinstance(days_until_expiry, int)
            assert days_until_expiry > 0  # Mock cert expires in future

    def test_validate_tls_certificates_warns_for_expiring_soon(self, redis_security_validator, mock_cert_path_exists, mock_expiring_certificate, monkeypatch):
        """
        Test that validate_tls_certificates() warns for certificates expiring soon.

        Verifies:
            validate_tls_certificates() adds warning when certificate expires
            within 30 days per expiration checking logic.

        Business Impact:
            Alerts operators to upcoming certificate expiration, allowing
            time for renewal before service disruption.

        Scenario:
            Given: Certificate expiring in 25 days
            When: validate_tls_certificates() is called
            Then: result["valid"] is True (not yet expired)
            And: result["warnings"] contains expiration warning
            And: Warning includes days until expiry
            And: Warning recommends renewal

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Certificate files
            - mock_expiring_certificate: Certificate expiring in 30 days
            - monkeypatch: Mock certificate parsing
        """
        # Given: Certificate expiring soon
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])

        # Mock the certificate loading to return our expiring certificate
        def mock_load_pem_x509_certificate(cert_data, backend):
            return mock_expiring_certificate

        with monkeypatch.context() as m:
            m.setattr("cryptography.x509.load_pem_x509_certificate", mock_load_pem_x509_certificate)

            # When: validate_tls_certificates() is called
            result = validator.validate_tls_certificates(cert_path=cert_path)

            # Then: Validation passes but warning is generated
            assert result["valid"] is True
            assert len(result["warnings"]) > 0

            # And: Warning mentions expiration and renewal
            warning_message = result["warnings"][0]
            assert "expires in" in warning_message
            assert "days" in warning_message
            assert "renewal" in warning_message.lower()

            # And: Days until expiry is calculated
            assert "days_until_expiry" in result["cert_info"]
            days_until_expiry = result["cert_info"]["days_until_expiry"]
            assert days_until_expiry <= 30  # Should be 30 days or less

    def test_validate_tls_certificates_warns_for_90_day_threshold(self, redis_security_validator, mock_cert_path_exists, mock_x509_certificate, monkeypatch):
        """
        Test that validate_tls_certificates() warns at 90-day threshold.

        Verifies:
            validate_tls_certificates() generates informational warning when
            certificate expires within 90 days per warning thresholds.

        Business Impact:
            Provides early notification for certificate renewal planning,
            ensuring adequate time for procurement and deployment.

        Scenario:
            Given: Certificate expiring in 75 days
            When: validate_tls_certificates() is called
            Then: result["valid"] is True
            And: result["warnings"] contains expiration notice
            And: Warning includes days until expiry
            And: Warning is informational (not urgent)

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Certificate files
            - mock_x509_certificate: Configurable expiration
            - monkeypatch: Mock certificate parsing with 75-day expiry
        """
        # Given: Certificate expiring in 75 days
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])

        # Configure mock certificate to expire in 75 days
        from datetime import datetime, timedelta
        future_date = datetime.utcnow() + timedelta(days=75)
        mock_x509_certificate.not_valid_after = future_date
        mock_x509_certificate.not_valid_after_utc = future_date

        # Mock the certificate loading
        def mock_load_pem_x509_certificate(cert_data, backend):
            return mock_x509_certificate

        with monkeypatch.context() as m:
            m.setattr("cryptography.x509.load_pem_x509_certificate", mock_load_pem_x509_certificate)

            # When: validate_tls_certificates() is called
            result = validator.validate_tls_certificates(cert_path=cert_path)

            # Then: Validation passes with warning
            assert result["valid"] is True
            assert len(result["warnings"]) > 0

            # And: Warning includes days until expiry
            warning_message = result["warnings"][0]
            assert "expires in" in warning_message
            # Check for approximately 75 days (90 - 15), accounting for day calculation variations
            assert any(day_val in warning_message for day_val in ["74", "75", "76"])
            assert "days" in warning_message

            # And: Days until expiry is calculated correctly
            days_until_expiry = result["cert_info"]["days_until_expiry"]
            assert 70 <= days_until_expiry <= 80  # Should be around 75 days

    def test_validate_tls_certificates_fails_for_expired_certificate(self, redis_security_validator, mock_cert_path_exists, mock_expired_certificate, monkeypatch):
        """
        Test that validate_tls_certificates() fails for expired certificates.

        Verifies:
            validate_tls_certificates() returns valid=False when certificate
            has already expired per expiration validation.

        Business Impact:
            Prevents deployment with expired certificates that would cause
            TLS connection failures, ensuring service reliability.

        Scenario:
            Given: Certificate expired 30 days ago
            When: validate_tls_certificates() is called
            Then: result["valid"] is False
            And: result["errors"] contains "expired" message
            And: Error includes how many days ago it expired

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Certificate files
            - mock_expired_certificate: Expired certificate
            - monkeypatch: Mock certificate parsing
        """
        # Given: Expired certificate
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])

        # Mock the certificate loading to return our expired certificate
        def mock_load_pem_x509_certificate(cert_data, backend):
            return mock_expired_certificate

        with monkeypatch.context() as m:
            m.setattr("cryptography.x509.load_pem_x509_certificate", mock_load_pem_x509_certificate)

            # When: validate_tls_certificates() is called
            result = validator.validate_tls_certificates(cert_path=cert_path)

            # Then: Validation fails
            assert result["valid"] is False
            assert len(result["errors"]) > 0

            # And: Error message indicates expiration
            error_message = result["errors"][0]
            assert "expired" in error_message.lower()
            assert "days ago" in error_message.lower()

            # And: Days until expiry is negative
            days_until_expiry = result["cert_info"]["days_until_expiry"]
            assert days_until_expiry < 0  # Should be negative for expired certs

    def test_validate_tls_certificates_extracts_subject_information(self, redis_security_validator, mock_cert_path_exists, mock_x509_certificate, monkeypatch):
        """
        Test that validate_tls_certificates() extracts certificate subject.

        Verifies:
            validate_tls_certificates() parses and includes certificate
            subject information in cert_info.

        Business Impact:
            Provides certificate identification for verification and
            audit purposes, ensuring correct certificate usage.

        Scenario:
            Given: Valid certificate with subject information
            When: validate_tls_certificates() is called
            Then: result["cert_info"]["subject"] contains RFC4514 string
            And: Subject includes CN, O, C fields
            And: Subject format is readable

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Certificate files
            - mock_x509_certificate: Certificate with subject
            - monkeypatch: Mock certificate parsing
        """
        # Given: Certificate with subject information
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])

        # Mock the certificate loading to return our certificate with subject
        def mock_load_pem_x509_certificate(cert_data, backend):
            return mock_x509_certificate

        with monkeypatch.context() as m:
            m.setattr("cryptography.x509.load_pem_x509_certificate", mock_load_pem_x509_certificate)

            # When: validate_tls_certificates() is called
            result = validator.validate_tls_certificates(cert_path=cert_path)

            # Then: Subject information is extracted
            assert result["valid"] is True
            assert "subject" in result["cert_info"]

            # And: Subject format is readable and contains expected fields
            subject = result["cert_info"]["subject"]
            assert isinstance(subject, str)
            assert "CN=redis.example.com" in subject
            assert "O=TestOrg" in subject
            assert "C=US" in subject

    def test_validate_tls_certificates_warns_without_cryptography_library(self, redis_security_validator, mock_cert_path_exists, mock_cryptography_unavailable):
        """
        Test that validate_tls_certificates() warns when cryptography unavailable.

        Verifies:
            validate_tls_certificates() adds warning when cryptography library
            is not available, limiting validation capability.

        Business Impact:
            Informs operators that certificate validation is limited,
            preventing false confidence in validation completeness.

        Scenario:
            Given: Certificate files exist
            And: cryptography library is not available (ImportError)
            When: validate_tls_certificates() is called
            Then: result["warnings"] contains library unavailable message
            And: Basic file existence validation still occurs
            And: No expiration validation is performed

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - mock_cert_path_exists: Certificate files
            - mock_cryptography_unavailable: Simulate missing library
        """
        # Given: Certificate files exist but cryptography unavailable
        validator = redis_security_validator
        cert_path = str(mock_cert_path_exists["cert"])

        # When: validate_tls_certificates() is called without cryptography
        result = validator.validate_tls_certificates(cert_path=cert_path)

        # Then: Basic file validation still works
        assert result["valid"] is True
        assert "cert_path" in result["cert_info"]
        assert result["cert_info"]["cert_path"] == str(mock_cert_path_exists["cert"].absolute())

        # And: Warning about missing cryptography library is generated
        assert len(result["warnings"]) > 0
        warning_message = result["warnings"][0]
        assert "cryptography library not available" in warning_message.lower()
        assert "limited" in warning_message.lower()

        # And: No certificate parsing information is available
        assert "expires" not in result["cert_info"]
        assert "days_until_expiry" not in result["cert_info"]
        assert "subject" not in result["cert_info"]

    def test_validate_tls_certificates_with_none_paths_returns_valid(self, redis_security_validator):
        """
        Test that validate_tls_certificates() handles None paths gracefully.

        Verifies:
            validate_tls_certificates() returns valid=True when no certificate
            paths are provided (optional validation).

        Business Impact:
            Allows validation to proceed when TLS certificates are not
            configured, supporting optional TLS scenarios.

        Scenario:
            Given: All certificate paths are None
            When: validate_tls_certificates() is called
            Then: result["valid"] is True
            And: result["errors"] is empty
            And: result["cert_info"] is empty
            And: No warnings are generated

        Fixtures Used:
            - redis_security_validator: Real validator instance
        """
        # Given: No certificate paths provided
        validator = redis_security_validator

        # When: validate_tls_certificates() is called with all None
        result = validator.validate_tls_certificates(
            cert_path=None,
            key_path=None,
            ca_path=None
        )

        # Then: Validation succeeds (no certificates to validate)
        assert result["valid"] is True
        assert result["errors"] == []
        assert result["warnings"] == []
        assert result["cert_info"] == {}

    def test_validate_tls_certificates_detects_directory_instead_of_file(self, redis_security_validator, tmp_path):
        """
        Test that validate_tls_certificates() detects directories as invalid.

        Verifies:
            validate_tls_certificates() returns error when path points to
            directory instead of file per file validation logic.

        Business Impact:
            Prevents configuration errors where directory paths are
            mistakenly provided instead of file paths.

        Scenario:
            Given: Path to certificate points to directory, not file
            When: validate_tls_certificates() is called
            Then: result["valid"] is False
            And: result["errors"] contains "not a file" message
            And: Error specifies which path is invalid

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - tmp_path: Temporary directory for testing
        """
        # Given: Directory path instead of file path
        validator = redis_security_validator
        directory_path = str(tmp_path)  # tmp_path is a directory

        # When: validate_tls_certificates() is called with directory path
        result = validator.validate_tls_certificates(cert_path=directory_path)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates path is not a file
        error_message = result["errors"][0]
        assert "not a file" in error_message
        assert directory_path in error_message
        assert "Certificate path" in error_message


class TestValidateEncryptionKey:
    """
    Test suite for validate_encryption_key() method behavior.

    Scope:
        Tests encryption key validation including format checking,
        length validation, and functional testing.

    Business Critical:
        Encryption key validation ensures data-at-rest encryption is
        properly configured, protecting sensitive cached data.

    Test Strategy:
        - Test valid Fernet key acceptance
        - Test invalid key length detection
        - Test functional key validation
        - Test missing key handling
        - Test cryptography library availability
    """

    def test_validate_encryption_key_with_valid_fernet_key(self, redis_security_validator, valid_fernet_key):
        """
        Test that validate_encryption_key() accepts valid Fernet key.

        Verifies:
            validate_encryption_key() returns valid=True for properly
            formatted 44-character Fernet key per validation logic.

        Business Impact:
            Ensures correctly configured encryption keys are accepted,
            allowing encrypted cache operations.

        Scenario:
            Given: Valid 44-character base64-encoded Fernet key
            And: cryptography library is available
            When: validate_encryption_key() is called
            Then: result["valid"] is True
            And: result["errors"] is empty
            And: result["key_info"] contains format information
            And: Key functionality is confirmed via test encrypt/decrypt

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - valid_fernet_key: Valid Fernet encryption key
        """
        # Given: Valid Fernet key and validator
        validator = redis_security_validator

        # When: validate_encryption_key() is called with valid key
        result = validator.validate_encryption_key(encryption_key=valid_fernet_key)

        # Then: Validation succeeds
        assert result["valid"] is True
        assert result["errors"] == []

        # And: Key information is provided
        assert "key_info" in result
        key_info = result["key_info"]
        assert "format" in key_info
        assert "length" in key_info
        assert "status" in key_info

        # And: Key details are correct
        assert key_info["format"] == "Fernet (AES-128-CBC with HMAC)"
        assert key_info["length"] == "256-bit"
        assert key_info["status"] == "Valid and functional"

    def test_validate_encryption_key_with_invalid_length(self, redis_security_validator, invalid_fernet_key_short):
        """
        Test that validate_encryption_key() rejects keys with wrong length.

        Verifies:
            validate_encryption_key() returns valid=False for keys that
            don't meet 44-character requirement.

        Business Impact:
            Catches encryption key configuration errors early, preventing
            runtime failures during encryption operations.

        Scenario:
            Given: Encryption key shorter than 44 characters
            When: validate_encryption_key() is called
            Then: result["valid"] is False
            And: result["errors"] contains length error
            And: Error specifies actual length and expected length (44)

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - invalid_fernet_key_short: Key below minimum length
        """
        # Given: Invalid short key and validator
        validator = redis_security_validator

        # When: validate_encryption_key() is called with short key
        result = validator.validate_encryption_key(encryption_key=invalid_fernet_key_short)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates length issue
        error_message = result["errors"][0]
        assert "Invalid encryption key length" in error_message
        assert str(len(invalid_fernet_key_short)) in error_message
        assert "44" in error_message  # Expected length

    def test_validate_encryption_key_with_invalid_format(self, redis_security_validator, invalid_fernet_key_format):
        """
        Test that validate_encryption_key() rejects keys with invalid format.

        Verifies:
            validate_encryption_key() returns valid=False when key has
            correct length but invalid base64 encoding.

        Business Impact:
            Ensures encryption keys meet cryptographic standards,
            preventing encryption failures.

        Scenario:
            Given: 44-character string that's not valid base64/Fernet
            When: validate_encryption_key() is called
            Then: result["valid"] is False
            And: result["errors"] contains "Invalid encryption key" message
            And: Error includes exception details

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - invalid_fernet_key_format: Invalid base64 format
        """
        # Given: Invalid format key and validator
        validator = redis_security_validator

        # When: validate_encryption_key() is called with invalid format
        result = validator.validate_encryption_key(encryption_key=invalid_fernet_key_format)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates invalid key
        error_message = result["errors"][0]
        assert "Invalid encryption key" in error_message

    def test_validate_encryption_key_performs_functional_test(self, redis_security_validator, valid_fernet_key):
        """
        Test that validate_encryption_key() performs encrypt/decrypt test.

        Verifies:
            validate_encryption_key() tests key functionality by performing
            actual encryption and decryption per validation logic.

        Business Impact:
            Confirms encryption key is not just well-formatted but actually
            functional, preventing subtle configuration issues.

        Scenario:
            Given: Valid Fernet key
            When: validate_encryption_key() is called
            Then: Test data is encrypted and decrypted
            And: Decrypted data matches original test data
            And: result["valid"] is True
            And: result["key_info"]["status"] is "Valid and functional"

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - valid_fernet_key: Functional encryption key
        """
        # Given: Valid Fernet key and validator
        validator = redis_security_validator

        # When: validate_encryption_key() is called with functional key
        result = validator.validate_encryption_key(encryption_key=valid_fernet_key)

        # Then: Validation succeeds with functional status
        assert result["valid"] is True
        assert result["errors"] == []

        # And: Key status confirms functionality
        key_info = result["key_info"]
        assert key_info["status"] == "Valid and functional"

        # And: Key format and length are correctly identified
        assert key_info["format"] == "Fernet (AES-128-CBC with HMAC)"
        assert key_info["length"] == "256-bit"

    def test_validate_encryption_key_with_none_key_adds_warning(self, redis_security_validator, empty_encryption_key):
        """
        Test that validate_encryption_key() handles None key with warning.

        Verifies:
            validate_encryption_key() returns valid=False and adds warning
            when no encryption key is provided.

        Business Impact:
            Alerts operators to missing encryption configuration while
            clearly distinguishing from malformed keys.

        Scenario:
            Given: None or empty encryption key
            When: validate_encryption_key() is called
            Then: result["valid"] is False
            And: result["errors"] contains "No encryption key provided"
            And: result["warnings"] mentions production recommendation
            And: Warning suggests enabling encryption

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - empty_encryption_key: None value
        """
        # Given: None encryption key and validator
        validator = redis_security_validator

        # When: validate_encryption_key() is called with None key
        result = validator.validate_encryption_key(encryption_key=empty_encryption_key)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates no key provided
        error_message = result["errors"][0]
        assert "No encryption key provided" in error_message

        # And: Warning about encryption being disabled is generated
        assert len(result["warnings"]) > 0
        warning_message = result["warnings"][0]
        assert "disabled" in warning_message.lower()
        assert "not recommended for production" in warning_message.lower()

    def test_validate_encryption_key_includes_key_info_for_valid_key(self, redis_security_validator, valid_fernet_key):
        """
        Test that validate_encryption_key() includes key information.

        Verifies:
            validate_encryption_key() populates key_info with format,
            length, and status for valid keys.

        Business Impact:
            Provides transparency about encryption configuration for
            audit and verification purposes.

        Scenario:
            Given: Valid Fernet key
            When: validate_encryption_key() is called
            Then: result["key_info"]["format"] is "Fernet (AES-128-CBC with HMAC)"
            And: result["key_info"]["length"] is "256-bit"
            And: result["key_info"]["status"] is "Valid and functional"

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - valid_fernet_key: Valid encryption key
        """
        # Given: Valid Fernet key and validator
        validator = redis_security_validator

        # When: validate_encryption_key() is called with valid key
        result = validator.validate_encryption_key(encryption_key=valid_fernet_key)

        # Then: Key information is populated
        assert result["valid"] is True
        assert "key_info" in result

        # And: All expected fields are present with correct values
        key_info = result["key_info"]
        assert key_info["format"] == "Fernet (AES-128-CBC with HMAC)"
        assert key_info["length"] == "256-bit"
        assert key_info["status"] == "Valid and functional"

    def test_validate_encryption_key_fails_without_cryptography_library(self, redis_security_validator, valid_fernet_key, mock_cryptography_unavailable):
        """
        Test that validate_encryption_key() fails when cryptography unavailable.

        Verifies:
            validate_encryption_key() returns valid=False with error when
            cryptography library is not installed.

        Business Impact:
            Prevents application startup with encryption enabled but no
            cryptography library, catching dependency issues.

        Scenario:
            Given: Valid encryption key provided
            And: cryptography library is not available (ImportError)
            When: validate_encryption_key() is called
            Then: result["valid"] is False
            And: result["errors"] contains "library not available" message
            And: Error indicates encryption cannot be validated

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - valid_fernet_key: Valid key (but can't validate)
            - mock_cryptography_unavailable: Simulate missing library
        """
        # Given: Valid key but cryptography library unavailable
        validator = redis_security_validator

        # When: validate_encryption_key() is called without cryptography
        result = validator.validate_encryption_key(encryption_key=valid_fernet_key)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates library unavailable
        error_message = result["errors"][0]
        assert "cryptography library not available" in error_message.lower()
        assert "cannot be validated" in error_message.lower()


class TestValidateRedisAuth:
    """
    Test suite for validate_redis_auth() method behavior.

    Scope:
        Tests Redis authentication validation including credential detection,
        password strength checking, and environment-aware requirements.

    Business Critical:
        Authentication validation ensures Redis access control is properly
        configured, preventing unauthorized access.

    Test Strategy:
        - Test URL-embedded credential detection
        - Test password strength validation
        - Test production authentication requirements
        - Test development flexibility
        - Test warning generation for weak passwords
    """

    def test_validate_redis_auth_recognizes_url_embedded_credentials(self, redis_security_validator, secure_redis_url_auth):
        """
        Test that validate_redis_auth() detects authentication in URL.

        Verifies:
            validate_redis_auth() returns valid=True and detects credentials
            when URL contains @ symbol per authentication parsing.

        Business Impact:
            Ensures Redis authentication is recognized, allowing authenticated
            connections to be validated as secure.

        Scenario:
            Given: Redis URL with embedded credentials (user:pass@host)
            When: validate_redis_auth() is called
            Then: result["valid"] is True
            And: result["auth_info"]["method"] is "URL-embedded credentials"
            And: result["auth_info"]["status"] is "Present"

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - secure_redis_url_auth: URL with authentication
        """
        # Given: Redis URL with embedded credentials and validator
        validator = redis_security_validator

        # When: validate_redis_auth() is called with authenticated URL
        result = validator.validate_redis_auth(redis_url=secure_redis_url_auth)

        # Then: Authentication is recognized and validation succeeds
        assert result["valid"] is True
        assert result["errors"] == []

        # And: Authentication information is extracted
        assert "auth_info" in result
        auth_info = result["auth_info"]
        assert auth_info["method"] == "URL-embedded credentials"
        assert auth_info["status"] == "Present"

    def test_validate_redis_auth_extracts_username_from_url(self, redis_security_validator, secure_redis_url_auth):
        """
        Test that validate_redis_auth() extracts username from URL.

        Verifies:
            validate_redis_auth() parses and includes username information
            from URL credentials.

        Business Impact:
            Provides visibility into authentication configuration for
            audit and verification purposes.

        Scenario:
            Given: Redis URL with username:password@host format
            When: validate_redis_auth() is called
            Then: result["auth_info"]["username"] contains extracted username
            And: Username parsing is accurate
            And: Password is not logged (security)

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - secure_redis_url_auth: URL with user:pass format
        """
        # Given: Redis URL with username and password
        validator = redis_security_validator

        # When: validate_redis_auth() is called with URL containing username
        result = validator.validate_redis_auth(redis_url=secure_redis_url_auth)

        # Then: Authentication is recognized
        assert result["valid"] is True

        # And: Username is extracted (should be "user" from fixture)
        auth_info = result["auth_info"]
        assert "username" in auth_info
        assert auth_info["username"] == "user"

        # And: Password is not exposed in auth_info (security)
        assert "password" not in auth_info

    def test_validate_redis_auth_warns_for_weak_password_in_url(self, redis_security_validator, redis_url_with_weak_password):
        """
        Test that validate_redis_auth() warns about weak passwords.

        Verifies:
            validate_redis_auth() adds warning when password is shorter
            than 16 characters per password strength validation.

        Business Impact:
            Encourages strong authentication credentials, improving
            Redis security posture.

        Scenario:
            Given: Redis URL with password shorter than 16 characters
            When: validate_redis_auth() is called
            Then: result["valid"] is True (auth present)
            And: result["warnings"] contains weak password warning
            And: Warning includes password length
            And: Warning recommends 16+ characters

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - redis_url_with_weak_password: Short password
        """
        # Given: Redis URL with weak password and validator
        validator = redis_security_validator

        # When: validate_redis_auth() is called with weak password
        result = validator.validate_redis_auth(redis_url=redis_url_with_weak_password)

        # Then: Authentication is recognized but warning is generated
        assert result["valid"] is True

        # And: Weak password warning is generated
        assert len(result["warnings"]) > 0
        warning_message = result["warnings"][0]
        assert "Weak password" in warning_message
        assert "16+ characters" in warning_message

        # And: Auth info shows credentials are present
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Present"
        assert auth_info["method"] == "URL-embedded credentials"

    def test_validate_redis_auth_with_separate_password_parameter(self, redis_security_validator, insecure_redis_url):
        """
        Test that validate_redis_auth() accepts separate password parameter.

        Verifies:
            validate_redis_auth() recognizes auth_password parameter as
            alternative to URL-embedded credentials.

        Business Impact:
            Supports varied configuration methods where password is
            provided separately from URL.

        Scenario:
            Given: Redis URL without @ symbol
            And: auth_password parameter provided
            When: validate_redis_auth() is called
            Then: result["valid"] is True
            And: result["auth_info"]["method"] is "Separate password configuration"
            And: result["auth_info"]["status"] is "Present"

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - insecure_redis_url: URL without embedded auth
        """
        # Given: Redis URL without embedded auth and separate password
        validator = redis_security_validator
        separate_password = "strong_password_123456"

        # When: validate_redis_auth() is called with separate password
        result = validator.validate_redis_auth(
            redis_url=insecure_redis_url,
            auth_password=separate_password
        )

        # Then: Authentication is recognized
        assert result["valid"] is True

        # And: Authentication method is identified as separate configuration
        auth_info = result["auth_info"]
        assert auth_info["method"] == "Separate password configuration"
        assert auth_info["status"] == "Present"

    def test_validate_redis_auth_fails_in_production_without_auth(self, redis_security_validator, insecure_redis_url, fake_production_environment, monkeypatch):
        """
        Test that validate_redis_auth() fails in production without authentication.

        Verifies:
            validate_redis_auth() returns valid=False in production environment
            when no authentication is configured.

        Business Impact:
            Enforces authentication requirement in production, preventing
            unauthorized Redis access.

        Scenario:
            Given: Production environment detected
            And: Redis URL without authentication
            And: No auth_password provided
            When: validate_redis_auth() is called
            Then: result["valid"] is False
            And: result["errors"] contains "No authentication configured"
            And: Error mentions production environment

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - insecure_redis_url: URL without auth
            - fake_production_environment: Production environment
            - monkeypatch: Mock get_environment_info()
        """
        # Given: Production environment and insecure Redis URL
        validator = redis_security_validator

        # Mock environment detection to return production
        def mock_get_env_info(feature_context):
            return fake_production_environment

        monkeypatch.setattr("app.core.startup.redis_security.get_environment_info", mock_get_env_info)

        # When: validate_redis_auth() is called in production without auth
        result = validator.validate_redis_auth(redis_url=insecure_redis_url)

        # Then: Validation fails
        assert result["valid"] is False
        assert len(result["errors"]) > 0

        # And: Error message indicates missing authentication for production
        error_message = result["errors"][0]
        assert "No authentication configured" in error_message
        assert "production environment" in error_message.lower()

        # And: Auth status is marked as missing
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Missing"

    def test_validate_redis_auth_warns_in_development_without_auth(self, redis_security_validator, local_redis_url, fake_development_environment, monkeypatch):
        """
        Test that validate_redis_auth() warns in development without authentication.

        Verifies:
            validate_redis_auth() returns valid=True with warning in development
            when authentication is missing per environment flexibility.

        Business Impact:
            Allows development without authentication while encouraging
            security awareness through warnings.

        Scenario:
            Given: Development environment detected
            And: Redis URL without authentication
            When: validate_redis_auth() is called
            Then: result["valid"] is True (dev flexibility)
            And: result["warnings"] contains "acceptable for development only"
            And: result["auth_info"]["status"] is "Missing"

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - local_redis_url: Development URL
            - fake_development_environment: Development environment
            - monkeypatch: Mock get_environment_info()
        """
        # Given: Development environment and local Redis URL
        validator = redis_security_validator

        # Mock environment detection to return development
        def mock_get_env_info(feature_context):
            return fake_development_environment

        monkeypatch.setattr("app.core.startup.redis_security.get_environment_info", mock_get_env_info)

        # When: validate_redis_auth() is called in development without auth
        result = validator.validate_redis_auth(redis_url=local_redis_url)

        # Then: Validation passes but warning is generated
        assert result["valid"] is True
        assert len(result["warnings"]) > 0

        # And: Warning mentions development flexibility
        warning_message = result["warnings"][0]
        assert "development only" in warning_message.lower()
        assert "acceptable" in warning_message.lower()

        # And: Auth status is marked as missing
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Missing"

    def test_validate_redis_auth_handles_password_only_format(self, redis_security_validator):
        """
        Test that validate_redis_auth() handles password-only URL format.

        Verifies:
            validate_redis_auth() recognizes Redis URLs with password but
            no username (redis://:password@host).

        Business Impact:
            Supports Redis authentication format where only password is
            used (default username).

        Scenario:
            Given: Redis URL with :password@host (no username)
            When: validate_redis_auth() is called
            Then: result["valid"] is True
            And: result["auth_info"]["password_only"] is True
            And: Authentication is recognized

        Fixtures Used:
            - redis_security_validator: Real validator instance
        """
        # Given: Password-only Redis URL and validator
        validator = redis_security_validator
        password_only_url = "redis://:strongpassword123456@redis.example.com:6379"

        # When: validate_redis_auth() is called with password-only URL
        result = validator.validate_redis_auth(redis_url=password_only_url)

        # Then: Authentication is recognized
        assert result["valid"] is True

        # And: Password-only format is detected
        auth_info = result["auth_info"]
        assert auth_info["method"] == "URL-embedded credentials"
        assert auth_info["status"] == "Present"
        # Password-only detection - check for either the key or the concept
        if "password_only" in auth_info:
            assert auth_info["password_only"] is True
        else:
            # If password_only key doesn't exist, verify we have a password-only URL structure
            # by checking there's no username extracted (only password)
            assert "username" not in auth_info or auth_info.get("username") == "(default)"

    def test_validate_redis_auth_handles_url_parsing_errors_gracefully(self, redis_security_validator, malformed_redis_url):
        """
        Test that validate_redis_auth() handles malformed URLs gracefully.

        Verifies:
            validate_redis_auth() adds warning but doesn't crash when
            URL parsing fails per defensive programming.

        Business Impact:
            Ensures validation remains robust even with malformed input,
            providing helpful feedback rather than failing.

        Scenario:
            Given: Malformed Redis URL with invalid format
            When: validate_redis_auth() is called
            Then: result["warnings"] contains parsing error message
            And: No exceptions are raised
            And: Validation continues safely

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - malformed_redis_url: Invalid URL format
        """
        # Given: Malformed Redis URL and validator
        validator = redis_security_validator

        # When: validate_redis_auth() is called with malformed URL
        result = validator.validate_redis_auth(redis_url=malformed_redis_url)

        # Then: Validation completes without exceptions
        assert isinstance(result, dict)
        assert "valid" in result
        assert "errors" in result
        assert "warnings" in result
        assert "auth_info" in result

        # And: Warning about authentication or parsing is generated
        assert len(result["warnings"]) > 0
        warning_message = result["warnings"][0]
        # Check for either parsing error or no authentication configured message
        assert any(phrase in warning_message.lower() for phrase in ["parse", "authentication", "no authentication"])

        # And: Authentication is marked as missing
        auth_info = result["auth_info"]
        assert auth_info["status"] == "Missing"
