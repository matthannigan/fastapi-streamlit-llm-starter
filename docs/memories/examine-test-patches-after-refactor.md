# Post-Refactoring Test Patch Issues

## Issue Description

After refactoring a monolithic module into submodules, tests that use `unittest.mock.patch()` may fail with `AttributeError` even when the refactored code has proper backward-compatible exports in `__init__.py`.

**Root Cause**: `patch()` works on actual object locations, not import references. Convenience exports create references but don't change where the original objects live.

## Example Scenario

**Before refactoring** (`app/core/environment.py`):
```python
# Single file with everything
environment_detector = EnvironmentDetector()
logger = logging.getLogger(__name__)

def get_environment_info():
    return environment_detector.detect_with_context()
```

**After refactoring**:
- `app/core/environment/api.py` - Contains `environment_detector` and `get_environment_info()`
- `app/core/environment/detector.py` - Contains `logger` and detector class
- `app/core/environment/__init__.py` - Re-exports everything for backward compatibility

**Test patches that break**:
```python
# These fail after refactoring even with __init__.py exports
patch('app.core.environment.environment_detector')  # Now in api.py
patch('app.core.environment.logger')                # Now in detector.py
patch('app.core.environment.get_environment_info')  # Now in api.py
```

## Quick Fix Guide for Coding Assistants

### 1. Identify Broken Patches
Look for `AttributeError` messages like:
```
AttributeError: <module 'app.core.environment'> does not have the attribute 'logger'
```

### 2. Find the Actual Object Location
```bash
# Search for where the object is actually defined
grep -r "logger = " app/core/environment/
grep -r "environment_detector = " app/core/environment/
grep -r "def get_environment_info" app/core/environment/
```

### 3. Update Patch Targets
```python
# Before (broken)
patch('app.core.environment.logger')
patch('app.core.environment.environment_detector')
patch('app.core.environment.get_environment_info')

# After (fixed)
patch('app.core.environment.detector.logger')
patch('app.core.environment.api.environment_detector')
patch('app.core.environment.api.get_environment_info')
```

### 4. Verify the Fix
- Run the specific failing test
- Run the full test suite for that module
- Search for other files with similar patterns: `find tests -name "*.py" -exec grep -l "patch.*app\.core\.environment" {} \;`

## Prevention

When doing module refactoring, immediately search for and update all test patches:
```bash
grep -r "patch.*module\.path" tests/
```

Remember: **Exports help users, not mocks**. The mock must patch where the code actually looks for the object.