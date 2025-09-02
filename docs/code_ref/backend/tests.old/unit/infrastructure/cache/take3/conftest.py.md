---
sidebar_label: conftest
---

# Test fixtures for AIResponseCache unit tests.

  file_path: `backend/tests.old/unit/infrastructure/cache/take3/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_ai.pyi file.

Fixture Categories:
    - Basic test data fixtures (sample texts, operations, responses)
    - Mock dependency fixtures (parameter mapper, key generator, monitor)
    - Configuration fixtures (valid/invalid parameter sets)
    - Error scenario fixtures (exception mocks, connection failures)

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

## valid_ai_params()

```python
def valid_ai_params():
```

Valid AIResponseCache initialization parameters.

Provides a complete set of valid parameters that should pass
validation and allow successful cache initialization.

## invalid_ai_params()

```python
def invalid_ai_params():
```

Invalid AIResponseCache initialization parameters for testing validation errors.

## mock_parameter_mapper()

```python
def mock_parameter_mapper():
```

Mock CacheParameterMapper for testing parameter mapping behavior.

Configured to return expected generic and AI-specific parameter
separation as documented in the parameter mapping interface.

## mock_parameter_mapper_with_validation_errors()

```python
def mock_parameter_mapper_with_validation_errors():
```

Mock parameter mapper that returns validation errors for testing error handling.

## mock_key_generator()

```python
def mock_key_generator():
```

Mock CacheKeyGenerator for testing key generation behavior.

## mock_performance_monitor()

```python
def mock_performance_monitor():
```

Mock CachePerformanceMonitor for testing metrics collection behavior.

## mock_generic_redis_cache()

```python
def mock_generic_redis_cache():
```

Mock GenericRedisCache parent class for testing inheritance behavior.

Configured with expected parent class methods and their documented behavior.

## mock_redis_connection_failure()

```python
def mock_redis_connection_failure():
```

Mock Redis connection failure for testing graceful degradation behavior.

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
