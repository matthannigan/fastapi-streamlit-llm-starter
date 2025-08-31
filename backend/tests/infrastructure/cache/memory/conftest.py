"""
Test fixtures for InMemoryCache unit tests.

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
"""

import pytest
import time
from typing import Any, Dict, Optional
from unittest.mock import MagicMock


# Note: sample_cache_key fixture is now provided by the parent conftest.py


# Note: sample_cache_value fixture is now provided by the parent conftest.py


@pytest.fixture
def sample_simple_value():
    """
    Simple cache value (string) for basic testing scenarios.
    
    Provides a simple string value to test basic cache operations
    without the complexity of nested data structures.
    """
    return "simple test value"


# Note: sample_ttl and short_ttl fixtures are now provided by the parent conftest.py


# Note: default_memory_cache fixture is now provided by the parent conftest.py


@pytest.fixture
def small_memory_cache():
    """
    InMemoryCache instance with small configuration for LRU eviction testing.
    
    Provides an InMemoryCache instance with reduced size limits
    to facilitate testing of LRU eviction behavior without
    needing to create thousands of entries.
    
    Configuration:
        - default_ttl: 300 seconds (5 minutes)
        - max_size: 3 entries (for easy eviction testing)
    """
    from app.infrastructure.cache.memory import InMemoryCache
    return InMemoryCache(default_ttl=300, max_size=3)


@pytest.fixture
def fast_expiry_memory_cache():
    """
    InMemoryCache instance with short default TTL for expiration testing.
    
    Provides an InMemoryCache instance configured with short TTL
    to facilitate testing of cache expiration behavior without
    long test execution times.
    
    Configuration:
        - default_ttl: 2 seconds (for fast expiration testing)
        - max_size: 100 entries
    """
    from app.infrastructure.cache.memory import InMemoryCache
    return InMemoryCache(default_ttl=2, max_size=100)


@pytest.fixture
def large_memory_cache():
    """
    InMemoryCache instance with large configuration for performance testing.
    
    Provides an InMemoryCache instance with expanded limits
    suitable for testing performance characteristics and
    statistics generation with larger datasets.
    
    Configuration:
        - default_ttl: 7200 seconds (2 hours)
        - max_size: 5000 entries
    """
    from app.infrastructure.cache.memory import InMemoryCache
    return InMemoryCache(default_ttl=7200, max_size=5000)


@pytest.fixture
def populated_memory_cache():
    """
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
    """
    from app.infrastructure.cache.memory import InMemoryCache
    import asyncio
    
    cache = InMemoryCache(default_ttl=3600, max_size=100)
    
    # Pre-populate with test data
    async def populate():
        await cache.set("user:1", {"id": 1, "name": "Alice"})
        await cache.set("user:2", {"id": 2, "name": "Bob"})
        await cache.set("session:abc", "active_session")
        await cache.set("config:app", {"theme": "dark", "version": "1.0"})
    
    # Run population in event loop if one exists, otherwise create one
    try:
        loop = asyncio.get_running_loop()
        # If we have a running loop, we need to use it
        task = loop.create_task(populate())
        # We can't await here since we're in a sync function, 
        # so we'll return a cache that needs to be populated by the test
        cache._needs_population = True
        cache._populate_task = populate
    except RuntimeError:
        # No running loop, we can create one
        asyncio.run(populate())
    
    return cache


@pytest.fixture
def cache_test_keys():
    """
    Set of diverse cache keys for bulk testing operations.
    
    Provides a variety of cache key patterns representative of
    real-world usage for testing batch operations, statistics,
    and key management functionality.
    """
    return [
        "user:123",
        "user:456", 
        "session:abc123",
        "session:def456",
        "config:global",
        "config:user:123",
        "temp:data:xyz",
        "api:cache:endpoint:1",
        "metrics:hourly:2023-01-01",
        "auth:token:user123"
    ]


@pytest.fixture
def cache_test_values():
    """
    Set of diverse cache values for bulk testing operations.
    
    Provides a variety of cache value types and structures
    representative of real-world usage for testing serialization,
    storage, and retrieval of different data types.
    """
    return [
        {"id": 123, "type": "user"},
        {"id": 456, "type": "user", "premium": True},
        "active_session_token",
        "inactive_session_token", 
        {"theme": "dark", "notifications": True},
        {"theme": "light", "user_id": 123, "permissions": ["read", "write"]},
        {"temporary": True, "expires": "2023-12-31"},
        {"endpoint": "/api/v1/users", "method": "GET", "cached_at": "2023-01-01T12:00:00Z"},
        {"date": "2023-01-01", "requests": 1542, "errors": 3},
        {"user_id": 123, "token": "jwt_token_here", "expires_at": "2023-01-01T13:00:00Z"}
    ]


@pytest.fixture
def mock_time_provider():
    """
    Mock time provider for testing TTL functionality without real time delays.
    
    Provides a controllable time source that allows tests to simulate
    time passage for TTL expiration testing without actually waiting.
    This is a stateful mock that maintains an internal time counter.
    
    Usage:
        mock_time.current_time = 1000  # Set base time
        mock_time.advance(3600)        # Advance by 1 hour
        assert mock_time.current_time == 4600

    Note:
        This fixture is crucial for creating **deterministic tests** for 
        time-dependent logic like TTL expiration. Instead of using `asyncio.sleep()`
        which slows down the test suite and can lead to flaky results, this mock 
        allows the test to instantly advance time, ensuring that expiration can be 
        tested quickly and reliably.
    """
    mock_time = MagicMock()
    mock_time.current_time = time.time()  # Start with real current time
    
    def get_time():
        return mock_time.current_time
    
    def advance_time(seconds):
        mock_time.current_time += seconds
        
    mock_time.time = get_time
    mock_time.advance = advance_time
    
    return mock_time


# Note: cache_statistics_sample fixture is now provided by the parent conftest.py


@pytest.fixture
def mixed_ttl_test_data():
    """
    Test data set with mixed TTL values for testing expiration scenarios.
    
    Provides a set of key-value pairs with different TTL values
    to test cache behavior with mixed expiration times.
    
    Structure:
        List of (key, value, ttl) tuples with varying expiration times
    """
    return [
        ("short:key1", "expires_soon", 1),      # 1 second
        ("medium:key2", {"data": "medium"}, 60), # 1 minute
        ("long:key3", {"data": "long"}, 3600),   # 1 hour
        ("no_ttl:key4", "never_expires", None),  # No expiration
        ("short:key5", "also_expires_soon", 2),  # 2 seconds
    ]