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
from app.infrastructure.cache.key_generator import CacheKeyGenerator

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

    def __init__(
        self,
        default_ttl: int = 3600,
        max_size: int = 1000,
        fail_on_connection_error: bool = False,
    ):
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
        # Validate parameters per public contract
        if not isinstance(default_ttl, int):
            raise ConfigurationError(
                "default_ttl must be an integer", {"default_ttl": default_ttl}
            )
        if not isinstance(max_size, int):
            raise ConfigurationError(
                "max_size must be an integer", {"max_size": max_size}
            )
        if not (1 <= default_ttl <= 86400):
            raise ConfigurationError(
                "default_ttl must be between 1 and 86400 seconds",
                {"default_ttl": default_ttl},
            )
        if not (1 <= max_size <= 100000):
            raise ConfigurationError(
                "max_size must be between 1 and 100000 entries", {"max_size": max_size}
            )

        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order: List[str] = []  # Track access order for LRU eviction

        # Statistics counters
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0
        self._memory_usage_bytes: int = 0

        # Initialize cache key generator for build_key compatibility
        self.key_generator = CacheKeyGenerator()

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
            # adjust memory usage before removing
            try:
                entry = self._cache.get(key)
                if entry is not None:
                    self._memory_usage_bytes -= entry.get("size_bytes", 0)
            finally:
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
                # adjust memory usage
                entry = self._cache.pop(lru_key)
                self._memory_usage_bytes -= entry.get("size_bytes", 0)
                self._evictions += 1
                # Log in a stable, testable format without f-string interpolation for the message template
                logger.debug("Evicting key %s (LRU)", lru_key)

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
                self._misses += 1
                logger.debug(f"Cache miss for key: {key}")
                return None

            entry = self._cache[key]

            # Check if entry has expired
            if self._is_expired(entry):
                # adjust memory usage before removing
                self._memory_usage_bytes -= entry.get("size_bytes", 0)
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                self._misses += 1
                logger.debug(f"Cache entry expired for key: {key}")
                return None

            # Update access order for LRU
            self._update_access_order(key)

            self._hits += 1
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

            # Estimate value size (best-effort)
            try:
                size_bytes = sys.getsizeof(value)
            except Exception:
                size_bytes = 0

            # If overwriting, adjust memory usage by removing old size first
            old_entry = self._cache.get(key)
            if old_entry is not None:
                self._memory_usage_bytes -= old_entry.get("size_bytes", 0)

            # Store the entry
            entry = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
                "size_bytes": size_bytes,
            }
            self._cache[key] = entry
            self._memory_usage_bytes += size_bytes

            # Update access order
            self._update_access_order(key)

            ttl_info = (
                f"TTL={ttl or self.default_ttl}s" if expires_at else "no expiration"
            )
            # Log at INFO to keep DEBUG reserved for hits/misses/evictions per contract
            logger.info(f"Set cache key {key} ({ttl_info})")

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
                entry = self._cache.pop(key)
                self._memory_usage_bytes -= entry.get("size_bytes", 0)
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
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._memory_usage_bytes = 0
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

        active_entries = len(self._cache) - expired_count
        total_lookups = self._hits + self._misses
        hit_rate = (self._hits / total_lookups) * 100 if total_lookups > 0 else 0.0

        stats = {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": active_entries,
            "max_size": self.max_size,
            "utilization": f"{active_entries}/{self.max_size}",
            "utilization_percent": (active_entries / self.max_size) * 100
            if self.max_size > 0
            else 0.0,
            "default_ttl": self.default_ttl,
            # Monitoring metrics per public contract
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "evictions": self._evictions,
            "memory_usage_bytes": max(self._memory_usage_bytes, 0),
        }

        # Back-compat fields expected by shared statistics fixtures
        # Human-readable memory usage string (simple KB/MB formatting)
        bytes_val = stats["memory_usage_bytes"]
        if bytes_val >= 1024 * 1024:
            mem_str = f"{bytes_val / (1024 * 1024):.1f}MB"
        elif bytes_val >= 1024:
            mem_str = f"{bytes_val / 1024:.1f}KB"
        else:
            mem_str = f"{bytes_val}B"

        stats.update(
            {
                "memory_cache_entries": active_entries,
                "memory_cache_size": self.max_size,
                "memory_usage": mem_str,
            }
        )

        return stats

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

    async def invalidate_pattern(
        self, pattern: str, operation_context: str = ""
    ) -> int:
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
        import fnmatch

        if not pattern:
            # Empty pattern means invalidate all
            keys_to_remove = list(self._cache.keys())
        else:
            # Find keys matching the pattern
            keys_to_remove = [
                key for key in self._cache.keys() if fnmatch.fnmatch(key, pattern)
            ]

        # Remove matching keys
        removed_count = 0
        for key in keys_to_remove:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                removed_count += 1

        if operation_context and removed_count > 0:
            logger.debug(
                f"InMemoryCache invalidated {removed_count} entries "
                f"for pattern '{pattern}' (context: {operation_context})"
            )

        return removed_count

    def get_invalidation_frequency_stats(self) -> dict:
        """
        Get cache invalidation frequency and pattern statistics.

        For InMemoryCache, this is a stub implementation that returns empty stats
        since invalidation tracking is not implemented for memory-only cache.

        Returns:
            dict: Empty statistics structure for consistency with API contract
        """
        return {
            "frequency": {},
            "patterns": {},
            "total_operations": 0,
            "performance": {},
        }

    def get_invalidation_recommendations(self) -> list:
        """
        Get optimization recommendations based on invalidation patterns.

        For InMemoryCache, this returns no recommendations since pattern
        analysis is not implemented for memory-only cache.

        Returns:
            list: Empty recommendations list
        """
        return []

    def get_cache_statistics(self) -> dict:
        """
        Get current memory cache statistics for internal use.

        Returns:
            dict: Basic cache statistics including entry count and memory usage
        """
        active_entries = len(self.get_active_keys())
        total_entries = len(self._cache)

        # Calculate approximate memory usage
        memory_bytes = 0
        for entry in self._cache.values():
            try:
                memory_bytes += len(str(entry).encode("utf-8"))
            except:
                memory_bytes += 100  # Rough estimate for non-string data

        # Format memory size
        if memory_bytes >= 1024 * 1024:
            memory_str = f"{memory_bytes / (1024 * 1024):.1f}MB"
        elif memory_bytes >= 1024:
            memory_str = f"{memory_bytes / 1024:.1f}KB"
        else:
            memory_str = f"{memory_bytes}B"

        return {
            "active_entries": active_entries,
            "total_entries": total_entries,
            "memory_usage": memory_str,
            "max_size": self.max_size,
            "utilization_percent": (active_entries / self.max_size) * 100
            if self.max_size > 0
            else 0,
        }

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
        # Get current memory cache statistics
        memory_stats = self.get_cache_statistics()
        active_entries = len(self.get_active_keys())

        # Calculate hit rate from existing counters
        total_operations = self._hits + self._misses
        hit_rate = (self._hits / total_operations) if total_operations > 0 else 0.0

        return {
            "redis": {
                "status": "disconnected",
                "message": "InMemoryCache does not use Redis backend",
            },
            "memory": {
                "status": "active",
                "entries": active_entries,
                "max_size": self.max_size,
                "utilization_percent": (active_entries / self.max_size) * 100
                if self.max_size > 0
                else 0,
                "memory_usage": memory_stats.get("memory_usage", "0B"),
            },
            "performance": {
                "status": "active",
                "hit_rate": round(hit_rate, 4),  # Actual hit rate calculation
                "total_operations": total_operations,
                "hits": self._hits,
                "misses": self._misses,
                "cache_type": "memory_only",
            },
        }

    def build_key(self, text: str, operation: str, options: Dict[str, Any]) -> str:
        """
        Build cache key using generic key generation logic.

        This helper method provides a generic interface for cache key generation
        without any domain-specific knowledge. It delegates to the CacheKeyGenerator
        for actual key generation, allowing domain services to build keys using
        the infrastructure layer's key generation patterns.

        Args:
            text: Input text for key generation
            operation: Operation type (generic string)
            options: Options dictionary containing all operation-specific data

        Returns:
            Generated cache key string

        Behavior:
            - Delegates to CacheKeyGenerator for actual key generation
            - No domain-specific logic or knowledge about operations
            - Generic interface suitable for any domain service usage
            - Maintains consistency with existing key generation patterns

        Examples:
            >>> # Basic operation key generation
            >>> cache = InMemoryCache()
            >>> key = cache.build_key(
            ...     text="Sample text",
            ...     operation="process",
            ...     options={"param": "value"}
            ... )

            >>> # Key generation with embedded question
            >>> key = cache.build_key(
            ...     text="Document content",
            ...     operation="qa",
            ...     options={"question": "What is this about?", "max_tokens": 150}
            ... )
        """
        return self.key_generator.generate_cache_key(text, operation, options)
