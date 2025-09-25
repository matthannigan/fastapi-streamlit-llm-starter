---
sidebar_label: conftest
---

# Authentication Integration Test Fixtures

  file_path: `backend/tests.new/integration/auth/conftest.py`

This module provides fixtures for authentication integration testing, including
environment-aware configuration, API key setup, and test clients with different
authentication scenarios.

## clean_environment()

```python
def clean_environment():
```

Ensure clean environment variables for each test.

## clean_environment_no_keys()

```python
def clean_environment_no_keys():
```

Ensure clean environment variables for each test with no API keys.

## development_environment()

```python
def development_environment(clean_environment):
```

Set up development environment (no API keys).

## production_environment()

```python
def production_environment(clean_environment):
```

Set up production environment with API keys.

## staging_environment()

```python
def staging_environment(clean_environment):
```

Set up staging environment with API keys.

## advanced_auth_config()

```python
def advanced_auth_config(clean_environment):
```

Set up advanced authentication configuration.

## single_api_key_config()

```python
def single_api_key_config(clean_environment):
```

Set up configuration with single API key.

## multiple_api_keys_config()

```python
def multiple_api_keys_config(clean_environment):
```

Set up configuration with multiple API keys.

## reload_auth_keys_after_multi()

```python
def reload_auth_keys_after_multi(multiple_api_keys_config):
```

Reload global auth keys after setting multiple key environment variables.

## reload_auth_keys_after_clear()

```python
def reload_auth_keys_after_clear(development_environment):
```

Ensure no keys are configured and reload global auth keys (development mode).

## mock_environment_detection()

```python
def mock_environment_detection():
```

Mock environment detection for controlled testing.

## mock_production_environment_detection()

```python
def mock_production_environment_detection(mock_environment_detection):
```

Mock environment detection to return production environment.

## mock_environment_detection_failure()

```python
def mock_environment_detection_failure():
```

Mock environment detection to fail.

## valid_api_key_headers()

```python
def valid_api_key_headers():
```

Headers with valid API key for authenticated requests.

## invalid_api_key_headers()

```python
def invalid_api_key_headers():
```

Headers with invalid API key for testing authentication failures.

## x_api_key_headers()

```python
def x_api_key_headers():
```

Headers using X-API-Key instead of Authorization Bearer.

## malformed_auth_headers()

```python
def malformed_auth_headers():
```

Headers with malformed authentication.

## missing_auth_headers()

```python
def missing_auth_headers():
```

Headers without any authentication.

## auth_system_with_keys()

```python
def auth_system_with_keys():
```

Create a fresh auth system with configured API keys.

## auth_system_without_keys()

```python
def auth_system_without_keys():
```

Create a fresh auth system without API keys (development mode).
