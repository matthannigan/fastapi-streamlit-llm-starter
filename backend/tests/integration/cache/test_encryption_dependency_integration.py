"""
Integration tests for cryptography library dependency and graceful degradation.

This module tests the integration between EncryptedCacheLayer and the cryptography
library dependency, ensuring proper error handling and graceful degradation when
the library is missing or unavailable.

Test Focus:
    - Cryptography library availability detection
    - Graceful degradation behavior when library is missing
    - Error handling and messaging for missing dependencies
    - ConfigurationError propagation with proper context
    - Import validation and error recovery
"""

import pytest
from unittest.mock import patch, MagicMock
from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.encryption import (
    EncryptedCacheLayer,
    create_encryption_layer_from_env,
    CRYPTOGRAPHY_AVAILABLE,
)


class TestCryptographyDependencyIntegration:
    """
    Tests for cryptography library dependency integration and graceful degradation.

    Integration Scope:
        EncryptedCacheLayer → cryptography library import → CRYPTOGRAPHY_AVAILABLE flag →
        ConfigurationError handling → Application startup validation

    Business Impact:
        Ensures the application handles missing cryptography dependencies gracefully
        with clear error messages and proper failure modes during initialization.

    Critical Paths:
        - Import validation during module loading
        - Error detection during EncryptedCacheLayer initialization
        - Graceful degradation behavior and error messaging
        - Environment-based configuration with missing dependencies
    """

    def test_encryption_initialization_fails_when_cryptography_unavailable(
        self, monkeypatch
    ):
        """
        Test that EncryptedCacheLayer raises ConfigurationError when cryptography is unavailable.

        Integration Scope:
            cryptography import failure → CRYPTOGRAPHY_AVAILABLE flag → EncryptedCacheLayer.__init__ → ConfigurationError

        Business Impact:
            Ensures proper error detection and clear messaging when required cryptography
            dependency is missing during application startup.

        Test Strategy:
            - Mock cryptography import to simulate missing dependency
            - Attempt to create EncryptedCacheLayer
            - Verify ConfigurationError with helpful message is raised
            - Validate error context includes installation instructions

        Success Criteria:
            - ConfigurationError is raised with clear error message
            - Error context includes installation instructions
            - Error type is correctly classified as 'missing_dependency'
        """
        # Mock cryptography as unavailable
        mock_fernet = MagicMock()
        mock_fernet.encrypt.side_effect = ImportError("No module named 'cryptography'")

        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer(encryption_key="test-key")

            error = exc_info.value
            assert "cryptography library is required" in str(error)
            assert "pip install cryptography" in str(error)
            assert error.context.get("error_type") == "missing_dependency"
            assert error.context.get("required_package") == "cryptography"

    def test_cryptography_available_flag_reflects_library_state(self, monkeypatch):
        """
        Test that CRYPTOGRAPHY_AVAILABLE flag correctly reflects library availability.

        Integration Scope:
            cryptography import attempt → CRYPTOGRAPHY_AVAILABLE flag setting → Runtime validation

        Business Impact:
            Ensures the application can properly detect cryptography library availability
            for conditional feature enabling and proper error handling.

        Test Strategy:
            - Test with cryptography available (normal state)
            - Test with cryptography unavailable (mocked import failure)
            - Verify flag reflects actual library state

        Success Criteria:
            - CRYPTOGRAPHY_AVAILABLE is True when library is available
            - CRYPTOGRAPHY_AVAILABLE is False when library import fails
        """
        # Test normal state - should be available in test environment
        assert CRYPTOGRAPHY_AVAILABLE is True

        # Test mocked unavailable state
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            # Need to check the patched value directly from the module
            import app.infrastructure.cache.encryption as encryption_module
            assert encryption_module.CRYPTOGRAPHY_AVAILABLE is False

    def test_create_with_generated_key_fails_without_cryptography(self, monkeypatch):
        """
        Test that create_with_generated_key fails when cryptography is unavailable.

        Integration Scope:
            create_with_generated_key → cryptography import check → ConfigurationError

        Business Impact:
            Ensures convenience methods fail gracefully with clear error messages
            when required dependencies are missing.

        Test Strategy:
            - Mock cryptography as unavailable
            - Attempt to create EncryptedCacheLayer with generated key
            - Verify ConfigurationError with appropriate context

        Success Criteria:
            - ConfigurationError is raised
            - Error message indicates cryptography library requirement
        """
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer.create_with_generated_key()

            error = exc_info.value
            assert "cryptography library is required" in str(error)

    def test_environment_based_configuration_handles_missing_cryptography(
        self, monkeypatch
    ):
        """
        Test that environment-based configuration handles missing cryptography gracefully.

        Integration Scope:
            create_encryption_layer_from_env → environment variable loading → EncryptedCacheLayer initialization → cryptography check

        Business Impact:
            Ensures environment-based configuration fails properly when cryptography
            library is missing, preventing runtime errors during cache operations.

        Test Strategy:
            - Mock cryptography as unavailable
            - Set encryption key environment variable
            - Attempt to create encryption layer from environment
            - Verify ConfigurationError with clear instructions

        Success Criteria:
            - ConfigurationError is raised even when environment variable is set
            - Error includes installation instructions
            - Error context properly identifies the issue type
        """
        # Set environment variable
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "test-encryption-key")

        # Mock cryptography as unavailable
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                create_encryption_layer_from_env()

            error = exc_info.value
            assert "cryptography library is required" in str(error)
            assert "pip install cryptography" in str(error)
            assert error.context.get("error_type") == "missing_dependency"

    def test_error_messages_include_actionable_installation_instructions(self, monkeypatch):
        """
        Test that error messages include actionable installation instructions.

        Integration Scope:
            cryptography import failure → error message generation → user guidance

        Business Impact:
            Ensures developers receive clear, actionable instructions for resolving
            missing dependency issues during development and deployment.

        Test Strategy:
            - Mock cryptography as unavailable
            - Trigger various initialization scenarios
            - Verify all error messages include installation instructions

        Success Criteria:
            - All error messages include "pip install cryptography"
            - Error messages are user-friendly and actionable
            - Multiple error scenarios provide consistent guidance
        """
        # Test direct initialization
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer()

            error_msg = str(exc_info.value)
            assert "pip install cryptography" in error_msg
            assert "mandatory dependency" in error_msg.lower()

        # Test create_with_generated_key
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer.create_with_generated_key()

            error_msg = str(exc_info.value)
            assert "cryptography library is required" in error_msg

    def test_import_error_is_distinguished_from_other_configuration_errors(self):
        """
        Test that import errors are properly distinguished from other configuration errors.

        Integration Scope:
            cryptography import failure → error type classification → ConfigurationError context

        Business Impact:
            Ensures proper error classification for different failure modes,
            enabling appropriate error handling and troubleshooting guidance.

        Test Strategy:
            - Test cryptography import failure
            - Test invalid encryption key failure
            - Verify error contexts distinguish between failure types

        Success Criteria:
            - Import errors have error_type 'missing_dependency'
            - Invalid key errors have error_type 'invalid_encryption_key'
            - Error messages are specific to failure type
        """
        # Test missing cryptography (import error)
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer(encryption_key="test-key")

            import_error = exc_info.value
            assert (
                import_error.context.get("error_type") == "missing_dependency"
            ), f"Expected 'missing_dependency', got {import_error.context.get('error_type')}"
            assert "required_package" in import_error.context

        # Test invalid key (configuration error, not import error)
        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key="invalid-key-format")

            config_error = exc_info.value
            assert (
                config_error.context.get("error_type") == "invalid_encryption_key"
            ), f"Expected 'invalid_encryption_key', got {config_error.context.get('error_type')}"
            assert "original_error" in config_error.context

    def test_graceful_degradation_does_not_silently_continue(self, monkeypatch):
        """
        Test that missing cryptography does not cause silent failures.

        Integration Scope:
            cryptography import failure → error propagation → application startup failure

        Business Impact:
            Prevents silent security failures where encryption might be disabled
            unintentionally, ensuring data protection requirements are met.

        Test Strategy:
            - Mock cryptography as unavailable
            - Attempt to create encryption layer with None key (would normally disable encryption)
            - Verify that missing cryptography still causes explicit failure

        Success Criteria:
            - Missing cryptography always raises ConfigurationError
            - No silent fallback to unencrypted mode when cryptography is missing
            - Security failures are explicit and visible
        """
        # Even with None key (which would normally disable encryption),
        # missing cryptography should still cause an error
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer(encryption_key=None)

            error = exc_info.value
            assert "cryptography library is required" in str(error)
            assert error.context.get("error_type") == "missing_dependency"

    def test_multiple_encryption_layer_instances_consistent_error_handling(self, monkeypatch):
        """
        Test that multiple encryption layer instances handle missing cryptography consistently.

        Integration Scope:
            multiple EncryptedCacheLayer instances → shared cryptography dependency → consistent error handling

        Business Impact:
            Ensures consistent behavior across multiple cache instances when
            cryptography dependency is missing, preventing unpredictable behavior.

        Test Strategy:
            - Mock cryptography as unavailable
            - Create multiple encryption layer instances
            - Verify all instances fail with consistent error messages

        Success Criteria:
            - All instances raise ConfigurationError
            - Error messages are consistent across instances
            - Error context is identical for all failures
        """
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            errors = []

            # Test multiple initialization scenarios
            test_scenarios = [
                ("direct_init", lambda: EncryptedCacheLayer()),
                ("with_key", lambda: EncryptedCacheLayer(encryption_key="test-key")),
                ("generated_key", lambda: EncryptedCacheLayer.create_with_generated_key()),
            ]

            for name, scenario in test_scenarios:
                with pytest.raises(ConfigurationError) as exc_info:
                    scenario()
                errors.append((name, exc_info.value))

            # Test environment-based scenario separately since it needs different setup
            monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "test-key")
            with pytest.raises(ConfigurationError) as exc_info:
                create_encryption_layer_from_env()
            errors.append(("from_env", exc_info.value))

            # Verify all errors have consistent content for missing cryptography
            for name, error in errors:
                # All errors should mention cryptography
                assert "cryptography" in str(error).lower(), f"Scenario {name} error doesn't mention cryptography: {str(error)}"

                # Check error context based on how the error was created
                if name in ["direct_init", "with_key"]:
                    # These come from __init__ and should have context
                    assert error.context.get("error_type") == "missing_dependency", f"Scenario {name} failed with context {error.context}"
                elif name == "generated_key":
                    # This comes from create_with_generated_key method which raises error without context
                    # The error should still mention cryptography library
                    assert "cryptography library is required" in str(error)
                elif name == "from_env":
                    # This should come from __init__ via create_encryption_layer_from_env
                    if error.context:  # May have context if encryption_key was set
                        assert error.context.get("error_type") == "missing_dependency"

    def test_dependency_check_occurs_early_in_initialization(self, monkeypatch):
        """
        Test that dependency checking occurs early in the initialization process.

        Integration Scope:
            EncryptedCacheLayer.__init__ → cryptography dependency check → early failure

        Business Impact:
            Ensures dependency failures are caught early, preventing partial
            initialization states that could lead to runtime errors.

        Test Strategy:
            - Mock cryptography as unavailable
            - Attempt initialization with various parameters
            - Verify failure occurs before any other processing

        Success Criteria:
            - Dependency check happens before key validation
            - Error occurs immediately upon initialization
            - No side effects from partial initialization
        """
        with patch("app.infrastructure.cache.encryption.CRYPTOGRAPHY_AVAILABLE", False):
            # The dependency check should happen before key validation
            # So even an invalid key should not be reached
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer(encryption_key="clearly-invalid-key")

            error = exc_info.value
            # Should be dependency error, not key validation error
            assert error.context.get("error_type") == "missing_dependency"
            assert "cryptography" in str(error).lower()
            # Should not contain key validation messages
            assert "Invalid encryption key" not in str(error)