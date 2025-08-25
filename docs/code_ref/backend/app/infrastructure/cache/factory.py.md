---
sidebar_label: factory
---

# [REFACTORED] Cache Factory for Explicit Cache Instantiation

  file_path: `backend/app/infrastructure/cache/factory.py`

This module provides a comprehensive factory system for creating cache instances
with explicit configuration and deterministic behavior. It replaces auto-detection
patterns with explicit factory methods that provide clear, predictable cache
instantiation for different use cases.

## Classes

CacheFactory: Main factory class providing explicit cache creation methods
for web applications, AI applications, testing environments,
and configuration-based instantiation.

## Key Features

- **Explicit Cache Creation**: Clear, deterministic factory methods for specific use cases
- **Environment-Optimized Defaults**: Pre-configured settings for web apps, AI apps, and testing
- **Configuration-Based Creation**: Flexible cache creation from configuration objects
- **Graceful Fallback**: Automatic fallback to InMemoryCache when Redis unavailable
- **Comprehensive Validation**: Input validation with detailed error messages
- **Error Handling**: Robust error handling with contextual information
- **Type Safety**: Full type annotations for IDE support and static analysis

## Factory Methods

- for_web_app(): Optimized cache for web applications with balanced performance
- for_ai_app(): Specialized cache for AI applications with larger storage and compression
- for_testing(): Testing-optimized cache with short TTLs and Redis test databases
- create_cache_from_config(): Flexible configuration-based cache creation

## Example Usage

Basic web application cache:
```python
factory = CacheFactory()
cache = await factory.for_web_app(redis_url="redis://localhost:6379")
await cache.set("session:123", {"user_id": 456})
```
AI application cache with custom settings:
```python
cache = await factory.for_ai_app(
    redis_url="redis://ai-cache:6379",
    default_ttl=7200,
    enable_compression=True
)
```
Testing cache with memory fallback:
```python
cache = await factory.for_testing(
    redis_url="redis://test:6379",
    fail_on_connection_error=False
)
```
Configuration-based cache creation:
```python
config = {
    "redis_url": "redis://production:6379",
    "default_ttl": 3600,
    "enable_l1_cache": True,
    "compression_threshold": 2000
}
cache = await factory.create_cache_from_config(config)
```

## Architecture Context

This factory is part of Phase 3 of the cache refactoring project, providing
explicit cache instantiation to replace auto-detection patterns. It enables
deterministic cache behavior while maintaining backward compatibility and
providing optimized defaults for different application types.

## Performance Considerations

- Factory methods execute in <10ms for typical configurations
- Redis connection validation adds 5-50ms depending on network latency
- Fallback to InMemoryCache is instantaneous (<1ms)
- All factory methods are async to support connection validation

## Error Handling

- ConfigurationError: Invalid parameters or configuration conflicts
- ValidationError: Input validation failures with specific field information
- InfrastructureError: Redis connection or infrastructure issues
- All errors include context data for debugging and monitoring

## Dependencies

### Required

- app.infrastructure.cache.base.CacheInterface: Cache interface contract
- app.infrastructure.cache.redis_generic.GenericRedisCache: Generic Redis cache
- app.infrastructure.cache.redis_ai.AIResponseCache: AI-specialized cache
- app.infrastructure.cache.memory.InMemoryCache: Memory fallback cache
- app.core.exceptions: Custom exception hierarchy

### Optional

- redis.asyncio: Redis connectivity (graceful degradation if unavailable)
- app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking
