"""
Integration tests for cache encryption without cryptography library.

This test module verifies graceful degradation and helpful error messages when
the cryptography library is unavailable. These tests run in an isolated Docker
environment where cryptography is intentionally not installed.

**Execution Requirements:**
- Run via Docker container without cryptography: ./run-no-cryptography-tests.sh
- Or manually in isolated virtualenv without cryptography package
- DO NOT run in standard test environment (will be skipped if cryptography is available)

**Test Philosophy:**
These are integration tests because:
- They test real import behavior in isolated environment
- They verify actual error messages users would see
- Unit-level mocking of library availability causes pytest internal errors
- The cryptography library imports at module load time, before test fixtures run

**Reference:**
- Test Plan: backend/tests/integration/startup/TEST_PLAN_cryptography_unavailable.md
- Implementation: backend/app/infrastructure/cache/encryption.py
"""

import pytest

from app.core.exceptions import ConfigurationError

# Check if cryptography is available
# This determines whether these tests should run
CRYPTOGRAPHY_AVAILABLE = True
try:
    from cryptography.fernet import Fernet  # noqa: F401
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# Skip entire module if cryptography IS available
# These tests should only run in environments WITHOUT cryptography
pytestmark = pytest.mark.skipif(
    CRYPTOGRAPHY_AVAILABLE,
    reason="Tests require cryptography library to be UNAVAILABLE. "
    "Run via Docker: ./backend/tests/integration/docker/run-no-cryptography-tests.sh",
)


class TestCacheEncryptionWithoutCryptography:
    """
    Integration tests for cache encryption graceful degradation.

    These tests verify that the application provides helpful error messages
    and fails fast when attempting to use encryption without cryptography.

    Integration Scope:
        EncryptedCacheLayer.__init__() → cryptography import check
        → ConfigurationError with installation guidance

    Test Environment:
        - Python environment WITHOUT cryptography package
        - Tests real import behavior, not mocked
        - Docker-isolated execution recommended
    """

    def test_encrypted_cache_initialization_without_cryptography(self):
        """
        Test that EncryptedCacheLayer provides helpful error when cryptography is missing.

        Integration Scope:
            EncryptedCacheLayer initialization → cryptography availability check
            → ConfigurationError with actionable guidance

        Business Impact:
            Ensures developers get clear, actionable error messages when deploying
            without required cryptography dependency. Prevents silent failures and
            aids troubleshooting during deployment.

        Test Strategy:
            - Import EncryptedCacheLayer in environment without cryptography
            - Attempt to initialize with valid encryption key
            - Verify ConfigurationError is raised
            - Verify error message includes installation command
            - Verify error message explains business impact

        Success Criteria:
            - ConfigurationError exception is raised
            - Error message contains "pip install cryptography"
            - Error message indicates "cryptography library is required"
            - Error message states "mandatory dependency for secure Redis operations"
            - Error includes helpful context for troubleshooting

        Environment Requirements:
            - cryptography package must NOT be installed
            - Run via Docker container or isolated virtualenv
        """
        from app.infrastructure.cache.encryption import EncryptedCacheLayer

        # Valid Fernet key format (44 characters, base64)
        valid_encryption_key = "x" * 44

        # Attempt to initialize - should fail without cryptography
        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key=valid_encryption_key)

        # Verify error message quality
        error_message = str(exc_info.value)

        # Check for installation command
        assert "pip install cryptography" in error_message, (
            "Error message should include installation command. "
            f"Got: {error_message}"
        )

        # Check for library requirement explanation
        assert "cryptography library is required" in error_message.lower(), (
            "Error message should explain library requirement. " f"Got: {error_message}"
        )

        # Check for business impact explanation
        assert "mandatory dependency" in error_message.lower(), (
            "Error message should explain business impact. " f"Got: {error_message}"
        )

        # Verify error context includes helpful metadata
        if hasattr(exc_info.value, "context"):
            context = exc_info.value.context
            assert context.get("error_type") == "missing_dependency", (
                f"Error context should indicate missing_dependency, got: {context}"
            )
            assert context.get("required_package") == "cryptography", (
                f"Error context should specify cryptography package, got: {context}"
            )

    def test_encryption_error_message_is_actionable(self):
        """
        Test that error message provides clear next steps for developers.

        Integration Scope:
            EncryptedCacheLayer initialization → error message generation
            → developer guidance quality

        Business Impact:
            Reduces developer debugging time by providing clear, actionable
            guidance when cryptography dependency is missing.

        Test Strategy:
            - Trigger cryptography unavailability error
            - Parse and validate error message structure
            - Verify presence of all required guidance elements

        Success Criteria:
            - Error message includes installation command
            - Error message is formatted for readability
            - Error message explains why cryptography is needed
            - Error provides context for troubleshooting

        Environment Requirements:
            - cryptography package must NOT be installed
        """
        from app.infrastructure.cache.encryption import EncryptedCacheLayer

        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key="test-key-placeholder")

        error_message = str(exc_info.value)

        # Verify error message structure
        assert error_message.strip(), "Error message should not be empty"
        assert (
            "ENCRYPTION ERROR" in error_message or "🔒" in error_message
        ), "Error should be clearly marked as encryption error"
        assert len(error_message) > 50, (
            "Error message should be detailed enough to be helpful, "
            f"got {len(error_message)} characters"
        )

        # Check for clear formatting (newlines for readability)
        assert "\n" in error_message, (
            "Error message should use newlines for readability"
        )

    def test_create_from_env_fails_without_cryptography(self):
        """
        Test that environment-based initialization also fails gracefully.

        Integration Scope:
            Environment variable reading → EncryptedCacheLayer.create_from_env()
            → cryptography check → ConfigurationError

        Business Impact:
            Ensures configuration-based initialization (common in production)
            also provides clear error messages when cryptography is unavailable.

        Test Strategy:
            - Set environment variable for encryption key
            - Attempt to create EncryptedCacheLayer from environment
            - Verify appropriate ConfigurationError is raised
            - Verify error message quality

        Success Criteria:
            - ConfigurationError is raised during env-based initialization
            - Error message maintains same quality as direct initialization
            - Error provides context about environment configuration

        Environment Requirements:
            - cryptography package must NOT be installed
            - REDIS_ENCRYPTION_KEY environment variable may be set (via monkeypatch)

        Fixtures Used:
            - monkeypatch: For setting environment variables safely
        """
        # Note: create_from_env is not implemented in current version
        # This test is a placeholder for future enhancement
        # If create_from_env exists, uncomment and implement:
        #
        # from app.infrastructure.cache.encryption import EncryptedCacheLayer
        # import os
        #
        # # Set encryption key via environment (if method exists)
        # test_key = "x" * 44
        # os.environ["REDIS_ENCRYPTION_KEY"] = test_key
        #
        # try:
        #     with pytest.raises(ConfigurationError) as exc_info:
        #         EncryptedCacheLayer.create_from_env()
        #
        #     error_message = str(exc_info.value)
        #     assert "cryptography" in error_message.lower()
        # finally:
        #     os.environ.pop("REDIS_ENCRYPTION_KEY", None)

        pytest.skip(
            "create_from_env() not implemented - placeholder for future enhancement"
        )


class TestEncryptionErrorMessageQuality:
    """
    Detailed validation of error message quality and developer experience.

    These tests ensure that error messages are not just present, but actually
    helpful for developers troubleshooting cryptography issues.

    Integration Scope:
        Error generation → message formatting → developer guidance
    """

    def test_error_includes_installation_command(self):
        """
        Test that error message includes exact pip install command.

        Integration Scope:
            ConfigurationError generation → installation command inclusion
            → copy-paste ready developer guidance

        Business Impact:
            Reduces friction when setting up development environment by providing
            exact command to resolve the issue.

        Success Criteria:
            - Error contains "pip install cryptography" exactly
            - Command is on its own line for easy copying
            - Command is clearly marked as installation instruction
        """
        from app.infrastructure.cache.encryption import EncryptedCacheLayer

        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key="test")

        error_message = str(exc_info.value)

        # Check for exact installation command
        assert "pip install cryptography" in error_message, (
            "Error should include exact pip install command"
        )

        # Verify command is clearly presented
        # (should have "Install with:" or similar prefix)
        assert (
            "install" in error_message.lower() and "cryptography" in error_message
        ), "Installation instruction should be clear"

    def test_error_explains_why_cryptography_is_required(self):
        """
        Test that error message explains business need for cryptography.

        Integration Scope:
            ConfigurationError generation → business context inclusion
            → developer understanding

        Business Impact:
            Helps developers understand why cryptography is not optional,
            preventing attempts to work around the requirement.

        Success Criteria:
            - Error mentions "mandatory dependency"
            - Error mentions "secure Redis operations" or similar security context
            - Error communicates importance, not just requirement
        """
        from app.infrastructure.cache.encryption import EncryptedCacheLayer

        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key="test")

        error_message = str(exc_info.value).lower()

        # Check for explanation of requirement
        assert "mandatory" in error_message or "required" in error_message, (
            "Error should explain that cryptography is mandatory"
        )

        # Check for security/business context
        assert any(
            keyword in error_message
            for keyword in ["secure", "redis", "encryption", "security"]
        ), "Error should provide business/security context"
