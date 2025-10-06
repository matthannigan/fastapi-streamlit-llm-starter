# Integration Tests - Current Status & Next Steps

## Problem Summary

Integration tests fail intermittently with "🔒 SECURITY ERROR: Failed to initialize mandatory security features" due to **global state pollution** from the `environment_detector` singleton.

## Root Cause

### Global Singleton Issue

**File**: `app/core/environment/api.py`
```python
# Global instance created at module import
environment_detector = EnvironmentDetector()
```

This singleton:
- Created once when module is imported
- Persists across ALL tests (even serial execution)
- Has internal caching (`self._signal_cache`)
- Reads environment variables and caches detection results

### How Tests Fail

1. Test A runs with `ENVIRONMENT='testing'` (via autouse fixture)
2. Test B explicitly sets `ENVIRONMENT='production'` to test production behavior
3. `environment_detector` caches production detection
4. Test C expects testing environment but gets cached production detection
5. SecurityConfig tries to use production TLS certificates → SECURITY ERROR

## What We've Tried

### ✅ Implemented (Partial Success)

1. **Autouse Fixture** (`tests/integration/conftest.py`):
   - Sets `ENVIRONMENT='testing'` for all integration tests
   - Helps but doesn't solve caching issue

2. **Fixed `production_environment_integration` Fixture**:
   - Changed from `os.environ` to `monkeypatch`
   - Changed scope from `module` to `function`
   - Ensures proper cleanup per test

3. **Serial Execution Hook** (`tests/integration/cache/conftest.py`):
   - Forces cache tests to run in same xdist worker
   - Reduces parallel execution race conditions

4. **Module-level Markers**:
   - Added `pytestmark = pytest.mark.no_parallel` to cache test modules
   - Backup mechanism for serial execution

### ❌ Doesn't Fully Solve

Even with `-n 0` (serial execution) and all fixtures:
- **Run 1**: 12 failures, 15 errors
- **Run 2**: 6 failures, 9 errors
- **Run 3**: 13 failures, 14 errors

Tests are still flaky due to `environment_detector` caching.

## Recommended Solutions

### Option 1: Add Reset Method to EnvironmentDetector (Proper Fix)

**Add to `app/core/environment/detector.py`**:
```python
def reset_cache(self):
    """Clear cached signals for testing isolation."""
    self._signal_cache.clear()
```

**Add autouse fixture**:
```python
@pytest.fixture(autouse=True)
def reset_environment_detector():
    """Reset environment detector cache before each test."""
    from app.core.environment.api import environment_detector
    environment_detector.reset_cache()
    yield
    environment_detector.reset_cache()
```

### Option 2: Make EnvironmentDetector Thread-Local (Better Architecture)

Replace global singleton with request-scoped instance:
```python
# Instead of module-level global
_detector_context = contextvars.ContextVar('detector', default=None)

def get_environment_info(...):
    detector = _detector_context.get()
    if detector is None:
        detector = EnvironmentDetector()
        _detector_context.set(detector)
    return detector.detect_with_context(...)
```

### Option 3: Skip Problematic Tests (Temporary Workaround)

Mark consistently failing tests with `@pytest.mark.skip(reason="Environment detection caching issue #XXX")` and create GitHub issues to track fixes.

## Current Test Results Pattern

### Consistently Failing Tests

These fail in most runs:
- `test_cache_security.py::TestCacheSecurityIntegration` (4 tests)
- `test_cache_integration.py` (3 tests)
- `test_cache_encryption.py::test_environment_configuration_integration_with_factory`
- `test_auth_status_integration.py::test_auth_status_environment_context_integration_production_vs_development`

### Intermittently Failing Tests

These fail sometimes:
- `test_encryption_end_to_end_workflows.py::TestEncryptedCacheEndToEndWorkflows` (8 tests)
- `test_cache_preset_behavior.py::TestCachePresetBehavior` (3 tests)
- `test_encryption_factory_integration.py::TestCacheFactoryEncryptionIntegration` (varies)

## Recommendation

**Immediate**: Implement Option 1 (add `reset_cache()` method) as it's:
- Low risk (doesn't change production code behavior)
- Surgical (only affects testing)
- Quick to implement

**Long-term**: Consider Option 2 for better architectural isolation.

## Files Modified

- `tests/conftest.py` - Added pytest hook for `no_parallel` marker
- `tests/integration/conftest.py` - Added global autouse fixture, fixed production fixture
- `tests/integration/cache/conftest.py` - Added autouse fixture + pytest hook for serial execution
- `tests/integration/cache/test_*.py` - Added `pytestmark = pytest.mark.no_parallel` to 9 modules
- `tests/integration/README.md` - Documentation
- `tests/integration/cache/ENVIRONMENT_OVERRIDE.md` - Troubleshooting guide
