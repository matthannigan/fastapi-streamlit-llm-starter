# Middleware Unit Testing

## Prompt 1: Update Fixtures

You are a senior software engineer specializing in writing maintainable, scalable, behavior-driven tests. We are creating a limited number of unit tests for our `app.core.middleware` component in `backend/tests/unit/middleware` following guidance from `backend/tests/unit/middleware/TEST_RECS.md`. First, read `@docs/guides/testing/WRITING_TESTS.md` and `@docs/guides/testing/UNIT_TESTS.md `. Summarize the 3 most important principles and the 3 most important anti-patterns from the documents.

Next please update the fixture skeleton file at `backend/tests/unit/middleware/conftest.py` to be consistent with other unit test fixtures such as `backend/tests/unit/resilience/conftest.py` and `backend/tests/unit/cache/conftest.py`. Add imports and comprehensive docstrings following guidance in `docs/guides/developer/DOCSTRINGS_TESTS.md`. Run `/lint fixer backend/tests/unit/middleware/conftest.py` custom slash command to identify and fix mypy lint issues until the fixtures are ready for use by our `middleware` unit test suite.

---

## Prompt 2: Thoroughly Revise Test Docstrings

Your next goal is to act as a **Test Suite Architect**. We are continuing to create a limited number of unit tests for our `app.core.middleware` component in `backend/tests/unit/middleware` following guidance from `backend/tests/unit/middleware/TEST_RECS.md`. 

The draft test files are located in `backend/tests/unit/middleware/test_*.py`.

For each draft test file, assign a general-purpose subagent to write detailed docstrings for classes and methods that serve as the specification for our tests following guidance in `docs/guides/developer/DOCSTRINGS_TESTS.md`, `@docs/guides/testing/WRITING_TESTS.md`, and `@docs/guides/testing/UNIT_TESTS.md `. The subagents may use the draft implementations in each file as a starting point and they need to ensure that the tests examine the functionality of the component only documented by its public contract in `backend/contracts/core/middleware/*.pyi`. All tests must use existing fixtures from `backend/tests/unit/conftest.py` and `backend/tests/unit/middleware/conftest.py` to isolate the unit tests from the rest of the system. **Subgents may not create any new tests, test files, or modify fixtures.**

Create a plan and assign a general-purpose subagent to implement each task in the plan. Spawn multiple subagents in parallel to accompish these tasks expeditiously and preserve our main context window.


## Prompt 3: Thoroughly Revise Test Code

Our next goal is to thoroughly revise the test code in our draft test files located in `backend/tests/unit/middleware/test_*.py`.

For each draft test file, we need to thoroughly revise the test methods and implement robust test logic given the pre-existing docstring skeletons. Also ask each subagent to run `/lint fixer backend/tests/unit/middleware/[test_file.py]` custom slash command to identify and fix mypy lint issues until the test are ready for use by our `middleware` unit test suite.

Create a plan and SEQUENTIALLY assign a new @agent-unit-test-implementer to implement each task in the plan.