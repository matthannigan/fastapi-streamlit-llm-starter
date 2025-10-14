Given $ARGUMENTS with the locations of unit test skeletons and public contract for the component under testing:

Search `backend/tests/unit/[component]/**/test_*.py` to create a comprehensive inventory of all unit test skeleton files that require implementation. We want to group the test files logically into batches both by `[module]` and such that each batch has no more than 5 files each.

**Batching Rules:**
- Group files by module to keep related functionality together
- Each batch must have no more than 5 files
- When a module has more than 5 files, split it into approximately equal-sized batches
  - Example: 6 files → 2 batches of 3 files each (NOT 5 + 1)
  - Example: 7 files → 2 batches: 4 files + 3 files (NOT 5 + 2)
  - Example: 8 files → 2 batches of 4 files each (NOT 5 + 3)
  - Example: 11 files → 3 batches: 4 + 4 + 3 files (NOT 5 + 5 + 1)
- Prioritize balanced distribution over strict equality

For each batch, create a task list that provides the filepaths for the following files:
  * Public contract for the module as located in `backend/contracts/**/[component]/[module].pyi`
  * Shared component fixtures as located in `backend/tests/unit/[component]/conftest.py`
  * Shared module fixtures as located in `backend/tests/unit/[component]/[module]/conftest.py`
  * List of test files (no more than 5) that require implementation

Save your output as Markdown to `backend/tests/unit/[component]/test-batches.md`.