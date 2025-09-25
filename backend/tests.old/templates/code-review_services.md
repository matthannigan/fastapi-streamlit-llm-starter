# Domain Service Tests Review Template - [SERVICE_AREA]

> **Instructions:** Replace `[SERVICE_AREA]` with the actual service domain (e.g., "Text Processing", "User Management", "Content Analysis"). 
> This template helps systematically review domain service tests to ensure they meet our criteria.

## Review Criteria for Domain Service Tests

Domain service tests should meet these criteria:
- ✅ **Business logic testing** - Test core business rules and domain-specific functionality
- ✅ **Service composition** - Verify proper orchestration of infrastructure components
- ✅ **Input validation & processing** - Test domain-specific data validation and transformation
- ✅ **Error handling & edge cases** - Verify business rule violations and boundary conditions
- ✅ **Infrastructure integration** - Test proper usage of infrastructure services (cache, AI, etc.)

## Files to Review

> **Instructions:** 
> 1. List all test files in the `backend/tests/services/` directory
> 2. Group them by logical categories (examples below)
> 3. Include file sizes and line counts for context
> 4. Use checkboxes `[ ]` initially, then mark `[x]` when reviewed
> 5. Add status indicators: **✅ PROPER SERVICE**, **❌ MOVE TO [DIRECTORY]**, **⚠️ PLACEHOLDER**

### Core Business Services
- [ ] `test_[domain_service].py` ([SIZE], [LINES] lines) - [Brief description of business logic tested]
- [ ] `test_[processing_service].py` ([SIZE], [LINES] lines) - [Brief description of processing logic]

### Data Processing & Transformation
- [ ] `test_[data_processor].py` ([SIZE], [LINES] lines) - [Brief description of data transformation logic]
- [ ] `test_[content_analyzer].py` ([SIZE], [LINES] lines) - [Brief description of analysis logic]

### Business Rule Validation
- [ ] `test_[validator_service].py` ([SIZE], [LINES] lines) - [Brief description of validation rules]
- [ ] `test_[business_rules].py` ([SIZE], [LINES] lines) - [Brief description of business rule testing]

### Workflow & Orchestration
- [ ] `test_[workflow_service].py` ([SIZE], [LINES] lines) - [Brief description of workflow logic]
- [ ] `test_[orchestrator].py` ([SIZE], [LINES] lines) - [Brief description of service orchestration]

### Domain-Specific Features
- [ ] `test_[feature_service].py` ([SIZE], [LINES] lines) - [Brief description of domain feature]

### Service Utilities
- [ ] `test_[service_helper].py` ([SIZE], [LINES] lines) - [Brief description of service utilities]

> **Note:** Adjust categories based on your service domain. Common categories include:
> - Core Business Services, Data Processing, Business Rules, Workflows, Domain Features, Service Utilities, etc.

## Review Notes

### Completed Reviews

> **Instructions:** For each file reviewed, add an entry like this:

**[N]. `test_[service_name].py` [STATUS_ICON] [CLASSIFICATION]**
   - [Key findings about what business logic is tested]
   - [Assessment of service composition and infrastructure usage]
   - [Notes about business rule validation and edge cases]
   - [Coverage of domain-specific scenarios and error handling]
   - Status: [Current location assessment and recommendation]

> **Status Icons:** ✅ ❌ ⚠️
> **Classifications:** 
> - **PROPER SERVICE** - correctly located and designed for domain service testing
> - **MISPLACED - [TEST_TYPE]** - should be moved to different directory (e.g., infrastructure, api, integration)
> - **PLACEHOLDER FILE** - contains only placeholder tests

### Issues Found

> **Instructions:** List all issues discovered during review:

1. **[Issue category]** ([file names]) [description]
2. **[Issue category]** ([file names]) [description]

> **Common issue categories:**
> - Placeholder files, Infrastructure logic in service tests, Missing business rule validation, Insufficient edge case coverage, Improper mocking of dependencies, etc.

### Recommendations

#### Immediate Actions
1. **Move misplaced tests:**
   - Move `test_[file].py` → `tests/[correct_directory]/test_[new_name].py`

2. **Complete placeholder tests:**
   - Implement `test_[file].py` with actual [service] tests
   - Or remove if service functionality is covered elsewhere

3. **Fix service test violations:**
   - [Specific recommendations for files that don't meet domain service testing criteria]

#### Overall Assessment

> **Instructions:** Provide overall assessment using this structure:

**[ASSESSMENT_LEVEL]** domain service test compliance! [Brief summary]

- ✅/❌ **Business logic coverage** - [Assessment details]
- ✅/❌ **Service composition testing** - [Assessment details]  
- ✅/❌ **Input validation & processing** - [Assessment details]
- ✅/❌ **Error handling & edge cases** - [Assessment details]
- ✅/❌ **Infrastructure integration** - [Assessment details]

**Key Strengths:**
- [List major strengths found in the service test suite]

**Areas for Improvement:**
- [List areas that need attention for better domain service testing coverage]

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
   - Copy this template to `backend/tests/services/service_review.md`
   - Replace `[SERVICE_AREA]` with your actual service domain name
   - List all test files in the services directory

2. **File Discovery:**
   ```bash
   # Get file list with sizes
   ls -la backend/tests/services/
   
   # Get line counts for all service test files
   wc -l backend/tests/services/*.py
   ```

3. **Review Process:**
   - Read each test file systematically
   - Check against domain service test criteria
   - Look for business logic testing, service composition, domain-specific validation
   - Assess proper mocking of infrastructure dependencies
   - Note coverage gaps in business rules and edge cases

4. **Classification Guidelines:**
   - **✅ PROPER SERVICE:** Tests business logic, service composition, domain-specific functionality
   - **❌ MOVE TO INFRASTRUCTURE:** Tests individual infrastructure components in isolation
   - **❌ MOVE TO API:** Tests HTTP endpoints using FastAPI TestClient
   - **❌ MOVE TO INTEGRATION:** Tests cross-layer interactions beyond service boundaries
   - **❌ MOVE TO PERFORMANCE:** Measures timing/throughput rather than business functionality
   - **⚠️ PLACEHOLDER:** Only contains TODO or empty tests

5. **Final Steps:**
   - Add TODO comments to misplaced files
   - Update progress tracking
   - Provide comprehensive recommendations

### Review Criteria Details

**Business logic testing:**
- Tests core domain rules and business processes
- Verifies domain-specific calculations and transformations
- Tests business workflow implementations
- Validates domain model behavior and state changes

**Service composition:**
- Tests proper orchestration of infrastructure services
- Verifies correct usage of cache, AI, database services
- Tests service dependency injection and configuration
- Validates service layer abstractions and interfaces

**Input validation & processing:**
- Tests domain-specific input validation rules
- Verifies data transformation and sanitization logic
- Tests business rule enforcement on inputs
- Validates proper handling of domain data types

**Error handling & edge cases:**
- Tests business rule violation scenarios
- Verifies proper exception handling for domain errors
- Tests boundary conditions and edge cases
- Validates error propagation and recovery mechanisms

**Infrastructure integration:**
- Tests proper mocking of infrastructure dependencies
- Verifies service behavior with different infrastructure states
- Tests fallback mechanisms and resilience patterns
- Validates configuration and dependency management 