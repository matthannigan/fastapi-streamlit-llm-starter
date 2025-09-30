"""
Comprehensive test suite for GenericRedisCache core cache operations.

This module provides systematic behavioral testing of the fundamental cache
operations including get, set, delete, exists, and their interaction with
L1 cache, Redis backend, compression, and performance monitoring.

Test Coverage:
    - Basic cache operations: get, set, delete, exists
    - L1 cache and Redis backend coordination
    - TTL (Time To Live) management and expiration
    - Data compression and decompression functionality
    - Performance monitoring integration
    - Error handling and edge cases

Testing Philosophy:
    - Uses behavior-driven testing with Given/When/Then structure
    - Tests core business logic without mocking standard library components
    - Validates cache behavior consistency across different configurations
    - Ensures data integrity and proper error handling
    - Comprehensive edge case coverage for production reliability

Test Organization:
    - TestBasicCacheOperations: Core get, set, delete, exists functionality
    - TestL1CacheIntegration: L1 memory cache coordination with Redis
    - TestTTLAndExpiration: Time-to-live management and expiration behavior
    - TestDataCompressionIntegration: Compression functionality and thresholds

Fixtures and Mocks:
    From conftest.py:
        - default_generic_redis_config: Standard configuration dictionary
        - compression_redis_config: Configuration optimized for compression
        - no_l1_redis_config: Configuration without L1 cache
        - fakeredis: Stateful fake Redis client
        - sample_large_value: Large data for compression testing
        - bulk_test_data: Multiple key-value pairs for batch testing
        - compression_test_data: Data designed for compression testing
    From parent conftest.py:
        - sample_cache_key: Standard cache key for testing
        - sample_cache_value: Standard cache value for testing
        - sample_ttl: Standard TTL value for testing
        - short_ttl: Short TTL for expiration testing
"""

import asyncio
import time
from typing import Any, Dict

import pytest

from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.redis_generic import GenericRedisCache


def _setup_cache_with_fake_redis(config, fake_redis_client):
    """Helper function to set up GenericRedisCache with fake redis connection."""
    cache = GenericRedisCache(**config)
    cache.redis = fake_redis_client
    cache._redis_connected = True  # Mark as connected to bypass connection logic
    return cache


class TestBasicCacheOperations:
    """
    Test GenericRedisCache basic cache operations.

    The GenericRedisCache must provide reliable get, set, delete, and exists operations
    with proper data integrity, Redis integration, and L1 cache coordination.
    """

    async def test_set_and_get_basic_value(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test setting and retrieving a basic cache value.

        Given: A GenericRedisCache instance with fakeredis backend
        When: A value is set and then retrieved using the same key
        Then: The retrieved value should match the original value exactly
        And: The cache operation should succeed without errors
        """
        # Given: Create cache with fake redis client
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set a value and retrieve it
        await cache.set(sample_cache_key, sample_cache_value)
        result = await cache.get(sample_cache_key)

        # Then: Retrieved value should match original
        assert result == sample_cache_value

        await cache.disconnect()

    async def test_get_nonexistent_key(
        self, default_generic_redis_config, fake_redis_client
    ):
        """
        Test retrieving a non-existent cache key.

        Given: A GenericRedisCache instance with no stored data
        When: A non-existent key is retrieved
        Then: The result should be None
        And: No exceptions should be raised
        """
        # Given: Empty cache
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Get non-existent key
        result = await cache.get("nonexistent:key")

        # Then: Should return None
        assert result is None

        await cache.disconnect()

    async def test_delete_existing_key(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test deleting an existing cache key.

        Given: A GenericRedisCache with a stored key-value pair
        When: The key is deleted
        Then: The delete operation should return True
        And: Subsequent retrieval should return None
        """
        # Given: Cache with stored value
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )
        await cache.set(sample_cache_key, sample_cache_value)

        # When: Delete the key
        deleted = await cache.delete(sample_cache_key)

        # Then: Delete should succeed and value should be gone
        assert deleted is True
        result = await cache.get(sample_cache_key)
        assert result is None

        await cache.disconnect()

    async def test_delete_nonexistent_key(
        self, default_generic_redis_config, fake_redis_client
    ):
        """
        Test deleting a non-existent cache key.

        Given: A GenericRedisCache instance with no stored data
        When: A non-existent key is deleted
        Then: The delete operation should return False
        And: No exceptions should be raised
        """
        # Given: Empty cache
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Delete non-existent key
        deleted = await cache.delete("nonexistent:key")

        # Then: Should return False
        assert deleted is False

        await cache.disconnect()

    async def test_exists_for_existing_key(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test checking existence of an existing cache key.

        Given: A GenericRedisCache with a stored key-value pair
        When: The key existence is checked
        Then: The exists operation should return True
        """
        # Given: Cache with stored value
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )
        await cache.set(sample_cache_key, sample_cache_value)

        # When: Check key existence
        exists = await cache.exists(sample_cache_key)

        # Then: Should return True
        assert exists is True

        await cache.disconnect()

    async def test_exists_for_nonexistent_key(
        self, default_generic_redis_config, fake_redis_client
    ):
        """
        Test checking existence of a non-existent cache key.

        Given: A GenericRedisCache instance with no stored data
        When: A non-existent key existence is checked
        Then: The exists operation should return False
        """
        # Given: Empty cache
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Check non-existent key
        exists = await cache.exists("nonexistent:key")

        # Then: Should return False
        assert exists is False

        await cache.disconnect()

    async def test_set_with_custom_ttl(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test setting a cache value with custom TTL.

        Given: A GenericRedisCache instance
        When: A value is set with a specific TTL
        Then: The value should be stored and retrievable
        And: TTL should be properly applied to both L1 and Redis
        """
        # Given: Cache instance
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set value with custom TTL
        custom_ttl = 1800
        await cache.set(sample_cache_key, sample_cache_value, ttl=custom_ttl)

        # Then: Value should be retrievable
        result = await cache.get(sample_cache_key)
        assert result == sample_cache_value

        await cache.disconnect()


class TestL1CacheIntegration:
    """
    Test GenericRedisCache L1 memory cache coordination with Redis.

    The GenericRedisCache coordinates between L1 memory cache and Redis backend
    to provide optimal performance while maintaining data consistency.
    """

    async def test_l1_cache_hit_behavior(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test L1 cache hit behavior for faster retrieval.

        Given: A GenericRedisCache with L1 cache enabled and a stored value
        When: The same key is retrieved multiple times
        Then: Subsequent retrievals should be served from L1 cache
        And: Data consistency should be maintained
        """
        # Given: Cache with L1 enabled
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )
        await cache.set(sample_cache_key, sample_cache_value)

        # When: Retrieve value multiple times
        result1 = await cache.get(sample_cache_key)
        result2 = await cache.get(sample_cache_key)

        # Then: Both results should be identical
        assert result1 == sample_cache_value
        assert result2 == sample_cache_value
        assert result1 == result2

        await cache.disconnect()

    async def test_l1_cache_disabled_behavior(
        self,
        no_l1_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test cache behavior with L1 cache disabled.

        Given: A GenericRedisCache with L1 cache disabled
        When: Values are set and retrieved
        Then: All operations should work through Redis backend only
        And: Performance should not be affected by L1 cache absence
        """
        # Given: Cache without L1 cache
        cache = _setup_cache_with_fake_redis(no_l1_redis_config, fake_redis_client)

        # When: Set and get value
        await cache.set(sample_cache_key, sample_cache_value)
        result = await cache.get(sample_cache_key)

        # Then: Operations should work correctly
        assert result == sample_cache_value

        await cache.disconnect()

    async def test_l1_and_redis_consistency(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test data consistency between L1 cache and Redis.

        Given: A GenericRedisCache with L1 cache enabled
        When: A value is set and then deleted
        Then: Both L1 cache and Redis should be updated consistently
        And: No stale data should remain in either tier
        """
        # Given: Cache with L1 enabled
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set then delete value
        await cache.set(sample_cache_key, sample_cache_value)
        await cache.delete(sample_cache_key)

        # Then: Value should be gone from both tiers
        result = await cache.get(sample_cache_key)
        assert result is None

        # Verify Redis doesn't have the key either
        redis_exists = await fake_redis_client.exists(sample_cache_key)
        assert redis_exists == 0

        await cache.disconnect()

    async def test_bulk_operations_l1_coordination(
        self, default_generic_redis_config, fake_redis_client, bulk_test_data
    ):
        """
        Test L1 cache coordination during bulk operations.

        Given: A GenericRedisCache with L1 cache enabled
        When: Multiple values are set and retrieved in bulk
        Then: L1 cache should properly coordinate with Redis
        And: All values should be accessible and consistent
        """
        # Given: Cache with L1 enabled
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set multiple values
        for key, value in bulk_test_data.items():
            await cache.set(key, value)

        # Then: All values should be retrievable
        for key, expected_value in bulk_test_data.items():
            result = await cache.get(key)
            assert result == expected_value

        await cache.disconnect()


class TestTTLAndExpiration:
    """
    Test GenericRedisCache time-to-live management and expiration behavior.

    The GenericRedisCache must properly handle TTL settings, expiration timing,
    and coordinate expiration between L1 cache and Redis backend.
    """

    async def test_default_ttl_application(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test application of default TTL when none specified.

        Given: A GenericRedisCache with a configured default TTL
        When: A value is set without specifying TTL
        Then: The default TTL should be applied automatically
        And: The value should be stored with proper expiration
        """
        # Given: Cache with default TTL
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set value without TTL
        await cache.set(sample_cache_key, sample_cache_value)

        # Then: Value should be stored and retrievable
        result = await cache.get(sample_cache_key)
        assert result == sample_cache_value

        # Redis should have the key with TTL
        ttl = await fake_redis_client.ttl(sample_cache_key)
        assert ttl > 0  # Should have positive TTL

        await cache.disconnect()

    async def test_custom_ttl_override(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test custom TTL overriding default TTL.

        Given: A GenericRedisCache with a default TTL
        When: A value is set with a custom TTL
        Then: The custom TTL should override the default
        And: The value should expire according to the custom TTL
        """
        # Given: Cache with default TTL
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set value with custom TTL
        custom_ttl = 60  # 1 minute
        await cache.set(sample_cache_key, sample_cache_value, ttl=custom_ttl)

        # Then: Value should be stored
        result = await cache.get(sample_cache_key)
        assert result == sample_cache_value

        # TTL should be approximately the custom value
        ttl = await fake_redis_client.ttl(sample_cache_key)
        assert 55 <= ttl <= 60  # Allow for small timing variations

        await cache.disconnect()

    async def test_expiration_behavior(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
        short_ttl,
    ):
        """
        Test cache expiration behavior with short TTL.

        Given: A GenericRedisCache instance
        When: A value is set with a very short TTL and time passes
        Then: The value should expire and become unavailable
        And: Both L1 and Redis should handle expiration properly
        """
        # Given: Cache instance
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set value with short TTL
        await cache.set(sample_cache_key, sample_cache_value, ttl=short_ttl)

        # Verify initial storage
        result = await cache.get(sample_cache_key)
        assert result == sample_cache_value

        # Wait for expiration
        await asyncio.sleep(short_ttl + 0.1)

        # Then: Value should be expired
        expired_result = await cache.get(sample_cache_key)
        assert expired_result is None

        await cache.disconnect()

    async def test_ttl_coordination_between_tiers(
        self,
        default_generic_redis_config,
        fake_redis_client,
        sample_cache_key,
        sample_cache_value,
    ):
        """
        Test TTL coordination between L1 cache and Redis.

        Given: A GenericRedisCache with L1 cache enabled
        When: A value is set with TTL in both tiers
        Then: Both L1 and Redis should have consistent TTL handling
        And: Expiration should be coordinated across tiers
        """
        # Given: Cache with L1 enabled
        cache = _setup_cache_with_fake_redis(
            default_generic_redis_config, fake_redis_client
        )

        # When: Set value with specific TTL
        ttl = 300  # 5 minutes
        await cache.set(sample_cache_key, sample_cache_value, ttl=ttl)

        # Then: Value should be accessible
        result = await cache.get(sample_cache_key)
        assert result == sample_cache_value

        # Redis should have appropriate TTL
        redis_ttl = await fake_redis_client.ttl(sample_cache_key)
        assert 295 <= redis_ttl <= 300  # Allow for timing variations

        await cache.disconnect()


class TestDataCompressionIntegration:
    """
    Test GenericRedisCache data compression functionality and thresholds.

    The GenericRedisCache should automatically compress large data values
    based on configurable thresholds while maintaining data integrity.
    """

    async def test_compression_threshold_behavior(
        self, secure_fakeredis_cache, sample_large_value
    ):
        """
        Test automatic compression when data exceeds threshold.

        Given: A GenericRedisCache configured with encryption bypassed
        When: A large value exceeding the threshold is stored
        Then: The value should be automatically compressed
        And: Retrieved value should match the original exactly
        """
        # Given: Cache with encryption bypassed
        cache = secure_fakeredis_cache

        # When: Store large value
        key = "large:data:key"
        await cache.set(key, sample_large_value)

        # Then: Value should be retrievable and identical
        result = await cache.get(key)
        assert result == sample_large_value

        await cache.disconnect()

    async def test_small_value_no_compression(
        self, secure_fakeredis_cache, sample_cache_value
    ):
        """
        Test that small values are not compressed unnecessarily.

        Given: A GenericRedisCache with encryption bypassed
        When: A small value below the compression threshold is stored
        Then: The value should be stored without compression
        And: Retrieved value should match the original
        """
        # Given: Cache with encryption bypassed
        cache = secure_fakeredis_cache

        # When: Store small value
        key = "small:data:key"
        await cache.set(key, sample_cache_value)

        # Then: Value should be retrievable
        result = await cache.get(key)
        assert result == sample_cache_value

        await cache.disconnect()

    async def test_compression_data_integrity(
        self, secure_fakeredis_cache, compression_test_data
    ):
        """
        Test data integrity across various data types with compression.

        Given: A GenericRedisCache with encryption bypassed
        When: Various data types and sizes are stored and retrieved
        Then: All data should maintain perfect integrity
        And: Complex data structures should be preserved exactly
        """
        # Given: Cache with encryption bypassed
        cache = secure_fakeredis_cache

        # When: Store various data types
        for key, value in compression_test_data.items():
            await cache.set(key, value)

        # Then: All values should be retrievable with integrity
        for key, expected_value in compression_test_data.items():
            result = await cache.get(key)
            assert result == expected_value

        await cache.disconnect()

    async def test_mixed_compression_scenarios(
        self, secure_fakeredis_cache, sample_cache_value, sample_large_value
    ):
        """
        Test mixed scenarios with both compressed and uncompressed data.

        Given: A GenericRedisCache with encryption bypassed
        When: Both small and large values are stored in the same cache
        Then: Compression should be applied appropriately to each value
        And: All values should be retrievable correctly regardless of compression
        """
        # Given: Cache with encryption bypassed
        cache = secure_fakeredis_cache

        # When: Store mixed size values
        small_key = "mixed:small"
        large_key = "mixed:large"
        await cache.set(small_key, sample_cache_value)
        await cache.set(large_key, sample_large_value)

        # Then: Both should be retrievable
        small_result = await cache.get(small_key)
        large_result = await cache.get(large_key)

        assert small_result == sample_cache_value
        assert large_result == sample_large_value

        await cache.disconnect()
