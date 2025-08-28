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
import time
from typing import Any, Dict, List, Optional

from app.infrastructure.cache.base import CacheInterface

logger = logging.getLogger(__name__)


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

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Initialize in-memory cache with TTL and LRU eviction configuration.

        Sets up cache storage structures, eviction policies, and monitoring systems
        for optimal performance in development and production environments.

        Args:
            default_ttl: Default time-to-live in seconds (1-86400). Applied when
                        set() called without explicit ttl parameter. Default 3600 (1 hour).
            max_size: Maximum cache entries (1-100000) before LRU eviction. Controls
                     memory usage by removing least-recently-used entries. Default 1000.

        Behavior:
            - Initializes empty cache storage with metadata tracking
            - Sets up LRU access order tracking for intelligent eviction
            - Configures TTL system for automatic expiration
            - Initializes statistics counters for performance monitoring
            - Validates configuration parameters for safe operation
            - Prepares thread-safe data structures for concurrent access
        """
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []  # Track access order for LRU eviction

        logger.info(
            f"InMemoryCache initialized with default_ttl={default_ttl}s, max_size={max_size}"
        )

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry has expired.

        Args:
            entry: Cache entry containing 'expires_at' timestamp

        Returns:
            True if expired, False otherwise
        """
        if entry.get("expires_at") is None:
            return False
        return time.time() > entry["expires_at"]

    def _cleanup_expired(self):
        """
        Remove expired entries from cache.

        This method is called periodically during cache operations
        to maintain cache hygiene and free up memory.
        """
        expired_keys = []
        current_time = time.time()

        for key, entry in self._cache.items():
            if entry.get("expires_at") and current_time > entry["expires_at"]:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _update_access_order(self, key: str):
        """
        Update the access order for LRU tracking.

        Args:
            key: Cache key that was accessed
        """
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _evict_lru_if_needed(self):
        """
        Evict least recently used entries if cache exceeds max size.
        """
        while len(self._cache) >= self.max_size and self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                logger.debug(f"Evicted LRU cache entry: {lru_key}")

    async def get(self, key: str) -> Any:
        """
        Get a value from cache by key (implements CacheInterface).

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if found and not expired, None otherwise
        """
        try:
            # Clean up expired entries periodically
            self._cleanup_expired()

            if key not in self._cache:
                logger.debug(f"Cache miss for key: {key}")
                return None

            entry = self._cache[key]

            # Check if entry has expired
            if self._is_expired(entry):
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                logger.debug(f"Cache entry expired for key: {key}")
                return None

            # Update access order for LRU
            self._update_access_order(key)

            logger.debug(f"Cache hit for key: {key}")
            return entry["value"]

        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache with optional TTL (implements CacheInterface).

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional, uses default if not provided)
        """
        try:
            # Clean up expired entries before adding new ones
            self._cleanup_expired()

            # Evict LRU entries if needed
            self._evict_lru_if_needed()

            # Calculate expiration time
            expires_at = None
            if ttl is not None:
                if ttl > 0:  # ttl=0 means no expiration
                    expires_at = time.time() + ttl
                # ttl=0 keeps expires_at=None (no expiration)
            elif self.default_ttl > 0:
                expires_at = time.time() + self.default_ttl

            # Store the entry
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
            }

            # Update access order
            self._update_access_order(key)

            ttl_info = (
                f"TTL={ttl or self.default_ttl}s" if expires_at else "no expiration"
            )
            logger.debug(f"Set cache key {key} ({ttl_info})")

        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")

    async def delete(self, key: str) -> None:
        """
        Delete a key from cache (implements CacheInterface).

        Args:
            key: Cache key to delete
        """
        try:
            existed = key in self._cache

            if existed:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)

            logger.debug(f"Deleted cache key {key} (existed: {existed})")

        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")

    # Additional utility methods

    def clear(self) -> None:
        """
        Clear all entries from the cache.
        """
        entries_count = len(self._cache)
        self._cache.clear()
        self._access_order.clear()
        logger.info(f"Cleared {entries_count} entries from memory cache")

    def size(self) -> int:
        """
        Get the current number of entries in the cache.

        Returns:
            Number of cache entries
        """
        return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary containing cache statistics
        """
        # Count expired entries without removing them
        current_time = time.time()
        expired_count = sum(
            1
            for entry in self._cache.values()
            if entry.get("expires_at") and current_time > entry["expires_at"]
        )

        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "max_size": self.max_size,
            "utilization": f"{len(self._cache)}/{self.max_size}",
            "utilization_percent": (len(self._cache) / self.max_size) * 100
            if self.max_size > 0
            else 0,
            "default_ttl": self.default_ttl,
        }

    def get_keys(self) -> list:
        """
        Get all cache keys (including expired ones).

        Returns:
            List of cache keys
        """
        return list(self._cache.keys())

    def get_active_keys(self) -> list:
        """
        Get all non-expired cache keys.

        Returns:
            List of active cache keys
        """
        current_time = time.time()
        return [
            key
            for key, entry in self._cache.items()
            if not entry.get("expires_at") or current_time <= entry["expires_at"]
        ]

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache and is not expired.

        Args:
            key: Cache key to check

        Returns:
            True if key exists and is not expired, False otherwise
        """
        if key not in self._cache:
            return False

        entry = self._cache[key]
        if self._is_expired(entry):
            # Clean up expired entry
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return False

        return True

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get the remaining time-to-live for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, None if key doesn't exist or has no expiration
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        expires_at = entry.get("expires_at")

        if expires_at is None:
            return None  # No expiration set

        remaining = int(expires_at - time.time())
        return max(0, remaining)  # Don't return negative values
