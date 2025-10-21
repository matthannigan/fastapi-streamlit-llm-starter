# Integration Test Migration - Current Status

## Summary

**Progress**: 6 passed, 15 failed, 1 xfailed out of 22 tests

The migration is mostly complete, but several tests are failing due to using FakeCache methods that don't exist on real AIResponseCache.

## ✅ What's Working

1. **Infrastructure Setup**: All fixtures work correctly
   - `test_settings` provides proper configuration
   - `ai_response_cache` creates working cache with fakeredis
   - `ai_response_cache_with_data` pre-populates cache correctly
   - `mock_pydantic_agent` provides AI mocking

2. **Basic Cache Hit Test**: First test passes completely
   - `test_cache_hit_returns_cached_response_without_ai_call` ✅ PASSING
   - Cache retrieval works
   - Cache hit detection works
   - Mock agent verification works

3. **Fixed Issues**:
   - Added `processing_time: 0.01` to cached data (was `None`, causing assertion failure)
   - All fixture setup issues resolved
   - Type errors resolved with `# type: ignore` comment
   - Redis connection handled properly (fakeredis doesn't need connect/disconnect)

## ❌ What's Failing

**Root Cause**: Tests using FakeCache inspection methods that don't exist on AIResponseCache

### Missing Methods

Tests are calling these FakeCache methods that aren't available on real cache:

1. **`get_all_keys()`** - Used to inspect cache contents
2. **`get_stored_ttl(key)`** - Used to verify TTL values
3. **Direct cache inspection**: `list(cache._data.keys())`, `len(cache._data)`

### Affected Tests (15 failures)

All failing tests fall into these categories:

1. **Cache Storage Verification** (1 test):
   - `test_cache_storage_after_successful_ai_processing` - Tries to verify cache was populated

2. **Cache Key Generation** (5 tests):
   - Tests that verify cache keys contain expected components
   - Need to verify cache was called with correct key structure

3. **TTL Management** (6 tests):
   - Tests that verify different operations use different TTLs
   - Need to verify cache.set() was called with correct TTL

4. **Batch Caching** (2 tests):
   - Tests for batch processing caching behavior
   - Need cache inspection to verify batch results stored

5. **Concurrent Requests** (1 test):
   - Test for concurrent request handling
   - Needs cache inspection

## 🔧 Solution Path

### Option 1: Mock cache.set() and cache.get() (Recommended)

**Approach**: Use `unittest.mock` to spy on cache operations instead of inspecting cache state.

**Why**: This is more aligned with integration testing - we test behavior (cache was called) not internal state.

**Pattern**:
```python
from unittest.mock import AsyncMock, patch

async def test_cache_storage_after_successful_ai_processing(test_settings, ai_response_cache, mock_pydantic_agent):
    """Test that successful AI responses are stored in cache."""

    # Spy on cache.set() to verify it was called
    original_set = ai_response_cache.set
    set_spy = AsyncMock(wraps=original_set)

    with patch.object(ai_response_cache, 'set', set_spy):
        processor = TextProcessorService(settings=test_settings, cache=ai_response_cache)

        request = TextProcessingRequest(text="Test", operation="summarize")
        await processor.process_text(request)

        # Verify cache.set was called
        set_spy.assert_called_once()

        # Verify TTL if needed
        call_args = set_spy.call_args
        assert call_args.kwargs.get('ttl') == expected_ttl
```

**Pros**:
- Tests behavior not implementation
- Works with real AIResponseCache
- More maintainable (no dependence on internal cache structure)
- Aligns with integration testing philosophy

**Cons**:
- Requires test rewrites
- More verbose than direct inspection

### Option 2: Add inspection methods to AIResponseCache (NOT Recommended)

**Approach**: Add `get_all_keys()`, `get_stored_ttl()` methods to AIResponseCache for testing

**Why Not**: Production code shouldn't be modified for test convenience. This violates separation of concerns.

### Option 3: Use cache.get() to verify storage (Partial Solution)

**Approach**: After operation, use `cache.get(key)` to verify data was stored

**Pattern**:
```python
async def test_cache_storage_after_successful_ai_processing(test_settings, ai_response_cache, mock_pydantic_agent):
    """Test that successful AI responses are stored in cache."""
    processor = TextProcessorService(settings=test_settings, cache=ai_response_cache)

    request = TextProcessingRequest(text="Test", operation="summarize")
    response = await processor.process_text(request)

    # Build the cache key the same way the service does
    cache_key = ai_response_cache.build_key(
        text=request.text,
        operation=request.operation.value,
        options=request.options or {}
    )

    # Verify data was stored
    cached_data = await ai_response_cache.get(cache_key)
    assert cached_data is not None
    assert cached_data['result'] == response.result
```

**Pros**:
- Simpler than mocking
- Tests actual cache behavior

**Cons**:
- Can't verify TTL directly
- Requires knowing cache key structure

## 📋 Recommended Action Plan

**Use combination of Option 1 (mocking) and Option 3 (get verification)**

### Phase 1: Fix Cache Storage Tests (1 test)
- Patch `cache.set()` to verify storage calls
- Or use `cache.get()` to verify data was stored

### Phase 2: Fix Cache Key Tests (5 tests)
- Patch `cache.get()` or `cache.set()` to inspect cache key format
- Verify key contains expected components

### Phase 3: Fix TTL Tests (6 tests)
- Patch `cache.set()` to inspect TTL parameter
- Verify correct TTL passed for each operation

### Phase 4: Fix Batch Tests (2 tests)
- Similar approach to Phase 1
- Verify multiple cache.set() calls for batch operations

### Phase 5: Fix Concurrent Test (1 test)
- May need different approach depending on what it's testing

## 🎯 Next Steps

1. **Choose strategy**: Decide between mock-based (Option 1) vs get-based (Option 3) verification
2. **Create helper utilities**: Build reusable test helpers for cache verification
3. **Fix one test category at a time**: Start with cache storage, then key generation, then TTL
4. **Run tests frequently**: Verify each fix doesn't break passing tests

## 📄 Related Files

- **Test file**: `tests/integration/text_processor/test_text_processor_cache_integration.py`
- **Fixture file**: `tests/integration/text_processor/conftest.py`
- **Cleanup guide**: `tests/integration/text_processor/TODO_CLEANUP_GUIDE.md`
- **Migration guide**: `tests/integration/text_processor/UPGRADE_UNIT_TESTS.md`

## 🔍 Diagnostic Commands

```bash
# Run single failing test with full output
../.venv/bin/python -m pytest \
  tests/integration/text_processor/test_text_processor_cache_integration.py::TestTextProcessorCachingStrategy::test_cache_storage_after_successful_ai_processing \
  -xvs --tb=long

# Run all tests to see progress
../.venv/bin/python -m pytest \
  tests/integration/text_processor/ \
  -v --tb=short

# Count passing vs failing
../.venv/bin/python -m pytest \
  tests/integration/text_processor/ \
  -v --tb=no | grep -E "passed|failed|xfailed"
```
