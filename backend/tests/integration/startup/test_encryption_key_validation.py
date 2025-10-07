"""
Integration tests for encryption key validation with cryptography.fernet.

This test module validates SEAM 3 from the integration test plan: the integration
between RedisSecurityValidator's validate_encryption_key() method and the
cryptography.fernet library for validating Fernet encryption keys.

Test Coverage:
    - Valid Fernet key validation through cryptography
    - Invalid key format detection and error reporting
    - Cryptography library unavailability handling
    - Key length validation
    - Encrypt/decrypt test validation

Integration Seam:
    validate_encryption_key() → cryptography.fernet.Fernet → encryption test

Business Impact:
    Ensures encryption keys are validated before cache initialization, preventing
    runtime failures and data security issues from invalid encryption configuration.

Reference:
    - Contract: backend/contracts/core/startup/redis_security.pyi (lines 146-159)
    - Test Plan: backend/tests/integration/startup/TEST_PLAN.md (lines 280-354)
    - Philosophy: docs/guides/testing/INTEGRATION_TESTS.md
"""

import pytest

# Test markers for execution control
CRYPTOGRAPHY_AVAILABLE = True
try:
    from cryptography.fernet import Fernet
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class TestEncryptionKeyValidationIntegration:
    """
    Integration tests for encryption key validation with cryptography library.

    Seam Under Test:
        RedisSecurityValidator.validate_encryption_key() → cryptography.fernet.Fernet
        → Fernet key validation → Encryption/decryption test → Validation result

    Critical Paths:
        1. Valid Key Path: Key format check → Fernet initialization → Encryption test → Success
        2. Invalid Key Path: Key format check → Format validation failure → Error generation
        3. Library Unavailable Path: Import check → ImportError handling → Validation failure

    Integration Scope:
        Tests the complete integration between the validator and the cryptography
        library, verifying that:
        - Valid Fernet keys are correctly validated through real cryptography operations
        - Invalid keys are properly detected and reported with helpful errors
        - Missing cryptography library fails validation gracefully

    Business Critical:
        Encryption key validation prevents cache initialization failures and ensures
        data-at-rest security is properly configured before the application starts.
    """

    def test_valid_fernet_key_passes_validation(self, redis_security_validator):
        """
        Test that valid Fernet encryption keys pass validation.

        Integration Scope:
            validate_encryption_key() → Fernet() constructor → fernet.encrypt()
            → fernet.decrypt() → validation result dictionary

        Business Impact:
            Ensures properly generated Fernet keys are recognized as valid,
            allowing secure cache encryption to be enabled without errors.

        Test Strategy:
            - Generate valid Fernet key using cryptography.fernet
            - Pass key to validator's validate_encryption_key() method
            - Verify validation succeeds with correct result structure
            - Verify key info contains expected format details

        Success Criteria:
            - result["valid"] is True
            - result["errors"] is empty list
            - result["key_info"]["format"] contains "Fernet"
            - No exceptions raised during validation

        Fixtures Used:
            - redis_security_validator: Real validator instance from conftest
        """
        # Arrange: Generate valid Fernet key using cryptography
        from cryptography.fernet import Fernet

        valid_key = Fernet.generate_key().decode("utf-8")

        # Act: Validate encryption key through real integration
        validator = redis_security_validator
        result = validator.validate_encryption_key(valid_key)

        # Assert: Validation succeeds with correct structure
        assert isinstance(result, dict), "Result must be dictionary"
        assert "valid" in result, "Result must contain 'valid' field"
        assert "errors" in result, "Result must contain 'errors' field"
        assert "warnings" in result, "Result must contain 'warnings' field"
        assert "key_info" in result, "Result must contain 'key_info' field"

        # Assert: Validation passes with no errors
        assert result["valid"] is True, "Valid Fernet key must pass validation"
        assert len(result["errors"]) == 0, "Valid key should have no errors"

        # Assert: Key info contains expected format details
        key_info = result["key_info"]
        assert "format" in key_info, "Key info must contain format"
        assert (
            "Fernet" in key_info["format"]
        ), "Format should identify as Fernet encryption"
        assert (
            "AES-128-CBC" in key_info["format"]
        ), "Format should mention AES-128-CBC algorithm"
        assert "HMAC" in key_info["format"], "Format should mention HMAC"
        assert "length" in key_info, "Key info must contain key length"
        assert "status" in key_info, "Key info must contain status"
        assert (
            key_info["status"] == "Valid and functional"
        ), "Status should confirm key is functional"

    def test_invalid_key_too_short_generates_error(self, redis_security_validator):
        """
        Test that encryption keys that are too short are rejected.

        Integration Scope:
            validate_encryption_key() → length validation → error generation

        Business Impact:
            Prevents weak or malformed encryption keys from being accepted,
            ensuring data security is not compromised.

        Test Strategy:
            - Provide key shorter than required 44 characters
            - Verify validation fails with appropriate error
            - Verify error message is helpful and actionable

        Success Criteria:
            - result["valid"] is False
            - result["errors"] contains length-related error
            - Error message mentions expected length (44 characters)

        Fixtures Used:
            - redis_security_validator: Real validator instance
        """
        # Arrange: Create key that is too short (Fernet requires 44 chars)
        short_key = "too-short-key"
        assert len(short_key) < 44, "Test key must be shorter than 44 characters"

        # Act: Validate short key
        validator = redis_security_validator
        result = validator.validate_encryption_key(short_key)

        # Assert: Validation fails
        assert result["valid"] is False, "Short key must fail validation"
        assert len(result["errors"]) > 0, "Validation failure must include errors"

        # Assert: Error message is helpful and mentions length
        error_message = " ".join(result["errors"]).lower()
        assert (
            "invalid encryption key length" in error_message
            or "length" in error_message
        ), "Error should mention key length issue"
        assert (
            "44" in " ".join(result["errors"])
        ), "Error should mention expected length of 44 characters"
        assert (
            str(len(short_key)) in " ".join(result["errors"])
        ), "Error should mention actual key length"

    def test_invalid_key_wrong_format_generates_error(
        self, redis_security_validator
    ):
        """
        Test that encryption keys with invalid base64 format are rejected.

        Integration Scope:
            validate_encryption_key() → Fernet() constructor → invalid base64
            → exception handling → error generation

        Business Impact:
            Prevents malformed keys from causing runtime failures during
            encryption operations, providing clear feedback at startup.

        Test Strategy:
            - Provide key with correct length but invalid base64 format
            - Verify validation fails when Fernet rejects the key
            - Verify error message indicates invalid key format

        Success Criteria:
            - result["valid"] is False
            - result["errors"] contains format-related error
            - Error mentions "invalid encryption key"

        Fixtures Used:
            - redis_security_validator: Real validator instance
        """
        # Arrange: Create key with correct length but invalid base64 format
        invalid_key = "!" * 44  # 44 chars but invalid base64
        assert (
            len(invalid_key) == 44
        ), "Test key must have correct length but invalid format"

        # Act: Validate key with invalid format
        validator = redis_security_validator
        result = validator.validate_encryption_key(invalid_key)

        # Assert: Validation fails
        assert result["valid"] is False, "Invalid format key must fail validation"
        assert len(result["errors"]) > 0, "Validation failure must include errors"

        # Assert: Error message indicates invalid key
        error_message = " ".join(result["errors"]).lower()
        assert (
            "invalid encryption key" in error_message or "invalid" in error_message
        ), "Error should indicate key is invalid"

    def test_empty_key_generates_error_and_warning(self, redis_security_validator):
        """
        Test that empty/None encryption keys are properly rejected.

        Integration Scope:
            validate_encryption_key(None) → empty check → error and warning generation

        Business Impact:
            Ensures encryption is not silently disabled due to missing
            configuration, alerting operators to security implications.

        Test Strategy:
            - Pass None as encryption key
            - Verify validation fails with error
            - Verify warning about disabled encryption is generated

        Success Criteria:
            - result["valid"] is False
            - result["errors"] mentions no key provided
            - result["warnings"] mentions disabled encryption

        Fixtures Used:
            - redis_security_validator: Real validator instance
        """
        # Arrange: Empty/None encryption key
        empty_key = None

        # Act: Validate empty key
        validator = redis_security_validator
        result = validator.validate_encryption_key(empty_key)

        # Assert: Validation fails
        assert result["valid"] is False, "Empty key must fail validation"
        assert len(result["errors"]) > 0, "Must generate error for missing key"

        # Assert: Error indicates no key provided
        error_message = " ".join(result["errors"]).lower()
        assert (
            "no encryption key" in error_message or "no" in error_message
        ), "Error should indicate key is missing"

        # Assert: Warning about disabled encryption
        assert (
            len(result["warnings"]) > 0
        ), "Should warn about disabled encryption in production"
        warning_message = " ".join(result["warnings"]).lower()
        assert (
            "disabled" in warning_message or "not recommended" in warning_message
        ), "Warning should mention encryption is disabled"
        assert (
            "production" in warning_message
        ), "Warning should mention production concerns"

    def test_valid_key_performs_encrypt_decrypt_test(
        self, redis_security_validator, valid_fernet_key
    ):
        """
        Test that validation performs actual encrypt/decrypt operations.

        Integration Scope:
            validate_encryption_key() → Fernet(key) → encrypt(test_data)
            → decrypt(encrypted) → verify roundtrip → validation result

        Business Impact:
            Verifies the encryption key is not just well-formed, but actually
            functional for encrypting and decrypting data, preventing runtime
            failures during cache operations.

        Test Strategy:
            - Provide valid Fernet key from fixture
            - Validate key through validator
            - Verify validation succeeds (proving encrypt/decrypt worked)
            - Verify key info indicates functional status

        Success Criteria:
            - result["valid"] is True
            - result["key_info"]["status"] indicates "functional"
            - No errors during validation

        Fixtures Used:
            - redis_security_validator: Real validator instance
            - valid_fernet_key: Valid Fernet key from unit conftest
        """
        # Arrange: Use valid Fernet key from shared fixture
        encryption_key = valid_fernet_key

        # Act: Validate key (internally performs encrypt/decrypt test)
        validator = redis_security_validator
        result = validator.validate_encryption_key(encryption_key)

        # Assert: Validation succeeds
        assert result["valid"] is True, "Valid key must pass validation"
        assert len(result["errors"]) == 0, "No errors for functional key"

        # Assert: Key info indicates key is functional (proving encrypt/decrypt worked)
        key_info = result["key_info"]
        assert "status" in key_info, "Key info must contain status"
        status = key_info["status"].lower()
        assert (
            "valid" in status and "functional" in status
        ), "Status should confirm key is valid and functional"

    def test_multiple_invalid_keys_generate_distinct_errors(
        self, redis_security_validator
    ):
        """
        Test that different invalid key scenarios generate distinct error messages.

        Integration Scope:
            validate_encryption_key() → multiple validation paths → distinct errors

        Business Impact:
            Ensures operators receive specific, actionable feedback for different
            configuration issues, reducing troubleshooting time.

        Test Strategy:
            - Test multiple invalid key scenarios
            - Verify each generates distinct error message
            - Verify errors are specific and actionable

        Success Criteria:
            - Short key error mentions length
            - Empty key error mentions missing key
            - Each error provides specific guidance

        Fixtures Used:
            - redis_security_validator: Real validator instance
        """
        # Arrange: Multiple invalid key scenarios
        validator = redis_security_validator
        scenarios = [
            ("", "empty string"),
            ("short", "too short"),
            ("x" * 10, "10 characters"),
            (None, "None value"),
        ]

        # Act & Assert: Each scenario generates distinct error
        for key, description in scenarios:
            result = validator.validate_encryption_key(key)

            # Assert: Validation fails
            assert (
                result["valid"] is False
            ), f"Validation must fail for {description}"
            assert (
                len(result["errors"]) > 0
            ), f"Must generate error for {description}"

            # Assert: Error message is specific
            error_message = " ".join(result["errors"]).lower()
            if key is None or key == "":
                assert (
                    "no encryption key" in error_message
                ), f"Error for {description} should mention missing key"
            else:
                assert (
                    "length" in error_message
                ), f"Error for {description} should mention length"
                assert (
                    "44" in " ".join(result["errors"])
                ), f"Error for {description} should mention expected length"
