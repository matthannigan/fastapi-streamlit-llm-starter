# Cache Infrastructure Testing Suite

## 1. Overview

This directory contains the comprehensive test suite for the cache infrastructure, located in `app/infrastructure/cache/`. The suite is designed to ensure the reliability, performance, and correctness of all caching components, from the base `CacheInterface` to the production-ready `GenericRedisCache` and `AIResponseCache` implementations.

Our testing approach has been carefully designed to follow modern, behavior-driven principles. We prioritize testing the documented behavior of integrated components over mocking actual internal implementation details. This results in a more robust, maintainable, and high-confidence test suite **that is resilient to internal refactoring**.

## 2. Core Testing Philosophies

The foundation of our testing strategy is to validate public contracts and observable behavior, not internal wiring. The overuse of internal mocking introduces critical risks that we actively avoid.

### Public Contracts

All test writing and debugging should be based on the "public contract" stub files located in `backend/contracts`. These are automatically generated from the production codebase located in `backend/app` via `make generate-contracts`.

Each `.pyi` file in `backend/contracts` represents the public-facing interface of its corresponding source `.py` file. It includes:
  * All necessary `import` statements.
  * Class definitions, including inheritance.
  * Public method signatures (including `__init__`) with full type hints.
  * The complete docstrings for the module, classes, and all public methods.

Crucially, all internal implementation logic (the code inside method bodies) has been **removed** and replaced with `...`.

The primary purpose of these stubs is to provide a clean, focused, and implementation-agnostic context for AI coding assistants to use when generating tests. This helps enforce our modern, behavior-driven testing philosophy.

### `backend/app/infrastructure/cache` Is the Unit Under Test (UUT)

Our testing strategy treats the entire `cache` component as the single **Unit Under Test (UUT)**. This means we test the component exclusively through its public-facing API—its "public contract"—treating its internal workings as a black box. 

#### Rationale: Building a Resilient Test Suite

Previous experiences with traditional unit testing led to a test suite that was "far too brittle". Tests were tightly coupled to the code's internal implementation, mocking private methods and asserting on internal data structures. As a result, any internal refactoring caused the entire test suite to fail, even when the component's external behavior remained unchanged. This created a high maintenance burden and actively discouraged essential improvements to the code.

By defining the entire component as the UUT, we adopt a **behavioral testing** approach. The primary goal is to create a durable test suite where tests pass regardless of the implementation approach, failing only if the public contract is violated. This strategy focuses on verifying *what* the component achieves, not *how* it achieves it, ensuring our tests support rather than hinder refactoring.

#### Tradeoffs and a New Verification Model

This decision represents a philosophical shift in how we approach verification, trading granular unit tests for a more holistic, multi-layered strategy.

* **Test Scope:** We write fewer, more comprehensive tests that exercise the public contract from the outside in. The suite is kept intentionally "small and focused," prioritizing high-value tests that verify critical behaviors and system flows.
* **Shifting Left with Static Analysis:** We place a heavy reliance on static analysis tools like `MyPy` and linters as our foundational layer of defense. These tools have proven to be "surprisingly effective" at catching nuanced type contract errors and API misuse at the earliest possible stage, providing a high return on investment.

* **The Modern Testing Pyramid:** Our approach reshapes the classic testing pyramid. **Static analysis** forms the largest and most crucial base. The middle layer consists of **behavioral and contract tests**. The peak is a small number of **integration and end-to-end tests** that verify critical user flows.

### Mocking Strategy: Fakes Over Mocks

Our behavioral testing philosophy requires a disciplined approach to managing dependencies, moving away from the brittle mocking patterns of the past.

* **No Mocking of Internals:** We follow a strict rule: "absolutely no mocking of internal details". Mocks are considered prone to brittleness and can create false positives by inaccurately representing real-world behavior.

* **Prefer Fakes and Real Infrastructure:** We strongly prefer using "fakes" (like `FakeRedis`) for fast local tests or "real infrastructure" via tools like `Testcontainers` for integration tests. Fakes provide a more honest and robust validation by simulating real behavior, while Testcontainers allow us to verify true wire-level interactions with ephemeral services.

* **Constrained Mocking at Boundaries:** When mocking is absolutely necessary for external dependencies, we only mock what leaves the process boundary. We use "No-Lies Mocks" that validate call signatures and arguments to ensure the mock is an honest reflection of the real interface, preventing tests from passing silently when the underlying contract is violated.

#### Consequences of Internal Mocking

* **Brittle Tests**: Mocks create a tight coupling between the test and the *implementation details* of the component. A minor internal refactoring can break dozens of tests, even if the public behavior is unchanged.

* **False Confidence**: Tests that heavily mock internals can achieve 100% code coverage while completely failing to validate the component's actual behavior, creating a dangerous illusion of quality.

* **Impeded Refactoring**: A test suite should enable refactoring with confidence. When tests are coupled to the implementation, they become a barrier to improvement, as developers avoid refactoring to prevent the cascade of breaking tests.

## 3. Mocking Strategy & Best Practices

Based on our core philosophy, we follow a strict decision framework for when and how to use mocks.

### Decision Framework: When Internal Mocking is Acceptable

#### ✅ **Acceptable Internal Mocking Scenarios**

  * **Error Handling Logic Testing**

      * **When**: Testing how a component handles specific, hard-to-trigger errors from its dependencies.
      * **Example**: Verifying the factory's error wrapping logic when a cache constructor fails.
      * **Rationale**: The focus is on the calling component's error handling, not the dependency's behavior.
      * **Requirement**: Should be supplemented with integration tests using invalid configurations to trigger real errors.

  * **Parameter Mapping and Transformation Testing**

      * **When**: Verifying that a component correctly transforms or passes arguments to a dependency.
      * **Example**: In `factory/test_factory.py`, patching `AIResponseCache` to inspect the keyword arguments passed to its constructor, ensuring `memory_cache_size` was correctly mapped from the input configuration.
      * **Rationale**: This tests the factory's specific logic without needing to exercise the full cache implementation. The mock only inspects call arguments.

#### ❌ **Unacceptable Internal Mocking Scenarios**

  * **Business Logic Testing**: Testing the core functionality of internal components.
      * **Alternative**: Use real components with test data.
  * **Configuration and Validation Testing**: Testing configuration loading, parsing, or validation.
      * **Alternative**: Use real `Settings` with test configuration files or environment variables.
  * **Integration Flow Testing**: Testing multi-component workflows.
      * **Alternative**: Use integration tests with real components.
  * **Performance and Resource Management Testing**: Testing memory usage, monitoring, or cleanup.
      * **Alternative**: Use real components and monitor their behavior.

### Anti-Pattern Summary

#### What to Avoid

❌ **Don't** mock internal cache components for functional testing (`CacheFactory`, `InMemoryCache`, `CachePerformanceMonitor`).
❌ **Don't** mock `Settings` for configuration that can be tested with real files/environment variables.
❌ **Don't** mock parameter mapping or validation logic for its functional outcome.
❌ **Don't** use internal mocking as a substitute for proper integration testing.

#### What to Use Instead

✅ **Use** real components with test-specific configurations.
✅ **Use** `fakeredis` for Redis simulation (as implemented in `redis_generic/conftest.py`).
✅ **Use** integration tests for multi-component scenarios.
✅ **Mock** only at true system boundaries (external services, file systems, network).
✅ **Use** internal mocking sparingly and only for specific interaction testing (e.g., error handling, parameter inspection).

-----

## 4. Test Harness Overview & Fixture Reference

The test suite relies on a well-defined set of `pytest` fixtures to provide test data and configured components.

### Fixture Philosophy and Patterns

1.  **Real Component Fixtures (Preferred)**: Instances of the *actual* production classes, configured for a test environment.

  * **Examples**: `default_memory_cache`, `small_memory_cache`.
  * **Use Case**: The best choice for unit and component tests. They test the real behavior of an implementation, leading to high-confidence tests that are resilient to refactoring.

2.  **High-Fidelity Fakes (For External Dependencies)**: Substitutes a dependency with a fake implementation that mimics the real dependency's behavior.

  * **Example**: `fake_redis_client` (which uses `fakeredis`).
  * **Use Case**: Allows realistic integration testing of components like `GenericRedisCache` without the overhead of a live Redis server, making tests faster and more reliable.

3.  **Mock-Based Fixtures (Use Sparingly)**: Uses `MagicMock` or `AsyncMock` to replace a component.

  * **Use Case**: Limited to the acceptable scenarios defined in the Mocking Strategy section, such as testing specific error-handling paths.

### Fixture Types at a Glance

| Fixture Type | Example(s) | Use Case | Key Benefit |
| :--- | :--- | :--- | :--- |
| **Real Components** | `default_memory_cache` | The default for unit/component tests. | Tests the actual production code for the highest confidence. |
| **High-Fidelity Fakes** | `fake_redis_client` | Isolate the UUT from external dependencies like Redis. | Realistic behavior simulation without network/IO overhead. |
| **Spec'd Mocks** | `mock_key_generator` | Sparingly, for error handling or argument inspection. | Isolate the UUT to test specific interaction logic. |

### Shared Fixtures (`backend/tests/infrastructure/cache/conftest.py`)

This file provides comprehensive fixtures used across all cache tests.

#### Cache Instance Fixtures

  * **`default_memory_cache`**: A standard `InMemoryCache` instance, perfect for testing any service that depends on the `CacheInterface`.
  * **`small_memory_cache`**: An `InMemoryCache` with `max_size=3` for easily testing LRU eviction logic.
  * **`fast_expiry_memory_cache`**: An `InMemoryCache` with `default_ttl=2` for testing expiration without long waits.
  * **`large_memory_cache`**: An `InMemoryCache` with expanded limits for performance testing.

#### Test Data Fixtures

  * **`sample_cache_key`**: A standard key (`"test:key:123"`) for consistency.
  * **`sample_cache_value`**: A standard dictionary value representing common application data.
  * **`sample_ttl` / `short_ttl`**: Standard TTL values (3600s and 1s).
  * **AI-Specific Data**: Includes `sample_text`, `sample_short_text`, `sample_long_text`, `sample_ai_response`, and `ai_cache_test_data` for testing AI cache features.

*(A complete list of module-specific fixtures can be found in the `conftest.py` file within each sub-directory.)*

## 5. Coding Assistant Prompts

The implementations in this directory are generated by a coding assistant guided by detailed prompts. This process ensures all generated code adheres strictly to our behavior-driven testing philosophy. Each prompt's core instructions are summarized below.

### Our 5-Step Test Generation Workflow

The test suite is built using a systematic, 5-step process with a coding assistant.

`Step 1: Context Alignment` -> `Step 2: Fixture Generation` -> `Step 3: Test Planning` -> `Step 4: Test Implementation` -> `Step 5: Verification`

### Step 1: Context Alignment (The "Why")

```markdown
You are a senior software engineer specializing in writing maintainable, scalable, behavior-driven tests. First, read `docs/guides/testing/1_WRITING_TESTS.md` and `backend/tests/infrastructure/cache/README.md`. Summarize the 3 most important principles and the 3 most important anti-patterns from the documents.
```

To align the AI assistant with the project's testing philosophy, we begin by instructing it to read `TESTING.md` and summarize its core principles and anti-patterns. This forces it to internalize the "why" before it begins coding.

### Step 2: Fixture Generation (The "Tools")

> full prompt: `docs/prompts/unit-tests/step2-fixtures.md`

To ensure our behavioral tests are properly isolated, we instruct the coding assistant to generate Pytest fixtures for external dependencies with the following guidance:

* **Prefer Fakes Over Mocks**: The prompt's primary instruction is to create "Fakes"—simple, in-memory implementations of a dependency's contract that provide realistic behavior. `MagicMock`-based fixtures are used only as a fallback when a Fake is not practical.

* **Strict System Boundaries**: Fixtures are created *only* for dependencies located outside the component under test. This rule strictly forbids the mocking of internal collaborators, ensuring the entire component is tested as a single unit.

* **"Happy Path" and "Honest" Fixtures**: All generated fixtures must represent a default "happy path" scenario. Any mock-based fixtures are required to use `spec=True` to ensure they are "honest" and accurately reflect the real dependency's interface.

#### Step 2.5: Fixture Verification (The "Smoke Test")

To build confidence in the test harness before writing the main tests, we create a small, fast test file (e.g., `test_conftest.py`) that consumes the primary mock fixtures.

This test doesn't check logic; it verifies that the mocks were created with the correct type and spec. This catches setup errors early.

```python
# test_conftest.py: A smoke test for your fixtures  
def test_mock_fixtures_are_configured_correctly(mock_key_generator, mock_performance_monitor):  
    # Verifies the mock was created with the right class interface.  
    # This will fail if the spec is wrong or the real class changes.  
    assert hasattr(mock_key_generator, 'generate_cache_key')  
    assert hasattr(mock_performance_monitor, 'get_performance_stats')
```

### Step 3: Test Planning (The "Blueprint")

> full prompt: `docs/prompts/unit-tests/step3-skeletons.md`

Before any test code is written, we generate a complete test plan using a "Docstring-Driven" approach. This is accomplished with a detailed prompt that instructs a coding assistant to create test skeletons using the following principles:

* **Role-Based Generation**: The assistant acts as a **Test Suite Architect**, focusing solely on planning the tests, not implementing them. Its only output is empty test methods with comprehensive docstrings that serve as specifications.

* **"Black Box" Design**: The entire test plan is generated by analyzing only the component's **public contract** (`.pyi` file). The prompt forbids any test design that would require knowledge of the component's internal implementation.

* **Comprehensive Behavioral Coverage**: The assistant is guided to create a systematic test plan that covers all aspects of the component's observable behavior, including initialization, core functionality, error handling, and edge cases.

* **Specification as Docstring**: Each docstring details the test's `Given/When/Then` scenario, its business impact, and the specific fixtures required for its implementation, creating a clear blueprint for the final step.

### Step 4: Test Implementation (The "Build")

```markdown
Search `backend/tests/infrastructure/cache/redis_ai/*.py` to identify all skeleton test files for the `redis_ai` module of the `cache` infrastructure component that require implementation. Then, create a new plan to faithfully execute the prompt described by `docs/prompts/unit-tests/step4-implementation.md` for the discovered test files using the @agent-unit-test-supervisor and @agent-unit-test-implementer agents.
```

> full prompt: `docs/prompts/unit-tests/step4-implementation.md`

* **Guiding Philosophy**: The assistant is instructed to test only the public contract and observable outcomes, adhering to the "Golden Rule" that a good test should pass even if the internal implementation is rewritten.

* **Strict Mocking Strategy**: The prompt explicitly forbids mocking any internal classes, methods, or collaborators within the cache component. Instead, tests must use provided fixtures that represent fakes (e.g., `fakeredis`) or real infrastructure. Mocks are only permitted at true system boundaries.

* **Handling Violations**: If a test skeleton appears to require knowledge of internal implementation details, the assistant is instructed to skip it and recommend rewriting it as an integration test that uses real components. This acts as a quality gate to prevent brittle, implementation-focused tests.

### Step 5: Code Review & Debugging (The "Quality Check")

To perform a final quality check against the core principles, we instruct the assistant to review the code it just wrote, comparing it against the "Good ✅ vs. Bad ❌" examples from Step 1 and refactoring any tests that are still coupled to implementation details.

We also run the test suite to identify errors and failures and work to debug them with the coding assistant.

## 6. Test Implementation Prioritization

When adding new tests or implementing skeleton tests, follow this established priority order to ensure the most critical functionality is always covered first.

#### Immediate Priority (High Business Impact)

1.  **Memory Cache Core Operations** - Foundation for all caching.
2.  **Redis Generic Cache Operations** - Production cache functionality.
3.  **AI Cache Core Operations** - Business-critical AI features.
4.  **Security Configuration** - Production security requirements.

#### Medium Priority

1.  **Performance Monitoring** - Operational visibility.
2.  **Configuration Management** - Deployment flexibility.
3.  **Cache Validation** - Configuration safety.

#### Lower Priority

1.  **Migration Operations** - Utility functionality.
2.  **Benchmarking** - Performance optimization.
3.  **Cache Presets** - Configuration convenience.

## 7. How to Run Tests

To run all tests in this suite, navigate to the repository root, activate the `.venv` virtual environment, and execute:

```bash
# Entire Test Suite
source ./.venv/bin/activate && make test-backend-infra-cache

# Individual Test
cd backend && source ../.venv/bin/activate && python -m pytest [test_file.py]
```

Tests automatically run in parallel by default. See more more settings at `backend/pytest.ini`.
