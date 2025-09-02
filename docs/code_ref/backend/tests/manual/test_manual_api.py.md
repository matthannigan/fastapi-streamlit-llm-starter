---
sidebar_label: test_manual_api
---

# Manual integration tests for API endpoints.

  file_path: `backend/tests/manual/test_manual_api.py`

These tests require actual AI API keys and make real API calls.
They are designed for manual testing and validation of the complete API flow.

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

## run_manual_tests()

```python
async def run_manual_tests():
```

Run all manual tests - can be called directly.
