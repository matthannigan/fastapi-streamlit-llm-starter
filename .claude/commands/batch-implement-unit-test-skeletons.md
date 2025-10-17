$ARGUMENTS contains a list of batches. Each batch contains the following files:
- Public contract for the module as located in `backend/contracts/**/[component]/[module].pyi`
- Shared component fixtures as located in `backend/tests/unit/[component]/conftest.py`
- Shared module fixtures as located in `backend/tests/unit/[component]/[module]/conftest.py`
- List of test files (no more than 5) that require implementation

Create a todo list and track your progress. Add 1 todo item for each batch, a summarize progress task after every 5 batches, and a final report at the end. 

When processing each batch, create up to 5 parallel @agent-unit-test-implementer agents to implement the test skeleton files. Give each subagent the public contract, shared component fixtures, shared module fixtures, and a specific test file to implement.

Once a batch is completed, mark it as done, update the todo list, and move on to the next batch in numerical order.

**Important**: DO NOT implement the batches themselves in parallel. Implement the batches sequentially and use parallel agents within the batches to process individual test files.

When all batches are completed, provide a final summary of the total number of test files implemented.