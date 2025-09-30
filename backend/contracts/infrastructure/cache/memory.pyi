"""
High-performance in-memory cache with TTL support and LRU eviction.

This module provides a lightweight, thread-safe in-memory caching solution optimized
for development, testing, and scenarios where external cache dependencies are not
available or desired.

## Key Features

- **TTL Support**: Automatic expiration with configurable time-to-live
- **LRU Eviction**: Intelligent memory management through least-recently-used eviction
- **Async Interface**: Full async/await compatibility
- **Statistics**: Built-in performance metrics and monitoring
- **Memory Efficient**: Automatic cleanup and configurable size limits

## Architecture

Two-tier storage system:

1. **Primary Storage**: Dictionary-based key-value store with metadata
2. **Access Tracking**: LRU ordering for intelligent eviction decisions

Each entry includes:
- `value`: The cached data
- `expires_at`: TTL expiration timestamp (optional)
- `created_at`: Creation timestamp for monitoring

## Configuration

- `default_ttl`: Default time-to-live in seconds (default: 3600)
- `max_size`: Maximum entries before LRU eviction (default: 1000)

## Usage

```python
cache = InMemoryCache(default_ttl=1800, max_size=500)

# Basic operations
await cache.set("user:123", {"name": "John", "role": "admin"})
await cache.set("session:abc", "active", ttl=300)  # Custom TTL

# Get a value
user_data = await cache.get("user:123")
if user_data:
    print(f"User: {user_data['name']}")

# Check if key exists
if await cache.exists("session:abc"):
    print("Session is active")

# Get cache statistics
stats = cache.get_stats()
print(f"Cache utilization: {stats['utilization_percent']:.1f}%")
```

Advanced usage with monitoring:
```python
# Create cache with custom configuration
cache = InMemoryCache(default_ttl=7200, max_size=2000)

# Monitor cache performance
stats = cache.get_stats()
logger.info(f"Cache stats: {stats['active_entries']} active, "
           f"{stats['expired_entries']} expired")

# Batch operations
keys_to_check = ["key1", "key2", "key3"]
active_keys = [k for k in keys_to_check if await cache.exists(k)]

# Manual cleanup (automatic cleanup happens during operations)
cache.clear()  # Clear all entries
```

## Usage Patterns

### Factory Method (Recommended for Most Cases)

**Use factory methods for consistent configuration and testing patterns:**

```python
from app.infrastructure.cache import CacheFactory

factory = CacheFactory()

# Testing scenarios - recommended approach
test_cache = await factory.for_testing(
    use_memory_cache=True,
    default_ttl=60,  # 1 minute for tests
    l1_cache_size=50
)

# Development environments
dev_cache = await factory.for_web_app(
    redis_url="redis://localhost:6379",
    fail_on_connection_error=False  # Falls back to InMemoryCache
)
```

**Factory Method Benefits:**
- Consistent test environment configurations
- Automatic fallback behavior when Redis unavailable
- Environment-optimized defaults
- Built-in parameter validation

### Direct Instantiation (Appropriate for)

**Use direct instantiation for simple applications and exact control scenarios:**

```python
# Testing scenarios requiring exact control
cache = InMemoryCache(default_ttl=1800, max_size=500)

# Simple applications with basic cache needs
cache = InMemoryCache(default_ttl=7200, max_size=2000)

# Fallback cache implementations
cache = InMemoryCache(default_ttl=3600, max_size=1000)
```

**Use direct instantiation when:**
- Building simple applications with basic caching needs
- Testing scenarios requiring exact behavioral control
- Implementing fallback cache strategies
- Developing specialized cache components

**📖 For comprehensive factory usage patterns and configuration examples, see [Cache Usage Guide](../../../docs/guides/infrastructure/cache/usage-guide.md).**

Performance Characteristics:
----------------------------
- **Get Operations**: O(1) average case, O(n) worst case during cleanup
- **Set Operations**: O(1) average case, O(n) during LRU eviction
- **Memory Usage**: ~100-200 bytes overhead per cached entry
- **Cleanup Frequency**: Automatic during get/set operations
- **Eviction Strategy**: LRU with configurable thresholds

Thread Safety:
---------------
This implementation is designed for use with asyncio and is safe for concurrent
access within a single event loop. For multi-threaded applications, consider
using appropriate synchronization mechanisms or a thread-safe cache implementation.

When to Use:
------------
**Ideal for:**
- Development and testing environments
- Applications with moderate caching needs (<10,000 entries)
- Scenarios where external cache dependencies are not desired
- Microservices with minimal infrastructure requirements
- Temporary caching during application startup

**Consider alternatives for:**
- High-volume production applications (>100,000 entries)
- Multi-process deployments requiring shared cache
- Applications requiring cache persistence across restarts
- Systems with strict memory usage constraints

Integration:
------------
This cache implements the CacheInterface protocol, making it compatible with
dependency injection systems and allowing seamless switching between cache
implementations (Redis, Memcached, etc.) without code changes.

Dependencies:
-------------
- asyncio: For asynchronous operations
- logging: For operational monitoring and debugging
- typing: For type hints and interface compliance
- datetime: For TTL calculations and timestamps

Monitoring & Debugging:
-----------------------
The cache provides comprehensive logging and statistics:
- Cache hits/misses logged at DEBUG level
- Eviction events logged at DEBUG level
- Error conditions logged at WARNING level
- Operational metrics available via get_stats()

Error Handling:
---------------
The implementation follows a resilient design pattern:
- Cache operations never raise exceptions to calling code
- Failed operations are logged and return sensible defaults
- Corrupted entries are automatically cleaned up
- Memory pressure is handled gracefully through eviction

Version Compatibility:
----------------------
- Python 3.7+: Full compatibility
- asyncio: Required for async operations
- Type hints: Fully annotated for IDE support and static analysis
"""

import logging
import sys
import time
from typing import Any, Dict, List, Optional
from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.base import CacheInterface


class InMemoryCache(CacheInterface):
    """
    High-performance in-memory cache with TTL support and LRU eviction for development and production use.
    
    Provides a complete caching solution storing data directly in application memory with automatic
    expiration, intelligent eviction policies, and comprehensive monitoring. Designed as a drop-in
    replacement for Redis during development or for applications requiring embedded caching.
    
    Attributes:
        default_ttl: int default time-to-live in seconds for cache entries
        max_size: int maximum entries before LRU eviction triggers
        _cache: Dict[str, Dict[str, Any]] internal storage with metadata
        _access_order: List[str] LRU tracking for eviction decisions
    
    Public Methods:
        get(): Retrieve value by key with automatic expiration handling
        set(): Store value with optional TTL and LRU management
        delete(): Remove entry immediately with cleanup
        exists(): Check key existence without affecting LRU order
        clear(): Remove all cached entries for testing/cleanup
        get_stats(): Retrieve cache performance statistics
    
    State Management:
        - Thread-safe for single event loop concurrent access
        - Automatic cleanup of expired entries during operations
        - LRU eviction maintains memory bounds automatically
        - Statistics tracking for monitoring and debugging
    
    Usage:
        # Development and testing configuration
        cache = InMemoryCache(default_ttl=1800, max_size=500)
    
        # Basic caching operations
        await cache.set("user:123", {"name": "John", "active": True})
        user_data = await cache.get("user:123")
        await cache.delete("user:123")
    
        # Advanced usage with custom TTL
        await cache.set("session:abc", "active", ttl=300)  # 5 minutes
        if await cache.exists("session:abc"):
            print("Session still active")
    
        # Production monitoring
        stats = cache.get_stats()
        print(f"Cache hit rate: {stats['hit_rate']:.2%}")
    
        # Testing and cleanup
        cache.clear()  # Remove all entries for clean test state
    """

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000, fail_on_connection_error: bool = False):
        """
        Initialize in-memory cache with TTL and LRU eviction configuration.
        
        Sets up cache storage structures, eviction policies, and monitoring systems
        for optimal performance in development and production environments.
        
        Args:
            default_ttl: Default time-to-live in seconds (1-86400). Applied when
                        set() called without explicit ttl parameter. Default 3600 (1 hour).
            max_size: Maximum cache entries (1-100000) before LRU eviction. Controls
                     memory usage by removing least-recently-used entries. Default 1000.
            fail_on_connection_error: Parameter for interface consistency with Redis caches.
                                     Always ignored for InMemoryCache since no connection is required.
        
        Behavior:
            - Initializes empty cache storage with metadata tracking
            - Sets up LRU access order tracking for intelligent eviction
            - Configures TTL system for automatic expiration
            - Initializes statistics counters for performance monitoring
            - Validates configuration parameters for safe operation
            - Prepares thread-safe data structures for concurrent access
        """
        ...

    async def get(self, key: str) -> Any:
        """
        Get a value from cache by key (implements CacheInterface).
        
        Args:
            key: Cache key to retrieve
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        ...

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache with optional TTL (implements CacheInterface).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional, uses default if not provided)
        """
        ...

    async def delete(self, key: str) -> None:
        """
        Delete a key from cache (implements CacheInterface).
        
        Args:
            key: Cache key to delete
        """
        ...

    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        ...

    def size(self) -> int:
        """
        Get the current number of entries in the cache.
        
        Returns:
            Number of cache entries
        """
        ...

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        ...

    def get_keys(self) -> list:
        """
        Get all cache keys (including expired ones).
        
        Returns:
            List of cache keys
        """
        ...

    def get_active_keys(self) -> list:
        """
        Get all non-expired cache keys.
        
        Returns:
            List of active cache keys
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache and is not expired.
        
        Args:
            key: Cache key to check
        
        Returns:
            True if key exists and is not expired, False otherwise
        """
        ...

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time-to-live for a key.
        
        Args:
            key: Cache key
        
        Returns:
            Remaining TTL in seconds, None if key doesn't exist or has no expiration
        """
        ...

    async def invalidate_pattern(self, pattern: str, operation_context: str = '') -> int:
        """
        Invalidate cache entries matching a glob-style pattern.
        
        Removes all cache entries whose keys match the specified pattern.
        This method provides compatibility with Redis-based cache APIs that
        support pattern-based invalidation for administrative operations.
        
        Args:
            pattern: Glob-style pattern to match cache keys. Empty string matches all keys.
                    Supports wildcards: * (any characters), ? (single character)
            operation_context: Context information for logging/monitoring (optional)
        
        Returns:
            int: Number of cache entries that were invalidated
        
        Behavior:
            - Pattern matching uses Python fnmatch for glob-style patterns
            - Empty pattern matches all entries (complete cache clear)
            - Expired entries are also removed during pattern matching
            - Operation is atomic - either all matching keys are removed or none
        
        Example:
            >>> cache = InMemoryCache()
            >>> await cache.set("user:123", "data1")
            >>> await cache.set("user:456", "data2")
            >>> await cache.set("session:abc", "session_data")
            >>> count = await cache.invalidate_pattern("user:*")
            >>> assert count == 2  # Removed user:123 and user:456
        """
        ...

    def get_invalidation_frequency_stats(self) -> dict:
        """
        Get cache invalidation frequency and pattern statistics.
        
        For InMemoryCache, this is a stub implementation that returns empty stats
        since invalidation tracking is not implemented for memory-only cache.
        
        Returns:
            dict: Empty statistics structure for consistency with API contract
        """
        ...

    def get_invalidation_recommendations(self) -> list:
        """
        Get optimization recommendations based on invalidation patterns.
        
        For InMemoryCache, this returns no recommendations since pattern
        analysis is not implemented for memory-only cache.
        
        Returns:
            list: Empty recommendations list
        """
        ...

    def get_cache_statistics(self) -> dict:
        """
        Get current memory cache statistics for internal use.
        
        Returns:
            dict: Basic cache statistics including entry count and memory usage
        """
        ...

    async def get_cache_stats(self) -> dict:
        """
        Get comprehensive cache statistics for monitoring and status endpoints.
        
        Returns cache status information consistent with the API contract,
        providing visibility into memory cache performance and utilization.
        
        Returns:
            dict: Cache statistics containing:
                - redis: Redis backend status (always disconnected for InMemoryCache)
                - memory: Memory cache status with entry counts and utilization
                - performance: Comprehensive performance metrics including actual hit rate calculation
        """
        ...
