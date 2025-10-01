# Integration Test Plan: Redis Security and Cache Encryption

## Overview

This comprehensive integration test plan covers the Redis security validation and cache encryption infrastructure. These tests verify critical security integrations between application startup, cache services, environment detection, and the cryptography library dependency.

## Analysis Objectives

1. **Identify Critical Seams**: Map component interactions requiring integration testing
2. **Map Data Flows**: Trace security validation and encryption through the system
3. **Find Integration Points**: Locate where components collaborate for security enforcement
4. **Identify Resilience Patterns**: Test graceful degradation when dependencies are unavailable
5. **Verify Environment-Aware Behavior**: Ensure security rules adapt to deployment contexts

## Component Architecture Analysis

### Core Components Identified

1. **RedisSecurityValidator** (`app/core/startup/redis_security.py`)
   - Production security enforcement with TLS and authentication validation
   - Environment-aware security requirements
   - Integration with environment detection system
   - Certificate and encryption key validation

2. **EncryptedCacheLayer** (`app/infrastructure/cache/encryption.py`)
   - Mandatory Fernet encryption for cached data
   - Cryptography library dependency with graceful degradation
   - Performance monitoring integration
   - Integration with Redis cache infrastructure

3. **Environment Detection** (`app/core/environment/`)
   - Centralized environment classification
   - Confidence scoring and reasoning
   - Feature-specific context support
   - Integration with security validator

4. **Cache Infrastructure** (`app/infrastructure/cache/`)
   - AIResponseCache with encryption integration
   - Redis and memory backend support
   - Performance monitoring and metrics
   - Graceful degradation patterns

### Critical Integration Seams Identified

## INTEGRATION TEST PLAN

### 1. SEAM: Application Startup → Redis Security Validator → Environment Detection
   **COMPONENTS**: `validate_startup_security()`, `RedisSecurityValidator`, `get_environment_info()`
   **CRITICAL PATH**: Application initialization → Environment detection → Security validation → Configuration enforcement
   **TEST SCENARIOS**:
   - Production environment enforces TLS requirements
   - Development environment allows flexible security
   - Missing cryptography library provides helpful error messages
   - Environment override mechanisms work correctly
   **INFRASTRUCTURE**: Environment variable manipulation, optional cryptography mocking
   **PRIORITY**: HIGH (security critical, blocks application startup)

### 2. SEAM: Redis Security Validator → Certificate Validation → Cryptography Library
   **COMPONENTS**: `validate_tls_certificates()`, `validate_encryption_key()`, cryptography library
   **CRITICAL PATH**: Security validation → Cryptography availability → Certificate/key validation → Result reporting
   **TEST SCENARIOS**:
   - Certificate validation with available cryptography (full validation)
   - Certificate validation without cryptography (basic file checks only)
   - Encryption key validation with cryptography (fernet key validation)
   - Encryption key validation without cryptography (graceful degradation)
   - Comprehensive validation report generation
   **INFRASTRUCTURE**: Test certificate files, valid/invalid fernet keys, cryptography availability control
   **PRIORITY**: HIGH (security validation, affects production deployment)

### 3. SEAM: Cache Infrastructure → EncryptedCacheLayer → Redis Security
   **COMPONENTS**: `AIResponseCache`, `EncryptedCacheLayer`, Redis connection, security validation
   **CRITICAL PATH**: Cache initialization → Encryption layer setup → Security validation → Cache operations
   **TEST SCENARIOS**:
   - Cache initialization with valid encryption key
   - Cache initialization with invalid encryption key (proper error handling)
   - Cache initialization without cryptography library (helpful error message)
   - Cache operations successfully encrypt/decrypt data
   - Cache performance monitoring integration
   **INFRASTRUCTURE**: fakeredis, test encryption keys, cryptography availability control
   **PRIORITY**: HIGH (core functionality, affects all cache operations)

### 4. SEAM: API Endpoints → Cache Services → Encryption Layer
   **COMPONENTS**: `/internal/cache/*` endpoints, `AIResponseCache`, `EncryptedCacheLayer`
   **CRITICAL PATH**: HTTP request → Cache operation → Encryption/decryption → Response
   **TEST SCENARIOS**:
   - Cache status endpoint with encrypted data
   - Cache metrics endpoint with performance monitoring
   - Cache invalidation with encrypted data
   - Encryption failure graceful degradation in API responses
   **INFRASTRUCTURE**: TestClient, fakeredis, encryption layer with controlled cryptography
   **PRIORITY**: MEDIUM (user-facing, has graceful degradation)

### 5. SEAM: Health Check System → Security Validation → Cache Infrastructure
   **COMPONENTS**: `/v1/health` endpoint, security validation, cache health checks
   **CRITICAL PATH**: Health check request → Component validation → Security status → Health response
   **TEST SCENARIOS**:
   - Health check includes security validation status
   - Health check detects cryptography library availability
   - Health check reflects encryption layer status
   - Graceful health reporting when security components fail
   **INFRASTRUCTURE**: TestClient, controlled component states
   **PRIORITY**: MEDIUM (monitoring and observability)

### 6. SEAM: Configuration Management → Security Validator → Environment
   **COMPONENTS**: Settings class, `RedisSecurityValidator`, environment detection
   **CRITICAL PATH**: Configuration load → Environment detection → Security rule application → Validation
   **TEST SCENARIOS**:
   - Configuration-driven security validation
   - Environment-specific security requirements
   - Override mechanism testing
   - Configuration validation error handling
   **INFRASTRUCTURE**: Environment variable manipulation, configuration testing
   **PRIORITY**: MEDIUM (configuration management)

## Detailed Test Implementation Plan

### Cryptography Library Unavailability Scenarios (Extending Existing Plan)

#### File: `tests/integration/startup/test_redis_security_cryptography_unavailable.py`

```python
class TestRedisSecurityCryptographyUnavailable:
    """
    Integration tests for Redis security validation when cryptography library is unavailable.

    These tests verify graceful degradation and helpful error messages when the mandatory
    cryptography dependency is missing, ensuring users get actionable guidance.

    Integration Scope:
        RedisSecurityValidator + Environment Detection + Cryptography Library Dependency

    Critical Paths:
        - Startup security validation without cryptography
        - Certificate validation with limited capabilities
        - Encryption key validation failures
    """

    @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE, reason="Test requires cryptography to be unavailable")
    def test_startup_security_without_cryptography_helpful_error(self):
        """
        Test that startup validation provides helpful error when cryptography is missing.

        Integration Scope:
            Application startup → Security validation → Missing dependency detection

        Business Impact:
            Users can understand what went wrong and how to fix it

        Success Criteria:
            - ConfigurationError raised with clear message
            - Error contains installation command
            - Error explains business impact
        """
        # Manipulate environment to simulate missing cryptography
        with pytest.raises(ConfigurationError) as exc_info:
            validate_redis_security("rediss://redis:6380")

        error_message = str(exc_info.value)
        assert "cryptography library is required" in error_message.lower()
        assert "install with:" in error_message.lower()
        assert "pip install cryptography" in error_message.lower()

    @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE, reason="Test requires cryptography to be unavailable")
    def test_tls_certificate_validation_limited_without_cryptography(self):
        """
        Test that TLS validation provides limited capability without cryptography.

        Integration Scope:
            Certificate validation → Cryptography availability → Graceful degradation

        Business Impact:
            Basic file validation still works, users understand limitations

        Success Criteria:
            - Basic file validation succeeds
            - Warning about limited capabilities
            - No certificate expiration information
        """
        validator = RedisSecurityValidator()

        # Create temporary certificate files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as cert_file:
            cert_file.write("-----BEGIN CERTIFICATE-----\nfake cert data\n-----END CERTIFICATE-----")
            cert_path = cert_file.name

        try:
            result = validator.validate_tls_certificates(cert_path=cert_path)

            # Basic validation should still work
            assert result["valid"] is True
            assert "files_exist" in result["checks"]

            # Should warn about limited capabilities
            assert any("cryptography" in warning.lower() for warning in result.get("warnings", []))

            # No advanced certificate info available
            assert result.get("certificate_info") is None

        finally:
            os.unlink(cert_path)

    @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE, reason="Test requires cryptography to be unavailable")
    def test_encryption_key_validation_fails_without_cryptography(self):
        """
        Test that encryption key validation fails gracefully without cryptography.

        Integration Scope:
            Encryption key validation → Cryptography dependency → Error handling

        Business Impact:
            Users understand encryption cannot be validated

        Success Criteria:
            - Validation fails appropriately
            - Clear error about missing library
            - Actionable error message
        """
        validator = RedisSecurityValidator()
        valid_fernet_key = "gAAAAABfZ4Q4zX7N9e2bY1aXcV3bN6m8PqR5sT2uV4wX7yZ0cA="

        result = validator.validate_encryption_key(valid_fernet_key)

        assert result["valid"] is False
        assert any("cryptography" in error.lower() for error in result.get("errors", []))
        assert "cannot be validated" in str(result).lower()
```

#### File: `tests/integration/startup/test_cache_encryption_cryptography_unavailable.py`

```python
class TestCacheEncryptionCryptographyUnavailable:
    """
    Integration tests for cache encryption when cryptography library is unavailable.

    These tests verify that the cache encryption layer fails gracefully and provides
    helpful error messages when the cryptography dependency is missing.

    Integration Scope:
        EncryptedCacheLayer + Cache Infrastructure + Cryptography Dependency

    Critical Paths:
        - Cache initialization without cryptography
        - Cache operations with encryption failures
        - Error propagation through cache infrastructure
    """

    @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE, reason="Test requires cryptography to be unavailable")
    def test_encrypted_cache_initialization_helpful_error(self):
        """
        Test that encrypted cache initialization provides helpful error without cryptography.

        Integration Scope:
            Cache initialization → Encryption layer → Missing dependency detection

        Business Impact:
            Users understand encryption failure and how to resolve

        Success Criteria:
            - ConfigurationError with helpful message
            - Clear installation instructions
            - Business impact explanation
        """
        with pytest.raises(ConfigurationError) as exc_info:
            EncryptedCacheLayer(encryption_key="test-key")

        error_message = str(exc_info.value)
        assert "cryptography library is required" in error_message.lower()
        assert "install with:" in error_message.lower()
        assert "pip install cryptography" in error_message.lower()
        assert "mandatory dependency" in error_message.lower()

    @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE, reason="Test requires cryptography to be unavailable")
    def test_cache_service_integration_without_cryptography(self):
        """
        Test that cache service handles encryption layer failure gracefully.

        Integration Scope:
            Cache service → Encryption layer → Error propagation

        Business Impact:
            Cache service fails gracefully when encryption unavailable

        Success Criteria:
            - Cache service initialization fails with clear error
            - Error message includes encryption failure context
            - Proper exception chaining
        """
        # This test simulates the real integration path where cache service
        # tries to initialize encryption layer and fails
        with pytest.raises(ConfigurationError) as exc_info:
            # Simulate cache service initialization path
            from app.infrastructure.cache.redis import AIResponseCache
            cache = AIResponseCache(redis_url="redis://localhost:6379")
            # Force encryption initialization
            cache._ensure_encryption_layer()

        error_message = str(exc_info.value)
        assert "cryptography" in error_message.lower()
        assert "encryption" in error_message.lower()
```

### Environment-Aware Security Validation Tests

#### File: `tests/integration/startup/test_environment_aware_security.py`

```python
class TestEnvironmentAwareSecurity:
    """
    Integration tests for environment-aware Redis security validation.

    These tests verify that security requirements adapt correctly to different
    deployment environments (production, development, testing).

    Integration Scope:
        RedisSecurityValidator + Environment Detection + Configuration Management

    Critical Paths:
        - Environment detection → Security rule application
        - Configuration override mechanisms
        - Environment-specific error messages
    """

    def test_production_environment_enforces_tls(self, monkeypatch):
        """
        Test that production environment enforces TLS requirements.

        Integration Scope:
            Production environment detection → TLS enforcement → Security validation

        Business Impact:
            Production deployments are secure by default

        Success Criteria:
            - Insecure Redis URL fails in production
            - Clear error message about TLS requirement
            - Proper ConfigurationError with security context
        """
        # Set production environment
        monkeypatch.setenv("ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Test insecure URL fails
        with pytest.raises(ConfigurationError) as exc_info:
            validator.validate_production_security("redis://redis:6379")

        error_message = str(exc_info.value)
        assert "tls" in error_message.lower()
        assert "production" in error_message.lower()
        assert "required" in error_message.lower()

    def test_development_environment_allows_flexibility(self, monkeypatch):
        """
        Test that development environment allows flexible security configuration.

        Integration Scope:
            Development environment detection → Flexible security → Success validation

        Business Impact:
            Development workflows are not blocked by strict security

        Success Criteria:
            - Insecure URL passes in development
            - Appropriate warnings logged
            - No exceptions raised for valid configuration
        """
        # Set development environment
        monkeypatch.setenv("ENVIRONMENT", "development")

        validator = RedisSecurityValidator()

        # Should not raise exception for insecure URL in development
        validator.validate_production_security("redis://localhost:6379")

        # Should work with secure URL too
        validator.validate_production_security("rediss://localhost:6379")

    def test_insecure_override_mechanism(self, monkeypatch):
        """
        Test that insecure override mechanism works correctly.

        Integration Scope:
            Override configuration → Security validation → Warning generation

        Business Impact:
            Emergency override capability with proper audit trail

        Success Criteria:
            - Override allows insecure connections
            - Security warnings are generated
            - Override only works when explicitly enabled
        """
        # Set production environment
        monkeypatch.setenv("ENVIRONMENT", "production")

        validator = RedisSecurityValidator()

        # Test override mechanism
        with pytest.raises(ConfigurationError):
            validator.validate_production_security("redis://redis:6379")

        # Should work with override
        validator.validate_production_security("redis://redis:6379", insecure_override=True)
```

### Complete Security Configuration Validation Tests

#### File: `tests/integration/startup/test_comprehensive_security_validation.py`

```python
class TestComprehensiveSecurityValidation:
    """
    Integration tests for comprehensive Redis security configuration validation.

    These tests verify the complete security validation workflow including
    TLS certificates, encryption keys, authentication, and connectivity.

    Integration Scope:
        RedisSecurityValidator + Certificate Validation + Encryption + Connectivity Testing

    Critical Paths:
        - Complete security configuration validation
        - Multi-component validation result aggregation
        - Error collection and reporting
    """

    def test_comprehensive_validation_success(self, tmp_path):
        """
        Test comprehensive validation with valid security configuration.

        Integration Scope:
            All security components → Validation orchestration → Success reporting

        Business Impact:
            Complete security validation for production deployment

        Success Criteria:
            - All validation components pass
            - Comprehensive validation report
            - Success status with detailed component status
        """
        validator = RedisSecurityValidator()

        # Create temporary certificate files
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text("-----BEGIN CERTIFICATE-----\nfake cert\n-----END CERTIFICATE-----")

        key_file = tmp_path / "key.pem"
        key_file.write_text("-----BEGIN PRIVATE KEY-----\nfake key\n-----END PRIVATE KEY-----")

        # Test comprehensive validation
        result = validator.validate_security_configuration(
            redis_url="rediss://redis:6380",
            encryption_key="gAAAAABfZ4Q4zX7N9e2bY1aXcV3bN6m8PqR5sT2uV4wX7yZ0cA=",
            tls_cert_path=str(cert_file),
            tls_key_path=str(key_file),
            test_connectivity=False  # Don't test real connectivity
        )

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.tls_status == "valid"
        assert result.encryption_status == "valid"
        assert result.auth_status == "valid"
        assert result.connectivity_status == "not_tested"

    def test_comprehensive_validation_failure_aggregation(self, tmp_path):
        """
        Test that validation failures are properly aggregated and reported.

        Integration Scope:
            Multiple validation failures → Error aggregation → Comprehensive reporting

        Business Impact:
            Users understand all security issues at once

        Success Criteria:
            - Multiple validation failures detected
            - Clear error messages for each failure
            - Validation report reflects overall failure
            - Specific component failure statuses
        """
        validator = RedisSecurityValidator()

        # Test with invalid configuration
        result = validator.validate_security_configuration(
            redis_url="redis://redis:6379",  # Insecure
            encryption_key="invalid-key",   # Invalid format
            test_connectivity=False
        )

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert result.tls_status == "invalid"  # Should detect insecure URL
        assert result.encryption_status == "invalid"  # Should detect invalid key

        # Check that error messages are helpful
        error_texts = [error.lower() for error in result.errors]
        assert any("tls" in error for error in error_texts)
        assert any("encryption" in error for error in error_texts)
```

### Cache Integration with Security Tests

#### File: `tests/integration/startup/test_cache_security_integration.py`

```python
class TestCacheSecurityIntegration:
    """
    Integration tests for cache infrastructure integration with security validation.

    These tests verify that the cache system properly integrates with security
    validation and encryption requirements.

    Integration Scope:
        Cache Infrastructure + Encryption Layer + Security Validation

    Critical Paths:
        - Cache initialization with security validation
        - Cache operations with encryption
        - Security validation in cache lifecycle
    """

    def test_cache_initialization_with_valid_encryption(self, fake_redis):
        """
        Test that cache initializes successfully with valid encryption.

        Integration Scope:
            Cache initialization → Encryption layer → Security validation

        Business Impact:
            Cache operations are secure by default

        Success Criteria:
            - Cache initializes with encryption
            - Encryption operations work correctly
            - Data is properly encrypted/decrypted
        """
        from app.infrastructure.cache.redis import AIResponseCache

        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            encryption_key="gAAAAABfZ4Q4zX7N9e2bY1aXcV3bN6m8PqR5sT2uV4wX7yZ0cA=",
            redis_client=fake_redis
        )

        # Test basic cache operations
        test_data = {"test": "data", "numbers": [1, 2, 3]}
        cache_key = "test_integration_key"

        # Store encrypted data
        cache.set(cache_key, test_data, timeout_seconds=60)

        # Retrieve decrypted data
        retrieved_data = cache.get(cache_key)

        assert retrieved_data == test_data
        assert cache.encryption.is_enabled is True

    def test_cache_initialization_without_encryption_key(self, fake_redis):
        """
        Test that cache handles missing encryption key appropriately.

        Integration Scope:
            Cache initialization → Missing encryption → Error handling

        Business Impact:
            Clear error messages for configuration issues

        Success Criteria:
            - Cache initialization fails gracefully
            - Helpful error message about encryption requirement
            - Proper exception type
        """
        from app.infrastructure.cache.redis import AIResponseCache

        with pytest.raises(ConfigurationError) as exc_info:
            AIResponseCache(
                redis_url="redis://localhost:6379",
                encryption_key=None,
                redis_client=fake_redis
            )

        error_message = str(exc_info.value)
        assert "encryption" in error_message.lower()
        assert "required" in error_message.lower()
```

## Test Infrastructure Requirements

### Environment Setup

1. **Cryptography Availability Control**:
   ```bash
   # Create environment without cryptography for integration tests
   python -m venv /tmp/test-no-crypto
   source /tmp/test-no-crypto/bin/activate
   pip install pytest redis fakeredis pydantic fastapi
   # DO NOT install cryptography
   ```

2. **Test Certificate Management**:
   - Temporary certificate file creation/cleanup
   - Valid and invalid certificate samples
   - Certificate expiration testing

3. **Environment Variable Testing**:
   - `monkeypatch` for environment manipulation
   - Production/development/testing environment simulation
   - Override mechanism testing

### Test Fixtures

```python
# conftest.py additions
@pytest.fixture
def test_certificates(tmp_path):
    """Provide test certificate files for TLS validation tests."""
    cert_file = tmp_path / "test_cert.pem"
    cert_file.write_text("-----BEGIN CERTIFICATE-----\nfake cert data\n-----END CERTIFICATE-----")

    key_file = tmp_path / "test_key.pem"
    key_file.write_text("-----BEGIN PRIVATE KEY-----\nfake key data\n-----END PRIVATE KEY-----")

    return {
        "cert_path": str(cert_file),
        "key_path": str(key_file)
    }

@pytest.fixture
def valid_fernet_key():
    """Provide a valid Fernet encryption key for testing."""
    return "gAAAAABfZ4Q4zX7N9e2bY1aXcV3bN6m8PqR5sT2uV4wX7yZ0cA="

@pytest.fixture
def environment_scenarios(monkeypatch):
    """Provide environment scenario setup for testing."""
    def set_environment(env_name):
        monkeypatch.setenv("ENVIRONMENT", env_name)

    return set_environment
```

### Test Execution Strategy

1. **Parallel Execution**: Most tests can run in parallel
2. **Environment Isolation**: Use pytest fixtures for environment control
3. **Resource Cleanup**: Proper cleanup of temporary files and connections
4. **Conditional Testing**: Skip tests based on cryptography availability

## Success Criteria

### Test Coverage Goals
- **Security Critical Paths**: 100% coverage
- **Environment Integration**: 95% coverage
- **Graceful Degradation**: 100% coverage
- **Error Handling**: 100% coverage

### Quality Metrics
- **Test Reliability**: Tests must be deterministic and reproducible
- **Error Message Quality**: All error messages must be actionable and helpful
- **Integration Completeness**: All identified seams must have test coverage
- **Performance**: Tests should complete within reasonable time limits

### Business Value Validation
- **Production Readiness**: Tests validate production deployment requirements
- **Developer Experience**: Tests provide clear feedback for configuration issues
- **Security Assurance**: Tests verify security requirements are enforced
- **Operational Stability**: Tests verify graceful degradation under failure conditions

## Migration Strategy

### From Unit Tests
- **Cryptography Unavailability Tests**: Move from unit to integration as specified in existing plan
- **Environment Integration Tests**: New tests for environment-aware security validation
- **Cache Integration Tests**: Expand existing cache tests to include security integration

### Test Implementation Priority
1. **HIGH**: Cryptography unavailability scenarios (existing plan)
2. **HIGH**: Environment-aware security validation
3. **MEDIUM**: Comprehensive security configuration validation
4. **MEDIUM**: Cache security integration
5. **LOW**: Advanced scenarios (certificate expiration, key rotation)

## References

### Related Documentation
- **Testing Guide**: `docs/guides/testing/INTEGRATION_TESTS.md`
- **Security Guide**: `docs/guides/infrastructure/SECURITY.md`
- **Cache Guide**: `docs/guides/infrastructure/CACHE.md`
- **Environment Detection**: `docs/guides/infrastructure/ENVIRONMENT_DETECTION.md`

### Related Code Files
- **Redis Security**: `backend/app/core/startup/redis_security.py`
- **Cache Encryption**: `backend/app/infrastructure/cache/encryption.py`
- **Environment Detection**: `backend/app/core/environment/`
- **Cache Infrastructure**: `backend/app/infrastructure/cache/`

### Existing Test Plans
- **Cryptography Unavailability**: `backend/tests/integration/startup/TEST_PLAN_cryptography_unavailable.md`
- **Unit Test Migration**: Backend unit tests marked for migration to integration