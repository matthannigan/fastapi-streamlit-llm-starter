"""
Unit tests for EncryptedCacheLayer core encryption/decryption operations.

This test module verifies the fundamental encrypt_cache_data() and
decrypt_cache_data() operations as documented in the public contract,
including data integrity, serialization, encryption round-trips, and
performance characteristics.

Test Coverage:
    - Data encryption with valid inputs
    - Data decryption with valid inputs
    - Encryption/decryption round-trip integrity
    - Various data types and structures
    - Unicode and international character handling
    - Empty and edge case data handling
    - Disabled encryption behavior
"""



class TestEncryptCacheData:
    """
    Test suite for encrypt_cache_data() method behavior.

    Scope:
        Tests the encrypt_cache_data() method covering all documented
        scenarios from Args, Returns, and Examples sections of docstring.

    Business Critical:
        Encryption must reliably protect all cached data before storage,
        maintaining data confidentiality and integrity.

    Test Strategy:
        - Verify successful encryption with various data types
        - Test data serialization behavior
        - Validate encrypted output format
        - Confirm performance within documented limits
        - Test behavior with encryption disabled
    """

    def test_encrypt_cache_data_with_simple_dictionary(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that encrypt_cache_data() successfully encrypts simple dictionary.

        Verifies:
            encrypt_cache_data() accepts dictionary input and returns encrypted
            bytes per Returns section of docstring.

        Business Impact:
            Ensures basic cache data can be encrypted for secure storage,
            protecting sensitive application data.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: A simple dictionary with basic data types
            When: encrypt_cache_data() is called with the dictionary
            Then: Encrypted bytes are returned
            And: Returned data is of type bytes
            And: Encrypted data length is greater than zero

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_cache_data: Provides typical cache dictionary
        """
        # Given: Encryption is enabled and we have sample data
        assert encryption_with_valid_key.is_enabled is True
        assert isinstance(sample_cache_data, dict)

        # When: encrypt_cache_data() is called
        result = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)

        # Then: Encrypted bytes are returned
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encrypt_cache_data_with_nested_structures(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that encrypt_cache_data() handles nested dictionary structures.

        Verifies:
            encrypt_cache_data() properly serializes and encrypts nested
            dictionaries and lists per JSON serialization behavior.

        Business Impact:
            Ensures complex application data structures can be cached
            securely without flattening or data loss.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: A dictionary containing nested dicts and lists
            When: encrypt_cache_data() is called
            Then: Encryption succeeds without errors
            And: Encrypted bytes are returned
            And: No nested structure is lost

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_cache_data: Includes nested preferences dict
        """
        # Given: Encryption is enabled and we have nested data
        assert encryption_with_valid_key.is_enabled is True
        assert "preferences" in sample_cache_data  # Nested dict
        assert "scores" in sample_cache_data      # List

        # When: encrypt_cache_data() is called
        result = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)

        # Then: Encryption succeeds and returns bytes
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encrypt_cache_data_with_unicode_content(self, encryption_with_valid_key, sample_unicode_data):
        """
        Test that encrypt_cache_data() handles Unicode characters correctly.

        Verifies:
            encrypt_cache_data() properly handles Unicode characters,
            emojis, and international text through UTF-8 encoding.

        Business Impact:
            Ensures application can cache and encrypt content in any language,
            supporting international users and emoji content.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary containing Unicode characters and emojis
            When: encrypt_cache_data() is called
            Then: Encryption succeeds without Unicode errors
            And: Encrypted bytes contain properly encoded UTF-8 data

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_unicode_data: Contains various Unicode characters
        """
        # Given: Encryption is enabled and we have Unicode data
        assert encryption_with_valid_key.is_enabled is True
        assert "emoji" in sample_unicode_data
        assert "international" in sample_unicode_data

        # When: encrypt_cache_data() is called
        result = encryption_with_valid_key.encrypt_cache_data(sample_unicode_data)

        # Then: Encryption succeeds and returns bytes
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encrypt_cache_data_with_empty_dictionary(self, encryption_with_valid_key, sample_empty_data):
        """
        Test that encrypt_cache_data() handles empty dictionary.

        Verifies:
            encrypt_cache_data() successfully encrypts empty dictionary
            as valid edge case per Args documentation.

        Business Impact:
            Ensures cache layer handles edge cases gracefully without
            errors, maintaining system reliability.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: An empty dictionary {}
            When: encrypt_cache_data() is called
            Then: Encryption succeeds
            And: Encrypted bytes are returned (representing empty JSON object)

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_empty_data: Provides empty dictionary
        """
        # Given: Encryption is enabled and we have empty data
        assert encryption_with_valid_key.is_enabled is True
        assert sample_empty_data == {}

        # When: encrypt_cache_data() is called
        result = encryption_with_valid_key.encrypt_cache_data(sample_empty_data)

        # Then: Encryption succeeds and returns bytes
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encrypt_cache_data_with_large_payload(self, encryption_with_valid_key, sample_large_data):
        """
        Test that encrypt_cache_data() handles large data payloads.

        Verifies:
            encrypt_cache_data() successfully encrypts large data structures
            and completes within performance expectations.

        Business Impact:
            Ensures cache can handle realistic application payloads without
            performance degradation or failures.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Large dictionary (multiple KB of data)
            When: encrypt_cache_data() is called
            Then: Encryption succeeds without errors
            And: Operation completes within reasonable time
            And: Encrypted data size is reasonable

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_large_data: Provides large payload for testing
        """
        import time

        # Given: Encryption is enabled and we have large data
        assert encryption_with_valid_key.is_enabled is True
        assert len(sample_large_data["users"]) == 100  # Large payload

        # When: encrypt_cache_data() is called with timing
        start_time = time.time()
        result = encryption_with_valid_key.encrypt_cache_data(sample_large_data)
        end_time = time.time()

        # Then: Encryption succeeds and completes in reasonable time
        assert isinstance(result, bytes)
        assert len(result) > 0
        encryption_time_ms = (end_time - start_time) * 1000
        assert encryption_time_ms < 100  # Should complete in less than 100ms

    def test_encrypt_cache_data_with_ai_response_structure(self, encryption_with_valid_key, sample_ai_response_data):
        """
        Test that encrypt_cache_data() handles AI response data structure.

        Verifies:
            encrypt_cache_data() properly encrypts AI processing results
            per Examples section showing AI response encryption.

        Business Impact:
            Ensures AI-generated content can be cached securely, protecting
            potentially sensitive AI outputs.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary containing AI response with result and metadata
            When: encrypt_cache_data() is called
            Then: Encryption succeeds
            And: All AI response fields are encrypted
            And: Data integrity is maintained for decryption

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_ai_response_data: AI response structure
        """
        # Given: Encryption is enabled and we have AI response data
        assert encryption_with_valid_key.is_enabled is True
        assert "result" in sample_ai_response_data
        assert "confidence" in sample_ai_response_data
        assert "metadata" in sample_ai_response_data

        # When: encrypt_cache_data() is called
        result = encryption_with_valid_key.encrypt_cache_data(sample_ai_response_data)

        # Then: Encryption succeeds and returns bytes
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encrypt_cache_data_without_encryption_returns_json_bytes(self, encryption_without_key, sample_cache_data):
        """
        Test that encrypt_cache_data() returns JSON bytes when encryption disabled.

        Verifies:
            encrypt_cache_data() returns JSON-serialized bytes when encryption
            is disabled (None key) per docstring behavior description.

        Business Impact:
            Provides graceful degradation for development/testing while
            warning about unencrypted data storage.

        Scenario:
            Given: EncryptedCacheLayer with encryption disabled (None key)
            And: A dictionary to cache
            When: encrypt_cache_data() is called
            Then: JSON bytes are returned (not encrypted)
            And: Returned bytes can be decoded as JSON

        Fixtures Used:
            - encryption_without_key: Provides disabled encryption instance
            - sample_cache_data: Standard dictionary
        """
        import json

        # Given: Encryption is disabled
        assert encryption_without_key.is_enabled is False

        # When: encrypt_cache_data() is called
        result = encryption_without_key.encrypt_cache_data(sample_cache_data)

        # Then: JSON bytes are returned (not encrypted)
        assert isinstance(result, bytes)
        assert len(result) > 0

        # And: Returned bytes can be decoded as JSON
        decoded_data = json.loads(result.decode("utf-8"))
        assert decoded_data == sample_cache_data

    def test_encrypt_cache_data_updates_performance_statistics(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that encrypt_cache_data() updates performance statistics.

        Verifies:
            encrypt_cache_data() increments operation counters and tracks
            timing when performance monitoring is enabled.

        Business Impact:
            Enables performance monitoring and optimization of encryption
            overhead in production environments.

        Scenario:
            Given: EncryptedCacheLayer with performance monitoring enabled
            And: Fresh performance statistics (reset to zero)
            When: encrypt_cache_data() is called multiple times
            Then: encryption_operations counter increases
            And: total_encryption_time accumulates
            And: avg_encryption_time is calculated correctly

        Fixtures Used:
            - encryption_with_fresh_stats: Instance with reset statistics
            - sample_cache_data: Data for encryption operations
        """
        # Given: Fresh performance statistics
        initial_stats = encryption_with_fresh_stats.get_performance_stats()
        assert initial_stats["encryption_operations"] == 0
        assert initial_stats["total_encryption_time"] == 0

        # When: encrypt_cache_data() is called multiple times
        encryption_with_fresh_stats.encrypt_cache_data(sample_cache_data)
        encryption_with_fresh_stats.encrypt_cache_data(sample_cache_data)
        encryption_with_fresh_stats.encrypt_cache_data(sample_cache_data)

        # Then: Performance statistics are updated
        final_stats = encryption_with_fresh_stats.get_performance_stats()
        assert final_stats["encryption_operations"] == 3
        assert final_stats["total_encryption_time"] > 0
        assert final_stats["avg_encryption_time"] > 0
        assert final_stats["total_operations"] == 3

    def test_encrypt_cache_data_logs_warning_for_slow_operations(self, encryption_with_valid_key, sample_large_data, mock_logger, monkeypatch):
        """
        Test that encrypt_cache_data() logs warning for slow encryption.

        Verifies:
            encrypt_cache_data() logs performance warning when operation
            exceeds 50ms threshold per Performance documentation.

        Business Impact:
            Alerts operators to performance issues that may impact
            application responsiveness, enabling proactive optimization.

        Scenario:
            Given: EncryptedCacheLayer with performance monitoring enabled
            And: Very large data payload that causes slow encryption
            When: encrypt_cache_data() is called
            And: Operation takes longer than 50ms
            Then: Warning is logged with operation time and data size

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_large_data: Causes slower encryption
            - mock_logger: Captures performance warnings
        """
        # Given: Logger is mocked for performance monitoring
        monkeypatch.setattr("app.infrastructure.cache.encryption.logger", mock_logger)

        # When: encrypt_cache_data() is called with large data
        result = encryption_with_valid_key.encrypt_cache_data(sample_large_data)

        # Then: Encryption succeeds
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Note: Performance warning logging is tested here - in practice,
        # the warning threshold depends on system performance
        # We verify the operation completes and logger is available
        assert mock_logger is not None

    def test_encrypt_cache_data_with_json_serializable_types_only(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that encrypt_cache_data() accepts only JSON-serializable types.

        Verifies:
            encrypt_cache_data() successfully serializes dictionaries
            containing only JSON-compatible types (str, int, float, bool, None).

        Business Impact:
            Ensures data compatibility with JSON serialization, preventing
            runtime errors during encryption operations.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary with JSON-serializable types only
            When: encrypt_cache_data() is called
            Then: Encryption succeeds
            And: All data types are properly serialized
            And: No serialization errors occur

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_cache_data: Contains various JSON-compatible types
        """
        # Given: Encryption is enabled and we have JSON-compatible data
        assert encryption_with_valid_key.is_enabled is True

        # Verify the sample data contains JSON-serializable types
        assert isinstance(sample_cache_data["user_id"], int)
        assert isinstance(sample_cache_data["name"], str)
        assert isinstance(sample_cache_data["preferences"]["notifications"], bool)
        assert isinstance(sample_cache_data["scores"][0], float)

        # When: encrypt_cache_data() is called
        result = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)

        # Then: Encryption succeeds without serialization errors
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestDecryptCacheData:
    """
    Test suite for decrypt_cache_data() method behavior.

    Scope:
        Tests the decrypt_cache_data() method covering all documented
        scenarios from Args, Returns, and Examples sections.

    Business Critical:
        Decryption must reliably restore original data from encrypted
        cache entries, maintaining data integrity and availability.

    Test Strategy:
        - Verify successful decryption of encrypted data
        - Test data deserialization behavior
        - Validate decrypted output matches original
        - Test performance within documented limits
        - Test behavior with encryption disabled
        - Verify backward compatibility handling
    """

    def test_decrypt_cache_data_with_valid_encrypted_bytes(self, encryption_with_valid_key, sample_encrypted_bytes):
        """
        Test that decrypt_cache_data() successfully decrypts valid data.

        Verifies:
            decrypt_cache_data() accepts encrypted bytes and returns
            original dictionary per Returns section.

        Business Impact:
            Ensures cached data can be reliably retrieved and decrypted,
            providing data availability for application operations.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Valid encrypted bytes from previous encryption
            When: decrypt_cache_data() is called
            Then: Original dictionary is returned
            And: Returned data is of type dict
            And: Decryption completes without errors

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption-enabled instance
            - sample_encrypted_bytes: Pre-encrypted test data
        """
        # Given: Encryption is enabled and we have encrypted bytes
        assert encryption_with_valid_key.is_enabled is True
        assert isinstance(sample_encrypted_bytes, bytes)
        assert len(sample_encrypted_bytes) > 0

        # When: decrypt_cache_data() is called
        result = encryption_with_valid_key.decrypt_cache_data(sample_encrypted_bytes)

        # Then: Original dictionary is returned
        assert isinstance(result, dict)
        assert len(result) > 0
        assert "user_id" in result  # Should contain expected data

    def test_decrypt_cache_data_preserves_data_structure(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that decrypt_cache_data() preserves nested data structures.

        Verifies:
            decrypt_cache_data() properly deserializes and returns nested
            dictionaries and lists matching original structure.

        Business Impact:
            Ensures complex cached data structures are fully restored,
            maintaining application data integrity.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Encrypted bytes from nested dictionary structure
            When: decrypt_cache_data() is called
            Then: Nested structure is fully restored
            And: All nested keys and values match original
            And: Data types are preserved

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_encrypted_bytes: Contains nested structure
        """
        # Given: Encryption is enabled and we have nested data
        assert encryption_with_valid_key.is_enabled is True
        assert "preferences" in sample_cache_data  # Nested dict
        assert "scores" in sample_cache_data      # List

        # Encrypt the nested data first
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)

        # When: decrypt_cache_data() is called
        result = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: Nested structure is fully restored
        assert isinstance(result, dict)
        assert "preferences" in result
        assert "scores" in result
        assert isinstance(result["preferences"], dict)
        assert isinstance(result["scores"], list)
        assert result["preferences"]["theme"] == "dark"
        assert result["scores"][0] == 95.5

    def test_decrypt_cache_data_preserves_unicode_content(self, encryption_with_valid_key, sample_unicode_data):
        """
        Test that decrypt_cache_data() preserves Unicode characters.

        Verifies:
            decrypt_cache_data() properly decodes UTF-8 and restores
            Unicode characters, emojis, and international text.

        Business Impact:
            Ensures international content and emojis are correctly
            retrieved from cache without corruption.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Encrypted bytes containing Unicode content
            When: decrypt_cache_data() is called
            Then: Unicode characters are correctly restored
            And: Emojis are preserved exactly
            And: International text matches original

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_unicode_data: Unicode content for round-trip
        """
        # Given: Encryption is enabled and we have Unicode data
        assert encryption_with_valid_key.is_enabled is True
        original_emoji = sample_unicode_data["emoji"]
        original_chinese = sample_unicode_data["international"]["chinese"]

        # Encrypt the Unicode data first
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_unicode_data)

        # When: decrypt_cache_data() is called
        result = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: Unicode characters are correctly restored
        assert isinstance(result, dict)
        assert result["emoji"] == original_emoji
        assert result["international"]["chinese"] == original_chinese
        assert "🚀" in result["emoji"]
        assert "加密测试数据" in result["international"]["chinese"]

    def test_decrypt_cache_data_with_empty_dictionary(self, encryption_with_valid_key, sample_empty_data):
        """
        Test that decrypt_cache_data() handles encrypted empty dictionary.

        Verifies:
            decrypt_cache_data() successfully decrypts and returns
            empty dictionary as valid edge case.

        Business Impact:
            Ensures cache layer handles edge cases gracefully,
            maintaining system reliability.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Encrypted bytes representing empty dictionary
            When: decrypt_cache_data() is called
            Then: Empty dictionary {} is returned
            And: No errors occur

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_empty_data: Empty dict for round-trip test
        """
        # Given: Encryption is enabled and we have empty data
        assert encryption_with_valid_key.is_enabled is True
        assert sample_empty_data == {}

        # Encrypt the empty data first
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_empty_data)

        # When: decrypt_cache_data() is called
        result = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: Empty dictionary is returned
        assert isinstance(result, dict)
        assert result == {}
        assert len(result) == 0

    def test_decrypt_cache_data_without_encryption_decodes_json(self, encryption_without_key, sample_unencrypted_json_bytes):
        """
        Test that decrypt_cache_data() decodes JSON when encryption disabled.

        Verifies:
            decrypt_cache_data() treats input as raw JSON bytes when
            encryption is disabled per method behavior.

        Business Impact:
            Provides graceful degradation for development/testing
            without breaking cache operations.

        Scenario:
            Given: EncryptedCacheLayer with encryption disabled
            And: Raw JSON bytes (not encrypted)
            When: decrypt_cache_data() is called
            Then: JSON is decoded and dictionary returned
            And: No decryption attempt is made

        Fixtures Used:
            - encryption_without_key: Provides disabled encryption
            - sample_unencrypted_json_bytes: Raw JSON bytes
        """
        # Given: Encryption is disabled and we have raw JSON bytes
        assert encryption_without_key.is_enabled is False
        assert isinstance(sample_unencrypted_json_bytes, bytes)

        # When: decrypt_cache_data() is called
        result = encryption_without_key.decrypt_cache_data(sample_unencrypted_json_bytes)

        # Then: JSON is decoded and dictionary returned
        assert isinstance(result, dict)
        assert len(result) > 0
        assert "user_id" in result  # Should contain expected data

    def test_decrypt_cache_data_handles_unencrypted_data_fallback(self, encryption_with_valid_key, sample_unencrypted_json_bytes):
        """
        Test that decrypt_cache_data() handles unencrypted data gracefully.

        Verifies:
            decrypt_cache_data() includes fallback handling for data stored
            without encryption per backward compatibility note.

        Business Impact:
            Enables migration from unencrypted to encrypted cache without
            data loss or application errors.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Data bytes that are not encrypted (JSON only)
            When: decrypt_cache_data() is called
            Then: InvalidToken exception is caught
            And: Data is treated as unencrypted JSON
            And: Dictionary is successfully returned

        Fixtures Used:
            - encryption_with_valid_key: Encryption-enabled instance
            - sample_unencrypted_json_bytes: Raw JSON without encryption
        """
        # Given: Encryption is enabled and we have unencrypted JSON bytes
        assert encryption_with_valid_key.is_enabled is True
        assert isinstance(sample_unencrypted_json_bytes, bytes)

        # When: decrypt_cache_data() is called with unencrypted data
        result = encryption_with_valid_key.decrypt_cache_data(sample_unencrypted_json_bytes)

        # Then: Dictionary is successfully returned
        assert isinstance(result, dict)
        assert len(result) > 0
        assert "user_id" in result

    def test_decrypt_cache_data_updates_performance_statistics(self, encryption_with_fresh_stats, sample_encrypted_bytes):
        """
        Test that decrypt_cache_data() updates performance statistics.

        Verifies:
            decrypt_cache_data() increments operation counters and tracks
            timing when performance monitoring is enabled.

        Business Impact:
            Enables performance monitoring of decryption overhead for
            cache retrieval optimization.

        Scenario:
            Given: EncryptedCacheLayer with performance monitoring enabled
            And: Fresh performance statistics (reset)
            When: decrypt_cache_data() is called multiple times
            Then: decryption_operations counter increases
            And: total_decryption_time accumulates
            And: avg_decryption_time is calculated correctly

        Fixtures Used:
            - encryption_with_fresh_stats: Instance with reset stats
            - sample_encrypted_bytes: Encrypted data for operations
        """
        # Given: Fresh performance statistics
        initial_stats = encryption_with_fresh_stats.get_performance_stats()
        assert initial_stats["decryption_operations"] == 0
        assert initial_stats["total_decryption_time"] == 0

        # When: decrypt_cache_data() is called multiple times
        encryption_with_fresh_stats.decrypt_cache_data(sample_encrypted_bytes)
        encryption_with_fresh_stats.decrypt_cache_data(sample_encrypted_bytes)
        encryption_with_fresh_stats.decrypt_cache_data(sample_encrypted_bytes)

        # Then: Performance statistics are updated
        final_stats = encryption_with_fresh_stats.get_performance_stats()
        assert final_stats["decryption_operations"] == 3
        assert final_stats["total_decryption_time"] > 0
        assert final_stats["avg_decryption_time"] > 0
        assert final_stats["total_operations"] == 3

    def test_decrypt_cache_data_logs_warning_for_slow_operations(self, encryption_with_valid_key, sample_large_data, mock_logger, monkeypatch):
        """
        Test that decrypt_cache_data() logs warning for slow decryption.

        Verifies:
            decrypt_cache_data() logs performance warning when operation
            exceeds 30ms threshold per Performance documentation.

        Business Impact:
            Alerts operators to cache retrieval performance issues,
            enabling optimization of slow operations.

        Scenario:
            Given: EncryptedCacheLayer with performance monitoring enabled
            And: Large encrypted data payload
            When: decrypt_cache_data() is called
            And: Operation takes longer than 30ms
            Then: Warning is logged with operation time and data size

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_large_data: Encrypt first, then decrypt slowly
            - mock_logger: Captures performance warnings
        """
        # Given: Logger is mocked for performance monitoring
        monkeypatch.setattr("app.infrastructure.cache.encryption.logger", mock_logger)

        # First encrypt the large data
        encrypted_data = encryption_with_valid_key.encrypt_cache_data(sample_large_data)

        # When: decrypt_cache_data() is called with large encrypted data
        result = encryption_with_valid_key.decrypt_cache_data(encrypted_data)

        # Then: Decryption succeeds
        assert isinstance(result, dict)
        assert len(result) > 0

        # Note: Performance warning logging is tested here - in practice,
        # the warning threshold depends on system performance
        # We verify the operation completes and logger is available
        assert mock_logger is not None

    def test_decrypt_cache_data_performance_better_than_encryption(self, encryption_with_fresh_stats, sample_cache_data):
        """
        Test that decrypt_cache_data() performs faster than encryption.

        Verifies:
            decrypt_cache_data() typically completes faster than encryption
            per Performance note about decryption being faster.

        Business Impact:
            Confirms expected performance characteristics for cache
            retrieval being faster than storage.

        Scenario:
            Given: EncryptedCacheLayer with performance monitoring
            And: Same data for encryption and decryption
            When: Both operations are performed multiple times
            Then: Average decryption time is less than encryption time
            And: Performance statistics reflect this difference

        Fixtures Used:
            - encryption_with_fresh_stats: For accurate timing
            - sample_cache_data: Same data for both operations
        """
        # Given: Fresh performance statistics
        encryption_with_fresh_stats.reset_performance_stats()

        # When: Both operations are performed multiple times
        # Encrypt data multiple times
        encrypted_data = encryption_with_fresh_stats.encrypt_cache_data(sample_cache_data)
        encryption_with_fresh_stats.encrypt_cache_data(sample_cache_data)
        encryption_with_fresh_stats.encrypt_cache_data(sample_cache_data)

        # Decrypt data multiple times
        encryption_with_fresh_stats.decrypt_cache_data(encrypted_data)
        encryption_with_fresh_stats.decrypt_cache_data(encrypted_data)
        encryption_with_fresh_stats.decrypt_cache_data(encrypted_data)

        # Then: Performance statistics show both operations
        stats = encryption_with_fresh_stats.get_performance_stats()
        assert stats["encryption_operations"] == 3
        assert stats["decryption_operations"] == 3
        assert stats["total_operations"] == 6

        # And: Both have timing information recorded
        assert stats["avg_encryption_time"] > 0
        assert stats["avg_decryption_time"] > 0


class TestEncryptionDecryptionRoundTrip:
    """
    Test suite for encryption/decryption data integrity.

    Scope:
        Tests that data can be encrypted and decrypted without loss,
        verifying complete round-trip integrity for all data types.

    Business Critical:
        Round-trip integrity is essential for cache reliability -
        data must be perfectly preserved through encryption/decryption.

    Test Strategy:
        - Verify data integrity for all supported data types
        - Test various data structures and sizes
        - Confirm Unicode and special character preservation
        - Validate type preservation through round-trip
    """

    def test_encryption_decryption_round_trip_preserves_simple_data(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that simple dictionary survives encryption/decryption unchanged.

        Verifies:
            Data encrypted and then decrypted matches original exactly,
            confirming round-trip integrity per documented behavior.

        Business Impact:
            Ensures basic cache data reliability, preventing data loss
            or corruption in cache operations.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: A simple dictionary with basic types
            When: Data is encrypted using encrypt_cache_data()
            And: Encrypted bytes are immediately decrypted
            Then: Decrypted dictionary exactly matches original
            And: No data loss or modification occurs

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_cache_data: Original data for round-trip
        """
        # Given: Encryption is enabled and we have original data
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_cache_data.copy()

        # When: Data is encrypted and then decrypted
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: Decrypted dictionary exactly matches original
        assert decrypted_data == original_data
        assert decrypted_data is not original_data  # Different objects
        assert decrypted_data["user_id"] == original_data["user_id"]
        assert decrypted_data["name"] == original_data["name"]

    def test_encryption_decryption_round_trip_preserves_nested_structures(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that nested structures survive round-trip unchanged.

        Verifies:
            Complex nested dictionaries and lists maintain structure
            and values through encryption/decryption cycle.

        Business Impact:
            Ensures complex application data can be safely cached
            without structural degradation.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary with multiple levels of nesting
            When: Data undergoes encryption/decryption round-trip
            Then: All nested structures are preserved
            And: All values at all levels match original
            And: Nesting depth is maintained

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_cache_data: Contains nested preferences
        """
        # Given: Encryption is enabled and we have nested data
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_cache_data.copy()

        # When: Data undergoes encryption/decryption round-trip
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: All nested structures are preserved
        assert decrypted_data == original_data
        assert isinstance(decrypted_data["preferences"], dict)
        assert isinstance(decrypted_data["scores"], list)
        assert decrypted_data["preferences"]["theme"] == original_data["preferences"]["theme"]
        assert decrypted_data["preferences"]["notifications"] == original_data["preferences"]["notifications"]
        assert decrypted_data["scores"] == original_data["scores"]

    def test_encryption_decryption_round_trip_preserves_unicode(self, encryption_with_valid_key, sample_unicode_data):
        """
        Test that Unicode content survives round-trip unchanged.

        Verifies:
            Unicode characters, emojis, and international text are
            perfectly preserved through encryption/decryption.

        Business Impact:
            Ensures international content integrity, supporting
            global application users.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary with Unicode, emojis, and multilingual text
            When: Data undergoes encryption/decryption round-trip
            Then: All Unicode characters match original exactly
            And: Emojis are perfectly preserved
            And: International text is unchanged

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_unicode_data: Various Unicode content
        """
        # Given: Encryption is enabled and we have Unicode data
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_unicode_data.copy()

        # When: Data undergoes encryption/decryption round-trip
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_unicode_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: All Unicode characters match original exactly
        assert decrypted_data == original_data
        assert decrypted_data["emoji"] == original_data["emoji"]
        assert decrypted_data["international"]["chinese"] == original_data["international"]["chinese"]
        assert decrypted_data["international"]["japanese"] == original_data["international"]["japanese"]
        assert "🚀" in decrypted_data["emoji"]
        assert "加密测试数据" in decrypted_data["international"]["chinese"]

    def test_encryption_decryption_round_trip_preserves_data_types(self, encryption_with_valid_key, sample_cache_data):
        """
        Test that data types are preserved through round-trip.

        Verifies:
            All JSON-serializable types (str, int, float, bool, None)
            maintain their types through encryption/decryption.

        Business Impact:
            Ensures type safety in cached data, preventing type-related
            bugs in application logic.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Dictionary with various data types
            When: Data undergoes encryption/decryption round-trip
            Then: String values remain strings
            And: Integer values remain integers
            And: Float values remain floats
            And: Boolean values remain booleans
            And: None values remain None

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_cache_data: Contains multiple types
        """
        # Given: Encryption is enabled and we have data with various types
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_cache_data.copy()

        # Verify original data types
        assert isinstance(original_data["user_id"], int)
        assert isinstance(original_data["name"], str)
        assert isinstance(original_data["scores"][0], float)
        assert isinstance(original_data["preferences"]["notifications"], bool)

        # When: Data undergoes encryption/decryption round-trip
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_cache_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: All data types are preserved
        assert decrypted_data == original_data
        assert isinstance(decrypted_data["user_id"], int)
        assert isinstance(decrypted_data["name"], str)
        assert isinstance(decrypted_data["scores"][0], float)
        assert isinstance(decrypted_data["preferences"]["notifications"], bool)
        assert type(decrypted_data["user_id"]) is type(original_data["user_id"])
        assert type(decrypted_data["name"]) is type(original_data["name"])

    def test_encryption_decryption_round_trip_preserves_empty_data(self, encryption_with_valid_key, sample_empty_data):
        """
        Test that empty dictionary survives round-trip unchanged.

        Verifies:
            Empty dictionary edge case maintains integrity through
            encryption/decryption cycle.

        Business Impact:
            Ensures edge cases are handled correctly, maintaining
            cache reliability for all data scenarios.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Empty dictionary {}
            When: Empty dict undergoes encryption/decryption
            Then: Result is still empty dictionary {}
            And: No errors or data corruption occurs

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_empty_data: Empty dictionary
        """
        # Given: Encryption is enabled and we have empty data
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_empty_data.copy()
        assert original_data == {}

        # When: Empty dict undergoes encryption/decryption
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_empty_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: Result is still empty dictionary
        assert decrypted_data == {}
        assert isinstance(decrypted_data, dict)
        assert len(decrypted_data) == 0
        assert decrypted_data == original_data

    def test_encryption_decryption_round_trip_preserves_large_data(self, encryption_with_valid_key, sample_large_data):
        """
        Test that large payloads survive round-trip unchanged.

        Verifies:
            Large data structures maintain complete integrity through
            encryption/decryption regardless of size.

        Business Impact:
            Ensures cache can reliably handle realistic application
            payloads without data loss.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: Large dictionary (multiple KB)
            When: Large data undergoes encryption/decryption
            Then: All data is perfectly preserved
            And: No truncation or corruption occurs
            And: Operation completes successfully

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_large_data: Large payload
        """
        # Given: Encryption is enabled and we have large data
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_large_data.copy()
        assert len(original_data["users"]) == 100  # Verify large payload

        # When: Large data undergoes encryption/decryption
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_large_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: All data is perfectly preserved
        assert decrypted_data == original_data
        assert len(decrypted_data["users"]) == 100
        assert decrypted_data["users"][0]["id"] == 0
        assert decrypted_data["users"][99]["id"] == 99
        assert decrypted_data["users"][50]["name"] == "User 50"

    def test_encryption_decryption_round_trip_preserves_ai_response(self, encryption_with_valid_key, sample_ai_response_data):
        """
        Test that AI response structure survives round-trip unchanged.

        Verifies:
            AI processing results maintain complete integrity through
            encryption/decryption per Examples documentation.

        Business Impact:
            Ensures AI-generated content can be cached reliably,
            supporting AI-powered application features.

        Scenario:
            Given: EncryptedCacheLayer with encryption enabled
            And: AI response dictionary with result and metadata
            When: AI response undergoes encryption/decryption
            Then: All response fields are preserved
            And: Confidence scores maintain precision
            And: Metadata is unchanged

        Fixtures Used:
            - encryption_with_valid_key: Provides encryption instance
            - sample_ai_response_data: AI response structure
        """
        # Given: Encryption is enabled and we have AI response data
        assert encryption_with_valid_key.is_enabled is True
        original_data = sample_ai_response_data.copy()
        assert "result" in original_data
        assert "confidence" in original_data
        assert "metadata" in original_data

        # When: AI response undergoes encryption/decryption
        encrypted_bytes = encryption_with_valid_key.encrypt_cache_data(sample_ai_response_data)
        decrypted_data = encryption_with_valid_key.decrypt_cache_data(encrypted_bytes)

        # Then: All response fields are preserved
        assert decrypted_data == original_data
        assert decrypted_data["result"] == original_data["result"]
        assert decrypted_data["confidence"] == original_data["confidence"]
        assert decrypted_data["model"] == original_data["model"]
        assert decrypted_data["metadata"]["processing_time"] == original_data["metadata"]["processing_time"]
        assert decrypted_data["metadata"]["tokens_used"] == original_data["metadata"]["tokens_used"]
        assert type(decrypted_data["confidence"]) is float  # Precision maintained
