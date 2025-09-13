---
sidebar_label: test_global_exception_handler_middleware
---

# Comprehensive tests for Global Exception Handler.

  file_path: `backend/tests/core/middleware/test_global_exception_handler_middleware.py`

Tests cover exception handling, HTTP status mapping, error response formatting,
request correlation, and special case handling.

## TestGlobalExceptionHandler

Test Global Exception Handler functionality.

### settings()

```python
def settings(self):
```

Test settings for exception handler configuration.

### app()

```python
def app(self, settings):
```

FastAPI app with global exception handler configured.

### test_setup_global_exception_handler()

```python
def test_setup_global_exception_handler(self, settings):
```

Test exception handler setup function.

### test_successful_request_no_exception()

```python
def test_successful_request_no_exception(self, app):
```

Test that successful requests are not affected by exception handler.

### test_validation_error_handling()

```python
def test_validation_error_handling(self, mock_logger, app):
```

Test handling of ValidationError exceptions.

### test_authentication_error_handling()

```python
def test_authentication_error_handling(self, mock_logger, app):
```

Test handling of AuthenticationError exceptions.

### test_authorization_error_handling()

```python
def test_authorization_error_handling(self, mock_logger, app):
```

Test handling of AuthorizationError exceptions.

### test_configuration_error_handling()

```python
def test_configuration_error_handling(self, mock_logger, app):
```

Test handling of ConfigurationError exceptions.

### test_business_logic_error_handling()

```python
def test_business_logic_error_handling(self, mock_logger, app):
```

Test handling of BusinessLogicError exceptions.

### test_infrastructure_error_handling()

```python
def test_infrastructure_error_handling(self, mock_logger, app):
```

Test handling of InfrastructureError exceptions.

### test_transient_ai_error_handling()

```python
def test_transient_ai_error_handling(self, mock_logger, app):
```

Test handling of TransientAIError exceptions.

### test_permanent_ai_error_handling()

```python
def test_permanent_ai_error_handling(self, mock_logger, app):
```

Test handling of PermanentAIError exceptions.

### test_generic_exception_handling()

```python
def test_generic_exception_handling(self, mock_logger, app):
```

Test handling of generic exceptions.

### test_api_version_error_special_case()

```python
def test_api_version_error_special_case(self, mock_logger, app):
```

Test special case handling for API version errors.

### test_request_validation_error_handling()

```python
def test_request_validation_error_handling(self, mock_logger, app):
```

Test handling of FastAPI request validation errors.

### test_request_id_correlation_in_logs()

```python
def test_request_id_correlation_in_logs(self, mock_logger, app):
```

Test that request ID is included in exception logs.

### test_exception_logging_structure()

```python
def test_exception_logging_structure(self, mock_logger, app):
```

Test structured logging format for exceptions.

### test_application_error_with_context()

```python
def test_application_error_with_context(self, mock_logger, app):
```

Test ApplicationError with context data.

### test_error_response_timestamp_format()

```python
def test_error_response_timestamp_format(self, mock_logger, app):
```

Test that error responses include properly formatted timestamps.

### test_exception_handler_doesnt_affect_normal_http_exceptions()

```python
def test_exception_handler_doesnt_affect_normal_http_exceptions(self, app):
```

Test that normal HTTP exceptions are handled by FastAPI.

### test_concurrent_exception_handling()

```python
def test_concurrent_exception_handling(self, mock_logger, app):
```

Test exception handling with concurrent requests.

### test_error_response_schema_compliance()

```python
def test_error_response_schema_compliance(self, app):
```

Test that error responses comply with ErrorResponse schema.

### test_context_variable_fallback()

```python
def test_context_variable_fallback(self, mock_logger, app):
```

Test fallback when request_id is not in state but in context.
