# Resilience Integration Testing

## Prompt 7: Fix Broken Integration Tests

**Purpose**: Analyze test failures, skips, and errors from integration test implementation (Prompt 6) and create structured recommendations for fixes.

**PREREQUISITE**: This prompt should only be run AFTER:
- Prompt 5 (Create Fixtures) - Fixtures are implemented
- Prompt 6 (Implement Tests) - Tests are implemented and have been run

---

## Input Requirements

1. **Test Plan Location**: `backend/tests/integration/resilience/TEST_PLAN.md`
2. **Public Contract Location**: `backend/contracts/api/internal/resilience/*.pyi`, `backend/contracts/infrastructure/resilience/*.pyi`
3. **Test Directory**: `backend/tests/integration/resilience/`
4. **Component README** (if available): `backend/app/infrastructure/resilience/README.md`, `backend/app/api/internal/resilience/README.md`
5. **Pytest Summary Output**:
```
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:398: Test requires complex AI service setup that conflicts with existing fixtures
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:392: No circuit breakers available for reset testing
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:66: Test client fixture includes API key, causing authentication to pass
SKIPPED [1] backend/tests/integration/resilience/test_api_resilience_orchestrator_integration.py:429: Flaky AI service fixture references non-existent PydanticAIAgent
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:66: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:196: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:135: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:382: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
SKIPPED [1] backend/tests/integration/resilience/test_text_processing_resilience_integration.py:165: Mocking requires service-level integration; current fixture structure doesn't support proper AI mocking
FAILED backend/tests/integration/resilience/test_config_environment_integration.py::TestConfigEnvironmentIntegration::test_preset_recommendation_api_auto_detects_environment - AssertionError: Expected staging or unknown detection, got: Environment.DEVELOPMENT (auto-detected)
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

**Output to**: `backend/tests/integration/resilience/TEST_FIXES.md`

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
../.venv/bin/python -m pytest tests/integration/resilience -v --tb=short > test_output.txt 2>&1

# Copy test_output.txt content to this prompt
# Agent will analyze and create TEST_FIXES.md
``` 