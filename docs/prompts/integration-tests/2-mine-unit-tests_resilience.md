# Integration Testing

## Prompt 2: Mine Unit Tests for Integration Opportunities

Analyze unit tests in `backend/tests/unit/resilience/**/*.py` to identify integration testing opportunities. See also `backend/tests/unit/resilience/README.md`. DO NOT convert the unit tests - instead, extract the integration seams they reveal and propose NEW integration tests.

Save the output to `backend/tests/integration/resilience/TEST_PLAN_2.md`

Create a plan and follow the guidance below:

**ANALYSIS OBJECTIVES:**
1. Identify what component boundaries are being mocked in unit tests
2. Extract integration scenarios implied by unit test coverage
3. Map seams between components revealed by dependency injection
4. Identify high-value integration tests that unit tests cannot verify
5. Propose integration test scenarios that complement (not replace) unit tests

**ANALYSIS PROCESS:**

STEP 1: CATALOG MOCKED DEPENDENCIES
For each unit test file, list:
- What components are mocked (cache, database, external APIs, etc.)
- Why they're mocked (external service, slow, test isolation, etc.)
- What interfaces/contracts are being tested

STEP 2: IDENTIFY REVEALED SEAMS
For each mocked dependency, identify:
- SEAM: [Component A] → [Mocked Component B]
- INTERFACE: What methods/operations cross this boundary
- UNIT TEST COVERAGE: What behaviors are verified in isolation
- INTEGRATION GAP: What behaviors require real components to verify

STEP 3: ASSESS INTEGRATION TEST VALUE
For each seam, evaluate:
- BUSINESS CRITICALITY: High/Medium/Low impact on users
- INTEGRATION RISK: What could go wrong when components interact
- UNIT TEST LIMITATIONS: What can't be verified without real integration
- RECOMMENDED: Should this become an integration test? Why?

STEP 4: CROSS-REFERENCE WITH PROMPT 1
For each seam identified:
- Check if Prompt 1 also identified this seam
- If YES: Mark as CONFIRMED (high priority - both architecture and usage support it)
- If NO: Mark as NEW (discovered via unit test analysis, investigate importance)

STEP 5: PROPOSE INTEGRATION TEST SCENARIOS
For HIGH-value seams, propose NEW integration test scenarios:
- TEST NAME: Descriptive name focusing on integration behavior
- SOURCE: CONFIRMED (Prompt 1 + Prompt 3) or NEW (Prompt 3 only)
- INTEGRATION SCOPE: List real components involved
- SCENARIO: What integration behavior to verify
- SUCCESS CRITERIA: Observable outcomes (not internal state)
- PRIORITY: Based on business criticality

**EXAMPLE OUTPUT:**

````markdown
## Unit Test Analysis: TextProcessorService

### Mocked Dependencies Found:

1. **AIResponseCache** - Mocked in 15 unit tests
   - Why mocked: External Redis dependency, test isolation
   - Interface tested: get(), set(), build_key()

2. **PydanticAI Agent** - Mocked in 12 unit tests
   - Why mocked: External API calls, costs, test speed
   - Interface tested: run()

### Integration Seams Revealed:

#### SEAM 1: TextProcessorService → AIResponseCache

**Unit Test Coverage:**
- ✅ Service calls cache.get() before processing
- ✅ Service calls cache.set() after successful processing
- ✅ Service builds correct cache keys with operation + text + options
- ✅ Service passes operation-specific TTLs to cache.set()

**Integration Gap:**
- ❌ Does caching actually improve performance with real Redis?
- ❌ Does cache survive across multiple requests?
- ❌ What happens when Redis connection fails?
- ❌ Do concurrent requests leverage cache correctly?

**Cross-Reference with Prompt 1:**
- STATUS: CONFIRMED (Prompt 1 also identified this seam with HIGH confidence)
- Architectural analysis noted cache as critical performance optimization
- Unit tests confirm heavy cache usage in practice

**Integration Test Value:** HIGH
- Business Critical: Caching reduces AI costs significantly ($$$)
- Integration Risk: Redis connection issues, TTL expiration, cache key collisions
- Unit Test Limitation: Unit tests verify "service uses cache correctly" but cannot verify "caching provides business value with real infrastructure"

**Recommended NEW Integration Tests:**

1. **test_cache_improves_performance_for_repeated_requests**
   - SOURCE: CONFIRMED (Prompt 1 + Prompt 3)
   - SCOPE: TextProcessorService + AIResponseCache + fakeredis
   - SCENARIO: Second identical request hits cache without calling AI
   - SUCCESS CRITERIA:
     * First request: cache_hit=False, AI called once
     * Second request: cache_hit=True, AI not called
     * Second request is significantly faster (< 50ms vs > 100ms)
   - PRIORITY: P0 (HIGH)

2. **test_service_handles_cache_failure_gracefully**
   - SOURCE: NEW (discovered via unit test analysis)
   - SCOPE: TextProcessorService + failing AIResponseCache
   - SCENARIO: Cache connection fails, service continues with AI processing
   - SUCCESS CRITERIA:
     * Request succeeds despite cache failure
     * Warning logged about cache unavailability
     * AI processing completes normally
   - PRIORITY: P1 (MEDIUM - resilience pattern)

#### SEAM 2: TextProcessorService → PydanticAI Agent

**Unit Test Coverage:**
- ✅ Service calls agent with correct prompt
- ✅ Service handles agent response correctly
- ✅ Service propagates agent errors

**Integration Gap:**
- ❌ Real AI responses match expected format
- ❌ Error handling works with real API errors

**Cross-Reference with Prompt 1:**
- STATUS: CONFIRMED (Prompt 1 identified this with MEDIUM confidence)
- Noted as potentially expensive to test

**Integration Test Value:** LOW
- Requires real API keys and costs money per test run
- Better suited for manual/E2E tests with @pytest.mark.manual
- Unit tests with mocks are sufficient for this seam

**Recommendation:** Skip integration tests, document manual testing approach

### Summary

**CONFIRMED Seams** (Prompt 1 + Prompt 3):
1. TextProcessorService → AIResponseCache (HIGH priority integration tests)
2. TextProcessorService → PydanticAI Agent (LOW priority, manual tests better)

**NEW Seams** (Prompt 3 only):
1. Cache failure resilience (discovered via unit test error handling)

**Unit Tests to Keep** (NOT convert):
- ✅ All 15 cache-related unit tests (verify correct cache usage)
- ✅ All 12 agent-related unit tests (verify correct AI interaction)
- These verify component correctness in isolation
- Integration tests will verify different concerns (performance, resilience)

**Integration Tests to Create** (NEW, complementary):
- ✅ test_cache_improves_performance_for_repeated_requests (P0)
- ✅ test_service_handles_cache_failure_gracefully (P1)
- These verify system behavior with real infrastructure
- Cannot be tested by unit tests alone

**Relationship Between Unit and Integration Tests:**

Unit Test Example:
```python
def test_service_stores_in_cache_with_ttl(mock_cache):
    """Verify service calls cache.set() with correct TTL."""
    service = Service(cache=mock_cache)
    service.process("data")
    mock_cache.set.assert_called_with(key="data", ttl=7200)
```
- Purpose: Verify service uses cache API correctly
- Value: Catches incorrect cache usage bugs

Integration Test (NEW, different concern):
```python
async def test_cache_improves_performance(service, real_cache):
    """Verify caching provides business value."""
    result1 = await service.process("data")
    result2 = await service.process("data")
    assert result2.cache_hit is True
    assert result2.processing_time < result1.processing_time * 0.1
```
- Purpose: Verify caching provides performance improvement
- Value: Catches integration bugs (cache not actually working)

Both tests are needed - they verify different concerns at different levels.
````

**IMPORTANT DISTINCTIONS:**

**DO NOT "convert" unit tests:**
- Unit tests have value verifying component behavior in isolation
- "Converting" implies replacing, but both tests are needed
- Unit test can pass while integration test fails (and vice versa)

**DO create NEW integration tests for different concerns:**
- Focus on what unit tests CANNOT verify (real infrastructure behavior)
- Test observable business outcomes (performance, resilience, state)
- Complement unit test coverage, don't duplicate it

**OUTPUT FORMAT:**
For each analyzed component, provide:
1. Mocked Dependencies Catalog
2. Integration Seams Identified
3. Cross-Reference with Prompt 1 (CONFIRMED vs NEW)
4. Integration Test Value Assessment
5. Recommended NEW Integration Test Scenarios (with SOURCE marker)
6. Relationship to Existing Unit Tests (keep vs. complement)

Generate a prioritized list of integration test scenarios that complement existing unit test coverage.