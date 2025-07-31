# Testing Guide

This document provides comprehensive information about the test suite for the FastAPI-Streamlit-LLM starter template.

## Overview

The test suite covers both backend and frontend components with the following types of tests:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions and API endpoints
- **End-to-End Tests**: Test complete user workflows
- **Code Quality**: Linting, type checking, and formatting validation

## Test Structure

The testing architecture follows the infrastructure vs domain service separation:

```
├── backend/
│   ├── tests/
│   │   ├── conftest.py            # Global test fixtures and configuration
│   │   ├── api/                   # API endpoint tests (dual-API structure)
│   │   │   ├── conftest.py        # API-specific fixtures
│   │   │   ├── v1/                # Public API tests (/v1/)
│   │   │   │   ├── test_main_endpoints.py
│   │   │   │   └── test_text_processing_endpoints.py
│   │   │   └── internal/          # Internal API tests (/internal/)
│   │   │       ├── test_admin_endpoints.py
│   │   │       ├── test_cache_endpoints.py
│   │   │       ├── test_monitoring_endpoints.py
│   │   │       └── test_resilience_*_endpoints.py
│   │   ├── core/                  # Core application functionality
│   │   │   ├── test_config.py
│   │   │   ├── test_dependencies.py
│   │   │   ├── test_exceptions.py
│   │   │   └── test_middleware.py
│   │   ├── infrastructure/        # Infrastructure service tests (>90% coverage)
│   │   │   ├── ai/               # AI infrastructure tests
│   │   │   ├── cache/            # Cache infrastructure tests
│   │   │   ├── monitoring/       # Monitoring infrastructure tests
│   │   │   ├── resilience/       # Resilience pattern tests
│   │   │   └── security/         # Security infrastructure tests
│   │   ├── services/             # Domain service tests (>70% coverage)
│   │   │   ├── test_response_validator.py
│   │   │   └── test_text_processing.py
│   │   ├── integration/          # Cross-component integration tests
│   │   │   ├── test_auth_endpoints.py
│   │   │   ├── test_cache_integration.py
│   │   │   ├── test_end_to_end.py
│   │   │   └── test_resilience_integration*.py
│   │   ├── performance/          # Performance and load testing
│   │   │   └── test_cache_performance.py
│   │   ├── manual/               # Manual tests (require running server)
│   │   │   ├── test_manual_api.py
│   │   │   └── test_manual_auth.py
│   │   └── shared_schemas/       # Shared model tests
│   │       ├── test_common_schemas.py
│   │       └── test_text_processing_schemas.py
│   ├── pytest.ini                # Pytest configuration with markers
│   └── requirements-dev.txt      # Testing dependencies
├── frontend/
│   ├── tests/
│   │   ├── conftest.py           # Test fixtures and configuration
│   │   ├── test_api_client.py    # API client tests
│   │   └── test_config.py        # Configuration tests
│   ├── pytest.ini               # Pytest configuration
│   └── requirements-dev.txt     # Testing dependencies
├── scripts/
│   ├── run_tests.py             # Main test runner script
│   └── test_integration.py      # Comprehensive testing scenarios
├── Makefile                     # Test automation commands
└── .github/workflows/test.yml   # CI/CD pipeline
```

## Running Tests

### Quick Start

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

### Virtual Environment Management

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

### Detailed Commands

#### Backend Tests

```bash
# Using Makefile (recommended - handles virtual environment automatically)
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

# Manual commands with virtual environment
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

#### Frontend Tests

```bash
# Using Makefile (recommended - handles virtual environment automatically)
make test-frontend

# Or manually with virtual environment
cd frontend
../.venv/bin/python -m pytest tests/ -v

# Run with coverage
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=html
```

#### Integration Tests

```bash
# Using Makefile (recommended - handles Docker availability detection)
make test

# Using the test runner script with virtual environment
.venv/bin/python run_tests.py

# Manual Docker Compose testing
docker-compose up -d
# Wait for services to start
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
docker-compose down

# Local testing without Docker
make test-local
```

## 🧪 Comprehensive Tests

### `scripts/test_integration.py`

Comprehensive testing suite that validates the entire system functionality.

**Test Categories:**
- 🏥 Core functionality tests
- 📝 Text processing operation tests
- 🚨 Error handling tests
- ⚡ Performance tests
- 🔄 Concurrent request tests

**Usage:**
```bash
python integration_test.py
```

**Test Results Example:**
```
📊 Test Results:
   Total Tests: 9
   ✅ Passed: 9
   ❌ Failed: 0
   📈 Success Rate: 100.0%
   ⏱️  Total Duration: 15.23s
   🕐 Average Test Time: 1.69s
```

### ⚡ Performance Considerations

#### Benchmarking Results
Typical performance metrics from `integration_test.py`:

| Operation | Avg Time | Success Rate |
|-----------|----------|--------------|
| Summarize | 2.1s     | 100%         |
| Sentiment | 1.8s     | 100%         |
| Key Points| 2.3s     | 100%         |
| Questions | 2.0s     | 100%         |
| Q&A       | 2.2s     | 100%         |

#### Optimization Tips
- Use appropriate `max_length` for summaries
- Batch similar operations when possible
- Implement caching for frequently requested content
- Monitor API rate limits

## Test Coverage

### Backend Coverage Requirements

The backend follows different coverage requirements based on architectural boundaries:

#### Infrastructure Services (>90% coverage required)
- **AI Infrastructure** (`app/infrastructure/ai/`)
  - Input sanitization and prompt injection protection
  - Prompt builder utilities
  - AI provider abstractions

- **Cache Infrastructure** (`app/infrastructure/cache/`)
  - Redis and memory cache implementations
  - Cache monitoring and performance metrics
  - Graceful degradation patterns

- **Resilience Infrastructure** (`app/infrastructure/resilience/`)
  - Circuit breaker pattern implementation
  - Retry mechanisms with exponential backoff
  - Orchestrator and configuration presets
  - Performance benchmarks

- **Security Infrastructure** (`app/infrastructure/security/`)
  - Multi-key authentication system
  - Security validation and protection

- **Monitoring Infrastructure** (`app/infrastructure/monitoring/`)
  - Health check implementations
  - Metrics collection and alerting

#### Domain Services (>70% coverage required)
- **Text Processing Service** (`app/services/text_processor.py`)
  - AI text processing using PydanticAI agents
  - Business-specific processing logic (educational examples)

- **Response Validator** (`app/services/response_validator.py`)
  - Business-specific response validation logic

#### API Endpoints (95%+ coverage)
- **Public API** (`/v1/`) - External-facing endpoints
  - Authentication validation
  - Health checks
  - Text processing operations
  - Error handling and CORS

- **Internal API** (`/internal/`) - Administrative endpoints  
  - Cache management (38 resilience endpoints)
  - Monitoring and metrics
  - Resilience management across 8 modules

#### Core Components (95%+ coverage)
- **Configuration Management** (`app/core/config.py`)
  - Dual-API configuration
  - Preset-based resilience system
  - Security and infrastructure settings

- **Dependency Injection** (`app/dependencies.py`)
  - Service provider patterns
  - Preset-based configuration loading

#### Shared Models (100% coverage)
- **Pydantic Models** (`shared/models.py` and `app/schemas/`)
  - Cross-service data models
  - Field validation and constraints
  - Serialization/deserialization

### Frontend Coverage

The frontend test suite covers:

- **API Client** (85%+ coverage)
  - HTTP request handling
  - Error handling
  - Response parsing
  - Timeout handling

- **Configuration** (100% coverage)
  - Environment variable handling
  - Default values
  - Settings validation

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

### Test Fixtures

#### Backend Fixtures (`backend/tests/conftest.py`)

**Global Fixtures:**
- `client`: FastAPI test client for main application
- `internal_client`: FastAPI test client for internal API
- `async_client`: Async HTTP client for integration tests
- `sample_text`: Sample text for processing operations
- `sample_request`: Sample processing request data
- `mock_ai_agent`: Mocked AI agent (auto-used to avoid external API calls)
- `redis_client`: Redis client for cache testing
- `memory_cache`: In-memory cache for testing

**Infrastructure-Specific Fixtures** (`backend/tests/infrastructure/conftest.py`):
- `circuit_breaker`: Circuit breaker instance for testing
- `retry_policy`: Retry policy configuration for testing  
- `resilience_config`: Test resilience configuration
- `cache_service`: Cache service with test configuration
- `health_monitor`: Health monitoring service for testing

**API-Specific Fixtures** (`backend/tests/api/conftest.py`):
- `authenticated_client`: Test client with API key authentication
- `internal_api_client`: Test client for internal endpoints
- `mock_dependencies`: Mocked dependency injection for testing

#### Frontend Fixtures (`frontend/tests/conftest.py`)

- `api_client`: API client instance
- `sample_text`: Sample text for testing
- `sample_request`: Sample processing request
- `sample_response`: Sample API response

## Mocking Strategy

### AI Service Mocking

The test suite uses comprehensive mocking for AI services to:

- Avoid external API calls during testing
- Ensure consistent test results
- Speed up test execution
- Test error scenarios and resilience patterns

```python
@pytest.fixture(autouse=True)
def mock_ai_agent():
    """Mock the AI agent to avoid actual API calls during testing."""
    with patch('app.services.text_processor.Agent') as mock:
        mock_instance = AsyncMock()
        mock_instance.run = AsyncMock(return_value=AsyncMock(data="Mock AI response"))
        mock.return_value = mock_instance
        yield mock_instance
```

### Infrastructure Service Mocking

Infrastructure tests use targeted mocking to test resilience patterns:

```python
# Circuit breaker testing
@pytest.fixture
def failing_service():
    """Mock service that fails to test circuit breaker behavior."""
    mock_service = AsyncMock()
    mock_service.call = AsyncMock(side_effect=Exception("Service unavailable"))
    return mock_service

# Cache testing with Redis fallback
@pytest.fixture
def redis_unavailable():
    """Mock Redis unavailability to test memory cache fallback."""
    with patch('redis.Redis') as mock_redis:
        mock_redis.side_effect = ConnectionError("Redis unavailable")
        yield mock_redis
```

### Environment Isolation

Tests use `monkeypatch.setenv()` for clean environment isolation:

```python
def test_resilience_preset_loading(monkeypatch):
    """Test preset loading with clean environment."""
    monkeypatch.setenv("RESILIENCE_PRESET", "production")
    # Test preset loading logic
```

### HTTP Client Mocking

Frontend tests mock HTTP clients to test different scenarios:

```python
async def test_health_check_success(self, api_client):
    """Test successful health check."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await api_client.health_check()
        assert result is True
```

## Code Quality Checks

### Linting

```bash
# Backend linting
cd backend
python -m flake8 app/
python -m mypy app/ --ignore-missing-imports

# Frontend linting
cd frontend
python -m flake8 app/
```

### Code Formatting

```bash
# Format all code (uses virtual environment automatically)
make format

# Manual formatting with virtual environment
cd backend
../.venv/bin/python -m black app/ tests/
../.venv/bin/python -m isort app/ tests/

cd ../frontend
../.venv/bin/python -m black app/ tests/
../.venv/bin/python -m isort app/ tests/
```

## Continuous Integration

### GitHub Actions

The project uses GitHub Actions for CI/CD with the following workflow:

1. **Test Matrix**: Tests run on Python 3.9, 3.10, and 3.11
2. **Dependency Installation**: Install both runtime and development dependencies
3. **Unit Tests**: Run all unit tests with coverage
4. **Code Quality**: Run linting and type checking
5. **Integration Tests**: Build and test with Docker Compose
6. **Coverage Upload**: Upload coverage reports to Codecov

### Local CI Simulation

```bash
# Run the same checks as CI (uses virtual environment automatically)
make ci-test

# Or manually with virtual environment:
cd backend
../.venv/bin/python -m pytest tests/ -v --cov=app --cov-report=xml
../.venv/bin/python -m flake8 app/
../.venv/bin/python -m mypy app/ --ignore-missing-imports

cd ../frontend
../.venv/bin/python -m pytest tests/ -v --cov=app --cov-report=xml
../.venv/bin/python -m flake8 app/
```

## Writing New Tests

### Backend Test Example

```python
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_new_endpoint(self, client: TestClient):
        """Test new API endpoint."""
        response = client.get("/new-endpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert "expected_field" in data
    
    async def test_new_service_method(self, service):
        """Test new service method."""
        result = await service.new_method("test_input")
        assert result.success is True
        assert result.data is not None
```

### Frontend Test Example

```python
class TestNewComponent:
    """Test new frontend component."""
    
    async def test_new_api_method(self, api_client):
        """Test new API client method."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.new_method()
            assert result["result"] == "success"
```

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### Test Organization

- Group related tests in classes
- Use fixtures for common setup
- Keep tests focused and independent
- Test both success and failure scenarios

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

## Performance Testing

### Load Testing

For performance testing, consider using:

```bash
# Install load testing tools
pip install locust

# Run load tests (if implemented)
locust -f tests/load_tests.py --host=http://localhost:8000
```

### Benchmarking

```bash
# Run tests with timing (using virtual environment)
.venv/bin/python -m pytest tests/ --durations=10

# Profile specific tests
.venv/bin/python -m pytest tests/test_main.py --profile
```

## Contributing to Tests

### Guidelines

1. **Write tests for new features**: All new code should include tests
2. **Maintain coverage**: Aim for >90% test coverage
3. **Test edge cases**: Include tests for error conditions and edge cases
4. **Use appropriate mocks**: Mock external dependencies appropriately
5. **Keep tests fast**: Unit tests should run quickly
6. **Document complex tests**: Add comments for complex test logic

### Pull Request Requirements

Before submitting a pull request:

1. Run the full test suite: `make test`
2. Check code quality: `make lint`
3. Format code: `make format`
4. Ensure coverage doesn't decrease
5. Add tests for new functionality

## Troubleshooting

### Common Test Failures

1. **API Key Issues**: Ensure `GEMINI_API_KEY` is set for tests (can be dummy value)
2. **Port Conflicts**: Ensure test ports are available
3. **Docker Issues**: Ensure Docker is running for integration tests, or use `make test-local` to skip Docker tests
4. **Dependency Issues**: Run `make install` to update dependencies in the virtual environment
5. **Python Version Issues**: The Makefile automatically detects the correct Python version
6. **Virtual Environment Issues**: Run `make clean-all` followed by `make install` to reset the environment

### Getting Help

- Check the test output for specific error messages
- Review the test configuration in `pytest.ini`
- Check the CI logs for additional context
- Refer to the pytest documentation for advanced usage

## Test Metrics

The test suite tracks the following metrics:

- **Test Coverage**: Percentage of code covered by tests
- **Test Duration**: Time taken to run tests
- **Test Success Rate**: Percentage of tests passing
- **Code Quality Score**: Results from linting and type checking

These metrics are tracked in CI and can be viewed in the coverage reports and GitHub Actions logs. 