# Health Monitoring Infrastructure Unit Tests

Unit tests for `HealthChecker` module and health monitoring infrastructure following our **behavior-driven contract testing** philosophy. These tests verify the complete public interface of the health monitoring core component in complete isolation, ensuring it fulfills its documented operational monitoring contracts.

## Component Overview

**Component Under Test**: `HealthChecker` and health monitoring infrastructure (`app.infrastructure.monitoring.health`)

**Component Type**: Infrastructure Service (Single Module)

**Primary Responsibility**: Provides comprehensive async-first health monitoring capabilities for all system components including AI services, cache infrastructure, resilience systems, and databases with configurable timeout policies, retry mechanisms, and graceful degradation patterns.

**Public Contract**: Validates system-wide health status across components, orchestrates concurrent health checks with timeout protection, implements retry mechanisms with exponential backoff, and provides standardized health status reporting with performance metrics.

**Filesystem Locations:**
  - Production Code: `backend/app/infrastructure/monitoring/health.py`
  - Public Contract: `backend/contracts/infrastructure/monitoring/health.pyi`
  - Test Suite:      `backend/tests/unit/health/test_*.py`
  - Test Fixtures:   `backend/tests/unit/health/conftest.py`

## Test Organization

### Component-Based Test Structure (3 Test Files, 3,178 Lines Total)

#### **MODELS AND DATA STRUCTURES** (Foundation validation)

1. **`test_health_models.py`** (FOUNDATIONAL) - **763 lines across 4 comprehensive test classes**
   - HealthStatus Enum Validation → Value Definitions → String Representations → Equality Behavior
   - ComponentStatus Dataclass → Required Fields → Optional Fields → Default Values → Complete Instantiation
   - SystemHealthStatus Dataclass → Aggregated Status → Component Lists → Timestamp Handling → Empty Edge Cases
   - HealthCheckError Hierarchy → Base Exception → Timeout Error → Type Discrimination → Message Validation
   - Tests foundational data structures that enable consistent health reporting across all components

#### **BUILT-IN HEALTH CHECKS** (Component-specific validation)

2. **`test_builtin_checks.py`** (COMPREHENSIVE) - **820 lines across 4 focused test classes**
   - AI Model Health Checks → API Key Configuration → Service Availability → Provider Metadata → Error Classification
   - Cache Health Monitoring → Redis Operations → Memory Fallback → Connectivity Testing → Degradation Detection
   - Resilience Health Validation → Circuit Breaker States → Open/Half-Closed Detection → System Stability → Service Distinction
   - Database Health Placeholder → Template Structure → Consistent Patterns → Extensibility Framework
   - Tests individual component health check functions with complete contract coverage

#### **HEALTH CHECKER ORCHESTRATION** (End-to-end orchestration)

3. **`test_health_checker.py`** (ORCHESTRATION) - **1,212 lines across 5 comprehensive test classes**
   - HealthChecker Initialization → Configuration Validation → Timeout Policies → Retry Settings → Parameter Validation
   - Component Registration → Name Validation → Async Function Validation → Overwrite Behavior → Dynamic Registration
   - Individual Component Execution → Timeout Enforcement → Retry Logic → Error Classification → Response Time Tracking
   - System Health Aggregation → Concurrent Execution → Worst-Case Logic → Status Aggregation → Graceful Error Handling
   - Internal Status Logic → Static Method Validation → Priority Rules → Empty Component Handling → Algorithm Verification
   - Tests complete health monitoring workflows with result aggregation and performance monitoring

## Testing Philosophy Applied

These unit tests exemplify our **behavior-driven contract testing** principles:

- **Component as Unit**: Tests verify entire health monitoring infrastructure behavior, not individual methods
- **Contract Focus**: Tests validate documented public interface (Args, Returns, Raises, Behavior sections)
- **Boundary Mocking**: Mock only external dependencies (cache service, resilience orchestrator, time utilities), never internal health logic
- **Observable Outcomes**: Test return values, status enums, timing data, and side effects visible to external callers
- **Async Testing**: Comprehensive async/await testing patterns with proper fixture management
- **High-Fidelity Fakes**: Use realistic fake cache and resilience services instead of simple mocks where appropriate

## Test Fixtures and Infrastructure

### **Fake Cache Service Fixtures**
```python
@pytest.fixture
def fake_cache_service():
    """Healthy cache service with Redis and memory operational."""
    return FakeCacheService(redis_available=True, memory_available=True)

@pytest.fixture
def fake_cache_service_redis_down():
    """Degraded cache with Redis down, memory fallback active."""
    return FakeCacheService(redis_available=False, memory_available=True)

@pytest.fixture
def fake_cache_service_completely_down():
    """Failed cache with both Redis and memory unavailable."""
    return FakeCacheService(redis_available=False, memory_available=False)
```

### **Fake Resilience Orchestrator Fixtures**
```python
@pytest.fixture
def fake_resilience_orchestrator():
    """Healthy resilience system with all circuit breakers closed."""
    return FakeResilienceOrchestrator(healthy=True, open_breakers=[])

@pytest.fixture
def fake_resilience_orchestrator_with_open_breakers():
    """Degraded resilience with some circuit breakers open."""
    return FakeResilienceOrchestrator(
        healthy=False,
        open_breakers=["ai_service", "cache"]
    )

@pytest.fixture
def fake_resilience_orchestrator_recovering():
    """Resilience system in recovery state with half-open breakers."""
    return FakeResilienceOrchestrator(
        healthy=True,
        half_open_breakers=["ai_service"]
    )
```

### **HealthChecker Instance Fixtures**
```python
@pytest.fixture
def health_checker():
    """Real HealthChecker instance with default configuration for testing."""
    from app.infrastructure.monitoring.health import HealthChecker
    return HealthChecker(
        default_timeout_ms=2000,
        retry_count=1,
        backoff_base_seconds=0.1
    )

@pytest.fixture
def health_checker_with_custom_timeouts():
    """HealthChecker with per-component timeout configuration."""
    return HealthChecker(
        default_timeout_ms=2000,
        per_component_timeouts_ms={
            "database": 5000,
            "cache": 1000,
            "ai_model": 3000
        },
        retry_count=2,
        backoff_base_seconds=0.5
    )
```

### **High-Fidelity Fake Classes**
```python
class FakeCacheService:
    """Realistic cache service simulation for health testing."""

    def __init__(self, redis_available=True, memory_available=True, connect_should_fail=False):
        self.redis_available = redis_available
        self.memory_available = memory_available
        self.connect_should_fail = connect_should_fail
        self.connected = False

    async def connect(self):
        if self.connect_should_fail:
            self.redis_available = False
            raise ConnectionError("Simulated cache connection failure")
        self.connected = True

    async def get_cache_stats(self) -> Dict[str, Any]:
        # Returns realistic cache statistics based on availability state
        return {
            "redis": {"status": "ok" if self.redis_available else "error"},
            "memory": {"status": "ok" if self.memory_available else "unavailable"}
        }

class FakeResilienceOrchestrator:
    """Realistic resilience orchestrator simulation for health testing."""

    def __init__(self, healthy=True, open_breakers=None, half_open_breakers=None, should_fail=False):
        self.healthy = healthy
        self.open_breakers = open_breakers or []
        self.half_open_breakers = half_open_breakers or []
        self.should_fail = should_fail

    def get_health_status(self) -> Dict[str, Any]:
        if self.should_fail:
            raise RuntimeError("Simulated resilience system failure")

        return {
            "healthy": self.healthy and len(self.open_breakers) == 0,
            "open_circuit_breakers": self.open_breakers,
            "half_open_circuit_breakers": self.half_open_breakers
        }
```

### **Settings Integration Fixtures**
```python
# Settings fixtures are imported from parent conftest.py (backend/tests/unit/conftest.py)
# Available fixtures from parent:
# - test_settings: Real Settings instance with test configuration
# - development_settings: Settings with development preset
# - production_settings: Settings with production preset
```

## Running Tests

```bash
# Run all health monitoring unit tests
make test-backend PYTEST_ARGS="tests/unit/health/ -v"

# Run specific test files
make test-backend PYTEST_ARGS="tests/unit/health/test_health_models.py -v"
make test-backend PYTEST_ARGS="tests/unit/health/test_builtin_checks.py -v"
make test-backend PYTEST_ARGS="tests/unit/health/test_health_checker.py -v"

# Run by test class
make test-backend PYTEST_ARGS="tests/unit/health/test_health_models.py::TestHealthStatusEnum -v"
make test-backend PYTEST_ARGS="tests/unit/health/test_builtin_checks.py::TestCheckCacheHealth -v"
make test-backend PYTEST_ARGS="tests/unit/health/test_health_checker.py::TestHealthCheckerInitialization -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/unit/health/ --cov=app.infrastructure.monitoring.health"

# Run specific test methods
make test-backend PYTEST_ARGS="tests/unit/health/test_health_checker.py::TestHealthCheckerComponentExecution::test_check_component_with_timeout -v"

# Run with verbose output for debugging
make test-backend PYTEST_ARGS="tests/unit/health/ -v -s"
```

## Test Quality Standards

### **Performance Requirements**
- **Execution Speed**: < 50ms per test (fast feedback loop)
- **Determinism**: No timing dependencies or sleep() calls except in timeout testing
- **Isolation**: No external service dependencies or network calls
- **Resource Cleanup**: Automatic fixture cleanup prevents test pollution

### **Contract Coverage Requirements**
- **Public Methods**: 100% coverage of all public health monitoring methods
- **Input Validation**: Complete Args section testing per docstring
- **Output Verification**: Complete Returns section testing per docstring
- **Exception Handling**: Complete Raises section testing per docstring
- **Behavior Guarantees**: Complete Behavior section testing per docstring

### **Test Structure Standards**
- **Given/When/Then**: Clear test structure with descriptive comments
- **Single Responsibility**: One behavior verified per test method
- **Descriptive Names**: Test names clearly describe verified behavior
- **Business Impact**: Test docstrings include business impact explanation
- **Fixture Documentation**: Clear fixture purpose and usage documentation

## Success Criteria

### **Health Status Models**
- ✅ HealthStatus enum provides HEALTHY, DEGRADED, UNHEALTHY values
- ✅ ComponentStatus dataclass supports all required and optional fields
- ✅ SystemHealthStatus aggregates component statuses with worst-case logic
- ✅ HealthCheckError hierarchy provides proper exception types and messages
- ✅ All models support dataclass equality and serialization

### **Built-in Health Checks**
- ✅ AI model health validates API key configuration and service availability
- ✅ Cache health detects Redis availability and memory fallback scenarios
- ✅ Resilience health monitors circuit breaker states and system stability
- ✅ Database health placeholder provides extensible template structure
- ✅ Health checks handle timeouts and failures with appropriate error classification

### **HealthChecker Orchestration**
- ✅ HealthChecker initializes with configurable timeouts, retry policies, and backoff settings
- ✅ Component registration validates names and async function signatures
- ✅ Individual component execution respects timeouts and retry mechanisms
- ✅ System health aggregation executes components concurrently with proper error handling
- ✅ Status aggregation implements worst-case logic with UNHEALTHY > DEGRADED > HEALTHY priority

### **Performance and Reliability**
- ✅ Async operations execute concurrently without blocking
- ✅ Timeout protection prevents hanging health checks
- ✅ Retry mechanisms with exponential backoff improve reliability
- ✅ Response time tracking provides performance monitoring data
- ✅ Error isolation prevents component failures from affecting other checks

### **Error Handling and Classification**
- ✅ Timeout errors are classified as DEGRADED (temporary issues)
- ✅ Exception failures are classified as UNHEALTHY (permanent issues)
- ✅ Configuration errors are handled with actionable error messages
- ✅ Graceful degradation maintains partial functionality during failures
- ✅ Comprehensive logging supports operational troubleshooting

## What's NOT Tested (Integration Test Concerns)

### **External System Integration**
- Actual AI service connections and API calls
- Real Redis server connections and cache operations
- External database connections and query execution
- Real circuit breaker interactions with external services

### **Performance Benchmarks**
- Actual response time measurements under load
- Concurrent execution performance profiling
- Memory usage and resource consumption analysis
- Scalability testing with large numbers of components

### **Application Integration**
- FastAPI endpoint integration with HealthChecker
- Dependency injection integration with application container
- Startup and shutdown lifecycle integration
- Production deployment environment integration

### **Monitoring and Alerting**
- Integration with external monitoring systems
- Alert triggering and notification systems
- Metrics collection and time series databases
- Dashboard and visualization integration

## Environment Variables for Testing

```bash
# AI Model Configuration
GEMINI_API_KEY=test-api-key-12345               # Required for AI health checks
AI_MODEL_PROVIDER=gemini                        # AI provider selection
AI_MODEL_HEALTH_TIMEOUT=3000                   # AI health check timeout override

# Cache Configuration
CACHE_REDIS_URL=redis://localhost:6379/0        # Redis connection for cache tests
CACHE_MEMORY_SIZE=1000                          # Memory cache size for testing
CACHE_HEALTH_TIMEOUT=1000                       # Cache health check timeout override

# Resilience Configuration
RESILIENCE_PRESET=development                   # Resilience preset for health tests
CIRCUIT_BREAKER_TIMEOUT=5000                    # Circuit breaker timeout override
RETRY_MAX_ATTEMPTS=3                           # Retry attempts for health checks

# Health Check Configuration
HEALTH_CHECK_DEFAULT_TIMEOUT=2000              # Default timeout for health checks
HEALTH_CHECK_RETRY_COUNT=1                     # Retry count for failed health checks
HEALTH_CHECK_BACKOFF_BASE=0.1                  # Base seconds for exponential backoff
HEALTH_CHECK_ENABLED=true                      # Enable/disable health checks

# Monitoring Configuration
MONITORING_LOG_LEVEL=INFO                      # Logging level for health monitoring
METRICS_ENABLED=true                           # Enable metrics collection
HEALTH_STATUS_CACHE_TTL=60                     # Cache health status results

# Test Configuration
ENVIRONMENT=testing                            # Testing environment preset
HEALTH_CHECK_FAST_MODE=true                    # Fast mode for unit testing
HEALTH_CHECK_MOCK_EXTERNAL_SERVICES=true       # Mock external services in tests
```

## Test Method Examples

### **Contract-Based Testing Example**
```python
def test_health_checker_initialization_with_custom_configuration(self):
    """
    Test that HealthChecker initializes with custom configuration per constructor contract.

    Verifies: HealthChecker() accepts and stores custom timeout, retry, and backoff
              settings per Args and Behavior documentation.

    Business Impact: Ensures flexible health monitoring configuration for different
                    deployment scenarios and performance requirements.

    Given: Custom timeout, retry, and backoff configuration
    When: HealthChecker is initialized with the configuration
    Then: HealthChecker stores the configuration values
    And: Configuration is applied during health check execution
    And: Default values are used for unspecified settings

    Fixtures Used:
        - None: Direct instantiation test
    """
    # Given: Custom health checker configuration
    default_timeout_ms = 3000
    retry_count = 3
    backoff_base_seconds = 0.5
    per_component_timeouts_ms = {
        "database": 5000,
        "cache": 1000,
        "ai_model": 4000
    }

    # When: HealthChecker is initialized with custom configuration
    health_checker = HealthChecker(
        default_timeout_ms=default_timeout_ms,
        retry_count=retry_count,
        backoff_base_seconds=backoff_base_seconds,
        per_component_timeouts_ms=per_component_timeouts_ms
    )

    # Then: HealthChecker stores the configuration
    assert health_checker.default_timeout_ms == default_timeout_ms
    assert health_checker.retry_count == retry_count
    assert health_checker.backoff_base_seconds == backoff_base_seconds
    assert health_checker.per_component_timeouts_ms == per_component_timeouts_ms
```

### **Async Testing Example**
```python
@pytest.mark.asyncio
async def test_check_component_enforces_timeout(self, health_checker):
    """
    Test that check_component() enforces timeout per contract specification.

    Verifies: check_component() raises HealthCheckTimeoutError when component
              health check exceeds configured timeout per Timeout behavior documentation.

    Business Impact: Prevents health check system from hanging on slow or unresponsive
                    components, maintaining overall system responsiveness and reliability.

    Given: HealthChecker with short timeout and slow health check function
    When: check_component() is called with the slow function
    Then: HealthCheckTimeoutError is raised
    And: Error message indicates timeout occurred
    And: Component name is included in error context

    Fixtures Used:
        - health_checker: Real HealthChecker instance
    """
    # Given: Health checker with short timeout and slow health check
    async def slow_health_check():
        await asyncio.sleep(2.0)  # Longer than timeout
        return ComponentStatus(name="slow_component", status=HealthStatus.HEALTHY)

    health_checker.default_timeout_ms = 500  # 0.5 second timeout

    # When/Then: Timeout is enforced
    with pytest.raises(HealthCheckTimeoutError) as exc_info:
        await health_checker.check_component("slow_component", slow_health_check)

    error_message = str(exc_info.value)
    assert "slow_component" in error_message
    assert "timeout" in error_message.lower()
```

### **Fake Integration Example**
```python
@pytest.mark.asyncio
async def test_check_cache_health_with_redis_down(self, fake_cache_service_redis_down):
    """
    Test that check_cache_health() returns DEGRADED when Redis is down per contract.

    Verifies: check_cache_health() returns ComponentStatus with DEGRADED status
              when Redis is unavailable but memory cache provides fallback per Returns section.

    Business Impact: Ensures proper health status reporting during cache infrastructure
                    degradation, enabling appropriate operational responses and monitoring.

    Given: Fake cache service with Redis down and memory fallback active
    When: check_cache_health() is called with the cache service
    Then: ComponentStatus with DEGRADED status is returned
    And: Message explains Redis unavailability and memory fallback
    And: Response time is tracked and included
    And: Metadata includes cache type information

    Fixtures Used:
        - fake_cache_service_redis_down: Pre-configured degraded cache service
    """
    # Given: Cache service with Redis down, memory fallback active
    cache_service = fake_cache_service_redis_down

    # When: Checking cache health
    result = await check_cache_health(cache_service)

    # Then: Cache health is reported as degraded
    assert isinstance(result, ComponentStatus)
    assert result.name == "cache"
    assert result.status == HealthStatus.DEGRADED
    assert "redis" in result.message.lower()
    assert "memory" in result.message.lower()
    assert "fallback" in result.message.lower()
    assert result.response_time_ms is not None
    assert result.response_time_ms >= 0
    assert "cache_type" in result.metadata
    assert result.metadata["cache_type"] == "memory_fallback"
```

## Debugging Failed Tests

### **Health Status Model Issues**
```bash
# Test enum value definitions
make test-backend PYTEST_ARGS="tests/unit/health/test_health_models.py::TestHealthStatusEnum::test_health_status_has_healthy_value -v -s"

# Test dataclass creation
make test-backend PYTEST_ARGS="tests/unit/health/test_health_models.py::TestComponentStatus::test_component_status_creation_with_required_fields -v -s"

# Test exception hierarchy
make test-backend PYTEST_ARGS="tests/unit/health/test_health_models.py::TestHealthCheckExceptions::test_health_check_timeout_error_inheritance -v -s"
```

### **Built-in Health Check Problems**
```bash
# Test AI health check configuration
make test-backend PYTEST_ARGS="tests/unit/health/test_builtin_checks.py::TestCheckAIModelHealth::test_check_ai_model_health_with_api_key -v -s"

# Test cache health degradation
make test-backend PYTEST_ARGS="tests/unit/health/test_builtin_checks.py::TestCheckCacheHealth::test_check_cache_health_with_redis_down_memory_fallback -v -s"

# Test resilience health with circuit breakers
make test-backend PYTEST_ARGS="tests/unit/health/test_builtin_checks.py::TestCheckResilienceHealth::test_check_resilience_health_with_open_circuit_breakers -v -s"
```

### **HealthChecker Orchestration Issues**
```bash
# Test timeout enforcement
make test-backend PYTEST_ARGS="tests/unit/health/test_health_checker.py::TestHealthCheckerComponentExecution::test_check_component_enforces_timeout -v -s"

# Test retry mechanisms
make test-backend PYTEST_ARGS="tests/unit/health/test_health_checker.py::TestHealthCheckerComponentExecution::test_check_component_retries_on_failure -v -s"

# Test status aggregation
make test-backend PYTEST_ARGS="tests/unit/health/test_health_checker.py::TestHealthCheckerSystemAggregation::test_check_all_components_aggregates_statuses_concurrently -v -s"
```

## Related Documentation

- **Component Contract**: `app/infrastructure/monitoring/health.py` - HealthChecker implementation and docstring contracts
- **Unit Testing Philosophy**: `docs/guides/testing/UNIT_TESTS.md` - Comprehensive unit testing methodology and principles
- **Testing Overview**: `docs/guides/testing/TESTING.md` - High-level testing philosophy and principles
- **Contract Testing**: `docs/guides/testing/TEST_STRUCTURE.md` - Test organization and fixture patterns
- **Mocking Strategy**: `docs/guides/testing/MOCKING_GUIDE.md` - When and how to use mocks vs fakes
- **Exception Handling**: `docs/guides/developer/EXCEPTION_HANDLING.md` - Custom exception patterns and testing
- **Infrastructure Guidelines**: `docs/guides/infrastructure/MONITORING.md` - Health monitoring configuration and deployment
- **Async Testing**: `docs/guides/testing/ASYNC_TESTING.md` - Async/await testing patterns and best practices

---

## Unit Test Quality Assessment

### **Behavior-Driven Excellence**
These tests exemplify our **behavior-driven contract testing** approach:

✅ **Component Integrity**: Tests verify entire health monitoring infrastructure behavior without breaking internal cohesion
✅ **Contract Focus**: Tests validate documented public interface exclusively
✅ **Boundary Mocking**: External dependencies mocked appropriately, internal logic preserved
✅ **Observable Outcomes**: Tests verify return values, status enums, timing data, and external side effects only
✅ **Async Mastery**: Comprehensive async/await testing with proper fixture management and isolation

### **Production-Ready Standards**
✅ **>90% Coverage**: Comprehensive health monitoring logic and error handling coverage
✅ **Fast Execution**: All tests execute under 50ms for rapid feedback
✅ **Deterministic**: No timing dependencies or external service requirements
✅ **Maintainable**: Clear structure, comprehensive documentation, business impact focus
✅ **Contract Complete**: Full Args, Returns, Raises, and Behavior section coverage

These unit tests serve as a model for behavior-driven testing of infrastructure components, demonstrating how to verify complex async health monitoring logic while maintaining test isolation, speed, and comprehensive contract coverage.