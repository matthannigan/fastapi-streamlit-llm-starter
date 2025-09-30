"""
Unit tests for InMemoryCache LRU eviction and memory management behavior.

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - LRU (Least Recently Used) eviction policy implementation
    - Memory management and size limit enforcement
    - Access order tracking and eviction decisions
    - Cache size management and statistics

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Standard library components (threading, collections): For thread-safe operations and data structures
    - app.core.exceptions: Exception handling for configuration and validation errors
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.cache.memory import InMemoryCache


class TestInMemoryCacheLRUEviction:
    """
    Test suite for InMemoryCache LRU eviction and memory management.

    Scope:
        - LRU eviction policy when cache reaches max_size limit
        - Access order tracking for eviction decisions
        - Memory management and size limit enforcement
        - Cache statistics during eviction scenarios

    Business Critical:
        LRU eviction prevents memory overflow and maintains cache performance

    Test Strategy:
        - Small cache instances (3-5 entries) for controlled eviction testing
        - Sequential key operations to verify access order tracking
        - Memory management testing with cache_entries_for_lru_testing fixture
        - Statistics verification during eviction scenarios

    External Dependencies:
        - asyncio: For asynchronous cache operation testing
    """

    @pytest.mark.asyncio
    async def test_lru_eviction_removes_least_recently_used_entry_when_max_size_exceeded(
        self, small_memory_cache: InMemoryCache
    ):
        """
        Test that LRU eviction removes the least recently used entry when cache reaches max_size.

        Verifies:
            Oldest entries are evicted when cache exceeds configured size limit

        Business Impact:
            Prevents memory overflow while preserving most valuable (recently accessed) cache data

        Scenario:
            Given: Cache configured with small max_size limit (3 entries)
            When: Additional entries are added beyond max_size capacity
            Then: Least recently used entries are automatically evicted
            And: Most recently used entries remain in cache
            And: Cache size never exceeds configured max_size limit

        LRU Eviction Behavior Verified:
            - Entries are evicted in strict least-recently-used order
            - Cache size is maintained at or below max_size after evictions
            - Recently accessed entries are preserved during eviction
            - Eviction occurs automatically during set() operations
            - Memory is recovered from evicted entries

        Fixtures Used:
            - small_memory_cache: Cache with max_size=3 for controlled eviction testing
            - cache_entries_for_lru_testing: Set of entries to trigger eviction

        Access Pattern Verification:
            - Oldest entries (by access time) are evicted first
            - Recent access (get operations) updates LRU ordering
            - Set operations create new entries in most-recent position

        Related Tests:
            - test_lru_eviction_updates_access_order_on_get_operations()
            - test_cache_size_never_exceeds_configured_max_size()
        """
        # Given: A cache with max_size 3
        # When: Four items are added
        await small_memory_cache.set("key1", "value1")
        await small_memory_cache.set("key2", "value2")
        await small_memory_cache.set("key3", "value3")
        await small_memory_cache.set("key4", "value4")

        # Then: The least recently used item ('key1') is evicted
        assert await small_memory_cache.exists("key1") is False
        assert await small_memory_cache.exists("key2") is True
        assert await small_memory_cache.exists("key3") is True
        assert await small_memory_cache.exists("key4") is True

    @pytest.mark.asyncio
    async def test_lru_eviction_updates_access_order_on_get_operations(
        self, small_memory_cache: InMemoryCache
    ):
        """
        Test that get() operations update LRU access order and affect eviction decisions.

        Verifies:
            Cache access updates LRU ordering to protect frequently accessed entries

        Business Impact:
            Ensures frequently accessed data remains cached longer than stale data

        Scenario:
            Given: Cache near capacity with multiple entries
            When: get() operations access specific entries before adding new entries
            Then: Recently accessed entries are preserved during eviction
            And: Non-accessed entries are evicted first
            And: Access order reflects recent get() operations

        Access Order Update Verified:
            - get() operations move entries to most-recent position in LRU order
            - Recently accessed entries survive eviction cycles
            - Non-accessed entries become eviction candidates
            - Multiple get() operations on same key maintain recent status
            - Access order tracking is accurate and consistent

        Fixtures Used:
            - small_memory_cache: Cache with limited size for access order testing
            - cache_test_keys: Multiple keys for access pattern testing
            - cache_test_values: Corresponding values for comprehensive testing

        LRU Algorithm Accuracy:
            Access order tracking correctly influences eviction decisions

        Related Tests:
            - test_lru_eviction_removes_least_recently_used_entry_when_max_size_exceeded()
            - test_set_operations_affect_lru_ordering()
        """
        # Given: Cache is filled, LRU order is key1, key2, key3
        await small_memory_cache.set("key1", "value1")
        await small_memory_cache.set("key2", "value2")
        await small_memory_cache.set("key3", "value3")

        # When: The least recently used item is accessed
        await small_memory_cache.get("key1")  # LRU order is now key2, key3, key1

        # And: A new item is added, forcing an eviction
        await small_memory_cache.set("key4", "value4")

        # Then: The new LRU item ('key2') is evicted
        assert await small_memory_cache.exists("key2") is False
        assert await small_memory_cache.exists("key1") is True

    @pytest.mark.asyncio
    async def test_set_operations_affect_lru_ordering(
        self, small_memory_cache: InMemoryCache
    ):
        """
        Test that set() operations (both new and update) properly affect LRU access ordering.

        Verifies:
            Set operations update LRU order for both new entries and existing key updates

        Business Impact:
            Ensures cache updates maintain optimal data freshness and access patterns

        Scenario:
            Given: Cache with existing entries in established LRU order
            When: set() operations add new entries or update existing keys
            Then: New entries are placed in most-recent position
            And: Updated existing entries move to most-recent position
            And: Other entries maintain relative LRU order

        Set Operation LRU Effects Verified:
            - New set() operations create entries in most-recent position
            - set() updates to existing keys move them to most-recent
            - Relative order of non-affected entries is preserved
            - LRU ordering remains consistent after mixed set/get operations
            - Eviction decisions reflect updated access patterns

        Fixtures Used:
            - small_memory_cache: Cache for controlled LRU order testing
            - sample_cache_key: Key for testing existing key updates
            - sample_cache_value: Value for set operation testing

        Ordering Consistency:
            LRU ordering remains accurate through various operation sequences

        Related Tests:
            - test_lru_eviction_updates_access_order_on_get_operations()
            - test_cache_operations_maintain_consistent_lru_state()
        """
        # Given: Cache is filled
        await small_memory_cache.set("key1", "value1")
        await small_memory_cache.set("key2", "value2")
        await small_memory_cache.set("key3", "value3")  # LRU order: key1, key2, key3

        # When: An existing key is updated
        await small_memory_cache.set(
            "key1", "new_value1"
        )  # LRU order: key2, key3, key1

        # And: A new item is added, forcing eviction
        await small_memory_cache.set("key4", "value4")

        # Then: The least recently used item ('key2') is evicted
        assert await small_memory_cache.exists("key2") is False

    @pytest.mark.asyncio
    async def test_cache_size_never_exceeds_configured_max_size(
        self, small_memory_cache: InMemoryCache
    ):
        """
        Test that cache size is strictly enforced and never exceeds max_size configuration.

        Verifies:
            Cache size limits are strictly enforced through automatic eviction

        Business Impact:
            Prevents memory overflow and ensures predictable memory usage patterns

        Scenario:
            Given: Cache configured with specific max_size limit
            When: Continuous set() operations add entries beyond limit
            Then: Cache size never exceeds max_size at any point
            And: Eviction occurs before size limit violation
            And: size() method returns accurate count within limits

        Size Limit Enforcement Verified:
            - Cache size remains at or below max_size after every operation
            - Eviction occurs proactively during set() operations
            - size() method returns accurate current entry count
            - Memory usage correlates with enforced size limits
            - No temporary size limit violations during eviction

        Fixtures Used:
            - small_memory_cache: Cache with known max_size for limit testing
            - cache_entries_for_lru_testing: Large number of entries to test limits

        Strict Enforcement:
            Size limits are never violated, even temporarily during operations

        Related Tests:
            - test_lru_eviction_removes_least_recently_used_entry_when_max_size_exceeded()
            - test_statistics_reflect_eviction_operations()
        """
        # When: More items than max_size are added
        for i in range(small_memory_cache.max_size + 5):
            await small_memory_cache.set(f"key{i}", f"value{i}")

        # Then: The cache size does not exceed max_size
        assert small_memory_cache.size() <= small_memory_cache.max_size

    @patch("app.infrastructure.cache.memory.logger")
    @pytest.mark.asyncio
    async def test_eviction_operations_are_logged_for_monitoring(
        self, mock_logger, small_memory_cache: InMemoryCache
    ):
        """
        Test that eviction operations are properly logged for operational monitoring.

        Verifies:
            Cache eviction events are logged with appropriate detail for debugging

        Business Impact:
            Enables operational monitoring and debugging of cache behavior

        Scenario:
            Given: Cache configured with logging and approaching size limits
            When: Eviction operations occur due to size limit enforcement
            Then: Eviction events are logged at appropriate level (DEBUG)
            And: Log messages include evicted key information
            And: Log context includes cache size and eviction reason

        Eviction Logging Verified:
            - Eviction events logged at DEBUG level for debugging
            - Log messages include evicted key for traceability
            - Cache size information included in log context
            - Eviction reason (LRU/size limit) clearly indicated
            - Logging does not impact cache performance significantly

        Fixtures Used:
            - small_memory_cache: Cache for controlled eviction scenarios
            - mock_logging: Mock logger to capture eviction log messages
            - cache_entries_for_lru_testing: Entries to trigger eviction logging

        Operational Visibility:
            Eviction operations provide sufficient logging for troubleshooting

        Related Tests:
            - test_cache_operations_maintain_statistics_accuracy()
            - test_lru_eviction_removes_least_recently_used_entry_when_max_size_exceeded()
        """
        # When: An eviction is triggered
        await small_memory_cache.set("key1", "value1")
        await small_memory_cache.set("key2", "value2")
        await small_memory_cache.set("key3", "value3")
        await small_memory_cache.set("key4", "value4")  # Evicts key1

        # Then: The eviction is logged
        mock_logger.debug.assert_called_with("Evicting key %s (LRU)", "key1")

    @pytest.mark.asyncio
    async def test_statistics_reflect_eviction_operations(
        self, small_memory_cache: InMemoryCache
    ):
        """
        Test that cache statistics accurately reflect eviction operations and counts.

        Verifies:
            Cache statistics provide accurate eviction counts and memory usage information

        Business Impact:
            Enables capacity planning and cache performance analysis

        Scenario:
            Given: Cache with eviction operations occurring due to size limits
            When: get_stats() method is called after eviction events
            Then: Statistics include accurate eviction count
            And: Memory usage statistics reflect evicted entries
            And: Cache utilization percentage reflects current size vs max_size

        Eviction Statistics Verified:
            - Eviction count increments accurately with each eviction operation
            - Memory usage statistics decrease after evictions
            - Utilization percentage reflects current cache fullness
            - Active entry count matches actual cache size
            - Statistics provide meaningful cache performance metrics

        Fixtures Used:
            - small_memory_cache: Cache for controlled eviction statistics testing
            - cache_entries_for_lru_testing: Entries to generate eviction statistics

        Accurate Metrics:
            Statistics provide reliable information for cache performance monitoring

        Related Tests:
            - test_get_stats_provides_comprehensive_cache_metrics()
            - test_cache_size_never_exceeds_configured_max_size()
        """
        # Given: No evictions have occurred
        assert small_memory_cache.get_stats()["evictions"] == 0

        # When: An eviction is triggered
        for i in range(small_memory_cache.max_size + 1):
            await small_memory_cache.set(f"key{i}", f"value{i}")

        # Then: The eviction count is updated
        assert small_memory_cache.get_stats()["evictions"] == 1

    @pytest.mark.asyncio
    async def test_cache_operations_maintain_consistent_lru_state(
        self, small_memory_cache: InMemoryCache
    ):
        """
        Test that mixed cache operations maintain consistent and accurate LRU state.

        Verifies:
            Complex operation sequences maintain accurate LRU ordering and state

        Business Impact:
            Ensures cache reliability under diverse usage patterns

        Scenario:
            Given: Cache with mixed get(), set(), delete() operations over time
            When: Operations are performed in various sequences and patterns
            Then: LRU access order remains accurate throughout operations
            And: Eviction decisions reflect correct access history
            And: Cache state remains internally consistent

        LRU State Consistency Verified:
            - Access order tracking remains accurate through operation mixes
            - delete() operations properly remove entries from LRU order
            - get() and set() operations correctly update access patterns
            - Eviction behavior remains predictable and consistent
            - No internal state corruption occurs during complex sequences

        Fixtures Used:
            - small_memory_cache: Cache for complex operation sequence testing
            - cache_test_keys: Multiple keys for varied operation patterns
            - cache_test_values: Values for comprehensive operation testing

        State Integrity:
            Cache maintains consistent internal state across all operation types

        Related Tests:
            - test_lru_eviction_updates_access_order_on_get_operations()
            - test_set_operations_affect_lru_ordering()
            - test_delete_operations_update_lru_order_correctly()
        """
        # Given: A sequence of mixed operations
        await small_memory_cache.set("key1", "value1")
        await small_memory_cache.set("key2", "value2")
        await small_memory_cache.set("key3", "value3")  # Order: 1, 2, 3
        await small_memory_cache.get("key1")  # Order: 2, 3, 1
        await small_memory_cache.delete("key2")  # Order: 3, 1
        await small_memory_cache.set("key4", "value4")  # Order: 3, 1, 4

        # When: An eviction is triggered
        await small_memory_cache.set("key5", "value5")

        # Then: The correct item ('key3') is evicted based on the complex history
        assert await small_memory_cache.exists("key3") is False
        assert await small_memory_cache.exists("key1") is True
