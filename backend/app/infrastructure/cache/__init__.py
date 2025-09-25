"""**Comprehensive cache infrastructure with multiple implementations and monitoring.**

This module serves as the central entry point for all cache-related functionality,
providing multiple cache implementations, configuration management, and comprehensive
monitoring capabilities for both web and AI applications.

## Directory Structure

The cache module is organized into specialized components:

- **Core Implementations**: `base.py`, `memory.py`, `redis_generic.py`, `redis_ai.py`
- **Configuration**: `config.py`, `ai_config.py`, `cache_presets.py`, `dependencies.py`
- **Utilities**: `factory.py`, `key_generator.py`, `parameter_mapping.py`
- **Advanced Features**: `monitoring.py`, `security.py`

## Main Components

- **CacheInterface**: Abstract base class for all cache implementations
- **AIResponseCache**: AI-optimized Redis cache with intelligent key generation
- **GenericRedisCache**: Flexible Redis cache with L1 memory cache
- **InMemoryCache**: High-performance in-memory cache with TTL and LRU eviction
- **CacheFactory**: Explicit cache creation with environment-optimized defaults
- **CacheConfig**: Comprehensive configuration management with preset system
- **CachePerformanceMonitor**: Real-time monitoring and analytics
- **FastAPI Dependencies**: Complete dependency injection with lifecycle management

## Quick Start

```python
# Preset-based configuration (recommended)
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory

config = get_cache_config()  # Uses CACHE_PRESET environment variable
cache = CacheFactory.create_cache_from_config(config)

# Standard cache operations
await cache.set("key", {"data": "value"}, ttl=3600)
result = await cache.get("key")
```

See the component README.md for comprehensive usage examples and configuration details.
"""

# Base interface
from .base import CacheInterface
# Memory implementation
from .memory import InMemoryCache
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
    # Memory implementation
    "InMemoryCache",
    # Monitoring and metrics
    "CachePerformanceMonitor",
    "PerformanceMetric",
    "CompressionMetric",
    "MemoryUsageMetric",
    "InvalidationMetric",
    # Factory and configuration
    "CacheFactory",
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
    "featuring explicit cache factory patterns, enhanced configuration management "
    "with builder pattern, and comprehensive FastAPI dependency injection with "
    "lifecycle management"
)
