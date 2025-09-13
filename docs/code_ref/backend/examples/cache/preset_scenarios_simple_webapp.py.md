---
sidebar_label: preset_scenarios_simple_webapp
---

# Simple Web Application Cache Example with Presets

  file_path: `backend/examples/cache/preset_scenarios_simple_webapp.py`

This example demonstrates how to use cache presets for a simple web application.
Shows the 'simple' and 'development' presets with basic caching patterns.

Environment Setup:
    # For development/testing
    export CACHE_PRESET=development
    
    # For small production deployment
    export CACHE_PRESET=simple
    export CACHE_REDIS_URL=redis://production:6379

Usage:
    python backend/examples/cache/preset_scenarios_simple_webapp.py
    curl http://localhost:8081/user/123
    curl http://localhost:8081/cache/info

## User

## CacheInfo

## lifespan()

```python
async def lifespan(app: FastAPI):
```

Application lifespan with cache initialization

## get_cache()

```python
async def get_cache() -> CacheInterface:
```

Get cache instance from app state

## root()

```python
async def root():
```

Root endpoint

## get_user()

```python
async def get_user(user_id: int):
```

Get user by ID with caching

Demonstrates basic cache usage patterns:
- Cache hit: Return cached data instantly
- Cache miss: Fetch from database, cache result

## get_active_users()

```python
async def get_active_users():
```

Get list of recently active users with caching

Demonstrates caching complex queries

## cache_info()

```python
async def cache_info():
```

Get cache information and statistics

Shows current preset configuration and performance

## clear_cache()

```python
async def clear_cache():
```

Clear all cache entries

## health_check()

```python
async def health_check():
```

Health check with cache status

## main()

```python
def main():
```

Run the simple web app example
