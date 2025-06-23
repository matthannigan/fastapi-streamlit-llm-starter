# API Tests Review Template - [API_VERSION/AREA]

> **Instructions:** Replace `[API_VERSION/AREA]` with the actual API area (e.g., "v1 Public API", "Internal Admin API", "Monitoring Endpoints"). 
> This template helps systematically review API tests to ensure they meet our criteria.

## Review Criteria for API Tests

API tests should meet these criteria:
- ✅ **HTTP endpoint testing** - Test actual HTTP requests/responses using FastAPI TestClient
- ✅ **Request/response validation** - Verify proper handling of headers, status codes, and body formats
- ✅ **Authentication & authorization** - Test access controls and permission boundaries
- ✅ **Error handling** - Verify proper error responses for invalid inputs and edge cases
- ✅ **API contract compliance** - Ensure responses match OpenAPI/schema specifications

## Files to Review

> **Instructions:** 
> 1. List all test files in the `backend/tests/api/` directory
> 2. Group them by logical categories (examples below)
> 3. Include file sizes and line counts for context
> 4. Use checkboxes `[ ]` initially, then mark `[x]` when reviewed
> 5. Add status indicators: **✅ PROPER API**, **❌ MOVE TO [DIRECTORY]**, **⚠️ PLACEHOLDER**

### Public API Endpoints (v1/)
- [ ] `test_[endpoint_group].py` ([SIZE], [LINES] lines) - [Brief description of endpoints tested]
- [ ] `test_[feature]_endpoints.py` ([SIZE], [LINES] lines) - [Brief description of feature endpoints]

### Internal/Admin API Endpoints (internal/)
- [ ] `test_[admin_feature].py` ([SIZE], [LINES] lines) - [Brief description of admin endpoints]
- [ ] `test_[monitoring_endpoints].py` ([SIZE], [LINES] lines) - [Brief description of monitoring endpoints]

### Authentication & Authorization
- [ ] `test_auth_[flow].py` ([SIZE], [LINES] lines) - [Brief description of auth testing]

### Error Handling & Validation
- [ ] `test_[validation_endpoints].py` ([SIZE], [LINES] lines) - [Brief description of validation testing]

### Health & Status Endpoints
- [ ] `test_health.py` ([SIZE], [LINES] lines) - [Brief description of health check endpoints]

### Custom API Features
- [ ] `test_[custom_feature].py` ([SIZE], [LINES] lines) - [Brief description of custom endpoints]

> **Note:** Adjust categories based on your API structure. Common categories include:
> - Public Endpoints, Internal/Admin, Authentication, Error Handling, Health Checks, Custom Features, etc.

## Review Notes

### Completed Reviews

> **Instructions:** For each file reviewed, add an entry like this:

**[N]. `test_[endpoint_group].py` [STATUS_ICON] [CLASSIFICATION]**
   - [Key findings about what endpoints are tested]
   - [Assessment of HTTP request/response testing]
   - [Notes about authentication and authorization coverage]
   - [Coverage of error cases and edge scenarios]
   - Status: [Current location assessment and recommendation]

> **Status Icons:** ✅ ❌ ⚠️
> **Classifications:** 
> - **PROPER API** - correctly located and designed for API endpoint testing
> - **MISPLACED - [TEST_TYPE]** - should be moved to different directory (e.g., integration, services, infrastructure)
> - **PLACEHOLDER FILE** - contains only placeholder tests

### Issues Found

> **Instructions:** List all issues discovered during review:

1. **[Issue category]** ([file names]) [description]
2. **[Issue category]** ([file names]) [description]

> **Common issue categories:**
> - Placeholder files, Missing authentication tests, Insufficient error handling coverage, Business logic in API tests, Missing status code validation, etc.

### Recommendations

#### Immediate Actions
1. **Move misplaced tests:**
   - Move `test_[file].py` → `tests/[correct_directory]/test_[new_name].py`

2. **Complete placeholder tests:**
   - Implement `test_[file].py` with actual [endpoint] tests
   - Or remove if API functionality is covered elsewhere

3. **Fix API test violations:**
   - [Specific recommendations for files that don't meet API testing criteria]

#### Overall Assessment

> **Instructions:** Provide overall assessment using this structure:

**[ASSESSMENT_LEVEL]** API test compliance! [Brief summary]

- ✅/❌ **HTTP endpoint coverage** - [Assessment details]
- ✅/❌ **Request/response validation** - [Assessment details]  
- ✅/❌ **Authentication & authorization testing** - [Assessment details]
- ✅/❌ **Error handling coverage** - [Assessment details]
- ✅/❌ **API contract compliance** - [Assessment details]

**Key Strengths:**
- [List major strengths found in the API test suite]

**Areas for Improvement:**
- [List areas that need attention for better API testing coverage]

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
   - Copy this template to `backend/tests/api/api_review.md`
   - Replace `[API_VERSION/AREA]` with your actual API area name
   - List all test files in the API directory

2. **File Discovery:**
   ```bash
   # Get file list with sizes
   ls -la backend/tests/api/
   
   # Get line counts for all API test files
   wc -l backend/tests/api/**/*.py
   ```

3. **Review Process:**
   - Read each test file systematically
   - Check against API test criteria
   - Look for HTTP endpoint testing, request/response validation, auth coverage
   - Assess proper use of FastAPI TestClient
   - Note coverage gaps in error handling and edge cases

4. **Classification Guidelines:**
   - **✅ PROPER API:** Tests HTTP endpoints using FastAPI TestClient, proper request/response validation
   - **❌ MOVE TO INFRASTRUCTURE:** Tests individual components in isolation without HTTP layer
   - **❌ MOVE TO INTEGRATION:** Tests cross-layer interactions beyond single endpoint
   - **❌ MOVE TO SERVICES:** Tests business logic without HTTP interface
   - **❌ MOVE TO PERFORMANCE:** Measures timing/throughput rather than endpoint functionality
   - **⚠️ PLACEHOLDER:** Only contains TODO or empty tests

5. **Final Steps:**
   - Add TODO comments to misplaced files
   - Update progress tracking
   - Provide comprehensive recommendations

### Review Criteria Details

**HTTP endpoint testing:**
- Uses FastAPI TestClient for actual HTTP requests
- Tests real HTTP methods (GET, POST, PUT, DELETE, etc.)
- Verifies endpoint routing and URL parameters

**Request/response validation:**
- Tests proper handling of request headers and body
- Verifies correct HTTP status codes (200, 400, 401, 404, 500, etc.)
- Validates response body format and content
- Tests content-type handling (JSON, form data, etc.)

**Authentication & authorization:**
- Tests protected endpoints require proper authentication
- Verifies API key validation and JWT token handling
- Tests role-based access control and permissions
- Validates unauthorized access returns appropriate errors

**Error handling:**
- Tests invalid request data returns proper 400 errors
- Verifies missing authentication returns 401 errors
- Tests not found resources return 404 errors
- Validates server errors return appropriate 500 responses

**API contract compliance:**
- Ensures responses match OpenAPI/schema specifications
- Tests backward compatibility of API responses
- Verifies proper error message formats
- Validates API versioning behavior 