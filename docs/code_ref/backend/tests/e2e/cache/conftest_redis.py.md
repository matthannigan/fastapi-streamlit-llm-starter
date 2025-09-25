---
sidebar_label: conftest_redis
---

# Enhanced E2E test fixtures with Testcontainers Redis support.

  file_path: `backend/tests/e2e/cache/conftest_redis.py`

This module provides fixtures for end-to-end cache testing with real Redis instances,
enabling comprehensive testing of Redis-specific features and behaviors.

## redis_container()

```python
def redis_container():
```

Session-scoped Redis container for e2e tests.

Provides a real Redis instance for testing Redis-specific behaviors
like pattern matching, TTL, persistence, and connection management.

Benefits:
    - Real Redis connectivity testing
    - Accurate pattern invalidation testing  
    - Performance metrics with actual Redis operations
    - Security feature testing (AUTH, TLS if configured)
    
Usage:
    Test functions can access redis connection details to configure
    cache instances with real Redis backends instead of InMemoryCache fallback.

## redis_config()

```python
def redis_config(redis_container):
```

Redis connection configuration from Testcontainers instance.

Returns:
    dict: Redis connection parameters for cache configuration

## enhanced_cache_preset_app()

```python
def enhanced_cache_preset_app(monkeypatch, redis_config):
```

Enhanced cache preset app factory with real Redis connectivity.

This fixture creates app instances that use real Redis instead of falling back
to InMemoryCache, enabling comprehensive testing of Redis-specific behaviors.

Usage:
    app_with_preset = enhanced_cache_preset_app("ai-production")
    # App will have real Redis connection and show "connected" status
    
Benefits:
    - Tests actual Redis connectivity and status
    - Validates Redis-specific cache operations
    - Enables realistic preset behavior testing
    - Provides real performance metrics and monitoring data

## enhanced_client_with_preset()

```python
def enhanced_client_with_preset(enhanced_cache_preset_app):
```

Enhanced async HTTP client factory with real Redis connectivity.

Usage:
    async with enhanced_client_with_preset("ai-production") as client:
        response = await client.get("/internal/cache/status")
        # Response will show "connected" Redis status
        
Use Cases:
    - Testing preset-driven behavior with real Redis
    - Validating cache invalidation patterns with Redis SCAN/DEL
    - Performance monitoring with actual Redis metrics
    - Security testing with Redis AUTH/TLS features

## redis_preset_scenarios()

```python
def redis_preset_scenarios():
```

Enhanced test scenarios for Redis-enabled cache preset behavior validation.

These scenarios reflect realistic expectations when Redis is available,
enabling proper validation of production-like preset behavior.

Scenarios:
    - ai-production, development: Should show Redis "connected"
    - minimal, disabled: Should show Redis "disconnected" (intentional)
