# In-Memory Cache Implementation Module

  file_path: `backend/app/infrastructure/cache/memory.py`

This module provides a high-performance, thread-safe in-memory caching solution with
advanced features including TTL (Time-To-Live) support, LRU (Least Recently Used)
eviction, and comprehensive cache management capabilities.

## Overview

---------
The InMemoryCache class serves as a lightweight, fast caching solution that stores
data directly in application memory. It's designed as a drop-in replacement for
Redis or other external caching systems during development, testing, or in scenarios
where external dependencies are not available or desired.

## Key Features

-------------
- **TTL Support**: Automatic expiration of cache entries with configurable time-to-live
- **LRU Eviction**: Intelligent memory management through least-recently-used eviction
- **Async Interface**: Fully asynchronous API compatible with modern Python applications
- **Memory Efficient**: Automatic cleanup of expired entries and configurable size limits
- **Statistics & Monitoring**: Built-in metrics and cache performance monitoring
- **Thread Safe**: Safe for use in concurrent environments (when used with asyncio)

## Architecture

-------------
The cache implements a two-tier storage system:
1. **Primary Storage**: Dictionary-based key-value store with metadata
2. **Access Tracking**: LRU ordering for intelligent eviction decisions

Each cache entry contains:
- `value`: The cached data
- `expires_at`: Timestamp for TTL-based expiration (optional)
- `created_at`: Entry creation timestamp for debugging/monitoring

## Configuration

--------------
- `default_ttl`: Default time-to-live in seconds (default: 3600)
- `max_size`: Maximum number of entries before LRU eviction (default: 1000)

## Usage Examples

---------------

## Basic usage

```python
cache = InMemoryCache(default_ttl=1800, max_size=500)

# Set a value with default TTL
await cache.set("user:123", {"name": "John", "role": "admin"})

# Set a value with custom TTL (5 minutes)
await cache.set("session:abc", "active", ttl=300)

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

## Performance Characteristics

----------------------------
- **Get Operations**: O(1) average case, O(n) worst case during cleanup
- **Set Operations**: O(1) average case, O(n) during LRU eviction
- **Memory Usage**: ~100-200 bytes overhead per cached entry
- **Cleanup Frequency**: Automatic during get/set operations
- **Eviction Strategy**: LRU with configurable thresholds

## Thread Safety

---------------
This implementation is designed for use with asyncio and is safe for concurrent
access within a single event loop. For multi-threaded applications, consider
using appropriate synchronization mechanisms or a thread-safe cache implementation.

## When to Use

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

## Integration

------------
This cache implements the CacheInterface protocol, making it compatible with
dependency injection systems and allowing seamless switching between cache
implementations (Redis, Memcached, etc.) without code changes.

## Dependencies

-------------
- asyncio: For asynchronous operations
- logging: For operational monitoring and debugging
- typing: For type hints and interface compliance
- datetime: For TTL calculations and timestamps

## Monitoring & Debugging

-----------------------
The cache provides comprehensive logging and statistics:
- Cache hits/misses logged at DEBUG level
- Eviction events logged at DEBUG level
- Error conditions logged at WARNING level
- Operational metrics available via get_stats()

## Error Handling

---------------
The implementation follows a resilient design pattern:
- Cache operations never raise exceptions to calling code
- Failed operations are logged and return sensible defaults
- Corrupted entries are automatically cleaned up
- Memory pressure is handled gracefully through eviction

## Version Compatibility

----------------------
- Python 3.7+: Full compatibility
- asyncio: Required for async operations
- Type hints: Fully annotated for IDE support and static analysis
