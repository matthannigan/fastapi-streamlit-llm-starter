# Integration Testing

## Prompt 5: Implement Priority Integration Tests from Test Plan

Use as many as [#] parallel @agent-integration-test-implementer sub-agents to implement [P#] integration tests for the component defined by the public contract at `[LOCATION_OF_PUBLIC_CONTRACT.pyi]` following our integration testing philosophy as documented in `docs/guides/testing/INTEGRATION_TESTS.md` and the validated test plan as documented in `[LOCATION_OF_TEST_PLAN_FINAL.md]`.

Assign each agent a specific seam to implement and ask them to save their output to a new Python file in `[DIRECTORY_OF_INTEGRATION_TESTS]`

Each agent must follow this implementation approach:

**IMPLEMENTATION PRINCIPLES:**
1. TEST FROM THE OUTSIDE-IN: Start from API endpoints or entry points
2. USE HIGH-FIDELITY FAKES: Prefer fakeredis, test containers over mocks
3. TEST BEHAVIOR, NOT IMPLEMENTATION: Verify observable outcomes
4. MAINTAIN TEST ISOLATION: Each test should be independent
5. DOCUMENT INTEGRATION SCOPE: Clear docstrings about what's being tested

**TEST STRUCTURE TEMPLATE:**
```python
class Test[IntegrationName]:
    """
    Integration tests for [describe the integration].
    
    Seam Under Test:
        [Component A] → [Component B] → [Component C]
        
    Critical Paths:
        - [Path 1]: [Description]
        - [Path 2]: [Description]
    """
    
    def test_[scenario]_[expected_outcome](self, [fixtures]):
        """
        Test [specific behavior] across [components].
        
        Integration Scope:
            [List components being integrated]
            
        Business Impact:
            [Why this integration matters]
            
        Test Strategy:
            - [Step 1]
            - [Step 2]
            - [Verification]
            
        Success Criteria:
            - [Observable outcome 1]
            - [Observable outcome 2]
        """
        # Arrange
        [setup test data and state]
        
        # Act
        [trigger the integration through entry point]
        
        # Assert
        [verify observable outcomes]
```

**FIXTURE REQUIREMENTS:**
- Use shared fixtures from conftest.py where available
- Create integration-specific fixtures for complex setups
- Prefer function-scoped fixtures for test isolation
- Use session-scoped fixtures only for expensive resources (test containers)

**COMMON PATTERNS TO USE:**

1. **API to Database Flow:**
```python
def test_api_persists_to_database(client, test_db):
    response = client.post("/endpoint", json=data)
    assert response.status_code == 200
    
    # Verify database state
    record = test_db.query(Model).filter_by(id=response.json()["id"]).first()
    assert record is not None
```

2. **Service Integration with Cache:**
```python
def test_service_uses_cache(service, fake_redis_cache):
    # First call - cache miss
    result1 = service.process("key")
    
    # Second call - cache hit
    result2 = service.process("key")
    
    # Verify same result (from cache)
    assert result1 == result2
    assert fake_redis_cache.get("key") is not None
```

3. **Resilience Pattern Integration:**
```python
def test_circuit_breaker_protects_service(service, unreliable_backend):
    # Trigger failures to open circuit
    for _ in range(threshold):
        unreliable_backend.fail_next_request()
        with pytest.raises(ServiceError):
            service.call_backend()
    
    # Circuit should be open
    with pytest.raises(CircuitOpenError):
        service.call_backend()
```

**AVOID:**
- Mocking internal component methods
- Testing implementation details
- Asserting on internal state
- Creating overly complex test setups
- Writing tests that depend on test execution order

Generate comprehensive integration tests that validate the critical paths identified in the test plan.
