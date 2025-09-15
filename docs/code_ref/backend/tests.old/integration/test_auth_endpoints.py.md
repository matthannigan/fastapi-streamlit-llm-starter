---
sidebar_label: test_auth_endpoints
---

# Integration tests for API endpoint authentication.

  file_path: `backend/tests.old/integration/test_auth_endpoints.py`

## TestAuthEndpoints

Integration tests for API endpoint authentication.

### client()

```python
def client(self):
```

Create a test client.

### test_process_endpoint_with_valid_api_key()

```python
def test_process_endpoint_with_valid_api_key(self, client):
```

Test /text_processing/process endpoint with valid API key.

### test_process_endpoint_with_invalid_api_key()

```python
def test_process_endpoint_with_invalid_api_key(self, client):
```

Test /text_processing/process endpoint with invalid API key.

### test_process_endpoint_without_api_key()

```python
def test_process_endpoint_without_api_key(self, client):
```

Test /text_processing/process endpoint without API key.

### test_process_endpoint_with_empty_api_key()

```python
def test_process_endpoint_with_empty_api_key(self, client):
```

Test /text_processing/process endpoint with empty API key.

### test_process_endpoint_with_malformed_auth_header()

```python
def test_process_endpoint_with_malformed_auth_header(self, client):
```

Test /text_processing/process endpoint with malformed authorization header.

### test_process_endpoint_development_mode()

```python
def test_process_endpoint_development_mode(self, client):
```

Test /text_processing/process endpoint in development mode (no API keys configured).

### test_process_endpoint_qa_operation_with_auth()

```python
def test_process_endpoint_qa_operation_with_auth(self, client):
```

Test /text_processing/process endpoint with Q&A operation and valid auth.

### test_process_endpoint_qa_operation_without_auth()

```python
def test_process_endpoint_qa_operation_without_auth(self, client):
```

Test QA operation requires authentication.

### test_process_endpoint_batch_operations_with_auth()

```python
def test_process_endpoint_batch_operations_with_auth(self, client):
```

Test that different operations work with authentication.

### test_process_endpoint_with_case_sensitive_api_key()

```python
def test_process_endpoint_with_case_sensitive_api_key(self, client):
```

Test that API keys are case-sensitive.

### test_process_endpoint_auth_logging()

```python
def test_process_endpoint_auth_logging(self, client):
```

Test that authentication attempts are logged.

## TestProcessEndpointAuthEdgeCases

Test edge cases and concurrent scenarios for process endpoint authentication.

### client()

```python
def client(self):
```

Create a test client.

### test_process_endpoint_auth_with_concurrent_requests()

```python
def test_process_endpoint_auth_with_concurrent_requests(self, client):
```

Test authentication with concurrent requests.
