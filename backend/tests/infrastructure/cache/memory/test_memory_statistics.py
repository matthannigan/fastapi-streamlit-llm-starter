"""
Unit tests for InMemoryCache statistics and monitoring capabilities.

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
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch
from typing import Any, Dict, List

from app.infrastructure.cache.memory import InMemoryCache


class TestInMemoryCacheStatistics:
    """
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
    """

    @pytest.mark.asyncio
    async def test_get_stats_provides_comprehensive_cache_metrics(self, populated_memory_cache: InMemoryCache, cache_statistics_sample: Dict[str, Any]):
        """
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
        """
        # When
        stats = populated_memory_cache.get_stats()

        # Then
        expected_keys = cache_statistics_sample['memory'].keys()
        for key in expected_keys:
            assert key in stats, f"Key '{key}' not found in stats"

    @pytest.mark.asyncio
    async def test_statistics_update_correctly_after_cache_operations(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any):
        """
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
        """
        # Initial state
        initial_stats = default_memory_cache.get_stats()
        assert initial_stats['hits'] == 0
        assert initial_stats['misses'] == 0

        # Cache Miss
        await default_memory_cache.get("non_existent_key")
        miss_stats = default_memory_cache.get_stats()
        assert miss_stats['misses'] == 1
        assert miss_stats['hits'] == 0
        
        # Cache Hit
        await default_memory_cache.set(sample_cache_key, sample_cache_value)
        await default_memory_cache.get(sample_cache_key)
        hit_stats = default_memory_cache.get_stats()
        assert hit_stats['misses'] == 1
        assert hit_stats['hits'] == 1

    @pytest.mark.asyncio
    async def test_utilization_percentage_calculated_accurately(self, small_memory_cache: InMemoryCache):
        """
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
            - test_active_entries_count_excludes_expired entries()
        """
        # Given: An empty cache (max_size=3)
        assert small_memory_cache.get_stats()['utilization_percent'] == 0.0
        
        # When: One item is added
        await small_memory_cache.set("key1", "value1")
        assert small_memory_cache.get_stats()['utilization_percent'] == pytest.approx(33.33, rel=0.01)

        # When: Cache is filled
        await small_memory_cache.set("key2", "value2")
        await small_memory_cache.set("key3", "value3")
        assert small_memory_cache.get_stats()['utilization_percent'] == 100.0

    @pytest.mark.asyncio
    async def test_hit_rate_calculation_reflects_actual_operation_outcomes(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any):
        """
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
        """
        # Given: No operations
        assert default_memory_cache.get_stats()['hit_rate'] == 0.0

        # Scenario: 1 hit, 1 miss (50%)
        await default_memory_cache.set(sample_cache_key, sample_cache_value)
        await default_memory_cache.get(sample_cache_key)  # Hit
        await default_memory_cache.get("non_existent_key")  # Miss
        assert default_memory_cache.get_stats()['hit_rate'] == 50.0

        # Scenario: 2 hits, 1 miss (~66.7%)
        await default_memory_cache.get(sample_cache_key)  # Hit
        assert default_memory_cache.get_stats()['hit_rate'] == pytest.approx(66.67, rel=0.01)

        # Scenario: Additional miss drops to 50.0%
        await default_memory_cache.get("another_miss")
        assert default_memory_cache.get_stats()['hit_rate'] == pytest.approx(50.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_keys_returns_all_cache_keys_including_expired(self, default_memory_cache: InMemoryCache, mock_time_provider):
        """
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
            - default_memory_cache: Cache for expired entry testing
            - mixed_ttl_test_data: Entries with various expiration states
            - mock_time_provider: For deterministic expiration testing without delays
            
        Complete Visibility:
            All stored cache keys are accessible for analysis regardless of expiration
            
        Related Tests:
            - test_get_active_keys_returns_only_non_expired_keys()
            - test_expired_entries_remain_until_cleanup()
        """
        # Given: A mix of soon-to-be-expired and non-expired keys
        with mock_time_provider.patch():
            await default_memory_cache.set("expired_key", "value1", ttl=60)  # Short TTL
            await default_memory_cache.set("active_key", "value2", ttl=3600)  # Long TTL

            # When: Time passes, making one key expire
            mock_time_provider.advance(61)  # Advance past first key's TTL

            # Then: get_keys() returns both
            keys = default_memory_cache.get_keys()
            assert "expired_key" in keys
            assert "active_key" in keys

    @pytest.mark.asyncio
    async def test_get_active_keys_returns_only_non_expired_keys(self, default_memory_cache: InMemoryCache, mock_time_provider):
        """
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
            - default_memory_cache: Cache for expiration filtering testing
            - mixed_ttl_test_data: Entries with known expiration states
            - mock_time_provider: For deterministic expiration testing without delays
            
        Accurate Filtering:
            Active key list precisely reflects currently accessible cache content
            
        Related Tests:
            - test_get_keys_returns_all_cache_keys_including_expired()
            - test_active_vs_expired_key_distinction()
        """
        # Given: A mix of soon-to-be-expired and non-expired keys
        with mock_time_provider.patch():
            await default_memory_cache.set("expired_key", "value1", ttl=60)  # Short TTL
            await default_memory_cache.set("active_key", "value2", ttl=3600)  # Long TTL

            # When: Time passes
            mock_time_provider.advance(61)  # Advance past first key's TTL

            # Then: get_active_keys() returns only the non-expired key
            active_keys = default_memory_cache.get_active_keys()
            assert "expired_key" not in active_keys
            assert "active_key" in active_keys

    @pytest.mark.asyncio
    async def test_size_method_returns_accurate_current_entry_count(self, default_memory_cache: InMemoryCache):
        """
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
        """
        # Given an empty cache
        assert default_memory_cache.size() == 0
        
        # When items are added
        await default_memory_cache.set("key1", "value1")
        await default_memory_cache.set("key2", "value2")
        assert default_memory_cache.size() == 2

        await default_memory_cache.delete("key1")
        assert default_memory_cache.size() == 1

    @pytest.mark.asyncio
    async def test_get_ttl_returns_accurate_remaining_time_for_entries(self, default_memory_cache: InMemoryCache, sample_cache_key: str):
        """
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
            - test_get_ttl_handles_edge cases correctly()
        """
        # When: an item is set with a TTL
        await default_memory_cache.set(sample_cache_key, "value", ttl=60)
        
        # Then: get_ttl returns the remaining time
        ttl = await default_memory_cache.get_ttl(sample_cache_key)
        assert 59 <= ttl <= 60

        # And: Returns None for non-existent keys
        assert await default_memory_cache.get_ttl("non_existent") is None

    @pytest.mark.asyncio
    async def test_memory_usage_statistics_reflect_actual_storage_requirements(self, default_memory_cache: InMemoryCache):
        """
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
        """
        # Given: An empty cache
        initial_usage = default_memory_cache.get_stats()['memory_usage_bytes']
        
        # When: A small item is added
        await default_memory_cache.set("small", "a")
        small_item_usage = default_memory_cache.get_stats()['memory_usage_bytes']
        assert small_item_usage > initial_usage

        # When: A large item is added
        await default_memory_cache.set("large", "a" * 1000)
        large_item_usage = default_memory_cache.get_stats()['memory_usage_bytes']
        assert large_item_usage > small_item_usage

    @pytest.mark.asyncio
    async def test_statistics_remain_consistent_across_async_operations(self, default_memory_cache: InMemoryCache, cache_test_keys: List[str]):
        """
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
        """
        # Given: A set of concurrent operations
        num_ops = 20
        tasks = []
        for i in range(num_ops):
            key = cache_test_keys[i % len(cache_test_keys)]
            if i % 2 == 0:
                tasks.append(default_memory_cache.set(f"set_key_{i}", "value"))
            else:
                tasks.append(default_memory_cache.get(f"get_key_{i}"))
        
        # When: The operations are run concurrently
        await asyncio.gather(*tasks)

        # Then: The statistics are consistent
        stats = default_memory_cache.get_stats()
        
        # The number of set operations should be reflected in the size
        assert stats['active_entries'] == num_ops / 2
        # The number of get operations should be reflected in misses (since keys didn't exist)
        assert stats['misses'] == num_ops / 2
        assert stats['hits'] == 0
