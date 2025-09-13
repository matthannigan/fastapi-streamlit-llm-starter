---
sidebar_label: test_request_size_middleware
---

# Comprehensive tests for Request Size Limiting Middleware

  file_path: `backend/tests/core/middleware/test_request_size_middleware.py`

Tests cover content-length validation, streaming size limits, endpoint-specific limits,
content-type limits, and DoS protection features.

## TestRequestSizeLimitMiddleware

Test the main request size limiting middleware.

### settings()

```python
def settings(self):
```

Test settings with size limiting configuration.

### app()

```python
def app(self, settings):
```

FastAPI test app with request size limiting middleware.

### test_middleware_initialization()

```python
def test_middleware_initialization(self, settings):
```

Test middleware initialization with custom settings.

### test_get_size_limit_endpoint_specific()

```python
def test_get_size_limit_endpoint_specific(self, app, settings):
```

Test endpoint-specific size limit retrieval.

### test_get_size_limit_content_type_specific()

```python
def test_get_size_limit_content_type_specific(self, app, settings):
```

Test content-type specific size limit retrieval.

### test_get_size_limit_default_fallback()

```python
def test_get_size_limit_default_fallback(self, app, settings):
```

Test fallback to default size limit.

### test_format_size_human_readable()

```python
def test_format_size_human_readable(self, app, settings):
```

Test human-readable size formatting.

### test_skip_size_check_for_get_requests()

```python
def test_skip_size_check_for_get_requests(self, app):
```

Test that GET requests skip size checking.

### test_content_length_header_validation_pass()

```python
def test_content_length_header_validation_pass(self, app):
```

Test passing content-length validation.

### test_content_length_header_validation_fail()

```python
def test_content_length_header_validation_fail(self, app):
```

Test failing content-length validation.

### test_invalid_content_length_header()

```python
def test_invalid_content_length_header(self, app):
```

Test handling of invalid Content-Length header.

### test_streaming_size_validation_pass()

```python
def test_streaming_size_validation_pass(self, app):
```

Test streaming size validation that passes.

### test_streaming_size_validation_fail()

```python
def test_streaming_size_validation_fail(self, app):
```

Test streaming size validation that fails.

### test_response_headers_include_size_info()

```python
def test_response_headers_include_size_info(self, app):
```

Test that successful responses include size limit information.

### test_different_limits_per_endpoint()

```python
def test_different_limits_per_endpoint(self, app):
```

Test different size limits for different endpoints.

### test_content_type_specific_limits()

```python
def test_content_type_specific_limits(self, app):
```

Test content-type specific size limits.

## TestRequestTooLargeException

Test custom exception for request size violations.

### test_exception_creation()

```python
def test_exception_creation(self):
```

Test creating RequestTooLargeException.

## TestASGIRequestSizeLimitMiddleware

Test ASGI-level request size limiting middleware.

### asgi_app()

```python
def asgi_app(self):
```

Simple ASGI app for testing.

### asgi_middleware()

```python
def asgi_middleware(self, asgi_app):
```

ASGI middleware with size limits.

### test_asgi_middleware_non_http_passthrough()

```python
async def test_asgi_middleware_non_http_passthrough(self, asgi_middleware):
```

Test ASGI middleware passes through non-HTTP requests.

### test_asgi_middleware_get_method_passthrough()

```python
async def test_asgi_middleware_get_method_passthrough(self, asgi_middleware):
```

Test ASGI middleware passes through GET requests.

### test_asgi_middleware_content_length_check_pass()

```python
async def test_asgi_middleware_content_length_check_pass(self, asgi_middleware):
```

Test ASGI middleware content-length validation passes.

### test_asgi_middleware_content_length_check_fail()

```python
async def test_asgi_middleware_content_length_check_fail(self, asgi_middleware):
```

Test ASGI middleware content-length validation fails.

### test_asgi_middleware_invalid_content_length()

```python
async def test_asgi_middleware_invalid_content_length(self, asgi_middleware):
```

Test ASGI middleware handles invalid content-length.

### test_asgi_middleware_streaming_validation()

```python
async def test_asgi_middleware_streaming_validation(self, asgi_middleware):
```

Test ASGI middleware streaming size validation.

## TestRequestSizeIntegration

Integration tests for request size limiting.

### integration_app()

```python
def integration_app(self):
```

App with comprehensive size limits for integration testing.

### test_progressive_size_limits()

```python
def test_progressive_size_limits(self, integration_app):
```

Test different endpoints with progressive size limits.

### test_content_type_precedence_over_endpoint()

```python
def test_content_type_precedence_over_endpoint(self, integration_app):
```

Test that endpoint limits take precedence over content-type limits.

### test_error_response_details()

```python
def test_error_response_details(self, integration_app):
```

Test detailed error responses for size violations.

### test_concurrent_size_validation()

```python
def test_concurrent_size_validation(self, integration_app):
```

Test size validation under concurrent load.

## TestRequestSizePerformance

Performance tests for request size limiting middleware.

### performance_app()

```python
def performance_app(self):
```

App configured for performance testing.

### test_size_validation_performance_overhead()

```python
def test_size_validation_performance_overhead(self, performance_app):
```

Test performance overhead of size validation.

### test_large_request_processing_time()

```python
def test_large_request_processing_time(self, performance_app):
```

Test processing time for large requests within limits.
