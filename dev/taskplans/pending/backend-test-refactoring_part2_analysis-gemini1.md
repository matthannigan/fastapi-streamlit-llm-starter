Based on a thorough review of your testing philosophy and the provided code, the key recommendation is to reclassify a significant portion of the tests currently in `backend/tests/unit/` as integration tests. Many tests, particularly for the API, middleware, and Redis-based cache layers, are already testing the collaboration between components rather than a single component in isolation. This is a good thing and aligns with your goal of creating robust, behavior-driven tests.

The primary action is to **move** these tests to the appropriate `integration/` subdirectories. A smaller set of tests, like those for `TextProcessorService`, are misaligned with the contract-driven philosophy and should be **discarded and rewritten** from scratch as outside-in integration tests. Finally, several test suites, such as those for `core/environment` and `infrastructure/ai/prompt_builder`, serve as excellent exemplars of your desired unit testing style and should be **kept and used as a reference**.

***

## Guiding Principles Analysis

My recommendations are based on the core principles synthesized from `UNIT_TESTS.md`, `INTEGRATION_TESTS.md`, and `WRITING_TESTS.md`:

* **The Component is the Unit:** A unit test verifies a single, whole component (often a class) in **complete isolation**.
* **Test Contracts, Not Implementation:** Tests should validate the public interface and observable behavior documented in docstrings. They must be resilient to internal refactoring.
* **Mock Only at System Boundaries:** Mocks or fakes are used exclusively for dependencies that cross a system boundary (e.g., external APIs, databases, filesystems). **Internal collaborators are never mocked.**
* **Integration Tests Verify Collaboration:** The purpose of an integration test is to verify that two or more *internal* components work together correctly. They are tested from the "outside-in" against a high-fidelity environment (e.g., using `TestClient` or `fakeredis`).
* **E2E vs. Integration:** The key difference is that integration tests **mock true external third-party services** (like the Gemini API), while E2E tests make **real network calls** to those services.

***

## Detailed Recommendations by Directory

### `backend/tests/unit/api/`

* **Recommendation:** **Move**
* **Action:** Move `test_health_endpoints.py` and `test_main_endpoints.py` to `backend/tests/integration/api/v1/`.
* **Rationale:** These tests use FastAPI's `TestClient` to make HTTP requests to the application. According to your `INTEGRATION_TESTS.md` guide, this is the primary pattern for "outside-in" integration testing. They are not testing a component in isolation but rather the collaboration of the FastAPI router, dependency injection, and the endpoint logic itself. They correctly test the "seam" between the web layer and the application.

### `backend/tests/unit/core/`

* **`environment/`**
    * **Recommendation:** **Keep & Use as Exemplar**
    * **Action:** No changes needed.
    * **Rationale:** These tests are a perfect example of your unit testing philosophy. They test a single component (the environment detector) in isolation. Dependencies on the filesystem (`Path.exists`) and operating system (`os.environ`) are correctly treated as system boundaries and patched. The assertions validate the observable output based on controlled inputs.

* **`middleware/`**
    * **Recommendation:** **Move**
    * **Action:** Move the entire `middleware/` test directory to `backend/tests/integration/core/middleware/`.
    * **Rationale:** Similar to the API tests, these tests use `TestClient` to verify the behavior of middleware in the context of a running FastAPI application. This is fundamentally integration testing, as it validates the collaboration between the middleware and the FastAPI framework's request/response lifecycle.

* **Other `core/` tests (`test_config.py`, `test_dependencies.py`, etc.)**
    * **Recommendation:** **Refactor/Review**
    * **Action:** Keep these in `unit/`, but review them to ensure they align with the "component is the unit" principle.
    * **Rationale:** Tests for `core/config.py` correctly test the `Settings` class in isolation. However, tests in `test_dependencies.py` validate dependency-provider functions (`get_cache_service`, `get_text_processor`) which inherently involve the creation and linking of multiple components. While they use mocks, they are testing the *wiring* of components, which borders on integration testing. A better approach might be to have dedicated integration tests that verify dependency injection works correctly from the API boundary down.

### `backend/tests/unit/infrastructure/`

* **`ai/` (`test_prompt_builder.py`, `test_sanitization.py`)**
    * **Recommendation:** **Keep & Use as Exemplar**
    * **Action:** No changes needed.
    * **Rationale:** These are excellent unit tests. They validate pure, stateless functions (`create_safe_prompt`) or single, isolated components (`PromptSanitizer`) with no external dependencies. They focus entirely on inputs and observable outputs, perfectly matching your contract-driven philosophy. The placeholder files (`test_client.py`, `test_gemini.py`) should be implemented following this pattern.

* **`cache/` (excluding `redis_ai` and `redis_generic`)**
    * **Recommendation:** **Keep**
    * **Action:** Most files here are well-placed unit tests.
    * **Rationale:** Tests for `base/`, `key_generator/`, `memory/`, `monitoring/`, and `parameter_mapping/` largely follow the unit test philosophy. They test a single component's logic in isolation. For instance, `key_generator/test_key_generator.py` correctly tests the `CacheKeyGenerator`'s contract without mocking its internal methods.

* **`cache/redis_ai/` and `cache/redis_generic/`**
    * **Recommendation:** **Move & Refactor**
    * **Action:** Move these entire test directories to `backend/tests/integration/infrastructure/cache/`. Refactor them to consistently use a high-fidelity `fakeredis` fixture instead of `MagicMock`.
    * **Rationale:** Any test that requires a Redis client—even a fake one—is testing the integration between your Python code and the Redis data store. This is the definition of an integration test as per your guides. Your current tests for these components correctly test behavior but are miscategorized as unit tests. Moving them clarifies their purpose and separates them from the faster, in-memory unit tests.

* **`resilience/`**
    * **Recommendation:** **Refactor & Split**
    * **Action:**
        1.  Move `test_resilience_integration.py` to `backend/tests/integration/infrastructure/resilience/`.
        2.  Move `test_performance_benchmarks.py` to `backend/tests/performance/`.
        3.  Keep the remaining files in `unit/`, as they correctly test the configuration, validation, and migration logic of the resilience component in isolation.
    * **Rationale:** The `infrastructure_review.md` file has already correctly identified this. The integration and performance tests are misplaced. The other files (`test_resilience.py`, `test_presets.py`, `test_validation_schemas.py`) are excellent examples of unit tests that validate the contract of the resilience configuration system without mocking internal collaborators.

* **`security/`**
    * **Recommendation:** **Refactor/Split**
    * **Action:** Split the tests. Tests that validate the logic of `APIKeyAuth` or `AuthConfig` in isolation (using fakes for settings) should remain in `unit/`. Tests that use dependencies like `verify_api_key_http` to validate behavior against a `TestClient` are integration tests and should be moved to `backend/tests/integration/infrastructure/security/`.
    * **Rationale:** This directory contains a mix. For example, `test_api_key_auth.py` correctly tests the `APIKeyAuth` class logic in isolation and belongs in `unit/`. However, any test that validates a FastAPI dependency (`Depends(...)`) within a request-response cycle is an integration test.

### `backend/tests/unit/services/`

* **`test_text_processing.py` and `test_response_validator.py`**
    * **Recommendation:** **Discard/Rewrite**
    * **Action:** These tests should be rewritten from scratch as integration tests located in `backend/tests/integration/services/` or as part of the API-level integration tests.
    * **Rationale:** These tests are the most significant violators of your stated philosophy. `test_text_processing.py` heavily mocks its primary collaborators (`AIResponseCache` and `Agent`). It tests that the service *calls its mocks correctly*, not that the *service fulfills its contract*. An internal refactoring of how `TextProcessorService` uses the cache would break these tests, even if the user-facing behavior is identical. The correct approach is an integration test that:
        1.  Initializes a *real* `TextProcessorService`.
        2.  Provides it with a *fake* `AIResponseCache` (like `InMemoryCache` or `fakeredis`).
        3.  Mocks only the true external boundary: the call to the Gemini API inside the `Agent`.
        4.  Asserts on the observable outcome: the `TextProcessingResponse` object and the state of the fake cache.
