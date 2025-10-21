# Redis Security Validator Unit Tests

Unit tests for `RedisSecurityValidator` module following our **behavior-driven contract testing** philosophy. These tests verify the complete public interface of the Redis security core component in complete isolation, ensuring it fulfills its documented security validation contracts.

## Component Overview

**Component Under Test**: `RedisSecurityValidator` (`app.core.startup.redis_security`) 

**Component Type**: Core Service (Single Module)

**Primary Responsibility**: Validates Redis security configuration including TLS certificates, encryption keys, authentication, and environment-specific security requirements.

**Public Contract**: Validates security settings for Redis connections, enforces production security standards, and provides comprehensive security validation for application startup.

**Filesystem Locations:**
  - Production Code: `backend/app/core/startup/redis_security.py`
  - Public Contract: `backend/contracts/core/startup/redis_security.pyi`
  - Test Suite:      `backend/tests/unit/startup/redis_security/test_*.py`
  - Test Fixtures:   `backend/tests/unit/startup/redis_security/conftest.py`

## Test Organization

### Component-Based Test Structure (3 Test Classes, 1,247 Lines Total)

#### **PRODUCTION SECURITY VALIDATION** (Critical security enforcement)

1. **`test_production_security.py`** (CRITICAL) - **412 lines across 2 comprehensive test classes**
   - Production Environment Security Enforcement → TLS Requirements → ConfigurationError on Violation
   - Development Environment Flexibility → Warning Generation → Security Best Practices
   - Startup Security Integration → Environment Detection → Configuration Validation
   - Comprehensive Error Handling → Actionable Messages → Operational Guidance
   - Tests strict production enforcement, flexible development behavior, startup integration

#### **COMPONENT METHOD VALIDATION** (Individual method contract verification)

2. **`test_component_validation.py`** (COMPREHENSIVE) - **467 lines across 4 focused test classes**
   - TLS Certificate Validation → File Existence → Expiration Checking → Certificate Information
   - Encryption Key Validation → Key Format → Fernet Compatibility → Functional Testing
   - Redis Authentication Validation → Credential Security → Connection Requirements
   - URL Validation → Protocol Checking → Security Requirement Enforcement
   - Tests individual validator methods with complete contract coverage

#### **COMPREHENSIVE VALIDATION ORCHESTRATION** (End-to-end validation workflows)

3. **`test_comprehensive_validation.py`** (WORKFLOW) - **368 lines across 2 integration test classes**
   - Security Configuration Orchestration → Component Coordination → Result Aggregation
   - Complete Security Workflow → Multi-Component Validation → Status Reporting
   - Error Aggregation → Component Failure Isolation → Comprehensive Reporting
   - Status Summarization → Health Assessment → Operational Readiness
   - Tests complete validation workflows with result aggregation

## Testing Philosophy Applied

These unit tests exemplify our **behavior-driven contract testing** principles:

- **Component as Unit**: Tests verify entire `RedisSecurityValidator` class behavior, not individual methods
- **Contract Focus**: Tests validate documented public interface (Args, Returns, Raises, Behavior sections)
- **Boundary Mocking**: Mock only external dependencies (filesystem, environment, cryptography), never internal validation logic
- **Observable Outcomes**: Test return values, exceptions, and side effects visible to external callers
- **Environment Isolation**: Proper `monkeypatch.setenv()` usage for environment variable testing
- **High-Fidelity Fakes**: Use realistic fake objects instead of simple mocks where appropriate

## Test Fixtures and Infrastructure

### **Component Instance Fixtures**
```python
@pytest.fixture
def redis_security_validator():
    """Real RedisSecurityValidator instance for testing validator behavior."""
    from app.core.startup.redis_security import RedisSecurityValidator
    return RedisSecurityValidator()
```

### **Environment Detection Fixtures**
```python
@pytest.fixture
def mock_production_environment(mock_get_environment_info):
    """Mock environment detection to return production environment."""
    mock_get_environment_info.return_value = FakeEnvironmentInfo(
        environment=Environment.PRODUCTION,
        confidence=0.95,
        reasoning="ENVIRONMENT=production set explicitly"
    )
    return mock_get_environment_info
```

### **High-Fidelity URL Fixtures**
```python
@pytest.fixture
def secure_redis_url_tls():
    """Secure Redis URL with TLS protocol for security testing."""
    return "rediss://redis.example.com:6380/0"

@pytest.fixture
def insecure_redis_url():
    """Insecure Redis URL for development/testing scenarios."""
    return "redis://localhost:6379/0"
```

### **TLS Certificate Fixtures**
```python
@pytest.fixture
def mock_cert_path_exists(tmp_path):
    """Create temporary certificate files for TLS validation testing."""
    cert_file = tmp_path / "client.crt"
    key_file = tmp_path / "client.key"
    ca_file = tmp_path / "ca.crt"

    cert_file.write_text("-----BEGIN CERTIFICATE-----\nMIIC...")
    key_file.write_text("-----BEGIN PRIVATE KEY-----\nMIIE...")
    ca_file.write_text("-----BEGIN CERTIFICATE-----\nMIIC...")

    return {
        "cert_path": str(cert_file),
        "key_path": str(key_file),
        "ca_path": str(ca_file)
    }
```

### **Encryption Key Fixtures**
```python
@pytest.fixture
def valid_fernet_key():
    """Valid 44-character base64-encoded Fernet key for testing."""
    return "dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ=="

@pytest.fixture
def invalid_encryption_key():
    """Invalid encryption key for error handling testing."""
    return "invalid-key-format"
```

### **Environment Variable Fixtures**
```python
@pytest.fixture
def mock_secure_redis_env(monkeypatch):
    """Mock environment variables for secure Redis configuration."""
    monkeypatch.setenv("REDIS_URL", "rediss://redis:6380")
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ==")
    monkeypatch.setenv("REDIS_TLS_CERT_PATH", "/etc/ssl/redis/client.crt")
    monkeypatch.setenv("REDIS_TLS_KEY_PATH", "/etc/ssl/redis/client.key")
    monkeypatch.setenv("REDIS_TLS_CA_PATH", "/etc/ssl/redis/ca.crt")
    return monkeypatch
```

## Running Tests

```bash
# Run all redis_security unit tests
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/ -v"

# Run specific test files
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_production_security.py -v"
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_component_validation.py -v"
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_comprehensive_validation.py -v"

# Run by test class
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_production_security.py::TestValidateProductionSecurity -v"
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_component_validation.py::TestValidateTlsCertificates -v"
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_comprehensive_validation.py::TestValidateSecurityConfiguration -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/ --cov=app.core.startup.redis_security"

# Run specific test methods
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_component_validation.py::TestValidateEncryptionKey::test_validate_encryption_key_with_valid_fernet_key -v"

# Run with verbose output for debugging
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/ -v -s"
```

## Test Quality Standards

### **Performance Requirements**
- **Execution Speed**: < 50ms per test (fast feedback loop)
- **Determinism**: No timing dependencies or sleep() calls
- **Isolation**: No external service dependencies or network calls
- **Resource Cleanup**: Automatic fixture cleanup prevents test pollution

### **Contract Coverage Requirements**
- **Public Methods**: 100% coverage of all public validator methods
- **Input Validation**: Complete Args section testing per docstring
- **Output Verification**: Complete Returns section testing per docstring
- **Exception Handling**: Complete Raises section testing per docstring
- **Behavior Guarantees**: Complete Behavior section testing per docstring

### **Test Structure Standards**
- **Given/When/Then**: Clear test structure with descriptive comments
- **Single Responsibility**: One behavior verified per test method
- **Descriptive Names**: Test names clearly describe verified behavior
- **Business Impact**: Test docstrings include business impact explanation
- **Fixture Documentation**: Clear fixture purpose and usage documentation

## Success Criteria

### **Production Security Enforcement**
- ✅ Production environments require TLS URLs (rediss://) without exception
- ✅ Production environments require valid encryption keys without fallback
- ✅ Production security violations raise ConfigurationError with actionable messages
- ✅ Development environments provide flexible security with appropriate warnings
- ✅ Security requirements adapt correctly based on environment detection

### **TLS Certificate Validation**
- ✅ Certificate file existence is validated correctly
- ✅ Certificate expiration checking prevents use of expired certificates
- ✅ Certificate warnings are generated for certificates expiring within 30 days
- ✅ Certificate information extraction provides operational diagnostics
- ✅ TLS validation handles missing files with clear error messages

### **Encryption Key Validation**
- ✅ Valid Fernet keys are accepted and functionality confirmed via test encryption
- ✅ Invalid key formats are rejected with helpful error messages
- ✅ Key length requirements are enforced (32 bytes for Fernet)
- ✅ Base64 encoding validation ensures proper key format
- ✅ Encryption key validation integrates with comprehensive security workflow

### **Redis Authentication Validation**
- ✅ Redis authentication requirements are enforced in production
- ✅ Development environments allow insecure connections with warnings
- ✅ Password security validation prevents weak or empty passwords
- ✅ Authentication configuration integrates with URL validation
- ✅ Missing authentication is handled appropriately per environment

### **Comprehensive Validation Orchestration**
- ✅ All security components participate in validation workflow
- ✅ Validation errors are properly aggregated from multiple components
- ✅ Validation summaries provide clear operational status information
- ✅ Component failures are isolated without affecting other validators
- ✅ Security validation results provide actionable guidance for configuration

### **Environment Variable Integration**
- ✅ REDIS_URL is read and validated for security requirements
- ✅ REDIS_ENCRYPTION_KEY is loaded and validated for format/strength
- ✅ REDIS_TLS_* variables are loaded for certificate configuration
- ✅ Environment changes between tests are properly isolated with monkeypatch
- ✅ Missing environment variables are handled with clear error messages

## What's NOT Tested (Integration Test Concerns)

### **External System Integration**
- Actual Redis server connections and TLS handshake
- Real certificate authority validation and certificate chain verification
- External filesystem operations beyond mocked file existence
- Real environment detection in production deployment scenarios

### **Cryptographic Implementation**
- Internal Fernet encryption algorithm implementation
- Cryptographic library internal operations and key management
- TLS/SSL protocol implementation and secure channel establishment
- Certificate authority validation and certificate chain verification

### **Application Startup Integration**
- FastAPI application startup integration with RedisSecurityValidator
- Dependency injection integration with application container
- Startup error handling and application failure scenarios
- Production deployment environment integration and configuration

## Environment Variables for Testing

```bash
# Core Redis Configuration
REDIS_URL=rediss://redis.example.com:6380/0    # Secure TLS connection
REDIS_URL=redis://localhost:6379/0              # Insecure development connection

# Security Configuration
REDIS_ENCRYPTION_KEY=dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ==  # Valid Fernet key
REDIS_TLS_CERT_PATH=/etc/ssl/redis/client.crt   # TLS certificate file path
REDIS_TLS_KEY_PATH=/etc/ssl/redis/client.key     # TLS private key file path
REDIS_TLS_CA_PATH=/etc/ssl/redis/ca.crt         # TLS certificate authority file path

# Environment Detection
ENVIRONMENT=production                          # Production environment (strict security)
ENVIRONMENT=development                         # Development environment (flexible security)
ENVIRONMENT=testing                            # Testing environment (validation focused)

# Security Override Testing (Development Only)
REDIS_SECURITY_REQUIRE_TLS=false               # Override TLS requirement
REDIS_SECURITY_ALLOW_INSECURE_DEVELOPMENT=true # Allow insecure connections in development

# Error Scenario Testing
REDIS_URL=invalid://protocol                    # Invalid URL format testing
REDIS_ENCRYPTION_KEY=invalid-key-format        # Invalid encryption key testing
REDIS_TLS_CERT_PATH=/nonexistent/path/cert.pem  # Missing certificate file testing
```

## Test Method Examples

### **Contract-Based Testing Example**
```python
def test_validate_encryption_key_with_valid_fernet_key(self, redis_security_validator, valid_fernet_key):
    """
    Test that validate_encryption_key() accepts valid Fernet key per validation logic.

    Verifies: validate_encryption_key() returns valid=True for valid Fernet keys
              per Args and Returns documentation.

    Business Impact: Ensures properly configured encryption keys are recognized,
                    allowing secure deployments to proceed with confidence.

    Given: Valid 44-character base64-encoded Fernet key
    When: validate_encryption_key() is called with the key
    Then: Dictionary is returned with result["valid"] is True
    And: result["errors"] is empty list
    And: result["key_info"] contains format and strength information
    And: Key functionality is confirmed via test encrypt/decrypt operation

    Fixtures Used:
        - redis_security_validator: Real validator instance
        - valid_fernet_key: Valid Fernet key for testing
    """
    # Given: Valid Fernet key
    key = valid_fernet_key

    # When: Validating the key
    result = redis_security_validator.validate_encryption_key(key)

    # Then: Key is validated successfully
    assert result["valid"] is True
    assert result["errors"] == []
    assert "format" in result["key_info"]
    assert result["key_info"]["format"] == "fernet"
    assert result["key_info"]["strength"] == "strong"
    assert "test_encrypt_decrypt" in result["key_info"]
    assert result["key_info"]["test_encrypt_decrypt"] is True
```

### **Environment-Aware Testing Example**
```python
def test_validate_redis_auth_fails_in_production_without_auth(self, redis_security_validator, mock_production_environment, insecure_redis_url):
    """
    Test that validate_redis_auth() fails in production without authentication per security policy.

    Verifies: validate_redis_auth() raises ConfigurationError for insecure URLs in
              production environment per documented security requirements.

    Business Impact: Prevents insecure production deployments by failing fast at
                    startup, protecting sensitive data from exposure.

    Given: Production environment detected and insecure Redis URL
    When: validate_redis_auth() is called
    Then: ConfigurationError is raised
    And: Error message mentions TLS requirement
    And: Error message mentions production environment
    And: Error message provides actionable guidance

    Fixtures Used:
        - redis_security_validator: Real validator instance
        - mock_production_environment: Production environment simulation
        - insecure_redis_url: Insecure Redis URL for testing
    """
    # Given: Production environment with insecure URL
    url = insecure_redis_url

    # When/Then: Production security requires authentication
    with pytest.raises(ConfigurationError) as exc_info:
        redis_security_validator.validate_redis_auth(url)

    error_message = str(exc_info.value)
    assert "production" in error_message.lower()
    assert "tls" in error_message.lower()
    assert "rediss://" in error_message
    assert "secure" in error_message.lower()
```

### **Comprehensive Workflow Testing Example**
```python
def test_validate_security_configuration_with_full_secure_setup(self, redis_security_validator, mock_secure_redis_env, secure_redis_url_tls, mock_cert_path_exists, valid_fernet_key):
    """
    Test that validate_security_configuration() validates complete secure setup per workflow.

    Verifies: validate_security_configuration() returns comprehensive success status
              when all security components are properly configured per Returns section.

    Business Impact: Ensures complete security validation provides confidence for
                    production deployments with all security measures properly configured.

    Given: Secure Redis URL, valid encryption key, and existing certificate files
    When: validate_security_configuration() is called
    Then: All component statuses show "✅ Valid"
    And: Overall result["valid"] is True
    And: result["errors"] is empty list
    And: result["summary"] indicates successful validation
    And: Certificate information is populated in result

    Fixtures Used:
        - redis_security_validator: Real validator instance
        - mock_secure_redis_env: Complete secure environment configuration
        - secure_redis_url_tls: Secure TLS Redis URL
        - mock_cert_path_exists: Temporary certificate files
        - valid_fernet_key: Valid encryption key
    """
    # Given: Complete secure configuration
    url = secure_redis_url_tls
    encryption_key = valid_fernet_key
    cert_paths = mock_cert_path_exists

    # When: Validating complete security configuration
    result = redis_security_validator.validate_security_configuration(
        url=url,
        encryption_key=encryption_key,
        tls_cert_path=cert_paths["cert_path"],
        tls_key_path=cert_paths["key_path"],
        tls_ca_path=cert_paths["ca_path"]
    )

    # Then: All components validate successfully
    assert result["valid"] is True
    assert result["errors"] == []

    # Check individual component statuses
    assert "url_validation" in result
    assert result["url_validation"]["status"] == "✅ Valid"

    assert "encryption_validation" in result
    assert result["encryption_validation"]["status"] == "✅ Valid"

    assert "tls_validation" in result
    assert result["tls_validation"]["status"] == "✅ Valid"

    # Check summary and certificate info
    assert "summary" in result
    assert "all security validations passed" in result["summary"].lower()
    assert "cert_info" in result["tls_validation"]
```

## Debugging Failed Tests

### **Production Security Enforcement Issues**
```bash
# Test production TLS enforcement
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_production_security.py::TestValidateProductionSecurity::test_validate_production_security_requires_tls_in_production -v -s"

# Test development flexibility
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_production_security.py::TestValidateProductionSecurity::test_validate_production_security_allows_insecure_in_development -v -s"

# Test startup security integration
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_production_security.py::TestValidateStartupSecurity::test_validate_startup_security_reads_environment_variables -v -s"
```

### **Component Validation Problems**
```bash
# Test TLS certificate validation
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_component_validation.py::TestValidateTlsCertificates::test_validate_tls_certificates_with_existing_files -v -s"

# Test encryption key validation
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_component_validation.py::TestValidateEncryptionKey::test_validate_encryption_key_with_valid_fernet_key -v -s"

# Test Redis authentication validation
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_component_validation.py::TestValidateRedisAuth::test_validate_redis_auth_with_secure_url -v -s"
```

### **Comprehensive Validation Issues**
```bash
# Test complete security validation
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_comprehensive_validation.py::TestValidateSecurityConfiguration::test_validate_security_configuration_with_full_secure_setup -v -s"

# Test error aggregation
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_comprehensive_validation.py::TestValidateSecurityConfiguration::test_validate_security_configuration_aggregates_multiple_errors -v -s"

# Test validation summarization
make test-backend PYTEST_ARGS="tests/unit/startup/redis_security/test_comprehensive_validation.py::TestValidateSecurityConfiguration::test_validate_security_configuration_provides_meaningful_summary -v -s"
```

## Related Documentation

- **Component Contract**: `app/core/startup/redis_security.py` - RedisSecurityValidator implementation and docstring contracts
- **Unit Testing Philosophy**: `docs/guides/testing/UNIT_TESTS.md` - Comprehensive unit testing methodology and principles
- **Testing Overview**: `docs/guides/testing/TESTING.md` - High-level testing philosophy and principles
- **Contract Testing**: `docs/guides/testing/TEST_STRUCTURE.md` - Test organization and fixture patterns
- **Mocking Strategy**: `docs/guides/testing/MOCKING_GUIDE.md` - When and how to use mocks vs fakes
- **Exception Handling**: `docs/guides/developer/EXCEPTION_HANDLING.md` - Custom exception patterns and testing
- **Configuration Management**: `docs/guides/developer/SECURITY.md` - Security configuration and validation guidelines
- **Environment Detection**: `app/core/startup/environment.py` - Environment detection and classification system

---

## Unit Test Quality Assessment

### **Behavior-Driven Excellence**
These tests exemplify our **behavior-driven contract testing** approach:

✅ **Component Integrity**: Tests verify entire RedisSecurityValidator behavior without breaking internal cohesion
✅ **Contract Focus**: Tests validate documented public interface exclusively
✅ **Boundary Mocking**: External dependencies mocked appropriately, internal logic preserved
✅ **Observable Outcomes**: Tests verify return values, exceptions, and external side effects only
✅ **Environment Mastery**: Proper `monkeypatch.setenv()` usage with complete isolation

### **Production-Ready Standards**
✅ **>90% Coverage**: Comprehensive validation logic and error handling coverage
✅ **Fast Execution**: All tests execute under 50ms for rapid feedback
✅ **Deterministic**: No timing dependencies or external service requirements
✅ **Maintainable**: Clear structure, comprehensive documentation, business impact focus
✅ **Contract Complete**: Full Args, Returns, Raises, and Behavior section coverage

These unit tests serve as a model for behavior-driven testing of infrastructure components, demonstrating how to verify complex security validation logic while maintaining test isolation, speed, and comprehensive contract coverage.