# Migration Analysis: Unit Test Fixtures → Integration Test Fixtures

## Quick Answer to Your Questions

### Q1: Do we need fixtures from unit test conftest files?

**Short Answer:** NO - Most unit test fixtures should be replaced, not reused.

**What to Keep:**
- ✅ `test_settings` - Already have refactored version in integration/cache/conftest.py
- ✅ Request/response test data fixtures (if any)

**What to Replace:**
- ❌ `fake_cache` → Replace with `ai_response_cache` (real cache + fakeredis)
- ❌ `fake_cache_with_hit` → Replace with `ai_response_cache_with_data`
- ❌ `mock_pydantic_agent` → **Keep for now** (see decision below)
- ❌ `fake_prompt_sanitizer` → Replace with real `PromptSanitizer` (optional)

### Q2: Can we create a batch edit script?

**Short Answer:** YES - See `migrate_integration_tests.py` below.

---

## Fixture Mapping: Unit → Integration

| Unit Test Fixture | Integration Replacement | Reasoning |
|-------------------|------------------------|-----------|
| `fake_cache` | `ai_response_cache` | Real AIResponseCache with fakeredis - tests actual cache behavior |
| `fake_cache_with_hit` | `ai_response_cache_with_data` | Pre-populated real cache for cache hit tests |
| `test_settings` | `test_settings` (from cache conftest) | Already refactored with monkeypatch |
| `mock_pydantic_agent` | **Keep temporarily** | Avoids requiring real AI API keys in tests |
| `fake_prompt_sanitizer` | Real `PromptSanitizer` | Simple enough to use real implementation |

---

## Decision: Keep or Replace mock_pydantic_agent?

### Option A: Keep Mock (Recommended for Now) ✅

**Pros:**
- ✅ No AI API keys required for tests
- ✅ Fast test execution
- ✅ Predictable responses
- ✅ Focus on cache integration, not AI integration

**Cons:**
- ❌ Doesn't test real AI agent behavior
- ❌ Not "true" integration test

**Verdict:** Keep mock for cache integration tests. Create separate "AI integration tests" later for end-to-end AI validation.

### Option B: Use Real PydanticAI Agent

**Pros:**
- ✅ True end-to-end integration
- ✅ Tests real AI responses

**Cons:**
- ❌ Requires GEMINI_API_KEY
- ❌ Slower (network calls)
- ❌ Non-deterministic responses
- ❌ Costs money per test run

**Verdict:** Save for E2E test suite, not integration tests.

---

## New Fixtures Needed in conftest.py

Add these to `backend/tests/integration/text_processor/conftest.py`:

```python
@pytest.fixture
async def ai_response_cache_with_data(fakeredis_client, monkeypatch):
    """
    Pre-populated AIResponseCache for testing cache hit scenarios.

    Follows pattern from unit tests' fake_cache_with_hit but uses
    real AIResponseCache to test production cache behavior.
    """
    from cryptography.fernet import Fernet

    # Setup encryption key
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)

    cache = AIResponseCache(
        redis_client=fakeredis_client,
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        enable_monitoring=True,
        enable_encryption=False,
    )

    await cache.connect()

    # Pre-populate with sample data
    cache_key = cache.build_cache_key(
        text="Sample text for testing",
        operation="summarize",
        options={"max_length": 100}
    )

    await cache.set(
        cache_key,
        {
            "result": "Cached summary of sample text content",
            "operation": "summarize",
            "cache_hit": True,
        },
        ttl=7200
    )

    try:
        yield cache
    finally:
        try:
            await cache.clear()
            await cache.disconnect()
        except Exception as e:
            print(f"Warning: Cache cleanup failed: {e}")


@pytest.fixture
def mock_pydantic_agent():
    """
    Mock PydanticAI Agent for testing without AI API keys.

    This mock allows integration tests to focus on cache behavior
    without requiring actual AI service calls.

    Note:
        For true end-to-end AI integration, create separate E2E tests
        with real AI agents using manual test markers.
    """
    from unittest.mock import AsyncMock, Mock

    mock_agent = Mock()
    mock_agent.run = AsyncMock()

    # Default response structure matching PydanticAI
    mock_agent.run.return_value = Mock(
        data="AI processed result",
        cost=Mock(request_tokens=10, response_tokens=20)
    )

    return mock_agent


@pytest.fixture
def fake_prompt_sanitizer():
    """
    Fake PromptSanitizer for tracking sanitization calls.

    Note:
        Consider replacing with real PromptSanitizer in integration tests
        since it's simple infrastructure with no external dependencies.
    """
    from unittest.mock import Mock

    sanitizer = Mock()
    sanitizer.sanitize = Mock(side_effect=lambda text: text)  # Pass-through
    sanitizer.sanitize_called = False

    def track_sanitize(text):
        sanitizer.sanitize_called = True
        return text

    sanitizer.sanitize.side_effect = track_sanitize
    return sanitizer
```

---

## Batch Migration Script

See `migrate_integration_tests.py` (next file)

---

## Migration Steps

1. ✅ Add new fixtures to conftest.py (see above)
2. ✅ Run batch migration script
3. ✅ Update test docstrings with "Integration Scope" sections
4. ✅ Run tests and fix any issues
5. ✅ Validate all tests pass

---

## Test Docstring Update Pattern

**Before (Unit Test):**
```python
async def test_cache_hit_returns_cached_response_without_ai_call(
    self, test_settings, fake_cache_with_hit, mock_pydantic_agent
):
    """
    Test cache hit returns cached response immediately without AI processing.

    Verifies:
        When cache contains response for request, process_text() returns
        cached response immediately without invoking AI agent.
    """
```

**After (Integration Test):**
```python
async def test_cache_hit_returns_cached_response_without_ai_call(
    self, test_settings, ai_response_cache_with_data, mock_pydantic_agent
):
    """
    Integration Test: Cache hit returns cached response without AI call.

    Integration Scope:
        TextProcessorService + AIResponseCache collaboration
        Tests real cache lookup behavior with production cache implementation.

    Verifies:
        When cache contains response for request, process_text() returns
        cached response immediately without invoking AI agent.

    Production Behaviors Tested:
        - Real cache key generation algorithm
        - L1 cache lookup before L2 (Redis)
        - Cache hit detection and metadata
        - Response deserialization from cache

    Business Impact:
        Reduces AI API costs and improves response times by serving cached
        responses for repeated requests without AI service calls.
    """
```

---

## What Gets Changed by Script

### Fixture Parameter Replacements

```python
# Before
def test_example(self, test_settings, fake_cache, mock_pydantic_agent):

# After
def test_example(self, test_settings, ai_response_cache, mock_pydantic_agent):
```

```python
# Before
def test_example(self, test_settings, fake_cache_with_hit, mock_pydantic_agent):

# After
def test_example(self, test_settings, ai_response_cache_with_data, mock_pydantic_agent):
```

### Cache Usage in Test Body

```python
# Before
processor = TextProcessorService(test_settings, fake_cache)
assert fake_cache.get_hit_count() == 1
cache_keys = await fake_cache.get_all_keys()

# After
processor = TextProcessorService(test_settings, ai_response_cache)
# Remove get_hit_count() - not available in real cache
cache_keys = await ai_response_cache.get_all_keys()
```

### Helper Function Updates

```python
# Before
def _create_text_processor_with_mock_agent(test_settings, cache_service, mock_pydantic_agent):

# After
def _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent):
```

---

## What Script CANNOT Change (Manual Review Required)

1. **Cache metric assertions** - FakeCache has `.get_hit_count()`, real cache doesn't
   ```python
   # Remove these:
   assert fake_cache.get_hit_count() == 1
   assert fake_cache.get_miss_count() == 1
   ```

2. **TTL access patterns** - FakeCache has `.get_stored_ttl()`, real cache internal
   ```python
   # Change from:
   stored_ttl = fake_cache.get_stored_ttl(cache_key)

   # To:
   # TTL testing done differently in integration tests
   ```

3. **Direct `_data` access** - FakeCache exposes `._data`, real cache doesn't
   ```python
   # Remove these:
   assert len(fake_cache._data) > 0
   ```

4. **Test docstrings** - Add "Integration Scope" sections manually

---

## Summary

**DO copy from .bak file:**
- ❌ NO - Most fixtures need replacement

**DO use batch script:**
- ✅ YES - Script handles 80% of migration
- ✅ Manual review required for cache metrics and docstrings

**DO keep mocks:**
- ✅ YES - Keep `mock_pydantic_agent` for now
- ✅ Focus on cache integration, not AI integration
