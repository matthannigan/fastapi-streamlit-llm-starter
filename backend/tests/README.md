# Backend Test Suite

This directory contains comprehensive tests for the FastAPI backend application, organized into clear categories for better maintainability and discoverability.

## Test Structure

The test suite follows a hierarchical structure that mirrors the application source code:

```
tests/
├── __init__.py
├── conftest.py
├── README.md (this file)
│
├── unit/                          # Unit tests (no external dependencies)
│   ├── __init__.py
│   ├── test_auth.py              # Authentication unit tests
│   ├── test_config.py            # Configuration tests
│   ├── test_dependencies.py      # Dependency injection tests
│   ├── test_dependency_injection.py
│   ├── test_models.py            # Data model tests
│   ├── test_resilience.py        # Resilience service unit tests
│   ├── test_sanitization.py      # Text sanitization tests
│   ├── test_text_processor.py    # Text processor service tests
│   │
│   ├── security/                 # Security module tests
│   │   ├── __init__.py
│   │   ├── test_context_isolation.py
│   │   └── test_response_validator.py
│   │
│   ├── services/                 # Service layer tests
│   │   ├── __init__.py
│   │   ├── test_cache.py         # Cache service tests (merged)
│   │   └── test_monitoring.py    # Monitoring service tests
│   │
│   └── utils/                    # Utility function tests
│       ├── __init__.py
│       ├── test_prompt_builder.py
│       └── test_prompt_utils.py
│
├── integration/                   # Integration tests (require running app)
│   ├── __init__.py
│   ├── test_auth_endpoints.py    # API authentication tests
│   ├── test_main_endpoints.py    # Main application endpoints
│   └── test_resilience_endpoints.py  # Resilience endpoint tests
│
├── test_manual_api.py            # Manual API tests (require live server + AI keys)
└── test_manual_auth.py           # Manual auth tests (require live server)
```

## Test Categories

### 1. Unit Tests (`unit/` directory)

Unit tests can be run without any external dependencies and test individual components in isolation.

**Run all unit tests:**
```bash
cd backend
pytest unit/ -v
```

**Run specific unit test categories:**
```bash
# Service layer tests
pytest unit/services/ -v

# Security tests
pytest unit/security/ -v

# Utility tests
pytest unit/utils/ -v

# Specific service
pytest unit/services/test_cache.py -v
```

### 2. Integration Tests (`integration/` directory)

Integration tests verify that components work together correctly. They use mocked external dependencies but test real endpoint behavior.

**Run all integration tests:**
```bash
cd backend
pytest integration/ -v
```

**Run specific integration test files:**
```bash
# Main application endpoints
pytest integration/test_main_endpoints.py -v

# Authentication endpoints
pytest integration/test_auth_endpoints.py -v

# Resilience endpoints
pytest integration/test_resilience_endpoints.py -v
```

### 3. Manual Tests (root directory)

Manual tests are designed for manual verification against a live server and require:
- A running FastAPI server at `http://localhost:8000`
- Valid AI API keys (e.g., `GEMINI_API_KEY`)
- Manual test API key: `API_KEY=test-api-key-12345`

**Manual test files:**
- `test_manual_api.py` - Manual API endpoint tests (marked with `@pytest.mark.manual`)
- `test_manual_auth.py` - Manual authentication tests (marked with `@pytest.mark.manual`)

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
pytest test_manual_api.py test_manual_auth.py -v -s -m "manual" --run-manual
```

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
# Run all unit tests only
pytest unit/ -v

# Run all integration tests only
pytest integration/ -v

# Run specific test file
pytest unit/services/test_cache.py -v

# Run specific test class
pytest unit/test_resilience.py::TestAIServiceResilience -v

# Run specific test method
pytest unit/test_resilience.py::TestAIServiceResilience::test_service_initialization -v
```

### Coverage Reports

```bash
# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term -v

# Coverage for specific modules
pytest unit/services/ --cov=app.services --cov-report=html -v
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

### Unit Tests

Place unit tests in the appropriate subdirectory under `unit/` that mirrors the application structure:

```bash
app/services/new_service.py  →  tests/unit/services/test_new_service.py
app/utils/new_utility.py     →  tests/unit/utils/test_new_utility.py
app/security/new_validator.py →  tests/unit/security/test_new_validator.py
```

### Integration Tests

Place integration tests in the `integration/` directory:
- Endpoint tests: `test_*_endpoints.py`
- Cross-component tests: `test_*_integration.py`

### Manual Tests

Add manual tests to the root test directory with `@pytest.mark.manual` decorator. These tests require the `--run-manual` flag to run.

## Common Issues and Solutions

### Connection Errors
If you see `httpx.ConnectError: All connection attempts failed`:
- Ensure the FastAPI server is running on `http://localhost:8000`
- Check that no firewall is blocking the connection
- Verify the server started successfully without errors

### Missing API Keys
If tests skip or fail due to missing API keys:
- Set the required environment variables (see manual tests section above)
- For testing without real API calls, use the unit tests instead

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
pytest unit/test_resilience.py -v -s --tb=long
```

**Stop on first failure:**
```bash
pytest unit/ -x -v
```

**Run only failed tests:**
```bash
pytest --lf -v
```

**Debug specific failing test:**
```bash
pytest unit/test_resilience.py::TestAIServiceResilience::test_service_initialization -v -s --tb=long
```