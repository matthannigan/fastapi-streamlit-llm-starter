---
sidebar_label: test_main_endpoints
---

# Tests for the main FastAPI application.

  file_path: `backend/tests/api/v1/test_main_endpoints.py`

## TestHealthEndpoint

Test health check endpoint.

### test_health_check()

```python
def test_health_check(self, client: TestClient):
```

Test health check returns 200.

## TestCORS

Test CORS configuration.

### test_cors_headers()

```python
def test_cors_headers(self, client: TestClient):
```

Test CORS headers are set correctly.

## TestErrorHandling

Test error handling.

### test_404_endpoint()

```python
def test_404_endpoint(self, client: TestClient):
```

Test 404 for non-existent endpoint.

## TestRootEndpoint

Test root endpoint.

### test_root_endpoint()

```python
def test_root_endpoint(self, client: TestClient):
```

Test the root endpoint.

## TestAPIDocumentation

Test API documentation endpoints.

### test_api_docs()

```python
def test_api_docs(self, client: TestClient):
```

Test that API documentation is accessible.

### test_openapi_schema()

```python
def test_openapi_schema(self, client: TestClient):
```

Test that OpenAPI schema is accessible.

## TestAuthentication

Test authentication functionality.

### test_auth_status_with_valid_key()

```python
def test_auth_status_with_valid_key(self, authenticated_client):
```

Test auth status with valid API key.

### test_auth_status_without_key()

```python
def test_auth_status_without_key(self, client):
```

Test auth status without API key in test environment.
