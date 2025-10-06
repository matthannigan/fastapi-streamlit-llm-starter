<context>
# Overview

## Problem Statement
The current `EnvironmentDetector` implementation uses a module-level global singleton that causes test isolation issues and lacks thread safety. The global instance (`environment_detector = EnvironmentDetector()`) persists across all tests, threads, and async tasks, leading to:

- **Test Pollution**: Environment detection state from one test affects subsequent tests
- **Cache Staleness**: Cached signals persist inappropriately across execution contexts
- **Manual Cleanup Required**: Tests need explicit `reset_cache()` calls via autouse fixtures
- **Thread Safety Concerns**: Shared global state in multi-threaded/async environments
- **Architectural Smell**: Global singletons violate dependency injection and testability principles

## Solution
Implement a **hybrid approach** that uses pytest detection to choose the optimal strategy:
- **In Production**: Global singleton for zero overhead (current behavior preserved)
- **In Tests (pytest)**: Context-local instances using `contextvars` for automatic isolation

This gives the best of both worlds: production performance + test isolation, with no API changes.

## Value Proposition

**For Testing:**
- ✅ **Automatic test isolation** - No fixtures or manual cleanup needed
- ✅ **Eliminates flaky tests** - Each test gets fresh detector instance
- ✅ **Simpler test code** - No autouse fixtures required
- ✅ **Better debugging** - Isolated state makes failures easier to diagnose

**For Production:**
- ✅ **Zero performance overhead** - Uses global singleton (current implementation)
- ✅ **No behavior changes** - Production code path unchanged
- ✅ **Lower migration risk** - Only test code path changes
- ✅ **Same API** - Zero changes to calling code
- ✅ **Easy rollback** - Can disable hybrid mode with single flag

## Who This Benefits
- **Developers** - Cleaner test code, fewer flaky tests
- **CI/CD Pipeline** - More reliable test execution
- **Production Systems** - Better concurrency support
- **Future Contributors** - Cleaner, more maintainable architecture

# Core Features

## Feature 1: Pytest-Aware Hybrid Detection
**What it does:**
Uses pytest detection (same pattern as `config.py`) to automatically choose between global singleton (production) and context-local storage (tests).

**Why it's important:**
Provides zero-overhead production performance while enabling automatic test isolation. Best of both worlds without requiring API changes or manual configuration.

**How it works:**
```python
import sys
import os
import contextvars

# Detect pytest at import time (same pattern as config.py)
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))

if _IS_PYTEST:
    # Testing: Use context-local storage for automatic test isolation
    _detector_context = contextvars.ContextVar('environment_detector', default=None)
    environment_detector = None  # No global singleton in test mode
else:
    # Production: Use global singleton for performance
    environment_detector = EnvironmentDetector()
    _detector_context = None  # No context var overhead in production

def get_environment_info(...):
    if _IS_PYTEST:
        # Test mode: context-local for isolation
        detector = _detector_context.get()
        if detector is None:
            detector = EnvironmentDetector()
            _detector_context.set(detector)
        return detector.detect_with_context(...)
    else:
        # Production mode: global singleton
        return environment_detector.detect_with_context(...)
```

## Feature 2: Lazy Detector Initialization (Tests Only)
**What it does:**
In pytest mode only, creates `EnvironmentDetector` instances on-demand per test context. In production, uses eager initialization at import time.

**Why it's important:**
Ensures each test starts with a fresh detector that reads current environment variables, eliminating the cache staleness problem. Production keeps existing behavior for performance.

**How it works:**
- **Production**: Detector created once at module import (current behavior)
- **Tests**: First call in test creates new detector, subsequent calls reuse
- **Tests**: Different tests get completely independent detectors
- **Tests**: Automatic garbage collection when test ends

## Feature 3: Simplified Test Fixtures
**What it does:**
Removes the need for `reset_cache()` autouse fixtures and manual cleanup in tests.

**Why it's important:**
Reduces test boilerplate, eliminates an entire class of fixture-related bugs, and makes tests easier to understand.

**How it works:**
```python
# BEFORE (with autouse fixture):
@pytest.fixture(autouse=True)
def reset_detector():
    environment_detector.reset_cache()
    yield
    environment_detector.reset_cache()

def test_something():
    env = get_environment_info()
    assert env.environment == Environment.TESTING

# AFTER (no fixture needed):
def test_something():
    env = get_environment_info()  # Automatically gets fresh detector
    assert env.environment == Environment.TESTING
```

## Feature 4: 100% Backward-Compatible API
**What it does:**
Maintains the exact same public API and production behavior. The hybrid approach is completely transparent to all calling code.

**Why it's important:**
Zero changes required to calling code across the entire codebase. Production code path is unchanged. The implementation change is invisible to consumers.

**How it works:**
All existing calls continue to work identically in both modes:
```python
# All of these work unchanged in production and tests
env = get_environment_info()
env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
is_prod = is_production_environment()
is_dev = is_development_environment()

# Production: Uses global singleton (same as before)
# Tests: Uses context-local (automatic isolation)
```

# User Experience

## Developer Personas

### Primary: Backend Developer (Test Writer)
**Needs:**
- Write isolated tests without worrying about shared state
- Debug failing tests without considering global state pollution
- Add new tests confidently without breaking existing ones

**Pain Points (Current):**
- Must remember to use autouse fixtures
- Flaky test failures due to cache pollution
- Difficult to debug state-related issues

**Benefits (After):**
- Tests "just work" with automatic isolation
- No fixture boilerplate required
- Failures are deterministic and debuggable

### Secondary: Infrastructure Developer (Maintainer)
**Needs:**
- Maintain thread-safe infrastructure code
- Support async/concurrent execution patterns
- Ensure reliability in production

**Pain Points (Current):**
- Global singleton creates thread safety concerns
- Manual cache management is error-prone
- Limited visibility into detector state

**Benefits (After):**
- Thread-safe by design
- No manual state management needed
- Clear context boundaries

## Key Developer Flows

### Flow 1: Writing a New Integration Test
**Current (with global singleton):**
1. Import `get_environment_info`
2. Remember to check autouse fixture exists in conftest
3. Write test logic
4. Debug if test pollutes other tests
5. Add `monkeypatch.setenv()` calls carefully

**After (with context-local):**
1. Import `get_environment_info`
2. Write test logic
3. Done - automatic isolation

### Flow 2: Testing Different Environments
**Current:**
```python
def test_prod_env(monkeypatch):
    environment_detector.reset_cache()  # Manual reset
    monkeypatch.setenv("ENVIRONMENT", "production")
    env = get_environment_info()
    assert env.environment == Environment.PRODUCTION
    environment_detector.reset_cache()  # Manual cleanup
```

**After:**
```python
def test_prod_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    env = get_environment_info()  # Fresh detector automatically
    assert env.environment == Environment.PRODUCTION
```

### Flow 3: Debugging a Flaky Test
**Current:**
1. Run test multiple times to reproduce
2. Check if autouse fixture is working
3. Verify test order isn't affecting results
4. Check for missing `reset_cache()` calls
5. Investigate cache pollution from other tests

**After:**
1. Run test (deterministic failure)
2. Debug actual test logic (no state pollution possible)
3. Done

## DX (Developer Experience) Improvements

### Simplification Metrics
- **Lines of test fixture code removed**: ~20-30 lines across conftest files
- **Autouse fixtures eliminated**: 2 (integration conftest, cache conftest)
- **Manual cleanup code removed**: All `reset_cache()` calls in tests
- **Cognitive load reduced**: No need to understand fixture execution order

### Code Quality Improvements
- **Clearer intent**: Tests focus on behavior, not state management
- **Better isolation**: Impossible to pollute other tests
- **Easier onboarding**: New developers don't need to learn fixture patterns
- **Self-documenting**: Context isolation is implicit in the architecture
</context>

<PRD>
# Technical Architecture

## System Components

### 1. Core Module: `app/core/environment/api.py`
**Current Implementation:**
```python
# Global singleton (PROBLEMATIC)
environment_detector = EnvironmentDetector()

def get_environment_info(...):
    return environment_detector.detect_with_context(...)
```

**New Implementation:**
```python
import contextvars

# Context-local storage
_detector_context: contextvars.ContextVar[Optional[EnvironmentDetector]] = (
    contextvars.ContextVar('environment_detector', default=None)
)

def get_environment_info(feature_context: FeatureContext = FeatureContext.DEFAULT) -> EnvironmentInfo:
    """Get environment info with automatic context isolation."""
    detector = _detector_context.get()
    if detector is None:
        detector = EnvironmentDetector()
        _detector_context.set(detector)
    return detector.detect_with_context(feature_context)
```

### 2. Supporting Module: `app/core/environment/detector.py`
**Changes Required:**
- **KEEP**: `reset_cache()` method (useful for edge cases and backward compat)
- **KEEP**: All existing detection logic
- **UPDATE**: Docstrings to mention hybrid usage pattern
- **NO NEW METHODS NEEDED**: `reset_cache()` already exists

**No breaking changes** - existing `EnvironmentDetector` class works as-is.
**Note**: In production mode, `reset_cache()` continues to work on the global singleton.

### 3. Test Infrastructure Updates

#### Remove from `tests/integration/conftest.py`:
```python
# DELETE THIS:
@pytest.fixture(autouse=True)
def setup_testing_environment_for_all_integration_tests(monkeypatch):
    from app.core.environment.api import environment_detector
    environment_detector.reset_cache()  # No longer needed
    monkeypatch.setenv("ENVIRONMENT", "testing")
    yield
    environment_detector.reset_cache()  # No longer needed
```

**Replace with:**
```python
@pytest.fixture(autouse=True)
def setup_testing_environment_for_all_integration_tests(monkeypatch):
    """Set default testing environment (no reset needed - automatic isolation)."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
```

#### Remove from `tests/integration/cache/conftest.py`:
```python
# DELETE THIS:
@pytest.fixture(autouse=True)
def setup_testing_environment(monkeypatch):
    from app.core.environment.api import environment_detector
    environment_detector.reset_cache()  # No longer needed
    # ...
```

## Data Models

### ContextVar Type Definition
```python
from typing import Optional
import contextvars
from .detector import EnvironmentDetector

_detector_context: contextvars.ContextVar[Optional[EnvironmentDetector]] = (
    contextvars.ContextVar(
        'environment_detector',
        default=None
    )
)
```

**Key Properties:**
- **Type**: `ContextVar[Optional[EnvironmentDetector]]`
- **Default**: `None` (triggers lazy initialization)
- **Scope**: Per execution context (test, thread, async task)
- **Lifetime**: Garbage collected when context ends

## APIs and Integrations

### Public API (UNCHANGED)
All existing function signatures remain identical:

```python
# Primary API
def get_environment_info(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> EnvironmentInfo:
    """Get environment info with context-local isolation."""

# Convenience APIs
def is_production_environment(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> bool:
    """Check production with context-local detection."""

def is_development_environment(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> bool:
    """Check development with context-local detection."""
```

### New Testing Utility (OPTIONAL)
```python
def reset_detector_for_context() -> None:
    """
    Reset detector for current context (pytest mode only).

    Rarely needed - each test automatically gets fresh detector.
    Only works in pytest mode. In production, this is a no-op.

    Only use if you need to force re-detection within same test.

    Example:
        def test_env_change_detection():
            env1 = get_environment_info()

            os.environ["ENVIRONMENT"] = "production"
            reset_detector_for_context()  # Force new detector (pytest only)

            env2 = get_environment_info()
            assert env1.environment != env2.environment
    """
    if _IS_PYTEST and _detector_context is not None:
        _detector_context.set(None)
    # In production mode, this is a no-op
```

## Infrastructure Requirements

### Runtime Requirements
- **Python Version**: 3.7+ (contextvars introduced in 3.7)
  - ✅ Already required by project (using 3.13.7)
- **Dependencies**: None (contextvars is stdlib)
- **Performance Impact**:
  - **Production**: Zero (uses existing global singleton approach)
  - **Tests**: Negligible (lazy initialization per test context)

### Testing Requirements
- **Pytest Version**: Current version sufficient
- **New Dependencies**: None
- **Test Isolation**: Automatic via pytest's context management

## Migration Strategy

### Breaking Changes
**None** - The public API remains identical. All calling code continues to work unchanged.

### Internal Changes
1. **Add pytest detection**: `_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))`
2. **Conditional initialization**: Global singleton (production) OR context variable (tests)
3. **Update function bodies**: Branch on `_IS_PYTEST` flag
4. **Remove autouse fixtures**: Delete reset_cache() fixtures from conftest files
5. **Update documentation**: Reflect hybrid architecture

### Production Code Path
- **Unchanged**: Still uses `environment_detector = EnvironmentDetector()` at import
- **Unchanged**: Still calls `environment_detector.detect_with_context()`
- **Unchanged**: Zero performance impact
- **Unchanged**: Same behavior as before

## Context Isolation Guarantees

### Test Isolation
```python
def test_a():
    # Context A: Fresh detector #1
    env = get_environment_info()

def test_b():
    # Context B: Fresh detector #2 (independent of #1)
    env = get_environment_info()
```

### Thread Isolation
```python
def worker_thread():
    # Thread context: Fresh detector per thread
    env = get_environment_info()

threads = [Thread(target=worker_thread) for _ in range(10)]
# Each thread gets independent detector
```

### Async Task Isolation
```python
async def async_task():
    # Async context: Fresh detector per task
    env = get_environment_info()

await asyncio.gather(
    async_task(),  # Independent detector
    async_task(),  # Independent detector
)
```

# Development Roadmap

## Phase 1: Core Hybrid Implementation (Foundation)
**Scope**: Add pytest detection and conditional initialization

**Deliverables:**
1. Update `app/core/environment/api.py`:
   - Import `sys`, `os`, `contextvars`
   - Add pytest detection: `_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))`
   - Add conditional initialization:
     ```python
     if _IS_PYTEST:
         _detector_context = ContextVar(...)
         environment_detector = None
     else:
         environment_detector = EnvironmentDetector()
         _detector_context = None
     ```
   - Update `get_environment_info()` with `if _IS_PYTEST:` branch
   - Update `is_production_environment()` (no changes needed - calls get_environment_info)
   - Update `is_development_environment()` (no changes needed - calls get_environment_info)
   - Add comprehensive docstrings explaining hybrid approach

2. Add optional testing utility:
   - Implement `reset_detector_for_context()` for edge case testing
   - Add `if _IS_PYTEST` check (no-op in production)
   - Document when/why to use it

3. Update docstrings in `app/core/environment/detector.py`:
   - Explain hybrid usage pattern
   - Update examples to show both modes
   - Note that `reset_cache()` still works in production mode

**Validation Criteria:**
- All existing unit tests pass without modification
- Production mode uses global singleton (verify with print/log)
- Test mode uses context-local (verify isolation with test)
- Can import and call all public functions in both modes

## Phase 2: Test Infrastructure Cleanup
**Scope**: Remove manual reset fixtures and cleanup code

**Deliverables:**
1. Update `tests/integration/conftest.py`:
   - Remove `environment_detector.reset_cache()` calls from autouse fixture
   - Simplify fixture to only set `ENVIRONMENT='testing'`
   - Update fixture docstring to explain automatic isolation

2. Update `tests/integration/cache/conftest.py`:
   - Remove `environment_detector.reset_cache()` calls from autouse fixture
   - Simplify fixture to only set `ENVIRONMENT='testing'`
   - Update fixture docstring

3. Search and remove any manual `reset_cache()` calls in tests:
   - Grep for `environment_detector.reset_cache()`
   - Grep for `from app.core.environment.api import environment_detector`
   - Remove imports and reset calls that are no longer needed

4. Clean up `tests/conftest.py`:
   - Review if root-level fixtures still need environment resets
   - Remove if context isolation makes them obsolete

**Validation Criteria:**
- Integration tests pass without autouse fixtures
- No manual reset calls remain in test code
- Tests are simpler and more readable

## Phase 3: Comprehensive Testing & Validation
**Scope**: Verify context isolation and test stability

**Deliverables:**
1. Run integration test suite multiple times:
   - Execute `pytest tests/integration/ -n 0` 10 times
   - Record failure counts
   - Should see 0 flaky failures (deterministic only)

2. Run integration tests in parallel:
   - Execute `pytest tests/integration/ -n auto` 10 times
   - Verify context isolation works with pytest-xdist
   - Should see same or better stability than serial execution

3. Add context isolation verification tests:
   ```python
   # tests/unit/core/environment/test_context_isolation.py
   def test_context_isolation_between_tests():
       """Verify each test gets fresh detector."""
       # Implementation

   def test_context_isolation_in_threads():
       """Verify thread safety with context vars."""
       # Implementation

   def test_context_isolation_in_async_tasks():
       """Verify async task isolation."""
       # Implementation
   ```

4. Performance benchmarking:
   - Measure test execution time before/after
   - Verify no performance regression
   - Document any improvements

**Validation Criteria:**
- 0 flaky test failures across 10 runs
- Thread safety verified via concurrent test execution
- Async task isolation verified
- Performance within acceptable range (±10%)

## Phase 4: Documentation & Knowledge Transfer
**Scope**: Update documentation to reflect new architecture

**Deliverables:**
1. Update `docs/guides/developer/APP_FACTORY_GUIDE.md`:
   - Add section on "Environment Detection Isolation"
   - Explain context-local pattern
   - Provide examples of when/why it matters

2. Update `tests/integration/README.md`:
   - Remove references to reset_cache() autouse fixture
   - Add section on automatic context isolation
   - Update troubleshooting guide

3. Update `tests/integration/CURRENT_STATUS.md`:
   - Document resolution of environment detection caching
   - Mark issue as resolved
   - Update recommendations

4. Update `tests/integration/cache/ENVIRONMENT_OVERRIDE.md`:
   - Explain context isolation
   - Remove reset_cache() references
   - Update troubleshooting section

5. Create architectural decision record:
   - `docs/architecture/decisions/ADR-XXX-context-local-environment-detector.md`
   - Document why we chose context vars over global singleton
   - Explain benefits and trade-offs
   - Provide migration guidance for future developers

**Validation Criteria:**
- All documentation accurately reflects new implementation
- No references to removed fixtures remain
- Clear explanation of context isolation pattern
- Easy for new developers to understand

# Logical Dependency Chain

## Build Order (Required Sequence)

### 1. Foundation: Context-Local Implementation
**Must build first** - All other work depends on this

**Tasks:**
- Replace global singleton with ContextVar
- Update get_environment_info() and helper functions
- Add reset_detector_for_context() utility
- Update core docstrings

**Rationale**: Everything else depends on the context-local mechanism working correctly.

**Validation**: Unit tests pass, manual smoke testing shows context isolation.

### 2. Test Fixture Cleanup
**Depends on**: Foundation (Phase 1)

**Tasks:**
- Remove reset_cache() calls from autouse fixtures
- Simplify integration test conftest files
- Remove manual reset calls from individual tests

**Rationale**: Can only remove fixtures once context isolation is working.

**Validation**: Integration tests pass without manual resets.

### 3. Comprehensive Testing
**Depends on**: Test Fixture Cleanup (Phase 2)

**Tasks:**
- Run stability tests (10x serial, 10x parallel)
- Add context isolation verification tests
- Benchmark performance

**Rationale**: Need clean test environment to validate stability improvements.

**Validation**: 0 flaky failures, performance acceptable.

### 4. Documentation
**Depends on**: Comprehensive Testing (Phase 3)

**Tasks:**
- Update all relevant docs
- Create ADR
- Update troubleshooting guides

**Rationale**: Should document proven, stable implementation.

**Validation**: Documentation review confirms accuracy.

## Incremental Development Strategy

### Iteration 1: Minimal Viable Change
**Goal**: Prove hybrid approach works

**Scope:**
- Add pytest detection logic
- Add conditional initialization (if/else for _IS_PYTEST)
- Update only `get_environment_info()` with branch logic
- Keep everything else unchanged
- Run subset of tests to verify

**Time**: ~20 minutes
**Risk**: Very Low - easily reversible, production path unchanged

### Iteration 2: Complete Core Functions
**Goal**: Full hybrid implementation

**Scope:**
- Verify helper functions work (they call get_environment_info, so no changes needed)
- Add `reset_detector_for_context()` with pytest check
- Update docstrings to explain hybrid approach
- Add comments explaining branch logic

**Time**: ~15 minutes
**Risk**: Very Low - API unchanged, production unchanged

### Iteration 3: Clean Up Simplest Fixtures
**Goal**: Remove obvious redundant fixtures

**Scope:**
- Remove reset_cache() from 1-2 conftest files
- Run related tests to verify

**Time**: ~15 minutes
**Risk**: Low - incremental removal

### Iteration 4: Complete Fixture Cleanup
**Goal**: Remove all manual reset code

**Scope:**
- Complete conftest cleanup
- Remove all reset_cache() calls
- Simplify all autouse fixtures

**Time**: ~30 minutes
**Risk**: Medium - more extensive changes

### Iteration 5: Validation & Documentation
**Goal**: Confirm stability and document

**Scope:**
- Run comprehensive test suite
- Update documentation
- Create ADR

**Time**: ~1 hour
**Risk**: Low - no code changes

## Parallel Work Opportunities

### Can Work in Parallel:
- **Documentation writing** (Phase 4) can start while testing (Phase 3) runs
- **Performance benchmarking** can run alongside stability testing
- **ADR writing** can begin during fixture cleanup

### Must Be Sequential:
- Core implementation → Fixture cleanup (fixtures depend on context isolation)
- Fixture cleanup → Stability testing (need clean environment to test)
- Implementation → Documentation (document working solution)

# Risks and Mitigations

## Technical Risks

### Risk 1: Unexpected Context Boundaries
**Risk**: ContextVar behavior differs from expectations in edge cases

**Likelihood**: Low
**Impact**: Medium

**Mitigation:**
- Write comprehensive context isolation tests first (Phase 3)
- Test thread boundaries explicitly
- Test async task boundaries explicitly
- Add assertions in detector initialization to catch unexpected contexts

**Fallback:**
- Keep `reset_cache()` method as escape hatch
- Can manually reset if automatic isolation fails

### Risk 2: Performance Regression
**Risk**: Lazy initialization per test context might add overhead to test suite

**Likelihood**: Very Low
**Impact**: Very Low (Tests only, production unaffected)

**Analysis:**
- **Production**: Zero overhead (uses global singleton as before)
- **Tests**: Creating EnvironmentDetector is lightweight (no heavy I/O)
- **Tests**: Only happens once per test (pytest contexts are relatively long-lived)
- **Tests**: Minimal per-test overhead (~1-5μs)

**Mitigation:**
- Benchmark test suite before/after (Phase 3)
- Production performance unchanged (can verify with profiling)
- Monitor CI/CD test execution times

**Acceptance Criteria**:
- Production: 0% performance impact (unchanged code path)
- Tests: <5% performance impact acceptable for automatic isolation

### Risk 3: Breaking Existing Test Assumptions
**Risk**: Some tests might rely on global singleton behavior

**Likelihood**: Low
**Impact**: Medium

**Mitigation:**
- Run full test suite after Phase 1 to identify breakages
- Review test failures to understand dependencies
- Add temporary compatibility layer if needed

**Examples of potential issues:**
```python
# Test that might break:
def test_detector_is_cached():
    env1 = get_environment_info()
    env2 = get_environment_info()
    assert env1 is env2  # Might fail if expecting same object

# Fix: Update test to reflect context-local behavior
def test_detector_is_cached_per_context():
    env1 = get_environment_info()
    env2 = get_environment_info()
    # Both use same detector within this context
    assert env1.environment == env2.environment
```

## Implementation Risks

### Risk 4: Incomplete Fixture Cleanup
**Risk**: Missing some manual reset_cache() calls or autouse fixtures

**Likelihood**: Medium
**Impact**: Low

**Mitigation:**
- Grep entire codebase for `reset_cache()`
- Grep for `environment_detector` imports
- Use IDE "find usages" to locate all references
- Create checklist of files to update

**Detection:**
```bash
# Find all reset_cache() calls
grep -r "reset_cache()" tests/

# Find all environment_detector imports
grep -r "from.*environment_detector" tests/

# Find all direct detector usage
grep -r "environment_detector\." tests/
```

### Risk 5: Pytest-xdist Compatibility Issues
**Risk**: Context isolation might not work correctly with parallel test execution

**Likelihood**: Very Low (pytest detection same in all workers)
**Impact**: Medium (would need investigation)

**Mitigation:**
- Pytest detection (`_IS_PYTEST`) works identically in all xdist workers
- Each xdist worker is a separate process with independent imports
- Each process gets its own context variables (process isolation)
- Test with pytest-xdist early (Phase 3)

**Validation:**
- Run: `pytest tests/integration/ -n auto` 10 times
- Compare stability with serial execution
- Should see same or better stability than current state

**Note**: Each xdist worker will detect pytest independently and use context-local mode. No cross-worker pollution possible due to process isolation.

## Organizational Risks

### Risk 6: Learning Curve for ContextVars
**Risk**: Future developers unfamiliar with contextvars pattern

**Likelihood**: Medium
**Impact**: Low

**Mitigation:**
- Comprehensive documentation (Phase 4)
- Clear docstrings with examples
- ADR explaining decision rationale
- Context isolation is "invisible" to most code (just works)

**Education Materials:**
- Add "Context Variables Explained" section to dev docs
- Link to Python contextvars documentation
- Provide comparison with thread-local storage

## Rollback Strategy

### If Critical Issues Arise

**Step 1: Preserve Current Working State**
```bash
git checkout -b rollback/context-local-detector
git revert <commit-hash>  # Revert context-local changes
```

**Step 2: Disable Hybrid Mode**
```python
# Simplest rollback: force production mode everywhere
# In app/core/environment/api.py
_IS_PYTEST = False  # Force global singleton for all contexts

# Or restore pure global singleton:
environment_detector = EnvironmentDetector()

def get_environment_info(...):
    return environment_detector.detect_with_context(...)
```

**Step 3: Restore Autouse Fixtures**
- Re-add reset_cache() calls to conftest files
- Restore manual cleanup code

**Step 4: Document Issues**
- Create GitHub issue with failure details
- Document what went wrong
- Plan alternative approach

**Rollback Time Estimate**: <1 hour (simple git revert)

# Appendix

## Research Findings

### Hybrid Approach vs Pure Context-Local vs Global Singleton

| Aspect | Hybrid (Chosen) | Pure Context-Local | Pure Global |
|--------|----------------|-------------------|-------------|
| **Production Performance** | ✅ Zero overhead | ⚠️ Minimal overhead | ✅ Zero overhead |
| **Test Isolation** | ✅ Automatic | ✅ Automatic | ❌ Manual fixtures |
| **Migration Risk** | ✅ Very Low | ⚠️ Medium | N/A |
| **Rollback Complexity** | ✅ Simple flag | ⚠️ Full revert | N/A |
| **Code Complexity** | ⚠️ Branch logic | ✅ Simple | ✅ Simple |
| **Production Behavior** | ✅ Unchanged | ⚠️ Changed | ✅ Current |

### ContextVars vs Thread-Local Storage (for Test Mode)

**ContextVars Advantages (used in test mode):**
- Work with asyncio (thread-local doesn't)
- Automatic cleanup (thread-local requires manual management)
- Safer default isolation
- Built-in Python 3.7+ (no dependencies)

**Thread-Local Disadvantages:**
- Doesn't work with async/await
- Manual lifecycle management
- Not pytest-friendly
- Can leak between tests if not cleaned up

**Production Mode:**
- Uses neither ContextVars nor Thread-Local
- Uses global singleton (existing approach)
- Zero overhead, proven reliability

### Pytest Detection and Context Isolation

**Pytest Detection Pattern (same as config.py):**
```python
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))
```

**Why This Works:**
- `"pytest" in sys.modules` - True when pytest is imported
- `os.getenv("PYTEST_CURRENT_TEST")` - Set by pytest during test execution
- Both checks cover all pytest invocation methods
- Evaluated once at import time (no runtime overhead)

**Pytest Context Isolation (Test Mode):**
1. Each test function is a new execution context
2. Fixtures create child contexts
3. Context vars automatically isolate per test
4. No manual management needed

**Pytest-xdist Behavior:**
- Each worker is a separate process
- Each process independently detects pytest
- Each process has independent contextvars
- No cross-worker pollution possible
- Context isolation maintained in all workers

### Performance Analysis

**Production Mode (Unchanged):**
- Global singleton created once at import
- Direct method call: `environment_detector.detect_with_context()`
- Zero branching overhead (same as current implementation)
- Zero memory overhead (same as current implementation)
- Performance: **Identical to current**

**Test Mode (Context-Local):**
- Overhead per test:
  - Pytest detection check: ~1ns (compiled at import)
  - `if _IS_PYTEST` branch: ~1-2ns (predictable)
  - ContextVar.get(): ~50-100ns (negligible)
  - EnvironmentDetector.__init__() (first call): ~1-5μs (lightweight)
- Overall impact per test: <0.001% (unmeasurable)

**Memory Overhead:**
- Production: Zero change
- Tests: One EnvironmentDetector per test (~1-2KB each)
- Tests: Garbage collected when test ends
- Tests: Negligible impact on test suite memory

## Technical Specifications

### ContextVar Type Signature
```python
from typing import Optional
import contextvars

_detector_context: contextvars.ContextVar[Optional[EnvironmentDetector]] = (
    contextvars.ContextVar(
        name='environment_detector',
        default=None
    )
)
```

### Lazy Initialization Pattern
```python
def get_environment_info(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> EnvironmentInfo:
    # Get detector for this context (returns None if not set)
    detector = _detector_context.get()

    # Lazy initialization on first access
    if detector is None:
        detector = EnvironmentDetector()
        _detector_context.set(detector)

    # Use context-local detector
    return detector.detect_with_context(feature_context)
```

### Context Lifecycle
```
Test Start → New Context Created
    ↓
First get_environment_info() call
    ↓
ContextVar.get() returns None
    ↓
Create EnvironmentDetector()
    ↓
ContextVar.set(detector)
    ↓
Subsequent calls return same detector
    ↓
Test End → Context Destroyed
    ↓
Detector Garbage Collected
```

## Reference Implementation

### Complete Updated `api.py` (Hybrid Approach)
```python
"""
Environment detection API with pytest-aware hybrid isolation.

This module provides environment detection with automatic test isolation
using a hybrid approach:
- Production: Global singleton for zero overhead
- Tests (pytest): Context-local instances for automatic isolation

The implementation is transparent to all calling code.
"""

import sys
import os
import contextvars
from typing import Optional

from .enums import Environment, FeatureContext
from .models import EnvironmentInfo
from .detector import EnvironmentDetector

# Detect pytest at import time (same pattern as config.py)
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))

if _IS_PYTEST:
    # Testing mode: Use context-local storage for automatic test isolation
    _detector_context: contextvars.ContextVar[Optional[EnvironmentDetector]] = (
        contextvars.ContextVar('environment_detector', default=None)
    )
    environment_detector = None  # No global singleton in test mode
else:
    # Production mode: Use global singleton for performance
    environment_detector = EnvironmentDetector()
    _detector_context = None  # No context var overhead in production


def get_environment_info(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> EnvironmentInfo:
    """
    Get environment information with pytest-aware automatic isolation.

    Uses hybrid approach based on pytest detection:
    - Production: Uses global singleton for zero overhead
    - Tests (pytest): Uses context-local instances for automatic isolation

    Args:
        feature_context: Feature context for specialized detection.

    Returns:
        EnvironmentInfo with detected environment and confidence.

    Behavior:
        Production Mode:
        - Uses global singleton created at import
        - Same behavior as current implementation
        - Zero performance overhead

        Test Mode (pytest):
        - First call in test creates new EnvironmentDetector
        - Subsequent calls in same test reuse the instance
        - Different tests get completely independent detectors
        - Automatic garbage collection when test ends
        - No manual cleanup needed

    Examples:
        >>> # Same code works in both production and tests
        >>> env = get_environment_info()
        >>> if env.environment == Environment.PRODUCTION:
        ...     configure_production_settings()
        >>>
        >>> # In pytest - each test gets fresh detector
        >>> # In production - uses global singleton
    """
    if _IS_PYTEST:
        # Test mode: context-local for isolation
        detector = _detector_context.get()
        if detector is None:
            detector = EnvironmentDetector()
            _detector_context.set(detector)
        return detector.detect_with_context(feature_context)
    else:
        # Production mode: global singleton (zero overhead)
        return environment_detector.detect_with_context(feature_context)


def is_production_environment(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> bool:
    """
    Check if running in production with pytest-aware detection.

    Uses hybrid approach (global singleton in production, context-local in tests).

    Args:
        feature_context: Feature context for specialized detection.

    Returns:
        True if production environment detected with confidence > 0.60.

    Examples:
        >>> if is_production_environment():
        ...     configure_production_logging()
    """
    env_info = get_environment_info(feature_context)
    return env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.60


def is_development_environment(
    feature_context: FeatureContext = FeatureContext.DEFAULT
) -> bool:
    """
    Check if running in development with pytest-aware detection.

    Uses hybrid approach (global singleton in production, context-local in tests).

    Args:
        feature_context: Feature context for specialized detection.

    Returns:
        True if development environment detected with confidence > 0.60.

    Examples:
        >>> if is_development_environment():
        ...     enable_debug_logging()
    """
    env_info = get_environment_info(feature_context)
    return env_info.environment == Environment.DEVELOPMENT and env_info.confidence > 0.60


def reset_detector_for_context() -> None:
    """
    Reset detector for current context (pytest mode only).

    Rarely needed - each test automatically gets fresh detector.
    Only works in pytest mode. In production, this is a no-op.

    Examples:
        >>> def test_env_change_detection():
        ...     env1 = get_environment_info()
        ...
        ...     os.environ["ENVIRONMENT"] = "production"
        ...     reset_detector_for_context()  # Force new detector (pytest only)
        ...
        ...     env2 = get_environment_info()
        ...     assert env1.environment != env2.environment
    """
    if _IS_PYTEST and _detector_context is not None:
        _detector_context.set(None)
    # In production mode, this is a no-op (environment_detector is global)
```

## Success Metrics

### Quantitative Metrics
- **Test Stability**: 0 flaky failures across 10 consecutive runs
- **Code Reduction**: 30-50 lines of fixture code removed
- **Production Performance**: 0% change (identical code path)
- **Test Performance**: <5% change in test execution time
- **Coverage**: Maintain or improve test coverage

### Qualitative Metrics
- **Code Clarity**: Tests are simpler and more focused
- **Maintainability**: Fewer global state concerns
- **Developer Confidence**: Tests are reliable and deterministic
- **Onboarding**: New developers understand pattern quickly
- **Production Safety**: Zero risk to production behavior

## Related Work

### Similar Patterns in Codebase
- **Pytest detection in `config.py`**: Uses same pattern for conditional .env loading
- **FastAPI app factory pattern** (`create_app()`): Similar isolation approach for tests
- **Settings factory pattern** (`create_settings()`): Similar per-test instance creation
- **Hybrid detector**: Complements existing patterns with test/production awareness

### Precedent: config.py Pytest Detection
The hybrid approach follows the proven pattern from `backend/app/core/config.py`:
```python
# Same pytest detection pattern
_IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))

if not _IS_PYTEST:
    load_dotenv(project_root / ".env")
else:
    # Pytest-specific behavior
    os.environ.pop("RESILIENCE_PRESET", None)
    os.environ.pop("RESILIENCE_CUSTOM_CONFIG", None)
```

This pattern is already tested, proven, and understood in the codebase.

### Industry Precedents
- FastAPI uses context-local request state
- Django uses thread-local for request handling
- AsyncIO uses context vars for task-local storage

### Future Applications
Pattern can be applied to:
- Cache instance management (per-request cache isolation)
- Resilience policy instances (per-task circuit breaker state)
- Monitoring context (per-request tracing)
</PRD>
