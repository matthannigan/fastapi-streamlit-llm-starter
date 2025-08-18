---
sidebar_label: redis_ai
---

# [REFACTORED] AI Response Cache Implementation with Generic Redis Cache Inheritance

  file_path: `backend/app/infrastructure/cache/redis_ai.py`

This module provides the refactored AIResponseCache that properly inherits from
GenericRedisCache while maintaining all AI-specific features and backward compatibility.

## Classes

AIResponseCache: Refactored AI cache implementation that extends GenericRedisCache
with AI-specific functionality including intelligent key generation,
operation-specific TTLs, and comprehensive AI metrics collection.

## Key Features

- **Clean Inheritance**: Proper inheritance from GenericRedisCache for core functionality
- **Parameter Mapping**: Uses CacheParameterMapper for clean parameter separation
- **AI-Specific Features**: Maintains all original AI functionality including:
- Intelligent cache key generation with text hashing
- Operation-specific TTLs and text size tiers
- Comprehensive AI metrics and performance monitoring
- Graceful degradation and pattern-based invalidation
- **Backward Compatibility**: Maintains existing API contracts and functionality

## Architecture

This refactored implementation follows the inheritance pattern where:
- GenericRedisCache provides core Redis functionality (L1 cache, compression, monitoring)
- AIResponseCache adds AI-specific features and customizations
- CacheParameterMapper handles parameter separation and validation
- AI-specific callbacks integrate with the generic cache event system

## Usage Examples

Basic Usage (maintains backward compatibility):
```python
cache = AIResponseCache(redis_url="redis://localhost:6379")
await cache.connect()

# Cache an AI response
await cache.cache_response(
    text="Long document to summarize...",
    operation="summarize",
    options={"max_length": 100},
    response={"summary": "Brief summary", "confidence": 0.95}
)
```

### Advanced Configuration

```python
cache = AIResponseCache(
    redis_url="redis://production:6379",
    default_ttl=7200,
    text_hash_threshold=500,
    memory_cache_size=200,
    text_size_tiers={
        'small': 300,
        'medium': 3000,
        'large': 30000
    }
)
```

## Dependencies

### Required

- app.infrastructure.cache.redis_generic.GenericRedisCache: Parent cache class
- app.infrastructure.cache.parameter_mapping.CacheParameterMapper: Parameter handling
- app.infrastructure.cache.key_generator.CacheKeyGenerator: AI key generation
- app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking
- app.core.exceptions: Custom exception handling

## Performance Considerations

- Inherits efficient L1 memory cache and compression from GenericRedisCache
- AI-specific callbacks add minimal overhead (<1ms per operation)
- Key generation optimized for large texts with streaming hashing
- Metrics collection designed for minimal performance impact

## Error Handling

- Uses custom exceptions following established patterns
- Graceful degradation when Redis unavailable
- Comprehensive logging with proper context
- All Redis operations wrapped with error handling
