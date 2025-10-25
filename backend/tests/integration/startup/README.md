# Startup Integration Tests

Integration tests for comprehensive system startup validation following our **small, dense suite with maximum confidence** philosophy. These tests validate the complete chain from environment detection through security configuration, certificate validation, encryption requirements, and authentication flows across all startup-critical infrastructure components.

## Test Organization

### Critical Integration Seams (28 Tests Total)

#### **ENVIRONMENT-AWARE SECURITY** (Foundation for startup validation)

1. **`test_environment_aware_security.py`** (FOUNDATION) - **11 tests across 4 comprehensive test classes**
   - Environment detection → Security configuration enforcement
   - RedisSecurityValidator → get_environment_info() → Security Rule Application
   - Comprehensive production error message validation with all fix options
   - Infrastructure security checklist validation for insecure overrides
   - Complete staging environment security validation flow
   - Staging environment informational messaging and security awareness
   - Tests production TLS requirements, development flexibility, staging behaviors, override mechanisms

#### **COMPREHENSIVE VALIDATION** (Core system functionality)

2. **`test_security_validation_integration.py`** (HIGHEST PRIORITY)
   - Complete security validation orchestration and result aggregation
   - validate_security_configuration() → Component validators → Result aggregation
   - Tests multi-component validation, error aggregation, summary generation

#### **AUTHENTICATION VALIDATION** (Security infrastructure)

3. **`test_authentication_validation.py`** (HIGH PRIORITY)
   - API key authentication configuration and validation
   - Redis authentication security requirements
   - Tests API key format validation, Redis auth enforcement, credential security

#### **CERTIFICATE VALIDATION** (Infrastructure security)

4. **`test_certificate_validation.py`** (HIGH PRIORITY)
   - TLS certificate validation and security verification
   - Certificate file validation, expiration checking, path resolution
   - Tests certificate file security, business rules, error handling

#### **ENCRYPTION KEY VALIDATION** (Data security)

5. **`test_encryption_key_validation.py`** (HIGH PRIORITY)
   - Encryption key validation and security requirements
   - Key format validation, strength verification, security compliance
   - Tests key generation, validation, business logic requirements

#### **CRYPTOGRAPHY UNAVAILABLE HANDLING** (Graceful degradation)

6. **`test_cache_encryption_cryptography_unavailable.py`** (SPECIALIZED)
   - Cache encryption graceful degradation when cryptography library unavailable
   - Docker-based tests in isolated environment without cryptography dependency
   - **Special Handling**: Requires Docker execution via `make test-no-cryptography`

7. **`test_redis_security_cryptography_unavailable.py`** (SPECIALIZED)
   - Redis security validation graceful degradation without cryptography library
   - Docker-based tests for certificate validation, encryption key validation limitations
   - **Special Handling**: Requires Docker execution via `make test-no-cryptography`

## Testing Philosophy Applied

- **Outside-In Testing**: All tests start from public interfaces and validate observable system behavior
- **High-Fidelity Infrastructure**: Real validation functions, actual security checks, live component integration
- **Behavior Focus**: Security validation responses, error messages, configuration enforcement, not internal validation logic
- **No Internal Mocking**: Tests real security validation collaboration across all infrastructure components
- **Contract Validation**: Ensures compliance with security validation contracts across all startup scenarios
- **Docker-Based Isolation**: Special tests use Docker to test actual library unavailability scenarios

## Cryptography Unavailable Tests - Special Handling

**Two test files require special Docker-based execution** to validate graceful degradation when the `cryptography` library is unavailable:

### Why Docker-Based Testing?
- **Import-Time Dependencies**: Cryptography imports at module load time, before test fixtures can intercept
- **Mocking Limitations**: Unit-level mocking of `builtins.__import__` causes pytest internal errors
- **True Isolation**: Docker provides actual missing library environment, not simulated

### Test Files Requiring Docker:
1. **`test_cache_encryption_cryptography_unavailable.py`** (393 lines)
   - Cache encryption initialization failure handling
   - Error message quality and actionable guidance
   - ConfigurationError with installation instructions

2. **`test_redis_security_cryptography_unavailable.py`** (479 lines)
   - TLS certificate validation graceful degradation
   - Encryption key validation limitations
   - Comprehensive validation with cryptography warnings

### Execution Methods:
```bash
# Recommended: Make command with colored output
make test-no-cryptography

# Direct shell script execution
./backend/tests/integration/docker/run-no-cryptography-tests.sh

# Manual Docker execution
docker build -f backend/tests/integration/docker/Dockerfile.no-cryptography -t no-crypto-tests .
docker run --rm no-crypto-tests
```

**Reference**: `backend/tests/integration/startup/CRYPTOGRAPHY_UNAVAILABLE_IMPLEMENTATION.md` for comprehensive implementation details, Docker configuration, and troubleshooting guide.

## Running Tests

```bash
# Run all startup integration tests
make test-backend PYTEST_ARGS="tests/integration/startup/ -v"

# Run by test category
make test-backend PYTEST_ARGS="tests/integration/startup/ -v -k 'environment'"
make test-backend PYTEST_ARGS="tests/integration/startup/ -v -k 'comprehensive'"
make test-backend PYTEST_ARGS="tests/integration/startup/ -v -k 'auth'"
make test-backend PYTEST_ARGS="tests/integration/startup/ -v -k 'certificate'"
make test-backend PYTEST_ARGS="tests/integration/startup/ -v -k 'encryption'"

# Run specific test classes
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestComprehensiveProductionErrorMessages -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestInsecureOverrideWarningContent -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestStagingEnvironmentSecurityValidation -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestStagingEnvironmentInformationalMessaging -v"

# Run specific test file
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_security_validation_integration.py -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_authentication_validation.py -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_certificate_validation.py -v"
make test-backend PYTEST_ARGS="tests/integration/startup/test_encryption_key_validation.py -v"

# Run cryptography unavailable tests (Docker-based)
make test-no-cryptography

# Run with coverage
make test-backend PYTEST_ARGS="tests/integration/startup/ --cov=app.core.startup"

# Run performance-focused validation tests
make test-backend PYTEST_ARGS="tests/integration/startup/test_security_validation_integration.py::test_comprehensive_validation_with_all_components_passing -v"
```

## Test Fixtures

### API and HTTP Infrastructure
- **`monkeypatch`**: Environment variable manipulation for configuration testing
- **`tmp_path`**: Temporary file system paths for certificate and key testing
- **`security_validator`**: Real RedisSecurityValidator instance with complete configuration

### Configuration Management
- **`production_environment`**: Production environment configuration for security testing
- **`development_environment`**: Development environment with flexible security rules
- **`security_config`**: Complete security configuration for comprehensive validation

### Security and Validation
- **`certificate_files`**: TLS certificate files for validation testing (valid, expired, self-signed)
- **`encryption_keys`**: Various encryption key formats for validation testing
- **`api_keys`**: API key configurations for authentication validation

### Docker Infrastructure (Cryptography Tests)
- **`no_cryptography_environment`**: Docker container without cryptography library
- **`isolated_python_environment`**: True isolation for library unavailability testing

## Success Criteria

### **Environment-Aware Security Validation**
- ✅ Production environments enforce TLS requirements for Redis connections
- ✅ Development environments provide flexible security rules for local testing
- ✅ Staging environments provide flexible security rules with appropriate messaging
- ✅ Override mechanisms generate appropriate warnings while allowing security bypasses
- ✅ Production security errors include comprehensive fix options with code examples
- ✅ Override warnings include complete infrastructure security checklist
- ✅ Staging environment logs informational messages about security flexibility
- ✅ Environment detection accurately identifies deployment context (production, staging, development)
- ✅ Security rule application adapts based on environment classification
- ✅ Behavioral validation demonstrates environment-specific security enforcement

### **Comprehensive Security Validation**
- ✅ All security components (TLS, encryption, authentication) participate in validation
- ✅ Validation errors are properly aggregated from multiple components
- ✅ Validation summaries provide clear, actionable security status information
- ✅ SecurityValidationResult structure enables programmatic security decisions
- ✅ Multi-component failures generate comprehensive error reports

### **Authentication Validation**
- ✅ API key format validation enforces proper key structure and requirements
- ✅ Redis authentication security requirements are enforced in production
- ✅ Invalid authentication configurations generate appropriate security errors
- ✅ Credential security validation prevents weak or compromised authentication
- ✅ Authentication validation integrates with comprehensive security orchestration

### **Certificate Validation**
- ✅ TLS certificate file validation confirms file existence and readability
- ✅ Certificate expiration checking prevents use of expired security certificates
- ✅ Certificate path resolution handles absolute and relative path configurations
- ✅ Certificate security validation enforces business rules for certificate usage
- ✅ Certificate validation errors provide clear diagnostic information

### **Encryption Key Validation**
- ✅ Encryption key format validation confirms proper key structure and encoding
- ✅ Key strength verification enforces minimum security requirements
- ✅ Key validation integrates with comprehensive security orchestration
- ✅ Invalid encryption keys generate appropriate security validation errors
- ✅ Key generation and validation follow established security standards

### **Cryptography Unavailable Graceful Degradation**
- ✅ Cache encryption initialization fails with helpful ConfigurationError messages
- ✅ Error messages include actionable installation commands ("pip install cryptography")
- ✅ Business impact explanations help users understand why cryptography is required
- ✅ TLS certificate validation gracefully degrades with warnings when cryptography unavailable
- ✅ Basic validation (file existence, key length) continues to work without cryptography
- ✅ Comprehensive validation includes cryptography availability warnings in results

### **Error Handling and Security Resilience**
- ✅ Invalid security configurations result in appropriate ValidationError responses
- ✅ Security validation continues operational during individual component failures
- ✅ Component validation failures are isolated and don't affect other security components
- ✅ System provides descriptive error messages for security troubleshooting
- ✅ Security validation maintains system security posture during partial failures

## What's NOT Tested (Unit Test Concerns)

### **Internal Security Validation Implementation**
- Individual security check algorithms and cryptographic operations
- Internal timeout handling and retry mechanisms within security validators
- Private method behavior in individual security validation functions
- Specific cryptographic library integration and error handling

### **Environment Detection Internal State**
- Internal environment detection registry management
- Environment classification algorithms and heuristics
- Internal security rule matching and application logic
- Concurrent environment detection and caching mechanisms

### **Security-Specific Infrastructure**
- Cryptographic library internal operations and key management
- Certificate authority validation and certificate chain verification
- Redis connection pooling and authentication mechanisms
- TLS/SSL handshake and secure channel establishment

### **Docker Container Internal Operations**
- Docker container internal networking and file system operations
- Container build process and dependency installation
- Container runtime environment and Python interpreter configuration

## Environment Variables for Testing

```bash
# Production Environment Configuration
ENVIRONMENT=production
REDIS_URL=rediss://localhost:6379  # TLS required in production
API_KEY=test-production-api-key-12345

# Development Environment Configuration
ENVIRONMENT=development
REDIS_URL=redis://localhost:6379   # Non-TLS allowed in development
API_KEY=test-dev-api-key-67890

# Security Override Testing
REDIS_SECURITY_REQUIRE_TLS=false
REDIS_SECURITY_ALLOW_INSECURE_DEVELOPMENT=true

# Certificate Validation Testing
REDIS_TLS_CERT_PATH=/path/to/certificate.pem
REDIS_TLS_KEY_PATH=/path/to/private.key

# Encryption Key Testing
REDIS_ENCRYPTION_KEY=test-encryption-key-32-chars-long

# Complex Security Failure Scenarios
REDIS_URL=invalid://protocol
API_KEY=invalid-format
REDIS_TLS_CERT_PATH=/nonexistent/path/cert.pem

# Cryptography Unavailable Testing (Docker)
# CRYPTOGRAPHY_LIBRARY=unavailable  # Simulated via Docker container
```

## Integration Points Tested

### **Environment-Aware Security Seam**
- Environment Detection → Security Configuration → Rule Enforcement
- Production vs Development security requirement application
- Override mechanism handling with appropriate warning generation

### **Comprehensive Validation Seam**
- validate_security_configuration() → Component Validators → Result Aggregation
- Multi-component validation orchestration and error collection
- SecurityValidationResult structure and summary generation

### **Authentication Security Seam**
- API Key Validation → Format Enforcement → Security Requirements
- Redis Authentication Security → Credential Validation → Connection Security
- Authentication integration with comprehensive security validation

### **Certificate Validation Seam**
- TLS Certificate Validation → File Verification → Security Enforcement
- Certificate Expiration Checking → Business Rule Application → Security Decisions
- Certificate Path Resolution → File System Integration → Validation Results

### **Encryption Key Validation Seam**
- Encryption Key Validation → Format Verification → Security Requirements
- Key Strength Assessment → Security Standard Enforcement → Validation Results
- Key integration with comprehensive security validation orchestration

### **Cryptography Unavailable Seam**
- Library Import Failure → Graceful Degradation → Helpful Error Messages
- Component Functionality Limitation → Warning Generation → User Guidance
- Validation Continuation → Basic Functionality Preservation → Limitation Communication

### **Configuration and Environment Seam**
- Environment Variables → Security Configuration → Validation Behavior
- Configuration validation and error handling across all security components
- Security requirement adaptation based on deployment environment

## Performance Expectations

- **Environment Detection**: <50ms for environment classification and security rule determination
- **Comprehensive Validation**: <200ms for complete security validation across all components
- **Individual Component Validation**: <100ms per component security validation (TLS, encryption, auth)
- **Certificate Validation**: <150ms for certificate file validation and security checking
- **Encryption Key Validation**: <50ms for key format and strength validation
- **Cryptography Unavailable Handling**: <100ms for graceful degradation and error generation
- **Error Handling**: <100ms for security validation failures and error aggregation

## Debugging Failed Tests

### **Environment-Aware Security Issues**
```bash
# Test production security enforcement
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestEnvironmentAwareSecurityValidation::test_production_environment_rejects_insecure_redis_url -v -s"

# Test development flexibility
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestEnvironmentAwareSecurityValidation::test_development_environment_allows_insecure_redis_url_with_warning -v -s"

# Test comprehensive production error messages
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestComprehensiveProductionErrorMessages::test_production_error_includes_all_fix_options -v -s"

# Test insecure override warnings
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestInsecureOverrideWarningContent::test_production_override_warning_includes_security_checklist -v -s"

# Test staging environment security validation
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestStagingEnvironmentSecurityValidation::test_staging_environment_bypasses_tls_enforcement -v -s"

# Test staging environment informational messaging
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::TestStagingEnvironmentInformationalMessaging::test_staging_environment_logs_informational_message -v -s"
```

### **Comprehensive Validation Problems**
```bash
# Test all components passing validation
make test-backend PYTEST_ARGS="tests/integration/startup/test_security_validation_integration.py::TestComprehensiveSecurityValidation::test_comprehensive_validation_with_all_components_passing -v -s"

# Test multi-component failure aggregation
make test-backend PYTEST_ARGS="tests/integration/startup/test_security_validation_integration.py::TestComprehensiveSecurityValidation::test_comprehensive_validation_aggregates_multiple_component_failures -v -s"
```

### **Authentication Validation Failures**
```bash
# Test API key validation
make test-backend PYTEST_ARGS="tests/integration/startup/test_authentication_validation.py -v -s"

# Verify Redis authentication security
make test-backend PYTEST_ARGS="tests/integration/startup/test_authentication_validation.py -v -k 'redis_auth'"
```

### **Certificate Validation Issues**
```bash
# Test certificate file validation
make test-backend PYTEST_ARGS="tests/integration/startup/test_certificate_validation.py -v -s"

# Verify expiration checking
make test-backend PYTEST_ARGS="tests/integration/startup/test_certificate_validation.py -v -k 'expiration'"
```

### **Encryption Key Validation Failures**
```bash
# Test key format validation
make test-backend PYTEST_ARGS="tests/integration/startup/test_encryption_key_validation.py -v -s"

# Verify key strength requirements
make test-backend PYTEST_ARGS="tests/integration/startup/test_encryption_key_validation.py -v -k 'strength'"
```

### **Cryptography Unavailable Test Issues**
```bash
# Run Docker-based cryptography tests with verbose output
make test-no-cryptography

# Manual Docker execution with debugging
docker build --progress=plain -f backend/tests/integration/docker/Dockerfile.no-cryptography -t no-crypto-debug .
docker run --rm no-crypto-debug pytest tests/integration/startup/test_*_cryptography_unavailable.py -vv --tb=long
```

### **Configuration and Error Handling Issues**
```bash
# Test invalid security configuration handling
make test-backend PYTEST_ARGS="tests/integration/startup/test_security_validation_integration.py::TestComprehensiveSecurityValidation::test_comprehensive_validation_provides_detailed_error_information -v -s"

# Verify error isolation across components
make test-backend PYTEST_ARGS="tests/integration/startup/test_security_validation_integration.py::TestComprehensiveSecurityValidation::test_comprehensive_validation_isolates_component_failures -v -s"
```

## Test Architecture

These integration tests follow our **behavior-focused testing** principles:

1. **Test Critical Paths**: Focus on high-value security validation workflows essential to system security and operational reliability
2. **Trust Contracts**: Use security validation interface contracts to define expected validation patterns
3. **Test from Outside-In**: Start from public security validation interfaces and validate observable system behavior
4. **Verify Integrations**: Test real security validation collaboration across all infrastructure components
5. **Use True Isolation**: Docker-based testing for actual library unavailability scenarios

The tests ensure system startup security provides reliable operational security validation, fails gracefully during security configuration issues, and maintains system security posture through proper error isolation and graceful degradation patterns.

## Special Test Execution Requirements

### **Cryptography Unavailable Tests**
**MANDATORY**: Use Docker-based execution - do NOT attempt to run these tests in standard environment
```bash
# ✅ CORRECT: Docker-based execution
make test-no-cryptography

# ❌ INCORRECT: Standard pytest execution
pytest tests/integration/startup/test_cache_encryption_cryptography_unavailable.py  # WILL BE SKIPPED
```

**Why Docker Required**: These tests validate actual behavior when cryptography library is missing, which cannot be reliably simulated through mocking due to import-time dependencies.

### **Environment Variable Testing**
**CRITICAL**: Always use `monkeypatch.setenv()` for environment variable manipulation in tests
```bash
# ✅ CORRECT: Use monkeypatch for environment variables
def test_production_security(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Test behavior...

# ❌ INCORRECT: Direct environment modification
def test_production_security():
    os.environ["ENVIRONMENT"] = "production"  # CAUSES TEST POLLUTION
```

## Related Documentation

- **Test Plan**: `TEST_PLAN.md` - Comprehensive test planning and security integration mapping
- **Cryptography Implementation**: `CRYPTOGRAPHY_UNAVAILABLE_IMPLEMENTATION.md` - Docker-based testing implementation details
- **Docker Testing Guide**: `backend/tests/integration/docker/README.md` - Comprehensive Docker testing instructions
- **Security Validation**: `backend/contracts/core/startup/redis_security.pyi` - Security validation system implementation
- **Integration Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md` - Testing methodology and principles
- **Cache Encryption**: `backend/contracts/infrastructure/cache/encryption.pyi` - Cache encryption implementation
- **Environment Detection**: `backend/contracts/core/startup/environment.pyi` - Environment detection and classification system
- **Security Configuration**: `docs/guides/developer/SECURITY.md` - Security configuration and validation guidelines
- **App Factory Pattern**: `docs/guides/developer/APP_FACTORY_GUIDE.md` - Testing patterns for startup validation