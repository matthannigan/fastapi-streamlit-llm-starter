# Simplify Environment Detector: Remove contextvars Complexity

**Priority:** Low
**Type:** Technical Debt / Optimization
**Component:** `backend/app/core/environment/`
**Effort:** Small (2-4 hours)

---

## Description

Consider simplifying the environment detector by removing the contextvars-based hybrid architecture. The current implementation uses context-local storage for test isolation, but this may be unnecessary given that the App Factory Pattern + monkeypatch already provide complete test isolation.

## Background

During the investigation of flaky integration tests (October 2025), we implemented a hybrid architecture for the environment detector:

- **Production**: Uses global singleton for zero overhead
- **Testing**: Uses `contextvars.ContextVar` for context-local detector instances

**Implementation Location:**
- `backend/app/core/environment/api.py` (lines 22-34)
- `backend/app/core/environment/detector.py` (`reset_cache()` method)

**Root Cause Discovery:**
The actual root cause of test flakiness was direct `os.environ[]` manipulation, not the environment detector itself. The contextvars solution was implemented before we understood this.

## Current Implementation

```python
# backend/app/core/environment/api.py
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))

if _IS_PYTEST:
    # Testing: Use context-local storage for automatic test isolation
    _detector_context = contextvars.ContextVar('environment_detector', default=None)
    environment_detector = None  # No global instance in tests
else:
    # Production: Use global singleton for zero overhead
    environment_detector = EnvironmentDetector()
    _detector_context = None
```

## Proposed Simplification

Replace the hybrid architecture with a simple singleton + cache reset approach:

```python
# backend/app/core/environment/api.py
environment_detector = EnvironmentDetector()

def get_environment_info(feature_context: FeatureContext = FeatureContext.DEFAULT) -> EnvironmentInfo:
    """Get environment information using the global detector."""
    return environment_detector.detect_with_context(feature_context)
```

**Test Isolation via:**
1. **App Factory Pattern**: Creates fresh app with fresh dependencies
2. **monkeypatch.setenv()**: Ensures clean environment variable state
3. **Optional**: Call `environment_detector.reset_cache()` in test fixtures if needed

## Why This Works

The complete test isolation solution is:

```python
def test_production_mode(monkeypatch):
    # Step 1: monkeypatch prevents env pollution
    monkeypatch.setenv("ENVIRONMENT", "production")

    # Step 2: App Factory creates fresh app that reads new env
    app = create_app()

    # Step 3: Environment detector reads fresh environment variables
    # No context-local storage needed - just fresh Settings + clean env
```

## Benefits of Simplification

### Reduced Complexity
- ✅ Simpler code: No pytest detection logic
- ✅ Easier to understand: Single execution path
- ✅ Less cognitive overhead: No context switching logic
- ✅ Fewer edge cases: No contextvars lifecycle management

### Maintained Benefits
- ✅ `reset_cache()` method still available for explicit cache clearing
- ✅ Production performance unchanged (still singleton)
- ✅ Test isolation maintained via App Factory + monkeypatch
- ✅ No breaking changes to public API

### Code Quality
- ✅ Follows YAGNI principle (You Aren't Gonna Need It)
- ✅ Reduces maintenance burden
- ✅ Clearer separation of concerns

## Why Current Implementation Is Not Harmful

**Keep for now if:**
- Already committed and working in production
- Team prefers defense-in-depth approach
- Provides psychological safety during testing

**Current pros:**
- Zero production overhead (singleton still used)
- Works correctly as implemented
- Provides additional isolation guarantee
- No known bugs or issues

## Risks & Considerations

### Low Risk Change
- **Testing**: Existing tests should pass unchanged
- **Production**: No production code paths affected
- **API**: Public interface remains identical

### Validation Required
1. Run full integration test suite 100+ times
2. Verify no test isolation issues emerge
3. Test with parallel execution (`pytest -n auto`)
4. Verify environment detection accuracy unchanged

### Potential Issues
- If tests directly import and cache detector, may need fixture updates
- Any test relying on context-local behavior needs review
- Verify no tests are calling detector outside of app context

## Acceptance Criteria

- [ ] Remove pytest detection logic from `api.py`
- [ ] Remove context-local storage implementation
- [ ] Simplify to single global singleton
- [ ] Keep `reset_cache()` method for explicit cache management
- [ ] Update docstrings to reflect simplified architecture
- [ ] Update contracts: `backend/contracts/core/environment/*.pyi`
- [ ] All integration tests pass (100 consecutive runs)
- [ ] Parallel test execution works (`pytest -n auto`)
- [ ] No test isolation issues observed
- [ ] Documentation updated to reflect simplified approach

## Related Context

**Root Cause Documentation:**
- `backend/tests/integration/CURRENT_STATUS.md` - Documents the actual root cause (os.environ pollution)
- `backend/tests/integration/README.md` - Monkeypatch pattern guidance
- `backend/CLAUDE.md` - Environment variable testing patterns

**Current Implementation:**
- App Factory Pattern: `backend/app/main.py` (`create_app()`)
- Environment Detector: `backend/app/core/environment/`
- Test Fixtures: `backend/tests/integration/conftest.py`

**PRDs and Design Docs:**
- `dev/taskplans/complete/2025-10-05_feature-app-factory_PRD.md` - App Factory implementation

## Implementation Notes

### Suggested Approach

1. **Phase 1**: Validation (1 hour)
   - Run extended test suite to establish baseline
   - Verify no tests rely on context-local behavior
   - Document any edge cases discovered

2. **Phase 2**: Simplification (1 hour)
   - Remove pytest detection logic
   - Remove contextvars implementation
   - Simplify to singleton pattern
   - Keep `reset_cache()` method

3. **Phase 3**: Testing (1-2 hours)
   - Run integration tests 100+ times
   - Test with parallel execution
   - Verify no regressions
   - Update documentation

### Alternative: Do Nothing

**Valid option**: Keep current implementation
- Working correctly as-is
- Zero production impact
- Provides defense-in-depth
- Not causing technical debt

**Future decision point**: Revisit during next major refactor

## Priority Justification

**Low Priority** because:
- Current implementation works correctly
- No bugs or performance issues
- Not blocking any features
- Pure code quality improvement
- Can be deferred indefinitely

**Consider prioritizing if:**
- Working on environment detection system anyway
- Onboarding new developers confused by complexity
- Refactoring test infrastructure more broadly
- Team consensus favors simplification

---

## Labels

- `type: technical-debt`
- `priority: low`
- `component: environment`
- `effort: small`
- `status: proposed`

## References

- Issue discovered: 2025-10-06
- Related to: Integration test flakiness investigation
- Depends on: App Factory Pattern (implemented)
- Blocks: None
