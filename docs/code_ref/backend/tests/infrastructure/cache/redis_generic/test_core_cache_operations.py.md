---
sidebar_label: test_core_cache_operations
---

# Comprehensive test suite for GenericRedisCache core cache operations.

  file_path: `backend/tests/infrastructure/cache/redis_generic/test_core_cache_operations.py`

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

## TestBasicCacheOperations

Test GenericRedisCache basic cache operations.

The GenericRedisCache must provide reliable get, set, delete, and exists operations
with proper data integrity, Redis integration, and L1 cache coordination.

### test_set_and_get_basic_value()

```python
async def test_set_and_get_basic_value(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test setting and retrieving a basic cache value.

Given: A GenericRedisCache instance with fakeredis backend
When: A value is set and then retrieved using the same key
Then: The retrieved value should match the original value exactly
And: The cache operation should succeed without errors

### test_get_nonexistent_key()

```python
async def test_get_nonexistent_key(self, default_generic_redis_config, fake_redis_client):
```

Test retrieving a non-existent cache key.

Given: A GenericRedisCache instance with no stored data
When: A non-existent key is retrieved
Then: The result should be None
And: No exceptions should be raised

### test_delete_existing_key()

```python
async def test_delete_existing_key(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test deleting an existing cache key.

Given: A GenericRedisCache with a stored key-value pair
When: The key is deleted
Then: The delete operation should return True
And: Subsequent retrieval should return None

### test_delete_nonexistent_key()

```python
async def test_delete_nonexistent_key(self, default_generic_redis_config, fake_redis_client):
```

Test deleting a non-existent cache key.

Given: A GenericRedisCache instance with no stored data
When: A non-existent key is deleted
Then: The delete operation should return False
And: No exceptions should be raised

### test_exists_for_existing_key()

```python
async def test_exists_for_existing_key(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test checking existence of an existing cache key.

Given: A GenericRedisCache with a stored key-value pair
When: The key existence is checked
Then: The exists operation should return True

### test_exists_for_nonexistent_key()

```python
async def test_exists_for_nonexistent_key(self, default_generic_redis_config, fake_redis_client):
```

Test checking existence of a non-existent cache key.

Given: A GenericRedisCache instance with no stored data
When: A non-existent key existence is checked
Then: The exists operation should return False

### test_set_with_custom_ttl()

```python
async def test_set_with_custom_ttl(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test setting a cache value with custom TTL.

Given: A GenericRedisCache instance
When: A value is set with a specific TTL
Then: The value should be stored and retrievable
And: TTL should be properly applied to both L1 and Redis

## TestL1CacheIntegration

Test GenericRedisCache L1 memory cache coordination with Redis.

The GenericRedisCache coordinates between L1 memory cache and Redis backend
to provide optimal performance while maintaining data consistency.

### test_l1_cache_hit_behavior()

```python
async def test_l1_cache_hit_behavior(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test L1 cache hit behavior for faster retrieval.

Given: A GenericRedisCache with L1 cache enabled and a stored value
When: The same key is retrieved multiple times
Then: Subsequent retrievals should be served from L1 cache
And: Data consistency should be maintained

### test_l1_cache_disabled_behavior()

```python
async def test_l1_cache_disabled_behavior(self, no_l1_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test cache behavior with L1 cache disabled.

Given: A GenericRedisCache with L1 cache disabled
When: Values are set and retrieved
Then: All operations should work through Redis backend only
And: Performance should not be affected by L1 cache absence

### test_l1_and_redis_consistency()

```python
async def test_l1_and_redis_consistency(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test data consistency between L1 cache and Redis.

Given: A GenericRedisCache with L1 cache enabled
When: A value is set and then deleted
Then: Both L1 cache and Redis should be updated consistently
And: No stale data should remain in either tier

### test_bulk_operations_l1_coordination()

```python
async def test_bulk_operations_l1_coordination(self, default_generic_redis_config, fake_redis_client, bulk_test_data):
```

Test L1 cache coordination during bulk operations.

Given: A GenericRedisCache with L1 cache enabled
When: Multiple values are set and retrieved in bulk
Then: L1 cache should properly coordinate with Redis
And: All values should be accessible and consistent

## TestTTLAndExpiration

Test GenericRedisCache time-to-live management and expiration behavior.

The GenericRedisCache must properly handle TTL settings, expiration timing,
and coordinate expiration between L1 cache and Redis backend.

### test_default_ttl_application()

```python
async def test_default_ttl_application(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test application of default TTL when none specified.

Given: A GenericRedisCache with a configured default TTL
When: A value is set without specifying TTL
Then: The default TTL should be applied automatically
And: The value should be stored with proper expiration

### test_custom_ttl_override()

```python
async def test_custom_ttl_override(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test custom TTL overriding default TTL.

Given: A GenericRedisCache with a default TTL
When: A value is set with a custom TTL
Then: The custom TTL should override the default
And: The value should expire according to the custom TTL

### test_expiration_behavior()

```python
async def test_expiration_behavior(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value, short_ttl):
```

Test cache expiration behavior with short TTL.

Given: A GenericRedisCache instance
When: A value is set with a very short TTL and time passes
Then: The value should expire and become unavailable
And: Both L1 and Redis should handle expiration properly

### test_ttl_coordination_between_tiers()

```python
async def test_ttl_coordination_between_tiers(self, default_generic_redis_config, fake_redis_client, sample_cache_key, sample_cache_value):
```

Test TTL coordination between L1 cache and Redis.

Given: A GenericRedisCache with L1 cache enabled
When: A value is set with TTL in both tiers
Then: Both L1 and Redis should have consistent TTL handling
And: Expiration should be coordinated across tiers

## TestDataCompressionIntegration

Test GenericRedisCache data compression functionality and thresholds.

The GenericRedisCache should automatically compress large data values
based on configurable thresholds while maintaining data integrity.

### test_compression_threshold_behavior()

```python
async def test_compression_threshold_behavior(self, compression_redis_config, fake_redis_client, sample_large_value):
```

Test automatic compression when data exceeds threshold.

Given: A GenericRedisCache configured with low compression threshold
When: A large value exceeding the threshold is stored
Then: The value should be automatically compressed
And: Retrieved value should match the original exactly

### test_small_value_no_compression()

```python
async def test_small_value_no_compression(self, compression_redis_config, fake_redis_client, sample_cache_value):
```

Test that small values are not compressed unnecessarily.

Given: A GenericRedisCache with compression enabled
When: A small value below the compression threshold is stored
Then: The value should be stored without compression
And: Retrieved value should match the original

### test_compression_data_integrity()

```python
async def test_compression_data_integrity(self, compression_redis_config, fake_redis_client, compression_test_data):
```

Test data integrity across various data types with compression.

Given: A GenericRedisCache with compression enabled
When: Various data types and sizes are stored and retrieved
Then: All data should maintain perfect integrity
And: Complex data structures should be preserved exactly

### test_mixed_compression_scenarios()

```python
async def test_mixed_compression_scenarios(self, compression_redis_config, fake_redis_client, sample_cache_value, sample_large_value):
```

Test mixed scenarios with both compressed and uncompressed data.

Given: A GenericRedisCache with compression configured
When: Both small and large values are stored in the same cache
Then: Compression should be applied appropriately to each value
And: All values should be retrievable correctly regardless of compression
