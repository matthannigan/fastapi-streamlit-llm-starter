---
sidebar_label: conftest
---

# Test fixtures for cache integration tests.

  file_path: `backend/tests/integration/cache/conftest.py`

This module provides reusable fixtures for cache integration testing,
focusing on cross-component behavior and service interactions.

Fixtures are imported from the main cache conftest.py to maintain consistency
and avoid duplication while enabling integration test isolation.

## test_settings()

```python
def test_settings():
```

Real Settings instance with test configuration for testing actual configuration behavior.

Provides a Settings instance loaded from test configuration, enabling tests
to verify actual configuration loading, validation, and environment detection
instead of using hardcoded mock values.

This fixture represents behavior-driven testing where we test the actual
Settings class functionality rather than mocking its behavior.

## development_settings()

```python
def development_settings():
```

Real Settings instance configured for development environment testing.

Provides Settings with development preset for testing development-specific behavior.

## production_settings()

```python
def production_settings():
```

Real Settings instance configured for production environment testing.

Provides Settings with production preset for testing production-specific behavior.

## real_cache_factory()

```python
async def real_cache_factory():
```

Real CacheFactory instance for testing factory behavior.

Provides an actual CacheFactory instance to test real factory logic,
parameter mapping, and cache creation behavior rather than mocking
the factory's internal operations.

This enables behavior-driven testing of the factory's actual logic.

## factory_memory_cache()

```python
async def factory_memory_cache(real_cache_factory):
```

Cache created via real factory using memory cache for testing.

Creates a cache through the real factory using memory cache option,
enabling testing of factory integration while avoiding Redis dependencies.

## factory_web_cache()

```python
async def factory_web_cache(real_cache_factory):
```

Cache created via real factory for web application testing.

Creates a cache through the real factory for web application use case,
with graceful fallback to memory cache if Redis is unavailable.

## factory_ai_cache()

```python
async def factory_ai_cache(real_cache_factory):
```

Cache created via real factory for AI application testing.

Creates a cache through the real factory for AI application use case,
with graceful fallback to memory cache if Redis is unavailable.

## sample_cache_key()

```python
def sample_cache_key():
```

Standard cache key for basic testing scenarios.

Provides a typical cache key string used across multiple test scenarios
for consistency in testing cache interfaces.

## sample_cache_value()

```python
def sample_cache_value():
```

Standard cache value for basic testing scenarios.

Provides a typical cache value (dictionary) that represents common
data structures cached in production applications.

## sample_ttl()

```python
def sample_ttl():
```

Standard TTL value for testing time-to-live functionality.

Provides a reasonable TTL value (in seconds) for testing
cache expiration behavior.

## default_memory_cache()

```python
def default_memory_cache():
```

InMemoryCache instance with default configuration for standard testing.

Provides a fresh InMemoryCache instance with default settings
suitable for most test scenarios. This represents the 'happy path'
configuration that should work reliably.

Configuration:
    - default_ttl: 3600 seconds (1 hour)
    - max_size: 1000 entries
