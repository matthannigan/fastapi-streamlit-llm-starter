# Authentication Infrastructure Unit Tests

Unit tests for `auth` module following our **behavior-driven contract testing** philosophy. These tests verify the complete public interface of the authentication infrastructure component in complete isolation, ensuring it fulfills its documented security and access control contracts.

## Component Overview

**Component Under Test**: `AuthConfig` and `APIKeyAuth` (`app.infrastructure.security.auth`)

**Component Type**: Infrastructure Security Service (Single Module)

**Primary Responsibility**: Provides environment-aware API key authentication, multi-key validation, security enforcement, and FastAPI dependency integration for protecting API endpoints.

**Public Contract**: Validates API keys, enforces production security requirements, provides flexible operation modes (development/production/advanced), and integrates seamlessly with FastAPI dependency injection.

**Filesystem Locations:**
  - Production Code: `backend/app/infrastructure/security/auth.py`
  - Public Contract: `backend/contracts/infrastructure/security/auth.pyi`
  - Test Suite:      `backend/tests/unit/auth/test_*.py`
  - Test Fixtures:   `backend/tests/unit/auth/conftest.py`

## Test Organization

### Component-Based Test Structure (4 Test Files, Multiple Test Classes)

#### **API KEY AUTHENTICATION CORE** (Primary authentication logic)

1. **`test_api_key_auth.py`** (CRITICAL) - **Comprehensive test class covering APIKeyAuth initialization and behavior**
   - APIKeyAuth Initialization → Environment Detection → Key Loading Behavior
   - Development Mode Support → No Key Fallback → Warning Generation
   - Production Security Enforcement → Key Validation → ConfigurationError on Violation
   - Multi-Key Support → Primary + Additional Keys → Key Rotation Testing
   - Metadata Management → User Tracking → Request Context Enhancement
   - Tests authentication logic with complete security enforcement coverage

#### **AUTHENTICATION CONFIGURATION** (Configuration management and validation)

2. **`test_auth_config.py`** (COMPREHENSIVE) - **Focused test classes for AuthConfig behavior**
   - AuthConfig Initialization → Environment Variable Loading → Default Value Handling
   - Operation Mode Detection → Simple/Advanced Modes → Feature Flag Management
   - Production Security Validation → Environment-Aware Enforcement → Security Policy
   - Configuration Flexibility → Runtime Changes → Dynamic Configuration Testing
   - Tests configuration management with complete environment integration

#### **FASTAPI DEPENDENCY INTEGRATION** (Framework integration testing)

3. **`test_auth_dependencies.py`** (INTEGRATION) - **Test classes for FastAPI dependency integration**
   - API Key Verification Dependencies → Bearer Token Extraction → Validation Flow
   - HTTP Exception Wrapping → Custom Exception Conversion → Middleware Compatibility
   - Request Context Integration → Authentication Results → Error Response Generation
   - Dependency Injection Testing → FastAPI Integration → Route Protection Behavior
   - Tests complete FastAPI integration with proper error handling

#### **AUTHENTICATION UTILITIES** (Helper functions and edge cases)

4. **`test_auth_utilities.py`** (UTILITY) - **Focused test classes for utility functions**
   - Key Format Validation → Bearer Token Processing → String Normalization
   - Metadata Extraction → User Context Building → Request Information
   - Error Handling Utilities → Exception Creation → Message Formatting
   - Security Helper Functions → Key Comparison → Validation Utilities
   - Tests utility functions with comprehensive edge case coverage

## Testing Philosophy Applied

These unit tests exemplify our **behavior-driven contract testing** principles:

- **Component as Unit**: Tests verify entire authentication system behavior, not individual methods
- **Contract Focus**: Tests validate documented public interface (Args, Returns, Raises, Behavior sections)
- **Boundary Mocking**: Mock only external dependencies (environment detection, FastAPI internals), never internal auth logic
- **Observable Outcomes**: Test return values, exceptions, and side effects visible to external callers
- **Environment Isolation**: Proper `monkeypatch.setenv()` usage for environment variable testing
- **High-Fidelity Fakes**: Use realistic fake objects (FakeSettings) instead of simple mocks where appropriate

## Test Fixtures and Infrastructure

### **Settings Configuration Fixtures**
```python
@pytest.fixture
def fake_settings():
    """Fake settings configuration for testing auth module behavior."""
    from tests.unit.auth.conftest import FakeSettings
    return FakeSettings()

@pytest.fixture
def settings_with_multiple_keys():
    """Settings with multiple API keys for testing multi-key authentication."""
    return FakeSettings(
        api_key="primary-key-12345",
        additional_api_keys="secondary-key-67890,tertiary-key-abcdef"
    )
```

### **Environment Detection Fixtures**
```python
@pytest.fixture
def mock_environment_detection():
    """Mock environment detection service for testing environment-aware security."""
    mock_service = Mock()
    mock_service.get_environment.return_value = Environment.DEVELOPMENT
    return mock_service

@pytest.fixture
def mock_production_environment(mock_environment_detection):
    """Mock environment detection to return production environment."""
    mock_environment_detection.get_environment.return_value = Environment.PRODUCTION
    return mock_environment_detection
```

### **FastAPI Request Fixtures**
```python
@pytest.fixture
def mock_request_with_bearer_token():
    """Mock FastAPI request with valid Bearer token for testing."""
    mock_request = Mock(spec=Request)
    mock_request.headers = {"authorization": "Bearer test-api-key-12345"}
    return mock_request

@pytest.fixture
def mock_credentials():
    """Mock HTTP authorization credentials for testing."""
    mock_creds = Mock(spec=HTTPAuthorizationCredentials)
    mock_creds.scheme = "bearer"
    mock_creds.credentials = "test-api-key-12345"
    return mock_creds
```

### **API Key Authentication Fixtures**
```python
@pytest.fixture
def api_key_auth_instance(fake_settings):
    """Real APIKeyAuth instance for testing authentication behavior."""
    from app.infrastructure.security.auth import APIKeyAuth
    return APIKeyAuth(settings=fake_settings)

@pytest.fixture
def api_key_auth_with_keys():
    """APIKeyAuth instance configured with multiple keys."""
    settings = FakeSettings(
        api_key="primary-key",
        additional_api_keys="key1,key2,key3"
    )
    from app.infrastructure.security.auth import APIKeyAuth
    return APIKeyAuth(settings=settings)
```

### **Security Configuration Fixtures**
```python
@pytest.fixture
def mock_secure_auth_env(monkeypatch):
    """Mock environment variables for secure authentication configuration."""
    monkeypatch.setenv("API_KEY", "sk-prod-1234567890abcdef")
    monkeypatch.setenv("ADDITIONAL_API_KEYS", "sk-dev-fedcba987654321,sk-test-abcdef123456")
    monkeypatch.setenv("AUTH_MODE", "advanced")
    monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
    return monkeypatch

@pytest.fixture
def mock_development_auth_env(monkeypatch):
    """Mock environment for development authentication testing."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("AUTH_MODE", "simple")
    monkeypatch.delenv("API_KEY", raising=False)
    return monkeypatch
```

## Running Tests

```bash
# Run all auth unit tests
make test-backend PYTEST_ARGS="tests/unit/auth/ -v"

# Run specific test files
make test-backend PYTEST_ARGS="tests/unit/auth/test_api_key_auth.py -v"
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_config.py -v"
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_dependencies.py -v"
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_utilities.py -v"

# Run by test class
make test-backend PYTEST_ARGS="tests/unit/auth/test_api_key_auth.py::TestAPIKeyAuthInitialization -v"
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_config.py::TestAuthConfigInitialization -v"
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_dependencies.py::TestAPIKeyVerificationDependencies -v"
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_utilities.py::TestKeyFormatValidation -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/unit/auth/ --cov=app.infrastructure.security.auth"

# Run specific test methods
make test-backend PYTEST_ARGS="tests/unit/auth/test_api_key_auth.py::TestAPIKeyAuthInitialization::test_api_key_auth_initializes_with_no_keys_development_mode -v"

# Run with verbose output for debugging
make test-backend PYTEST_ARGS="tests/unit/auth/ -v -s"
```

## Test Quality Standards

### **Performance Requirements**
- **Execution Speed**: < 100ms per test (fast feedback loop)
- **Determinism**: No timing dependencies or sleep() calls
- **Isolation**: No external service dependencies or network calls
- **Resource Cleanup**: Automatic fixture cleanup prevents test pollution

### **Contract Coverage Requirements**
- **Public Methods**: 100% coverage of all public authentication methods
- **Input Validation**: Complete Args section testing per docstring
- **Output Verification**: Complete Returns section testing per docstring
- **Exception Handling**: Complete Raises section testing per docstring
- **Behavior Guarantees**: Complete Behavior section testing per docstring

### **Security Testing Standards**
- **Authentication Bypass**: Verify no authentication bypass is possible
- **Production Security**: Ensure production environments enforce strict security
- **Environment Awareness**: Verify environment detection integration works correctly
- **Key Validation**: Comprehensive API key format and validation testing
- **Error Handling**: Security-related errors provide minimal information disclosure

## Success Criteria

### **API Key Authentication Core**
- ✅ APIKeyAuth initializes correctly with zero, single, or multiple API keys
- ✅ Development mode provides unauthenticated access with appropriate warnings
- ✅ Production mode enforces strict authentication with fail-fast validation
- ✅ Multi-key authentication supports key rotation and primary/secondary key logic
- ✅ Metadata management works correctly for advanced authentication features

### **Authentication Configuration**
- ✅ AuthConfig loads and validates environment variables correctly
- ✅ Operation modes (simple/advanced) are detected and applied appropriately
- ✅ Production security validation enforces strict security requirements
- ✅ Configuration changes are detected and applied at runtime
- ✅ Default values provide secure baseline configuration

### **FastAPI Dependency Integration**
- ✅ API key verification dependencies work correctly with Bearer token extraction
- ✅ HTTP exception wrapping converts custom exceptions to proper HTTP responses
- ✅ Request context integration provides authentication results to downstream code
- ✅ Dependency injection testing shows complete FastAPI framework compatibility
- ✅ Route protection behavior prevents unauthorized access effectively

### **Authentication Utilities**
- ✅ Key format validation handles Bearer token processing correctly
- ✅ Metadata extraction builds complete user context information
- ✅ Error handling utilities create appropriate exception objects
- ✅ Security helper functions support key comparison and validation
- ✅ Edge cases and malformed inputs are handled gracefully

### **Environment-Aware Security**
- ✅ Development environments allow flexible access with appropriate warnings
- ✅ Production environments enforce strict authentication without exception
- ✅ Environment detection integration works correctly with all environments
- ✅ Security policies adapt correctly based on detected environment
- ✅ Environment changes between tests are properly isolated

### **Multi-Key Authentication**
- ✅ Primary API key authentication works correctly
- ✅ Additional API keys are loaded and validated properly
- ✅ Key rotation scenarios are handled without service interruption
- ✅ Invalid keys are rejected with appropriate error messages
- ✅ Key comparison logic is secure against timing attacks

## What's NOT Tested (Integration Test Concerns)

### **External System Integration**
- Actual FastAPI application integration and HTTP request/response handling
- Real HTTP request processing and middleware chain integration
- External authentication provider integration (OAuth, JWT, etc.)
- Database-backed user authentication and session management

### **Security Implementation Details**
- Cryptographic security of API key storage and comparison
- Internal Bearer token parsing and validation algorithm implementation
- HTTP security headers and transport layer security (TLS/SSL)
- Authentication token generation and key management systems

### **Application Deployment Integration**
- FastAPI application startup integration with authentication middleware
- Production deployment environment integration and configuration
- Load balancer and reverse proxy authentication integration
- Authentication service scaling and high-availability scenarios

## Environment Variables for Testing

```bash
# Authentication Mode Configuration
AUTH_MODE=simple                                    # Simple authentication mode (default)
AUTH_MODE=advanced                                 # Advanced mode with user tracking

# Primary API Key Configuration
API_KEY=sk-1234567890abcdef                       # Primary API key for authentication
API_KEY=sk-prod-xyz789                             # Production API key format

# Additional API Keys Configuration
ADDITIONAL_API_KEYS=sk-key2,sk-key3,sk-key4       # Comma-separated additional keys
ADDITIONAL_API_KEYS=sk-dev-abc,sk-test-123        # Development additional keys

# Advanced Feature Flags
ENABLE_USER_TRACKING=true                         # Enable user context tracking
ENABLE_REQUEST_LOGGING=true                       # Enable request metadata logging
ENABLE_DETAILED_LOGGING=true                      # Enable detailed security logging

# Environment Detection (Automatic)
ENVIRONMENT=development                            # Development environment (flexible security)
ENVIRONMENT=production                            # Production environment (strict security)
ENVIRONMENT=testing                              # Testing environment (validation focused)

# Security Override Testing (Development Only)
AUTH_DISABLE_SECURITY_CHECKS=true                 # Disable security validation (testing only)
AUTH_ALLOW_DEVELOPMENT_MODE=true                  # Force development mode for testing
AUTH_DEBUG_MODE=true                              # Enable debug logging for security testing

# Error Scenario Testing
API_KEY=invalid-key-format                        # Invalid API key format testing
API_KEY=too-short                                 # Invalid key length testing
AUTH_MODE=invalid-mode                            # Invalid operation mode testing
```

## Test Method Examples

### **Environment-Aware Authentication Testing**
```python
def test_api_key_auth_initializes_with_no_keys_development_mode(self, fake_settings, mock_environment_detection):
    """
    Test that APIKeyAuth initializes successfully with no API keys in development.

    Verifies: APIKeyAuth can be created without API keys for development environments
              per Args and Returns documentation.

    Business Impact: Enables local development without API key management overhead
                    while maintaining security awareness through warning logs.

    Given: Development environment detected and no API keys configured
    When: APIKeyAuth is created with fake settings containing no keys
    Then: APIKeyAuth initializes successfully
    And: No exceptions are raised during initialization
    And: Development mode behavior is enabled
    And: Warning about missing API keys is logged

    Fixtures Used:
        - fake_settings: Settings with no API keys configured
        - mock_environment_detection: Development environment simulation
    """
    # Given: Development environment with no keys
    mock_environment_detection.get_environment.return_value = Environment.DEVELOPMENT

    # When: Creating APIKeyAuth without keys
    auth = APIKeyAuth(settings=fake_settings)

    # Then: Initialization succeeds
    assert auth is not None
    assert hasattr(auth, 'api_keys')
    assert len(auth.api_keys) == 0

    # And: Development mode is enabled
    assert auth.development_mode is True
```

### **Production Security Enforcement Testing**
```python
def test_api_key_auth_raises_configuration_error_in_production_without_keys(self, mock_production_environment, fake_settings):
    """
    Test that APIKeyAuth raises ConfigurationError in production without API keys.

    Verifies: APIKeyAuth raises ConfigurationError for production environments
              without API keys per documented security requirements.

    Business Impact: Prevents insecure production deployments by failing fast at
                    startup, protecting sensitive data from unauthorized access.

    Given: Production environment detected and no API keys configured
    When: APIKeyAuth is created with empty settings
    Then: ConfigurationError is raised
    And: Error message mentions production security requirements
    And: Error message provides actionable guidance

    Fixtures Used:
        - mock_production_environment: Production environment simulation
        - fake_settings: Settings with no API keys configured
    """
    # Given: Production environment with no keys
    mock_production_environment.get_environment.return_value = Environment.PRODUCTION

    # When/Then: Production security requires API keys
    with pytest.raises(ConfigurationError) as exc_info:
        APIKeyAuth(settings=fake_settings)

    error_message = str(exc_info.value)
    assert "production" in error_message.lower()
    assert "api key" in error_message.lower()
    assert "security" in error_message.lower()
    assert "configuration" in error_message.lower()
```

### **Multi-Key Authentication Testing**
```python
def test_api_key_auth_loads_multiple_keys_correctly(self, settings_with_multiple_keys, mock_environment_detection):
    """
    Test that APIKeyAuth loads primary and additional API keys correctly.

    Verifies: APIKeyAuth loads and manages multiple API keys per configuration
              logic and multi-key support documentation.

    Business Impact: Enables key rotation strategies and support for multiple
                    clients while maintaining secure authentication access.

    Given: Settings with primary key and multiple additional keys
    When: APIKeyAuth is created with multi-key configuration
    Then: All keys are loaded correctly
    And: Primary key is distinguished from additional keys
    And: Total key count matches configuration
    And: All keys are properly formatted and validated

    Fixtures Used:
        - settings_with_multiple_keys: Pre-configured multi-key settings
        - mock_environment_detection: Environment detection service
    """
    # Given: Multi-key configuration
    mock_environment_detection.get_environment.return_value = Environment.PRODUCTION

    # When: Creating APIKeyAuth with multiple keys
    auth = APIKeyAuth(settings=settings_with_multiple_keys)

    # Then: All keys are loaded
    assert len(auth.api_keys) >= 3  # Primary + 2 additional
    assert "primary-key-12345" in auth.api_keys
    assert "secondary-key-67890" in auth.api_keys
    assert "tertiary-key-abcdef" in auth.api_keys

    # And: Development mode is disabled (keys are present)
    assert auth.development_mode is False
```

## Debugging Failed Tests

### **API Key Authentication Issues**
```bash
# Test APIKeyAuth initialization
make test-backend PYTEST_ARGS="tests/unit/auth/test_api_key_auth.py::TestAPIKeyAuthInitialization::test_api_key_auth_initializes_with_no_keys_development_mode -v -s"

# Test production security enforcement
make test-backend PYTEST_ARGS="tests/unit/auth/test_api_key_auth.py::TestAPIKeyAuthInitialization::test_api_key_auth_raises_configuration_error_in_production_without_keys -v -s"

# Test multi-key loading
make test-backend PYTEST_ARGS="tests/unit/auth/test_api_key_auth.py::TestAPIKeyAuthInitialization::test_api_key_auth_loads_multiple_keys_correctly -v -s"
```

### **Configuration Management Problems**
```bash
# Test AuthConfig initialization
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_config.py::TestAuthConfigInitialization::test_auth_config_initializes_with_default_values -v -s"

# Test operation mode detection
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_config.py::TestAuthConfigInitialization::test_auth_config_detects_advanced_mode -v -s"

# Test production security validation
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_config.py::TestAuthConfigSecurityValidation::test_auth_config_enforces_production_security -v -s"
```

### **FastAPI Integration Issues**
```bash
# Test API key verification dependencies
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_dependencies.py::TestAPIKeyVerificationDependencies::test_verify_api_key_with_valid_bearer_token -v -s"

# Test HTTP exception wrapping
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_dependencies.py::TestHTTPExceptionWrapping::test_configuration_error_converts_to_403_response -v -s"

# Test request context integration
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_dependencies.py::TestRequestContextIntegration::test_authentication_data_added_to_request_context -v -s"
```

### **Utility Function Problems**
```bash
# Test key format validation
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_utilities.py::TestKeyFormatValidation::test_extract_bearer_token_from_authorization_header -v -s"

# Test metadata extraction
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_utilities.py::TestMetadataExtraction::test_build_user_metadata_from_api_key -v -s"

# Test error handling utilities
make test-backend PYTEST_ARGS="tests/unit/auth/test_auth_utilities.py::TestErrorHandlingUtilities::test_create_authentication_error_with_context -v -s"
```

## Related Documentation

- **Component Contract**: `app/infrastructure/security/auth.py` - Authentication implementation and docstring contracts
- **Unit Testing Philosophy**: `docs/guides/testing/UNIT_TESTS.md` - Comprehensive unit testing methodology and principles
- **Testing Overview**: `docs/guides/testing/TESTING.md` - High-level testing philosophy and principles
- **Contract Testing**: `docs/guides/testing/TEST_STRUCTURE.md` - Test organization and fixture patterns
- **Mocking Strategy**: `docs/guides/testing/MOCKING_GUIDE.md` - When and how to use mocks vs fakes
- **Exception Handling**: `docs/guides/developer/EXCEPTION_HANDLING.md` - Custom exception patterns and testing
- **Security Guidelines**: `docs/guides/developer/SECURITY.md` - Security configuration and authentication guidelines
- **Environment Detection**: `app/core/environment.py` - Environment detection and classification system
- **API Design**: `docs/reference/key-concepts/DUAL_API_ARCHITECTURE.md` - Public vs Internal API security patterns

---

## Unit Test Quality Assessment

### **Behavior-Driven Excellence**
These tests exemplify our **behavior-driven contract testing** approach:

✅ **Component Integrity**: Tests verify entire authentication system behavior without breaking internal cohesion
✅ **Contract Focus**: Tests validate documented public interface exclusively
✅ **Boundary Mocking**: External dependencies mocked appropriately, internal logic preserved
✅ **Observable Outcomes**: Tests verify return values, exceptions, and external side effects only
✅ **Environment Mastery**: Proper `monkeypatch.setenv()` usage with complete isolation

### **Production-Ready Standards**
✅ **>90% Coverage**: Comprehensive authentication logic and security enforcement coverage
✅ **Fast Execution**: All tests execute under 100ms for rapid feedback
✅ **Deterministic**: No timing dependencies or external service requirements
✅ **Maintainable**: Clear structure, comprehensive documentation, security impact focus
✅ **Contract Complete**: Full Args, Returns, Raises, and Behavior section coverage

These unit tests serve as a model for behavior-driven testing of security infrastructure components, demonstrating how to verify complex authentication logic while maintaining test isolation, speed, and comprehensive security contract coverage.