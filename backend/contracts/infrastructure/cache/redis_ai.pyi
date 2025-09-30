"""
AI-optimized Redis cache with intelligent key generation and compression.

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

## Usage Patterns

### Factory Method (Recommended)

**Most AI applications should use factory methods for AI-optimized defaults and intelligent features:**

```python
from app.infrastructure.cache import CacheFactory

factory = CacheFactory()

# AI applications - recommended approach
cache = await factory.for_ai_app(
    redis_url="redis://localhost:6379",
    default_ttl=3600,  # 1 hour
    operation_ttls={
        "summarize": 7200,  # 2 hours - summaries are stable
        "sentiment": 86400,  # 24 hours - sentiment rarely changes
        "translate": 14400   # 4 hours - translations moderately stable
    }
)

# Production AI cache with security
from app.infrastructure.security import SecurityConfig
security_config = SecurityConfig(
    redis_auth="ai-cache-password",
    use_tls=True,
    verify_certificates=True
)
cache = await factory.for_ai_app(
    redis_url="rediss://ai-production:6380",
    security_config=security_config,
    text_hash_threshold=1000,
    fail_on_connection_error=True
)
```

**Factory Method Benefits for AI Applications:**
- AI-optimized defaults with operation-specific TTLs
- Intelligent text hashing for large inputs
- Enhanced compression for AI response storage
- AI-specific monitoring and performance analytics
- Automatic fallback with graceful degradation

### Direct Instantiation (Advanced AI Use Cases)

**Use direct instantiation for specialized AI cache configurations:**

```python
cache = AIResponseCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600,
    text_hash_threshold=500,
    operation_ttls={
        "custom_ai_operation": 1800,
        "specialized_nlp": 7200
    },
    compression_threshold=1000,
    compression_level=8
)

# Manual connection handling required
connected = await cache.connect()
if not connected:
    raise InfrastructureError("AI cache connection required")

# AI response caching with intelligent key generation
key = cache.build_key(
    text="Long document to process...",
    operation="summarize",
    options={"max_length": 100}
)
await cache.set(key, {"summary": "Brief summary"}, ttl=3600)
```

**Use direct instantiation when:**
- Building custom AI cache implementations with specialized features
- Requiring exact AI parameter combinations not supported by factory methods
- Developing AI-specific frameworks or libraries
- Migrating legacy AI systems with custom configurations

**📖 For comprehensive factory usage patterns and AI-specific configuration examples, see [Cache Usage Guide](../../../docs/guides/infrastructure/cache/usage-guide.md).**

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
"""

import hashlib
import inspect
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock
from app.core.exceptions import ConfigurationError, InfrastructureError, ValidationError
from app.infrastructure.cache.key_generator import CacheKeyGenerator
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
from app.infrastructure.cache.redis_generic import GenericRedisCache


class AIResponseCache(GenericRedisCache):
    """
    AI Response Cache with automatic security inheritance.
    
    This secure-first implementation inherits all security features from GenericRedisCache
    automatically, including TLS encryption, authentication, and data encryption at rest.
    All AI-specific functionality is preserved while security is handled transparently.
    
    ## Key Features
    
    - **Automatic Security**: Inherits TLS, authentication, and encryption from GenericRedisCache
    - **AI-Optimized**: Specialized features for AI response caching and text processing
    - **Clean Architecture**: Simplified parameters focus on AI-specific functionality
    - **Backward Compatible**: Existing API preserved with deprecation warnings for security params
    - **Enhanced Performance**: AI-specific callbacks and metrics collection
    
    ## Automatic Security Features
    
    All security features are enabled automatically without configuration:
    - **TLS Encryption**: Secure Redis connections with certificate validation
    - **Authentication**: Automatic Redis authentication and ACL support
    - **Data Encryption**: Transparent Fernet encryption for all cached data
    - **Security Validation**: Automatic environment-aware security enforcement
    
    ## AI-Specific Parameters
    
    Focus on AI functionality - security is handled automatically:
    - `redis_url` (str): Redis connection URL (security applied automatically)
    - `default_ttl` (int): Default time-to-live for cache entries
    - `text_hash_threshold` (int): Character threshold for text hashing
    - `hash_algorithm`: Hash algorithm for large texts
    - `compression_threshold` (int): Size threshold for compression
    - `compression_level` (int): Compression level (1-9)
    - `text_size_tiers` (Dict[str, int]): Text categorization thresholds
    - `l1_cache_size` (int): Maximum L1 cache entries
    - `operation_ttls` (Dict[str, int]): TTL values per AI operation type
    
    ## Returns
    
    A fully functional AIResponseCache instance with automatic security inheritance.
    
    ## Examples
    
    ```python
    # Simple usage - security is automatic
    cache = AIResponseCache(redis_url="redis://localhost:6379")
    await cache.connect()
    
    # AI-optimized configuration
    cache = AIResponseCache(
        redis_url="redis://production:6379",
        text_hash_threshold=1000,
        l1_cache_size=200,
        operation_ttls={
            "summarize": 7200,  # 2 hours
            "sentiment": 86400, # 24 hours
        }
    )
    
    # All security features are enabled automatically:
    # - TLS encryption for Redis connections
    # - Fernet encryption for cached data
    # - Automatic authentication and validation
    ```
    
    Note:
        Security parameters (security_config, use_tls, etc.) are no longer needed
        and will generate deprecation warnings. Security is always enabled.
    """

    def __init__(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 3600, text_hash_threshold: int = 1000, hash_algorithm = hashlib.sha256, compression_threshold: int = 1000, compression_level: int = 6, text_size_tiers: Optional[Dict[str, int]] = None, memory_cache_size: Optional[int] = None, l1_cache_size: int = 100, enable_l1_cache: bool = True, performance_monitor: Optional[CachePerformanceMonitor] = None, operation_ttls: Optional[Dict[str, int]] = None, **kwargs):
        """
        Initialize AIResponseCache with automatic security inheritance.
        
        This simplified constructor focuses on AI-specific parameters while
        automatically inheriting security features from the secure GenericRedisCache.
        All security features (TLS, authentication, encryption) are enabled automatically.
        
        Args:
            redis_url: Redis connection URL (security features applied automatically)
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
        
        Raises:
            ConfigurationError: If parameter mapping fails or invalid configuration
            ValidationError: If parameter validation fails
            InfrastructureError: If Redis connection fails (automatic fallback to memory cache)
        
        Note:
            Security features (TLS, authentication, encryption) are automatically enabled
            by the parent GenericRedisCache. No explicit security configuration needed.
        """
        ...

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

    async def invalidate_by_operation(self, operation: str, operation_context: str = '') -> int:
        """
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
        """
        ...

    async def clear(self, operation_context: str = 'test_clear') -> None:
        """
        Clear all AI cache entries from both Redis and the L1 memory cache.
        
        This method removes keys matching the AI cache namespace (ai_cache:*)
        from Redis and purges the in-process L1 cache.
        
        Args:
            operation_context: Optional context string for metrics.
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
                - ai_metrics: AI-specific performance metrics
        
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
        """
        ...

    async def connect(self) -> bool:
        """
        Initialize Redis connection honoring this module's aioredis/flags.
        
        Mirrors the parent implementation but binds to the aioredis symbol
        defined in this module so unit tests can patch
        `app.infrastructure.cache.redis_ai.aioredis` as expected.
        """
        ...

    def get_ai_performance_summary(self) -> Dict[str, Any]:
        """
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
        """
        ...

    def get_text_tier_statistics(self) -> Dict[str, Any]:
        """
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
        """
        ...

    def get_operation_performance(self) -> Dict[str, Any]:
        """
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
        """
        ...

    @property
    def memory_cache(self) -> Dict[str, Any]:
        """
        Legacy compatibility property for memory cache access.
        """
        ...

    @memory_cache.setter
    def memory_cache(self, value: Dict[str, Any]) -> None:
        """
        Legacy compatibility setter for memory cache (not used in new implementation).
        """
        ...

    @memory_cache.deleter
    def memory_cache(self) -> None:
        """
        Legacy compatibility deleter for memory cache.
        """
        ...

    @property
    def memory_cache_size(self) -> int:
        """
        Legacy compatibility property for memory cache size.
        """
        ...

    @property
    def memory_cache_order(self) -> List[str]:
        """
        Legacy compatibility property for memory cache order (not used in new implementation).
        """
        ...
