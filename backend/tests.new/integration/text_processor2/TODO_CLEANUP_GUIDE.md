# TODO(integration) Cleanup Guide

## Quick Summary

**Simple answer:** Most lines should be **DELETED**, a few need **REPLACEMENT**.

**Time estimate:** 15-30 minutes

---

## Pattern-by-Pattern Guide

### ❌ Pattern 1: DELETE - get_hit_count() / get_miss_count()

**What to delete:**
```python
# TODO(integration): Remove FakeCache metric - assert ai_response_cache.get_hit_count() == 1
# TODO(integration): Remove FakeCache metric - assert ai_response_cache.get_miss_count() == 1
# TODO(integration): Remove FakeCache metric - assert ai_response_cache.get_miss_count() >= 1
```

**Why?** AIResponseCache doesn't expose hit/miss counters. Integration tests verify cache behavior through responses, not internal metrics.

**What verifies cache hits/misses instead?**
```python
# Already in the test:
assert response.cache_hit is True   # Verifies cache hit
assert response.cache_hit is False  # Verifies cache miss
```

**Action:** **DELETE these lines entirely** (no replacement)

---

### ❌ Pattern 2: DELETE - Direct ._data access for length check

**What to delete:**
```python
# TODO(integration): Remove FakeCache metric - assert len(ai_response_cache._data) > 0
```

**Why?** AIResponseCache doesn't expose `._data`. This checked if cache stored something.

**What verifies storage instead?**
```python
# Option 1: Query the cache directly
cache_key = ai_response_cache.build_cache_key(
    text=request.text,
    operation=request.operation,
    options=request.options or {}
)
cached_value = await ai_response_cache.get(cache_key)
assert cached_value is not None  # Verifies cache stored the value

# Option 2: Just verify response says it cached
# (Most tests already do this - no additional assertion needed)
assert response.cache_hit is False  # First call stored to cache
```

**Action:** **DELETE these lines** - Storage is verified by subsequent cache hit tests

---

### 🔧 Pattern 3: REPLACE - Getting cache keys

**What to replace:**
```python
# TODO(integration): Remove FakeCache metric - cache_keys = list(ai_response_cache._data.keys())
# TODO(integration): Remove FakeCache metric - first_cache_keys = list(ai_response_cache._data.keys())
# TODO(integration): Remove FakeCache metric - all_cache_keys = list(ai_response_cache._data.keys())
```

**Why?** AIResponseCache doesn't expose `._data`, but it has `get_all_keys()` method.

**Replace with:**
```python
# Get all cache keys using real cache API
cache_keys = await ai_response_cache.get_all_keys()
```

**Action:** **REPLACE** `list(ai_response_cache._data.keys())` with `await ai_response_cache.get_all_keys()`

---

### ❌ Pattern 4: DELETE - get_stored_ttl()

**What to delete:**
```python
# TODO(integration): Remove FakeCache metric - stored_ttl = ai_response_cache.get_stored_ttl(cache_keys[0])
# TODO(integration): Remove FakeCache metric - Can verify via ai_response_cache.get_stored_ttl(cache_key) showing
```

**Why?** AIResponseCache doesn't expose `get_stored_ttl()`. TTL is internal to Redis.

**What verifies TTL instead?**
```python
# For integration tests, we verify TTL was passed during set():
# (This happens in the service code, no assertion needed in test)

# For TTL EXPIRATION testing (new tests to add later):
import time
await cache.set(key, value, ttl=1)  # 1 second TTL
time.sleep(2)  # Wait for expiration
result = await cache.get(key)
assert result is None  # TTL expired
```

**Action:** **DELETE these lines** - TTL storage tested implicitly, expiration tested separately

---

## Batch Cleanup Script

Instead of manual line-by-line editing, use this script:

```python
#!/usr/bin/env python3
"""Quick cleanup of TODO(integration) lines."""

import re
from pathlib import Path

def cleanup_todos(file_path: Path):
    content = file_path.read_text()
    original = content

    # Pattern 1 & 2 & 4: DELETE commented lines entirely
    patterns_to_delete = [
        r'\s*# TODO\(integration\):.*get_hit_count.*\n',
        r'\s*# TODO\(integration\):.*get_miss_count.*\n',
        r'\s*# TODO\(integration\):.*len\(ai_response_cache\._data\).*\n',
        r'\s*# TODO\(integration\):.*get_stored_ttl.*\n',
    ]

    for pattern in patterns_to_delete:
        content = re.sub(pattern, '', content)

    # Pattern 3: REPLACE ._data.keys() with get_all_keys()
    # Uncomment the line and fix it
    content = re.sub(
        r'\s*# TODO\(integration\):.*- (.*) = list\(ai_response_cache\._data\.keys\(\)\)',
        r'\1 = await ai_response_cache.get_all_keys()',
        content
    )

    if content != original:
        file_path.write_text(content)
        print(f"✅ Cleaned up {file_path}")
        return True
    else:
        print(f"ℹ️  No changes needed for {file_path}")
        return False

if __name__ == '__main__':
    file_path = Path(__file__).parent / 'text_processor_cache_integration.py'
    cleanup_todos(file_path)
```

Save as `cleanup_todos.py` and run:
```bash
python cleanup_todos.py
```

---

## Manual Cleanup Commands

### Option 1: View all TODO lines

```bash
grep -n "TODO(integration)" text_processor_cache_integration.py
```

### Option 2: Count how many to clean up

```bash
grep -c "TODO(integration)" text_processor_cache_integration.py
```

### Option 3: Delete by pattern (be careful!)

```bash
# Backup first!
cp text_processor_cache_integration.py text_processor_cache_integration.py.backup

# Delete get_hit_count lines
sed -i '' '/TODO(integration).*get_hit_count/d' text_processor_cache_integration.py

# Delete get_miss_count lines
sed -i '' '/TODO(integration).*get_miss_count/d' text_processor_cache_integration.py

# Delete len(._data) lines
sed -i '' '/TODO(integration).*len(ai_response_cache._data)/d' text_processor_cache_integration.py

# Delete get_stored_ttl lines
sed -i '' '/TODO(integration).*get_stored_ttl/d' text_processor_cache_integration.py
```

---

## Quick Decision Tree

```
Does the line have TODO(integration)?
│
├─ Contains "get_hit_count"?        → DELETE (verify via response.cache_hit)
├─ Contains "get_miss_count"?       → DELETE (verify via response.cache_hit)
├─ Contains "len(._data)"?          → DELETE (storage verified implicitly)
├─ Contains "get_stored_ttl"?       → DELETE (TTL is internal)
├─ Contains "list(._data.keys())"?  → REPLACE with "await .get_all_keys()"
└─ Other?                           → Review manually
```

---

## After Cleanup: Verify Tests Pass

```bash
cd ../../..  # Back to backend/

# Run all integration tests
../.venv/bin/python -m pytest tests/integration/text_processor/ -v

# Run specific test to verify
../.venv/bin/python -m pytest tests/integration/text_processor/text_processor_cache_integration.py::TestTextProcessorCachingStrategy::test_cache_hit_returns_cached_response_without_ai_call -v --tb=short
```

---

## Summary

| Pattern | Action | Count | Replacement |
|---------|--------|-------|-------------|
| `get_hit_count()` | DELETE | ~3 | Already verified via `response.cache_hit` |
| `get_miss_count()` | DELETE | ~4 | Already verified via `response.cache_hit` |
| `len(._data)` | DELETE | ~3 | Storage verified implicitly |
| `get_stored_ttl()` | DELETE | ~2 | TTL is internal |
| `list(._data.keys())` | REPLACE | ~8 | `await .get_all_keys()` |

**Total TODO lines:** ~20
**Time to clean:** 15-30 minutes (or 2 minutes with script)

---

## Recommended Approach

**Option A: Use the cleanup script (2 minutes)**
```bash
# Create cleanup_todos.py from the script above
python cleanup_todos.py
```

**Option B: Manual sed commands (5 minutes)**
```bash
# Backup + delete patterns
cp text_processor_cache_integration.py text_processor_cache_integration.py.backup
sed -i '' '/TODO(integration).*get_hit_count/d' text_processor_cache_integration.py
sed -i '' '/TODO(integration).*get_miss_count/d' text_processor_cache_integration.py
sed -i '' '/TODO(integration).*len(ai_response_cache._data)/d' text_processor_cache_integration.py
sed -i '' '/TODO(integration).*get_stored_ttl/d' text_processor_cache_integration.py
# Manually fix the ._data.keys() → get_all_keys() lines (8 lines)
```

**Option C: Manual editor search/replace (15-30 minutes)**
- Search for each pattern
- Delete or replace according to guide above
