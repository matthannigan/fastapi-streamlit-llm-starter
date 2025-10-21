# Integration Test Plan for Text Processor Service
## PROMPT 2 - UNIT TEST MINING ANALYSIS

Based on analysis of unit tests in `backend/tests/unit/text_processor/` and the quality report (`backend/tests/unit/text_processor/QUALITY_REPORT.md`), this document identifies integration testing opportunities revealed by existing unit test patterns and proposes NEW integration tests that complement (not replace) existing unit test coverage.

## Unit Test Analysis: TextProcessorService

### Mocked Dependencies Found:

#### 1. **AIResponseCache** - Mocked via `FakeCache` in ~60 unit tests
**Why Mocked**: External Redis dependency, test isolation, realistic state management
**Interface Tested**: `get()`, `set()`, `delete()`, `build_cache_key()`, TTL management
**Mock Type**: High-fidelity fake implementation (stateful in-memory cache)

#### 2. **PydanticAI Agent** - Mocked via `mock_pydantic_agent` in ~40 unit tests
**Why Mocked**: External library dependency, API costs, test speed, reliability
**Interface Tested**: `run()` method for AI processing
**Mock Type**: AsyncMock with configurable return values

#### 3. **AI Resilience Orchestrator** - Mocked via `mock_ai_resilience` in ~25 unit tests
**Why Mocked**: Global singleton infrastructure, circuit breaker state complexity
**Interface Tested**: `register_operation()`, `get_health_status()`, circuit breaker methods
**Mock Type**: Mock with default healthy behavior

#### 4. **PromptSanitizer** - Mocked via `fake_prompt_sanitizer` in ~20 unit tests
**Why Mocked**: Complex security validation logic, test isolation
**Interface Tested**: `sanitize_input()`, `sanitize_options()`, injection detection
**Mock Type**: High-fidelity fake with call tracking

#### 5. **ResponseValidator** - Mocked via `mock_response_validator` in ~15 unit tests
**Why Mocked**: Complex validation logic, external service component
**Interface Tested**: `validate()`, `validate_response()`, security checks
**Mock Type**: Mock with configurable validation behavior

### Integration Seams Revealed:

#### SEAM 1: TextProcessorService → AIResponseCache (Cache Collaboration)

**Unit Test Coverage:**
- ✅ Service calls cache.get() before AI processing (cache-first strategy)
- ✅ Service calls cache.set() after successful processing with correct TTL
- ✅ Service builds cache keys using cache.build_cache_key() method
- ✅ Service handles cache hits vs misses correctly
- ✅ Cache metadata (cache_hit flag) properly set in responses
- ✅ Operation-specific TTLs correctly applied (summarize: 7200s, sentiment: 3600s, etc.)

**Integration Gap:**
- ❌ Does cache actually improve performance with real Redis infrastructure?
- ❌ Does cache survive across multiple service instances/requests?
- ❌ What happens when Redis connection fails during operations?
- ❌ Do concurrent requests properly share cache state?
- ❌ Does cache compression work correctly with real data?
- ❌ Does cache memory management work under load?

**Cross-Reference with Prompt 1:**
- **STATUS**: CONFIRMED (Prompt 1 also identified this seam with HIGH confidence)
- **Architectural Analysis**: Noted cache as critical performance optimization
- **Unit Test Evidence**: 60+ cache-related tests confirm heavy cache usage in practice
- **Quality Report**: Explicitly calls out cache behavior tests as integration tests

**Integration Test Value:** HIGH
- **Business Critical**: Caching reduces AI costs significantly (estimated 60-80% cost savings)
- **Integration Risk**: Redis connection failures, TTL expiration race conditions, cache key collisions
- **Unit Test Limitation**: Unit tests verify "service uses cache correctly" but cannot verify "caching provides business value with real infrastructure"

#### SEAM 2: TextProcessorService → PydanticAI Agent (AI Integration)

**Unit Test Coverage:**
- ✅ Service calls agent.run() with correct prompt parameters
- ✅ Service handles different AI response formats per operation
- ✅ Service propagates AI agent errors correctly
- ✅ Service configures agent with correct model settings
- ✅ Response parsing and field population works correctly

**Integration Gap:**
- ❌ Real AI responses match expected format and quality
- ❌ API rate limiting and timeout handling works with real Gemini API
- ❌ Error handling works with actual API failures (network issues, rate limits)
- ❌ Authentication with real API keys works correctly

**Cross-Reference with Prompt 1:**
- **STATUS**: CONFIRMED (Prompt 1 identified this seam with MEDIUM confidence)
- **Architectural Analysis**: Noted as potentially expensive to test
- **Unit Test Evidence**: 40+ AI-related tests confirm agent integration is core functionality
- **Quality Report**: Properly mocked as external library boundary

**Integration Test Value:** LOW (for automated integration tests)
- **Cost Issue**: Requires real API keys and costs money per test run
- **Reliability Issue**: Depends on external service availability
- **Better Suited**: Manual/E2E tests with `@pytest.mark.manual`
- **Unit Tests**: Sufficient for contract verification with mocks

#### SEAM 3: TextProcessorService → AI Resilience Orchestrator (Resilience Integration)

**Unit Test Coverage:**
- ✅ Service registers operations with resilience orchestrator on initialization
- ✅ Different resilience strategies applied per operation type
- ✅ Service uses resilience patterns when calling AI agent
- ✅ Circuit breaker state affects processing behavior

**Integration Gap:**
- ❌ Real circuit breaker actually trips on repeated failures
- ❌ Retry mechanisms work with actual transient failures
- ❌ Circuit breaker recovery works after timeout periods
- ❌ Resilience monitoring provides accurate metrics
- ❌ Different resilience strategies behave differently under load

**Cross-Reference with Prompt 1:**
- **STATUS**: CONFIRMED (Prompt 1 identified this seam with HIGH confidence)
- **Architectural Analysis**: Noted resilience as critical for service reliability
- **Unit Test Evidence**: 25+ resilience-related tests show extensive resilience integration
- **Quality Report**: 1 xfail test marked as appropriate infrastructure collaboration

**Integration Test Value:** HIGH
- **Business Critical**: Service reliability and user experience depend on resilience
- **Integration Risk**: Circuit breaker state management, retry logic complexity
- **Unit Test Limitation**: Unit tests verify "resilience is used" but cannot verify "resilience provides reliability under real failure conditions"

#### SEAM 4: TextProcessorService → PromptSanitizer + ResponseValidator (Security Integration)

**Unit Test Coverage:**
- ✅ Service calls sanitizer for all input text and options
- ✅ Service calls validator for all AI responses
- ✅ Injection detection triggers appropriate error handling
- ✅ Validation failures are handled gracefully

**Integration Gap:**
- ❌ Real prompt injection attempts are correctly blocked
- ❌ Actual harmful AI responses are detected and blocked
- ❌ Security validation doesn't break normal functionality
- ❌ Performance impact of security checks is acceptable

**Cross-Reference with Prompt 1:**
- **STATUS**: CONFIRMED (Prompt 1 identified this seam with HIGH confidence)
- **Architectural Analysis**: Noted security as non-negotiable requirement
- **Unit Test Evidence**: 35+ security-related tests show comprehensive security integration
- **Quality Report**: Properly mocked as complex external validation logic

**Integration Test Value:** MEDIUM
- **Security Critical**: Protection against prompt injection and harmful responses
- **Integration Risk**: Security validation might have false positives/negatives
- **Unit Test Limitation**: Unit tests verify "security is called" but cannot verify "security actually blocks threats"

#### SEAM 5: TextProcessorService → Batch Processing + Concurrency (Batch Integration)

**Unit Test Coverage:**
- ✅ Service processes batch requests concurrently using asyncio.gather()
- ✅ Concurrency semaphore limits simultaneous processing
- ✅ Individual request failures don't affect other requests
- ✅ Batch results are aggregated correctly with status tracking

**Integration Gap:**
- ❌ Concurrency limits actually prevent resource exhaustion
- ❌ Batch performance scales correctly under load
- ❌ Memory usage remains bounded during large batch processing
- ❌ Individual request caching works correctly in batch context

**Cross-Reference with Prompt 1:**
- **STATUS**: CONFIRMED (Prompt 1 identified this seam with MEDIUM confidence)
- **Architectural Analysis**: Noted batch processing as efficiency feature
- **Unit Test Evidence**: 60+ batch-related tests confirm extensive batch functionality
- **Quality Report**: 3 xfail tests indicate complex interaction with resilience patterns

**Integration Test Value:** MEDIUM
- **Business Impact**: Batch processing efficiency for bulk operations
- **Integration Risk**: Resource exhaustion, memory leaks under load
- **Unit Test Limitation**: Unit tests verify "batch logic works" but cannot verify "batch scales efficiently"

### Assessment Summary

**CONFIRMED Seams** (Prompt 1 + Prompt 2):
1. **TextProcessorService → AIResponseCache** (HIGH priority integration tests)
2. **TextProcessorService → PydanticAI Agent** (LOW priority - better as manual tests)
3. **TextProcessorService → AI Resilience Orchestrator** (HIGH priority integration tests)
4. **TextProcessorService → Security Components** (MEDIUM priority integration tests)
5. **TextProcessorService → Batch Processing Concurrency** (MEDIUM priority integration tests)

**NEW Seams** (Prompt 2 only):
- No new seams discovered - unit test patterns align well with architectural analysis

**Key Insights from Unit Test Analysis:**

#### Cache Integration is Most Critical
- 60+ cache-related unit tests (27% of all unit tests)
- Quality Report explicitly calls out cache tests as integration tests
- Heavy cache usage in practice confirms architectural importance
- Business value is clear: cost reduction and performance improvement

#### Resilience Integration is Undervalued in Unit Tests
- Only 25+ resilience-related tests despite being critical for reliability
- 1 xfail test indicates unit tests struggle with resilience complexity
- Architectural analysis identified resilience as HIGH priority
- Unit tests can't verify real failure/recovery scenarios

#### Security Integration is Well-Tested but Needs Real Threats
- 35+ security-related unit tests show comprehensive coverage
- Proper use of fakes for testing security integration patterns
- Need real threat scenarios to verify actual protection

#### AI Integration is Properly Mocked
- 40+ AI-related unit tests show extensive coverage
- Correct use of mocks for external library dependency
- Real AI testing is expensive and better suited for manual tests

### Recommended NEW Integration Test Scenarios

#### P0 (HIGH Priority) - Critical Business Value

**1. test_cache_improves_performance_for_repeated_requests**
- **SOURCE**: CONFIRMED (Prompt 1 + Prompt 2)
- **INTEGRATION SCOPE**: TextProcessorService + AIResponseCache (fakeredis) + HTTP client
- **SCENARIO**: Second identical request hits cache without calling AI, providing measurable performance improvement
- **SUCCESS CRITERIA**:
  * First request: cache_hit=False, AI called once, processing_time > 100ms
  * Second request: cache_hit=True, AI not called, processing_time < 50ms
  * Performance improvement > 50% for cached requests
  * Response content identical between cached and fresh requests
- **PRIORITY**: P0 (HIGH - direct cost savings and performance impact)

**2. test_resilience_circuit_breaker_protects_from_cascading_failures**
- **SOURCE**: CONFIRMED (Prompt 1 + Prompt 2)
- **INTEGRATION SCOPE**: TextProcessorService + AIResilienceOrchestrator + failing AI service
- **SCENARIO**: Repeated AI failures trigger circuit breaker, preventing cascading failures
- **SUCCESS CRITERIA**:
  * Initial failures are handled with retries
  * After failure threshold, circuit opens and fails fast
  * Circuit open state prevents AI calls and returns fallback responses
  * Circuit recovers after timeout period
  * System remains responsive during AI service outages
- **PRIORITY**: P0 (HIGH - service reliability and user experience)

**3. test_cache_failure_graceful_degradation**
- **SOURCE**: NEW (discovered via unit test analysis - FakeCache vs real cache failure)
- **INTEGRATION SCOPE**: TextProcessorService + failing AIResponseCache + AI service
- **SCENARIO**: Cache connection failure doesn't stop text processing, service continues with AI calls
- **SUCCESS CRITERIA**:
  * Requests succeed despite cache unavailability
  * Appropriate warning logged about cache failure
  * AI processing continues normally without cache
  * Response indicates cache_hit=False due to cache failure
  * Service recovery when cache becomes available
- **PRIORITY**: P0 (HIGH - resilience and availability)

#### P1 (MEDIUM Priority) - Important Features

**4. test_security_integration_blocks_real_threats**
- **SOURCE**: CONFIRMED (Prompt 1 + Prompt 2)
- **INTEGRATION SCOPE**: TextProcessorService + PromptSanitizer + ResponseValidator + real threat samples
- **SCENARIO**: Real prompt injection attempts and harmful AI responses are blocked
- **SUCCESS CRITERIA**:
  * Known prompt injection patterns are rejected with ValidationError
  * Malicious AI responses are detected and blocked
  * Legitimate requests pass through security validation
  * Security validation doesn't significantly impact performance
  * Detailed security events are logged appropriately
- **PRIORITY**: P1 (MEDIUM - security validation needs real threat testing)

**5. test_batch_processing_scales_under_load**
- **SOURCE**: CONFIRMED (Prompt 1 + Prompt 2)
- **INTEGRATION SCOPE**: TextProcessorService + concurrency monitoring + large batch requests
- **SCENARIO**: Large batch processes efficiently within concurrency limits
- **SUCCESS CRITERIA**:
  * Batch of 100+ requests processes within reasonable time
  * Concurrency limits prevent resource exhaustion
  * Memory usage remains bounded during processing
  * Individual request failures don't affect batch completion
  * Performance scales linearly with batch size (within limits)
- **PRIORITY**: P1 (MEDIUM - efficiency and scalability)

**6. test_cache_compression_and_memory_efficiency**
- **SOURCE**: NEW (discovered via unit test analysis - FakeCache doesn't test compression)
- **INTEGRATION SCOPE**: TextProcessorService + AIResponseCache with compression enabled
- **SCENARIO**: Cache compression reduces memory usage while maintaining performance
- **SUCCESS CRITERIA**:
  * Large responses are compressed before caching
  * Compression ratio meets expectations (>30% reduction)
  * Decompression time is minimal (< 10ms overhead)
  * Memory usage stays within configured limits
  * Cache hit performance is maintained with compression
- **PRIORITY**: P1 (MEDIUM - memory efficiency and cost optimization)

#### P2 (LOW Priority) - Operational Concerns

**7. test_ai_integration_with_real_api_key**
- **SOURCE**: CONFIRMED (Prompt 1 + Prompt 2)
- **INTEGRATION SCOPE**: TextProcessorService + real Gemini API + manual test marker
- **SCENARIO**: Real AI API integration test for validation and quality assurance
- **SUCCESS CRITERIA**:
  * Real AI responses match expected format and quality
  * API rate limiting is handled gracefully
  * Authentication with real API keys works
  * Processing times are within acceptable ranges
  * Response quality meets business requirements
- **PRIORITY**: P2 (LOW - expensive, better as manual test)
- **NOTE**: Mark with `@pytest.mark.manual` for occasional validation

### Relationship Between Unit and Integration Tests

**Unit Tests to Keep** (NOT convert - provide different value):
- ✅ All 60+ cache-related unit tests (verify correct cache usage patterns)
- ✅ All 40+ AI-related unit tests (verify correct AI integration)
- ✅ All 25+ resilience-related unit tests (verify correct resilience usage)
- ✅ All 35+ security-related unit tests (verify correct security integration)
- ✅ All 60+ batch-related unit tests (verify correct batch logic)

**Unit Test Example (complementary to integration tests):**
```python
async def test_service_stores_in_cache_with_correct_ttl(fake_cache, mock_pydantic_agent):
    """Verify service calls cache.set() with correct TTL per operation."""
    # Unit test verifies correct API usage
    service = TextProcessorService(settings, fake_cache)
    request = TextProcessingRequest(text="test", operation="summarize")
    await service.process_text(request)

    # Verifies contract compliance
    stored_ttl = fake_cache.get_stored_ttl("summarize_key")
    assert stored_ttl == 7200  # Summarize TTL
```

**Integration Test (NEW, different concern):**
```python
async def test_cache_ttl_expires_correctly_with_real_redis(service, real_cache):
    """Verify cache TTL actually expires with real Redis."""
    # Integration test verifies real infrastructure behavior
    request = TextProcessingRequest(text="test", operation="summarize")

    # First request stores in cache
    response1 = await service.process_text(request)
    assert response1.cache_hit is False

    # Wait for TTL expiration (use short TTL for testing)
    await asyncio.sleep(2)  # TTL = 1 second for test

    # Second request should miss cache due to expiration
    response2 = await service.process_text(request)
    assert response2.cache_hit is False
    assert mock_ai_agent.run.call_count == 2  # AI called twice
```

**Both tests are needed** - they verify different concerns at different levels:
- Unit tests verify **correct usage** of infrastructure interfaces
- Integration tests verify **actual behavior** of infrastructure components

### Implementation Notes

#### Critical Success Factors
- **Use fakeredis**: For Redis cache simulation with high fidelity
- **Real Resilience Orchestrator**: For actual circuit breaker and retry behavior
- **HTTP Client Testing**: Test through FastAPI TestClient for outside-in approach
- **Configurable Failures**: Ability to simulate infrastructure failures
- **Performance Monitoring**: Measure actual performance improvements

#### Infrastructure Requirements
- **fakeredis**: High-fidelity Redis simulation
- **Real resilience orchestrator**: Actual circuit breaker and retry logic
- **Test HTTP client**: FastAPI TestClient for API-level testing
- **Failure simulation**: Configurable failure injection for testing
- **Performance measurement**: Timing and memory usage tracking

#### Test Data Requirements
- **Real threat samples**: Prompt injection attempts and harmful responses
- **Large text samples**: For compression and memory efficiency testing
- **Batch data**: Mixed operation types for large batch testing
- **Performance benchmarks**: Expected timing and memory usage baselines

## Summary

**Unit Test Analysis Reveals:**
1. **Cache integration is most critical** - 60+ tests confirm heavy usage, clear business value
2. **Resilience integration needs real testing** - unit tests can't verify actual failure recovery
3. **Security integration needs real threats** - unit tests verify patterns but not actual protection
4. **AI integration is properly mocked** - real testing is expensive and better as manual tests
5. **Batch processing integration is important** - concurrency and scaling need verification

**Recommended Integration Test Priority:**
1. **P0 (HIGH)**: Cache performance, resilience reliability, cache failure handling
2. **P1 (MEDIUM)**: Security validation, batch scaling, compression efficiency
3. **P2 (LOW)**: Real AI integration (manual testing)

**Key Insight**: Unit tests provide excellent coverage of **interface correctness**, while integration tests should focus on **infrastructure behavior** and **business value** that cannot be verified with mocks alone.