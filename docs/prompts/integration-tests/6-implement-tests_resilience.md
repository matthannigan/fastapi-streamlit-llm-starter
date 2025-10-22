# Integration Testing

## Prompt 6: Implement Priority Integration Tests from Test Plan

Implement priority `P0` and `P1` integration tests as specified in the validated test plan at `backend/tests/integration/resilience/TEST_PLAN.md`.

These tests must follow our integration testing philosophy as documented in `docs/guides/testing/INTEGRATION_TESTS.md` for the component defined by the public contracts at `backend/contracts/api/internal/resilience/*.pyi` and `backend/contracts/infrastructure/resilience/*.pyi`.

### Batch Implementation Strategy

**IMPORTANT**: For efficiency and parallel execution, implement tests in batches of no more than 3 seams at a time.

**For each batch:**

1. **Select Seams for Batch** - Choose 3 seams from the test plan:
   - Prioritize by test plan order (P0 first, then P1, etc.)
   - Group related seams when possible (same API endpoint, same service layer)
   - Note any interdependencies between seams

2. **Spawn Parallel Subagents** - Use the Task tool to launch 3 `integration-test-implementer` subagents **IN PARALLEL** (send a single message with multiple Task tool invocations).

   **For EACH subagent, provide:**
   ```markdown
   Implement integration tests for the following seam from TEST_PLAN.md:

   **Seam**: [Seam name/identifier from test plan]

   **Integration Scope**: [Copy from test plan]

   **Business Impact**: [Copy from test plan]

   **Test Strategy**: [Copy from test plan]

   **Success Criteria**: [Copy from test plan]

   **Test Plan Location**: `backend/tests/integration/resilience/TEST_PLAN.md`

   **Public Contracts**: `backend/contracts/api/internal/resilience/*.pyi`, `backend/contracts/infrastructure/resilience/*.pyi`

   **Fixtures Locations**: backend/tests/integration/resilience/conftest.py, backend/tests/integration/conftest.py

   **Output File**: backend/tests/integration/resilience/test_[seam_name]_integration.py

   Use the fixtures from conftest.py as-is. Do not create or modify fixtures.
   ```

3. **Wait for Batch Completion** - All subagents in the batch must complete before proceeding to validation.

   **Note**: Each subagent has already run and fixed their individual tests. Your job is to verify batch-level integration.

4. **Validate Batch Integration** - After ALL subagents complete, verify tests work together:
   ```bash
   # Run all tests in the batch together
   cd backend
   ../.venv/bin/python -m pytest backend/tests/integration/resilience/test_*_integration.py -v --tb=short
   ```

   **What to check** (individual tests should already pass):
   - ✅ No conflicts between tests from different subagents
   - ✅ No shared state issues across test files
   - ✅ No fixture scope conflicts
   - ✅ All tests pass when run together

   **If batch-level failures occur**:
   - Look for cross-test conflicts (one test affecting another)
   - Check for fixture scope issues (session fixtures being modified)
   - Verify no shared mutable state between test files
   - Review skipped tests and their reasons - may indicate larger issues

5. **Batch Isolation Check** - Verify batch tests don't depend on execution order:
   ```bash
   ../.venv/bin/python -m pytest backend/tests/integration/resilience/test_*_integration.py --randomly -v
   ```

   > **Note**: If pytest-randomly is configured by default in `pyproject.toml` or `pytest.ini`, the `--randomly` flag is redundant but harmless. This step is included for portability across different pytest configurations.

   **If order-dependent failures occur**:
   - These indicate cross-test state pollution (individual subagents tested in isolation)
   - Look for shared fixtures being modified
   - Check for database/cache state not being cleaned up
   - Verify fixture scopes are appropriate

6. **Mark Progress** - Update tracking (comment in test plan or notes) indicating batch completed.

**Repeat for next batch** until all P# seams are implemented.

---

### Final Validation

After ALL batches complete, verify the complete test suite:

**Note**: Individual tests have been validated by subagents, and batches have been validated. This final step verifies cross-batch integration and completeness.

1. **Run complete integration test suite**:
   ```bash
   cd backend
   ../.venv/bin/python -m pytest backend/tests/integration/resilience -v --tb=short
   ```

   **Purpose**: Verify all batches work together as a cohesive suite

2. **Verify test isolation across full suite**:
   ```bash
   ../.venv/bin/python -m pytest backend/tests/integration/resilience --randomly -v
   ```

   > **Note**: If pytest-randomly is configured by default, the `--randomly` flag is redundant but harmless.

   **Purpose**: Catch any cross-batch state pollution

3. **Check test count matches plan**:
   - Review TEST_PLAN.md seam count
   - Count implemented test files: `ls backend/tests/integration/resilience/test_*_integration.py | wc -l`
   - Verify all P# seams have corresponding test files

4. **Optional: Coverage check**:
   ```bash
   ../.venv/bin/python -m pytest backend/tests/integration/resilience --cov=[COMPONENT_UNDER_TEST] --cov-report=term-missing
   ```

---

### Success Criteria

Implementation is complete when:

- ✅ All P# seams from test plan have test files
- ✅ All tests pass consistently
- ✅ Tests pass in random order (proper isolation)
- ✅ No fixture errors or import errors
- ✅ Tests follow project standards (docstrings, naming, structure)
- ✅ Test output files follow naming: `test_[seam_name]_integration.py`

**Next Step**: Proceed to Prompt 7 (Documentation) to create README.md for the integration test suite.

---

### Subagent Prompt: [@agent-integration-test-implementer](../../../.claude/agents/integration-test-implementer.md)
