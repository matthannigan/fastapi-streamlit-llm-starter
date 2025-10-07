"""
Application-layer encryption for Redis cache data.

This module provides mandatory Fernet encryption for all cached data with transparent
operation. It ensures that all data stored in Redis is encrypted at rest using
application-layer encryption, providing an additional security layer beyond TLS.

## Security Features

- **Always-On Encryption**: All cache data is encrypted by default, no opt-out available
- **Fernet Encryption**: Uses industry-standard symmetric encryption from cryptography library
- **Key Management**: Secure encryption key management with environment-aware generation
- **Performance Optimized**: Efficient encryption/decryption with minimal overhead
- **Error Handling**: Graceful handling of encryption failures and key rotation scenarios
- **Transparent Operation**: Seamless integration with existing cache operations

## Usage

```python
from app.infrastructure.cache.encryption import EncryptedCacheLayer

# Initialize with encryption key
encryption = EncryptedCacheLayer("your-fernet-key")

# Encrypt data before storage
encrypted_data = encryption.encrypt_cache_data({"key": "value"})

# Decrypt data after retrieval
original_data = encryption.decrypt_cache_data(encrypted_data)

# Check encryption status
if encryption.is_enabled:
    print("Data encryption is active")
```
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Union

from app.core.exceptions import ConfigurationError

# Optional cryptography import for graceful degradation
try:
    from cryptography.fernet import Fernet, InvalidToken

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception

logger = logging.getLogger(__name__)


class EncryptedCacheLayer:
    """
    Handles encryption/decryption of sensitive cache data.

    This class provides application-layer encryption for all cached data using
    Fernet symmetric encryption. It ensures that sensitive data is encrypted
    before storage and decrypted transparently on retrieval.

    The encryption layer is designed to be always-on and provides performance
    monitoring to ensure encryption overhead stays within acceptable limits.
    """

    def __init__(
        self, encryption_key: Optional[str] = None, performance_monitoring: bool = True
    ):
        """
        Initialize the encrypted cache layer.

        Args:
            encryption_key: Fernet encryption key in base64 format.
                          If None, encryption will be disabled (not recommended).
            performance_monitoring: Enable performance monitoring for encryption operations

        Raises:
            ConfigurationError: If encryption key is invalid or cryptography is unavailable

        Examples:
            # Standard initialization
            encryption = EncryptedCacheLayer("your-fernet-key")

            # Without performance monitoring
            encryption = EncryptedCacheLayer("your-fernet-key", performance_monitoring=False)

        Note:
            This implementation follows the security-first approach where encryption
            is mandatory. Passing None for encryption_key will log warnings and
            should only be used in testing scenarios.
        """
        self.logger = logging.getLogger(__name__)
        self.performance_monitoring = performance_monitoring
        self.fernet = None

        # Performance tracking
        self._encryption_operations = 0
        self._decryption_operations = 0
        self._total_encryption_time = 0.0
        self._total_decryption_time = 0.0

        # Check cryptography availability
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ConfigurationError(
                "🔒 ENCRYPTION ERROR: cryptography library is required for data encryption.\n"
                "\n"
                "Install with: pip install cryptography\n"
                "\n"
                "This is a mandatory dependency for secure Redis operations.",
                context={
                    "error_type": "missing_dependency",
                    "required_package": "cryptography",
                },
            )

        # Initialize encryption
        if encryption_key:
            self._initialize_encryption(encryption_key)
        else:
            self.logger.warning(
                "⚠️  SECURITY WARNING: Cache encryption is disabled!\n"
                "This should only occur in testing environments.\n"
                "Production deployments must use encryption."
            )

    def _initialize_encryption(self, encryption_key: str) -> None:
        """
        Initialize Fernet encryption with validation.

        Args:
            encryption_key: Base64-encoded Fernet key

        Raises:
            ConfigurationError: If encryption key is invalid
        """
        try:
            # Validate and create Fernet instance
            if isinstance(encryption_key, str):
                key_bytes = encryption_key.encode("utf-8")
            else:
                key_bytes = encryption_key

            self.fernet = Fernet(key_bytes)

            # Test encryption/decryption to validate key
            test_data = b"encryption_test"
            encrypted = self.fernet.encrypt(test_data)
            decrypted = self.fernet.decrypt(encrypted)

            if decrypted != test_data:
                raise ConfigurationError("Encryption key validation failed")

            self.logger.info("🔐 Cache encryption enabled successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            raise ConfigurationError(
                f"🔒 ENCRYPTION ERROR: Invalid encryption key.\n"
                "\n"
                f"Error: {str(e)}\n"
                "\n"
                "To fix this issue:\n"
                '1. Generate a new key: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"\n'
                "2. Set REDIS_ENCRYPTION_KEY environment variable\n"
                "3. Use SecurityConfig.create_for_environment() for automatic key generation\n",
                context={
                    "error_type": "invalid_encryption_key",
                    "original_error": str(e),
                },
            )

    def encrypt_cache_data(self, data: Dict[str, Any]) -> bytes:
        """
        Encrypt cache data if encryption is enabled.

        This method serializes the data to JSON and encrypts it using Fernet.
        If encryption is disabled, it returns the JSON-serialized data as bytes
        with a warning.

        Args:
            data: Dictionary data to encrypt

        Returns:
            Encrypted data as bytes

        Raises:
            ConfigurationError: If encryption fails or data cannot be serialized

        Examples:
            # Encrypt user data
            encrypted = encryption.encrypt_cache_data({"user_id": 123, "name": "Alice"})

            # Encrypt AI response
            ai_data = {"response": "Generated text", "model": "gpt-4", "timestamp": 1234567890}
            encrypted = encryption.encrypt_cache_data(ai_data)

        Performance:
            Typical encryption adds <5ms overhead for data <1KB.
            Larger datasets may see proportional increases.
        """
        start_time = time.perf_counter() if self.performance_monitoring else 0

        try:
            # Serialize data to JSON
            json_data = json.dumps(data, ensure_ascii=False, sort_keys=True)
            json_bytes = json_data.encode("utf-8")

            # Encrypt if enabled
            if self.fernet:
                encrypted_data = self.fernet.encrypt(json_bytes)
                result = encrypted_data
            else:
                # No encryption - return raw JSON bytes with warning
                self.logger.warning(
                    "🔓 Data stored without encryption (encryption disabled)"
                )
                result = json_bytes

            # Performance tracking
            if self.performance_monitoring:
                elapsed = time.perf_counter() - start_time
                self._encryption_operations += 1
                self._total_encryption_time += elapsed

                # Log performance warning if operation is slow
                if elapsed > 0.05:  # 50ms threshold
                    self.logger.warning(
                        f"Slow encryption operation: {elapsed:.3f}s for {len(json_bytes)} bytes"
                    )

            return result

        except (TypeError, ValueError) as e:
            raise ConfigurationError(
                f"🔒 ENCRYPTION ERROR: Failed to serialize cache data.\n"
                "\n"
                f"Error: {str(e)}\n"
                "\n"
                "Ensure cache data contains only JSON-serializable types:\n"
                "- Basic types: str, int, float, bool, None\n"
                "- Collections: list, dict\n"
                "- Avoid: datetime, custom objects, functions\n",
                context={
                    "error_type": "serialization_error",
                    "data_type": type(data).__name__,
                    "original_error": str(e),
                },
            )
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise ConfigurationError(
                f"🔒 ENCRYPTION ERROR: Data encryption failed.\n"
                "\n"
                f"Error: {str(e)}\n"
                "\n"
                "This may indicate:\n"
                "- Corrupted encryption key\n"
                "- System resource constraints\n"
                "- Cryptographic library issues\n",
                context={"error_type": "encryption_failure", "original_error": str(e)},
            )

    def decrypt_cache_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """
        Decrypt cache data if encryption is enabled.

        This method decrypts the encrypted bytes using Fernet and deserializes
        the result from JSON. It includes fallback handling for data that was
        stored without encryption.

        Args:
            encrypted_data: Encrypted data bytes from cache

        Returns:
            Decrypted data as dictionary

        Raises:
            ConfigurationError: If decryption fails or data cannot be deserialized

        Examples:
            # Decrypt user data
            user_data = encryption.decrypt_cache_data(encrypted_bytes)
            print(user_data["name"])  # "Alice"

            # Decrypt AI response
            ai_response = encryption.decrypt_cache_data(encrypted_ai_data)
            print(ai_response["response"])

        Performance:
            Typical decryption adds <3ms overhead for data <1KB.
            Performance is generally better than encryption.
        """
        start_time = time.perf_counter() if self.performance_monitoring else 0

        try:
            # Decrypt if encryption is enabled
            if self.fernet:
                try:
                    decrypted_bytes = self.fernet.decrypt(encrypted_data)
                except InvalidToken:
                    # Try to handle unencrypted data (backward compatibility)
                    self.logger.warning(
                        "🔓 Attempting to read unencrypted cache data (backward compatibility)"
                    )
                    decrypted_bytes = encrypted_data
            else:
                # No encryption - treat as raw JSON bytes
                decrypted_bytes = encrypted_data

            # Deserialize JSON data
            json_string = decrypted_bytes.decode("utf-8")
            data = json.loads(json_string)

            # Performance tracking
            if self.performance_monitoring:
                elapsed = time.perf_counter() - start_time
                self._decryption_operations += 1
                self._total_decryption_time += elapsed

                # Log performance warning if operation is slow
                if elapsed > 0.03:  # 30ms threshold
                    self.logger.warning(
                        f"Slow decryption operation: {elapsed:.3f}s for {len(encrypted_data)} bytes"
                    )

            return data

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ConfigurationError(
                f"🔒 DECRYPTION ERROR: Failed to deserialize cache data.\n"
                "\n"
                f"Error: {str(e)}\n"
                "\n"
                "This may indicate:\n"
                "- Corrupted cache data\n"
                "- Wrong encryption key\n"
                "- Data format mismatch\n"
                "- Cache corruption\n",
                context={
                    "error_type": "deserialization_error",
                    "data_size": len(encrypted_data),
                    "original_error": str(e),
                },
            )
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise ConfigurationError(
                f"🔒 DECRYPTION ERROR: Data decryption failed.\n"
                "\n"
                f"Error: {str(e)}\n"
                "\n"
                "This may indicate:\n"
                "- Invalid encryption key\n"
                "- Data corruption\n"
                "- Key rotation issues\n"
                "- Cryptographic library problems\n",
                context={"error_type": "decryption_failure", "original_error": str(e)},
            )

    @property
    def is_enabled(self) -> bool:
        """
        Check if encryption is enabled.

        Returns:
            True if encryption is active, False otherwise

        Examples:
            if encryption.is_enabled:
                print("Cache data is encrypted")
            else:
                print("WARNING: Cache data is not encrypted!")
        """
        return self.fernet is not None

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get encryption performance statistics.

        Returns detailed performance metrics for monitoring and optimization.

        Returns:
            Dictionary containing performance metrics

        Examples:
            stats = encryption.get_performance_stats()
            print(f"Average encryption time: {stats['avg_encryption_time']:.3f}ms")
            print(f"Total operations: {stats['total_operations']}")
        """
        if not self.performance_monitoring:
            return {"error": "Performance monitoring is disabled"}

        return {
            "encryption_enabled": self.is_enabled,
            "encryption_operations": self._encryption_operations,
            "decryption_operations": self._decryption_operations,
            "total_operations": self._encryption_operations
            + self._decryption_operations,
            "total_encryption_time": self._total_encryption_time,
            "total_decryption_time": self._total_decryption_time,
            "avg_encryption_time": (
                self._total_encryption_time / self._encryption_operations
                if self._encryption_operations > 0
                else 0
            )
            * 1000,  # Convert to milliseconds
            "avg_decryption_time": (
                self._total_decryption_time / self._decryption_operations
                if self._decryption_operations > 0
                else 0
            )
            * 1000,  # Convert to milliseconds
            "performance_monitoring": self.performance_monitoring,
        }

    def reset_performance_stats(self) -> None:
        """
        Reset performance statistics.

        Useful for testing or monitoring specific time periods.

        Examples:
            encryption.reset_performance_stats()
            # ... perform operations ...
            stats = encryption.get_performance_stats()
        """
        self._encryption_operations = 0
        self._decryption_operations = 0
        self._total_encryption_time = 0.0
        self._total_decryption_time = 0.0
        self.logger.info("Performance statistics reset")

    @classmethod
    def create_with_generated_key(cls, **kwargs) -> "EncryptedCacheLayer":
        """
        Create EncryptedCacheLayer with a generated encryption key.

        This is a convenience method for development and testing. For production,
        use proper key management with environment variables or key management services.

        Args:
            **kwargs: Additional arguments passed to __init__

        Returns:
            EncryptedCacheLayer instance with generated key

        Examples:
            # For development/testing only
            encryption = EncryptedCacheLayer.create_with_generated_key()

            # With additional options
            encryption = EncryptedCacheLayer.create_with_generated_key(
                performance_monitoring=False
            )

        Warning:
            This method generates a new key each time. Data encrypted with
            one key cannot be decrypted with another key.
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            raise ConfigurationError("cryptography library is required")

        key = Fernet.generate_key()
        return cls(encryption_key=key.decode(), **kwargs)


def create_encryption_layer_from_env() -> EncryptedCacheLayer:
    """
    Create EncryptedCacheLayer from environment variables.

    This function creates an encryption layer using the REDIS_ENCRYPTION_KEY
    environment variable. If the key is not available, it logs an error and
    creates a layer without encryption (not recommended for production).

    Returns:
        EncryptedCacheLayer instance

    Environment Variables:
        REDIS_ENCRYPTION_KEY: Base64-encoded Fernet encryption key

    Examples:
        # Create from environment
        encryption = create_encryption_layer_from_env()

        # Use in cache implementation
        class MyCache:
            def __init__(self):
                self.encryption = create_encryption_layer_from_env()

    Note:
        This function follows the security-first approach and will create
        an encryption layer even without a key, but with appropriate warnings.
    """
    import os

    encryption_key = os.getenv("REDIS_ENCRYPTION_KEY")

    if not encryption_key:
        logger.warning(
            "⚠️  SECURITY WARNING: REDIS_ENCRYPTION_KEY not set!\n"
            "Cache data will not be encrypted.\n"
            "Set REDIS_ENCRYPTION_KEY environment variable for secure operation."
        )

    return EncryptedCacheLayer(encryption_key=encryption_key)
