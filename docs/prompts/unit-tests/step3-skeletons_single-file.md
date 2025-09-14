# Skeleton Generation Prompt for Coding Assistant

## **Objective**

Your goal is to act as a **Test Suite Architect**. You will create a comprehensive set of test skeletons for `backend/core/environment.py`. You will **only** write test classes, empty test methods, and the detailed docstrings that serve as the specification for each test. **You will not write any implementation code.**

This "Docstring-Driven" approach ensures we plan our entire test suite by focusing on observable behaviors defined in the public contract *before* implementation begins.

## **Guiding Philosophy: The Component is the Unit**

Our testing philosophy treats the entire `environment.py` as a single **Unit Under Test (UUT)**. Every test you design must treat the UUT as a black box, interacting with it exclusively through its public API.

  * **Source of Truth**: The public contract defined in `backend/contracts/core/environment.pyi` and its corresponding production docstrings.
  * **Core Principle**: Your test plan must verify *what* the component does, not *how* it does it.

## **Critical Rules & Constraints**

1.  **No Implementation Knowledge**: You must design tests that can be written without ever seeing the UUT's source code. Base everything on the public contract.
2.  **No Internal Mocking**: Your test plans **must not** rely on mocking any internal part of the `environment`. The docstrings should only reference fixtures for dependencies that are **external** to the component.
3.  **Focus on Observable Outcomes**: The "Then" part of your `Given/When/Then` scenarios must describe a result that an external observer can see (e.g., a return value, a state change in a *fake* dependency, or a specific exception being raised).
      * **Avoid**: "Then: The internal `_process_data` method is called."
      * **Prefer**: "Then: The item is successfully stored and can be retrieved with the correct value."
4.  **Comprehensive Coverage**: Your plan must include tests for happy paths, configuration, error handling, and relevant edge cases.

## **Core Task: Create the Test Skeletons**

Generate skeleton tests in `backend/tests/core/test_environment.py`.

1.  **Systematically Analyze the Contract**: Review the `.pyi` file and the module's docstring to identify all public methods and their documented behaviors, arguments, return values, and exceptions.
2.  **Plan Test Categories**: Group the tests into logical classes that cover the full contract. Suggested categories include:
      * `Test[ModuleName]Initialization`: How the component is configured and instantiated.
      * `Test[ModuleName]CoreFunctionality`: The main "happy path" behaviors.
      * `Test[ModuleName]ErrorHandling`: How the component responds to bad input, failed dependencies, or invalid states.
      * `Test[ModuleName]EdgeCases`: Behavior at documented boundaries or with unusual (but valid) inputs.
3.  **Write Detailed Docstrings**: For each empty test method, write a comprehensive docstring using the template and guidance from `docs/guides/developer/DOCSTRINGS_TESTS.md`.
      * Clearly state the `Verifies`, `Business Impact`, and `Scenario (Given/When/Then)`.
      * Under a `Fixtures Used` section, list the specific fixtures from the shared or module-specific `conftest.py` that will be needed to set up the test scenario.

## Examples of a well-formed behavioral test docstrings

```python
# From: test_cache_operations.py
class TestCacheCoreFunctionality:
    """Tests the core get/set/delete operations of the cache."""

    def test_set_and_get_retrieves_correct_value(self):
        """
        Test that a value set in the cache can be retrieved successfully.

        Verifies:
            The cache correctly stores and retrieves a simple key-value pair.

        Business Impact:
            Ensures the fundamental storage mechanism of the cache is reliable.

        Scenario:
            Given: A connected cache instance and a key-value pair.
            When: The 'set' method is called with the key and value.
            And: The 'get' method is subsequently called with the same key.
            Then: The returned value matches the original value that was set.

        Fixtures Used:
            - connected_cache_instance: Provides a ready-to-use cache component.
        """
        pass

    def test_get_nonexistent_key_returns_none(self):
        """
        Test that retrieving a key that does not exist returns None.

        Verifies:
            The cache handles cache misses gracefully without raising an error.

        Business Impact:
            Prevents application crashes when attempting to access non-existent data.

        Scenario:
            Given: A connected cache instance.
            When: The 'get' method is called with a key that has not been set.
            Then: The method returns None.

        Fixtures Used:
            - connected_cache_instance: Provides a ready-to-use cache component.
        """
        pass
```