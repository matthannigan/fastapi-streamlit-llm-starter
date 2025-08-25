"""
[REFACTORED] Cache Factory for Explicit Cache Instantiation

This module provides a comprehensive factory system for creating cache instances
with explicit configuration and deterministic behavior. It replaces auto-detection
patterns with explicit factory methods that provide clear, predictable cache
instantiation for different use cases.

Classes:
    CacheFactory: Main factory class providing explicit cache creation methods
                 for web applications, AI applications, testing environments,
                 and configuration-based instantiation.

Key Features:
    - **Explicit Cache Creation**: Clear, deterministic factory methods for specific use cases
    - **Environment-Optimized Defaults**: Pre-configured settings for web apps, AI apps, and testing
    - **Configuration-Based Creation**: Flexible cache creation from configuration objects
    - **Graceful Fallback**: Automatic fallback to InMemoryCache when Redis unavailable
    - **Comprehensive Validation**: Input validation with detailed error messages
    - **Error Handling**: Robust error handling with contextual information
    - **Type Safety**: Full type annotations for IDE support and static analysis

Factory Methods:
    - for_web_app(): Optimized cache for web applications with balanced performance
    - for_ai_app(): Specialized cache for AI applications with larger storage and compression
    - for_testing(): Testing-optimized cache with short TTLs and Redis test databases
    - create_cache_from_config(): Flexible configuration-based cache creation

Example Usage:
    Basic web application cache:
        >>> factory = CacheFactory()
        >>> cache = await factory.for_web_app(redis_url="redis://localhost:6379")
        >>> await cache.set("session:123", {"user_id": 456})

    AI application cache with custom settings:
        >>> cache = await factory.for_ai_app(
        ...     redis_url="redis://ai-cache:6379",
        ...     default_ttl=7200,
        ...     enable_compression=True
        ... )

    Testing cache with memory fallback:
        >>> cache = await factory.for_testing(
        ...     redis_url="redis://test:6379",
        ...     fail_on_connection_error=False
        ... )

    Configuration-based cache creation:
        >>> config = {
        ...     "redis_url": "redis://production:6379",
        ...     "default_ttl": 3600,
        ...     "enable_l1_cache": True,
        ...     "compression_threshold": 2000
        ... }
        >>> cache = await factory.create_cache_from_config(config)

Architecture Context:
    This factory is part of Phase 3 of the cache refactoring project, providing
    explicit cache instantiation to replace auto-detection patterns. It enables
    deterministic cache behavior while maintaining backward compatibility and
    providing optimized defaults for different application types.

Performance Considerations:
    - Factory methods execute in <10ms for typical configurations
    - Redis connection validation adds 5-50ms depending on network latency
    - Fallback to InMemoryCache is instantaneous (<1ms)
    - All factory methods are async to support connection validation

Error Handling:
    - ConfigurationError: Invalid parameters or configuration conflicts
    - ValidationError: Input validation failures with specific field information
    - InfrastructureError: Redis connection or infrastructure issues
    - All errors include context data for debugging and monitoring

Dependencies:
    Required:
        - app.infrastructure.cache.base.CacheInterface: Cache interface contract
        - app.infrastructure.cache.redis_generic.GenericRedisCache: Generic Redis cache
        - app.infrastructure.cache.redis_ai.AIResponseCache: AI-specialized cache
        - app.infrastructure.cache.memory.InMemoryCache: Memory fallback cache
        - app.core.exceptions: Custom exception hierarchy
    
    Optional:
        - redis.asyncio: Redis connectivity (graceful degradation if unavailable)
        - app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking
"""

import logging
from typing import Any, Dict, Optional, Union, TYPE_CHECKING
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.memory import InMemoryCache


class CacheFactory:
    """
    Factory class for explicit cache instantiation with environment-optimized defaults.
    
    This factory provides deterministic cache creation for different use cases,
    replacing auto-detection patterns with explicit configuration. Each factory
    method returns a fully configured cache instance optimized for specific
    application types and environments.
    
    Factory Methods:
        - for_web_app(): Web application cache with balanced performance
        - for_ai_app(): AI application cache with enhanced storage and compression
        - for_testing(): Testing cache with short TTLs and test database support
        - create_cache_from_config(): Configuration-driven cache creation
    
    Error Handling:
        All factory methods include comprehensive error handling with fallback
        to InMemoryCache when Redis is unavailable. Errors are logged with
        context information for debugging and monitoring.
    
    Example:
        >>> factory = CacheFactory()
        >>> cache = await factory.for_web_app(redis_url="redis://localhost:6379")
        >>> isinstance(cache, GenericRedisCache)
        True
    """

    def __init__(self):
        """
        Initialize the CacheFactory with default configuration.
        """
        ...

    async def for_web_app(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 1800, enable_l1_cache: bool = True, l1_cache_size: int = 200, compression_threshold: int = 2000, compression_level: int = 6, fail_on_connection_error: bool = False, **kwargs) -> CacheInterface:
        """
        Create a cache optimized for web applications with balanced performance.
        
        This factory method creates a GenericRedisCache configured with defaults
        optimized for typical web application caching patterns. It provides
        balanced performance between memory usage and cache hit rates, with
        moderate TTLs suitable for session data, API responses, and page caching.
        
        Web Application Optimizations:
            - 30-minute default TTL for reasonable session/data freshness
            - L1 memory cache enabled for fastest access to frequently used data
            - 200-item L1 cache size for good memory usage vs. hit rate balance
            - 2KB compression threshold to optimize network and storage
            - Moderate compression level (6) for balanced speed vs. compression ratio
            - Graceful Redis fallback for high availability
        
        Args:
            redis_url: Redis server URL (default: "redis://redis:6379")
            default_ttl: Default time-to-live in seconds (default: 1800/30min)
            enable_l1_cache: Enable in-memory L1 cache (default: True)
            l1_cache_size: Maximum L1 cache entries (default: 200)
            compression_threshold: Compress data above this size in bytes (default: 2000)
            compression_level: Zlib compression level 1-9 (default: 6)
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
            **kwargs: Additional parameters passed to GenericRedisCache
        
        Returns:
            CacheInterface: Configured cache instance (GenericRedisCache or InMemoryCache fallback)
        
        Raises:
            ValidationError: Invalid parameter values or combinations
            ConfigurationError: Configuration conflicts or missing requirements
            InfrastructureError: Redis connection failed and fail_on_connection_error=True
        
        Examples:
            Basic web application cache:
                >>> factory = CacheFactory()
                >>> cache = await factory.for_web_app()
                >>> await cache.set("session:abc123", {"user_id": 456})
            
            Production web cache with custom Redis:
                >>> cache = await factory.for_web_app(
                ...     redis_url="redis://production:6379",
                ...     default_ttl=3600,  # 1 hour
                ...     fail_on_connection_error=True
                ... )
            
            High-performance web cache:
                >>> cache = await factory.for_web_app(
                ...     l1_cache_size=500,
                ...     compression_threshold=5000,
                ...     compression_level=9
                ... )
        """
        ...

    async def for_ai_app(self, redis_url: str = 'redis://redis:6379', default_ttl: int = 3600, enable_l1_cache: bool = True, l1_cache_size: int = 100, compression_threshold: int = 1000, compression_level: int = 6, text_hash_threshold: int = 500, memory_cache_size: Optional[int] = None, operation_ttls: Optional[Dict[str, int]] = None, fail_on_connection_error: bool = False, **kwargs) -> CacheInterface:
        """
        Create a cache optimized for AI applications with enhanced storage and compression.
        
        This factory method creates an AIResponseCache configured with defaults
        optimized for AI workloads. It provides enhanced compression for large AI
        responses, operation-specific TTLs, intelligent key generation, and
        performance optimizations for typical AI usage patterns.
        
        AI Application Optimizations:
            - 1-hour default TTL for reasonable AI response freshness
            - Lower compression threshold (1KB) for better storage efficiency
            - 100-item L1 cache for frequently accessed AI responses
            - Text hashing threshold for intelligent key generation
            - Operation-specific TTLs for different AI operations
            - Enhanced monitoring for AI-specific metrics
        
        Args:
            redis_url: Redis server URL (default: "redis://redis:6379")
            default_ttl: Default time-to-live in seconds (default: 3600/1hr)
            enable_l1_cache: Enable in-memory L1 cache (default: True)
            l1_cache_size: Maximum L1 cache entries (default: 100)
            compression_threshold: Compress data above this size in bytes (default: 1000)
            compression_level: Zlib compression level 1-9 (default: 6)
            text_hash_threshold: Hash text above this length for keys (default: 500)
            memory_cache_size: Override l1_cache_size if provided
            operation_ttls: Custom TTLs per AI operation type
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
            **kwargs: Additional parameters passed to AIResponseCache
        
        Returns:
            CacheInterface: Configured AIResponseCache or InMemoryCache fallback
        
        Raises:
            ValidationError: Invalid parameter values or combinations
            ConfigurationError: Configuration conflicts or missing requirements
            InfrastructureError: Redis connection failed and fail_on_connection_error=True
        
        Examples:
            Basic AI application cache:
                >>> factory = CacheFactory()
                >>> cache = await factory.for_ai_app()
                >>> await cache.cache_response(
                ...     text="Document to analyze...",
                ...     operation="summarize",
                ...     options={"max_length": 100},
                ...     response={"summary": "Brief summary"}
                ... )
            
            Production AI cache with custom settings:
                >>> cache = await factory.for_ai_app(
                ...     redis_url="redis://ai-production:6379",
                ...     default_ttl=7200,  # 2 hours
                ...     operation_ttls={
                ...         "summarize": 1800,  # 30 minutes
                ...         "sentiment": 3600,  # 1 hour
                ...         "translate": 7200   # 2 hours
                ...     }
                ... )
            
            High-compression AI cache:
                >>> cache = await factory.for_ai_app(
                ...     compression_threshold=500,
                ...     compression_level=9,
                ...     text_hash_threshold=200
                ... )
        """
        ...

    async def for_testing(self, redis_url: str = 'redis://redis:6379/15', default_ttl: int = 60, enable_l1_cache: bool = False, l1_cache_size: int = 50, compression_threshold: int = 1000, compression_level: int = 1, fail_on_connection_error: bool = False, use_memory_cache: bool = False, **kwargs) -> CacheInterface:
        """
        Create a cache optimized for testing environments with short TTLs and fast operations.
        
        This factory method creates a cache configured for testing scenarios with
        short TTLs, minimal memory usage, fast operations, and support for Redis
        test databases. It can also return a pure InMemoryCache for isolated testing.
        
        Testing Optimizations:
            - 1-minute default TTL for quick test data expiration
            - Redis database 15 by default for test isolation
            - L1 cache disabled to simplify testing behavior
            - Fast compression (level 1) for minimal test overhead
            - Small cache sizes for minimal memory usage
            - Option to use InMemoryCache for isolated tests
        
        Args:
            redis_url: Redis server URL with test DB (default: "redis://redis:6379/15")
            default_ttl: Default time-to-live in seconds (default: 60/1min)
            enable_l1_cache: Enable in-memory L1 cache (default: False)
            l1_cache_size: Maximum L1 cache entries (default: 50)
            compression_threshold: Compress data above this size in bytes (default: 1000)
            compression_level: Zlib compression level 1-9 (default: 1)
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
            use_memory_cache: Force InMemoryCache usage (default: False)
            **kwargs: Additional parameters passed to cache implementation
        
        Returns:
            CacheInterface: Configured cache instance optimized for testing
        
        Raises:
            ValidationError: Invalid parameter values or combinations
            ConfigurationError: Configuration conflicts or missing requirements
            InfrastructureError: Redis connection failed and fail_on_connection_error=True
        
        Examples:
            Basic testing cache:
                >>> factory = CacheFactory()
                >>> cache = await factory.for_testing()
                >>> await cache.set("test_key", "test_value")
            
            Memory-only testing cache:
                >>> cache = await factory.for_testing(use_memory_cache=True)
                >>> # Guaranteed to be InMemoryCache
            
            Custom test database:
                >>> cache = await factory.for_testing(
                ...     redis_url="redis://test-server:6379/10",
                ...     default_ttl=30  # 30 seconds
                ... )
            
            Strict testing with connection requirements:
                >>> cache = await factory.for_testing(
                ...     fail_on_connection_error=True,
                ...     enable_l1_cache=True
                ... )
        """
        ...

    async def create_cache_from_config(self, config: Dict[str, Any], fail_on_connection_error: bool = False) -> CacheInterface:
        """
        Create a cache instance from a configuration dictionary with flexible parameter support.
        
        This factory method provides maximum flexibility by accepting a configuration
        dictionary and automatically determining the appropriate cache type based on
        the provided parameters. It supports both GenericRedisCache and AIResponseCache
        configurations with automatic parameter mapping and validation.
        
        Configuration Detection:
            - If AI-specific parameters are present (text_hash_threshold, operation_ttls),
              creates an AIResponseCache
            - Otherwise, creates a GenericRedisCache
            - Automatically handles parameter mapping and validation
            - Provides comprehensive error messages for invalid configurations
        
        Args:
            config: Configuration dictionary with cache parameters
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
        
        Required Configuration Keys:
            - redis_url (str): Redis server URL
        
        Optional Configuration Keys:
            Common parameters:
                - default_ttl (int): Default time-to-live in seconds
                - enable_l1_cache (bool): Enable in-memory L1 cache
                - l1_cache_size (int): Maximum L1 cache entries
                - compression_threshold (int): Compress data above this size
                - compression_level (int): Zlib compression level 1-9
            
            AI-specific parameters (triggers AIResponseCache):
                - text_hash_threshold (int): Hash text above this length
                - operation_ttls (Dict[str, int]): Custom TTLs per operation
                - memory_cache_size (int): Override l1_cache_size
        
        Returns:
            CacheInterface: Configured cache instance based on configuration
        
        Raises:
            ValidationError: Invalid configuration parameters or missing required keys
            ConfigurationError: Configuration conflicts or incompatible parameters
            InfrastructureError: Redis connection failed and fail_on_connection_error=True
        
        Examples:
            Basic Redis cache configuration:
                >>> config = {
                ...     "redis_url": "redis://localhost:6379",
                ...     "default_ttl": 3600,
                ...     "enable_l1_cache": True,
                ...     "compression_threshold": 2000
                ... }
                >>> cache = await factory.create_cache_from_config(config)
                >>> isinstance(cache, GenericRedisCache)
                True
            
            AI cache configuration:
                >>> config = {
                ...     "redis_url": "redis://ai-cache:6379",
                ...     "default_ttl": 7200,
                ...     "text_hash_threshold": 500,
                ...     "operation_ttls": {"summarize": 1800, "sentiment": 3600}
                ... }
                >>> cache = await factory.create_cache_from_config(config)
                >>> isinstance(cache, AIResponseCache)
                True
            
            Production configuration with strict error handling:
                >>> config = {
                ...     "redis_url": "redis://production:6379",
                ...     "default_ttl": 3600,
                ...     "compression_level": 9,
                ...     "enable_l1_cache": True,
                ...     "l1_cache_size": 500
                ... }
                >>> cache = await factory.create_cache_from_config(
                ...     config, 
                ...     fail_on_connection_error=True
                ... )
        """
        ...
