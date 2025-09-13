---
sidebar_label: conftest
---

# Test fixtures for GenericRedisCache unit tests.

  file_path: `backend/tests/infrastructure/cache/redis_generic/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_generic.pyi file.

Fixture Categories:
    - Basic test data fixtures (keys, values, Redis URLs, TTL values)
    - Mock dependency fixtures (InMemoryCache, CachePerformanceMonitor, SecurityConfig)
    - Configuration fixtures (various GenericRedisCache configurations)
    - Redis operation fixtures (connection states, callback systems)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateful mocks maintain internal state for realistic behavior
    - Mock dependencies are spec'd against real classes for accuracy

## sample_redis_url()

```python
def sample_redis_url():
```

Standard Redis URL for testing connections.

Provides a typical Redis connection URL used across multiple test scenarios
for consistency in testing Redis connection functionality.

## sample_secure_redis_url()

```python
def sample_secure_redis_url():
```

Secure Redis URL with TLS for testing secure connections.

Provides a Redis URL with TLS encryption for testing
security-enabled cache configurations.

## sample_large_value()

```python
def sample_large_value():
```

Large cache value for testing compression functionality.

Provides a large data structure that exceeds typical compression
thresholds to test compression behavior.

## fake_redis_client()

```python
def fake_redis_client():
```

Fake Redis client for testing Redis operations.

Provides a fakeredis instance that behaves like a real Redis server,
including proper Redis operations, data types, expiration, and error handling.
This provides more realistic testing than mocks while not requiring a real Redis instance.

## default_generic_redis_config()

```python
def default_generic_redis_config():
```

Default GenericRedisCache configuration for standard testing.

Provides a standard configuration dictionary suitable for most test scenarios.
This represents the 'happy path' configuration that should work reliably.

## secure_generic_redis_config()

```python
def secure_generic_redis_config(mock_path_exists):
```

Secure GenericRedisCache configuration for security testing.

Provides a configuration with security features enabled for testing
secure Redis connections and security validation.

Creates the security configuration on-demand to ensure mock_path_exists
is active during SecurityConfig creation.

## mock_path_exists()

```python
def mock_path_exists():
```

Fixture that mocks pathlib.Path.exists for certificate file validation.

Uses autospec=True to ensure the mock's signature matches the real
method, which is crucial for using side_effect correctly. The default
return_value is True for "happy path" tests.

Note: This fixture is now redundant since it's already defined in parent conftest,
but kept here for clarity in the redis_generic test module context.

## mock_ssl_context()

```python
def mock_ssl_context():
```

Fixture that mocks SSL certificate loading operations for security testing.

Mocks ssl.SSLContext.load_cert_chain and ssl.SSLContext.load_verify_locations
to prevent actual file system access during testing. Essential for security
tests that require TLS configuration without real certificate files.

## compression_redis_config()

```python
def compression_redis_config():
```

GenericRedisCache configuration optimized for compression testing.

Provides a configuration with low compression threshold and high compression level
to facilitate testing of compression functionality.

## no_l1_redis_config()

```python
def no_l1_redis_config():
```

GenericRedisCache configuration without L1 cache for Redis-only testing.

Provides a configuration with L1 cache disabled to test pure Redis
operations without memory cache interference.

## sample_callback_functions()

```python
def sample_callback_functions():
```

Sample callback functions for testing the callback system.

Provides a set of test callback functions that can be used to test
the callback registration and invocation system.

## bulk_test_data()

```python
def bulk_test_data():
```

Bulk test data for testing batch operations and performance.

Provides a set of key-value pairs for testing bulk operations,
L1 cache behavior, and performance characteristics.

## compression_test_data()

```python
def compression_test_data():
```

Test data specifically designed for compression testing.

Provides data with varying sizes and compressibility to test
compression threshold behavior and compression ratio calculations.
