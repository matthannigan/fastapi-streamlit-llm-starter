# Backend Test Suite

This directory contains comprehensive tests for the FastAPI backend application, organized into clear categories for better maintainability and discoverability.

## Test Structure

The test suite follows a hierarchical structure that mirrors the application source code:

```
backend/tests/
├── conftest.py                    # Global fixtures and test configuration (405 lines)
├── fixtures.py                    # Reusable test data factories (39 lines)
├── mocks.py                       # Common mock objects (61 lines)
├── assertions.py                  # Custom test assertions (35 lines)
├── README.md                      # Test documentation and guidelines (288 lines)
│
├── infrastructure/                # Tests for reusable template components
│   ├── conftest.py                # Infrastructure-specific fixtures (15 lines)
│   │
│   ├── ai/
│   │   ├── test_client.py              # AI client interface tests (21 lines)
│   │   ├── test_gemini.py              # Gemini implementation tests (14 lines)
│   │   ├── test_prompt_builder.py      # Prompt construction tests (415 lines)
│   │   ├── test_sanitization.py        # Input sanitization tests (307 lines)
│   │   └── test_response_validator.py  # Response validation tests (301 lines)
│   │
│   ├── cache/
│   │   ├── test_base.py          # Cache interface tests (14 lines)
│   │   ├── test_redis.py         # Redis cache implementation (14 lines)
│   │   ├── test_memory.py        # In-memory cache tests (14 lines)
│   │   ├── test_cache.py         # Comprehensive cache tests (3673 lines)
│   │   └── test_monitoring.py    # Cache monitoring tests (2337 lines)
│   │
│   ├── resilience/
│   │   ├── test_resilience.py              # Core resilience functionality (1753 lines)
│   │   ├── test_circuit_breaker.py         # Circuit breaker pattern tests (14 lines)
│   │   ├── test_retry.py                   # Retry mechanism tests (14 lines)
│   │   ├── test_presets.py                 # Resilience preset configuration tests (408 lines)
│   │   ├── test_resilience_integration.py  # Resilience integration tests (230 lines)
│   │   ├── test_validation_schemas.py      # Schema validation tests (361 lines)
│   │   ├── test_backward_compatibility.py  # Backward compatibility tests (743 lines)
│   │   ├── test_env_recommendations.py     # Environment-specific tests (340 lines)
│   │   ├── test_adv_config_scenarios.py    # Complex config tests (675 lines)
│   │   ├── test_security_validation.py     # Security validation tests (473 lines)
│   │   └── test_migration_utils.py         # Migration utility tests (478 lines)
│   │
│   ├── security/
│   │   └── test_auth.py          # Authentication and authorization tests (362 lines)
│   │
│   └── monitoring/
│       ├── test_metrics.py       # Metrics collection tests (14 lines)
│       ├── test_health.py        # Health check tests (14 lines)
│       └── test_performance_benchmarks.py # Performance monitoring tests (508 lines)
│
├── core/                         # Tests for application-specific setup
│   ├── test_config.py                # Configuration loading and validation (224 lines)
│   ├── test_config_monitoring.py     # Configuration monitoring tests (602 lines)
│   ├── test_exceptions.py            # Custom exception handling (14 lines)
│   ├── test_middleware.py            # CORS, error handling, logging (19 lines)
│   ├── test_dependencies.py          # Dependency injection (426 lines)
│   └── test_dependency_injection.py  # Advanced dependency injection tests (82 lines)
│
├── services/                     # Tests for domain/business logic
│   └── test_text_processing.py   # Text processing service tests (1163 lines)
│
├── api/                          # API endpoint tests
│   ├── conftest.py               # API-specific fixtures (auth, clients) (19 lines)
│   │
│   ├── v1/                       # Versioned public API tests
│   │   ├── test_text_processing.py  # /v1/text_processing/process, /v1/text_processing/batch_process (703 lines)
│   │   └── test_health.py           # /v1/health, /v1/auth/status (20 lines)
│   │
│   └── internal/                       # Internal/admin API tests
│       ├── test_monitoring.py              # /monitoring/* endpoints (550 lines)
│       ├── test_admin.py                   # /admin/* endpoints (14 lines)
│       ├── test_resilience_validation.py   # Resilience validation endpoints (575 lines)
│       └── test_resilience_performance.py  # Resilience performance tests (333 lines)
│
├── shared_schemas/           # Schema validation tests
│   ├── test_text_processing.py   # Request/response model tests (164 lines)
│   ├── test_monitoring.py        # Monitoring model tests (15 lines)
│   └── test_common.py            # Shared models and enums (61 lines)
│
├── integration/                     # Cross-layer integration tests
│   ├── conftest.py                      # Integration-specific fixtures (19 lines)
│   ├── test_end_to_end.py               # Full request flow tests (638 lines)
│   ├── test_auth_endpoints.py           # Authentication integration (321 lines)
│   ├── test_resilience_integration1.py  # Resilience + API integration part 1 (408 lines)
│   ├── test_resilience_integration2.py  # Resilience + API integration part 2 (554 lines)
│   ├── test_cache_integration.py        # Cache + service integration (14 lines)
│   └── test_request_isolation.py        # Request isolation and context tests (627 lines)
│
├── performance/               # Performance and load tests
│   └── test_cache_performance.py  # Cache performance tests (14 lines)
│
├── manual/                    # Manual testing scripts
│   ├── test_manual_api.py         # Manual API tests (require live server + AI keys) (158 lines)
│   └── test_manual_auth.py        # Manual auth tests (require live server) (167 lines)
│
└── templates/                 # Code review templates for tests
    ├── code-review_api.md
    ├── code-review_core.md 
    ├── code-review_infrastructure.md
    ├── code-review_integration.md
    ├── code-review_performance.md
    ├── code-review_services.md
    └── code-review_shared-schemas.md
```

## Test Categories

### 1. Infrastructure Tests (`infrastructure/` directory) 🏗️

Tests for reusable template components that are business-agnostic and stable across projects. These test individual infrastructure services in isolation with mocked external dependencies.

**Characteristics:**
- High test coverage requirements (>90%)
- Business-agnostic abstractions
- Stable APIs with backward compatibility guarantees
- Performance-critical implementations

**Run all infrastructure tests:**
```bash
cd backend
pytest infrastructure/ -v
```

**Run specific infrastructure categories:**
```bash
# AI infrastructure (clients, prompt builders, validators)
pytest infrastructure/ai/ -v

# Cache infrastructure (Redis, memory, monitoring)
pytest infrastructure/cache/ -v

# Resilience infrastructure (circuit breakers, retries, presets)
pytest infrastructure/resilience/ -v

# Security infrastructure (auth, validation)
pytest infrastructure/security/ -v

# Monitoring infrastructure (metrics, health, benchmarks)
pytest infrastructure/monitoring/ -v
```

### 2. Core Tests (`core/` directory) ⚙️

Tests for application-specific setup and configuration that bridges infrastructure and domain concerns.

**Run core tests:**
```bash
cd backend
pytest core/ -v
```

**Core test categories:**
```bash
# Configuration management
pytest core/test_config.py -v

# Dependency injection
pytest core/test_dependencies.py -v

# Exception handling
pytest core/test_exceptions.py -v
```

### 3. Domain Service Tests (`services/` directory) 💼

Tests for business-specific implementations that compose infrastructure services. These are expected to be replaced/modified per project.

**Run service tests:**
```bash
cd backend
pytest services/ -v
```

### 4. API Tests (`api/` directory) 🌐

Tests for HTTP endpoints using FastAPI TestClient, organized by API visibility and versioning.

**Run all API tests:**
```bash
cd backend
pytest api/ -v
```

**API test categories:**
```bash
# Public versioned API endpoints
pytest api/v1/ -v

# Internal/admin API endpoints
pytest api/internal/ -v
```

### 5. Schema Tests (`shared_schemas/` directory) 📋

Tests for Pydantic model validation, request/response schemas, and data structures.

**Run schema tests:**
```bash
cd backend
pytest shared_schemas/ -v
```

### 6. Integration Tests (`integration/` directory) 🔗

Cross-layer integration tests that verify components work together correctly. These test interactions between multiple services and layers.

**Characteristics:**
- Test multiple services together
- May use real external dependencies (Redis, databases)
- Focus on service boundary interactions
- End-to-end request flows

**Run all integration tests:**
```bash
cd backend
pytest integration/ -v
```

**Integration test categories:**
```bash
# Full request flow tests
pytest integration/test_end_to_end.py -v

# Authentication integration
pytest integration/test_auth_endpoints.py -v

# Resilience integration
pytest integration/test_resilience_integration*.py -v

# Cache integration
pytest integration/test_cache_integration.py -v

# Request isolation and context
pytest integration/test_request_isolation.py -v
```

### 7. Performance Tests (`performance/` directory) 🚀

Actual performance and load testing that measures system characteristics rather than testing functionality.

**Run performance tests:**
```bash
cd backend
pytest performance/ -v
```

### 8. Manual Tests (`manual/` directory) 🔧

Manual tests designed for verification against a live server. These require external setup and are marked for manual execution.

**Requirements:**
- Running FastAPI server at `http://localhost:8000`
- Valid AI API keys (e.g., `GEMINI_API_KEY`)
- Manual test API key: `API_KEY=test-api-key-12345`

**To run manual tests:**
```bash
# 1. Set up environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# 2. Start the FastAPI server
cd backend
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests in another terminal
cd backend
pytest manual/ -v -s -m "manual" --run-manual
```

## Code Review Process 📋

The `templates/` directory contains systematic code review templates for each test category. These templates help ensure tests meet their specific criteria and are properly located within the test directory structure.

### Available Review Templates

Each template is designed for a specific test category:

- **`code-review_infrastructure.md`** - For reviewing infrastructure tests (`infrastructure/` directory)
- **`code-review_core.md`** - For reviewing core application tests (`core/` directory)
- **`code-review_services.md`** - For reviewing domain service tests (`services/` directory)
- **`code-review_api.md`** - For reviewing API endpoint tests (`api/` directory)
- **`code-review_shared-schemas.md`** - For reviewing schema validation tests (`shared_schemas/` directory)
- **`code-review_integration.md`** - For reviewing integration tests (`integration/` directory)
- **`code-review_performance.md`** - For reviewing performance tests (`performance/` directory)

### When to Initiate Code Reviews

**Recommended Review Triggers:**

1. **After major refactoring** - When test structure or organization changes significantly
2. **Before releases** - To ensure test quality and proper categorization
3. **When adding new test categories** - To verify tests are placed correctly
4. **During onboarding** - To help new team members understand test organization
5. **When test failures increase** - To identify structural issues or misplaced tests
6. **Quarterly maintenance** - Regular review to maintain test quality standards

### How to Conduct a Code Review

**Step 1: Choose the appropriate template**
```bash
# Copy the relevant template for your review area
cp backend/tests/templates/code-review_infrastructure.md backend/tests/infrastructure/review_2024-01-15.md
```

**Step 2: Gather file information**
```bash
# Get file list and sizes for the review area
cd backend/tests/infrastructure
ls -la
wc -l *.py */*.py
```

**Step 3: Follow the template process**
- List all files to be reviewed with checkboxes
- Review each file systematically against the criteria
- Document findings and classifications
- Identify misplaced tests and add TODO comments
- Provide comprehensive recommendations

**Step 4: Take action on findings**
```bash
# Move misplaced tests to correct directories
mv tests/infrastructure/test_integration_feature.py tests/integration/test_feature_integration.py

# Add TODO comments to files that need relocation
# (Done during the review process)
```

### Review Criteria by Category

**Infrastructure Tests** 🏗️
- Business-agnostic abstractions
- Isolated testing with mocked dependencies
- High test coverage (>90%)
- Stable API contract testing
- Performance-critical implementations

**Core Tests** ⚙️
- Application-specific setup and configuration
- Infrastructure-domain bridge functionality
- Dependency injection and wiring
- Middleware and cross-cutting concerns
- Configuration validation

**Services Tests** 💼
- Business logic and domain rules
- Service composition and orchestration
- Input validation and processing
- Error handling and edge cases
- Infrastructure integration

**API Tests** 🌐
- HTTP endpoint testing
- Request/response validation
- Authentication and authorization
- Error handling and status codes
- API contract compliance

**Schema Tests** 📋
- Pydantic model validation
- Request/response schema testing
- Data structure integrity
- Validation edge cases
- Schema evolution support

**Integration Tests** 🔗
- Cross-layer integration
- Service boundary interactions
- End-to-end workflows
- Realistic dependency usage
- System interaction patterns

**Performance Tests** 🚀
- System characteristic measurement
- Quantitative metrics collection
- Load and stress testing
- Performance regression detection
- Resource utilization monitoring

### Review Output and Documentation

Each review should produce:
- **Review report** - Detailed findings and recommendations
- **Action items** - Specific tasks to address issues
- **TODO comments** - Added to misplaced files with relocation guidance
- **Progress tracking** - Metrics on review completion and issue resolution

### Example Review Commands

```bash
# Start an infrastructure review
cp backend/tests/templates/code-review_infrastructure.md backend/tests/infrastructure/infrastructure_review.md

# Start an API review  
cp backend/tests/templates/code-review_api.md backend/tests/api/api_review.md

# Start an integration review
cp backend/tests/templates/code-review_integration.md backend/tests/integration/integration_review.md
```

The review templates provide systematic approaches to ensure test quality, proper organization, and adherence to category-specific criteria.

## Running Tests

### Default Test Execution

By default, tests run in parallel for faster feedback using pytest-xdist:

```bash
cd backend
pytest -v  # Runs fast tests in parallel, excluding slow and manual tests
```

### Comprehensive Test Options

```bash
# Run all tests including slow ones (excluding manual)
pytest -v -m "not manual" --run-slow

# Run all tests including manual ones (requires live server)
pytest -v -m "not slow" --run-manual

# Run only slow tests (requires --run-slow flag)
pytest -v -m "slow" --run-slow

# Run only manual tests (requires --run-manual flag)
pytest -v -m "manual" --run-manual

# Run both slow and manual tests together
pytest -v -m "slow or manual" --run-slow --run-manual

# Run tests sequentially (for debugging)
pytest -v -n 0
```

### Test-Specific Commands

```bash
# Run all infrastructure tests only
pytest infrastructure/ -v

# Run all integration tests only
pytest integration/ -v

# Run specific test file
pytest infrastructure/cache/test_cache.py -v

# Run specific test class
pytest infrastructure/resilience/test_resilience.py::TestAIServiceResilience -v

# Run specific test method
pytest infrastructure/resilience/test_resilience.py::TestAIServiceResilience::test_service_initialization -v

# Run by test category
pytest core/ api/ services/ -v  # Application-specific tests
pytest infrastructure/ -v       # Template component tests
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term -v

# Coverage for specific modules
pytest infrastructure/cache/ --cov=app.infrastructure.cache --cov-report=html -v
pytest services/ --cov=app.services --cov-report=html -v
pytest api/ --cov=app.routers --cov-report=html -v
```

## Test Markers

The test suite uses several pytest markers to categorize tests:

- `slow` - Marks tests that take longer to run (excluded by default, requires `--run-slow`)
- `manual` - Marks tests requiring manual server setup (excluded by default, requires `--run-manual`)  
- `integration` - Marks integration tests
- `retry` - Marks tests that specifically test retry logic
- `circuit_breaker` - Marks tests for circuit breaker functionality
- `no_parallel` - Marks tests that must run sequentially

### Special Test Flags

- `--run-slow` - Enables slow tests that involve actual timing, retries, and performance testing
- `--run-manual` - Enables manual tests that require a live server and real API keys

## Adding New Tests

### Infrastructure Tests 🏗️

Place infrastructure tests for reusable template components:

```bash
app/infrastructure/cache/new_cache.py     →  tests/infrastructure/cache/test_new_cache.py
app/infrastructure/ai/new_client.py       →  tests/infrastructure/ai/test_new_client.py
app/infrastructure/security/new_auth.py   →  tests/infrastructure/security/test_new_auth.py
```

**Requirements:**
- >90% test coverage
- Mock external dependencies
- Test API contracts and error handling

### Core Tests ⚙️

Place core application setup tests:

```bash
app/core/new_config.py        →  tests/core/test_new_config.py
app/core/new_middleware.py    →  tests/core/test_new_middleware.py
```

### Domain Service Tests 💼

Place domain/business logic tests:

```bash
app/services/new_domain_service.py  →  tests/services/test_new_domain_service.py
```

**Note:** These are meant to be replaced in actual projects.

### API Tests 🌐

Place endpoint tests organized by API type:

```bash
# Public API endpoints
app/routers/v1/new_endpoint.py    →  tests/api/v1/test_new_endpoint.py

# Internal/admin endpoints  
app/routers/internal/new_admin.py →  tests/api/internal/test_new_admin.py
```

### Schema Tests 📋

Place Pydantic model tests:

```bash
shared/models/new_model.py  →  tests/shared_schemas/test_new_model.py
```

### Integration Tests 🔗

Place cross-layer integration tests in `integration/`:
- Full workflow tests: `test_*_end_to_end.py`
- Service interaction tests: `test_*_integration.py`
- Authentication flows: `test_*_auth.py`

### Manual Tests 🔧

Add manual tests to `manual/` directory with `@pytest.mark.manual` decorator. These tests require the `--run-manual` flag to run.

## Common Issues and Solutions

### Connection Errors
If you see `httpx.ConnectError: All connection attempts failed`:
- Ensure the FastAPI server is running on `http://localhost:8000`
- Check that no firewall is blocking the connection
- Verify the server started successfully without errors

### Missing API Keys
If tests skip or fail due to missing API keys:
- Set the required environment variables (see manual tests section above)
- For testing without real API calls, use the infrastructure tests instead (they mock external dependencies)

### Parallel Testing Issues
If tests fail when run in parallel but pass when run sequentially:
- Use `monkeypatch.setenv()` for environment variable isolation
- Mark tests with `@pytest.mark.no_parallel` if they must run sequentially
- Ensure tests don't share mutable state

### Import Errors
If you see import errors after the restructure:
- Check that all `__init__.py` files are present
- Verify test imports use correct relative paths
- Make sure the backend directory is your working directory when running tests

## Test Configuration

Tests use the configuration from `pytest.ini` in the backend directory. Key settings:
- Parallel execution by default (`-n auto --dist worksteal`)
- Async test support via `pytest-asyncio`
- Coverage reporting
- Custom markers for different test types
- Automatic exclusion of slow and manual tests (unless `--run-slow` or `--run-manual` flags are used)

### Test Exclusion Logic

By default, the test configuration excludes:
- **Slow tests**: Filtered by pytest.ini marker expression AND skipped by conftest.py unless `--run-slow` is provided
- **Manual tests**: Filtered by pytest.ini marker expression AND skipped by conftest.py unless `--run-manual` is provided

This dual protection ensures that special test categories only run when explicitly requested.

## Debugging Tests

**Run with detailed output:**
```bash
pytest infrastructure/resilience/test_resilience.py -v -s --tb=long
```

**Stop on first failure:**
```bash
pytest infrastructure/ -x -v
```

**Run only failed tests:**
```bash
pytest --lf -v
```

**Debug specific failing test:**
```bash
pytest infrastructure/resilience/test_resilience.py::TestAIServiceResilience::test_service_initialization -v -s --tb=long
```