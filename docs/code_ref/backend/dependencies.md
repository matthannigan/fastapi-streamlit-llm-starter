# FastAPI Dependency Providers Module.

This module provides dependency injection functions for FastAPI endpoints,
offering centralized access to core application services and configuration.

## Dependencies Provided

get_settings(): Cached application settings provider that returns a singleton
Settings instance for consistent configuration access across the application.

get_fresh_settings(): Uncached settings provider that creates fresh Settings
instances on each call. Primarily used for testing scenarios where
configuration overrides or isolated instances are needed.

get_cache_service(): Async AI response cache service provider that creates
and configures an AIResponseCache instance with Redis connectivity.
Includes graceful degradation to in-memory-only operation when Redis
is unavailable.

## Usage

These dependency providers are designed to be used with FastAPI's dependency
injection system through the Depends() function:

```python
@app.get("/endpoint")
async def endpoint(
settings: Settings = Depends(get_settings),
cache: AIResponseCache = Depends(get_cache_service)
):
# Use injected dependencies
pass
```

## Notes

- get_settings() uses functools.lru_cache for performance optimization
- get_cache_service() handles Redis connection failures gracefully
- All providers follow FastAPI's dependency injection patterns
