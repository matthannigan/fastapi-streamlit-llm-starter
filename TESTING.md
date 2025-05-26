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
│   │   ├── conftest.py          # Test fixtures and configuration
│   │   ├── test_main.py         # FastAPI endpoint tests
│   │   ├── test_text_processor.py # Service layer tests
│   │   └── test_models.py       # Pydantic model tests
│   ├── pytest.ini              # Pytest configuration
│   └── requirements-dev.txt     # Testing dependencies
├── frontend/
│   ├── tests/
│   │   ├── conftest.py          # Test fixtures and configuration
│   │   ├── test_api_client.py   # API client tests
│   │   └── test_config.py       # Configuration tests
│   ├── pytest.ini              # Pytest configuration
│   └── requirements-dev.txt     # Testing dependencies
├── run_tests.py                 # Main test runner script
├── Makefile                     # Test automation commands
└── .github/workflows/test.yml   # CI/CD pipeline
```

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run tests with coverage
make test-coverage
```

### Detailed Commands

#### Backend Tests

```bash
cd backend

# Run all backend tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_main.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run specific test class
python -m pytest tests/test_main.py::TestHealthEndpoint -v

# Run specific test method
python -m pytest tests/test_main.py::TestHealthEndpoint::test_health_check -v
```

#### Frontend Tests

```bash
cd frontend

# Run all frontend tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

#### Integration Tests

```bash
# Using the test runner script
python run_tests.py

# Using Docker Compose
docker-compose up -d
# Wait for services to start
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
docker-compose down
```

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
# Format all code
make format

# Backend formatting
cd backend
python -m black app/ tests/
python -m isort app/ tests/

# Frontend formatting
cd frontend
python -m black app/ tests/
python -m isort app/ tests/
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
# Run the same checks as CI
make ci-test

# Or manually:
cd backend
python -m pytest tests/ -v --cov=app --cov-report=xml
python -m flake8 app/
python -m mypy app/ --ignore-missing-imports

cd ../frontend
python -m pytest tests/ -v --cov=app --cov-report=xml
python -m flake8 app/
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
# Run with verbose output
python -m pytest tests/ -v -s

# Run specific test with debugging
python -m pytest tests/test_main.py::test_specific_function -v -s --pdb

# Run with coverage and keep temporary files
python -m pytest tests/ --cov=app --cov-report=html --keep-durations=10
```

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes the project root
2. **Async Test Issues**: Use `pytest-asyncio` and proper async fixtures
3. **Mock Issues**: Ensure mocks are properly configured and reset between tests
4. **Environment Variables**: Use `patch.dict` to mock environment variables

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
# Run tests with timing
python -m pytest tests/ --durations=10

# Profile specific tests
python -m pytest tests/test_main.py --profile
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
3. **Docker Issues**: Ensure Docker is running for integration tests
4. **Dependency Issues**: Run `make install` to update dependencies

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