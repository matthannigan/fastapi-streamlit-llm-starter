---
sidebar_label: test_api_resilience_pipeline
---

# Integration Tests: API → Resilience Orchestrator → Circuit Breaker → Retry Pipeline

  file_path: `backend/tests.new/integration/resilience/test_api_resilience_pipeline.py`

This module tests the complete user-facing resilience functionality by validating
the integration between API endpoints, resilience orchestration, circuit breaker
patterns, and retry mechanisms.

Integration Scope:
    - API endpoints (v1/text_processing/*) → AIServiceResilience orchestrator
    - Resilience orchestration → Circuit breaker state management
    - Circuit breaker → Retry pipeline → AI service calls
    - Error classification → Fallback response generation

Business Impact:
    Core resilience functionality that directly affects user experience
    during AI service outages and failures

Test Strategy:
    - Test from the outside-in through HTTP API endpoints
    - Use high-fidelity fakes (fakeredis) for infrastructure components
    - Verify observable outcomes (HTTP responses, error codes, response content)
    - Test both success and failure scenarios with circuit breaker transitions
    - Validate fallback mechanisms and graceful degradation

Critical Paths:
    - User request → Resilience orchestration → Circuit breaker → Retry → Response
    - Failure detection → Circuit breaker open → Fallback response
    - Recovery testing → Circuit breaker half-open → Service restoration
    - Concurrent requests → Circuit breaker state consistency

## TestAPIResiliencePipeline

Integration tests for the complete API → Resilience Orchestrator → Circuit Breaker → Retry Pipeline.

Seam Under Test:
    API endpoints → AIServiceResilience → EnhancedCircuitBreaker → Retry mechanisms → AI service calls

Critical Paths:
    - User request → Resilience orchestration → Success response
    - Transient failures → Retry execution → Success response
    - Circuit breaker open → Fallback response → Service degradation
    - Service recovery → Circuit breaker half-open → Closed state
    - Concurrent requests → Circuit breaker state consistency

Business Impact:
    Core user-facing resilience functionality that directly affects user experience
    during AI service outages, ensuring system reliability and graceful degradation

### setup_resilience_for_api_tests()

```python
def setup_resilience_for_api_tests(self):
```

Set up resilience system for API integration testing.

### unreliable_text_processor()

```python
def unreliable_text_processor(self, unreliable_ai_service):
```

Create a text processor service with controllable AI service.

### test_successful_request_circuit_breaker_closed()

```python
def test_successful_request_circuit_breaker_closed(self, client: TestClient, unreliable_ai_service):
```

Test that a successful request completes normally with circuit breaker remaining closed.

Integration Scope:
    API endpoint → Resilience orchestration → Circuit breaker → AI service call

Business Impact:
    Validates that normal operation works correctly without triggering resilience patterns

Test Strategy:
    - Make single successful request through API
    - Verify circuit breaker remains closed
    - Confirm response contains expected data
    - Validate no retry attempts occurred

Success Criteria:
    - HTTP 200 response with valid result
    - Circuit breaker state remains closed
    - Response contains processed text
    - No resilience metrics incremented

### test_transient_failure_retry_success()

```python
def test_transient_failure_retry_success(self, client: TestClient, unreliable_ai_service):
```

Test that transient failures trigger retries and eventually succeed.

Integration Scope:
    API endpoint → Resilience orchestration → Retry mechanism → AI service call

Business Impact:
    Validates retry functionality for temporary service issues

Test Strategy:
    - Configure service to fail twice then succeed
    - Make API request and verify retry behavior
    - Confirm final success after retries
    - Validate circuit breaker remains closed

Success Criteria:
    - HTTP 200 response after retries
    - Response contains successful result
    - Circuit breaker remains closed
    - Retry metrics incremented appropriately

### test_circuit_breaker_opens_after_failures()

```python
def test_circuit_breaker_opens_after_failures(self, client: TestClient, unreliable_ai_service):
```

Test that circuit breaker opens after repeated failures to prevent cascade failures.

Integration Scope:
    API endpoint → Resilience orchestration → Circuit breaker → Failure handling

Business Impact:
    Protects AI service from overload during outages

Test Strategy:
    - Configure service to fail permanently
    - Make multiple requests to trigger circuit breaker
    - Verify circuit breaker opens and fails fast
    - Confirm subsequent requests fail immediately

Success Criteria:
    - Circuit breaker opens after failure threshold
    - Subsequent requests fail immediately (fail-fast)
    - HTTP 503 Service Unavailable responses
    - Circuit breaker state correctly reported

### test_circuit_breaker_recovery_with_half_open()

```python
def test_circuit_breaker_recovery_with_half_open(self, client: TestClient, unreliable_ai_service):
```

Test circuit breaker recovery through half-open state testing.

Integration Scope:
    API endpoint → Circuit breaker recovery → Half-open testing → State transition

Business Impact:
    Automatic service recovery without manual intervention

Test Strategy:
    - Force circuit breaker open with failures
    - Wait for recovery timeout
    - Make request to test half-open state
    - Verify circuit breaker transitions to closed on success

Success Criteria:
    - Circuit breaker transitions from open to half-open to closed
    - Service recovery happens automatically
    - Successful request after recovery period
    - Health status reflects recovery state

### test_fallback_response_when_circuit_breaker_open()

```python
def test_fallback_response_when_circuit_breaker_open(self, client: TestClient, unreliable_ai_service):
```

Test that fallback responses are provided when circuit breaker is open.

Integration Scope:
    API endpoint → Circuit breaker → Fallback mechanism → Response generation

Business Impact:
    Graceful degradation instead of complete service failure

Test Strategy:
    - Open circuit breaker with repeated failures
    - Make request when circuit breaker is open
    - Verify fallback response is returned
    - Confirm response structure matches expected format

Success Criteria:
    - HTTP 200 response with fallback content
    - Response contains fallback text
    - Metadata indicates fallback was used
    - Circuit breaker remains open

### test_concurrent_requests_circuit_breaker_consistency()

```python
def test_concurrent_requests_circuit_breaker_consistency(self, client: TestClient, unreliable_ai_service):
```

Test circuit breaker state consistency under concurrent load.

Integration Scope:
    Multiple concurrent API requests → Circuit breaker state management → Response consistency

Business Impact:
    Ensures system stability during high load with failures

Test Strategy:
    - Start multiple concurrent requests during circuit breaker opening
    - Verify all requests handle circuit breaker state consistently
    - Confirm no race conditions or state corruption

Success Criteria:
    - All concurrent requests complete successfully
    - Circuit breaker state remains consistent
    - No exceptions or hung requests
    - Response times remain reasonable

### test_resilience_metrics_tracking()

```python
def test_resilience_metrics_tracking(self, client: TestClient, unreliable_ai_service):
```

Test that resilience metrics are properly tracked through the pipeline.

Integration Scope:
    API endpoint → Resilience orchestration → Metrics collection → Health reporting

Business Impact:
    Provides operational visibility into resilience system behavior

Test Strategy:
    - Make requests with different outcomes
    - Verify metrics are collected for each operation
    - Check health status reflects current state
    - Validate metrics structure and content

Success Criteria:
    - Metrics collected for each operation
    - Success/failure counts accurate
    - Circuit breaker state transitions tracked
    - Health status reflects current metrics

### test_different_operations_isolated_circuit_breakers()

```python
def test_different_operations_isolated_circuit_breakers(self, client: TestClient, unreliable_ai_service):
```

Test that different operations have isolated circuit breakers.

Integration Scope:
    Multiple API operations → Separate circuit breakers → Independent failure handling

Business Impact:
    Ensures failure in one operation doesn't affect others

Test Strategy:
    - Fail one operation to open its circuit breaker
    - Verify other operations continue working normally
    - Confirm circuit breaker isolation

Success Criteria:
    - Failed operation has open circuit breaker
    - Other operations maintain closed circuit breakers
    - Failed operation returns fallback/degraded responses
    - Other operations return normal responses
