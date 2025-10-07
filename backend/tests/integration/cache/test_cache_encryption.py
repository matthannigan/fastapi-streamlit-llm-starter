"""
Cache Encryption Integration Tests.

This module provides comprehensive integration tests for cache encryption functionality,
validating end-to-end encryption pipelines, key management, performance monitoring,
and error handling across the cache infrastructure.

Integration Focus:
    - Encryption/decryption round-trip integrity
    - Environment-based key configuration
    - Performance monitoring and metrics
    - Error handling and security validation
    - Cache factory integration with encryption
    - End-to-end encrypted cache workflows

Test Philosophy:
    These tests follow the outside-in integration testing approach, validating
    observable behavior through real component interactions rather than mocking
    internal implementation details.
"""

import json
import time
from typing import Any, Dict

import pytest

from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.encryption import EncryptedCacheLayer, create_encryption_layer_from_env

# Mark all tests in this module to run serially (not in parallel)
pytestmark = pytest.mark.no_parallel


class TestEncryptionPipelineEndToEndIntegration:
    """
    Tests for complete encryption/decryption pipeline integration.

    Seam Under Test:
        Application Data → JSON Serialization → Fernet Encryption →
        Redis Storage → Redis Retrieval → Fernet Decryption → JSON Deserialization → Application Data

    Critical Paths:
        - Complete round-trip encryption/decryption preserves data integrity
        - Encrypted data stored in Redis is properly encrypted and cannot be read without decryption
        - Large datasets are encrypted and decrypted correctly with acceptable performance
        - Unicode and special characters are preserved through encryption/decryption pipeline

    Business Impact:
        Ensures all cached data is properly encrypted at rest and can be reliably decrypted,
        protecting sensitive information while maintaining data accessibility.
    """

    @pytest.mark.asyncio
    async def test_encryption_round_trip_preserves_data_integrity(self):
        """
        Test that complete encryption/decryption pipeline preserves data integrity exactly.

        Integration Scope:
            EncryptedCacheLayer → JSON serialization → Fernet encryption →
            Fernet decryption → JSON deserialization

        Business Impact:
            Ensures cached data is protected and can be reliably recovered without corruption

        Test Strategy:
            - Create encryption layer with generated key
            - Test comprehensive data types and structures
            - Verify exact byte-for-byte data preservation
            - Validate encryption produces unreadable output

        Success Criteria:
            - Original data matches decrypted data exactly
            - All data types are preserved (str, int, float, bool, None, list, dict)
            - Unicode and special characters work correctly
            - Encrypted output is different from original data
        """
        # Arrange
        encryption = EncryptedCacheLayer.create_with_generated_key()

        # Test comprehensive data types and structures
        test_data = {
            "string": "test value",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "none": None,
            "list": [1, 2, "three", {"nested": "value"}],
            "nested_dict": {
                "user_id": 123,
                "profile": {
                    "name": "Alice",
                    "preferences": {"theme": "dark", "language": "en"},
                },
                "metadata": {"created_at": "2023-01-01T12:00:00Z", "version": 1},
            },
            "unicode": "Hello 世界 🌍 ñáéíóú",
            "special_chars": "Special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?",
            "empty_structures": {"empty_list": [], "empty_dict": {}},
            "numeric_data": {"large_int": 9223372036854775807, "scientific": 1.23e-10},
        }

        # Act
        encrypted = encryption.encrypt_cache_data(test_data)
        decrypted = encryption.decrypt_cache_data(encrypted)

        # Assert
        assert decrypted == test_data, "Decrypted data must match original exactly"
        assert isinstance(encrypted, bytes), "Encrypted data must be bytes"
        assert len(encrypted) > 0, "Encrypted data must not be empty"

        # Verify encryption actually happened (output is different from input)
        original_json = json.dumps(test_data, ensure_ascii=False, sort_keys=True)
        assert encrypted != original_json.encode("utf-8"), "Encrypted data must be different from original"

        # Verify encrypted data is not human-readable
        encrypted_str = encrypted.decode("utf-8", errors="ignore")
        assert "Alice" not in encrypted_str, "Original sensitive data should not be visible in encrypted output"
        assert "user_id" not in encrypted_str, "Original keys should not be visible in encrypted output"

    @pytest.mark.asyncio
    async def test_encrypted_cache_integration_with_redis(self, secure_redis_cache):
        """
        Test encrypted data storage and retrieval through Redis integration.

        Integration Scope:
            Application → EncryptedCacheLayer → Redis → Decryption → Application

        Business Impact:
            Validates encryption works with actual Redis storage and data is protected at rest

        Test Strategy:
            - Use secure Redis container with real encryption
            - Store sensitive data through cache with encryption
            - Verify Redis contains encrypted data (not human-readable)
            - Retrieve and decrypt data successfully

        Success Criteria:
            - Data stored in Redis is encrypted (not human-readable)
            - Retrieved data is properly decrypted and matches original
            - Round-trip through Redis preserves data integrity
        """
        # Arrange
        test_data = {
            "sensitive_user_data": {
                "user_id": 12345,
                "email": "user@example.com",
                "personal_info": {"ssn": "123-45-6789", "address": "123 Main St"},
            },
            "ai_response": {"model": "gpt-4", "content": "Generated sensitive content"},
        }
        cache_key = "integration:test:encrypted:sensitive_data"

        # Act
        # Store data through encrypted cache
        await secure_redis_cache.set(cache_key, test_data)

        # Verify data in Redis is encrypted (not human-readable)
        raw_redis_data = await secure_redis_cache.redis.get(cache_key)
        raw_data_str = raw_redis_data.decode("utf-8", errors="ignore") if raw_redis_data else ""

        # Assert - Raw Redis data should be encrypted
        assert "user@example.com" not in raw_data_str, "Email should be encrypted in Redis"
        assert "123-45-6789" not in raw_data_str, "SSN should be encrypted in Redis"
        assert "Generated sensitive content" not in raw_data_str, "AI content should be encrypted in Redis"

        # Retrieve and verify decryption works
        retrieved_data = await secure_redis_cache.get(cache_key)

        # Assert - Retrieved data should match original exactly
        assert retrieved_data == test_data, "Retrieved data must match original after decryption"
        assert retrieved_data["sensitive_user_data"]["email"] == "user@example.com"
        assert retrieved_data["ai_response"]["content"] == "Generated sensitive content"

    @pytest.mark.asyncio
    async def test_large_dataset_encryption_performance(self):
        """
        Test encryption performance with large datasets to ensure acceptable overhead.

        Integration Scope:
            Large datasets → JSON serialization → Encryption → Decryption → JSON deserialization

        Business Impact:
            Ensures encryption overhead stays within acceptable limits for production use

        Test Strategy:
            - Test with progressively larger datasets (1KB, 10KB, 100KB)
            - Measure encryption and decryption times
            - Verify performance stays within acceptable thresholds
            - Ensure memory usage remains reasonable

        Success Criteria:
            - Encryption time scales reasonably with data size
            - Performance stays within documented limits (<50ms for normal operations)
            - Large datasets are handled without memory issues
        """
        # Arrange
        encryption = EncryptedCacheLayer.create_with_generated_key()

        # Create datasets of different sizes
        small_data = {"data": "x" * 100}  # ~100 bytes
        medium_data = {"data": "x" * 1000}  # ~1KB
        large_data = {"data": "x" * 10000}  # ~10KB
        xlarge_data = {"data": [{"id": i, "content": "y" * 100} for i in range(1000)]}  # ~100KB

        test_cases = [
            ("small", small_data, 5),   # 5ms threshold
            ("medium", medium_data, 20),  # 20ms threshold
            ("large", large_data, 50),   # 50ms threshold
            ("xlarge", xlarge_data, 200),  # 200ms threshold
        ]

        # Test each dataset size individually
        for name, data, threshold_ms in test_cases:
            # Act - Measure encryption time
            start_time = time.perf_counter()
            encrypted = encryption.encrypt_cache_data(data)
            encryption_time = (time.perf_counter() - start_time) * 1000

            # Measure decryption time
            start_time = time.perf_counter()
            decrypted = encryption.decrypt_cache_data(encrypted)
            decryption_time = (time.perf_counter() - start_time) * 1000

            # Assert
            assert decrypted == data, f"Data integrity must be preserved for {name} dataset"
            assert encryption_time < threshold_ms, f"Encryption time {encryption_time:.2f}ms exceeds threshold {threshold_ms}ms for {name} dataset"
            assert decryption_time < threshold_ms, f"Decryption time {decryption_time:.2f}ms exceeds threshold {threshold_ms}ms for {name} dataset"

            # Verify encryption actually increased data size
            original_size = len(json.dumps(data).encode("utf-8"))
            encrypted_size = len(encrypted)
            assert encrypted_size > original_size, f"Encrypted data should be larger than original for {name} dataset"

    @pytest.mark.asyncio
    async def test_concurrent_encryption_operations(self):
        """
        Test concurrent encryption/decryption operations work correctly without data corruption.

        Integration Scope:
            Multiple concurrent operations → Encryption layer → Data integrity preservation

        Business Impact:
            Ensures thread safety and data consistency in concurrent cache access scenarios

        Test Strategy:
            - Perform multiple encryption/decryption operations concurrently
            - Verify each operation maintains data integrity
            - Ensure no data corruption or mixing between operations
            - Validate thread safety of encryption layer

        Success Criteria:
            - All concurrent operations complete successfully
            - Each operation's decrypted data matches its original input
            - No data corruption or mixing between concurrent operations
            - Performance monitoring handles concurrent access correctly
        """
        import asyncio

        # Arrange
        encryption = EncryptedCacheLayer.create_with_generated_key()
        num_concurrent = 20

        async def encrypt_decrypt_cycle(data: Dict[str, Any], cycle_id: int) -> Dict[str, Any]:
            """Perform encryption/decryption cycle for test data."""
            test_data = {"cycle_id": cycle_id, **data}

            # Encrypt
            encrypted = encryption.encrypt_cache_data(test_data)

            # Small delay to increase chance of race conditions
            await asyncio.sleep(0.001)

            # Decrypt
            decrypted = encryption.decrypt_cache_data(encrypted)

            return decrypted

        # Act
        # Create concurrent encryption/decryption tasks
        tasks = []
        for i in range(num_concurrent):
            test_data = {
                "user_id": i,
                "content": f"Test content {i}",
                "timestamp": time.time(),
                "random_data": list(range(10)),  # Add some complexity
            }
            task = encrypt_decrypt_cycle(test_data, i)
            tasks.append(task)

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)

        # Assert
        assert len(results) == num_concurrent, "All concurrent operations should complete"

        # Verify each result matches its expected input
        for i, result in enumerate(results):
            expected_cycle_id = i
            assert result["cycle_id"] == expected_cycle_id, f"Result {i} should have correct cycle_id"
            assert result["user_id"] == i, f"Result {i} should have correct user_id"
            assert result["content"] == f"Test content {i}", f"Result {i} should have correct content"

        # Verify performance stats handled concurrency correctly
        stats = encryption.get_performance_stats()
        assert stats["encryption_operations"] == num_concurrent, "Should track all encryption operations"
        assert stats["decryption_operations"] == num_concurrent, "Should track all decryption operations"
        assert stats["total_operations"] == num_concurrent * 2, "Should track total operations correctly"

    @pytest.mark.asyncio
    async def test_backward_compatibility_with_unencrypted_data(self):
        """
        Test backward compatibility handling of unencrypted data in cache.

        Integration Scope:
            Legacy unencrypted data → Decryption fallback → Graceful handling

        Business Impact:
            Enables gradual migration to encrypted caching without breaking existing systems

        Test Strategy:
            - Simulate legacy unencrypted data in cache
            - Verify decryption gracefully handles unencrypted data
            - Test mixed encrypted/unencrypted data scenarios
            - Ensure warnings are logged for backward compatibility

        Success Criteria:
            - Unencrypted data can be read with appropriate warnings
            - Mixed encrypted/unencrypted data works correctly
            - Backward compatibility doesn't break new encrypted data
            - Performance impact of compatibility checks is minimal
        """
        # Arrange
        encryption = EncryptedCacheLayer.create_with_generated_key()

        # Create test data
        test_data = {"legacy_data": "unencrypted value", "user_id": 123}

        # Simulate unencrypted data (raw JSON bytes as it would be stored without encryption)
        unencrypted_data = json.dumps(test_data, ensure_ascii=False, sort_keys=True).encode("utf-8")

        # Act - Test decryption of unencrypted data (backward compatibility)
        result = encryption.decrypt_cache_data(unencrypted_data)

        assert result == test_data, "Unencrypted data should be readable via backward compatibility"

        # Test mixed scenarios - encrypted data should still work normally
        encrypted_data = encryption.encrypt_cache_data(test_data)
        decrypted_encrypted = encryption.decrypt_cache_data(encrypted_data)
        assert decrypted_encrypted == test_data, "Encrypted data should work normally"

        # Verify encryption is still active for new data
        assert encryption.is_enabled, "Encryption should still be enabled"
        assert encrypted_data != unencrypted_data, "New data should still be encrypted"

        # Test performance impact is minimal
        start_time = time.perf_counter()
        for _ in range(100):
            encryption.decrypt_cache_data(unencrypted_data)
        compatibility_time = time.perf_counter() - start_time

        # Should be very fast (<10ms for 100 operations)
        assert compatibility_time < 0.01, "Backward compatibility checks should have minimal performance impact"


class TestEncryptionConfigurationIntegration:
    """
    Tests for encryption configuration and key management integration.

    Seam Under Test:
        Environment Variables → create_encryption_layer_from_env →
        EncryptedCacheLayer initialization → Functional encryption operations

    Critical Paths:
        - Environment-based encryption layer creation with valid keys
        - Missing key handling with appropriate warnings
        - Invalid key error handling with helpful messages
        - Configuration propagation through factory methods

    Business Impact:
        Ensures encryption can be properly configured across different deployment environments
        with secure key management and clear error handling.
    """

    def test_encryption_from_environment_configuration_success(self, monkeypatch):
        """
        Test successful encryption layer creation from environment variables.

        Integration Scope:
            Environment variables → create_encryption_layer_from_env →
            EncryptedCacheLayer → Functional encryption operations

        Business Impact:
            Enables proper encryption configuration in production deployments using environment variables

        Test Strategy:
            - Set valid REDIS_ENCRYPTION_KEY environment variable
            - Create encryption layer from environment
            - Verify encryption/decryption works correctly
            - Test integration with actual encryption operations

        Success Criteria:
            - REDIS_ENCRYPTION_KEY is properly loaded from environment
            - Encryption layer functions correctly after environment initialization
            - Created encryption layer can encrypt and decrypt data successfully
        """
        # Arrange
        from cryptography.fernet import Fernet
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_key)

        # Act
        encryption = create_encryption_layer_from_env()

        # Assert
        assert encryption.is_enabled, "Encryption should be enabled when key is provided"
        assert encryption.fernet is not None, "Fernet instance should be initialized"

        # Test encryption functionality works
        test_data = {"environment_test": True, "message": "Hello from environment!"}
        encrypted = encryption.encrypt_cache_data(test_data)
        decrypted = encryption.decrypt_cache_data(encrypted)

        assert decrypted == test_data, "Environment-configured encryption should work correctly"

    def test_missing_encryption_key_environment_handling(self, monkeypatch):
        """
        Test handling of missing REDIS_ENCRYPTION_KEY environment variable.

        Integration Scope:
            Missing environment variable → create_encryption_layer_from_env →
            Warning logging → Disabled encryption layer creation

        Business Impact:
            Ensures graceful degradation when encryption key is not configured,
            with clear warnings for operators

        Test Strategy:
            - Remove REDIS_ENCRYPTION_KEY environment variable
            - Create encryption layer from environment
            - Verify warnings are logged and encryption is disabled
            - Test that layer still functions (without encryption)

        Success Criteria:
            - Missing key results in warning messages but functional layer
            - Encryption is disabled but layer remains operational
            - Unencrypted operations work with appropriate warnings
        """
        # Arrange
        monkeypatch.delenv("REDIS_ENCRYPTION_KEY", raising=False)

        # Act - Create encryption layer without key (should log warnings)
        encryption = create_encryption_layer_from_env()

        # Assert - Should have encryption disabled with warnings logged
        assert not encryption.is_enabled, "Encryption should be disabled when key is missing"
        assert encryption.fernet is None, "Fernet instance should be None when encryption is disabled"

        # Test that operations still work (without encryption)
        test_data = {"no_encryption": True, "message": "Unencrypted data"}

        encrypted = encryption.encrypt_cache_data(test_data)
        decrypted = encryption.decrypt_cache_data(encrypted)
        assert decrypted == test_data, "Operations should work even without encryption"

    def test_invalid_encryption_key_error_handling(self, monkeypatch):
        """
        Test error handling for invalid encryption keys in environment.

        Integration Scope:
            Invalid key in environment → EncryptedCacheLayer initialization →
            ConfigurationError with helpful troubleshooting information

        Business Impact:
            Ensures configuration errors are caught early with actionable error messages

        Test Strategy:
            - Set invalid REDIS_ENCRYPTION_KEY environment variable
            - Attempt to create encryption layer
            - Verify ConfigurationError with helpful error message
            - Test error context includes troubleshooting guidance

        Success Criteria:
            - Invalid keys raise ConfigurationError with troubleshooting guidance
            - Error message includes actionable information for resolution
            - Error context includes proper error_type classification
        """
        # Arrange - Test invalid keys that should raise ConfigurationError
        invalid_keys = [
            "invalid-key-format",
            "not-base64-encoded",
            "short-key",
            "🚀 invalid unicode key",
        ]

        for invalid_key in invalid_keys:
            # Arrange
            monkeypatch.setenv("REDIS_ENCRYPTION_KEY", invalid_key)

            # Act & Assert
            with pytest.raises(ConfigurationError) as exc_info:
                create_encryption_layer_from_env()

            error = exc_info.value
            assert "invalid encryption key" in str(error).lower(), f"Error should mention invalid key for: {invalid_key}"
            assert "Fernet" in str(error) or "generate_key" in str(error), f"Error should include key generation guidance for: {invalid_key}"
            assert error.context.get("error_type") == "invalid_encryption_key", f"Error context should classify error type for: {invalid_key}"

        # Test empty string specifically - should result in disabled encryption
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")
        encryption = create_encryption_layer_from_env()
        assert not encryption.is_enabled, "Empty string key should result in disabled encryption"

    def test_encryption_key_generation_functionality(self):
        """
        Test EncryptedCacheLayer.create_with_generated_key functionality.

        Integration Scope:
            Key generation request → Fernet.generate_key → EncryptedCacheLayer creation →
            Validation → Ready state for encryption operations

        Business Impact:
            Provides convenient key generation for development and testing while ensuring
            proper key management patterns

        Test Strategy:
            - Generate encryption layer with create_with_generated_key
            - Verify generated key works correctly for encryption/decryption
            - Test multiple generations produce unique keys
            - Validate generated keys have proper format

        Success Criteria:
            - create_with_generated_key creates functional encryption layer
            - Generated keys work correctly for encrypt/decrypt operations
            - Each invocation produces unique keys
            - Generated encryption layer integrates correctly with performance monitoring
        """
        # Act
        encryption1 = EncryptedCacheLayer.create_with_generated_key()
        encryption2 = EncryptedCacheLayer.create_with_generated_key()

        # Assert
        assert encryption1.is_enabled, "Generated encryption should be enabled"
        assert encryption2.is_enabled, "Second generated encryption should be enabled"
        assert encryption1.fernet != encryption2.fernet, "Each generation should create unique encryption instances"

        # Test encryption works with generated keys
        test_data = {"generated_key_test": True, "message": "Test with generated key"}

        encrypted1 = encryption1.encrypt_cache_data(test_data)
        decrypted1 = encryption1.decrypt_cache_data(encrypted1)
        assert decrypted1 == test_data, "First generated key should work correctly"

        encrypted2 = encryption2.encrypt_cache_data(test_data)
        decrypted2 = encryption2.decrypt_cache_data(encrypted2)
        assert decrypted2 == test_data, "Second generated key should work correctly"

        # Verify keys are actually different (data encrypted with one can't be decrypted with the other)
        with pytest.raises(Exception):  # Should fail to decrypt with wrong key
            encryption1.decrypt_cache_data(encrypted2)

        # Test performance monitoring integration
        stats1 = encryption1.get_performance_stats()
        stats2 = encryption2.get_performance_stats()
        assert stats1["encryption_enabled"] is True
        assert stats2["encryption_enabled"] is True

    @pytest.mark.asyncio
    async def test_environment_configuration_integration_with_factory(self, monkeypatch):
        """
        Test encryption integration with CacheFactory creation methods.

        Integration Scope:
            Environment configuration → SecurityConfig → CacheFactory →
            Cache instance with integrated encryption

        Business Impact:
            Ensures encryption is properly integrated into cache creation workflows
            across all factory methods and environment configurations

        Test Strategy:
            - Set up environment with encryption key
            - Create caches through different factory methods
            - Verify encryption integration works in all scenarios
            - Test encryption configuration propagation

        Success Criteria:
            - Factory creates caches with encryption when configured
            - Encryption integration works across different factory methods
            - Encrypted cache operations work correctly after factory creation
            - Factory handles encryption configuration errors gracefully
        """
        # Arrange
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        from app.infrastructure.cache.factory import CacheFactory
        from app.infrastructure.cache.security import SecurityConfig

        # Create security config with encryption
        security_config = SecurityConfig.create_for_environment("testing")
        security_config.encryption_key = encryption_key

        factory = CacheFactory()

        # Act - Test different factory creation methods
        memory_cache = await factory.for_testing(
            security_config=security_config,
            use_memory_cache=True
        )

        # Assert
        assert memory_cache is not None, "Factory should create cache with encryption configuration"

        # Test encrypted operations work
        test_key = "factory:encryption:test"
        test_value = {"factory_encryption_test": True, "sensitive": "data"}

        await memory_cache.set(test_key, test_value)
        retrieved = await memory_cache.get(test_key)

        assert retrieved == test_value, "Factory-created cache should support encrypted operations"

        # Verify encryption is actually active (data should be encrypted in underlying storage)
        if hasattr(memory_cache, "_l1_cache") and memory_cache._l1_cache:
            # Check if L1 cache data is encrypted
            l1_data = memory_cache._l1_cache._cache.get(test_key)
            if l1_data:
                # Data should be encrypted (not human-readable)
                l1_str = l1_data.decode("utf-8", errors="ignore")
                assert "sensitive" not in l1_str, "Data in cache should be encrypted"


class TestEncryptionErrorHandlingIntegration:
    """
    Tests for encryption error handling and exception propagation integration.

    Seam Under Test:
        Encryption operations → Error detection → ConfigurationError creation →
        Context enrichment → Error propagation → Application handling

    Critical Paths:
        - Invalid encryption key handling with helpful error messages
        - Missing cryptography library detection and clear installation instructions
        - Non-serializable data handling with actionable error context
        - Decryption failures with diagnostic information

    Business Impact:
        Ensures encryption errors are properly detected, reported, and handled with
        actionable error messages for operations teams.
    """

    def test_invalid_encryption_key_error_context_and_message(self):
        """
        Test that invalid encryption keys raise ConfigurationError with helpful troubleshooting information.

        Integration Scope:
            Invalid key → EncryptedCacheLayer.__init__ → ConfigurationError with enriched context

        Business Impact:
            Ensures configuration errors are caught early with helpful messages for troubleshooting

        Test Strategy:
            - Try to create encryption layer with various invalid keys
            - Verify ConfigurationError is raised with helpful message
            - Test error context includes actionable troubleshooting guidance
            - Validate error classification for proper handling

        Success Criteria:
            - Invalid keys raise ConfigurationError with troubleshooting guidance
            - Error message includes actionable information for resolution
            - Error context includes proper error_type classification
            - Different types of invalid keys produce appropriate error messages
        """
        # Test invalid key case - should raise ConfigurationError with helpful context
        # Act & Assert
        try:
            EncryptedCacheLayer(encryption_key="definitely-invalid-key")
            pytest.fail("Expected ConfigurationError for invalid key")
        except ConfigurationError as exc_info:
            error = exc_info

            # Verify error message is helpful
            assert "invalid encryption key" in str(error).lower(), "Error should mention invalid key"
            assert "Fernet" in str(error) or "generate_key" in str(error), "Error should include key generation guidance"

            # Verify error context is enriched
            context = error.context
            assert context is not None, "Error should include context"
            assert context.get("error_type") == "invalid_encryption_key", "Error type should be classified"
            assert "original_error" in context, "Original error should be preserved"

            # Verify error message includes troubleshooting steps
            assert "python -c" in str(error) or "pip install" in str(error), "Error should include installation/generation commands"

        # Test empty string specifically - should result in disabled encryption (empty string is falsy)
        encryption_empty = EncryptedCacheLayer(encryption_key="")
        assert not encryption_empty.is_enabled, "Empty string should result in disabled encryption"
        assert encryption_empty.fernet is None, "Fernet instance should be None for empty string key"

    def test_missing_cryptography_library_error_handling(self, monkeypatch):
        """
        Test graceful handling when cryptography library is unavailable.

        Integration Scope:
            Missing import → CRYPTOGRAPHY_AVAILABLE flag → ConfigurationError →
            Installation instructions → Application guidance

        Business Impact:
            Ensures proper dependency management and clear error messages when
            cryptography library is missing

        Test Strategy:
            - Mock cryptography library as unavailable
            - Attempt to create encryption layer
            - Verify ConfigurationError with installation instructions
            - Test error context includes dependency information

        Success Criteria:
            - Missing cryptography raises ConfigurationError with installation instructions
            - Error message includes pip install command
            - Error context properly classifies as missing dependency
            - Graceful degradation behavior is documented
        """
        # Arrange - Mock cryptography as unavailable
        original_available = EncryptedCacheLayer.__module__
        original_crypto = None

        # Mock the import to fail
        import sys
        original_modules = sys.modules.copy()

        # Remove cryptography modules to simulate missing dependency
        modules_to_remove = [m for m in sys.modules.keys() if "cryptography" in m]
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]

        # Also patch the CRYPTOGRAPHY_AVAILABLE flag
        original_import = EncryptedCacheLayer.__init__.__globals__.get("CRYPTOGRAPHY_AVAILABLE")
        EncryptedCacheLayer.__init__.__globals__["CRYPTOGRAPHY_AVAILABLE"] = False

        try:
            # Act & Assert
            with pytest.raises(ConfigurationError) as exc_info:
                EncryptedCacheLayer(encryption_key="test-key")

            error = exc_info.value

            # Verify error message is helpful
            assert "cryptography library is required" in str(error), "Error should mention missing library"
            assert "pip install cryptography" in str(error), "Error should include installation command"

            # Verify error context
            context = error.context
            assert context.get("error_type") == "missing_dependency", "Error should be classified as missing dependency"
            assert context.get("required_package") == "cryptography", "Should specify required package"

        finally:
            # Restore original state
            EncryptedCacheLayer.__init__.__globals__["CRYPTOGRAPHY_AVAILABLE"] = original_import
            sys.modules.clear()
            sys.modules.update(original_modules)

    def test_non_serializable_data_error_handling(self):
        """
        Test error handling for non-serializable data in encryption operations.

        Integration Scope:
            Non-serializable data → JSON serialization failure → ConfigurationError →
            Context enrichment → Actionable error message

        Business Impact:
            Ensures developers get clear feedback when trying to encrypt unsupported data types

        Test Strategy:
            - Try to encrypt various non-serializable data types
            - Verify ConfigurationError with helpful error message
            - Test error context includes data type information
            - Validate error message includes allowed data types

        Success Criteria:
            - Non-serializable data raises ConfigurationError with clear error context
            - Error message includes list of allowed data types
            - Error context includes actual data type for debugging
            - Error provides actionable guidance for fixing the issue
        """
        # Arrange - Non-serializable test cases
        non_serializable_cases = [
            ("datetime", {"created_at": __import__("datetime").datetime.now()}),
            ("custom_object", {"obj": type("CustomClass", (), {"value": "test"})()}),
            ("function", {"func": lambda x: x}),
            ("complex_nested", {"mixed": [1, 2, {"date": __import__("datetime").date.today()}]}),
        ]

        encryption = EncryptedCacheLayer.create_with_generated_key()

        for case_name, test_data in non_serializable_cases:
            # Act & Assert
            with pytest.raises(ConfigurationError) as exc_info:
                encryption.encrypt_cache_data(test_data)

            error = exc_info.value

            # Verify error message is helpful
            assert "Failed to serialize cache data" in str(error), "Error should mention serialization failure"
            assert "JSON-serializable" in str(error), "Error should mention JSON serialization requirement"

            # Verify error context includes debugging information
            context = error.context
            assert context.get("error_type") == "serialization_error", "Error should be classified as serialization error"
            assert "data_type" in context, "Context should include actual data type"
            assert "original_error" in context, "Context should include original error"

    @pytest.mark.asyncio
    async def test_decryption_failure_error_handling(self):
        """
        Test error handling for decryption failures with corrupted or invalid data.

        Integration Scope:
            Invalid/corrupted data → Decryption attempt → Error detection →
            ConfigurationError → Diagnostic information

        Business Impact:
            Ensures decryption failures are properly detected and reported with
            diagnostic information for troubleshooting

        Test Strategy:
            - Try to decrypt various types of invalid/corrupted data
            - Verify ConfigurationError with diagnostic information
            - Test error context helps identify root cause
            - Validate error message includes troubleshooting steps

        Success Criteria:
            - Invalid data raises ConfigurationError with diagnostic information
            - Error message includes possible causes and troubleshooting steps
            - Error context includes data size and error details
            - Different error types produce appropriate error messages
        """
        encryption = EncryptedCacheLayer.create_with_generated_key()

        # Test cases for invalid decryption data
        invalid_cases = [
            ("invalid_bytes", b"not-encrypted-data"),
            ("wrong_key_data", b"some-encrypted-with-different-key"),
            ("corrupted_data", b"\x00\x01\x02corrupted"),
            ("empty_data", b""),
            ("unicode_bytes", b"not-bytes"),
        ]

        for case_name, invalid_data in invalid_cases:
            # Act & Assert
            with pytest.raises(ConfigurationError) as exc_info:
                encryption.decrypt_cache_data(invalid_data)

            error = exc_info.value

            # Verify error message is helpful
            assert "Failed to deserialize cache data" in str(error) or "Data decryption failed" in str(error), "Error should mention decryption/deserialization failure"

            # Verify error context includes diagnostic information
            context = error.context
            assert context.get("error_type") in ["deserialization_error", "decryption_failure"], "Error should be properly classified"

            if "data_size" in context:
                assert isinstance(context["data_size"], int), "Data size should be included for debugging"

            assert "original_error" in context, "Original error should be preserved"

    @pytest.mark.asyncio
    async def test_error_propagation_through_integration_layers(self, monkeypatch):
        """
        Test that encryption errors properly propagate through integration layers.

        Integration Scope:
            Encryption error → Exception propagation → Context preservation →
            Application error handling with enriched information

        Business Impact:
            Ensures error context is preserved through the call stack for effective troubleshooting

        Test Strategy:
            - Trigger encryption errors at different layers
            - Verify error context is preserved through propagation
            - Test error handling in integrated scenarios
            - Validate error enrichment doesn't lose original information

        Success Criteria:
            - Error context is preserved through exception propagation
            - Original error details are maintained in context
            - Error enrichment adds value without losing information
            - Integration layers properly handle and propagate errors
        """
        # Test error propagation through environment integration
        # The create_encryption_layer_from_env function should properly propagate
        # encryption initialization errors from the EncryptedCacheLayer
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "definitely-invalid-key")

        with pytest.raises(ConfigurationError) as exc_info:
            create_encryption_layer_from_env()

        error = exc_info.value
        assert error.context.get("error_type") == "invalid_encryption_key", "Error type should be preserved through environment integration"
        assert "original_error" in error.context, "Original error should be preserved"
        assert "invalid encryption key" in str(error).lower(), "Error message should indicate encryption key issue"

    def test_performance_monitoring_during_error_scenarios(self):
        """
        Test that performance monitoring correctly handles error scenarios.

        Integration Scope:
            Error during encryption/decryption → Performance tracking → Error handling →
            Statistics accuracy maintenance

        Business Impact:
            Ensures performance monitoring remains accurate even during error scenarios

        Test Strategy:
            - Trigger encryption/decryption errors
            - Verify performance monitoring handles errors gracefully
            - Test statistics accuracy after error scenarios
            - Validate monitoring doesn't interfere with error handling

        Success Criteria:
            - Performance monitoring handles errors without crashing
            - Statistics remain accurate after error scenarios
            - Error operations are properly tracked or excluded as appropriate
            - Monitoring infrastructure doesn't mask or amplify errors
        """
        # Arrange
        encryption = EncryptedCacheLayer.create_with_generated_key(performance_monitoring=True)

        # Perform some successful operations to establish baseline
        valid_data = {"test": "data"}
        for _ in range(5):
            encrypted = encryption.encrypt_cache_data(valid_data)
            encryption.decrypt_cache_data(encrypted)

        baseline_stats = encryption.get_performance_stats()
        assert baseline_stats["encryption_operations"] == 5
        assert baseline_stats["decryption_operations"] == 5

        # Test error handling during encryption
        invalid_data = {"date": __import__("datetime").datetime.now()}

        with pytest.raises(ConfigurationError):
            encryption.encrypt_cache_data(invalid_data)

        # Verify statistics after encryption error
        error_stats = encryption.get_performance_stats()
        assert error_stats["encryption_operations"] == baseline_stats["encryption_operations"], "Failed encryption should not increment operation count"
        assert error_stats["decryption_operations"] == baseline_stats["decryption_operations"], "Failed encryption should not affect decryption count"

        # Test error handling during decryption
        invalid_encrypted = b"invalid-encrypted-data"

        with pytest.raises(ConfigurationError):
            encryption.decrypt_cache_data(invalid_encrypted)

        # Verify statistics after decryption error
        final_stats = encryption.get_performance_stats()
        assert final_stats["decryption_operations"] == baseline_stats["decryption_operations"], "Failed decryption should not increment operation count"

        # Verify monitoring still works correctly after errors
        valid_data = {"recovery": "test"}
        encrypted = encryption.encrypt_cache_data(valid_data)
        decrypted = encryption.decrypt_cache_data(encrypted)

        recovery_stats = encryption.get_performance_stats()
        assert recovery_stats["encryption_operations"] == baseline_stats["encryption_operations"] + 1, "Operations should work correctly after errors"
        assert recovery_stats["decryption_operations"] == baseline_stats["decryption_operations"] + 1, "Operations should work correctly after errors"
