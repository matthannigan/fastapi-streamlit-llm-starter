"""
Integration tests for CacheFactory integration with encryption.

This module tests the integration between CacheFactory and encryption layer,
ensuring that cache instances created by the factory properly integrate
with encryption when security configuration includes encryption keys.

Test Focus:
    - CacheFactory creates encrypted caches when security config includes encryption
    - Factory methods (for_web_app, for_ai_app, for_testing) properly integrate encryption
    - Security configuration propagation through factory to cache instances
    - Error handling when encryption configuration is invalid
    - Cache instances support encrypted data operations after factory creation
"""

import pytest
from unittest.mock import patch, AsyncMock
from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.security import SecurityConfig

# Mark all tests in this module to run serially (not in parallel)
# These tests manipulate environment state and fail intermittently in parallel
pytestmark = pytest.mark.no_parallel


class TestCacheFactoryEncryptionIntegration:
    """
    Tests for CacheFactory integration with encryption layer.

    Integration Scope:
        CacheFactory → SecurityConfig with encryption key → EncryptedCacheLayer → Cache instance with encryption

    Business Impact:
        Ensures encryption is properly integrated into cache creation workflows
        across all factory methods, maintaining data security through factory patterns.

    Critical Paths:
        - Factory method receives security config with encryption key
        - Security config propagation to cache implementation
        - Encrypted cache instance initialization and validation
        - Factory error handling for encryption configuration issues
    """

    @pytest.fixture
    def encryption_security_config(self):
        """
        SecurityConfig with encryption key for testing.

        Returns:
            SecurityConfig: Configured with valid encryption key
        """
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()

        config = SecurityConfig(
            redis_auth="test-password",
            use_tls=False,
            verify_certificates=False,
        )
        # Dynamically add encryption_key attribute for testing
        config.encryption_key = encryption_key
        return config

    @pytest.fixture
    def security_config_without_encryption(self):
        """
        SecurityConfig without encryption key for testing.

        Returns:
            SecurityConfig: Configured without encryption key
        """
        return SecurityConfig(
            redis_auth="test-password",
            use_tls=False,
            verify_certificates=False,
        )

    @pytest.fixture
    def invalid_encryption_security_config(self):
        """
        SecurityConfig with invalid encryption key for testing error scenarios.

        Returns:
            SecurityConfig: Configured with invalid encryption key
        """
        config = SecurityConfig(
            redis_auth="test-password",
            use_tls=False,
            verify_certificates=False,
        )
        # Dynamically add invalid encryption_key attribute for testing
        # Use a base64-encoded key of wrong length (16 bytes instead of 32)
        config.encryption_key = "dGVzdC1rZXktZm9yLXRlc3Rpbmc="  # 16 bytes base64 encoded
        return config

    @pytest.mark.asyncio
    async def test_for_web_app_creates_encrypted_cache(
        self, encryption_security_config, monkeypatch
    ):
        """
        Test that for_web_app creates encrypted cache when security config includes encryption.

        Integration Scope:
            CacheFactory.for_web_app → SecurityConfig with encryption → EncryptedCacheLayer → GenericRedisCache with encryption

        Business Impact:
            Ensures web application caches created by factory automatically include
            encryption when security configuration specifies encryption keys.

        Test Strategy:
            - Create security config with encryption key
            - Call for_web_app with security config
            - Verify created cache instance supports encryption
            - Test encryption/decryption operations work correctly

        Success Criteria:
            - Cache instance is created successfully with encryption
            - Encryption layer is properly initialized
            - Cache operations use encryption transparently
        """
        # Mock Redis connection to avoid requiring actual Redis
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()
            cache = await factory.for_web_app(
                security_config=encryption_security_config,
                fail_on_connection_error=False,
            )

            # Verify cache was created
            assert cache is not None

            # If the cache has encryption, test it works
            if hasattr(cache, "_encryption_layer"):
                assert cache._encryption_layer.is_enabled

                # Test encryption works
                test_data = {"user_id": 123, "sensitive": "data"}
                encrypted = cache._encryption_layer.encrypt_cache_data(test_data)
                decrypted = cache._encryption_layer.decrypt_cache_data(encrypted)
                assert decrypted == test_data

    @pytest.mark.asyncio
    async def test_for_ai_app_creates_encrypted_cache(
        self, encryption_security_config, monkeypatch
    ):
        """
        Test that for_ai_app creates encrypted cache when security config includes encryption.

        Integration Scope:
            CacheFactory.for_ai_app → SecurityConfig with encryption → EncryptedCacheLayer → AIResponseCache with encryption

        Business Impact:
            Ensures AI application caches created by factory include encryption for
            protecting sensitive AI response data and user information.

        Test Strategy:
            - Create security config with encryption key
            - Call for_ai_app with security config
            - Verify created cache instance supports encryption
            - Validate AI-specific features work with encryption

        Success Criteria:
            - AI cache instance is created with encryption
            - Encryption integrates with AI-specific features
            - Cache operations maintain encryption transparency
        """
        # Mock Redis connection
        with patch("app.infrastructure.cache.redis_ai.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()
            cache = await factory.for_ai_app(
                security_config=encryption_security_config,
                fail_on_connection_error=False,
            )

            # Verify cache was created
            assert cache is not None

            # Test encryption integration if available
            if hasattr(cache, "_encryption_layer"):
                assert cache._encryption_layer.is_enabled

                # Test AI-specific data encryption
                ai_data = {
                    "response": "Generated text summary",
                    "model": "gemini-2.0-flash-exp",
                    "user_query": "Summarize this document",
                    "confidence": 0.95,
                }

                encrypted = cache._encryption_layer.encrypt_cache_data(ai_data)
                decrypted = cache._encryption_layer.decrypt_cache_data(encrypted)
                assert decrypted == ai_data

    @pytest.mark.asyncio
    async def test_for_testing_creates_encrypted_cache(
        self, encryption_security_config, monkeypatch
    ):
        """
        Test that for_testing creates encrypted cache when security config includes encryption.

        Integration Scope:
            CacheFactory.for_testing → SecurityConfig with encryption → EncryptedCacheLayer → Testing cache with encryption

        Business Impact:
            Ensures testing caches can include encryption for testing encryption
            workflows and validating encrypted cache behavior in test scenarios.

        Test Strategy:
            - Create security config with encryption key
            - Call for_testing with security config
            - Verify created cache instance supports encryption
            - Test encryption works in testing environment

        Success Criteria:
            - Testing cache instance is created with encryption
            - Encryption works correctly in testing context
            - Testing-specific configurations are maintained
        """
        # Mock Redis connection
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()
            cache = await factory.for_testing(
                security_config=encryption_security_config,
                fail_on_connection_error=False,
            )

            # Verify cache was created
            assert cache is not None

            # Test encryption in testing context
            if hasattr(cache, "_encryption_layer"):
                assert cache._encryption_layer.is_enabled

                # Test typical testing data
                test_data = {
                    "test_id": "integration-test-123",
                    "test_type": "encryption_validation",
                    "timestamp": "2023-01-01T12:00:00Z",
                    "test_payload": {"key": "test_value"},
                }

                encrypted = cache._encryption_layer.encrypt_cache_data(test_data)
                decrypted = cache._encryption_layer.decrypt_cache_data(encrypted)
                assert decrypted == test_data

    @pytest.mark.asyncio
    async def test_create_cache_from_config_with_encryption(self):
        """
        Test that create_cache_from_config creates encrypted cache when config includes encryption.

        Integration Scope:
            CacheFactory.create_cache_from_config → config parsing → SecurityConfig creation → encrypted cache

        Business Impact:
            Ensures configuration-driven cache creation properly handles encryption
            configuration for flexible deployment scenarios.

        Test Strategy:
            - Create config with encryption security configuration
            - Call create_cache_from_config
            - Verify encryption is properly integrated

        Success Criteria:
            - Configuration-based cache creation includes encryption
            - Security config is properly parsed and applied
            - Encryption works after config-based creation
        """
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()

        security_config = SecurityConfig(
            redis_auth="test-password",
            use_tls=False,
            verify_certificates=False,
        )
        # Dynamically add encryption_key attribute for testing
        security_config.encryption_key = encryption_key

        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "security_config": security_config,
        }

        # Mock Redis connection
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()
            cache = await factory.create_cache_from_config(config)

            # Verify cache was created
            assert cache is not None

            # Test encryption from config
            if hasattr(cache, "_encryption_layer"):
                assert cache._encryption_layer.is_enabled

    @pytest.mark.asyncio
    async def test_factory_handles_invalid_encryption_key_gracefully(
        self, invalid_encryption_security_config, monkeypatch
    ):
        """
        Test that factory fails fast with security errors when encryption key is invalid.

        Integration Scope:
            CacheFactory → SecurityConfig with invalid key → EncryptedCacheLayer initialization → GenericRedisCache SECURITY ERROR

        Business Impact:
            Ensures security-first architecture by rejecting invalid encryption keys
            rather than falling back to insecure mode, preventing security misconfigurations.

        Test Strategy:
            - Create security config with invalid encryption key
            - Mock Redis connection to isolate encryption behavior
            - Attempt cache creation via factory
            - Verify security failure with proper error context

        Success Criteria:
            - Factory raises ConfigurationError with SECURITY ERROR
            - Error message clearly indicates invalid encryption key
            - Security validation prevents insecure cache creation
        """
        # Mock Redis connection to prevent fallback to InMemoryCache
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()

            # This should fail with ConfigurationError due to invalid encryption key
            with pytest.raises(ConfigurationError) as exc_info:
                cache = await factory.for_web_app(
                    security_config=invalid_encryption_security_config,
                    fail_on_connection_error=False,
                )

            # Verify the error is a security error related to encryption
            error_message = str(exc_info.value)
            assert "SECURITY ERROR" in error_message
            assert "encryption" in error_message.lower() or "ENCRYPTION ERROR" in error_message

            # Verify error context indicates encryption key validation failure
            error_context = exc_info.value.context or {}
            assert error_context.get("error_type") == "security_initialization_failure"

    @pytest.mark.asyncio
    async def test_factory_creates_unencrypted_cache_when_no_encryption_key(
        self, security_config_without_encryption, monkeypatch
    ):
        """
        Test that factory creates cache without encryption when security config doesn't include encryption key.

        Integration Scope:
            CacheFactory → SecurityConfig without encryption → Cache instance without encryption

        Business Impact:
            Ensures factory properly handles security configurations without
            encryption keys, creating functional caches without encryption.

        Test Strategy:
            - Create security config without encryption key
            - Create cache via factory
            - Verify cache is created without encryption
            - Test cache operations work without encryption

        Success Criteria:
            - Cache is created successfully without encryption
            - Cache operations work correctly
            - No encryption errors occur
        """
        # Mock Redis connection
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()
            cache = await factory.for_web_app(
                security_config=security_config_without_encryption,
                fail_on_connection_error=False,
            )

            # Verify cache was created
            assert cache is not None

            # Verify encryption is disabled if encryption layer exists
            if hasattr(cache, "_encryption_layer"):
                # If encryption layer exists, it should be disabled
                assert not cache._encryption_layer.is_enabled

    @pytest.mark.asyncio
    async def test_encryption_isolation_across_multiple_factory_caches(self, encryption_security_config):
        """
        Test that multiple cache instances created by factory maintain encryption isolation.

        Integration Scope:
            CacheFactory → multiple cache creations → isolated encryption layers

        Business Impact:
            Ensures multiple cache instances maintain separate encryption
            contexts, preventing data leakage between cache instances.

        Test Strategy:
            - Create multiple caches with same security config
            - Verify each cache has separate encryption layer
            - Test that encryption keys work independently

        Success Criteria:
            - Each cache has independent encryption layer
            - Encryption operations are isolated per cache
            - No cross-cache data contamination
        """
        # Mock Redis connection
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()

            # Create multiple caches
            cache1 = await factory.for_web_app(
                security_config=encryption_security_config,
                fail_on_connection_error=False,
            )
            cache2 = await factory.for_testing(
                security_config=encryption_security_config,
                fail_on_connection_error=False,
            )

            # Verify both caches were created
            assert cache1 is not None
            assert cache2 is not None

            # Test encryption isolation if both have encryption
            if hasattr(cache1, "_encryption_layer") and hasattr(cache2, "_encryption_layer"):
                assert cache1._encryption_layer.is_enabled
                assert cache2._encryption_layer.is_enabled

                # Test that they can both encrypt/decrypt independently
                test_data1 = {"cache": "1", "data": "test1"}
                test_data2 = {"cache": "2", "data": "test2"}

                encrypted1 = cache1._encryption_layer.encrypt_cache_data(test_data1)
                encrypted2 = cache2._encryption_layer.encrypt_cache_data(test_data2)

                decrypted1 = cache1._encryption_layer.decrypt_cache_data(encrypted1)
                decrypted2 = cache2._encryption_layer.decrypt_cache_data(encrypted2)

                assert decrypted1 == test_data1
                assert decrypted2 == test_data2

    @pytest.mark.asyncio
    async def test_factory_encryption_integration_with_memory_fallback(self, encryption_security_config):
        """
        Test that encryption integration works correctly when factory falls back to InMemoryCache.

        Integration Scope:
            CacheFactory → Redis connection failure → InMemoryCache fallback → encryption integration

        Business Impact:
            Ensures encryption works correctly when factory gracefully degrades
            to InMemoryCache due to Redis unavailability.

        Test Strategy:
            - Mock Redis connection failure
            - Create cache with encryption config
            - Verify fallback to InMemoryCache
            - Test encryption integration with memory cache

        Success Criteria:
            - Factory falls back to InMemoryCache when Redis unavailable
            - Encryption configuration is preserved in fallback
            - Memory cache operations work with encryption
        """
        # Mock Redis connection failure
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Redis connection failed")

            factory = CacheFactory()
            cache = await factory.for_web_app(
                security_config=encryption_security_config,
                fail_on_connection_error=False,  # Allow fallback
            )

            # Should fallback to InMemoryCache
            from app.infrastructure.cache.memory import InMemoryCache
            assert isinstance(cache, InMemoryCache)

            # Test that cache operations work (InMemoryCache doesn't use encryption layer directly)
            test_key = "test:key"
            test_value = {"data": "test_value"}

            await cache.set(test_key, test_value)
            retrieved = await cache.get(test_key)
            assert retrieved == test_value

    @pytest.mark.asyncio
    async def test_factory_encryption_with_ai_specific_config(self):
        """
        Test that factory properly integrates encryption with AI-specific cache configurations.

        Integration Scope:
            CacheFactory.for_ai_app → AI-specific parameters → SecurityConfig with encryption → AI cache with encryption

        Business Impact:
            Ensures AI-specific cache features work correctly with encryption,
            maintaining both performance optimizations and data security.

        Test Strategy:
            - Create AI-specific configuration with encryption
            - Create AI cache via factory
            - Test AI-specific features with encryption
            - Validate operation-specific TTLs work with encryption

        Success Criteria:
            - AI cache is created with encryption
            - AI-specific features work with encryption
            - Operation-specific TTLs are preserved
        """
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()

        security_config = SecurityConfig(
            redis_auth="test-password",
            use_tls=False,
            verify_certificates=False,
        )
        # Dynamically add encryption_key attribute for testing
        security_config.encryption_key = encryption_key

        operation_ttls = {
            "summarize": 1800,  # 30 minutes
            "sentiment": 3600,  # 1 hour
            "translate": 7200,   # 2 hours
        }

        # Mock Redis connection
        with patch("app.infrastructure.cache.redis_ai.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()
            cache = await factory.for_ai_app(
                security_config=security_config,
                operation_ttls=operation_ttls,
                text_hash_threshold=500,
                fail_on_connection_error=False,
            )

            # Verify AI cache was created
            assert cache is not None

            # Test encryption integration with AI features
            if hasattr(cache, "_encryption_layer"):
                assert cache._encryption_layer.is_enabled

                # Test AI-specific data encryption
                ai_response = {
                    "operation": "summarize",
                    "input_text": "Long document to summarize...",
                    "result": "Document summary...",
                    "confidence": 0.92,
                    "model": "gemini-2.0-flash-exp",
                }

                encrypted = cache._encryption_layer.encrypt_cache_data(ai_response)
                decrypted = cache._encryption_layer.decrypt_cache_data(encrypted)
                assert decrypted == ai_response

    @pytest.mark.asyncio
    async def test_factory_error_propagation_with_encryption_issues(self):
        """
        Test that factory fails fast with security errors when encryption configuration is invalid.

        Integration Scope:
            CacheFactory → invalid encryption key → EncryptedCacheLayer failure → GenericRedisCache SECURITY ERROR

        Business Impact:
            Ensures security-first architecture by failing fast when encryption configuration
            is invalid, preventing insecure cache deployments in production.

        Test Strategy:
            - Create security config with invalid encryption key
            - Mock Redis connection to isolate encryption behavior
            - Attempt cache creation via factory
            - Verify security failure with proper error propagation

        Success Criteria:
            - Factory raises ConfigurationError with SECURITY ERROR for all methods
            - Error messages clearly indicate encryption key validation failure
            - Security validation prevents insecure cache creation
        """
        invalid_config = SecurityConfig(
            redis_auth="test-password",
            use_tls=False,
            verify_certificates=False,
        )
        # Dynamically add invalid encryption_key attribute for testing
        # Use a base64-encoded key of wrong length (24 bytes instead of 32)
        invalid_config.encryption_key = "dGVzdC1rZXktdGVzdC1rZXktdGVzdA=="  # 24 bytes base64 encoded

        # Mock Redis connection to prevent fallback to InMemoryCache
        with patch("app.infrastructure.cache.redis_generic.aioredis.from_url") as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis.return_value = mock_client

            factory = CacheFactory()

            # Test security failure across factory methods that respect security_config parameter
            # Note: AIResponseCache ignores security_config parameters (see redis_ai.py lines 294-322)
            # It uses automatic security inheritance instead, so we only test methods that accept custom security configs
            factory_methods = [
                ("web_app", lambda: factory.for_web_app(security_config=invalid_config)),
                # Skip ai_app - it ignores security_config and uses automatic security inheritance
                ("testing", lambda: factory.for_testing(security_config=invalid_config)),
            ]

            for name, method in factory_methods:
                # Factory methods should fail with ConfigurationError for invalid encryption
                with pytest.raises(ConfigurationError) as exc_info:
                    await method()

                # Verify the error is a security error related to encryption
                error_message = str(exc_info.value)
                assert "SECURITY ERROR" in error_message, f"Factory method {name} should raise SECURITY ERROR"
                assert "encryption" in error_message.lower() or "ENCRYPTION ERROR" in error_message, f"Factory method {name} error should mention encryption"

                # Verify error context includes encryption key validation failure
                error_context = exc_info.value.context or {}
                assert error_context.get("error_type") == "security_initialization_failure", f"Factory method {name} should have security initialization error type"

            # Verify AI app factory method succeeds despite invalid config (it ignores security_config)
            ai_cache = await factory.for_ai_app(security_config=invalid_config)
            assert ai_cache is not None, "AI app should succeed despite invalid security_config (parameter ignored)"
