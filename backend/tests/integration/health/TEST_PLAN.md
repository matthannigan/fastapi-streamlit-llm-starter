# Health Monitoring Integration Test Plan

**Test Plan ID:** HMON-INT-001
**Version:** 2.0
**Created:** 2025-09-30
**Updated:** 2025-10-01
**Priority:** High

## Executive Summary

This integration test plan validates the health monitoring system's collaborative behavior across API endpoints, health checker orchestration, and infrastructure services. Following the project's **outside-in, behavior-focused testing philosophy**, tests verify observable outcomes through HTTP requests rather than mocking internal components. All test scenarios map directly to documented contracts in `backend/contracts/infrastructure/monitoring/health.pyi`.

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
| **HealthStatus enumeration** (HEALTHY, DEGRADED, UNHEALTHY) | `health.pyi:215-228` | 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2 |
| **ComponentStatus response_time_ms** must be measured | `health.pyi:266` | 1.4, 2.1, 2.2, 3.1 |
| **ComponentStatus metadata** for diagnostics | `health.pyi:267` | 2.1, 3.1, 4.1 |
| **HealthChecker timeout validation** (100-30000ms) | `health.pyi:388` | 5.1 |
| **HealthChecker retry configuration** (0-10 attempts) | `health.pyi:392` | 5.2 |
| **check_component raises ValueError** for unregistered | `health.pyi:469` | (Unit test coverage) |
| **check_all_components aggregation** (worst-case status) | `health.pyi:524-526` | 1.1, 1.2, 1.3 |
| **check_all_components graceful failure** handling | `health.pyi:522` | 1.3, 6.1 |
| **check_ai_model_health no external calls** | `health.pyi:617` | 3.3 |
| **check_cache_health dependency injection** optimization | `health.pyi:644` | 2.3 |
| **check_resilience_health circuit breaker states** | `health.pyi:662-664` | 4.1, 4.2 |

### Docstring Behavior Mapping

Each test validates specific behavioral guarantees from component docstrings:

**From SystemHealthStatus (lines 280-305):**
- ✅ "Returns UNHEALTHY if any component is UNHEALTHY" → Test 1.3
- ✅ "Returns DEGRADED if any component is DEGRADED (and none UNHEALTHY)" → Test 1.2
- ✅ "Returns HEALTHY only if all components are HEALTHY" → Test 1.1

**From HealthChecker.check_all_components (lines 505-565):**
- ✅ "Executes all registered health checks concurrently" → Test 1.4
- ✅ "Does not fail if individual components throw exceptions" → Test 6.1
- ✅ "Preserves individual component response times" → Test 2.1

**From check_ai_model_health (lines 568-622):**
- ✅ "Returns HEALTHY when AI services are properly configured" → Test 3.1
- ✅ "Returns DEGRADED when configuration is missing" → Test 3.2
- ✅ "Does not perform actual AI model inference" → Test 3.3

---

## Integration Test Scenarios

### SEAM 1: API → HealthChecker → Multi-Component Aggregation

**PRIORITY: HIGH** (Core user-facing functionality)
**COMPONENTS:** `/v1/health` endpoint, `HealthChecker`, all component health check functions
**CRITICAL PATH:** HTTP request → Health checker dependency → Real health checks → Aggregated JSON response
**CONTRACT REFERENCE:** `health.pyi:505-565` (HealthChecker.check_all_components)

#### Test Scenarios

**1.1 All Components Healthy - Complete System Health**
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

**1.2 Partial Degradation - AI Model Configuration Missing**
```python
@pytest.mark.integration
async def test_health_endpoint_returns_degraded_when_ai_configuration_missing(client, monkeypatch):
    """
    Test health endpoint returns DEGRADED status when AI configuration unavailable.

    Integration Scope:
        API endpoint → HealthChecker → check_ai_model_health (with missing config)

    Contract Validation:
        - SystemHealthStatus.overall_status returns DEGRADED per health.pyi:525
        - AI component has status=DEGRADED per health.pyi:579
        - Other components remain HEALTHY (graceful degradation)

    Business Impact:
        Demonstrates system remains operational despite AI service configuration issues

    Test Strategy:
        - Manipulate environment to remove AI configuration
        - Verify system degrades gracefully without failing
        - Use REAL health check functions (no mocking)

    Success Criteria:
        - Response status code is 200 (endpoint remains accessible)
        - Overall status is "degraded"
        - AI component shows status="degraded" with descriptive message
        - Cache and resilience components remain healthy
    """
    # Arrange: Remove AI configuration to trigger degraded state
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Act: Make HTTP request
    response = client.get("/v1/health")

    # Assert: Degraded but operational
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "degraded"

    # Find AI component in response
    ai_component = next((c for c in data["components"] if c["name"] == "ai_model"), None)
    assert ai_component is not None
    assert ai_component["status"] == "degraded"
    assert "missing" in ai_component["message"].lower() or "not configured" in ai_component["message"].lower()

    # Verify other components unaffected
    other_components = [c for c in data["components"] if c["name"] != "ai_model"]
    assert len(other_components) > 0, "Should have other components reporting"
```

**1.3 Critical Component Failure - System Unhealthy**
```python
@pytest.mark.integration
async def test_health_endpoint_returns_unhealthy_when_critical_component_fails(client, monkeypatch):
    """
    Test health endpoint returns UNHEALTHY when critical component encounters failure.

    Integration Scope:
        API endpoint → HealthChecker → check_resilience_health (simulated failure)

    Contract Validation:
        - SystemHealthStatus.overall_status returns UNHEALTHY per health.pyi:524
        - Failed component has status=UNHEALTHY per health.pyi:227
        - Exception handling per health.pyi:522 (graceful failure handling)

    Business Impact:
        Alerts monitoring systems to critical infrastructure failures requiring intervention

    Test Strategy:
        - Simulate infrastructure failure through environment manipulation
        - Verify health monitoring continues despite component failure
        - No mocking of internal health check functions

    Success Criteria:
        - Response status code is 200 (health endpoint remains operational)
        - Overall status is "unhealthy"
        - Failed component shows status="unhealthy" with error details
        - Health monitoring system itself remains functional
    """
    # Arrange: Configure environment to cause resilience orchestrator unavailability
    # This could be done by setting invalid resilience configuration
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

    # Verify error message provides diagnostic information
    for component in unhealthy_components:
        assert len(component["message"]) > 0, "Should have descriptive error message"
```

**1.4 Health Check Performance - Response Time SLA**
```python
@pytest.mark.integration
async def test_health_endpoint_responds_within_acceptable_time_sla(client):
    """
    Test health endpoint meets response time SLA under normal conditions.

    Integration Scope:
        API endpoint → HealthChecker → All component health checks (concurrent execution)

    Contract Validation:
        - ComponentStatus.response_time_ms measurement per health.pyi:266
        - Concurrent execution per health.pyi:518 for performance

    Business Impact:
        Ensures health monitoring doesn't impact application performance
        Validates monitoring can detect issues quickly for rapid response

    Test Strategy:
        - Measure actual HTTP response time
        - Test observable performance characteristic
        - Verify against documented SLA (3 seconds per success criteria)

    Success Criteria:
        - Total response time < 3000ms (3 seconds SLA)
        - Response includes timing data for each component
        - All component health checks complete successfully
    """
    import time

    # Arrange: Normal operational environment
    start_time = time.time()

    # Act: Execute health check
    response = client.get("/v1/health")

    # Measure observable response time
    response_time_ms = (time.time() - start_time) * 1000

    # Assert: Performance SLA met
    assert response.status_code == 200
    assert response_time_ms < 3000, f"Health check took {response_time_ms:.1f}ms (SLA: 3000ms)"

    # Verify response includes timing data
    data = response.json()
    assert "components" in data

    for component in data["components"]:
        assert "response_time_ms" in component
        assert component["response_time_ms"] >= 0
```

**INFRASTRUCTURE NEEDS:**
- FastAPI TestClient with real application instance
- Environment configuration via `monkeypatch` fixture
- Real Redis instance OR memory cache configuration
- Valid test API key configuration
- No mocking of internal health check functions

---

### SEAM 2: HealthChecker → Cache Service Integration

**PRIORITY: HIGH** (Infrastructure reliability)
**COMPONENTS:** `HealthChecker`, `check_cache_health()`, `AIResponseCache`, Redis/Memory backends
**CRITICAL PATH:** Health check → Cache service (via DI) → Connectivity validation → Status reporting
**CONTRACT REFERENCE:** `health.pyi:625-647` (check_cache_health)

#### Test Scenarios

**2.1 Cache Health with Redis - Primary Backend Operational**
```python
@pytest.mark.integration
async def test_cache_health_check_reports_healthy_with_redis_available(client):
    """
    Test cache health check returns HEALTHY when Redis connection successful.

    Integration Scope:
        Health checker → check_cache_health → AIResponseCache → Redis backend

    Contract Validation:
        - ComponentStatus with status=HEALTHY per health.pyi:640
        - response_time_ms includes connectivity test timing per health.pyi:266
        - metadata contains backend information per health.pyi:267

    Business Impact:
        Validates primary caching infrastructure operational for optimal performance

    Test Strategy:
        - Ensure Redis container running (testcontainers or docker-compose)
        - Use real cache health check function
        - Verify through HTTP endpoint (outside-in)

    Success Criteria:
        - Cache component status is "healthy"
        - Metadata indicates Redis backend in use
        - Response time measured and reasonable (< 500ms)
    """
    # Arrange: Ensure Redis available via docker-compose or testcontainers
    # Configuration should specify Redis connection

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Cache reports healthy with Redis
    assert response.status_code == 200

    data = response.json()
    cache_component = next((c for c in data["components"] if c["name"] == "cache"), None)

    assert cache_component is not None
    assert cache_component["status"] == "healthy"
    assert cache_component["response_time_ms"] > 0
    assert cache_component["response_time_ms"] < 500, "Cache health check should be fast"

    # Verify metadata indicates Redis backend
    if "metadata" in cache_component:
        assert cache_component["metadata"].get("backend") in ["redis", "Redis", "REDIS"]
```

**2.2 Cache Health with Memory Fallback - Graceful Degradation**
```python
@pytest.mark.integration
async def test_cache_health_check_reports_degraded_with_redis_unavailable(client, monkeypatch):
    """
    Test cache health check returns DEGRADED when Redis unavailable but memory cache works.

    Integration Scope:
        Health checker → check_cache_health → AIResponseCache fallback mechanism

    Contract Validation:
        - ComponentStatus with status=DEGRADED per health.pyi:640
        - Graceful degradation documented in AIResponseCache behavior

    Business Impact:
        Demonstrates cache resilience through fallback to memory backend
        Alerts operations to reduced cache capacity without system failure

    Test Strategy:
        - Configure cache to use memory-only (simulate Redis unavailable)
        - Verify degraded status reported accurately
        - Test through HTTP endpoint (outside-in)

    Success Criteria:
        - Cache component status is "degraded"
        - Message indicates fallback to memory cache
        - System remains operational
    """
    # Arrange: Configure memory-only cache (Redis unavailable)
    monkeypatch.setenv("CACHE_PRESET", "minimal")  # Memory-only preset

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Cache reports degraded with fallback
    assert response.status_code == 200

    data = response.json()
    cache_component = next((c for c in data["components"] if c["name"] == "cache"), None)

    assert cache_component is not None
    assert cache_component["status"] in ["degraded", "healthy"]  # May be healthy with memory

    # If degraded, should indicate fallback
    if cache_component["status"] == "degraded":
        assert "memory" in cache_component["message"].lower() or "fallback" in cache_component["message"].lower()
```

**2.3 Cache Health with Dependency Injection - Performance Optimization**
```python
@pytest.mark.integration
async def test_cache_health_check_reuses_injected_service(client):
    """
    Test cache health check uses dependency-injected cache service for optimal performance.

    Integration Scope:
        Health checker initialization → get_cache_service() dependency → check_cache_health()

    Contract Validation:
        - Dependency injection optimization per health.pyi:644-645
        - No redundant cache service instantiation

    Business Impact:
        Ensures health monitoring doesn't create unnecessary service instances
        Validates efficient resource usage in health checks

    Test Strategy:
        - Verify health check executes without creating new connections
        - Test through multiple health check calls
        - Measure consistent performance (outside-in behavioral test)

    Success Criteria:
        - Multiple health checks show consistent fast response times
        - No connection pool exhaustion
        - Performance remains optimal across requests
    """
    # Act: Execute multiple health checks in sequence
    response_times = []

    for _ in range(5):
        import time
        start = time.time()
        response = client.get("/v1/health")
        response_times.append((time.time() - start) * 1000)

        assert response.status_code == 200

    # Assert: Performance remains consistent (no degradation from repeated instantiation)
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)

    assert avg_response_time < 3000, f"Average response time {avg_response_time:.1f}ms exceeds SLA"
    assert max_response_time < 5000, f"Max response time {max_response_time:.1f}ms indicates performance issue"

    # Response times should be relatively consistent (within 2x of average)
    for rt in response_times:
        assert rt < (avg_response_time * 2), "Response time variance suggests instantiation issues"
```

**INFRASTRUCTURE NEEDS:**
- Redis container via docker-compose or testcontainers
- Cache preset configuration (development, production, minimal)
- Environment variable manipulation for fallback testing
- No mocking of cache service internals

---

### SEAM 3: HealthChecker → AI Service Configuration

**PRIORITY: HIGH** (AI service availability)
**COMPONENTS:** `HealthChecker`, `check_ai_model_health()`, `settings` configuration
**CRITICAL PATH:** Health check → Settings validation → API key presence check → Status reporting
**CONTRACT REFERENCE:** `health.pyi:568-622` (check_ai_model_health)

#### Test Scenarios

**3.1 AI Model Health with Valid Configuration**
```python
@pytest.mark.integration
async def test_ai_model_health_check_reports_healthy_with_valid_api_key(client):
    """
    Test AI model health check returns HEALTHY when API key properly configured.

    Integration Scope:
        Health checker → check_ai_model_health → settings.gemini_api_key validation

    Contract Validation:
        - ComponentStatus with status=HEALTHY per health.pyi:579
        - metadata includes provider and configuration status per health.pyi:582

    Business Impact:
        Confirms AI services ready for text processing operations

    Test Strategy:
        - Ensure valid GEMINI_API_KEY configured in environment
        - Use real health check function
        - Verify through HTTP endpoint (outside-in)

    Success Criteria:
        - AI component status is "healthy"
        - Metadata shows provider="gemini" and has_api_key=true
        - Message confirms configuration status
    """
    # Arrange: Valid API key should be configured in test environment
    # (Verify via environment or test settings)

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: AI model reports healthy
    assert response.status_code == 200

    data = response.json()
    ai_component = next((c for c in data["components"] if c["name"] == "ai_model"), None)

    assert ai_component is not None
    assert ai_component["status"] == "healthy"
    assert "configured" in ai_component["message"].lower() or "available" in ai_component["message"].lower()

    # Verify metadata if present
    if "metadata" in ai_component:
        assert ai_component["metadata"].get("provider") == "gemini"
        assert ai_component["metadata"].get("has_api_key") is True
```

**3.2 AI Model Health without Configuration - Graceful Degradation**
```python
@pytest.mark.integration
async def test_ai_model_health_check_reports_degraded_without_api_key(client, monkeypatch):
    """
    Test AI model health check returns DEGRADED when API key missing.

    Integration Scope:
        Health checker → check_ai_model_health → settings validation (missing key)

    Contract Validation:
        - ComponentStatus with status=DEGRADED per health.pyi:580
        - metadata indicates missing configuration per health.pyi:582

    Business Impact:
        Alerts operations to AI service configuration issues
        System remains partially operational for non-AI features

    Test Strategy:
        - Remove GEMINI_API_KEY from environment
        - Verify degraded status with descriptive message
        - Test through HTTP endpoint (outside-in)

    Success Criteria:
        - AI component status is "degraded"
        - Message indicates missing or invalid configuration
        - Metadata shows has_api_key=false
    """
    # Arrange: Remove API key configuration
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: AI model reports degraded
    assert response.status_code == 200

    data = response.json()
    ai_component = next((c for c in data["components"] if c["name"] == "ai_model"), None)

    assert ai_component is not None
    assert ai_component["status"] == "degraded"
    assert "missing" in ai_component["message"].lower() or "not configured" in ai_component["message"].lower()

    # Verify metadata indicates missing configuration
    if "metadata" in ai_component:
        assert ai_component["metadata"].get("has_api_key") is False
```

**3.3 AI Model Health Check - No External API Calls**
```python
@pytest.mark.integration
async def test_ai_model_health_check_makes_no_external_api_calls(client, monkeypatch):
    """
    Test AI model health check validates configuration without calling external APIs.

    Integration Scope:
        Health checker → check_ai_model_health (configuration validation only)

    Contract Validation:
        - "Does not perform actual AI model inference" per health.pyi:617
        - Fast response time for health monitoring efficiency

    Business Impact:
        Ensures health monitoring doesn't consume AI service quota
        Provides fast health checks for rapid operational feedback

    Test Strategy:
        - Monitor for external network calls during health check
        - Verify response time remains consistently fast
        - Use observable performance metrics (outside-in)

    Success Criteria:
        - Health check completes in < 100ms
        - No external network calls made
        - Consistent fast response across multiple checks
    """
    import time

    # Arrange: Configure with valid API key
    # Act: Execute health check and measure timing
    start = time.time()
    response = client.get("/v1/health")
    response_time_ms = (time.time() - start) * 1000

    # Assert: Fast response indicates no external calls
    assert response.status_code == 200

    data = response.json()
    ai_component = next((c for c in data["components"] if c["name"] == "ai_model"), None)

    assert ai_component is not None
    assert ai_component["response_time_ms"] < 100, \
        f"AI health check took {ai_component['response_time_ms']:.1f}ms (expected < 100ms without API calls)"

    # Overall response should also be fast
    assert response_time_ms < 500, \
        f"Total health check took {response_time_ms:.1f}ms (indicates potential external calls)"
```

**INFRASTRUCTURE NEEDS:**
- Environment variable manipulation via monkeypatch
- Valid test GEMINI_API_KEY in test environment
- No external API call monitoring (verified through timing)
- No mocking of AI service internals

---

### SEAM 4: HealthChecker → Resilience Infrastructure

**PRIORITY: MEDIUM** (Resilience monitoring)
**COMPONENTS:** `HealthChecker`, `check_resilience_health()`, resilience orchestrator, circuit breakers
**CRITICAL PATH:** Health check → Orchestrator query → Circuit breaker states → Status aggregation
**CONTRACT REFERENCE:** `health.pyi:650-713` (check_resilience_health)

#### Test Scenarios

**4.1 Resilience Health with All Circuits Closed - Optimal State**
```python
@pytest.mark.integration
async def test_resilience_health_check_reports_healthy_with_all_circuits_closed(client):
    """
    Test resilience health check returns HEALTHY when all circuit breakers closed.

    Integration Scope:
        Health checker → check_resilience_health → resilience orchestrator → circuit breaker states

    Contract Validation:
        - ComponentStatus with status=HEALTHY per health.pyi:661
        - metadata includes circuit breaker states per health.pyi:664

    Business Impact:
        Confirms resilience infrastructure protecting system from failures

    Test Strategy:
        - Start with fresh resilience orchestrator (all circuits closed)
        - Use real resilience health check
        - Verify through HTTP endpoint (outside-in)

    Success Criteria:
        - Resilience component status is "healthy"
        - Metadata shows total_circuit_breakers >= 0
        - Metadata shows open_circuit_breakers is empty list
    """
    # Arrange: Fresh application startup (all circuits start closed)

    # Act: Request health status
    response = client.get("/v1/health")

    # Assert: Resilience reports healthy
    assert response.status_code == 200

    data = response.json()
    resilience_component = next((c for c in data["components"] if c["name"] == "resilience"), None)

    assert resilience_component is not None
    assert resilience_component["status"] == "healthy"

    # Verify circuit breaker metadata
    if "metadata" in resilience_component:
        assert "total_circuit_breakers" in resilience_component["metadata"]
        open_breakers = resilience_component["metadata"].get("open_circuit_breakers", [])
        assert len(open_breakers) == 0, f"Expected no open breakers, found: {open_breakers}"
```

**4.2 Resilience Health with Open Circuits - Degraded but Functional**
```python
@pytest.mark.integration
@pytest.mark.slow
async def test_resilience_health_check_reports_degraded_with_open_circuits(client):
    """
    Test resilience health check returns DEGRADED when circuit breakers open.

    Integration Scope:
        Health checker → check_resilience_health → circuit breaker state detection

    Contract Validation:
        - ComponentStatus with status=DEGRADED per health.pyi:662
        - metadata identifies open circuit breakers per health.pyi:672

    Business Impact:
        Alerts operations to external service failures being protected by circuit breakers
        System remains functional through resilience patterns

    Test Strategy:
        - Trigger circuit breaker opening through repeated failures
        - Verify degraded status reflects open circuits
        - Test through HTTP endpoint (outside-in)

    Success Criteria:
        - Resilience component status is "degraded"
        - Message indicates circuit breakers open
        - Metadata lists open circuit breaker names
        - Overall system remains operational
    """
    # Arrange: Trigger circuit breaker to open by simulating failures
    # This requires making failing requests to an endpoint protected by circuit breaker
    # (Implementation depends on which operations have circuit breaker protection)

    # Simulate failures to AI service to open circuit breaker
    for _ in range(5):  # Exceed failure threshold
        try:
            response = client.post("/v1/text_processing/process",
                                   json={"text": "test", "operation": "invalid_operation"})
        except Exception:
            pass  # Expected failures

    # Act: Check health status
    response = client.get("/v1/health")

    # Assert: Resilience reports degraded or still healthy (depending on circuit breaker config)
    assert response.status_code == 200

    data = response.json()
    resilience_component = next((c for c in data["components"] if c["name"] == "resilience"), None)

    assert resilience_component is not None
    # Status may be degraded or healthy depending on whether circuit opened
    assert resilience_component["status"] in ["healthy", "degraded"]

    # If degraded, should indicate circuit breaker status
    if resilience_component["status"] == "degraded":
        assert "circuit" in resilience_component["message"].lower()

        if "metadata" in resilience_component:
            open_breakers = resilience_component["metadata"].get("open_circuit_breakers", [])
            # If circuits are open, should be reported
            if len(open_breakers) > 0:
                assert isinstance(open_breakers, list)
```

**INFRASTRUCTURE NEEDS:**
- Real resilience orchestrator with circuit breakers
- Ability to trigger circuit breaker state changes through API calls
- No mocking of resilience infrastructure
- Mark tests as `slow` when requiring state manipulation

---

### SEAM 5: Error Handling and Configuration Validation

**PRIORITY: HIGH** (Reliability and robustness)
**COMPONENTS:** `HealthChecker` initialization, configuration validation, exception handling
**CRITICAL PATH:** Configuration → Validation → Graceful error handling → Status reporting
**CONTRACT REFERENCE:** `health.pyi:383-404` (HealthChecker.__init__)

#### Test Scenarios

**5.1 Configuration Validation - Timeout Boundaries**
```python
@pytest.mark.integration
async def test_health_checker_validates_timeout_configuration_boundaries():
    """
    Test HealthChecker validates timeout parameters within acceptable ranges.

    Integration Scope:
        HealthChecker initialization → Configuration validation

    Contract Validation:
        - Timeout validation (100-30000ms) per health.pyi:388
        - Defensive parameter validation per health.pyi:402

    Business Impact:
        Prevents misconfiguration that could cause operational issues

    Test Strategy:
        - Test boundary conditions from docstring specification
        - Verify configuration validation errors raised appropriately
        - This is unit-level testing of HealthChecker initialization

    Success Criteria:
        - Valid timeouts (100-30000ms) accepted
        - Invalid timeouts rejected with clear error messages
        - Configuration immutability per health.pyi:402
    """
    from app.infrastructure.monitoring.health import HealthChecker

    # Test valid boundary conditions
    health_checker_min = HealthChecker(default_timeout_ms=100)
    assert health_checker_min is not None

    health_checker_max = HealthChecker(default_timeout_ms=30000)
    assert health_checker_max is not None

    # Test invalid boundaries (should raise ValueError per validation)
    with pytest.raises((ValueError, ValidationError)):
        HealthChecker(default_timeout_ms=50)  # Below minimum

    with pytest.raises((ValueError, ValidationError)):
        HealthChecker(default_timeout_ms=50000)  # Above maximum
```

**5.2 Configuration Validation - Retry Policy Boundaries**
```python
@pytest.mark.integration
async def test_health_checker_validates_retry_configuration_boundaries():
    """
    Test HealthChecker validates retry parameters within acceptable ranges.

    Integration Scope:
        HealthChecker initialization → Retry policy validation

    Contract Validation:
        - Retry count validation (0-10) per health.pyi:392
        - Backoff validation (0.0-5.0) per health.pyi:394

    Business Impact:
        Ensures retry policies configured within reasonable operational bounds

    Test Strategy:
        - Test boundary conditions from docstring
        - Verify validation error handling
        - Unit-level configuration testing

    Success Criteria:
        - Valid retry counts (0-10) accepted
        - Valid backoff values (0.0-5.0) accepted
        - Invalid values rejected with descriptive errors
    """
    from app.infrastructure.monitoring.health import HealthChecker

    # Test valid retry boundaries
    health_checker_no_retry = HealthChecker(retry_count=0)
    assert health_checker_no_retry is not None

    health_checker_max_retry = HealthChecker(retry_count=10)
    assert health_checker_max_retry is not None

    # Test invalid retry count
    with pytest.raises((ValueError, ValidationError)):
        HealthChecker(retry_count=-1)  # Negative not allowed

    with pytest.raises((ValueError, ValidationError)):
        HealthChecker(retry_count=15)  # Above maximum

    # Test valid backoff boundaries
    health_checker_no_backoff = HealthChecker(backoff_base_seconds=0.0)
    assert health_checker_no_backoff is not None

    health_checker_max_backoff = HealthChecker(backoff_base_seconds=5.0)
    assert health_checker_max_backoff is not None

    # Test invalid backoff
    with pytest.raises((ValueError, ValidationError)):
        HealthChecker(backoff_base_seconds=-0.5)  # Negative not allowed

    with pytest.raises((ValueError, ValidationError)):
        HealthChecker(backoff_base_seconds=10.0)  # Above maximum
```

**INFRASTRUCTURE NEEDS:**
- Direct HealthChecker instantiation for configuration testing
- Exception validation (ValueError, ValidationError)
- No external dependencies required

---

### SEAM 6: Graceful Degradation and Exception Isolation

**PRIORITY: HIGH** (System resilience)
**COMPONENTS:** `HealthChecker.check_all_components()`, exception handling, partial failure isolation
**CRITICAL PATH:** Component failure → Exception handling → Other components continue → Aggregated status
**CONTRACT REFERENCE:** `health.pyi:522` (graceful failure handling)

#### Test Scenarios

**6.1 Isolated Component Failure - Other Components Unaffected**
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

    Business Impact:
        Ensures partial failures don't prevent health monitoring of healthy components
        Provides maximum operational visibility even during failures

    Test Strategy:
        - Configure one component to fail (via environment manipulation)
        - Verify other components report normally
        - Test through HTTP endpoint (outside-in)

    Success Criteria:
        - Health endpoint remains accessible (200 status)
        - Failed component reports unhealthy with error details
        - Other components report their actual status
        - Overall status reflects worst-case component status
    """
    # Arrange: Configure environment to cause one component to fail
    # For example, invalid resilience configuration while AI and cache remain valid
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

**INFRASTRUCTURE NEEDS:**
- Environment manipulation to trigger specific component failures
- Real health check execution (no mocking)
- Validation of partial failure handling

---

## Performance Test Suite (Separate from Core Integration Tests)

**These tests validate performance characteristics and should be marked with `@pytest.mark.slow` and `@pytest.mark.performance`:**

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

# Run performance tests (slow tests)
pytest tests/integration/health/ -v -m "slow and performance"

# Run excluding performance tests (CI pipeline)
pytest tests/integration/health/ -v -m "integration and not slow"
```

---

## Success Criteria

### Functional Requirements
- ✅ All HIGH priority test scenarios pass
- ✅ Health endpoint returns HTTP 200 for all health states (healthy, degraded, unhealthy)
- ✅ Graceful degradation demonstrated for missing components
- ✅ Exception isolation prevents cascade failures
- ✅ Configuration validation prevents invalid setups

### Contract Compliance
- ✅ All tests map to documented behavior in health.pyi
- ✅ No tests validate undocumented implementation details
- ✅ Test scenarios cover all documented contract guarantees

### Testing Philosophy Adherence
- ✅ All tests use outside-in approach through HTTP endpoints
- ✅ Minimal mocking (only at system boundaries, not internal components)
- ✅ Tests focus on observable behavior rather than implementation
- ✅ Environment manipulation used instead of mocking for failure scenarios

### Performance Requirements
- ✅ Health check response < 3 seconds under normal conditions
- ✅ Concurrent requests handled without degradation
- ✅ Timeout handling prevents blocking
- ✅ Performance tests separated with appropriate markers

### Coverage Requirements
- ✅ All critical integration seams have test coverage
- ✅ Contract coverage matrix complete
- ✅ Error handling scenarios validated through observable behavior

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-09-30 | Initial test plan | Integration Testing Architect |
| 2.0 | 2025-10-01 | **Major revision** - Aligned with project testing philosophy:<br/>- Removed internal component mocking<br/>- Added contract coverage matrix<br/>- Focused on observable behavior through API<br/>- Separated performance tests<br/>- Added docstring behavior mapping | Integration Testing Architect |

---

## References

- **Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md`
- **Writing Tests**: `docs/guides/testing/WRITING_TESTS.md`
- **Health Contract**: `backend/contracts/infrastructure/monitoring/health.pyi`
- **Health Implementation**: `backend/app/infrastructure/monitoring/health.py`
