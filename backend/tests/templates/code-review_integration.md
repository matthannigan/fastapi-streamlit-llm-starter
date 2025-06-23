# Integration Tests Review Template - [MODULE_NAME]

> **Instructions:** Replace `[MODULE_NAME]` with the actual integration area (e.g., "Resilience Service", "Cache Integration", "Auth Flow"). 
> This template helps systematically review integration tests to ensure they meet our criteria.

## Review Criteria for Integration Tests

Integration tests should meet these criteria:
- ✅ **Cross-layer integration** - Test multiple services/components working together
- ✅ **Service boundary interactions** - Verify interfaces between different layers
- ✅ **End-to-end workflows** - Test complete request flows through the system
- ✅ **Real dependency usage** - May use actual Redis, databases, or external services (when appropriate)
- ✅ **Realistic data flows** - Test with realistic data scenarios and edge cases

## Files to Review

> **Instructions:** 
> 1. List all test files in the `backend/tests/integration/` directory
> 2. Group them by logical categories (examples below)
> 3. Include file sizes and line counts for context
> 4. Use checkboxes `[ ]` initially, then mark `[x]` when reviewed
> 5. Add status indicators: **✅ PROPER INTEGRATION**, **❌ MOVE TO [DIRECTORY]**, **⚠️ PLACEHOLDER**

### End-to-End Workflows
- [ ] `test_[workflow]_end_to_end.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[feature]_integration.py` ([SIZE], [LINES] lines) - [Brief description]

### Service Boundary Testing
- [ ] `test_[service]_[other_service]_integration.py` ([SIZE], [LINES] lines) - [Brief description]

### Authentication & Authorization Flows
- [ ] `test_auth_[flow].py` ([SIZE], [LINES] lines) - [Brief description]

### Data Layer Integration
- [ ] `test_[service]_database_integration.py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_cache_integration.py` ([SIZE], [LINES] lines) - [Brief description]

### External Service Integration
- [ ] `test_[external_service]_integration.py` ([SIZE], [LINES] lines) - [Brief description]

### Cross-Component Scenarios
- [ ] `test_[scenario]_integration.py` ([SIZE], [LINES] lines) - [Brief description]

> **Note:** Adjust categories based on your integration scope. Common categories include:
> - End-to-End Workflows, Service Boundaries, Auth Flows, Data Layer, External Services, Cross-Component Scenarios, etc.

## Review Notes

### Completed Reviews

> **Instructions:** For each file reviewed, add an entry like this:

**[N]. `test_[integration_scenario].py` [STATUS_ICON] [CLASSIFICATION]**
   - [Key findings about what integration is being tested]
   - [Assessment of cross-layer/service interactions]
   - [Notes about real vs mocked dependencies]
   - [Coverage of integration scenarios and edge cases]
   - Status: [Current location assessment and recommendation]

> **Status Icons:** ✅ ❌ ⚠️
> **Classifications:** 
> - **PROPER INTEGRATION** - correctly located and designed for integration testing
> - **MISPLACED - [TEST_TYPE]** - should be moved to different directory (e.g., infrastructure, api, services)
> - **PLACEHOLDER FILE** - contains only placeholder tests

### Issues Found

> **Instructions:** List all issues discovered during review:

1. **[Issue category]** ([file names]) [description]
2. **[Issue category]** ([file names]) [description]

> **Common issue categories:**
> - Placeholder files, Misplaced unit tests, Over-mocked dependencies, Missing end-to-end scenarios, Infrastructure logic in integration tests, etc.

### Recommendations

#### Immediate Actions
1. **Move misplaced tests:**
   - Move `test_[file].py` → `tests/[correct_directory]/test_[new_name].py`

2. **Complete placeholder tests:**
   - Implement `test_[file].py` with actual [integration] tests
   - Or remove if integration scenarios are covered elsewhere

3. **Fix integration violations:**
   - [Specific recommendations for files that don't meet integration criteria]

#### Overall Assessment

> **Instructions:** Provide overall assessment using this structure:

**[ASSESSMENT_LEVEL]** integration test compliance! [Brief summary]

- ✅/❌ **Cross-layer integration coverage** - [Assessment details]
- ✅/❌ **Service boundary interaction testing** - [Assessment details]  
- ✅/❌ **End-to-end workflow testing** - [Assessment details]
- ✅/❌ **Realistic dependency usage** - [Assessment details]
- ✅/❌ **Complete scenario coverage** - [Assessment details]

**Key Strengths:**
- [List major strengths found in the integration test suite]

**Areas for Improvement:**
- [List areas that need attention for better integration coverage]

> **Assessment levels:** EXCELLENT, GOOD, FAIR, NEEDS IMPROVEMENT

## Review Progress

> **Instructions:** Update these metrics as you progress:

**Started:** [DATE]
**Files Reviewed:** [X]/[TOTAL] ([PERCENTAGE]% complete)
**Issues Found:** [COUNT] ([breakdown by type])
**Recommendations Made:** [COUNT]

---

## Usage Instructions

### How to Use This Template

1. **Preparation:**
   - Copy this template to `backend/tests/integration/integration_review.md`
   - Replace `[MODULE_NAME]` with your actual integration area name
   - List all test files in the integration directory

2. **File Discovery:**
   ```bash
   # Get file list with sizes
   ls -la backend/tests/integration/
   
   # Get line counts
   wc -l backend/tests/integration/*.py
   ```

3. **Review Process:**
   - Read each test file systematically
   - Check against integration test criteria
   - Look for service boundary interactions, cross-layer testing, end-to-end flows
   - Assess appropriate use of real vs mocked dependencies
   - Note coverage gaps in integration scenarios

4. **Classification Guidelines:**
   - **✅ PROPER INTEGRATION:** Tests multiple services/layers together, realistic workflows
   - **❌ MOVE TO INFRASTRUCTURE:** Tests single component in isolation
   - **❌ MOVE TO API:** Tests only HTTP endpoints without cross-layer interaction
   - **❌ MOVE TO SERVICES:** Tests only business logic without integration aspects
   - **❌ MOVE TO PERFORMANCE:** Measures timing/throughput rather than integration
   - **⚠️ PLACEHOLDER:** Only contains TODO or empty tests

5. **Final Steps:**
   - Add TODO comments to misplaced files
   - Update progress tracking
   - Provide comprehensive recommendations

### Review Criteria Details

**Cross-layer integration:**
- Tests multiple services/components working together
- Verifies data flows between different system layers
- Tests service composition and orchestration

**Service boundary interactions:**
- Tests interfaces between different services
- Verifies contract compliance across boundaries
- Tests error propagation and handling between services

**End-to-end workflows:**
- Tests complete user scenarios through the system
- Verifies full request/response cycles
- Tests realistic business workflows

**Realistic dependency usage:**
- May use actual databases, Redis, external services when appropriate
- Balances real dependencies with test speed and reliability
- Tests actual integration points, not just mocked interfaces

**Complete scenario coverage:**
- Tests both success and failure integration scenarios
- Tests edge cases in service interactions
- Verifies error handling across service boundaries 