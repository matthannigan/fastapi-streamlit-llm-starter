"""
Test fixtures for encryption module unit tests.

This module provides reusable fixtures for testing the encryption module following
behavior-driven testing principles. Fixtures provide test doubles (Fakes and Mocks)
for external dependencies while keeping internal cache infrastructure components real.

Fixture Categories:
    - Fake Fernet implementation (lightweight encryption for testing)
    - Real encryption layer instances (with various configurations)
    - Test data fixtures (encryption keys, cache data)
    - Mock logger fixtures (for testing logging behavior)

Design Philosophy:
    - Prefer Fakes over Mocks for stateful behavior (Fernet encryption)
    - Mock only at system boundaries (logging, I/O)
    - Fixtures represent 'happy path' behavior by default
    - Error scenarios configured within individual tests
"""

import pytest

# Real imports from the same application (not mocked)


# =============================================================================
# Fake Fernet Implementation (Preferred over Mock)
# =============================================================================


class FakeFernet:
    """
    Fake Fernet encryption implementation for testing.

    Provides a lightweight, in-memory encryption implementation that simulates
    Fernet's behavior without requiring the full cryptography library. This
    enables fast, deterministic testing of encryption functionality.

    Behavior:
        - Encrypts by prepending "ENCRYPTED:" prefix to JSON bytes
        - Decrypts by removing "ENCRYPTED:" prefix
        - Raises InvalidToken for data not starting with "ENCRYPTED:"
        - Stateless - each operation is independent
        - Deterministic - same input always produces same output

    Usage:
        fake_fernet = FakeFernet(b"fake-key")
        encrypted = fake_fernet.encrypt(b"test data")
        decrypted = fake_fernet.decrypt(encrypted)
        assert decrypted == b"test data"

    Note:
        This is NOT cryptographically secure and should NEVER be used
        in production. It exists solely for testing encryption logic.
    """

    def __init__(self, key: bytes):
        """
        Initialize fake Fernet with a key.

        Args:
            key: Encryption key (not validated, accepts any bytes)
        """
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """
        Fake encrypt by prefixing data.

        Args:
            data: Plain data to encrypt

        Returns:
            "Encrypted" data with ENCRYPTED: prefix

        Behavior:
            Simple prefix-based transformation that's easily reversible
            for testing decryption logic without real cryptography.
        """
        return b"ENCRYPTED:" + data

    def decrypt(self, token: bytes) -> bytes:
        """
        Fake decrypt by removing prefix.

        Args:
            token: "Encrypted" data to decrypt

        Returns:
            Original data without ENCRYPTED: prefix

        Raises:
            FakeInvalidToken: If token doesn't start with ENCRYPTED:

        Behavior:
            Validates token format and strips prefix to simulate
            decryption behavior for testing error handling.
        """
        if not token.startswith(b"ENCRYPTED:"):
            raise FakeInvalidToken("Invalid token format")
        return token[len(b"ENCRYPTED:") :]

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a fake encryption key for testing.

        Returns:
            Deterministic fake key bytes

        Behavior:
            Returns fixed test key for reproducible test behavior.
        """
        return b"fake-test-key-32-bytes-long!!!!!"


class FakeInvalidToken(Exception):
    """
    Fake InvalidToken exception matching cryptography.fernet.InvalidToken.

    Used by FakeFernet to simulate decryption failures without requiring
    the real cryptography library.
    """



# =============================================================================
# Encryption Key Fixtures
# =============================================================================
# NOTE: Common encryption key fixtures have been moved to backend/tests/unit/conftest.py
#       and are available to all test modules:
#       - valid_fernet_key
#       - invalid_fernet_key_short
#       - invalid_fernet_key_format
#       - empty_encryption_key
#
# Use those shared fixtures instead of defining module-specific ones.


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_cache_data():
    """
    Sample cache data for encryption testing.

    Provides a typical dictionary structure that would be cached and encrypted,
    representing realistic application data.

    Returns:
        Dictionary with various data types (str, int, float, list, dict)

    Use Cases:
        - Testing data serialization before encryption
        - Testing encryption/decryption round-trip
        - Testing data integrity preservation

    Example:
        def test_encryption_preserves_data_integrity(encryption, sample_cache_data):
            encrypted = encryption.encrypt_cache_data(sample_cache_data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            assert decrypted == sample_cache_data
    """
    return {
        "user_id": 12345,
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "preferences": {
            "theme": "dark",
            "language": "en",
            "notifications": True,
        },
        "scores": [95.5, 87.3, 92.1],
        "metadata": {
            "created_at": "2023-01-15T10:30:00Z",
            "updated_at": "2023-09-30T14:45:00Z",
        },
    }


@pytest.fixture
def sample_ai_response_data():
    """
    Sample AI response data for encryption testing.

    Provides a typical AI processing result structure that would be
    cached with encryption for security.

    Returns:
        Dictionary representing AI processing results

    Use Cases:
        - Testing AI response encryption
        - Testing large payload handling
        - Testing nested structure serialization

    Example:
        def test_ai_response_encryption(encryption, sample_ai_response_data):
            encrypted = encryption.encrypt_cache_data(sample_ai_response_data)
            assert len(encrypted) > 0
    """
    return {
        "result": "This is a comprehensive summary of the input document covering key points about AI technology, machine learning advances, and practical applications.",
        "confidence": 0.95,
        "model": "gemini-2.0-flash-exp",
        "metadata": {
            "processing_time": 1.234,
            "tokens_used": 567,
            "operation": "summarize",
        },
        "timestamp": "2023-09-30T15:00:00Z",
    }


@pytest.fixture
def sample_unicode_data():
    """
    Sample data with Unicode characters for testing encoding.

    Provides dictionary containing various Unicode characters, emojis,
    and international text to test proper encoding/decoding.

    Returns:
        Dictionary with Unicode strings in multiple languages

    Use Cases:
        - Testing UTF-8 encoding handling
        - Testing emoji preservation through encryption
        - Testing international character support

    Example:
        def test_unicode_data_encryption(encryption, sample_unicode_data):
            encrypted = encryption.encrypt_cache_data(sample_unicode_data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            assert decrypted["emoji"] == sample_unicode_data["emoji"]
    """
    return {
        "emoji": "Testing with emojis! 🚀 🌟 ✨ 🎯 🔐",
        "international": {
            "chinese": "加密测试数据",
            "japanese": "暗号化テストデータ",
            "russian": "Тестовые данные шифрования",
            "arabic": "بيانات اختبار التشفير",
            "mixed": "Hello 世界 🌍 Привет мир! مرحبا",
        },
        "special_chars": "Chars: àáâãäåæçèéêëìíîïñòóôõöøùúûüý",
    }


@pytest.fixture
def sample_empty_data():
    """
    Empty dictionary for testing edge case handling.

    Returns:
        Empty dictionary

    Use Cases:
        - Testing empty data encryption
        - Testing minimal payload handling
        - Testing edge case serialization

    Example:
        def test_empty_data_encryption(encryption, sample_empty_data):
            encrypted = encryption.encrypt_cache_data(sample_empty_data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            assert decrypted == {}
    """
    return {}


@pytest.fixture
def sample_large_data():
    """
    Large data payload for performance testing.

    Provides a large dictionary to test encryption performance
    and verify behavior with larger payloads.

    Returns:
        Dictionary with large nested data structure

    Use Cases:
        - Testing encryption performance monitoring
        - Testing large payload handling
        - Testing serialization of complex structures

    Example:
        def test_large_data_performance(encryption, sample_large_data):
            encrypted = encryption.encrypt_cache_data(sample_large_data)
            stats = encryption.get_performance_stats()
            assert stats["avg_encryption_time"] < 50  # Less than 50ms
    """
    return {
        "users": [
            {
                "id": i,
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "data": "x" * 100,  # 100 chars per user
            }
            for i in range(100)
        ],
        "metadata": {"total": 100, "generated": "test"},
    }


# =============================================================================
# Encrypted Bytes Fixtures
# =============================================================================


@pytest.fixture
def sample_encrypted_bytes(valid_fernet_key, sample_cache_data):
    """
    Pre-encrypted sample data for testing decryption.

    Provides encrypted bytes generated from sample_cache_data using
    valid_fernet_key for testing decryption behavior.

    Returns:
        Encrypted bytes from sample_cache_data

    Use Cases:
        - Testing decryption logic independently
        - Testing encrypted data handling
        - Testing cache retrieval with encrypted data

    Dependencies:
        Requires cryptography library for real encryption

    Example:
        def test_decryption_of_encrypted_data(encryption, sample_encrypted_bytes):
            decrypted = encryption.decrypt_cache_data(sample_encrypted_bytes)
            assert "user_id" in decrypted
    """
    import json

    try:
        from cryptography.fernet import Fernet

        fernet = Fernet(valid_fernet_key.encode())
        json_data = json.dumps(sample_cache_data, ensure_ascii=False, sort_keys=True)
        return fernet.encrypt(json_data.encode("utf-8"))
    except ImportError:
        # Fallback to fake encryption
        fake_fernet = FakeFernet(b"test-key")
        json_data = json.dumps(sample_cache_data, ensure_ascii=False, sort_keys=True)
        return fake_fernet.encrypt(json_data.encode("utf-8"))


@pytest.fixture
def sample_invalid_encrypted_bytes():
    """
    Invalid encrypted bytes for testing decryption error handling.

    Provides bytes that cannot be decrypted to test error handling
    in decryption logic.

    Returns:
        Invalid encrypted bytes

    Use Cases:
        - Testing InvalidToken exception handling
        - Testing decryption error messages
        - Testing graceful failure with corrupted data

    Example:
        def test_decryption_handles_invalid_data(encryption, sample_invalid_encrypted_bytes):
            with pytest.raises(ConfigurationError):
                encryption.decrypt_cache_data(sample_invalid_encrypted_bytes)
    """
    return b"invalid-encrypted-data-cannot-be-decrypted"


@pytest.fixture
def sample_unencrypted_json_bytes(sample_cache_data):
    """
    Unencrypted JSON bytes for testing backward compatibility.

    Provides JSON-serialized bytes without encryption for testing
    backward compatibility with data stored before encryption was enabled.

    Returns:
        JSON bytes without encryption

    Use Cases:
        - Testing backward compatibility
        - Testing unencrypted data fallback handling
        - Testing migration from unencrypted to encrypted cache

    Example:
        def test_decryption_handles_unencrypted_data(encryption, sample_unencrypted_json_bytes):
            # Should handle gracefully or raise appropriate error
            try:
                decrypted = encryption.decrypt_cache_data(sample_unencrypted_json_bytes)
            except ConfigurationError:
                pass  # Expected for strict encryption mode
    """
    import json

    json_data = json.dumps(sample_cache_data, ensure_ascii=False, sort_keys=True)
    return json_data.encode("utf-8")


# =============================================================================
# Real Encryption Layer Instances
# =============================================================================


@pytest.fixture
def encryption_with_valid_key(valid_fernet_key):
    """
    EncryptedCacheLayer instance with valid encryption key.

    Provides a real EncryptedCacheLayer instance configured with
    a valid encryption key for testing standard encryption behavior.

    Returns:
        EncryptedCacheLayer with encryption enabled

    Use Cases:
        - Testing standard encryption operations
        - Testing encryption/decryption round-trips
        - Testing performance monitoring

    Example:
        def test_encryption_enabled(encryption_with_valid_key):
            assert encryption_with_valid_key.is_enabled is True
    """
    from app.infrastructure.cache.encryption import EncryptedCacheLayer

    return EncryptedCacheLayer(
        encryption_key=valid_fernet_key, performance_monitoring=True
    )


@pytest.fixture
def encryption_without_key():
    """
    EncryptedCacheLayer instance without encryption key (disabled).

    Provides a real EncryptedCacheLayer instance without encryption
    for testing disabled encryption behavior and warnings.

    Returns:
        EncryptedCacheLayer with encryption disabled

    Use Cases:
        - Testing disabled encryption behavior
        - Testing warning message generation
        - Testing backward compatibility mode

    Example:
        def test_encryption_disabled(encryption_without_key):
            assert encryption_without_key.is_enabled is False
    """
    from app.infrastructure.cache.encryption import EncryptedCacheLayer

    return EncryptedCacheLayer(encryption_key=None, performance_monitoring=True)


@pytest.fixture
def encryption_without_monitoring(valid_fernet_key):
    """
    EncryptedCacheLayer instance with monitoring disabled.

    Provides a real EncryptedCacheLayer instance with performance
    monitoring disabled for testing performance tracking behavior.

    Returns:
        EncryptedCacheLayer with monitoring disabled

    Use Cases:
        - Testing performance monitoring toggle
        - Testing get_performance_stats() with monitoring disabled
        - Testing overhead of performance tracking

    Example:
        def test_monitoring_disabled(encryption_without_monitoring):
            stats = encryption_without_monitoring.get_performance_stats()
            assert "error" in stats
    """
    from app.infrastructure.cache.encryption import EncryptedCacheLayer

    return EncryptedCacheLayer(
        encryption_key=valid_fernet_key, performance_monitoring=False
    )


@pytest.fixture
def encryption_with_generated_key():
    """
    EncryptedCacheLayer instance with auto-generated key.

    Provides a real EncryptedCacheLayer instance created using
    the create_with_generated_key() class method for testing
    key generation functionality.

    Returns:
        EncryptedCacheLayer with generated encryption key

    Use Cases:
        - Testing key generation method
        - Testing development/testing convenience features
        - Testing generated key validation

    Example:
        def test_generated_key_encryption(encryption_with_generated_key):
            assert encryption_with_generated_key.is_enabled is True
            data = {"test": "data"}
            encrypted = encryption_with_generated_key.encrypt_cache_data(data)
            assert len(encrypted) > 0
    """
    from app.infrastructure.cache.encryption import EncryptedCacheLayer

    return EncryptedCacheLayer.create_with_generated_key(performance_monitoring=True)


# =============================================================================
# Mock Logger and Cryptography Availability Fixtures
# =============================================================================
# NOTE: These common fixtures have been moved to backend/tests/unit/conftest.py
#       and are available to all test modules:
#       - mock_logger
#       - mock_cryptography_unavailable
#
# Use those shared fixtures instead of defining module-specific ones.


# =============================================================================
# Performance Testing Fixtures
# =============================================================================


@pytest.fixture
def encryption_with_fresh_stats(valid_fernet_key):
    """
    EncryptedCacheLayer with reset performance statistics.

    Provides a real EncryptedCacheLayer instance with performance
    monitoring enabled and statistics reset to zero for testing
    performance tracking behavior from a clean slate.

    Returns:
        EncryptedCacheLayer with reset statistics

    Use Cases:
        - Testing performance metric accumulation
        - Testing average calculation logic
        - Testing statistics reset functionality

    Example:
        def test_performance_stats_accumulation(encryption_with_fresh_stats):
            stats = encryption_with_fresh_stats.get_performance_stats()
            assert stats["total_operations"] == 0

            encryption_with_fresh_stats.encrypt_cache_data({"test": "data"})

            stats = encryption_with_fresh_stats.get_performance_stats()
            assert stats["total_operations"] == 1
    """
    from app.infrastructure.cache.encryption import EncryptedCacheLayer

    encryption = EncryptedCacheLayer(
        encryption_key=valid_fernet_key, performance_monitoring=True
    )
    encryption.reset_performance_stats()
    return encryption
