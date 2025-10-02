# Integration Test Plan: Redis Security Validation

## Executive Summary

This test plan identifies and prioritizes integration test scenarios for the Redis security validation component (`app.core.startup.redis_security`). The plan follows an **outside-in testing philosophy**, starting from application boundaries and testing component collaboration rather than internal implementation details.

## Critical Context

**Component Under Test:** Redis security validation at application startup
- **Public Contract:** `backend/contracts/core/startup/redis_security.pyi`
- **Implementation:** `backend/app/core/startup/redis_security.py`
- **Current Integration Status:** ✅ INTEGRATED into application startup sequence
- **Integration Point:** `backend/app/main.py` lifespan() function (lines 468-479)

**Key Implementation Details:** The component is actively called during application startup in `main.py`, performing security validation before health infrastructure initialization. Production environments enforce TLS requirements and fail fast on security violations.

## Integration Testing Philosophy

**Test from Outside-In:**
- Start at application boundaries (API endpoints, startup sequence, CLI tools)
- Test component collaboration, not individual methods
- Use high-fidelity fakes (fakeredis) over mocks
- Verify observable behavior from user perspective

**Prioritize Business Impact:**
- HIGH: Security enforcement, startup failures, user-facing errors
- MEDIUM: Configuration validation, operational tools, graceful degradation
- LOW: Performance optimization, advanced edge cases, optional features

## Component Architecture Analysis

### Dependencies Identified

```
RedisSecurityValidator
├── Environment Detection (app.core.environment)
│   ├── get_environment_info()
│   ├── Environment enum (PRODUCTION, DEVELOPMENT, TESTING)
│   └── FeatureContext.SECURITY_ENFORCEMENT
├── Exception Handling (app.core.exceptions)
│   └── ConfigurationError
└── Cryptography Library (external)
    ├── x509 certificate parsing
    └── Fernet encryption validation
```

### Integration Points Identified

1. **Application Startup Sequence** (FUTURE - not currently integrated)
   - Main application lifecycle (`app.main:lifespan`)
   - Cache service initialization (`app.dependencies:get_cache_service`)
   - Health check infrastructure (`app.dependencies:initialize_health_infrastructure`)

2. **Environment Detection Integration** (ACTIVE)
   - Production vs development security rules
   - Confidence scoring and environment classification
   - Feature-specific context (SECURITY_ENFORCEMENT)

3. **Cryptography Library Dependency** (ACTIVE)
   - Certificate validation and expiration checking
   - Fernet encryption key validation
   - Graceful degradation when library unavailable

4. **Configuration Management** (ACTIVE)
   - Environment variable reading (`REDIS_URL`, `REDIS_INSECURE_ALLOW_PLAINTEXT`)
   - TLS certificate paths (`REDIS_TLS_CERT_PATH`, etc.)
   - Encryption key configuration (`REDIS_ENCRYPTION_KEY`)

## Integration Test Scenarios

### Priority 1: HIGH (Security-Critical, Startup Blockers)

#### SEAM 1: Standalone Security Validation → Environment Detection → Configuration Enforcement

**Components:** `validate_redis_security()`, `RedisSecurityValidator`, `get_environment_info()`

**Critical Path:** Standalone invocation → Environment detection → Security rule application → Pass/fail decision

**Business Impact:** Security enforcement works correctly for future startup integration

**Test Scenarios:**

1. **Production Environment Enforces TLS Requirements**
   ```python
   # File: tests/integration/startup/test_environment_aware_security.py
   def test_production_environment_rejects_insecure_redis_url(monkeypatch):
       """
       INTEGRATION: Standalone validator → Environment detection → Security enforcement

       Verify that production environment detection correctly triggers TLS enforcement
       and rejects insecure Redis URLs with helpful error messages.
       """
       # Set production environment indicators
       monkeypatch.setenv("ENVIRONMENT", "production")
       monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

       validator = RedisSecurityValidator()

       # Test: Insecure URL should fail in production
       with pytest.raises(ConfigurationError) as exc_info:
           validator.validate_production_security("redis://redis:6379")

       error = str(exc_info.value)
       assert "production environment requires secure" in error.lower()
       assert "tls" in error.lower()
       assert "rediss://" in error
   ```

2. **Development Environment Allows Flexible Security**
   ```python
   def test_development_environment_allows_insecure_redis_url(monkeypatch):
       """
       INTEGRATION: Standalone validator → Environment detection → Flexible rules

       Verify that development environment detection correctly allows insecure
       Redis URLs while logging appropriate informational messages.
       """
       monkeypatch.setenv("ENVIRONMENT", "development")

       validator = RedisSecurityValidator()

       # Test: Insecure URL should succeed in development (no exception)
       validator.validate_production_security("redis://localhost:6379")

       # Test: Secure URL also works
       validator.validate_production_security("rediss://localhost:6380")
   ```

3. **Insecure Override Mechanism with Production Warnings**
   ```python
   def test_production_override_allows_insecure_with_warning(monkeypatch, caplog):
       """
       INTEGRATION: Override configuration → Security bypass → Warning generation

       Verify that explicit insecure override works in production but generates
       appropriate security warnings for audit trail.
       """
       monkeypatch.setenv("ENVIRONMENT", "production")

       validator = RedisSecurityValidator()

       # Test: Override should allow insecure connection
       with caplog.at_level(logging.WARNING):
           validator.validate_production_security(
               "redis://redis:6379",
               insecure_override=True
           )

       # Verify warning was logged
       assert any("SECURITY WARNING" in record.message for record in caplog.records)
       assert any("insecure Redis connection" in record.message.lower()
                  for record in caplog.records)
   ```

**Infrastructure Needs:** Environment variable manipulation (`monkeypatch`), logging capture

**Priority Justification:** HIGH - Security enforcement is core functionality, failure prevents safe production deployment

---

#### SEAM 2: Certificate Validation → Cryptography Library → Graceful Degradation

**Components:** `validate_tls_certificates()`, cryptography library, file system

**Critical Path:** Certificate path validation → Cryptography availability check → Certificate parsing → Expiration validation

**Business Impact:** TLS validation works correctly, gracefully degrades without cryptography

**Test Scenarios:**

1. **Valid Certificates with Cryptography Available**
   ```python
   # File: tests/integration/startup/test_certificate_validation.py
   def test_valid_certificates_pass_validation(tmp_path):
       """
       INTEGRATION: Certificate files → Cryptography parsing → Validation success

       Verify that valid certificate files are correctly validated when
       cryptography library is available.
       """
       # Create test certificate files
       cert_file = tmp_path / "cert.pem"
       cert_file.write_text("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")

       key_file = tmp_path / "key.pem"
       key_file.write_text("-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----")

       validator = RedisSecurityValidator()
       result = validator.validate_tls_certificates(
           cert_path=str(cert_file),
           key_path=str(key_file)
       )

       assert result["valid"] is True
       assert len(result["errors"]) == 0
   ```

2. **Missing Certificate Files Generate Errors**
   ```python
   def test_missing_certificate_files_generate_errors():
       """
       INTEGRATION: File system check → Missing file detection → Error reporting

       Verify that missing certificate files are detected and reported with
       helpful error messages.
       """
       validator = RedisSecurityValidator()
       result = validator.validate_tls_certificates(
           cert_path="/nonexistent/cert.pem",
           key_path="/nonexistent/key.pem"
       )

       assert result["valid"] is False
       assert any("not found" in error.lower() for error in result["errors"])
   ```

3. **Cryptography Unavailable Provides Limited Validation**
   ```python
   @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE,
                       reason="Requires cryptography to be unavailable")
   def test_certificate_validation_warns_without_cryptography(tmp_path):
       """
       INTEGRATION: Certificate files → Missing cryptography → Limited validation

       Verify that certificate validation gracefully degrades to basic file
       checks when cryptography library is unavailable.

       NOTE: This test must run in environment without cryptography installed.
       See TEST_PLAN_cryptography_unavailable.md for execution instructions.
       """
       cert_file = tmp_path / "cert.pem"
       cert_file.write_text("-----BEGIN CERTIFICATE-----\nfake\n-----END CERTIFICATE-----")

       validator = RedisSecurityValidator()
       result = validator.validate_tls_certificates(cert_path=str(cert_file))

       # Basic validation should still work
       assert result["valid"] is True

       # Should warn about limited capabilities
       assert any("cryptography" in warning.lower()
                  for warning in result.get("warnings", []))

       # No advanced certificate info available
       assert result.get("cert_info", {}).get("expires") is None
   ```

**Infrastructure Needs:** Temporary file system (`tmp_path`), optional cryptography availability control

**Priority Justification:** HIGH - TLS validation is security-critical for production deployments

---

#### SEAM 3: Encryption Key Validation → Cryptography Library → Fernet Validation

**Components:** `validate_encryption_key()`, cryptography.fernet, key format validation

**Critical Path:** Key format check → Fernet initialization → Encryption test → Validation result

**Business Impact:** Ensures encryption keys are valid before cache initialization

**Test Scenarios:**

1. **Valid Fernet Key Passes Validation**
   ```python
   # File: tests/integration/startup/test_encryption_key_validation.py
   def test_valid_fernet_key_passes_validation():
       """
       INTEGRATION: Valid key → Fernet initialization → Encryption test → Success

       Verify that valid Fernet encryption keys are correctly validated.
       """
       from cryptography.fernet import Fernet
       valid_key = Fernet.generate_key().decode('utf-8')

       validator = RedisSecurityValidator()
       result = validator.validate_encryption_key(valid_key)

       assert result["valid"] is True
       assert result["key_info"]["format"] == "Fernet (AES-128-CBC with HMAC)"
       assert len(result["errors"]) == 0
   ```

2. **Invalid Key Format Generates Error**
   ```python
   def test_invalid_key_format_generates_error():
       """
       INTEGRATION: Invalid key → Format validation → Error generation

       Verify that invalid encryption key formats are detected and reported.
       """
       validator = RedisSecurityValidator()
       result = validator.validate_encryption_key("invalid-short-key")

       assert result["valid"] is False
       assert any("invalid encryption key length" in error.lower()
                  for error in result["errors"])
   ```

3. **Cryptography Unavailable Fails Validation**
   ```python
   @pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE,
                       reason="Requires cryptography to be unavailable")
   def test_encryption_key_validation_fails_without_cryptography():
       """
       INTEGRATION: Valid key → Missing cryptography → Validation failure

       Verify that encryption key validation fails gracefully when cryptography
       library is unavailable.

       NOTE: This test must run in environment without cryptography installed.
       See TEST_PLAN_cryptography_unavailable.md for execution instructions.
       """
       valid_key = "x" * 44  # Valid length but can't be validated

       validator = RedisSecurityValidator()
       result = validator.validate_encryption_key(valid_key)

       assert result["valid"] is False
       assert any("cryptography library not available" in error.lower()
                  for error in result["errors"])
   ```

**Infrastructure Needs:** Cryptography library for key generation, optional availability control

**Priority Justification:** HIGH - Encryption key validation prevents cache initialization failures

---

### Priority 2: MEDIUM (Operational Tools, Configuration Validation)

#### SEAM 4: Comprehensive Security Configuration → Multi-Component Validation → Result Aggregation

**Components:** `validate_security_configuration()`, all validation methods, `SecurityValidationResult`

**Critical Path:** Configuration gathering → Multi-component validation → Error aggregation → Result summary

**Business Impact:** Comprehensive security audit tool for operations teams

**Test Scenarios:**

1. **Comprehensive Validation Success Path**
   ```python
   # File: tests/integration/startup/test_comprehensive_validation.py
   def test_comprehensive_validation_all_components_pass(tmp_path):
       """
       INTEGRATION: Full configuration → All validators → Success aggregation

       Verify that comprehensive security validation succeeds when all
       components are properly configured.
       """
       from cryptography.fernet import Fernet

       # Create test certificates
       cert_file = tmp_path / "cert.pem"
       cert_file.write_text("-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")

       key_file = tmp_path / "key.pem"
       key_file.write_text("-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----")

       # Generate valid encryption key
       encryption_key = Fernet.generate_key().decode('utf-8')

       validator = RedisSecurityValidator()
       result = validator.validate_security_configuration(
           redis_url="rediss://redis:6380",
           encryption_key=encryption_key,
           tls_cert_path=str(cert_file),
           tls_key_path=str(key_file),
           test_connectivity=False
       )

       assert result.is_valid is True
       assert "✅" in result.tls_status
       assert "✅" in result.encryption_status
       assert len(result.errors) == 0
   ```

2. **Validation Failure Aggregation**
   ```python
   def test_comprehensive_validation_aggregates_multiple_failures(monkeypatch):
       """
       INTEGRATION: Invalid configuration → Multiple validators → Error aggregation

       Verify that validation failures from multiple components are correctly
       aggregated and reported in the validation result.
       """
       monkeypatch.setenv("ENVIRONMENT", "production")

       validator = RedisSecurityValidator()
       result = validator.validate_security_configuration(
           redis_url="redis://redis:6379",  # Insecure
           encryption_key="invalid-key",    # Invalid format
           test_connectivity=False
       )

       assert result.is_valid is False
       assert len(result.errors) > 0
       assert "❌" in result.tls_status
       assert "❌" in result.encryption_status

       # Check that errors from both TLS and encryption are present
       error_text = " ".join(result.errors).lower()
       assert "tls" in error_text or "encryption" in error_text
   ```

3. **Validation Summary Format**
   ```python
   def test_validation_result_summary_format():
       """
       INTEGRATION: Validation result → Summary generation → Human-readable output

       Verify that validation result summary generates proper human-readable
       output for operational logging and audit trails.
       """
       validator = RedisSecurityValidator()
       result = validator.validate_security_configuration(
           redis_url="rediss://redis:6380",
           test_connectivity=False
       )

       summary = result.summary()
       assert "Redis Security Validation Report" in summary
       assert "TLS/SSL:" in summary
       assert "Encryption:" in summary
       assert "Auth:" in summary
   ```

**Infrastructure Needs:** Temporary files, cryptography library, environment manipulation

**Priority Justification:** MEDIUM - Operational tool for security auditing, not startup-critical

---

#### SEAM 5: Authentication Validation → URL Parsing → Password Strength Check

**Components:** `validate_redis_auth()`, URL parsing, environment detection

**Critical Path:** URL parsing → Authentication detection → Password strength check → Result generation

**Business Impact:** Ensures Redis authentication is properly configured for production

**Test Scenarios:**

1. **URL-Embedded Credentials Detection**
   ```python
   # File: tests/integration/startup/test_authentication_validation.py
   def test_url_embedded_credentials_detected():
       """
       INTEGRATION: Redis URL → Authentication parsing → Validation success

       Verify that authentication credentials embedded in Redis URL are
       correctly detected and validated.
       """
       validator = RedisSecurityValidator()
       result = validator.validate_redis_auth("redis://user:strongpassword123456@redis:6379")

       assert result["valid"] is True
       assert result["auth_info"]["method"] == "URL-embedded credentials"
       assert result["auth_info"]["username"] == "user"
   ```

2. **Weak Password Warning**
   ```python
   def test_weak_password_generates_warning():
       """
       INTEGRATION: Redis URL → Password strength check → Warning generation

       Verify that weak passwords generate security warnings while still
       passing validation.
       """
       validator = RedisSecurityValidator()
       result = validator.validate_redis_auth("redis://user:weak@redis:6379")

       assert result["valid"] is True
       assert any("weak password" in warning.lower()
                  for warning in result.get("warnings", []))
   ```

3. **Production Requires Authentication**
   ```python
   def test_production_requires_authentication(monkeypatch):
       """
       INTEGRATION: Environment detection → Auth validation → Production enforcement

       Verify that production environment requires authentication configuration.
       """
       monkeypatch.setenv("ENVIRONMENT", "production")

       validator = RedisSecurityValidator()
       result = validator.validate_redis_auth("redis://redis:6379")

       assert result["valid"] is False
       assert any("no authentication configured" in error.lower()
                  for error in result.get("errors", []))
   ```

**Infrastructure Needs:** Environment variable manipulation

**Priority Justification:** MEDIUM - Important security check, but not startup-blocking

---

### Priority 1: HIGH (Security-Critical, Startup Blockers) - Continued

#### SEAM 6: Application Startup → Security Validation → Cache Initialization

**Status:** INTEGRATED - Active in production startup sequence

**Components:** `app.main:lifespan`, `validate_redis_security()`, `app.dependencies:get_cache_service`

**Critical Path:** Application startup → Redis security validation → Cache service initialization → Application ready

**Business Impact:** Ensures application fails fast if Redis security is misconfigured

**Test Scenarios:**

1. **Application Startup Validates Redis Security**
   ```python
   # File: tests/integration/startup/test_app_startup_security.py
   async def test_application_startup_validates_redis_security(monkeypatch):
       """
       INTEGRATION: App startup → Security validation → Startup success/failure

       Verify that application startup performs Redis security validation and
       fails fast if security requirements are not met.
       """
       monkeypatch.setenv("ENVIRONMENT", "production")
       monkeypatch.setenv("REDIS_URL", "redis://redis:6379")  # Insecure

       # Test: Application startup should fail with security error
       with pytest.raises(ConfigurationError) as exc_info:
           async with lifespan(app):
               pass

       assert "security" in str(exc_info.value).lower()
   ```

2. **Cache Service Respects Security Validation**
   ```python
   async def test_cache_service_respects_security_validation(monkeypatch):
       """
       INTEGRATION: Cache init → Security check → Initialization decision

       Verify that cache service initialization respects Redis security
       validation results.
       """
       monkeypatch.setenv("REDIS_URL", "rediss://redis:6380")
       monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "valid-key-here")

       cache = await get_cache_service()
       assert cache is not None
   ```

**Infrastructure Needs:** TestClient, async test fixtures, application lifecycle management

**Priority Justification:** HIGH - Security validation is now integrated into startup, critical for production safety

---

## Test Infrastructure Requirements

### Environment Setup

```python
# conftest.py additions

@pytest.fixture
def production_environment(monkeypatch):
    """Set production environment indicators."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    yield

@pytest.fixture
def development_environment(monkeypatch):
    """Set development environment indicators."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    yield

@pytest.fixture
def valid_fernet_key():
    """Generate valid Fernet encryption key."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode('utf-8')

@pytest.fixture
def test_certificates(tmp_path):
    """Create temporary test certificate files."""
    cert_file = tmp_path / "test_cert.pem"
    cert_file.write_text(
        "-----BEGIN CERTIFICATE-----\n"
        "MIICmzCCAYMCAgPoMA0GCSqGSIb3DQEBBQUAMBQxEjAQBgNVBAMTCWxvY2FsaG9z\n"
        "-----END CERTIFICATE-----"
    )

    key_file = tmp_path / "test_key.pem"
    key_file.write_text(
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\n"
        "-----END PRIVATE KEY-----"
    )

    return {
        "cert_path": str(cert_file),
        "key_path": str(key_file)
    }
```

### Cryptography Availability Testing

See `TEST_PLAN_cryptography_unavailable.md` for detailed guidance on testing scenarios where cryptography library is unavailable. Key approaches:

1. **Docker-based isolation** (Recommended)
2. **Virtual environment script**
3. **Tox environment configuration**

### Test Organization

```
tests/integration/startup/
├── conftest.py                           # Shared fixtures
├── test_environment_aware_security.py    # Priority 1: Environment integration
├── test_certificate_validation.py        # Priority 1: Certificate validation
├── test_encryption_key_validation.py     # Priority 1: Encryption key validation
├── test_app_startup_security.py          # Priority 1: Startup integration (ACTIVE)
├── test_comprehensive_validation.py      # Priority 2: Full validation flow
└── test_authentication_validation.py     # Priority 2: Auth validation
```

## Success Criteria

### Test Coverage Targets
- **Priority 1 (HIGH)**: 100% coverage of security-critical paths
- **Priority 2 (MEDIUM)**: 90% coverage of operational tools
- **Priority 3 (LOW)**: Deferred until feature integration

### Quality Metrics
- **Test Reliability**: All tests must be deterministic and repeatable
- **Error Message Quality**: All failures must provide actionable error messages
- **Execution Speed**: Integration tests should complete within 30 seconds
- **Isolation**: Tests must not interfere with each other or require specific execution order

### Business Value Validation
- **Production Readiness**: Tests validate production deployment requirements
- **Developer Experience**: Clear test failures guide configuration fixes
- **Security Assurance**: Tests verify security requirements are enforced
- **Operational Stability**: Tests verify graceful degradation under failure conditions

## Migration from Existing Plans

### Salvage from TEST_PLAN.md.old

**Reusable Elements:**
- Component architecture context ✓ (incorporated above)
- Test infrastructure fixtures ✓ (incorporated in conftest section)
- Success criteria ✓ (incorporated above)

**Discarded Elements:**
- Internal method testing (conflicts with outside-in philosophy)
- Mock-heavy approaches (replaced with high-fidelity fakes)
- Connectivity testing (deferred to Priority 3 / future work)

### Integration with TEST_PLAN_cryptography_unavailable.md

**Relationship:**
- This plan covers **normal operation** with cryptography available
- Cryptography unavailability plan covers **graceful degradation** scenarios
- Tests marked with `@pytest.mark.skipif(CRYPTOGRAPHY_AVAILABLE)` reference unavailability plan
- Both plans are complementary and together provide complete coverage

## Implementation Approach

### Phase 1: Priority 1 Tests (Sprint 1-2)
1. Environment-aware security validation
2. Certificate validation with cryptography
3. Encryption key validation
4. Cryptography unavailability scenarios (reference separate plan)

### Phase 2: Priority 2 Tests (Sprint 3)
1. Comprehensive validation workflow
2. Authentication validation
3. Multi-component error aggregation

### Phase 3: Priority 3 Tests (Future)
1. Application startup integration (when feature implemented)
2. Cache service integration (when feature implemented)
3. Health check integration (when feature implemented)

## References

### Related Documentation
- **Testing Philosophy:** `docs/guides/testing/TESTING.md`
- **Security Guide:** `docs/guides/infrastructure/CACHE.md#security`
- **Environment Detection:** `docs/guides/infrastructure/ENVIRONMENT_DETECTION.md`

### Related Code Files
- **Implementation:** `backend/app/core/startup/redis_security.py`
- **Contract:** `backend/contracts/core/startup/redis_security.pyi`
- **Environment Detection:** `backend/app/core/environment/`
- **Configuration:** `backend/app/core/config.py`

### Related Test Plans
- **Cryptography Unavailability:** `backend/tests/integration/startup/TEST_PLAN_cryptography_unavailable.md`
- **Health Check Integration:** `backend/tests/integration/health/TEST_PLAN.md`
- **Cache Encryption Integration:** `backend/tests/integration/cache/TEST_PLAN.md`
