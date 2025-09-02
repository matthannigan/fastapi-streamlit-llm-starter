---
sidebar_label: redis_ai
---

# AI-optimized Redis cache with intelligent key generation and compression.

  file_path: `backend/app/infrastructure/cache/redis_ai.py`

This module provides a specialized Redis cache implementation optimized for AI response
caching. It extends GenericRedisCache with AI-specific features including intelligent
key generation for large texts, operation-specific TTLs, and advanced monitoring.

## Classes

**AIResponseCache**: AI-optimized Redis cache that extends GenericRedisCache with
specialized features for AI workloads including text processing and response caching.

## Key Features

- **Intelligent Key Generation**: Automatic text hashing for large inputs
- **Operation-Specific TTLs**: Different expiration times per AI operation type
- **Text Size Tiers**: Optimized handling based on input text size
- **Advanced Compression**: Smart compression with configurable thresholds
- **AI Metrics**: Specialized monitoring for AI response patterns
- **Graceful Degradation**: Fallback to memory-only mode when Redis unavailable

## Architecture

Inheritance pattern:
- **GenericRedisCache**: Provides core Redis functionality and L1 memory cache
- **AIResponseCache**: Adds AI-specific optimizations and intelligent features
- **CacheParameterMapper**: Handles parameter validation and mapping

## Usage

```python
cache = AIResponseCache(redis_url="redis://localhost:6379")
await cache.connect()

# AI response caching with intelligent key generation
key = cache.build_key(
    text="Long document to process...",
    operation="summarize",
    options={"max_length": 100}
)
await cache.set(key, {"summary": "Brief summary"}, ttl=3600)
        ...         'large': 30000
        ...     }
        ... )

Dependencies:
    Required:
        - app.infrastructure.cache.redis_generic.GenericRedisCache: Parent cache class
        - app.infrastructure.cache.parameter_mapping.CacheParameterMapper: Parameter handling
        - app.infrastructure.cache.key_generator.CacheKeyGenerator: AI key generation
        - app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking
        - app.core.exceptions: Custom exception handling

Performance Considerations:
    - Inherits efficient L1 memory cache and compression from GenericRedisCache
    - AI-specific callbacks add minimal overhead (<1ms per operation)
    - Key generation optimized for large texts with streaming hashing
    - Metrics collection designed for minimal performance impact

Error Handling:
    - Uses custom exceptions following established patterns
    - Graceful degradation when Redis unavailable
    - Comprehensive logging with proper context
    - All Redis operations wrapped with error handling

## AIResponseCache

AI Response Cache with enhanced inheritance architecture.

This refactored implementation properly inherits from GenericRedisCache while
maintaining all AI-specific functionality. It uses CacheParameterMapper for
clean parameter separation and provides comprehensive AI metrics collection.

### Key Improvements
- Clean inheritance from GenericRedisCache for core functionality
- Proper parameter mapping using CacheParameterMapper
- AI-specific callbacks integrated with generic cache events
- Maintains backward compatibility with existing API
- Enhanced error handling with custom exceptions

### Parameters
All original AIResponseCache parameters are supported with automatic mapping:
- `redis_url` (str): Redis connection URL
- `default_ttl` (int): Default time-to-live for cache entries
- `text_hash_threshold` (int): Character threshold for text hashing
- `hash_algorithm`: Hash algorithm for large texts
- `compression_threshold` (int): Size threshold for compression
- `compression_level` (int): Compression level (1-9)
- `text_size_tiers` (Dict[str, int]): Text categorization thresholds
- `memory_cache_size` (int): Maximum L1 cache entries (mapped to l1_cache_size)
- `performance_monitor` (CachePerformanceMonitor): Performance monitoring instance

### Returns
A fully functional AIResponseCache instance with enhanced architecture.

### Examples
```python
# Basic usage (backward compatible)
cache = AIResponseCache(redis_url="redis://localhost:6379")
await cache.connect()

# Advanced configuration
cache = AIResponseCache(
    redis_url="redis://production:6379",
    text_hash_threshold=1000,
    memory_cache_size=200,
    text_size_tiers={'small': 500, 'medium': 5000, 'large': 50000}
)
```

### __init__()

```python
def __init__(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 3600, text_hash_threshold: int = 1000, hash_algorithm = hashlib.sha256, compression_threshold: int = 1000, compression_level: int = 6, text_size_tiers: Optional[Dict[str, int]] = None, memory_cache_size: Optional[int] = None, l1_cache_size: int = 100, enable_l1_cache: bool = True, performance_monitor: Optional[CachePerformanceMonitor] = None, operation_ttls: Optional[Dict[str, int]] = None, security_config: Optional['SecurityConfig'] = None, fail_on_connection_error: bool = False):
```

Initialize AIResponseCache with parameter mapping and inheritance.

This constructor uses CacheParameterMapper to separate AI-specific parameters
from generic Redis parameters, then properly initializes the parent class
and sets up AI-specific features.

Args:
    redis_url: Redis connection URL
    default_ttl: Default time-to-live for cache entries in seconds
    text_hash_threshold: Character count threshold for text hashing
    hash_algorithm: Hash algorithm to use for large texts
    compression_threshold: Size threshold in bytes for compressing cache data
    compression_level: Compression level (1-9, where 9 is highest compression)
    text_size_tiers: Text size tiers for caching strategy optimization
    memory_cache_size: DEPRECATED. Use l1_cache_size instead. Maximum number of items 
                      in the in-memory cache. If provided, overrides l1_cache_size for backward compatibility.
    l1_cache_size: Maximum number of items in the L1 in-memory cache (modern parameter)
    enable_l1_cache: Enable/disable L1 in-memory cache for performance optimization
    performance_monitor: Optional performance monitor for tracking cache metrics
    operation_ttls: TTL values per AI operation type
    security_config: Optional security configuration for secure Redis connections,
                   including authentication, TLS encryption, and security validation
    fail_on_connection_error: If True, raise InfrastructureError when Redis unavailable.
                             If False (default), gracefully fallback to memory-only mode.

Raises:
    ConfigurationError: If parameter mapping fails or invalid configuration
    ValidationError: If parameter validation fails
    InfrastructureError: If Redis connection fails and fail_on_connection_error=True

### build_key()

```python
def build_key(self, text: str, operation: str, options: Dict[str, Any]) -> str:
```

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

### invalidate_pattern()

```python
async def invalidate_pattern(self, pattern: str, operation_context: str = ''):
```

Invalidate cache entries matching a specified pattern.

Searches for cache keys matching the given pattern and removes them
from Redis. Records invalidation metrics for monitoring and analysis.

Args:
    pattern (str): Pattern to match cache keys (supports wildcards).
                  Example: "summarize" matches keys containing "summarize".
    operation_context (str, optional): Context describing why invalidation
                                     was triggered. Defaults to "".

Returns:
    None: This method performs invalidation as a side effect.

Raises:
    None: All Redis exceptions are caught and logged as warnings.

Note:
    - Actual Redis pattern used is "ai_cache:*{pattern}*"
    - Performance metrics are automatically recorded
    - Zero matches is not considered an error

Example:
    >>> cache = AIResponseCache()
    >>> await cache.invalidate_pattern(
    ...     pattern="summarize",
    ...     operation_context="model_update"
    ... )
    # Invalidates all cache entries with "summarize" in the key

### invalidate_by_operation()

```python
async def invalidate_by_operation(self, operation: str, operation_context: str = '') -> int:
```

Invalidate cache entries for a specific operation type with comprehensive metrics tracking.

Removes all cached responses for a particular AI operation type while preserving
other operation types intact. Uses the inherited invalidate_pattern method from
GenericRedisCache for the actual invalidation work, but adds AI-specific pattern
building, metrics recording, and enhanced logging.

Args:
    operation (str): Operation type to invalidate (e.g., 'summarize', 'sentiment')
    operation_context (str, optional): Context describing why this operation's
                                     cache was invalidated. Auto-generated if not provided.

Returns:
    int: Number of cache entries that were invalidated

Raises:
    ValidationError: If operation parameter is invalid
    InfrastructureError: If invalidation fails critically

Example:
    >>> cache = AIResponseCache()
    >>> # Invalidate all summarization results due to model update
    >>> count = await cache.invalidate_by_operation(
    ...     operation="summarize",
    ...     operation_context="summarization_model_updated"
    ... )
    >>> print(f"Invalidated {count} summarization cache entries")

### clear()

```python
async def clear(self, operation_context: str = 'test_clear') -> None:
```

Clear all AI cache entries from both Redis and the L1 memory cache.

This method removes keys matching the AI cache namespace (ai_cache:*)
from Redis and purges the in-process L1 cache.

Args:
    operation_context: Optional context string for metrics.

### get_cache_stats()

```python
async def get_cache_stats(self) -> Dict[str, Any]:
```

Get comprehensive cache statistics including Redis and memory cache metrics.

Collects statistics from Redis (if available), in-memory cache, and
performance monitoring system. Also records current memory usage for tracking.

Returns:
    Dict[str, Any]: Comprehensive cache statistics containing:
        - redis: Redis connection status, key count, memory usage
        - memory: In-memory cache statistics and utilization
        - performance: Hit ratios, operation timings, compression stats
        - ai_metrics: AI-specific performance metrics

Raises:
    None: Redis errors are caught and logged, returning error status.

Example:
    >>> cache = AIResponseCache()
    >>> stats = await cache.get_cache_stats()
    >>> print(f"Hit ratio: {stats['performance']['hit_ratio']:.2%}")
    >>> print(f"Redis keys: {stats['redis']['keys']}")
    >>> print(f"Memory cache: {stats['memory']['memory_cache_entries']}")

### get_cache_hit_ratio()

```python
def get_cache_hit_ratio(self) -> float:
```

Get the current cache hit ratio as a percentage.

Calculates the percentage of cache operations that resulted in hits
(successful retrievals) versus misses.

Returns:
    float: Hit ratio as a percentage (0.0 to 100.0).
          Returns 0.0 if no operations have been recorded.

Example:
    >>> cache = AIResponseCache()
    >>> # After some cache operations...
    >>> hit_ratio = cache.get_cache_hit_ratio()
    >>> print(f"Cache hit ratio: {hit_ratio:.1f}%")
    Cache hit ratio: 75.3%

### get_performance_summary()

```python
def get_performance_summary(self) -> Dict[str, Any]:
```

Get a comprehensive summary of cache performance metrics.

Provides a consolidated view of key performance indicators including
hit ratios, operation counts, timing statistics, memory usage, and
AI-specific metrics.

Returns:
    Dict[str, Any]: Performance summary containing:
        - hit_ratio: Cache hit percentage
        - total_operations: Total cache operations performed
        - cache_hits/cache_misses: Breakdown of successful/failed retrievals
        - recent_avg_cache_operation_time: Average cache operation time
        - ai_operation_metrics: AI-specific operation performance data
        - text_tier_distribution: Distribution of cached content by text size

Example:
    >>> cache = AIResponseCache()
    >>> summary = cache.get_performance_summary()
    >>> print(f"Operations: {summary['total_operations']}")
    >>> print(f"Hit ratio: {summary['hit_ratio']:.1f}%")
    >>> print(f"Avg operation time: {summary['recent_avg_cache_operation_time']:.3f}s")

### connect()

```python
async def connect(self) -> bool:
```

Initialize Redis connection honoring this module's aioredis/flags.

Mirrors the parent implementation but binds to the aioredis symbol
defined in this module so unit tests can patch
`app.infrastructure.cache.redis_ai.aioredis` as expected.

### get_ai_performance_summary()

```python
def get_ai_performance_summary(self) -> Dict[str, Any]:
```

Get comprehensive AI-specific performance summary with analytics and optimization recommendations.

Provides a detailed overview of AI cache performance including operation-specific metrics,
text tier analysis, overall hit rates, and actionable optimization recommendations.
This method serves as the primary dashboard for AI cache performance monitoring.

Returns:
    Dict[str, Any]: Comprehensive performance summary containing:
        - total_operations: Total cache operations performed
        - overall_hit_rate: Overall cache hit rate percentage
        - hit_rate_by_operation: Hit rates broken down by AI operation type
        - text_tier_distribution: Distribution of cached content by text size tiers
        - key_generation_stats: Statistics from the cache key generator
        - optimization_recommendations: AI-specific optimization suggestions
        - inherited_stats: Core cache statistics from parent GenericRedisCache

Example:
    >>> cache = AIResponseCache()
    >>> summary = cache.get_ai_performance_summary()
    >>> print(f"Overall hit rate: {summary['overall_hit_rate']:.1f}%")
    >>> print(f"Total operations: {summary['total_operations']}")
    >>> for op, rate in summary['hit_rate_by_operation'].items():
    ...     print(f"{op}: {rate:.1f}%")

### get_text_tier_statistics()

```python
def get_text_tier_statistics(self) -> Dict[str, Any]:
```

Get comprehensive text tier statistics and performance analysis.

Provides detailed analysis of how different text size tiers are performing
in terms of cache efficiency, distribution, and optimization opportunities.

Returns:
    Dict[str, Any]: Text tier statistics containing:
        - tier_configuration: Current text size tier thresholds
        - tier_distribution: Number of operations per tier
        - tier_performance_analysis: Performance metrics by tier
        - tier_recommendations: Optimization suggestions per tier

Example:
    >>> cache = AIResponseCache()
    >>> stats = cache.get_text_tier_statistics()
    >>> print("Tier distribution:")
    >>> for tier, count in stats['tier_distribution'].items():
    ...     print(f"  {tier}: {count} operations")

### get_operation_performance()

```python
def get_operation_performance(self) -> Dict[str, Any]:
```

Get detailed performance metrics for AI operations.

Provides comprehensive performance analysis for each AI operation type including
duration statistics, operation counts, TTL configurations, and percentile analysis.

Returns:
    Dict[str, Any]: Operation performance metrics containing:
        - operations: Performance metrics per operation type with:
            - avg_duration_ms: Average operation duration in milliseconds
            - min_duration_ms: Minimum operation duration
            - max_duration_ms: Maximum operation duration
            - percentiles: p50, p95, p99 percentile durations
            - total_operations: Total number of operations performed
            - configured_ttl: TTL setting for this operation
        - summary: Overall performance summary across all operations

Example:
    >>> cache = AIResponseCache()
    >>> perf = cache.get_operation_performance()
    >>> for op, metrics in perf['operations'].items():
    ...     print(f"{op}: {metrics['avg_duration_ms']:.1f}ms avg, {metrics['total_operations']} ops")

### memory_cache()

```python
def memory_cache(self) -> Dict[str, Any]:
```

Legacy compatibility property for memory cache access.

### memory_cache()

```python
def memory_cache(self, value: Dict[str, Any]) -> None:
```

Legacy compatibility setter for memory cache (not used in new implementation).

### memory_cache()

```python
def memory_cache(self) -> None:
```

Legacy compatibility deleter for memory cache.

### memory_cache_size()

```python
def memory_cache_size(self) -> int:
```

Legacy compatibility property for memory cache size.

### memory_cache_order()

```python
def memory_cache_order(self) -> List[str]:
```

Legacy compatibility property for memory cache order (not used in new implementation).
