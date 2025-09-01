---
sidebar_label: Mocking
---

# Mocking Strategy: Fakes Over Mocks

Our behavioral testing philosophy requires a disciplined approach to managing dependencies, moving away from the brittle mocking patterns of the past.

- **No Mocking of Internals**: We follow a strict rule: "absolutely no mocking of internal details". Mocks are considered prone to brittleness and can create false positives.
- **Prefer Fakes and Real Infrastructure**: We strongly prefer using "fakes" (like `FakeRedis`) for fast local tests or "real infrastructure" via tools like `Testcontainers` for integration tests. Fakes provide a more honest and robust validation by simulating real behavior.
- **Constrained Mocking at Boundaries**: When mocking is absolutely necessary for external dependencies, we only mock what leaves the process boundary. We use "No-Lies Mocks" that validate call signatures to ensure the mock is an honest reflection of the real interface.

## Decision Framework: When Internal Mocking is Acceptable

The following framework, adopted from our infrastructure testing suite, governs when internal mocking is permitted project-wide.

### ✅ **Acceptable Internal Mocking Scenarios**

- **Error Handling Logic Testing**

    - **When**: Testing how a component handles specific, hard-to-trigger errors from its direct dependencies.
    - **Rationale**: The focus is on the calling component's error handling, not the dependency's behavior.
    - **Requirement**: Should be supplemented with integration tests using invalid configurations to trigger real errors.

- **Parameter Mapping and Transformation Testing**

    - **When**: Verifying that a component correctly transforms or passes arguments to a dependency.
    - **Rationale**: This tests a component's specific orchestration logic without needing to exercise the full dependency. The mock only inspects call arguments.

### ❌ **Unacceptable Internal Mocking Scenarios**

- **Business Logic Testing**: Testing the core functionality of internal components.
    - **Alternative**: Use real components with test data.
- **Integration Flow Testing**: Testing multi-component workflows.
    - **Alternative**: Use integration tests with real components.
- **Performance and Resource Management Testing**: Testing memory usage, monitoring, or cleanup.
    - **Alternative**: Use real components and monitor their behavior.

## Mocking Strategy

**Anti-Patterns: What NOT to Mock in Unit Tests:**
* **Parent Classes**: Do not mock methods from a class's parent (e.g., `GenericRedisCache.set`).
* **Internal Helper Classes**: Do not mock internal collaborators (e.g., `CacheKeyGenerator`).
* **Private Methods**: Never test or mock private methods (e.g., `_decompress_data`).

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

