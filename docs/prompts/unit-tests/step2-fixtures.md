### Fixture Generation Prompt for Coding Assistant

**Objective**

Your goal is to create high-quality, reusable Pytest fixtures for the **external dependencies** of the modules within `[path_to_component]`. These fixtures will be used to test each module's behavior while isolating it from systems outside its component boundary.

The public contracts of the modules currently being reviewed are:

  * `path_to_module1.pyi`
  * `path_to_module2.pyi`
  * `path_to_module3.pyi`

### **Guiding Philosophy: Prefer Fakes, Mock at Boundaries**

Our testing strategy treats an entire component (e.g., `[component.address.dot.notation]`) as the Unit Under Test (UUT). This means we mock only at true **system boundaries**.

Crucially, we prefer creating simple, in-memory **Fakes** over using `MagicMock` whenever possible. A "Fake" is a lightweight, working implementation of a dependency's contract that provides more realistic behavior than a mock. Mocks should only be used when a Fake is not practical.

### **Your Role: Test Dependency Specialist**

You are an expert in our testing philosophy and creating test doubles (Fakes and Mocks) that enable robust, behavior-driven testing. Before beginning, review these critical guides:

  * **`docs/guides/testing/UNIT_TESTS.md`** - Unit testing philosophy, principles, and the 5-step test generation process
  * **`docs/guides/testing/MOCKING_GUIDE.md`** - Decision framework for Fakes vs Mocks, boundary identification, and anti-patterns
  * **`docs/guides/testing/WRITING_TESTS.md`** - Docstring-driven test development and test structure patterns

Your task is to analyze a module's dependencies and create the necessary fixtures to isolate it for testing.

### **Core Task**

Create a todo list and track your progress.

For each module listed above:

1.  **Analyze Dependencies**: Review its public contract to identify all its direct dependencies (classes it imports, inherits from, or receives as arguments).
2.  **Define the Boundary**: A dependency is "external" if it is located **outside** the `[path_to_component]` directory. Anything inside this directory is part of the UUT and **must not** be mocked or faked.
3.  **Review Existing Fixtures**: Check `backend/tests/conftest.py`, `backend/tests/unit/conftest.py`, and `backend/tests/unit/[component]/conftest.py` to see if a suitable fixture already exists.
4.  **Decide: Fake or Mock?**: For each new external dependency, first determine if a simple, in-memory "Fake" is feasible. If not, create a `MagicMock`-based fixture.
5.  **Implement and Place Fixture**: Create the new fixture in the module-specific `conftest.py` at `backend/tests/unit/[component]/[module]/conftest.py`.
6.  **Placeholder `conftest.py` If None**: If there are no new module-specific fixtures, add placeholder text to `backend/tests/unit/[component]/[module]/conftest.py` like in the example of `backend/tests/unit/cache/dependencies/conftest.py`.

### **Critical Rules & Constraints**

1.  **Fakes \> Mocks**: Always prefer creating a Fake if the dependency's behavior is simple enough to simulate (e.g., stateful storage, simple transformations).
2.  **Strict Boundaries**: Only create fixtures for dependencies outside the `[component.address.dot.notation]` namespace.
3.  **"No-Lies" Mocks**: All `MagicMock`-based fixtures **MUST** use `spec=True` against the real class to ensure they accurately reflect the dependency's interface. Use `AsyncMock` for `async` methods.
4.  **Happy Path Only**: Fixtures must only provide default "happy path" behavior. Individual tests are responsible for configuring error conditions or specific edge cases.
5.  **Document Everything**: Every new fixture must have a comprehensive docstring explaining its purpose, behavior, and whether it's stateful, as outlined in `docs/guides/developer/DOCSTRINGS_TESTS.md`.
6.  **NEVER Mock Custom Exceptions**: Exception classes from `app.core.exceptions` are part of the application's public contract and should **NEVER** be mocked. Tests verify that the correct exceptions are raised per the component's docstring contract. See the detailed guidance below.

### **Example Implementation**

You can reference `backend/tests/unit/auth/conftest.py` as an example implementation for the `auth` module defined by the public contract at `backend/contracts/infrastructure/security/auth.pyi`.

-----

### **Implementation Guidelines**

#### **Creating Fakes (Preferred)**

A Fake is a real class that implements the dependency's interface in a lightweight way.

  * **Use Case**: Ideal for stateful dependencies (like a cache or a repository) or services with simple logic.
  * **Implementation**: Create a class that has the same public methods as the real dependency's contract. For stateful fakes, use an in-memory object like a dictionary to store state.

*Example of a Stateful Fake Cache Fixture:*

```python
# in conftest.py
@pytest.fixture
def fake_stateful_cache():
    """Provides a fake, in-memory cache for testing."""
    class FakeCache:
        def __init__(self):
            self._data = {}
        async def get(self, key: str):
            return self._data.get(key)
        async def set(self, key: str, value: Any):
            self._data[key] = value
    return FakeCache()
```

#### **Creating Mocks (Fallback)**

Use a mock when a Fake is too complex (e.g., simulating a third-party API client).

  * **Use Case**: For complex, stateless dependencies or when you only need to verify that a method was called.
  * **Implementation**: Use `unittest.mock.MagicMock` or `AsyncMock` with `spec=True`. Configure a default `return_value` that aligns with the "happy path" specified in the dependency's public contract.

*Example of a Spec'd Mock Fixture:*

```python
# in conftest.py
from unittest.mock import MagicMock, create_autospec
from some.external.dependency import ExternalApiClient

@pytest.fixture
def mock_external_api_client():
    """Provides a spec'd mock for the ExternalApiClient."""
    # create_autospec is a convenient way to create a spec'd mock
    mock = create_autospec(ExternalApiClient, instance=True)
    mock.make_request.return_value = {"status": "success", "data": {}}
    return mock
```

---

### **Rule: NEVER Mock Custom Exception Classes**

Custom exceptions from `app.core.exceptions` (such as `ValidationError`, `ConfigurationError`, `InfrastructureError`, `TransientAIError`, etc.) are **part of the application's public contract** and should **NEVER** be mocked in test fixtures.

Exception types appear in the `Raises:` section of docstrings and define the component's documented behavior. Tests verify that components raise the correct exceptions as specified in their contracts.

Custom exceptions are defined within `app/core/exceptions.py` as part of the application codebase. They are **not external dependencies** that cross system boundaries.

#### **What TO DO: Use Real Exception Classes**

```python
# ✅ CORRECT: Use real exception classes in tests
from app.core.exceptions import ValidationError, InfrastructureError

def test_service_raises_validation_error():
    """Test service raises ValidationError for empty input per docstring."""
    service = ProcessingService()

    # Use REAL exception class to verify contract
    with pytest.raises(ValidationError, match="Input cannot be empty"):
        service.process("")
```

#### **What NOT TO DO: Mock Exception Classes**

```python
# ❌ WRONG: Never mock exception classes
@pytest.fixture
def mock_validation_error(mocker):
    """DO NOT DO THIS - mocks the exception class itself"""
    return mocker.patch('app.core.exceptions.ValidationError')

# ❌ WRONG: Never mock exception instances
@pytest.fixture
def fake_exceptions():
    """DO NOT DO THIS - creates fake exception instances"""
    class FakeValidationError(Exception):
        pass
    return {"ValidationError": FakeValidationError}
```

#### **When Exception Mocking IS Acceptable**

There are **two specific scenarios** where mocking exception-related behavior is appropriate:

**Scenario 1: Mocking Exception Classification Functions**

When testing resilience logic that **uses** exception classification (not the exceptions themselves):

```python
# ✅ ACCEPTABLE: Mock the classification function (not the exceptions)
@pytest.fixture
def mock_classify_ai_exception():
    """
    Mock classify_ai_exception function to isolate retry decision logic.

    This tests how retry logic RESPONDS to classification results,
    not the classification implementation itself.
    """
    mock = Mock(spec=callable)
    # Configure default behavior - tests can override
    mock.return_value = True  # Default: exception is retryable
    return mock

def test_retry_respects_classification(mock_classify_ai_exception):
    """Test retry logic respects exception classification results."""
    mock_classify_ai_exception.return_value = False  # Non-retryable

    # Use REAL exception, but mock classification function
    failing_op = Mock(side_effect=ValidationError("bad input"))

    with pytest.raises(ValidationError):
        retry_with_classification(failing_op, mock_classify_ai_exception)

    # Should fail immediately without retries
    assert failing_op.call_count == 1
```

**Scenario 2: Mocking Exception Routing/Orchestration Logic**

When testing how orchestrators **route or handle different exception types** (testing decision logic, not exception validation):

```python
# ✅ ACCEPTABLE: Mock exception types for testing routing decisions
@pytest.fixture
def mock_exception_router():
    """
    Mock exception type classification for testing orchestrator routing.

    This tests orchestrator DECISION LOGIC about which policy to apply,
    not whether exceptions are raised correctly.
    """
    class MockExceptionInfo:
        def __init__(self, exc_type: str, severity: str):
            self.type = exc_type
            self.severity = severity

    return {
        "timeout": MockExceptionInfo("TimeoutError", "high"),
        "auth": MockExceptionInfo("AuthError", "critical"),
    }

def test_orchestrator_applies_correct_policy(mock_exception_router):
    """Test orchestrator selects appropriate resilience policy per exception type."""
    orchestrator = ResilienceOrchestrator()

    # Testing ROUTING logic with mock exception info
    policy = orchestrator.get_policy_for_exception(mock_exception_router["timeout"])
    assert policy.max_retries == 3  # High-severity timeout policy
```

**Key Principle**: Mock **functions that process exceptions**, not **the exceptions themselves**.
