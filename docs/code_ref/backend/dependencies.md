# FastAPI Dependency Providers Module.

This module provides centralized dependency injection functions for FastAPI endpoints,
implementing the Dependency Injection pattern to manage application services and
configuration access. It serves as the integration layer between FastAPI's DI system
and the application's infrastructure services.

## Architecture

The module follows FastAPI's dependency injection patterns to provide:
- **Singleton Configuration**: Cached settings for consistent application configuration
- **Service Lifecycle Management**: Proper initialization and error handling for services
- **Graceful Degradation**: Fallback mechanisms when external dependencies fail
- **Testing Support**: Alternative providers for testing scenarios

## Dependencies Provided

### Configuration Dependencies

#### `get_settings()`
**Cached application settings provider** that returns a singleton Settings instance
for consistent configuration access across the application.

- **Caching**: Uses `@lru_cache()` decorator for performance optimization
- **Consistency**: Ensures the same configuration throughout request lifecycle
- **Thread-safe**: Safe for concurrent access in multi-threaded environments

#### `get_fresh_settings()`
**Uncached settings provider** that creates fresh Settings instances on each call.
Primarily designed for testing scenarios where configuration overrides or isolated
instances are needed.

- **Testing**: Allows environment variable overrides per test
- **Isolation**: Each call creates a completely independent Settings instance
- **Development**: Useful for configuration testing and validation

### Service Dependencies

#### `get_cache_service()`
**Async AI response cache service provider** that creates and configures an
AIResponseCache instance with comprehensive Redis connectivity and fallback mechanisms.

- **Redis Integration**: Attempts connection to Redis backend
- **Graceful Degradation**: Falls back to memory-only operation when Redis unavailable
- **Configuration Integration**: Automatically applies all cache-related settings
- **Error Handling**: Logs connection failures but continues operation
- **Performance Optimization**: Configures compression, TTL, and memory limits

## Usage Patterns

### Basic Dependency Injection
```python
from fastapi import FastAPI, Depends
from app.dependencies import get_settings, get_cache_service

app = FastAPI()

@app.get("/endpoint")
async def endpoint(
settings: Settings = Depends(get_settings),
cache: AIResponseCache = Depends(get_cache_service)
):
# Access configuration
if settings.debug:
logger.info("Debug mode enabled")

# Use cache service
cached_result = await cache.get_cached_response(text, operation, options)
return {"result": cached_result}
```

### Testing with Fresh Settings
```python
from app.dependencies import get_fresh_settings

@app.get("/test-endpoint")
async def test_endpoint(
settings: Settings = Depends(get_fresh_settings)
):
# Each test gets isolated settings
return {"env": settings.environment}
```

### Nested Dependencies
```python
# Dependencies can depend on other dependencies
async def get_ai_service(
settings: Settings = Depends(get_settings),
cache: AIResponseCache = Depends(get_cache_service)
) -> AIService:
return AIService(settings.gemini_api_key, cache)
```

## Configuration Integration

The cache service dependency automatically integrates with all cache-related settings:

- `redis_url`: Redis connection string with fallback to memory-only
- `cache_default_ttl`: Default time-to-live for cached responses
- `cache_text_hash_threshold`: Text size threshold for key hashing
- `cache_compression_threshold`: Response size threshold for compression
- `cache_compression_level`: Compression level (1-9, higher = better compression)
- `cache_text_size_tiers`: Text categorization for caching strategies
- `cache_memory_cache_size`: Maximum in-memory cache entries

## Error Handling & Resilience

### Cache Service Resilience
The `get_cache_service()` dependency implements comprehensive error handling:

1. **Connection Attempts**: Tries to connect to Redis during initialization
2. **Graceful Fallback**: On connection failure, logs warning and continues
3. **Memory-only Operation**: Cache operates without persistence when Redis unavailable
4. **No Request Failures**: Cache connection issues never cause request failures

### Logging Integration
All dependency providers include appropriate logging:
- **Warning Level**: Redis connection failures (operational issue, not error)
- **Debug Level**: Dependency creation and configuration details
- **Error Context**: Meaningful error messages for troubleshooting

## Performance Considerations

### Settings Caching
- **LRU Cache**: `get_settings()` uses `@lru_cache()` for O(1) access
- **Memory Efficiency**: Single Settings instance shared across all requests
- **No Re-parsing**: Environment variables parsed only once at startup

### Service Initialization
- **Async Initialization**: Cache service uses async initialization pattern
- **Connection Pooling**: Redis connections managed by aioreids internally
- **Resource Cleanup**: Proper lifecycle management for service dependencies

## Testing Integration

The module provides testing-friendly alternatives:

```python
# In tests, override with fresh settings
app.dependency_overrides[get_settings] = get_fresh_settings

# Or provide completely custom settings
def get_test_settings():
return Settings(debug=True, redis_url="redis://test:6379")

app.dependency_overrides[get_settings] = get_test_settings
```

## Dependencies

- `functools.lru_cache`: Settings caching mechanism
- `fastapi.Depends`: FastAPI dependency injection system
- `app.core.config.Settings`: Application configuration class
- `app.infrastructure.cache.AIResponseCache`: Cache service implementation
