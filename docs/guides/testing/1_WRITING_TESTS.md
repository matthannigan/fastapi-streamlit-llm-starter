# Writing Tests

## Docstring-Driven Test Development

This project promotes **docstring-driven test development**, where comprehensive function and class docstrings serve as specifications for generating focused, behavior-based tests. This approach creates tests that verify what functions *should do* rather than how they *currently work*.

> **📖 Comprehensive Docstring Guidance**: See **[DOCSTRINGS_CODE.md](./DOCSTRINGS_CODE.md)** for production code docstring standards and **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)** for test documentation templates and philosophy.

### Core Principles

1. **TEST WHAT'S DOCUMENTED**: Only test behaviors, inputs, outputs, and exceptions mentioned in docstrings
2. **IGNORE IMPLEMENTATION**: Don't test internal methods, private attributes, or undocumented behavior  
3. **FOCUS ON CONTRACTS**: Test that the function fulfills its documented contract
4. **USE DOCSTRING EXAMPLES**: Convert docstring examples into actual test cases
5. **TEST EDGE CASES FROM DOCS**: If docstring mentions limits (1-50,000 characters), test the boundaries
6. **DON'T OVER-TEST**: If it's not in the docstring, it's probably not worth testing

### Converting Docstrings to Tests

#### Input Contract Testing
**Rich Docstring:**
```python
def validate_config(config: dict) -> ValidationResult:
    """
    Validates AI service configuration.
    
    Args:
        config: Configuration dictionary with required keys:
               - 'model': str, one of ['gpt-4', 'claude', 'gemini']
               - 'timeout': int, 1-300 seconds
               - 'retries': int, 0-10 attempts
               Optional keys:
               - 'fallback_model': str, same options as 'model'
    
    Returns:
        ValidationResult containing:
        - is_valid: bool, True if config passes validation
        - errors: List[str], validation error messages if any
        
    Raises:
        TypeError: If config is not a dictionary
        
    Behavior:
        - Validates all required fields are present
        - Checks field value constraints and types
        - Returns detailed error messages for debugging
        - Accepts None values for optional fields
    """
```

**Generated Tests:**
```python
class TestValidateConfig:
    """Test config validation per docstring specification."""
    
    def test_validate_config_required_fields(self):
        """Test validation requires all mandatory fields per docstring."""
        minimal_config = {
            'model': 'gpt-4',
            'timeout': 30,
            'retries': 3
        }
        result = validate_config(minimal_config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_config_invalid_model(self):
        """Test validation rejects invalid model names per docstring."""
        config = {'model': 'invalid-model', 'timeout': 30, 'retries': 3}
        result = validate_config(config)
        assert not result.is_valid
        assert any('model' in error for error in result.errors)
        
    def test_validate_config_timeout_boundaries(self):
        """Test timeout boundary conditions per docstring (1-300 seconds)."""
        # Test lower boundary
        config = {'model': 'gpt-4', 'timeout': 1, 'retries': 3}
        result = validate_config(config)
        assert result.is_valid
        
        # Test upper boundary  
        config = {'model': 'gpt-4', 'timeout': 300, 'retries': 3}
        result = validate_config(config)
        assert result.is_valid
        
        # Test invalid boundaries
        config = {'model': 'gpt-4', 'timeout': 0, 'retries': 3}
        result = validate_config(config)
        assert not result.is_valid
        
    def test_validate_config_type_error(self):
        """Test TypeError raised for non-dict input per docstring."""
        with pytest.raises(TypeError):
            validate_config("not a dict")
```

#### Behavior Contract Testing
**Rich Docstring:**
```python
async def with_retry(operation: Callable, strategy: RetryStrategy) -> Any:
    """
    Executes operation with retry logic according to strategy.
    
    Args:
        operation: Async callable to execute
        strategy: RetryStrategy with max_attempts and delay_seconds
        
    Returns:
        Result of successful operation execution
        
    Raises:
        Original exception if all retry attempts fail
        
    Behavior:
        - Attempts operation according to strategy.max_attempts
        - Waits strategy.delay_seconds between attempts  
        - Raises original exception if all attempts fail
        - Returns immediately on first success
        - Logs each retry attempt for monitoring
    """
```

**Generated Tests:**
```python
class TestWithRetry:
    """Test retry behavior per docstring specification."""
    
    @pytest.mark.asyncio
    async def test_with_retry_succeeds_immediately(self):
        """Test retry returns immediately on first success per docstring."""
        success_operation = AsyncMock(return_value="success")
        strategy = RetryStrategy(max_attempts=3, delay_seconds=1)
        
        result = await with_retry(success_operation, strategy)
        
        assert result == "success"
        success_operation.assert_called_once()  # No retries needed
        
    @pytest.mark.asyncio  
    async def test_with_retry_exhausts_attempts(self):
        """Test retry raises original exception after max attempts per docstring."""
        failing_operation = AsyncMock(side_effect=ValueError("test error"))
        strategy = RetryStrategy(max_attempts=2, delay_seconds=0.1)
        
        with pytest.raises(ValueError, match="test error"):
            await with_retry(failing_operation, strategy)
            
        assert failing_operation.call_count == 2  # Max attempts reached
        
    @pytest.mark.asyncio
    async def test_with_retry_respects_delay(self):
        """Test retry waits delay_seconds between attempts per docstring."""
        attempt_times = []
        
        def record_time():
            attempt_times.append(time.time())
            if len(attempt_times) < 2:
                raise ValueError("fail first time")
            return "success"
            
        operation = AsyncMock(side_effect=record_time)
        strategy = RetryStrategy(max_attempts=3, delay_seconds=0.5)
        
        result = await with_retry(operation, strategy)
        
        assert result == "success"
        assert len(attempt_times) == 2
        delay_actual = attempt_times[1] - attempt_times[0]
        assert 0.4 <= delay_actual <= 0.6  # Allow some timing variance
```

#### Return Contract Testing
**Rich Docstring:**
```python
def process_batch(items: List[str]) -> BatchResult:
    """
    Processes a batch of text items.
    
    Returns:
        BatchResult with:
        - success_count: int, number of successfully processed items
        - failed_items: List[str], items that failed processing  
        - results: List[ProcessedItem], successful results in order
        - total_time: float, processing time in seconds
        
        Guarantees:
        - success_count + len(failed_items) == len(input items)
        - results list contains only successful items
        - failed_items preserves original input strings
    """
```

**Generated Tests:**
```python
def test_process_batch_counts_match(self):
    """Test batch result counts match input per docstring guarantee."""
    items = ["valid1", "invalid", "valid2"]  
    result = process_batch(items)
    
    # Test docstring guarantee
    assert result.success_count + len(result.failed_items) == len(items)
    assert len(result.results) == result.success_count
    
def test_process_batch_preserves_failed_items(self):
    """Test failed items preserve original strings per docstring."""
    items = ["valid", "invalid_item", "valid"]
    result = process_batch(items)
    
    # Failed items should contain original strings
    for failed_item in result.failed_items:
        assert failed_item in items
```

### Recommended Test Generation Workflow

To ensure all new tests adhere to our behavior-driven philosophy, we follow a systematic, 5-step process, often guided by a coding assistant. This workflow enforces our principles and produces a robust, maintainable test suite.

- **Step 1: Context Alignment (The "Why")**: The process begins by aligning with the project's core testing philosophies, principles, and anti-patterns. This ensures the "why" is understood before any code is written.
- **Step 2: Fixture Generation (The "Tools")**: Fixtures are generated for any dependencies *outside* the component under test. This step prioritizes fakes over mocks and strictly forbids mocking internal collaborators.
- **Step 3: Test Planning (The "Blueprint")**: Before implementation, a complete test plan is generated as a series of empty test methods with comprehensive docstrings. This plan is designed by analyzing *only* the component's public contract (`.pyi` file), ensuring a "black box" design.
- **Step 4: Test Implementation (The "Build")**: The test skeletons from the planning phase are implemented. The guiding rule is to test only observable outcomes and public contracts, ensuring tests are resilient to refactoring.
- **Step 5: Code Review & Verification (The "Quality Check")**: A final quality check is performed, comparing the generated tests against the project's principles and anti-patterns to refactor any tests that are still coupled to implementation details.

## Traditional Test Examples with Rich Documentation

### Backend Test Example
```python
class TestNewFeature:
    """
    Test suite for new feature functionality.
    
    Scope:
        - API endpoint behavior and response validation
        - Service method integration and error handling
        - Business logic verification for feature workflows
        
    Business Critical:
        Feature failures directly impact user workflows and system reliability
        
    Test Strategy:
        - Unit tests for individual service methods
        - Integration tests for API endpoint contracts
        - Error scenario coverage for resilience validation
    """
    
    def test_new_endpoint(self, client: TestClient):
        """
        Test that new API endpoint returns expected response structure.
        
        API Contract:
            GET /new-endpoint should return 200 with required fields
            
        Business Impact:
            Provides core functionality access to frontend clients
            
        Success Criteria:
            - Status code 200 indicates successful processing
            - Response contains expected_field for client usage
            - Response format matches API specification
        """
        response = client.get("/new-endpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert "expected_field" in data
    
    async def test_new_service_method(self, service):
        """
        Test that service method processes input and returns valid result.
        
        Behavior Under Test:
            Service method transforms test input into structured response
            
        Business Impact:
            Core processing logic that affects user data handling
            
        Success Criteria:
            - Processing completes successfully (success=True)
            - Result contains processed data for downstream usage
            - No exceptions during normal operation
        """
        result = await service.new_method("test_input")
        assert result.success is True
        assert result.data is not None
```

### Frontend Test Example
```python
class TestNewComponent:
    """
    Test suite for new frontend API client component.
    
    Integration Scope:
        Tests API client communication patterns and error handling
        
    External Dependencies:
        - Mocked HTTP client for deterministic testing
        - Real async patterns for realistic behavior validation
    """
    
    async def test_new_api_method(self, api_client):
        """
        Test that API client method handles successful responses correctly.
        
        Integration Behavior:
            API client makes HTTP request and processes JSON response
            
        Business Impact:
            Ensures frontend can successfully communicate with backend services
            
        Test Isolation:
            Uses mocked HTTP client to avoid external dependencies
            
        Success Criteria:
            - HTTP request is made with correct parameters
            - JSON response is parsed and returned to caller
            - Result format matches expected client interface
        """
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.new_method()
            assert result["result"] == "success"
```

> **📖 Test Documentation Templates**: See **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)** for comprehensive test docstring templates including unit tests, integration tests, API tests, security tests, and performance tests.

## Test Generation Guidelines

### Systematic Docstring-to-Test Mapping
- **Args section** → Input validation tests and boundary conditions
- **Returns section** → Return value structure and content verification  
- **Raises section** → Exception condition tests
- **Behavior section** → Observable outcome tests for each documented behavior
- **Examples section** → Convert to executable test cases

### Test Documentation Standards

When writing test docstrings, focus on **WHY** the test exists rather than **HOW** it works:

**Essential Elements for Test Documentation:**
- **Behavior Being Verified**: What specific functionality is being tested
- **Business Impact**: Why this test matters to users/stakeholders  
- **Test Scenario**: Given/When/Then or specific conditions being tested
- **Success Criteria**: What constitutes a passing test
- **Failure Impact**: What breaks if this test starts failing

**Quick Example:**
```python
def test_api_returns_400_for_missing_required_field(self, client):
    """
    Test that API validates required fields and returns proper error codes.
    
    Business Impact:
        Provides clear feedback to API consumers about request format errors
        
    Test Scenario:
        When required 'text' field is missing from request body
        
    Success Criteria:
        - Returns 400 status code for validation errors
        - Error response includes field-specific validation message
    """
```

### Test Structure Best Practices
- **Use descriptive test names** that reflect documented behavior
- **Group related tests in test classes** organized by function/class under test
- **Include both positive and negative test cases** based on docstring specifications
- **Use appropriate fixtures and mocking** for external dependencies
- **Focus on testing contracts, not implementation details**
- **Document test intent clearly** using the standards from DOCSTRINGS_TESTS.md

### Property-Based Testing for Edge Cases

Instead of writing dozens of individual edge case tests, use property-based testing to generate comprehensive test scenarios:

```python
from hypothesis import given, strategies as st

@given(
    text=st.text(min_size=1, max_size=10000),
    operation=st.sampled_from(["summarize", "analyze", "extract"])
)
def test_text_processing_handles_any_valid_input(text, operation, client):
    """Test that all valid inputs are handled gracefully."""
    response = client.post("/v1/text_processing/process",
                          json={"text": text, "operation": operation})
    
    # Should never crash, always return structured response
    assert response.status_code in [200, 400, 422]
    assert "error" in response.json() or "result" in response.json()

@given(
    config_dict=st.dictionaries(
        keys=st.sampled_from(['model', 'timeout', 'retries']),
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.integers(min_value=1, max_value=1000),
            st.none()
        )
    )
)
def test_config_validation_handles_any_input(config_dict):
    """Test that configuration validation never crashes."""
    result = validate_config(config_dict)
    
    # Should always return ValidationResult, never crash
    assert hasattr(result, 'is_valid')
    assert hasattr(result, 'errors')
    assert isinstance(result.errors, list)
```

### Refactoring Tests: From Brittle to Maintainable

**Before (Brittle, Implementation-Focused):**
```python
def test_text_processor_with_retry_and_circuit_breaker(
    text_processor, mock_ai_agent, mock_retry_policy, mock_circuit_breaker
):
    """Test that text processor uses retry and circuit breaker correctly."""
    mock_ai_agent.run.side_effect = [Exception(), Exception(), "Success"]
    mock_retry_policy.should_retry.side_effect = [True, True, False]
    mock_circuit_breaker.call.return_value = "Success"
    
    result = text_processor.process("test")
    
    # Tests internal implementation details
    assert mock_retry_policy.should_retry.call_count == 3
    assert mock_circuit_breaker.call.call_count == 1
    assert mock_ai_agent.run.call_count == 3
    assert result == "Success"
```

**Problems with the above:**
- Tests internal method calls, not behavior
- Breaks when refactoring resilience implementation
- Doesn't verify user-observable outcomes
- Complex mocking setup obscures test intent

**After (Maintainable, Behavior-Focused):**
```python
def test_text_processing_recovers_from_transient_failures(client):
    """Test that text processing recovers from transient failures."""
    # Setup: Configure test to simulate transient failure
    with patch('app.services.ai_provider.call') as mock_ai:
        mock_ai.side_effect = [
            Exception("Temporary service failure"), 
            "Successfully processed text"
        ]
        
        response = client.post("/v1/text_processing/process",
                              json={"text": "test input", "operation": "summarize"})
        
        # Assert on user-visible behavior
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "processed text" in response.json()["result"].lower()
```

**Benefits of the refactored test:**
- Tests user-observable behavior (API response)
- Survives internal implementation changes
- Clear test intent and failure messages
- Minimal mocking at system boundary only

### What to Test vs. What to Avoid

**✅ Test These (From Docstrings):**
- **Input validation** and boundary conditions mentioned in Args
- **Return value structure** and guarantees specified in Returns
- **Exception conditions** listed in Raises section  
- **Observable behaviors** documented in Behavior section
- **Usage patterns** shown in Examples section

**❌ Avoid Testing These:**
- **Internal implementation details** not mentioned in docstring
- **Private methods** or undocumented attributes
- **Specific algorithms** or data structures used internally
- **Framework integration details** (covered by framework tests)
- **Trivial functions** without documented behavior contracts

## Behavior-Focused Testing Guidance

### Benefits of Behavior-Focused Testing

1. **Refactoring Safety**: Tests continue passing when you improve implementation
2. **Real Confidence**: Tests verify that features actually work for users
3. **Living Documentation**: Tests describe what the system should do
4. **Faster Development**: Less test maintenance during development
5. **Better API Design**: Forces you to think about external contracts

### Applying Behavior Focus to Common Scenarios

#### Testing API Endpoints

```python
# ✅ GOOD: Tests API contract behavior
def test_process_text_endpoint_returns_success(client):
    """Test that text processing endpoint returns expected response structure."""
    response = client.post("/api/v1/process", json={
        "text": "Sample text to process",
        "operation": "summarize"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "processing_time" in data
    assert len(data["result"]) > 0

# ❌ BAD: Tests internal implementation
def test_process_text_endpoint_calls_text_processor_service(client):
    """Test that endpoint calls TextProcessorService internally."""
    with patch('app.api.v1.text_processing.text_processor_service') as mock:
        client.post("/api/v1/process", json={"text": "test", "operation": "summarize"})
        mock.process.assert_called_once()
```

#### Testing Service Classes

```python
# ✅ GOOD: Tests service behavior and state changes
async def test_cache_service_stores_and_retrieves_data():
    """Test that cache service properly stores and retrieves data."""
    cache = CacheService()
    
    await cache.set("test_key", "test_value")
    result = await cache.get("test_key")
    
    assert result == "test_value"

# ✅ GOOD: Tests error handling behavior  
async def test_cache_service_handles_missing_keys():
    """Test that cache service returns None for missing keys."""
    cache = CacheService()
    
    result = await cache.get("nonexistent_key")
    
    assert result is None

# ❌ BAD: Tests internal Redis client usage
async def test_cache_service_uses_redis_client_correctly():
    """Test that cache service calls Redis client methods."""
    with patch('redis.asyncio.Redis') as mock_redis:
        cache = CacheService()
        await cache.set("key", "value")
        
        mock_redis.return_value.set.assert_called_once_with("key", "value")
```

#### Testing Resilience Patterns

```python  
# ✅ GOOD: Tests resilience behavior outcomes
async def test_circuit_breaker_fails_fast_when_open():
    """Test that circuit breaker fails immediately when open."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
    
    # Force circuit breaker to open state
    for _ in range(3):
        try:
            await breaker.call(lambda: exec('raise Exception("service down")'))
        except:
            pass
    
    # Should fail immediately without calling function
    start_time = time.time()
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(lambda: "should not be called")
    
    # Verify it failed fast (under 100ms)
    assert time.time() - start_time < 0.1

# ❌ BAD: Tests internal state management
def test_circuit_breaker_updates_failure_count_correctly():
    """Test that circuit breaker increments internal failure counter."""
    breaker = CircuitBreaker(failure_threshold=2)
    
    try:
        breaker.call(lambda: exec('raise Exception("fail")'))
    except:
        pass
        
    # Tests private internal state
    assert breaker._failure_count == 1
```

### Transitioning to Behavior-Focused Tests

1. **Start with docstrings**: Write comprehensive behavior documentation first
2. **Test public interfaces**: Focus on public methods and API endpoints
3. **Think like a user**: What would external users expect this code to do?
4. **Test outcomes, not steps**: Verify results, not the process to get there
5. **Mock external dependencies only**: Don't mock your own internal code

## Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*` (typically `TestFunctionName` or `TestClassName`)
- Test methods: `test_*` with descriptive names explaining the documented behavior being tested
- Use names like: `test_function_validates_input_per_docstring()` or `test_service_handles_timeout_behavior()`

### Test Class Documentation

Test classes should include comprehensive docstrings that provide context about the entire test suite:

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

This provides essential context for understanding test failures and maintaining the test suite over time.

## Test Organization

- **Group related tests in classes** organized around the component being tested
- **Use fixtures for common setup** but ensure tests remain focused on documented contracts
- **Keep tests focused and independent** - each test should verify one aspect of the documented contract
- **Test both success and failure scenarios** as documented in the function's specification
- **Organize tests to mirror docstring structure** (Args tests, Returns tests, Behavior tests, etc.)
