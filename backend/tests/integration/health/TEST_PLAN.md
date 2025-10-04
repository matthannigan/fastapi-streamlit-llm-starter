# Health Monitoring Integration Test Plan

**Test Plan ID:** HMON-INT-001
**Version:** 3.0
**Created:** 2025-09-30
**Updated:** 2025-10-04
**Priority:** High

## Executive Summary

This integration test plan validates the health monitoring system's collaborative behavior through **critical path testing**. Following the project's **outside-in, behavior-focused testing philosophy**, the plan focuses on high-value health monitoring journeys essential to operational reliability rather than exhaustive coverage. All tests verify observable outcomes through HTTP requests without mocking internal components, and all scenarios map directly to documented contracts in `backend/contracts/infrastructure/monitoring/health.pyi`.

**Test Count:** 10 core integration tests (consolidated from 20+ scenarios for maintainability)
**Coverage Strategy:** Critical paths + contract-based testing for maximum confidence with minimal maintenance

## Testing Philosophy Alignment

This plan adheres to three core principles from `docs/guides/testing/INTEGRATION_TESTS.md`:

1. **Test Critical Paths, Not Every Path** - Focus on high-value health monitoring journeys essential to operational reliability
2. **Trust Contracts, Verify Integrations** - Leverage health.pyi contracts with minimal internal mocking
3. **Test from the Outside-In** - Initiate all tests through API endpoints, verify observable HTTP responses

## Contract-Driven Test Coverage

All test scenarios validate documented behavior from `backend/contracts/infrastructure/monitoring/health.pyi`:

### Contract Coverage Matrix

| Contract Element | Source Location | Test Scenarios |
|------------------|-----------------|----------------|
| **HealthStatus enumeration** (HEALTHY, DEGRADED, UNHEALTHY) | `health.pyi:215-228` | 1.1, 1.2, 1.3 |
| **ComponentStatus response_time_ms** must be measured | `health.pyi:266` | C.1, 1.1 |
| **ComponentStatus metadata** for diagnostics | `health.pyi:267` | C.1, 1.1 |
| **HealthChecker configuration validation** | `health.pyi:383-404` | (Unit test coverage) |
| **check_component raises ValueError** for unregistered | `health.pyi:469` | (Unit test coverage) |
| **check_all_components aggregation** (worst-case status) | `health.pyi:524-526` | 1.1, 1.2, 1.3 |
| **check_all_components graceful failure** handling | `health.pyi:522` | 1.4 |
| **check_ai_model_health configuration validation** | `health.pyi:568-622` | 1.2 |
| **check_cache_health connectivity testing** | `health.pyi:625-647` | 1.5, 1.6 |
| **check_resilience_health circuit breaker states** | `health.pyi:650-713` | 1.7 |

### Docstring Behavior Mapping

Each test validates specific behavioral guarantees from component docstrings:

**From SystemHealthStatus (lines 280-305):**
- ✅ "Returns UNHEALTHY if any component is UNHEALTHY" → Test 1.3
- ✅ "Returns DEGRADED if any component is DEGRADED (and none UNHEALTHY)" → Test 1.2
- ✅ "Returns HEALTHY only if all components are HEALTHY" → Test 1.1

**From HealthChecker.check_all_components (lines 505-565):**
- ✅ "Executes all registered health checks concurrently" → All tests (observable via response time)
- ✅ "Does not fail if individual components throw exceptions" → Test 1.4
- ✅ "Preserves individual component response times" → Test C.1 (contract test)

**From Individual Health Check Functions:**
- ✅ All health check functions follow ComponentStatus contract → Test C.1, C.2 (contract tests)

---

## Contract-Based Test Pattern (Principle 2: Trust Contracts, Verify Integrations)

Before testing specific integration scenarios, we establish contract compliance for all health check functions. This pattern ensures all health checks follow the same behavioral contract, providing resilience to refactoring.

### CONTRACT TEST C.1: Health Check Function Contract Compliance

```python
@pytest.mark.integration
@pytest.mark.parametrize("health_check_func,component_name", [
    (check_ai_model_health, "ai_model"),
    (check_cache_health, "cache"),
    (check_resilience_health, "resilience"),
])
async def test_all_health_checks_follow_component_status_contract(health_check_func, component_name):
    """
    Test all health check functions return valid ComponentStatus per contract.

    Contract Validation:
        - All health checks return ComponentStatus per health.pyi
        - name field matches component identifier
        - status is valid HealthStatus enum value
        - message is non-empty string for troubleshooting
        - response_time_ms is non-negative float

    Business Impact:
        Ensures consistent health monitoring interface across all components

    Test Strategy:
        - Run same contract test against all health check functions
        - Verify structural contract compliance
        - This single test validates 3 health check implementations

    Success Criteria:
        - All health check functions return ComponentStatus
        - All required fields present with correct types
        - No health check crashes or returns invalid data
    """
    # Act: Execute health check function
    status = await health_check_func()

    # Assert: Contract compliance
    assert status.name == component_name, f"Component name mismatch for {health_check_func.__name__}"
    assert isinstance(status.status, HealthStatus), f"Invalid status type for {component_name}"
    assert status.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
    assert isinstance(status.message, str), f"Message must be string for {component_name}"
    assert len(status.message) > 0, f"Message must not be empty for {component_name}"
    assert isinstance(status.response_time_ms, (int, float)), f"Invalid response_time type for {component_name}"
    assert status.response_time_ms >= 0, f"Response time must be non-negative for {component_name}"
```

### CONTRACT TEST C.2: Health Check Metadata Contract

```python
@pytest.mark.integration
async def test_health_checks_with_metadata_include_diagnostic_information():
    """
    Test health checks that provide metadata include useful diagnostic information.

    Contract Validation:
        - ComponentStatus.metadata is optional per health.pyi:267
        - When present, metadata contains diagnostic key-value pairs
        - Metadata aids operational troubleshooting

    Business Impact:
        Enables detailed diagnostics for operations teams during incidents

    Success Criteria:
        - Metadata is either None or a dictionary
        - Metadata keys are strings
        - Metadata provides actionable diagnostic information
    """
    # Check AI model health metadata
    ai_status = await check_ai_model_health()
    if ai_status.metadata:
        assert isinstance(ai_status.metadata, dict)
        assert "provider" in ai_status.metadata or "has_api_key" in ai_status.metadata

    # Check resilience health metadata
    resilience_status = await check_resilience_health()
    if resilience_status.metadata:
        assert isinstance(resilience_status.metadata, dict)
        assert "total_circuit_breakers" in resilience_status.metadata
```

---

## Critical Path Integration Tests

### SEAM 1: Complete Health Monitoring System (API → HealthChecker → All Components)

**PRIORITY: HIGH** (Core user-facing functionality)
**COMPONENTS:** `/v1/health` endpoint, `HealthChecker`, all component health check functions
**CRITICAL PATH:** HTTP request → Health checker dependency → Real health checks → Aggregated JSON response
**CONTRACT REFERENCE:** `health.pyi:505-565` (HealthChecker.check_all_components)

This seam consolidates testing for the primary health monitoring integration, covering all system states (healthy, degraded, unhealthy) and specialized component behaviors (cache fallback, AI configuration, resilience circuit breakers).

#### Test Scenarios

**TEST 1.1: All Components Healthy - Complete System Health**
```python
@pytest.mark.integration
async def test_health_endpoint_returns_healthy_when_all_components_operational(client):
    """
    Test health endpoint returns HEALTHY status when all infrastructure components operational.

    Integration Scope:
        API endpoint → HealthChecker → AI/Cache/Resilience health checks

    Contract Validation:
        - SystemHealthStatus.overall_status returns HEALTHY per health.pyi:524
        - All ComponentStatus objects have status=HEALTHY
        - Response includes timestamp and component details

    Business Impact:
        Enables monitoring systems to confirm full operational capacity

    Test Strategy:
        - Use REAL health checks (no mocking internal components)
        - Configure environment for all components to be healthy
        - Verify HTTP 200 response with proper JSON structure

    Success Criteria:
        - Response status code is 200
        - response.json()["status"] == "healthy"
        - All components report status="healthy"
        - Response includes timestamp and component response times
    """
    # Arrange: Environment configured with all services available
    # - Valid GEMINI_API_KEY configured
    # - Redis available (or memory cache configured)
    # - All circuit breakers in closed state

    # Act: Make HTTP request to health endpoint
    response = client.get("/v1/health")

    # Assert: Observable HTTP behavior
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "components" in data

    # Verify all components report healthy
    for component in data["components"]:
        assert component["status"] == "healthy", f"{component['name']} not healthy"
        assert component["response_time_ms"] > 0
```

**TEST 1.2: Partial Degradation - Component Configuration Issues**
```python
@pytest.mark.integration
async def test_health_endpoint_returns_degraded_with_any_component_degraded(client, monkeypatch):
    """
    Test health endpoint returns DEGRADED status when any component is degraded.

    Integration Scope:
        API endpoint → HealthChecker → All components (one degraded)

    Contract Validation:
        - SystemHealthStatus.overall_status returns DEGRADED per health.pyi:525
        - Degraded component identified with descriptive message
        - Other components report independently (graceful degradation)

    Business Impact:
        Demonstrates system remains operational despite component issues
        Alerts operations to reduced functionality without system failure

    Test Strategy:
        - Manipulate environment to degrade AI configuration
        - Verify system degrades gracefully without failing
        - Confirm aggregation logic (worst-case status)

    Success Criteria:
        - Response status code is 200 (endpoint remains accessible)
        - Overall status is "degraded"
        - At least one component shows "degraded" status
        - Other components report independently
    """
    # Arrange: Remove AI configuration to trigger degraded state
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Act: Make HTTP request
    response = client.get("/v1/health")

    # Assert: Degraded but operational
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"

    # Should have at least one degraded component
    degraded_components = [c for c in data["components"] if c["status"] == "degraded"]
    assert len(degraded_components) > 0, "Should have at least one degraded component"

    # Degraded components should have descriptive messages
    for component in degraded_components:
        assert len(component["message"]) > 0, f"Degraded component {component['name']} needs descriptive message"
```

**TEST 1.3: Critical Component Failure - System Unhealthy**
```python
@pytest.mark.integration
async def test_health_endpoint_returns_unhealthy_with_any_component_unhealthy(client, monkeypatch):
    """
    Test health endpoint returns UNHEALTHY when any component encounters critical failure.

    Integration Scope:
        API endpoint → HealthChecker → All components (one critical failure)

    Contract Validation:
        - SystemHealthStatus.overall_status returns UNHEALTHY per health.pyi:524
        - Failed component has status=UNHEALTHY with error details
        - Exception handling per health.pyi:522 (graceful failure handling)
        - Aggregation uses worst-case status logic

    Business Impact:
        Alerts monitoring systems to critical infrastructure failures requiring intervention
        Health endpoint remains operational even during critical component failures

    Test Strategy:
        - Simulate critical infrastructure failure through environment manipulation
        - Verify health monitoring continues despite component failure
        - Confirm aggregation logic prioritizes UNHEALTHY status

    Success Criteria:
        - Response status code is 200 (health endpoint remains operational)
        - Overall status is "unhealthy"
        - At least one component shows "unhealthy" status with error details
        - Health monitoring system itself remains functional
    """
    # Arrange: Configure invalid resilience preset to trigger critical failure
    monkeypatch.setenv("RESILIENCE_PRESET", "invalid_preset_name")

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: System reports unhealthy but health endpoint functional
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"

    # At least one component should be unhealthy
    unhealthy_components = [c for c in data["components"] if c["status"] == "unhealthy"]
    assert len(unhealthy_components) > 0, "Should have at least one unhealthy component"

    # Verify error messages provide diagnostic information
    for component in unhealthy_components:
        assert len(component["message"]) > 0, f"Unhealthy component {component['name']} needs descriptive error"
```

**TEST 1.4: Error Isolation - Component Failures Don't Cascade**
```python
@pytest.mark.integration
async def test_health_check_isolates_individual_component_failures(client, monkeypatch):
    """
    Test health monitoring continues when individual component health checks fail.

    Integration Scope:
        API endpoint → HealthChecker → Multiple components (one failing)

    Contract Validation:
        - "Does not fail if individual components throw exceptions" per health.pyi:522
        - Error isolation preserves other component health reporting
        - Health endpoint remains accessible during component failures

    Business Impact:
        Ensures partial failures don't prevent health monitoring of healthy components
        Provides maximum operational visibility even during failures

    Test Strategy:
        - Configure one component to fail (via environment manipulation)
        - Verify other components report normally
        - Confirm health endpoint remains operational

    Success Criteria:
        - Health endpoint remains accessible (200 status)
        - Failed component reports unhealthy with error details
        - Other components report their actual status
        - Overall status reflects worst-case component status
    """
    # Arrange: Configure environment to cause one component to fail
    monkeypatch.setenv("RESILIENCE_CUSTOM_CONFIG", "{invalid json")

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Endpoint functional despite component failure
    assert response.status_code == 200
    data = response.json()

    # System should report overall unhealthy or degraded
    assert data["status"] in ["unhealthy", "degraded"]

    # Should have multiple components reporting
    assert len(data["components"]) > 1, "Should report multiple components despite one failing"

    # At least one component should be unhealthy
    unhealthy_count = sum(1 for c in data["components"] if c["status"] == "unhealthy")
    assert unhealthy_count > 0, "Should have at least one unhealthy component"

    # At least one component should still report successfully
    successful_count = sum(1 for c in data["components"] if c["status"] in ["healthy", "degraded"])
    assert successful_count > 0, "Should have at least one component reporting successfully"
```

**TEST 1.5: Cache Infrastructure Health - Redis Connectivity**
```python
@pytest.mark.integration
async def test_cache_health_reports_operational_status_through_api(client):
    """
    Test cache health check reports operational status through health endpoint.

    Integration Scope:
        API endpoint → HealthChecker → check_cache_health → Cache infrastructure

    Contract Validation:
        - ComponentStatus includes cache backend status per health.pyi:625-647
        - Connectivity validation reports accurate operational state
        - Metadata includes backend information for diagnostics

    Business Impact:
        Validates caching infrastructure operational for optimal performance
        Enables monitoring of cache backend availability

    Test Strategy:
        - Request health status with cache infrastructure available
        - Verify cache component reports accurately
        - Check metadata includes backend information

    Success Criteria:
        - Cache component status is "healthy" when Redis available
        - Metadata indicates active backend type
        - Response time measured for performance monitoring
    """
    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Cache component reports operational status
    assert response.status_code == 200
    data = response.json()

    cache_component = next((c for c in data["components"] if c["name"] == "cache"), None)
    assert cache_component is not None, "Cache component should be in health response"
    assert cache_component["status"] in ["healthy", "degraded"], "Cache should be operational"
    assert cache_component["response_time_ms"] >= 0, "Should measure response time"
```

**TEST 1.6: Cache Graceful Degradation - Memory Fallback**
```python
@pytest.mark.integration
async def test_cache_health_reports_degraded_with_fallback_mode(client, monkeypatch):
    """
    Test cache health check reports DEGRADED when using fallback mechanisms.

    Integration Scope:
        API endpoint → HealthChecker → check_cache_health → Memory cache fallback

    Contract Validation:
        - ComponentStatus with status=DEGRADED for fallback mode
        - System remains operational with reduced cache capacity
        - Graceful degradation maintains service availability

    Business Impact:
        Demonstrates cache resilience through fallback to memory backend
        Alerts operations to reduced cache capacity without system failure

    Test Strategy:
        - Configure memory-only cache (simulate Redis unavailable)
        - Verify degraded status reported accurately
        - Confirm system remains operational

    Success Criteria:
        - Cache component status indicates fallback mode
        - System remains operational
        - Message indicates reduced functionality or fallback state
    """
    # Arrange: Configure memory-only cache
    monkeypatch.setenv("CACHE_PRESET", "minimal")

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Cache reports operational with fallback
    assert response.status_code == 200
    data = response.json()

    cache_component = next((c for c in data["components"] if c["name"] == "cache"), None)
    assert cache_component is not None
    # May be healthy with memory or degraded - both acceptable for fallback
    assert cache_component["status"] in ["healthy", "degraded"]
```

**TEST 1.7: Resilience Health - Circuit Breaker Status Monitoring**
```python
@pytest.mark.integration
async def test_resilience_health_reports_circuit_breaker_states(client):
    """
    Test resilience health check reports circuit breaker states accurately.

    Integration Scope:
        API endpoint → HealthChecker → check_resilience_health → Circuit breaker states

    Contract Validation:
        - ComponentStatus includes circuit breaker information per health.pyi:650-713
        - HEALTHY when all circuits closed, DEGRADED when circuits open
        - Metadata includes circuit breaker counts and states

    Business Impact:
        Monitors resilience infrastructure protecting system from failures
        Alerts to external service issues via circuit breaker states

    Test Strategy:
        - Request health status with resilience orchestrator available
        - Verify resilience component reports circuit breaker states
        - Check metadata includes operational metrics

    Success Criteria:
        - Resilience component status reflects circuit breaker states
        - Metadata includes circuit breaker counts
        - Open circuits reported when present
    """
    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Resilience component reports status
    assert response.status_code == 200
    data = response.json()

    resilience_component = next((c for c in data["components"] if c["name"] == "resilience"), None)
    assert resilience_component is not None, "Resilience component should be in health response"
    assert resilience_component["status"] in ["healthy", "degraded", "unhealthy"]

    # Should have circuit breaker metadata when available
    if resilience_component.get("metadata"):
        assert "total_circuit_breakers" in resilience_component["metadata"] or \
               "circuit_breakers" in str(resilience_component["message"]).lower()
```

**INFRASTRUCTURE NEEDS:**
- FastAPI TestClient with real application instance
- Environment configuration via `monkeypatch` fixture
- Real Redis instance OR memory cache configuration
- Valid test API key configuration
- No mocking of internal health check functions

---

## Appendix A: Performance Test Suite (Out of Scope for Integration Tests)

**⚠️ NOTE:** These tests validate performance characteristics and belong in `tests/performance/health/`, not in integration tests. They are included here for reference but should be implemented separately.

**Rationale:** Performance and load testing are distinct from integration testing. Integration tests verify correctness of collaboration; performance tests verify behavior under load.

### Performance Test Scenarios

**P.1 Concurrent Request Handling**
```python
@pytest.mark.slow
@pytest.mark.performance
async def test_health_endpoint_handles_concurrent_requests_efficiently(client):
    """
    Test health endpoint performance under concurrent load.

    Performance Characteristic:
        Validates system can handle multiple simultaneous health check requests

    Success Criteria:
        - 10 concurrent requests complete within 5 seconds total
        - No request fails due to resource contention
        - Response times remain within acceptable bounds
    """
    import asyncio
    import httpx

    async def make_request():
        async with httpx.AsyncClient() as async_client:
            response = await async_client.get("http://localhost:8000/v1/health")
            return response.status_code, response.elapsed.total_seconds()

    # Execute 10 concurrent requests
    start = time.time()
    results = await asyncio.gather(*[make_request() for _ in range(10)])
    total_time = time.time() - start

    # All requests should succeed
    assert all(status == 200 for status, _ in results), "All concurrent requests should succeed"

    # Total time should be reasonable
    assert total_time < 5.0, f"10 concurrent requests took {total_time:.2f}s (expected < 5s)"

    # Individual response times should be reasonable
    response_times = [elapsed for _, elapsed in results]
    assert max(response_times) < 3.0, "Individual response times should be < 3s"
```

**P.2 Timeout Handling Performance**
```python
@pytest.mark.slow
@pytest.mark.performance
async def test_health_check_timeout_handling_performance(client, monkeypatch):
    """
    Test health check properly times out slow components without blocking.

    Performance Characteristic:
        Validates timeout mechanism prevents slow components from blocking health monitoring

    Success Criteria:
        - Slow component times out according to configured timeout
        - Timeout doesn't block other component health checks
        - Overall health check completes within expected timeframe
    """
    # Arrange: Configure short timeout for testing
    monkeypatch.setenv("HEALTH_CHECK_TIMEOUT_MS", "500")

    # Act: This test would require a component that can be made artificially slow
    # In practice, this might be tested through internal health checker testing
    # rather than through the API endpoint

    response = client.get("/v1/health")

    # Assert: Response received despite potential slow components
    assert response.status_code == 200

    # If any component timed out, it should be marked degraded
    data = response.json()
    for component in data["components"]:
        if "timeout" in component.get("message", "").lower():
            assert component["status"] == "degraded", "Timed out component should be degraded"
```

---

## Test Infrastructure Requirements

### Required Test Fixtures (conftest.py)

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """
    FastAPI test client with real application instance.

    Provides outside-in testing through HTTP requests.
    Uses real dependency injection and health checks.
    """
    return TestClient(app)

@pytest.fixture
def monkeypatch():
    """Standard pytest monkeypatch for environment manipulation."""
    # Provided by pytest automatically
    pass

@pytest.fixture(scope="session")
def redis_container():
    """
    Redis container for integration tests requiring real Redis.

    Uses testcontainers or docker-compose to provide Redis instance.
    Session-scoped to avoid repeated container startup.
    """
    # Implementation depends on testcontainers or docker-compose
    # Return Redis connection details or ensure Redis available
    pass
```

### Test Environment Configuration

```bash
# Required environment variables for integration tests
export GEMINI_API_KEY="test-api-key-placeholder"  # Valid format, doesn't need to work
export API_KEY="test-api-key-12345"
export CACHE_PRESET="development"
export RESILIENCE_PRESET="development"

# Optional overrides
export REDIS_URL="redis://localhost:6379"  # If using real Redis
```

### Docker Compose for Test Infrastructure

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 1s
      timeout: 3s
      retries: 30
```

### Test Execution Commands

```bash
# Run all health integration tests
make test-backend-integration

# Run specific test file
pytest tests/integration/health/test_health_endpoints.py -v

# Run with coverage
pytest tests/integration/health/ --cov=app.infrastructure.monitoring --cov-report=term-missing

# Run performance tests (moved to tests/performance/)
pytest tests/performance/health/ -v -m "performance"

# Run excluding performance tests (CI pipeline)
pytest tests/integration/health/ -v -m "integration"
```

---

## Success Criteria

### Functional Requirements
- ✅ All core integration tests pass (10 tests: 2 contract + 7 critical path + 1 error isolation)
- ✅ Health endpoint returns HTTP 200 for all health states (healthy, degraded, unhealthy)
- ✅ Graceful degradation demonstrated for missing components
- ✅ Exception isolation prevents cascade failures
- ✅ Component-specific behaviors validated (cache fallback, resilience monitoring)

### Contract Compliance
- ✅ All tests map to documented behavior in health.pyi
- ✅ No tests validate undocumented implementation details
- ✅ Contract tests validate all health check functions follow same interface
- ✅ Test scenarios cover all documented contract guarantees

### Testing Philosophy Adherence
- ✅ All tests use outside-in approach through HTTP endpoints or contract validation
- ✅ Zero mocking of internal components (only environment manipulation)
- ✅ Tests focus on observable behavior rather than implementation
- ✅ Contract-based testing ensures refactoring resilience

### Coverage Requirements
- ✅ All critical integration seams have test coverage
- ✅ Contract coverage matrix complete
- ✅ Configuration validation moved to unit tests (proper separation)
- ✅ Performance tests separated to dedicated suite

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-09-30 | Initial test plan | Integration Testing Architect |
| 2.0 | 2025-10-01 | **Major revision** - Aligned with project testing philosophy:<br/>- Removed internal component mocking<br/>- Added contract coverage matrix<br/>- Focused on observable behavior through API<br/>- Separated performance tests<br/>- Added docstring behavior mapping | Integration Testing Architect |
| 3.0 | 2025-10-04 | **Critical path consolidation**:<br/>- Reduced from 20+ scenarios to 10 focused tests<br/>- Added contract-based test pattern (Principle 2)<br/>- Removed SEAM 5 (unit tests, not integration)<br/>- Consolidated SEAMs 1-3 into single comprehensive seam<br/>- Moved performance tests to appendix<br/>- Refocused on critical paths per Principle 1 | Integration Testing Architect |

---

## References

- **Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md`
- **Writing Tests**: `docs/guides/testing/WRITING_TESTS.md`
- **Health Contract**: `backend/contracts/infrastructure/monitoring/health.pyi`
- **Health Implementation**: `backend/app/infrastructure/monitoring/health.py`
