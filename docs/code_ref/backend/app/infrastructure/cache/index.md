---
sidebar_label: cache
---

# Cache Infrastructure

Comprehensive caching infrastructure for FastAPI applications with multiple implementations, preset-based configuration, and advanced monitoring. Supports both web applications and AI workloads with intelligent optimization.

## Quick Start

```python
# 1. Set environment preset
export CACHE_PRESET=development  # or production, ai-production

# 2. Use in FastAPI application
from app.infrastructure.cache.dependencies import get_cache_service
from fastapi import Depends

@app.post("/api/process")
async def process_data(
    request: ProcessRequest,
    cache: CacheInterface = Depends(get_cache_service)
):
    cached_result = await cache.get(f"process:{request.id}")
    if cached_result:
        return cached_result
    
    result = await process_service.execute(request)
    await cache.set(f"process:{request.id}", result, ttl=3600)
    return result
```

## Architecture Overview

### Cache Interface

All implementations follow the `CacheInterface` contract for seamless polymorphic usage:

```python
# Standard interface - works with any implementation
await cache.set(key: str, value: Any, ttl: Optional[int])
result = await cache.get(key: str) -> Any | None
await cache.delete(key: str)
```

### Implementation Comparison

| Feature | InMemoryCache | GenericRedisCache | AIResponseCache |
|---------|---------------|-------------------|-----------------|
| **Best For** | Development, Testing | Web Applications | AI Workloads |
| **Persistence** | None | Redis | Redis |
| **L1 Cache** | N/A | Memory | Memory |
| **Compression** | No | Configurable | Intelligent |
| **Key Generation** | Simple | Standard | AI-Optimized |
| **TTL Strategy** | Fixed | Flexible | Operation-Specific |
| **Monitoring** | Basic | Advanced | Comprehensive |

## Implementation Guide

### InMemoryCache

**When to Use**: Development, testing, lightweight applications

```python
from app.infrastructure.cache import InMemoryCache

cache = InMemoryCache(
    default_ttl=3600,    # 1 hour default
    max_size=1000        # LRU eviction at 1000 entries
)

# Basic usage
await cache.set("user:123", {"name": "John"})
user = await cache.get("user:123")

# Statistics
stats = cache.get_stats()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
```

**Features**:
- Sub-millisecond response times
- TTL with automatic cleanup
- LRU eviction for memory management
- Built-in statistics and monitoring
- No external dependencies

### GenericRedisCache

**When to Use**: Web applications, shared cache across instances

```python
from app.infrastructure.cache import GenericRedisCache

cache = GenericRedisCache(
    redis_url="redis://localhost:6379",
    default_ttl=7200,
    memory_cache_size=500,    # L1 cache size
    compression_threshold=1024  # Compress > 1KB
)

await cache.connect()

# Two-tier caching (L1 memory + L2 Redis)
await cache.set("session:abc", session_data)
data = await cache.get("session:abc")  # Served from L1 if available
```

**Features**:
- L1 memory cache + L2 Redis persistence
- Intelligent compression with monitoring
- Graceful degradation (memory-only fallback)
- Connection pooling and retry logic
- Performance monitoring and analytics

### AIResponseCache

**When to Use**: AI applications, text processing, response caching

```python
from app.infrastructure.cache import AIResponseCache

cache = AIResponseCache(
    redis_url="redis://production:6379",
    text_hash_threshold=1000,        # Hash texts > 1000 chars
    operation_ttls={                 # Operation-specific TTLs
        "summarize": 7200,           # 2 hours
        "sentiment": 86400,          # 24 hours
        "qa": 1800                   # 30 minutes
    }
)

await cache.connect()

# Intelligent key generation for AI operations
key = cache.build_key(
    text="Long document to analyze...",
    operation="summarize",
    options={"max_length": 200}
)

await cache.set(key, ai_response, ttl=7200)
```

**Features**:
- Intelligent key generation with text hashing
- Operation-specific TTL management
- Text size tier optimization
- AI-specific monitoring metrics
- Advanced compression for large responses

## Configuration

### Preset System

**Single Environment Variable**: `CACHE_PRESET` replaces 28+ individual configuration variables.

```bash
# Choose one preset:
export CACHE_PRESET=development     # Local development
export CACHE_PRESET=production      # Web applications  
export CACHE_PRESET=ai-production   # AI workloads

# Optional overrides:
export CACHE_REDIS_URL=redis://custom-server:6379
export ENABLE_AI_CACHE=true
export CACHE_CUSTOM_CONFIG='{"compression_level": 9}'
```

### Available Presets

| Preset | Implementation | Use Case | TTL | Features |
|--------|---------------|----------|-----|----------|
| `disabled` | InMemoryCache | Minimal overhead | 5min | Cache disabled |
| `minimal` | InMemoryCache | Resource-constrained | 15min | Basic caching |
| `development` | InMemoryCache | Local development | 30min | Debug-friendly |
| `production` | GenericRedisCache | Web applications | 2hr | High performance |
| `ai-development` | AIResponseCache | AI development | 30min | AI features, debug |
| `ai-production` | AIResponseCache | AI production | 4hr | Full AI optimization |

### Custom Configuration

For advanced scenarios, use the configuration builder:

```python
from app.infrastructure.cache import CacheConfigBuilder

config = (CacheConfigBuilder()
    .for_environment("production")
    .with_redis("redis://prod-cluster:6379")
    .with_ai_features(text_hash_threshold=2000)
    .with_compression(threshold=500, level=6)
    .build())

cache = CacheFactory.create_cache_from_config(config)
```

## FastAPI Integration

### Dependency Injection

```python
from app.infrastructure.cache.dependencies import (
    get_cache_service,      # Auto-configured from CACHE_PRESET
    get_cache_config,       # Configuration object
    get_cache_health_status # Health monitoring
)

# Main cache dependency
@app.post("/api/data")
async def process_data(
    cache: CacheInterface = Depends(get_cache_service)
):
    # Cache automatically configured from environment preset
    pass

# Health check endpoint
@app.get("/health/cache")
async def cache_health():
    return await get_cache_health_status()

# Configuration info
@app.get("/internal/cache/config")
async def cache_config(config = Depends(get_cache_config)):
    return {
        "preset": config.preset_name,
        "implementation": type(cache).__name__,
        "redis_url": config.redis_url
    }
```

### Lifecycle Management

Dependencies handle connection lifecycle automatically:

- **Startup**: Cache connects during first dependency injection
- **Shutdown**: Connections cleaned up via weak reference registry
- **Health**: Automatic health monitoring with Redis ping checks
- **Fallback**: Graceful degradation on Redis connection failures

## Advanced Features

### Performance Monitoring

```python
from app.infrastructure.cache import CachePerformanceMonitor

# Built-in monitoring for all cache implementations
monitor = cache.performance_monitor

# Get real-time statistics
stats = await monitor.get_performance_summary()
print(f"Hit ratio: {stats['hit_ratio']:.2%}")
print(f"Average response time: {stats['avg_response_time']:.2f}ms")

# Memory usage tracking
memory_stats = monitor.get_memory_usage_stats()
if memory_stats['usage_mb'] > memory_stats['warning_threshold_mb']:
    logger.warning("Cache memory usage high")

# Export metrics for external monitoring
metrics_data = monitor.export_metrics()
```

### Security Features

```python
from app.infrastructure.cache.security import SecurityConfig

# TLS and authentication for production
security_config = SecurityConfig(
    use_tls=True,
    username="cache_user",
    password="secure_password",
    cert_file="/path/to/cert.pem"
)

cache = GenericRedisCache(
    redis_url="rediss://secure-redis:6380",  # Note: rediss://
    security_config=security_config
)
```

## Integration Patterns

### Domain Service Pattern (Recommended)

Keep cache logic in domain services, not controllers:

```python
# ✅ Good: Domain service handles cache logic
class TextProcessorService:
    def __init__(self, cache: CacheInterface):
        self.cache = cache
    
    async def process_text(self, text: str, operation: str) -> dict:
        # Service builds cache keys with domain knowledge
        cache_key = f"text_process:{operation}:{hash(text)}"
        
        cached = await self.cache.get(cache_key)
        if cached:
            return cached
        
        result = await self._process(text, operation)
        
        # Domain-specific TTL logic
        ttl = self._get_ttl_for_operation(operation)
        await self.cache.set(cache_key, result, ttl=ttl)
        
        return result

# FastAPI controller just uses the service
@app.post("/process")
async def process_text(
    request: ProcessRequest,
    cache: CacheInterface = Depends(get_cache_service)
):
    service = TextProcessorService(cache)
    return await service.process_text(request.text, request.operation)
```

### Testing Patterns

```python
import pytest
from app.infrastructure.cache.dependencies import get_test_cache

@pytest.fixture
async def test_cache():
    cache = get_test_cache()
    yield cache
    # Automatic cleanup handled by test cache

async def test_caching_behavior(test_cache):
    # Test with real cache behavior
    await test_cache.set("test_key", {"data": "value"})
    result = await test_cache.get("test_key")
    assert result == {"data": "value"}
```

## Documentation Links

For detailed user documentation:

- **[Configuration Guide](../../../docs/guides/infrastructure/cache/configuration.md)** - Comprehensive configuration options
- **[Usage Guide](../../../docs/guides/infrastructure/cache/usage-guide.md)** - User-focused usage patterns  
- **[API Reference](../../../docs/guides/infrastructure/cache/api-reference.md)** - Complete API documentation
- **[Migration Guide](../../../docs/guides/infrastructure/cache/migration.md)** - Detailed migration instructions
- **[Benchmarking](../../../docs/guides/infrastructure/cache/benchmarking.md)** - Performance testing and optimization
- **[Testing Guide](../../../docs/guides/infrastructure/cache/testing.md)** - Testing strategies and patterns
- **[Troubleshooting](../../../docs/guides/infrastructure/cache/troubleshooting.md)** - Common issues and solutions

## Performance Characteristics

| Operation | InMemoryCache | GenericRedisCache | AIResponseCache |
|-----------|---------------|-------------------|-----------------|
| **Get** (hit) | <1ms | ~2-5ms (L1: <1ms) | ~2-5ms (L1: <1ms) |
| **Set** | <1ms | ~3-8ms | ~5-15ms (with compression) |
| **Memory** | ~200 bytes/entry | ~300 bytes/entry + Redis | Variable with compression |
| **Startup** | Instant | Redis connection time | Redis connection time |
| **Throughput** | 10K+ ops/sec | 1-5K ops/sec | 500-2K ops/sec |

## Error Handling

All implementations provide graceful error handling:

- **Connection Failures**: Automatic fallback to memory-only mode
- **Serialization Errors**: Logged warnings, operations continue
- **Memory Pressure**: Automatic LRU eviction and cleanup
- **Redis Unavailable**: Seamless degradation with health monitoring

Choose the right implementation for your use case, configure with presets for simplicity, and leverage the comprehensive monitoring for production optimization.