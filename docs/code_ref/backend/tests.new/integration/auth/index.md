# Authentication Integration Tests

This directory contains comprehensive integration tests for the environment-aware authentication security system (`app.infrastructure.security.auth`). These tests validate the integration between authentication components, environment detection, FastAPI dependency injection, and HTTP handling.

## Overview

The authentication system serves as a critical security foundation that affects all protected endpoints. These integration tests ensure reliable collaboration between:

- **Environment Detection Integration** - Authentication security policies driven by environment detection
- **Exception Handling Integration** - Custom exceptions with HTTP conversion and context preservation
- **FastAPI Dependency Integration** - Multiple authentication dependencies for different use cases
- **API Endpoint Integration** - Authentication status endpoint demonstrating complete flow
- **Configuration Integration** - Environment variable-based security configuration

## Test Organization

### HIGH PRIORITY Tests (Security Critical)

1. **`test_environment_security.py`** - Environment-aware security enforcement integration
   - Tests production security requirements
   - Validates development mode bypass
   - Verifies environment detection fallback behavior
   - ⚠️ Some tests marked `no_parallel` for environment isolation

2. **`test_http_exception_handling.py`** - HTTP exception conversion and middleware compatibility
   - Tests HTTP 401 response formatting
   - Validates error context preservation
   - Ensures middleware compatibility

3. **`test_dependency_injection.py`** - FastAPI dependency injection integration
   - Tests secure route protection
   - Validates authentication metadata injection
   - Ensures concurrent request handling
   - ⚠️ Most tests marked `no_parallel` for environment isolation

4. **`test_error_context.py`** - Authentication error context and debugging
   - Tests error context preservation
   - Validates debugging information inclusion
   - Ensures security monitoring support

### MEDIUM PRIORITY Tests (Functionality & Operations)

5. **`test_authentication_features.py`** - Multi-key authentication with environment configuration
   - Tests multi-key authentication support
   - Validates configuration management
   - Ensures feature flag functionality

6. **`test_status_api.py`** - Authentication status API integration
   - Tests public API authentication validation
   - Validates environment-aware responses
   - Ensures proper error response formatting

7. **`test_programmatic_auth.py`** - Programmatic authentication integration
   - Tests non-HTTP authentication scenarios
   - Validates background task authentication
   - Ensures thread-safe programmatic access

8. **`test_system_monitoring.py`** - Authentication system status and monitoring
   - Tests operational visibility
   - Validates monitoring endpoint functionality
   - Ensures status information accuracy
   - ⚠️ Some tests marked `no_parallel` for environment isolation

9. **`test_concurrency.py`** - Authentication thread safety and performance
   - Tests concurrent request handling
   - Validates thread safety
   - Ensures performance under load
   - ⚠️ Some tests marked `no_parallel` for environment isolation

## Test Fixtures

The `conftest.py` file provides comprehensive fixtures for different testing scenarios:

- **Environment Configuration**: Development, production, staging environments
- **Authentication Setup**: Single key, multiple keys, advanced configuration
- **Mock Services**: Environment detection mocking, failure simulation
- **HTTP Clients**: Valid/invalid authentication headers, malformed requests

## Key Integration Seams Tested

| Seam | Components Involved | Critical Path | Priority |
|------|-------------------|---------------|----------|
| **Environment-Aware Security Enforcement** | `APIKeyAuth` → `EnvironmentDetector` → `AuthConfig` | Environment detection → Security policy → Authentication enforcement | HIGH |
| **HTTP Exception Conversion** | `verify_api_key_http` → `AuthenticationError` → `HTTPException` | Exception raising → HTTP conversion → Response formatting | HIGH |
| **FastAPI Dependency Injection** | `Depends(verify_api_key_http)` → Authentication validation → Route access | Dependency resolution → Auth validation → Endpoint execution | HIGH |
| **Multi-Key Authentication** | `APIKeyAuth` → `AuthConfig` → Environment variables | Key loading → Validation → Access control | MEDIUM |
| **Authentication Status API** | `/v1/auth/status` → `verify_api_key_http` → `EnvironmentDetector` | HTTP request → Auth validation → Environment-aware response | MEDIUM |
| **Programmatic Authentication** | `verify_api_key_string` → `APIKeyAuth` → Environment detection | String validation → Auth system → Environment-based behavior | MEDIUM |

## Running the Tests

### Standard Execution
```bash
# Run all authentication integration tests
pytest backend/tests/integration/auth/ -v

# Run specific test file
pytest backend/tests/integration/auth/test_environment_security.py -v

# Run with coverage
pytest backend/tests/integration/auth/ --cov=app.infrastructure.security.auth --cov-report=term-missing

# Run tests matching specific pattern
pytest backend/tests/integration/auth/ -k "test_http_exception" -v
```

### Test Isolation Requirements

**⚠️ Important**: Due to test isolation requirements, some tests need special execution to avoid intermittent failures:

#### Option 1: Sequential Execution (Recommended)
```bash
# Run tests requiring isolation first
pytest backend/tests/integration/auth/ -m "no_parallel" --tb=no -q

# Then run remaining tests
pytest backend/tests/integration/auth/ -m "not no_parallel" --tb=no -q
```

#### Option 2: Using Markers
```bash
# Run only tests marked for parallel execution
pytest backend/tests/integration/auth/ -m "not no_parallel" --tb=no -q

# Run only tests requiring sequential execution
pytest backend/tests/integration/auth/ -m "no_parallel" --tb=no -q
```

### Test Markers

- **`no_parallel`**: Tests that require sequential execution due to environment isolation needs
- **`integration`**: Standard integration tests that can run in parallel
- **`slow`**: Performance or load tests (excluded by default)

**Tests marked with `no_parallel`** need specific environment conditions (like no API keys or specific API keys) and can be affected by global state changes from other tests. These should be run first or separately for reliable results.

### Troubleshooting

#### Intermittent Failures
If you encounter intermittent test failures:

1. **Run tests with proper isolation**:
   ```bash
   # Option 1: Sequential execution
   pytest backend/tests/integration/auth/ -m "no_parallel" --tb=no -q
   pytest backend/tests/integration/auth/ -m "not no_parallel" --tb=no -q

   # Option 2: Disable parallel execution entirely
   pytest backend/tests/integration/auth/ -n 0 --tb=no -q
   ```

2. **Check test isolation**: Tests marked `no_parallel` need specific environment conditions and should run before other tests that might modify global state.

3. **Verify environment variables**: Some tests may be affected by environment variables set in other tests. The `no_parallel` tests create isolated environments.

## Success Criteria

The test suite ensures:

- **Security**: All critical security enforcement paths validated (>90% coverage)
- **Compatibility**: HTTP exception conversion and middleware integration verified
- **Reliability**: Authentication system works consistently across environments
- **Performance**: Authentication completes efficiently under normal conditions
- **Robustness**: System handles authentication failures and edge cases gracefully
- **Monitoring**: Comprehensive operational visibility and debugging capabilities

## Integration with Infrastructure

These tests validate the authentication system's integration with:

- **Environment Detection Service** - Unified environment detection for security policies
- **Exception Handling System** - Custom exceptions with HTTP status mapping
- **FastAPI Framework** - Dependency injection and middleware compatibility
- **Configuration Management** - Environment variable-based security configuration
- **Logging System** - Structured logging for security monitoring

## Behavioral Testing Approach

Following the project's behavioral testing philosophy, these tests:

- **Focus on observable behavior** rather than implementation details
- **Test from the outside-in** starting from API endpoints and public interfaces
- **Validate integration seams** between components rather than internal logic
- **Use high-fidelity test infrastructure** (FastAPI test client, real environment variables)
- **Document business impact** and integration scope for each test scenario

This approach ensures the authentication system integrates reliably with all dependent infrastructure components while maintaining security, performance, and operational visibility standards.
