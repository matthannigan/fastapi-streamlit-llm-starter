---
sidebar_label: test_request_logging_middleware
---

# Comprehensive tests for Request Logging middleware.

  file_path: `backend/tests.old/unit/core/middleware/test_request_logging_middleware.py`

Tests cover request/response logging, correlation IDs, timing information,
sensitive data filtering, and structured logging.

## TestRequestLoggingMiddleware

Test Request Logging middleware functionality.

### settings()

```python
def settings(self):
```

Test settings with request logging configuration.

### app()

```python
def app(self, settings):
```

FastAPI app with request logging middleware.

### test_middleware_initialization()

```python
def test_middleware_initialization(self, settings):
```

Test middleware initialization with settings.

### test_middleware_initialization_defaults()

```python
def test_middleware_initialization_defaults(self):
```

Test middleware initialization with default values.

### test_request_start_logging()

```python
def test_request_start_logging(self, mock_logger, app):
```

Test request start logging with correlation ID.

### test_request_completion_logging()

```python
def test_request_completion_logging(self, mock_logger, app):
```

Test successful request completion logging.

### test_request_id_generation_and_context()

```python
def test_request_id_generation_and_context(self, mock_logger, app):
```

Test request ID generation and context variable setting.

### test_request_state_integration()

```python
def test_request_state_integration(self, app):
```

Test that request ID is stored in request state.

### test_slow_request_warning()

```python
def test_slow_request_warning(self, mock_logger, app):
```

Test slow request detection and warning logging.

### test_client_error_logging_level()

```python
def test_client_error_logging_level(self, mock_logger, app):
```

Test logging level for client errors (4xx).

### test_server_error_logging_level()

```python
def test_server_error_logging_level(self, mock_logger, app):
```

Test logging level for server errors (5xx).

### test_exception_handling_logging()

```python
def test_exception_handling_logging(self, mock_logger, app):
```

Test logging when exceptions occur during request processing.

### test_post_request_with_body_logging()

```python
def test_post_request_with_body_logging(self, mock_logger, app):
```

Test logging POST requests with request body.

### test_query_parameters_logging()

```python
def test_query_parameters_logging(self, mock_logger, app):
```

Test logging of query parameters.

### test_user_agent_logging()

```python
def test_user_agent_logging(self, mock_logger, app):
```

Test user agent header logging.

### test_response_size_logging()

```python
def test_response_size_logging(self, mock_logger, app):
```

Test response size calculation and logging.

### test_timing_accuracy()

```python
def test_timing_accuracy(self, mock_logger, app):
```

Test request timing accuracy in logs.

### test_different_http_methods_logging()

```python
def test_different_http_methods_logging(self, mock_logger, app):
```

Test logging across different HTTP methods.

### test_context_variables_isolation()

```python
def test_context_variables_isolation(self, settings):
```

Test that context variables are properly isolated between requests.

### test_sensitive_headers_filtering()

```python
def test_sensitive_headers_filtering(self, mock_logger, app):
```

Test that sensitive headers are not logged.

### test_client_ip_logging()

```python
def test_client_ip_logging(self, mock_logger, app):
```

Test client IP address logging.

### test_request_id_correlation()

```python
def test_request_id_correlation(self, mock_logger, app):
```

Test request ID correlation between start and completion logs.
