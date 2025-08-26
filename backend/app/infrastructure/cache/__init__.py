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
    >>> # Cache an AI response
    >>> await ai_cache.cache_response(
    ...     text="Document to process",
    ...     operation="summarize",
    ...     options={"max_length": 100},
    ...     response={"summary": "Brief summary"}
    ... )
    >>> 
    >>> # Get cached response
    >>> result = await ai_cache.get_cached_response(
    ...     text="Document to process",
    ...     operation="summarize",
    ...     options={"max_length": 100}
    ... )

Legacy Usage (Still Supported):
    >>> from app.infrastructure.cache import AIResponseCache, GenericRedisCache, InMemoryCache
    >>> from app.infrastructure.cache import AIResponseCacheConfig
    >>> 
    >>> # AI-specific Redis cache with configuration
    >>> config = AIResponseCacheConfig(redis_url="redis://localhost:6379")
    >>> cache = AIResponseCache(**config.to_ai_cache_kwargs())
    >>> await cache.connect()
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

# Base interface
from .base import CacheInterface
# Performance benchmarking
from .benchmarks import (BenchmarkResult, BenchmarkSuite,
                         CacheBenchmarkDataGenerator, CachePerformanceBenchmark,
                         CachePerformanceThresholds, ComparisonResult,
                         PerformanceRegressionDetector)
# Compatibility wrapper (removed - no longer needed)
# Memory implementation
from .memory import InMemoryCache
# Migration utilities
from .migration import CacheMigrationManager
# Monitoring and metrics
from .monitoring import (CachePerformanceMonitor, CompressionMetric,
                         InvalidationMetric, MemoryUsageMetric,
                         PerformanceMetric)
# AI-specific Redis implementation
from .redis_ai import AIResponseCache
# Generic Redis implementation  
from .redis_generic import GenericRedisCache, REDIS_AVAILABLE, aioredis
# Cache key generation
from .key_generator import CacheKeyGenerator
# AI configuration management
from .ai_config import AIResponseCacheConfig
# Parameter mapping utilities
from .parameter_mapping import ValidationResult, CacheParameterMapper
# Security components
from .security import (RedisCacheSecurityManager, SecurityConfig, 
                       SecurityValidationResult, create_security_config_from_env)
# Phase 3 enhancements
# Factory for explicit cache instantiation
from .factory import CacheFactory
# Enhanced configuration management
from .config import (CacheConfig, AICacheConfig, CacheConfigBuilder, 
                     EnvironmentPresets, ValidationResult as ConfigValidationResult)
# FastAPI dependency integration
from .dependencies import (get_settings, get_cache_config, get_cache_service, 
                          get_web_cache_service, get_ai_cache_service, 
                          get_test_cache, get_test_redis_cache, 
                          get_fallback_cache_service, validate_cache_configuration,
                          get_cache_service_conditional, cleanup_cache_registry,
                          get_cache_health_status, CacheDependencyManager)

# Export all public components
__all__ = [
    # Base interface
    "CacheInterface",
    # AI Redis implementation
    "AIResponseCache",
    "AIResponseCacheConfig",
    # Generic Redis implementation
    "GenericRedisCache",
    "REDIS_AVAILABLE",
    "aioredis",
    # Cache key generation
    "CacheKeyGenerator",
    # Parameter mapping and validation
    "ValidationResult",
    "CacheParameterMapper",
    # Security components
    "RedisCacheSecurityManager",
    "SecurityConfig",
    "SecurityValidationResult",
    "create_security_config_from_env",
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
    # Memory implementation
    "InMemoryCache",
    # Monitoring and metrics
    "CachePerformanceMonitor",
    "PerformanceMetric",
    "CompressionMetric",
    "MemoryUsageMetric",
    "InvalidationMetric",
    # Phase 3 enhancements
    # Factory for explicit cache instantiation
    "CacheFactory",
    # Enhanced configuration management
    "CacheConfig",
    "AICacheConfig", 
    "CacheConfigBuilder",
    "EnvironmentPresets",
    "ConfigValidationResult",
    # FastAPI dependency integration
    "get_settings",
    "get_cache_config",
    "get_cache_service",
    "get_web_cache_service",
    "get_ai_cache_service",
    "get_test_cache",
    "get_test_redis_cache",
    "get_fallback_cache_service",
    "validate_cache_configuration",
    "get_cache_service_conditional",
    "cleanup_cache_registry",
    "get_cache_health_status",
    "CacheDependencyManager",
]

# Version information
__version__ = "3.0.0"

# Module metadata
__author__ = "FastAPI Streamlit LLM Starter"
__description__ = (
    "Comprehensive caching infrastructure with Redis and in-memory implementations, "
    "featuring Phase 3 enhancements: explicit cache factory patterns, enhanced "
    "configuration management with builder pattern, and comprehensive FastAPI "
    "dependency injection with lifecycle management"
)
