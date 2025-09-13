---
sidebar_label: test_text_processing_endpoints
---

# Tests for the text processing endpoints of the FastAPI application.

  file_path: `backend/tests/api/v1/test_text_processing_endpoints.py`

## TestOperationsEndpoint

Test operations endpoint.

### test_get_operations()

```python
def test_get_operations(self, client: TestClient):
```

Test getting available operations.

## TestProcessEndpoint

Test text processing endpoint.

### test_process_summarize()

```python
def test_process_summarize(self, authenticated_client, sample_text, mock_processor):
```

Test text summarization with authentication using DI override.

### test_process_sentiment()

```python
def test_process_sentiment(self, authenticated_client, sample_text, mock_processor):
```

Test sentiment analysis with authentication using DI override.

### test_process_qa_without_question()

```python
def test_process_qa_without_question(self, authenticated_client, sample_text, mock_processor):
```

Test Q&A without question returns error - handle both HTTP responses and ValidationError exceptions.

### test_process_qa_with_question()

```python
def test_process_qa_with_question(self, authenticated_client, sample_text, mock_processor):
```

Test Q&A with question and authentication using DI override.

### test_process_invalid_operation()

```python
def test_process_invalid_operation(self, authenticated_client, sample_text, mock_processor):
```

Test invalid operation returns error.

### test_process_empty_text()

```python
def test_process_empty_text(self, authenticated_client, mock_processor):
```

Test empty text returns validation error.

### test_process_text_too_long()

```python
def test_process_text_too_long(self, authenticated_client, mock_processor):
```

Test text too long returns validation error.

## TestCacheIntegration

Test cache integration with processing endpoints.

### test_process_with_cache_miss()

```python
def test_process_with_cache_miss(self, authenticated_client, sample_text):
```

Test processing with cache miss.

### test_process_with_cache_hit()

```python
def test_process_with_cache_hit(self, authenticated_client, sample_text):
```

Test processing with cache hit.

## TestBatchProcessEndpoint

Test the /text_processing/batch_process endpoint.

### test_batch_process_success()

```python
def test_batch_process_success(self, authenticated_client: TestClient, sample_text):
```

Test successful batch processing.

### test_batch_process_exceeds_limit()

```python
def test_batch_process_exceeds_limit(self, authenticated_client: TestClient, sample_text):
```

Test batch processing with too many requests - handle both HTTP responses and ValidationError exceptions.

### test_batch_process_empty_requests_list()

```python
def test_batch_process_empty_requests_list(self, authenticated_client: TestClient):
```

Test batch processing with an empty requests list - use flexible response structure checking.

### test_batch_process_no_auth()

```python
def test_batch_process_no_auth(self, client: TestClient, sample_text):
```

Test batch processing without authentication - handle both HTTP responses and AuthenticationError exceptions.

### test_batch_process_invalid_auth()

```python
def test_batch_process_invalid_auth(self, client: TestClient, sample_text):
```

Test batch processing with invalid authentication - handle both HTTP responses and AuthenticationError exceptions.

### test_batch_process_service_exception()

```python
def test_batch_process_service_exception(self, authenticated_client: TestClient, sample_text):
```

Test batch processing when the service raises an exception - handle both HTTP responses and InfrastructureError exceptions.

## TestBatchStatusEndpoint

Test the /text_processing/batch_status/{batch_id} endpoint.

### test_get_batch_status_success()

```python
def test_get_batch_status_success(self, authenticated_client: TestClient):
```

Test getting batch status successfully.

### test_get_batch_status_no_auth()

```python
def test_get_batch_status_no_auth(self, client: TestClient):
```

Test getting batch status without authentication - handle both HTTP responses and AuthenticationError exceptions.

### test_get_batch_status_invalid_auth()

```python
def test_get_batch_status_invalid_auth(self, client: TestClient):
```

Test getting batch status with invalid authentication - handle both HTTP responses and AuthenticationError exceptions.

## TestAuthentication

Test authentication functionality.

### test_process_with_explicit_auth()

```python
def test_process_with_explicit_auth(self, client, sample_text):
```

Test process endpoint with explicit authentication.

### test_process_with_invalid_auth()

```python
def test_process_with_invalid_auth(self, client, sample_text):
```

Test that invalid API keys are rejected - handle both HTTP responses and AuthenticationError exceptions.

### test_authenticated_client_fixture()

```python
def test_authenticated_client_fixture(self, authenticated_client, sample_text):
```

Test that the authenticated_client fixture works correctly.

### test_operations_endpoint_with_auth()

```python
def test_operations_endpoint_with_auth(self, authenticated_client):
```

Test operations endpoint with authentication (optional auth).
