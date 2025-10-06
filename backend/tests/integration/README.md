# Integration Tests

## Running Integration Tests

Integration tests should be run **serially** (not in parallel) to avoid race conditions from shared global state.

### Recommended Commands

```bash
# From backend/ directory
PYTHONPATH=$PWD ../.venv/bin/python -m pytest tests/integration/ -n 0

# From project root using Makefile
make test-backend-integration
```

### Why Serial Execution?

Integration tests manipulate:
- Environment variables
- Global singleton instances (`environment_detector`)
- Docker containers
- Shared cache state

Running in parallel with pytest-xdist (`-n auto`) causes race conditions where:
- One test's environment changes affect another test in a different worker
- Global instances cache stale state from previous tests
- Tests pass individually but fail intermittently when run together

### Performance Trade-off

- **Serial (`-n 0`)**: Slower (~6-8s) but 100% reliable
- **Parallel (`-n auto`)**: Faster (~4-5s) but 0-15 failures per run (flaky)

Integration tests are a small subset of the test suite, so the serial execution overhead is acceptable for reliability.

## Critical Testing Pattern: Always Use monkeypatch for Environment Variables

**⚠️ CRITICAL: Never use direct `os.environ` manipulation in tests. Always use `monkeypatch.setenv()`.**

### The Problem with Direct Environment Variable Modification

Direct `os.environ[]` assignment bypasses pytest's cleanup mechanisms and causes **permanent test pollution**:

```python
# ❌ BAD - Causes permanent pollution
def test_production_behavior():
    os.environ["ENVIRONMENT"] = "production"  # NEVER DO THIS
    # This change persists across ALL subsequent tests!
```

**Why this is dangerous:**
1. **No automatic cleanup**: Changes persist after test completes
2. **Test order dependency**: Later tests see polluted environment state
3. **Flaky tests**: Tests pass/fail based on execution order
4. **Parallel execution breaks**: Worker processes inherit polluted state
5. **Debugging nightmare**: Failures appear random and intermittent

### The Solution: Use monkeypatch.setenv()

Always use pytest's `monkeypatch` fixture to modify environment variables:

```python
# ✅ GOOD - Automatic cleanup
def test_production_behavior(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Change is automatically cleaned up after test completes
```

**Benefits:**
1. **Automatic cleanup**: pytest restores original value after test
2. **Test isolation**: Each test gets clean environment
3. **Parallel safe**: Changes are isolated to test process
4. **Explicit dependency**: Test signature shows it modifies environment
5. **Reliable**: Tests pass/fail consistently regardless of order

### Complete Testing Patterns

#### Pattern 1: Single Environment Variable

```python
def test_with_environment_override(monkeypatch):
    """Test behavior with specific environment setting."""
    # Set environment variable
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-key")

    # Create app AFTER setting environment
    app = create_app()
    client = TestClient(app)

    # Test with production environment
    response = client.get("/v1/auth/status")
    assert response.status_code == 401  # Production requires auth
```

#### Pattern 2: Multiple Environment Variables

```python
def test_with_multiple_overrides(monkeypatch):
    """Test with multiple environment variable overrides."""
    # Set multiple variables
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("CACHE_PRESET", "production")
    monkeypatch.setenv("ENABLE_AI_CACHE", "true")

    # Create app with all overrides active
    app = create_app()
    # Test behavior...
```

#### Pattern 3: Removing Environment Variables

```python
def test_without_environment_variable(monkeypatch):
    """Test behavior when environment variable is missing."""
    # Remove environment variable
    monkeypatch.delenv("API_KEY", raising=False)

    # Test behavior with missing variable
    with pytest.raises(ConfigurationError):
        create_app()
```

#### Pattern 4: Environment Fixtures (Reusable Patterns)

```python
# In conftest.py
@pytest.fixture
def production_environment(monkeypatch):
    """Configure production environment for testing."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("CACHE_PRESET", "production")
    return monkeypatch

@pytest.fixture
def development_environment(monkeypatch):
    """Configure development environment for testing."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("CACHE_PRESET", "development")
    return monkeypatch

# In test files
def test_production_security(production_environment):
    """Test uses production_environment fixture."""
    app = create_app()
    # Test production behavior...

def test_development_mode(development_environment):
    """Test uses development_environment fixture."""
    app = create_app()
    # Test development behavior...
```

#### Pattern 5: Testing Environment Transitions

```python
def test_environment_transitions(monkeypatch):
    """Test behavior across different environment configurations."""
    # Test development first
    monkeypatch.setenv("ENVIRONMENT", "development")
    dev_app = create_app()
    dev_client = TestClient(dev_app)

    dev_response = dev_client.get("/v1/health")
    assert dev_response.status_code == 200

    # Now test production (monkeypatch automatically cleans up)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-key")
    prod_app = create_app()
    prod_client = TestClient(prod_app)

    prod_response = prod_client.get("/v1/health")
    assert prod_response.status_code == 200
```

### Common Mistakes and Fixes

#### Mistake 1: Direct os.environ Assignment

```python
# ❌ BAD - Permanent pollution
import os

def test_environment():
    os.environ["ENVIRONMENT"] = "production"
    # This persists forever!

# ✅ GOOD - Automatic cleanup
def test_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Automatically cleaned up
```

#### Mistake 2: Setting Environment After App Creation

```python
# ❌ BAD - Environment change happens too late
def test_environment(monkeypatch):
    app = create_app()  # Uses current environment
    monkeypatch.setenv("ENVIRONMENT", "production")  # Too late!

# ✅ GOOD - Environment set before app creation
def test_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    app = create_app()  # Uses production environment
```

#### Mistake 3: Forgetting monkeypatch Parameter

```python
# ❌ BAD - No monkeypatch parameter
def test_environment():
    monkeypatch.setenv("ENVIRONMENT", "production")  # NameError!

# ✅ GOOD - Include monkeypatch in test signature
def test_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
```

#### Mistake 4: Using os.environ in Fixtures

```python
# ❌ BAD - Direct modification in fixture
@pytest.fixture
def production_env():
    os.environ["ENVIRONMENT"] = "production"
    yield
    # Manual cleanup is error-prone

# ✅ GOOD - Use monkeypatch in fixtures
@pytest.fixture
def production_env(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Automatic cleanup by pytest
    return monkeypatch
```

### App Factory Pattern Integration

The App Factory Pattern works seamlessly with monkeypatch:

```python
def test_with_fresh_app_and_environment(monkeypatch):
    """
    Demonstrates proper integration of App Factory Pattern with monkeypatch.

    Key Principle: Set environment BEFORE creating app.
    """
    # Step 1: Configure environment
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("CACHE_PRESET", "disabled")
    monkeypatch.setenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "true")

    # Step 2: Create fresh app with configured environment
    app = create_app()

    # Step 3: Test with fully isolated configuration
    client = TestClient(app)
    response = client.get("/v1/health")
    assert response.status_code == 200

    # Step 4: Cleanup happens automatically after test
```

### Migration Checklist

If updating existing tests that use direct `os.environ` manipulation:

- [ ] Replace all `os.environ["VAR"] = "value"` with `monkeypatch.setenv("VAR", "value")`
- [ ] Replace all `del os.environ["VAR"]` with `monkeypatch.delenv("VAR", raising=False)`
- [ ] Add `monkeypatch` parameter to test function signatures
- [ ] Update fixtures to use `monkeypatch` instead of direct modification
- [ ] Remove manual cleanup code (pytest handles it automatically)
- [ ] Verify tests pass when run in different orders: `pytest --random-order`
- [ ] Ensure app creation happens AFTER environment configuration

### Test Organization

```
tests/integration/
├── auth/          # Authentication integration tests
├── cache/         # Cache infrastructure integration tests (forced serial via conftest hook)
├── environment/   # Environment detection integration tests
├── health/        # Health check integration tests
└── startup/       # Application startup integration tests
```

### Troubleshooting

**Error**: "🔒 SECURITY ERROR: Failed to initialize mandatory security features"

**Cause**: Test running without `ENVIRONMENT` set or with stale environment detection

**Solution**:
1. Ensure running with `-n 0` (serial)
2. Check `tests/integration/cache/conftest.py` has autouse fixture setting `ENVIRONMENT='testing'`
3. Verify no other test is unsetting `ENVIRONMENT` during execution

**Error**: Tests pass individually but fail when run together

**Cause**: Shared state pollution from parallel execution

**Solution**: Always run integration tests with `-n 0`
