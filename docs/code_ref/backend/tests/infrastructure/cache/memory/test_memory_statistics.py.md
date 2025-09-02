---
sidebar_label: test_memory_statistics
---

# Unit tests for InMemoryCache statistics and monitoring capabilities.

  file_path: `backend/tests/infrastructure/cache/memory/test_memory_statistics.py`

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

Coverage Focus:
    - get_stats() method providing comprehensive cache metrics
    - get_keys() and get_active_keys() methods for cache introspection
    - size() method for current cache entry count
    - get_ttl() method for remaining TTL information

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Standard library components (threading, collections): For thread-safe operations and data structures
    - app.core.exceptions: Exception handling for configuration and validation errors

## TestInMemoryCacheStatistics

Test suite for InMemoryCache statistics and monitoring capabilities.

Scope:
    - get_stats() method providing comprehensive cache performance metrics
    - get_keys() and get_active_keys() methods for cache introspection
    - size() method for accurate cache entry counting
    - get_ttl() method for TTL information and expiration monitoring
    
Business Critical:
    Statistics enable cache performance monitoring and capacity planning
    
Test Strategy:
    - Statistics accuracy testing using populated cache instances
    - Active vs expired key differentiation using fast_expiry_memory_cache
    - Memory usage and utilization calculations using various cache sizes
    - TTL information accuracy using mixed_ttl_test_data fixture
    
External Dependencies:
    - time: For TTL calculations and expiration timing
    - asyncio: For asynchronous method testing

### test_get_stats_provides_comprehensive_cache_metrics()

```python
def test_get_stats_provides_comprehensive_cache_metrics(self):
```

Test that get_stats() returns comprehensive cache performance and usage metrics.

Verifies:
    Statistics dictionary contains all documented metrics with accurate values
    
Business Impact:
    Enables cache performance monitoring, capacity planning, and optimization
    
Scenario:
    Given: Cache with various operations performed (hits, misses, evictions)
    When: get_stats() method is called
    Then: Complete statistics dictionary is returned with all documented fields
    And: All numeric values are accurate based on actual cache operations
    And: Percentage calculations are mathematically correct
    
Statistics Fields Verified:
    - active_entries: Count of non-expired cache entries
    - expired_entries: Count of expired but not yet cleaned entries  
    - total_entries: Sum of active and expired entries
    - max_size: Configured maximum cache size
    - utilization_percent: (active_entries / max_size) * 100
    - hit_rate: hits / (hits + misses) as percentage
    - hits: Total cache hit count since initialization
    - misses: Total cache miss count since initialization
    - evictions: Total LRU eviction count
    - memory_usage_bytes: Estimated memory usage of cached data
    
Fixtures Used:
    - populated_memory_cache: Cache with known operations for statistics testing
    - cache_statistics_sample: Expected statistics structure for verification
    
Metric Accuracy:
    All statistics reflect actual cache state and operation history
    
Related Tests:
    - test_statistics_update_correctly_after_cache_operations()
    - test_utilization_percentage_calculated_accurately()

### test_statistics_update_correctly_after_cache_operations()

```python
def test_statistics_update_correctly_after_cache_operations(self):
```

Test that cache statistics update accurately as operations are performed.

Verifies:
    Statistics counters increment correctly with each cache operation type
    
Business Impact:
    Ensures reliable performance monitoring throughout cache lifecycle
    
Scenario:
    Given: Fresh cache instance with zero statistics
    When: Various cache operations (get, set, delete) are performed
    Then: Statistics counters update accurately after each operation
    And: Hit/miss ratios reflect actual operation outcomes
    And: Memory usage statistics change appropriately with data storage
    
Operation Impact on Statistics:
    - set() operations increment appropriate counters
    - get() hits increment hit counter and update hit rate
    - get() misses increment miss counter and update hit rate  
    - delete() operations may affect memory usage calculations
    - Eviction operations increment eviction counter
    
Fixtures Used:
    - default_memory_cache: Fresh cache for operation statistics testing
    - sample_cache_key: Key for controlled operation testing
    - sample_cache_value: Value for statistics impact testing
    
Real-Time Accuracy:
    Statistics reflect cache state immediately after each operation
    
Related Tests:
    - test_get_stats_provides_comprehensive_cache_metrics()
    - test_hit_rate_calculation_reflects_actual_operation_outcomes()

### test_utilization_percentage_calculated_accurately()

```python
def test_utilization_percentage_calculated_accurately(self):
```

Test that utilization percentage in statistics reflects accurate cache fullness.

Verifies:
    Utilization percentage calculation is mathematically correct and meaningful
    
Business Impact:
    Enables capacity planning and cache sizing decisions
    
Scenario:
    Given: Cache with known max_size and varying number of active entries
    When: get_stats() is called at different cache fullness levels
    Then: utilization_percent accurately reflects (active_entries / max_size) * 100
    And: Percentage updates correctly as entries are added or removed
    And: Utilization reflects only active entries, not expired entries
    
Utilization Calculation Verified:
    - Empty cache shows 0% utilization
    - Half-full cache shows 50% utilization  
    - Full cache shows 100% utilization
    - Expired entries do not count toward utilization
    - Evicted entries properly reduce utilization percentage
    
Fixtures Used:
    - small_memory_cache: Cache with known max_size for percentage testing
    - cache_entries_for_lru_testing: Varying numbers of entries for utilization testing
    
Mathematical Accuracy:
    Percentage calculations are precise and reflect actual cache state
    
Related Tests:
    - test_get_stats_provides_comprehensive_cache_metrics()
    - test_active_entries_count_excludes_expired_entries()

### test_hit_rate_calculation_reflects_actual_operation_outcomes()

```python
def test_hit_rate_calculation_reflects_actual_operation_outcomes(self):
```

Test that hit rate calculation in statistics accurately reflects cache performance.

Verifies:
    Hit rate percentage accurately represents actual cache hit/miss ratio
    
Business Impact:
    Enables cache effectiveness evaluation and optimization decisions
    
Scenario:
    Given: Cache with known sequence of hit and miss operations
    When: get_stats() is called after various hit/miss scenarios
    Then: hit_rate accurately reflects hits / (hits + misses) percentage
    And: Hit rate updates correctly with each get() operation
    And: Hit rate calculation handles edge cases (no operations, all hits, all misses)
    
Hit Rate Scenarios Tested:
    - No operations performed (hit rate should be 0 or undefined)
    - All cache hits (hit rate should be 100%)
    - All cache misses (hit rate should be 0%)
    - Mixed hit/miss operations (hit rate should be accurate percentage)
    - Hit rate changes appropriately with new operations
    
Fixtures Used:
    - default_memory_cache: Cache for controlled hit/miss testing
    - sample_cache_key: Key for known hit scenarios
    - cache_test_keys: Multiple keys for miss scenario testing
    
Performance Measurement:
    Hit rate provides meaningful cache effectiveness metrics
    
Related Tests:
    - test_statistics_update_correctly_after_cache_operations()
    - test_cache_hits_and_misses_tracked_accurately()

### test_get_keys_returns_all_cache_keys_including_expired()

```python
def test_get_keys_returns_all_cache_keys_including_expired(self):
```

Test that get_keys() returns all cache keys including expired entries.

Verifies:
    Complete key inventory includes both active and expired entries
    
Business Impact:
    Enables comprehensive cache analysis and debugging including expired data
    
Scenario:
    Given: Cache containing both active and expired entries
    When: get_keys() method is called
    Then: All stored keys are returned including expired entries
    And: Key list includes both unexpired and expired entry keys
    And: No keys are missing from the complete inventory
    
Key Inventory Completeness Verified:
    - Active (non-expired) keys included in results
    - Expired but not cleaned keys included in results
    - Deleted keys are not included in results
    - Key list order is consistent but not necessarily sorted
    - Empty cache returns empty key list
    
Fixtures Used:
    - fast_expiry_memory_cache: Cache for expired entry testing
    - mixed_ttl_test_data: Entries with various expiration states
    - cache_test_keys: Known keys for inventory verification
    
Complete Visibility:
    All stored cache keys are accessible for analysis regardless of expiration
    
Related Tests:
    - test_get_active_keys_returns_only_non_expired_keys()
    - test_expired_entries_remain_until_cleanup()

### test_get_active_keys_returns_only_non_expired_keys()

```python
def test_get_active_keys_returns_only_non_expired_keys(self):
```

Test that get_active_keys() returns only currently valid, non-expired keys.

Verifies:
    Active key list excludes expired entries and includes only accessible data
    
Business Impact:
    Enables analysis of currently useful cache content for optimization
    
Scenario:
    Given: Cache containing mix of active and expired entries
    When: get_active_keys() method is called  
    Then: Only non-expired keys are returned in the list
    And: Expired keys are excluded from active key list
    And: All returned keys correspond to retrievable cache entries
    
Active Key Filtering Verified:
    - Non-expired keys included in active key list
    - Expired keys excluded from active key list
    - Recently expired keys properly filtered out
    - Active key list matches entries accessible via get() method
    - Empty active list when all entries expired
    
Fixtures Used:
    - fast_expiry_memory_cache: Cache for expiration filtering testing
    - mixed_ttl_test_data: Entries with known expiration states
    - sample_cache_key: Active key for positive verification
    
Accurate Filtering:
    Active key list precisely reflects currently accessible cache content
    
Related Tests:
    - test_get_keys_returns_all_cache_keys_including_expired()
    - test_active_vs_expired_key_distinction()

### test_size_method_returns_accurate_current_entry_count()

```python
def test_size_method_returns_accurate_current_entry_count(self):
```

Test that size() method returns accurate count of current cache entries.

Verifies:
    Size count reflects actual number of stored entries including expired ones
    
Business Impact:
    Enables memory usage monitoring and cache capacity assessment
    
Scenario:
    Given: Cache with known number of stored entries (active and expired)
    When: size() method is called
    Then: Accurate count of all stored entries is returned
    And: Count includes both active and expired entries
    And: Count reflects actual internal storage state
    
Size Count Accuracy Verified:
    - Count matches actual number of stored cache entries
    - Both active and expired entries counted in size
    - Deleted entries not counted in size
    - Size updates immediately after set/delete operations  
    - Empty cache returns size of 0
    
Fixtures Used:
    - populated_memory_cache: Cache with known entry count
    - mixed_ttl_test_data: Entries for size counting verification
    - default_memory_cache: Fresh cache for empty size testing
    
Immediate Accuracy:
    Size method reflects current storage state without delay
    
Related Tests:
    - test_cache_size_never_exceeds_configured_max_size() (from LRU tests)
    - test_size_decreases_after_delete_operations()

### test_get_ttl_returns_accurate_remaining_time_for_entries()

```python
def test_get_ttl_returns_accurate_remaining_time_for_entries(self):
```

Test that get_ttl() method returns accurate remaining TTL for cache entries.

Verifies:
    TTL information accurately reflects remaining time before expiration
    
Business Impact:
    Enables cache entry lifecycle monitoring and expiration planning
    
Scenario:
    Given: Cache entries with known TTL values and creation times
    When: get_ttl() is called for various entries at different time points
    Then: Remaining TTL accurately reflects time until expiration
    And: TTL decreases over time for time-sensitive entries
    And: None returned for non-existent or expired entries
    
TTL Accuracy Verified:
    - Remaining TTL calculated correctly based on creation time and TTL
    - TTL values decrease over time as expiration approaches
    - Expired entries return None from get_ttl()
    - Non-existent keys return None from get_ttl()
    - Entries with no TTL (permanent) return appropriate indicator
    
Fixtures Used:
    - mixed_ttl_test_data: Entries with various TTL configurations
    - sample_cache_key: Key for TTL calculation testing
    - mock_time_provider: For controlled time advancement if needed
    
Time Sensitivity:
    TTL calculations accurately reflect passage of time
    
Related Tests:
    - test_ttl_expiration_behavior_matches_get_ttl_predictions()
    - test_get_ttl_handles_edge_cases_correctly()

### test_memory_usage_statistics_reflect_actual_storage_requirements()

```python
def test_memory_usage_statistics_reflect_actual_storage_requirements(self):
```

Test that memory usage statistics accurately estimate actual cache memory consumption.

Verifies:
    Memory usage calculations provide meaningful estimates for capacity planning
    
Business Impact:
    Enables memory capacity planning and resource allocation decisions
    
Scenario:
    Given: Cache with entries of various sizes and types
    When: get_stats() is called to retrieve memory usage information  
    Then: memory_usage_bytes provides reasonable estimate of actual memory usage
    And: Memory usage increases with larger or more numerous entries
    And: Memory usage decreases after entry deletions or evictions
    
Memory Usage Accuracy Verified:
    - Memory estimates correlate with actual data size
    - Larger entries contribute more to memory usage calculations
    - Memory usage decreases after deletions and evictions
    - Empty cache shows minimal or zero memory usage
    - Memory estimates are reasonable for capacity planning
    
Fixtures Used:
    - cache_test_values: Values of various sizes for memory testing
    - large_memory_cache: Cache for substantial memory usage testing
    - high_memory_pressure_scenario: Large entries for memory calculation testing
    
Resource Planning:
    Memory statistics enable informed capacity planning decisions
    
Related Tests:
    - test_get_stats_provides_comprehensive_cache_metrics()
    - test_memory_usage_decreases_after_evictions()

### test_statistics_remain_consistent_across_async_operations()

```python
def test_statistics_remain_consistent_across_async_operations(self):
```

Test that cache statistics remain consistent and accurate during concurrent async operations.

Verifies:
    Statistics accuracy is maintained during concurrent cache operations
    
Business Impact:
    Ensures reliable monitoring in multi-threaded/async application environments
    
Scenario:
    Given: Cache with concurrent async operations (get, set, delete) running
    When: get_stats() is called during or after concurrent operations
    Then: Statistics remain internally consistent and mathematically accurate
    And: No race conditions cause incorrect statistics
    And: Final statistics accurately reflect all completed operations
    
Concurrency Safety Verified:
    - Hit/miss counters remain accurate during concurrent operations
    - Memory usage calculations remain consistent
    - Utilization percentages remain mathematically correct
    - No statistics corruption occurs during async operations
    - Statistics updates are atomic and consistent
    
Fixtures Used:
    - default_memory_cache: Cache for concurrent operation testing
    - cache_test_keys: Multiple keys for concurrent access patterns
    - cache_test_values: Values for concurrent operation testing
    
Thread Safety:
    Statistics remain accurate in concurrent access scenarios
    
Related Tests:
    - test_statistics_update_correctly_after_cache_operations()
    - test_cache_operations_maintain_consistent_internal_state()
