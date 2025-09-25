---
sidebar_label: conftest
---

# Test fixtures shared across cache infrastructure unit tests.

  file_path: `backend/tests/unit/cache/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
that are commonly used across multiple cache module test suites.

Fixture Categories:
    - Mock dependency fixtures (settings, cache factory, cache interface, performance monitor, memory cache)
    - Custom exception fixtures
    - Basic test data fixtures (keys, values, TTL values, text samples)
    - AI-specific data fixtures (responses, operations, options)
    - Statistics fixtures (sample performance data)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateful mocks maintain internal state for realistic behavior

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

## real_performance_monitor()

```python
async def real_performance_monitor():
```

Real performance monitor instance for integration testing.

Provides an actual CachePerformanceMonitor instance to test real
monitoring behavior, metric accuracy, and integration patterns
rather than mocking monitoring operations.

## cache_implementations()

```python
def cache_implementations():
```

Real cache implementations for polymorphism testing.

Provides a list of actual cache implementations to test polymorphic
behavior and interface compliance across different cache types.

Uses real implementations rather than mocked interfaces to verify
actual polymorphic behavior and interface adherence.

## sample_empty_value()

```python
def sample_empty_value():
```

Empty cache value for testing edge cases.

Provides an empty dictionary value to test cache behavior
with empty data structures and edge case handling.

## sample_unicode_value()

```python
def sample_unicode_value():
```

Unicode cache value for testing international character support.

Provides a dictionary containing various Unicode characters,
emojis, and international text for testing proper encoding
and decoding of cached values.

## sample_null_value()

```python
def sample_null_value():
```

Null cache value for testing None handling.

Provides None value to test cache behavior with null values,
ensuring proper distinction between "key not found" and
"key exists but value is None".

## sample_whitespace_key()

```python
def sample_whitespace_key():
```

Cache key with whitespace for testing key validation.

Provides a key containing various whitespace characters
to test key normalization and validation logic.

## sample_large_key()

```python
def sample_large_key():
```

Large cache key for testing key length limits.

Provides a very long key to test cache behavior with
keys that might exceed typical length limits.

## shared_sample_texts()

```python
def shared_sample_texts():
```

Sample texts from shared module for consistent cross-component testing.

Provides access to standardized sample texts used across frontend
and backend components for consistent testing patterns.

## shared_unicode_text()

```python
def shared_unicode_text():
```

Unicode-rich text from shared data for international testing.

Combines shared sample data with additional Unicode content
for comprehensive international character testing.

## shared_empty_text()

```python
def shared_empty_text():
```

Empty text value for testing empty input handling.

Provides empty string to test how cache components handle
empty text inputs in AI processing contexts.

## shared_whitespace_text()

```python
def shared_whitespace_text():
```

Text containing only whitespace for edge case testing.

Provides whitespace-only string to test text normalization
and validation in cache key generation and AI processing.

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

## mock_path_exists()

```python
def mock_path_exists():
```

Fixture that mocks pathlib.Path.exists.

Uses autospec=True to ensure the mock's signature matches the real
method, which is crucial for using side_effect correctly. The default
return_value is True for "happy path" tests.

Note:
    This is a prime example of a **good mock** because it isolates the test 
    from an external system boundary—the filesystem. By mocking 
    `pathlib.Path.exists`, tests for `SecurityConfig` can run reliably and 
    quickly without requiring actual certificate files to be present on the 
    testing machine.

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

## short_ttl()

```python
def short_ttl():
```

Short TTL value for testing expiration scenarios.

Provides a very short TTL value useful for testing
cache expiration without long waits in tests.

## sample_text()

```python
def sample_text():
```

Sample text for AI cache testing.

Provides typical text content that would be processed by AI operations,
used across multiple test scenarios for consistency.

## sample_short_text()

```python
def sample_short_text():
```

Short sample text below hash threshold for testing text tier behavior.

## sample_long_text()

```python
def sample_long_text():
```

Long sample text above hash threshold for testing text hashing behavior.

## sample_ai_response()

```python
def sample_ai_response():
```

Sample AI response data for caching tests.

Represents typical AI processing results with various data types
to test serialization and caching behavior.

## sample_options()

```python
def sample_options():
```

Sample operation options for AI processing.

## ai_cache_test_data()

```python
def ai_cache_test_data():
```

Comprehensive test data set for AI cache operations.

Provides various combinations of texts, operations, options, and responses
for testing different scenarios described in the docstrings.

## cache_statistics_sample()

```python
def cache_statistics_sample():
```

Sample cache statistics data for testing statistics methods.

Provides realistic cache statistics data matching the structure documented
in cache statistics contracts for testing statistics display and monitoring.
