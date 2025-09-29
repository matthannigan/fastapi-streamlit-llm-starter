# Health Monitoring Infrastructure - Test Plan

## Overview

Comprehensive test coverage for `backend/app/infrastructure/monitoring/health.py` following behavior-driven, contract-focused testing principles.

## Test Organization

### Test Files

1. **`test_health_checker.py`** - HealthChecker class orchestration
2. **`test_builtin_checks.py`** - Built-in health check functions
3. **`test_health_models.py`** - Data models and enums

### Coverage Statistics

- **Total Test Skeletons**: 95 test methods
- **Test Classes**: 16 test classes
- **Components Tested**: All public interfaces from health.pyi contract

## Test File Breakdown

### 1. test_health_checker.py (58 tests)

Tests the centralized HealthChecker orchestration service.

**Test Classes:**
- `TestHealthCheckerInitialization` (7 tests)
  - Default configuration
  - Custom timeout/retry settings
  - Parameter validation
  - Per-component timeout overrides

- `TestHealthCheckerRegistration` (6 tests)
  - Health check registration
  - Name validation
  - Async function validation
  - Overwrite behavior

- `TestHealthCheckerComponentExecution` (13 tests)
  - Individual component health checks
  - Timeout enforcement
  - Retry with exponential backoff
  - Error classification (DEGRADED vs UNHEALTHY)
  - Response time tracking
  - Logging behavior

- `TestHealthCheckerSystemAggregation` (9 tests)
  - Concurrent execution
  - Status aggregation (worst-case logic)
  - Timestamp generation
  - Graceful error handling
  - Metadata preservation

- `TestHealthCheckerInternalStatusAggregation` (6 tests)
  - _determine_overall_status() static method
  - Worst-case aggregation algorithm
  - Empty component list handling
  - Priority rules (UNHEALTHY > DEGRADED > HEALTHY)

**Coverage Areas:**
- ✅ Configuration validation
- ✅ Component registration
- ✅ Timeout policies
- ✅ Retry mechanisms
- ✅ Error handling
- ✅ Concurrent execution
- ✅ Status aggregation

### 2. test_builtin_checks.py (26 tests)

Tests standalone health check functions for system components.

**Test Classes:**
- `TestCheckAIModelHealth` (6 tests)
  - API key configuration validation
  - HEALTHY/DEGRADED/UNHEALTHY states
  - No actual API calls (performance)
  - Provider metadata
  - Response timing

- `TestCheckCacheHealth` (9 tests)
  - Redis operational (HEALTHY)
  - Redis down with memory fallback (DEGRADED)
  - Complete cache failure (UNHEALTHY)
  - Dependency injection optimization
  - Connection failure handling
  - Cache type metadata

- `TestCheckResilienceHealth` (7 tests)
  - All circuits closed (HEALTHY)
  - Open circuit breakers (DEGRADED)
  - Orchestrator failure (UNHEALTHY)
  - Circuit breaker metadata
  - Half-open state detection
  - Service vs infrastructure failure distinction

- `TestCheckDatabaseHealth` (4 tests)
  - Placeholder verification
  - Template structure
  - Consistent naming
  - Response time pattern

**Coverage Areas:**
- ✅ AI configuration validation
- ✅ Cache connectivity testing
- ✅ Circuit breaker monitoring
- ✅ Database placeholder structure

### 3. test_health_models.py (31 tests)

Tests data structures and exceptions for health reporting.

**Test Classes:**
- `TestHealthStatusEnum` (5 tests)
  - HEALTHY/DEGRADED/UNHEALTHY values
  - String representations
  - Equality comparison

- `TestComponentStatus` (9 tests)
  - Required fields (name, status)
  - Optional fields (message, response_time_ms, metadata)
  - Default values
  - Complete instantiation
  - Dataclass equality

- `TestSystemHealthStatus` (6 tests)
  - Required fields (overall_status, components, timestamp)
  - Components list handling
  - Empty components edge case
  - Complete instantiation
  - Dataclass equality

- `TestHealthCheckExceptions` (6 tests)
  - HealthCheckError base exception
  - HealthCheckTimeoutError inheritance
  - Exception messages
  - Type discrimination
  - Try/except handling patterns

**Coverage Areas:**
- ✅ Enum definitions
- ✅ Dataclass structure
- ✅ Default values
- ✅ Exception hierarchy

## Testing Principles Applied

### 1. Contract-Driven Testing
- All tests derive from public contract in `health.pyi`
- Tests verify documented Args, Returns, Raises, Behavior
- No tests for internal implementation details

### 2. Component as Unit
- Tests treat entire `health` module as Unit Under Test
- No mocking of internal collaborators
- External dependencies (cache, resilience) use Fakes from conftest.py

### 3. Observable Outcomes
- Tests verify return values, status enums, exceptions
- No assertions on internal method calls or private state
- Focus on what external callers can observe

### 4. Comprehensive Coverage

**By Behavior Type:**
- ✅ Happy path scenarios (all components healthy)
- ✅ Configuration validation (parameters, defaults)
- ✅ Error handling (timeouts, failures, exceptions)
- ✅ Edge cases (empty lists, boundary values)
- ✅ Performance (response time tracking, concurrent execution)

**By Component Type:**
- ✅ Core orchestration (HealthChecker)
- ✅ Built-in checks (AI, cache, resilience, database)
- ✅ Data models (status, enums, exceptions)

## Fixtures Required

From `backend/tests/unit/health/conftest.py`:

**Fake Dependencies:**
- `fake_cache_service` - Healthy cache
- `fake_cache_service_redis_down` - Degraded cache
- `fake_cache_service_completely_down` - Failed cache
- `fake_cache_service_connection_fails` - Connection error
- `fake_resilience_orchestrator` - Healthy resilience
- `fake_resilience_orchestrator_with_open_breakers` - Degraded resilience
- `fake_resilience_orchestrator_recovering` - Half-open circuits
- `fake_resilience_orchestrator_failed` - Failed resilience

From `backend/tests/unit/conftest.py`:
- `test_settings` - Real Settings with test configuration
- `development_settings` - Development preset
- `production_settings` - Production preset

## Implementation Notes

### Test Execution Order
Tests are independent and can run in any order or in parallel.

### Async Testing
Many tests require `@pytest.mark.asyncio` decorator (to be added during implementation).

### Timing Tests
Some tests verify timeout and retry behavior - may need tolerance ranges for CI/CD.

### Logging Tests
Tests that verify logging behavior will need pytest `caplog` fixture.

### Mocking Requirements
Minimal mocking required:
- Patch `ai_resilience` import in resilience health check tests
- Patch `get_cache_service` import in cache health check tests (fallback path)
- Monkeypatch `settings.gemini_api_key` for AI configuration tests

## Test Execution

```bash
# Run all health monitoring tests
pytest tests/unit/health/ -v

# Run specific test file
pytest tests/unit/health/test_health_checker.py -v

# Run specific test class
pytest tests/unit/health/test_health_checker.py::TestHealthCheckerInitialization -v

# Run with coverage
pytest tests/unit/health/ --cov=app.infrastructure.monitoring.health --cov-report=term-missing
```

## Success Criteria

- ✅ All 95 tests pass consistently
- ✅ Tests focus on observable behavior only
- ✅ Complete coverage of public contract
- ✅ Tests survive implementation refactoring
- ✅ Fast execution (< 50ms per test target)
- ✅ >90% code coverage (infrastructure requirement)

## Next Steps

1. Implement test logic following skeleton docstrings
2. Add async decorators where needed
3. Verify all fixtures work correctly
4. Run tests and achieve green status
5. Validate coverage metrics meet >90% target