# App Factory Pattern for FastAPI - PRD

## Overview

**Problem**: The current FastAPI application uses module-level singleton initialization, causing test isolation issues where shared state bleeds between tests. This manifests as intermittent integration test failures when tests run in random order.

**Solution**: Refactor to an app factory pattern that creates fresh FastAPI instances on demand, ensuring complete state isolation between tests while maintaining backward compatibility for production use.

**Value**: Eliminates flaky tests, improves developer experience, and establishes a more maintainable architecture that aligns with FastAPI best practices.

## Core Features

### 1. Factory Function for App Creation

**What it does**: Provides a `create_app()` function that returns a fresh FastAPI instance with all dependencies properly initialized.

**Why it's important**: Allows tests to create isolated app instances with test-specific configurations while maintaining the current production deployment model.

**How it works**:
- Moves all app initialization logic from module-level to function scope
- Takes optional configuration parameters for testing scenarios
- Returns a fully configured FastAPI instance

### 2. Backward Compatibility Layer

**What it does**: Maintains the existing `app` module-level instance for production deployments and existing code.

**Why it's important**: Ensures zero breaking changes for production deployments, Docker containers, and any code that imports `from app.main import app`.

**How it works**:
- Creates default module-level `app = create_app()` for production use
- Existing deployment configurations continue to work without modification
- ASGI servers (Uvicorn) can still reference `app.main:app`

### 3. Test Client Fixture Enhancement

**What it does**: Updates the `test_client` fixture to use `create_app()` for fresh instances per test.

**Why it's important**: Provides automatic test isolation without requiring test authors to understand the implementation details.

**How it works**:
- Calls `create_app()` in the fixture
- Each test receives a completely fresh FastAPI instance
- Environment variables set in test fixtures properly initialize the new app

### 4. Settings Reinitialization Support

**What it does**: Ensures Pydantic Settings objects are created fresh for each app instance.

**Why it's important**: Pydantic Settings cache environment variables at initialization; stale caches cause auth and environment detection failures.

**How it works**:
- Factory function creates new Settings() instance per call
- Avoids module-level Settings singleton
- Tests can manipulate environment variables and see effects immediately

## User Experience

### User Personas

**Persona 1: Test Author**
- Needs: Reliable, isolated tests that pass consistently
- Pain points: Intermittent failures due to test ordering, difficulty debugging state contamination
- Experience improvement: Write tests naturally without worrying about execution order or cleanup

**Persona 2: Template User/Developer**
- Needs: Clear examples of proper FastAPI architecture
- Pain points: Confusion about singleton vs. factory patterns
- Experience improvement: Learning from well-architected template code

**Persona 3: DevOps/Deployment Engineer**
- Needs: Stable deployment process without breaking changes
- Pain points: Configuration changes that break existing deployments
- Experience improvement: No changes required to existing deployment configs

### Key User Flows

**Flow 1: Running Integration Tests**
```python
# Before (flaky)
def test_auth(test_client):  # Sometimes fails due to cached state
    response = test_client.get("/v1/health")
    assert response.status_code == 200

# After (reliable)
def test_auth(test_client):  # Always passes, fresh app instance
    response = test_client.get("/v1/health")
    assert response.status_code == 200
```

**Flow 2: Production Deployment**
```bash
# Before
uvicorn app.main:app --host 0.0.0.0 --port 8000

# After (no change required)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Flow 3: Custom Test Scenarios**
```python
# New capability: Creating app with custom config
def test_with_custom_config():
    from app.main import create_app
    app = create_app(settings_override={"ENVIRONMENT": "test"})
    # Test with specific configuration
```

## Technical Architecture

### System Components

**1. App Factory Module** (`app/main.py`)
```python
def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Factory function to create a fresh FastAPI app instance.

    Args:
        settings: Optional Settings override for testing

    Returns:
        Fully configured FastAPI application
    """
    # Initialize settings
    # Create FastAPI instance
    # Register routers
    # Configure middleware
    # Setup lifespan events
    return app

# Backward compatibility
app = create_app()
```

**2. Settings Factory** (`app/core/config.py`)
```python
def create_settings() -> Settings:
    """Create a fresh Settings instance from current environment."""
    return Settings()

def get_settings() -> Settings:
    """Dependency injection for settings in route handlers."""
    return create_settings()
```

**3. Test Infrastructure** (`tests/integration/conftest.py`)
```python
@pytest.fixture(scope="function")
def test_client():
    """Create test client with fresh app instance."""
    from app.main import create_app
    app = create_app()
    with TestClient(app) as client:
        yield client
```

### Data Models

No new data models required. Existing Pydantic models remain unchanged.

### APIs and Integrations

**External Impact**: None - all APIs remain unchanged
- Existing endpoints: No modifications
- Authentication flows: No changes to behavior
- Client integrations: Fully backward compatible

**Internal Changes**:
- Dependency injection patterns updated to use factory functions
- Test fixtures leverage factory pattern
- Startup/shutdown lifecycle managed within factory

### Infrastructure Requirements

**Development**: No new dependencies required
**Testing**: Existing pytest infrastructure sufficient
**Production**: No infrastructure changes needed

## Development Roadmap

### Phase 1: Foundation - Settings Factory

**Scope**: Refactor Settings initialization to support fresh instances

**Deliverables**:
- `create_settings()` factory function
- Update `get_settings()` dependency to use factory
- Ensure all route handlers use dependency injection
- Verify no module-level Settings caching

**Success Criteria**:
- Tests can modify environment variables and see immediate effect
- Settings initialized fresh per request in tests
- Production behavior unchanged

### Phase 2: App Factory Core

**Scope**: Create the main `create_app()` factory function

**Deliverables**:
- `create_app()` function with all initialization logic
- Move router registration into factory
- Move middleware configuration into factory
- Move lifespan events into factory
- Create backward-compatible `app = create_app()` at module level

**Success Criteria**:
- Production deployment works without changes
- `uvicorn app.main:app` continues to function
- Multiple `create_app()` calls produce independent instances

### Phase 3: Test Infrastructure Update

**Scope**: Update test fixtures to use factory pattern

**Deliverables**:
- Update `test_client` fixture to call `create_app()`
- Remove module reload workarounds from conftest.py
- Add documentation for test authors
- Update integration test examples

**Success Criteria**:
- All integration tests pass consistently (10+ consecutive runs)
- No module reloading required in fixtures
- Test execution time remains similar or improves

### Phase 4: Documentation and Examples

**Scope**: Document the pattern and provide usage examples

**Deliverables**:
- Update `backend/AGENTS.md` with factory pattern guidance
- Add examples to testing documentation
- Document settings override patterns for tests
- Create migration guide for template users

**Success Criteria**:
- Clear examples of using factory in tests
- Documentation explains why and when to use pattern
- Template users understand how to customize

### Phase 5: Validation and Cleanup

**Scope**: Verify stability and remove deprecated code

**Deliverables**:
- Run extended test suite (100+ runs) to verify stability
- Remove any remaining module reload code
- Clean up deprecated patterns
- Add regression tests for test isolation

**Success Criteria**:
- Zero intermittent test failures over 100 runs
- No module reload code in test infrastructure
- CI/CD passes consistently

## Logical Dependency Chain

**Foundational (Must Build First)**:
1. Settings Factory (Phase 1)
   - Required before app factory because Settings must be reinitializable
   - Smallest atomic change that can be tested independently
   - Validates that environment variable changes propagate correctly

2. App Factory Core (Phase 2)
   - Depends on Settings factory being complete
   - Establishes the pattern for all other factories
   - Must maintain backward compatibility as a hard requirement

**Incremental Improvement (Build Upon Foundation)**:
3. Test Infrastructure Update (Phase 3)
   - Depends on app factory being available
   - Immediate visible benefit (stable tests)
   - Proves the factory pattern solves the problem

4. Documentation (Phase 4)
   - Should happen after implementation is proven
   - Captures lessons learned during implementation
   - Provides examples based on real working code

**Validation (Final Polish)**:
5. Extended Testing & Cleanup (Phase 5)
   - Validates that all previous phases work together
   - Removes technical debt from workarounds
   - Ensures production-ready quality

**Rationale for Ordering**:
- Settings first because it's the smallest isolated change
- App factory second because it's the core architectural change
- Tests third because they provide immediate validation
- Docs fourth because they should reflect working implementation
- Cleanup last because we need stable foundation first

## Risks and Mitigations

### Technical Challenges

**Risk 1: Circular Dependencies**
- **Description**: App initialization may have circular imports with dependencies
- **Likelihood**: Medium
- **Impact**: High - could block factory implementation
- **Mitigation**:
  - Audit current import graph before starting
  - Use lazy imports within factory function if needed
  - Consider dependency injection for circular references

**Risk 2: Stateful Singletons**
- **Description**: Some infrastructure services may assume singleton pattern
- **Likelihood**: Medium
- **Impact**: Medium - may require refactoring service initialization
- **Mitigation**:
  - Audit all infrastructure services for stateful initialization
  - Create factory methods for services that cache state
  - Document which services are safe to reinitialize

**Risk 3: Performance Impact**
- **Description**: Creating fresh app instances per test may slow test suite
- **Likelihood**: Low
- **Impact**: Low - tests already do module reloading
- **Mitigation**:
  - Benchmark current test execution time
  - Compare before/after performance
  - Optimize factory if needed (lazy initialization, caching)

### MVP Definition

**Minimum Viable Product**: Phases 1-3 must be complete
- Settings factory working
- App factory functional
- Test fixture using factory
- All integration tests passing consistently

**Nice to Have (Can Defer)**:
- Settings override parameters for custom test scenarios
- Comprehensive documentation (basic docs sufficient for MVP)
- Extended validation testing (initial 10-run validation sufficient)

**Out of Scope for MVP**:
- Frontend application factory (separate effort)
- Unit test updates (focus on integration tests where issue manifests)
- Performance optimizations beyond baseline

### Resource Constraints

**Development Time**:
- Phase 1: 2-4 hours
- Phase 2: 4-6 hours
- Phase 3: 2-3 hours
- Total MVP: 8-13 hours

**Testing Requirements**:
- Must run integration tests 10+ times per phase
- CI/CD must pass before merging each phase
- Manual verification of production deployment scenario

**Knowledge Requirements**:
- Understanding of FastAPI app lifecycle
- Familiarity with pytest fixture scope and execution order
- Knowledge of Pydantic Settings caching behavior

## Success Metrics

**Primary Metric**: Integration test stability
- **Target**: 100% pass rate over 100 consecutive runs
- **Current**: ~80% pass rate (intermittent failures)
- **Measurement**: `for i in {1..100}; do pytest tests/integration/ || break; done`

**Secondary Metrics**:
- Test execution time: No more than 10% increase
- Code complexity: Reduced (remove module reload workarounds)
- Developer experience: Qualitative improvement (no more flaky test debugging)

## Appendix

### Research Findings

**FastAPI Recommendations**:
- Official FastAPI docs recommend factory pattern for testing
- Tiangolo (FastAPI author) uses factories in example projects
- Pattern is standard in Flask, Django, and other Python web frameworks

**Current Workarounds**:
```python
# Current fixture attempts module reload
if 'app.core.config' in sys.modules:
    importlib.reload(sys.modules['app.core.config'])
```
This is unreliable because:
- Pydantic Settings cache values at class definition time
- importlib.reload() doesn't reinitialize cached objects
- Incomplete - misses other modules with cached state

**Root Cause Confirmed**:
- Module-level `app = FastAPI(...)` created once at import
- Module-level `settings = Settings()` caches environment variables
- Tests change environment but can't invalidate these caches

### Technical Specifications

**Factory Function Signature**:
```python
def create_app(
    settings: Optional[Settings] = None,
    include_routers: bool = True,
    include_middleware: bool = True,
    lifespan: Optional[Callable] = None
) -> FastAPI:
    """
    Create a fresh FastAPI application instance.

    Args:
        settings: Optional Settings instance for testing. If None, creates from environment.
        include_routers: Whether to register API routers (default: True)
        include_middleware: Whether to configure middleware (default: True)
        lifespan: Optional custom lifespan context manager

    Returns:
        Fully configured FastAPI instance
    """
```

**Backward Compatibility**:
```python
# app/main.py
app = create_app()  # Default instance for production

# All existing code continues to work:
from app.main import app  # Gets default instance

# Tests can create fresh instances:
from app.main import create_app
test_app = create_app()  # Fresh instance
```

### Example Implementation

**Before** (Current):
```python
# app/main.py
from app.core.config import settings  # Module-level singleton

app = FastAPI(title=settings.PROJECT_NAME)  # Created once at import

# Register routers at module level
app.include_router(v1_router, prefix="/v1")
app.include_router(internal_router, prefix="/internal")
```

**After** (Factory Pattern):
```python
# app/main.py
def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """Create a fresh FastAPI instance."""
    # Initialize settings
    app_settings = settings or create_settings()

    # Create app
    app = FastAPI(title=app_settings.PROJECT_NAME)

    # Register routers
    app.include_router(v1_router, prefix="/v1")
    app.include_router(internal_router, prefix="/internal")

    # Configure middleware
    setup_middleware(app, app_settings)

    # Setup lifespan
    @app.on_event("startup")
    async def startup():
        await initialize_services(app_settings)

    return app

# Backward compatibility
app = create_app()
```

### Related Issues

- Intermittent integration test failures documented in test runs
- pytest-random-order exposing test isolation issues
- Authentication state bleeding between tests
- Environment detection inconsistencies in tests

### Future Enhancements (Out of Scope)

- Configuration-driven app creation (YAML/JSON config files)
- Multiple app variants (minimal, full-featured, debug mode)
- Plugin system for dynamic router/middleware registration
- Performance profiling and optimization of factory function
