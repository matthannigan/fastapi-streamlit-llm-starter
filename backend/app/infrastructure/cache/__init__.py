"""
Cache Infrastructure Module

This module provides a comprehensive caching infrastructure with multiple implementations
and monitoring capabilities. It serves as the single point of entry for all cache-related
functionality in the application.

Main Components:
    - CacheInterface: Abstract base class for all cache implementations
    - AIResponseCache: Redis-based cache with compression and tiered storage
    - InMemoryCache: High-performance in-memory cache with TTL and LRU eviction
    - CacheKeyGenerator: Optimized cache key generation for large texts
    - CachePerformanceMonitor: Comprehensive performance monitoring and analytics

Cache Implementations:
    - Redis-based caching with fallback to memory-only mode
    - In-memory caching with TTL and LRU eviction
    - Graceful degradation when Redis is unavailable

Monitoring and Analytics:
    - Real-time performance metrics
    - Memory usage tracking
    - Compression efficiency monitoring
    - Cache invalidation pattern analysis
    - Automatic threshold-based alerting

Usage Example:
    >>> from app.infrastructure.cache import AIResponseCache, InMemoryCache
    >>> 
    >>> # Redis-based cache for production
    >>> cache = AIResponseCache(redis_url="redis://localhost:6379")
    >>> await cache.connect()
    >>> 
    >>> # In-memory cache for development/testing
    >>> memory_cache = InMemoryCache(default_ttl=3600, max_size=1000)
    >>> 
    >>> # Cache an AI response
    >>> await cache.cache_response(
    ...     text="Document to process",
    ...     operation="summarize",
    ...     options={"max_length": 100},
    ...     response={"summary": "Brief summary"}
    ... )
    >>> 
    >>> # Get cached response
    >>> result = await cache.get_cached_response(
    ...     text="Document to process",
    ...     operation="summarize",
    ...     options={"max_length": 100}
    ... )

Configuration:
    The cache system supports extensive configuration for:
    - TTL (Time-To-Live) settings per operation type
    - Compression thresholds and levels
    - Memory cache size limits
    - Performance monitoring thresholds
    - Redis connection settings
"""

# Base interface
from .base import CacheInterface
# Performance benchmarking
from .benchmarks import (BenchmarkResult, BenchmarkSuite,
                         CacheBenchmarkDataGenerator, CachePerformanceBenchmark,
                         CachePerformanceThresholds, ComparisonResult,
                         PerformanceRegressionDetector)
# Compatibility wrapper
from .compatibility import CacheCompatibilityWrapper
# Memory implementation
from .memory import InMemoryCache
# Migration utilities
from .migration import CacheMigrationManager
# Monitoring and metrics
from .monitoring import (CachePerformanceMonitor, CompressionMetric,
                         InvalidationMetric, MemoryUsageMetric,
                         PerformanceMetric)
# Redis implementation with all components
from .redis import (REDIS_AVAILABLE, AIResponseCache, CacheKeyGenerator,
                    aioredis)
# Generic Redis implementation
from .redis_generic import GenericRedisCache

# Export all public components
__all__ = [
    # Base interface
    "CacheInterface",
    # Redis implementation
    "AIResponseCache",
    "CacheKeyGenerator",
    "REDIS_AVAILABLE",
    "aioredis",
    # Generic Redis implementation
    "GenericRedisCache",
    # Performance benchmarking
    "CachePerformanceBenchmark",
    "BenchmarkResult",
    "BenchmarkSuite",
    "ComparisonResult",
    "CacheBenchmarkDataGenerator",
    "PerformanceRegressionDetector",
    "CachePerformanceThresholds",
    # Migration utilities
    "CacheMigrationManager",
    # Compatibility wrapper
    "CacheCompatibilityWrapper",
    # Memory implementation
    "InMemoryCache",
    # Monitoring and metrics
    "CachePerformanceMonitor",
    "PerformanceMetric",
    "CompressionMetric",
    "MemoryUsageMetric",
    "InvalidationMetric",
]

# Version information
__version__ = "1.0.0"

# Module metadata
__author__ = "FastAPI Streamlit LLM Starter"
__description__ = (
    "Comprehensive caching infrastructure with Redis and in-memory implementations"
)
