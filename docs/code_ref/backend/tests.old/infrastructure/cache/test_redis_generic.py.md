---
sidebar_label: test_redis_generic
---

# Comprehensive unit tests for GenericRedisCache implementation.

  file_path: `backend/tests.old/infrastructure/cache/test_redis_generic.py`

This module tests all aspects of the GenericRedisCache including L1 caching,
compression, monitoring integration, callback system, and error handling.
Designed to achieve 95%+ line coverage.

## TestGenericRedisCache

Test suite for GenericRedisCache with comprehensive coverage.

### performance_monitor()

```python
def performance_monitor(self):
```

Create a performance monitor for testing.

### cache()

```python
def cache(self, performance_monitor):
```

Create a GenericRedisCache instance for testing.

### cache_no_l1()

```python
def cache_no_l1(self, performance_monitor):
```

Create a GenericRedisCache instance without L1 cache.

### test_initialization_with_l1_cache()

```python
def test_initialization_with_l1_cache(self, cache):
```

Test cache initialization with L1 cache enabled.

### test_initialization_without_l1_cache()

```python
def test_initialization_without_l1_cache(self, cache_no_l1):
```

Test cache initialization with L1 cache disabled.

### test_register_callback()

```python
def test_register_callback(self, cache):
```

Test callback registration system.

### test_fire_callback_with_exception()

```python
def test_fire_callback_with_exception(self, cache, caplog):
```

Test callback firing handles exceptions gracefully.

### test_compress_data_small_data()

```python
def test_compress_data_small_data(self, cache):
```

Test compression with data below threshold.

### test_compress_data_large_data()

```python
def test_compress_data_large_data(self, cache):
```

Test compression with data above threshold.

### test_decompress_data_raw()

```python
def test_decompress_data_raw(self, cache):
```

Test decompression of raw (uncompressed) data.

### test_decompress_data_compressed()

```python
def test_decompress_data_compressed(self, cache):
```

Test decompression of compressed data.

### test_connect_redis_unavailable()

```python
async def test_connect_redis_unavailable(self, cache):
```

Test connection when Redis is unavailable.

### test_connect_success()

```python
async def test_connect_success(self, cache):
```

Test successful Redis connection.

### test_connect_failure()

```python
async def test_connect_failure(self, cache):
```

Test Redis connection failure.

### test_disconnect_success()

```python
async def test_disconnect_success(self, cache):
```

Test successful Redis disconnection.

### test_disconnect_with_error()

```python
async def test_disconnect_with_error(self, cache, caplog):
```

Test disconnection with Redis error.

### test_disconnect_no_connection()

```python
async def test_disconnect_no_connection(self, cache):
```

Test disconnection when not connected.

### test_get_l1_cache_hit()

```python
async def test_get_l1_cache_hit(self, cache):
```

Test cache get with L1 cache hit.

### test_get_redis_hit()

```python
async def test_get_redis_hit(self, cache):
```

Test cache get with Redis hit (L1 miss).

### test_get_cache_miss()

```python
async def test_get_cache_miss(self, cache):
```

Test cache get with complete miss.

### test_get_redis_unavailable()

```python
async def test_get_redis_unavailable(self, cache):
```

Test cache get when Redis is unavailable.

### test_get_redis_error()

```python
async def test_get_redis_error(self, cache):
```

Test cache get with Redis error.

### test_get_without_l1_cache()

```python
async def test_get_without_l1_cache(self, cache_no_l1):
```

Test cache get without L1 cache.

### test_set_success()

```python
async def test_set_success(self, cache):
```

Test successful cache set operation.

### test_set_with_compression()

```python
async def test_set_with_compression(self, cache):
```

Test set operation with data compression.

### test_set_redis_unavailable()

```python
async def test_set_redis_unavailable(self, cache):
```

Test set operation when Redis is unavailable.

### test_set_redis_error()

```python
async def test_set_redis_error(self, cache):
```

Test set operation with Redis error.

### test_set_without_l1_cache()

```python
async def test_set_without_l1_cache(self, cache_no_l1):
```

Test set operation without L1 cache.

### test_delete_key_exists()

```python
async def test_delete_key_exists(self, cache):
```

Test delete operation when key exists.

### test_delete_key_not_exists()

```python
async def test_delete_key_not_exists(self, cache):
```

Test delete operation when key doesn't exist.

### test_delete_redis_error()

```python
async def test_delete_redis_error(self, cache):
```

Test delete operation with Redis error.

### test_delete_without_l1_cache()

```python
async def test_delete_without_l1_cache(self, cache_no_l1):
```

Test delete operation without L1 cache.

### test_exists_l1_cache_hit()

```python
async def test_exists_l1_cache_hit(self, cache):
```

Test exists operation with L1 cache hit.

### test_exists_redis_hit()

```python
async def test_exists_redis_hit(self, cache):
```

Test exists operation with Redis hit (L1 miss).

### test_exists_not_found()

```python
async def test_exists_not_found(self, cache):
```

Test exists operation when key is not found.

### test_exists_redis_error()

```python
async def test_exists_redis_error(self, cache):
```

Test exists operation with Redis error.

### test_exists_without_l1_cache()

```python
async def test_exists_without_l1_cache(self, cache_no_l1):
```

Test exists operation without L1 cache.

### test_performance_monitoring_integration()

```python
def test_performance_monitoring_integration(self, cache):
```

Test that performance monitoring is properly integrated.

### test_full_cache_workflow()

```python
async def test_full_cache_workflow(self, cache):
```

Test complete cache workflow: set, get, exists, delete.

### test_callback_system_comprehensive()

```python
def test_callback_system_comprehensive(self, cache):
```

Test comprehensive callback system functionality.

### test_edge_cases_and_error_handling()

```python
async def test_edge_cases_and_error_handling(self, cache):
```

Test various edge cases and error conditions.

### test_compression_threshold_edge_cases()

```python
def test_compression_threshold_edge_cases(self, cache):
```

Test compression behavior at threshold boundaries.

### test_ttl_parameter_handling()

```python
async def test_ttl_parameter_handling(self, cache):
```

Test TTL parameter handling in set operations.
