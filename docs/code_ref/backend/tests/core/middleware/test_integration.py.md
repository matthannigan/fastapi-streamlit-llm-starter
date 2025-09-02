---
sidebar_label: test_integration
---

# Integration tests for core middleware functionality.

  file_path: `backend/tests/core/middleware/test_integration.py`

## TestMiddlewareIntegration

Integration tests for core middleware functionality.

### middleware_app()

```python
def middleware_app(self):
```

App with core middleware for integration testing.

### test_middleware_app_basic_functionality()

```python
def test_middleware_app_basic_functionality(self, middleware_app):
```

Test basic functionality with middleware stack.

### test_health_check_endpoint()

```python
def test_health_check_endpoint(self, middleware_app):
```

Test health check endpoint with middleware.
