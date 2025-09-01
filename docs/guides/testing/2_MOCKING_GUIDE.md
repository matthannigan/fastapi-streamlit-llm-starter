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

### ✅ Acceptable Internal Mocking Scenarios

- **Error Handling Logic Testing**

    - **When**: Testing how a component handles specific, hard-to-trigger errors from its direct dependencies.
    - **Rationale**: The focus is on the calling component's error handling, not the dependency's behavior.
    - **Requirement**: Should be supplemented with integration tests using invalid configurations to trigger real errors.

- **Parameter Mapping and Transformation Testing**

    - **When**: Verifying that a component correctly transforms or passes arguments to a dependency.
    - **Rationale**: This tests a component's specific orchestration logic without needing to exercise the full dependency. The mock only inspects call arguments.

### ❌ Unacceptable Internal Mocking Scenarios

- **Business Logic Testing**: Testing the core functionality of internal components.
    - **Alternative**: Use real components with test data.
- **Integration Flow Testing**: Testing multi-component workflows.
    - **Alternative**: Use integration tests with real components.
- **Performance and Resource Management Testing**: Testing memory usage, monitoring, or cleanup.
    - **Alternative**: Use real components and monitor their behavior.

## Practical Mocking Strategies

### "No-Lies Mocks" Implementation

When mocking is necessary, use **"No-Lies Mocks"** that validate call signatures to ensure they accurately reflect real interfaces:

```python
# ✅ GOOD: No-Lies Mock validates the actual interface
import inspect
from unittest.mock import Mock, patch

def create_no_lies_mock(real_class):
    """Create a mock that validates call signatures against the real interface."""
    mock = Mock(spec=real_class)
    
    # Validate method signatures on call
    for name, method in inspect.getmembers(real_class, predicate=inspect.ismethod):
        if not name.startswith('_'):  # Skip private methods
            original_signature = inspect.signature(method)
            setattr(mock, name, Mock(spec=original_signature))
    
    return mock

# Usage in tests
@patch('external_service.HTTPClient')
def test_api_client_with_validated_mock(mock_http_client_class):
    # Mock validates actual HTTPClient interface
    mock_client = create_no_lies_mock(HTTPClient)
    mock_http_client_class.return_value = mock_client
    
    # This will fail if get() signature changes in real HTTPClient
    mock_client.get.return_value = Mock(status_code=200, json=lambda: {"result": "success"})
    
    api_client = APIClient()
    result = api_client.fetch_data()
    
    # Test validates actual interface usage
    mock_client.get.assert_called_once_with("/api/data", headers={"Accept": "application/json"})
```

### Decision Framework: Fake vs Mock vs Real

Use this decision tree to determine the appropriate testing strategy:

```python
# 1. PREFER: Real dependencies for internal components
def test_cache_service_stores_data():
    """✅ Use real Redis cache or FakeRedis - no mocking needed."""
    cache = CacheService()  # Uses real implementation
    
    cache.set("key", "value")
    result = cache.get("key")
    
    assert result == "value"

# 2. ACCEPTABLE: Fakes for external infrastructure  
def test_cache_with_fake_redis():
    """✅ Use FakeRedis for fast, deterministic tests."""
    import fakeredis
    
    with patch('redis.Redis', fakeredis.FakeRedis):
        cache = CacheService()
        cache.set("key", "value")
        result = cache.get("key")
        assert result == "value"

# 3. LAST RESORT: Mocks only at system boundaries
def test_external_api_integration():
    """✅ Mock external HTTP calls only."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock(status_code=200, json=lambda: {"external": "data"})
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        service = ExternalAPIService()
        result = await service.fetch_external_data()
        
        assert result["external"] == "data"
```

### Anti-Patterns: What NOT to Mock in Unit Tests

**❌ Do NOT Mock These:**

```python
# ❌ BAD: Mocking parent classes
class TestAIResponseCache:
    def test_set_method(self):
        with patch.object(GenericRedisCache, 'set') as mock_parent_set:
            cache = AIResponseCache()
            cache.set("key", "value")
            mock_parent_set.assert_called_once()  # Tests inheritance, not behavior

# ❌ BAD: Mocking internal collaborators
def test_cache_key_generation():
    with patch('app.cache.CacheKeyGenerator') as mock_generator:
        mock_generator.return_value.generate.return_value = "generated_key"
        cache = CacheService()
        cache.set("original_key", "value")
        mock_generator.return_value.generate.assert_called()  # Tests implementation

# ❌ BAD: Mocking private methods
def test_data_compression():
    cache = CacheService()
    with patch.object(cache, '_compress_data') as mock_compress:
        cache.set("key", "large_value")
        mock_compress.assert_called()  # Tests private implementation
```

**✅ Do This Instead:**

```python
# ✅ GOOD: Test observable behavior
class TestAIResponseCache:
    def test_stores_and_retrieves_ai_responses(self):
        """Test that AI cache properly stores and retrieves responses."""
        cache = AIResponseCache()
        
        ai_response = {"model": "gemini", "response": "Generated content"}
        cache.set("prompt_key", ai_response)
        
        retrieved = cache.get("prompt_key")
        assert retrieved == ai_response
        assert retrieved["model"] == "gemini"

# ✅ GOOD: Test end-to-end behavior with real collaborators
def test_cache_service_generates_appropriate_keys():
    """Test that cache service creates appropriate keys for different data types."""
    cache = CacheService()  # Uses real CacheKeyGenerator
    
    # Test with different inputs to verify key generation behavior
    cache.set("user:123", {"name": "John"})
    cache.set("session:abc", {"token": "xyz"})
    
    # Verify behavior through observable outcomes
    user_data = cache.get("user:123")
    session_data = cache.get("session:abc")
    
    assert user_data["name"] == "John"
    assert session_data["token"] == "xyz"
```

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

