---
sidebar_label: test_manual_auth
---

# Manual authentication tests for the FastAPI application.

  file_path: `backend/tests.old/manual/test_manual_auth.py`

These tests are designed to run against a live server instance
and validate authentication behavior manually.

## TestManualAuthentication

Manual authentication tests for the FastAPI application.

### call_endpoint()

```python
def call_endpoint(self, endpoint: str, api_key: Optional[str] = None, method: str = 'GET', data: Optional[dict] = None) -> Tuple[Optional[int], Union[dict, str, None]]:
```

Helper method to test an endpoint with optional API key.

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

### test_complete_auth_suite()

```python
def test_complete_auth_suite(self):
```

Run the complete authentication test suite.

## run_manual_auth_tests()

```python
def run_manual_auth_tests():
```

Run all manual auth tests - can be called directly.
