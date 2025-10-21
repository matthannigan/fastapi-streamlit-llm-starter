# Upgrading from FakeCache to AIResponseCache + fakeredis for Integration Tests

## Overview

The recommendation is to use real production cache implementations (AIResponseCache or GenericRedisCache) backed by fakeredis (an in-memory Redis simulator) instead of the
simple FakeCache for integration tests. This provides more realistic testing while maintaining speed and isolation.

## Understanding the Three Approaches

### 1. FakeCache (Current Unit Test Approach) ✅ Keep for Unit Tests

**What it is:**
```python
class FakeCache:
    def __init__(self):
        self._data: dict[str, Any] = {}  # Simple dictionary
        self._ttls: dict[str, int] = {}   # Stores but doesn't enforce TTL
```

**Characteristics:**
- Simple dictionary-based fake (50 lines of code)
- Does NOT enforce TTL expiration - just stores the value
- Simplified cache key generation - uses hash() function
- No L1/L2 caching layers
- No compression, encryption, or monitoring
- No callbacks or lifecycle hooks
- Perfect for testing TextProcessorService in isolation

**Best for:** Unit tests where you only need to verify "Did we check cache? Did we store result?"

### 2. AIResponseCache + fakeredis (Recommended for Integration Tests) 🎯 Target

**What it is:**
```python
# Real production cache backed by fakeredis (in-memory Redis simulator)
import fakeredis.aioredis

fake_redis = fakeredis.aioredis.FakeRedis()  # Simulates Redis in-memory
cache = AIResponseCache(
    redis_client=fake_redis,  # Use fake instead of real Redis
    default_ttl=3600,
    enable_l1_cache=True,
    compression_threshold=500
)
```

**Characteristics:**
- Real production code (AIResponseCache from app/infrastructure/cache/redis_ai.py)
- Realistic Redis behavior - TTL actually expires, Redis commands work correctly
- All production features enabled:
- L1 (memory) + L2 (Redis) caching layers
- Compression for large values
- Encryption (can be disabled for testing)
- Performance monitoring and callbacks
- Cache key generation using production algorithms
- AI-specific optimizations (batch caching, intelligent TTLs)
- Fast - No network calls, all in-memory
- Isolated - Each test gets fresh fakeredis instance

**Best for:** Integration tests verifying TextProcessorService + Cache collaboration

### 3. AIResponseCache + Real Redis Container (Current Integration Test Approach)

**What it is:**
```python
# Uses Docker container with real Redis server
container = RedisContainer("redis:7-alpine")
cache = AIResponseCache(
    redis_url=container.get_connection_url(),
    # ... real production configuration
)
```

**Characteristics:**
- Real Redis server running in Docker
- Complete production environment including TLS, authentication
- Tests actual network communication and Redis protocol
- Slower - Docker startup, network overhead
- Most realistic - Catches Redis-specific edge cases

**Best for:** End-to-end integration tests and deployment validation

### Detailed Comparison: FakeCache vs AIResponseCache + fakeredis

#### Feature Comparison Table

| Feature                    | FakeCache               | AIResponseCache + fakeredis | Real Redis             |
|----------------------------|-------------------------|-----------------------------|------------------------|
| TTL Enforcement            | ❌ Stored but ignored    | ✅ Actually expires         | ✅ Actually expires     |
| L1 (Memory) Cache          | ❌ N/A                   | ✅ Production code          | ✅ Production code      |
| L2 (Redis) Cache           | ❌ N/A                   | ✅ Simulated                | ✅ Real                 |
| Compression                | ❌ No                    | ✅ Yes (configurable)       | ✅ Yes                  |
| Encryption                 | ❌ No                    | ⚠️ Patchable                | ✅ Yes                  |
| Cache Key Algorithm        | ⚠️ Simple hash           | ✅ Production algorithm     | ✅ Production algorithm |
| Performance Monitoring     | ❌ Basic counters        | ✅ Full metrics             | ✅ Full metrics         |
| Callbacks (on_set, on_get) | ❌ No                    | ✅ Yes                      | ✅ Yes                  |
| Redis Commands             | ❌ N/A                   | ✅ Full Redis API           | ✅ Full Redis API       |
| Test Speed                 | ⚡ Fastest                | ⚡ Fast                     | 🐌 Slower (Docker)      |
| Test Isolation             | ✅ Perfect               | ✅ Perfect                  | ⚠️ Good                 |
| Setup Complexity           | ✅ Trivial               | ⚠️ Moderate                 | ❌ Complex              |
| Code Coverage              | ⚠️ Cache interface only  | ✅ Cache + integration      | ✅ Full stack           |

## Practical Examples

### Example 1: Current Unit Test with FakeCache
```python
# backend/tests/unit/text_processor/test_caching_behavior.py
async def test_cache_hit_returns_cached_response(fake_cache, test_settings):
    """Test cache hit with FakeCache - tests interface only."""

    # Pre-populate FakeCache
    cache_key = "summarize:12345:"
    await fake_cache.set(cache_key, {"result": "Cached summary"}, ttl=7200)

    # Create service with FakeCache
    service = TextProcessorService(test_settings, fake_cache)

    # Call service
    response = await service.process_text(request)

    # Verify cache was used
    assert response.cache_hit is True
    assert fake_cache.get_hit_count() == 1  # FakeCache counter
```

**What this tests:**
- ✅ TextProcessorService checks cache before AI call
- ✅ Cached responses are returned correctly
- ❌ Does NOT test: TTL expiration, L1 cache effectiveness, compression thresholds, real cache key generation

### Example 2: Integration Test with AIResponseCache + fakeredis
```python
# backend/tests/integration/text_processor_cache/test_cache_integration.py
import fakeredis.aioredis
from app.infrastructure.cache.redis_ai import AIResponseCache

@pytest.fixture
async def integration_cache():
    """Real AIResponseCache backed by fakeredis."""
    fake_redis = fakeredis.aioredis.FakeRedis(decode_responses=False)

    cache = AIResponseCache(
        redis_client=fake_redis,
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        # Disable encryption for simplicity (or patch it)
    )

    await cache.connect()
    yield cache
    await cache.disconnect()

async def test_ttl_expiration_integration(integration_cache, test_settings):
    """Test that cache entries actually expire after TTL."""

    # Create service with real cache
    service = TextProcessorService(test_settings, integration_cache)

    # First call - cache miss, stores with short TTL
    request = ProcessingRequest(text="Test", operation="summarize")
    response1 = await service.process_text(request)
    assert response1.cache_hit is False

    # Second call immediately - cache hit
    response2 = await service.process_text(request)
    assert response2.cache_hit is True

    # Wait for TTL to expire (fakeredis respects time.sleep)
    import time
    time.sleep(2)  # Assuming 1-second TTL for test

    # Third call - cache miss due to expiration
    response3 = await service.process_text(request)
    assert response3.cache_hit is False  # FakeCache would still return cached value!

async def test_l1_cache_reduces_redis_calls(integration_cache, test_settings):
    """Test L1 (memory) cache layer optimization."""

    service = TextProcessorService(test_settings, integration_cache)

    # Track Redis operations
    redis_get_count = 0
    original_get = integration_cache._client.get

    async def counting_get(*args, **kwargs):
        nonlocal redis_get_count
        redis_get_count += 1
        return await original_get(*args, **kwargs)

    integration_cache._client.get = counting_get

    # First call - misses L1 and L2
    await service.process_text(request)
    assert redis_get_count == 1  # Checked Redis

    # Second call - hits L1, doesn't check Redis
    await service.process_text(request)
    assert redis_get_count == 1  # Still 1! L1 cache worked

    # FakeCache has no L1 layer - can't test this!

async def test_compression_for_large_responses(integration_cache, test_settings):
    """Test compression kicks in for large AI responses."""

    service = TextProcessorService(test_settings, integration_cache)

    # Generate large response (exceeds compression threshold)
    large_request = ProcessingRequest(
        text="Generate very long summary" * 100,
        operation="summarize"
    )

    await service.process_text(large_request)

    # Verify compression was used (check internal metrics)
    stats = await integration_cache.get_stats()
    assert stats["compressed_entries"] > 0

    # FakeCache doesn't compress - can't verify this behavior!
```

**What integration tests add:**
- ✅ TTL expiration actually works - entries disappear after timeout
- ✅ L1 cache reduces Redis calls - performance optimization verified
- ✅ Compression behavior - large values are compressed
- ✅ Cache key collisions - production algorithm tested
- ✅ Batch caching optimization - AI-specific features tested
- ✅ Monitoring callbacks - performance metrics captured

## Migration Guide: Moving Tests from Unit to Integration

### Prerequisites: Leverage Existing Shared Fixtures

**Before creating new fixtures, understand what's already available in `backend/tests/integration/conftest.py`:**

#### ✅ Already Available - No Action Needed

1. **`setup_testing_environment_for_all_integration_tests`** (autouse fixture)
   - **Automatically sets** `ENVIRONMENT=testing` for ALL integration tests
   - Sets `REDIS_INSECURE_ALLOW_PLAINTEXT=true`
   - Provides default encryption key: `REDIS_ENCRYPTION_KEY`
   - **You don't need to set these** - they're automatic

2. **`integration_app` and `integration_client`** (function-scoped)
   - Fresh app instances using App Factory Pattern
   - Complete test isolation - each test gets new app
   - **Reuse these** instead of creating custom app fixtures

3. **Environment setup fixtures**
   - `production_environment_integration` - Production env with API keys
   - **Use monkeypatch pattern** from these fixtures as reference

#### 📖 Lessons from Cache Integration Tests

The existing cache integration tests (`backend/tests/integration/cache/`) provide battle-tested patterns:

**✅ Best Practices to Follow:**
- Use `monkeypatch.setenv()` for all environment variables (never `os.environ[]`)
- Generate proper Fernet keys for encryption testing
- Use function-scoped fixtures for test isolation
- Implement proper cleanup with try/finally blocks
- Consider serial execution for tests with shared state

**❌ Anti-Patterns to Avoid:**
- Direct `os.environ[]` manipulation (causes test pollution)
- Session-scoped fixtures for stateful resources
- Insufficient cleanup in fixture teardown

See `backend/tests/integration/cache/README.md` for comprehensive integration testing patterns.

---

### ⚠️ CRITICAL: Environment Variable Testing Pattern

**Always use `monkeypatch.setenv()` for environment variables. Never use `os.environ[]` directly.**

This is a **mandatory** coding standard to prevent test pollution and flaky tests:

```python
# ❌ NEVER DO THIS - Causes permanent test pollution
import os

def test_production():
    os.environ["ENVIRONMENT"] = "production"  # Persists forever!
    # This change affects ALL subsequent tests

# ❌ EVEN IN FIXTURES - Still wrong!
@pytest.fixture
def wrong_pattern():
    os.environ["CACHE_PRESET"] = "development"  # NO!
    # Manual cleanup is error-prone and often fails

# ✅ ALWAYS DO THIS - Automatic cleanup
def test_production(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Automatically restored after test completes

# ✅ IN FIXTURES TOO - Correct pattern
@pytest.fixture
def correct_pattern(monkeypatch):
    monkeypatch.setenv("CACHE_PRESET", "development")
    # Cleanup happens automatically
```

**Why this matters:**
- Direct `os.environ[]` modification bypasses pytest cleanup
- Changes persist across all subsequent tests
- Causes flaky, order-dependent test failures
- This was the root cause of integration test flakiness in our project

**⚠️ Known Anti-Pattern Still Present:**
The file `backend/tests/integration/cache/conftest.py` (lines 90-191) still uses direct `os.environ[]` manipulation in `test_settings`, `development_settings`, and `production_settings` fixtures. **Do not copy this pattern.** Phase 2 of this plan will fix these anti-patterns.

**See:** `backend/tests/integration/README.md` for comprehensive environment variable testing patterns.

---

### Step 1: Create Integration Test Fixture

Create backend/tests/integration/text_processor/conftest.py:

```python
"""
Fixtures for text_processor + cache integration tests.

Follows patterns from backend/tests/integration/cache/conftest.py
while leveraging shared fixtures from backend/tests/integration/conftest.py.
"""

import pytest
import fakeredis.aioredis
from cryptography.fernet import Fernet
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.services.text_processor import TextProcessorService

# =============================================================================
# Serial Execution (if needed for shared state)
# =============================================================================

# Uncomment if tests share state or have timing dependencies:
# def pytest_collection_modifyitems(items):
#     """Force text_processor integration tests to run serially."""
#     for item in items:
#         item.add_marker(pytest.mark.xdist_group(name="text_processor_serial"))


# =============================================================================
# Cache Infrastructure Fixtures
# =============================================================================

@pytest.fixture
async def fakeredis_client():
    """
    FakeRedis client for integration testing.

    Provides in-memory Redis simulation without Docker overhead.
    Follows pattern from cache integration tests but uses fakeredis
    instead of real Redis container for faster execution.

    Returns:
        FakeRedis: Async-compatible fake Redis client

    Note:
        decode_responses=False matches production Redis behavior
    """
    return fakeredis.aioredis.FakeRedis(decode_responses=False)


@pytest.fixture
async def ai_response_cache(fakeredis_client, monkeypatch):
    """
    Real AIResponseCache backed by fakeredis for integration testing.

    Follows cache integration test patterns:
    - Uses proper Fernet key generation (like secure_redis_cache)
    - Uses monkeypatch for environment variables (best practice)
    - Proper cleanup in try/finally block
    - Tests real production code with realistic infrastructure

    Differences from cache/conftest.py secure_redis_cache:
    - Uses fakeredis instead of secure Redis container
    - Simplified encryption (can be enabled if needed)
    - Function-scoped instead of session-scoped

    Integration Scope:
        Tests collaboration between TextProcessorService and AIResponseCache
        using production cache code with simulated Redis backend.

    Args:
        fakeredis_client: FakeRedis client fixture
        monkeypatch: Pytest fixture for environment variable manipulation

    Yields:
        AIResponseCache: Connected cache instance with full features

    Note:
        Encryption disabled by default for simplicity.
        See Phase 4 for encryption options if needed.
    """
    # Generate proper encryption key (following cache integration pattern)
    # This ensures encryption infrastructure works even if we disable it
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)

    cache = AIResponseCache(
        redis_client=fakeredis_client,
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        enable_monitoring=True,
        enable_encryption=False,  # Simplified for testing (see Phase 4)
    )

    await cache.connect()

    try:
        yield cache
    finally:
        # Proper cleanup following cache integration pattern
        try:
            await cache.clear()
            await cache.disconnect()
        except Exception as e:
            print(f"Warning: Cache cleanup failed: {e}")


@pytest.fixture
async def integration_text_processor(test_settings, ai_response_cache):
    """
    TextProcessorService with real cache for integration testing.

    Leverages:
    - test_settings from shared conftest.py (if available)
    - ai_response_cache from this conftest.py

    Integration Scope:
        TextProcessorService + AIResponseCache + PydanticAI Agent collaboration

    Args:
        test_settings: Settings instance from shared fixtures
        ai_response_cache: Real cache instance backed by fakeredis

    Returns:
        TextProcessorService: Service instance configured for integration testing
    """
    return TextProcessorService(
        settings=test_settings,
        cache=ai_response_cache,
    )


# =============================================================================
# Test Data Fixtures (optional)
# =============================================================================

@pytest.fixture
def sample_processing_request():
    """Standard text processing request for integration testing."""
    from app.schemas import ProcessingRequest
    return ProcessingRequest(
        text="Sample text for processing",
        operation="summarize"
    )
```

### Step 2: Migrate Cache Collaboration Tests

Before (Unit Test with FakeCache):
```python
# backend/tests/unit/text_processor/test_caching_behavior.py
async def test_cache_key_includes_operation_type(fake_cache, test_settings):
    """Test cache key generation includes operation type."""
    service = TextProcessorService(test_settings, fake_cache)

    await service.process_text(summarize_request)

    keys = await fake_cache.get_all_keys()
    assert any("summarize" in key for key in keys)
```

After (Integration Test with AIResponseCache):
```python
# backend/tests/integration/text_processor_cache/test_cache_key_generation.py
async def test_cache_key_includes_operation_type(integration_text_processor, ai_response_cache):
    """
    Integration Test: Verify cache key generation between text_processor and cache.
    
    Integration Scope: TextProcessorService + AIResponseCache collaboration
    
    Tests:
        - TextProcessorService generates cache keys correctly
        - AIResponseCache stores with proper key format
        - Cache key includes operation type for uniqueness
    """
    await integration_text_processor.process_text(summarize_request)

    # Use real cache API to inspect keys
    keys = await ai_response_cache.get_all_keys()
    assert any("summarize" in key for key in keys)

    # Also verify we can retrieve by key (production cache key generation)
    cache_key = ai_response_cache.build_cache_key(
        text=summarize_request.text,
        operation="summarize",
        options={}
    )
    cached_value = await ai_response_cache.get(cache_key)
    assert cached_value is not None
```

### Step 3: Update Test Docstrings

```python
async def test_cache_miss_triggers_ai_processing_and_stores_result(
    integration_text_processor, ai_response_cache
):
    """
    Integration Test: Verify cache miss → AI call → cache storage workflow.
    
    Integration Scope:
        TextProcessorService + AIResponseCache + PydanticAI Agent collaboration
    
    Workflow Tested:
        1. TextProcessorService checks cache (miss)
        2. TextProcessorService calls PydanticAI Agent
        3. TextProcessorService stores result in cache
        4. Second identical request hits cache
    
    Production Behaviors Verified:
        - Real cache key generation algorithm
        - TTL storage and retrieval
        - L1 cache population after set()
        - Compression if response exceeds threshold
    
    Business Impact:
        Ensures cache-first strategy works end-to-end, reducing AI costs
        and improving response times for repeated requests.
    """
```

## Trade-offs and When to Use Each Approach

### Use FakeCache (Unit Tests)

**When:**
- Testing TextProcessorService logic in complete isolation
- Verifying "Did we call cache.get()? Did we call cache.set()?"
- Testing error handling when cache returns None
- Fast iteration during development

**Example Tests:**
- test_initialization_with_cache_dependency()
- test_process_text_checks_cache_before_ai_call()
- test_fallback_when_cache_unavailable()

### Use AIResponseCache + fakeredis (Integration Tests)

**When:**
- Testing collaboration between TextProcessor and Cache
- Verifying TTL expiration, L1 caching, compression
- Testing cache key generation with production algorithm
- Validating AI-specific cache optimizations

**Example Tests:**
- test_ttl_expiration_prevents_stale_data()
- test_l1_cache_reduces_redis_calls()
- test_compression_for_large_ai_responses()
- test_batch_requests_leverage_cache_individually()

### Use Real Redis Container (E2E Integration Tests)

**When:**
- Testing complete deployment including network, TLS, encryption
- Verifying Redis-specific edge cases (connection failures, timeouts)
- Performance testing under realistic load
- Pre-production validation

**Example Tests:**
- test_cache_survives_redis_restart()
- test_tls_encryption_for_sensitive_data()
- test_cache_performance_under_concurrent_load()

## Implementation Checklist

### Phase 1: Setup fakeredis Infrastructure

- fakeredis already in project dependencies (pyproject.toml)
- Create tests/integration/text_processor_cache/conftest.py
- Add ai_response_cache fixture with fakeredis backend
- Add integration_text_processor fixture

### Phase 2: Migrate Cache Collaboration Tests

- Move 19 tests from test_caching_behavior.py → test_cache_integration.py
- TestTextProcessorCachingStrategy class (6 tests)
- TestTextProcessorCacheKeyGeneration class (5 tests)
- TestTextProcessorCacheTTLManagement class (5 tests)
- TestTextProcessorCacheBehaviorIntegration class (3 tests)
- Move 3 tests from test_batch_processing.py → test_batch_cache_integration.py
- TestTextProcessorBatchCaching class
- Update all test docstrings with "Integration Scope" sections

### Phase 3: Enhance Integration Tests

- Add TTL expiration tests (currently untestable with FakeCache)
- Add L1 cache effectiveness tests
- Add compression threshold tests
- Add monitoring callback tests

### Phase 4: Optional - Encryption Handling

**Three approaches for handling encryption in integration tests:**

#### Option A: Disable encryption (simplest - recommended)

**Best for:** Most integration tests focused on cache behavior, not encryption.

```python
# Already implemented in Step 1 fixture
cache = AIResponseCache(
    redis_client=fakeredis_client,
    enable_encryption=False,  # Simplified testing
    ...
)
```

**Pros:**
- ✅ No cryptography dependency complexity
- ✅ Faster test execution
- ✅ Focus on cache collaboration, not encryption

**Cons:**
- ❌ Doesn't test encryption integration

---

#### Option B: Use proper test encryption key (recommended if testing encryption)

**Best for:** Tests that validate encryption is applied correctly.

**Follows cache integration test pattern from `secure_redis_cache` fixture:**

```python
from cryptography.fernet import Fernet

@pytest.fixture
async def ai_response_cache_with_encryption(fakeredis_client, monkeypatch):
    """
    AIResponseCache with proper test encryption key.

    Follows pattern from cache/conftest.py secure_redis_cache fixture.
    Tests real encryption behavior with generated test key.
    """
    # Generate proper Fernet key for testing
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)

    cache = AIResponseCache(
        redis_client=fakeredis_client,
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=500,
        enable_monitoring=True,
        enable_encryption=True,  # ← Enable encryption
    )

    await cache.connect()

    try:
        yield cache
    finally:
        try:
            await cache.clear()
            await cache.disconnect()
        except Exception as e:
            print(f"Warning: Cache cleanup failed: {e}")
```

**Pros:**
- ✅ Tests real encryption infrastructure
- ✅ Validates encryption key generation and usage
- ✅ Catches encryption-related integration bugs

**Cons:**
- ⚠️ Requires cryptography library
- ⚠️ Slightly slower due to encryption overhead

---

#### Option C: Patch encryption (if avoiding cryptography dependency)

**Best for:** Testing environments where cryptography library isn't available.

```python
from unittest.mock import patch

@pytest.fixture
async def ai_response_cache_patched_encryption(fakeredis_client, monkeypatch):
    """AIResponseCache with encryption patched for fakeredis."""

    # Set dummy encryption key (required by config validation)
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "dummy-key-for-patched-encryption")

    # Patch encryption to no-op for fakeredis
    with patch('app.infrastructure.cache.encryption.EncryptedCacheLayer.encrypt',
                side_effect=lambda x: x):
        with patch('app.infrastructure.cache.encryption.EncryptedCacheLayer.decrypt',
                    side_effect=lambda x: x):
            cache = AIResponseCache(
                redis_client=fakeredis_client,
                default_ttl=3600,
                enable_encryption=True,
                ...
            )
            await cache.connect()
            yield cache
```

**Pros:**
- ✅ No cryptography dependency needed
- ✅ Tests encryption code paths without actual encryption

**Cons:**
- ❌ Doesn't test real encryption behavior
- ❌ More complex mocking setup

---

#### Recommendation

**For text_processor integration tests:** Use **Option A** (disable encryption)
- Focus is on TextProcessorService + Cache collaboration
- Encryption is infrastructure concern, already tested in cache integration suite
- Keeps tests simple and fast

**If you need encryption testing:** Use **Option B** (proper test key)
- Follow cache integration test patterns
- See `backend/tests/integration/cache/test_cache_encryption.py` for examples

## Benefits Summary

Using AIResponseCache + fakeredis for integration tests provides:

1. More realistic testing - Production cache code, realistic Redis behavior
2. Better coverage - Tests L1 caching, compression, TTL expiration, monitoring
3. Still fast - No Docker overhead, all in-memory
4. Catches integration bugs - Cache key collisions, TTL misconfiguration, compression issues
5. Documents architecture - Clear separation between unit (isolation) and integration (collaboration)
6. Enables future enhancements - Easy to add new cache features and test them

While maintaining:
- ✅ Fast test execution (no network calls)
- ✅ Perfect test isolation (fresh fakeredis per test)
- ✅ No external dependencies (no Docker required)
- ✅ Deterministic behavior (no timing issues)

## Questions to Consider

1. Do we need encryption in integration tests?
  - If yes: Use Option B (patch encryption)
  - If no: Use Option A (disable encryption) - simpler
2. Should we keep some tests in unit suite?
  - Yes - Keep basic "did we call cache?" tests in unit suite
  - Move complex "how does cache behave?" tests to integration suite
3. Test execution time?
  - fakeredis adds ~5-10ms per test vs FakeCache
  - Total suite impact: ~0.5 seconds for 22 tests
  - Still acceptable for CI/CD