# Docstring Templates and Guidance for Testing

## Philosophy of Test Documentation

Test documentation serves fundamentally different purposes than production code documentation:

**Production Code Docs**: Explain how to USE the code (see [DOCSTRINGS_CODE.md](./DOCSTRINGS_CODE.md))  
**Test Docs**: Explain WHY the test exists and WHAT it's verifying

This document works in conjunction with our production code docstring standards to create a comprehensive documentation ecosystem where rich production docstrings serve as specifications for behavior-focused test development.

### Core Principles for Test Documentation

1. **Document Intent, Not Implementation**: Explain what behavior is being verified
2. **Focus on Business Value**: Why does this test matter to users/stakeholders?
3. **Clarify Test Boundaries**: What specific scenario is being tested vs. what isn't
4. **Aid Debugging**: Help future developers understand test failures quickly
5. **Communicate Risk**: What breaks if this test starts failing?

---

## Test Docstring Template

### Unit Test Template
```python
def test_validate_api_key_rejects_invalid_format():
    """
    Test that API key validation rejects malformed keys.
    
    Verifies:
        Invalid key formats are rejected with appropriate error messages
        
    Business Impact:
        Prevents unauthorized access attempts with malformed credentials
        
    Scenario:
        Given: API key with invalid format (missing prefix, wrong length)
        When: Validation is performed
        Then: ValidationError is raised with specific format error message
        
    Edge Cases Covered:
        - Empty strings
        - Keys without 'sk-' prefix  
        - Keys with incorrect length
        - Keys with invalid characters

    Mocks Used:
        - mock_verify_api_key
        - mock_api_key_auth
        
    Related Tests:
        - test_validate_api_key_accepts_valid_format()
        - test_validate_api_key_checks_service_permissions()
    """
```

### Integration Test Template
```python
def test_resilience_service_handles_api_failures():
    """
    Test that resilience service gracefully handles external API failures.
    
    Integration Scope:
        Tests interaction between ResilienceService, CircuitBreaker, and RetryPolicy
        
    Business Impact:
        Ensures application remains responsive when external services are down
        
    Test Flow:
        1. Configure resilience service with 3 retry attempts
        2. Mock external API to fail consistently
        3. Verify circuit breaker opens after threshold failures
        4. Verify fallback response is returned
        5. Verify metrics are properly recorded
        
    External Dependencies:
        - Mocked AI service API (simulates downtime)
        - Real circuit breaker and retry components
        
    Success Criteria:
        - No exceptions propagate to caller
        - Fallback response matches expected format
        - Circuit breaker state transitions correctly
        - Retry attempts match configuration
    """
```

### API Test Template
```python
def test_process_endpoint_returns_400_for_invalid_input():
    """
    Test that /api/v1/process endpoint validates input and returns proper error codes.
    
    API Contract:
        POST /api/v1/process should return 400 for invalid request bodies
        
    Business Impact:
        Provides clear feedback to API consumers about request format errors
        
    Request Scenarios:
        - Missing required 'text' field
        - Empty text content
        - Text exceeding maximum length (50,000 characters)
        - Invalid content-type headers
        
    Expected Response:
        - Status: 400 Bad Request
        - Body: {"error": "validation_failed", "details": [...]}
        - Headers: Content-Type application/json
        
    Security Considerations:
        Error messages should not expose internal system details
    """
```

---

## Documentation Patterns by Test Type

### **Behavior Verification Tests**
Focus on documenting the specific behavior being verified:

```python
def test_user_creation_sends_welcome_email():
    """
    Verify that user creation triggers welcome email delivery.
    
    Critical Business Function:
        New users must receive onboarding communications
        
    Behavior Under Test:
        When a user account is successfully created, the system automatically
        sends a welcome email with account activation instructions
        
    Failure Impact:
        Users won't receive activation emails, blocking account setup
        
    Test Isolation:
        Uses mocked email service to avoid external dependencies
    """
```

### **Edge Case and Boundary Tests**
Explain why the edge case matters:

```python
def test_batch_processing_handles_empty_input_list():
    """
    Verify that batch processor handles empty input gracefully.
    
    Edge Case Rationale:
        Empty batches can occur during low-traffic periods or data filtering
        
    Expected Behavior:
        - Returns immediately without error
        - Produces empty results with proper metadata
        - Logs appropriate "no items to process" message
        
    Risk if Broken:
        Application could crash during legitimate empty batch scenarios
        
    Design Decision:
        Empty batches are valid and should not be treated as errors
    """
```

### **Error Handling Tests**
Document the error scenario and recovery expectations:

```python
def test_database_connection_failure_uses_cache_fallback():
    """
    Verify system resilience when primary database becomes unavailable.
    
    Failure Scenario:
        Database connection is lost during active user session
        
    Expected Recovery:
        - System detects connection failure
        - Switches to read-only cache for data retrieval
        - Logs degraded mode activation
        - Returns cached data with staleness indicators
        
    Business Continuity:
        Users can continue reading data during database outages
        
    Limitations:
        Write operations will fail until database connectivity is restored
    """
```

### **Performance and Load Tests**
Document performance expectations and thresholds:

```python
def test_api_response_time_under_load():
    """
    Verify API maintains acceptable response times under concurrent load.
    
    Performance Requirements:
        - 95th percentile response time < 500ms
        - Support 100 concurrent requests
        - No memory leaks during sustained load
        
    Load Profile:
        100 concurrent users making requests for 60 seconds
        
    Success Criteria:
        - Average response time < 200ms
        - No HTTP 5xx errors
        - Memory usage returns to baseline after test
        
    Business Impact:
        Poor performance degrades user experience and may violate SLA
        
    Infrastructure:
        Test uses local resources; production performance may vary
    """
```

### **Security Tests**
Clearly document security scenarios and expected protections:

```python
def test_authentication_prevents_sql_injection():
    """
    Verify that authentication endpoints are protected against SQL injection.
    
    Security Threat:
        Malicious users attempt SQL injection via login credentials
        
    Attack Vectors Tested:
        - Classic SQL injection in username field
        - Blind SQL injection attempts
        - Union-based injection patterns
        
    Expected Protection:
        - All malicious inputs are safely escaped/parameterized
        - No database errors are exposed to client
        - Failed attempts are logged for security monitoring
        
    Compliance Requirement:
        Required for SOC 2 Type II certification
        
    Test Limitations:
        Static injection patterns only; does not cover all possible variants
    """
```

---

## Test Class Documentation

### Test Suite Overview
```python
class TestUserAuthentication:
    """
    Test suite for user authentication and authorization workflows.
    
    Scope:
        - Login/logout functionality
        - Password validation and security
        - Session management
        - Multi-factor authentication
        - Account lockout policies
        
    Business Critical:
        Authentication failures directly impact user access and security
        
    Test Strategy:
        - Unit tests for individual validation functions
        - Integration tests for complete auth flows
        - Security tests for attack prevention
        - Performance tests for auth under load
        
    External Dependencies:
        - Mocked user database
        - Real password hashing (bcrypt)
        - Mocked email service for 2FA
        
    Known Limitations:
        - Does not test actual email delivery
        - Browser session persistence not covered
        - LDAP integration tested separately
    """
```

### Fixture Documentation
```python
@pytest.fixture
def authenticated_user():
    """
    Provides a fully authenticated user for testing protected endpoints.
    
    User Profile:
        - Standard user permissions (not admin)
        - Active account status
        - Email verified
        - No special role assignments
        
    Use Cases:
        - Testing endpoints that require authentication
        - Verifying user-specific data access
        - Testing standard user workflows
        
    Cleanup:
        User session is automatically cleaned up after test completion
        
    Related Fixtures:
        - admin_user: For testing admin-only functionality
        - unverified_user: For testing email verification flows
    """
```

---

## Anti-Patterns in Test Documentation

### ❌ DON'T Document Implementation Details
```python
def test_user_service_creates_user():
    """
    Test calls UserService.create_user() method with UserData object,
    validates the response using assertEquals, and checks the database
    using SQLAlchemy session.query() to verify user was inserted.
    """
```

### ❌ DON'T Restate What the Code Obviously Does
```python
def test_addition():
    """Test that 2 + 2 equals 4."""  # Adds no value
```

### ❌ DON'T Document Test Mechanics Instead of Purpose
```python
def test_api_endpoint():
    """
    Creates a test client, makes a POST request with JSON data,
    and asserts the response status code is 200.
    """
```

### ✅ DO Document Intent and Business Value
```python
def test_payment_processing_prevents_double_charges():
    """
    Verify that duplicate payment submissions are rejected to prevent
    accidental double-charging of customers.
    
    Business Rule:
        Identical payment requests within 5 minutes are considered duplicates
        
    Customer Protection:
        Prevents financial harm from accidental double-clicks or network retries
    """
```

---

## Special Documentation Considerations

### **Flaky Test Documentation**
```python
@pytest.mark.flaky(reruns=3)
def test_external_api_integration():
    """
    Test integration with third-party weather API.
    
    Flakiness Note:
        This test may fail due to external API rate limiting or temporary
        network issues. Automatic retry is configured.
        
    Monitoring:
        If this test fails consistently, check:
        1. External API service status
        2. Network connectivity
        3. Rate limit configuration
        
    Alternatives:
        Consider mocking this integration if flakiness becomes problematic
    """
```

### **Slow Test Documentation**
```python
@pytest.mark.slow
def test_full_data_migration():
    """
    Test complete data migration from legacy to new database schema.
    
    Duration: ~30 seconds
    
    Performance Impact:
        This test processes large datasets and may consume significant memory
        
    CI/CD Integration:
        Runs only in nightly builds, not on every commit
        
    Test Data:
        Uses production-like dataset (10,000 records) for realistic validation
    """
```

### **Platform-Specific Test Documentation**
```python
@pytest.mark.skipif(sys.platform == "win32", reason="Unix-specific file permissions")
def test_file_permission_security():
    """
    Verify that sensitive files are created with restricted permissions.
    
    Platform Requirement:
        Unix-like systems only (Linux, macOS)
        
    Security Requirement:
        Configuration files containing secrets must be readable only by owner
        
    Windows Note:
        Windows file permissions work differently; separate test exists
    """
```

---

## Integration with Coding Assistants

### Prompt for Generating Test Documentation

```
Write comprehensive documentation for the test [TEST_NAME] following our test documentation standards:

**FOCUS ON:**
1. WHY the test exists (business value, risk mitigation)
2. WHAT specific behavior is being verified
3. WHAT scenarios/edge cases are covered
4. WHAT the failure impact would be
5. HOW the test fits into the broader test strategy

**INCLUDE SECTIONS:**
- Brief description of what behavior is being tested
- Business impact or user value being protected
- Test scenario or flow (Given/When/Then if helpful)
- Edge cases or boundaries being validated
- Related tests or dependencies
- Any special considerations (performance, security, etc.)

**AVOID:**
- Describing test implementation mechanics
- Restating what the code obviously does
- Focusing on testing framework usage
- Implementation details of the system under test

**STYLE:**
- Write for future developers who need to understand test failures
- Explain context that isn't obvious from the test name
- Be concise but informative
- Focus on the "why" behind the test
```

---

## Benefits of Rich Test Documentation

### **For Development Teams:**
- **Faster Debugging**: Clear documentation helps identify why tests fail
- **Better Coverage Decisions**: Understanding test intent guides coverage improvements
- **Easier Maintenance**: Well-documented tests are easier to update during refactoring
- **Knowledge Transfer**: New team members understand testing strategy quickly

### **For Stakeholders:**
- **Risk Visibility**: Business impact documentation shows what's protected
- **Compliance**: Security and performance test documentation aids audits
- **Decision Support**: Clear test boundaries help prioritize testing investments

### **For System Reliability:**
- **Regression Prevention**: Well-documented tests are less likely to be accidentally removed
- **Quality Assurance**: Business-focused test documentation ensures meaningful coverage
- **Incident Response**: Test documentation helps diagnose production issues

---

## Related Documentation

### **Prerequisites:**
- **[DOCSTRINGS_CODE.md](./DOCSTRINGS_CODE.md)**: Production code docstring standards that serve as test specifications
- **[TESTING.md](./TESTING.md)**: Comprehensive testing philosophy and behavior-driven test development

### **Complementary Guides:**
- **[CODE_STANDARDS.md](./CODE_STANDARDS.md)**: Overall code quality standards including documentation requirements
- **[EXCEPTION_HANDLING.md](./EXCEPTION_HANDLING.md)**: Exception testing patterns that complement docstring-driven testing

By documenting not just what tests do, but why they matter and what they protect, we create a test suite that serves as both quality assurance and system documentation.