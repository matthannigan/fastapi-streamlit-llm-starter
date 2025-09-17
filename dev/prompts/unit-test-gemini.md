```
npx --prefix /Users/matth/Github/MGH/repomix repomix --output repomix-output/repomix_backend-cache-parameter_mapping_U.md --quiet --include "backend/contracts/core/exceptions.pyi,backend/**/cache/parameter_mapping/**/*,backend/**/cache/**/*parameter_mapping*.*,backend/tests/infrastructure/cache/conftest.py,docs/guides/testing/TESTING.md,docs/guides/testing/WRITING_TESTS.md,docs/guides/developer/DOCSTRINGS_TESTS.md" --ignore "backend/app/**/*.*"
```

### Unit Test Prompt for Coding Assistant

Build out the test skeletons located at `backend/tests/infrastructure/cache/parameter_mapping/test_parameter_mapping.py`.

Your task is to implement the test logic based on the guiding philosophy, mocking strategy, and constraints detailed below. The public contract you must test against is defined in `backend/contracts/infrastructure/cache/parameter_mapping.pyi`.

---

### **Guiding Philosophy: Test Behavior, Not Implementation**

Your implementation must adhere to the principles in `docs/guides/testing/WRITING_TESTS.md` and `docs/guides/developer/DOCSTRINGS_TESTS.md`. The single most important rule is:

> **The Golden Rule of Testing:** Test the public contract documented in the docstring. **Do NOT test the implementation code inside a function.** A good test should still pass even if the entire function body is rewritten, as long as the behavior remains the same.

You are testing what the component *does* from an external observer's perspective, not *how* it does it internally. Your tests must survive internal refactoring.

### **Mocking and Dependencies Strategy**

This is the most critical part of your task. Our philosophy is to **mock only at system boundaries** and **prefer fakes over mocks**.

* **ALLOWED ✅**:
    * Use provided "fake" dependencies, such as the `fakeredis` fixture. These simulate real behavior and are preferred.
    * Use fixtures that represent true external services (e.g., a third-party network API), if provided.

* **FORBIDDEN ❌**:
    * **DO NOT** use `patch` to mock any class, method, or function that is internal to the cache component itself. The entire component is the unit under test.
    * **DO NOT** test private methods or attributes (e.g., `_decompress_data` or `_validation_cache`).
    * **DO NOT** assert on the internal implementation, such as how many times an internal helper function was called.

---

### **Your Role and Responsibilities**

You are a **Behavioral Test Implementation Specialist**. Your sole focus is to implement robust, behavior-driven test logic within pre-existing skeletons that verify observable outcomes.

1.  **Implement Test Logic**: Fill in the test methods based on their detailed docstrings, which serve as the test specification.
2.  **Use Provided Fixtures**: Correctly use fixtures from `conftest.py` files. Prefer fakes over mocks.
3.  **Write Behavioral Assertions**: Assert only on final results and observable side effects (e.g., what is returned, what state has changed in a *fake* dependency).

---

### **Critical Constraints**

1.  **NEVER** modify `conftest.py` files.
2.  **NEVER** use `patch` to mock any module, class, or method that is part of the cache component's internal implementation.
3.  **ALWAYS** test through the public contract (`.pyi` file). Do not test private or protected members.
4.  **FOCUS** exclusively on observable outcomes. A test is successful if the component produces the correct output or side effect, regardless of the internal path taken to get there.
5.  **ENSURE** each test is independent and isolated.

---

### **Implementation Approach**

1.  **Understand the Goal**: Read the test method's docstring and the `Verifies`, `Scenario`, and `Business Impact` sections to understand the required behavior.
2.  **Structure the Test**: Follow the Given/When/Then structure provided in the skeleton's docstring comments.
3.  **Arrange (Given)**: Set up the initial state. This includes preparing input data and configuring the behavior of any *external* dependency mocks or fakes provided by fixtures.
4.  **Act (When)**: Call the public method on the Unit Under Test (the cache component).
5.  **Assert (Then)**: Write clear assertions that verify the final, observable outcome as documented.
6.  **Verify**: Run `pytest` to ensure the test passes and meets all constraints.

If a unit test appears to require substantial internal mocking or knowledge of implementation details, it should be rewritten instead as an integration test:
* Mark it with `@pytest.mark.skip(reason="[Replace with integration test using real components]")`.
* Add Python comments on the line above the method with additional details to explain your integration test recommendation.

Your final output must be the code diff to create revised test files with all methods implemented.