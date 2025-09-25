---
sidebar_label: test_cors_middleware
---

# Comprehensive tests for CORS middleware.

  file_path: `backend/tests.old/unit/core/middleware/test_cors_middleware.py`

Tests cover CORS configuration, origin validation, credentials handling,
header/method allowances, and preflight request processing.

## TestCORSMiddleware

Test CORS middleware setup and configuration.

### settings()

```python
def settings(self):
```

Test settings with CORS configuration.

### app()

```python
def app(self):
```

Basic FastAPI app for testing.

### cors_app()

```python
def cors_app(self, app, settings):
```

FastAPI app with CORS middleware configured.

### test_setup_cors_middleware()

```python
def test_setup_cors_middleware(self, app, settings):
```

Test CORS middleware setup function.

### test_cors_simple_request_allowed_origin()

```python
def test_cors_simple_request_allowed_origin(self, cors_app):
```

Test simple CORS request with allowed origin.

### test_cors_simple_request_disallowed_origin()

```python
def test_cors_simple_request_disallowed_origin(self, cors_app):
```

Test simple CORS request with disallowed origin.

### test_cors_preflight_request_allowed_origin()

```python
def test_cors_preflight_request_allowed_origin(self, cors_app):
```

Test CORS preflight request with allowed origin.

### test_cors_preflight_request_disallowed_origin()

```python
def test_cors_preflight_request_disallowed_origin(self, cors_app):
```

Test CORS preflight request with disallowed origin.

### test_cors_credentials_support()

```python
def test_cors_credentials_support(self, cors_app):
```

Test CORS credentials support.

### test_cors_all_methods_allowed()

```python
def test_cors_all_methods_allowed(self, cors_app):
```

Test that all HTTP methods are allowed in CORS.

### test_cors_all_headers_allowed()

```python
def test_cors_all_headers_allowed(self, cors_app):
```

Test that all headers are allowed in CORS.

### test_cors_no_origin_header()

```python
def test_cors_no_origin_header(self, cors_app):
```

Test request without Origin header (same-origin request).

### test_cors_multiple_origins_configuration()

```python
def test_cors_multiple_origins_configuration(self):
```

Test CORS setup with multiple allowed origins.

### test_cors_wildcard_origin_configuration()

```python
def test_cors_wildcard_origin_configuration(self):
```

Test CORS setup with wildcard origin (development mode).

### test_cors_middleware_logging()

```python
def test_cors_middleware_logging(self, app, settings):
```

Test that CORS middleware setup includes proper logging.

### test_cors_empty_origins_list()

```python
def test_cors_empty_origins_list(self):
```

Test CORS setup with empty origins list.

### test_cors_response_headers_preservation()

```python
def test_cors_response_headers_preservation(self, cors_app):
```

Test that CORS middleware preserves other response headers.
