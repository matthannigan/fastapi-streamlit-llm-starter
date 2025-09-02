---
sidebar_label: __init__
---

# **Comprehensive cache infrastructure with multiple implementations and monitoring.**

  file_path: `backend/app/infrastructure/cache/__init__.py`

This module serves as the central entry point for all cache-related functionality,
providing multiple cache implementations, configuration management, and comprehensive
monitoring capabilities for both web and AI applications.

## Directory Structure

The cache module is organized into specialized components:

- **Core Implementations**: `base.py`, `memory.py`, `redis_generic.py`, `redis_ai.py`
- **Configuration**: `config.py`, `ai_config.py`, `cache_presets.py`, `dependencies.py`
- **Utilities**: `factory.py`, `key_generator.py`, `parameter_mapping.py`
- **Advanced Features**: `monitoring.py`, `security.py`, `migration.py`
- **Benchmarking**: `benchmarks/` subdirectory with performance testing tools

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
