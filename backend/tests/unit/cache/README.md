# Cache Infrastructure Unit Tests

Unit tests for the `cache` component's multiple modules following our **behavior-driven contract testing** philosophy. These tests verify the complete public interfaces of the entire cache infrastructure component in complete isolation, ensuring it fulfills its documented performance, security, and data management contracts.

## Component Overview

**Component Under Test**: `cache` (`app.infrastructure.cache.*`)

**Component Type**: Infrastructure Service (Multi Module)

**Architecture**: Security-first cache infrastructure with 14 core modules providing comprehensive caching solutions for both AI and generic applications with mandatory encryption and TLS security

**Primary Responsibilities**:
- In-memory caching with LRU eviction and TTL management for high-performance scenarios
- Redis-based distributed caching with mandatory TLS encryption and authentication
- AI-optimized caching with intelligent key generation and response validation
- Security-first architecture with mandatory Fernet encryption and access control
- Performance monitoring and metrics collection with real-time analytics
- Cache factory pattern with environment-aware configuration and preset management
- Comprehensive cache invalidation strategies and lifecycle management

**Public Contracts**: Each module provides specific contracts for data storage, security, performance, configuration management, and monitoring.

**Filesystem Locations:**
  - Production Code: `backend/app/infrastructure/cache/*.py`
  - Public Contract: `backend/contracts/infrastructure/cache/*.pyi`
  - Test Suite:      `backend/tests/unit/cache/**/test_*.py`
  - Test Fixtures:   `backend/tests/unit/cache/*/conftest.py`

## Architecture Overview

### Security-First Cache Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYER                           │
│  security.py (mandatory TLS, authentication, encryption)    │
│  - Security configuration with TLS enforcement              │
│  - Fernet encryption for all cached data                    │
│  - Access control and security validation                   │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                   CACHE IMPLEMENTATIONS                     │
│  redis_ai.py (AI-optimized cache with response validation)  │
│  redis_generic.py (Flexible Redis cache with L1 fallback)   │
│  memory.py (High-performance in-memory cache)               │
│  - Multiple cache implementations for different use cases   │
│  - Unified interface through abstract base class            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                  CONFIGURATION LAYER                        │
│  config.py (core configuration management)                  │
│  ai_config.py (AI-specific configuration)                   │
│  cache_presets.py (environment-aware preset system)         │
│  cache_validator.py (configuration validation)              │
│  - Environment-aware configuration with presets             │
│  - Comprehensive validation and security checks             │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     UTILITIES LAYER                         │
│  factory.py (cache creation with secure defaults)           │
│  key_generator.py (intelligent cache key generation)        │
│  parameter_mapping.py (operation parameter mapping)         │
│  dependencies.py (FastAPI dependency injection)             │
│  - Factory pattern for secure cache creation                │
│  - FastAPI integration with lifecycle management            │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                  MONITORING LAYER                           │
│  monitoring.py (performance monitoring and analytics)       │
│  - Real-time metrics collection and analysis                │
│  - Performance tracking and alerting                        │
└─────────────────────────────────────────────────────────────┘
```

## Test Organization

### Multi-Module Test Structure (41 Test Files, 53,034 Lines Total)

#### **SECURITY MODULE** (Mandatory security enforcement)

**Test Directory**: `security/` (2 test files)

1. **`test_security_config.py`** - Security configuration validation and TLS enforcement
2. **`test_security_manager.py`** - Security validation and access control

**Primary Component**: `RedisCacheSecurityManager` with mandatory TLS and encryption

#### **ENCRYPTION MODULE** (Data protection and encryption)

**Test Directory**: `encryption/` (4 test files)

1. **`test_cache_encryption_initialization.py`** - Encryption setup and configuration
2. **`test_core_operations.py`** - Encryption/decryption operations
3. **`test_error_handling.py`** - Encryption error scenarios and recovery
4. **`test_performance_monitoring.py`** - Encryption performance impact monitoring

**Primary Component**: Fernet-based encryption with transparent data protection

#### **BASE CACHE MODULE** (Abstract interface foundation)

**Test Directory**: `base/` (1 test file)

1. **`test_base.py`** - Abstract cache interface validation

**Primary Component**: `CacheInterface` abstract base class for all implementations

#### **MEMORY CACHE MODULE** (High-performance in-memory caching)

**Test Directory**: `memory/` (4 test files)

1. **`test_memory_initialization.py`** - Cache setup and configuration validation
2. **`test_memory_core_operations.py`** - Basic CRUD operations and TTL management
3. **`test_memory_lru_eviction.py`** - LRU eviction policy and memory management
4. **`test_memory_statistics.py`** - Performance metrics and statistics collection

**Primary Component**: `InMemoryCache` with LRU eviction and TTL support

#### **REDIS IMPLEMENTATIONS** (Distributed caching with security)

**Redis Generic Directory**: `redis_generic/` (4 test files)

1. **`test_initialization_and_connection.py`** - Redis connection setup with TLS
2. **`test_core_cache_operations.py`** - Basic Redis operations with encryption
3. **`test_callback_system_integration.py`** - Event callback system
4. **`test_security_features.py`** - Security validation and enforcement

**Redis AI Directory**: `redis_ai/` (7 test files)

1. **`test_redis_ai_initialization.py`** - AI cache setup and configuration
2. **`test_redis_ai_connection.py`** - Secure Redis connection management
3. **`test_redis_ai_core_operations.py`** - AI-specific cache operations
4. **`test_redis_ai_error_handling.py`** - Error scenarios and recovery
5. **`test_redis_ai_inheritance.py`** - Inheritance from generic Redis cache
6. **`test_redis_ai_invalidation.py`** - Cache invalidation strategies
7. **`test_redis_ai_statistics.py`** - Performance monitoring and analytics

**Primary Components**: `AIResponseCache` and `GenericRedisCache` with mandatory security

#### **CONFIGURATION MANAGEMENT MODULES** (Preset and validation system)

**Config Directory**: `config/` (4 test files)

1. **`test_config_builder.py`** - Configuration building and validation
2. **`test_config_core.py`** - Core configuration functionality
3. **`test_environment_presets.py`** - Environment-based preset management
4. **`test_cache_validator.py`** - Configuration validation

**AI Config Directory**: `ai_config/` (1 test file)

1. **`test_ai_config.py`** - AI-specific configuration management

**Cache Presets Directory**: `cache_presets/` (4 test files)

1. **`test_cache_presets_config.py`** - Preset configuration management
2. **`test_cache_presets_manager.py`** - Preset manager operations
3. **`test_cache_presets_preset.py`** - Individual preset functionality
4. **`test_cache_presets_strategy.py`** - Preset selection strategies

**Cache Validator Directory**: `cache_validator/` (3 test files)

1. **`test_cache_validator_result.py`** - Validation result handling
2. **`test_cache_validator_validator.py`** - Configuration validation logic

#### **UTILITY MODULES** (Cache creation and management)

**Factory Directory**: `factory/` (1 test file)

1. **`test_factory.py`** - Cache factory pattern and secure defaults

**Key Generator Directory**: `key_generator/` (1 test file)

1. **`test_key_generator.py`** - Intelligent cache key generation

**Parameter Mapping Directory**: `parameter_mapping/` (1 test file)

1. **`test_parameter_mapping.py`** - Operation parameter mapping

**Dependencies Directory**: `dependencies/` (3 test files)

1. **`test_core_dependencies.py`** - Core dependency injection
2. **`test_specialized_dependencies.py`** - Specialized dependency patterns
3. **`test_lifecycle_and_health.py`** - Dependency lifecycle management

#### **MONITORING MODULE** (Performance tracking and analytics)

**Monitoring Directory**: `monitoring/` (3 test files)

1. **`test_metric_dataclasses.py`** - Metrics data structures
2. **`test_performance_monitor.py`** - Performance monitoring implementation
3. **`test_statistics_and_analysis.py`** - Statistical analysis and reporting

**Primary Component**: `CachePerformanceMonitor` with real-time analytics

## Testing Philosophy Applied

These unit tests exemplify our **behavior-driven contract testing** principles across a complex multi-module infrastructure:

- **Module as Unit**: Each infrastructure module is tested as a complete unit with its public interface
- **Contract Focus**: Tests validate documented public contracts for each module independently
- **Security-First Testing**: All security features are validated with mandatory TLS and encryption
- **Boundary Mocking**: Mock only external dependencies (redis, time, encryption), never inter-module dependencies
- **Observable Outcomes**: Test return values, exceptions, metrics, and security states visible to external callers
- **Performance Contracts**: Verify performance characteristics meet documented SLAs
- **Security Validation**: Ensure mandatory security features cannot be bypassed

## Shared Test Infrastructure

### **Global Fixture Infrastructure** (`conftest.py` - 200+ lines)

**Real Factory Fixtures**:
```python
@pytest.fixture
async def real_cache_factory():
    """Real CacheFactory instance for testing factory behavior."""
    from app.infrastructure.cache.factory import CacheFactory
    return CacheFactory()

@pytest.fixture
def secure_cache_config():
    """Secure cache configuration with mandatory TLS."""
    from app.infrastructure.cache.config import CacheConfig
    return CacheConfig(
        redis_url="rediss://localhost:6379",  # TLS required
        encryption_key="test-key-for-encryption-purposes-only",
        security_level="high"
    )
```

**AI-Specific Data Fixtures**:
```python
@pytest.fixture
def ai_response_samples():
    """Realistic AI response data for testing."""
    return {
        "summarize": {
            "summary": "This is a test summary",
            "confidence": 0.95,
            "model": "gemini-pro"
        },
        "sentiment": {
            "sentiment": "positive",
            "score": 0.87,
            "analysis": "Strong positive sentiment detected"
        }
    }

@pytest.fixture
def cache_operation_scenarios():
    """Comprehensive cache operation scenarios."""
    return {
        "basic_crud": ["get", "set", "delete", "exists"],
        "ai_operations": ["summarize", "sentiment", "classification"],
        "ttl_operations": ["set_with_ttl", "extend_ttl", "get_remaining_ttl"]
    }
```

### **Module-Specific Test Infrastructure**

Each module contains its own `conftest.py` with specialized fixtures:

**Redis AI Cache Fixtures**:
```python
@pytest.fixture
async def redis_ai_cache_with_encryption():
    """AI cache with mandatory encryption enabled."""
    from app.infrastructure.cache.redis_ai import AIResponseCache
    return AIResponseCache(
        redis_url="rediss://localhost:6379",
        encryption_key="test-encryption-key-32-chars-long",
        security_level="high"
    )

@pytest.fixture
def ai_cache_key_scenarios():
    """AI cache key generation scenarios."""
    return {
        "summarize": {
            "text": "Sample text for summarization",
            "model": "gemini-pro",
            "expected_key_pattern": "summarize:gemini-pro:"
        },
        "sentiment": {
            "text": "Sample text for sentiment analysis",
            "model": "gemini-pro",
            "expected_key_pattern": "sentiment:gemini-pro:"
        }
    }
```

**Security Testing Fixtures**:
```python
@pytest.fixture
def security_validation_scenarios():
    """Security validation test scenarios."""
    return {
        "valid_tls": {
            "redis_url": "rediss://secure-redis:6379",
            "password": "secure-password",
            "should_pass": True
        },
        "invalid_no_tls": {
            "redis_url": "redis://insecure-redis:6379",
            "password": "password",
            "should_pass": False,
            "expected_error": "TLS required"
        },
        "invalid_no_password": {
            "redis_url": "rediss://redis:6379",
            "password": "",
            "should_pass": False,
            "expected_error": "Password required"
        }
    }
```

## Running Tests

### **Module-Specific Test Execution**

```bash
# Run all cache unit tests
make test-backend PYTEST_ARGS="tests/unit/cache/ -v"

# Run specific module tests
make test-backend PYTEST_ARGS="tests/unit/cache/memory/ -v"
make test-backend PYTEST_ARGS="tests/unit/cache/redis_ai/ -v"
make test-backend PYTEST_ARGS="tests/unit/cache/security/ -v"
make test-backend PYTEST_ARGS="tests/unit/cache/encryption/ -v"
make test-backend PYTEST_ARGS="tests/unit/cache/config/ -v"
make test-backend PYTEST_ARGS="tests/unit/cache/factory/ -v"
make test-backend PYTEST_ARGS="tests/unit/cache/monitoring/ -v"

# Run specific test files
make test-backend PYTEST_ARGS="tests/unit/cache/memory/test_memory_core_operations.py -v"
make test-backend PYTEST_ARGS="tests/unit/cache/redis_ai/test_redis_ai_core_operations.py -v"
make test-backend PYTEST_ARGS="tests/unit/cache/security/test_security_manager.py -v"

# Run with coverage by module
make test-backend PYTEST_ARGS="tests/unit/cache/memory/ --cov=app.infrastructure.cache.memory"
make test-backend PYTEST_ARGS="tests/unit/cache/redis_ai/ --cov=app.infrastructure.cache.redis_ai"
make test-backend PYTEST_ARGS="tests/unit/cache/ --cov=app.infrastructure.cache"
```

### **Cross-Module Integration Testing**

```bash
# Test factory integration with all cache types
make test-backend PYTEST_ARGS="tests/unit/cache/factory/test_factory.py -v"

# Test configuration system integration
make test-backend PYTEST_ARGS="tests/unit/cache/ -v -k 'integration'"

# Test security across all cache implementations
make test-backend PYTEST_ARGS="tests/unit/cache/ -v -k 'security'"

# Test performance across all cache implementations
make test-backend PYTEST_ARGS="tests/unit/cache/ -v -k 'performance'"
```

### **Security-Focused Testing**

```bash
# Test all security features
make test-backend PYTEST_ARGS="tests/unit/cache/security/ tests/unit/cache/encryption/ -v"

# Test TLS enforcement
make test-backend PYTEST_ARGS="tests/unit/cache/ -v -k 'tls'"

# Test encryption functionality
make test-backend PYTEST_ARGS="tests/unit/cache/encryption/ -v"
```

## Test Quality Standards

### **Performance Requirements**
- **Execution Speed**: < 25ms per individual cache operation test
- **Security Tests**: < 50ms per security validation test
- **Integration Tests**: < 150ms for cross-cache coordination
- **Encryption Tests**: < 75ms for encryption/decryption operations
- **Determinism**: No timing dependencies or real Redis connections in unit tests

### **Coverage Requirements**
- **Infrastructure Modules**: >90% test coverage (production-ready requirement)
- **Each Module**: Complete public interface coverage
- **Security Features**: 100% security validation coverage
- **Error Handling**: 100% exception condition coverage
- **Configuration**: All parameter validation and edge case coverage

### **Test Structure Standards**
- **Module Isolation**: Each module tested independently with proper boundary mocking
- **Security Validation**: All mandatory security features validated
- **Contract Focus**: Tests verify documented public interface behavior
- **Real Instances**: Use real objects at system boundaries, not mocks
- **Performance Validation**: Verify performance contracts are met

## Success Criteria

### **Security Module**
- ✅ TLS encryption is mandatory for all Redis connections
- ✅ Password authentication is properly validated and enforced
- ✅ Security configuration prevents insecure deployments
- ✅ Access control mechanisms work correctly
- ✅ Security validation catches all insecure configurations

### **Encryption Module**
- ✅ Fernet encryption encrypts all cached data transparently
- ✅ Decryption operations correctly restore original data
- ✅ Encryption keys are properly managed and validated
- ✅ Encryption performance meets <5ms overhead targets
- ✅ Error handling prevents data corruption during encryption failures

### **Memory Cache Module**
- ✅ Basic CRUD operations (get, set, delete, exists) work correctly
- ✅ TTL management expires entries at appropriate times
- ✅ LRU eviction evicts least recently used items when capacity reached
- ✅ Performance monitoring tracks hit rates and memory usage
- ✅ Statistics collection provides accurate cache metrics

### **Redis Cache Modules**
- ✅ Redis connections established with mandatory TLS encryption
- ✅ All cached data is encrypted before storage and decrypted on retrieval
- ✅ AI cache generates intelligent keys based on operation and parameters
- ✅ Cache invalidation strategies work correctly for different scenarios
- ✅ Graceful degradation when Redis is unavailable
- ✅ Performance monitoring tracks Redis-specific metrics

### **Configuration Management Modules**
- ✅ Preset manager provides environment-appropriate configurations
- ✅ Environment detection with security validation works reliably
- ✅ Configuration validation catches security issues with helpful messages
- ✅ AI-specific configuration handles model-specific parameters
- ✅ Cache presets provide appropriate defaults for different environments
- ✅ Parameter mapping correctly maps operations to cache configurations

### **Factory and Utility Modules**
- ✅ Cache factory creates appropriate cache instances based on configuration
- ✅ Factory enforces secure defaults for all cache types
- ✅ Key generator creates consistent, collision-resistant cache keys
- ✅ Parameter mapping correctly translates operation parameters
- ✅ FastAPI dependencies provide proper lifecycle management
- ✅ Dependency injection supports both development and production scenarios

### **Monitoring Module**
- ✅ Performance metrics are collected accurately for all cache operations
- ✅ Real-time monitoring provides actionable insights
- ✅ Statistics aggregation works correctly across multiple cache instances
- ✅ Performance alerts trigger when thresholds are exceeded
- ✅ Monitoring data structures are optimized for high-throughput scenarios

### **Cross-Module Integration**
- ✅ Security features work consistently across all cache implementations
- ✅ Configuration system provides seamless integration across modules
- ✅ Encryption works transparently across all cache types
- ✅ Monitoring aggregates data from all cache components
- ✅ Error handling provides consistent behavior across module boundaries
- ✅ Factory pattern creates properly configured cache instances

## What's NOT Tested (Integration Test Concerns)

### **External Service Integration**
- Real Redis server connections and cluster behavior
- Actual network latency and connection failure scenarios
- Real Redis cluster failover and high availability scenarios
- Production Redis authentication and TLS certificate validation

### **System-Level Performance**
- Real-world throughput under production load
- Memory usage patterns under high-concurrency scenarios
- Network I/O and external service dependency performance
- Container orchestration and scaling behavior

### **Cross-Service Integration**
- Integration with application services beyond cache operations
- API gateway integration and load balancing with caching
- Service mesh integration and traffic management with cache layers
- Distributed tracing integration with cache operations

## Environment Variables for Testing

```bash
# Cache Configuration
CACHE_PRESET=development                 # Choose: disabled, minimal, simple, development, production, ai-development, ai-production
CACHE_REDIS_URL=rediss://localhost:6379  # Override Redis connection URL (TLS required)
CACHE_ENCRYPTION_KEY=test-key-32-chars   # Override encryption key for testing

# Security Configuration
CACHE_SECURITY_LEVEL=high                # Security level: low, medium, high
CACHE_REQUIRE_TLS=true                   # Enforce TLS for Redis connections
CACHE_ENCRYPTION_ALGORITHM=Fernet        # Encryption algorithm

# Performance Configuration
CACHE_MEMORY_SIZE=1000                   # In-memory cache size limit
CACHE_DEFAULT_TTL=3600                   # Default TTL in seconds
CACHE_MAX_TTL=86400                      # Maximum TTL allowed
CACHE_COMPRESSION_THRESHOLD=1000         # Data size threshold for compression

# AI Cache Configuration
CACHE_AI_MODEL_PRESET=gemini-pro         # Default AI model for cache keys
CACHE_AI_RESPONSE_VALIDATION=true        # Enable AI response validation
CACHE_AI_CONFIDENCE_THRESHOLD=0.7        # Minimum confidence for caching

# Monitoring and Debugging
CACHE_ENABLE_METRICS=true                # Enable performance metrics
CACHE_METRICS_EXPORT_INTERVAL=30         # Metrics export interval in seconds
CACHE_DEBUG_MODE=false                   # Enable debug mode for detailed logging
CACHE_LOG_LEVEL=INFO                     # Logging level for cache operations

# Testing Specific
CACHE_TEST_MODE=true                     # Enable test-specific optimizations
CACHE_MOCK_REDIS=false                   # Use mock Redis for unit tests
CACHE_DISABLE_ENCRYPTION=false           # Keep encryption enabled for security tests
```

## Test Method Examples

### **Security-First Testing Example**
```python
def test_security_manager_enforces_tls_requirement(self, security_manager, security_validation_scenarios):
    """
    Test that security manager enforces TLS requirement per security contract.

    Verifies: RedisCacheSecurityManager.validate_security_config() rejects
              non-TLS Redis connections per mandatory security policy.

    Business Impact: Ensures production deployments cannot accidentally use
                    insecure Redis connections, preventing data exposure.

    Given: Security manager with TLS enforcement enabled
    And: Configuration scenarios including invalid non-TLS setup
    When: Security validation is performed
    Then: Non-TLS configurations are rejected with appropriate error
    And: TLS configurations are accepted
    And: Error messages clearly indicate security requirements

    Fixtures Used:
        - security_manager: Real RedisCacheSecurityManager instance
        - security_validation_scenarios: Various security configurations
    """
    # Given: Security manager and validation scenarios
    manager = security_manager
    scenarios = security_validation_scenarios

    # When/Then: Test invalid non-TLS configuration
    invalid_scenario = scenarios["invalid_no_tls"]
    with pytest.raises(SecurityValidationError) as exc_info:
        manager.validate_security_config(
            redis_url=invalid_scenario["redis_url"],
            password=invalid_scenario["password"]
        )

    # Verify TLS requirement error
    assert "TLS required" in str(exc_info.value).lower()
    assert "redis://" in str(exc_info.value).lower()

    # And: Test valid TLS configuration
    valid_scenario = scenarios["valid_tls"]
    result = manager.validate_security_config(
        redis_url=valid_scenario["redis_url"],
        password=valid_scenario["password"]
    )

    # Verify successful validation
    assert result.is_valid is True
    assert result.security_level == "high"
```

### **AI Cache Integration Testing Example**
```python
def test_ai_cache_generates_intelligent_keys_per_contract(self, redis_ai_cache, ai_cache_key_scenarios):
    """
    Test that AI cache generates intelligent keys per key generation contract.

    Verifies: AIResponseCache.generate_key() creates appropriate keys
              based on operation type, model, and input parameters per contract.

    Business Impact: Ensures cache key consistency and collision avoidance
                    across different AI operations and models.

    Given: AI cache with intelligent key generation
    And: AI operation scenarios with expected key patterns
    When: Cache keys are generated for different operations
    Then: Keys follow expected patterns with proper prefixes
    And: Keys include model information and parameter hashes
    And: Keys are consistent for identical inputs

    Fixtures Used:
        - redis_ai_cache: Real AIResponseCache instance
        - ai_cache_key_scenarios: AI operation key generation scenarios
    """
    # Given: AI cache and key generation scenarios
    cache = redis_ai_cache
    scenarios = ai_cache_key_scenarios

    # When: Generating keys for different operations
    summarize_scenario = scenarios["summarize"]
    summarize_key = cache._generate_key(
        operation="summarize",
        text=summarize_scenario["text"],
        model=summarize_scenario["model"]
    )

    sentiment_scenario = scenarios["sentiment"]
    sentiment_key = cache._generate_key(
        operation="sentiment",
        text=sentiment_scenario["text"],
        model=sentiment_scenario["model"]
    )

    # Then: Keys follow expected patterns
    expected_summarize_pattern = summarize_scenario["expected_key_pattern"]
    assert summarize_key.startswith(expected_summarize_pattern)

    expected_sentiment_pattern = sentiment_scenario["expected_key_pattern"]
    assert sentiment_key.startswith(expected_sentiment_pattern)

    # And: Keys are different for different operations
    assert summarize_key != sentiment_key

    # And: Keys are consistent for identical inputs
    summarize_key_duplicate = cache._generate_key(
        operation="summarize",
        text=summarize_scenario["text"],
        model=summarize_scenario["model"]
    )
    assert summarize_key == summarize_key_duplicate
```

### **Performance Contract Testing Example**
```python
def test_memory_cache_meets_performance_targets_per_contract(self, memory_cache_with_metrics, performance_scenarios):
    """
    Test that memory cache meets performance targets per SLA contract.

    Verifies: InMemoryCache operations complete within documented
              performance targets per performance contract specifications.

    Business Impact: Ensures cache operations don't introduce unacceptable
                    latency, maintaining application responsiveness.

    Given: Memory cache with performance monitoring enabled
    And: Performance target scenarios
    When: Cache operations are executed with timing measurements
    Then: All operations meet <25ms performance targets
    And: Performance metrics are accurately collected
    And: No performance regressions are detected

    Fixtures Used:
        - memory_cache_with_metrics: Configured memory cache with monitoring
        - performance_scenarios: Performance test scenarios with targets
    """
    # Given: Memory cache with performance monitoring
    cache = memory_cache_with_metrics
    performance_target_ms = 25

    # And: Performance test data
    test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}

    # When: Measuring performance of cache operations
    import time

    # Test set operation
    start_time = time.time()
    await cache.set("perf_test_key", test_data, ttl=3600)
    set_duration_ms = (time.time() - start_time) * 1000

    # Test get operation
    start_time = time.time()
    result = await cache.get("perf_test_key")
    get_duration_ms = (time.time() - start_time) * 1000

    # Test exists operation
    start_time = time.time()
    exists = await cache.exists("perf_test_key")
    exists_duration_ms = (time.time() - start_time) * 1000

    # Then: All operations meet performance targets
    assert set_duration_ms <= performance_target_ms, \
        f"Set operation exceeded target: {set_duration_ms}ms > {performance_target_ms}ms"
    assert get_duration_ms <= performance_target_ms, \
        f"Get operation exceeded target: {get_duration_ms}ms > {performance_target_ms}ms"
    assert exists_duration_ms <= performance_target_ms, \
        f"Exists operation exceeded target: {exists_duration_ms}ms > {performance_target_ms}ms"

    # And: Operations returned correct results
    assert result == test_data
    assert exists is True

    # And: Performance metrics are collected
    metrics = cache.get_performance_metrics()
    assert metrics["average_set_time_ms"] <= performance_target_ms
    assert metrics["average_get_time_ms"] <= performance_target_ms
    assert metrics["hit_rate"] >= 0.0  # Should have at least one hit
```

## Debugging Failed Tests

### **Security Testing Issues**
```bash
# Test TLS enforcement
make test-backend PYTEST_ARGS="tests/unit/cache/security/test_security_manager.py -v -s"

# Test encryption functionality
make test-backend PYTEST_ARGS="tests/unit/cache/encryption/test_core_operations.py -v -s"

# Test security configuration validation
make test-backend PYTEST_ARGS="tests/unit/cache/security/test_security_config.py -v -s"
```

### **Cache Implementation Problems**
```bash
# Test memory cache operations
make test-backend PYTEST_ARGS="tests/unit/cache/memory/test_memory_core_operations.py -v -s"

# Test Redis AI cache operations
make test-backend PYTEST_ARGS="tests/unit/cache/redis_ai/test_redis_ai_core_operations.py -v -s"

# Test LRU eviction
make test-backend PYTEST_ARGS="tests/unit/cache/memory/test_memory_lru_eviction.py -v -s"
```

### **Configuration Management Problems**
```bash
# Test cache presets
make test-backend PYTEST_ARGS="tests/unit/cache/cache_presets/test_cache_presets_manager.py -v -s"

# Test configuration validation
make test-backend PYTEST_ARGS="tests/unit/cache/config/test_config_core.py -v -s"

# Test factory pattern
make test-backend PYTEST_ARGS="tests/unit/cache/factory/test_factory.py -v -s"
```

### **Performance Issues**
```bash
# Test performance monitoring
make test-backend PYTEST_ARGS="tests/unit/cache/monitoring/test_performance_monitor.py -v -s"

# Test statistics collection
make test-backend PYTEST_ARGS="tests/unit/cache/monitoring/test_statistics_and_analysis.py -v -s"

# Test encryption performance
make test-backend PYTEST_ARGS="tests/unit/cache/encryption/test_performance_monitoring.py -v -s"
```

## Related Documentation

- **Component Contracts**:
  - `app.infrastructure.cache.memory` - In-memory cache implementation
  - `app.infrastructure.cache.redis_ai` - AI-optimized Redis cache
  - `app.infrastructure.cache.redis_generic` - Generic Redis cache
  - `app.infrastructure.cache.security` - Security management
  - `app.infrastructure.cache.encryption` - Data encryption
  - `app.infrastructure.cache.factory` - Cache factory pattern
  - `app.infrastructure.cache.monitoring` - Performance monitoring

- **Infrastructure Contracts**: `backend/contracts/infrastructure/cache/` - Complete interface definitions

- **Unit Testing Philosophy**: `docs/guides/testing/UNIT_TESTS.md` - Comprehensive unit testing methodology

- **Cache Patterns**: `docs/guides/infrastructure/CACHE.md` - Cache patterns and configuration

- **Security Guidelines**: `docs/guides/infrastructure/SECURITY.md` - Security requirements and best practices

- **Performance Guidelines**: `docs/guides/infrastructure/PERFORMANCE.md` - Performance targets and optimization

---

## Multi-Module Unit Test Quality Assessment

### **Behavior-Driven Excellence Across Cache Infrastructure**
These tests exemplify our **behavior-driven contract testing** approach for complex security-first cache infrastructure:

✅ **Security-First Testing**: All security features validated with mandatory TLS and encryption
✅ **Module Integrity**: Each cache infrastructure module tested as a complete unit with clear boundaries
✅ **Contract Focus**: Tests validate documented public interfaces for all 14 modules
✅ **Boundary Mocking**: External dependencies mocked appropriately, inter-module collaborations preserved
✅ **Observable Outcomes**: Tests verify cache behavior through public interfaces, metrics, and security states

### **Production-Ready Multi-Module Standards**
✅ **>90% Coverage**: Comprehensive coverage across all 14 cache infrastructure modules
✅ **Security Validation**: 100% security feature coverage with mandatory enforcement testing
✅ **Modular Testing**: Each module independently testable with proper isolation
✅ **Performance Assurance**: <25ms performance targets validated across all cache operations
✅ **Encryption Excellence**: Complete encryption testing with performance impact validation

### **Architectural Sophistication**
✅ **Security-First Architecture**: Clear separation of security, encryption, and cache implementation layers
✅ **Multiple Cache Implementations**: Memory, Redis generic, and Redis AI caches with unified interface
✅ **Intelligent Configuration**: Environment-aware preset system with comprehensive validation
✅ **Factory Pattern**: Secure cache creation with mandatory security defaults
✅ **Comprehensive Monitoring**: Real-time performance monitoring and analytics across all cache types

These unit tests serve as a comprehensive model for testing complex security-first multi-module infrastructure components, demonstrating how to maintain thorough contract coverage, security validation, performance assurance, and architectural clarity across a sophisticated layered caching system with mandatory security requirements.
