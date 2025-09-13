---
sidebar_label: Execution
---

# Running Tests

## Quick Start

The project now includes automatic virtual environment management for testing. You can run tests without manually managing Python environments.

```bash
# Create virtual environment and install dependencies
make install

# Run all tests (includes Docker integration tests if available)
make test

# Run local tests only (no Docker required)
make test-local

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run tests with coverage
make test-coverage
```

## Virtual Environment Management

The Makefile automatically handles Python executable detection and virtual environment management:

- **Automatic Python Detection**: Uses `python3` or `python` based on availability
- **Virtual Environment Creation**: Creates `.venv/` directory automatically
- **Dependency Management**: Installs all required dependencies in the virtual environment
- **Environment Awareness**: Detects if running in Docker, virtual environment, or system Python

```bash
# Create virtual environment (done automatically by make install)
make venv

# Install dependencies in virtual environment
make install

# Run tests without Docker dependency
make test-local

# Clean up virtual environment
make clean-all
```

## Detailed Commands

### Backend Tests

```bash
# Using Makefile (Recommended - handles virtual environment automatically)
make test-backend                       # Run fast tests (default)
make test-backend-all                   # Run all tests including slow ones
make test-backend-manual                # Run manual tests (requires running server)
make test-coverage                      # Run tests with coverage reporting

# Specific test categories
make test-backend-api                   # API endpoint tests
make test-backend-core                  # Core functionality tests  
make test-backend-infrastructure        # Infrastructure service tests
make test-backend-services              # Domain service tests
make test-backend-integration           # Integration tests
make test-backend-performance           # Performance tests
```

**Advanced/Debugging Commands** (when Makefile doesn't meet your needs):

<details>
<summary>Manual pytest commands with virtual environment</summary>

```bash
cd backend

# Default: Run fast tests in parallel (excludes slow and manual tests)
../.venv/bin/python -m pytest tests/ -v

# Run specific test directories
../.venv/bin/python -m pytest tests/api/ -v                        # API endpoint tests
../.venv/bin/python -m pytest tests/core/ -v                       # Core functionality tests
../.venv/bin/python -m pytest tests/infrastructure/ -v             # Infrastructure service tests
../.venv/bin/python -m pytest tests/services/ -v                   # Domain service tests
../.venv/bin/python -m pytest tests/integration/ -v                # Integration tests
../.venv/bin/python -m pytest tests/performance/ -v                # Performance tests

# Run all tests including slow ones (excluding manual)
../.venv/bin/python -m pytest tests/ -v -m "not manual" --run-slow

# Run only slow tests (requires --run-slow flag)
../.venv/bin/python -m pytest tests/ -v -m "slow" --run-slow

# Run manual tests (requires running server and --run-manual flag)
../.venv/bin/python -m pytest tests/ -v -m "manual" --run-manual

# Run with coverage
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run tests sequentially (for debugging)
../.venv/bin/python -m pytest tests/ -v -n 0

# Run specific test markers
../.venv/bin/python -m pytest tests/ -v -m "retry" --run-slow             # Retry logic tests
../.venv/bin/python -m pytest tests/ -v -m "circuit_breaker" --run-slow   # Circuit breaker tests
../.venv/bin/python -m pytest tests/ -v -m "no_parallel"                  # Tests that must run sequentially
```

</details>

### Frontend Tests

```bash
# Using Makefile (Recommended - handles virtual environment automatically)
make test-frontend

# Run with coverage
make test-frontend-coverage
```

**Manual Commands** (for debugging):
<details>
<summary>Manual pytest commands with virtual environment</summary>

```bash
cd frontend
../.venv/bin/python -m pytest tests/ -v

# Run with coverage
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=html
```

</details>

### Integration Tests

```bash
# Using Makefile (Recommended - handles Docker availability detection)
make test                               # Full test suite with Docker if available
make test-local                         # Local testing without Docker

# Using the test runner script
make run-test-script                    # Uses .venv/bin/python run_tests.py
```

**Manual Docker Testing** (for advanced scenarios):
<details>
<summary>Manual Docker Compose testing</summary>

```bash
# Start services
docker-compose up -d

# Wait for services to start
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health

# Run tests against running services
make test-manual

# Clean up
docker-compose down
```

</details>

## Test Configuration

### Pytest Configuration

The backend uses pytest with parallel execution and comprehensive markers:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -n auto                    # Parallel execution with auto-detection
    --dist worksteal          # Work-stealing load balancing
    -v                        # Verbose output
    --strict-markers          # Strict marker validation
    --tb=short               # Short traceback format
    --asyncio-mode=auto      # Automatic async support
    -m "not slow and not manual"  # Exclude slow and manual tests by default
asyncio_default_fixture_loop_scope = function
markers =
    asyncio: marks tests as async
    slow: marks tests as slow (deselect with '-m "not slow"')
    manual: marks tests as manual (deselect with '-m "not manual"')
    integration: marks tests as integration tests
    retry: marks tests that test retry logic specifically
    circuit_breaker: marks tests that test circuit breaker functionality
    no_parallel: marks tests that must run sequentially (not in parallel)
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::pytest.PytestDeprecationWarning
```

The frontend uses a simpler configuration:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --asyncio-mode=auto
markers =
    asyncio: marks tests as async
```

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with verbose output (using virtual environment)
.venv/bin/python -m pytest tests/ -v -s

# Run specific test with debugging
.venv/bin/python -m pytest tests/test_main.py::test_specific_function -v -s --pdb

# Run with coverage and keep temporary files
.venv/bin/python -m pytest tests/ --cov=app --cov-report=html --keep-durations=10

# Or use Makefile commands with additional pytest options
make test-backend PYTEST_ARGS="-v -s --pdb"
```

### Test Execution Features

#### Parallel Execution
By default, tests run in parallel using pytest-xdist:
- **Auto-detection**: `-n auto --dist worksteal` automatically determines optimal worker count
- **Environment isolation**: Tests use `monkeypatch.setenv()` for clean environments
- **Work-stealing**: Dynamic load balancing across test workers
- **Sequential tests**: Use `@pytest.mark.no_parallel` for tests that must run sequentially

#### Test Markers
- **`slow`**: Comprehensive resilience tests, timing tests, and performance scenarios
- **`manual`**: Require running FastAPI server and real API keys
- **`integration`**: Test component interactions with mocked external services
- **`retry`**: Test retry logic and exponential backoff patterns
- **`circuit_breaker`**: Test circuit breaker functionality and recovery
- **`no_parallel`**: Must run sequentially (not in parallel with other tests)

#### Special Flags
- **`--run-slow`**: Enable tests marked as `slow` (excluded by default)
- **`--run-manual`**: Enable tests marked as `manual` (excluded by default)

### Manual Test Requirements

Manual tests (`-m "manual"`) require:
- FastAPI server running on `http://localhost:8000`
- `API_KEY=test-api-key-12345` environment variable for authentication tests
- `GEMINI_API_KEY` environment variable for AI features and live API testing
- Use `--run-manual` flag to enable manual tests

**Setup for manual tests:**
```bash
# 1. Set environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"
export RESILIENCE_PRESET="development"  # or appropriate preset

# 2. Start server (from project root)
source .venv/bin/activate
cd backend/
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests (in another terminal, from project root)
source .venv/bin/activate
cd backend/
pytest -v -s -m "manual" --run-manual

# 4. Test both public and internal APIs
curl http://localhost:8000/v1/health        # Public API
curl http://localhost:8000/internal/health  # Internal API
```

### Slow Test Categories

Slow tests (`-m "slow"`) include:
- **Resilience pattern testing**: Circuit breaker recovery, retry with backoff
- **Performance benchmarks**: Cache performance, concurrent request handling
- **Integration scenarios**: End-to-end workflows with multiple service interactions
- **Timeout testing**: Testing various timeout scenarios and recovery patterns

### Common Issues

#### Configuration Issues
1. **Resilience Configuration**: Ensure `RESILIENCE_PRESET` is set (default: `simple`)
2. **API Key Issues**: Set `GEMINI_API_KEY` for AI tests (can be dummy value for unit tests)
3. **Authentication**: Use `API_KEY=test-api-key-12345` for manual authentication tests
4. **Environment Variables**: Use `monkeypatch.setenv()` in fixtures for test isolation

#### Infrastructure Issues
5. **Redis Connection**: Tests automatically fall back to memory cache if Redis unavailable
6. **Port Conflicts**: Ensure ports 8000 (backend) and 8501 (frontend) are available
7. **Docker Issues**: Use `make test-local` to run tests without Docker dependency

#### Test Execution Issues
8. **Parallel Execution**: Use `-n 0` to disable parallel execution for debugging
9. **Slow Tests**: Use `--run-slow` flag to enable comprehensive resilience testing
10. **Manual Tests**: Requires running server - use `--run-manual` flag
11. **Marker Issues**: Use `--strict-markers` to catch undefined test markers

#### Development Issues
12. **Virtual Environment**: Run `make clean-all` and `make install` to reset environment
13. **Python Version**: Makefile automatically detects `python3` or `python`
14. **Dependencies**: Run `make install` to update all dependencies
15. **Coverage Issues**: Infrastructure services require >90%, domain services >70%

## Troubleshooting

### Common Test Issues & Solutions

| Problem | Root Cause | Solution | Prevention |
|---------|------------|----------|------------|
| **Tests break during refactoring** | Too much implementation testing | Focus on behavior testing, reduce internal mocking | Use docstring-driven test development |
| **Tests take too long** | Too many integration tests | Increase unit test ratio, optimize test data | Follow test pyramid, mock external dependencies |
| **Flaky/inconsistent tests** | Too much real I/O or timing dependencies | Mock external dependencies, use deterministic test data | Mock at system boundaries only |
| **Hard to understand test failures** | Poor test names, unclear assertions | Use descriptive, behavior-focused test names | Write tests from user perspective |
| **Tests pass but bugs reach production** | Poor coverage of critical paths | Focus testing on user-facing workflows | Prioritize critical user journey coverage |
| **Developers skip running tests** | Tests are slow or unreliable | Optimize for fast feedback, fix flaky tests | Maintain <60s test execution time |

### Quick Debugging Commands

```bash
# Run only fast tests during development
pytest -m "not slow and not manual"

# Debug specific test with detailed output
pytest path/to/test.py::test_name -v -s --pdb

# Run tests without parallel execution for debugging
pytest tests/ -n 0 -v

# Update snapshots after intentional changes
pytest --snapshot-update

# Run with maximum verbosity
pytest tests/ -vv --tb=long
```

### Environment Issues

**Common Setup Problems:**

1. **API Key Issues**: Ensure `GEMINI_API_KEY` is set for AI tests (can be dummy value for unit tests)
2. **Port Conflicts**: Ensure test ports (8000, 8501) are available for manual tests
3. **Docker Issues**: Use `make test-local` to skip Docker tests if Docker unavailable
4. **Dependency Issues**: Run `make install` to update dependencies in virtual environment
5. **Python Version Issues**: Makefile automatically detects correct Python version
6. **Virtual Environment Issues**: Run `make clean-all` followed by `make install` to reset
