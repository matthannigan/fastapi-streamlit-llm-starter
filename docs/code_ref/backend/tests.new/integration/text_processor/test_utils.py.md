---
sidebar_label: test_utils
---

# Integration test utilities and helpers for TextProcessorService testing.

  file_path: `backend/tests.new/integration/text_processor/test_utils.py`

This module provides comprehensive utilities and helper functions specifically
designed for integration testing of the TextProcessorService and related components.

Key Utilities:
- Test data generators for various scenarios
- Response validators and assertion helpers
- Performance measurement tools
- Error simulation utilities
- Configuration helpers for different test scenarios
- Batch processing test utilities

## ErrorSimulator

Utility class for simulating different types of errors in tests.

### __init__()

```python
def __init__(self):
```

### set_error_pattern()

```python
def set_error_pattern(self, pattern: str, error_type: str = 'infrastructure_error'):
```

Set error pattern for simulation.

Args:
    pattern: Pattern type ('every_third', 'first_two', 'random', 'all')
    error_type: Type of error to simulate

### simulate_errors()

```python
async def simulate_errors(self, user_prompt: str) -> MagicMock:
```

Simulate errors based on configured pattern.

Args:
    user_prompt: Input prompt (used for call counting)

Returns:
    Mock result object

Raises:
    Exception: Based on configured error pattern

## MockAIService

Mock AI service for integration testing with realistic responses.

### __init__()

```python
def __init__(self):
```

### smart_agent_run()

```python
async def smart_agent_run(self, user_prompt: str) -> MagicMock:
```

Return content-aware responses based on input.

Args:
    user_prompt: Input prompt containing user text

Returns:
    Mock result object with appropriate response

## generate_test_text()

```python
def generate_test_text(length: int = 100, prefix: str = 'Test text') -> str:
```

Generate test text of specified length for integration testing.

Args:
    length: Desired length of generated text
    prefix: Prefix text to include at the beginning

Returns:
    Generated text of approximately specified length

## generate_batch_test_data()

```python
def generate_batch_test_data(count: int = 5, operation: str = 'summarize', mixed_operations: bool = True) -> tuple[List[str], List[str]]:
```

Generate test data for batch processing integration tests.

Args:
    count: Number of test items to generate
    operation: Default operation for all items
    mixed_operations: Whether to mix operations for more realistic testing

Returns:
    Tuple of (texts, operations) lists

## generate_malicious_text()

```python
def generate_malicious_text(scenario: str = 'injection') -> str:
```

Generate potentially malicious text for security testing.

Args:
    scenario: Type of malicious content to generate

Returns:
    Text designed to test security controls

## generate_performance_test_data()

```python
def generate_performance_test_data(size: str = 'medium') -> Dict[str, Any]:
```

Generate test data for performance testing scenarios.

Args:
    size: Size of test data ('small', 'medium', 'large', 'xlarge')

Returns:
    Dictionary containing test data and expected performance metrics

## create_batch_request()

```python
def create_batch_request(texts: List[str], operations: List[str], batch_id: str = 'test_batch', questions: Optional[List[str]] = None, options: Optional[List[Dict]] = None) -> Dict[str, Any]:
```

Create a batch request from lists of texts and operations.

Args:
    texts: List of text strings to process
    operations: List of operations corresponding to texts
    batch_id: Unique identifier for the batch
    questions: Optional list of questions for Q&A operations
    options: Optional list of options for each request

Returns:
    Dictionary representing batch processing request

## create_mixed_operation_batch()

```python
def create_mixed_operation_batch(count: int = 5, batch_id: str = 'mixed_ops_batch') -> Dict[str, Any]:
```

Create a batch request with mixed operations for comprehensive testing.

## validate_text_processing_response()

```python
def validate_text_processing_response(response_data: Dict[str, Any], operation: str, expected_success: bool = True) -> None:
```

Validate that text processing response has correct structure and content.

Args:
    response_data: Response data from text processing endpoint
    operation: Expected operation type
    expected_success: Whether the operation should have succeeded

Raises:
    AssertionError: If response doesn't match expected structure

## validate_batch_processing_response()

```python
def validate_batch_processing_response(response_data: Dict[str, Any], expected_total: int, expected_completed: Optional[int] = None) -> None:
```

Validate that batch processing response has correct structure.

Args:
    response_data: Response data from batch processing endpoint
    expected_total: Expected total number of requests
    expected_completed: Expected number of completed requests

Raises:
    AssertionError: If response doesn't match expected structure

## validate_health_response()

```python
def validate_health_response(health_data: Dict[str, Any], expected_healthy: bool = True) -> None:
```

Validate that health check response has correct structure.

Args:
    health_data: Response data from health check endpoint
    expected_healthy: Whether the service should report as healthy

Raises:
    AssertionError: If response doesn't match expected structure

## validate_error_response()

```python
def validate_error_response(response_data: Dict[str, Any], expected_error_type: Optional[str] = None, expected_status_code: Optional[int] = None) -> None:
```

Validate that error response has correct structure and content.

Args:
    response_data: Response data from error endpoint
    expected_error_type: Expected type of error
    expected_status_code: Expected HTTP status code

Raises:
    AssertionError: If response doesn't match expected structure

## measure_sync_performance()

```python
def measure_sync_performance(func, *args, **kwargs) -> Dict[str, Any]:
```

Measure performance of a synchronous function call.

Args:
    func: Function to measure
    *args: Positional arguments for the function
    **kwargs: Keyword arguments for the function

Returns:
    Dictionary containing result and performance metrics

## measure_async_performance()

```python
async def measure_async_performance(func, *args, **kwargs) -> Dict[str, Any]:
```

Measure performance of an asynchronous function call.

Args:
    func: Async function to measure
    *args: Positional arguments for the function
    **kwargs: Keyword arguments for the function

Returns:
    Dictionary containing result and performance metrics

## measure_concurrent_performance()

```python
def measure_concurrent_performance(func, requests: List[Dict], max_concurrent: int = 5) -> Dict[str, Any]:
```

Measure performance of concurrent function calls.

Args:
    func: Function to call concurrently
    requests: List of request dictionaries
    max_concurrent: Maximum number of concurrent calls

Returns:
    Dictionary containing results and performance metrics

## create_authenticated_client()

```python
def create_authenticated_client(client: TestClient, api_key: str = 'test-api-key-12345'):
```

Create a test client with authentication headers.

Args:
    client: FastAPI TestClient instance
    api_key: API key for authentication

Returns:
    Tuple of (client, headers) for authenticated requests

## create_optional_auth_client()

```python
def create_optional_auth_client(client: TestClient, api_key: str = 'optional-auth-key'):
```

Create a test client with optional authentication headers.

Args:
    client: FastAPI TestClient instance
    api_key: Optional API key for authentication

Returns:
    Tuple of (client, headers) for optionally authenticated requests

## make_authenticated_request()

```python
def make_authenticated_request(client: TestClient, method: str, endpoint: str, api_key: str = 'test-api-key-12345', **kwargs):
```

Make an authenticated HTTP request.

Args:
    client: FastAPI TestClient instance
    method: HTTP method (GET, POST, etc.)
    endpoint: API endpoint path
    api_key: API key for authentication
    **kwargs: Additional arguments for the request

Returns:
    HTTP response object

## make_authenticated_async_request()

```python
async def make_authenticated_async_request(client: AsyncClient, method: str, endpoint: str, api_key: str = 'test-api-key-12345', **kwargs):
```

Make an authenticated async HTTP request.

Args:
    client: AsyncClient instance
    method: HTTP method (GET, POST, etc.)
    endpoint: API endpoint path
    api_key: API key for authentication
    **kwargs: Additional arguments for the request

Returns:
    HTTP response object

## create_test_settings()

```python
def create_test_settings(environment: str = 'test', resilience_enabled: bool = True, debug: bool = False, **overrides) -> Dict[str, Any]:
```

Create test settings configuration.

Args:
    environment: Environment name
    resilience_enabled: Whether to enable resilience features
    debug: Debug mode flag
    **overrides: Additional settings to override

Returns:
    Dictionary of test settings

## assert_successful_response()

```python
def assert_successful_response(response, expected_status: int = 200):
```

Assert that HTTP response indicates success.

Args:
    response: HTTP response object
    expected_status: Expected HTTP status code

Raises:
    AssertionError: If response doesn't indicate success

## assert_error_response()

```python
def assert_error_response(response, expected_status: int, expected_error_type: Optional[str] = None):
```

Assert that HTTP response indicates error.

Args:
    response: HTTP response object
    expected_status: Expected HTTP status code
    expected_error_type: Expected type of error

Raises:
    AssertionError: If response doesn't indicate expected error

## assert_performance_requirements()

```python
def assert_performance_requirements(execution_time: float, max_time: float, success_rate: float = 1.0, min_success_rate: float = 0.95):
```

Assert that performance meets requirements.

Args:
    execution_time: Actual execution time
    max_time: Maximum allowed execution time
    success_rate: Actual success rate
    min_success_rate: Minimum required success rate

Raises:
    AssertionError: If performance doesn't meet requirements

## create_cache_scenario()

```python
def create_cache_scenario(cache_hit: bool = False, cache_data: Optional[Dict] = None):
```

Create cache testing scenario configuration.

Args:
    cache_hit: Whether cache should return data
    cache_data: Data to return from cache if cache_hit is True

Returns:
    Dictionary containing cache scenario configuration

## create_failure_scenario()

```python
def create_failure_scenario(failure_type: str = 'infrastructure', expected_status: int = 502):
```

Create failure testing scenario configuration.

Args:
    failure_type: Type of failure to simulate
    expected_status: Expected HTTP status code for failure

Returns:
    Dictionary containing failure scenario configuration

## create_performance_scenario()

```python
def create_performance_scenario(batch_size: int = 5, concurrent_requests: int = 3, expected_max_time: float = 5.0):
```

Create performance testing scenario configuration.

Args:
    batch_size: Number of requests in batch
    concurrent_requests: Number of concurrent requests
    expected_max_time: Maximum expected execution time

Returns:
    Dictionary containing performance scenario configuration
