# Backend Test Suite

This directory contains comprehensive tests for the FastAPI backend application.

## Test Categories

### 1. Unit Tests
These tests can be run without any external dependencies:
- `test_resilience.py` - Tests for the AI service resilience module
- `test_text_processor.py` - Tests for the text processing service
- `test_cache.py` - Tests for caching functionality
- `test_models.py` - Tests for data models

**Run unit tests:**
```bash
pytest tests/test_resilience.py tests/test_text_processor.py tests/test_cache.py tests/test_models.py -v
```

### 2. Integration Tests
These tests require a running FastAPI server:
- `test_main.py` - Main application integration tests

**Run integration tests:**
```bash
# First, start the FastAPI server:
cd backend
uvicorn app.main:app --reload --port 8000

# Then run the tests in another terminal:
pytest tests/test_main.py -v
```

### 3. Manual Tests
These tests are designed for manual verification and require:
- A running FastAPI server at `http://localhost:8000`
- Valid AI API keys (e.g., `GEMINI_API_KEY`)
- Manual test API key: `API_KEY=test-api-key-12345`

**Manual test files:**
- `test_manual_api.py` - Manual API endpoint tests
- `test_manual_auth.py` - Manual authentication tests

**To run manual tests:**
```bash
# 1. Set up environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# 2. Start the FastAPI server
cd backend
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests in another terminal
pytest tests/test_manual_api.py tests/test_manual_auth.py -v -s
```

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

### Import Errors
If you see `NameError: name 'os' is not defined`:
- This has been fixed in recent updates
- Make sure you're using the latest version of the test files

### Circuit Breaker Issues
If you see `AttributeError: 'EnhancedCircuitBreaker' object has no attribute 'failure_threshold'`:
- This has been fixed in recent updates
- The circuit breaker now properly inherits and implements required attributes

## Running All Tests

**Run all unit tests (no external dependencies):**
```bash
pytest tests/ -v --ignore=tests/test_manual_api.py --ignore=tests/test_manual_auth.py --ignore=tests/test_main.py
```

**Run specific test files:**
```bash
# Single file
pytest tests/test_resilience.py -v

# Multiple files
pytest tests/test_resilience.py tests/test_text_processor.py -v

# Specific test class or method
pytest tests/test_resilience.py::TestAIServiceResilience::test_service_initialization -v
```

## Test Configuration

Tests use the configuration from `pytest.ini` in the backend directory. Key settings:
- Async test support via `pytest-asyncio`
- Coverage reporting
- Custom markers for different test types

## Debugging Tests

**Run with detailed output:**
```bash
pytest tests/test_resilience.py -v -s --tb=long
```

**Stop on first failure:**
```bash
pytest tests/ -x -v
```

**Run only failed tests:**
```bash
pytest --lf -v
``` 