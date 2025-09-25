---
sidebar_label: conftest
---

# Integration test fixtures and utilities for TextProcessorService testing.

  file_path: `backend/tests.new/integration/text_processor/conftest.py`

This module provides comprehensive fixtures and utilities specifically designed
for integration testing of the TextProcessorService and related components.

Fixtures are organized by category:
- Service fixtures: TextProcessorService instances with various configurations
- Mock fixtures: AI agent, cache, and resilience mocking
- Data fixtures: Sample text and request data for testing
- Client fixtures: HTTP clients for API testing
- Configuration fixtures: Settings and configuration for different environments

## ErrorSimulator

Utility class for simulating different types of errors.

### __init__()

```python
def __init__(self):
```

### set_error_pattern()

```python
def set_error_pattern(self, pattern):
```

Set error pattern for simulation.

### simulate_errors()

```python
async def simulate_errors(self, user_prompt):
```

Simulate errors based on configured pattern.

## mock_settings()

```python
def mock_settings():
```

Create mock settings for TextProcessorService testing.

## mock_cache()

```python
def mock_cache():
```

Create mock cache service for TextProcessorService testing.

## text_processor_service()

```python
def text_processor_service(mock_settings, mock_cache):
```

Create TextProcessorService instance with mocked dependencies.

## text_processor_service_with_real_cache()

```python
def text_processor_service_with_real_cache(mock_settings):
```

Create TextProcessorService instance with real cache implementation for integration testing.

## mock_ai_agent()

```python
def mock_ai_agent():
```

Create intelligent mock AI agent for integration testing.

## mock_ai_agent_autouse()

```python
def mock_ai_agent_autouse(mock_ai_agent):
```

Automatically mock AI agent for all tests in this directory.

## sample_text()

```python
def sample_text():
```

Sample text for integration testing.

## sample_texts()

```python
def sample_texts():
```

Multiple sample texts for batch processing testing.

## malicious_input_text()

```python
def malicious_input_text():
```

Sample text with potential security issues for sanitization testing.

## sample_request()

```python
def sample_request(sample_text):
```

Sample text processing request for testing.

## sample_batch_request()

```python
def sample_batch_request(sample_texts):
```

Sample batch processing request for testing.

## client()

```python
def client():
```

Create FastAPI test client for integration testing.

## auth_headers()

```python
def auth_headers():
```

Headers with valid authentication for protected endpoints.

## invalid_auth_headers()

```python
def invalid_auth_headers():
```

Headers with invalid authentication for testing auth failures.

## optional_auth_headers()

```python
def optional_auth_headers():
```

Headers with optional authentication for public endpoints.

## async_client()

```python
def async_client():
```

Create async HTTP client for integration testing.

## development_settings()

```python
def development_settings():
```

Settings configured for development environment.

## production_settings()

```python
def production_settings():
```

Settings configured for production environment.

## custom_settings()

```python
def custom_settings():
```

Settings with custom configuration for testing overrides.

## cache_hit_scenario()

```python
def cache_hit_scenario():
```

Configuration for cache hit testing scenario.

## cache_miss_scenario()

```python
def cache_miss_scenario():
```

Configuration for cache miss testing scenario.

## failure_scenario()

```python
def failure_scenario():
```

Configuration for failure scenario testing.

## mixed_batch_scenario()

```python
def mixed_batch_scenario():
```

Configuration for mixed success/failure batch scenario.

## create_authenticated_client()

```python
def create_authenticated_client(client, api_key = 'test-api-key-12345'):
```

Create a test client with authentication headers.

## create_batch_request()

```python
def create_batch_request(texts, operations, batch_id = 'test_batch'):
```

Create a batch request from lists of texts and operations.

## assert_batch_success_response()

```python
def assert_batch_success_response(response_data, expected_total, expected_completed = None):
```

Assert that batch response indicates successful processing.

## assert_health_status_healthy()

```python
def assert_health_status_healthy(health_data):
```

Assert that health status indicates healthy system.

## performance_test_config()

```python
def performance_test_config():
```

Configuration for performance testing scenarios.

## measure_performance()

```python
def measure_performance(func, *args, **kwargs):
```

Measure performance of a function call.

## measure_async_performance()

```python
async def measure_async_performance(func, *args, **kwargs):
```

Measure performance of an async function call.

## generate_test_text()

```python
def generate_test_text(length = 100, prefix = 'Test text'):
```

Generate test text of specified length.

## generate_batch_test_data()

```python
def generate_batch_test_data(count = 5, operation = 'summarize'):
```

Generate test data for batch processing.

## error_simulator()

```python
def error_simulator():
```

Create error simulator for testing error handling.

## assert_text_processing_response()

```python
def assert_text_processing_response(response_data, operation, expected_success = True):
```

Assert that text processing response has correct structure.

## assert_batch_processing_response()

```python
def assert_batch_processing_response(response_data, expected_total, expected_completed = None):
```

Assert that batch processing response has correct structure.

## assert_error_response()

```python
def assert_error_response(response_data, expected_error_type = None):
```

Assert that error response has correct structure.
