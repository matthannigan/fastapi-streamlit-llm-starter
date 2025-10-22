# Integration Test Prompts

This directory contains prompts for AI-assisted integration test development following a systematic discovery → planning → implementation → documentation workflow.

## Complete Workflow

### Standard Workflow (With Unit Tests)

**Phase 1: Discovery** (Identify Integration Opportunities)
1. [Identify Seams](./1-identify-seams.md) - Architectural analysis
2. [Mine Unit Tests](./2-mine-unit-tests.md) - Extract integration insights from existing tests

**Phase 2: Planning** (Consolidate and Prioritize)
3. [Review & Prioritize](./3-review-prioritize.md) - Consolidate seams, deduplicate, prioritize
4. [Review Test Plan](./4-review-test-plan.md) - Optional quality gate with different LLM

**Phase 3: Implementation**
5. [Create Fixtures](./5-create-fixtures.md) - Build `conftest.py` with all required test fixtures
6. [Implement Tests](./6-implement-tests.md) - Write integration tests using fixtures from Step 5
7. **Debug Tests** - Get all tests passing, reclassify any E2E tests

**Phase 4: Documentation**
8. [Document Tests](./6-documentation.md) - Create README for integration test suite

### Alternate Workflow (No Unit Tests)

**Phase 1: Discovery & Planning**
1. [Identify Seams](./1-identify-seams.md) - Use expensive model, skip 2-4

**Phase 2: Implementation**
2. [Create Fixtures](./5-create-fixtures.md) - Build `conftest.py` with all required test fixtures
3. [Implement Tests](./6-implement-tests.md) - Write tests using fixtures from Step 2
4. **Debug Tests** - Get tests passing

**Phase 3: Documentation**
5. [Document Tests](./7-documentation.md) - Create README

## Prompt Details

| Prompt | Purpose | Input | Output |
|--------|---------|-------|--------|
| 1. Identify Seams | Find integration boundaries from architecture | Codebase, architecture docs | Seam list with confidence levels |
| 2. Mine Unit Tests | Extract integration insights from unit tests | Unit test files | Integration gaps and opportunities |
| 3. Review & Prioritize | Consolidate and deduplicate seams | Prompts 1+2 output | Prioritized test plan (P0/P1/P2) |
| 4. Review Test Plan | Optional quality check | Prompt 3 output | Validated/revised test plan |
| 5. Create Fixtures | Build `conftest.py` with required fixtures | Test plan's `Required Fixtures` section | Fixtures ready for test implementation |
| 6. Implement Tests | Write integration tests using fixtures | Test plan + fixtures from Step 5 | Working test files |
| 7. Document Tests | Create README for test suite | Implemented tests + test plan | README.md |

## Model Recommendations

### Cost-Effective Approach
- **Prompts 1-3**: Fast/cheap model (Haiku, GPT-4 Turbo)
- **Prompt 4**: Expensive/smart model (Opus, GPT-4) - Quality gate
- **Prompts 5-7**: Fast/cheap model (Haiku, GPT-4 Turbo)

### Quality-First Approach
- **All Prompts**: Expensive/smart model (Opus, GPT-4)
- **Skip Prompt 4** (no need for separate review)

### Time-Constrained Approach
- **All Prompts**: Fast/cheap model (Haiku, GPT-4 Turbo)
- **Skip Prompt 4** (no review step)

## Key Principles

**Discovery Before Implementation**: Prompts 1-4 identify and validate integration opportunities before writing any code, preventing wasted effort on low-value tests.

**Fixtures Before Tests**: Prompt 5 implements all required test fixtures BEFORE test implementation (Prompt 6). This separation ensures:
- Consistent testing infrastructure across all test files
- Prevents ad-hoc fixture creation during test implementation
- Enables fixture reuse and reduces duplication
- Allows test implementers to focus on test logic, not infrastructure setup

**Mining Not Converting**: Prompt 2 extracts integration insights from unit tests but doesn't convert them. Unit and integration tests serve complementary purposes.

**Optional Quality Gate**: Prompt 4 allows using an expensive model to validate work from cheaper model, optimizing cost vs. quality.

**Documentation as Code**: Prompt 7 creates README that accurately reflects implemented tests, not just what was planned.

## See Also

- [Integration Tests Guide](../../guides/testing/INTEGRATION_TESTS.md) - Comprehensive integration testing philosophy and patterns
- [Writing Tests Guide](../../guides/testing/WRITING_TESTS.md) - Docstring-driven test development
- [Testing Overview](../../guides/testing/TESTING.md) - Overall testing strategy