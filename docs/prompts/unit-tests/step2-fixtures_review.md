You are a senior software engineer specializing in writing maintainable, scalable, behavior-driven tests. First, read `@docs/guides/testing/WRITING_TESTS.md` and 
`@docs/guides/testing/UNIT_TESTS.md `. Summarize the 3 most important principles and the 3 most important anti-patterns from the documents.

Then, review the fixtures created at `backend/tests/unit/resilience /conftest.py` and `backend/tests/unit/resilience/**/conftest.py` and assess the quality of the creation 
of resuable testing fixtures for the `app.infrastructure.resilience` component. We analyzed the dependencies of each module in `resilience` and created the necessary fixtures to isolate it for testing.

The prompt for fixtures generation was:

````markdown
### **Guiding Philosophy: Prefer Fakes, Mock at Boundaries**

Our testing strategy treats an entire component (e.g., `app.infrastructure.resilience`) as the Unit Under Test (UUT). This means we mock only at true **system boundaries**.

Crucially, we prefer creating simple, in-memory **Fakes** over using `MagicMock` whenever possible. A "Fake" is a lightweight, working implementation of a dependency's contract that provides more realistic behavior than a mock. Mocks should only be used when a Fake is not practical.

We analyzed the dependencies of each module in `app.infrastructure.resilience` and created the necessary fixtures to isolate it for testing.

### **Core Task**

For each module in `backend/app/infrastructure/resilience/`:

1.  **Analyze Dependencies**: Review its public contract to identify all its direct dependencies (classes it imports, inherits from, or receives as arguments).
2.  **Define the Boundary**: A dependency is "external" if it is located **outside** the `backend/app/infrastructure/resilience/` directory. Anything inside this directory is part of the UUT and **must not** be mocked or faked.
3.  **Review Existing Fixtures**: Check `backend/tests/conftest.py`, `backend/tests/unit/conftest.py`, and `backend/tests/unit/llm_security/conftest.py` to see if a suitable fixture already exists.
4.  **Decide: Fake or Mock?**: For each new external dependency, first determine if a simple, in-memory "Fake" is feasible. If not, create a `MagicMock`-based fixture.
5.  **Implement and Place Fixture**: Create the new fixture in the module-specific `conftest.py` at `backend/tests/unit/llm_security/[module]/conftest.py`.
6.  **Placeholder `conftest.py` If None**: If there are no new module-specific fixtures, add placeholder text to `backend/tests/unit/llm_security/[module]/conftest.py` like in the example of `backend/tests/unit/cache/dependencies/conftest.py`.

### **Critical Rules & Constraints**

1.  **Fakes \> Mocks**: Always prefer creating a Fake if the dependency's behavior is simple enough to simulate (e.g., stateful storage, simple transformations).
2.  **Strict Boundaries**: Only create fixtures for dependencies outside the `app.infrastructure.resilience` namespace.
3.  **"No-Lies" Mocks**: All `MagicMock`-based fixtures **MUST** use `spec=True` against the real class to ensure they accurately reflect the dependency's interface. Use `AsyncMock` for `async` methods.
4.  **Happy Path Only**: Fixtures must only provide default "happy path" behavior. Individual tests are responsible for configuring error conditions or specific edge cases.
5.  **Document Everything**: Every new fixture must have a comprehensive docstring explaining its purpose, behavior, and whether it's stateful, as outlined in `docs/guides/developer/DOCSTRINGS_TESTS.md`.

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
````