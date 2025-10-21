# Text Processor Unit Test Suite Quality Report

**Component Under Test**: `TextProcessorService`
**Public Contract**: `backend/contracts/services/text_processor.pyi`
**Test Suite Location**: `backend/tests/unit/text_processor/`
**Date**: 2025-10-19
**Review Standard**: Behavior-driven unit testing principles from `docs/guides/testing/`

---

## Executive Summary

The text_processor unit test suite demonstrates **strong adherence to behavior-driven testing principles** with comprehensive contract coverage and proper isolation through fakes/mocks. The test suite contains **217 test methods** across 6 test files covering initialization, core functionality, error handling, caching, and batch processing.

**Overall Quality Score**: **8.5/10**

**Key Strengths**:
- Excellent public contract focus following the .pyi file
- Proper use of high-fidelity fakes (FakeCache, FakePromptSanitizer)
- Comprehensive docstrings with business impact and test scenarios
- Good test organization by functional area
- Appropriate mocking of external dependencies only (PydanticAI Agent, ai_resilience)

**Key Recommendations**:
1. **Transform caching behavior tests into integration tests** (25-30 tests) - these test text_processor collaboration with cache infrastructure
2. **Address 5 xfail tests** to achieve 100% passing rate
3. **Consider integration tests for resilience orchestrator collaboration** (currently properly mocked)

---

## Test Suite Structure

### Test Files Analysis

| File | Test Count | Purpose | Quality |
|------|------------|---------|---------|
| `test_initialization.py` | ~25 | Service initialization, config validation | ✅ Excellent |
| `test_core_functionality.py` | ~40 | Core operations (SUMMARIZE, SENTIMENT, etc.) | ✅ Excellent |
| `test_error_handling.py` | ~30 | Input validation, AI failures, fallbacks | ✅ Excellent |
| `test_caching_behavior.py` | ~60 | Cache-first strategy, TTL, key generation | ⚠️ Should be integration |
| `test_batch_processing.py` | ~60 | Concurrent batch processing | ✅ Very Good |
| `conftest.py` | N/A | Test fixtures and fakes | ✅ Excellent |

---

## Principle Adherence Assessment

### ✅ Principle 1: Test Behavior, Not Implementation (Score: 9/10)

**Strengths**:
- Tests focus on public `process_text()` and `process_batch()` methods from the .pyi contract
- Tests verify observable outcomes (response fields, status codes, exceptions)
- Good use of Given/When/Then structure in docstrings
- Tests validate contract requirements (Args validation, Returns structure, Raises conditions)

**Example of Excellence**:
```python
async def test_process_text_summarize_returns_result_field(self, test_settings, fake_cache, mock_pydantic_agent):
    """Verifies: SUMMARIZE operation returns response with result field"""
    # Tests observable outcome - result field population, not how it's done
    response = await service.process_text(request)
    assert response.result is not None
    assert response.sentiment is None  # Only result field populated
```

**Minor Issues**:
- A few tests reference internal implementation patterns (e.g., checking cache key format details)
- Some test names could better describe *what* behavior is being verified vs *how*

**Recommendation**: Continue this excellent pattern. The few minor deviations don't impact maintainability.

---

### ✅ Principle 2: Mock Only at System Boundaries (Score: 9/10)

**Strengths**:
- Excellent use of high-fidelity **FakeCache** (stateful in-memory implementation) instead of mocks
- Excellent use of **FakePromptSanitizer** for tracking sanitization calls
- Proper mocking of true external dependencies:
  - `mock_pydantic_agent` - External PydanticAI library
  - `mock_response_validator` - External service component
  - `mock_ai_resilience` - Infrastructure singleton orchestrator
- **No mocking of internal text_processor methods** - perfect adherence

**Example of Excellence**:
```python
@pytest.fixture
def fake_cache():
    """High-fidelity fake cache with stateful behavior"""
    return FakeCache()  # Real cache interface implementation, not Mock()
```

**Critical Observation**:
The use of `FakeCache` instead of mocking Redis directly is **exemplary**. This provides realistic cache behavior while maintaining test isolation and speed.

**Recommendation**: This is best-in-class mocking strategy. No changes needed.

---

### ⚠️ Principle 3: Test from the Outside-In (Score: 7/10)

**Strengths**:
- All tests invoke public methods: `process_text()`, `process_batch()`
- Tests never call private methods like `_summarize_text()`, `_build_cache_key()` directly
- Tests verify end-to-end behavior through public API

**Areas for Improvement**:
The **caching behavior tests** (`test_caching_behavior.py`) are actually **integration tests** that should be in `tests/integration/`:

**Why these are integration tests, not unit tests**:

1. **They test collaboration between TextProcessorService and Cache infrastructure**:
   ```python
   async def test_cache_hit_returns_cached_response_without_ai_call(...)
       # This tests text_processor + cache collaboration
       # Cache is an infrastructure service, text_processor is a domain service
   ```

2. **They verify the seam between domain and infrastructure**:
   - `test_cache_key_includes_operation_type()` - Tests cache key generation integration
   - `test_summarize_operation_uses_configured_ttl()` - Tests TTL storage integration
   - `test_first_request_stores_second_request_hits_cache()` - Tests complete cache workflow

3. **Per INTEGRATION_TESTS.md, "Integration tests verify component collaboration"**:
   > "Integration tests verify the collaborative behavior of two or more internal components as they work together to fulfill a specific use case"

**Tests that should be integration tests** (~25-30 tests):
- Entire `TestTextProcessorCachingStrategy` class (cache-first workflow)
- Entire `TestTextProcessorCacheKeyGeneration` class (text_processor → cache collaboration)
- Entire `TestTextProcessorCacheTTLManagement` class (TTL storage collaboration)
- `TestTextProcessorBatchCaching` class (batch + cache collaboration)

**Tests that should remain unit tests**:
- All tests in `test_initialization.py` - Testing service setup
- All tests in `test_core_functionality.py` - Testing operation dispatch and response population
- All tests in `test_error_handling.py` - Testing fallback logic
- Batch processing tests that don't focus on caching specifically

**Recommendation**:
Move caching behavior tests to `tests/integration/text_processor_cache_integration.py`. This would:
- Improve conceptual clarity (unit tests = isolated component, integration = collaboration)
- Allow using `AIResponseCache` instead of `FakeCache` for more realistic integration testing
- Free up unit tests to focus purely on text processing logic

---

## Contract Coverage Analysis

### Public Methods from `.pyi` Contract

| Method | Contract Element | Test Coverage | Quality |
|--------|------------------|---------------|---------|
| `__init__()` | Settings, cache, optional deps | ✅ 8 tests | Excellent |
| `process_text()` | All 5 operations | ✅ 25+ tests | Excellent |
| `process_text()` | Input validation | ✅ 5 tests | Excellent |
| `process_text()` | Exception handling | ✅ 15 tests | Excellent |
| `process_text()` | Caching behavior | ⚠️ 30 tests | Should be integration |
| `process_batch()` | Concurrent processing | ✅ 20 tests | Very Good |
| `process_batch()` | Batch aggregation | ✅ 10 tests | Excellent |

### Docstring Contract Coverage

✅ **Args Section**: Input validation extensively tested
✅ **Returns Section**: Response structure verification comprehensive
✅ **Raises Section**: All exception conditions tested (ValueError, ServiceUnavailableError, ValidationError)
✅ **Behavior Section**: Observable behaviors well-covered (cache-first, fallback, logging)
✅ **Examples Section**: Docstring examples validated through tests

**Coverage Score**: **95%** - Missing only indirect private method behaviors that shouldn't be tested in unit tests anyway.

---

## Test Quality Deep Dive

### Fixture Quality (conftest.py): ✅ Excellent (10/10)

**Strengths**:
- **FakeCache**: Stateful, realistic cache implementation with hit/miss tracking
- **FakePromptSanitizer**: Tracks sanitization calls without complex validation logic
- **Mock specifications**: Uses `create_autospec()` for proper spec'd mocks
- Convenience fixtures for common scenarios (`fake_cache_with_hit`, `mock_response_validator_with_failure`)

**Example of Excellence**:
```python
class FakeCache:
    """High-fidelity fake with realistic state management"""
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._hit_count = 0  # Verification helpers
        self._miss_count = 0
```

This is **textbook** fake implementation following testing best practices.

---

### Test Initialization Suite: ✅ Excellent (9/10)

**Strengths**:
- Tests all initialization scenarios (valid settings, memory cache fallback, missing API key)
- Verifies operation registry validation indirectly
- Tests resilience registration behavior
- Comprehensive docstrings with business impact

**Example**:
```python
def test_initialization_validates_operation_registry(...)
    """Tests _validate_operation_registry() indirectly through initialization"""
    # ✅ Tests observable behavior (successful init) not internal validation logic
```

**Minor Issue**:
- `test_initialization_with_missing_gemini_api_key_raises_error()` uses `os.environ` directly instead of `monkeypatch` (anti-pattern per backend/CLAUDE.md)

**Recommendation**: Update environment variable handling to use `monkeypatch.setenv()`.

---

### Core Functionality Tests: ✅ Excellent (9/10)

**Strengths**:
- Comprehensive coverage of all 5 operations (SUMMARIZE, SENTIMENT, KEY_POINTS, QUESTIONS, QA)
- Tests response field population per operation type
- Tests operation dispatch routing
- Excellent use of Given/When/Then structure

**Example of Excellence**:
```python
async def test_process_text_sentiment_returns_sentiment_result(...)
    """Test SENTIMENT operation populates sentiment field with SentimentResult"""
    # Given: SENTIMENT request
    # When: process_text() is called
    # Then: Response contains sentiment field, others are None
    assert response.sentiment.sentiment == "positive"
    assert response.result is None  # Other fields correctly None
```

**Minor Issues**:
- 2 tests marked as `@pytest.mark.skip` due to complex integration needs
- Some tests have very long setup code (could benefit from additional fixtures)

---

### Error Handling Tests: ✅ Excellent (9/10)

**Strengths**:
- Comprehensive coverage of validation errors, AI failures, fallback responses
- Tests graceful degradation with fallback metadata
- Operation-specific fallback testing (string, list, SentimentResult)
- Excellent test of error isolation in degraded scenarios

**Example of Excellence**:
```python
async def test_sentiment_fallback_returns_neutral_sentiment(...)
    """Test SENTIMENT fallback generates neutral SentimentResult"""
    # ✅ Tests observable fallback behavior, not internal _get_fallback_sentiment()
    assert response.sentiment.sentiment == "neutral"
    assert response.metadata["service_status"] == "degraded"
```

**Issue**:
- 1 test marked `@pytest.mark.xfail` due to circuit breaker integration complexity
  - **This is actually appropriate** - circuit breaker state is infrastructure concern

**Recommendation**: Document why the xfail test is acceptable (tests infrastructure collaboration that belongs in integration tests).

---

### Caching Behavior Tests: ⚠️ Should Be Integration Tests (6/10 for unit test suite)

**Why These Should Be Integration Tests**:

According to `docs/reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md`:
- **Cache** is an **infrastructure service** (production-ready, business-agnostic)
- **TextProcessorService** is a **domain service** (educational example)

According to `docs/guides/testing/INTEGRATION_TESTS.md`:
> "Integration tests verify the collaborative behavior of two or more internal components"

**These tests verify text_processor ↔ cache collaboration**:

1. **Cache-first strategy tests** - Tests how text_processor uses cache:
   ```python
   test_cache_hit_returns_cached_response_without_ai_call()
   # Tests: text_processor checks cache → cache returns → text_processor skips AI
   ```

2. **Cache key generation tests** - Tests integration boundary:
   ```python
   test_cache_key_includes_operation_type()
   # Tests: text_processor → cache.build_cache_key() → cache stores with key
   ```

3. **TTL management tests** - Tests storage integration:
   ```python
   test_summarize_operation_uses_configured_ttl()
   # Tests: text_processor → cache.set(key, value, ttl=7200)
   ```

**Impact**: These are **well-written tests** but in the **wrong test directory**. They belong in `tests/integration/`.

**What Would Change**:
- Move to `tests/integration/text_processor_cache_integration.py`
- Optionally use `AIResponseCache` with `fakeredis` instead of `FakeCache` for more realistic testing
- Update docstrings to emphasize "Integration Scope: TextProcessorService + Cache collaboration"

**Unit tests would still test**:
- That process_text() returns responses (without focusing on cache mechanics)
- That fallbacks work when cache misses occur
- Core operation logic

---

### Batch Processing Tests: ✅ Very Good (8/10)

**Strengths**:
- Comprehensive concurrent processing tests
- Tests concurrency semaphore limiting
- Tests error isolation between requests
- Tests batch result aggregation

**Issues**:
- 3 tests marked `@pytest.mark.xfail` with detailed explanations:
  1. `test_process_batch_isolates_individual_request_failures` - Call count issue with resilience retries
  2. `test_process_batch_includes_error_messages_for_failures` - Partial graceful degradation update
  3. `test_batch_processing_logs_start_and_completion` - Log message format mismatch

**Positive Note**: The xfail reasons are **exceptionally well-documented**, explaining:
- Root cause of failure
- Why the test design is incompatible
- What needs to be fixed

**Example**:
```python
@pytest.mark.xfail(
    reason="Test design incompatible with graceful degradation and resilience patterns. "
           "Issue: Test uses call_count to selectively fail requests #2 and #4, but resilience "
           "layer retries failed operations multiple times, causing call_count to increment "
           "unpredictably..."
)
```

**Recommendation**:
1. Fix or remove the 3 xfail tests to achieve 100% passing suite
2. Consider if some batch+cache tests should also be integration tests

---

## Integration vs Unit Test Assessment

### Tests That Should Be Integration Tests

Based on the definition: "Integration tests verify that multiple components collaborate correctly when working together to fulfill a use case."

#### 1. **Cache Collaboration Tests** (HIGH PRIORITY to move)

**From `test_caching_behavior.py`**:

| Test Class | Tests to Move | Reason |
|------------|---------------|---------|
| `TestTextProcessorCachingStrategy` | ALL 6 tests | Tests text_processor + cache workflow collaboration |
| `TestTextProcessorCacheKeyGeneration` | ALL 5 tests | Tests text_processor → cache.build_cache_key() integration |
| `TestTextProcessorCacheTTLManagement` | ALL 5 tests | Tests text_processor → cache.set(ttl) integration |
| `TestTextProcessorCacheBehaviorIntegration` | ALL 3 tests | Explicitly named "integration" - tests complete cache workflow |

**Total**: ~19 tests should move to integration

**Specific examples**:
```python
# INTEGRATION TEST - Tests text_processor + cache collaboration
test_cache_hit_returns_cached_response_without_ai_call()
test_cache_miss_triggers_ai_processing_and_stores_result()
test_first_request_stores_second_request_hits_cache()

# INTEGRATION TEST - Tests cache key generation seam
test_cache_key_includes_operation_type()
test_cache_key_includes_text_content()
test_cache_key_generation_delegates_to_cache_service()

# INTEGRATION TEST - Tests TTL storage integration
test_summarize_operation_uses_configured_ttl()
test_different_operations_use_different_ttls()
```

**From `test_batch_processing.py`**:

| Test Class | Tests to Move | Reason |
|------------|---------------|---------|
| `TestTextProcessorBatchCaching` | ALL 3 tests | Tests batch + cache collaboration |

**Total**: ~3 tests should move to integration

**Specific examples**:
```python
# INTEGRATION TEST - Tests batch + cache workflow
test_batch_requests_can_hit_cache_individually()
test_batch_stores_successful_results_in_cache()
test_duplicate_requests_in_batch_leverage_cache()  # Already xfail
```

#### 2. **Resilience Orchestrator Collaboration** (Consider for integration tests)

**Currently properly mocked** - These tests correctly mock `ai_resilience` at the system boundary:

```python
# CURRENT UNIT TEST - Correctly mocks ai_resilience
def test_initialization_registers_operations_with_resilience(mock_ai_resilience):
    # Verifies registration calls occurred - tests interface, not integration
    mock_ai_resilience.register_operation.assert_called()
```

**Recommendation**:
- **Keep unit tests as-is** with mocked `ai_resilience`
- **Add integration tests** (`tests/integration/text_processor_resilience_integration.py`) to verify:
  - Actual retry behavior with real resilience orchestrator
  - Circuit breaker state transitions
  - Fallback triggering under real failure scenarios

These would test the **seam** between text_processor and resilience infrastructure.

---

### Summary of Test Relocation

**Recommended moves**:

1. **Create** `tests/integration/text_processor_cache_integration.py`:
   - Move ~22 caching collaboration tests from `test_caching_behavior.py` and `test_batch_processing.py`
   - Optionally upgrade from FakeCache to AIResponseCache with fakeredis
   - Update docstrings: Add "Integration Scope: TextProcessorService + Cache collaboration"

2. **Keep in unit tests**:
   - Initialization tests (verifying service setup)
   - Core functionality tests (operation logic without cache focus)
   - Error handling and fallback tests (without cache focus)
   - Batch processing core tests (concurrency, aggregation without cache focus)
   - All tests with mocked external dependencies

3. **Consider creating** `tests/integration/text_processor_resilience_integration.py`:
   - Test retry behavior with real orchestrator
   - Test circuit breaker integration
   - Test fallback triggering
   - Test operation-specific resilience strategies

**Impact on test suite**:
- Unit tests: ~195 tests (from 217) - **Faster execution, clearer purpose**
- Integration tests: ~22 new tests - **Better conceptual clarity**
- **Total coverage remains the same** - just better organized

---

## Test Documentation Quality: ✅ Excellent (9/10)

**Strengths**:
- Comprehensive docstrings following DOCSTRINGS_TESTS.md standards
- Includes "Business Impact" sections explaining why tests matter
- Clear "Scenario" sections with Given/When/Then structure
- "Fixtures Used" sections document dependencies
- "Observable Behavior" sections explain what's being verified

**Example of Excellence**:
```python
async def test_cache_hit_returns_cached_response_without_ai_call(...):
    """
    Test cache hit returns cached response immediately without AI processing.

    Business Impact:
        Reduces AI API costs and improves response times by serving cached
        responses for repeated requests without AI service calls.

    Scenario:
        Given: Fake cache pre-populated with response for specific request
        When: process_text() is called
        Then: Cached response is returned immediately
        And: response.cache_hit is True
        And: AI agent is not called
    """
```

This is **exemplary** test documentation.

**Minor Issue**:
- Some xfail tests have reason text exceeding docstring (could move to separate doc)

---

## Xfail Tests Analysis

### 5 Tests Marked as `@pytest.mark.xfail`

| Test | File | Reason | Should Fix? |
|------|------|---------|-------------|
| `test_circuit_breaker_open_prevents_ai_calls` | error_handling | Technical limitation: Circuit breaker bound at class definition | ⚠️ Expected - integration test needed |
| `test_process_batch_isolates_individual_request_failures` | batch_processing | Call count incompatible with retry logic | ✅ Yes - redesign test |
| `test_process_batch_includes_error_messages_for_failures` | batch_processing | Partial graceful degradation update | ✅ Yes - complete update |
| `test_batch_processing_logs_start_and_completion` | batch_processing | Log message format mismatch | ✅ Yes - align with actual logs |
| `test_duplicate_requests_in_batch_leverage_cache` | batch_processing | Known cache race condition | ⚠️ Expected - architectural limitation |

**Positive**: All xfail reasons are **exceptionally well-documented** with:
- Root cause explanation
- Why current design is incompatible
- What needs to be fixed

**Recommendation**:
1. **Fix 3 tests** (batch isolation, error messages, logging) - These are test design issues
2. **Keep 2 xfails** (circuit breaker, duplicate cache) - These test architectural limitations appropriately
3. **Add integration tests** for the 2 expected xfails to properly test those behaviors

---

## Skipped Tests Analysis

### 2 Tests Marked as `@pytest.mark.skip`

Both in `test_core_functionality.py`:

1. `test_process_text_sanitizes_input_before_processing`:
   - Reason: "Test requires complex PromptSanitizer integration beyond basic Agent mocking"
   - **Recommendation**: This is actually testable in unit tests - use the `fake_prompt_sanitizer` fixture

2. `test_process_text_validates_response_before_returning`:
   - Reason: "Test requires complex ResponseValidator integration beyond basic Agent mocking"
   - **Recommendation**: This is also testable - inject `mock_response_validator` and verify it's called

**Action**: Un-skip these 2 tests and implement them with existing fixtures.

---

## Key Findings & Recommendations

### 🎯 High Priority Recommendations

1. **Move caching tests to integration suite** (Priority: HIGH)
   - Create `tests/integration/text_processor_cache_integration.py`
   - Move ~22 cache collaboration tests
   - Consider using AIResponseCache instead of FakeCache for more realistic integration

2. **Fix or remove 3 xfail tests** (Priority: MEDIUM)
   - `test_process_batch_isolates_individual_request_failures` - Redesign without call_count dependency
   - `test_process_batch_includes_error_messages_for_failures` - Complete graceful degradation update
   - `test_batch_processing_logs_start_and_completion` - Align with actual log format

3. **Implement 2 skipped tests** (Priority: LOW)
   - Both are implementable with existing fixtures
   - Would increase confidence in sanitization and validation

4. **Fix environment variable test pattern** (Priority: LOW)
   - Update `test_initialization_with_missing_gemini_api_key_raises_error()` to use `monkeypatch`

### 📊 Metrics Summary

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Total tests | 217 | - | ✅ |
| Passing tests | 210 (96.8%) | 100% | ⚠️ Fix xfails |
| Xfail tests | 5 (2.3%) | 2 (expected) | ⚠️ Fix 3 |
| Skip tests | 2 (0.9%) | 0 | ⚠️ Implement |
| Contract coverage | 95% | 90%+ | ✅ |
| Behavior focus | 9/10 | 8/10 | ✅ |
| Mocking strategy | 9/10 | 8/10 | ✅ |
| Test organization | 7/10 | 8/10 | ⚠️ Move integration tests |

### ✅ What's Working Well

1. **Excellent contract-driven testing** - Tests follow the .pyi contract meticulously
2. **Best-in-class fixture design** - FakeCache and FakePromptSanitizer are exemplary
3. **Proper external dependency mocking** - PydanticAI Agent and ai_resilience correctly identified as boundaries
4. **Comprehensive docstrings** - Business impact and scenario documentation excellent
5. **Zero internal method mocking** - Perfect adherence to "don't mock yourself" principle

### ⚠️ Areas for Improvement

1. **Test suite organization** - Caching tests belong in integration suite
2. **Xfail test resolution** - 3 tests have fixable design issues
3. **Skipped test implementation** - 2 tests are implementable with current infrastructure
4. **Integration test gap** - Missing explicit integration tests for resilience collaboration

---

## Conclusion

The text_processor unit test suite demonstrates **strong engineering discipline** with excellent adherence to behavior-driven testing principles. The test suite is **comprehensive, well-documented, and maintainable**.

The primary improvement opportunity is **conceptual organization** rather than test quality:
- **22 well-written tests** are testing **component collaboration** (integration) rather than **component isolation** (unit)
- Moving these to the integration suite would **improve clarity** and enable **more realistic integration testing**

**Overall Assessment**: This is a **high-quality test suite** that properly validates the text_processor contract. With the recommended reorganization and minor fixes, it would be **exemplary**.

**Recommended Action Plan**:
1. Week 1: Move caching tests to integration suite
2. Week 2: Fix 3 xfail tests with design issues
3. Week 3: Implement 2 skipped tests
4. Week 4: Add resilience integration tests

---

## Appendix: Test-by-Test Classification

### Unit Tests (Keep as-is): ~195 tests

**test_initialization.py** (ALL tests remain unit tests):
- ✅ All tests verify service initialization behavior in isolation
- ✅ Proper mocking of external dependencies

**test_core_functionality.py** (ALL tests remain unit tests):
- ✅ All tests verify operation dispatch and response field population
- ✅ Tests focus on text processing logic, not infrastructure integration

**test_error_handling.py** (ALL tests remain unit tests):
- ✅ All tests verify error handling and fallback behavior
- ✅ Proper mocking of AI service failures

**test_batch_processing.py** (MOST tests remain unit tests):
- ✅ Keep: All concurrency, aggregation, result tracking tests
- ⚠️ Move: `TestTextProcessorBatchCaching` class (3 tests)

### Integration Tests (Move to integration/): ~22 tests

**test_caching_behavior.py** (MOST tests become integration):
- ⚠️ Move: `TestTextProcessorCachingStrategy` (6 tests)
- ⚠️ Move: `TestTextProcessorCacheKeyGeneration` (5 tests)
- ⚠️ Move: `TestTextProcessorCacheTTLManagement` (5 tests)
- ⚠️ Move: `TestTextProcessorCacheBehaviorIntegration` (3 tests)

**test_batch_processing.py**:
- ⚠️ Move: `TestTextProcessorBatchCaching` (3 tests)

### Detailed Test-by-Test Listing

**Cache Integration Tests to Move** (from `test_caching_behavior.py`):

1. `test_cache_hit_returns_cached_response_without_ai_call` - Tests cache-first workflow
2. `test_cache_miss_triggers_ai_processing_and_stores_result` - Tests cache miss handling
3. `test_cache_check_occurs_before_input_sanitization` - Tests cache optimization
4. `test_cache_storage_after_successful_ai_processing` - Tests cache storage
5. `test_cache_hit_includes_cache_metadata_in_response` - Tests cache metadata
6. `test_cache_miss_includes_cache_metadata_in_response` - Tests cache metadata
7. `test_cache_key_includes_operation_type` - Tests key generation integration
8. `test_cache_key_includes_text_content` - Tests key generation integration
9. `test_cache_key_includes_options_when_provided` - Tests key generation integration
10. `test_cache_key_includes_question_for_qa_operation` - Tests key generation integration
11. `test_cache_key_generation_delegates_to_cache_service` - Tests delegation
12. `test_summarize_operation_uses_configured_ttl` - Tests TTL storage
13. `test_sentiment_operation_uses_shorter_ttl` - Tests TTL storage
14. `test_qa_operation_uses_shortest_ttl` - Tests TTL storage
15. `test_different_operations_use_different_ttls` - Tests TTL storage
16. `test_ttl_retrieval_from_operation_config_registry` - Tests TTL storage
17. `test_first_request_stores_second_request_hits_cache` - Tests complete workflow
18. `test_cache_effectiveness_with_varied_requests` - Tests cache isolation
19. `test_cache_handles_concurrent_identical_requests` - Tests concurrency + cache

**Batch Cache Integration Tests to Move** (from `test_batch_processing.py`):

20. `test_batch_requests_can_hit_cache_individually` - Tests batch + cache
21. `test_batch_stores_successful_results_in_cache` - Tests batch + cache
22. `test_duplicate_requests_in_batch_leverage_cache` - Tests batch + cache (xfail)

---

*End of Report*
