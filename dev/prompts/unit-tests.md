### **Key Learnings & Workflow for Maintainable Unit Tests**

This document summarizes the principles and a structured, multi-step process for generating high-quality, maintainable, behavior-driven unit tests, particularly when collaborating with an AI coding assistant. The core philosophy is derived from the project's TESTING.md guide.

### **1. The Core Philosophy: Test Behavior, Not Implementation**

The central principle is to test a component's **public contract**—what it promises to do—rather than its internal implementation details. A well-written test should verify the observable outcomes of an action and should not break when the internal code is refactored, as long as the external behavior remains unchanged.

#### **The "Good ✅" vs. "Bad ❌" Pattern**

* **❌ Bad (Implementation Testing):** Asserts that an internal method was called or that a private attribute has a certain state. This is brittle and couples the test to the code's internal structure.  
```python
  # BAD: Tests internal calls, not the outcome.  
  def test_cache_response_calls_parent_set(ai_cache_instance):  
      # ... setup ...  
      ai_cache_instance.cache_response(...)  
      # This assertion is brittle. What if the parent method is renamed?  
      ai_cache_instance.set.assert_awaited_once()
```

* **✅ Good (Behavior Testing):** Performs an action and then asserts the final, observable result of that action. This is robust and tests what the user of the code actually cares about.  
```python
  # GOOD: Tests the observable outcome.  
  def test_cache_and_retrieve_response_successful(ai_cache_instance):  
      # Action: Store a value in the cache.  
      ai_cache_instance.cache_response("key", "value")  
      # Assert the Outcome: The value can be retrieved.  
      retrieved = await ai_cache_instance.get_cached_response("key")  
      assert retrieved["result"] == "value"
```

### **2. The 5-Step Workflow for AI-Assisted Test Generation**

To reliably guide an AI assistant to produce tests that follow this philosophy, we established a structured, five-step process. This workflow moves from high-level principles to detailed implementation, with verification steps along the way.

#### **Step 1: Principle Ingestion**

Goal: Align the AI assistant with the project's testing philosophy.  
Action: Begin by instructing the assistant to read TESTING.md and summarize its core principles and anti-patterns. This forces it to internalize the "why" before it begins coding.

#### **Step 2: Create Dependency Fixtures (conftest.py)**

Goal: Create the reusable, "happy path" test environment.  
Action: Instruct the assistant to identify the Unit Under Test's (UUT) direct dependencies from its public contract (.pyi file). For each dependency, create a pytest fixture that provides a mock.

* **Shallow Mocking:** Only mock direct dependencies. Do not mock the dependencies of your dependencies.  
* **Spec'd Mocks:** Ensure mocks are "spec'd" against the real classes to prevent mocking non-existent methods (spec=RealClass).  
* **Stateful Mocks:** For dependencies that manage state (like a cache), the mock must be stateful. Use a simple dictionary or object to simulate its state so that the effects of actions can be observed.  
```python
  # conftest.py: A stateful mock for a cache dependency  
  @pytest.fixture  
  def mock_cache_instance():  
      mock_storage = {} # This dictionary simulates the cache's state

      async def mock_set(key, value):  
          mock_storage[key] = value

      async def mock_get(key):  
          return mock_storage.get(key)

      # Create the mock and attach the stateful methods  
      mock = AsyncMock(spec=RealCacheClass)  
      mock.set.side_effect = mock_set  
      mock.get.side_effect = mock_get  
      return mock
```
#### Verify the Fixtures (The "Smoke Test")

Goal: Build confidence in the test harness before writing the main tests.  
Action: Create a small, fast test file (e.g., test_conftest.py) that consumes the primary mock fixtures. This test doesn't check logic; it verifies that the mocks were created with the correct type and spec. This catches setup errors early.  
# test_conftest.py: A smoke test for your fixtures  
def test_mock_fixtures_are_configured_correctly(mock_key_generator, mock_performance_monitor):  
    # Verifies the mock was created with the right class interface.  
    # This will fail if the spec is wrong or the real class changes.  
    assert hasattr(mock_key_generator, 'generate_cache_key')  
    assert hasattr(mock_performance_monitor, 'get_performance_stats')

#### **Step 3: Create the Test Suite Skeleton**

**Goal**: Plan the entire test suite by defining what to test before writing any implementation code.  

**Action**: Instruct the assistant to create the test file(s) with only test classes, empty test methods, and detailed docstrings. This "Docstring-Driven" approach forces a focus on the UUT's public contract and observable behaviors.

**Prompt**
Create a plan and execute the following prompt on these UUTs:
- `factory`
- `key_generator`
- `migration`

```
Create a skeleton test suite for the UUT, `backend/contracts/infrastructure/cache/[UUT].pyi` in separate files within `backend/tests/unit/infrastructure/cache/[UUT]/`.
1. Each test must verify an observable behavior described in the UUT's docstrings. Do not test private methods or implementation details. DO NOT write any test code right now. 
2. Instead, create detailed docstrings using the guidance in `docs/guides/developer/DOCSTRINGS_TESTS.md` to describe the intended testing classes and methods.
 - In the docstring for each test, describe the 'Given/When/Then' scenario in terms of observable behavior. For example, instead of saying 'the set method is called', describe the outcome: 'the data is successfully stored and can be retrieved'.
 - In each docstring, identify which fixtures and mocks (if any) from `backend/tests/unit/infrastructure/cache/conftest.py` or `backend/tests/unit/infrastructure/cache/[UUT]]/conftest.py` should be used for each test.
3. If necessary due to a large number of tests, group tests into major categories of testing and place them in separate classes, converting class names to snake case for file naming, e.g., `test_[UUT]_[class_name].py`. If multiple files are not necessary, place all tests in a single file named `test_[UUT].py`.
```

As a reference, see a completed example for `redis_ai` in `backend/tests/unit/infrastructure/cache/redis_ai/`.


#### **Step 4: Write the Test Code**

Create a plan and execute the following prompt on these UUTs:
- `factory`
- `key_generator`
- `security`

```
Build out the unit test skeletons located at `backend/tests/infrastructure/cache/[UUT]/` using @agent-unit-test-supervisor and @agent-unit-test-implementer . The public contract for [UUT] is located at `backend/contracts/infrastructure/cache/[UUT].pyi`. Tests should be built using behavior-driven principles as outlined in `docs/guides/developer/TESTING.md` and `docs/guides/developer/DOCSTRINGS_TESTS.md` using spec'd mocks located in `backend/tests/infrastructure/cache/conftest.py` or `backend/tests/infrastructure/cache/[UUT]/conftest.py`.
```

**Goal:** Implement the planned tests, focusing on observable outcomes.  

**Action:** Instruct the assistant to fill in the code for the skeleton created in Step 3.

* **Configure Mocks Locally:** The "happy path" fixtures from conftest.py are the default. For any test that requires a failure or edge case, configure the mock's behavior (return_value or side_effect) *inside that specific test function*.  

* **Assert the Outcome:** The assertions must verify the final result, not the intermediate steps.  
```python
  # test_my_module.py  
  def test_uut_handles_dependency_failure_gracefully(uut_instance, mock_dependency):  
      # Locally configure the mock for this specific scenario  
      mock_dependency.do_something.side_effect = InfrastructureError("It broke!")

      # Assert the final, observable outcome  
      result = uut_instance.perform_action()  
      assert result.status == "FAILED_GRACEFULLY"
```
#### **Step 5: Self-Correction and Review**

Goal: Perform a final quality check against the core principles.  
Action: Instruct the assistant to review the code it just wrote, comparing it against the "Good ✅ vs. Bad ❌" examples from Step 1 and refactoring any tests that are still coupled to implementation details.

### **3. Managing Test Suite Scale**

As a test suite grows, managing file size and fixture scope is critical for maintainability.

* **Splitting Test Files:** A large test skeleton (e.g., >1000 lines) should be split into multiple files *before* Step 4. A natural way to do this is to have one file per test class. This makes the files easier for humans to read and provides smaller, more focused context for the AI assistant, leading to higher-quality code generation.  
* **Hierarchical conftest.py:** pytest loads fixtures from conftest.py files in the current directory and all parent directories. Use this to manage scope:  
  * **High-Level conftest.py (e.g., tests/infrastructure/cache/conftest.py):** Place highly reusable fixtures here that are needed by tests for multiple components (e.g., mock_performance_monitor).  
  * **Low-Level conftest.py (e.g., tests/infrastructure/cache/redis_ai/conftest.py):** Create a conftest.py here only for fixtures that are *exclusively* used by the redis_ai tests.

By following this structured, iterative, and principle-driven approach, you can effectively guide an AI assistant to produce a comprehensive unit test suite that is robust, maintainable, and provides true confidence in your application's behavior.