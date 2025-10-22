# Integration Testing

## Prompt 2: Consolidate and Validate Integration Test Plan

Review and consolidate integration test opportunities in `backend/tests/integration/resilience/TEST_PLAN_1.md` (architectural analysis) and `backend/tests/integration/resilience/TEST_PLAN_2.md` (unit test mining) to create a final, validated integration test plan.

Save the output to `backend/tests/integration/resilience/TEST_PLAN_DRAFT.md`

**OBJECTIVES:**
1. **DEDUPLICATE**: Merge overlapping seams from both sources
2. **VALIDATE**: Confirm each proposed test has clear business value
3. **PRIORITIZE**: Rank by business impact and integration risk
4. **ELIMINATE**: Remove low-value or redundant tests
5. **FINALIZE**: Create implementation-ready test plan for Prompt 2

**INPUTS:**
- Prompt 1 output: Architectural seams with confidence levels
- Prompt 2 output: Unit test analysis with CONFIRMED/NEW markers

**DEDUPLICATION PROCESS:**

For each seam identified in Prompt 1:
- Check if Prompt 2 also identified this seam (look for CONFIRMED marker)
- If YES (CONFIRMED): **Highest priority** - both architecture and usage support it
- If NO: **Lower priority** - verify seam is actually used before implementing

For each seam identified in Prompt 2:
- Check if Prompt 1 also identified this seam
- If YES (CONFIRMED): Already handled above
- If NO (NEW): **Investigate** - why was it missed in architecture? Is it important?
- Mark for implementation if high unit test coverage reveals real usage

**MERGE CRITERIA:**

Two seams should be merged if:
- They involve the same component boundaries
- They test similar integration behaviors
- One scenario is more comprehensive than the other

Example Merge:
- Prompt 1: "API → Service → Cache (verify cache hit/miss)"
- Prompt 2: "Service → Cache (verify cache improves performance)"
- **MERGED**: "API → Service → Cache (verify cache hit/miss improves performance)"
  - Combines architectural scope (API entry point) with behavioral outcome (performance)
  - Single comprehensive test instead of two overlapping tests

**PRIORITIZATION MATRIX:**

| Source | Business Impact | Integration Risk | Priority |
|--------|----------------|------------------|----------|
| CONFIRMED (Prompt 1 + 3) | HIGH | HIGH | **P0** - Must have |
| CONFIRMED (Prompt 1 + 3) | HIGH | MEDIUM | **P1** - Should have |
| CONFIRMED (Prompt 1 + 3) | MEDIUM | HIGH | **P1** - Should have |
| NEW (Prompt 2 only) | HIGH | HIGH | **P1** - Should have |
| Prompt 1 only | MEDIUM | HIGH | **P2** - Could have |
| Either source | LOW | LOW | **P3** - Skip |

**ELIMINATION CRITERIA:**

Remove integration test if ANY of these apply:
- [ ] Adequately covered by unit tests (no integration value)
- [ ] Low business impact AND low integration risk
- [ ] Better suited for E2E/manual testing (requires real external services, API costs)
- [ ] Duplicate of higher-priority test
- [ ] Tests implementation detail, not integration behavior
- [ ] Would be brittle or difficult to maintain

**VALIDATION CHECKLIST:**

For each proposed integration test, verify:

✅ **TESTS A SEAM** (not internal logic)
- [ ] Test spans multiple real components
- [ ] Test verifies cross-component behavior
- [ ] Test would fail if components don't integrate correctly
- ❌ Does NOT just verify single component with mocks

✅ **COMPLEMENTS UNIT TESTS** (not duplicates)
- [ ] Test verifies something unit tests cannot (real infrastructure behavior)
- [ ] Test focuses on integration concerns (performance, resilience, state)
- [ ] Unit tests verify correctness, integration tests verify working together
- ❌ Does NOT re-test component logic already covered by unit tests

✅ **HAS BUSINESS VALUE** (not just technical coverage)
- [ ] Test failure indicates real business impact
- [ ] Test verifies user-facing behavior or critical system property
- [ ] Test protects against realistic failure scenarios
- ❌ Does NOT test low-value edge cases

✅ **USES REAL INFRASTRUCTURE** (not excessive mocking)
- [ ] Uses real cache (fakeredis) OR real database (test containers)
- [ ] Mocks only external APIs or expensive resources
- [ ] Verifies observable outcomes, not mock call counts
- ❌ Does NOT mock everything and verify method calls

**OUTPUT FORMAT:**

```markdown
## FINAL INTEGRATION TEST PLAN

### Consolidation Summary
- Prompt 1 identified: [N] seams
- Prompt 2 identified: [N] seams
- CONFIRMED (both sources): [N] seams
- NEW (Prompt 2 only): [N] seams
- Merged: [N] overlapping scenarios
- Eliminated: [N] low-value tests

### P0 - Must Have (Critical Path)

1. **SEAM**: [Name]
   - **SOURCE**: CONFIRMED (Prompt 1 HIGH confidence + Prompt 2 CONFIRMED)
   - **COMPONENTS**: [List real components involved]
   - **SCENARIOS** (merged from both sources):
     * [Scenario 1 from Prompt 1]
     * [Scenario 2 from Prompt 2]
     * [Additional scenarios if needed]
   - **BUSINESS VALUE**: [Why this is critical]
   - **INTEGRATION RISK**: [What could go wrong]
   - **IMPLEMENTATION NOTES**:
     * Fixtures needed: [e.g., ai_response_cache, test_db]
     * Complexity estimate: Low/Medium/High
     * Expected test count: [N] test methods
   - **VALIDATION**: ✅ Passes all validation criteria

### P1 - Should Have (Important)

2. **SEAM**: [Name]
   - **SOURCE**: CONFIRMED (Prompt 1 MEDIUM confidence + Prompt 2 CONFIRMED)
   - [Same format as P0]

3. **SEAM**: [Name]
   - **SOURCE**: NEW (Prompt 2 only - discovered via unit test analysis)
   - [Same format]

### P2 - Could Have (Nice to Have)

4. **SEAM**: [Name]
   - **SOURCE**: Prompt 1 only (architectural, verify usage before implementing)
   - [Same format]

### Deferred/Eliminated

**SEAM**: [Name]
- **SOURCE**: [Prompt 1 / Prompt 2 / both]
- **REASON FOR DEFERRAL**:
  - [ ] Better suited for manual testing (@pytest.mark.manual)
  - [ ] Requires expensive external resources (real AI API)
  - [ ] Adequately covered by unit tests
  - [ ] Low business value (admin feature, reporting)
  - [ ] Other: [explain]
- **ALTERNATIVE**: [How to test this instead]

**SEAM**: [Name]
- **SOURCE**: [Prompt 1 / Prompt 2]
- **REASON FOR ELIMINATION**:
  - [ ] Duplicate of higher-priority test
  - [ ] Tests implementation detail, not integration
  - [ ] Unit test disguised as integration test
  - [ ] Would be brittle/hard to maintain
  - [ ] Other: [explain]

### Implementation Order

**Sprint 1 (MVP):**
- All P0 tests (critical path validation)
- Estimated effort: [N] hours

**Sprint 2 (Hardening):**
- All P1 tests (important integrations + resilience)
- Estimated effort: [N] hours

**Future Backlog:**
- P2 tests as time allows
- Deferred tests if business priority changes
```

**EXAMPLE CONSOLIDATION:**

Prompt 1 Output:
```markdown
1. SEAM: API → TextProcessingService → Cache
   CONFIDENCE: HIGH
   PRIORITY: HIGH
   SCENARIOS: Cache hit/miss behavior
```

Prompt 2 Output:
```markdown
1. SEAM: TextProcessorService → AIResponseCache
   SOURCE: CONFIRMED
   PRIORITY: P0
   SCENARIOS:
   - test_cache_improves_performance_for_repeated_requests
   - test_service_handles_cache_failure_gracefully
```

Consolidated (Prompt 3):
```markdown
### P0 - Must Have

1. **SEAM**: API → TextProcessingService → AIResponseCache → fakeredis
   - **SOURCE**: CONFIRMED (Prompt 1 HIGH + Prompt 2 CONFIRMED)
   - **COMPONENTS**: /v1/process endpoint, TextProcessingService, AIResponseCache, fakeredis
   - **SCENARIOS** (merged):
     * Cache hit returns cached result without AI call
     * Cache miss calls AI and stores result
     * Cache improves performance for repeated requests (< 50ms vs > 100ms)
     * Cache handles concurrent identical requests
     * Service continues when cache fails (resilience)
   - **BUSINESS VALUE**:
     * Reduces AI costs by caching repeated requests
     * Improves response time for cache hits (< 50ms target)
     * Ensures graceful degradation when Redis unavailable
   - **INTEGRATION RISK**:
     * Redis connection failures
     * Cache key collisions
     * TTL expiration issues
     * Concurrent access race conditions
   - **IMPLEMENTATION NOTES**:
     * Fixtures: ai_response_cache (real AIResponseCache + fakeredis), mock_pydantic_agent
     * Complexity: Medium (need concurrency testing)
     * Expected test count: 5 test methods
   - **VALIDATION**: ✅ All criteria passed
     * ✅ Tests real Service + Cache integration
     * ✅ Complements unit tests (verifies performance, not just API calls)
     * ✅ High business value (cost savings + performance)
     * ✅ Uses fakeredis (real infrastructure simulation)
```

**FINAL CHECK:**
Before sending to Prompt 4 for implementation:
1. Review P0 tests - are these truly critical path?
2. Check for duplication within priority levels
3. Verify each test has clear success criteria
4. Confirm fixture availability in conftest.py
5. Estimate if test plan is achievable in sprint

Generate a final, consolidated, implementation-ready test plan.
