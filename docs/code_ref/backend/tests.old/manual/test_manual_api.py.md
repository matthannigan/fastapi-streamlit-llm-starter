---
sidebar_label: test_manual_api
---

# Manual integration tests for API endpoints.

  file_path: `backend/tests.old/manual/test_manual_api.py`

These tests require actual AI API keys and make real API calls.
They are designed for manual testing and validation of the complete API flow.

## APITestHelper

Helper class for manual API testing with comprehensive scenario coverage.

### call_endpoint()

```python
def call_endpoint(endpoint: str, api_key: Optional[str] = None, method: str = 'GET', data: Optional[dict] = None) -> Tuple[Optional[int], Union[dict, str, None]]:
```

Reusable helper method for endpoint testing with optional API key.

This pattern enables comprehensive scenario coverage across different endpoints
with consistent error handling and response validation.

## TestManualAPI

Manual integration tests for the FastAPI application.

### test_health_endpoint()

```python
async def test_health_endpoint(self):
```

Test the health endpoint.

### test_operations_endpoint()

```python
async def test_operations_endpoint(self):
```

Test the operations endpoint.

### process_text_operation()

```python
async def process_text_operation(self, operation: str, text: str, options: Optional[Dict[str, Any]] = None, question: Optional[str] = None) -> Tuple[int, Optional[dict]]:
```

Helper method to test text processing endpoint for a specific operation.

### test_all_text_processing_operations()

```python
async def test_all_text_processing_operations(self):
```

Test all text processing operations with AI integration.

### test_manual_integration_suite()

```python
async def test_manual_integration_suite(self):
```

Run the complete manual integration test suite.

## TestManualAuthentication

Manual authentication tests with comprehensive scenario coverage.

These tests validate authentication behavior across different endpoint types
and security scenarios, derived from legacy testing patterns.

### test_public_endpoints()

```python
def test_public_endpoints(self):
```

Test public endpoints that should work without API key.

### test_protected_endpoints_without_auth()

```python
def test_protected_endpoints_without_auth(self):
```

Test protected endpoints without API key (should fail).

### test_protected_endpoints_with_invalid_auth()

```python
def test_protected_endpoints_with_invalid_auth(self):
```

Test protected endpoints with invalid API key (should fail).

### test_protected_endpoints_with_valid_auth()

```python
def test_protected_endpoints_with_valid_auth(self):
```

Test protected endpoints with valid API key (should work if configured).

### test_optional_auth_endpoints()

```python
def test_optional_auth_endpoints(self):
```

Test endpoints that work with or without authentication.

### test_auth_edge_cases()

```python
def test_auth_edge_cases(self):
```

Test authentication edge cases and malformed requests.

### test_complete_auth_suite()

```python
def test_complete_auth_suite(self):
```

Run the complete authentication test suite.

## run_manual_tests()

```python
async def run_manual_tests():
```

Run all manual tests - can be called directly.
