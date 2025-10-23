# Middleware Integration Testing

## Prompt 5: Create Integration Test Fixtures

**Purpose**: Implement all required test fixtures from the TEST_PLAN.md into the target directory's `conftest.py` before implementing integration tests. This establishes the testing infrastructure that will be used as-is during test implementation.

**Context**: This step creates the foundational test fixtures identified in the test plan's `### Required Test Fixtures` section. By implementing fixtures first, we ensure consistent testing infrastructure and prevent agents from creating ad-hoc or inconsistent fixtures during test implementation.

**When to Use**: After test plan review (Prompt 4) and before test implementation (Prompt 6).

---

## Input Requirements

**Required Files**:
1. **Test Plan** (Prompt 3/4 output): Contains `### Required Test Fixtures` section
    - Location: `backend/tests/integration/middleware/TEST_PLAN_FINAL.md`:930-1072

2. **Target Directory**: Where fixtures will be implemented
    - Primary location: `backend/tests/integration/middleware/conftest.py`
    - Shared fixtures: `backend/tests/integration/conftest.py` (for cross-suite reuse)

3. **Reference Documentation**:
    - `docs/guides/testing/INTEGRATION_TESTS.md` - Integration testing philosophy
    - `backend/CLAUDE.md` - App Factory Pattern and testing guidelines
    - `backend/tests/integration/README.md` - Integration test patterns
    - `backend/app/core/middleware/README.md` - Middleware explainer
    - `backend/contracts/main.pyi` - Public contract for `main.py`
    - `backend/contracts/core/middleware/*.pyi` - Public contracts for core middleware services component 

---

## Fixture Implementation Process

### Step 1: Review Test Plan Fixtures (10 minutes)

**Read the `### Required Fixtures` section from the test plan**:

The test plan should categorize fixtures as:
- **Reusable Existing Fixtures**: Already implemented, reference by import
- **Fixtures to Adapt**: Copy pattern from existing fixtures with modifications
- **New Fixtures Needed**: Implement from scratch following patterns

**Understand the fixture hierarchy**:
1. **Shared fixtures** (`backend/tests/integration/conftest.py`):
   - Used across multiple integration test suites
   - Examples: `fakeredis_client`, `authenticated_headers`, `integration_client`

2. **Suite-specific fixtures** (`backend/tests/integration/middleware/conftest.py`):
   - Used only within this integration test suite
   - Examples: Service instances, custom settings, domain-specific test data

**Flag if missing**: If test plan lacks fixture documentation, request clarification before proceeding.

### Step 2: Verify Existing Fixture Availability (15 minutes)

**Check what's already available in shared fixtures**:

```bash
# Review existing integration test fixtures
cat backend/tests/integration/conftest.py
ls -la backend/tests/integration/**/conftest.py
```

**For each "Reusable Existing Fixture" in the test plan**:
- [ ] Verify fixture exists at documented location
- [ ] Confirm fixture signature matches test plan description
- [ ] Check fixture scope (function/session) is appropriate
- [ ] Validate fixture dependencies are available
- [ ] Note any version differences or recent changes

**Document verification results**:
```markdown
## Verified Existing Fixtures

 **fakeredis_client** - `integration/conftest.py:229-262`
   - Verified: Available and up-to-date
   - Scope: function (correct for test isolation)
   - Usage: Import directly, no modifications needed

� **authenticated_headers** - `integration/conftest.py:92-97`
   - Verified: Available but may need API key override for this suite
   - Scope: function
   - Usage: May need to create suite-specific variant with different key
```

### Step 3: Implement App Factory Pattern Fixtures (30 minutes)

**CRITICAL**: All integration tests must use the App Factory Pattern for proper test isolation.

**Reference**: See `backend/CLAUDE.md` - "App Factory Pattern" section for comprehensive guidance.

#### Pattern 1: Basic Test Client (Required for API tests)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture(scope="function")
def test_client(monkeypatch):
    """
    Test client for [component] integration tests with isolated app instance.

    Uses App Factory Pattern to create fresh FastAPI app that picks up
    current environment variables set via monkeypatch.

    Returns:
        TestClient: HTTP client with fresh app instance

    Note:
        - Environment must be set BEFORE calling this fixture
        - Each test gets completely isolated app instance
        - Settings are loaded fresh from current environment
    """
    # Set default test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("API_KEY", "test-api-key-12345")

    # Create fresh app AFTER environment is configured
    app = create_app()
    return TestClient(app)
```

#### Pattern 2: Custom Settings Pattern (For specific configurations)

```python
from app.core.config import create_settings


@pytest.fixture(scope="function")
def test_settings(monkeypatch):
    """
    Real Settings instance for [component] integration tests.

    Provides actual Settings object with test-appropriate configuration
    that can be used to initialize services and verify behavior.

    Returns:
        Settings: Fresh settings instance from current environment

    Note:
        - Uses factory pattern to pick up current environment
        - Modify via monkeypatch BEFORE calling this fixture
        - Settings validation rules are fully applied
    """
    # Set test configuration
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("CACHE_PRESET", "disabled")
    monkeypatch.setenv("RESILIENCE_PRESET", "simple")

    # Create fresh settings from current environment
    return create_settings()
```

#### Pattern 3: Component-Specific Test Client (For custom app configuration)

```python
@pytest.fixture(scope="function")
def [component]_test_client(monkeypatch, test_settings):
    """
    Test client with [component]-specific configuration.

    Creates isolated app with custom settings for testing [component]
    integration scenarios.

    Args:
        monkeypatch: Pytest fixture for environment configuration
        test_settings: Real Settings instance with test configuration

    Returns:
        TestClient: HTTP client configured for [component] testing
    """
    # Set component-specific environment
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("[COMPONENT]_ENABLED", "true")

    # Create app with custom settings
    app = create_app(settings_obj=test_settings)
    return TestClient(app)
```

**Key Implementation Rules**:
1.  **Always use `monkeypatch.setenv()`** - NEVER use `os.environ[]` directly
2.  **Set environment BEFORE creating app** - Order matters for factory pattern
3.  **Use function scope** - Each test gets fresh instances for isolation
4.  **Call `create_app()` in fixture** - Don't import module-level `app`

### Step 4: Implement High-Fidelity Fake Fixtures (20 minutes)

**Principle**: Use high-fidelity fakes (fakeredis, testcontainers) instead of mocks for infrastructure dependencies.

#### Pattern 1: FakeRedis Client (Reuse existing if available)

```python
@pytest.fixture(scope="function")
async def fakeredis_client():
    """
    High-fidelity Redis fake for [component] cache integration testing.

    Provides in-memory Redis simulation with full API compatibility,
    enabling realistic cache integration tests without Docker overhead.

    Returns:
        FakeRedis: Async-compatible fake Redis client

    Note:
        - Full Redis API compatibility (commands, data structures)
        - decode_responses=False matches production behavior
        - Each test gets fresh instance (function-scoped)
        - No network calls - all operations in-memory

    See Also:
        - backend/tests/integration/conftest.py:229-262 for shared version
    """
    import fakeredis.aioredis
    return fakeredis.aioredis.FakeRedis(decode_responses=False)
```

#### Pattern 2: Mock External Service (Controlled behavior)

```python
from unittest.mock import AsyncMock, Mock


@pytest.fixture
def mock_[external_service]():
    """
    Mock [external service] for testing [component] integration with controlled behavior.

    Provides predictable mock responses for testing integration scenarios
    without calling real external APIs.

    Returns:
        Mock: Configured mock with default behavior

    Usage:
        ```python
        def test_integration(mock_external_service):
            # Override default behavior
            mock_external_service.call.return_value = "custom response"

            # Test integration
            result = service.process()

            # Verify mock was called correctly
            mock_external_service.call.assert_called_once()
        ```

    Note:
        - Default behavior returns successful responses
        - Override return_value or side_effect in tests for failure scenarios
        - Mock is reset between tests (function scope)
    """
    mock = AsyncMock()  # Use AsyncMock for async services, Mock for sync

    # Set default behavior
    mock.call.return_value = "default success response"
    mock.is_available.return_value = True

    return mock
```

#### Pattern 3: Failing Infrastructure (Resilience testing)

```python
@pytest.fixture
def failing_[infrastructure]():
    """
    [Infrastructure] mock that simulates failures for resilience testing.

    Provides controlled failure simulation to test circuit breakers,
    retries, and graceful degradation patterns.

    Returns:
        Mock: Mock configured to raise exceptions

    Usage:
        ```python
        def test_handles_failure(failing_cache):
            # Cache will raise ConnectionError
            result = service.process_with_cache()

            # Verify graceful degradation
            assert result is not None
            assert "cache unavailable" in result.warnings
        ```
    """
    mock = AsyncMock()
    mock.get.side_effect = ConnectionError("Simulated connection failure")
    mock.set.side_effect = ConnectionError("Simulated connection failure")
    return mock
```

### Step 5: Implement Service Fixtures (30 minutes)

**Create fixtures for the components being integration tested.**

#### Pattern 1: Real Service with Real Dependencies

```python
@pytest.fixture
async def [service_name](test_settings, fakeredis_client):
    """
    Real [ServiceName] instance for integration testing.

    Provides actual service implementation with high-fidelity infrastructure
    fakes, enabling realistic integration testing of [describe integration].

    Args:
        test_settings: Real Settings with test configuration
        fakeredis_client: High-fidelity Redis fake for cache

    Returns:
        [ServiceName]: Fully initialized service instance

    Note:
        - Uses real service implementation (not mocked)
        - Infrastructure dependencies are high-fidelity fakes
        - Service is fully initialized with test configuration
        - Cleanup happens automatically after test
    """
    from app.services.[module] import [ServiceName]

    # Initialize service with real dependencies
    service = [ServiceName](
        settings=test_settings,
        cache_client=fakeredis_client
    )

    # Perform any required initialization
    await service.initialize()

    yield service

    # Cleanup after test
    if hasattr(service, 'cleanup'):
        await service.cleanup()
```

#### Pattern 2: Infrastructure Service with Real Configuration

```python
@pytest.fixture
def [infrastructure_service](test_settings):
    """
    Real [InfrastructureService] for testing integration with [components].

    Provides production infrastructure service with test configuration,
    enabling validation of [describe what's being validated].

    Args:
        test_settings: Real Settings with test configuration

    Returns:
        [InfrastructureService]: Configured infrastructure service

    Note:
        - Uses real infrastructure implementation
        - Configuration from real Settings object
        - Tests actual infrastructure behavior, not mocks
    """
    from app.infrastructure.[module] import [InfrastructureService]

    # Create service with real settings
    service = [InfrastructureService](settings=test_settings)

    return service
```

#### Pattern 3: Service with Mocked External Dependencies

```python
@pytest.fixture
def [service_name]_with_mocked_external(test_settings, mock_external_service):
    """
    [ServiceName] with mocked external service for controlled integration testing.

    Provides real service implementation with mocked external dependencies,
    enabling testing of integration logic without external API calls.

    Args:
        test_settings: Real Settings with test configuration
        mock_external_service: Mock of external service dependency

    Returns:
        [ServiceName]: Service instance with mocked external dependency

    Note:
        - Internal service logic is real (not mocked)
        - External API calls are mocked for test control
        - Enables testing of error handling and edge cases
    """
    from app.services.[module] import [ServiceName]

    # Initialize service with mock external dependency
    service = [ServiceName](
        settings=test_settings,
        external_service=mock_external_service
    )

    return service
```

### Step 6: Implement Test Data Fixtures (15 minutes)

**Create fixtures for reusable test data specific to this integration suite.**

#### Pattern 1: Sample Domain Data

```python
@pytest.fixture
def sample_[domain_entity]():
    """
    Sample [domain entity] for integration testing.

    Provides realistic test data that represents a valid [entity] for
    testing integration scenarios.

    Returns:
        dict: Sample [entity] data with all required fields

    Note:
        - Data is valid according to domain rules
        - Includes all required fields for integration flows
        - Modify in tests for specific scenarios
    """
    return {
        "field1": "value1",
        "field2": "value2",
        # Include all required fields
    }
```

#### Pattern 2: Test Data Factory

```python
@pytest.fixture
def [entity]_factory():
    """
    Factory function for creating [entity] test data with variations.

    Provides flexible test data generation for different integration scenarios.

    Returns:
        Callable: Factory function that creates [entity] instances

    Usage:
        ```python
        def test_integration(entity_factory):
            # Create default entity
            entity1 = entity_factory()

            # Create with overrides
            entity2 = entity_factory(field1="custom value")

            # Test integration
            result = service.process(entity1, entity2)
        ```
    """
    def _create_entity(**overrides):
        """Create test entity with optional field overrides."""
        defaults = {
            "field1": "default1",
            "field2": "default2",
            # Default values
        }
        return {**defaults, **overrides}

    return _create_entity
```

### Step 7: Implement Authentication Fixtures (10 minutes, if needed)

**For API integration tests that require authentication.**

#### Pattern 1: Authenticated Headers (Reuse existing if available)

```python
@pytest.fixture
def authenticated_headers():
    """
    Headers with valid authentication for [component] API integration tests.

    Returns:
        dict: HTTP headers with valid Authorization Bearer token

    Note:
        - Uses test API key configured in environment
        - Valid for all authenticated endpoints
        - Modify in tests for specific auth scenarios

    See Also:
        - backend/tests/integration/conftest.py:92-97 for shared version
    """
    return {
        "Authorization": "Bearer test-api-key-12345",
        "Content-Type": "application/json"
    }
```

#### Pattern 2: Component-Specific Auth Headers

```python
@pytest.fixture
def [component]_auth_headers():
    """
    Authentication headers specific to [component] testing.

    Returns:
        dict: HTTP headers with [component]-specific authentication

    Note:
        - Uses [component]-specific API key
        - May include additional headers required by [component]
    """
    return {
        "Authorization": "Bearer [component]-test-key",
        "X-Component-ID": "[component-id]",
        "Content-Type": "application/json"
    }
```

### Step 8: Document Fixtures and Usage (10 minutes)

**Create clear documentation for all fixtures at the top of conftest.py.**

```python
"""
Integration test fixtures for [component] testing.

This module provides fixtures for testing [component] integration with
[list key dependencies]. All fixtures follow the App Factory Pattern
for proper test isolation.

Key Fixtures:
    - test_client: HTTP client with isolated app instance
    - test_settings: Real Settings with test configuration
    - [service_name]: Real service with high-fidelity dependencies
    - fakeredis_client: High-fidelity Redis fake (from shared fixtures)
    - authenticated_headers: Valid auth headers (from shared fixtures)

Shared Fixtures (from backend/tests/integration/conftest.py):
    - fakeredis_client: In-memory Redis simulation
    - authenticated_headers: Valid API authentication
    - integration_client: Pre-configured test client

Usage:
    Test files in this directory automatically have access to all fixtures
    defined here and in parent conftest.py files.

    ```python
    def test_integration(test_client, authenticated_headers):
        response = test_client.post("/api/endpoint", headers=authenticated_headers)
        assert response.status_code == 200
    ```

Critical Patterns:
    - Always use monkeypatch.setenv() for environment variables
    - Set environment BEFORE creating app/settings
    - Use function scope for test isolation
    - Use high-fidelity fakes (fakeredis) over mocks

See Also:
    - backend/CLAUDE.md - App Factory Pattern guide
    - docs/guides/testing/INTEGRATION_TESTS.md - Integration testing philosophy
    - backend/tests/integration/README.md - Integration test patterns
"""
```

### Step 9: Fix Lint Errors (10-15 minutes)

**CRITICAL**: Run MyPy linting on the generated conftest.py and fix all type errors before proceeding to test implementation.

**Why This Step Matters:**

Generated fixture code often has type annotation issues:
- Missing type hints on fixture return values
- Incorrect async/sync generator types
- Invalid constructor parameters from hallucination
- Missing TYPE_CHECKING imports for forward references
- Incorrect class names or import paths

**Fixing these NOW prevents test implementation blockers later.**

**Step 9.1: Run Lint Check**

```bash
cd backend
../.venv/bin/python -m mypy backend/tests/integration/middleware/conftest.py
```

**Step 9.2: Fix Lint Errors Automatically**

If lint errors are found, use the lint-fixer agent to resolve them:

```
Use the Task tool to launch the lint-fixer agent with:

"Fix all MyPy lint errors in backend/tests/integration/middleware/conftest.py"
```

The lint-fixer agent will:
- Add missing type annotations to fixtures
- Fix async generator return types (`AsyncGenerator[Type, None]`)
- Add TYPE_CHECKING imports for forward references
- Correct invalid constructor parameters
- Fix incorrect class names or import paths
- Add `# type: ignore` for expected library stub issues

**Step 9.3: Verify Fixes**

After lint-fixer completes, verify:

```bash
# Should show 0 errors or only expected informational warnings
../.venv/bin/python -m mypy backend/tests/integration/middleware/conftest.py

# Verify fixtures can be imported
../.venv/bin/python -c "from tests.integration.[suite].conftest import *; print('✅ Fixtures import successfully')"
```

**Common Issues the Lint-Fixer Resolves:**

1. **Missing Type Annotations**:
   ```python
   # Before (lint error)
   @pytest.fixture
   def test_client(monkeypatch):
       ...

   # After (fixed)
   @pytest.fixture
   def test_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
       ...
   ```

2. **Incorrect Async Generator Types**:
   ```python
   # Before (lint error)
   @pytest.fixture
   async def async_service() -> AsyncGenerator:
       ...

   # After (fixed)
   async def async_service() -> AsyncGenerator[ServiceType, None]:
       ...
   ```

3. **Invalid Constructor Parameters** (from hallucination):
   ```python
   # Before (lint error - parameter doesn't exist)
   service = TextProcessorService(agent="gemini", resilience=...)

   # After (fixed - correct parameters)
   service = TextProcessorService(ai_resilience=..., cache=...)
   ```

4. **Missing TYPE_CHECKING Imports**:
   ```python
   # Before (lint error)
   from app.core.config import Settings

   # After (fixed)
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from app.core.config import Settings
   ```

**Expected Warnings (Not Errors):**

Some informational warnings are expected and acceptable:
- `Missing library stubs` for internal modules - this is fine for test fixtures
- These don't block test execution

**Do NOT proceed to Prompt 6 until**:
- ✅ MyPy shows 0 errors (informational warnings OK)
- ✅ Fixtures can be imported without errors
- ✅ All type annotations are present and correct

---

## Implementation Checklist

Before marking fixture implementation complete, verify:

### App Factory Pattern
- [ ] All test clients use `create_app()` (not module-level import)
- [ ] Environment is set via `monkeypatch.setenv()` BEFORE app creation
- [ ] All fixtures use function scope for test isolation
- [ ] Settings fixtures use `create_settings()` factory

### High-Fidelity Testing
- [ ] Infrastructure dependencies use fakes (fakeredis, not mocks)
- [ ] Only external APIs/services are mocked (not internal components)
- [ ] Mocks have default behavior configured
- [ ] Failing infrastructure fixtures available for resilience tests

### Service Fixtures
- [ ] Real service implementations (not mocked)
- [ ] Proper initialization and cleanup (async where needed)
- [ ] Dependencies properly injected via fixture parameters
- [ ] Clear docstrings explaining integration scope

### Documentation
- [ ] Module-level docstring explains fixture organization
- [ ] Each fixture has comprehensive docstring with:
  - [ ] Purpose and integration scope
  - [ ] Args/Returns documentation
  - [ ] Usage examples for complex fixtures
  - [ ] References to related fixtures
- [ ] Shared fixtures are documented with references to their location
- [ ] Critical patterns documented (monkeypatch, app factory)

### Reusability
- [ ] No duplicate implementations of shared fixtures
- [ ] References to existing shared fixtures where appropriate
- [ ] New fixtures are reusable across multiple tests
- [ ] Clear distinction between suite-specific and shared fixtures

### Type Safety (Step 9)
- [ ] MyPy linting passes (0 errors, informational warnings OK)
- [ ] All fixtures have proper type annotations
- [ ] Async generators use correct type: `AsyncGenerator[Type, None]`
- [ ] TYPE_CHECKING imports added where needed
- [ ] Fixtures can be imported without errors
- [ ] No invalid constructor parameters (from hallucination)

---

## Common Fixture Patterns Reference

### Environment Variable Management

```python
#  CORRECT: Always use monkeypatch
def test_example(monkeypatch):
    monkeypatch.setenv("VAR", "value")
    # Test code

# L WRONG: Never use os.environ directly
def test_wrong():
    os.environ["VAR"] = "value"  # Causes test pollution!
```

### Async Fixture Pattern

```python
@pytest.fixture
async def async_service():
    """Async service fixture with proper lifecycle."""
    service = await create_async_service()
    yield service
    await service.cleanup()
```

### Fixture Dependency Chain

```python
@pytest.fixture
def settings(monkeypatch):
    """Base settings fixture."""
    monkeypatch.setenv("ENVIRONMENT", "testing")
    return create_settings()

@pytest.fixture
def service(settings):
    """Service depends on settings fixture."""
    return ServiceClass(settings=settings)

@pytest.fixture
def client(service):
    """Client depends on service fixture."""
    return ClientClass(service=service)
```

### Parametrized Fixtures

```python
@pytest.fixture(params=["development", "production"])
def environment_settings(request, monkeypatch):
    """Test with multiple environment configurations."""
    env = request.param
    monkeypatch.setenv("ENVIRONMENT", env)
    return create_settings()
```

---

## Output Format

After implementing fixtures, provide structured summary:

```markdown
## Fixture Implementation Summary

### Implemented Fixtures

#### App Factory Pattern Fixtures
-  **test_client** (line X-Y)
  - Purpose: HTTP client with isolated app instance
  - Dependencies: monkeypatch
  - Scope: function

-  **test_settings** (line X-Y)
  - Purpose: Real Settings with test configuration
  - Dependencies: monkeypatch
  - Scope: function

#### Service Fixtures
-  **[service_name]** (line X-Y)
  - Purpose: Real service with high-fidelity dependencies
  - Dependencies: test_settings, fakeredis_client
  - Scope: function

#### Infrastructure Fixtures
-  **fakeredis_client** (line X-Y)
  - Purpose: High-fidelity Redis fake for cache testing
  - Dependencies: None
  - Scope: function
  - Note: May reference shared fixture instead

#### Mock Fixtures
-  **mock_[external_service]** (line X-Y)
  - Purpose: Mock external service for controlled testing
  - Dependencies: None
  - Scope: function

### Reused Shared Fixtures

From `backend/tests/integration/conftest.py`:
- **fakeredis_client** (line 229-262) - Used directly
- **authenticated_headers** (line 92-97) - Used directly

### Documentation

-  Module docstring complete with usage examples
-  All fixtures have comprehensive docstrings
-  Shared fixture references documented
-  Critical patterns highlighted (monkeypatch, app factory)

### Type Safety (Step 9)

-  MyPy linting: **PASSED** (0 errors)
-  All type annotations: **COMPLETE**
-  Fixtures import successfully: **VERIFIED**

### Testing Notes

**Ready for Prompt 6 (Test Implementation)**:
- All required fixtures from test plan implemented
- Fixtures follow App Factory Pattern for isolation
- High-fidelity fakes used for infrastructure
- Type-safe and lint-free (Step 9 complete)
- Documentation complete for test implementers

**Fixture Usage Guidelines for Test Implementers**:
1. Use fixtures as-is without modification
2. Override behavior in tests via fixture parameters
3. Follow monkeypatch pattern for environment configuration
4. Reference fixture docstrings for usage examples
```

---

## Success Criteria

Fixture implementation is complete when:

1. **All Required Fixtures Implemented**: Every fixture listed in test plan is implemented or referenced
2. **App Factory Pattern Applied**: All fixtures follow isolation patterns correctly
3. **High-Fidelity Infrastructure**: Real fakes used instead of mocks where appropriate
4. **Comprehensive Documentation**: Module and fixture docstrings explain purpose and usage
5. **Type-Safe and Lint-Free** (Step 9): MyPy passes with 0 errors, all type annotations correct
6. **Ready for Test Implementation**: Test implementers can use fixtures as-is in Prompt 6
7. **No Duplication**: Shared fixtures referenced, not duplicated
8. **Proper Scoping**: Function scope for isolation, session scope only when necessary
9. **Verified Working**: All fixtures load without errors (run `pytest --collect-only`)

---

## Verification Commands

Before proceeding to Prompt 6:

```bash
cd backend

# CRITICAL: Verify type safety (Step 9)
../.venv/bin/python -m mypy backend/tests/integration/middleware/conftest.py
# Expected: 0 errors (informational warnings OK)

# Verify fixtures load correctly
../.venv/bin/python -m pytest backend/tests/integration/middleware/conftest.py --collect-only

# Check for fixture conflicts
../.venv/bin/python -m pytest backend/tests/integration/middleware --fixtures

# Verify no import errors
../.venv/bin/python -c "import sys; sys.path.insert(0, '.'); from tests.integration.middleware.conftest import *"
```

---

## Next Steps

After completing fixture implementation:

1. **CRITICAL - Fix lint errors (Step 9)**: Run MyPy and fix all type errors using lint-fixer agent
2. **Verify fixtures load**: Run all verification commands above
3. **Update test plan**: Add fixture line numbers to test plan for reference
4. **Proceed to Prompt 6**: Begin test implementation using fixtures as-is
5. **No fixture modifications**: Test implementers should NOT modify fixtures unless explicitly needed

**DO NOT skip Step 9** - Type errors will cause test implementation failures in Prompt 6.
