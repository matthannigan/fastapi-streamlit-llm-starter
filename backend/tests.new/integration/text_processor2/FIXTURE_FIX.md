# Fixture Fix: test_settings Added + Redis Connection Issue

## ✅ Fixed: test_settings Missing

**Added `test_settings` fixture to conftest.py**

The fixture was missing, causing all tests to fail. Now added with proper monkeypatch pattern.

---

## ⚠️ Current Issue: Redis Connection

**Problem:** AIResponseCache is trying to connect to real Redis (`redis:6379`) instead of using the fakeredis client we're passing.

**Error Message:**
```
WARNING - Redis connection failed: Error 8 connecting to redis:6379. nodename nor servname provided, or not known. - using memory-only mode
```

### Root Cause

The `AIResponseCache.connect()` method ignores the `redis_client` parameter we pass and tries to create its own connection to Redis.

### Solutions

#### Option 1: Don't call connect() (Quick Fix)

Remove the `await cache.connect()` line from fixtures since we're passing a pre-connected fakeredis client:

```python
@pytest.fixture(scope="function")
async def ai_response_cache(fakeredis_client, monkeypatch):
    """..."""
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)

    cache = AIResponseCache(
        redis_client=fakeredis_client,  # Already connected
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        enable_monitoring=True,
        enable_encryption=False,
    )

    # ❌ REMOVE THIS LINE - fakeredis_client is already connected
    # await cache.connect()

    try:
        yield cache
    finally:
        try:
            await cache.clear()
            # await cache.disconnect()  # Also remove if it causes issues
        except Exception as e:
            print(f"Warning: Cache cleanup failed: {e}")
```

**Apply to all 3 cache fixtures:**
1. `ai_response_cache`
2. `ai_response_cache_with_data`
3. (Any others that call connect())

---

#### Option 2: Check if AIResponseCache accepts pre-connected clients

If `AIResponseCache` is designed to accept a `redis_client` parameter, it should use that client instead of creating a new connection.

**Check the AIResponseCache implementation:**
```python
# In app/infrastructure/cache/redis_ai.py
# Does __init__ check if redis_client is provided?
# Does connect() respect the redis_client parameter?
```

If the implementation has a bug where it ignores `redis_client`, we may need to fix the production code.

---

## Quick Test

Try removing `connect()` calls:

```bash
# 1. Edit conftest.py - comment out await cache.connect() lines (3 fixtures)

# 2. Run test again
../.venv/bin/python -m pytest tests/integration/text_processor/test_text_processor_cache_integration.py::TestTextProcessorCachingStrategy::test_cache_hit_returns_cached_response_without_ai_call -v --tb=short
```

---

## Expected Behavior

✅ **What should happen:**
- Fakeredis client is passed to AIResponseCache
- AIResponseCache uses the fakeredis client internally
- No connection attempts to real Redis
- Tests run fast (all in-memory)

❌ **What's happening:**
- AIResponseCache ignores redis_client parameter
- Tries to connect to real Redis at redis:6379
- Falls back to memory-only mode
- Tests still work but warning appears

---

## Next Steps

1. ✅ **Already fixed:** Added test_settings fixture
2. ⚠️ **To fix:** Remove `await cache.connect()` from fixtures
3. ✅ **Test:** Run a single test to verify
4. ✅ **If works:** Run all tests

---

## Files to Modify

Edit: `tests/integration/text_processor/conftest.py`

Comment out lines:
- Line ~143: `await cache.connect()`  (in ai_response_cache)
- Line ~215: `await cache.connect()`  (in ai_response_cache_with_data)
- Optionally comment out corresponding disconnect() calls
