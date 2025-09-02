---
sidebar_label: test_api_client
---

# Tests for the API client.

  file_path: `frontend/tests/test_api_client.py`

## TestAPIClient

Test the APIClient class.

### test_health_check_success()

```python
async def test_health_check_success(self, api_client):
```

Test successful health check.

### test_health_check_failure()

```python
async def test_health_check_failure(self, api_client):
```

Test failed health check.

### test_health_check_exception()

```python
async def test_health_check_exception(self, api_client):
```

Test health check with exception.

### test_get_operations_success()

```python
async def test_get_operations_success(self, api_client):
```

Test successful get operations.

### test_get_operations_failure()

```python
async def test_get_operations_failure(self, api_client):
```

Test failed get operations.

### test_process_text_success()

```python
async def test_process_text_success(self, api_client, sample_request, sample_response):
```

Test successful text processing.

### test_process_text_api_error()

```python
async def test_process_text_api_error(self, api_client, sample_request):
```

Test text processing with API error.

### test_process_text_timeout()

```python
async def test_process_text_timeout(self, api_client, sample_request):
```

Test text processing with timeout.

### test_process_text_general_exception()

```python
async def test_process_text_general_exception(self, api_client, sample_request):
```

Test text processing with general exception.

## TestRunAsync

Test the run_async helper function.

### test_run_async_success()

```python
def test_run_async_success(self):
```

Test successful async execution.

### test_run_async_with_exception()

```python
def test_run_async_with_exception(self):
```

Test async execution with exception.

## api_client()

```python
def api_client():
```

Create an API client instance for testing.
