Use as many as 4 parallel @agent-integration-test-implementer sub-agents to implement all integration tests for the component defined by the public contract at `backend/contracts/core/startup/redis_security.pyi` following our integration testing philosophy as documented in `docs/guides/testing/INTEGRATION_TESTS.md` and the test plan as documented in `backend/tests/integration/startup/TEST_PLAN.md`.

**Priority-Based Implementation Order:**

### Phase 1: Priority 1 Tests (Sprint 1-2)
1. Environment-aware security validation
2. Certificate validation with cryptography
3. Encryption key validation
4. Cryptography unavailability scenarios (reference separate plan)

### Phase 2: Priority 2 Tests (Sprint 3)
1. Comprehensive validation workflow
2. Authentication validation
3. Multi-component error aggregation