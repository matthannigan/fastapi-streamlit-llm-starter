---
sidebar_label: conftest
---

# Test fixtures for InMemoryCache unit tests.

  file_path: `backend/tests/infrastructure/cache/memory/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the memory.pyi file.

Fixture Categories:
    - Basic test data fixtures (sample keys, values, TTL values)
    - InMemoryCache instance fixtures (various configurations)
    - Mock dependency fixtures (if needed for external integrations)
    - Test scenario fixtures (cache state setups for specific tests)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateful mocks maintain internal state for realistic behavior

## sample_simple_value()

```python
def sample_simple_value():
```

Simple cache value (string) for basic testing scenarios.

Provides a simple string value to test basic cache operations
without the complexity of nested data structures.

## small_memory_cache()

```python
def small_memory_cache():
```

InMemoryCache instance with small configuration for LRU eviction testing.

Provides an InMemoryCache instance with reduced size limits
to facilitate testing of LRU eviction behavior without
needing to create thousands of entries.

Configuration:
    - default_ttl: 300 seconds (5 minutes)
    - max_size: 3 entries (for easy eviction testing)

## fast_expiry_memory_cache()

```python
def fast_expiry_memory_cache():
```

InMemoryCache instance with short default TTL for expiration testing.

Provides an InMemoryCache instance configured with short TTL
to facilitate testing of cache expiration behavior without
long test execution times.

Configuration:
    - default_ttl: 2 seconds (for fast expiration testing)
    - max_size: 100 entries

## large_memory_cache()

```python
def large_memory_cache():
```

InMemoryCache instance with large configuration for performance testing.

Provides an InMemoryCache instance with expanded limits
suitable for testing performance characteristics and
statistics generation with larger datasets.

Configuration:
    - default_ttl: 7200 seconds (2 hours)
    - max_size: 5000 entries

## populated_memory_cache()

```python
async def populated_memory_cache():
```

Pre-populated InMemoryCache instance for testing operations on existing data.

Provides an InMemoryCache instance with several entries already cached
to test operations like get, exists, delete on pre-existing data.

Pre-populated entries:
    - "user:1": {"id": 1, "name": "Alice"}
    - "user:2": {"id": 2, "name": "Bob"} 
    - "session:abc": "active_session"
    - "config:app": {"theme": "dark", "version": "1.0"}

Note:
    This fixture is useful for testing the 'read' and 'delete' paths of a 
    component's logic without cluttering the test with setup code. It provides 
    a cache that is already in a known state.

## cache_test_keys()

```python
def cache_test_keys():
```

Set of diverse cache keys for bulk testing operations.

Provides a variety of cache key patterns representative of
real-world usage for testing batch operations, statistics,
and key management functionality.

## cache_test_values()

```python
def cache_test_values():
```

Set of diverse cache values for bulk testing operations.

Provides a variety of cache value types and structures
representative of real-world usage for testing serialization,
storage, and retrieval of different data types.

## mock_time_provider()

```python
def mock_time_provider():
```

Mock time provider for testing TTL functionality without real time delays.

Provides a controllable time source that allows tests to simulate
time passage for TTL expiration testing without actually waiting.
This is a stateful mock that maintains an internal time counter.

Usage:
    with mock_time_provider.patch():
        cache.set("key", "value", ttl=60)
        mock_time_provider.advance(61)  # Advance by 61 seconds
        assert cache.get("key") is None  # Should be expired

Context Manager Methods:
    - patch(): Returns context manager that patches time.time()
    - advance(seconds): Advance time by specified seconds
    - set_time(timestamp): Set absolute time
    - reset(): Reset to current real time

Note:
    This fixture is crucial for creating **deterministic tests** for 
    time-dependent logic like TTL expiration. Instead of using `asyncio.sleep()`
    which slows down the test suite and can lead to flaky results, this mock 
    allows the test to instantly advance time, ensuring that expiration can be 
    tested quickly and reliably.

## mixed_ttl_test_data()

```python
def mixed_ttl_test_data():
```

Test data set with mixed TTL values for testing expiration scenarios.

Provides a set of key-value pairs with different TTL values
to test cache behavior with mixed expiration times.

Structure:
    List of (key, value, ttl) tuples with varying expiration times
