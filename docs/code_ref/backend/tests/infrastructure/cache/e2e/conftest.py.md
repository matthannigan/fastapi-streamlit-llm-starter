---
sidebar_label: conftest
---

# Test fixtures for manual cache E2E tests.

  file_path: `backend/tests/infrastructure/cache/e2e/conftest.py`

This module provides fixtures for end-to-end cache testing that require
a live server and real API authentication.

## client()

```python
async def client(cache_preset_app):
```

Async HTTP client for cache E2E tests with rate limiting disabled.

Provides:
    AsyncClient configured with ASGI transport for FastAPI app testing
    with rate limiting middleware disabled for E2E testing
    
Use Cases:
    - Testing cache API endpoints with FastAPI app
    - Validating authentication and authorization workflows
    - End-to-end cache operation validation
    
Cleanup:
    Client connection is automatically closed after test completion

## authenticated_client()

```python
async def authenticated_client(cache_preset_app):
```

Async HTTP client pre-configured with valid authentication headers and rate limiting disabled.

Authentication:
    Uses API_KEY environment variable or test default
    Headers include Authorization: Bearer <token> for HTTPBearer security
    
Use Cases:
    - Testing protected cache management endpoints
    - Validating authenticated cache operations
    - Monitoring and metrics endpoint testing
    
Cleanup:
    Client connection is automatically closed after test completion

## cleanup_test_cache()

```python
async def cleanup_test_cache(authenticated_client):
```

Automatic cleanup of test cache entries before and after tests.

Cleanup Strategy:
    - Pre-test: Clean any existing e2e_test:* patterns
    - Post-test: Clean all patterns created during test execution
    
Business Impact:
    Ensures test isolation and prevents test interference,
    maintaining reliable and repeatable test execution
    
Cleanup Patterns:
    - e2e_test:*               (all E2E test patterns)
    - e2e_test:monitoring_workflow:*   (monitoring test patterns)
    - e2e_test:auth_check:*    (authentication test patterns)
    - e2e_test:preset_behavior:*       (preset behavior test patterns)

## cache_preset_app()

```python
def cache_preset_app(monkeypatch):
```

Factory for creating app instances with specific cache presets.

Usage:
    app_with_preset = cache_preset_app("ai-production")
    
Supported Presets:
    - disabled: No caching functionality
    - simple: Memory cache with moderate TTLs
    - development: Memory + Redis fallback for testing
    - production: Redis-first with memory fallback
    - ai-development: AI-optimized development settings
    - ai-production: AI-optimized production settings
    
Implementation:
    Uses monkeypatch to set CACHE_PRESET environment variable for proper isolation
    Returns fresh app instance with specified configuration

## client_with_preset()

```python
def client_with_preset(cache_preset_app):
```

Async HTTP client factory for testing different cache presets.

Usage:
    async with client_with_preset("ai-production") as client:
        response = await client.get("/internal/cache/status")
        
Configuration:
    Each client instance uses a fresh app with specified preset
    Environment isolation prevents test interference
    
Use Cases:
    - Testing preset-driven configuration behavior
    - Validating cache status across different environments
    - End-to-end configuration validation

## api_key_scenarios()

```python
def api_key_scenarios():
```

Test scenarios for API key authentication validation.

Scenarios:
    - missing: No API key provided (should return 401)
    - invalid: Invalid API key format (should return 401)
    - wrong: Wrong but valid format API key (should return 401)
    - valid: Correct API key from environment (should return 200)
    
Use Cases:
    - Parametrized authentication testing
    - Security validation across endpoints
    - Authorization boundary testing

## cache_preset_scenarios()

```python
def cache_preset_scenarios():
```

Test scenarios for cache preset behavior validation.

Scenarios:
    Each tuple contains (preset_name, expected_redis_status, expected_memory_status)
    
Expected Behaviors:
    - ai-production: Redis connected, memory active
    - disabled: Redis disconnected, memory disabled
    - development: Redis connected (with fallback), memory active
    - simple: Redis disconnected, memory active
    
Use Cases:
    - Parametrized preset behavior testing
    - Configuration validation across environments
    - End-to-end cache status verification
