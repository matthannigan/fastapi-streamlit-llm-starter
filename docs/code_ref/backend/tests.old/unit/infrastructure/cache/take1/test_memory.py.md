---
sidebar_label: test_memory
---

# Comprehensive unit tests for InMemoryCache implementation following docstring-driven development.

  file_path: `backend/tests.old/unit/infrastructure/cache/take1/test_memory.py`

This test module verifies the core behavior and contracts defined in the InMemoryCache docstrings,
focusing on observable behavior rather than implementation details. Tests cover TTL expiration,
LRU eviction, statistics monitoring, and async safety per the documented contracts.

Test Classes:
    TestInMemoryCacheBasics: Core cache operations (get, set, delete, exists)
    TestInMemoryCacheTTL: Time-to-live expiration behavior and cleanup
    TestInMemoryCacheLRU: LRU eviction policy and capacity management
    TestInMemoryCacheStatistics: Monitoring and statistics features
    TestInMemoryCacheEdgeCases: Error handling and boundary conditions
    TestInMemoryCacheAsync: Async behavior and concurrent access patterns

Coverage Target: >90% (infrastructure requirement)
Focus: Test behavior contracts from docstrings, not internal implementation

## CacheInterface

Basic cache interface.

### get()

```python
async def get(self, key: str):
```

### set()

```python
async def set(self, key: str, value: Any, ttl: Optional[int] = None):
```

### delete()

```python
async def delete(self, key: str):
```

## InMemoryCache

In-memory cache implementation for testing.

### __init__()

```python
def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
```

### get()

```python
async def get(self, key: str) -> Any:
```

### set()

```python
async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

### delete()

```python
async def delete(self, key: str) -> None:
```

### clear()

```python
def clear(self) -> None:
```

### size()

```python
def size(self) -> int:
```

### get_stats()

```python
def get_stats(self) -> Dict[str, Any]:
```

### get_keys()

```python
def get_keys(self) -> list:
```

### get_active_keys()

```python
def get_active_keys(self) -> list:
```

### exists()

```python
async def exists(self, key: str) -> bool:
```

### get_ttl()

```python
async def get_ttl(self, key: str) -> Optional[int]:
```

## TestInMemoryCacheBasics

Test basic cache operations per InMemoryCache docstring contracts.

Tests core cache interface behavior: get, set, delete, exists operations
following the documented contracts in the class and method docstrings.

### cache()

```python
def cache(self):
```

Create fresh cache instance for each test to ensure isolation.

### test_get_nonexistent_key_returns_none()

```python
async def test_get_nonexistent_key_returns_none(self, cache):
```

Test that cache get() returns None for nonexistent keys per docstring contract.

Business Impact:
    Ensures consistent behavior for cache misses, allowing graceful fallback handling
    
Scenario:
    Given: Empty cache with no stored entries
    When: get() called with any key
    Then: Returns None as documented in get() method docstring
    
Docstring Contract:
    "Returns cached value if found and not expired, None otherwise"

### test_set_and_get_preserves_value_type()

```python
async def test_set_and_get_preserves_value_type(self, cache):
```

Test that cache preserves original data types through set/get cycle per docstring.

Business Impact:
    Ensures type safety for cached data, preventing serialization issues
    
Scenario:
    Given: Various data types (dict, list, string, int, bool)
    When: Data stored via set() and retrieved via get()
    Then: Original types and values are preserved exactly
    
Docstring Contract:
    get(): "preserving original data types and structure"
    set(): "Stores value with type preservation where possible"

### test_set_overwrites_existing_key()

```python
async def test_set_overwrites_existing_key(self, cache):
```

Test that set() overwrites existing values for same key per docstring behavior.

Business Impact:
    Ensures cache updates work correctly for changing data
    
Scenario:
    Given: Key already exists in cache with value1
    When: set() called with same key and value2
    Then: get() returns value2, not value1
    
Docstring Contract:
    set(): "Overwrites existing values for the same key"

### test_delete_removes_existing_key()

```python
async def test_delete_removes_existing_key(self, cache):
```

Test that delete() removes cached entries immediately per docstring contract.

Business Impact:
    Ensures cache invalidation works correctly for data consistency
    
Scenario:
    Given: Key exists in cache with a value
    When: delete() called on the key
    Then: Subsequent get() returns None
    
Docstring Contract:
    delete(): "Removes cache entry immediately if present"

### test_delete_nonexistent_key_is_noop()

```python
async def test_delete_nonexistent_key_is_noop(self, cache):
```

Test that delete() gracefully handles nonexistent keys per docstring behavior.

Business Impact:
    Prevents errors when attempting to delete already-removed cache entries
    
Scenario:
    Given: Key does not exist in cache
    When: delete() called on the key
    Then: Operation succeeds without error (idempotent behavior)
    
Docstring Contract:
    delete(): "No-op for non-existent keys (graceful handling)"
    delete(): "Success regardless of key existence for idempotent behavior"

### test_exists_returns_correct_boolean()

```python
async def test_exists_returns_correct_boolean(self, cache):
```

Test that exists() correctly identifies key presence per method contract.

Business Impact:
    Enables efficient cache key checking without retrieving full values
    
Scenario:
    Given: Some keys exist, others don't
    When: exists() called on various keys
    Then: Returns True for existing keys, False for missing keys
    
Method Contract:
    exists(): "True if key exists and is not expired, False otherwise"

## TestInMemoryCacheTTL

Test TTL (time-to-live) expiration behavior per InMemoryCache docstring contracts.

Tests automatic expiration of cache entries based on TTL configuration,
cleanup behavior, and TTL-related method contracts.

### cache()

```python
def cache(self):
```

Create cache with short default TTL for testing expiration.

### test_set_uses_default_ttl_when_none_specified()

```python
async def test_set_uses_default_ttl_when_none_specified(self, cache):
```

Test that set() applies default TTL when no explicit ttl provided per docstring.

Business Impact:
    Ensures consistent expiration behavior for cache entries
    
Scenario:
    Given: Cache configured with default_ttl=2 seconds
    When: set() called without ttl parameter
    Then: Entry expires after default TTL period
    
Docstring Contract:
    __init__(): "Applied when set() called without explicit ttl parameter"
    set(): "If None, uses implementation default or no expiration"

### test_set_with_custom_ttl_overrides_default()

```python
async def test_set_with_custom_ttl_overrides_default(self, cache):
```

Test that explicit TTL parameter overrides default TTL per set() docstring.

Business Impact:
    Allows flexible expiration times for different types of cached data
    
Scenario:
    Given: Cache with default_ttl=2 seconds
    When: set() called with custom ttl=1 second
    Then: Entry expires after custom TTL, not default TTL
    
Docstring Contract:
    set(): "ttl: Optional time-to-live in seconds for automatic expiration"

### test_set_with_zero_ttl_disables_expiration()

```python
async def test_set_with_zero_ttl_disables_expiration(self, cache):
```

Test that TTL=0 creates entries with no expiration per documented behavior.

Business Impact:
    Allows permanent caching of critical data that shouldn't expire
    
Scenario:
    Given: Cache entry set with ttl=0
    When: Time passes beyond default TTL
    Then: Entry remains accessible (no expiration)
    
Expected Behavior:
    Zero TTL should disable expiration for this entry

### test_expired_entries_cleaned_during_get()

```python
async def test_expired_entries_cleaned_during_get(self, cache):
```

Test that expired entries are automatically cleaned during get() operations.

Business Impact:
    Prevents memory leaks by automatically removing expired entries
    
Scenario:
    Given: Cache entry that has expired
    When: get() called on expired entry
    Then: Entry is removed and None returned
    
Docstring Contract:
    get(): "Check if entry has expired" and automatic cleanup

### test_exists_removes_expired_entries()

```python
async def test_exists_removes_expired_entries(self, cache):
```

Test that exists() method removes expired entries per method docstring.

Business Impact:
    Ensures exists() provides accurate results and maintains cache hygiene
    
Scenario:
    Given: Cache entry that has expired
    When: exists() called on expired entry
    Then: Returns False and removes entry from cache
    
Docstring Contract:
    exists(): "Clean up expired entry" when expired entry found

### test_get_ttl_returns_remaining_time()

```python
async def test_get_ttl_returns_remaining_time(self, cache):
```

Test that get_ttl() returns accurate remaining time per method docstring.

Business Impact:
    Allows applications to make decisions based on cache entry lifetime
    
Scenario:
    Given: Cache entry with known TTL
    When: get_ttl() called before expiration
    Then: Returns remaining seconds (approximately)
    
Method Contract:
    get_ttl(): "Remaining TTL in seconds, None if key doesn't exist or has no expiration"

### test_get_ttl_returns_none_for_no_expiration()

```python
async def test_get_ttl_returns_none_for_no_expiration(self, cache):
```

Test that get_ttl() returns None for entries without expiration.

Business Impact:
    Distinguishes between expiring and permanent cache entries
    
Scenario:
    Given: Cache entry set with ttl=0 (no expiration)
    When: get_ttl() called
    Then: Returns None
    
Method Contract:
    get_ttl(): "None if key doesn't exist or has no expiration"

### test_get_ttl_returns_none_for_nonexistent_key()

```python
async def test_get_ttl_returns_none_for_nonexistent_key(self, cache):
```

Test that get_ttl() returns None for nonexistent keys per docstring.

Business Impact:
    Provides consistent behavior for missing cache keys
    
Scenario:
    Given: Key does not exist in cache
    When: get_ttl() called
    Then: Returns None
    
Method Contract:
    get_ttl(): "None if key doesn't exist or has no expiration"

## TestInMemoryCacheLRU

Test LRU (Least Recently Used) eviction behavior per InMemoryCache docstring contracts.

Tests capacity management, eviction policies, and access order tracking
as documented in the cache implementation.

### small_cache()

```python
def small_cache(self):
```

Create cache with small max_size for testing eviction.

### test_cache_respects_max_size_limit()

```python
async def test_cache_respects_max_size_limit(self, small_cache):
```

Test that cache enforces max_size limit through LRU eviction per docstring.

Business Impact:
    Prevents unbounded memory growth by limiting cache size
    
Scenario:
    Given: Cache with max_size=3
    When: 4 entries are added
    Then: Only 3 most recent entries remain
    
Docstring Contract:
    __init__(): "Maximum cache entries (1-100000) before LRU eviction"
    set(): "Evict LRU entries if needed"

### test_get_updates_lru_order()

```python
async def test_get_updates_lru_order(self, small_cache):
```

Test that get() operations update LRU access order per docstring behavior.

Business Impact:
    Ensures frequently accessed items remain cached longer
    
Scenario:
    Given: Cache at capacity with keys in order: key1, key2, key3
    When: key1 is accessed via get(), then key4 is added
    Then: key2 is evicted (now least recently used), not key1
    
Docstring Contract:
    get(): "Update access order for LRU"

### test_set_updates_lru_order_for_existing_keys()

```python
async def test_set_updates_lru_order_for_existing_keys(self, small_cache):
```

Test that set() on existing keys updates their LRU position per behavior.

Business Impact:
    Ensures cache updates also refresh access order
    
Scenario:
    Given: Cache at capacity with keys: key1, key2, key3
    When: key1 is updated via set(), then key4 is added
    Then: key2 is evicted, not key1 (which was refreshed)
    
Docstring Contract:
    set(): "Update access order" and "Overwrites existing values"

### test_eviction_happens_before_adding_new_entry()

```python
async def test_eviction_happens_before_adding_new_entry(self, small_cache):
```

Test that LRU eviction occurs before adding new entries per implementation.

Business Impact:
    Ensures cache never exceeds max_size limit during operations
    
Scenario:
    Given: Cache exactly at max_size capacity
    When: New entry is added
    Then: Eviction occurs first, maintaining size limit
    
Implementation Behavior:
    set() calls _evict_lru_if_needed() before adding new entries

## TestInMemoryCacheStatistics

Test statistics and monitoring features per InMemoryCache docstring contracts.

Tests cache metrics, utilization tracking, and monitoring capabilities
as documented in the get_stats() method and class overview.

### cache()

```python
def cache(self):
```

Create cache for statistics testing.

### test_get_stats_returns_required_fields()

```python
def test_get_stats_returns_required_fields(self, cache):
```

Test that get_stats() returns all documented statistics fields.

Business Impact:
    Enables comprehensive cache monitoring and performance analysis
    
Scenario:
    Given: Fresh cache instance
    When: get_stats() called
    Then: Returns dictionary with all documented metrics
    
Docstring Contract:
    get_stats(): "Dictionary containing cache statistics" with specific fields

### test_stats_track_total_entries_correctly()

```python
async def test_stats_track_total_entries_correctly(self, cache):
```

Test that statistics accurately track total entry count per contract.

Business Impact:
    Provides accurate cache size monitoring for capacity planning
    
Scenario:
    Given: Empty cache
    When: Entries are added and removed
    Then: total_entries reflects actual count accurately
    
Statistical Contract:
    get_stats(): Accurate count of all entries including expired

### test_stats_distinguish_active_vs_expired_entries()

```python
async def test_stats_distinguish_active_vs_expired_entries(self, cache):
```

Test that statistics correctly separate active from expired entries.

Business Impact:
    Enables monitoring of cache health and expiration effectiveness
    
Scenario:
    Given: Mix of active and expired entries
    When: get_stats() called
    Then: active_entries + expired_entries = total_entries
    
Statistical Contract:
    get_stats(): Accurate separation of active vs expired entries

### test_stats_calculate_utilization_correctly()

```python
def test_stats_calculate_utilization_correctly(self, cache):
```

Test that utilization statistics are calculated accurately per contract.

Business Impact:
    Provides capacity utilization metrics for performance monitoring
    
Scenario:
    Given: Cache with max_size=100 and some entries
    When: get_stats() called
    Then: utilization_percent = (total_entries / max_size) * 100
    
Statistical Contract:
    get_stats(): Accurate utilization percentage calculation

### test_stats_utilization_with_entries()

```python
async def test_stats_utilization_with_entries(self, cache):
```

Test utilization calculation with actual entries.

Business Impact:
    Verifies utilization metrics accuracy for monitoring
    
Scenario:
    Given: 25 entries in cache with max_size=100
    When: get_stats() called
    Then: utilization_percent = 25.0

### test_size_method_returns_current_count()

```python
def test_size_method_returns_current_count(self, cache):
```

Test that size() method returns accurate entry count per method contract.

Business Impact:
    Provides simple cache size checking for application logic
    
Scenario:
    Given: Cache with known number of entries
    When: size() called
    Then: Returns exact count of cache entries
    
Method Contract:
    size(): "Number of cache entries"

### test_size_reflects_actual_entries()

```python
async def test_size_reflects_actual_entries(self, cache):
```

Test that size() reflects actual entry count after operations.

### test_get_keys_returns_all_keys()

```python
async def test_get_keys_returns_all_keys(self, cache):
```

Test that get_keys() returns all keys including expired per method contract.

Business Impact:
    Enables cache introspection for debugging and monitoring
    
Scenario:
    Given: Cache with active and expired entries
    When: get_keys() called
    Then: Returns all keys regardless of expiration status
    
Method Contract:
    get_keys(): "List of cache keys (including expired ones)"

### test_get_active_keys_excludes_expired()

```python
async def test_get_active_keys_excludes_expired(self, cache):
```

Test that get_active_keys() returns only non-expired keys per contract.

Business Impact:
    Enables filtering of valid cache entries for application logic
    
Scenario:
    Given: Cache with active and expired entries
    When: get_active_keys() called
    Then: Returns only keys that haven't expired
    
Method Contract:
    get_active_keys(): "List of active cache keys" (non-expired)

## TestInMemoryCacheEdgeCases

Test edge cases and error handling per InMemoryCache docstring contracts.

Tests boundary conditions, error scenarios, and resilient behavior
as documented in the implementation.

### cache()

```python
def cache(self):
```

Create cache for edge case testing.

### test_clear_removes_all_entries()

```python
def test_clear_removes_all_entries(self, cache):
```

Test that clear() removes all cached entries per method contract.

Business Impact:
    Enables complete cache reset for testing and cleanup operations
    
Scenario:
    Given: Cache with multiple entries
    When: clear() called
    Then: All entries removed, size becomes 0
    
Method Contract:
    clear(): "Clear all entries from the cache"

### test_clear_removes_all_entries_async_setup()

```python
async def test_clear_removes_all_entries_async_setup(self, cache):
```

Setup entries and test clear functionality.

### test_operations_are_resilient_to_exceptions()

```python
async def test_operations_are_resilient_to_exceptions(self, cache):
```

Test that cache operations handle errors gracefully per docstring design.

Business Impact:
    Ensures cache failures don't crash application, maintaining service availability
    
Scenario:
    Given: Cache operation encounters internal error
    When: Exception occurs during operation
    Then: Method returns sensible default without raising
    
Docstring Contract:
    "Cache operations never raise exceptions to calling code"
    "Failed operations are logged and return sensible defaults"

### test_negative_ttl_handled_gracefully()

```python
async def test_negative_ttl_handled_gracefully(self, cache):
```

Test that negative TTL values are handled appropriately.

Business Impact:
    Prevents configuration errors from causing cache failures
    
Scenario:
    Given: set() called with negative TTL
    When: Cache processes the entry
    Then: Entry behavior is predictable (likely immediate expiration)

### test_very_large_ttl_handled_correctly()

```python
async def test_very_large_ttl_handled_correctly(self, cache):
```

Test that very large TTL values work correctly.

Business Impact:
    Supports long-term caching scenarios without overflow issues
    
Scenario:
    Given: Entry set with very large TTL (years)
    When: Entry is accessed
    Then: Entry remains accessible without time calculation issues

### test_empty_string_key_handled_correctly()

```python
async def test_empty_string_key_handled_correctly(self, cache):
```

Test that empty string keys are handled appropriately.

Business Impact:
    Prevents edge case key values from causing cache errors
    
Scenario:
    Given: Operations called with empty string key
    When: Cache processes the operations
    Then: Operations complete without error

### test_none_value_storage()

```python
async def test_none_value_storage(self, cache):
```

Test that None values can be stored and retrieved correctly.

Business Impact:
    Allows caching of None results to avoid repeated expensive operations
    
Scenario:
    Given: None value stored in cache
    When: Retrieved via get()
    Then: None is returned (distinguishable from cache miss)

## TestInMemoryCacheAsync

Test async behavior and concurrent access patterns per InMemoryCache contracts.

Tests async safety, concurrent operations, and proper async interface implementation
as documented in the cache interface and implementation.

### cache()

```python
def cache(self):
```

Create cache for async testing.

### test_all_interface_methods_are_async()

```python
async def test_all_interface_methods_are_async(self, cache):
```

Test that core interface methods are properly async per CacheInterface contract.

Business Impact:
    Ensures compatibility with async application frameworks
    
Scenario:
    Given: Cache instance implementing CacheInterface
    When: Core methods called with await
    Then: Methods execute as proper coroutines
    
Interface Contract:
    All CacheInterface methods must be async/awaitable

### test_concurrent_operations_are_safe()

```python
async def test_concurrent_operations_are_safe(self, cache):
```

Test that concurrent cache operations don't corrupt data per docstring design.

Business Impact:
    Ensures cache reliability under concurrent load in async applications
    
Scenario:
    Given: Multiple async operations running concurrently
    When: Operations access same and different keys simultaneously
    Then: All operations complete successfully with correct results
    
Docstring Contract:
    "Thread-safe for single event loop concurrent access"

### test_cleanup_during_concurrent_access()

```python
async def test_cleanup_during_concurrent_access(self, cache):
```

Test that cleanup operations work correctly during concurrent access.

Business Impact:
    Ensures cache maintenance doesn't interfere with ongoing operations
    
Scenario:
    Given: Concurrent read/write operations with expiring entries
    When: Cleanup occurs during concurrent access
    Then: Valid entries remain accessible, expired entries are removed
