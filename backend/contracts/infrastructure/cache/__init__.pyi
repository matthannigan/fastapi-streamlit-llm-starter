"""
**Security-first cache infrastructure with comprehensive Redis and in-memory implementations.**

This module serves as the central entry point for all cache-related functionality,
providing multiple cache implementations with mandatory security, configuration management,
and comprehensive monitoring capabilities for both web and AI applications.

## Security-First Architecture

**All Redis connections enforce mandatory security:**
- **TLS Encryption**: Required for all Redis connections (rediss:// protocol)
- **Authentication**: Strong password authentication mandatory
- **Data Encryption**: Always-on Fernet encryption for cached data
- **Environment-Aware**: Security levels adapt per environment (development, staging, production)

## Directory Structure

The cache module is organized into specialized components:

- **Core Implementations**: `base.py`, `memory.py`, `redis_generic.py`, `redis_ai.py`
- **Security & Configuration**: `security.py`, `config.py`, `ai_config.py`, `cache_presets.py`
- **Utilities**: `factory.py`, `key_generator.py`, `parameter_mapping.py`, `dependencies.py`
- **Monitoring**: `monitoring.py`

## Main Components

- **CacheInterface**: Abstract base class for all cache implementations
- **AIResponseCache**: AI-optimized Redis cache with security and intelligent key generation
- **GenericRedisCache**: Flexible Redis cache with mandatory security and L1 memory cache
- **InMemoryCache**: High-performance in-memory cache with TTL and LRU eviction
- **SecurityConfig**: Mandatory security configuration with TLS and encryption
- **RedisCacheSecurityManager**: Security validation and enforcement
- **CacheFactory**: Explicit cache creation with environment-optimized secure defaults
- **CacheConfig**: Comprehensive configuration management with preset system
- **CachePerformanceMonitor**: Real-time monitoring and analytics
- **FastAPI Dependencies**: Complete dependency injection with lifecycle management

## Quick Start

```python
# Preset-based secure configuration (recommended)
from app.infrastructure.cache.dependencies import get_cache_config
from app.infrastructure.cache import CacheFactory

# Uses CACHE_PRESET environment variable with automatic secure Redis setup
config = get_cache_config()
cache = CacheFactory.create_cache_from_config(config)

# Standard cache operations with transparent encryption
await cache.set("key", {"data": "value"}, ttl=3600)
result = await cache.get("key")
```

## Security Setup

For one-command secure Redis setup:
```bash
# Automated secure setup (generates certificates, passwords, encryption keys)
./scripts/setup-secure-redis.sh

# Or manually generate configuration
python scripts/generate-secure-env.py --environment production
```

See the component README.md for comprehensive usage examples and configuration details.
See docs/guides/infrastructure/cache/security.md for security architecture and setup.
"""

from .base import CacheInterface
from .memory import InMemoryCache
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

__all__ = ['CacheInterface', 'AIResponseCache', 'AIResponseCacheConfig', 'GenericRedisCache', 'REDIS_AVAILABLE', 'aioredis', 'CacheKeyGenerator', 'ValidationResult', 'CacheParameterMapper', 'RedisCacheSecurityManager', 'SecurityConfig', 'SecurityValidationResult', 'create_security_config_from_env', 'InMemoryCache', 'CachePerformanceMonitor', 'PerformanceMetric', 'CompressionMetric', 'MemoryUsageMetric', 'InvalidationMetric', 'CacheFactory', 'CacheConfig', 'AICacheConfig', 'CacheConfigBuilder', 'EnvironmentPresets', 'ConfigValidationResult', 'get_settings', 'get_cache_config', 'get_cache_service', 'get_web_cache_service', 'get_ai_cache_service', 'get_test_cache', 'get_test_redis_cache', 'get_fallback_cache_service', 'validate_cache_configuration', 'get_cache_service_conditional', 'cleanup_cache_registry', 'get_cache_health_status', 'CacheDependencyManager']
