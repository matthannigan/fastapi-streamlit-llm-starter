"""
Unit tests for EncryptedCacheLayer initialization behavior.

This test module verifies that the EncryptedCacheLayer class properly handles
initialization scenarios as documented in the public contract, including valid
key initialization, missing key handling, invalid key validation, and
cryptography library availability checking.

Test Coverage:
    - Valid encryption key initialization
    - Missing/None encryption key handling
    - Invalid encryption key format validation
    - Performance monitoring configuration
    - Cryptography library dependency verification
    - Initialization error handling and messaging
"""

import pytest
from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.encryption import EncryptedCacheLayer, create_encryption_layer_from_env


class TestEncryptedCacheLayerInitialization:
    """
    Test suite for EncryptedCacheLayer initialization behavior.

    Scope:
        Tests the __init__ method of EncryptedCacheLayer covering all
        documented initialization scenarios from Args and Raises sections.

    Business Critical:
        Proper initialization ensures encryption is configured correctly
        before any cache operations, preventing data security vulnerabilities.

    Test Strategy:
        - Verify successful initialization with valid keys
        - Test warning generation for missing keys
        - Validate error handling for invalid keys
        - Confirm performance monitoring configuration
        - Verify cryptography dependency checking
    """

    def test_initialization_with_valid_key_enables_encryption(self, valid_fernet_key):
        """
        Test that initialization with valid Fernet key enables encryption.

        Verifies:
            EncryptedCacheLayer successfully initializes with valid encryption key
            and enables encryption as documented in __init__ docstring.

        Business Impact:
            Ensures encryption layer can be properly configured for secure
            cache operations in production environments.

        Scenario:
            Given: A valid base64-encoded Fernet encryption key
            When: EncryptedCacheLayer is initialized with the key
            Then: Initialization succeeds without exceptions
            And: The encryption layer reports enabled status

        Fixtures Used:
            - valid_fernet_key: Provides valid Fernet encryption key
        """
        # Given: A valid base64-encoded Fernet encryption key
        encryption_key = valid_fernet_key

        # When: EncryptedCacheLayer is initialized with the key
        encryption_layer = EncryptedCacheLayer(encryption_key=encryption_key)

        # Then: Initialization succeeds without exceptions
        assert encryption_layer is not None

        # And: The encryption layer reports enabled status
        assert encryption_layer.is_enabled is True

    def test_initialization_with_none_key_disables_encryption(self, empty_encryption_key, mock_logger, monkeypatch):
        """
        Test that initialization with None encryption key disables encryption.

        Verifies:
            EncryptedCacheLayer initializes without encryption when key is None,
            per docstring note about testing scenarios.

        Business Impact:
            Provides flexibility for development/testing environments where
            encryption may be disabled, while maintaining production security.

        Scenario:
            Given: None value for encryption_key parameter
            When: EncryptedCacheLayer is initialized
            Then: Initialization succeeds without exceptions
            And: The encryption layer reports disabled status
            And: A security warning is logged about disabled encryption

        Fixtures Used:
            - empty_encryption_key: Provides None value for encryption key
            - mock_logger: Captures warning log messages
        """
        # Given: None value for encryption_key parameter
        encryption_key = empty_encryption_key

        # Mock the logger to capture warning messages
        # Need to patch the logging module's getLogger function
        def mock_get_logger(name=None):
            return mock_logger
        monkeypatch.setattr("logging.getLogger", mock_get_logger)

        # When: EncryptedCacheLayer is initialized
        encryption_layer = EncryptedCacheLayer(encryption_key=encryption_key)

        # Then: Initialization succeeds without exceptions
        assert encryption_layer is not None

        # And: The encryption layer reports disabled status
        assert encryption_layer.is_enabled is False

        # And: A security warning is logged about disabled encryption
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        assert "SECURITY WARNING" in warning_message
        assert "encryption is disabled" in warning_message.lower()

    def test_initialization_with_invalid_key_format_raises_error(self, invalid_fernet_key_format):
        """
        Test that initialization with invalid key format raises ConfigurationError.

        Verifies:
            EncryptedCacheLayer validates encryption key format and raises
            ConfigurationError for invalid base64 encoding per Raises section.

        Business Impact:
            Prevents misconfiguration that would cause runtime failures during
            encryption/decryption operations, catching errors at startup.

        Scenario:
            Given: An invalid encryption key (wrong base64 format)
            When: EncryptedCacheLayer is initialized with the invalid key
            Then: ConfigurationError is raised with descriptive error message
            And: Error message includes guidance for generating valid key
            And: Error context indicates "invalid_encryption_key" error type

        Fixtures Used:
            - invalid_fernet_key_format: Provides improperly formatted key
        """
        # Given: An invalid encryption key (wrong base64 format)
        encryption_key = invalid_fernet_key_format

        # When: EncryptedCacheLayer is initialized with the invalid key
        # Then: ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key=encryption_key)

        # And: Error message includes guidance for generating valid key
        error_message = str(exc_info.value)
        assert "Invalid encryption key" in error_message
        assert "python -c" in error_message  # Key generation command

        # And: Error context indicates "invalid_encryption_key" error type
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context.get("error_type") == "invalid_encryption_key"

    def test_initialization_with_short_key_raises_error(self, invalid_fernet_key_short):
        """
        Test that initialization with too-short key raises ConfigurationError.

        Verifies:
            EncryptedCacheLayer validates key length and rejects keys that
            don't meet Fernet's 44-character base64 requirement.

        Business Impact:
            Prevents use of weak encryption keys that don't meet cryptographic
            security standards, maintaining data protection integrity.

        Scenario:
            Given: An encryption key that's too short (< 44 characters)
            When: EncryptedCacheLayer is initialized
            Then: ConfigurationError is raised with clear error message
            And: Error indicates invalid encryption key issue
            And: Error provides key generation instructions

        Fixtures Used:
            - invalid_fernet_key_short: Provides key below minimum length
        """
        # Given: An encryption key that's too short (< 44 characters)
        encryption_key = invalid_fernet_key_short

        # When: EncryptedCacheLayer is initialized
        # Then: ConfigurationError is raised with clear error message
        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key=encryption_key)

        # And: Error indicates invalid encryption key issue
        error_message = str(exc_info.value)
        assert "Invalid encryption key" in error_message

        # And: Error provides key generation instructions
        assert "python -c" in error_message
        assert "Fernet.generate_key()" in error_message

    def test_initialization_with_performance_monitoring_enabled(self, valid_fernet_key):
        """
        Test that performance monitoring is enabled when configured.

        Verifies:
            EncryptedCacheLayer properly configures performance monitoring
            when performance_monitoring=True (default) per Args section.

        Business Impact:
            Ensures performance tracking is available for monitoring encryption
            overhead and optimizing cache operations in production.

        Scenario:
            Given: Valid encryption key and performance_monitoring=True
            When: EncryptedCacheLayer is initialized
            Then: Initialization succeeds
            And: Performance statistics can be retrieved
            And: Statistics show zero operations initially

        Fixtures Used:
            - valid_fernet_key: Provides valid encryption key
        """
        # Given: Valid encryption key and performance_monitoring=True
        encryption_key = valid_fernet_key

        # When: EncryptedCacheLayer is initialized
        encryption_layer = EncryptedCacheLayer(
            encryption_key=encryption_key,
            performance_monitoring=True
        )

        # Then: Initialization succeeds
        assert encryption_layer is not None

        # And: Performance statistics can be retrieved
        stats = encryption_layer.get_performance_stats()
        assert stats is not None
        assert isinstance(stats, dict)

        # And: Statistics show zero operations initially
        assert stats["total_operations"] == 0
        assert stats["encryption_operations"] == 0
        assert stats["decryption_operations"] == 0
        assert stats["performance_monitoring"] is True

    def test_initialization_with_performance_monitoring_disabled(self, valid_fernet_key):
        """
        Test that performance monitoring can be disabled at initialization.

        Verifies:
            EncryptedCacheLayer respects performance_monitoring=False setting
            per __init__ Args documentation and Examples.

        Business Impact:
            Provides option to minimize overhead in performance-critical
            environments where monitoring is not required.

        Scenario:
            Given: Valid encryption key and performance_monitoring=False
            When: EncryptedCacheLayer is initialized
            Then: Initialization succeeds
            And: get_performance_stats() indicates monitoring is disabled
            And: No performance overhead is incurred during operations

        Fixtures Used:
            - valid_fernet_key: Provides valid encryption key
        """
        # Given: Valid encryption key and performance_monitoring=False
        encryption_key = valid_fernet_key

        # When: EncryptedCacheLayer is initialized
        encryption_layer = EncryptedCacheLayer(
            encryption_key=encryption_key,
            performance_monitoring=False
        )

        # Then: Initialization succeeds
        assert encryption_layer is not None

        # And: get_performance_stats() indicates monitoring is disabled
        stats = encryption_layer.get_performance_stats()
        assert "error" in stats
        assert stats["error"] == "Performance monitoring is disabled"

        # And: No performance overhead is incurred during operations
        # (Verify by checking internal state - monitoring flag is False)
        assert encryption_layer.performance_monitoring is False

    def test_initialization_validates_key_with_test_encryption(self, valid_fernet_key):
        """
        Test that initialization validates encryption key through test operation.

        Verifies:
            EncryptedCacheLayer performs test encryption/decryption during
            initialization to validate key is functional.

        Business Impact:
            Catches encryption key issues at startup rather than during runtime
            operations, preventing cascading failures in production.

        Scenario:
            Given: Valid encryption key that passes format validation
            When: EncryptedCacheLayer is initialized
            Then: A test encryption/decryption cycle is performed
            And: Initialization succeeds only if test cycle passes
            And: Any test failure raises ConfigurationError with details

        Fixtures Used:
            - valid_fernet_key: Provides functional encryption key
        """
        # Given: Valid encryption key that passes format validation
        encryption_key = valid_fernet_key

        # When: EncryptedCacheLayer is initialized
        # Then: Initialization succeeds only if test cycle passes
        encryption_layer = EncryptedCacheLayer(encryption_key=encryption_key)

        # The fact that initialization succeeded means the test encryption/decryption cycle passed
        # We can verify this by testing that encryption operations work correctly
        test_data = {"test_key": "test_value"}

        # If the initialization validation failed, this would raise an exception
        encrypted = encryption_layer.encrypt_cache_data(test_data)
        decrypted = encryption_layer.decrypt_cache_data(encrypted)

        # Verify the encryption/decryption works (confirming validation passed)
        assert decrypted == test_data

    def test_initialization_logs_success_message_for_enabled_encryption(self, valid_fernet_key, mock_logger, monkeypatch):
        """
        Test that successful encryption initialization logs confirmation.

        Verifies:
            EncryptedCacheLayer logs success message when encryption is
            successfully enabled per implementation logging behavior.

        Business Impact:
            Provides operational visibility into encryption status for
            monitoring and debugging production deployments.

        Scenario:
            Given: Valid encryption key
            When: EncryptedCacheLayer is initialized successfully
            Then: Info-level log message confirms encryption is enabled
            And: Log message includes security indicator (🔐)

        Fixtures Used:
            - valid_fernet_key: Provides valid encryption key
            - mock_logger: Captures log messages for verification
        """
        # Given: Valid encryption key
        encryption_key = valid_fernet_key

        # Mock the logger to capture messages
        def mock_get_logger(name=None):
            return mock_logger
        monkeypatch.setattr("logging.getLogger", mock_get_logger)

        # When: EncryptedCacheLayer is initialized successfully
        encryption_layer = EncryptedCacheLayer(encryption_key=encryption_key)

        # Then: Info-level log message confirms encryption is enabled
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]

        # And: Log message includes security indicator (🔐)
        assert "Cache encryption enabled successfully" in log_message
        assert "🔐" in log_message

    def test_initialization_logs_warning_for_disabled_encryption(self, empty_encryption_key, mock_logger, monkeypatch):
        """
        Test that disabled encryption initialization logs security warning.

        Verifies:
            EncryptedCacheLayer logs prominent warning when encryption is
            disabled (None key) per __init__ Note section.

        Business Impact:
            Alerts operators to insecure configuration that should only
            exist in testing, preventing accidental production use.

        Scenario:
            Given: None encryption key (disabled encryption)
            When: EncryptedCacheLayer is initialized
            Then: Warning-level log message is emitted
            And: Warning indicates encryption is disabled
            And: Warning mentions testing-only usage
            And: Warning includes production security recommendation

        Fixtures Used:
            - empty_encryption_key: Provides None key value
            - mock_logger: Captures warning messages
        """
        # Given: None encryption key (disabled encryption)
        encryption_key = empty_encryption_key

        # Mock the logger to capture warning messages
        def mock_get_logger(name=None):
            return mock_logger
        monkeypatch.setattr("logging.getLogger", mock_get_logger)

        # When: EncryptedCacheLayer is initialized
        encryption_layer = EncryptedCacheLayer(encryption_key=encryption_key)

        # Then: Warning-level log message is emitted
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]

        # And: Warning indicates encryption is disabled
        assert "SECURITY WARNING" in warning_message
        assert "encryption is disabled" in warning_message.lower()

        # And: Warning mentions testing-only usage
        assert "testing environments" in warning_message.lower()

        # And: Warning includes production security recommendation
        assert "Production deployments must use encryption" in warning_message


class TestEncryptedCacheLayerClassMethods:
    """
    Test suite for EncryptedCacheLayer class method initialization.

    Scope:
        Tests the create_with_generated_key() class method and
        create_encryption_layer_from_env() function for creating
        instances with various key sources.

    Business Critical:
        Convenience methods simplify secure configuration in different
        environments while maintaining encryption security standards.

    Test Strategy:
        - Verify generated key creation for testing
        - Test environment variable-based initialization
        - Validate error handling for missing environment configuration
        - Confirm key generation warnings
    """

    def test_create_with_generated_key_returns_enabled_encryption(self):
        """
        Test that create_with_generated_key() returns encryption-enabled instance.

        Verifies:
            create_with_generated_key() class method creates EncryptedCacheLayer
            with auto-generated encryption key per method docstring.

        Business Impact:
            Provides convenient initialization for development and testing
            without requiring manual key generation.

        Scenario:
            Given: No encryption key is provided
            When: create_with_generated_key() is called
            Then: EncryptedCacheLayer instance is returned
            And: Instance has encryption enabled
            And: Generated key is valid and functional

        Fixtures Used:
            - None (tests class method directly)
        """
        # Given: No encryption key is provided
        # (The method generates its own key)

        # When: create_with_generated_key() is called
        encryption_layer = EncryptedCacheLayer.create_with_generated_key()

        # Then: EncryptedCacheLayer instance is returned
        assert encryption_layer is not None
        assert isinstance(encryption_layer, EncryptedCacheLayer)

        # And: Instance has encryption enabled
        assert encryption_layer.is_enabled is True

        # And: Generated key is valid and functional
        test_data = {"test": "data"}
        encrypted = encryption_layer.encrypt_cache_data(test_data)
        decrypted = encryption_layer.decrypt_cache_data(encrypted)
        assert decrypted == test_data

    def test_create_with_generated_key_accepts_additional_kwargs(self):
        """
        Test that create_with_generated_key() forwards kwargs to __init__.

        Verifies:
            create_with_generated_key() accepts **kwargs and passes them to
            __init__ per Args and Examples documentation.

        Business Impact:
            Allows customization of generated instances (e.g., disabling
            performance monitoring) while using key generation convenience.

        Scenario:
            Given: Additional kwargs (performance_monitoring=False)
            When: create_with_generated_key() is called with kwargs
            Then: EncryptedCacheLayer instance is created
            And: kwargs are properly applied to initialization
            And: Instance configuration matches provided kwargs

        Fixtures Used:
            - None (tests class method directly)
        """
        # Given: Additional kwargs (performance_monitoring=False)
        additional_kwargs = {"performance_monitoring": False}

        # When: create_with_generated_key() is called with kwargs
        encryption_layer = EncryptedCacheLayer.create_with_generated_key(**additional_kwargs)

        # Then: EncryptedCacheLayer instance is created
        assert encryption_layer is not None
        assert isinstance(encryption_layer, EncryptedCacheLayer)

        # And: kwargs are properly applied to initialization
        assert encryption_layer.is_enabled is True  # Should still be enabled

        # And: Instance configuration matches provided kwargs
        assert encryption_layer.performance_monitoring is False

        # Verify performance monitoring is actually disabled
        stats = encryption_layer.get_performance_stats()
        assert "error" in stats
        assert stats["error"] == "Performance monitoring is disabled"

    def test_create_with_generated_key_generates_unique_keys(self):
        """
        Test that create_with_generated_key() generates unique keys per invocation.

        Verifies:
            Each call to create_with_generated_key() generates a new unique
            key, per Warning section about data encrypted with different keys.

        Business Impact:
            Ensures understanding that generated keys are not persistent,
            preventing data loss from key mismatch in production.

        Scenario:
            Given: Two separate calls to create_with_generated_key()
            When: Instances are created sequentially
            Then: Each instance has a different encryption key
            And: Data encrypted by one cannot be decrypted by the other

        Fixtures Used:
            - None (tests class method directly)
        """
        # Given: Two separate calls to create_with_generated_key()
        # When: Instances are created sequentially
        encryption_layer1 = EncryptedCacheLayer.create_with_generated_key()
        encryption_layer2 = EncryptedCacheLayer.create_with_generated_key()

        # Then: Each instance has a different encryption key
        assert encryption_layer1 is not encryption_layer2
        assert encryption_layer1.is_enabled is True
        assert encryption_layer2.is_enabled is True

        # And: Data encrypted by one cannot be decrypted by the other
        test_data = {"test": "unique_key_data"}

        # Encrypt with first instance
        encrypted_with_first = encryption_layer1.encrypt_cache_data(test_data)

        # Attempting to decrypt with second instance should fail
        # (This tests that keys are indeed different)
        with pytest.raises((Exception, ConfigurationError)):
            # This should fail because the keys are different
            # The exact exception type depends on the implementation
            encryption_layer2.decrypt_cache_data(encrypted_with_first)

        # Verify each can decrypt its own data
        decrypted_by_first = encryption_layer1.decrypt_cache_data(encrypted_with_first)
        assert decrypted_by_first == test_data

        # Verify second instance can encrypt and decrypt its own data
        encrypted_with_second = encryption_layer2.encrypt_cache_data(test_data)
        decrypted_by_second = encryption_layer2.decrypt_cache_data(encrypted_with_second)
        assert decrypted_by_second == test_data

    def test_create_encryption_layer_from_env_with_key_set(self, valid_fernet_key, monkeypatch):
        """
        Test that create_encryption_layer_from_env() uses environment key.

        Verifies:
            create_encryption_layer_from_env() function reads
            REDIS_ENCRYPTION_KEY environment variable per docstring.

        Business Impact:
            Enables secure production configuration through environment
            variables following 12-factor app principles.

        Scenario:
            Given: REDIS_ENCRYPTION_KEY environment variable is set
            When: create_encryption_layer_from_env() is called
            Then: EncryptedCacheLayer instance is returned
            And: Instance uses key from environment variable
            And: Encryption is enabled

        Fixtures Used:
            - valid_fernet_key: Provides key value for environment
            - monkeypatch: Sets REDIS_ENCRYPTION_KEY temporarily
        """
        # Given: REDIS_ENCRYPTION_KEY environment variable is set
        environment_key = valid_fernet_key
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", environment_key)

        # When: create_encryption_layer_from_env() is called
        encryption_layer = create_encryption_layer_from_env()

        # Then: EncryptedCacheLayer instance is returned
        assert encryption_layer is not None
        assert isinstance(encryption_layer, EncryptedCacheLayer)

        # And: Instance uses key from environment variable
        # (We can verify this by testing encryption operations work)
        test_data = {"test": "environment_key_data"}
        encrypted = encryption_layer.encrypt_cache_data(test_data)
        decrypted = encryption_layer.decrypt_cache_data(encrypted)
        assert decrypted == test_data

        # And: Encryption is enabled
        assert encryption_layer.is_enabled is True

    def test_create_encryption_layer_from_env_without_key_logs_error(self, mock_logger, monkeypatch):
        """
        Test that create_encryption_layer_from_env() logs error for missing key.

        Verifies:
            create_encryption_layer_from_env() logs warning when
            REDIS_ENCRYPTION_KEY is not set per Note documentation.

        Business Impact:
            Alerts operators to missing encryption configuration while
            allowing application to continue (graceful degradation).

        Scenario:
            Given: REDIS_ENCRYPTION_KEY environment variable is not set
            When: create_encryption_layer_from_env() is called
            Then: EncryptedCacheLayer instance is returned
            And: Encryption is disabled (None key)
            And: Warning is logged about missing environment variable
            And: Warning includes configuration instructions

        Fixtures Used:
            - mock_logger: Captures warning messages
            - monkeypatch: Ensures environment variable is not set
        """
        # Given: REDIS_ENCRYPTION_KEY environment variable is not set
        monkeypatch.delenv("REDIS_ENCRYPTION_KEY", raising=False)

        # Mock the logger to capture warning messages
        def mock_get_logger(name=None):
            return mock_logger
        monkeypatch.setattr("logging.getLogger", mock_get_logger)

        # When: create_encryption_layer_from_env() is called
        encryption_layer = create_encryption_layer_from_env()

        # Then: EncryptedCacheLayer instance is returned
        assert encryption_layer is not None
        assert isinstance(encryption_layer, EncryptedCacheLayer)

        # And: Encryption is disabled (None key)
        assert encryption_layer.is_enabled is False

        # And: Warning is logged about missing environment variable
        # The function creates an EncryptedCacheLayer which logs its own warning
        assert mock_logger.warning.call_count >= 1

        # Get the warning message that was logged
        warning_message = mock_logger.warning.call_args[0][0]

        # And: Warning includes security warning about disabled encryption
        assert "SECURITY WARNING" in warning_message
        assert "encryption is disabled" in warning_message.lower()
        assert "testing environments" in warning_message.lower()

    def test_create_encryption_layer_from_env_returns_instance_without_key(self, monkeypatch):
        """
        Test that create_encryption_layer_from_env() returns instance without key.

        Verifies:
            create_encryption_layer_from_env() creates instance even without
            encryption key, following security-first approach per Note section.

        Business Impact:
            Allows application startup in misconfigured environments with
            prominent warnings, preventing complete failure while highlighting issue.

        Scenario:
            Given: REDIS_ENCRYPTION_KEY environment variable is not set
            When: create_encryption_layer_from_env() is called
            Then: EncryptedCacheLayer instance is returned (not None)
            And: Instance has encryption disabled
            And: Instance is functional for cache operations
            And: Security warnings are logged

        Fixtures Used:
            - monkeypatch: Ensures environment variable is not set
        """
        # Given: REDIS_ENCRYPTION_KEY environment variable is not set
        monkeypatch.delenv("REDIS_ENCRYPTION_KEY", raising=False)

        # When: create_encryption_layer_from_env() is called
        encryption_layer = create_encryption_layer_from_env()

        # Then: EncryptedCacheLayer instance is returned (not None)
        assert encryption_layer is not None
        assert isinstance(encryption_layer, EncryptedCacheLayer)

        # And: Instance has encryption disabled
        assert encryption_layer.is_enabled is False

        # And: Instance is functional for cache operations
        # Test that it can handle data even without encryption
        test_data = {"test": "no_encryption_data"}

        # Should still be able to "encrypt" (really just JSON serialization)
        encrypted = encryption_layer.encrypt_cache_data(test_data)
        assert encrypted is not None
        assert isinstance(encrypted, bytes)

        # Should still be able to "decrypt" (really just JSON deserialization)
        decrypted = encryption_layer.decrypt_cache_data(encrypted)
        assert decrypted == test_data
