# FastAPI Backend Agent Guidance

This file provides guidance to coding assistants and agents when working with code in the `backend` subdirectory of this project.

General agent instructions regarding the repository overall are available at `../AGENTS.md`.

## Backend Architecture

The FastAPI backend follows a **dual-API architecture** with clear separation between Infrastructure and Domain Services:

### Core Architecture

- **Dual FastAPI Application** (`app/main.py`): 
  - **Public API** (`/v1/`): External-facing domain endpoints with authentication
  - **Internal API** (`/internal/`): Administrative infrastructure endpoints
- **Dependency Injection** (`app/dependencies.py`): Centralized service providers with preset-based configuration
- **Core Configuration** (`app/core/`): Application setup, middleware, and settings management
- **Shared Models** (`../shared/models.py` and `app/schemas/`): Cross-service Pydantic data models

### Dual API Structure

**Public API (`/v1/`)**: External business endpoints with authentication → `http://localhost:8000/docs`
- `auth.py` - Authentication validation
- `health.py` - System health checks  
- `text_processing.py` - AI text processing operations
- `deps.py` - API-specific dependencies

**Internal API (`/internal/`)**: Administrative infrastructure endpoints → `http://localhost:8000/internal/docs`
- `cache.py` - Cache management and monitoring
- `monitoring.py` - System metrics and performance
- `resilience/` - Comprehensive resilience management (circuit breakers, presets, benchmarks)

Detailed documentation: `docs/reference/key-concepts/DUAL_API_ARCHITECTURE.md`

### Key Architectural Concept: Infrastructure vs Domain Services

| Type | Infrastructure Services 🏗️ | Domain Services 💼 |
|------|---------------------------|--------------------|
| **Status** | Production-Ready - Keep & Extend | Educational Examples - Replace |
| **Purpose** | Business-agnostic technical capabilities | Business-specific implementations |
| **Coverage** | >90% test coverage required | >70% test coverage required |
| **Location** | `app/infrastructure/` | `app/services/` |
| **Examples** | Cache, Resilience, Security, Monitoring | Text processing, validation |

Detailed documentation: `docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md`

#### Infrastructure Services (`app/infrastructure/`)

**Business-agnostic, reusable technical capabilities (>90% test coverage):**

- **AI Infrastructure** (`ai/`):
  - `input_sanitizer.py` - Prompt injection protection and security
  - `prompt_builder.py` - Secure prompt construction utilities

- **Cache Infrastructure** (`cache/`):
  - `base.py` - Abstract cache interface for extensibility
  - `memory.py` - In-memory cache implementation
  - `redis.py` - Redis-based AIResponseCache with graceful degradation
  - `monitoring.py` - Performance monitoring and metrics

- **Resilience Infrastructure** (`resilience/`):
  - `circuit_breaker.py` - Circuit breaker pattern implementation
  - `retry.py` - Retry mechanisms with exponential backoff
  - `orchestrator.py` - Unified resilience pattern orchestration
  - `config_presets.py` - Simplified preset-based configuration system
  - `performance_benchmarks.py` - Performance testing and validation

- **Security Infrastructure** (`security/`):
  - `auth.py` - API key authentication with multiple key support

- **Monitoring Infrastructure** (`monitoring/`):
  - `health.py` - Health check implementations and status monitoring
  - `metrics.py` - Metrics collection and alerting

#### Domain Services (`app/services/`) **[Educational Examples]**

**Business-specific implementations serving as educational examples:**
- **TextProcessorService** (`text_processor.py`): **Example implementation** of AI text processing using PydanticAI agents with Gemini models - demonstrates how to integrate LLMs with proper error handling and validation
- **ResponseValidator** (`response_validator.py`): **Example of** business-specific response validation logic - shows patterns for validating AI responses

**💡 Template Usage Note**: These domain services are **learning examples** that demonstrate best practices. Replace them with your specific business logic while maintaining the architectural patterns and using the infrastructure services.

### Examples Directory (`app/examples/`) **[Learning Resources]**

**Infrastructure usage examples for educational purposes:**
- **Cache Examples**: Demonstrates Redis and memory cache patterns with fallback strategies
- **Resilience Examples**: Shows circuit breaker, retry, and orchestrator usage patterns
- **AI Integration Examples**: Patterns for secure LLM integration with PydanticAI
- **Monitoring Examples**: Health checks, metrics collection, and performance monitoring

## App Factory Pattern (Critical for Testing)

### Overview

The backend implements the **App Factory Pattern** to solve test isolation issues caused by module-level singletons. This pattern creates fresh FastAPI and Settings instances on demand, enabling complete test isolation while maintaining 100% backward compatibility for production deployments.

**Problem Solved**: Module-level `app = FastAPI()` and `settings = Settings()` are cached at import time, causing environment variable changes in tests to not propagate, leading to intermittent test failures.

**Solution**: Factory functions create fresh instances that immediately reflect current environment state.

### Core Factory Functions

#### 1. `create_app()` - FastAPI Application Factory

**Location**: `app/main.py`

```python
def create_app(
    settings_obj: Optional[Settings] = None,
    include_routers: bool = True,
    include_middleware: bool = True,
    lifespan: Optional[Callable] = None
) -> FastAPI:
    """Create fresh FastAPI app instance with complete configuration."""
```

**Parameters**:
- `settings_obj`: Optional Settings instance for custom configuration (defaults to `create_settings()`)
- `include_routers`: Whether to register API routers (default: True)
- `include_middleware`: Whether to configure middleware stack (default: True)
- `lifespan`: Optional custom lifespan context manager for testing

**Key Behaviors**:
- Creates completely independent FastAPI instances
- Uses provided settings or creates fresh ones from current environment
- Maintains dual-API architecture (public + internal apps)
- Enables test isolation by creating fresh app per test

#### 2. `create_settings()` - Settings Factory

**Location**: `app/core/config.py`

```python
def create_settings() -> Settings:
    """Create fresh Settings instance from current environment variables."""
```

**Key Behaviors**:
- Creates new Settings instance on each call
- Reads current environment variables (not cached values)
- Applies all Pydantic validation rules
- Enables environment override testing

#### 3. `get_settings_factory()` - FastAPI Dependency

**Location**: `app/core/config.py`

```python
def get_settings_factory() -> Settings:
    """FastAPI-compatible dependency that returns fresh Settings instances."""
```

**Use Cases**:
- FastAPI dependency injection: `Depends(get_settings_factory)`
- Request-level configuration isolation
- Testing with custom settings per request

### Test Fixture Patterns

#### Basic Test Client Pattern

```python
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.config import create_settings

@pytest.fixture(scope="function")
def test_client():
    """Create isolated test client with fresh app instance."""
    # Factory creates fresh app that picks up current environment
    app = create_app()
    return TestClient(app)

def test_endpoint(test_client):
    """Each test gets completely isolated app instance."""
    response = test_client.get("/v1/health")
    assert response.status_code == 200
```

#### Custom Settings Pattern

```python
@pytest.fixture(scope="function")
def test_client_with_custom_settings():
    """Create test client with specific configuration."""
    # Create custom settings
    test_settings = create_settings()
    test_settings.debug = True
    test_settings.log_level = "DEBUG"
    test_settings.cache_preset = "disabled"

    # Create app with custom settings
    app = create_app(settings_obj=test_settings)
    return TestClient(app)

def test_with_custom_config(test_client_with_custom_settings):
    """Test with specific configuration overrides."""
    response = test_client_with_custom_settings.get("/")
    assert response.status_code == 200
```

#### Environment Override Pattern

```python
@pytest.fixture
def production_client(monkeypatch):
    """Create client with production environment."""
    # Set production environment variables
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("API_KEY", "test-prod-key")

    # Create app AFTER environment is set
    # Factory will pick up the environment variables
    app = create_app()
    return TestClient(app)

def test_production_auth(production_client):
    """Test production authentication behavior."""
    # This client has production environment configuration
    response = production_client.get("/v1/auth/status")
    # Production requires authentication
    assert response.status_code == 401
```

#### Minimal App Pattern (Middleware/Router Isolation)

```python
@pytest.fixture
def minimal_app():
    """Create app without routers for middleware testing."""
    return create_app(include_routers=False, include_middleware=True)

@pytest.fixture
def core_app():
    """Create app without middleware for core functionality testing."""
    return create_app(include_routers=True, include_middleware=False)

def test_middleware_only(minimal_app):
    """Test middleware without endpoint complexity."""
    client = TestClient(minimal_app)
    response = client.get("/")
    assert response.status_code == 200
```

### Common Testing Scenarios

#### Scenario 1: Testing Different Environments

```python
def test_environment_isolation():
    """Test that apps pick up environment changes immediately."""
    import os

    # Set development environment
    os.environ['ENVIRONMENT'] = 'development'
    dev_app = create_app()

    # Change to production environment
    os.environ['ENVIRONMENT'] = 'production'
    os.environ['API_KEY'] = 'prod-key'
    prod_app = create_app()

    # Both apps are independent and reflect their environment
    assert dev_app is not prod_app
```

#### Scenario 2: Integration Test Fixtures

```python
# In tests/integration/conftest.py
@pytest.fixture(scope="function")
def integration_app():
    """Fresh app for integration testing."""
    return create_app()

@pytest.fixture(scope="function")
def integration_client(integration_app):
    """HTTP client for integration tests."""
    return TestClient(integration_app)

# In your integration tests
def test_full_authentication_flow(integration_client):
    """Test complete auth flow with isolated app."""
    response = integration_client.get("/v1/auth/status")
    assert response.status_code in [200, 401]
```

#### Scenario 3: Custom Lifespan Testing

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def test_lifespan(app: FastAPI):
    """Custom lifespan for test-specific setup."""
    # Custom initialization
    print("Test app starting")
    yield
    # Custom cleanup
    print("Test app shutting down")

def test_with_custom_lifespan():
    """Test with custom lifecycle management."""
    app = create_app(lifespan=test_lifespan)
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
```

### Backward Compatibility (Production Deployments)

**Zero changes required for existing deployments:**

```python
# Traditional import still works (uses factory internally)
from app.main import app

# Uvicorn deployment unchanged
# uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker deployment unchanged
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Module-level app is created via factory** (Line 1970 in `app/main.py`):
```python
app = create_app()  # Uses factory, maintains singleton behavior
```

### Migration Guide for Agents

**When writing new tests:**

```python
# ✅ RECOMMENDED: Use factory pattern
from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

# ❌ AVOID: Module-level import (may have isolation issues)
from app.main import app
client = TestClient(app)
```

**When updating existing tests:**
1. Replace `from app.main import app` with `from app.main import create_app`
2. Create app in fixture: `app = create_app()`
3. Use function scope for fixtures to ensure fresh instances
4. Set environment variables BEFORE creating app

**When testing with custom configuration:**
1. Use `create_settings()` to get fresh settings instance
2. Modify settings as needed
3. Pass to `create_app(settings_obj=custom_settings)`

### Common Pitfalls and Solutions

**Pitfall 1: Reusing app across tests**
```python
# ❌ BAD: Module-level app reused
app = create_app()

def test_one():
    client = TestClient(app)  # Shared state!

# ✅ GOOD: Fresh app per test
@pytest.fixture
def client():
    return TestClient(create_app())
```

**Pitfall 2: Setting environment after app creation**
```python
# ❌ BAD: Environment set after app created
app = create_app()
os.environ['API_KEY'] = 'test-key'  # Too late!

# ✅ GOOD: Environment set before app creation
os.environ['API_KEY'] = 'test-key'
app = create_app()  # Picks up API_KEY
```

**Pitfall 3: Using cached settings dependency**
```python
# ❌ BAD: Cached settings won't update
from app.dependencies import get_settings  # Cached!

# ✅ GOOD: Factory creates fresh settings
from app.core.config import get_settings_factory
# Use with Depends(get_settings_factory)
```

### Performance Considerations

- **App creation time**: ~5ms per instance (negligible in tests)
- **Memory overhead**: ~1-2MB per app instance
- **Test impact**: Minimal - reliability benefits far outweigh overhead
- **Optimization**: Reuse app within single test when appropriate

### Key Files and References

**Implementation Files**:
- `app/main.py` - `create_app()`, `create_public_app_with_settings()`, `create_internal_app_with_settings()`
- `app/core/config.py` - `create_settings()`, `get_settings_factory()`

**Test Examples**:
- `tests/unit/app/test_app_factory.py` - Comprehensive app factory test suite
- `tests/unit/config/test_config_factory.py` - Settings factory test suite
- `tests/integration/conftest.py` - Integration test fixture patterns
- `tests/integration/auth/conftest.py` - Auth-specific test fixtures

**Documentation**:
- `docs/guides/developer/APP_FACTORY_GUIDE.md` - **Comprehensive factory pattern guide**
- `docs/guides/testing/TESTING.md` - Testing methodology and patterns

### Quick Reference

**Create fresh app for testing:**
```python
from app.main import create_app
app = create_app()
```

**Create app with custom settings:**
```python
from app.main import create_app
from app.core.config import create_settings

settings = create_settings()
settings.debug = True
app = create_app(settings_obj=settings)
```

**Create minimal app for isolated testing:**
```python
app = create_app(include_routers=False, include_middleware=False)
```

**Test fixture pattern:**
```python
@pytest.fixture(scope="function")
def client():
    return TestClient(create_app())
```

## Additional Backend Features

### Configuration

Settings are managed through `app/core/config.py` with comprehensive Pydantic validation:
- **Dual API configuration** (public + internal endpoints)
- **AI model configuration** (Gemini API with security settings)
- **Preset-based resilience system** (simple, development, production presets)
- **Custom resilience configuration** via JSON for advanced use cases
- **Security settings** (API keys, CORS, authentication)
- **Infrastructure settings** (Redis, cache, monitoring)
- **Performance settings** (batch processing limits, concurrency controls)

### Cache Infrastructure

**Production-ready caching with Redis and memory fallback:**

- **Cache Architecture** (`app/infrastructure/cache/`):
  - `base.py` - Abstract cache interface for extensibility
  - `memory.py` - In-memory cache implementation
  - `redis.py` - Redis-based AIResponseCache with graceful degradation
  - `monitoring.py` - Performance monitoring and metrics

**Quick Start - Environment Configuration:**
```bash
# Choose one preset based on environment
CACHE_PRESET=development              # Choose: disabled, minimal, simple, development, production, ai-development, ai-production

# Optional Cache Overrides (only when needed)
CACHE_REDIS_URL=redis://localhost:6379  # Override Redis connection URL
ENABLE_AI_CACHE=true                     # Toggle AI cache features
```

**Available cache presets:**
- `disabled`: No caching
- `minimal`: Memory-only cache with basic settings
- `simple`: Memory cache with moderate TTLs
- `development`: Memory + Redis fallback, short TTLs for testing
- `production`: Redis-first with memory fallback, optimized TTLs
- `ai-development`: AI-optimized settings for development
- `ai-production`: AI-optimized settings for production

**Advanced Cache Configuration:**
```bash
# Custom Cache Configuration (JSON overrides)
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 500,
  "memory_cache_size": 2000,
  "operation_ttls": {
    "summarize": 7200,
    "sentiment": 3600
  }
}'
```

### Resilience Infrastructure

The application implements comprehensive resilience patterns:
- **Circuit Breakers**: Prevent cascade failures during AI service outages
- **Retry Strategies**: Configurable retry with exponential backoff and jitter
- **Operation-Specific Policies**: Different resilience strategies per operation type (conservative, balanced, aggressive)
- **Graceful Degradation**: Cache operates without Redis if connection fails

**Quick Start - Environment Configuration:**
```bash
# Choose one preset based on environment
RESILIENCE_PRESET=simple      # General use, testing
RESILIENCE_PRESET=development # Local dev, fast feedback  
RESILIENCE_PRESET=production  # Production workloads

# Advanced: Custom configuration
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
```

**Command Line Tools:**
```bash
# Resilience management via Makefile
make list-resil-presets           # List available presets
make show-resil-preset PRESET=production  # Show preset details
make validate-resil-config        # Validate current configuration
make recommend-resil-preset ENV=production  # Get recommendations
```

### Security & AI Safety Features

**Production-grade security measures built into the infrastructure:**
- **Prompt Injection Protection** (`app/infrastructure/ai/input_sanitizer.py`): Detects and blocks malicious prompt injection attempts
- **Input Sanitization**: Comprehensive input validation and sanitization for all AI operations
- **API Key Authentication**: Multi-key support with secure header-based authentication
- **Internal API Protection**: Administrative endpoints disabled in production environments
- **Response Validation**: AI output validation and sanitization to prevent harmful content
- **Rate Limiting**: Built-in request limiting on resilience validation endpoints
- **Security Logging**: Comprehensive audit trails for security monitoring

### Error Handling

**Global Exception Management:**
- Global exception handler in main.py
- Service-specific error handling with proper HTTP status codes
- Structured logging with request tracing
- AI response validation and sanitization

**Custom Exception Usage - CRITICAL:**
- **Always use custom exceptions** (`ConfigurationError`, `ValidationError`, `InfrastructureError`) instead of generic exceptions like `ValueError`, `HTTPException`
- **Reference**: See `docs/guides/developer/EXCEPTION_HANDLING.md` for comprehensive exception handling guidelines
- **Context required**: All custom exceptions should include contextual information for debugging
- **HTTP mapping**: Custom exceptions automatically map to appropriate HTTP status codes via `get_http_status_for_exception`

**Exception Patterns:**
- **Infrastructure**: Use structured exceptions with proper classification (`ConfigurationError` for config issues, `InfrastructureError` for service failures)
- **Domain**: Use business-specific error messages with infrastructure error handling (`ValidationError` for input validation)
- **API**: Custom exceptions automatically return appropriate HTTP status codes with structured error responses
- **Import pattern**: `from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError, get_http_status_for_exception`

**Testing Exception Handling:**
```python
# ✅ Test exception behavior per docstring
def test_service_raises_validation_error_for_invalid_input():
    \"\"\"Test that service raises ValidationError for invalid input per docstring.\"\"\"
    with pytest.raises(ValidationError) as exc_info:
        service.process_data(invalid_input)
    assert "validation" in str(exc_info.value).lower()

# ✅ Test API error response behavior
def test_api_returns_proper_status_for_validation_error(client):
    \"\"\"Test API returns 422 for ValidationError per exception mapping.\"\"\"
    response = client.post("/api/endpoint", json={"invalid": "data"})
    assert response.status_code == 422
    assert "validation" in response.json()["detail"].lower()
```



## Backend Testing

### Agent Testing Assistance - Practical Guidance

**Common Agent Issues When Running Tests:**

#### Recommended Testing Commands for Agents

**1. Use Makefile (Preferred - handles environment automatically):**
```bash
# From project root (where Makefile lives)
make test-backend                      # Fast tests only
make test-backend-all                  # All tests including slow
make test-backend-infra-cache          # Cache infrastructure tests
make test-backend-infra-ai             # AI infrastructure tests
make test-backend-infra-resilience     # Resilience infrastructure tests

# With specific pytest arguments
make test-backend PYTEST_ARGS="tests/infrastructure/cache/test_redis.py -v --tb=short"
```

**2. Direct Python Commands (when Makefile unavailable):**
```bash
# From backend/ directory:
../.venv/bin/python -m pytest tests/ -v                    # Fast tests
../.venv/bin/python -m pytest tests/ -v -m "slow" --run-slow        # Slow tests
../.venv/bin/python -m pytest tests/ -v -m "manual" --run-manual    # Manual tests
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=term    # With coverage

# From project root:
.venv/bin/python -c "import os; os.chdir('backend'); import pytest; pytest.main(['-v', 'tests/'])"
```

**3. Environment Verification Before Testing:**
```bash
# Always verify environment before running tests
pwd                                    # Confirm location
ls -la .venv/bin/python               # Check venv exists (from root)
ls -la backend/pytest.ini             # Check backend structure
make help | head -10                   # Verify Makefile available
```

### Test Organization & Structure

**Backend Test Directory Structure** (`backend/tests/`):
```
tests/
├── api/                     # API endpoint tests
│   ├── v1/                  # Public API tests (/v1/*)
│   └── internal/            # Internal API tests (/internal/*)
├── core/                    # Core functionality (config, exceptions)
├── infrastructure/          # Infrastructure service tests (>90% coverage)
│   ├── cache/               # Cache service tests
│   ├── ai/                  # AI service tests
│   ├── resilience/          # Resilience pattern tests
│   ├── security/            # Security service tests
│   └── monitoring/          # Monitoring service tests
├── services/                # Domain service tests (>70% coverage)
├── integration/             # Cross-component tests
└── manual/                  # Tests requiring live server
```

**Test Markers & Execution:**
- **Fast tests** (default): Excluded slow and manual markers
- **`slow` marker**: Comprehensive resilience tests, performance scenarios
- **`manual` marker**: Require running server and real API keys
- **`integration` marker**: Component interactions with mocked external services
- **`no_parallel` marker**: Must run sequentially

**Special Test Flags:**
- `--run-slow`: Enable slow tests
- `--run-manual`: Enable manual tests
- `--cov=app`: Coverage reporting
- `-n auto`: Parallel execution (default)

### Manual Test Setup (For Live API Testing)

**When agents need to run manual tests:**

```bash
# 1. Set environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# 2. Start server (from project root)
source .venv/bin/activate
cd backend/
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests (in another terminal, from project root)
source .venv/bin/activate
cd backend/
pytest -v -s -m "manual" --run-manual
```


### Writing New Tests - Quick Reference

**Follow docstring-driven test development:**
1. **TEST WHAT'S DOCUMENTED** - Focus on docstring contracts (Args, Returns, Raises)
2. **IGNORE IMPLEMENTATION** - Test behavior, not internal details
3. **DOCUMENT TEST PURPOSE** - Explain business impact and failure scenarios

**Detailed guidance:** `docs/guides/testing/TESTING.md`

**Agent Testing Checklist:**
- [ ] Tests run from correct directory (use `make` commands when possible)
- [ ] Virtual environment properly activated (`.venv` in project root)
- [ ] Test markers used appropriately (`slow`, `manual`, `integration`)
- [ ] Coverage maintained per architectural boundaries (Infrastructure >90%, Domain >70%)
- [ ] Exception testing follows custom exception patterns
- [ ] Parallel execution compatibility (use `monkeypatch.setenv()` for environment variables)


## See Also

**Agent Guidance Files:**
- **General Repository**: `../AGENTS.md` for cross-cutting concerns and development commands
- **Frontend Integration**: `../frontend/AGENTS.md` for frontend-backend API integration
- **Documentation Work**: `../docs/AGENTS.md` for updating backend-related documentation
- **Template Customization**: `../AGENTS.template-users.md` for helping users customize backend services

**Key Backend Documentation:**
- **Architecture Concepts**: `../docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md` - Critical architectural distinction
- **API Design**: `../docs/reference/key-concepts/DUAL_API_ARCHITECTURE.md` - Public vs Internal API patterns
- **Testing Methodology**: `../docs/guides/testing/TESTING.md` - Comprehensive testing guidance and patterns
- **Exception Handling**: `../docs/guides/developer/EXCEPTION_HANDLING.md` - Custom exception patterns and testing
- **Code Standards**: `../docs/guides/developer/CODE_STANDARDS.md` - Backend development standards and patterns

**Configuration & Setup:**
- **Environment Variables**: `../docs/get-started/ENVIRONMENT_VARIABLES.md` - Backend configuration patterns
- **Authentication Setup**: `../docs/guides/developer/AUTHENTICATION.md` - API key management and security
- **Backend Guide**: `../docs/guides/BACKEND.md` - Comprehensive backend development guide
