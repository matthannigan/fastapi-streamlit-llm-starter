---
sidebar_label: test_setup
---

# Tests for the main middleware setup function.

  file_path: `backend/tests/core/middleware/test_setup.py`

## TestMiddlewareSetup

Test the main middleware setup function.

### settings()

```python
def settings(self):
```

Test settings with all middleware enabled.

### app()

```python
def app(self):
```

Basic FastAPI app for testing.

### test_setup_middleware_all_enabled()

```python
def test_setup_middleware_all_enabled(self, app, settings):
```

Test middleware setup with all components enabled.

### test_setup_middleware_selective_disable()

```python
def test_setup_middleware_selective_disable(self, app):
```

Test middleware setup with some components disabled.

### test_setup_middleware_enhanced_components()

```python
def test_setup_middleware_enhanced_components(self, app):
```

Test setup with enhanced middleware components.
