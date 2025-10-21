# Integration Testing

## Prompt 4: Review and Validate Integration Test Plan (OPTIONAL Quality Gate)

**Purpose**: Independent validation of the integration test plan by a different (typically more capable) LLM before implementation begins.

**Context**: This optional step provides a quality gate between planning (Prompts 1-3) and implementation (Prompt 5). It's most valuable when:
- Using fast/cheap models for Prompts 1-3
- Working on complex/critical components
- Uncertain about prioritization decisions
- New to integration testing philosophy

**Economic Rationale**: Pay for quality only at decision points. Use cheap models for analysis (Prompts 1-3), expensive model for validation (Prompt 4), cheap model for
implementation (Prompt 5).

**When to Skip**: Simple components, confident in Prompt 3 output, or already used expensive model for Prompts 1-3.

---

## Input Requirements

**Required Files**:
1. **Test Plan** (Prompt 3 output): Usually named `TEST_PLAN.md` or `INTEGRATION_TEST_PLAN.md`
    - Consolidated seams from Prompts 1 and 2
    - Prioritized as P0/P1/P2/Deferred
    - Validation checkboxes should be completed

2. **Testing Philosophy Documentation**:
    - `docs/guides/testing/INTEGRATION_TESTS.md` - Integration testing philosophy
    - `docs/guides/testing/WRITING_TESTS.md` - Docstring-driven test development

**Optional Context** (if available):
- Original Prompt 1 output (architectural analysis)
- Original Prompt 2 output (unit test mining)
- Public interface/contract (`.pyi` file or docstrings)
- Existing integration test READMEs for reference

---

## Review Process

### Step 1: Understand Testing Philosophy (5 minutes)

Read the following and summarize key principles:

1. **Review `docs/guides/testing/INTEGRATION_TESTS.md`**:
    - What is our definition of integration testing?
    - What are the 3 most important principles?
    - What are the 3 most important anti-patterns?

2. **Review `docs/guides/testing/WRITING_TESTS.md`**:
    - What is docstring-driven test development?
    - How should tests relate to documented behavior?
    - What should NOT be tested?

**Output**: Brief summary showing you understand our testing philosophy.

### Step 2: Validate Test Plan Structure (10 minutes)

**Check the test plan has required sections**:

- [ ] Consolidation Summary (Prompt 1 + 2 seams identified)
- [ ] P0 - Must Have (Critical path tests)
- [ ] P1 - Should Have (Important integrations)
- [ ] P2 - Could Have (Nice to have)
- [ ] Deferred/Eliminated (What was excluded and why)

**Validate each seam entry has**:
- [ ] SOURCE marker (CONFIRMED, NEW, Prompt 1 only)
- [ ] COMPONENTS list (real components involved)
- [ ] SCENARIOS (concrete test scenarios)
- [ ] BUSINESS VALUE (why this matters)
- [ ] INTEGRATION RISK (what could go wrong)
- [ ] IMPLEMENTATION NOTES (fixtures, complexity, test count)
- [ ] VALIDATION checkboxes (all checked ✅)

**Flag if missing**: Any required section or incomplete seam documentation.

### Step 3: Critical Review - Integration vs. Unit Tests (15 minutes)

**For each P0/P1 seam, verify it's truly an integration test**:

**✅ PASS - This is an integration test if**:
- [ ] Tests multiple real components working together
- [ ] Uses high-fidelity infrastructure (fakeredis, testcontainers)
- [ ] Verifies behavior unit tests CANNOT verify
- [ ] Has clear business value beyond unit test coverage
- [ ] Focuses on seams/boundaries, not component internals

**❌ FAIL - This is a unit test disguised as integration if**:
- [ ] Mocks most dependencies and verifies method calls
- [ ] Only exercises single component with mocked collaborators
- [ ] Duplicates existing unit test coverage
- [ ] Tests implementation details, not integration behavior
- [ ] Could be verified by unit tests alone

**Actionable Feedback**:
- For FAILs: "This should be a unit test because..."
- For borderline: "Consider whether this provides value beyond unit test X"
- For PASSes: Confirm integration value

### Step 4: Validate Prioritization (10 minutes)

**Check P0 (Must Have) tests are truly critical**:

Review the prioritization matrix from Prompt 3:
| Source | Business Impact | Integration Risk | Priority |
|--------|----------------|------------------|----------|
| CONFIRMED (Prompt 1 + 2) | HIGH | HIGH | P0 |

**For each P0 seam, verify**:
- [ ] Both Prompt 1 AND Prompt 2 identified it (CONFIRMED)
- [ ] Business impact is genuinely HIGH (user-facing, costs, security)
- [ ] Integration risk is genuinely HIGH (failure modes are realistic)
- [ ] Failure would impact critical path or business operations

**Challenge questionable P0s**:
- "Seam X is marked P0 but only identified in Prompt 1 - should this be P1?"
- "Business value claims 'improves performance' but no performance requirement exists - is this P1?"
- "Integration risk is 'Redis might fail' but we have graceful degradation - reconsider priority?"

**Check P1/P2 aren't actually P0**:
- Security-critical integration in P1? Should be P0
- User-facing feature in P2? Should be P0 or P1

### Step 5: Review for Missing Seams (10 minutes)

**Based on testing philosophy, check for common gaps**:

**Resilience Patterns** (often missing):
- [ ] What happens when cache fails?
- [ ] What happens when database is unavailable?
- [ ] What happens when external API is slow/down?
- [ ] Are there circuit breakers that need integration testing?

**Security Boundaries** (critical):
- [ ] Are authentication seams tested?
- [ ] Is authorization enforcement tested?
- [ ] Are encryption workflows tested end-to-end?
- [ ] Are TLS/certificate integrations validated?

**Performance-Critical Paths** (business impact):
- [ ] Is caching performance improvement verified?
- [ ] Are batch operations tested for performance?
- [ ] Are concurrent access patterns validated?

**Actionable Feedback**:
- "Consider adding: Service → Cache failure resilience test (P1)"
- "Security gap: Authentication → Authorization integration not tested (P0)"

### Step 6: Review Deferred/Eliminated Tests (5 minutes)

**Validate deferral reasons are sound**:

**Good reasons to defer**:
- ✅ Better suited for E2E tests (requires real external API)
- ✅ Adequately covered by unit tests (no integration value)
- ✅ Low business value (admin feature, rare use case)
- ✅ Requires expensive resources (real AI API with costs)

**Bad reasons to defer (should reconsider)**:
- ❌ "Too complex to test" (may indicate critical integration risk)
- ❌ "Don't know how to test" (may need better approach)
- ❌ "Takes too long to run" (may need better infrastructure)

**Actionable Feedback**:
- "Test X deferred as 'too complex' but it's security-critical - reconsider as P1 with simplified approach"
- "Test Y deferred to E2E but doesn't need real API - could use mock, add as P1"

### Step 7: Validate Test Count and Scope (5 minutes)

**Check if test plan is realistic**:

**Integration test suites should be small and dense**:
- P0 tests: Typically 3-7 test files (critical path only)
- P1 tests: Typically 3-10 test files (important integrations)
- P2 tests: Typically 0-5 test files (nice to have)

**Red flags**:
- ❌ More than 15 P0 tests (likely including non-critical tests)
- ❌ More than 30 total integration tests (too comprehensive, not selective)
- ❌ Tests that span too many components (likely E2E, not integration)
- ❌ Tests with minimal business value in P0 (wrong priority)

**Actionable Feedback**:
- "20 P0 tests is too many - integration tests should be selective. Recommend moving tests X, Y, Z to P1/P2"
- "Test covers API → Service → Cache → Database → External API - this is E2E, not integration"

---

## Output Format

**Provide structured review with this format**:

```markdown
## Integration Test Plan Review

### Executive Summary
- **Overall Assessment**: [Strong / Acceptable / Needs Revision]
- **Total Seams**: P0: [N], P1: [N], P2: [N], Deferred: [N]
- **Critical Issues**: [Number of blocking issues]
- **Recommendations**: [Number of suggestions]
- **Estimated Implementation Effort**: [N hours for P0, N hours for P1]

### Testing Philosophy Alignment
[Brief summary showing you understand our testing philosophy - 2-3 sentences]

**Key Principles**:
1. [Principle from INTEGRATION_TESTS.md]
2. [Principle from INTEGRATION_TESTS.md]
3. [Principle from WRITING_TESTS.md]

### Validation Results

#### ✅ Strengths
1. [What's done well]
2. [What's done well]
3. [What's done well]

#### ⚠️ Issues Found

**CRITICAL (Must Fix Before Implementation)**:
1. **[Seam Name]** - [Issue]
    - **Problem**: [What's wrong]
    - **Impact**: [Why this matters]
    - **Recommendation**: [Specific action]
    - **Priority**: Change from [X] to [Y] OR Remove OR Revise

2. [Continue for all critical issues]

**SUGGESTIONS (Consider Improvements)**:
1. **[Seam Name]** - [Suggestion]
    - **Observation**: [What could be better]
    - **Benefit**: [Value of making change]
    - **Recommendation**: [Optional action]

#### ❌ Missing Seams (Gaps)
1. **[Suggested Seam]** - [Gap identified]
    - **Components**: [What should be integrated]
    - **Business Value**: [Why this matters]
    - **Recommended Priority**: P0/P1/P2
    - **Rationale**: [Why this was likely missed]

#### 🔄 Priority Adjustments
**Recommend Moving to Higher Priority**:
- [Seam X]: P1 → P0 (Reason: [security-critical / user-facing / etc.])

**Recommend Moving to Lower Priority**:
- [Seam Y]: P0 → P1 (Reason: [not critical path / covered by unit tests / etc.])

### Deferred Tests Review
**Appropriately Deferred**:
- ✅ [Test A]: [Good reason]
- ✅ [Test B]: [Good reason]

**Questionable Deferrals**:
- ⚠️ [Test C]: [Reason to reconsider]
- ⚠️ [Test D]: [Reason to reconsider]

### Revised Test Plan

[Only include this section if changes are recommended]

**If critical issues or priority adjustments are needed, provide**:
- Updated P0 list with changes explained
- Updated P1 list with changes explained
- New seams to add with full documentation (SOURCE, COMPONENTS, etc.)
- Deferred tests to reconsider

**Otherwise state**: "No revisions needed - proceed to implementation with current plan"

### Final Recommendation

- [ ] **APPROVE**: Proceed to Prompt 5 (Implementation) with current plan
- [ ] **APPROVE WITH MINOR CHANGES**: Address suggestions, then proceed to Prompt 5
- [ ] **REVISION REQUIRED**: Address critical issues, then re-review
- [ ] **RECONSIDER APPROACH**: Fundamental issues with integration scope or philosophy

[Explanation of recommendation]

---
Example Review Outputs

Example 1: Approval with Minor Changes

## Integration Test Plan Review

### Executive Summary
- **Overall Assessment**: Strong with minor suggestions
- **Total Seams**: P0: 4, P1: 6, P2: 2, Deferred: 3
- **Critical Issues**: 0
- **Recommendations**: 3 minor suggestions
- **Estimated Implementation Effort**: 8 hours for P0, 12 hours for P1

### Validation Results

#### ✅ Strengths
1. P0 seams are all CONFIRMED (Prompt 1 + 2) with high business value
2. Clear seam descriptions using → arrows
3. Appropriate use of fakeredis (not mocks)
4. Realistic test count (10 total - selective, not comprehensive)

#### SUGGESTIONS (Consider Improvements)**:
1. **TextProcessorService → AIResponseCache** - Add resilience test
    - **Observation**: Plan includes cache hit/miss but not cache failure
    - **Benefit**: Validates graceful degradation (business-critical)
    - **Recommendation**: Add "Service handles cache failure gracefully" as P1 test

[Additional suggestions...]

### Final Recommendation
- [x] **APPROVE WITH MINOR CHANGES**: Address suggestions, then proceed to Prompt 5

Example 2: Revision Required

## Integration Test Plan Review

### Executive Summary
- **Overall Assessment**: Needs Revision
- **Total Seams**: P0: 12, P1: 8, P2: 5, Deferred: 2
- **Critical Issues**: 3 blocking issues
- **Recommendations**: 5 priority adjustments

### Validation Results

#### ⚠️ Issues Found

**CRITICAL (Must Fix Before Implementation)**:
1. **Service → Cache Key Validation** - Unit test disguised as integration test
    - **Problem**: Test mocks cache and verifies .build_key() was called with correct params
    - **Impact**: Duplicates unit test coverage, provides no integration value
    - **Recommendation**: Remove from integration tests (already covered in unit tests)
    - **Priority**: Remove

2. **API → Service → Cache → Database → External API** - Too many components
    - **Problem**: Spans 5 components across multiple boundaries
    - **Impact**: This is an E2E test, not integration test
    - **Recommendation**: Reclassify as E2E test or split into smaller integration tests
    - **Priority**: Remove from integration suite

[Continue...]

### Final Recommendation
- [ ] **REVISION REQUIRED**: Address critical issues, then re-review

---
Success Criteria

Review is complete when:

1. Philosophy Understanding: Demonstrates clear understanding of our integration testing principles
2. Structural Validation: Confirms test plan has all required sections
3. Integration Verification: Validates tests are truly integration (not unit tests)
4. Priority Validation: Confirms P0 tests are genuinely critical path
5. Gap Analysis: Identifies missing seams (resilience, security, performance)
6. Honest Assessment: Provides actionable feedback, not rubber stamp approval
7. Clear Recommendation: Explicit APPROVE/REVISE decision with reasoning

The review should provide specific, actionable feedback that improves test plan quality before implementation begins.