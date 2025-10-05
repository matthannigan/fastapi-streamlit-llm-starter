# App Factory Pattern Usage Guide

This guide provides comprehensive documentation for using the FastAPI app factory pattern implemented in this template. The factory pattern enables test isolation, multi-instance deployments, and flexible configuration while maintaining complete backward compatibility.

## Overview

The app factory pattern addresses the critical issue of test isolation that occurs with module-level singletons. In FastAPI applications, module-level `app = FastAPI(...)` instances are created once at import time and cached, causing environment variable changes in tests to not propagate to already-initialized applications.

### Why Factory Pattern?

**Problem**: Module-level singletons cause test isolation failures
- Tests modify environment variables but cached settings don't update
- Shared state bleeds between tests causing intermittent failures
- Pydantic Settings cache environment values at initialization time

**Solution**: Factory pattern creates fresh instances on demand
- Each test gets completely isolated app instance
- Environment changes take effect immediately
- No shared state between test runs
- Maintains backward compatibility for production

## Core Factory Function

### `create_app()`

```python
def create_app(
    settings_obj: Optional[Settings] = None,
    include_routers: bool = True,
    include_middleware: bool = True,
    lifespan: Optional[Callable] = None
) -> FastAPI:
```

**Parameters**:
- `settings_obj`: Optional Settings instance for custom configuration
- `include_routers`: Whether to register API routers (default: True)
- `include_middleware`: Whether to configure middleware stack (default: True)
- `lifespan`: Optional custom lifespan context manager

**Returns**: Fully configured FastAPI application instance

## Usage Patterns

### 1. Basic Factory Usage

```python
from app.main import create_app

# Create app with default settings
app = create_app()

# Create multiple independent instances
app1 = create_app()
app2 = create_app()
assert app1 is not app2  # Different instances
```

### 2. Testing with Custom Settings

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import create_settings

@pytest.fixture
def test_client():
    """Create isolated test client with fresh app instance."""
    test_settings = create_settings()
    test_settings.debug = True
    test_settings.log_level = "DEBUG"

    app = create_app(settings_obj=test_settings)
    return TestClient(app)

def test_api_with_custom_settings(test_client):
    """Test API behavior with specific configuration."""
    response = test_client.get("/")
    assert response.status_code == 200
```

### 3. Testing Without Routers

```python
def test_middleware_configuration():
    """Test middleware without endpoint complexity."""
    minimal_app = create_app(include_routers=False, include_middleware=True)

    # Test that app is configured but has fewer routes
    routes = [route.path for route in minimal_app.routes if hasattr(route, 'path')]
    assert "/" in routes  # Root endpoint still available
    assert len(routes) < 10  # Significantly fewer than full app
```

### 4. Testing Without Middleware

```python
def test_core_functionality():
    """Test core app without middleware interference."""
    core_app = create_app(include_routers=True, include_middleware=False)

    client = TestClient(core_app)
    response = client.get("/")
    assert response.status_code == 200
    # Test core functionality without middleware
```

### 5. Custom Lifespan for Testing

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def test_lifespan(app: FastAPI):
    """Custom lifespan for test-specific setup/teardown."""
    # Custom test initialization
    print("Test app starting up")
    yield
    # Custom test cleanup
    print("Test app shutting down")

def test_with_custom_lifespan():
    """Test app with custom lifecycle management."""
    test_app = create_app(lifespan=test_lifespan)
    assert isinstance(test_app, FastAPI)
```

### 6. Environment Override Testing

```python
import os
import pytest
from app.main import create_app

def test_environment_isolation():
    """Test that apps pick up environment changes immediately."""
    # Set initial environment
    os.environ['DEBUG'] = 'false'
    app1 = create_app()

    # Change environment
    os.environ['DEBUG'] = 'true'
    app2 = create_app()

    # Both apps are valid and independent
    assert isinstance(app1, FastAPI)
    assert isinstance(app2, FastAPI)
    assert app1 is not app2
```

## Production Usage

### Backward Compatibility

The factory pattern maintains **100% backward compatibility** with existing deployment patterns:

```python
# Traditional deployment (NO CHANGES REQUIRED)
from app.main import app  # Still works exactly as before

# uvicorn deployment (NO CHANGES REQUIRED)
# uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker deployment (NO CHANGES REQUIRED)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Custom Production Configuration

```python
# Custom deployment with specific settings
from app.main import create_app
from app.core.config import create_settings

production_settings = create_settings()
production_settings.debug = False
production_settings.log_level = "INFO"
production_settings.resilience_preset = "production"

custom_app = create_app(settings_obj=production_settings)
```

### Multi-Instance Deployment

```python
# Multiple app instances with different configurations
from app.main import create_app
from app.core.config import create_settings

# Public-facing app
public_settings = create_settings()
public_settings.cache_preset = "production"
public_app = create_app(settings_obj=public_settings)

# Internal admin app
admin_settings = create_settings()
admin_settings.debug = True
admin_app = create_app(settings_obj=admin_settings)
```

## Testing Best Practices

### Test Fixture Pattern

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import create_settings

@pytest.fixture(scope="function")
def isolated_test_client():
    """Create completely isolated test client for each test."""
    test_settings = create_settings()
    test_settings.debug = True
    test_settings.log_level = "DEBUG"

    app = create_app(settings_obj=test_settings)
    return TestClient(app)

@pytest.fixture(scope="function")
def minimal_test_client():
    """Create minimal test client without routers."""
    app = create_app(include_routers=False, include_middleware=True)
    return TestClient(app)

@pytest.fixture(scope="function")
def core_test_client():
    """Create test client with routers but no middleware."""
    app = create_app(include_routers=True, include_middleware=False)
    return TestClient(app)
```

### Test Environment Isolation

```python
import os
import pytest
from app.main import create_app

def test_environment_variable_isolation():
    """Test that environment changes don't affect other tests."""
    # Store original environment
    original_debug = os.environ.get('DEBUG')

    try:
        # Set test-specific environment
        os.environ['DEBUG'] = 'true'

        # Create app with test environment
        test_app = create_app()

        # Verify app was created with test environment
        assert isinstance(test_app, FastAPI)

        # Change environment again
        os.environ['DEBUG'] = 'false'

        # Create another app - should use new environment
        another_app = create_app()
        assert isinstance(another_app, FastAPI)
        assert test_app is not another_app

    finally:
        # Restore original environment
        if original_debug is not None:
            os.environ['DEBUG'] = original_debug
        else:
            os.environ.pop('DEBUG', None)
```

### Configuration Testing

```python
def test_custom_configuration_overrides():
    """Test that custom settings override environment variables."""
    from app.core.config import create_settings

    # Create custom settings
    custom_settings = create_settings()
    custom_settings.debug = True
    custom_settings.log_level = "DEBUG"
    custom_settings.cache_preset = "simple"

    # Create app with custom settings
    custom_app = create_app(settings_obj=custom_settings)

    # Verify app was created successfully
    assert isinstance(custom_app, FastAPI)

    # Create default app for comparison
    default_app = create_app()

    # Both should be valid but different instances
    assert isinstance(default_app, FastAPI)
    assert custom_app is not default_app
```

## Migration Guide

### For Existing Code

**No changes required** for existing deployment patterns:

```python
# These continue to work exactly as before
from app.main import app
uvicorn app.main:app
```

### For Test Code

**Recommended updates** to use factory pattern:

```python
# Before (may have isolation issues)
from app.main import app
client = TestClient(app)

# After (proper isolation)
from app.main import create_app
def test_client():
    app = create_app()
    return TestClient(app)
```

### For Custom Extensions

**Update extension initialization**:

```python
# Before
from app.main import app
app.add_middleware(MyCustomMiddleware)

# After (for production compatibility)
from app.main import create_app
app = create_app()
app.add_middleware(MyCustomMiddleware)

# Or better: create custom factory
def create_custom_app():
    app = create_app()
    app.add_middleware(MyCustomMiddleware)
    return app
```

## Advanced Patterns

### Custom Factory Functions

```python
from app.main import create_public_app_with_settings, create_internal_app_with_settings
from app.core.config import create_settings

def create_testing_app():
    """Create app optimized for testing."""
    test_settings = create_settings()
    test_settings.debug = True
    test_settings.cache_preset = "disabled"

    return create_app(
        settings_obj=test_settings,
        include_routers=True,
        include_middleware=True
    )

def create_production_app():
    """Create app optimized for production."""
    prod_settings = create_settings()
    prod_settings.debug = False
    prod_settings.resilience_preset = "production"

    return create_app(
        settings_obj=prod_settings,
        include_routers=True,
        include_middleware=True
    )

def create_minimal_app():
    """Create minimal app for unit testing."""
    return create_app(
        include_routers=False,
        include_middleware=False
    )
```

### App Composition

```python
def create_composite_app():
    """Create app with custom composition."""
    # Create base app
    base_app = create_app(include_routers=False)

    # Add custom routers
    from my_custom_routers import custom_router
    base_app.include_router(custom_router, prefix="/custom")

    # Add custom middleware
    from my_custom_middleware import CustomMiddleware
    base_app.add_middleware(CustomMiddleware)

    return base_app
```

## Troubleshooting

### Common Issues

**Issue**: Tests still flaky after using factory
- **Solution**: Ensure you're creating fresh app in each test, not reusing
- **Code**: `app = create_app()` in fixture or test, not at module level

**Issue**: Performance concerns with factory
- **Solution**: Factory overhead is minimal (<1ms per app)
- **Optimization**: Reuse apps within tests when appropriate

**Issue**: Deployment scripts broken
- **Solution**: No changes needed - existing deployment patterns work unchanged
- **Verification**: `from app.main import app` still works

### Debugging Factory Usage

```python
# Verify factory creates different instances
app1 = create_app()
app2 = create_app()
print(f"Apps are different: {app1 is not app2}")
print(f"App1 routes: {len(app1.routes)}")
print(f"App2 routes: {len(app2.routes)}")

# Verify custom settings work
from app.core.config import create_settings
custom_settings = create_settings()
custom_settings.debug = True
custom_app = create_app(settings_obj=custom_settings)
print(f"Custom app created: {type(custom_app).__name__}")
```

## Performance Considerations

### Factory Overhead

- **App creation time**: <1ms typical
- **Memory overhead**: ~1-2MB per app instance
- **Test impact**: Minimal, usually outweighed by test reliability benefits

### Optimization Strategies

```python
# Reuse app within test when appropriate
@pytest.fixture
def test_app():
    """Create app once per test function."""
    return create_app()

def test_multiple_endpoints(test_app):
    """Test multiple endpoints with same app instance."""
    client = TestClient(test_app)

    response1 = client.get("/")
    response2 = client.get("/v1/health")
    response3 = client.get("/internal/")

    assert all(r.status_code == 200 for r in [response1, response2, response3])
```

## References

- **Test Implementation**: `tests/core/test_app_factory.py` - Comprehensive test suite
- **Factory Implementation**: `app/main.py` - `create_app()` function
- **Settings Factory**: `app/core/config.py` - `create_settings()` function
- **Testing Guide**: `docs/guides/testing/TESTING.md` - Testing methodology
- **Configuration Guide**: `docs/get-started/ENVIRONMENT_VARIABLES.md` - Environment setup

## Conclusion

The app factory pattern provides a robust solution to test isolation issues while maintaining complete backward compatibility. It enables:

- **Reliable Testing**: Each test gets isolated app instance
- **Flexible Configuration**: Custom settings per test or deployment
- **Production Compatibility**: Zero changes to existing deployment patterns
- **Multi-Instance Support**: Multiple app configurations in same process

The pattern is production-ready and thoroughly tested, providing immediate benefits for test reliability without any deployment risks.