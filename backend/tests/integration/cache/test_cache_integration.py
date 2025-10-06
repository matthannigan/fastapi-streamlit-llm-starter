"""
Integration tests for cache infrastructure components.

This test suite verifies cross-component interactions using real implementations
instead of extensive mocking. Tests demonstrate how different cache components
work together to provide complete functionality.

Coverage Focus:
    - Factory + Cache + Monitor integration
    - Settings + Factory integration
    - Cache + Key Generator + Performance Monitor integration
    - End-to-end cache workflows with real components

External Dependencies:
    Uses real components with graceful degradation for Redis unavailability.
    No internal mocking - only system boundary mocking where necessary.
"""

import asyncio
from typing import Any, Dict

import pytest

from app.core.exceptions import InfrastructureError
from app.infrastructure.cache.factory import CacheFactory

# Mark all tests in this module to run serially (not in parallel)
# These tests manipulate environment state and fail intermittently in parallel
pytestmark = pytest.mark.no_parallel
from app.infrastructure.cache.key_generator import CacheKeyGenerator
from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestCacheFactoryIntegration:
    """
    Integration tests for CacheFactory with other components.

    Tests real component interactions rather than mocked dependencies.
    """

    @pytest.mark.asyncio
    async def test_factory_creates_cache_with_monitoring_integration(self):
        """
        Test complete factory workflow with performance monitoring integration.

        Verifies:
            Factory creates cache with real monitoring component integration

        Business Impact:
            Ensures end-to-end monitoring functionality works correctly

        Integration Points:
            - CacheFactory -> Cache creation
            - Cache -> Performance monitoring integration
            - Monitor -> Metrics collection during operations
        """
        # Given: Real factory and monitor components
        factory = CacheFactory()
        monitor = CachePerformanceMonitor()

        # When: Factory creates cache with monitoring
        cache = await factory.for_testing(
            performance_monitor=monitor, use_memory_cache=True
        )

        # Then: Integration should work end-to-end
        assert cache is not None

        # Test actual monitoring integration through operations
        test_key = "integration:factory:monitoring"
        test_value = {"integration_test": True, "component": "factory"}

        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)

        assert retrieved_value == test_value

        # Clean up
        await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_factory_with_settings_creates_configured_cache(self, test_settings):
        """
        Test factory integration with real Settings configuration.

        Verifies:
            Factory respects actual configuration from Settings

        Integration Points:
            - Settings -> Configuration loading
            - Factory -> Configuration application
            - Cache -> Configured behavior
        """
        # Given: Real settings and factory
        factory = CacheFactory()

        # When: Factory uses real settings configuration
        cache = await factory.for_web_app(
            settings=test_settings,
            fail_on_connection_error=False,  # Allow graceful degradation
        )

        # Then: Cache should be created with settings-based configuration
        assert cache is not None

        # Test cache functionality with settings-derived configuration
        test_key = "integration:settings:config"
        test_value = {"settings_integration": True}

        await cache.set(test_key, test_value)
        result = await cache.get(test_key)

        assert result == test_value

        # Clean up
        await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_factory_testing_database_isolation_with_testcontainers(
        self, secure_redis_container, monkeypatch
    ):
        """
        Test factory creates cache with proper test database isolation using secure Redis.

        Verifies:
            Factory.for_testing() uses Redis database 15 for test isolation when using default URL
            Factory properly handles secure Redis connections with TLS and authentication

        Business Impact:
            Ensures test data isolation preventing interference between test runs
            Validates security configuration works correctly with factory methods

        Integration Points:
            - CacheFactory -> Test cache creation with database isolation
            - Secure Testcontainer -> TLS-enabled Redis with authentication
            - Security configuration -> Proper TLS and auth handling
            - Default database behavior -> Standard test database isolation
        """
        from cryptography.fernet import Fernet

        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.security import SecurityConfig

        # Set required security environment variables
        # Generate proper Fernet key for encryption
        test_encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)
        monkeypatch.setenv("REDIS_PASSWORD", secure_redis_container["password"])
        monkeypatch.setenv("ENVIRONMENT", "testing")

        # Create security configuration
        # Note: encryption_key is handled via environment variable (set above)
        security_config = SecurityConfig(
            redis_auth=secure_redis_container["password"],
            use_tls=True,
            tls_ca_path=secure_redis_container["ca_cert"],
            verify_certificates=False,  # Self-signed test certificates
        )

        try:
            # Get secure connection URL
            secure_url = secure_redis_container["url"]

            # Test 1: Use default behavior (factory adds /15 automatically)
            factory = CacheFactory()
            cache_with_default_url = await factory.for_testing(
                redis_url=secure_url,  # Secure rediss:// URL, no database specified
                security_config=security_config,
            )

            # Verify we got a real Redis cache (not InMemoryCache fallback)
            assert isinstance(
                cache_with_default_url, GenericRedisCache
            ), f"Expected GenericRedisCache, got {type(cache_with_default_url)}"

            # Prove isolation works with real operations (encrypted)
            test_key = "test:db_isolation_default"
            await cache_with_default_url.set(test_key, "isolated_data_default")
            assert await cache_with_default_url.get(test_key) == "isolated_data_default"

            # Cleanup
            await cache_with_default_url.delete(test_key)

            # Test 2: Explicitly specify database 15 (should behave the same)
            secure_url_with_db = (
                secure_url.replace("/0", "/15")
                if "/0" in secure_url
                else f"{secure_url}/15"
            )
            cache_with_explicit_db = await factory.for_testing(
                redis_url=secure_url_with_db, security_config=security_config
            )

            # Verify we got a real Redis cache
            assert isinstance(
                cache_with_explicit_db, GenericRedisCache
            ), f"Expected GenericRedisCache, got {type(cache_with_explicit_db)}"

            # Prove explicit database isolation works
            test_key_explicit = "test:db_isolation_explicit"
            await cache_with_explicit_db.set(
                test_key_explicit, "isolated_data_explicit"
            )
            assert (
                await cache_with_explicit_db.get(test_key_explicit)
                == "isolated_data_explicit"
            )

            # Cleanup
            await cache_with_explicit_db.delete(test_key_explicit)

            # Verify both caches are functional and isolated
            assert (
                cache_with_default_url.redis is not None
            ), "Redis connection should be established for default URL"
            assert (
                cache_with_explicit_db.redis is not None
            ), "Redis connection should be established for explicit URL"

        except Exception as e:
            # Better error reporting for debugging
            import logging

            logging.getLogger(__name__).error(f"Test failed with secure Redis: {e}")
            raise


class TestCacheKeyGeneratorIntegration:
    """
    Integration tests for CacheKeyGenerator with cache and monitoring.

    Tests real component interactions in key generation workflows.
    """

    @pytest.mark.asyncio
    async def test_key_generator_with_cache_and_monitoring_integration(self):
        """
        Test complete key generation workflow with cache and monitoring.

        Verifies:
            Key generator integrates properly with cache operations and monitoring

        Business Impact:
            Ensures key generation, caching, and monitoring work together correctly

        Integration Points:
            - KeyGenerator -> Key generation with monitoring
            - Cache -> Key-based operations
            - Monitor -> Key generation metrics
        """
        # Given: Real components integrated together
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(performance_monitor=monitor)
        factory = CacheFactory()
        cache = await factory.for_testing(
            performance_monitor=monitor, use_memory_cache=True
        )

        # When: Using integrated workflow
        text = "Integration test for key generation and caching"
        operation = "test_integration"
        options = {"integration": True}

        # Generate key with monitoring
        cache_key = key_generator.generate_cache_key(text, operation, options)

        # Use key with cache (also monitored)
        test_value = {"text": text, "operation": operation, "generated_key": cache_key}

        await cache.set(cache_key, test_value)
        retrieved_value = await cache.get(cache_key)

        # Then: End-to-end workflow should work correctly
        assert retrieved_value == test_value
        # Key should contain the operation (actual key format may vary)
        assert operation in cache_key

        # Verify key exists
        key_exists = await cache.exists(cache_key)
        assert key_exists is True

        # Clean up
        await cache.delete(cache_key)

        # Verify cleanup
        exists_after_delete = await cache.exists(cache_key)
        assert exists_after_delete is False


class TestEndToEndCacheWorkflows:
    """
    End-to-end integration tests for complete cache workflows.

    Tests realistic usage patterns with multiple integrated components.
    """

    @pytest.mark.asyncio
    async def test_complete_ai_cache_workflow_integration(self):
        """
        Test complete AI cache workflow with all components integrated.

        Verifies:
            All AI cache components work together in realistic workflows

        Business Impact:
            Ensures AI cache functionality works end-to-end in production scenarios

        Integration Points:
            - Factory -> AI cache creation
            - KeyGenerator -> AI-specific key generation
            - Cache -> AI response storage and retrieval
            - Monitor -> AI cache performance tracking
        """
        # Given: Complete AI cache setup with real components
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(
            performance_monitor=monitor, text_hash_threshold=1000
        )
        factory = CacheFactory()

        # Create AI cache with monitoring
        cache = await factory.for_ai_app(
            performance_monitor=monitor, fail_on_connection_error=False
        )

        # When: Performing complete AI cache workflow
        # Simulate AI text processing workflow
        texts = [
            "Short text for AI processing",
            "Much longer text that should trigger hashing behavior in the key generator "
            * 20,
            "Another AI processing request with different content",
        ]

        operations = ["summarize", "sentiment", "key_points"]

        # Process multiple AI requests
        for i, text in enumerate(texts):
            operation = operations[i % len(operations)]

            # Generate AI-appropriate cache key
            cache_key = key_generator.generate_cache_key(text, operation, {})

            # Store AI response
            ai_response = {
                "operation": operation,
                "text_length": len(text),
                "result": f"AI {operation} result for text {i+1}",
                "metadata": {"processed_at": "2023-01-01", "model": "test"},
            }

            await cache.set(cache_key, ai_response, ttl=3600)

            # Retrieve and verify
            retrieved = await cache.get(cache_key)
            assert retrieved == ai_response
            assert await cache.exists(cache_key) is True

        # Clean up all test data
        for i, text in enumerate(texts):
            operation = operations[i % len(operations)]
            cache_key = key_generator.generate_cache_key(text, operation, {})
            await cache.delete(cache_key)

            # Verify cleanup
            assert await cache.exists(cache_key) is False

    @pytest.mark.asyncio
    async def test_cache_fallback_behavior_integration(self):
        """
        Test cache fallback behavior integration across components.

        Verifies:
            Graceful degradation works across all integrated components

        Business Impact:
            Ensures system resilience when external dependencies are unavailable

        Integration Points:
            - Factory -> Fallback cache creation
            - Settings -> Fallback configuration
            - Components -> Graceful degradation behavior
        """
        # Given: Factory configured for fallback behavior
        factory = CacheFactory()

        # When: Creating cache with fallback enabled
        cache = await factory.for_web_app(
            redis_url="redis://invalid-host:99999",  # Intentionally invalid
            fail_on_connection_error=False,  # Enable graceful fallback
        )

        # Then: Should get fallback cache that works normally
        assert cache is not None

        # Test normal operations work with fallback
        test_key = "integration:fallback:test"
        test_value = {"fallback": True, "working": True}

        await cache.set(test_key, test_value)
        retrieved = await cache.get(test_key)

        assert retrieved == test_value
        assert await cache.exists(test_key) is True

        # Clean up
        await cache.delete(test_key)
        assert await cache.exists(test_key) is False


class TestCacheComponentInteroperability:
    """
    Shared Contract Tests for cache component interoperability and compatibility.

    Verifies different cache implementations can be used interchangeably by testing
    actual cache instances rather than factory method variations. This implements
    the "Shared Contract Tests" pattern to ensure all cache implementations adhere
    to the same behavioral contract.

    This test suite runs the exact same test code against both a high-fidelity
    Redis instance (using Testcontainers) and a fast in-memory fake (using FakeRedis).
    This guarantees that any cache backend will adhere to the exact same behavioral contract.

    Testing Approach:
        - Direct GenericRedisCache instantiation for focused contract testing
        - Real Redis via Testcontainers for complete fidelity
        - FakeRedis for fast, Redis-compatible behavior without external dependencies
        - Identical test logic ensures true behavioral equivalence
    """

    # Note: _create_fakeredis_backed_cache helper removed
    # FakeRedis integration will be added in Phase 2 with encryption patching
    # For now, all shared contract tests use only secure real Redis testcontainer

    @pytest.fixture
    async def cache_instances_via_factory(self, secure_redis_container, monkeypatch):
        """
        Alternative fixture demonstrating factory-based cache instance creation with security.

        This approach uses CacheFactory.for_testing() to create cache instances
        using the secure Redis testcontainer. This provides broader scope testing
        that includes the factory's assembly logic with proper security configuration.

        Use this fixture when you want to test:
        - The complete service assembly process via CacheFactory
        - Factory configuration handling and parameter mapping with security
        - Integration between factory, cache, monitoring, and security components

        Note: FakeRedis variant will be added in Phase 2 with encryption patching.
        """
        from cryptography.fernet import Fernet

        from app.infrastructure.cache.factory import CacheFactory
        from app.infrastructure.cache.security import SecurityConfig

        # Set required environment variables for security
        # Generate proper Fernet key for encryption
        test_encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)
        monkeypatch.setenv("REDIS_PASSWORD", secure_redis_container["password"])
        monkeypatch.setenv("ENVIRONMENT", "testing")

        cache_instances = []

        try:
            # Create factory for service assembly
            factory = CacheFactory()

            # Create security config for testing
            # Note: encryption_key is handled via environment variable (set above)
            security_config = SecurityConfig(
                redis_auth=secure_redis_container["password"],
                use_tls=True,
                tls_ca_path=secure_redis_container["ca_cert"],
                verify_certificates=False,  # Self-signed test certificates
            )

            # 1. Real secure Redis cache via factory
            real_redis_cache = await factory.for_testing(
                redis_url=secure_redis_container["url"],
                enable_l1_cache=False,
                fail_on_connection_error=True,
                security_config=security_config,
            )

            cache_instances = [
                ("factory_real_redis", real_redis_cache)
                # Phase 2 TODO: Add factory_fake_redis with encryption patched
            ]

            yield cache_instances

        finally:
            # Cleanup: Clear caches
            for cache_name, cache in cache_instances:
                try:
                    if hasattr(cache, "clear"):
                        await cache.clear()
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).warning(
                        f"Cache cleanup error for {cache_name}: {e}"
                    )

    # Note: cache_instances fixture now provided by conftest.py
    # Uses secure Redis testcontainer with TLS, authentication, and encryption
    # Removed local fixture definition to use global secure fixture

    @pytest.mark.asyncio
    async def test_cache_shared_contract_basic_operations(self, cache_instances):
        """
        Shared contract test for basic cache operations across implementations.

        Verifies that all cache implementations provide identical behavior for
        the core CacheInterface contract: get, set, exists, delete operations.

        This test ensures behavioral equivalence between different cache backends,
        making them truly interchangeable in production applications.

        Contract Verification:
            - set() stores values correctly
            - get() retrieves exact values
            - exists() reports key presence accurately
            - delete() removes keys completely
            - All operations maintain consistent behavior across implementations
        """
        for cache_name, cache in cache_instances:
            # Given: A cache implementation and test data
            test_key = f"contract:basic:{cache_name}"
            test_value = {"cache_type": cache_name, "contract_test": True}

            # When: Performing basic operations
            await cache.set(test_key, test_value)
            retrieved = await cache.get(test_key)
            exists_before_delete = await cache.exists(test_key)

            await cache.delete(test_key)
            exists_after_delete = await cache.exists(test_key)
            retrieved_after_delete = await cache.get(test_key)

            # Then: All implementations must behave identically
            assert retrieved == test_value, f"get() failed for {cache_name}"
            assert (
                exists_before_delete is True
            ), f"exists() before delete failed for {cache_name}"
            assert (
                exists_after_delete is False
            ), f"exists() after delete failed for {cache_name}"
            assert (
                retrieved_after_delete is None
            ), f"get() after delete failed for {cache_name}"

    @pytest.mark.asyncio
    async def test_cache_shared_contract_ttl_behavior(self, cache_instances):
        """
        Shared contract test for TTL (time-to-live) behavior across implementations.

        Verifies that all cache implementations handle TTL consistently:
        - Keys with TTL are stored correctly
        - TTL values are respected during storage
        - Key existence behavior is consistent

        Note: This test focuses on TTL setting behavior rather than expiration
        timing to avoid test flakiness while still verifying contract compliance.
        """
        for cache_name, cache in cache_instances:
            # Given: A cache implementation and TTL test data
            test_key = f"contract:ttl:{cache_name}"
            test_value = {"ttl_test": True, "cache_type": cache_name}
            ttl_seconds = 3600

            # When: Setting value with TTL
            await cache.set(test_key, test_value, ttl=ttl_seconds)
            retrieved = await cache.get(test_key)
            exists = await cache.exists(test_key)

            # Then: All implementations must store TTL values correctly
            assert retrieved == test_value, f"TTL set/get failed for {cache_name}"
            assert exists is True, f"TTL exists check failed for {cache_name}"

            # Cleanup
            await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_cache_shared_contract_data_types(self, cache_instances):
        """
        Shared contract test for data type handling across implementations.

        Verifies that all cache implementations handle various Python data types
        consistently, ensuring serialization/deserialization behavior is equivalent.
        """
        test_data = {
            "string": "test string value",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3, "mixed", {"nested": True}],
            "dict": {
                "nested": {"deeply": {"nested": "value"}},
                "numbers": [1, 2, 3],
                "mixed": True,
            },
        }

        for cache_name, cache in cache_instances:
            for data_type, test_value in test_data.items():
                # Given: A cache implementation and various data types
                test_key = f"contract:types:{cache_name}:{data_type}"

                # When: Storing and retrieving different data types
                await cache.set(test_key, test_value)
                retrieved = await cache.get(test_key)

                # Then: All implementations must preserve data integrity
                assert (
                    retrieved == test_value
                ), f"Data type {data_type} failed for {cache_name}"

                # Cleanup
                await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_cache_shared_contract_interface_compliance(self, cache_instances):
        """
        Shared contract test for CacheInterface compliance across implementations.

        Verifies that all cache implementations expose the required interface methods
        and that these methods are callable with the expected signatures.
        """
        required_methods = ["get", "set", "delete", "exists"]

        for cache_name, cache in cache_instances:
            # Then: All implementations must expose required interface methods
            for method_name in required_methods:
                assert hasattr(
                    cache, method_name
                ), f"Method {method_name} missing from {cache_name}"
                assert callable(
                    getattr(cache, method_name)
                ), f"Method {method_name} not callable in {cache_name}"

    @pytest.mark.asyncio
    async def test_factory_assembled_cache_shared_contract(
        self, cache_instances_via_factory
    ):
        """
        Demonstration test using the factory-based fixture for broader scope testing.

        This test demonstrates the alternative approach that includes factory assembly
        logic in the contract testing. It tests the same behavioral contract but with
        broader coverage of the service creation pipeline.

        Use this approach when you want to validate that the CacheFactory correctly
        assembles cache services that adhere to the same behavioral contracts.
        """
        for cache_name, cache in cache_instances_via_factory:
            # Given: A factory-assembled cache implementation and test data
            test_key = f"factory_contract:basic:{cache_name}"
            test_value = {
                "cache_type": cache_name,
                "assembled_by": "factory",
                "contract_test": True,
            }

            # When: Performing basic operations on factory-assembled cache
            await cache.set(test_key, test_value)
            retrieved = await cache.get(test_key)
            exists_before_delete = await cache.exists(test_key)

            await cache.delete(test_key)
            exists_after_delete = await cache.exists(test_key)
            retrieved_after_delete = await cache.get(test_key)

            # Then: Factory-assembled caches must behave identically to directly instantiated ones
            assert retrieved == test_value, f"Factory get() failed for {cache_name}"
            assert (
                exists_before_delete is True
            ), f"Factory exists() before delete failed for {cache_name}"
            assert (
                exists_after_delete is False
            ), f"Factory exists() after delete failed for {cache_name}"
            assert (
                retrieved_after_delete is None
            ), f"Factory get() after delete failed for {cache_name}"
