---
sidebar_label: dependencies
---

# FastAPI Dependency Integration with Lifecycle Management

  file_path: `backend/app/infrastructure/cache/dependencies.py`

This module provides comprehensive FastAPI dependency injection for cache services
with lifecycle management, thread-safe registry, and health monitoring. It implements
explicit cache creation patterns using CacheFactory methods and supports graceful
degradation with fallback to InMemoryCache.

## Classes

CacheDependencyManager: Core dependency manager for cache lifecycle and registry

## Functions

get_settings: Cached settings dependency for configuration access
get_cache_config: Configuration builder with environment detection
get_cache_service: Main cache service dependency with registry management
get_web_cache_service: Web-optimized cache service dependency
get_ai_cache_service: AI-optimized cache service dependency
get_test_cache: Testing cache dependency with memory fallback
get_test_redis_cache: Redis testing cache for integration tests
get_fallback_cache_service: Always returns InMemoryCache for degraded mode
validate_cache_configuration: Configuration validation dependency
get_cache_service_conditional: Conditional cache selection based on parameters
cleanup_cache_registry: Lifecycle cleanup for cache registry
get_cache_health_status: Comprehensive health check dependency

## Key Features

- **Thread-Safe Registry**: Weak reference cache registry with asyncio.Lock
- **Explicit Factory Usage**: Uses CacheFactory.create_cache_from_config() for deterministic creation
- **Graceful Degradation**: Automatic fallback to InMemoryCache on Redis failures
- **Lifecycle Management**: Proper cache connection and cleanup handling
- **Health Monitoring**: Comprehensive health checks with ping() method support
- **Configuration Building**: Environment-aware configuration from settings
- **Test Integration**: Specialized dependencies for testing scenarios
- **Async Safety**: Full async/await patterns with proper error handling

## Architecture

This module integrates with:
- CacheFactory for explicit cache creation
- CacheConfig and CacheConfigBuilder for configuration management
- FastAPI dependency injection system for request-scoped cache access
- Application settings for environment-specific configuration
- Custom exception hierarchy for structured error handling

## Examples

Basic cache dependency usage:
@app.get("/api/data")
async def get_data(cache: CacheInterface = Depends(get_cache_service)):
cached_data = await cache.get("api_data")
if cached_data:
return cached_data

# Fetch fresh data
fresh_data = fetch_api_data()
await cache.set("api_data", fresh_data, ttl=300)
return fresh_data

AI cache dependency usage:
@app.post("/api/ai/summarize")
async def summarize_text(
request: SummarizeRequest,
ai_cache: CacheInterface = Depends(get_ai_cache_service)
):
# AI cache automatically handles operation-specific TTLs and text hashing
cached_result = await ai_cache.cache_response(
text=request.text,
operation="summarize",
options=request.options,
response=None  # Will check cache first
)
return cached_result

Health check integration:
@app.get("/health/cache")
async def cache_health(
health_status: dict = Depends(get_cache_health_status)
):
return health_status

## Performance Considerations

- Cache registry uses weak references to prevent memory leaks
- Connection establishment is async and non-blocking
- Fallback operations are near-instantaneous (<1ms)
- Health checks prefer lightweight ping() over full operations
- Registry cleanup removes dead references efficiently

## Error Handling

- ConfigurationError: Configuration building or validation failures
- InfrastructureError: Cache connection or infrastructure issues
- ValidationError: Invalid configuration parameters
- All errors include context data for debugging and monitoring

## Dependencies

### Required

- app.infrastructure.cache.factory.CacheFactory: Explicit cache creation
- app.infrastructure.cache.config.CacheConfig: Configuration management
- app.infrastructure.cache.base.CacheInterface: Cache interface contract
- app.core.config.Settings: Application settings access
- app.core.exceptions: Custom exception hierarchy
- fastapi.Depends: Dependency injection framework

### Optional

- redis.asyncio: Redis connectivity for health checks
- app.infrastructure.cache.monitoring: Performance monitoring
