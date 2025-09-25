---
sidebar_label: test_security_middleware
---

# Comprehensive tests for Security middleware.

  file_path: `backend/tests.old/unit/core/middleware/test_security_middleware.py`

Tests cover security headers injection, request validation, content security policy,
request size limits, and endpoint-specific CSP rules.

## TestSecurityMiddleware

Test Security middleware functionality.

### settings()

```python
def settings(self):
```

Test settings with security configuration.

### app()

```python
def app(self, settings):
```

FastAPI app with security middleware.

### test_middleware_initialization()

```python
def test_middleware_initialization(self, settings):
```

Test middleware initialization with settings.

### test_security_headers_injection_api()

```python
def test_security_headers_injection_api(self, app):
```

Test security headers are injected for API endpoints.

### test_security_headers_injection_docs()

```python
def test_security_headers_injection_docs(self, app):
```

Test relaxed CSP for documentation endpoints.

### test_security_headers_injection_redoc()

```python
def test_security_headers_injection_redoc(self, app):
```

Test relaxed CSP for ReDoc endpoint.

### test_security_headers_injection_openapi()

```python
def test_security_headers_injection_openapi(self, app):
```

Test relaxed CSP for OpenAPI spec.

### test_security_headers_injection_internal()

```python
def test_security_headers_injection_internal(self, app):
```

Test relaxed CSP for internal endpoints.

### test_request_size_validation_within_limit()

```python
def test_request_size_validation_within_limit(self, app):
```

Test request size validation within limits.

### test_request_size_validation_exceeds_limit()

```python
def test_request_size_validation_exceeds_limit(self, app):
```

Test request size validation when exceeding limits.

### test_request_size_validation_invalid_content_length()

```python
def test_request_size_validation_invalid_content_length(self, app):
```

Test request with invalid Content-Length header.

### test_excessive_headers_validation()

```python
def test_excessive_headers_validation(self, app):
```

Test validation of excessive headers count.

### test_headers_count_within_limit()

```python
def test_headers_count_within_limit(self, app):
```

Test request with headers count within limit.

### test_is_docs_endpoint_detection()

```python
def test_is_docs_endpoint_detection(self, settings):
```

Test documentation endpoint detection logic.

### test_middleware_disabled_security_headers()

```python
def test_middleware_disabled_security_headers(self):
```

Test middleware when security headers are disabled.

### test_custom_settings_initialization()

```python
def test_custom_settings_initialization(self):
```

Test middleware initialization with custom settings.

### test_csp_header_content_api_endpoints()

```python
def test_csp_header_content_api_endpoints(self, app):
```

Test detailed CSP content for API endpoints.

### test_csp_header_content_docs_endpoints()

```python
def test_csp_header_content_docs_endpoints(self, app):
```

Test detailed CSP content for documentation endpoints.

### test_response_without_content_length_header()

```python
def test_response_without_content_length_header(self, app):
```

Test request without Content-Length header.

### test_middleware_exception_handling()

```python
async def test_middleware_exception_handling(self, settings):
```

Test middleware behavior when downstream raises exception.

### test_permissions_policy_header()

```python
def test_permissions_policy_header(self, app):
```

Test Permissions-Policy header content.

### test_hsts_header_configuration()

```python
def test_hsts_header_configuration(self, app):
```

Test HSTS header configuration.
