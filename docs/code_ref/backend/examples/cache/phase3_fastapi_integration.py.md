---
sidebar_label: phase3_fastapi_integration
---

# Example FastAPI Application Integration with Phase 4 Preset-Based Cache Configuration

  file_path: `backend/examples/cache/phase3_fastapi_integration.py`

This example demonstrates how to integrate Phase 4 preset-based cache configuration
with FastAPI applications, showcasing the simplified approach that reduces 28+
environment variables to 1-4 variables.

🚀 NEW in Phase 4: Preset-Based Configuration
    OLD WAY (28+ environment variables):
        CACHE_DEFAULT_TTL=1800, CACHE_MEMORY_CACHE_SIZE=200, CACHE_COMPRESSION_THRESHOLD=2000, ...
    
    NEW WAY (1-4 environment variables):
        CACHE_PRESET=development
        CACHE_REDIS_URL=redis://localhost:6379  # Override if needed
        ENABLE_AI_CACHE=true                     # Feature toggle

Features Demonstrated:
    - Preset-based cache configuration (Phase 4 enhancement)
    - FastAPI dependency injection with cache services
    - Cache lifecycle management (startup/shutdown)
    - Health check endpoints with cache status
    - Explicit cache factory usage with preset loading
    - Configuration-based cache setup via presets
    - Cache monitoring and status endpoints
    - Graceful degradation patterns

Environment Setup:
    # Simplified configuration using presets
    export CACHE_PRESET=development              # Choose: disabled, minimal, simple, development, production, ai-development, ai-production
    export CACHE_REDIS_URL=redis://localhost:6379   # Essential override
    export ENABLE_AI_CACHE=true                  # AI features toggle

Usage:
    python backend/examples/cache/phase3_fastapi_integration.py
    
    # Then visit:
    # http://localhost:8080/docs - API documentation
    # http://localhost:8080/health - Health check
    # http://localhost:8080/cache/status - Cache status
    # http://localhost:8080/cache/test - Test cache operations

## CacheTestRequest

## CacheTestResponse

## HealthResponse

## CacheStatusResponse

## lifespan()

```python
async def lifespan(app: FastAPI):
```

FastAPI lifespan handler demonstrating cache initialization and cleanup

## get_demo_cache()

```python
async def get_demo_cache(cache_type: str = 'web') -> CacheInterface:
```

Get a demo cache instance by type

## root()

```python
async def root():
```

Root endpoint with API information

## health_check()

```python
async def health_check():
```

Comprehensive health check including cache status

Demonstrates integration with Phase 3 health monitoring

## cache_status()

```python
async def cache_status():
```

Detailed cache status information

Shows configuration and performance stats for each cache type

## test_cache_operations()

```python
async def test_cache_operations(request: CacheTestRequest, cache_type: str = 'web', cache: CacheInterface = Depends(get_demo_cache)):
```

Test cache operations with a specific cache type

Demonstrates basic cache operations with the Phase 3 infrastructure

## clear_cache()

```python
async def clear_cache(cache_type: str = 'web', cache: CacheInterface = Depends(get_demo_cache)):
```

Clear all entries from a specific cache

## preset_info()

```python
async def preset_info():
```

Show current preset configuration and available presets

🚀 Phase 4 Feature: Demonstrates the preset-based configuration system

## dependency_demo()

```python
async def dependency_demo(web_cache: CacheInterface = Depends(get_web_cache_service), ai_cache: CacheInterface = Depends(get_ai_cache_service), main_cache: CacheInterface = Depends(get_cache_service)):
```

Demonstrate using the actual Phase 3 dependency injection system

This endpoint shows how to use the dependency functions in a real application

## main()

```python
def main():
```

Main function to run the example application
