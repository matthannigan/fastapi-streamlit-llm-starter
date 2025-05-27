# Testing Guide

This document provides comprehensive information about the test suite for the FastAPI-Streamlit-LLM starter template.

## Overview

The test suite covers both backend and frontend components with the following types of tests:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions and API endpoints
- **End-to-End Tests**: Test complete user workflows
- **Code Quality**: Linting, type checking, and formatting validation

## Test Structure

```
├── backend/
│   ├── tests/
│   │   ├── conftest.py            # Test fixtures and configuration
│   │   ├── test_main.py           # FastAPI endpoint tests
│   │   ├── test_text_processor.py # Service layer tests
│   │   └── test_models.py         # Pydantic model tests
│   ├── pytest.ini                 # Pytest configuration
│   └── requirements-dev.txt       # Testing dependencies
├── frontend/
│   ├── tests/
│   │   ├── conftest.py            # Test fixtures and configuration
│   │   ├── test_api_client.py     # API client tests
│   │   └── test_config.py         # Configuration tests
│   ├── pytest.ini                 # Pytest configuration
│   └── requirements-dev.txt       # Testing dependencies
├── frontend/
│   ├── run_tests.py               # Main test runner script
│   └── test_integration.py        # Comprehensive testing scenarios
├── Makefile                       # Test automation commands
└── .github/workflows/test.yml     # CI/CD pipeline
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
make test-backend

# Or manually with virtual environment
cd backend
../.venv/bin/python -m pytest tests/ -v

# Run specific test file
../.venv/bin/python -m pytest tests/test_main.py -v

# Run with coverage
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=html

# Run specific test class
../.venv/bin/python -m pytest tests/test_main.py::TestHealthEndpoint -v

# Run specific test method
../.venv/bin/python -m pytest tests/test_main.py::TestHealthEndpoint::test_health_check -v
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

### Backend Coverage

The backend test suite covers:

- **API Endpoints** (95%+ coverage)
  - Health check endpoint
  - Operations listing
  - Text processing endpoints
  - Error handling
  - CORS configuration

- **Service Layer** (90%+ coverage)
  - Text processing service
  - AI agent integration (mocked)
  - Error handling and validation

- **Models** (100% coverage)
  - Pydantic model validation
  - Field constraints
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

Both backend and frontend use pytest with the following configuration:

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
    slow: marks tests as slow
    integration: marks tests as integration tests
```

### Test Fixtures

#### Backend Fixtures (`backend/tests/conftest.py`)

- `client`: FastAPI test client
- `async_client`: Async HTTP client
- `sample_text`: Sample text for processing
- `sample_request`: Sample processing request
- `mock_ai_agent`: Mocked AI agent (auto-used)

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
- Test error scenarios

```python
@pytest.fixture(autouse=True)
def mock_ai_agent():
    """Mock the AI agent to avoid actual API calls during testing."""
    with patch('backend.app.services.text_processor.Agent') as mock:
        mock_instance = AsyncMock()
        mock_instance.run = AsyncMock(return_value=AsyncMock(data="Mock AI response"))
        mock.return_value = mock_instance
        yield mock_instance
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

### Common Issues

1. **Python Command Not Found**: The Makefile automatically detects `python3` or `python` - no manual configuration needed
2. **Virtual Environment Issues**: Run `make clean-all` and `make install` to recreate the virtual environment
3. **Import Errors**: Ensure you're using the virtual environment Python (`.venv/bin/python`) or Makefile commands
4. **Async Test Issues**: Use `pytest-asyncio` and proper async fixtures
5. **Mock Issues**: Ensure mocks are properly configured and reset between tests
6. **Environment Variables**: Use `patch.dict` to mock environment variables
7. **Docker Not Available**: Use `make test-local` to run tests without Docker dependency

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