---
sidebar_label: test_memory_core_operations
---

# Unit tests for InMemoryCache core operations (get, set, delete, exists).

  file_path: `backend/tests/infrastructure/cache/memory/test_memory_core_operations.py`

This test suite verifies the observable behaviors documented in the
InMemoryCache public contract (memory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

Coverage Focus:
    - Core CacheInterface implementation (get, set, delete, exists)
    - TTL handling and expiration behavior
    - Value storage and retrieval accuracy
    - Key existence checking and validation

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Standard library components (threading, collections): For thread-safe operations and data structures
    - app.core.exceptions: Exception handling for configuration and validation errors

## TestInMemoryCacheCoreOperations

Test suite for InMemoryCache core cache operations implementing CacheInterface.

Scope:
    - get() method behavior with TTL expiration and value retrieval
    - set() method behavior with value storage and TTL configuration
    - delete() method behavior with key removal and cleanup
    - exists() method behavior with key presence validation
    
Business Critical:
    Core operations directly impact application performance and data consistency
    
Test Strategy:
    - Unit tests for each CacheInterface method using fixture data
    - TTL expiration testing using fast_expiry_memory_cache and mock time
    - Data integrity verification using sample cache values
    - Edge case testing for boundary conditions and error scenarios
    
External Dependencies:
    - asyncio: For asynchronous operation support
    - time: For TTL calculations and expiration timing (can be mocked)

### test_get_returns_stored_value_when_key_exists_and_not_expired()

```python
async def test_get_returns_stored_value_when_key_exists_and_not_expired(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any):
```

Test that get() returns the original stored value for valid, non-expired cache entries.

Verifies:
    Previously stored values are retrieved accurately without modification
    
Business Impact:
    Ensures cached data maintains integrity and provides reliable retrieval
    
Scenario:
    Given: Value has been stored in cache using set() method
    When: get() is called with the same cache key before TTL expiration
    Then: Original stored value is returned unchanged
    And: Value type and structure are preserved exactly
    And: No side effects occur during retrieval (no modification)
    
Data Integrity Verified:
    - Complex data structures (dictionaries, lists) returned unchanged by value, not by reference
    - String values returned with original content and encoding
    - Numeric values returned with original precision
    - Boolean and None values returned correctly
    - No serialization artifacts or data corruption
    
Fixtures Used:
    - default_memory_cache: Cache instance for testing operations
    - sample_cache_key: Standard cache key for consistent testing
    - sample_cache_value: Complex data structure for integrity verification
    
Cache Hit Behavior:
    Successful cache hits return exact data without performance degradation
    
Related Tests:
    - test_get_returns_none_when_key_does_not_exist()
    - test_get_returns_none_when_key_expired()
    - test_set_stores_value_successfully_for_retrieval()

### test_get_returns_none_when_key_does_not_exist()

```python
async def test_get_returns_none_when_key_does_not_exist(self, default_memory_cache: InMemoryCache, sample_cache_key: str):
```

Test that get() returns None for non-existent cache keys.

Verifies:
    Cache misses are clearly indicated by None return value
    
Business Impact:
    Allows applications to distinguish between cached data and cache misses
    
Scenario:
    Given: Cache key has never been stored or has been deleted
    When: get() is called with non-existent cache key
    Then: None is returned to indicate cache miss
    And: No exceptions are raised for legitimate misses
    And: Cache state remains unchanged by miss operation
    
Cache Miss Behavior Verified:
    - None return value clearly indicates absence of cached data
    - No side effects from miss operations (no entry creation)
    - Miss operations do not affect other cached entries
    - Performance remains consistent for miss scenarios
    
Fixtures Used:
    - default_memory_cache: Fresh cache instance for miss testing
    - sample_cache_key: Key that has not been stored
    
Clean Miss Handling:
    Cache misses are handled gracefully without errors or state changes
    
Related Tests:
    - test_get_returns_stored_value_when_key_exists_and_not_expired()
    - test_exists_returns_false_for_non_existent_key()

### test_get_returns_none_when_key_expired()

```python
async def test_get_returns_none_when_key_expired(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any, mock_time_provider):
```

Test that get() returns None for expired cache entries and cleans up expired data.

Verifies:
    Expired entries are treated as cache misses and automatically cleaned up
    
Business Impact:
    Ensures stale data is not served and memory is recovered from expired entries
    
Scenario:
    Given: Value was stored with TTL that has now passed
    When: get() is called after TTL expiration time
    Then: None is returned indicating expired entry treated as miss
    And: Expired entry is automatically removed from cache storage
    And: Memory is recovered from expired entry cleanup
    
TTL Expiration Behavior Verified:
    - Entries become inaccessible immediately after TTL expiration
    - Expired entries are automatically cleaned up during get operations
    - Memory usage decreases after expired entry cleanup
    - No stale data is ever returned after expiration
    
Fixtures Used:
    - default_memory_cache: Cache for expiration testing
    - sample_cache_key: Key for storing entry that will expire
    - sample_cache_value: Value to store and verify expiration
    - mock_time_provider: For controlling time advancement without delays
    
Automatic Cleanup Verification:
    Expired entries are removed automatically without manual intervention
    
Related Tests:
    - test_get_returns_stored_value_when_key_exists_and_not_expired()
    - test_automatic_cleanup_removes_expired_entries()

### test_set_stores_value_successfully_for_retrieval()

```python
async def test_set_stores_value_successfully_for_retrieval(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any):
```

Test that set() stores values correctly and makes them available for get() operations.

Verifies:
    Values stored via set() can be successfully retrieved via get()
    
Business Impact:
    Ensures fundamental cache storage functionality works correctly
    
Scenario:
    Given: InMemoryCache instance ready for operations
    When: set() is called with key, value, and optional TTL
    Then: Value is stored and immediately available via get()
    And: Stored value matches original exactly (no corruption)
    And: Cache size increases to reflect new entry
    
Storage Behavior Verified:
    - Values are stored with correct key association
    - Complex data structures maintain integrity during storage
    - Storage operation completes without errors
    - Immediate availability for retrieval after storage
    - Cache statistics reflect storage operation
    
Fixtures Used:
    - default_memory_cache: Cache instance for storage testing
    - sample_cache_key: Key for storage operation
    - sample_cache_value: Complex data for storage integrity testing
    
Storage Integrity:
    Set and get operations work together to provide reliable data storage
    
Related Tests:
    - test_get_returns_stored_value_when_key_exists_and_not_expired()
    - test_set_with_custom_ttl_applies_expiration()

### test_set_with_custom_ttl_applies_expiration()

```python
async def test_set_with_custom_ttl_applies_expiration(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any, mock_time_provider):
```

Test that set() with custom TTL parameter applies correct expiration timing.

Verifies:
    Custom TTL values override default TTL for individual cache entries
    
Business Impact:
    Allows fine-grained control over cache entry lifetimes for different data types
    
Scenario:
    Given: Cache initialized with default TTL configuration
    When: set() is called with custom TTL parameter different from default
    Then: Entry expires according to custom TTL, not default TTL
    And: Other entries with default TTL are unaffected
    And: Custom TTL timing is accurately applied
    
Custom TTL Behavior Verified:
    - Custom TTL overrides default configuration for specific entry
    - Different entries can have different expiration times simultaneously
    - TTL timing is accurate to within reasonable precision
    - Zero or negative TTL values handled according to contract
    
Fixtures Used:
    - default_memory_cache: Cache with known default TTL for comparison
    - sample_cache_key: Key for custom TTL testing
    - sample_cache_value: Value for TTL expiration testing
    - mock_time_provider: For deterministic TTL testing without delays
    
TTL Flexibility:
    Cache supports per-entry TTL customization for diverse use cases
    
Related Tests:
    - test_set_stores_value_successfully_for_retrieval()
    - test_get_returns_none_when_key_expired()

### test_set_with_none_ttl_uses_default_ttl()

```python
async def test_set_with_none_ttl_uses_default_ttl(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any, mock_time_provider):
```

Test that set() with None TTL parameter applies the configured default TTL.

Verifies:
    None TTL parameter results in default TTL application as documented
    
Business Impact:
    Ensures consistent behavior when TTL parameter is explicitly set to None
    
Scenario:
    Given: Cache configured with specific default TTL value
    When: set() is called with ttl=None parameter explicitly
    Then: Default TTL from cache configuration is applied
    And: Entry expiration behavior matches default TTL timing
    And: None TTL is treated equivalently to omitted TTL parameter
    
Default TTL Application Verified:
    - None TTL parameter triggers default TTL usage
    - Default TTL from constructor configuration is applied
    - Behavior is identical to omitting TTL parameter entirely
    - Expiration timing matches configured default
    
Fixtures Used:
    - default_memory_cache: Cache with known default TTL configuration
    - sample_cache_key: Key for default TTL testing
    - sample_cache_value: Value for TTL behavior verification
    - mock_time_provider: For deterministic TTL testing without delays
    
Parameter Consistency:
    None TTL parameter provides predictable default TTL application
    
Related Tests:
    - test_set_with_custom_ttl_applies_expiration()
    - test_set_stores_value_successfully_for_retrieval()

### test_delete_removes_existing_key_successfully()

```python
async def test_delete_removes_existing_key_successfully(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any):
```

Test that delete() removes existing cache entries and frees memory.

Verifies:
    Stored cache entries are completely removed by delete operations
    
Business Impact:
    Enables cache cleanup and memory management for dynamic applications
    
Scenario:
    Given: Cache entry exists and is accessible via get()
    When: delete() is called with the cache key
    Then: Entry is completely removed from cache storage
    And: Subsequent get() returns None indicating removal
    And: Cache size decreases to reflect entry removal
    And: Memory is freed from removed entry
    
Deletion Behavior Verified:
    - Entry becomes immediately inaccessible after deletion
    - Cache storage size decreases appropriately
    - Memory usage decreases after deletion
    - No residual data remains from deleted entry
    - Delete operation completes without errors
    
Fixtures Used:
    - default_memory_cache: Cache instance for deletion testing
    - sample_cache_key: Key of entry to delete
    - sample_cache_value: Value to store before deletion test
    
Complete Removal:
    Deleted entries are thoroughly removed without leaving traces
    
Related Tests:
    - test_delete_non_existent_key_handles_gracefully()
    - test_get_returns_none_when_key_does_not_exist()

### test_delete_non_existent_key_handles_gracefully()

```python
async def test_delete_non_existent_key_handles_gracefully(self, default_memory_cache: InMemoryCache, sample_cache_key: str):
```

Test that delete() handles non-existent keys gracefully without errors.

Verifies:
    Delete operations on non-existent keys complete without raising exceptions
    
Business Impact:
    Provides robust cache management that handles edge cases gracefully
    
Scenario:
    Given: Cache key does not exist in cache storage
    When: delete() is called with non-existent key
    Then: No exception is raised by delete operation
    And: Cache state remains unchanged by invalid delete
    And: Other cache entries are unaffected by invalid delete
    
Graceful Handling Verified:
    - No exceptions raised for non-existent key deletion
    - Cache integrity maintained during invalid delete operations
    - Performance remains consistent for invalid delete scenarios
    - Other cache entries completely unaffected
    
Fixtures Used:
    - default_memory_cache: Cache instance for graceful deletion testing
    - sample_cache_key: Key that has not been stored
    
Robust Error Handling:
    Delete operations are resilient to edge cases and invalid input
    
Related Tests:
    - test_delete_removes_existing_key_successfully()
    - test_exists_returns_false_for_non_existent_key()

### test_exists_returns_true_for_valid_non_expired_entry()

```python
async def test_exists_returns_true_for_valid_non_expired_entry(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any):
```

Test that exists() returns True for stored, non-expired cache entries.

Verifies:
    Key existence checking accurately identifies valid cache entries
    
Business Impact:
    Allows applications to check cache status without retrieving data
    
Scenario:
    Given: Value has been stored with valid TTL remaining
    When: exists() is called with the stored cache key
    Then: True is returned indicating entry exists and is valid
    And: Entry remains unchanged by existence check
    And: No side effects occur from existence checking
    
Existence Check Behavior Verified:
    - True return indicates valid, accessible cache entry
    - Existence check does not modify cache entry or access patterns
    - Check operation has minimal performance impact
    - Results are consistent with get() operation availability
    
Fixtures Used:
    - default_memory_cache: Cache instance for existence testing
    - sample_cache_key: Key for existence verification
    - sample_cache_value: Value to store for existence test
    
Non-Intrusive Checking:
    Existence checks do not affect cache entry state or access patterns
    
Related Tests:
    - test_exists_returns_false_for_non_existent_key()
    - test_exists_returns_false_for_expired_entry()

### test_exists_returns_false_for_non_existent_key()

```python
async def test_exists_returns_false_for_non_existent_key(self, default_memory_cache: InMemoryCache, sample_cache_key: str):
```

Test that exists() returns False for keys that have never been stored.

Verifies:
    Existence checking correctly identifies absence of cache entries
    
Business Impact:
    Enables applications to avoid unnecessary cache operations on missing data
    
Scenario:
    Given: Cache key has never been stored in cache
    When: exists() is called with non-existent key
    Then: False is returned indicating key does not exist
    And: No side effects occur from checking non-existent key
    And: Cache state remains unchanged by existence check
    
Non-Existence Detection Verified:
    - False return clearly indicates key absence
    - Check operation does not create entries or side effects
    - Performance remains consistent for non-existent key checks
    - Results align with get() method behavior for missing keys
    
Fixtures Used:
    - default_memory_cache: Fresh cache instance for non-existence testing
    - sample_cache_key: Key that has not been stored
    
    
Accurate Detection:
    Existence checks provide reliable information about cache state
    
Related Tests:
    - test_exists_returns_true_for_valid_non_expired_entry()
    - test_get_returns_none_when_key_does_not_exist()

### test_exists_returns_false_for_expired_entry()

```python
async def test_exists_returns_false_for_expired_entry(self, default_memory_cache: InMemoryCache, sample_cache_key: str, sample_cache_value: Any, mock_time_provider):
```

Test that exists() returns False for expired cache entries and triggers cleanup.

Verifies:
    Expired entries are correctly identified as non-existent and cleaned up
    
Business Impact:
    Ensures applications receive accurate cache state information and expired data is removed
    
Scenario:
    Given: Cache entry was stored with TTL that has now expired
    When: exists() is called with expired entry key
    Then: False is returned indicating entry no longer exists
    And: Expired entry is automatically removed during existence check
    And: Memory is recovered from expired entry cleanup
    
Expiration Detection Verified:
    - Expired entries return False from exists() check
    - Automatic cleanup occurs during expiration detection
    - Memory usage decreases after expired entry removal
    - Behavior consistent with get() method expiration handling
    
Fixtures Used:
    - default_memory_cache: Cache for expiration testing
    - sample_cache_key: Key for entry that will expire
    - sample_cache_value: Value to store and verify expiration
    - mock_time_provider: For deterministic expiration testing without delays
    
Automatic Maintenance:
    Cache automatically maintains accuracy through expiration cleanup
    
Related Tests:
    - test_exists_returns_true_for_valid_non_expired_entry()
    - test_get_returns_none_when_key_expired()
