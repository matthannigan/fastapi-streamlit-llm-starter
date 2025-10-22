# Text Processor Integration Testing

## Prompt 7: Fix Broken Integration Tests

**Purpose**: Analyze test failures, skips, and errors from integration test implementation (Prompt 6) and create structured recommendations for fixes.

**PREREQUISITE**: This prompt should only be run AFTER:
- Prompt 5 (Create Fixtures) - Fixtures are implemented
- Prompt 6 (Implement Tests) - Tests are implemented and have been run

---

## Input Requirements

1. **Test Plan Location**: `backend/tests/integration/text_processor/TEST_PLAN.md`
2. **Public Contract Location**: `backend/contracts/api/v1/text_processing.pyi`, `backend/contracts/services/text_processor.pyi`
3. **Test Directory**: `backend/tests/integration/text_processor/`
4. **Component README** (if available): `docs/guides/domain-services/TEXT_PROCESSING.md`
5. **Pytest Summary Output**:
```
================================================================================ warnings summary =================================================================================
tests/integration/text_processor/test_batch_cache_integration.py::TestBatchCacheIntegration::test_batch_with_duplicate_requests_hits_cache_correctly
tests/integration/text_processor/test_batch_cache_integration.py::TestBatchCacheIntegration::test_duplicate_detection_across_batch_items
  /Users/matth/Github/MGH/fastapi-streamlit-llm-starter/.venv/lib/python3.13/site-packages/pydantic/main.py:463: UserWarning: Pydantic serializer warnings:
    PydanticSerializationUnexpectedValue(Expected `SentimentResult` - serialized value may not be as expected [input_value={'sentiment': 'neutral', ...emporarily unavailable'}, input_type=dict])
    return self.__pydantic_serializer__.to_python(

tests/integration/text_processor/test_batch_cache_integration.py::TestBatchCacheIntegration::test_batch_with_duplicate_requests_hits_cache_correctly
tests/integration/text_processor/test_batch_cache_integration.py::TestBatchCacheIntegration::test_duplicate_detection_across_batch_items
  /Users/matth/Github/MGH/fastapi-streamlit-llm-starter/.venv/lib/python3.13/site-packages/pydantic/type_adapter.py:572: UserWarning: Pydantic serializer warnings:
    PydanticSerializationUnexpectedValue(Expected `SentimentResult` - serialized value may not be as expected [input_value={'sentiment': 'neutral', ...emporarily unavailable'}, input_type=dict])
    PydanticSerializationUnexpectedValue(Expected `SentimentResult` - serialized value may not be as expected [input_value={'sentiment': 'neutral', ...emporarily unavailable'}, input_type=dict])
    return self.serializer.to_python(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================================================================= short test summary info =============================================================================
SKIPPED [1] backend/tests/integration/text_processor/test_security_integration.py:272: Performance testing requires service-level mocking
SKIPPED [1] backend/tests/integration/text_processor/test_cache_failure_resilience_integration.py:416: 
    Cache recovery mechanisms are not yet implemented in TextProcessorService.

    Current Behavior: Service cannot recover from cache failures as cache failures
    cause complete service failure rather than graceful degradation.

    Expected Behavior: Service should automatically recover when cache becomes
    available again, switching from AI fallback back to normal caching behavior.

    Required Implementation:
    1. Implement cache failure detection and graceful degradation
    2. Add cache recovery detection mechanisms
    3. Automatically switch back to cache usage when available
    4. Maintain service state awareness of cache availability
    5. Provide performance improvements when cache recovers

    This test serves as documentation for the required recovery patterns
    and can be enabled once cache recovery mechanisms are implemented.
SKIPPED [1] backend/tests/integration/text_processor/test_security_integration.py:308: Logging testing requires controlled service setup
SKIPPED [1] backend/tests/integration/text_processor/test_cache_failure_resilience_integration.py:79: 
    Cache failure resilience is not yet implemented in TextProcessorService.

    Current Behavior: Cache get failures cause InfrastructureError to propagate,
    resulting in service failure instead of graceful degradation to AI processing.

    Expected Behavior: Service should catch cache InfrastructureError, log warning,
    and proceed with AI processing as fallback mechanism.

    Required Implementation:
    1. Wrap cache.get() calls in try-catch blocks in process_text()
    2. Log appropriate warnings when cache failures occur
    3. Continue with AI processing when cache is unavailable
    4. Set cache_hit=False in response when fallback is used

    This test serves as documentation for the required resilience pattern
    and can be enabled once cache failure handling is implemented.
SKIPPED [1] backend/tests/integration/text_processor/test_security_integration.py:238: Requires service-level mocking for proper testing
SKIPPED [1] backend/tests/integration/text_processor/test_cache_failure_resilience_integration.py:532: 
    Comprehensive cache failure handling is not yet implemented in TextProcessorService.

    Current Behavior: All cache failure scenarios cause InfrastructureError to propagate,
    resulting in complete service failure regardless of failure type or pattern.

    Expected Behavior: Service should handle various cache failure scenarios gracefully,
    maintaining service availability and providing consistent fallback behavior.

    Required Implementation:
    1. Implement graceful degradation for all cache failure types
    2. Add comprehensive error handling for intermittent failures
    3. Add comprehensive error handling for complete failures
    4. Add comprehensive error handling for partial recovery scenarios
    5. Ensure consistent response quality across all failure scenarios
    6. Add comprehensive logging and monitoring for different failure types

    This test serves as documentation for the required comprehensive resilience patterns
    and can be enabled once full cache failure handling is implemented.
SKIPPED [1] backend/tests/integration/text_processor/test_cache_failure_resilience_integration.py:182: 
    Cache storage failure resilience is not yet implemented in TextProcessorService.

    Current Behavior: Cache set failures cause InfrastructureError to propagate,
    resulting in service failure even after successful AI processing.

    Expected Behavior: Service should catch cache set InfrastructureError, log warning,
    and still return successful AI processing response to the user.

    Required Implementation:
    1. Wrap cache.set() calls in try-catch blocks in process_text()
    2. Log appropriate warnings when cache storage failures occur
    3. Return successful AI response even if cache storage fails
    4. Ensure cache storage failures don't affect response delivery

    This test serves as documentation for the required resilience pattern
    and can be enabled once cache storage failure handling is implemented.
SKIPPED [1] backend/tests/integration/text_processor/test_cache_failure_resilience_integration.py:285: 
    Cache failure logging is not yet implemented in TextProcessorService.

    Current Behavior: Cache failures cause InfrastructureError to propagate without
    any logging of cache unavailability or graceful degradation attempts.

    Expected Behavior: Service should catch cache InfrastructureError, log detailed
    warnings about cache unavailability, and provide operational visibility.

    Required Implementation:
    1. Add comprehensive logging for cache get failures
    2. Add comprehensive logging for cache set failures
    3. Include diagnostic information in log messages
    4. Ensure logging doesn't expose sensitive data
    5. Use appropriate log levels (WARNING for cache issues)

    This test serves as documentation for the required logging patterns
    and can be enabled once cache failure logging is implemented.
SKIPPED [1] backend/tests/integration/text_processor/test_authentication_integration.py:158: 
Authentication integration tests reveal a test environment issue with exception handling.

Analysis:
- AuthenticationError is properly raised for invalid API keys
- Global exception handler should convert AuthenticationError to 401 HTTP responses
- Issue: TestClient receives raw AuthenticationError instead of HTTP response
- Authentication logic works correctly - problem is in test environment setup

Root Cause:
The global exception handler may not be properly registered in the test environment
or there's a conflict between TestClient and exception handling middleware.

Required Fix:
- Investigate global exception handler registration in test environment
- Verify middleware setup order in test client creation
- Ensure AuthenticationError is properly mapped to 401 responses

Authentication System Status: ✅ Working correctly
Test Environment Issue: ❌ Exception handling not converting to HTTP responses
SKIPPED [1] backend/tests/integration/text_processor/test_resilience_integration.py:336: Health endpoint structure doesn't match expected schema - current implementation returns different health data structure. To fix: need to verify actual health endpoint implementation and update test assertions.
SKIPPED [1] backend/tests/integration/text_processor/test_resilience_integration.py:369: Test implementation fails because graceful degradation returns successful responses instead of error codes - current fallback mechanism provides responses but changes status to FALLBACK_USED internally. To fix: need to test fallback response content rather than error codes.
SKIPPED [1] backend/tests/integration/text_processor/test_resilience_integration.py:200: Test requires circuit breaker state management across HTTP requests - current implementation uses fallback responses which mask circuit breaker behavior. To fix: need direct service-level testing or circuit breaker state persistence.
SKIPPED [1] backend/tests/integration/text_processor/test_resilience_integration.py:235: Test requires circuit breaker state management across HTTP requests - current implementation uses fallback responses which prevent circuit breaker state testing. To fix: need service-level testing with circuit breaker isolation.
SKIPPED [1] backend/tests/integration/text_processor/test_resilience_integration.py:268: Test requires circuit breaker state timing control across HTTP requests - current fallback mechanisms prevent circuit breaker state transitions. To fix: need direct service testing with circuit breaker timeout control.
SKIPPED [1] backend/tests/integration/text_processor/test_authentication_integration.py:312: 
Same AuthenticationError handling issue affects consistency test.

The consistency test requires testing invalid/missing authentication scenarios,
which are affected by the same exception handling issue identified in other tests.

Authentication system works correctly for valid authentication scenarios.
Only invalid/missing authentication scenarios are affected by test environment issue.
SKIPPED [1] backend/tests/integration/text_processor/test_security_integration.py:201: Response validation mocking requires deeper service integration
SKIPPED [1] backend/tests/integration/text_processor/test_resilience_integration.py:302: Test requires operation-specific resilience strategy configuration access - current implementation uses uniform retry behavior across all operations. To fix: need access to individual operation resilience configurations.
SKIPPED [1] backend/tests/integration/text_processor/test_authentication_integration.py:228: 
Same AuthenticationError handling issue as test_invalid_api_key_rejects_requests_with_401_status.

Authentication system correctly identifies missing API keys and raises AuthenticationError,
but test environment fails to convert to HTTP 401 responses.

See test_invalid_api_key_rejects_requests_with_401_status for detailed analysis.
FAILED backend/tests/integration/text_processor/test_cache_integration.py::TestCacheIntegration::test_cache_hit_returns_fast_response_without_ai_call - AssertionError: Cache hit should be faster: first=1587.2084582224488ms, second=2406.664416193962ms
```

---

## Analysis Framework

### Step 1: Categorize Issues

**For each test issue, classify into ONE category:**

#### Category A: Test Logic Issues (Fix Test)
**Indicators**:
- Incorrect assertions or expectations
- Test doesn't match public contract behavior
- Test expectations conflict with documented behavior
- Flawed test setup or teardown

**Examples**:
- `AssertionError: Expected staging, got: DEVELOPMENT` - Test expectation may be wrong
- Test checks internal state instead of observable behavior
- Test assumes specific implementation detail

#### Category B: Fixture/Setup Issues (Fix Fixtures)
**Indicators**:
- Fixture missing or incomplete
- Fixture configuration doesn't match test needs
- Fixture scope issues (session vs. function)
- Missing mocks or test doubles

**Examples**:
- `Test client fixture includes API key, causing authentication to pass` - Fixture needs variant
- `Flaky AI service fixture references non-existent PydanticAIAgent` - Fixture implementation broken
- `No circuit breakers available for reset testing` - Missing fixture setup

#### Category C: Production Code Issues (Fix Implementation)
**Indicators**:
- Code doesn't fulfill public contract
- Missing functionality documented in contract
- Incorrect behavior that violates contract
- Configuration or initialization issues

**Examples**:
- Feature documented in contract `.pyi` file not implemented
- Implementation returns wrong type or values
- Missing error handling specified in contract

#### Category D: E2E Tests Misclassified as Integration (Reclassify)
**Indicators**:
- Test requires external services (real Redis, real AI APIs)
- Test requires running server (manual test)
- Test crosses too many system boundaries
- Test takes > 5 seconds to run

**Examples**:
- `Test requires complex AI service setup` - May be E2E, not integration
- Tests requiring real API keys or network calls
- Tests that depend on Docker containers

#### Category E: Intentional Skips (Document Only)
**Indicators**:
- Test marked with `pytest.mark.skip` or `pytest.mark.skipif`
- Known limitation or future work
- Platform-specific or environment-specific skip
- Conditional skip for missing dependencies

**Examples**:
- Tests marked with `@pytest.mark.skip(reason="Future feature")`
- Tests skipped on specific OS or Python versions
- Tests requiring optional dependencies

---

### Step 2: Analyze Each Issue

**For EACH test issue, provide structured analysis:**

#### Template:

```markdown
### Issue #[N]: [Brief Description]

**File**: `[file.py:line]`
**Test Name**: `test_[name]`
**Category**: [A/B/C/D/E]
**Severity**: [Blocker|Critical|Important|Minor]

**Observed Behavior**:
[What happened - copy pytest output]

**Expected Behavior**:
[What should happen according to test plan and public contract]

**Root Cause Analysis**:
[Why this is happening - check fixtures, test logic, implementation]

**Recommended Fix**:
- [ ] **Action 1**: [Specific change needed]
- [ ] **Action 2**: [Specific change needed]

**Contract References**:
- Public Contract: `[contract.pyi:line]` - [relevant contract specification]
- Test Plan: `TEST_PLAN.md` - [Seam #N, Scenario #M]

**Testing Philosophy Check**:
- [ ] Does test verify observable behavior (not internal state)?
- [ ] Does test use high-fidelity fakes (not mocks)?
- [ ] Does test validate business value (not implementation details)?
```

---

### Step 3: Prioritize Fixes

**Assign severity based on business impact:**

- **Blocker**: Prevents running any tests, critical path failure, production code bug
- **Critical**: High-value integration seam not tested, fixture completely broken
- **Important**: Partial test coverage, fixture limitations, minor behavior gaps
- **Minor**: Test quality improvements, documentation fixes, nice-to-haves

---

### Step 4: Create Fix Recommendations Document

**Output to**: `backend/tests/integration/text_processor/TEST_FIXES.md`

**Document Structure**:

```markdown
# Integration Test Fixes

**Component**: [Component name]
**Test Plan**: [Link to TEST_PLAN.md]
**Analysis Date**: [Date]

## Summary

**Total Issues**: [N]
- Blocker: [N]
- Critical: [N]
- Important: [N]
- Minor: [N]

**By Category**:
- Category A (Test Logic): [N]
- Category B (Fixtures): [N]
- Category C (Production Code): [N]
- Category D (Reclassify E2E): [N]
- Category E (Intentional Skip): [N]

---

## Blockers (Fix First)

[Use Issue Template from Step 2]

---

## Critical Issues

[Use Issue Template from Step 2]

---

## Important Issues

[Use Issue Template from Step 2]

---

## Minor Issues

[Use Issue Template from Step 2]

---

## Implementation Recommendations

### Phase 1: Blockers (Immediate)
1. [Fix #1 - Brief description]
2. [Fix #2 - Brief description]

### Phase 2: Critical (Short-term)
1. [Fix #3 - Brief description]
2. [Fix #4 - Brief description]

### Phase 3: Important (Medium-term)
[Fixes that can be scheduled]

### Phase 4: Minor (Future)
[Nice-to-have improvements]

---

## Common Patterns Identified

[Document recurring issues - fixture patterns, test setup issues, etc.]

---

## Testing Philosophy Compliance

**Behavior vs. Implementation**: [Assessment]
**High-Fidelity Fakes**: [Assessment]
**Business Value Focus**: [Assessment]

---

## Next Steps

1. Review recommendations with team
2. Prioritize fixes based on business impact
3. Implement Phase 1 (Blockers) immediately
4. Schedule Phases 2-4 based on capacity
5. Re-run test suite after each phase
```

---

## Critical Testing Patterns to Check

### App Factory Pattern
**Check for**: Tests creating app BEFORE setting environment variables

```python
# ❌ WRONG - Environment set after app creation
def test_wrong_order(monkeypatch):
    app = create_app()  # Too early!
    monkeypatch.setenv("ENVIRONMENT", "production")

# ✅ CORRECT - Environment set before app creation
def test_correct_order(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    app = create_app()  # Picks up environment
```

### Environment Variable Handling
**Check for**: Direct `os.environ` manipulation (causes test pollution)

```python
# ❌ WRONG - Causes test pollution
os.environ["VAR"] = "value"

# ✅ CORRECT - Automatic cleanup
monkeypatch.setenv("VAR", "value")
```

### Fixture Scope Issues
**Check for**: Session fixtures being modified, causing cross-test pollution

```python
# ❌ WRONG - Session fixture modified
@pytest.fixture(scope="session")
def shared_cache():
    cache = Cache()
    return cache

def test_modifies_cache(shared_cache):
    shared_cache.clear()  # Affects other tests!

# ✅ CORRECT - Function scope or immutable
@pytest.fixture(scope="function")
def isolated_cache():
    return Cache()
```

### High-Fidelity Fakes
**Check for**: Over-mocking instead of using real libraries or fakes

```python
# ❌ WRONG - Mocking real library
mock_circuit_breaker = MagicMock()

# ✅ CORRECT - Use real library
from circuitbreaker import CircuitBreaker
real_circuit_breaker = CircuitBreaker(...)
```

---

## Reference Documentation

**Testing Philosophy**:
- `docs/guides/testing/TESTING.md` - Overall testing methodology
- `docs/guides/testing/INTEGRATION_TESTS.md` - Integration test philosophy
- `backend/CLAUDE.md` - App Factory Pattern section

**Testing Patterns**:
- `backend/tests/integration/README.md` - Integration test patterns
- `backend/tests/integration/conftest.py` - Shared fixtures
- `docs/guides/developer/CODE_STANDARDS.md` - Coding standards

**Common Issues**:
- `backend/CLAUDE.md` - Environment Variable Testing Patterns section
- `backend/CLAUDE.md` - App Factory Pattern section

---

## Success Criteria

Analysis is complete when TEST_FIXES.md includes:

- ✅ All test issues categorized (A/B/C/D/E)
- ✅ Each issue has severity level (Blocker/Critical/Important/Minor)
- ✅ Root cause identified for each issue
- ✅ Specific, actionable recommendations provided
- ✅ Contract references for each issue
- ✅ Testing philosophy compliance checked
- ✅ Implementation phases prioritized
- ✅ Common patterns documented

**Next Step**: Review TEST_FIXES.md with team, then implement fixes starting with Blockers.

---

## Example Usage

```bash
# Run tests and capture output
cd backend
../.venv/bin/python -m pytest tests/integration/text_processor -v --tb=short > test_output.txt 2>&1

# Copy test_output.txt content to this prompt
# Agent will analyze and create TEST_FIXES.md
``` 