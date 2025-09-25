---
sidebar_label: test_utils
---

# Tests for core middleware utility functions.

  file_path: `backend/tests.old/unit/core/middleware/test_utils.py`

## TestMiddlewareUtilities

Test middleware utility functions.

### test_get_request_id_from_state()

```python
def test_get_request_id_from_state(self):
```

Test getting request ID from request state.

### test_get_request_id_from_context()

```python
def test_get_request_id_from_context(self):
```

Test getting request ID from context when not in state.

### test_get_request_duration_valid()

```python
def test_get_request_duration_valid(self):
```

Test getting request duration with valid timing.

### test_get_request_duration_no_timing()

```python
def test_get_request_duration_no_timing(self):
```

Test getting request duration without timing information.

### test_add_response_headers()

```python
def test_add_response_headers(self):
```

Test adding custom headers to response.

### test_add_response_headers_skip_restricted()

```python
def test_add_response_headers_skip_restricted(self):
```

Test that restricted headers are not added.

### test_is_health_check_request_health_paths()

```python
def test_is_health_check_request_health_paths(self):
```

Test health check detection for standard health paths.

### test_is_health_check_request_health_prefix()

```python
def test_is_health_check_request_health_prefix(self):
```

Test health check detection for paths starting with /health.

### test_is_health_check_request_user_agent()

```python
def test_is_health_check_request_user_agent(self):
```

Test health check detection based on User-Agent header.

### test_is_health_check_request_regular_request()

```python
def test_is_health_check_request_regular_request(self):
```

Test that regular requests are not detected as health checks.
