# Backend Test Suite Refactoring — Part 2 Analysis (gpt-5)

Date: 2025-09-18
Scope: backend/tests and the testing guides

This document provides detailed recommendations for reorganizing, refactoring, and selectively discarding backend tests to align with the project’s behavior-driven, contract-focused testing philosophy.

Inputs reviewed
- docs/guides/testing/UNIT_TESTS.md
- docs/guides/testing/INTEGRATION_TESTS.md
- docs/guides/testing/WRITING_TESTS.md
- Inventory and spot reads of backend/tests/**/*

Executive summary
- Most tests are already under unit/, integration/, e2e/, performance/, and manual/ with sensible grouping.
- Several files are mis-categorized (primarily “integration” tests living under unit/). These should be relocated.
- A handful of API tests rely on heavy internal mocking and extremely flexible assertions. These undermine contract-driven testing and should be discarded and rewritten from scratch as clean, contract-based integration tests.
- Many tests assert on implementation details (assert_called*, call counts). These should be refactored to assert only observable behavior per the published contracts (Args, Returns, Raises, Behavior), using high-fidelity fakes at boundaries.

What each test tier should cover (from the guides)
- Unit: One component in complete isolation; mock only true externals; verify public contract and observable outcomes; very fast.
- Integration: Collaboration of 2–3 internal components or API→Service→Infra seam; minimal mocking (only externals), prefer high-fidelity fakes; verify seams from outside-in.
- E2E: Full application workflows with real external services (or sanctioned sandbox), minimal to no mocking; slower; validates user journeys.

A. Relocation recommendations (move tests to correct tier folders)
Legend: → denotes target folder suggestion under backend/tests

1) Move to integration/
These files test API endpoints with TestClient or verify collaboration across multiple internal components:
- unit/api/v1/test_health_endpoints.py → integration/api/v1/
- unit/api/v1/test_main_endpoints.py → integration/api/v1/
- unit/core/middleware/test_integration.py → integration/core/middleware/
- unit/core/middleware/test_enhanced_middleware_integration.py →
  - Split: the core interaction tests → integration/core/middleware/
  - Performance-marked tests/classes (e.g., TestMiddlewarePerformance) → performance/core/middleware/
- unit/infrastructure/cache/redis_generic/test_callback_system_integration.py → integration/cache/redis_generic/
- unit/infrastructure/resilience/test_resilience_integration.py → integration/infrastructure/resilience/
- api/internal/test_resilience_endpoints.py → integration/api/internal/
  - Note: See Section C (Discard & rewrite). This file is a transitional amalgam with heavy internal mocking and flexible assertions; do not move as-is—rewrite in the integration folder.

2) Keep in e2e/
Existing e2e tests generally look correct and should remain:
- e2e/cache/**/* (cache workflows, preset-driven behavior, enhanced monitoring)
- e2e/test_backward_compatibility.py

3) Keep in integration/
Existing integration tests are appropriately placed; retain:
- integration/api/internal/**/*
- integration/api/v1/**/*
- integration/cache/**/*
- integration/test_request_isolation.py
- integration/test_resilience_integration2.py
  - See Section B.2 for targeted refactors (remove overly flexible assertions and MagicMock usage where unnecessary; prefer real preset objects and deterministic expectations).

4) Keep in unit/
The majority of tests under unit/ appear correctly scoped as behavioral unit tests. Notable areas to leave in unit/ include:
- unit/core/**/* (except the two integration-labeled files listed above)
- unit/infrastructure/**/* (except the two integration/performance misplacements noted above)
- unit/services/**/* (but refactor style per Section B.3)
- unit/shared_schemas/**/*

5) Move to performance/
These are performance/benchmark-style tests and should not live under unit/:
- unit/infrastructure/resilience/test_performance_benchmarks.py → performance/resilience/
- Keep existing: performance/test_health_check_performance.py

6) Leave manual/ as-is
- manual/test_manual_api.py remains under manual/ and out of automated tiers.

B. Refactor recommendations (toward contract-driven behavioral testing)

B.1 API integration tests (endpoints)
- Files: integration/api/v1/*, integration/api/internal/*, and the to-be-rewritten api/internal/test_resilience_endpoints.py
  - Replace flexible assertions (e.g., status_code in [200, 500, 404]) with exact, contract-driven expectations. If the contract is uncertain, define it in docstrings/schemas and then assert precisely.
  - Avoid mocking internal infrastructure/services (e.g., app.infrastructure.resilience.ai_resilience). Only mock true external services/networks. Use fakes for internal infra (fakeredis, in-memory repos) per the Integration Tests guide.
  - Prefer snapshot testing (e.g., syrupy) for complex JSON responses to validate the API contract holistically. This reduces brittle, field-by-field assertions and locks the response schema.
  - Ensure auth paths rely on realistic authentication fixtures (valid/invalid tokens as inputs) rather than mocking internal auth functions. Assert observable behavior (401 vs 200 and response structure).

B.2 Integration tests for resilience and presets
- Files: integration/test_resilience_integration2.py, integration/api/internal/test_resilience_*_endpoints.py
  - Reduce MagicMock usage to the minimal boundary. When verifying preset selection → service config → endpoint behavior, use real preset objects and real configuration transformations. Assert on the observable results (e.g., config values propagated to endpoints, circuit breaker state transitions) not on internal call counts.
  - Replace any flexible range assertions that are non-deterministic with crisp expectations derived from documented contracts (UNIT_TESTS/INTEGRATION_TESTS guidelines). If timing-sensitive, mock time deterministically.

B.3 Service unit tests (text processing)
- File: unit/services/test_text_processing.py
  - Anti-patterns detected: multiple assert_called*, heavy mocking of internal collaborators.
  - Refactor to match unit testing principles:
    - Treat TextProcessorService as the unit. Mock only true external boundaries (e.g., AI provider HTTP calls). Keep internal sanitization/validation behaviors real to preserve component integrity.
    - Assert only observable outcomes: returned response DTOs, raised exceptions, and side effects on injected external dependencies (e.g., cache interactions can be validated via cache fake observable state rather than call counts).
    - Use contract-derived scenarios (invalid operation → ValidationError; QA operation requires question; etc.).

B.4 Security/auth unit tests
- Files: unit/infrastructure/security/test_auth_*.py, test_auth_utilities.py, test_auth_dependencies.py
  - Reduce assert_called/interaction assertions that tie tests to internal implementation.
  - Prefer environment/context fixtures to exercise behavior (e.g., production vs development), asserting on outcomes (errors raised, returns) rather than internal method invocation counts.

B.5 Middleware tests
- Files: unit/core/middleware/*
  - For single-middleware tests, using a minimal FastAPI harness is an acceptable “unit” harness. Keep assertions on externally observable effects: headers added, status codes, response encodings. Avoid asserting that internal middleware methods were called.
  - For multi-middleware interaction tests (already flagged for relocation), split into:
    - Integration tests (stack interactions, header propagation, error layering)
    - Performance tests (@pytest.mark.slow) in performance/
  - Replace any time.sleep with deterministic time control or simplified conditions. Remove print statements; rely on explicit assertions.

B.6 Cache infrastructure tests
- Files: unit/infrastructure/cache/**/*, integration/cache/**/*
  - Where unit tests connect to a real Redis or rely on Redis-specific semantics, move those to integration and use Testcontainers or an approved fake that supports needed features.
  - Contract-style unit tests should verify CacheInterface behavior via fakes, focusing on observable semantics (set/get/exists/delete, TTL expiration with deterministic time control, serialization guarantees) and avoid asserting internal Redis client calls.

B.7 General refactoring patterns to apply broadly
- Replace assert_called*, assert_called_once*, assert_called_once_with, and call_count-style assertions that target internal implementation with assertions on observable outcomes.
- Remove flexible assertions that accept multiple status codes or wildly varying shapes. Lock down exact contracts via docstrings and snapshots.
- Eliminate time.sleep in tests. Use deterministic time mocking or make operations synchronous for tests.
- Use high-fidelity fakes at the system boundary: fakeredis for cache; in-memory stores for repositories.
- Ensure every test has a succinct docstring describing:
  - Verifies: Specific contract guarantee
  - Business Impact: Why the behavior matters
  - Given/When/Then or clear scenario framing

C. Discard and rewrite from scratch
These tests should be replaced with clean, contract-driven suites (the cost to fix outweighs the benefit of incremental refactoring):

1) backend/tests/api/internal/test_resilience_endpoints.py
- Issues:
  - Heavy internal mocking of resilience services (mocking internal providers breaks our integration testing philosophy).
  - Extremely flexible assertions (e.g., allowing 200, 404, 500 interchangeably) that bypass contract validation.
  - Transitional notes (merging old files) suggest historical drift and unclear scope.
- Replacement approach:
  - Write integration tests that drive the endpoints via TestClient without mocking internal resilience, using real configs/presets (or high-fidelity fakes for external-only boundaries).
  - Adopt snapshot testing for response payloads and assert exact status codes per API contract.

2) Optional: integration/test_resilience_integration2.py — partial rewrite recommended
- Rationale:
  - Currently uses MagicMocks and flexible assertions in places. While not a full discard, re-author tests to consume real preset objects, deterministic values, and exact response/behavior contracts. If rewriting is simpler than chasing brittle expectations, prefer rewrite.

D. Keep-as-is (no move) with minor polish
- e2e/cache/**/*: Looks correctly scoped; ensure minimal mocking and prefer snapshot assertions for response bodies.
- integration/api/v1/test_auth_endpoints.py and test_text_processing_endpoints.py: Keep; consider snapshot testing for complex JSON responses and explicit auth contract assertions.
- unit/shared_schemas/**/*: Good unit-level tests for Pydantic models/validators; maintain clear contract coverage.

E. Directory structure and naming guidance
- Maintain top-level separation: unit/, integration/, e2e/, performance/, manual/
- For moved middleware tests:
  - integration/core/middleware/ for multi-middleware interactions
  - performance/core/middleware/ for marked slow/perf tests
- For cache tests:
  - unit/infrastructure/cache/ for contract-focused behavior with fakes
  - integration/cache/ for real Redis semantics or multi-component flows
- Keep API-level tests under integration/api/v1 and integration/api/internal (outside-in focus).

F. Concrete move list (actionable checklist)
Move to integration/
- unit/api/v1/test_health_endpoints.py → integration/api/v1/
- unit/api/v1/test_main_endpoints.py → integration/api/v1/
- unit/core/middleware/test_integration.py → integration/core/middleware/
- unit/core/middleware/test_enhanced_middleware_integration.py → integration/core/middleware/ (split perf to performance/)
- unit/infrastructure/cache/redis_generic/test_callback_system_integration.py → integration/cache/redis_generic/
- unit/infrastructure/resilience/test_resilience_integration.py → integration/infrastructure/resilience/
- api/internal/test_resilience_endpoints.py → integration/api/internal/ (discard and rewrite there)

Move to performance/
- unit/infrastructure/resilience/test_performance_benchmarks.py → performance/resilience/
- From test_enhanced_middleware_integration.py: move @pytest.mark.slow performance classes/tests → performance/core/middleware/

No move (confirm placement)
- e2e/**/*, integration/**/* (except those explicitly listed), unit/**/* (except those explicitly listed), performance/**/*, manual/**/*

G. Example refactors (file-specific notes)
- unit/services/test_text_processing.py
  - Remove internal collaborator mocks and call-count assertions; mock only external AI provider.
  - Validate responses and raised exceptions per docstring contract (e.g., QA requires question; invalid operation raises ValidationError).
- integration/api/v1/test_text_processing_endpoints.py
  - Add snapshot tests for full JSON response; assert concrete status codes and headers.
  - Ensure no internal service mocking; introduce high-fidelity fakes for external boundaries only (if any).
- unit/infrastructure/security/test_auth_utilities.py
  - Replace assert_called* with behavior assertions: returns, raised errors, and derived header/token parsing.
  - Use environment fixtures (monkeypatch) to drive production/development paths deterministically.
- unit/core/middleware/test_compression_middleware.py and test_rate_limiting_middleware.py
  - Remove time.sleep; mock time or use deterministic counters.
  - Assert external results (content-encoding headers, 429s with specific error codes, versioning headers) over internal method interactions.
- integration/test_resilience_integration2.py
  - Use real preset objects; assert exact propagated config and endpoint behavior. Reduce MagicMock to the boundary only.

H. Next steps (suggested order of operations)
1) Relocate miscategorized tests (Section F) to establish a clean baseline by tier.
2) Discard and rewrite backend/tests/api/internal/test_resilience_endpoints.py as contract-driven integration tests with snapshots.
3) Refactor service and security unit tests to remove implementation-coupled assertions; adopt contract-driven scenarios.
4) Split integration/performance concerns in middleware tests; eliminate sleeps and prints; add deterministic assertions.
5) Introduce snapshot testing where payloads are complex (API integration and E2E).
6) Run make test-backend and iterate on any flakiness (eliminate timing dependencies and flexible assertions).

This plan aligns the suite with the documented philosophy: behavior-driven, contract-focused verification, mocking only at true external boundaries, and a clear tiered structure for unit vs. integration vs. E2E vs. performance vs. manual tests.
