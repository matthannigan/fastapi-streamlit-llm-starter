# Health Monitoring Integration Tests

This directory contains comprehensive integration tests for the health monitoring infrastructure system (`app.infrastructure.monitoring.health`). These tests verify the integration between health monitoring components, API endpoints, dependency injection, and external systems.

## Overview

The health monitoring system provides comprehensive system observability, monitoring the health of critical infrastructure components including cache services, AI models, resilience patterns, and database connectivity. The integration tests ensure these components work together correctly to provide reliable monitoring capabilities.

## Test Structure

### High Priority Tests (Critical for monitoring reliability and API compatibility)

#### 1. Cache System Health Integration (`test_cache_health_integration.py`)
- **Purpose**: Verify integration between HealthChecker and AIResponseCache
- **Key Tests**:
  - Cache service connectivity with Redis and memory fallback
  - Performance monitoring integration
  - Graceful degradation with cache failures
  - Cache statistics collection and reporting

#### 2. Resilience System Health Integration (`test_resilience_health_integration.py`)
- **Purpose**: Test circuit breaker and resilience pattern health monitoring
- **Key Tests**:
  - Circuit breaker state monitoring and reporting
  - Resilience metrics collection and integration
  - Open circuit breaker detection and alerting
  - Resilience service availability monitoring

#### 3. AI Model Health Integration (`test_ai_model_health_integration.py`)
- **Purpose**: Test AI service connectivity and model validation
- **Key Tests**:
  - API key validation and presence detection
  - AI service connectivity verification
  - Model availability and health assessment
  - Provider-specific health validation

#### 4. Health Monitoring API Integration (`test_health_api_integration.py`)
- **Purpose**: Test meta-monitoring API endpoints
- **Key Tests**:
  - Comprehensive API response structure validation
  - Component-level health reporting
  - Authentication integration
  - Endpoint discovery functionality

#### 5. FastAPI Dependency Injection Integration (`test_dependency_injection_integration.py`)
- **Purpose**: Test health checker service lifecycle
- **Key Tests**:
  - Singleton behavior through dependency injection
  - Component registration and availability
  - Service lifecycle management
  - Concurrent access patterns

#### 6. Health Check Exception Handling Integration (`test_health_check_exception_handling.py`)
- **Purpose**: Test custom exception handling
- **Key Tests**:
  - Custom exception hierarchy and error handling
  - Error context preservation and debugging
  - Graceful degradation with component failures
  - Exception aggregation and reporting

### Medium Priority Tests (Important for functionality and performance)

#### 7. Database Health Integration (`test_database_health_integration.py`)
- **Purpose**: Test database connectivity validation (currently placeholder)
- **Key Tests**:
  - Placeholder implementation behavior
  - Response structure compliance
  - Future implementation compatibility
  - Performance characteristics

#### 8. Timeout and Retry Integration (`test_timeout_retry_integration.py`)
- **Purpose**: Test health check timeout and retry behavior
- **Key Tests**:
  - Timeout handling with custom configurations
  - Retry logic with transient and persistent failures
  - Backoff strategy integration
  - Performance under timeout/retry conditions

#### 9. Configuration-Driven Health Monitoring (`test_configuration_driven_health.py`)
- **Purpose**: Test configuration-based health checks
- **Key Tests**:
  - Timeout configuration flexibility
  - Per-component timeout configuration
  - Retry configuration flexibility
  - Environment-specific configuration

#### 10. Health Monitoring Performance and Metrics (`test_health_monitoring_performance.py`)
- **Purpose**: Test performance measurement
- **Key Tests**:
  - Individual component performance characteristics
  - System-wide performance aggregation
  - Performance under failure conditions
  - Performance scaling with component count

## Test Philosophy

These integration tests follow the project's integration testing philosophy:

### Behavior-Focused Testing
- Tests verify observable outcomes, not internal implementation
- Focuses on component collaboration and system behavior
- Validates integration points between health monitoring components

### Outside-In Testing
- Tests are initiated from API endpoints or entry points
- Verifies end-to-end integration scenarios
- Focuses on user-observable behavior

### High-Fidelity Test Environment
- Uses real or high-fidelity fake infrastructure (fakeredis, test containers)
- Minimal mocking of internal components
- Realistic test scenarios that mirror production conditions

## Running the Tests

### Prerequisites
- All backend dependencies installed
- Test database or fakeredis available
- API keys configured for AI services (for manual tests)

### Test Execution Commands

```bash
# Run all health monitoring integration tests
pytest backend/tests/integration/health/ -v

# Run specific test files
pytest backend/tests/integration/health/test_cache_health_integration.py -v
pytest backend/tests/integration/health/test_resilience_health_integration.py -v

# Run with coverage
pytest backend/tests/integration/health/ --cov=app.infrastructure.monitoring --cov-report=term-missing

# Run specific test scenarios
pytest backend/tests/integration/health/ -k "test_cache_health_integration_with_redis" -v

# Run performance tests
pytest backend/tests/integration/health/test_health_monitoring_performance.py -v

# Run with different configurations
pytest backend/tests/integration/health/ -v --tb=short
```

### Test Markers

- `@pytest.mark.integration`: General integration test marker
- `@pytest.mark.slow`: Performance and load testing scenarios
- `@pytest.mark.manual`: Tests requiring real external services

### Test Data and Fixtures

The tests use comprehensive fixtures defined in `conftest.py`:

- **Health Checker Fixtures**: Various health checker configurations
- **Cache Service Fixtures**: Real and mock cache services
- **Resilience Service Fixtures**: Healthy and unhealthy resilience services
- **Settings Fixtures**: Different environment configurations
- **Performance Monitoring Fixtures**: Real performance monitors

## Test Scenarios

### Critical Integration Points

1. **Cache System Integration**
   - Health checker registration with cache service
   - Performance monitoring integration
   - Redis and memory fallback scenarios
   - Statistics collection and reporting

2. **Resilience System Integration**
   - Circuit breaker state monitoring
   - Metrics collection and aggregation
   - Open circuit breaker detection
   - Resilience service availability

3. **AI Service Integration**
   - API key validation and presence
   - Service connectivity verification
   - Provider-specific health validation
   - Model availability assessment

4. **API Integration**
   - HTTP endpoint functionality
   - Response structure validation
   - Authentication integration
   - Component health aggregation

5. **Dependency Injection Integration**
   - Singleton behavior verification
   - Component registration validation
   - Service lifecycle management
   - Concurrent access patterns

### Failure Scenarios

The tests cover various failure scenarios:

- **Component Failures**: Individual component health check failures
- **Timeout Scenarios**: Health checks exceeding timeout limits
- **Exception Handling**: Custom exception propagation and handling
- **Configuration Issues**: Invalid or missing configuration
- **Performance Degradation**: Slow or unresponsive components
- **Concurrent Load**: Multiple simultaneous health check requests

## Key Integration Patterns Tested

### 1. Component Registration and Discovery
```python
# Health checker registration
health_checker.register_check("cache", check_cache_health)

# Component discovery through dependency injection
checker = get_health_checker()
registered_checks = list(checker._checks.keys())
```

### 2. Health Status Aggregation
```python
# System-wide health assessment
system_health = await health_checker.check_all_components()
overall_status = system_health.overall_status
components = system_health.components
```

### 3. Performance Monitoring Integration
```python
# Performance metrics collection
result = await health_checker.check_component("cache")
response_time = result.response_time_ms
metadata = result.metadata  # Performance data
```

### 4. Error Handling and Recovery
```python
# Graceful error handling
try:
    result = await health_checker.check_component("failing_component")
except HealthCheckError as e:
    # Handle specific health check errors
    logger.error(f"Health check failed: {e}")
```

### 5. Configuration-Driven Behavior
```python
# Configuration-based health checking
checker = HealthChecker(
    default_timeout_ms=settings.health_check_timeout,
    retry_count=settings.health_check_retries
)
```

## Performance Requirements

The integration tests validate performance characteristics:

- **Individual Health Checks**: <100ms for simple checks, <500ms for complex checks
- **System Health Checks**: <1 second for typical systems, <3 seconds for large systems
- **Concurrent Operations**: Support for multiple simultaneous health checks
- **Memory Usage**: Minimal memory overhead for monitoring operations
- **CPU Impact**: Low CPU impact during health monitoring

## Monitoring and Observability

The tests verify monitoring and observability features:

- **Response Time Tracking**: Accurate measurement of health check duration
- **Error Context**: Detailed error information for troubleshooting
- **Component Metadata**: Rich metadata for operational insights
- **Performance Metrics**: Performance data collection and reporting
- **Health Status History**: Status tracking over time

## Future Enhancements

### Planned Test Coverage
- Real database connectivity testing (when database is implemented)
- External service integration testing
- Load testing under realistic production scenarios
- Long-running health monitoring stability tests
- Cross-component failure scenario testing

### Test Infrastructure Improvements
- Testcontainers for realistic infrastructure testing
- Performance benchmarking and regression testing
- Automated test data generation for large-scale scenarios
- Integration with external monitoring systems for end-to-end testing

## Troubleshooting

### Common Issues

1. **Redis Connection Issues**
   - Ensure fakeredis is properly configured
   - Check Redis URL configuration
   - Verify cache service initialization

2. **Performance Test Timeouts**
   - Increase timeout values for slow test scenarios
   - Check system resources during performance testing
   - Verify test isolation between performance tests

3. **Component Registration Failures**
   - Verify component names are unique
   - Check health check function signatures
   - Ensure async functions are properly defined

4. **Dependency Injection Issues**
   - Verify FastAPI app configuration
   - Check dependency override configurations
   - Ensure singleton behavior is maintained

### Debug Tips

- Use `-v` flag for verbose test output
- Use `-s` flag to see print statements during tests
- Run individual test files for focused debugging
- Check fixture setup in `conftest.py` for test dependencies
- Verify mock configurations for external service simulation

## Related Documentation

- **[Integration Testing Guide](../../../guides/testing/INTEGRATION_TESTS.md)**: Integration testing philosophy and patterns
- **[Health Monitoring Implementation](../../infrastructure/monitoring/README.md)**: Health monitoring system documentation
- **[Testing Overview](../../../guides/testing/TESTING.md)**: Overall testing strategy and principles
- **[Test Structure Guide](../../../guides/testing/TEST_STRUCTURE.md)**: Test organization and fixtures

## Contributing

When adding new integration tests:

1. Follow the established test structure and naming conventions
2. Include comprehensive docstrings following the project's documentation standards
3. Add appropriate fixtures to `conftest.py` if needed
4. Verify tests work with the existing test infrastructure
5. Update this README with new test descriptions
6. Ensure tests align with the integration testing philosophy

## Test Results Summary

### Coverage Goals
- **High Priority Tests**: >90% integration coverage for health monitoring system
- **Medium Priority Tests**: >70% integration coverage for health monitoring features
- **Performance Validation**: All performance requirements met
- **Error Scenarios**: All critical failure scenarios covered

### Success Criteria
- **Reliability**: Health checks complete successfully under normal conditions
- **Performance**: Individual health checks complete in <100ms, full system check in <500ms
- **Robustness**: System handles health check failures gracefully without affecting application
- **Accuracy**: Health status accurately reflects actual component health
- **Monitoring**: External monitoring systems can reliably access health status via API
