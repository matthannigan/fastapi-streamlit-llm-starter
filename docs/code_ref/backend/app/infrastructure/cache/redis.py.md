---
sidebar_label: redis
---

# [DEPRECATED] Redis-based AI Response Cache Implementation

  file_path: `backend/app/infrastructure/cache/redis.py`

⚠️  WARNING: This module is deprecated and has been refactored into a modular structure.

Please migrate to the new modular imports:
- AIResponseCache: from app.infrastructure.cache.redis_ai import AIResponseCache
- CacheKeyGenerator: from app.infrastructure.cache.key_generator import CacheKeyGenerator
- REDIS_AVAILABLE, aioredis: from app.infrastructure.cache.redis_generic import REDIS_AVAILABLE, aioredis

This compatibility module will be removed in a future version.

LEGACY: This module provides a comprehensive Redis-based caching solution specifically designed
for AI response caching with advanced features including intelligent key generation,
compression, tiered caching, and performance monitoring.

## Classes

CacheKeyGenerator: Optimized cache key generator that efficiently handles large texts
by using hashing strategies and metadata inclusion for uniqueness.

AIResponseCache: Main cache implementation providing Redis-backed storage with
in-memory caching tier, compression, and comprehensive monitoring.

## Key Features

- **Tiered Caching**: Memory cache for small, frequently accessed items with Redis
as the persistent backend storage tier.

- **Intelligent Compression**: Automatic compression of large responses using zlib
with configurable thresholds and compression levels.

- **Optimized Key Generation**: Efficient cache key generation that hashes large
texts while preserving readability for smaller content.

- **Performance Monitoring**: Comprehensive metrics collection including hit ratios,
operation timings, compression statistics, and memory usage tracking.

- **Graceful Degradation**: Continues operation without Redis connectivity, falling
back to memory-only caching when Redis is unavailable.

- **Operation-Specific TTLs**: Different time-to-live values based on operation
type (e.g., sentiment analysis cached longer than Q&A responses).

- **Pattern-Based Invalidation**: Flexible cache invalidation supporting pattern
matching for bulk operations and operation-specific clearing.

## Configuration

The cache system supports extensive configuration through constructor parameters:

- redis_url: Redis connection URL (default: "redis://redis:6379")
- text_hash_threshold: Size threshold for text hashing (default: 1000 chars)
- compression_threshold: Response size threshold for compression (default: 1000 bytes)
- memory_cache_size: Maximum in-memory cache entries (default: 100)
- text_size_tiers: Text categorization thresholds for caching strategy
- operation_ttls: TTL values per operation type

## Usage Examples

### Basic Usage

```python
cache = AIResponseCache(redis_url="redis://localhost:6379")
await cache.connect()

# Cache an AI response
await cache.cache_response(
    text="Long document to summarize...",
    operation="summarize",
    options={"max_length": 100},
    response={"summary": "Brief summary", "confidence": 0.95}
)

# Retrieve cached response
cached = await cache.get_cached_response(
    text="Long document to summarize...",
    operation="summarize",
    options={"max_length": 100}
)
if cached:
    print(f"Cache hit: {cached['summary']}")
```

### Performance Monitoring

```python
# Get comprehensive performance statistics
stats = await cache.get_cache_stats()
print(f"Hit ratio: {cache.get_cache_hit_ratio():.1f}%")
print(f"Total operations: {stats['performance']['total_operations']}")

# Get performance summary
summary = cache.get_performance_summary()
print(f"Average operation time: {summary['recent_avg_cache_operation_time']:.3f}s")
```

### Cache Management

```python
# Invalidate specific operation type
await cache.invalidate_by_operation("summarize",
                                    operation_context="model_update")

# Invalidate using pattern matching
await cache.invalidate_pattern("sentiment",
                               operation_context="batch_invalidation")

# Get memory usage warnings
warnings = cache.get_memory_warnings()
for warning in warnings:
    print(f"{warning['severity']}: {warning['message']}")
```

### Advanced Configuration

```python
# Configure with custom settings
cache = AIResponseCache(
    redis_url="redis://production:6379",
    default_ttl=7200,  # 2 hours
    text_hash_threshold=500,  # Hash texts over 500 chars
    compression_threshold=2000,  # Compress responses over 2KB
    compression_level=9,  # Maximum compression
    memory_cache_size=200,  # Larger memory cache
    text_size_tiers={
        'small': 300,
        'medium': 3000,
        'large': 30000
    }
)
```

## Dependencies

### Required

- redis: Async Redis client (redis[asyncio])
- Standard library: hashlib, json, zlib, pickle, asyncio, logging, datetime, time

### Optional

- Redis server connection (graceful degradation when unavailable)

## Thread Safety

This module is designed for async/await usage and is not thread-safe for
synchronous concurrent access. Use appropriate async synchronization if needed.

## Performance Considerations

- Memory cache provides sub-millisecond access for frequently used small items
- Compression reduces Redis memory usage but adds CPU overhead for large responses
- Key generation for large texts uses streaming hashing to minimize memory usage
- Performance monitoring adds minimal overhead (<1ms per operation)

## Error Handling

- Redis connection failures result in graceful degradation to memory-only caching
- All Redis operations are wrapped with error handling and logging
- Cache misses due to errors are recorded in performance metrics
- Serialization errors are logged but don't interrupt application flow
