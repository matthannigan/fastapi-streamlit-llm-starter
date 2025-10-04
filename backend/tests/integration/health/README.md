# Health Monitoring Integration Tests

Integration tests for the comprehensive health monitoring system following our **small, dense suite with maximum confidence** philosophy. These tests validate the complete chain from API requests through health checker orchestration to individual component health status reporting across the entire infrastructure stack.

## Test Organization

### Critical Integration Seams (14 Tests Total)

#### **CONTRACT TESTS** (Foundation for all health monitoring)

1. **`test_contract_compliance.py`** (FOUNDATION)
   - Health check function contract compliance and metadata validation
   - Health Check Functions → ComponentStatus Contract → Health Checker Integration
   - Tests contract structure, metadata compliance, and response time validation

#### **CRITICAL PATH INTEGRATION** (Core system functionality)

2. **`test_critical_path_integration.py`** (HIGHEST PRIORITY)
   - Complete health monitoring system through API endpoint
   - HTTP Request → Health Endpoint → Health Checker → All Components → Aggregated Response
   - Tests system states (healthy, degraded, unhealthy) and error isolation

#### **COMPONENT-SPECIFIC INTEGRATION** (Infrastructure component validation)

3. **`test_component_integration.py`** (HIGH PRIORITY)
   - Individual component health behaviors through API integration
   - API Endpoint → Health Checker → Specific Component → Component Status Response
   - Tests cache infrastructure, resilience monitoring, and graceful degradation

## Testing Philosophy Applied

- **Outside-In Testing**: All tests start from HTTP API endpoints and validate observable responses
- **High-Fidelity Infrastructure**: Real FastAPI TestClient, actual health check functions, live component monitoring
- **Behavior Focus**: HTTP responses, component status aggregation, timing measurements, not internal health logic
- **No Internal Mocking**: Tests real health checker collaboration across all infrastructure components
- **Contract Validation**: Ensures compliance with `health.pyi` contracts across all health monitoring scenarios

## Running Tests

```bash
# Run all health integration tests
make test-backend PYTEST_ARGS="tests/integration/health/ -v"

# Run by test category
make test-backend PYTEST_ARGS="tests/integration/health/ -v -k 'contract'"
make test-backend PYTEST_ARGS="tests/integration/health/ -v -k 'critical_path'"
make test-backend PYTEST_ARGS="tests/integration/health/ -v -k 'component'"

# Run specific test file
make test-backend PYTEST_ARGS="tests/integration/health/test_contract_compliance.py -v"
make test-backend PYTEST_ARGS="tests/integration/health/test_critical_path_integration.py -v"
make test-backend PYTEST_ARGS="tests/integration/health/test_component_integration.py -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/integration/health/ --cov=app.infrastructure.monitoring.health"

# Run performance-focused tests
make test-backend PYTEST_ARGS="tests/integration/health/test_contract_compliance.py::test_all_health_checks_follow_component_status_contract -v"
```

## Test Fixtures

### API and HTTP Infrastructure
- **`client`**: FastAPI TestClient for real HTTP request validation
- **`monkeypatch`**: Environment variable manipulation for configuration testing
- **`health_checker`**: Real health checker instance with all registered components

### Configuration Management
- **`healthy_environment`**: All components configured for optimal operation
- **`degraded_ai_environment`**: Missing AI configuration for degraded state testing
- **`invalid_resilience_environment`**: Broken resilience configuration for failure testing
- **`memory_cache_environment`**: Memory-only cache for fallback testing

### Performance and Monitoring
- **`response_time_validator`**: Performance threshold validation for health checks
- **`metadata_validator`**: Component metadata structure and content validation
- **`aggregation_validator`**: System health aggregation logic verification

## Success Criteria

### **Contract Compliance and Structure**
- ✅ All health check functions return valid ComponentStatus per `health.pyi` contract
- ✅ Component names match identifiers used in health checker registration
- ✅ Health status values are valid HealthStatus enumeration values
- ✅ Response time measurements are non-negative and accurate for performance monitoring
- ✅ Metadata structures provide actionable diagnostic information when present

### **Critical Path System Integration**
- ✅ Health endpoint returns HTTP 200 for all system states (healthy, degraded, unhealthy)
- ✅ System health aggregation follows worst-case logic (UNHEALTHY > DEGRADED > HEALTHY)
- ✅ Individual component failures don't cascade or break health monitoring system
- ✅ Health monitoring continues operational during component configuration issues
- ✅ Graceful degradation maintains system availability during partial failures

### **Component-Specific Health Monitoring**
- ✅ Cache infrastructure reports accurate operational status (Redis/memory fallback)
- ✅ Resilience monitoring provides circuit breaker state visibility
- ✅ AI model configuration validation reports proper degraded/healthy states
- ✅ Component metadata includes diagnostic information for operational troubleshooting
- ✅ Response time measurements enable performance monitoring and alerting

### **Error Handling and Resilience**
- ✅ Invalid component configurations result in appropriate health status (DEGRADED/UNHEALTHY)
- ✅ Health endpoint remains accessible during individual component failures
- ✅ Component health check failures are isolated and don't affect other components
- ✅ System provides descriptive error messages for operational troubleshooting
- ✅ Performance thresholds are maintained during various health states

## What's NOT Tested (Unit Test Concerns)

### **Internal Health Check Implementation**
- Individual component health check algorithms and logic
- Internal timeout handling and retry mechanisms within health checks
- Private method behavior in individual health check functions
- Specific component connectivity validation logic

### **Health Checker Internal State**
- Internal health check registry management
- Component registration and deregistration mechanics
- Internal timeout and retry policy implementation
- Concurrent health check execution scheduling

### **Component-Specific Infrastructure**
- Redis connection pooling and caching mechanisms
- Circuit breaker internal state transitions
- AI service API connectivity and authentication
- Database connectivity validation (placeholder implementation)

## Environment Variables for Testing

```bash
# Healthy Configuration (Default)
GEMINI_API_KEY=test-gemini-api-key
API_KEY=test-api-key-12345
CACHE_PRESET=development
RESILIENCE_PRESET=development

# Degraded AI Configuration
# GEMINI_API_KEY= (removed to trigger degraded state)

# Invalid Resilience Configuration
RESILIENCE_PRESET=invalid_preset_name

# Cache Configuration Testing
CACHE_PRESET=minimal
CACHE_PRESET=disabled

# Complex Failure Scenarios
RESILIENCE_CUSTOM_CONFIG={invalid json
CACHE_REDIS_URL=redis://invalid-host:6379
```

## Integration Points Tested

### **Contract Compliance Seam**
- Health Check Functions → ComponentStatus Contract → Health Checker Integration
- Contract structure validation across all health monitoring functions
- Metadata compliance and diagnostic information availability

### **Critical Path Integration Seam**
- HTTP Request → Health Endpoint → Health Checker → All Components → Aggregated Response
- System health aggregation logic and worst-case status determination
- Error isolation and graceful degradation patterns

### **API Health Endpoint Seam**
- FastAPI Routing → Health Checker Dependency → Component Health Checks → JSON Response
- HTTP response structure and status code validation
- Performance measurement and timing accuracy

### **Component Health Monitoring Seam**
- Health Checker → Individual Component Health Checks → Component Status Response
- Cache infrastructure health monitoring (Redis/memory fallback)
- Resilience system circuit breaker state monitoring
- AI model configuration validation

### **Configuration and Environment Seam**
- Environment Variables → Component Configuration → Health Check Behavior
- Configuration validation and error handling
- Graceful degradation during configuration issues

## Performance Expectations

- **Health Endpoint Response**: <200ms for complete system health check
- **Individual Component Checks**: <100ms per component health check (most complete in <10ms)
- **Contract Validation**: <50ms for health check function contract compliance
- **Error Handling**: <150ms for health checks with component failures
- **Response Time Accuracy**: Microsecond-precision measurement (simple checks may complete in <0.01ms)

## Debugging Failed Tests

### **Contract Compliance Issues**
```bash
# Test health check function contract compliance
make test-backend PYTEST_ARGS="tests/integration/health/test_contract_compliance.py::test_all_health_checks_follow_component_status_contract -v -s"

# Verify metadata structure compliance
make test-backend PYTEST_ARGS="tests/integration/health/test_contract_compliance.py::test_health_checks_with_metadata_include_diagnostic_information -v -s"
```

### **Critical Path Integration Problems**
```bash
# Test healthy system behavior
make test-backend PYTEST_ARGS="tests/integration/health/test_critical_path_integration.py::TestCriticalPathHealthIntegration::test_health_endpoint_returns_healthy_when_all_components_operational -v -s"

# Test degraded system handling
make test-backend PYTEST_ARGS="tests/integration/health/test_critical_path_integration.py::TestCriticalPathHealthIntegration::test_health_endpoint_returns_degraded_with_any_component_degraded -v -s"
```

### **Component Health Monitoring Failures**
```bash
# Test cache infrastructure health
make test-backend PYTEST_ARGS="tests/integration/health/test_component_integration.py::TestComponentHealthIntegration::test_cache_health_reports_operational_status_through_api -v -s"

# Verify resilience monitoring
make test-backend PYTEST_ARGS="tests/integration/health/test_component_integration.py::TestComponentHealthIntegration::test_resilience_health_reports_circuit_breaker_states -v -s"
```

### **Configuration and Error Handling Issues**
```bash
# Test invalid configuration handling
make test-backend PYTEST_ARGS="tests/integration/health/test_critical_path_integration.py::TestCriticalPathHealthIntegration::test_health_endpoint_returns_unhealthy_with_any_component_unhealthy -v -s"

# Verify error isolation
make test-backend PYTEST_ARGS="tests/integration/health/test_critical_path_integration.py::TestCriticalPathHealthIntegration::test_health_check_isolates_individual_component_failures -v -s"
```

## Test Architecture

These integration tests follow our **behavior-focused testing** principles:

1. **Test Critical Paths**: Focus on high-value health monitoring workflows essential to operational reliability
2. **Trust Contracts**: Use `health.pyi` contracts to define expected health monitoring interfaces
3. **Test from Outside-In**: Start from HTTP API endpoints and validate observable system behavior
4. **Verify Integrations**: Test real health checker collaboration across all infrastructure components

The tests ensure health monitoring provides reliable operational visibility, fails gracefully during infrastructure issues, and maintains system availability through proper error isolation and graceful degradation patterns.

## Related Documentation

- **Test Plan**: `TEST_PLAN.md` - Comprehensive test planning and scenario mapping
- **Health Contract**: `backend/contracts/infrastructure/monitoring/health.pyi` - Health monitoring interface definitions
- **Integration Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md` - Testing methodology and principles
- **Health Implementation**: `backend/app/infrastructure/monitoring/health.py` - Health monitoring system implementation