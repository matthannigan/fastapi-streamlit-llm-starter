# Typecheck Error Fix Guide

## Summary of Errors

Your mypy errors fall into 3 categories:

1. **Import-untyped** (4 errors) - Missing type stubs
2. **No-untyped-def** (32 errors) - Missing function type annotations
3. **Union-attr** (6 errors) - Type narrowing issues in batch test

---

## Quick Fix (Recommended)

### Option 1: Add `# type: ignore` to entire test file

**Fastest solution** - Tests don't require strict typing:

Add this at the top of the file (line 1):
```python
# type: ignore[import-untyped, no-untyped-def, union-attr]
"""Integration tests for TextProcessorService + AIResponseCache collaboration.
```

**Pros:**
- ✅ 1 line change
- ✅ Standard practice for test files
- ✅ Focuses typing effort on production code

**Cons:**
- ❌ Disables ALL type checking for this file

---

### Option 2: Configure mypy to skip integration tests

**Better project-wide solution:**

In `backend/pyproject.toml` or `backend/mypy.ini`:

```ini
[tool.mypy]
# ... existing config ...

[[tool.mypy.overrides]]
module = "tests.integration.*"
ignore_errors = true
```

**Pros:**
- ✅ Applies to all integration tests
- ✅ Production code still fully typed
- ✅ Standard practice

---

### Option 3: Fix each error individually

**Most thorough but time-consuming:**

Use the script I created:
```bash
cd tests/integration/text_processor/
python fix_typechecks.py --dry-run  # Preview
python fix_typechecks.py            # Apply
```

**Or manual fixes below...**

---

## Manual Fix Guide (If You Want Full Typing)

### Fix 1: Import-untyped Errors (4 lines)

**Add `# type: ignore[import-untyped]` to imports:**

```python
# Line 23
from app.infrastructure.cache.redis_ai import AIResponseCache  # type: ignore[import-untyped]

# Line 28
from app.services.text_processor import TextProcessorService  # type: ignore[import-untyped]

# Line 29
from app.schemas import TextProcessingRequest, TextProcessingOperation  # type: ignore[import-untyped]

# Line 185 (if exists)
from app.infrastructure.ai import PromptSanitizer  # type: ignore[import-untyped]
```

**Why?** These modules don't have type stubs (`.pyi` files or `py.typed` marker).

---

### Fix 2: No-untyped-def Errors (32 functions)

**Add `-> None:` to all async test functions:**

```python
# Before
async def test_cache_hit_returns_cached_response_without_ai_call(self, test_settings, ...):

# After
async def test_cache_hit_returns_cached_response_without_ai_call(self, test_settings, ...) -> None:
```

**Batch replace with sed:**
```bash
# Backup first
cp text_processor_cache_integration.py text_processor_cache_integration.py.backup

# Add -> None to all async def test_ functions
sed -i '' 's/\(async def test_[^(]*([^)]*)\):/\1 -> None:/g' text_processor_cache_integration.py
```

**Also fix the helper function (line 32):**
```python
# Before
def _create_text_processor_with_mock_agent(test_settings, ai_response_cache, mock_pydantic_agent):

# After
from typing import Any  # Add to imports

def _create_text_processor_with_mock_agent(
    test_settings: Any,
    ai_response_cache: Any,
    mock_pydantic_agent: Any
) -> TextProcessorService:
```

---

### Fix 3: Union-attr Errors (6 errors in batch test)

**Problem:** Lines 1346-1351 access attributes on objects that mypy thinks might be `BaseException`.

**Find the batch processing test around line 1340:**

```python
# Add this comment before the for loop that accesses response.result, etc.
# Type narrowing: responses are TextProcessingResponse, not BaseException

# Or add type: ignore to specific lines:
assert all(r.result for r in responses)  # type: ignore[union-attr]
assert all(r.cache_hit is False for r in responses)  # type: ignore[union-attr]
```

---

## Recommended Approach

**For integration tests, I recommend Option 1 or 2** (ignore typing in tests).

### Why?

1. **Test files don't need strict typing** - Focus should be on test logic, not types
2. **Standard practice** - Most projects skip strict typing for tests
3. **Production code still typed** - Your service and infrastructure code keeps full typing
4. **Less maintenance** - Test fixtures change frequently, typing them is overhead

### Implementation

**Add to top of file:**
```python
# type: ignore[import-untyped, no-untyped-def, union-attr]
"""Integration tests for TextProcessorService + AIResponseCache collaboration.
```

**Or add to mypy config:**
```ini
# backend/pyproject.toml
[[tool.mypy.overrides]]
module = "tests.integration.*"
ignore_errors = true
```

---

## Validation

After applying fixes:

```bash
# Check mypy errors
mypy tests/integration/text_processor/text_processor_cache_integration.py

# Should show 0 errors if Option 1/2, or all errors fixed if Option 3

# Verify tests still work
pytest tests/integration/text_processor/ -v
```

---

## Files Created

- ✅ `fix_typechecks.py` - Automated fixing script (Option 3)
- ✅ `TYPECHECK_FIX_GUIDE.md` - This guide (all options)

---

## My Recommendation

```python
# Add this single line at the top of text_processor_cache_integration.py
# type: ignore[import-untyped, no-untyped-def, union-attr]
```

**Reasoning:**
- ✅ Quick (1 line)
- ✅ Standard practice for test files
- ✅ Keeps production code fully typed
- ✅ Tests still run perfectly
- ✅ Focuses effort where it matters

**Then run:**
```bash
mypy tests/integration/text_processor/text_processor_cache_integration.py
# Should show 0 errors

pytest tests/integration/text_processor/ -v
# All tests should pass
```
