# Shared Schema Tests Review Template - [SCHEMA_AREA]

> **Instructions:** Replace `[SCHEMA_AREA]` with the actual schema area (e.g., "Text Processing Models", "Monitoring Schemas", "Common Data Structures"). 
> This template helps systematically review shared schema tests to ensure they meet our criteria.

## Review Criteria for Shared Schema Tests

Shared schema tests should meet these criteria:
- ✅ **Pydantic model validation** - Test field validation, type coercion, and constraint enforcement
- ✅ **Request/response schemas** - Test API contract compliance and data structure validation
- ✅ **Data structure integrity** - Test model serialization, deserialization, and field relationships
- ✅ **Validation edge cases** - Test boundary conditions, invalid inputs, and error handling
- ✅ **Schema evolution** - Test backward compatibility and schema migration scenarios

## Files to Review

> **Instructions:** 
> 1. List all test files in the `backend/tests/shared_schemas/` directory
> 2. Group them by logical categories (examples below)
> 3. Include file sizes and line counts for context
> 4. Use checkboxes `[ ]` initially, then mark `[x]` when reviewed
> 5. Add status indicators: **✅ PROPER SCHEMA**, **❌ MOVE TO [DIRECTORY]**, **⚠️ PLACEHOLDER**

### Request/Response Models
- [ ] `test_[api_models].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[request_schemas].py` ([SIZE], [LINES] lines) - [Brief description]

### Domain Data Structures
- [ ] `test_[domain_models].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[business_entities].py` ([SIZE], [LINES] lines) - [Brief description]

### Common/Shared Models
- [ ] `test_common_[schemas].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[enums_constants].py` ([SIZE], [LINES] lines) - [Brief description]

### Configuration Schemas
- [ ] `test_[config_models].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[settings_schemas].py` ([SIZE], [LINES] lines) - [Brief description]

### Validation & Error Models
- [ ] `test_[error_schemas].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[validation_models].py` ([SIZE], [LINES] lines) - [Brief description]

### Monitoring & Metrics Models
- [ ] `test_[monitoring_schemas].py` ([SIZE], [LINES] lines) - [Brief description]
- [ ] `test_[metrics_models].py` ([SIZE], [LINES] lines) - [Brief description]

> **Note:** Adjust categories based on your schema structure. Common categories include:
> - Request/Response Models, Domain Data Structures, Common/Shared Models, Configuration Schemas, Validation Models, etc.

## Review Notes

### Completed Reviews

> **Instructions:** For each file reviewed, add an entry like this:

**[N]. `test_[schema].py` [STATUS_ICON] [CLASSIFICATION]**
   - [Key findings about what the test covers]
   - [Assessment of Pydantic model validation coverage]
   - [Notes about schema validation and edge cases]
   - [Coverage of serialization/deserialization scenarios]
   - Status: [Current location assessment and recommendation]

> **Status Icons:** ✅ ❌ ⚠️
> **Classifications:** 
> - **PROPER SCHEMA** - correctly located and designed schema tests
> - **MISPLACED - [TEST_TYPE]** - should be moved to different directory
> - **PLACEHOLDER FILE** - contains only placeholder tests

### Issues Found

> **Instructions:** List all issues discovered during review:

1. **[Issue category]** ([file names]) [description]
2. **[Issue category]** ([file names]) [description]

> **Common issue categories:**
> - Placeholder files, Misplaced API tests, Misplaced service logic tests, Missing validation tests, Incomplete edge case coverage, etc.

### Recommendations

#### Immediate Actions
1. **Move misplaced tests:**
   - Move `test_[file].py` → `tests/[correct_directory]/test_[new_name].py`

2. **Complete placeholder tests:**
   - Implement `test_[file].py` with actual schema validation tests
   - Or remove if functionality is covered elsewhere

3. **Fix schema test violations:**
   - [Specific recommendations for files that don't meet schema test criteria]

#### Overall Assessment

> **Instructions:** Provide overall assessment using this structure:

**[ASSESSMENT_LEVEL]** schema test compliance! [Brief summary]

- ✅/❌ **Pydantic model validation** - [Assessment details]
- ✅/❌ **Request/response schema testing** - [Assessment details]  
- ✅/❌ **Data structure integrity** - [Assessment details]
- ✅/❌ **Validation edge cases** - [Assessment details]
- ✅/❌ **Schema evolution support** - [Assessment details]

**Key Strengths:**
- [List major strengths found in the schema tests]

**Areas for Improvement:**
- [List areas that need attention in schema validation]

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
   - Copy this template to `backend/tests/shared_schemas/schema_review.md`
   - Replace `[SCHEMA_AREA]` with your actual schema area name
   - List all test files in the target directory

2. **File Discovery:**
   ```bash
   # Get file list with sizes
   ls -la backend/tests/shared_schemas/
   
   # Get line counts
   wc -l backend/tests/shared_schemas/*.py
   ```

3. **Review Process:**
   - Read each test file systematically
   - Check against shared schema test criteria
   - Look for Pydantic model validation, field constraints, type checking
   - Assess validation edge cases and error handling
   - Note coverage gaps in serialization/deserialization scenarios

4. **Classification Guidelines:**
   - **✅ PROPER SCHEMA:** Tests Pydantic models, validation, serialization
   - **❌ MOVE TO API:** Tests HTTP endpoints or API behavior
   - **❌ MOVE TO SERVICES:** Tests business logic or service operations
   - **❌ MOVE TO INTEGRATION:** Tests cross-service data flow
   - **❌ MOVE TO INFRASTRUCTURE:** Tests infrastructure components
   - **⚠️ PLACEHOLDER:** Only contains TODO or empty tests

5. **Final Steps:**
   - Add TODO comments to misplaced files
   - Update progress tracking
   - Provide comprehensive recommendations

### Review Criteria Details

**Pydantic model validation:**
- Tests field validation rules and constraints
- Tests type coercion and conversion behavior
- Tests custom validators and validation logic
- Tests required vs optional field handling

**Request/response schemas:**
- Tests API contract compliance
- Tests serialization to/from JSON
- Tests field aliasing and naming conventions
- Tests nested model validation

**Data structure integrity:**
- Tests model initialization and construction
- Tests field default values and factories
- Tests model inheritance and composition
- Tests enum and constant validation

**Validation edge cases:**
- Tests boundary conditions and limits
- Tests invalid input handling and error messages
- Tests null/empty value handling
- Tests malformed data scenarios

**Schema evolution:**
- Tests backward compatibility with old data
- Tests optional field additions
- Tests field deprecation scenarios
- Tests migration and transformation logic 