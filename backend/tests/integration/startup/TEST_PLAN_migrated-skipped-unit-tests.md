# Integration Test Plan: Migrated Skipped Unit Tests

## Overview

This test plan addresses 4 skipped unit tests from `test_production_security.py` that were identified as requiring integration testing rather than unit testing with mocks. These tests verify critical environment-aware security validation flows.

## Analysis: Why Integration Tests?

The skipped tests involve **multi-component collaboration** that cannot be properly tested with mocks:

**Critical Seam**: RedisSecurityValidator ↔ get_environment_info() ↔ Environment Configuration

This integration validates:
1. Environment detection accuracy (development/staging/production)
2. Security rule application based on detected environment
3. Error messaging quality and actionable guidance
4. Override mechanism behavior with appropriate warnings

**Why Not Unit Tests?**
- Environment mocking bypasses real environment detection logic
- Tests should verify the **actual collaboration** between components
- Security validation depends on **real environment state interpretation**
- Error messages include **environment-specific details** from real detection

## Integration Test Plan

### PRIORITY: HIGH (Security Critical)

---

## 1. SEAM: Comprehensive Error Message Validation in Production

**SEAM NAME**: Production Security Error → Complete Fix Guidance Generation

**COMPONENTS**:
- RedisSecurityValidator.validate_production_security()
- get_environment_info() (real environment detection)
- ConfigurationError exception with formatted guidance

**CRITICAL PATH**:
Production Environment Detection → Insecure URL Validation → ConfigurationError → Fix Options Generation

**TEST SCENARIOS**:

1. **Complete Fix Options Verification**
   ```
   Given: Production environment detected via environment variables
   And: Insecure Redis URL (redis://host:6379)
   When: validate_production_security() is called
   Then: ConfigurationError includes ALL THREE documented fix options:
         - Option 1: Switch to TLS (rediss://)
         - Option 2: Use authenticated connection
         - Option 3: Use insecure override (with warnings)
   And: Each option includes specific configuration examples
   And: Error message is actionable and complete
   ```

2. **Error Message Structure Validation**
   ```
   Given: Production environment
   And: Insecure Redis URL
   When: ConfigurationError is raised
   Then: Error message contains:
         - Clear problem statement
         - Environment detection details (confidence level)
         - Complete fix guidance section
         - Code examples for each fix option
         - Security implications explanation
   ```

**INFRASTRUCTURE NEEDS**:
- monkeypatch for environment variable manipulation
- Real RedisSecurityValidator instance
- No mocks - test actual error message generation

**PRIORITY**: HIGH (Security + Developer Experience)

**SUCCESS CRITERIA**:
- [ ] ConfigurationError contains all three fix options
- [ ] Each fix option includes code examples
- [ ] Environment confidence level is included
- [ ] Error message is developer-friendly and actionable
- [ ] Security implications are clearly explained

**IMPLEMENTATION FILE**: `test_environment_aware_security.py`

**EXISTING COVERAGE**: Partial - current integration test verifies error is raised but doesn't check complete fix options

---

## 2. SEAM: Insecure Override Warning Content Validation

**SEAM NAME**: Production Override → Infrastructure Security Checklist Warning

**COMPONENTS**:
- RedisSecurityValidator.validate_production_security()
- Logging system
- get_environment_info()
- insecure_override parameter handling

**CRITICAL PATH**:
Production Environment → Insecure URL + Override Flag → Security Warning → Checklist Generation

**TEST SCENARIOS**:

1. **Complete Security Checklist Verification**
   ```
   Given: Production environment detected
   And: Insecure Redis URL with insecure_override=True
   When: validate_production_security() is called
   Then: Security warning includes infrastructure security checklist:
         - Network isolation requirements
         - Firewall configuration requirements
         - VPC/private network requirements
         - Access control requirements
         - Monitoring and audit requirements
   And: Warning emphasizes production risk
   ```

2. **Warning Severity and Visibility**
   ```
   Given: Production + insecure override
   When: Warning is logged
   Then: Warning uses WARNING or ERROR log level
   And: Warning includes "SECURITY WARNING" prefix
   And: Warning is prominently formatted
   And: Warning includes business risk explanation
   ```

**INFRASTRUCTURE NEEDS**:
- monkeypatch for environment variables
- caplog fixture to capture log messages
- Real RedisSecurityValidator instance

**PRIORITY**: HIGH (Security + Compliance)

**SUCCESS CRITERIA**:
- [ ] Warning includes complete infrastructure security checklist
- [ ] All checklist items are present and specific
- [ ] Warning severity is appropriate (WARNING/ERROR level)
- [ ] Business risk is clearly communicated
- [ ] Warning is prominently formatted for visibility

**IMPLEMENTATION FILE**: `test_environment_aware_security.py`

**EXISTING COVERAGE**: Partial - current test verifies warning exists but not checklist content

---

## 3. SEAM: Staging Environment Security Validation Flow

**SEAM NAME**: Staging Environment Detection → Flexible Security Enforcement

**COMPONENTS**:
- RedisSecurityValidator.validate_production_security()
- get_environment_info() (staging environment detection)
- Security rule application logic

**CRITICAL PATH**:
Staging Environment Variables → Environment Detection → Security Rule Selection → Validation Behavior

**TEST SCENARIOS**:

1. **Staging Environment Bypasses Strict Enforcement**
   ```
   Given: Staging environment detected (ENVIRONMENT=staging)
   And: Insecure Redis URL (redis://host:6379)
   When: validate_production_security() is called
   Then: No ConfigurationError is raised
   And: Validation completes successfully
   And: Staging is treated as non-production environment
   ```

2. **Staging Accepts Both Secure and Insecure URLs**
   ```
   Given: Staging environment
   When: Validating secure URL (rediss://host:6380)
   Then: Validation succeeds
   When: Validating insecure URL (redis://host:6379)
   Then: Validation also succeeds
   And: Both are treated equally in staging
   ```

3. **Staging vs Production Behavior Distinction**
   ```
   Given: Same insecure Redis URL
   When: Tested in staging environment
   Then: Validation succeeds
   When: Tested in production environment
   Then: ConfigurationError is raised
   And: Demonstrates environment-specific security rules
   ```

**INFRASTRUCTURE NEEDS**:
- monkeypatch for environment variables
- Real RedisSecurityValidator instances
- No mocks - test real environment detection

**PRIORITY**: HIGH (Deployment Flexibility + Security Posture)

**SUCCESS CRITERIA**:
- [ ] Staging environment bypasses TLS enforcement
- [ ] Both secure and insecure URLs accepted in staging
- [ ] Staging behavior differs from production
- [ ] Staging behavior differs from development
- [ ] Environment detection correctly identifies staging

**IMPLEMENTATION FILE**: `test_environment_aware_security.py`

**EXISTING COVERAGE**: None - staging tests missing entirely from integration suite

**NOTE**: Similar staging test exists in `test_authentication_validation.py` - use consistent pattern

---

## 4. SEAM: Staging Environment Informational Messaging

**SEAM NAME**: Staging Detection → Informational Logging → Security Awareness

**COMPONENTS**:
- RedisSecurityValidator.validate_production_security()
- Logging system
- get_environment_info() (staging detection)

**CRITICAL PATH**:
Staging Environment → Security Validation → Informational Message → Developer Guidance

**TEST SCENARIOS**:

1. **Staging Informational Message Content**
   ```
   Given: Staging environment detected
   And: Insecure Redis URL
   When: validate_production_security() is called
   Then: INFO-level log message is generated
   And: Message explains staging security flexibility
   And: Message mentions TLS is optional in staging
   And: Message encourages TLS testing for production readiness
   ```

2. **Staging Message vs Development Message**
   ```
   Given: Staging environment
   When: Informational message is logged
   Then: Message is specific to staging context
   And: Message differs from development mode message
   And: Message emphasizes pre-production testing
   And: Message suggests production-like security testing
   ```

3. **Message Tone and Guidance Quality**
   ```
   Given: Staging environment with insecure URL
   When: Informational message is logged
   Then: Tone is informative, not warning/alarming
   And: Message provides actionable TLS testing guidance
   And: Message balances flexibility with security awareness
   ```

**INFRASTRUCTURE NEEDS**:
- monkeypatch for environment variables
- caplog fixture for log message capture
- Real RedisSecurityValidator instance

**PRIORITY**: MEDIUM (Developer Experience + Security Education)

**SUCCESS CRITERIA**:
- [ ] INFO-level log message generated for staging
- [ ] Message explains staging security flexibility
- [ ] Message encourages TLS testing
- [ ] Message tone is informative, not alarming
- [ ] Message differs from development mode messaging

**IMPLEMENTATION FILE**: `test_environment_aware_security.py`

**EXISTING COVERAGE**: None - staging logging tests missing

---

## Implementation Strategy

### Phase 1: Complete Fix Options Test (Highest Priority)
Enhance existing integration test to verify complete error message content:

```python
def test_production_error_includes_all_fix_options(monkeypatch):
    """
    Test that production security error includes all documented fix options.

    Integration Scope:
        RedisSecurityValidator → get_environment_info() → ConfigurationError generation

    Business Impact:
        Ensures developers receive complete, actionable guidance when security
        validation fails, reducing time to resolution

    Test Strategy:
        - Set production environment via monkeypatch
        - Trigger validation with insecure URL
        - Verify ConfigurationError contains all three fix options
        - Verify each option includes code examples

    Success Criteria:
        - Error includes "Option 1: Switch to TLS"
        - Error includes "Option 2: Use authenticated connection"
        - Error includes "Option 3: Use insecure override"
        - Each option includes specific configuration examples
        - Environment detection details are included
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

    validator = RedisSecurityValidator()

    with pytest.raises(ConfigurationError) as exc_info:
        validator.validate_production_security("redis://redis:6379")

    error_message = str(exc_info.value)

    # Verify all three fix options are present
    assert "How to fix this:" in error_message or "Fix options:" in error_message

    # Option 1: TLS
    assert "rediss://" in error_message
    assert "TLS" in error_message

    # Option 2: Authentication
    assert "authenticated" in error_message.lower()
    assert "redis://user:password@" in error_message or "credentials" in error_message.lower()

    # Option 3: Override
    assert "insecure_override" in error_message.lower()
    assert "override" in error_message.lower()

    # Verify environment detection details
    assert "environment" in error_message.lower()
    assert "production" in error_message.lower()
```

### Phase 2: Override Warning Checklist Test
Add new test for infrastructure security checklist:

```python
def test_production_override_warning_includes_security_checklist(
    monkeypatch, caplog
):
    """
    Test that insecure override warning includes infrastructure security checklist.

    Integration Scope:
        Production detection → Override mechanism → Warning generation → Checklist

    Business Impact:
        Ensures operators understand minimum security requirements when using
        insecure override, maintaining security awareness and compliance

    Success Criteria:
        - Warning includes network isolation requirements
        - Warning includes firewall configuration guidance
        - Warning includes VPC/private network requirements
        - Warning includes access control requirements
        - Warning includes monitoring requirements
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")

    validator = RedisSecurityValidator()

    with caplog.at_level(logging.WARNING):
        validator.validate_production_security(
            "redis://redis:6379", insecure_override=True
        )

    warning_messages = [
        record.message
        for record in caplog.records
        if record.levelno == logging.WARNING
    ]

    assert len(warning_messages) > 0, "Expected security warning to be logged"

    # Combine all warning messages for comprehensive check
    full_warning = " ".join(warning_messages)

    # Verify infrastructure security checklist items
    assert "network" in full_warning.lower() or "isolation" in full_warning.lower()
    assert "firewall" in full_warning.lower() or "security group" in full_warning.lower()
    assert "vpc" in full_warning.lower() or "private network" in full_warning.lower()
    assert "access control" in full_warning.lower() or "authentication" in full_warning.lower()
    assert "monitoring" in full_warning.lower() or "audit" in full_warning.lower()
```

### Phase 3: Staging Environment Tests
Add comprehensive staging environment tests:

```python
def test_staging_environment_bypasses_tls_enforcement(monkeypatch):
    """
    Test that staging environment allows flexible security like development.

    Integration Scope:
        Staging environment detection → Security rule application → Flexible validation

    Business Impact:
        Enables staging deployments to test configurations without mandatory TLS,
        supporting varied deployment scenarios while maintaining production security
    """
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    validator = RedisSecurityValidator()

    # Should not raise ConfigurationError for insecure URL in staging
    validator.validate_production_security("redis://redis:6379")

    # Test passes if no exception raised

def test_staging_environment_logs_informational_message(monkeypatch, caplog):
    """
    Test that staging environment logs appropriate informational message.

    Integration Scope:
        Staging detection → Informational logging → Developer guidance

    Business Impact:
        Communicates security expectations for staging while allowing
        deployment flexibility and encouraging TLS testing
    """
    monkeypatch.setenv("ENVIRONMENT", "staging")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)

    validator = RedisSecurityValidator()

    with caplog.at_level(logging.INFO):
        validator.validate_production_security("redis://redis:6379")

    info_messages = [
        record.message
        for record in caplog.records
        if record.levelno == logging.INFO
    ]

    assert any("staging" in msg.lower() for msg in info_messages)
    assert any(
        "tls" in msg.lower() or "security" in msg.lower()
        for msg in info_messages
    )
    assert any(
        "optional" in msg.lower() or "flexible" in msg.lower()
        for msg in info_messages
    )
```

### Phase 4: Validation and Documentation
1. **Run all integration tests** to ensure new tests work with existing suite
2. **Update README.md** to document new test coverage
3. **Remove skipped unit tests** once integration coverage is complete
4. **Update test counts** in integration test documentation

## Test Execution Strategy

### Running the New Tests

```bash
# Run all new staging-related tests
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py -v -k 'staging'"

# Run complete fix options test
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::test_production_error_includes_all_fix_options -v"

# Run override warning checklist test
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py::test_production_override_warning_includes_security_checklist -v"

# Run all environment-aware security integration tests
make test-backend PYTEST_ARGS="tests/integration/startup/test_environment_aware_security.py -v"
```

### Success Metrics

**Coverage Enhancement**:
- ✅ Production error messages: Complete fix options verified (upgrade from partial)
- ✅ Override warnings: Infrastructure security checklist verified (upgrade from partial)
- ✅ Staging environment: Full validation flow covered (new coverage)
- ✅ Staging logging: Informational messaging verified (new coverage)

**Test Quality**:
- All tests use real environment detection (no mocks)
- All tests use monkeypatch for environment isolation
- All tests verify observable behavior (error messages, logs)
- All tests are fast (< 100ms per test)

**Documentation Quality**:
- Each test has comprehensive integration-focused docstring
- Business impact clearly stated
- Integration scope explicitly defined
- Success criteria enumerated

## Migration Path

### Step 1: Implement New Integration Tests (This Plan)
- Add 4 new integration tests to `test_environment_aware_security.py`
- Verify all tests pass with real environment detection
- Document coverage improvements

### Step 2: Verify Coverage Completeness
- Run all integration tests to confirm coverage
- Compare with original skipped unit tests
- Ensure all behaviors are now tested

### Step 3: Remove Skipped Unit Tests
- Delete skipped tests from `test_production_security.py`
- Update unit test documentation
- Update test count expectations

### Step 4: Documentation Updates
- Update `backend/tests/integration/startup/README.md`
- Add new test scenarios to success criteria
- Update test count and coverage metrics

## Related Documentation

- **Integration Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md`
- **Existing Integration Tests**: `backend/tests/integration/startup/README.md`
- **Environment Testing Pattern**: `backend/CLAUDE.md` - Environment Variable Testing
- **Startup Test Plan**: `backend/tests/integration/startup/TEST_PLAN.md`

## Conclusion

All 4 skipped unit tests are **true integration test opportunities** that validate critical environment-aware security flows. They test the collaboration between:
- Environment detection (get_environment_info)
- Security validation (RedisSecurityValidator)
- Error messaging and logging systems

These tests belong in the integration suite because they verify **real multi-component behavior** that cannot be properly tested with mocks. The test plan provides comprehensive coverage while following integration testing best practices.
