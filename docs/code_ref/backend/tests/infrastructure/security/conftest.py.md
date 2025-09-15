---
sidebar_label: conftest
---

# Security infrastructure test fixtures providing dependencies for auth module testing.

  file_path: `backend/tests/infrastructure/security/conftest.py`

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the security component from systems outside its boundary.

Dependencies covered:
- Settings configuration (Fake)
- Environment detection service (Mock)
- Custom exception classes (Real imports)
- FastAPI security utilities (Mock)

## FakeSettings

Fake settings configuration for testing auth module behavior.

Provides a lightweight, configurable settings implementation that simulates
the real Settings class without complex initialization or external dependencies.

Behavior:
    - Supports setting api_key and additional_api_keys for test scenarios
    - Provides default values that work for "happy path" testing
    - Stateful - can be modified during tests to simulate different configurations
    - No validation or complex logic - pure data container

Usage:
    # Default configuration (no keys)
    settings = FakeSettings()
    assert settings.api_key is None

    # Single API key configuration
    settings = FakeSettings(api_key="test-key-123")
    assert settings.api_key == "test-key-123"

    # Multiple keys configuration
    settings = FakeSettings(
        api_key="primary-key",
        additional_api_keys="key1,key2,key3"
    )

### __init__()

```python
def __init__(self, api_key: Optional[str] = None, additional_api_keys: Optional[str] = None):
```

## fake_settings()

```python
def fake_settings():
```

Provides a fake settings configuration for auth module testing.

Returns a FakeSettings instance with no API keys configured by default,
simulating development mode behavior. Individual tests can customize
the returned settings instance to test different scenarios.

Behavior:
    - Default: No API keys configured (development mode)
    - Stateful: Tests can modify the returned instance
    - Realistic: Matches the interface expected by auth module

Use Cases:
    - Testing development mode behavior (no keys)
    - Testing single API key scenarios
    - Testing multiple API key scenarios
    - Testing configuration validation logic

Test Customization:
    def test_auth_with_api_key(fake_settings):
        fake_settings.api_key = "test-key-123"
        # Test will see this key configuration
        auth = APIKeyAuth()
        assert auth.verify_api_key("test-key-123")

## fake_settings_with_primary_key()

```python
def fake_settings_with_primary_key():
```

Provides fake settings with a single primary API key configured.

Pre-configured for testing scenarios where authentication is required
and only one API key is needed.

Returns:
    FakeSettings with api_key="test-primary-key-123"

Use Cases:
    - Testing single key validation
    - Testing production security enforcement
    - Testing authentication success scenarios

## fake_settings_with_multiple_keys()

```python
def fake_settings_with_multiple_keys():
```

Provides fake settings with multiple API keys configured.

Pre-configured for testing scenarios involving multiple valid keys
such as key rotation, team access, or service-to-service authentication.

Returns:
    FakeSettings with:
    - api_key="test-primary-key-123"
    - additional_api_keys="test-key-456,test-key-789"

Use Cases:
    - Testing multiple key validation
    - Testing key rotation scenarios
    - Testing metadata assignment for different key types

## mock_environment_detection()

```python
def mock_environment_detection():
```

Provides spec'd mock for environment detection service.

Mocks the get_environment_info function from app.core.environment with
realistic return values for testing environment-aware security behavior.

Default Behavior:
    - Returns development environment with high confidence
    - Includes realistic reasoning for environment detection
    - Safe for all test scenarios (non-production environment)

Customization:
    Individual tests can reconfigure the mock to simulate different
    environments (production, staging) and confidence levels.

Use Cases:
    - Testing development mode behavior
    - Testing production security enforcement
    - Testing environment detection integration
    - Testing error context inclusion

Test Customization:
    def test_production_security(mock_environment_detection):
        # Configure mock to return production environment
        mock_environment_detection.return_value = MockEnvironmentInfo(
            environment=Environment.PRODUCTION,
            confidence=0.95,
            reasoning="Production indicators detected"
        )
        # Test production security enforcement

## mock_production_environment()

```python
def mock_production_environment(mock_environment_detection):
```

Pre-configured mock for production environment detection.

Configures the environment detection mock to return production environment
with high confidence, useful for testing production security enforcement.

Returns:
    Mock configured to return:
    - environment: Environment.PRODUCTION
    - confidence: 0.95
    - reasoning: "Production deployment detected"

Use Cases:
    - Testing production security validation
    - Testing API key requirement enforcement
    - Testing production-specific error messages

## mock_staging_environment()

```python
def mock_staging_environment(mock_environment_detection):
```

Pre-configured mock for staging environment detection.

Configures the environment detection mock to return staging environment
with high confidence, useful for testing staging-specific behavior.

Returns:
    Mock configured to return:
    - environment: Environment.STAGING
    - confidence: 0.88
    - reasoning: "Staging environment indicators found"

Use Cases:
    - Testing staging security requirements
    - Testing environment-specific configuration
    - Testing staging deployment scenarios

## mock_http_bearer_credentials()

```python
def mock_http_bearer_credentials():
```

Provides spec'd mock for FastAPI HTTPAuthorizationCredentials.

Creates a realistic mock of FastAPI's HTTPAuthorizationCredentials class
with configurable credentials for testing authentication dependency behavior.

Default Behavior:
    - Returns None (simulating missing Authorization header)
    - Individual tests can configure specific credential values

Customization:
    Tests can set the credentials attribute to simulate different
    authentication scenarios.

Use Cases:
    - Testing missing credentials scenarios
    - Testing valid API key authentication
    - Testing invalid API key scenarios
    - Testing Bearer token format validation

Test Customization:
    def test_valid_credentials(mock_http_bearer_credentials):
        mock_http_bearer_credentials.credentials = "test-api-key-123"
        # Test authentication with this key

    def test_missing_credentials():
        # Use default None value for missing credentials test

## valid_http_bearer_credentials()

```python
def valid_http_bearer_credentials(mock_http_bearer_credentials):
```

Pre-configured mock with valid Bearer credentials.

Provides HTTPAuthorizationCredentials mock configured with a valid
test API key for testing successful authentication scenarios.

Returns:
    Mock with credentials="test-valid-key-123"

Use Cases:
    - Testing successful authentication flows
    - Testing API key validation logic
    - Testing authenticated endpoint access

## invalid_http_bearer_credentials()

```python
def invalid_http_bearer_credentials(mock_http_bearer_credentials):
```

Pre-configured mock with invalid Bearer credentials.

Provides HTTPAuthorizationCredentials mock configured with an invalid
test API key for testing authentication failure scenarios.

Returns:
    Mock with credentials="invalid-test-key"

Use Cases:
    - Testing authentication failure handling
    - Testing invalid API key rejection
    - Testing error response generation
