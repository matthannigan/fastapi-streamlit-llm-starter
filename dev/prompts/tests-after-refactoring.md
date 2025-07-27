I've recently completed a refactoring of `backend/app/`. Please help me fix testing failures systematically. Unless I explicitly direct you, do not make any modifications to modules in `backend/app/`. Instead, focus your updates on the test code in `backend/tests/`.

## Primary Objectives
1. **Behavior-Focused Testing**: Make tests focus on public API behavior rather than internal implementation details
2. **Resilient Assertions**: Create robust tests that survive refactoring without losing test value
3. **Defensive Programming**: Add appropriate error handling and null checks in tests

## Common Refactoring-Related Failure Patterns to Address

### 1. **URL/Endpoint Route Changes**
- Look for 404 errors indicating endpoint paths have changed
- Update URL patterns to match new routing structure
- Check for prefix changes in router configurations

### 2. **HTTP Status Code Evolution**
- Accept semantically appropriate status codes (e.g., 422 for validation errors, 401 for auth failures)
- Use ranges like `assert response.status_code in [200, 422]` instead of exact matches
- Distinguish between business logic errors (200 with error payload) vs HTTP protocol errors (4xx/5xx)

### 3. **Authentication Handling Variations**
- Handle both HTTP response patterns (`401` status) and exception patterns (`AuthenticationError`)
- Use try-catch blocks: `try: assert response.status_code == 401; except AuthenticationError: pass`
- Test the security requirement, not the specific error mechanism

### 4. **Response Structure Changes**
- Use conditional field access: `if "field" in data and data["field"] is not None:`
- Verify data types and structure rather than exact values when appropriate
- Check for field presence before asserting specific values

### 5. **Mock Dependency Issues**
- Make mock assertions flexible: accept both mocked values and real fallback values
- Focus on behavior verification rather than strict mock call verification
- Use conditional checks: `if mock_value == expected: assert exact_match; else: assert valid_structure`

### 6. **Error Response Format Evolution**
- Handle different error response structures (FastAPI validation errors vs custom error responses)
- Check for both `detail` fields (HTTP errors) and custom error arrays (business logic)

### 7. **Exception Type Transitions** ⭐ *New Pattern*
- When refactoring changes from HTTP responses to custom exceptions (e.g., `AuthenticationError`, `ValidationError`, `InfrastructureError`)
- Update imports to include new exception types: `from app.core.exceptions import AuthenticationError, ValidationError`
- Use dual-pattern testing that handles both approaches gracefully
- Verify exception context and error messages contain appropriate keywords

### 8. **Multi-Format Error Response Structures** ⭐ *New Pattern*
- Handle multiple error response formats in the same test
- Check for FastAPI format (`{"detail": [...]}`) vs custom format (`{"error": "...", "error_code": "..."}`)
- Use cascading conditional checks with fallback validation
- Avoid assumptions about which format will be returned

### 9. **Keyword-Based Error Message Validation** ⭐ *New Pattern*
- Replace exact string matching with keyword-based validation
- Use `.lower()` and `in` operators for case-insensitive partial matching
- Focus on error semantics rather than exact wording
- Handle different error message templates gracefully

### 10. **Settings/Configuration Isolation** ⭐ *New Pattern*
- Properly save and restore configuration changes in tests
- Use try/finally blocks to ensure settings are reset even if tests fail
- Be aware that configuration changes can affect other tests running in parallel
- Consider using fixtures or context managers for configuration changes

### 11. **Dependency Override Cleanup** ⭐ *New Pattern*
- Always clean up `app.dependency_overrides` in finally blocks
- Use proper test isolation to avoid dependency leakage between tests
- Be consistent with override patterns across test suites
- Consider using fixtures for common dependency override patterns

## Testing Strategies to Apply

### **Flexible Assertions**
```python
# Instead of: assert data["value"] == 85.5
# Use: assert isinstance(data["value"], (int, float)) and data["value"] >= 0

# Instead of: assert response.status_code == 200  
# Use: assert response.status_code in [200, 422]  # Accept semantically valid codes
```

### **Defensive Data Access**
```python
# Instead of: assert data["nested"]["field"] == "value"
# Use: 
if "nested" in data and data["nested"] and "field" in data["nested"]:
    assert data["nested"]["field"] == "value"
else:
    assert isinstance(data.get("nested"), (dict, type(None)))
```

### **Robust Authentication Testing**
```python
# Instead of: assert response.status_code == 401
# Use:
try:
    response = client.get(endpoint)
    assert response.status_code == 401
except AuthenticationError as e:
    assert "API key required" in str(e)
```

### **Exception Type Transition Handling** ⭐ *New Strategy*
```python
# Handle both HTTP responses and custom exceptions
try:
    response = client.post(endpoint, json=payload)
    # If we get a response, check for appropriate error status codes
    assert response.status_code in [400, 422]
    # Check error message using flexible validation
    response_data = response.json()
    error_text = str(response_data).lower()
    assert "validation" in error_text or "invalid" in error_text
except ValidationError as e:
    # If ValidationError is raised, verify it contains expected context
    assert "required" in str(e).lower() or "validation" in str(e).lower()
```

### **Multi-Format Error Response Checking** ⭐ *New Strategy*
```python
# Handle different error response structures gracefully
error_detail = response.json()

# Check for either FastAPI validation format or custom error format
if "detail" in error_detail:
    # FastAPI validation error format
    assert any("validation_error" in str(error).lower() 
              for error in error_detail["detail"])
elif "error" in error_detail and error_detail.get("error"):
    # Custom error response format
    error_text = str(error_detail["error"]).lower()
    assert "validation" in error_text or "invalid" in error_text
else:
    # Fallback: check entire response for error indicators
    response_text = str(error_detail).lower()
    assert "error" in response_text or "invalid" in response_text
```

### **Keyword-Based Error Validation** ⭐ *New Strategy*
```python
# Instead of: assert "Batch size exceeds maximum limit of 2 requests" in response["detail"]
# Use flexible keyword-based validation:
error_text = str(response_data).lower()
assert ("exceeds" in error_text or "limit" in error_text or 
        "maximum" in error_text or "batch" in error_text)
```

### **Configuration Change Isolation** ⭐ *New Strategy*
```python
# Properly isolate configuration changes
def test_with_config_change(self, authenticated_client):
    original_value = settings.MAX_BATCH_REQUESTS_PER_CALL
    settings.MAX_BATCH_REQUESTS_PER_CALL = 2  # Temporarily change for test
    
    try:
        # Test logic here
        response = authenticated_client.post(endpoint, json=payload)
        assert response.status_code in [400, 422]
    finally:
        # Always restore original value
        settings.MAX_BATCH_REQUESTS_PER_CALL = original_value
```

### **Dependency Override Pattern** ⭐ *New Strategy*
```python
# Consistent dependency override with proper cleanup
def test_with_mock_service(self, authenticated_client):
    # Create mock
    mock_service = MagicMock()
    mock_service.process = AsyncMock(return_value=expected_result)
    
    # Override dependency
    app.dependency_overrides[get_service] = lambda: mock_service
    
    try:
        # Test logic here
        response = authenticated_client.post(endpoint, json=payload)
        assert response.status_code == 200
        
        # Verify mock was called (but be flexible about arguments)
        mock_service.process.assert_called_once()
    finally:
        # Always clean up overrides
        app.dependency_overrides.clear()
```

### **Mock Tolerance**
```python
# Instead of: mock.method.assert_called_once_with(exact_args)
# Use: 
if mock.method.called:
    mock.method.assert_called_once()  # Verify it was called, be flexible about args
```

## Success Criteria
- Tests verify the intended behavior and API contract
- Tests are resilient to reasonable implementation changes
- Authentication and authorization requirements are properly enforced
- Error handling works appropriately for edge cases
- Response structures contain expected data types and required fields
- Tests focus on user-facing functionality rather than internal mechanics
- Exception transitions are handled gracefully without losing test coverage
- Configuration changes are properly isolated and don't affect other tests

## Debugging Approach
1. **Analyze Error Patterns**: Group failures by type (routing, auth, validation, etc.)
2. **Check for Exception Type Changes**: Look for HTTP responses that now raise custom exceptions
3. **Update Imports**: Add imports for new exception types (`AuthenticationError`, `ValidationError`, etc.)
4. **Update URLs First**: Fix any endpoint routing changes
5. **Handle Auth Systematically**: Address authentication pattern changes across all tests
6. **Make Assertions Flexible**: Replace brittle exact-match assertions with behavioral checks
7. **Isolate Configuration Changes**: Ensure test-specific config changes don't leak to other tests
8. **Clean Up Dependencies**: Verify all dependency overrides are properly cleaned up
9. **Test Incrementally**: Run small test subsets to verify fixes before moving to the next group
10. **Preserve Test Intent**: Ensure fixes maintain the original testing purpose while improving robustness

## Import Updates Checklist
When refactoring introduces custom exceptions, update test imports:
```python
# Add to test file imports:
from app.core.exceptions import AuthenticationError, ValidationError, InfrastructureError
```
