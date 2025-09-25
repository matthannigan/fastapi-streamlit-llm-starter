---
sidebar_label: conftest
---

# Integration-specific fixtures for testing.

  file_path: `backend/tests/integration/conftest.py`

## production_environment_integration()

```python
def production_environment_integration():
```

Set up production environment with API keys for integration tests.

## integration_app()

```python
def integration_app():
```

Application instance for integration testing.

## integration_client()

```python
def integration_client(integration_app, production_environment_integration):
```

HTTP client for integration testing with production environment setup.

## async_integration_client()

```python
async def async_integration_client(integration_app):
```

Async HTTP client for integration testing.

## authenticated_headers()

```python
def authenticated_headers():
```

Headers with valid authentication for integration tests.

## invalid_api_key_headers()

```python
def invalid_api_key_headers():
```

Headers with invalid API key for integration tests.

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
