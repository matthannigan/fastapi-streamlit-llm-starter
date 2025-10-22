# Integration Test Fixes

**Component**: Resilience Infrastructure Integration Tests
**Test Plan**: `backend/tests/integration/resilience/TEST_PLAN.md`
**Analysis Date**: 2025-10-22

## Summary

**Total Issues**: 10
- Blocker: 1
- Critical: 4
- Important: 4
- Minor: 1

**By Category**:
- Category A (Test Logic): 1
- Category B (Fixtures): 5
- Category C (Production Code): 0
- Category D (Reclassify E2E): 0
- Category E (Intentional Skip): 4

---

## Blockers (Fix First)

### Issue #1: Environment Auto-Detection Test Failure

**File**: `test_config_environment_integration.py:220`
**Test Name**: `test_preset_recommendation_api_auto_detects_environment`
**Category**: A (Test Logic)
**Severity**: Blocker

**Observed Behavior**:
```
FAILED backend/tests/integration/resilience/test_config_environment_integration.py::TestConfigEnvironmentIntegration::test_preset_recommendation_api_auto_detects_environment - AssertionError: Expected staging or unknown detection, got: Environment.DEVELOPMENT (auto-detected)
```

**Expected Behavior**:
Test sets staging environment indicators (`ENVIRONMENT=staging-environment-v2`, `DEPLOYMENT_STAGE=staging`) and expects environment detection to identify this as staging or unknown. However, the system detects it as DEVELOPMENT.

**Root Cause Analysis**:
The test uses `resilience_test_client` fixture which explicitly sets `ENVIRONMENT=testing` in conftest.py line 115, overriding the test's monkeypatch settings. This violates the App Factory Pattern - the test modifies environment variables AFTER the app is already created.

**Critical Pattern Violation**:
```python
# In conftest.py lines 94-121
@pytest.fixture(scope="function")
def resilience_test_client(monkeypatch, resilience_test_settings):
    # Sets ENVIRONMENT="testing" AFTER settings already created
    monkeypatch.setenv("ENVIRONMENT", "testing")  # Line 115
    app = create_app(settings_obj=resilience_test_settings)  # Uses pre-created settings
    return TestClient(app)

# In test (line 248)
monkeypatch.setenv("ENVIRONMENT", "staging-environment-v2")  # TOO LATE - app already exists
```

**Recommended Fix**:
- [ ] **Action 1**: Test must NOT use `resilience_test_client` fixture since it needs custom environment
- [ ] **Action 2**: Create app directly in test AFTER setting environment variables
- [ ] **Action 3**: Follow App Factory Pattern: environment setup → settings creation → app creation

**Correct Pattern**:
```python
def test_preset_recommendation_api_auto_detects_environment(
    self,
    monkeypatch: pytest.MonkeyPatch
):
    # Set environment FIRST
    monkeypatch.setenv("ENVIRONMENT", "staging-environment-v2")
    monkeypatch.setenv("DEPLOYMENT_STAGE", "staging")
    monkeypatch.setenv("API_KEY", "test-resilience-key-12345")
    
    # Create app AFTER environment setup
    app = create_app()
    test_client = TestClient(app)
    
    # Now test with correctly configured app
    response = test_client.get(...)
```

**Contract References**:
- Test Plan: `TEST_PLAN.md` - Seam #2 (Configuration Presets → Environment Detection)
- Pattern Documentation: `backend/CLAUDE.md` - App Factory Pattern section

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior (API response) - YES
- ✅ Does test use high-fidelity fakes - YES (real environment detection)
- ❌ Does test validate business value - YES, but implementation is broken

---

## Critical Issues

### Issue #2: Authentication Test Skipped

**File**: `test_api_resilience_orchestrator_integration.py:66`
**Test Name**: `test_circuit_breaker_endpoints_require_authentication`
**Category**: B (Fixture)
**Severity**: Critical

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:66: Test client fixture includes API key, causing authentication to pass
```

**Expected Behavior**:
Test should verify that resilience endpoints return 401 Unauthorized when accessed without authentication or with invalid credentials.

**Root Cause Analysis**:
The `resilience_test_client` fixture in conftest.py (line 94-121) always initializes the app with a valid API key (`API_KEY=test-resilience-key-12345`). This means authentication is globally enabled and the fixture doesn't provide a way to test unauthenticated requests.

**Recommended Fix**:
- [ ] **Action 1**: Create new fixture `unauthenticated_resilience_client` that creates app WITHOUT API key
- [ ] **Action 2**: Test should use `unauthenticated_resilience_client` for unauthenticated requests
- [ ] **Action 3**: Keep existing `resilience_test_client` for authenticated tests
- [ ] **Action 4**: May need `invalid_api_key_headers` fixture for invalid auth tests

**New Fixture Implementation**:
```python
@pytest.fixture(scope="function")
def unauthenticated_resilience_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Test client without authentication for testing auth requirements."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")
    # NO API_KEY set - authentication disabled
    
    app = create_app()
    return TestClient(app)

@pytest.fixture
def invalid_api_key_headers() -> Dict[str, str]:
    """Headers with invalid API key for auth testing."""
    return {
        "Authorization": "Bearer invalid-key-xyz",
        "Content-Type": "application/json"
    }
```

**Contract References**:
- Public Contract: `orchestrator.pyi` - All endpoints should require authentication
- Test Plan: `TEST_PLAN.md` - Seam #1, Scenario 1 (API authentication protects endpoints)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES (401 status codes)
- ✅ Does test use high-fidelity fakes - YES (real FastAPI auth)
- ✅ Does test validate business value - YES (security critical)

---

### Issue #3: Circuit Breaker Reset Test Skipped

**File**: `test_api_resilience_orchestrator_integration.py:392`
**Test Name**: `test_administrative_reset_works_through_real_circuit_breaker_state_changes`
**Category**: B (Fixture)
**Severity**: Critical

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:392: No circuit breakers available for reset testing
```

**Expected Behavior**:
Test should create circuit breakers, trigger failures to open them, then verify that administrative reset API successfully closes them.

**Root Cause Analysis**:
Test attempts to create circuit breakers by calling `real_text_processor_service.process_text()` (line 361), but:
1. The service may not actually create circuit breakers if AI service mock isn't properly configured
2. The `failing_ai_service` fixture isn't being used (it's in the test signature but not applied)
3. Circuit breaker creation depends on actual failures occurring, which may not happen with current mock setup

**Recommended Fix**:
- [ ] **Action 1**: Use `failing_ai_service` fixture to ensure operations actually fail
- [ ] **Action 2**: Pre-create circuit breakers in test setup by triggering multiple failures
- [ ] **Action 3**: Verify circuit breaker exists before attempting reset
- [ ] **Action 4**: Consider creating helper fixture that provides pre-failed circuit breakers

**Improved Test Implementation**:
```python
async def test_administrative_reset_works_through_real_circuit_breaker_state_changes(
    self,
    resilience_test_client,
    resilience_auth_headers,
    ai_resilience_orchestrator,
    failing_ai_service,  # Use this fixture
    real_text_processor_service
):
    # Force circuit breaker creation by triggering failures
    operation_name = "process_text"
    
    # Trigger multiple failures to create and potentially open circuit breaker
    for i in range(5):
        try:
            asyncio.run(real_text_processor_service.process_text(f"test {i}"))
        except Exception:
            pass  # Expected failures
    
    # Verify circuit breaker was created
    assert operation_name in ai_resilience_orchestrator.circuit_breakers, \
        "Circuit breaker should be created after operations"
    
    # Now test reset functionality...
```

**Contract References**:
- Public Contract: `orchestrator.pyi:477-492` - `reset_metrics()` method
- Test Plan: `TEST_PLAN.md` - Seam #1, Scenario 3 (Administrative reset functionality)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES (circuit breaker state changes)
- ✅ Does test use high-fidelity fakes - YES (real circuit breaker library)
- ✅ Does test validate business value - YES (operational management critical)

---

### Issue #4: AI Service Failure Test Skipped

**File**: `test_api_resilience_orchestrator_integration.py:398`
**Test Name**: `test_ai_service_failures_trigger_actual_circuit_breaker_opening`
**Category**: E (Intentional Skip)
**Severity**: Critical

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:398: Test requires complex AI service setup that conflicts with existing fixtures
```

**Expected Behavior**:
Test should verify that repeated AI service failures cause the circuit breaker to open through the actual circuitbreaker library.

**Root Cause Analysis**:
This is marked as intentional skip by developer. The note indicates fixture conflicts with AI service setup. Looking at the fixture structure:
1. The `failing_ai_service` fixture patches `app.services.text_processor.Agent` at import time
2. However, `real_text_processor_service` is created before this patch is applied
3. The service already has its Agent instance initialized with the real implementation

**Recommended Fix**:
- [ ] **Action 1**: This is actually **Category B (Fixture Issue)**, not Category E
- [ ] **Action 2**: Create fixture that provides TextProcessorService with pre-configured failing agent
- [ ] **Action 3**: OR modify test to patch Agent BEFORE creating real_text_processor_service
- [ ] **Action 4**: Consider factory fixture pattern for service creation with configurable agent

**Alternative Approach**:
```python
@pytest.fixture
async def text_processor_with_failing_ai(
    ai_resilience_orchestrator,
    resilience_test_settings,
    failing_ai_service
) -> AsyncGenerator[Any, None]:
    """TextProcessorService with pre-configured failing AI."""
    # Patch is already active from failing_ai_service fixture
    from app.services.text_processor import TextProcessorService
    from app.infrastructure.cache.memory import InMemoryCache
    
    # Service will pick up the mocked Agent
    service = TextProcessorService(
        settings=resilience_test_settings,
        cache=InMemoryCache(),
        ai_resilience=ai_resilience_orchestrator
    )
    yield service
```

**Contract References**:
- Public Contract: `orchestrator.pyi:265-305` - `get_or_create_circuit_breaker()` method
- Test Plan: `TEST_PLAN.md` - Seam #1, Scenario 4 (AI failures trigger circuit breaker)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES (circuit breaker state)
- ✅ Does test use high-fidelity fakes - YES (real circuitbreaker library)
- ✅ Does test validate business value - YES (core resilience functionality)

---

### Issue #5: Retry Logic Test Skipped

**File**: `test_api_resilience_orchestrator_integration.py:429`
**Test Name**: `test_retry_logic_respects_real_circuit_breaker_state`
**Category**: B (Fixture)
**Severity**: Critical

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:429: Flaky AI service fixture references non-existent PydanticAIAgent
```

**Expected Behavior**:
Test should verify that tenacity retry logic coordinates properly with circuit breaker state - operations should fail fast when circuit breaker is open.

**Root Cause Analysis**:
The skip reason indicates `flaky_ai_service` fixture has incorrect implementation. Looking at conftest.py line 409-451:
```python
@pytest.fixture
def flaky_ai_service():
    with patch('app.services.text_processor.Agent') as mock_class:
        # This patch is correct
```

However, the skip message mentions "PydanticAIAgent" which doesn't exist. This suggests:
1. Test was written expecting different AI service implementation
2. Codebase uses `Agent` from pydantic-ai, not `PydanticAIAgent`
3. Fixture is correct, skip reason is outdated

**Recommended Fix**:
- [ ] **Action 1**: Remove skip decorator - fixture appears to be correct
- [ ] **Action 2**: Verify `flaky_ai_service` fixture works with current implementation
- [ ] **Action 3**: If fixture doesn't work, apply same fix as Issue #4 (service creation timing)
- [ ] **Action 4**: Update skip reason if keeping skip for legitimate reason

**Contract References**:
- Public Contract: `orchestrator.pyi:367-454` - `with_resilience()` decorator with retry behavior
- Test Plan: `TEST_PLAN.md` - Seam #1, Scenario 5 (Retry logic respects circuit breaker)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES (retry behavior and fail-fast)
- ✅ Does test use high-fidelity fakes - YES (real tenacity and circuitbreaker)
- ✅ Does test validate business value - YES (coordination critical for resilience)

---

## Important Issues

### Issue #6: Text Processing Resilience Protection Test Skipped

**File**: `test_text_processing_resilience_integration.py:66`
**Test Name**: `test_text_processing_operations_protected_by_real_resilience_decorators`
**Category**: B (Fixture)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:66: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
```

**Expected Behavior**:
Test should verify that TextProcessorService operations are protected by real resilience decorators and that operations are tracked by the resilience orchestrator.

**Root Cause Analysis**:
Same root cause as Issues #4 and #5. The test comment (lines 92-99) explicitly states:
```python
# NOTE: This test is skipped because the current fixture structure doesn't properly
# mock the AI agent at service creation time. The TextProcessorService creates its
# Agent instance during __init__, but the mock fixtures are applied after service creation.
```

This is the same timing issue - service initialization happens before mock patches are applied.

**Recommended Fix**:
- [ ] **Action 1**: Apply same solution as Issues #4 and #5 - service factory fixture
- [ ] **Action 2**: Create `text_processor_with_mock_ai` fixture that patches BEFORE service creation
- [ ] **Action 3**: Document proper fixture usage pattern in conftest.py
- [ ] **Action 4**: Consider using dependency injection for AI service in TextProcessorService

**Contract References**:
- Public Contract: `orchestrator.pyi:367-454` - `with_resilience()` decorator behavior
- Test Plan: `TEST_PLAN.md` - Seam #3, Scenario 1 (Operations protected by decorators)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES (metrics and tracking)
- ✅ Does test use high-fidelity fakes - YES (real decorators and orchestrator)
- ✅ Does test validate business value - YES (core integration validation)

---

### Issue #7: AI Service Failures Circuit Breaker Test Skipped

**File**: `test_text_processing_resilience_integration.py:135`
**Test Name**: `test_ai_service_failures_trigger_real_circuit_breaker_protection`
**Category**: B (Fixture)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:135: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
```

**Expected Behavior**:
Test should verify that AI service failures trigger real circuit breaker opening through the service layer.

**Root Cause Analysis**:
Same fixture timing issue as Issues #4, #5, and #6.

**Recommended Fix**:
- [ ] **Action 1**: Same solution as previous fixture issues - service factory pattern
- [ ] **Action 2**: May be able to share fixture with Issue #4 solution
- [ ] **Action 3**: Document pattern in conftest.py for future test authors

**Contract References**:
- Test Plan: `TEST_PLAN.md` - Seam #3, Scenario 2 (AI failures trigger circuit breaker)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES
- ✅ Does test use high-fidelity fakes - YES
- ✅ Does test validate business value - YES

---

### Issue #8: Transient Failures Retry Test Skipped

**File**: `test_text_processing_resilience_integration.py:165`
**Test Name**: `test_transient_ai_failures_trigger_appropriate_real_retry_behavior`
**Category**: B (Fixture)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:165: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
```

**Expected Behavior**:
Test should verify that transient AI failures trigger tenacity retry behavior with proper attempt tracking.

**Root Cause Analysis**:
Same fixture timing issue.

**Recommended Fix**:
- [ ] **Action 1**: Same solution - service factory pattern
- [ ] **Action 2**: Use `flaky_ai_service` fixture with corrected service creation

**Contract References**:
- Test Plan: `TEST_PLAN.md` - Seam #3, Scenario 3 (Transient failures trigger retry)

**Testing Philosophy Check**:
- ✅ Does test verify observable behavior - YES
- ✅ Does test use high-fidelity fakes - YES
- ✅ Does test validate business value - YES

---

### Issue #9: Graceful Degradation Test Skipped

**File**: `test_text_processing_resilience_integration.py:196`
**Test Name**: `test_graceful_degradation_works_when_ai_services_are_unavailable`
**Category**: E (Intentional Skip)
**Severity**: Important

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:196: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
```

**Expected Behavior**:
Test should verify that service provides fallback responses when AI services are completely unavailable.

**Root Cause Analysis**:
Initially appears to be same fixture issue, BUT looking at the passing tests (lines 227-299), there are TWO tests that DO work:
- `test_resilience_integration_with_graceful_degradation_and_caching` (line 227) - PASSES
- `test_performance_integration_with_caching_and_resilience_patterns` (line 300) - PASSES

These passing tests DON'T mock the AI service at all - they use the real service with invalid API key, which naturally triggers graceful degradation. This suggests the skipped test is redundant.

**Recommended Fix**:
- [ ] **Action 1**: Verify if this test adds value beyond passing tests
- [ ] **Action 2**: If redundant, remove test entirely
- [ ] **Action 3**: If not redundant, apply same fixture fix as other tests
- [ ] **Action 4**: Document that graceful degradation is already validated by passing tests

**Contract References**:
- Test Plan: `TEST_PLAN.md` - Seam #3, Scenario 4 (Graceful degradation)

**Testing Philosophy Check**:
- ⚠️ May be redundant with passing tests
- ✅ Passing tests already validate graceful degradation behavior

---

### Issue #10: Performance Targets Test Skipped

**File**: `test_text_processing_resilience_integration.py:382`
**Test Name**: `test_real_performance_targets_met_with_actual_resilience_overhead`
**Category**: E (Intentional Skip)
**Severity**: Minor

**Observed Behavior**:
```
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:382: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
```

**Expected Behavior**:
Test should verify performance targets are met with resilience overhead across multiple operation types.

**Root Cause Analysis**:
Similar to Issue #9, there IS a passing performance test (`test_performance_integration_with_caching_and_resilience_patterns` at line 300) that validates performance targets. This test may be redundant or attempting to test broader scenarios.

**Recommended Fix**:
- [ ] **Action 1**: Review if passing test covers same scenarios
- [ ] **Action 2**: If broader coverage needed, apply fixture fix
- [ ] **Action 3**: If redundant, consider removing or marking as future enhancement
- [ ] **Action 4**: Document that basic performance validation already passing

**Contract References**:
- Test Plan: `TEST_PLAN.md` - Seam #3, Scenario 6 (Performance targets with resilience)

**Testing Philosophy Check**:
- ⚠️ May be redundant with passing test
- ✅ Basic performance validation already covered

---

## Implementation Recommendations

### Phase 1: Blockers (Immediate - 4-6 hours)

1. **Fix Issue #1 (Environment Detection Failure)** - 2-3 hours
   - Modify test to create app directly instead of using fixture
   - Verify environment detection works correctly
   - Document proper App Factory Pattern usage

2. **Create Unauthenticated Client Fixture (Issue #2)** - 2-3 hours
   - Add `unauthenticated_resilience_client` fixture to conftest.py
   - Add `invalid_api_key_headers` fixture
   - Un-skip and fix authentication test
   - Verify all auth scenarios work

### Phase 2: Critical (Short-term - 8-12 hours)

3. **Fix Fixture Timing Issues (Issues #3-#8)** - 8-12 hours
   - Create service factory fixtures that accept pre-configured mocks
   - Add `text_processor_with_failing_ai` fixture
   - Add `text_processor_with_flaky_ai` fixture  
   - Add `text_processor_with_mock_ai` fixture
   - Document fixture usage pattern in conftest.py
   - Un-skip and verify all affected tests pass
   - Update fixture documentation

### Phase 3: Important (Medium-term - 4-6 hours)

4. **Review Redundant Tests (Issues #9-#10)** - 2-3 hours
   - Compare skipped tests with passing tests
   - Determine if additional coverage needed
   - Either fix or remove redundant tests
   - Document coverage gaps if any

5. **Documentation and Patterns** - 2-3 hours
   - Document App Factory Pattern violations to avoid
   - Document correct fixture timing patterns
   - Add examples to conftest.py docstrings
   - Update TEST_PLAN.md with fixture guidance

### Phase 4: Validation (Final - 2-3 hours)

6. **End-to-End Validation** - 2-3 hours
   - Run complete test suite
   - Verify no regressions
   - Check test isolation (run tests in random order)
   - Validate metrics and cleanup
   - Update documentation with lessons learned

---

## Common Patterns Identified

### Pattern 1: App Factory Pattern Violations
**Problem**: Tests modify environment after app/settings creation
**Solution**: Always set environment → create settings → create app
**Affected Tests**: Issue #1

### Pattern 2: Fixture Timing Issues
**Problem**: Mocks applied after service initialization
**Solution**: Service factory fixtures or dependency injection
**Affected Tests**: Issues #3-#8

### Pattern 3: Missing Authentication Variants
**Problem**: Only authenticated test client available
**Solution**: Multiple client fixtures for different auth states
**Affected Tests**: Issue #2

### Pattern 4: Redundant Test Coverage
**Problem**: Skipped tests duplicate passing test coverage
**Solution**: Review and consolidate test scenarios
**Affected Tests**: Issues #9-#10

---

## Testing Philosophy Compliance

### Behavior vs. Implementation
**Assessment**: ✅ GOOD
- All tests focus on observable behavior (API responses, circuit breaker states, metrics)
- No tests checking private methods or internal state
- Tests validate end-to-end integration flows

### High-Fidelity Fakes
**Assessment**: ✅ EXCELLENT
- Uses real circuit breaker library (not mocked)
- Uses real tenacity retry library (not mocked)
- Uses real FastAPI test client
- Only mocks external AI service at boundary
- Could improve: Use fakeredis instead of InMemoryCache where applicable

### Business Value Focus
**Assessment**: ✅ EXCELLENT  
- All tests validate critical business functionality
- Tests cover operational requirements (monitoring, administration)
- Tests verify user-facing reliability (graceful degradation, performance)
- Clear business impact documented in test docstrings

### Maintainability Issues
**Assessment**: ⚠️ NEEDS IMPROVEMENT
- Fixture timing issues affect 6 tests
- App Factory Pattern violations
- Insufficient fixture documentation
- Some test duplication

---

## Next Steps

1. **Review recommendations with team** - Ensure approach aligns with project priorities
2. **Prioritize fixes based on business impact** - Focus on blockers first
3. **Implement Phase 1 (Blockers) immediately** - 4-6 hours
4. **Schedule Phases 2-4 based on capacity** - 14-21 hours remaining
5. **Re-run test suite after each phase** - Validate fixes and prevent regressions
6. **Update documentation** - Prevent future similar issues

**Total Estimated Effort**: 20-27 hours across all phases

**Expected Outcome**:
- 10/10 tests either passing or properly documented as intentional skips
- Clear fixture patterns documented
- App Factory Pattern violations eliminated
- No test isolation issues
- Comprehensive resilience integration coverage validated
