# Quick Start: Running the Migration Script

## TL;DR

```bash
# From backend/tests/integration/text_processor/ directory:

# 1. Preview changes (recommended first step)
python migrate_integration_tests.py --dry-run

# 2. Apply changes
python migrate_integration_tests.py

# 3. Manual cleanup (see below)

# 4. Run tests
cd ../../../  # Back to backend directory
../.venv/bin/python -m pytest tests/integration/text_processor/ -v
```

---

## Step-by-Step Guide

### Step 1: Review Analysis (DONE - Already created!)

✅ Read `MIGRATION_ANALYSIS.md` for complete fixture mapping and decisions

**Key Points:**
- Most unit test fixtures replaced with integration fixtures
- `mock_pydantic_agent` kept (no API keys needed)
- Real `AIResponseCache` instead of `FakeCache`
- All new fixtures already added to `conftest.py`

---

### Step 2: Preview Changes (DRY RUN)

```bash
cd backend/tests/integration/text_processor/

# See what would be changed WITHOUT modifying files
python migrate_integration_tests.py --dry-run
```

**What to look for:**
- ✅ `fake_cache` → `ai_response_cache` replacements
- ✅ `fake_cache_with_hit` → `ai_response_cache_with_data` replacements
- ✅ Helper function parameter updates
- ⚠️ Commented lines with `TODO(integration)` - these need manual review

---

### Step 3: Run Migration Script

```bash
# Apply all automated changes
python migrate_integration_tests.py
```

**Script will automatically:**
- ✅ Replace fixture parameters
- ✅ Update variable names in test bodies
- ✅ Update helper function signatures
- ✅ Comment out FakeCache-specific metrics
- ✅ Update module docstring

**Script output shows:**
```
================================================================================
Processing: text_processor_cache_integration.py
================================================================================

✅ File updated successfully!

📊 Changes Summary:
   - 157 total changes

📝 Detailed Changes:
   Line 53:
      - fake_cache → ai_response_cache
   ...
```

---

### Step 4: Manual Cleanup Required

The script comments lines that need manual attention:

#### 4a. Remove FakeCache Metrics

Find lines marked with `# TODO(integration)`:

```bash
grep -n "TODO(integration)" text_processor_cache_integration.py
```

**Remove these patterns:**

```python
# ❌ Remove - FakeCache specific
# TODO(integration): Remove FakeCache metric - assert fake_cache.get_hit_count() == 1
# TODO(integration): Remove FakeCache metric - assert fake_cache.get_miss_count() == 1
# TODO(integration): Remove FakeCache metric - assert len(fake_cache._data) > 0
# TODO(integration): Remove FakeCache metric - stored_ttl = fake_cache.get_stored_ttl(key)
```

**Why?** `AIResponseCache` doesn't expose `.get_hit_count()` or `._data` - these are FakeCache testing helpers.

**What to do instead:**
- For cache hit verification: Check `response.cache_hit == True`
- For cache miss verification: Check `response.cache_hit == False`
- For cache storage verification: Query cache with `await cache.get(key)` and check it's not None

#### 4b. Update Test Docstrings

Add "Integration Scope" section to each test:

**Template:**

```python
async def test_cache_hit_returns_cached_response_without_ai_call(
    self, test_settings, ai_response_cache_with_data, mock_pydantic_agent
):
    """
    Integration Test: Cache hit returns cached response without AI call.

    Integration Scope:
        TextProcessorService + AIResponseCache collaboration
        Tests real cache lookup behavior with production cache implementation.

    Production Behaviors Tested:
        - Real cache key generation algorithm
        - L1 cache lookup before L2 (Redis)
        - Cache hit detection and metadata
        - Response deserialization from cache

    Business Impact:
        Reduces AI API costs and improves response times by serving cached
        responses for repeated requests without AI service calls.

    Verifies:
        When cache contains response for request, process_text() returns
        cached response immediately without invoking AI agent.
    """
```

---

### Step 5: Run Tests

```bash
# From backend/ directory
cd ../../..  # Or cd to backend/

# Run all text_processor integration tests
../.venv/bin/python -m pytest tests/integration/text_processor/ -v

# Run specific test file
../.venv/bin/python -m pytest tests/integration/text_processor/text_processor_cache_integration.py -v --tb=short

# Run with coverage
../.venv/bin/python -m pytest tests/integration/text_processor/ --cov=app.services.text_processor --cov-report=term-missing
```

---

## What to Expect After Migration

### Tests Should:
- ✅ Use real `AIResponseCache` with fakeredis
- ✅ Test production cache key generation
- ✅ Test L1 + L2 caching layers
- ✅ Test cache TTL storage (not expiration yet)
- ✅ Maintain fast execution (~same speed as unit tests)
- ✅ Keep mocked AI agent (no API keys needed)

### Tests Will NOT (Yet):
- ❌ Test TTL expiration behavior (add new tests for this)
- ❌ Test L1 cache effectiveness (add new tests for this)
- ❌ Test compression thresholds (add new tests for this)
- ❌ Test real AI agent integration (E2E tests only)

---

## Troubleshooting

### Issue: "fixture 'ai_response_cache' not found"

**Solution:** Fixtures are in `conftest.py` which is already created with all needed fixtures.

### Issue: "fixture 'test_settings' not found"

**Solution:** Import from cache integration conftest:
```bash
# Verify test_settings exists
grep -n "def test_settings" tests/integration/cache/conftest.py
```

The fixture should be available via pytest fixture discovery.

### Issue: Tests fail with "AttributeError: 'AIResponseCache' object has no attribute 'get_hit_count'"

**Solution:** Remove the FakeCache metric lines:
```bash
# Find all instances
grep -n "get_hit_count\|get_miss_count\|get_stored_ttl\|._data\|._ttls" text_processor_cache_integration.py

# Remove or comment out those assertions
```

### Issue: Tests are slow

**Checklist:**
- ✅ Using `fakeredis` not real Redis? (should be in conftest.py)
- ✅ Tests are function-scoped? (each test gets fresh cache)
- ✅ No Docker containers starting? (fakeredis is in-memory)

Expected performance: ~same as unit tests (0.1-0.5s per test)

---

## Next Steps After Migration

### Phase 1: Get Tests Passing ✅
1. Run migration script
2. Remove FakeCache metrics
3. Verify all tests pass

### Phase 2: Enhance with Integration-Only Tests
4. Add TTL expiration tests (FakeCache couldn't test this)
5. Add L1 cache effectiveness tests
6. Add compression threshold tests
7. Add monitoring callback tests

See `UPGRADE_UNIT_TESTS.md` Phase 3 for examples.

### Phase 3: Update Documentation
8. Update test docstrings with Integration Scope
9. Update class docstrings
10. Document production behaviors tested

---

## Quick Commands Reference

```bash
# Preview migration
python migrate_integration_tests.py --dry-run

# Run migration
python migrate_integration_tests.py

# Find FakeCache metrics to remove
grep -n "get_hit_count\|get_miss_count\|._data\|get_stored_ttl" text_processor_cache_integration.py

# Find TODO comments
grep -n "TODO(integration)" text_processor_cache_integration.py

# Run tests (from backend/)
../.venv/bin/python -m pytest tests/integration/text_processor/ -v

# Run single test
../.venv/bin/python -m pytest tests/integration/text_processor/text_processor_cache_integration.py::TestTextProcessorCachingStrategy::test_cache_hit_returns_cached_response_without_ai_call -v --tb=short
```

---

## Summary

✅ **Fixtures ready** - All fixtures added to `conftest.py`
✅ **Script ready** - Automated migration handles 80% of work
⚠️ **Manual cleanup** - Remove FakeCache metrics, update docstrings
✅ **Tests should pass** - With manual cleanup, all tests should work
🚀 **Ready to enhance** - Add integration-only tests afterward

**Time estimate:**
- Run script: 1 minute
- Manual cleanup: 30-60 minutes
- Enhanced tests: 2-4 hours
