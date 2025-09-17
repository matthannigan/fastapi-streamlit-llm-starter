### Fixture Generation Prompt for Coding Assistant

**Objective**

Your goal is to create high-quality, reusable Pytest fixtures for the **external dependencies** of the modules within `backend/app/infrastructure/[component]/`. These fixtures will be used to test each module's behavior while isolating it from systems outside its component boundary.

The modules currently being reviewed are:

  * `module1.py`
  * `module2.py`
  * `module3.py`

### **Guiding Philosophy: Prefer Fakes, Mock at Boundaries**

Our testing strategy treats an entire component (e.g., `cache`) as the Unit Under Test (UUT). This means we mock only at true **system boundaries**.

Crucially, we prefer creating simple, in-memory **Fakes** over using `MagicMock` whenever possible. A "Fake" is a lightweight, working implementation of a dependency's contract that provides more realistic behavior than a mock. Mocks should only be used when a Fake is not practical.

### **Your Role: Test Dependency Specialist**

You are an expert in creating test doubles (Fakes and Mocks) that enable robust, behavior-driven testing. Your task is to analyze a module's dependencies and create the necessary fixtures to isolate it for testing.

### **Core Task**

For each module listed above:

1.  **Analyze Dependencies**: Review its public contract at `backend/contracts/infrastructure/[component]/[module].pyi` to identify all its direct dependencies (classes it imports, inherits from, or receives as arguments).
2.  **Define the Boundary**: A dependency is "external" if it is located **outside** the `backend/app/infrastructure/[component]/` directory. Anything inside this directory is part of the UUT and **must not** be mocked or faked.
3.  **Review Existing Fixtures**: Check `backend/tests/infrastructure/[component]/conftest.py` to see if a suitable fixture already exists.
4.  **Decide: Fake or Mock?**: For each new external dependency, first determine if a simple, in-memory "Fake" is feasible. If not, create a `MagicMock`-based fixture.
5.  **Implement and Place Fixture**: Create the new fixture in the module-specific `conftest.py` at `backend/tests/infrastructure/[component]/[module]/conftest.py`.

### **Critical Rules & Constraints**

1.  **Fakes \> Mocks**: Always prefer creating a Fake if the dependency's behavior is simple enough to simulate (e.g., stateful storage, simple transformations).
2.  **Strict Boundaries**: Only create fixtures for dependencies outside the `app.infrastructure.[component]` namespace.
3.  **"No-Lies" Mocks**: All `MagicMock`-based fixtures **MUST** use `spec=True` against the real class to ensure they accurately reflect the dependency's interface. Use `AsyncMock` for `async` methods.
4.  **Happy Path Only**: Fixtures must only provide default "happy path" behavior. Individual tests are responsible for configuring error conditions or specific edge cases.
5.  **Document Everything**: Every new fixture must have a comprehensive docstring explaining its purpose, behavior, and whether it's stateful, as outlined in `DOCSTRINGS_TESTS.md`.

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