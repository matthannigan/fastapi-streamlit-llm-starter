"""
[DEPRECATED] Redis-based AI Response Cache Implementation

⚠️  WARNING: This module is deprecated and has been refactored into a modular structure.
    
    Please migrate to the new modular imports:
    - AIResponseCache: from app.infrastructure.cache.redis_ai import AIResponseCache
    - CacheKeyGenerator: from app.infrastructure.cache.key_generator import CacheKeyGenerator
    - REDIS_AVAILABLE, aioredis: from app.infrastructure.cache.redis_generic import REDIS_AVAILABLE, aioredis
    
    This compatibility module will be removed in a future version.

LEGACY: This module provides a comprehensive Redis-based caching solution specifically designed 
for AI response caching with advanced features including intelligent key generation, 
compression, tiered caching, and performance monitoring.

Classes:
    CacheKeyGenerator: Optimized cache key generator that efficiently handles large texts
                      by using hashing strategies and metadata inclusion for uniqueness.
    
    AIResponseCache: Main cache implementation providing Redis-backed storage with 
                    in-memory caching tier, compression, and comprehensive monitoring.

Key Features:
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

Configuration:
    The cache system supports extensive configuration through constructor parameters:
    
    - redis_url: Redis connection URL (default: "redis://redis:6379")
    - text_hash_threshold: Size threshold for text hashing (default: 1000 chars)
    - compression_threshold: Response size threshold for compression (default: 1000 bytes)
    - memory_cache_size: Maximum in-memory cache entries (default: 100)
    - text_size_tiers: Text categorization thresholds for caching strategy
    - operation_ttls: TTL values per operation type

Usage Examples:
    Basic Usage:
        >>> cache = AIResponseCache(redis_url="redis://localhost:6379")
        >>> await cache.connect()
        >>> 
        >>> # Cache an AI response
        >>> await cache.cache_response(
        ...     text="Long document to summarize...",
        ...     operation="summarize",
        ...     options={"max_length": 100},
        ...     response={"summary": "Brief summary", "confidence": 0.95}
        ... )
        >>> 
        >>> # Retrieve cached response
        >>> cached = await cache.get_cached_response(
        ...     text="Long document to summarize...",
        ...     operation="summarize", 
        ...     options={"max_length": 100}
        ... )
        >>> if cached:
        ...     print(f"Cache hit: {cached['summary']}")

    Performance Monitoring:
        >>> # Get comprehensive performance statistics
        >>> stats = await cache.get_cache_stats()
        >>> print(f"Hit ratio: {cache.get_cache_hit_ratio():.1f}%")
        >>> print(f"Total operations: {stats['performance']['total_operations']}")
        >>> 
        >>> # Get performance summary
        >>> summary = cache.get_performance_summary()
        >>> print(f"Average operation time: {summary['recent_avg_cache_operation_time']:.3f}s")

    Cache Management:
        >>> # Invalidate specific operation type
        >>> await cache.invalidate_by_operation("summarize", 
        ...                                     operation_context="model_update")
        >>> 
        >>> # Invalidate using pattern matching
        >>> await cache.invalidate_pattern("sentiment", 
        ...                                operation_context="batch_invalidation")
        >>> 
        >>> # Get memory usage warnings
        >>> warnings = cache.get_memory_warnings()
        >>> for warning in warnings:
        ...     print(f"{warning['severity']}: {warning['message']}")

    Advanced Configuration:
        >>> # Configure with custom settings
        >>> cache = AIResponseCache(
        ...     redis_url="redis://production:6379",
        ...     default_ttl=7200,  # 2 hours
        ...     text_hash_threshold=500,  # Hash texts over 500 chars
        ...     compression_threshold=2000,  # Compress responses over 2KB
        ...     compression_level=9,  # Maximum compression
        ...     memory_cache_size=200,  # Larger memory cache
        ...     text_size_tiers={
        ...         'small': 300,
        ...         'medium': 3000, 
        ...         'large': 30000
        ...     }
        ... )

Dependencies:
    Required:
        - redis: Async Redis client (redis[asyncio])
        - Standard library: hashlib, json, zlib, pickle, asyncio, logging, datetime, time
    
    Optional:
        - Redis server connection (graceful degradation when unavailable)

Thread Safety:
    This module is designed for async/await usage and is not thread-safe for 
    synchronous concurrent access. Use appropriate async synchronization if needed.

Performance Considerations:
    - Memory cache provides sub-millisecond access for frequently used small items
    - Compression reduces Redis memory usage but adds CPU overhead for large responses
    - Key generation for large texts uses streaming hashing to minimize memory usage
    - Performance monitoring adds minimal overhead (<1ms per operation)

Error Handling:
    - Redis connection failures result in graceful degradation to memory-only caching
    - All Redis operations are wrapped with error handling and logging
    - Cache misses due to errors are recorded in performance metrics
    - Serialization errors are logged but don't interrupt application flow
"""

import hashlib
import json
import logging
import time
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.infrastructure.cache.key_generator import CacheKeyGenerator
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from .redis_generic import GenericRedisCache


class AIResponseCache(GenericRedisCache):
    def __init__(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 3600, text_hash_threshold: int = 1000, hash_algorithm = hashlib.sha256, compression_threshold: int = 1000, compression_level: int = 6, text_size_tiers: Optional[Dict[str, int]] = None, memory_cache_size: int = 100, performance_monitor: Optional[CachePerformanceMonitor] = None):
        """
        Initialize AIResponseCache with injectable configuration.
        
        **DEPRECATED**: Direct usage of AIResponseCache is deprecated. Use GenericRedisCache
        with CacheCompatibilityWrapper for new implementations, or migrate to the new cache interfaces.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live for cache entries in seconds
            text_hash_threshold: Character count threshold for text hashing
            hash_algorithm: Hash algorithm to use for large texts
            compression_threshold: Size threshold in bytes for compressing cache data
            compression_level: Compression level (1-9, where 9 is highest compression)
            text_size_tiers: Text size tiers for caching strategy optimization (None for defaults)
            memory_cache_size: Maximum number of items in the in-memory cache
            performance_monitor: Optional performance monitor for tracking cache metrics
        """
        ...

    async def connect(self) -> bool:
        """
        Initialize Redis connection honoring this module's aioredis/flags.
        
        Mirrors the parent implementation but binds to the aioredis symbol
        defined in this module so unit tests can patch
        `app.infrastructure.cache.redis.aioredis` as expected.
        """
        ...

    async def get_cached_response(self, text: str, operation: str, options: Dict[str, Any], question: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Multi-tier cache retrieval with memory cache optimization for small texts.
        Includes comprehensive performance monitoring for cache hit ratio tracking.
        
        Args:
            text: Input text content
            operation: Operation type
            options: Operation options
            question: Optional question for Q&A operations
        
        Returns:
            Cached response if found, None otherwise
        """
        ...

    async def cache_response(self, text: str, operation: str, options: Dict[str, Any], response: Dict[str, Any], question: Optional[str] = None):
        """
        Cache AI response with compression for large data and appropriate TTL.
        
        Stores an AI response in the cache with intelligent compression based on
        response size, appropriate TTL based on operation type, and comprehensive
        performance monitoring.
        
        Args:
            text (str): Input text that generated this response.
            operation (str): Operation type (e.g., 'summarize', 'sentiment').
            options (Dict[str, Any]): Operation options used to generate response.
            response (Dict[str, Any]): AI response data to cache.
            question (str, optional): Question for Q&A operations. Defaults to None.
        
        Returns:
            None: This method performs caching as a side effect.
        
        Raises:
            None: All Redis exceptions are caught and logged as warnings.
        
        Note:
            - Responses larger than compression_threshold are automatically compressed
            - TTL varies by operation type (e.g., sentiment: 24h, qa: 30min)
            - Performance metrics are automatically recorded
        
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.cache_response(
            ...     text="Long document...",
            ...     operation="summarize",
            ...     options={"max_length": 100},
            ...     response={"summary": "Brief summary", "confidence": 0.95}
            ... )
        """
        ...

    async def invalidate_pattern(self, pattern: str, operation_context: str = ''):
        """
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
        """
        ...

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics including Redis and memory cache metrics.
        
        Collects statistics from Redis (if available), in-memory cache, and
        performance monitoring system. Also records current memory usage for tracking.
        
        Returns:
            Dict[str, Any]: Comprehensive cache statistics containing:
                - redis: Redis connection status, key count, memory usage
                - memory: In-memory cache statistics and utilization
                - performance: Hit ratios, operation timings, compression stats
        
        Raises:
            None: Redis errors are caught and logged, returning error status.
        
        Example:
            >>> cache = AIResponseCache()
            >>> stats = await cache.get_cache_stats()
            >>> print(f"Hit ratio: {stats['performance']['hit_ratio']:.2%}")
            >>> print(f"Redis keys: {stats['redis']['keys']}")
            >>> print(f"Memory cache: {stats['memory']['memory_cache_entries']}")
        """
        ...

    def get_cache_hit_ratio(self) -> float:
        """
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
        """
        ...

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of cache performance metrics.
        
        Provides a consolidated view of key performance indicators including
        hit ratios, operation counts, timing statistics, and memory usage.
        
        Returns:
            Dict[str, Any]: Performance summary containing:
                - hit_ratio: Cache hit percentage
                - total_operations: Total cache operations performed
                - cache_hits/cache_misses: Breakdown of successful/failed retrievals
                - recent_avg_key_generation_time: Average key generation time
                - recent_avg_cache_operation_time: Average cache operation time
                - total_invalidations/total_keys_invalidated: Invalidation statistics
                - memory_usage: Memory usage statistics (if available)
        
        Example:
            >>> cache = AIResponseCache()
            >>> summary = cache.get_performance_summary()
            >>> print(f"Operations: {summary['total_operations']}")
            >>> print(f"Hit ratio: {summary['hit_ratio']:.1f}%")
            >>> print(f"Avg operation time: {summary['recent_avg_cache_operation_time']:.3f}s")
        """
        ...

    def record_memory_usage(self, redis_stats: Optional[Dict[str, Any]] = None):
        """
        Record current memory usage of cache components.
        
        Captures a snapshot of memory usage across different cache tiers
        including in-memory cache and Redis (if available). This data is
        used for performance monitoring and capacity planning.
        
        Args:
            redis_stats (Dict[str, Any], optional): Redis statistics from INFO command.
                                                   If None, only memory cache stats are recorded.
        
        Returns:
            None: This method records metrics as a side effect.
        
        Raises:
            None: All exceptions are caught and logged as warnings.
        
        Note:
            Called automatically by get_cache_stats() but can be called
            manually for more frequent memory monitoring.
        
        Example:
            >>> cache = AIResponseCache()
            >>> redis_info = await cache.redis.info() if cache.redis else None
            >>> cache.record_memory_usage(redis_info)
        """
        ...

    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """
        Get detailed memory usage statistics for cache components.
        
        Returns comprehensive memory usage information including utilization
        percentages, growth trends, and efficiency metrics.
        
        Returns:
            Dict[str, Any]: Memory usage statistics containing:
                - current_usage: Current memory consumption
                - historical_trend: Memory usage over time
                - efficiency_metrics: Memory efficiency indicators
                - warning_indicators: Memory usage warnings if applicable
        
        Example:
            >>> cache = AIResponseCache()
            >>> memory_stats = cache.get_memory_usage_stats()
            >>> print(f"Memory cache utilization: {memory_stats.get('utilization', 0):.1f}%")
        """
        ...

    def get_memory_warnings(self) -> List[Dict[str, Any]]:
        """
        Get active memory-related warnings and alerts.
        
        Returns any current warnings about memory usage that may indicate
        performance issues or capacity constraints.
        
        Returns:
            List[Dict[str, Any]]: List of active memory warnings, each containing:
                - severity: Warning level ('warning', 'critical')
                - message: Human-readable warning description
                - threshold: The threshold that was exceeded
                - current_value: Current value that triggered the warning
                - recommendations: Suggested actions to resolve the issue
        
        Example:
            >>> cache = AIResponseCache()
            >>> warnings = cache.get_memory_warnings()
            >>> for warning in warnings:
            ...     print(f"{warning['severity'].upper()}: {warning['message']}")
            WARNING: Memory cache approaching size limit (95/100 entries)
        """
        ...

    def reset_performance_stats(self):
        """
        Reset all performance statistics and measurements.
        
        Clears all accumulated performance data including hit/miss counts,
        timing measurements, compression statistics, and memory usage history.
        Useful for starting fresh performance analysis periods.
        
        Returns:
            None: This method resets statistics as a side effect.
        
        Warning:
            This action cannot be undone. All historical performance data
            will be lost. Consider exporting metrics before resetting if
            historical data is needed.
        
        Example:
            >>> cache = AIResponseCache()
            >>> # Export current metrics before reset if needed
            >>> metrics = cache.get_performance_summary()
            >>> cache.reset_performance_stats()
            >>> print("Performance statistics reset")
        """
        ...

    def get_invalidation_frequency_stats(self) -> Dict[str, Any]:
        """
        Get invalidation frequency statistics and analysis.
        
        Provides detailed analysis of cache invalidation patterns including
        frequency, timing, and efficiency metrics. Useful for optimizing
        cache management strategies.
        
        Returns:
            Dict[str, Any]: Invalidation statistics containing:
                - frequency_metrics: How often invalidations occur
                - pattern_analysis: Most common invalidation patterns
                - timing_statistics: Time taken for invalidation operations
                - efficiency_indicators: Invalidation effectiveness metrics
        
        Example:
            >>> cache = AIResponseCache()
            >>> stats = cache.get_invalidation_frequency_stats()
            >>> print(f"Invalidations per hour: {stats.get('per_hour', 0)}")
            >>> print(f"Most common pattern: {stats.get('top_patterns', ['None'])[0]}")
        """
        ...

    def get_invalidation_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get recommendations based on invalidation patterns and performance data.
        
        Analyzes invalidation patterns and provides actionable recommendations
        for optimizing cache invalidation strategies and improving performance.
        
        Returns:
            List[Dict[str, Any]]: List of recommendations, each containing:
                - type: Recommendation category ('optimization', 'warning', 'configuration')
                - priority: Importance level ('high', 'medium', 'low')
                - message: Human-readable recommendation
                - action: Specific action to take
                - expected_benefit: Expected performance improvement
        
        Example:
            >>> cache = AIResponseCache()
            >>> recommendations = cache.get_invalidation_recommendations()
            >>> for rec in recommendations:
            ...     if rec['priority'] == 'high':
            ...         print(f"HIGH: {rec['message']}")
            HIGH: Consider increasing TTL for sentiment operations (low invalidation value)
        """
        ...

    async def invalidate_all(self, operation_context: str = 'manual_clear_all'):
        """
        Invalidate all cache entries in Redis and memory cache.
        
        Clears the entire cache by invalidating all entries. This is a
        comprehensive operation that affects both Redis and in-memory caches.
        
        Args:
            operation_context (str, optional): Context describing why the full
                                             invalidation was triggered.
                                             Defaults to "manual_clear_all".
        
        Returns:
            None: This method performs invalidation as a side effect.
        
        Warning:
            This operation removes ALL cached data and cannot be undone.
            Use with caution in production environments.
        
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.invalidate_all(operation_context="model_deployment")
            >>> print("All cache entries have been cleared")
        """
        ...

    async def invalidate_by_operation(self, operation: str, operation_context: str = ''):
        """
        Invalidate cache entries for a specific operation type.
        
        Removes all cached responses for a particular operation (e.g., 'summarize',
        'sentiment') while leaving other operation types intact.
        
        Args:
            operation (str): Operation type to invalidate (e.g., 'summarize', 'sentiment').
            operation_context (str, optional): Context describing why this operation's
                                             cache was invalidated. Auto-generated if not provided.
        
        Returns:
            None: This method performs invalidation as a side effect.
        
        Example:
            >>> cache = AIResponseCache()
            >>> # Invalidate all summarization results due to model update
            >>> await cache.invalidate_by_operation(
            ...     operation="summarize",
            ...     operation_context="summarization_model_updated"
            ... )
            >>> print("All summarization cache entries cleared")
        """
        ...

    async def invalidate_memory_cache(self, operation_context: str = 'memory_cache_clear'):
        """
        Clear the in-memory cache and record the invalidation event.
        
        Removes all entries from the in-memory cache tier while preserving
        Redis cache entries. Records the invalidation for performance monitoring.
        
        Args:
            operation_context (str, optional): Context describing why the memory cache
                                             was cleared. Defaults to "memory_cache_clear".
        
        Returns:
            None: This method performs cache clearing as a side effect.
        
        Note:
            This only affects the in-memory cache tier. Redis cache entries
            remain intact and will repopulate the memory cache on access.
        
        Example:
            >>> cache = AIResponseCache()
            >>> await cache.invalidate_memory_cache(
            ...     operation_context="memory_optimization"
            ... )
            >>> print("Memory cache cleared, Redis cache preserved")
        """
        ...
