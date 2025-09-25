# Infrastructure Tests Review Template - [MODULE_NAME]

> **Instructions:** Replace `[MODULE_NAME]` with the actual module name (e.g., "Cache", "Security", "AI"). 
> This template helps systematically review infrastructure tests to ensure they meet our criteria.

## Review Criteria for Infrastructure Tests

Infrastructure tests should meet these criteria:
- ✅ **High test coverage requirements (>90%)**
- ✅ **Business-agnostic abstractions** - not tied to specific business logic
- ✅ **Stable APIs with backward compatibility guarantees**  
- ✅ **Performance-critical implementations**
- ✅ **Test individual infrastructure services in isolation with mocked external dependencies**

## Files to Review

> **Instructions:** 
> 1. List all test files in the `backend/tests/infrastructure/[module]/` directory
> 2. Group them by logical categories (examples below)
> 3. Include file sizes and line counts for context
> 4. Use checkboxes `[ ]` initially, then mark `[x]` when reviewed
> 5. Add status indicators: **✅ PROPER INFRASTRUCTURE**, **❌ MOVE TO [DIRECTORY]**, **⚠️ PLACEHOLDER**

### Core Infrastructure Components
- [ ] `test_[component].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[component2].py` ([SIZE], [LINES] lines) - [Brief description]

### Configuration & Management
- [ ] `test_[config_component].py` ([SIZE], [LINES] lines) - [Brief description]

### Integration & Communication
- [ ] `test_[integration_component].py` ([SIZE], [LINES] lines) - [Brief description]

### Security & Validation
- [ ] `test_[security_component].py` ([SIZE], [LINES] lines) - [Brief description]

### Performance & Monitoring
- [ ] `test_[performance_component].py` ([SIZE], [LINES] lines) - [Brief description]

### Utilities & Helpers
- [ ] `test_[utility_component].py` ([SIZE], [LINES] lines) - [Brief description]

> **Note:** Adjust categories based on your module's structure. Common categories include:
> - Core Components, Configuration, Integration, Security, Performance, Utilities, Error Handling, etc.

## Review Notes

### Completed Reviews

> **Instructions:** For each file reviewed, add an entry like this:

**[N]. `test_[component].py` [STATUS_ICON] [CLASSIFICATION]**
   - [Key findings about what the test covers]
   - [Assessment of business-agnostic nature]
   - [Notes about test isolation and mocking]
   - [Coverage and edge case assessment]
   - Status: [Current location assessment and recommendation]

> **Status Icons:** ✅ ❌ ⚠️
> **Classifications:** 
> - **PROPER INFRASTRUCTURE** - correctly located and designed
> - **MISPLACED - [TEST_TYPE]** - should be moved to different directory
> - **PLACEHOLDER FILE** - contains only placeholder tests

### Issues Found

> **Instructions:** List all issues discovered during review:

1. **[Issue category]** ([file names]) [description]
2. **[Issue category]** ([file names]) [description]

> **Common issue categories:**
> - Placeholder files, Misplaced integration tests, Misplaced performance tests, Business logic in infrastructure tests, Missing mocking, etc.

### Recommendations

#### Immediate Actions
1. **Move misplaced tests:**
   - Move `test_[file].py` → `tests/[correct_directory]/test_[new_name].py`

2. **Complete placeholder tests:**
   - Implement `test_[file].py` with actual [component] tests
   - Or remove if functionality is covered elsewhere

3. **Fix infrastructure violations:**
   - [Specific recommendations for files that don't meet criteria]

#### Overall Assessment

> **Instructions:** Provide overall assessment using this structure:

**[ASSESSMENT_LEVEL]** infrastructure test compliance! [Brief summary]

- ✅/❌ **Business-agnostic abstractions** - [Assessment details]
- ✅/❌ **Isolated testing with mocked dependencies** - [Assessment details]  
- ✅/❌ **High test coverage** - [Assessment details]
- ✅/❌ **Stable API contract testing** - [Assessment details]
- ✅/❌ **Performance-critical implementations** - [Assessment details]

**Key Strengths:**
- [List major strengths found in the module's tests]

**Areas for Improvement:**
- [List areas that need attention]

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
   - Copy this template to `backend/tests/infrastructure/[module]/infrastructure_review.md`
   - Replace `[MODULE_NAME]` with your actual module name
   - List all test files in the target directory

2. **File Discovery:**
   ```bash
   # Get file list with sizes
   ls -la backend/tests/infrastructure/[module]/
   
   # Get line counts
   wc -l backend/tests/infrastructure/[module]/*.py
   ```

3. **Review Process:**
   - Read each test file systematically
   - Check against infrastructure test criteria
   - Look for business logic, external dependencies, integration concerns
   - Assess test isolation and mocking
   - Note coverage gaps or edge cases

4. **Classification Guidelines:**
   - **✅ PROPER INFRASTRUCTURE:** Business-agnostic, isolated, comprehensive
   - **❌ MOVE TO INTEGRATION:** Tests multiple services together
   - **❌ MOVE TO PERFORMANCE:** Measures timing/throughput/resource usage
   - **❌ MOVE TO API:** Tests HTTP endpoints
   - **❌ MOVE TO SERVICES:** Tests business logic
   - **⚠️ PLACEHOLDER:** Only contains TODO or empty tests

5. **Final Steps:**
   - Add TODO comments to misplaced files
   - Update progress tracking
   - Provide comprehensive recommendations

### Review Criteria Details

**Business-agnostic abstractions:**
- Tests focus on reusable patterns, not specific business rules
- Could be used across different applications/domains
- Infrastructure concerns, not domain logic

**Isolated testing:**
- External dependencies are mocked
- Tests don't rely on network, filesystem, databases
- Each test can run independently

**High coverage:**
- Edge cases and error conditions tested
- Boundary value testing
- Both success and failure paths covered

**Stable APIs:**
- Tests verify backward compatibility
- Breaking changes would be caught
- Configuration migration tested

**Performance-critical:**
- Infrastructure that affects system performance
- Caching, connection pooling, retry logic, etc.
- Error handling and resilience patterns 