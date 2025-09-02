---
sidebar_label: test_request_isolation
---

# Comprehensive test suite for context isolation and request boundary logging.

  file_path: `backend/tests/integration/test_request_isolation.py`

This test suite verifies that:
1. No context leakage occurs between requests
2. Request boundary logging works correctly
3. The system maintains proper isolation under various conditions

## TestContextIsolation

Test suite for verifying context isolation between requests.

### setup_ai_mocking()

```python
def setup_ai_mocking(self, mock_cache_service):
```

Automatically set up AI and cache mocking for all tests in this class.

### client()

```python
def client(self):
```

Create a test client.

### headers()

```python
def headers(self):
```

Standard headers for authenticated requests.

### async_client()

```python
def async_client(self):
```

Create an async test client.

### mock_settings()

```python
def mock_settings(self):
```

Create mock settings for TextProcessorService.

### mock_cache()

```python
def mock_cache(self):
```

Create mock cache for TextProcessorService.

### mock_cache_service()

```python
def mock_cache_service(self):
```

Create mock cache service for dependency injection.

### test_sequential_requests_no_context_leakage()

```python
def test_sequential_requests_no_context_leakage(self, client, headers):
```

Test that sequential requests don't leak context between them.

### test_injection_attempt_isolation()

```python
def test_injection_attempt_isolation(self, client, headers):
```

Test that injection attempts don't affect subsequent requests.

### test_concurrent_requests_isolation()

```python
async def test_concurrent_requests_isolation(self, headers):
```

Test that concurrent requests don't interfere with each other.

### test_cache_isolation_by_content()

```python
def test_cache_isolation_by_content(self, client, headers, mock_cache_service):
```

Test that cache isolation works correctly based on content.

### test_service_level_isolation()

```python
def test_service_level_isolation(self, mock_settings, mock_cache):
```

Test that the TextProcessorService maintains isolation.

### test_different_operations_isolation()

```python
def test_different_operations_isolation(self, client, headers):
```

Test that different operations don't leak context.

### test_qa_operation_isolation()

```python
def test_qa_operation_isolation(self, client, headers):
```

Test Q&A operation doesn't leak context to other requests.

### test_batch_processing_isolation()

```python
async def test_batch_processing_isolation(self, headers):
```

Test that batch processing maintains isolation between items.

### test_error_handling_isolation()

```python
def test_error_handling_isolation(self, client, headers):
```

Test that error conditions don't leak context.

### test_memory_isolation_verification()

```python
def test_memory_isolation_verification(self, mock_settings, mock_cache):
```

Test that there's no shared memory between service calls.

## TestRequestBoundaryLogging

Test suite for verifying request boundary logging functionality.

### setup_cache_mocking()

```python
def setup_cache_mocking(self, mock_cache_service):
```

Automatically set up cache mocking for all tests in this class.

### client()

```python
def client(self):
```

Create a test client.

### headers()

```python
def headers(self):
```

Standard headers for authenticated requests.

### mock_cache_service()

```python
def mock_cache_service(self):
```

Create mock cache service for dependency injection.

### test_request_boundary_logging_format()

```python
def test_request_boundary_logging_format(self, client, headers, caplog):
```

Test that request boundary logging follows the correct format.

### test_processing_boundary_logging()

```python
def test_processing_boundary_logging(self, client, headers, caplog):
```

Test that processing boundary logging works correctly.

### test_unique_request_ids()

```python
def test_unique_request_ids(self, client, headers, caplog):
```

Test that each request gets a unique ID.
