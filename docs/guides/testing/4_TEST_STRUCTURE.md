---
sidebar_label: Structure & Organization
---

# Test Structure & Organization

The testing architecture follows both the infrastructure vs domain service separation and a pragmatic organization focused on test purpose and maintainability:

## Current Test Structure

> **📋 Component-Specific Testing Patterns**: 
> - **Backend Testing**: See [Backend Development Guide](../../backend/AGENTS.md) for FastAPI-specific testing patterns, infrastructure service testing, and domain service examples
> - **Frontend Testing**: See [Frontend Development Guide](../../frontend/AGENTS.md) for Streamlit testing patterns, API client testing, and UI component validation

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

## Test Categories Explained

### Functional Tests (User-Facing Behavior)
**Purpose**: Verify that the system works correctly from a user's perspective  
**Scope**: End-to-end workflows, API contracts, user journeys  
**Mocking**: Minimal - only external services (LLM APIs, external databases)  
**Examples**:
```python
def test_complete_text_processing_workflow(client):
    """Test the complete text processing workflow from request to response."""
    # User submits text for processing
    response = client.post("/v1/process", json={
        "text": "Sample article content...",
        "operation": "summarize", 
        "max_length": 100
    })
    
    # Verify user gets expected response structure
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["result"]) <= 100
    assert "processing_time" in data
```

### Integration Tests (Component Interactions)
**Purpose**: Verify that system components work together correctly  
**Scope**: Service interactions, infrastructure integration, data flow  
**Mocking**: Selective - mock external systems but use real internal components  
**Examples**:
```python
def test_cache_integration_with_resilience(cache_service, circuit_breaker):
    """Test that caching works correctly with resilience patterns."""
    # Should cache successful results
    result1 = cache_service.get_or_compute("key1", lambda: "computed_value")
    assert result1 == "computed_value"
    
    # Should serve from cache on subsequent calls
    result2 = cache_service.get_or_compute("key1", lambda: "different_value")  
    assert result2 == "computed_value"  # Served from cache
```

### Unit Tests (Component Contract and Pure Logic)

**Purpose**: Verify a single component works correctly in isolation by testing its public contract. Also used for pure, stateless utility functions.
**Scope**: The component's public-facing API, treating its internal workings as a black box. Tests focus on observable behavior and should be resilient to internal refactoring.
**Mocking**: Heavy mocking for true external dependencies (e.g., third-party APIs) at the system boundary only. **Strictly forbids** mocking of internal collaborators within the component under test. High-fidelity fakes (like `fakeredis`) are strongly preferred over mocks.
**Examples**:

```python
# ✅ GOOD: Tests the observable behavior of the entire cache component
def test_cache_stores_and_retrieves_data(default_memory_cache):
    """
    Given a cache instance adhering to the CacheInterface,
    When a value is set with a key,
    Then the same value should be retrievable with that key.
    """
    key = "test:key"
    value = {"data": "value"}
    
    default_memory_cache.set(key, value)
    retrieved_value = default_memory_cache.get(key)
    
    assert retrieved_value == value

# ❌ BAD: Mocks an internal collaborator to test an implementation detail
def test_cache_uses_internal_key_generator(mock_key_generator):
    """Tests that the cache calls an internal dependency."""
    cache = GenericRedisCache(key_generator=mock_key_generator)
    
    cache.set("test:key", "value")

    # This test is brittle and breaks if the internal wiring changes,
    # even if the cache's external behavior is still correct.
    mock_key_generator.generate.assert_called_once_with("test:key")
```

### Manual Tests (Real Service Integration)
**Purpose**: Verify integration with real external services  
**Scope**: LLM API calls, performance benchmarks, smoke tests  
**Mocking**: None - uses real external services  
**Examples**:
```python
@pytest.mark.manual
def test_gemini_api_integration_smoke():
    """Smoke test to verify Gemini API integration works end-to-end."""
    # Requires real GEMINI_API_KEY and network access
    response = requests.post("http://localhost:8000/v1/process", 
                           headers={"X-API-Key": "test-key"},
                           json={"text": "Test input", "operation": "summarize"})
    
    assert response.status_code == 200
    assert response.json()["success"] is True
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

#### Fixture Documentation Standards

All fixtures follow the unified documentation standards outlined in the [Writing Tests Guide](./1_WRITING_TESTS.md#unified-test-documentation-standards).

> **📖 Fixture Documentation Templates**: See **[DOCSTRINGS_TESTS.md](../developer/DOCSTRINGS_TESTS.md)** section on "Fixture Documentation" for comprehensive fixture docstring patterns and examples.

