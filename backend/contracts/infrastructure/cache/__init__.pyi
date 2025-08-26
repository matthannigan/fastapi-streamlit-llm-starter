"""
Cache Infrastructure Module

This module provides a comprehensive caching infrastructure with multiple implementations
and monitoring capabilities. It serves as the single point of entry for all cache-related
functionality in the application.

Main Components:
    - CacheInterface: Abstract base class for all cache implementations
    - AIResponseCache: AI-specific Redis cache with intelligent features
    - GenericRedisCache: Generic Redis cache base implementation
    - InMemoryCache: High-performance in-memory cache with TTL and LRU eviction
    - CacheKeyGenerator: Optimized cache key generation for large texts
    - CachePerformanceMonitor: Comprehensive performance monitoring and analytics
    - AIResponseCacheConfig: Configuration management for AI cache
    - CacheParameterMapper: Parameter mapping and validation utilities
    - RedisCacheSecurityManager: Redis security management and authentication
    - SecurityConfig: Security configuration for Redis connections

Phase 3 Enhancements:
    - CacheFactory: Explicit cache creation with deterministic behavior
    - CacheConfig: Enhanced configuration management with validation
    - AICacheConfig: AI-specific configuration extensions
    - CacheConfigBuilder: Builder pattern for flexible configuration
    - EnvironmentPresets: Pre-configured settings for different environments
    - FastAPI Dependencies: Comprehensive dependency injection system with lifecycle management

Cache Implementations:
    - Redis-based caching with fallback to memory-only mode
    - In-memory caching with TTL and LRU eviction
    - Graceful degradation when Redis is unavailable

Security Features:
    - TLS/SSL encryption for Redis connections
    - Authentication support with username/password
    - Redis AUTH command support
    - Certificate-based authentication
    - Security configuration validation
    - Connection security management

Monitoring and Analytics:
    - Real-time performance metrics
    - Memory usage tracking
    - Compression efficiency monitoring
    - Cache invalidation pattern analysis
    - Automatic threshold-based alerting

Usage Example (Phase 3 Factory Pattern):
    >>> from app.infrastructure.cache import CacheFactory, CacheConfigBuilder
    >>> 
    >>> # Explicit cache creation for web applications
    >>> web_cache = CacheFactory.for_web_app(redis_url="redis://localhost:6379")
    >>> await web_cache.connect()
    >>> 
    >>> # Explicit cache creation for AI applications
    >>> ai_cache = CacheFactory.for_ai_app(redis_url="redis://localhost:6379")
    >>> await ai_cache.connect()
    >>> 
    >>> # Configuration-based cache creation
    >>> config = (CacheConfigBuilder()
    ...           .for_environment("production")
    ...           .with_redis("redis://localhost:6379")
    ...           .with_ai_features()
    ...           .build())
    >>> cache = CacheFactory.create_cache_from_config(config)
    >>> 
    >>> # Testing cache creation
    >>> test_cache = CacheFactory.for_testing("memory")
    >>> 
    >>> # Standard interface usage (infrastructure layer)
    >>> cache_key = ai_cache.build_key("Document to process", "summarize", {"max_length": 100})
    >>> await ai_cache.set(cache_key, {"summary": "Brief summary"}, ttl=3600)
    >>> 
    >>> # Get cached response using standard interface
    >>> result = await ai_cache.get(cache_key)
    >>> 
    >>> # Domain service usage (recommended pattern)
    >>> from app.services.text_processor import TextProcessorService
    >>> service = TextProcessorService(settings=settings, cache=ai_cache)
    >>> # Domain service handles all cache logic internally using standard interface

Direct Infrastructure Usage (Advanced):
    >>> from app.infrastructure.cache import AIResponseCache, GenericRedisCache, InMemoryCache
    >>> from app.infrastructure.cache import AIResponseCacheConfig
    >>> 
    >>> # AI-specific Redis cache with configuration (uses standard interface)
    >>> config = AIResponseCacheConfig(redis_url="redis://localhost:6379")
    >>> cache = AIResponseCache(**config.to_ai_cache_kwargs())
    >>> await cache.connect()
    >>> 
    >>> # Standard interface methods only
    >>> cache_key = cache.build_key("text", "operation", {"option": "value"})
    >>> await cache.set(cache_key, data, ttl=3600)
    >>> result = await cache.get(cache_key)
    >>> 
    >>> # Security configuration for Redis
    >>> from app.infrastructure.cache import SecurityConfig, RedisCacheSecurityManager
    >>> security_config = SecurityConfig(
    ...     username="cache_user",
    ...     password="secure_password",
    ...     use_tls=True
    ... )
    >>> security_manager = RedisCacheSecurityManager(security_config)

Configuration:
    The cache system supports extensive configuration for:
    - TTL (Time-To-Live) settings per operation type
    - Compression thresholds and levels
    - Memory cache size limits
    - Performance monitoring thresholds
    - Redis connection settings
    - Security settings (TLS, authentication, certificates)
    - Migration and compatibility options
"""

from .base import CacheInterface
from .benchmarks import BenchmarkResult, BenchmarkSuite, CacheBenchmarkDataGenerator, CachePerformanceBenchmark, CachePerformanceThresholds, ComparisonResult, PerformanceRegressionDetector
from .memory import InMemoryCache
from .migration import CacheMigrationManager
from .monitoring import CachePerformanceMonitor, CompressionMetric, InvalidationMetric, MemoryUsageMetric, PerformanceMetric
from .redis_ai import AIResponseCache
from .redis_generic import GenericRedisCache, REDIS_AVAILABLE, aioredis
from .key_generator import CacheKeyGenerator
from .ai_config import AIResponseCacheConfig
from .parameter_mapping import ValidationResult, CacheParameterMapper
from .security import RedisCacheSecurityManager, SecurityConfig, SecurityValidationResult, create_security_config_from_env
from .factory import CacheFactory
from .config import CacheConfig, AICacheConfig, CacheConfigBuilder, EnvironmentPresets, ValidationResult as ConfigValidationResult
from .dependencies import get_settings, get_cache_config, get_cache_service, get_web_cache_service, get_ai_cache_service, get_test_cache, get_test_redis_cache, get_fallback_cache_service, validate_cache_configuration, get_cache_service_conditional, cleanup_cache_registry, get_cache_health_status, CacheDependencyManager

__all__ = ['CacheInterface', 'AIResponseCache', 'AIResponseCacheConfig', 'GenericRedisCache', 'REDIS_AVAILABLE', 'aioredis', 'CacheKeyGenerator', 'ValidationResult', 'CacheParameterMapper', 'RedisCacheSecurityManager', 'SecurityConfig', 'SecurityValidationResult', 'create_security_config_from_env', 'CachePerformanceBenchmark', 'BenchmarkResult', 'BenchmarkSuite', 'ComparisonResult', 'CacheBenchmarkDataGenerator', 'PerformanceRegressionDetector', 'CachePerformanceThresholds', 'CacheMigrationManager', 'InMemoryCache', 'CachePerformanceMonitor', 'PerformanceMetric', 'CompressionMetric', 'MemoryUsageMetric', 'InvalidationMetric', 'CacheFactory', 'CacheConfig', 'AICacheConfig', 'CacheConfigBuilder', 'EnvironmentPresets', 'ConfigValidationResult', 'get_settings', 'get_cache_config', 'get_cache_service', 'get_web_cache_service', 'get_ai_cache_service', 'get_test_cache', 'get_test_redis_cache', 'get_fallback_cache_service', 'validate_cache_configuration', 'get_cache_service_conditional', 'cleanup_cache_registry', 'get_cache_health_status', 'CacheDependencyManager']
