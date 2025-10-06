# Integration Tests - Environment and Parallel Execution

## Overview

Integration tests manipulate shared global state (environment variables, `environment_detector` instance) that causes race conditions when run in parallel with pytest-xdist.

### Solutions Implemented

1. **Autouse Fixture** (`tests/integration/cache/conftest.py`):
   - Sets `ENVIRONMENT='testing'` for all cache integration tests
   - Prevents "🔒 SECURITY ERROR" by ensuring SecurityConfig uses test settings

2. **Serial Execution Hook** (`tests/integration/cache/conftest.py`):
   - Forces ALL cache integration tests to run in same xdist worker (sequentially)
   - Prevents race conditions from parallel execution

### Running Integration Tests

**Recommended approach (serially)**:
```bash
# From backend directory
PYTHONPATH=$PWD ../.venv/bin/python -m pytest tests/integration/ -n 0

# Or use Makefile (will be updated to use -n 0)
make test-integration
```

**Why `-n 0` (serial execution)?**
- Integration tests share global `environment_detector` instance
- Pytest-xdist workers share the same Python process/imports
- Environment variable changes in one test affect other tests in parallel workers
- Running serially eliminates race conditions (slower but reliable)

## Autouse Fixture

**Location**: `tests/integration/cache/conftest.py::setup_testing_environment`

```python
@pytest.fixture(autouse=True)
def setup_testing_environment(monkeypatch):
    """Set ENVIRONMENT='testing' for all cache integration tests."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
```

## Why This Is Needed

Without `ENVIRONMENT` set:
- `SecurityConfig.create_for_environment()` defaults to **production-level security**
- Production requires TLS certificates at paths like `/etc/ssl/redis-client.crt`
- These paths don't exist in test environments
- Cache initialization fails with security error

With `ENVIRONMENT='testing'`:
- TLS enabled but self-signed certs accepted
- Reduced monitoring overhead for faster tests
- Shorter timeouts appropriate for test execution

## Tests That Override This Fixture

### 1. `test_encryption_end_to_end_workflows.py::test_configuration_workflow_encryption_initialization_across_environments`

**File**: `tests/integration/cache/test_encryption_end_to_end_workflows.py`

**Purpose**: Explicitly tests that encryption initialization works correctly across different environments (development, production, testing).

**Environment Overrides**:
```python
# Tests development environment
monkeypatch.setenv("ENVIRONMENT", "development")
monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")

# Tests production environment
monkeypatch.setenv("ENVIRONMENT", "production")
monkeypatch.setenv("REDIS_ENCRYPTION_KEY", prod_key)

# Tests testing environment (redundant with autouse but explicitly sets it)
monkeypatch.setenv("ENVIRONMENT", "testing")
monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_key)
```

**Why Override Needed**: This test validates encryption behavior is consistent across all deployment environments. It must explicitly set each environment to verify environment-specific configuration.

## Adding New Tests That Need Different Environments

If you need to test production/development/staging-specific behavior:

```python
@pytest.mark.asyncio
async def test_production_specific_behavior(self, monkeypatch):
    """Test that requires production environment."""
    # Override the autouse fixture's default
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "production-key")

    # Your test code here
    # SecurityConfig will now use production settings
```

## Related Documentation

- **App Factory Pattern**: `docs/guides/developer/APP_FACTORY_GUIDE.md`
- **SecurityConfig Implementation**: `app/infrastructure/cache/security.py:create_for_environment()`
- **Integration Testing Guide**: `docs/guides/testing/TESTING.md`

## Troubleshooting

### Error: "🔒 SECURITY ERROR: Failed to initialize mandatory security features"

**Cause**: Test is running without `ENVIRONMENT` set (autouse fixture not applying)

**Solution**:
1. Verify test file is in `tests/integration/cache/` directory
2. Check that `conftest.py` is being loaded
3. Ensure test doesn't unset `ENVIRONMENT` before cache creation

### Error: Test expects production behavior but gets testing behavior

**Cause**: Autouse fixture is overriding your intended environment

**Solution**: Use `monkeypatch.setenv("ENVIRONMENT", "production")` in your test to override the autouse fixture's default
