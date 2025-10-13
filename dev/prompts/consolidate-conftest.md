You are a senior software engineer specializing in writing maintainable, scalable, behavior-driven tests. First, review `docs/guides/testing/WRITING_TESTS.md` and `docs/guides/testing/UNIT_TESTS.md`. Then summarize the 3 most important principles and the 3 most important anti-patterns from these documents.

---

Your next goal is to ensure our test suite is as clean and efficient as our production code and adheres to DRY (Don't Repeat Yourself) principles.

I have provided a markdown export showing the contents of multiple `conftest.py` files from a specific directory (`[parent_directory]`) and its `module`-based subdirectories (`[parent_directory]/**/`).

Please perform a thorough review of these fixtures and provide a detailed refactoring plan. Your plan should identify which fixtures are good candidates for consolidation into the shared, parent `conftest.py` file at `[parent_directory]/conftest.py`.

**Your analysis must follow this structure:**

1.  **High-Level Summary:** Start with a brief, one-paragraph summary of your findings. To what degree is there overlap? Is consolidation recommended?

2.  **Fixtures to MERGE into Shared `conftest.py`:**
    * List every fixture that is a strong candidate for consolidation.
    * **Criteria for Merging:** A fixture should be moved if it is generic enough to be reused by tests in **more than one** subdirectory. Prime candidates include:
        * Generic test data (e.g., `sample_text`, `sample_cache_key`).
        * "Happy path" mocks for common, shared dependencies (e.g., `mock_performance_monitor`) with identical `spec=` attributes.
    * For each fixture, provide a brief, one-sentence justification for why it should be shared.

3.  **Fixtures to KEEP in Local `conftest.py` Files:**
    * List fixtures that should remain in their specific subdirectories (e.g., `[parent_directory]/[module]/conftest.py`).
    * **Criteria for Keeping Local:** A fixture should remain local if it is tightly coupled to the specific module it tests. Prime candidates include:
        * Mocks for dependencies that are unique to that one module (e.g., `mock_parameter_mapper` for `redis_ai`).
        * Complex, stateful mocks that are only relevant to one component's tests (e.g., `mock_redis_client` for `redis_generic`).
        * Configuration fixtures specific to one class's constructor (e.g., `valid_ai_params`).
    * For each fixture, state which subdirectory it belongs to and provide a brief justification.

4.  **Strategic Recommendation:**
    * Conclude with a brief strategic recommendation. Does this refactoring significantly improve the test suite? Are there any potential risks or next steps to consider?

Please present your final output as a clear, well-formatted markdown document.