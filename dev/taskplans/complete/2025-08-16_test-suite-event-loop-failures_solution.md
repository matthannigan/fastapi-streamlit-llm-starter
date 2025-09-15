# Test Suite Event Loop Solution

## Critique and Verification of Analysis

Your root cause analysis is spot on. The problem is a classic side effect of combining three things:

1.  **A Global Singleton:** The `ai_resilience = AIServiceResilience()` instance in `backend/app/infrastructure/resilience/orchestrator.py`.
2.  **Import-Time Execution:** This instance is created the moment any module imports `orchestrator.py` or a module that imports it (like `resilience/__init__.py` or `services/text_processor.py`).
3.  **Async Test Frameworks:** `pytest-asyncio` sets up and tears down event loops around tests, but if a module is imported *before* the test's event loop is active, any top-level async-related setup (like the one implicitly happening inside `AIServiceResilience`) can fail or conflict with the test runner's loop.

Running tests in a different order (which `pytest` often does) changes the import order, explaining why failures are inconsistent and often appear only during a full suite run. Your recommended next step—**lazy initialization**—is precisely the correct architectural solution.

Here is a concrete, step-by-step guide to implement this fix across your application.

-----

## Recommended Refactoring Plan

This plan will eliminate the import-time side effects, make the resilience service more testable, and align it better with FastAPI's dependency injection principles.

### Deliverable 1: Implement Lazy Initialization for the Resilience Service

First, modify the global singleton pattern to instantiate the service only when it's first needed.

**File:** `backend/app/infrastructure/resilience/orchestrator.py`

**Current Code (Problematic):**

```python
# ... imports ...
logger = logging.getLogger(__name__)

class AIServiceResilience:
    # ... class definition ...

# Global instance - initialize immediately to support decorators at import time
ai_resilience = AIServiceResilience() # <-- This runs on import!

# Convenience decorator functions
def with_operation_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for operation-specific resilience."""
    return ai_resilience.with_resilience(operation_name, fallback=fallback)
# ... other decorators ...
```

**Recommended Change (Lazy Initialization):**
Replace the direct instantiation with a getter function that uses a cached global instance.

```python
# ... imports ...
import threading
from typing import Optional, Callable
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIServiceResilience:
    # ... existing class definition ...

# --- REVISED LAZY INITIALIZATION PATTERN ---

_ai_resilience_instance: Optional[AIServiceResilience] = None
_lock = threading.Lock()

def get_resilience_service() -> AIServiceResilience:
    """
    Get the singleton instance of the resilience service, creating it if necessary.
    This function enables thread-safe lazy initialization.
    """
    global _ai_resilience_instance
    if _ai_resilience_instance is None:
        with _lock:
            # Double-checked locking to prevent race conditions
            if _ai_resilience_instance is None:
                _ai_resilience_instance = AIServiceResilience(settings=settings)
    return _ai_resilience_instance

def reset_resilience_service_for_testing():
    """
    Reset the singleton instance of the resilience service.
    This should ONLY be used in test environments to ensure isolation.
    """
    global _ai_resilience_instance
    with _lock:
        _ai_resilience_instance = None

# Convenience decorator functions (will be refactored in next step)
# ...
```

***Note:*** While this first change introduces the pattern, the decorators will still fail because they capture the `ai_resilience` variable at import time. The next step is crucial.

### Deliverable 2: Refactor Decorators to be Runtime-Aware

The convenience decorators (`@with_operation_resilience`, etc.) must be refactored to get the resilience service instance *when the decorated function is called*, not when the decorator is defined.

**File:** `backend/app/infrastructure/resilience/orchestrator.py`

**Current Decorator Code (Problematic):**

```python
def with_operation_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for operation-specific resilience."""
    # This captures `ai_resilience` at import time, when the loop might not exist
    return ai_resilience.with_resilience(operation_name, fallback=fallback)
```

**Recommended Change (Runtime Service Acquisition):**
Rewrite the convenience decorators to acquire the service instance at runtime and cache the dynamically created resilient function to optimize performance.

```python
from functools import wraps
from typing import Dict

# Cache for dynamically decorated functions to avoid re-creation on every call
_resilient_function_cache: Dict[Callable, Callable] = {}
_decorator_lock = threading.Lock()

def with_operation_resilience(operation_name: str, fallback: Optional[Callable] = None):
    """Global decorator for operation-specific resilience that acquires the service at runtime."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use a lock to ensure thread-safe access to the cache
            with _decorator_lock:
                # Check if the function has already been decorated and cached
                if func not in _resilient_function_cache:
                    # 1. Get the resilience service at runtime (lazy initialization)
                    service = get_resilience_service()
                    # 2. Apply the resilience decorator from the service instance
                    resilient_func = service.with_resilience(operation_name, fallback=fallback)(func)
                    # 3. Cache the decorated function
                    _resilient_function_cache[func] = resilient_func
            
            # 4. Execute the cached resilient function
            cached_func = _resilient_function_cache[func]
            return await cached_func(*args, **kwargs)
        return wrapper
    return decorator

# NOTE: This same runtime-aware and cached pattern must be applied to all other 
# convenience decorators: with_aggressive_resilience, with_balanced_resilience, 
# with_conservative_resilience, and with_critical_resilience.
```

This new pattern correctly defers the interaction with the `AIServiceResilience` instance until the decorated function is actually executed, completely resolving the event loop conflict.

### Deliverable 3: Establish Dependency Injection Provider

Create a formal dependency provider for the resilience service, allowing it to be injected into FastAPI endpoints and other services cleanly.

**File:** `backend/app/dependencies.py`

```python
# ... other imports
from app.infrastructure.resilience.orchestrator import AIServiceResilience, get_resilience_service as get_resilience_service_instance

# ... other providers
    
def get_resilience_service() -> AIServiceResilience:
    """
    Dependency provider for the AI resilience service.
    Uses the lazy-initialized singleton instance.
    """
    return get_resilience_service_instance()
```

### Deliverable 4: Refactor Direct Usage in Application Code

Replace all direct imports and usage of the old `ai_resilience` global instance with the new dependency injection pattern.

This makes dependencies explicit and testing far easier. The primary example is the health check.

**File:** `backend/app/api/v1/health.py` (Example)

**Current Direct Import:**

```python
# ...
from app.infrastructure.resilience import ai_resilience # Direct import of global instance
# ...
async def health_check():
    # ...
    try:
        resilience_healthy = ai_resilience.is_healthy()
    # ...
```

**Recommended Change:**

```python
# ...
from fastapi import Depends
from app.dependencies import get_resilience_service
from app.infrastructure.resilience.orchestrator import AIServiceResilience
# ...
async def health_check(resilience_service: AIServiceResilience = Depends(get_resilience_service)):
    # ...
    try:
        resilience_healthy = resilience_service.is_healthy()
    # ...
```

### Deliverable 5: Update Testing Strategy and Fixtures

Adapt the test suite to use app.dependency_overrides for mocking the resilience service, and create a fixture to reset the singleton between tests.

With the global singleton pattern replaced by dependency injection, your tests can become cleaner and more robust by using FastAPI's `dependency_overrides`.

**File:** `backend/tests/conftest.py` (or a relevant test file)

**Recommended New Pattern (Dependency Override):**

```python
import pytest
from unittest.mock import MagicMock
from app.main import app
from app.dependencies import get_resilience_service
from app.infrastructure.resilience.orchestrator import (
    AIServiceResilience, 
    reset_resilience_service_for_testing
)

@pytest.fixture(autouse=True)
def reset_singleton_services():
    """Fixture to reset singleton services before each test."""
    reset_resilience_service_for_testing()
    # Add other service resets here if needed

@pytest.fixture
def mock_resilience_service() -> MagicMock:
    """Provides a MagicMock replacement for the AIServiceResilience."""
    # Create a mock with the same interface as the real service
    mock_service = MagicMock(spec=AIServiceResilience)
    mock_service.is_healthy.return_value = True # Default mock behavior
    
    # Override the dependency for the app
    app.dependency_overrides[get_resilience_service] = lambda: mock_service
    
    yield mock_service
    
    # Clean up the override after the test
    del app.dependency_overrides[get_resilience_service]

# Example test using the new fixture
def test_health_check_with_mocked_resilience(client, mock_resilience_service):
    # Set the mock's behavior for this specific test
    mock_resilience_service.is_healthy.return_value = False

    response = client.get("/v1/health")
    data = response.json()

    assert data["resilience_healthy"] is False
```

### Deliverable 6: Document the New Pattern

Add documentation to `docs/guides/developer/CORE_MODULE_INTEGRATION.md` and the `orchestrator.py` module docstring explaining the lazy initialization pattern and the correct way to access and test the service.

## Summary of Benefits from this Refactor

By implementing these changes, you will gain:

1.  **Elimination of Event Loop Errors:** The root cause of the `RuntimeError` will be fixed by deferring service instantiation until an event loop is guaranteed to be running.
2.  **Improved Testability:** Using dependency injection makes mocking services for tests trivial and robust, eliminating the need for complex patching of global objects.
3.  **Better Architecture:** The application will better adhere to SOLID principles by making dependencies explicit and removing import-time side effects.
4.  **Increased Stability:** The codebase becomes more predictable, as the order of module imports will no longer affect the application's runtime behavior.