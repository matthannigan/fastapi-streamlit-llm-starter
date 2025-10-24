"""
Unit tests for EncryptedCacheLayer error handling behavior.

This test module verifies that the EncryptedCacheLayer class properly handles
error scenarios as documented in the Raises sections of the public contract,
including serialization failures, decryption errors, invalid token handling,
and corrupted data scenarios.

Test Coverage:
    - Serialization errors with non-JSON-serializable data
    - Decryption errors with corrupted or invalid data
    - InvalidToken exception handling
    - ConfigurationError raising with proper context
    - Error message clarity and helpfulness
    - JSON deserialization error handling
"""

import pytest
from app.core.exceptions import ConfigurationError


class TestEncryptCacheDataErrorHandling:
    """
    Test suite for encrypt_cache_data() error handling.

    Scope:
        Tests error scenarios for encrypt_cache_data() covering all
        documented exception conditions from Raises section.

    Business Critical:
        Proper error handling prevents data corruption and provides
        clear debugging information when encryption fails.

    Test Strategy:
        - Test serialization errors with invalid data types
        - Verify ConfigurationError is raised appropriately
        - Validate error messages provide actionable guidance
        - Confirm error context includes debugging information
    """

    def test_encrypt_cache_data_with_non_serializable_datetime_raises_error(self, encryption_with_valid_key):
        """
        Test that encrypt_cache_data() raises ConfigurationError for datetime objects.

        Verifies:
            encrypt_cache_data() raises ConfigurationError when data contains
            datetime objects that cannot be JSON-serialized per Raises section.

        Business Impact:
            Prevents silent failures with non-serializable data, catching
            configuration issues early with clear error messages.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary containing datetime object
            When: encrypt_cache_data() is called
            Then: ConfigurationError is raised
            And: Error message indicates serialization failure
            And: Error message lists JSON-serializable types
            And: Error context includes "serialization_error" type

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
        """
        from datetime import datetime

        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Dictionary containing datetime object
        data_with_datetime = {
            "user_id": 123,
            "created_at": datetime.now(),  # Non-serializable datetime
            "name": "Test User"
        }

        # When: encrypt_cache_data() is called
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(data_with_datetime)

        # Then: ConfigurationError is raised
        assert exc_info.type == ConfigurationError

        # And: Error message indicates serialization failure
        error_message = str(exc_info.value)
        assert "Failed to serialize cache data" in error_message

        # And: Error message lists JSON-serializable types
        assert "Basic types: str, int, float, bool, None" in error_message
        assert "Collections: list, dict" in error_message
        assert "Avoid: datetime, custom objects, functions" in error_message

        # And: Error context includes "serialization_error" type
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "serialization_error"
        assert error_context["data_type"] == "dict"
        assert "original_error" in error_context

    def test_encrypt_cache_data_with_custom_object_raises_error(self, encryption_with_valid_key):
        """
        Test that encrypt_cache_data() raises ConfigurationError for custom objects.

        Verifies:
            encrypt_cache_data() rejects custom class instances that cannot
            be JSON-serialized per serialization requirements.

        Business Impact:
            Prevents cache corruption with unsupported data types,
            guiding developers to use serializable structures.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary containing custom class instance
            When: encrypt_cache_data() is called
            Then: ConfigurationError is raised
            And: Error message indicates serialization error
            And: Error message suggests avoiding custom objects
            And: Error context includes data type information

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
        """
        # Custom class that is not JSON-serializable
        class CustomObject:
            def __init__(self, value):
                self.value = value

        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Dictionary containing custom class instance
        data_with_custom_object = {
            "user_id": 123,
            "custom_data": CustomObject("test_value"),  # Non-serializable object
            "name": "Test User"
        }

        # When: encrypt_cache_data() is called
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(data_with_custom_object)

        # Then: ConfigurationError is raised
        assert exc_info.type == ConfigurationError

        # And: Error message indicates serialization error
        error_message = str(exc_info.value)
        assert "Failed to serialize cache data" in error_message

        # And: Error message suggests avoiding custom objects
        assert "Avoid: datetime, custom objects, functions" in error_message

        # And: Error context includes data type information
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "serialization_error"
        assert error_context["data_type"] == "dict"
        assert "original_error" in error_context

    def test_encrypt_cache_data_with_function_raises_error(self, encryption_with_valid_key):
        """
        Test that encrypt_cache_data() raises ConfigurationError for functions.

        Verifies:
            encrypt_cache_data() rejects dictionary containing function
            references per JSON serialization limitations.

        Business Impact:
            Prevents invalid cache data that would fail on retrieval,
            maintaining cache data integrity.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary containing function reference
            When: encrypt_cache_data() is called
            Then: ConfigurationError is raised
            And: Error message indicates serialization failure
            And: Error message lists valid types (excluding functions)

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
        """
        # A sample function for testing
        def sample_function():
            return "This function is not JSON serializable"

        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Dictionary containing function reference
        data_with_function = {
            "user_id": 123,
            "callback": sample_function,  # Non-serializable function
            "name": "Test User"
        }

        # When: encrypt_cache_data() is called
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(data_with_function)

        # Then: ConfigurationError is raised
        assert exc_info.type == ConfigurationError

        # And: Error message indicates serialization failure
        error_message = str(exc_info.value)
        assert "Failed to serialize cache data" in error_message

        # And: Error message lists valid types (excluding functions)
        assert "Basic types: str, int, float, bool, None" in error_message
        assert "Collections: list, dict" in error_message
        assert "Avoid: datetime, custom objects, functions" in error_message

    def test_encrypt_cache_data_serialization_error_includes_helpful_context(self, encryption_with_valid_key):
        """
        Test that serialization errors include helpful debugging context.

        Verifies:
            ConfigurationError for serialization failures includes context
            with error type, data type, and original error per error handling.

        Business Impact:
            Provides developers with actionable error information for
            quick issue resolution and debugging.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Data that cannot be serialized
            When: encrypt_cache_data() raises ConfigurationError
            Then: Error context includes "error_type": "serialization_error"
            And: Error context includes "data_type" information
            And: Error context includes "original_error" details
            And: Error message includes guidance on fixing the issue

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
        """
        from datetime import datetime

        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Data that cannot be serialized
        unserializable_data = {
            "timestamp": datetime.now(),  # This will cause serialization error
            "data": "test"
        }

        # When: encrypt_cache_data() raises ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(unserializable_data)

        # Then: Error context includes "error_type": "serialization_error"
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "serialization_error"

        # And: Error context includes "data_type" information
        assert error_context["data_type"] == "dict"

        # And: Error context includes "original_error" details
        assert "original_error" in error_context
        assert error_context["original_error"] != ""
        assert "datetime" in error_context["original_error"] or "not JSON serializable" in error_context["original_error"].lower()

        # And: Error message includes guidance on fixing the issue
        error_message = str(exc_info.value)
        assert "Ensure cache data contains only JSON-serializable types" in error_message
        assert "Basic types: str, int, float, bool, None" in error_message
        assert "Collections: list, dict" in error_message

    def test_encrypt_cache_data_encryption_failure_raises_configuration_error(self, encryption_with_valid_key, monkeypatch):
        """
        Test that encryption failures raise ConfigurationError with context.

        Verifies:
            encrypt_cache_data() raises ConfigurationError for encryption
            failures with proper error context per Raises documentation.

        Business Impact:
            Ensures encryption failures are caught and reported clearly,
            preventing silent data corruption.

        Scenario:
            Given: EncryptedCacheLayer with potentially corrupted key
            And: Valid serializable data
            When: Encryption operation fails internally
            Then: ConfigurationError is raised
            And: Error message indicates encryption failure
            And: Error context includes "encryption_failure" type
            And: Error suggests possible causes (corrupted key, etc.)

        Fixtures Used:
            - encryption_with_valid_key: Base encryption instance
            - monkeypatch: Simulate encryption failure
        """
        # Given: EncryptedCacheLayer with potentially corrupted key
        encryption = encryption_with_valid_key

        # And: Valid serializable data
        valid_data = {"user_id": 123, "name": "Test User", "active": True}

        # When: Encryption operation fails internally
        def mock_encrypt_failure(*args, **kwargs):
            raise Exception("Simulated encryption failure")

        # Patch the encrypt method to simulate failure
        monkeypatch.setattr(encryption.fernet, "encrypt", mock_encrypt_failure)

        # Then: ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(valid_data)

        # And: Error message indicates encryption failure
        error_message = str(exc_info.value)
        assert "Data encryption failed" in error_message

        # And: Error context includes "encryption_failure" type
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "encryption_failure"

        # And: Error suggests possible causes (corrupted key, etc.)
        assert "Corrupted encryption key" in error_message
        assert "System resource constraints" in error_message
        assert "Cryptographic library issues" in error_message

    def test_encrypt_cache_data_with_circular_reference_raises_error(self, encryption_with_valid_key):
        """
        Test that encrypt_cache_data() handles circular references appropriately.

        Verifies:
            encrypt_cache_data() raises ConfigurationError when data
            contains circular references that break JSON serialization.

        Business Impact:
            Prevents infinite loops during serialization, maintaining
            application stability and performance.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary with circular reference to itself
            When: encrypt_cache_data() is called
            Then: ConfigurationError is raised (or ValueError caught)
            And: Error indicates serialization issue
            And: System remains stable (no infinite loop)

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
        """
        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Dictionary with circular reference to itself
        circular_data = {"name": "test", "value": 123}
        circular_data["self"] = circular_data  # Create circular reference

        # When: encrypt_cache_data() is called
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(circular_data)

        # Then: ConfigurationError is raised
        assert exc_info.type == ConfigurationError

        # And: Error indicates serialization issue
        error_message = str(exc_info.value)
        assert "Failed to serialize cache data" in error_message

        # And: System remains stable (test completes without infinite loop)
        # The fact that we reach this assertion proves system stability
        assert True  # Test completes successfully

        # Additionally verify the error context shows it's a serialization error
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "serialization_error"

    def test_encrypt_cache_data_error_message_suggests_fix(self, encryption_with_valid_key):
        """
        Test that encryption error messages include fix suggestions.

        Verifies:
            ConfigurationError messages for encryption failures include
            actionable steps to fix the issue per error message patterns.

        Business Impact:
            Reduces troubleshooting time by providing developers with
            clear guidance on resolving encryption issues.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Data that causes serialization error
            When: ConfigurationError is raised
            Then: Error message includes "To fix this issue:" section
            Or: Error message includes guidance on valid data types
            And: Message suggests specific actions to resolve error

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
        """
        from datetime import datetime

        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Data that causes serialization error
        problematic_data = {
            "timestamp": datetime.now(),  # This will cause serialization error
            "user_id": 123
        }

        # When: ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(problematic_data)

        # Then: Error message includes guidance on valid data types
        error_message = str(exc_info.value)
        assert "Ensure cache data contains only JSON-serializable types" in error_message

        # And: Message suggests specific actions to resolve error
        assert "Basic types: str, int, float, bool, None" in error_message
        assert "Collections: list, dict" in error_message
        assert "Avoid: datetime, custom objects, functions" in error_message

        # Verify the message structure is helpful and actionable
        assert error_message.count("\n\n") >= 1  # Has blank lines for readability
        assert "🔒" in error_message  # Has security emoji for visual identification


class TestDecryptCacheDataErrorHandling:
    """
    Test suite for decrypt_cache_data() error handling.

    Scope:
        Tests error scenarios for decrypt_cache_data() covering all
        documented exception conditions from Raises section.

    Business Critical:
        Proper decryption error handling prevents application crashes
        and provides clear feedback on data integrity issues.

    Test Strategy:
        - Test InvalidToken exception handling
        - Verify JSON deserialization error handling
        - Test corrupted data scenarios
        - Validate error messages and context
        - Test wrong encryption key detection
    """

    def test_decrypt_cache_data_with_corrupted_bytes_raises_error(self, encryption_with_valid_key, sample_invalid_encrypted_bytes):
        """
        Test that decrypt_cache_data() raises ConfigurationError for corrupted data.

        Verifies:
            decrypt_cache_data() raises ConfigurationError when encrypted
            data is corrupted per Raises documentation.

        Business Impact:
            Detects cache corruption early, preventing silent data loss
            or application errors from invalid cached data.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Corrupted encrypted bytes (not valid Fernet token)
            When: decrypt_cache_data() is called
            Then: ConfigurationError is raised
            And: Error message indicates decryption failure
            And: Error suggests possible causes (corruption, wrong key)
            And: Error context includes "decryption_failure" type

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_invalid_encrypted_bytes: Corrupted data
        """
        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Corrupted encrypted bytes (not valid Fernet token)
        corrupted_data = sample_invalid_encrypted_bytes

        # When: decrypt_cache_data() is called
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.decrypt_cache_data(corrupted_data)

        # Then: ConfigurationError is raised
        assert exc_info.type == ConfigurationError

        # And: Error message indicates deserialization failure (fallback behavior)
        error_message = str(exc_info.value)
        assert "Failed to deserialize cache data" in error_message

        # And: Error suggests possible causes (corruption, wrong key)
        assert "Corrupted cache data" in error_message
        assert "Wrong encryption key" in error_message
        assert "Data format mismatch" in error_message

        # And: Error context includes "deserialization_error" type (due to fallback)
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "deserialization_error"
        assert "original_error" in error_context

    def test_decrypt_cache_data_with_wrong_key_raises_error(self, encryption_with_valid_key, encryption_with_generated_key):
        """
        Test that decrypt_cache_data() detects wrong encryption key.

        Verifies:
            decrypt_cache_data() raises ConfigurationError when data was
            encrypted with different key per key rotation scenarios.

        Business Impact:
            Prevents decryption with wrong key that would produce garbage
            data, detecting key rotation issues.

        Scenario:
            Given: EncryptedCacheLayer with one encryption key
            And: Data encrypted with different encryption key
            When: decrypt_cache_data() is called
            Then: ConfigurationError is raised
            And: Error message indicates invalid encryption key
            And: Error suggests key rotation issues
            And: Error context includes helpful debugging info

        Fixtures Used:
            - encryption_with_valid_key: Instance with one key
            - encryption_with_generated_key: Generate data with different key
        """
        # Given: EncryptedCacheLayer with one encryption key
        decryption_encryption = encryption_with_valid_key

        # And: Data encrypted with different encryption key
        encryption_with_different_key = encryption_with_generated_key
        test_data = {"user_id": 123, "name": "Test User"}
        data_with_different_key = encryption_with_different_key.encrypt_cache_data(test_data)

        # When: decrypt_cache_data() is called
        with pytest.raises(ConfigurationError) as exc_info:
            decryption_encryption.decrypt_cache_data(data_with_different_key)

        # Then: ConfigurationError is raised
        assert exc_info.type == ConfigurationError

        # And: Error message indicates deserialization failure (fallback behavior)
        error_message = str(exc_info.value)
        assert "Failed to deserialize cache data" in error_message

        # And: Error suggests key rotation issues (among other causes)
        assert "Wrong encryption key" in error_message

        # And: Error context includes helpful debugging info
        error_context = exc_info.value.context
        assert error_context is not None
        assert error_context["error_type"] == "deserialization_error"
        assert "original_error" in error_context

    def test_decrypt_cache_data_error_includes_data_size_context(self, encryption_with_valid_key, sample_invalid_encrypted_bytes):
        """
        Test that decryption errors include data size in error context.

        Verifies:
            ConfigurationError for decryption failures includes data size
            in context for debugging per error context patterns.

        Business Impact:
            Provides operators with data size information to identify
            potential corruption patterns or size-related issues.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Invalid encrypted data of specific size
            When: decrypt_cache_data() raises ConfigurationError
            Then: Error context includes "data_size" field
            And: Data size value matches input bytes length
            And: Size information aids in debugging

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_invalid_encrypted_bytes: Known size invalid data
        """
        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Invalid encrypted data of specific size
        invalid_data = sample_invalid_encrypted_bytes
        expected_size = len(invalid_data)

        # When: decrypt_cache_data() raises ConfigurationError
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.decrypt_cache_data(invalid_data)

        # Then: Error context includes "data_size" field
        error_context = exc_info.value.context
        assert error_context is not None
        assert "data_size" in error_context

        # And: Data size value matches input bytes length
        assert error_context["data_size"] == expected_size

        # And: Size information aids in debugging (we have access to it)
        assert isinstance(error_context["data_size"], int)
        assert error_context["data_size"] > 0

    def test_decrypt_cache_data_error_suggests_possible_causes(self, encryption_with_valid_key, sample_invalid_encrypted_bytes):
        """
        Test that decryption error messages suggest possible causes.

        Verifies:
            ConfigurationError messages for decryption include list of
            possible causes per error message format.

        Business Impact:
            Guides troubleshooting by suggesting likely root causes,
            reducing time to resolution for cache issues.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Data that causes decryption error
            When: ConfigurationError is raised
            Then: Error message includes "This may indicate:" section
            And: Message lists possible causes (corrupted data, wrong key, etc.)
            And: Suggestions are actionable and specific

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_invalid_encrypted_bytes: Triggers error
        """
        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Data that causes decryption error
        problematic_data = sample_invalid_encrypted_bytes

        # When: ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.decrypt_cache_data(problematic_data)

        # Then: Error message includes "This may indicate:" section
        error_message = str(exc_info.value)
        assert "This may indicate:" in error_message

        # And: Message lists possible causes (corrupted data, wrong key, etc.)
        assert "Corrupted cache data" in error_message
        assert "Wrong encryption key" in error_message
        assert "Data format mismatch" in error_message
        assert "Cache corruption" in error_message

        # And: Suggestions are actionable and specific
        # The suggestions are specific and give clear direction
        assert "key" in error_message.lower()
        assert "corruption" in error_message.lower()

    def test_decrypt_cache_data_invalid_token_triggers_fallback_handling(self, encryption_with_valid_key, sample_unencrypted_json_bytes, mock_logger, monkeypatch):
        """
        Test that InvalidToken exception triggers backward compatibility fallback.

        Verifies:
            decrypt_cache_data() catches InvalidToken exception and attempts
            to handle unencrypted data per backward compatibility behavior.

        Business Impact:
            Enables migration from unencrypted to encrypted cache without
            losing existing cached data or causing errors.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Unencrypted JSON bytes (InvalidToken will be raised)
            When: decrypt_cache_data() is called
            Then: InvalidToken exception is caught internally
            And: Fallback to unencrypted JSON parsing is attempted
            And: Warning is logged about unencrypted data
            And: Data is successfully returned if valid JSON

        Fixtures Used:
            - encryption_with_valid_key: Encryption-enabled instance
            - sample_unencrypted_json_bytes: Raw JSON triggering fallback
            - mock_logger: Captures backward compatibility warning
        """
        # Given: EncryptedCacheLayer with encryption enabled
        encryption = encryption_with_valid_key

        # And: Unencrypted JSON bytes (InvalidToken will be raised)
        unencrypted_data = sample_unencrypted_json_bytes

        # Patch the logger to capture the warning
        monkeypatch.setattr(encryption.logger, "warning", mock_logger)

        # When: decrypt_cache_data() is called
        result = encryption.decrypt_cache_data(unencrypted_data)

        # Then: InvalidToken exception is caught internally
        # (Verified by successful execution and warning logged)

        # And: Fallback to unencrypted JSON parsing is attempted
        # And: Data is successfully returned if valid JSON
        assert isinstance(result, dict)
        assert "user_id" in result  # Based on sample_cache_data structure

        # And: Warning is logged about unencrypted data
        mock_logger.assert_called_once()
        warning_call = mock_logger.call_args[0][0]  # Get the warning message
        assert "Attempting to read unencrypted cache data" in warning_call
        assert "backward compatibility" in warning_call


class TestErrorMessageQuality:
    """
    Test suite for error message quality and helpfulness.

    Scope:
        Tests that error messages from EncryptedCacheLayer are clear,
        actionable, and include appropriate context for debugging.

    Business Critical:
        High-quality error messages reduce troubleshooting time and
        improve developer experience when issues occur.

    Test Strategy:
        - Verify error messages are descriptive
        - Confirm error context includes debugging information
        - Validate fix suggestions are actionable
        - Test error formatting and structure
    """

    def test_configuration_errors_include_emoji_prefix(self, encryption_with_valid_key):
        """
        Test that ConfigurationError messages include security emoji prefix.

        Verifies:
            ConfigurationError messages for encryption issues include
            🔒 emoji prefix per error message formatting pattern.

        Business Impact:
            Makes encryption-related errors visually distinctive in logs,
            helping operators quickly identify security-related issues.

        Scenario:
            Given: EncryptedCacheLayer that will raise ConfigurationError
            When: Error is raised (serialization, decryption, or init error)
            Then: Error message starts with "🔒 ENCRYPTION ERROR:" or similar
            And: Emoji makes error visually distinctive
            And: Message format is consistent across error types

        Fixtures Used:
            - encryption_with_valid_key: Various error scenarios
        """
        from datetime import datetime

        # Test serialization error
        encryption = encryption_with_valid_key
        data_with_datetime = {"timestamp": datetime.now()}

        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(data_with_datetime)

        # Then: Error message starts with "🔒 ENCRYPTION ERROR:" or similar
        error_message = str(exc_info.value)
        assert "🔒" in error_message
        assert "ENCRYPTION ERROR" in error_message

        # Test decryption error with corrupted data
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.decrypt_cache_data(b"corrupted-data")

        error_message = str(exc_info.value)
        assert "🔒" in error_message
        assert "DECRYPTION ERROR" in error_message

        # And: Emoji makes error visually distinctive
        # The presence of 🔒 emoji makes errors visually distinctive
        assert error_message.count("🔒") >= 1

        # And: Message format is consistent across error types
        # Both error types follow the same pattern with emoji prefix

    def test_error_messages_include_blank_lines_for_readability(self, encryption_with_valid_key):
        """
        Test that error messages use blank lines to improve readability.

        Verifies:
            ConfigurationError messages include newlines between sections
            for better formatting per error message pattern.

        Business Impact:
            Improves error message readability in logs and terminal output,
            making errors easier to parse quickly.

        Scenario:
            Given: EncryptedCacheLayer raising ConfigurationError
            When: Error message is formatted
            Then: Message includes "\\n\\n" between sections
            And: Error details are separated from suggestions
            And: Overall format is easy to read

        Fixtures Used:
            - encryption_with_valid_key: Trigger various errors
        """
        from datetime import datetime

        # Given: EncryptedCacheLayer raising ConfigurationError
        encryption = encryption_with_valid_key
        problematic_data = {"timestamp": datetime.now()}

        # When: Error message is formatted
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(problematic_data)

        error_message = str(exc_info.value)

        # Then: Message includes "\n\n" between sections
        assert "\n\n" in error_message

        # And: Error details are separated from suggestions
        # The message should have distinct sections separated by blank lines
        sections = error_message.split("\n\n")
        assert len(sections) >= 2  # At least 2 sections

        # First section should contain the error description
        assert "Failed to serialize cache data" in sections[0]

        # Later sections should contain suggestions or guidance
        combined_sections = " ".join(sections[1:])
        assert "JSON-serializable" in combined_sections

        # And: Overall format is easy to read
        # The presence of blank lines and structured content makes it readable
        assert error_message.count("\n") >= 4  # Should have multiple lines for structure

    def test_error_context_includes_error_type_classification(self, encryption_with_valid_key):
        """
        Test that error context includes error_type field for classification.

        Verifies:
            ConfigurationError context dict includes "error_type" field
            with classification (serialization_error, encryption_failure, etc.).

        Business Impact:
            Enables automated error monitoring and classification in
            production systems for better observability.

        Scenario:
            Given: EncryptedCacheLayer raising ConfigurationError
            When: Error is raised with context
            Then: context["error_type"] is present
            And: error_type value is descriptive and consistent
            And: Error type enables automated categorization

        Fixtures Used:
            - encryption_with_valid_key: Various error scenarios
        """
        from datetime import datetime

        # Test serialization error
        encryption = encryption_with_valid_key
        problematic_data = {"timestamp": datetime.now()}

        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(problematic_data)

        # Then: context["error_type"] is present
        error_context = exc_info.value.context
        assert error_context is not None
        assert "error_type" in error_context

        # And: error_type value is descriptive and consistent
        assert error_context["error_type"] == "serialization_error"

        # Test decryption error (actually falls back to deserialization error)
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.decrypt_cache_data(b"invalid-data")

        error_context = exc_info.value.context
        assert "error_type" in error_context
        assert error_context["error_type"] == "deserialization_error"

        # And: Error type enables automated categorization
        # The error types are standardized for automated processing
        valid_error_types = [
            "serialization_error",
            "encryption_failure",
            "decryption_failure",
            "deserialization_error",
            "missing_dependency",
            "invalid_encryption_key"
        ]
        assert error_context["error_type"] in valid_error_types

    def test_error_context_preserves_original_error_information(self, encryption_with_valid_key):
        """
        Test that error context includes original_error details.

        Verifies:
            ConfigurationError context includes "original_error" field
            with original exception message for debugging.

        Business Impact:
            Preserves low-level error details for developers debugging
            encryption issues, without exposing in main message.

        Scenario:
            Given: EncryptedCacheLayer raising ConfigurationError
            And: Underlying exception with specific error message
            When: ConfigurationError is raised
            Then: context["original_error"] contains original message
            And: Original error details are preserved
            And: Developers can access low-level debugging info

        Fixtures Used:
            - encryption_with_valid_key: Trigger wrapped errors
        """
        from datetime import datetime

        # Given: EncryptedCacheLayer raising ConfigurationError
        encryption = encryption_with_valid_key
        problematic_data = {"timestamp": datetime.now()}

        # When: ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(problematic_data)

        # Then: context["original_error"] contains original message
        error_context = exc_info.value.context
        assert error_context is not None
        assert "original_error" in error_context

        # And: Original error details are preserved
        original_error = error_context["original_error"]
        assert original_error != ""
        assert len(original_error) > 0

        # The original error should contain information about datetime serialization
        assert "datetime" in original_error.lower() or "not json serializable" in original_error.lower()

        # And: Developers can access low-level debugging info
        # The context is accessible and contains useful debugging information
        assert isinstance(original_error, str)

        # Test with decryption error as well
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.decrypt_cache_data(b"invalid-data")

        error_context = exc_info.value.context
        assert "original_error" in error_context
        assert error_context["original_error"] != ""

    def test_serialization_error_lists_supported_types(self, encryption_with_valid_key):
        """
        Test that serialization errors list JSON-serializable types.

        Verifies:
            Serialization ConfigurationError messages include list of
            supported types (str, int, float, bool, None, list, dict).

        Business Impact:
            Guides developers to use correct data types, preventing
            repeated serialization errors.

        Scenario:
            Given: EncryptedCacheLayer with non-serializable data
            When: Serialization ConfigurationError is raised
            Then: Error message lists "Basic types: str, int, float, bool, None"
            And: Error message lists "Collections: list, dict"
            And: Error message suggests avoiding datetime, custom objects

        Fixtures Used:
            - encryption_with_valid_key: Trigger serialization error
        """
        from datetime import datetime

        # Given: EncryptedCacheLayer with non-serializable data
        encryption = encryption_with_valid_key
        problematic_data = {"timestamp": datetime.now()}

        # When: Serialization ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data(problematic_data)

        error_message = str(exc_info.value)

        # Then: Error message lists "Basic types: str, int, float, bool, None"
        assert "Basic types: str, int, float, bool, None" in error_message

        # And: Error message lists "Collections: list, dict"
        assert "Collections: list, dict" in error_message

        # And: Error message suggests avoiding datetime, custom objects
        assert "Avoid: datetime, custom objects, functions" in error_message

        # Verify the message is comprehensive and helpful
        assert "JSON-serializable" in error_message
        assert "Ensure cache data contains only JSON-serializable types" in error_message

    def test_initialization_error_provides_key_generation_command(self, invalid_fernet_key_format):
        """
        Test that initialization errors include key generation command.

        Verifies:
            Invalid key ConfigurationError includes command to generate
            valid Fernet key per error guidance pattern.

        Business Impact:
            Provides developers with immediate solution to fix invalid
            key configuration, reducing support burden.

        Scenario:
            Given: EncryptedCacheLayer with invalid encryption key
            When: Initialization ConfigurationError is raised
            Then: Error message includes key generation command
            And: Command is: python -c "from cryptography.fernet import Fernet..."
            And: Instructions mention environment variable setting

        Fixtures Used:
            - invalid_fernet_key_format: Trigger initialization error
        """
        from app.infrastructure.cache.encryption import EncryptedCacheLayer

        # Given: EncryptedCacheLayer with invalid encryption key
        invalid_key = invalid_fernet_key_format

        # When: Initialization ConfigurationError is raised
        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key=invalid_key)

        error_message = str(exc_info.value)

        # Then: Error message includes key generation command
        assert "python -c" in error_message
        assert "from cryptography.fernet import Fernet" in error_message
        assert "Fernet.generate_key().decode()" in error_message

        # And: Command is properly formatted
        assert 'python -c "from cryptography.fernet import Fernet' in error_message

        # And: Instructions mention environment variable setting
        assert "Set REDIS_ENCRYPTION_KEY environment variable" in error_message

        # Verify it's formatted as helpful guidance
        assert "To fix this issue:" in error_message
        assert "Generate a new key:" in error_message
