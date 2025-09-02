---
sidebar_label: test_cache
---

# Tests for AI response cache functionality.

  file_path: `backend/tests.old/infrastructure/cache/test_cache.py`

TODO: split this into multiple files

## TestAIResponseCache

Test the AIResponseCache class.

### cache_instance()

```python
def cache_instance(self):
```

Create a fresh cache instance for testing.

### mock_redis()

```python
def mock_redis(self):
```

Mock Redis client.

### test_instantiation_without_global_settings()

```python
def test_instantiation_without_global_settings(self):
```

Test that AIResponseCache can be instantiated without global settings.

### test_instantiation_with_custom_config()

```python
def test_instantiation_with_custom_config(self):
```

Test that AIResponseCache can be instantiated with custom configuration.

### test_connect_method_uses_injected_config()

```python
def test_connect_method_uses_injected_config(self):
```

Test that connect method uses injected configuration instead of global settings.

### test_cache_key_generation()

```python
def test_cache_key_generation(self, cache_instance):
```

Test cache key generation consistency.

### test_cache_key_options_order_independence()

```python
def test_cache_key_options_order_independence(self, cache_instance):
```

Test that options order doesn't affect cache key.

### test_redis_connection_success()

```python
async def test_redis_connection_success(self, cache_instance, mock_redis):
```

Test successful Redis connection.

### test_redis_connection_failure()

```python
async def test_redis_connection_failure(self, cache_instance):
```

Test Redis connection failure graceful degradation.

### test_redis_unavailable()

```python
async def test_redis_unavailable(self, cache_instance):
```

Test behavior when Redis is not available.

### test_cache_miss()

```python
async def test_cache_miss(self, cache_instance, mock_redis):
```

Test cache miss scenario.

### test_cache_hit()

```python
async def test_cache_hit(self, cache_instance, mock_redis):
```

Test cache hit scenario.

### test_cache_storage()

```python
async def test_cache_storage(self, cache_instance, mock_redis):
```

Test caching response data.

### test_operation_specific_ttl()

```python
async def test_operation_specific_ttl(self, cache_instance, mock_redis):
```

Test that different operations get appropriate TTL values.

### test_cache_invalidation()

```python
async def test_cache_invalidation(self, cache_instance, mock_redis):
```

Test cache pattern invalidation.

### test_cache_stats()

```python
async def test_cache_stats(self, cache_instance, mock_redis):
```

Test cache statistics retrieval.

### test_cache_stats_unavailable()

```python
async def test_cache_stats_unavailable(self, cache_instance):
```

Test cache stats when Redis unavailable.

### test_cache_error_handling()

```python
async def test_cache_error_handling(self, cache_instance, mock_redis):
```

Test graceful error handling in cache operations.

### test_cache_with_question_parameter()

```python
async def test_cache_with_question_parameter(self, cache_instance, mock_redis):
```

Test cache operations with question parameter.

### test_text_tier_classification()

```python
async def test_text_tier_classification(self, cache_instance):
```

Test _get_text_tier method correctly classifies text sizes.

### test_memory_cache_update_basic()

```python
def test_memory_cache_update_basic(self, cache_instance):
```

Test basic memory cache update functionality.

### test_memory_cache_update_existing_key()

```python
def test_memory_cache_update_existing_key(self, cache_instance):
```

Test updating existing key in memory cache.

### test_memory_cache_fifo_eviction()

```python
def test_memory_cache_fifo_eviction(self, cache_instance):
```

Test FIFO eviction when memory cache reaches size limit.

### test_memory_cache_hit_for_small_text()

```python
async def test_memory_cache_hit_for_small_text(self, cache_instance, mock_redis):
```

Test that small text hits memory cache before Redis.

### test_memory_cache_miss_falls_back_to_redis()

```python
async def test_memory_cache_miss_falls_back_to_redis(self, cache_instance, mock_redis):
```

Test that memory cache miss for small text falls back to Redis.

### test_medium_text_skips_memory_cache()

```python
async def test_medium_text_skips_memory_cache(self, cache_instance, mock_redis):
```

Test that medium/large text doesn't use memory cache.

### test_memory_cache_statistics()

```python
async def test_memory_cache_statistics(self, cache_instance, mock_redis):
```

Test memory cache statistics in cache stats.

### test_memory_cache_initialization()

```python
def test_memory_cache_initialization(self, cache_instance):
```

Test memory cache is properly initialized.

### test_compression_data_small_data()

```python
def test_compression_data_small_data(self, cache_instance):
```

Test that small data is not compressed.

### test_compression_data_large_data()

```python
def test_compression_data_large_data(self, cache_instance):
```

Test that large data is compressed.

### test_compression_threshold_configuration()

```python
def test_compression_threshold_configuration(self):
```

Test that compression threshold can be configured.

## TestMemoryCacheOperations

Comprehensive unit tests for memory cache operations.

### memory_cache_instance()

```python
def memory_cache_instance(self):
```

Create a cache instance for memory cache testing.

### small_memory_cache_instance()

```python
def small_memory_cache_instance(self):
```

Create a cache instance with small memory cache for eviction testing.

### memory_mock_redis()

```python
def memory_mock_redis(self):
```

Mock Redis instance for memory cache testing.

### test_memory_cache_hit_returns_correct_data()

```python
def test_memory_cache_hit_returns_correct_data(self, memory_cache_instance):
```

Test that cache hit returns the correct cached data.

### test_memory_cache_miss_returns_none()

```python
def test_memory_cache_miss_returns_none(self, memory_cache_instance):
```

Test that cache miss returns None for non-existent keys.

### test_memory_cache_fifo_eviction_detailed()

```python
def test_memory_cache_fifo_eviction_detailed(self, small_memory_cache_instance):
```

Test detailed FIFO eviction behavior when cache reaches capacity.

### test_memory_cache_access_pattern_complex()

```python
def test_memory_cache_access_pattern_complex(self, small_memory_cache_instance):
```

Test complex access patterns with cache updates.

### test_memory_cache_boundary_conditions()

```python
def test_memory_cache_boundary_conditions(self, memory_cache_instance):
```

Test cache behavior at boundary conditions.

### test_memory_cache_duplicate_key_handling()

```python
def test_memory_cache_duplicate_key_handling(self, memory_cache_instance):
```

Test handling of duplicate keys in cache updates.

### test_memory_cache_data_integrity()

```python
def test_memory_cache_data_integrity(self, memory_cache_instance):
```

Test that cached data maintains integrity over operations.

### test_memory_cache_concurrent_access_simulation()

```python
def test_memory_cache_concurrent_access_simulation(self, memory_cache_instance):
```

Test simulation of concurrent access patterns.

### test_memory_cache_integration_with_get_cached_response()

```python
async def test_memory_cache_integration_with_get_cached_response(self, memory_cache_instance, memory_mock_redis):
```

Test memory cache integration with the main cache retrieval method.

### test_memory_cache_miss_fallback_to_redis()

```python
async def test_memory_cache_miss_fallback_to_redis(self, memory_cache_instance, memory_mock_redis):
```

Test memory cache miss properly falls back to Redis.

### test_memory_cache_eviction_preserves_consistency()

```python
def test_memory_cache_eviction_preserves_consistency(self, small_memory_cache_instance):
```

Test that eviction maintains consistency between cache and order list.

### test_memory_cache_performance_characteristics()

```python
def test_memory_cache_performance_characteristics(self, memory_cache_instance):
```

Test performance characteristics of memory cache operations.

### test_memory_cache_edge_case_empty_operations()

```python
def test_memory_cache_edge_case_empty_operations(self, memory_cache_instance):
```

Test edge cases with empty keys, values, and operations.

### test_cache_response_includes_compression_metadata()

```python
async def test_cache_response_includes_compression_metadata(self, memory_cache_instance, memory_mock_redis):
```

Test that cached responses include compression metadata.

### test_cache_retrieval_handles_compressed_data()

```python
async def test_cache_retrieval_handles_compressed_data(self, memory_cache_instance, memory_mock_redis):
```

Test that cache retrieval properly handles compressed data.

### test_cache_response_timing_tracking()

```python
async def test_cache_response_timing_tracking(self, memory_cache_instance, memory_mock_redis):
```

Test that cache_response records performance timing metrics.

### test_cache_response_timing_on_failure()

```python
async def test_cache_response_timing_on_failure(self, memory_cache_instance, memory_mock_redis):
```

Test that cache_response records timing even when Redis operations fail.

### test_cache_response_timing_on_connection_failure()

```python
async def test_cache_response_timing_on_connection_failure(self, memory_cache_instance):
```

Test that cache_response records timing when Redis connection fails.

### test_cache_response_compression_tracking()

```python
async def test_cache_response_compression_tracking(self, memory_cache_instance, memory_mock_redis):
```

Test that cache_response records compression metrics when compression is used.

### test_cache_response_no_compression_tracking_for_small_data()

```python
async def test_cache_response_no_compression_tracking_for_small_data(self, memory_cache_instance, memory_mock_redis):
```

Test that cache_response doesn't record compression metrics for small data.

### test_cache_response_compression_tracking_for_small_data()

```python
async def test_cache_response_compression_tracking_for_small_data(self, memory_cache_instance, memory_mock_redis):
```

Test that compression metrics are NOT recorded for small data.

### test_memory_usage_recording()

```python
def test_memory_usage_recording(self, memory_cache_instance):
```

Test that memory usage is recorded properly.

### test_memory_usage_recording_failure()

```python
def test_memory_usage_recording_failure(self, memory_cache_instance):
```

Test memory usage recording when Redis stats are unavailable.

### test_get_memory_usage_stats()

```python
def test_get_memory_usage_stats(self, memory_cache_instance):
```

Test getting memory usage statistics.

### test_get_memory_warnings()

```python
def test_get_memory_warnings(self, memory_cache_instance):
```

Test memory warning generation.

### test_cache_stats_includes_memory_tracking()

```python
async def test_cache_stats_includes_memory_tracking(self, memory_cache_instance, memory_mock_redis):
```

Test that get_cache_stats triggers memory usage recording and includes memory stats.

### test_cache_stats_memory_recording_redis_unavailable()

```python
async def test_cache_stats_memory_recording_redis_unavailable(self, memory_cache_instance):
```

Test memory usage recording when Redis is unavailable.

### test_memory_usage_with_large_cache()

```python
def test_memory_usage_with_large_cache(self, memory_cache_instance):
```

Test memory usage tracking with large cache.

### test_memory_threshold_configuration()

```python
def test_memory_threshold_configuration(self, memory_cache_instance):
```

Test memory threshold configuration.

### test_memory_usage_integration_with_performance_stats()

```python
def test_memory_usage_integration_with_performance_stats(self, memory_cache_instance):
```

Test integration between memory usage and performance stats.

### test_memory_usage_cleanup_on_reset()

```python
def test_memory_usage_cleanup_on_reset(self, memory_cache_instance):
```

Test that memory usage data is cleaned up on reset.

### test_invalidate_pattern_tracking_success()

```python
async def test_invalidate_pattern_tracking_success(self, memory_cache_instance, memory_mock_redis):
```

Test invalidation tracking with successful operation.

### test_invalidate_pattern_tracking_no_keys_found()

```python
async def test_invalidate_pattern_tracking_no_keys_found(self, memory_cache_instance, memory_mock_redis):
```

Test invalidation tracking when no keys are found.

### test_invalidate_pattern_tracking_redis_connection_failed()

```python
async def test_invalidate_pattern_tracking_redis_connection_failed(self, memory_cache_instance):
```

Test invalidation tracking when Redis connection fails.

### test_invalidate_pattern_tracking_redis_error()

```python
async def test_invalidate_pattern_tracking_redis_error(self, memory_cache_instance, memory_mock_redis):
```

Test invalidation tracking when Redis operation fails.

### test_invalidate_all()

```python
async def test_invalidate_all(self, memory_cache_instance, memory_mock_redis):
```

Test invalidate_all convenience method.

### test_invalidate_by_operation()

```python
async def test_invalidate_by_operation(self, memory_cache_instance, memory_mock_redis):
```

Test invalidate_by_operation convenience method.

### test_invalidate_memory_cache()

```python
async def test_invalidate_memory_cache(self, memory_cache_instance):
```

Test memory cache invalidation tracking.

### test_get_invalidation_frequency_stats()

```python
def test_get_invalidation_frequency_stats(self, memory_cache_instance):
```

Test invalidation frequency statistics.

### test_get_invalidation_recommendations()

```python
def test_get_invalidation_recommendations(self, memory_cache_instance):
```

Test invalidation recommendations.

### test_invalidation_integration_with_performance_stats()

```python
def test_invalidation_integration_with_performance_stats(self, memory_cache_instance):
```

Test invalidation integration with performance statistics.

### test_invalidation_events_cleanup()

```python
def test_invalidation_events_cleanup(self, memory_cache_instance):
```

Test that invalidation events are cleaned up on reset.

## TestCacheKeyGenerator

Test the CacheKeyGenerator class.

### key_generator()

```python
def key_generator(self):
```

Create a fresh CacheKeyGenerator instance for testing.

### custom_key_generator()

```python
def custom_key_generator(self):
```

Create a CacheKeyGenerator with custom settings.

### test_instantiation_with_defaults()

```python
def test_instantiation_with_defaults(self, key_generator):
```

Test CacheKeyGenerator instantiation with default parameters.

### test_instantiation_with_custom_params()

```python
def test_instantiation_with_custom_params(self, custom_key_generator):
```

Test CacheKeyGenerator instantiation with custom parameters.

### test_short_text_handling()

```python
def test_short_text_handling(self, key_generator):
```

Test that short texts are kept as-is with sanitization.

### test_short_text_sanitization()

```python
def test_short_text_sanitization(self, key_generator):
```

Test that special characters are sanitized in short texts.

### test_long_text_hashing()

```python
def test_long_text_hashing(self, key_generator):
```

Test that long texts are hashed efficiently.

### test_long_text_with_custom_threshold()

```python
def test_long_text_with_custom_threshold(self, custom_key_generator):
```

Test long text handling with custom threshold.

### test_hash_consistency()

```python
def test_hash_consistency(self, key_generator):
```

Test that identical texts produce identical hashes.

### test_hash_uniqueness()

```python
def test_hash_uniqueness(self, key_generator):
```

Test that different texts produce different hashes.

### test_cache_key_generation_basic()

```python
def test_cache_key_generation_basic(self, key_generator):
```

Test basic cache key generation.

### test_cache_key_with_question()

```python
def test_cache_key_with_question(self, key_generator):
```

Test cache key generation with question parameter.

### test_cache_key_without_options()

```python
def test_cache_key_without_options(self, key_generator):
```

Test cache key generation without options.

### test_cache_key_consistency()

```python
def test_cache_key_consistency(self, key_generator):
```

Test that identical inputs produce identical cache keys.

### test_cache_key_options_order_independence()

```python
def test_cache_key_options_order_independence(self, key_generator):
```

Test that options order doesn't affect cache key.

### test_cache_key_with_long_text()

```python
def test_cache_key_with_long_text(self, key_generator):
```

Test cache key generation with long text that gets hashed.

### test_cache_key_performance_improvement()

```python
def test_cache_key_performance_improvement(self, key_generator):
```

Test that new implementation is more efficient for large texts.

### test_empty_string_handling()

```python
def test_empty_string_handling(self, key_generator):
```

Test CacheKeyGenerator behavior with empty strings.

### test_boundary_threshold_conditions()

```python
def test_boundary_threshold_conditions(self, key_generator):
```

Test behavior at exact threshold boundaries.

### test_unicode_and_special_characters()

```python
def test_unicode_and_special_characters(self, key_generator):
```

Test CacheKeyGenerator with Unicode and special characters.

### test_various_option_value_types()

```python
def test_various_option_value_types(self, key_generator):
```

Test cache key generation with different option value types.

### test_performance_monitor_integration()

```python
def test_performance_monitor_integration(self):
```

Test CacheKeyGenerator with performance monitor integration.

### test_different_hash_algorithms()

```python
def test_different_hash_algorithms(self):
```

Test CacheKeyGenerator with different hash algorithms.

### test_none_and_invalid_inputs_handling()

```python
def test_none_and_invalid_inputs_handling(self, key_generator):
```

Test CacheKeyGenerator behavior with None and edge case inputs.

### test_cache_key_structure_validation()

```python
def test_cache_key_structure_validation(self, key_generator):
```

Test the structure and format of generated cache keys.

### test_cache_key_length_constraints()

```python
def test_cache_key_length_constraints(self, key_generator):
```

Test that cache keys don't become excessively long.

### test_concurrent_key_generation_consistency()

```python
def test_concurrent_key_generation_consistency(self, key_generator):
```

Test that concurrent key generation produces consistent results.

### test_performance_monitor_data_integrity()

```python
def test_performance_monitor_data_integrity(self):
```

Test that performance monitor receives accurate data.

### test_text_sanitization_edge_cases()

```python
def test_text_sanitization_edge_cases(self, key_generator):
```

Test edge cases in text sanitization.

### test_hash_metadata_inclusion()

```python
def test_hash_metadata_inclusion(self, key_generator):
```

Test that hash includes metadata for uniqueness.

### test_question_parameter_hashing_consistency()

```python
def test_question_parameter_hashing_consistency(self, key_generator):
```

Test that question parameter hashing is consistent and secure.

### test_options_hashing_security()

```python
def test_options_hashing_security(self, key_generator):
```

Test that sensitive options are properly hashed.

## TestAIResponseCacheTierSelection

Comprehensive tests for AIResponseCache tier selection logic.

### cache_instance()

```python
def cache_instance(self):
```

Create a fresh cache instance for tier testing.

### mock_redis()

```python
def mock_redis(self):
```

Mock Redis client for tier testing.

### test_tier_configuration_defaults()

```python
def test_tier_configuration_defaults(self, cache_instance):
```

Test that tier configuration has expected default values.

### test_tier_configuration_custom()

```python
def test_tier_configuration_custom(self):
```

Test that tier configuration can be customized.

### test_text_tier_classification_comprehensive()

```python
def test_text_tier_classification_comprehensive(self, cache_instance):
```

Test comprehensive text tier classification including all boundaries.

### test_small_tier_uses_memory_cache_on_cache_hit()

```python
async def test_small_tier_uses_memory_cache_on_cache_hit(self, cache_instance, mock_redis):
```

Test that small tier text uses memory cache when available.

### test_medium_tier_skips_memory_cache_directly_to_redis()

```python
async def test_medium_tier_skips_memory_cache_directly_to_redis(self, cache_instance, mock_redis):
```

Test that medium tier text bypasses memory cache and goes directly to Redis.

### test_large_tier_skips_memory_cache_directly_to_redis()

```python
async def test_large_tier_skips_memory_cache_directly_to_redis(self, cache_instance, mock_redis):
```

Test that large tier text bypasses memory cache and goes directly to Redis.

### test_xlarge_tier_skips_memory_cache_directly_to_redis()

```python
async def test_xlarge_tier_skips_memory_cache_directly_to_redis(self, cache_instance, mock_redis):
```

Test that xlarge tier text bypasses memory cache and goes directly to Redis.

### test_tier_boundary_memory_cache_behavior()

```python
async def test_tier_boundary_memory_cache_behavior(self, cache_instance, mock_redis):
```

Test memory cache behavior at exact tier boundaries.

### test_mixed_tier_cache_behavior_isolation()

```python
async def test_mixed_tier_cache_behavior_isolation(self, cache_instance, mock_redis):
```

Test that different tiers don't interfere with each other's caching behavior.

### test_tier_selection_with_custom_thresholds()

```python
async def test_tier_selection_with_custom_thresholds(self, mock_redis):
```

Test tier selection with custom threshold configuration.

### test_tier_selection_affects_cache_storage_behavior()

```python
async def test_tier_selection_affects_cache_storage_behavior(self, cache_instance, mock_redis):
```

Test that tier selection affects how responses are stored in cache.

### test_tier_selection_error_handling()

```python
async def test_tier_selection_error_handling(self, cache_instance):
```

Test tier selection behavior with edge cases and error conditions.

### test_tier_selection_memory_cache_eviction_behavior()

```python
async def test_tier_selection_memory_cache_eviction_behavior(self, cache_instance, mock_redis):
```

Test that memory cache eviction only affects small tier items.

### test_tier_selection_configuration_immutability_during_operation()

```python
def test_tier_selection_configuration_immutability_during_operation(self, cache_instance):
```

Test that tier configuration doesn't change during cache operations.

## TestDataCompressionDecompression

Comprehensive unit tests for data compression and decompression functionality.

### cache_instance()

```python
def cache_instance(self):
```

Create a cache instance for compression testing.

### custom_compression_cache()

```python
def custom_compression_cache(self):
```

Create a cache instance with custom compression settings.

### no_compression_cache()

```python
def no_compression_cache(self):
```

Create a cache instance with very high compression threshold (effectively no compression).

### test_small_data_compression_and_decompression()

```python
def test_small_data_compression_and_decompression(self, cache_instance):
```

Test that small data is handled correctly without compression.

### test_large_data_compression_and_decompression()

```python
def test_large_data_compression_and_decompression(self, cache_instance):
```

Test that large data is compressed and decompressed correctly.

### test_empty_data_handling()

```python
def test_empty_data_handling(self, cache_instance):
```

Test handling of empty data structures.

### test_very_large_data_handling()

```python
def test_very_large_data_handling(self, cache_instance):
```

Test handling of very large data structures.

### test_various_data_types_compression()

```python
def test_various_data_types_compression(self, cache_instance):
```

Test compression/decompression with various Python data types.

### test_boundary_threshold_compression()

```python
def test_boundary_threshold_compression(self, cache_instance):
```

Test compression behavior at exact threshold boundaries.

### test_custom_compression_settings()

```python
def test_custom_compression_settings(self, custom_compression_cache):
```

Test compression with custom threshold and level settings.

### test_compression_ratio_validation()

```python
def test_compression_ratio_validation(self, cache_instance):
```

Test that compression ratios are within expected ranges for different data types.

### test_error_handling_corrupted_data()

```python
def test_error_handling_corrupted_data(self, cache_instance):
```

Test error handling for corrupted or invalid compressed data.

### test_compression_performance_characteristics()

```python
def test_compression_performance_characteristics(self, cache_instance):
```

Test performance characteristics of compression/decompression operations.

### test_compression_with_none_and_invalid_inputs()

```python
def test_compression_with_none_and_invalid_inputs(self, cache_instance):
```

Test compression/decompression with None and invalid inputs.

### test_compression_consistency_across_calls()

```python
def test_compression_consistency_across_calls(self, cache_instance):
```

Test that compression produces consistent results across multiple calls.

### test_no_compression_behavior()

```python
def test_no_compression_behavior(self, no_compression_cache):
```

Test behavior when compression is effectively disabled (very high threshold).

### test_compression_with_circular_references_error_handling()

```python
def test_compression_with_circular_references_error_handling(self, cache_instance):
```

Test that circular references are handled appropriately.

### test_compression_memory_efficiency()

```python
def test_compression_memory_efficiency(self, cache_instance):
```

Test that compression reduces data size effectively.

## TestRedisIntegrationTests

Integration tests for Redis cache interactions with proper mocking.

### integration_cache_instance()

```python
def integration_cache_instance(self):
```

Create a cache instance for integration testing.

### mock_redis_client()

```python
def mock_redis_client(self):
```

Create a comprehensive mock Redis client for integration testing.

### test_redis_set_operation_stores_data_correctly()

```python
async def test_redis_set_operation_stores_data_correctly(self, integration_cache_instance, mock_redis_client):
```

Test that Redis set operations store data correctly with proper serialization.

### test_redis_get_operation_retrieves_data_correctly()

```python
async def test_redis_get_operation_retrieves_data_correctly(self, integration_cache_instance, mock_redis_client):
```

Test that Redis get operations retrieve data correctly with proper deserialization.

### test_redis_get_operation_returns_none_for_missing_data()

```python
async def test_redis_get_operation_returns_none_for_missing_data(self, integration_cache_instance, mock_redis_client):
```

Test that Redis get operations return None for missing/non-existent data.

### test_redis_expiration_settings_work_as_expected()

```python
async def test_redis_expiration_settings_work_as_expected(self, integration_cache_instance, mock_redis_client):
```

Test that Redis expiration (TTL) settings work correctly for different operations.

### test_redis_connection_error_handling()

```python
async def test_redis_connection_error_handling(self, integration_cache_instance):
```

Test error handling for Redis connection issues.

### test_redis_unavailable_graceful_degradation()

```python
async def test_redis_unavailable_graceful_degradation(self, integration_cache_instance):
```

Test graceful degradation when Redis is not available.

### test_redis_operation_error_handling_during_get()

```python
async def test_redis_operation_error_handling_during_get(self, integration_cache_instance, mock_redis_client):
```

Test error handling during Redis get operations.

### test_redis_operation_error_handling_during_set()

```python
async def test_redis_operation_error_handling_during_set(self, integration_cache_instance, mock_redis_client):
```

Test error handling during Redis set operations.

### test_redis_invalidation_operations()

```python
async def test_redis_invalidation_operations(self, integration_cache_instance, mock_redis_client):
```

Test Redis invalidation operations work correctly.

### test_redis_stats_collection()

```python
async def test_redis_stats_collection(self, integration_cache_instance, mock_redis_client):
```

Test Redis statistics collection works correctly.

### test_redis_compression_integration()

```python
async def test_redis_compression_integration(self, integration_cache_instance, mock_redis_client):
```

Test Redis integration with data compression for large responses.

### test_redis_binary_data_handling()

```python
async def test_redis_binary_data_handling(self, integration_cache_instance, mock_redis_client):
```

Test Redis binary data handling for compressed responses.

### test_redis_concurrent_operations_simulation()

```python
async def test_redis_concurrent_operations_simulation(self, integration_cache_instance, mock_redis_client):
```

Test Redis operations under simulated concurrent access.

### test_redis_memory_tier_integration()

```python
async def test_redis_memory_tier_integration(self, integration_cache_instance, mock_redis_client):
```

Test Redis integration with memory cache tiers.

## TestCacheHitRatioTracking

Test cache hit ratio tracking functionality.

### performance_monitor()

```python
def performance_monitor(self):
```

Create a CachePerformanceMonitor instance for testing.

### cache_service()

```python
def cache_service(self, performance_monitor):
```

Create an AIResponseCache with performance monitoring.

### test_cache_hit_ratio_initialization()

```python
def test_cache_hit_ratio_initialization(self, cache_service):
```

Test that cache hit ratio starts at 0%.

### test_cache_miss_tracking()

```python
async def test_cache_miss_tracking(self, cache_service):
```

Test that cache misses are properly tracked.

### test_redis_cache_hit_tracking()

```python
async def test_redis_cache_hit_tracking(self, cache_service):
```

Test that Redis cache hits are properly tracked.

### test_memory_cache_hit_tracking()

```python
async def test_memory_cache_hit_tracking(self, cache_service):
```

Test that memory cache hits are properly tracked.

### test_mixed_cache_operations_hit_ratio()

```python
async def test_mixed_cache_operations_hit_ratio(self, cache_service):
```

Test hit ratio calculation with mixed hits and misses.

### test_key_generation_timing_tracking()

```python
def test_key_generation_timing_tracking(self, cache_service):
```

Test that key generation timing is tracked.

### test_redis_connection_failure_tracking()

```python
async def test_redis_connection_failure_tracking(self, cache_service):
```

Test that Redis connection failures are tracked as misses.

### test_redis_error_tracking()

```python
async def test_redis_error_tracking(self, cache_service):
```

Test that Redis errors are tracked as misses with error details.

### test_performance_summary()

```python
def test_performance_summary(self, cache_service):
```

Test the performance summary method.

### test_performance_stats_reset()

```python
def test_performance_stats_reset(self, cache_service):
```

Test that performance statistics can be reset.

### test_cache_stats_includes_performance()

```python
async def test_cache_stats_includes_performance(self, cache_service):
```

Test that get_cache_stats includes performance metrics.
