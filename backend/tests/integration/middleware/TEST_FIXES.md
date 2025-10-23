# Integration Test Fixes - Logging Redaction Integration

**Component**: Request Logging Middleware → Sensitive Data Redaction Integration
**Test Plan**: `TEST_PLAN_FINAL.md` - SEAM 9
**Test File**: `test_logging_redaction_integration.py`
**Analysis Date**: 2025-01-23

---

## Summary

**Total Issues**: 3 (all skipped tests)
- Blocker: 0
- Critical: 0
- Important: 3
- Minor: 0

**By Category**:
- Category A (Test Logic): 0
- Category B (Fixtures): 3
- Category C (Production Code): 0
- Category D (Reclassify E2E): 0
- Category E (Intentional Skip): 0

**Test Status**: 4 passed, 3 skipped

---

## Important Issues

### Issue #1: Request Body Redaction Test Requires Authenticated Endpoint

**File**: `test_logging_redaction_integration.py:317`
**Test Name**: `test_response_body_redaction_for_sensitive_data`
**Category**: B (Fixture Issue)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] tests/integration/middleware/test_logging_redaction_integration.py:317: 
Test requires POST request to authenticated endpoint - requires production code changes 
to enable testing of request body redaction without valid API keys
```

**Expected Behavior**:
Test should validate that response body redaction works correctly for sensitive data in API responses, verifying that response metadata (status, size, timing) is preserved while sensitive fields are redacted from logs.

**Root Cause Analysis**:
The test attempts to POST to `/v1/text_processing/process` which is an authenticated endpoint. The current test fixture `test_client_with_logging` uses `API_KEY=test-api-key-12345` but the request doesn't include proper authentication headers. The test design requires a valid API key to test response body logging, but this creates coupling between authentication testing and logging middleware testing.

**Testing Philosophy Violation**:
- **Issue**: Test is coupled to authentication infrastructure instead of testing logging behavior in isolation
- **Problem**: Integration test should test logging middleware behavior, not authentication requirements
- **Solution**: Need fixture that provides authenticated test client OR test endpoint that doesn't require authentication

**Recommended Fix**:
- [x] **Action 1**: Create new fixture `authenticated_test_client_with_logging` that includes valid API key headers
- [x] **Action 2**: Update test to use authenticated client fixture
- [x] **Action 3**: Alternative: Create test-only endpoint that doesn't require authentication but returns response with sensitive data
- [x] **Action 4**: Verify response body logging configuration is enabled in test settings

**Fixture Solution (Recommended)**:
```python
# In tests/integration/middleware/conftest.py

@pytest.fixture(scope="function")
def authenticated_test_client_with_logging(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """
    Test client with logging enabled and valid authentication headers.
    
    Provides authenticated test client for testing middleware behavior
    that requires authentication without coupling to authentication testing.
    """
    # Set test configuration with logging enabled
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")
    monkeypatch.setenv("REQUEST_LOGGING_ENABLED", "true")
    monkeypatch.setenv("PERFORMANCE_MONITORING_ENABLED", "true")
    monkeypatch.setenv("LOG_REQUEST_BODIES", "true")   # Enable body logging
    monkeypatch.setenv("LOG_RESPONSE_BODIES", "true")  # Enable response logging
    
    # Create fresh app with logging configuration
    app = create_app()
    
    # Create client with default authentication headers
    client = TestClient(app, raise_server_exceptions=False)
    
    # Monkey-patch client to include auth headers automatically
    original_request = client.request
    def request_with_auth(*args, **kwargs):
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        if 'authorization' not in kwargs['headers']:
            kwargs['headers']['Authorization'] = 'Bearer test-api-key-12345'
        return original_request(*args, **kwargs)
    
    client.request = request_with_auth
    return client
```

**Test Update**:
```python
def test_response_body_redaction_for_sensitive_data(
    authenticated_test_client_with_logging: TestClient, 
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test response body redaction (now uses authenticated client)."""
    # Test implementation remains the same
    # Client automatically includes authentication headers
```

**Contract References**:
- Public Contract: `request_logging.pyi:100-139` - `dispatch()` method behavior
- Test Plan: `TEST_PLAN_FINAL.md` - SEAM 9, Scenario 3 (Request body redaction)

**Testing Philosophy Check**:
- [x] Does test verify observable behavior (not internal state)? YES - Tests log output
- [x] Does test use high-fidelity fakes (not mocks)? YES - Uses real middleware and caplog
- [x] Does test validate business value (not implementation details)? YES - Security compliance
- [ ] Is test properly isolated from authentication concerns? NO - Currently coupled

---

### Issue #2: Structured Redaction Patterns Test Requires Authenticated Endpoint

**File**: `test_logging_redaction_integration.py:398`
**Test Name**: `test_structured_redaction_patterns_work_correctly`
**Category**: B (Fixture Issue)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] tests/integration/middleware/test_logging_redaction_integration.py:398: 
Test requires POST request to authenticated endpoint - requires production code changes 
to enable testing of structured redaction patterns without valid API keys
```

**Expected Behavior**:
Test should validate that structured redaction patterns work correctly for nested JSON data structures, verifying that sensitive fields are redacted at all nesting levels while non-sensitive fields are preserved.

**Root Cause Analysis**:
Same root cause as Issue #1 - test attempts to POST to authenticated endpoint `/v1/text_processing/process` without proper authentication headers. The test is designed to validate recursive redaction through complex object hierarchies, but requires authentication to reach the endpoint.

**Testing Philosophy Violation**:
- **Issue**: Same as Issue #1 - coupling to authentication infrastructure
- **Problem**: Integration test should test logging middleware redaction patterns, not endpoint security
- **Solution**: Same as Issue #1 - need authenticated fixture or test-specific endpoint

**Recommended Fix**:
- [x] **Action 1**: Use the same `authenticated_test_client_with_logging` fixture from Issue #1
- [x] **Action 2**: Update test signature to use authenticated client fixture
- [x] **Action 3**: Verify request body logging is configured to capture nested structures
- [x] **Action 4**: Consider adding validation that redaction works at all nesting depths

**Test Update**:
```python
def test_structured_redaction_patterns_work_correctly(
    authenticated_test_client_with_logging: TestClient,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test structured redaction patterns for nested data (now authenticated)."""
    # Test implementation remains the same
    # Uses authenticated client to reach endpoint
```

**Additional Validation Needed**:
```python
# After test body, add explicit depth validation
def test_redaction_depth_validation(
    authenticated_test_client_with_logging: TestClient,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Validate redaction works at various nesting depths."""
    test_cases = [
        # Depth 1: {"password": "secret"}
        {"password": "level1-secret"},
        
        # Depth 2: {"user": {"password": "secret"}}
        {"user": {"password": "level2-secret"}},
        
        # Depth 3: {"user": {"auth": {"password": "secret"}}}
        {"user": {"auth": {"password": "level3-secret"}}},
        
        # Depth 4+: even deeper nesting
        {"a": {"b": {"c": {"password": "level4-secret"}}}},
    ]
    
    for depth, test_data in enumerate(test_cases, start=1):
        caplog.clear()
        with caplog.at_level("INFO", logger="app.core.middleware.request_logging"):
            response = authenticated_test_client_with_logging.post(
                "/v1/text_processing/process",
                json=test_data
            )
        
        # Verify secret not leaked at any depth
        all_logs = " ".join([record.message for record in caplog.records])
        assert f"level{depth}-secret" not in all_logs, \
            f"Redaction failed at nesting depth {depth}"
```

**Contract References**:
- Public Contract: `request_logging.pyi:100-139` - `dispatch()` method with body logging
- Test Plan: `TEST_PLAN_FINAL.md` - SEAM 9, Scenario 3 (Structured redaction)

**Testing Philosophy Check**:
- [x] Does test verify observable behavior (not internal state)? YES - Tests log output
- [x] Does test use high-fidelity fakes (not mocks)? YES - Uses real middleware
- [x] Does test validate business value (not implementation details)? YES - Security for complex data
- [ ] Is test properly isolated from authentication concerns? NO - Currently coupled

---

### Issue #3: Error Logging Redaction Test Requires Authenticated Endpoint

**File**: `test_logging_redaction_integration.py:588`
**Test Name**: `test_redaction_doesnt_break_error_logging`
**Category**: B (Fixture Issue)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] tests/integration/middleware/test_logging_redaction_integration.py:588: 
Test requires POST request to authenticated endpoint - requires production code changes 
to enable testing of error logging with sensitive data without valid API keys
```

**Expected Behavior**:
Test should validate that sensitive data redaction works correctly even in error scenarios, ensuring that error logging maintains correlation IDs and debugging information while redacting sensitive data from error logs.

**Root Cause Analysis**:
Same root cause as Issues #1 and #2 - test includes scenarios that POST to authenticated endpoints. The test is designed to validate error handling with redaction across multiple error types (404, 405, 422), but some scenarios require authentication.

**Testing Philosophy Violation**:
- **Issue**: Same coupling to authentication infrastructure
- **Problem**: Error logging redaction should be testable independently of authentication
- **Solution**: Mix of authenticated and unauthenticated error scenarios

**Recommended Fix**:
- [x] **Action 1**: Split test into authenticated and unauthenticated scenarios
- [x] **Action 2**: Use `authenticated_test_client_with_logging` for 422 validation error scenario
- [x] **Action 3**: Use regular `test_client_with_logging` for 404 and 405 scenarios (no auth needed)
- [x] **Action 4**: Verify error logs include correlation IDs but redact sensitive data

**Test Refactoring (Recommended)**:
```python
def test_redaction_in_unauthenticated_error_logs(
    test_client_with_logging: TestClient,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test redaction works for errors that don't require authentication."""
    error_requests = [
        # Request with invalid endpoint (404) - no auth required
        {
            "url": "/v1/nonexistent",
            "method": "get",
            "headers": {"Authorization": "Bearer error-token-404"}
        },
        # Request with invalid method (405) - no auth required
        {
            "url": "/v1/health",
            "method": "patch",
            "headers": {"X-API-Key": "error-key-405"}
        }
    ]
    
    for request_config in error_requests:
        caplog.clear()
        with caplog.at_level("INFO", logger="app.core.middleware.request_logging"):
            if request_config["method"] == "get":
                response = test_client_with_logging.get(
                    request_config["url"],
                    headers=request_config["headers"]
                )
            elif request_config["method"] == "patch":
                response = test_client_with_logging.patch(
                    request_config["url"],
                    headers=request_config["headers"]
                )
        
        # Verify error response
        assert response.status_code >= 400
        
        # Verify sensitive data redacted from error logs
        all_logs = [record.message for record in caplog.records]
        for log_message in all_logs:
            if "error-token-404" in request_config["headers"].get("Authorization", ""):
                assert "error-token-404" not in log_message
            if "error-key-405" in request_config["headers"].get("X-API-Key", ""):
                assert "error-key-405" not in log_message
        
        # Verify correlation ID present
        correlation_found = any("[req_id:" in log for log in all_logs)
        assert correlation_found


def test_redaction_in_authenticated_error_logs(
    authenticated_test_client_with_logging: TestClient,
    caplog: pytest.LogCaptureFixture
) -> None:
    """Test redaction works for validation errors on authenticated endpoints."""
    # Request with invalid data (422) - requires auth
    error_request = {
        "url": "/v1/text_processing/process",
        "method": "post",
        "json": {"invalid_field": "test", "password": "error-pass-422"}
    }
    
    caplog.clear()
    with caplog.at_level("INFO", logger="app.core.middleware.request_logging"):
        response = authenticated_test_client_with_logging.post(
            error_request["url"],
            json=error_request["json"]
        )
    
    # Verify error response (422 or 400)
    assert response.status_code >= 400
    
    # Verify password redacted from error logs
    all_logs = [record.message for record in caplog.records]
    for log_message in all_logs:
        assert "error-pass-422" not in log_message, \
            "Password not redacted from validation error logs"
    
    # Verify correlation ID present in error logs
    correlation_found = any("[req_id:" in log for log in all_logs)
    assert correlation_found, "Correlation ID missing from error logs"
```

**Contract References**:
- Public Contract: `request_logging.pyi:100-139` - `dispatch()` exception handling
- Test Plan: `TEST_PLAN_FINAL.md` - SEAM 9, Scenario 1-2 (Header and query redaction)

**Testing Philosophy Check**:
- [x] Does test verify observable behavior (not internal state)? YES - Tests log output
- [x] Does test use high-fidelity fakes (not mocks)? YES - Uses real error handling
- [x] Does test validate business value (not implementation details)? YES - Error security
- [ ] Is test properly isolated from authentication concerns? NO - Needs splitting

---

## Implementation Recommendations

### Phase 1: Fixture Creation (Immediate - 30 minutes)

**Priority: HIGH - Blocks all 3 skipped tests**

1. **Create `authenticated_test_client_with_logging` fixture** in `conftest.py`
   - Add fixture with automatic authentication header injection
   - Configure body logging environment variables
   - Enable request/response body logging in settings
   - Test fixture with simple authenticated request

2. **Verify fixture isolation**
   - Test that fixture creates fresh app per test (function scope)
   - Test that authentication headers are properly included
   - Test that body logging is enabled in configuration

### Phase 2: Test Updates (Short-term - 1 hour)

**Priority: HIGH - Enables all security compliance tests**

1. **Update Issue #1 test** (`test_response_body_redaction_for_sensitive_data`)
   - Change fixture from `test_client_with_logging` to `authenticated_test_client_with_logging`
   - Remove `@pytest.mark.skip` decorator
   - Run test and verify it passes
   - Verify response body logging captures and redacts sensitive data

2. **Update Issue #2 test** (`test_structured_redaction_patterns_work_correctly`)
   - Change fixture from `test_client_with_logging` to `authenticated_test_client_with_logging`
   - Remove `@pytest.mark.skip` decorator
   - Run test and verify nested redaction works correctly
   - Add depth validation assertions

3. **Split Issue #3 test** (`test_redaction_doesnt_break_error_logging`)
   - Create `test_redaction_in_unauthenticated_error_logs` for 404/405 scenarios
   - Create `test_redaction_in_authenticated_error_logs` for 422 scenarios
   - Remove original `@pytest.mark.skip` decorator
   - Run both new tests and verify they pass

### Phase 3: Validation (Medium-term - 30 minutes)

**Priority: MEDIUM - Ensure comprehensive coverage**

1. **Run full test suite**
   ```bash
   cd backend
   ../.venv/bin/python -m pytest tests/integration/middleware/test_logging_redaction_integration.py -v
   ```
   Expected: 7 passed, 0 skipped (4 existing + 3 newly enabled)

2. **Verify test isolation**
   ```bash
   # Run with randomization to verify isolation
   cd backend
   ../.venv/bin/python -m pytest tests/integration/middleware/test_logging_redaction_integration.py -v --randomly-seed=12345
   ```
   Expected: All tests pass regardless of execution order

---

## Common Patterns Identified

### Pattern 1: Authentication Coupling in Middleware Tests

**Issue**: Multiple tests require authenticated endpoints to test middleware behavior, creating unnecessary coupling between middleware integration tests and authentication infrastructure.

**Impact**: Tests become brittle and harder to maintain. Middleware behavior testing is blocked by authentication requirements that aren't related to the middleware under test.

**Solution**: 
- Create authenticated test client fixtures that handle authentication automatically
- Separate authentication testing from middleware behavior testing
- Use test-specific endpoints that don't require authentication when possible

### Pattern 2: Missing Body Logging Configuration

**Issue**: Tests assume request/response body logging is enabled but don't explicitly configure it in test settings.

**Impact**: Tests may fail or skip due to missing configuration even when the underlying middleware works correctly.

**Solution**:
- Explicitly configure body logging in test fixtures
- Add environment variables: `LOG_REQUEST_BODIES=true`, `LOG_RESPONSE_BODIES=true`
- Document body logging requirements in fixture docstrings

### Pattern 3: Test Fixture Reuse Limitations

**Issue**: Existing `test_client_with_logging` fixture doesn't include authentication headers, limiting its reuse for authenticated endpoint testing.

**Impact**: Tests must create their own authentication headers or skip testing authenticated scenarios.

**Solution**:
- Create specialized fixtures for common testing scenarios (authenticated + logging)
- Use fixture composition: base fixture + authentication wrapper
- Document fixture capabilities and limitations

---

## Testing Philosophy Compliance

**Behavior vs. Implementation**: ✅ GOOD
- All tests verify observable log output, not internal middleware state
- Tests check for sensitive data absence in logs (security outcome)
- Tests validate correlation ID presence (functionality outcome)

**High-Fidelity Fakes**: ✅ GOOD
- Tests use real middleware with actual logging configuration
- Tests use pytest's `caplog` for realistic log capture
- No mocking of logging internals or redaction logic

**Business Value Focus**: ✅ GOOD
- Tests validate security compliance (sensitive data protection)
- Tests ensure debugging capabilities (correlation IDs maintained)
- Tests verify operational requirements (error logging works with redaction)

**Test Isolation**: ⚠️ NEEDS IMPROVEMENT
- Tests currently coupled to authentication infrastructure
- Fixture improvements will resolve isolation issues
- After fixes, tests will be properly isolated

---

## Next Steps

1. ✅ Review recommendations with team
2. ⏭️ Implement Phase 1: Create `authenticated_test_client_with_logging` fixture
3. ⏭️ Implement Phase 2: Update all 3 skipped tests
4. ⏭️ Implement Phase 3: Run validation and verify coverage
5. ⏭️ Document fixture usage patterns in `conftest.py`
6. ⏭️ Update test plan status to reflect completed tests

**Estimated Total Time**: ~2 hours
- Fixture creation: 30 minutes
- Test updates: 1 hour
- Validation and documentation: 30 minutes

---

## Success Criteria

- ✅ All 3 skipped tests are enabled and passing
- ✅ Tests run with `pytest-randomly` without failures
- ✅ Test coverage for request body logging increases
- ✅ Tests properly isolated from authentication concerns
- ✅ Fixture pattern documented for future test development
- ✅ No regression in existing 4 passing tests

**Final Target**: 7 passed, 0 skipped in `test_logging_redaction_integration.py`

---

**Status**: ✅ Analysis Complete - Ready for Implementation
**Last Updated**: 2025-01-23
**Next Action**: Create `authenticated_test_client_with_logging` fixture
