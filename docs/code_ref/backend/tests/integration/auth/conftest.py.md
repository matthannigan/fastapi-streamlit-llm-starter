---
sidebar_label: conftest
---

# Shared fixtures for authentication integration tests.

  file_path: `backend/tests/integration/auth/conftest.py`

Provides environment manipulation, test client setup, and authentication
configuration for testing authentication system integration.

## reload_auth_system()

```python
def reload_auth_system():
```

Force authentication system to reload configuration and keys.

Must be called after environment variables are modified to ensure
the authentication system picks up the changes.

## client()

```python
def client():
```

FastAPI test client for authentication integration testing.

Provides real HTTP client that exercises complete FastAPI middleware
stack including authentication dependencies and exception handling.

Use Cases:
    - Testing complete HTTP authentication flows
    - Validating HTTP response codes and headers
    - Testing middleware integration and compatibility

## clean_environment()

```python
def clean_environment(monkeypatch):
```

Clean environment fixture that removes all auth-related variables.

Ensures test isolation by clearing authentication configuration
before each test, preventing environment variable pollution.

Cleanup Actions:
    - Removes API_KEY and ADDITIONAL_API_KEYS
    - Clears AUTH_MODE and tracking settings
    - Resets ENVIRONMENT variable

## production_environment()

```python
def production_environment(clean_environment):
```

Configure production environment for testing production security enforcement.

Sets up environment variables that trigger production security mode
with API key requirements and strict validation.

Configuration:
    - ENVIRONMENT=production (triggers production security)
    - API_KEY=test-production-key (primary key)
    - ADDITIONAL_API_KEYS=test-secondary-key (additional keys)

## development_environment()

```python
def development_environment(clean_environment):
```

Configure development environment for testing development mode behavior.

Sets up environment that triggers development mode with optional
authentication and appropriate warnings.

Configuration:
    - ENVIRONMENT=development (triggers development mode)
    - No API keys configured (enables development mode)

## development_with_keys_environment()

```python
def development_with_keys_environment(clean_environment):
```

Configure development environment with API keys for mixed-mode testing.

Tests scenario where development environment has API keys configured,
ensuring authentication still works but with development-appropriate behavior.

Configuration:
    - ENVIRONMENT=development
    - API_KEY=test-dev-key (development key)

## multiple_api_keys_environment()

```python
def multiple_api_keys_environment(clean_environment):
```

Configure environment with multiple API keys for key management testing.

Tests multi-key authentication scenarios including primary key,
additional keys, and whitespace handling.

Configuration:
    - Primary key via API_KEY
    - Multiple additional keys via ADDITIONAL_API_KEYS
    - Keys with various formatting (whitespace testing)

## auth_headers_valid()

```python
def auth_headers_valid():
```

Generate valid authentication headers for testing.

Returns:
    Dict with Authorization header using Bearer token format

## auth_headers_invalid()

```python
def auth_headers_invalid():
```

Generate invalid authentication headers for testing.

Returns:
    Dict with Authorization header using invalid API key

## auth_headers_secondary()

```python
def auth_headers_secondary():
```

Generate authentication headers using secondary API key.

Returns:
    Dict with Authorization header using secondary key from ADDITIONAL_API_KEYS
