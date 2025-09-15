# Summary of Test Suite Event Loop Issues

## The Problem
After the recent resilience service refactoring, the test suite is experiencing widespread RuntimeError: There is no current event loop in thread 'MainThread' errors. While individual test files often run successfully, running the full test suite triggers numerous event loop conflicts.

## Root Cause Analysis

1. **Global Singleton Pattern**: The resilience service uses a global singleton (ai_resilience) that's initialized at module import time, potentially before pytest has properly set up async test environments.
2. **Auto-patching Issue**: The patch_global_resilience fixture was originally set with autouse=True, meaning it was automatically applied to ALL tests, including those that don't need resilience functionality. This caused event loop lifecycle conflicts in unrelated async tests.
3. **Import-time Side Effects**: The global ai_resilience instance is created during module import, which can interfere with pytest's async fixture setup and event loop management.

## What We've Tried

1. Removed autouse=True from the patch_global_resilience fixture to make patching opt-in rather than automatic. This helped reduce errors in some isolated test runs.
2. Updated specific test files to explicitly use the patch_global_resilience fixture where needed (e.g., test_resilience.py, test_text_processing.py).
3. Verified pytest configuration - asyncio_mode = auto is correctly set in pytest.ini, which should handle async test discovery and event loop creation.

## Current Status

- Partial Success: Individual test files or small groups often run without errors
- Full Suite Still Failing: Running the complete test suite still produces many event loop errors
- Inconsistent Behavior: Some tests work in isolation but fail when run as part of the full suite

## Options for Further Investigation

1. **Lazy Initialization of Global Singleton**
- Modify the resilience service to use lazy initialization instead of creating the global instance at import time
- Use a factory pattern or getter function that creates the instance only when first accessed
2. **Event Loop Fixture Enhancement**
- Create a more robust event loop fixture that ensures a fresh event loop for each test
- Consider using pytest-asyncio's event_loop_policy fixture to better control loop creation
3. **Test Isolation Improvements**
- Add explicit event loop cleanup in test teardown
- Use asyncio.set_event_loop(None) after each test to ensure clean state
- Consider running resilience-related tests in a separate test session
4. **Module-Level Import Deferral**
- Defer imports of modules that create the global resilience instance
- Use local imports within test functions instead of module-level imports
5. **Context Manager Approach**
- Wrap resilience service usage in a context manager that properly manages event loop lifecycle
- Ensure proper cleanup even when tests fail
6. **Parallel Test Execution Issues**
- Investigate if pytest-xdist parallel execution is contributing to the problem
- Try running tests with -n 0 to disable parallelization and see if errors persist
7. **Fixture Scope Analysis**
- Review all fixtures using scope="session" or scope="module" that might be holding onto event loops
- Consider changing the event_loop fixture scope or creating test-specific loop fixtures

## Recommended Next Steps

1. **Immediate**: Focus on lazy initialization of the global resilience singleton to prevent import-time side effects
2. **Short-term**: Enhance event loop management in tests with explicit setup/teardown
3. **Long-term**: Consider refactoring away from the global singleton pattern in favor of dependency injection, which would make the system more testable and avoid these types of conflicts

The core issue appears to be the interaction between the global singleton pattern, import-time initialization, and pytest's async test management. A comprehensive solution will likely require addressing the architectural pattern rather than just patching the symptoms.