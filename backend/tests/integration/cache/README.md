# Cache Infrastructure Integration Tests

Integration tests for comprehensive cache infrastructure validation following our **small, dense suite with maximum confidence** philosophy. These tests validate the complete chain from factory assembly through security configuration, encryption pipelines, performance monitoring, and API management across all cache-critical infrastructure components.

## Test Organization

### Critical Integration Seams (9 Test Files, 5,048 Lines Total)

#### **CORE INFRASTRUCTURE INTEGRATION** (Foundation for cache validation)

1. **`test_cache_integration.py`** (FOUNDATION) - **684 lines across 4 comprehensive test classes**
   - Cache Factory Integration → Settings Configuration → Component Assembly
   - Cache Key Generator Integration → Performance Monitoring → Cache Operations
   - End-to-End Cache Workflows → AI Cache Patterns → Fallback Behavior
   - Cache Component Interoperability → Shared Contracts → Behavioral Equivalence
   - Tests factory assembly, key generation, complete workflows, contract compliance
   - **Special Infrastructure**: Secure Redis testcontainer with TLS authentication and encryption

2. **`test_cache_preset_behavior.py`** (CORE CONFIGURATION)
   - Preset-Driven Behavioral Differences → Configuration Application → Observable Behavior
   - Graceful Degradation → Redis Fallback → InMemoryCache Activation
   - Configuration Parameter Acceptance → Factory Method Validation → Error Handling
   - Testing Cache Isolation → Multi-Instance Behavior → Resource Management
   - Tests meaningful distinctions between presets, fallback behavior, configuration validation

#### **SECURITY AND ENCRYPTION INTEGRATION** (Security-critical infrastructure)

3. **`test_cache_encryption.py`** (HIGHEST PRIORITY) - **974 lines across 3 comprehensive test classes**
   - Complete Encryption Pipeline → JSON Serialization → Fernet Encryption → Redis Storage
   - Redis Integration with Encryption → Encrypted Data Validation → Decryption Verification
   - Performance Testing → Large Dataset Encryption → Threshold Validation
   - Concurrent Operations → Thread Safety → Data Integrity Under Load
   - Backward Compatibility → Legacy Data Handling → Migration Support
   - Environment Configuration → Key Management → Security Validation
   - Tests end-to-end encryption, performance, concurrency, backward compatibility

4. **`test_encryption_dependency_integration.py`** (SPECIALIZED) - **380 lines**
   - Cryptography Library Dependency → Import Validation → Graceful Degradation
   - Error Classification → Import vs Configuration Errors → Proper Handling
   - Error Message Quality → Installation Instructions → Actionable Guidance
   - Security-First Architecture → Silent Failure Prevention → Error Visibility
   - Tests missing dependency handling, error classification, security-first behavior

5. **`test_encryption_end_to_end_workflows.py`** (HIGHEST PRIORITY) - **663 lines**
   - Complete AI Cache Workflows → API Endpoints → Encrypted Storage → Monitoring
   - Cache Invalidation with Encryption → Pattern-Based Cleanup → Security Preservation
   - Health Check Integration → Encryption Status → Monitoring Integration
   - Performance Monitoring Integration → Encryption Metrics → Overall Performance
   - Multi-Cache Isolation → Cross-Cache Encryption → Security Boundaries
   - Error Handling Workflows → Encryption-Specific Scenarios → Recovery Patterns
   - Security Validation → Data Protection Verification → Confidentiality Assurance
   - Configuration Workflows → Environment-Specific Initialization → Production Readiness
   - Monitoring Workflows → Performance/Security Metrics → Operational Visibility
   - Tests complete workflows, security validation, monitoring integration

6. **`test_encryption_factory_integration.py`** (HIGH PRIORITY) - **655 lines**
   - Factory Method Integration → Web/AI/Testing Methods → Encryption Application
   - Configuration-Based Creation → JSON Configuration → Encryption Integration
   - Error Handling → Invalid Encryption Keys → Security Validation
   - Memory Fallback → Encryption with InMemoryCache → Degradation Support
   - AI-Specific Features → Operation-Specific TTLs → Encryption Enhancement
   - Isolation Testing → Multi-Cache Encryption → Security Boundaries
   - Tests factory encryption integration, security validation, AI features

7. **`test_cache_security.py`** (HIGH PRIORITY) - **600 lines**
   - Security Configuration Integration → AUTH/ACL/TLS → Security Application
   - Cache Factory Security Integration → Security Config → Cache Types
   - Security Validation → Authentication → Connection Security
   - Error Handling → Invalid Configuration → Security Enforcement
   - Configuration-Based Security → JSON Configuration → Security Settings
   - Tests comprehensive security configuration, authentication, TLS integration

#### **LIFECYCLE AND DEPENDENCY INTEGRATION** (System reliability)

8. **`test_cache_lifecycle_health.py`** (HIGH PRIORITY) - **436 lines**
   - Health Check Dependencies → Connected/Disconnected Cache → Status Assessment
   - Cleanup Dependencies → Registry Management → Resource Cleanup
   - Dependency Manager Integration → FastAPI DI System → Service Integration
   - Comprehensive Reporting → Diagnostic Information → Operational Visibility
   - Tests lifecycle management, health monitoring, resource cleanup

#### **API MANAGEMENT INTEGRATION** (Administrative control)

9. **`test_cache_mgmt_api.py`** (MEDIUM PRIORITY) - **295 lines**
   - HTTP-to-Cache Stack Validation → Complete API-to-Backend Testing
   - Cache Invalidation Workflow → Pattern-Based Invalidation → Cleanup Validation
   - Metrics Accuracy Verification → Real Operation Tracking → Performance Data
   - API Contract Validation → Response Structure → Interface Compliance
   - Tests API integration patterns, administrative control, contract validation

## Testing Philosophy Applied

- **Outside-In Testing**: All tests start from public interfaces and validate observable system behavior
- **High-Fidelity Infrastructure**: Real Redis containers with TLS, encryption, authentication, not mocked databases
- **Behavior Focus**: Cache factory responses, encryption integrity, security enforcement, not internal cache logic
- **No Internal Mocking**: Tests real cache collaboration across all infrastructure components
- **Contract Validation**: Ensures compliance with cache interface contracts across all implementations
- **Production-Grade Security**: Real TLS certificates, encryption keys, and security validation
- **Performance Rigor**: Real performance thresholds and comprehensive metrics collection
- **Concurrent Operation Testing**: Thread safety and data integrity validation under load

## Special Test Infrastructure Requirements

### **Secure Redis Testcontainer**
**Mandatory Infrastructure**: Real Redis container with TLS, authentication, and encryption
- **TLS Configuration**: Self-signed certificates for secure connection testing
- **Authentication**: Password-based Redis authentication validation
- **Encryption**: Real encryption key management and validation
- **Network Isolation**: Container-based isolation for test independence

### **Performance Monitoring Infrastructure**
- **Real-Time Metrics**: Performance tracking with configurable thresholds
- **Threshold Validation**: <5ms for small datasets, <50ms for large datasets
- **Concurrent Testing**: 20 concurrent operations for thread safety validation
- **Metrics Collection**: Comprehensive performance and security metrics

### **Security Testing Infrastructure**
- **Cryptography Dependency**: Real cryptography library integration testing
- **Key Management**: Environment-based and generated key validation
- **Certificate Management**: TLS certificate creation and validation
- **Security Configuration**: AUTH, ACL, TLS configuration testing

## Running Tests

```bash
# Run all cache integration tests
make test-backend PYTEST_ARGS="tests/integration/cache/ -v"

# Run by test category
make test-backend PYTEST_ARGS="tests/integration/cache/ -v -k 'integration'"
make test-backend PYTEST_ARGS="tests/integration/cache/ -v -k 'encryption'"
make test-backend PYTEST_ARGS="tests/integration/cache/ -v -k 'security'"
make test-backend PYTEST_ARGS="tests/integration/cache/ -v -k 'lifecycle'"
make test-backend PYTEST_ARGS="tests/integration/cache/ -v -k 'preset'"
make test-backend PYTEST_ARGS="tests/integration/cache/ -v -k 'factory'"

# Run specific test files
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_integration.py -v"
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py -v"
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_security.py -v"
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_lifecycle_health.py -v"
make test-backend PYTEST_ARGS="tests/integration/cache/test_encryption_end_to_end_workflows.py -v"

# Run specific test classes
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_integration.py::TestCacheFactoryIntegration -v"
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionPipelineEndToEndIntegration -v"
make test-backend PYTEST_ARGS="tests/integration/cache/test_encryption_end_to_end_workflows.py::TestEncryptedCacheEndToEndWorkflows -v"

# Run with coverage
make test-backend PYTEST_ARGS="tests/integration/cache/ --cov=app.infrastructure.cache"

# Run performance-focused tests
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionPerformanceIntegration -v"

# Run concurrent operation tests
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionConcurrentOperationsIntegration -v"
```

## Test Fixtures

### **Cache Infrastructure**
- **`secure_redis_cache`**: Real Redis cache instance with TLS and authentication
- **`cache_factory`**: Complete CacheFactory instance with configuration management
- **`performance_monitor`**: Real performance monitoring with metrics collection
- **`cache_with_monitoring`**: Cache instance with integrated performance monitoring

### **Security and Encryption**
- **`encryption_layer`**: Complete encryption layer with generated keys
- **`security_config`**: Comprehensive security configuration (AUTH, TLS, encryption)
- **`tls_certificates`**: TLS certificate management for secure connections
- **`encryption_keys`**: Various encryption key configurations for testing

### **Configuration and Environment**
- **`cache_settings`**: Real Settings instance with cache configuration
- **`cache_preset_manager`**: Preset-based configuration management
- **`environment_config`**: Environment-specific configuration testing
- **`json_configuration`**: JSON-based configuration validation

### **Application Integration**
- **`test_app`**: FastAPI application with cache dependencies
- **`cache_dependencies`**: FastAPI dependency injection for cache services
- **`health_checker`**: Health check integration for cache services
- **`cleanup_dependency`**: Cache cleanup and lifecycle management

## Success Criteria

### **Cache Factory Integration**
- ✅ CacheFactory creates appropriate cache types for different application scenarios (web, AI, testing)
- ✅ Factory assembly respects security configuration and applies it correctly to cache instances
- ✅ Factory handles Redis connection failures gracefully with InMemoryCache fallback
- ✅ Factory creates isolated cache instances for testing scenarios with proper database isolation
- ✅ Factory assembly completes within performance SLAs (<500ms for cache creation)
- ✅ Factory properly integrates performance monitoring components during cache assembly

### **Cache Encryption Integration**
- ✅ Complete round-trip encryption/decryption preserves data integrity for all JSON-serializable data types
- ✅ Encrypted data stored in Redis is properly encrypted and cannot be read without decryption
- ✅ Large datasets (>1KB, >10KB, >100KB) are encrypted and decrypted within performance thresholds
- ✅ Concurrent encrypt/decrypt operations work correctly without data corruption (20 concurrent tasks)
- ✅ Backward compatibility fallback correctly handles legacy unencrypted data with appropriate warnings
- ✅ Environment-based encryption configuration works correctly across different deployment environments
- ✅ Encryption performance overhead is within acceptable limits (<5ms for small datasets)

### **Cache Security Integration**
- ✅ Security configuration properly enables Redis authentication with password-based auth
- ✅ Security configuration correctly enables TLS encryption for Redis connections
- ✅ CacheFactory integrates security configuration into cache instances without breaking functionality
- ✅ Secure Redis connections work correctly with TLS certificates and certificate verification
- ✅ Security configuration errors are detected and reported appropriately during cache creation
- ✅ Cache security integrates correctly with environment-based configuration loading

### **Cache Lifecycle and Health Integration**
- ✅ Health check dependency accurately reports healthy status for functional cache instances
- ✅ Health check detects and reports degraded status for problematic cache connections
- ✅ Health check provides comprehensive diagnostic information for troubleshooting cache issues
- ✅ Cache cleanup dependency properly disconnects active cache connections during shutdown
- ✅ Cache registry is properly cleared during application lifecycle cleanup
- ✅ Health check performance meets acceptable response time requirements (<100ms)

### **Cache Preset Behavior Integration**
- ✅ Cache preset manager provides appropriate configurations for different environments
- ✅ Preset configurations result in observable behavioral differences between cache instances
- ✅ Environment detection correctly triggers appropriate cache preset selection
- ✅ Preset configurations are properly applied by CacheFactory during cache creation
- ✅ Graceful degradation maintains service continuity with appropriate fallback behavior
- ✅ Preset system handles missing or invalid configurations gracefully

### **Cache Management API Integration**
- ✅ Cache management API endpoints correctly implement cache invalidation with pattern matching
- ✅ Cache metrics API provides accurate and comprehensive cache performance data
- ✅ Cache status API provides detailed infrastructure status and diagnostic information
- ✅ API authentication properly controls access to cache management endpoints
- ✅ Cache management operations work correctly across different cache implementations

### **End-to-End Cache Workflows Integration**
- ✅ Complete AI cache workflow with encrypted key generation, storage, retrieval, and monitoring integration
- ✅ Cache invalidation workflows work with encrypted data patterns and security preservation
- ✅ Health check workflows include encryption status reporting and diagnostic information
- ✅ Performance monitoring includes encryption metrics in overall cache performance tracking
- ✅ Multi-cache workflows maintain encryption isolation across different cache types
- ✅ Error handling workflows include encryption-specific error scenarios and recovery patterns

### **Cache Component Interoperability**
- ✅ All cache implementations provide identical behavior for basic cache operations (get, set, exists, delete)
- ✅ Cache implementations handle TTL (time-to-live) behavior consistently across all types
- ✅ Different cache implementations preserve data integrity for various Python data types
- ✅ Cache interface compliance is maintained across all implementations
- ✅ Cache implementations provide consistent error handling and behavior patterns

## What's NOT Tested (Unit Test Concerns)

### **Internal Cache Implementation**
- Individual cache storage algorithms and data structures
- Internal Redis connection pooling and management
- Private method behavior in individual cache implementations
- Specific serialization/deserialization algorithms and optimizations

### **Internal Security Implementation**
- Individual cryptographic operations and key management algorithms
- Internal TLS/SSL handshake and secure channel establishment
- Certificate authority validation and certificate chain verification
- Internal authentication token generation and validation

### **Internal Performance Monitoring**
- Individual performance metric collection algorithms
- Internal timing and measurement implementations
- Private method behavior in performance monitoring systems
- Specific metrics storage and retrieval optimizations

### **Infrastructure Internal Operations**
- Redis container internal operations and networking
- Docker container runtime environment and configuration
- Container build process and dependency installation
- Testcontainer internal lifecycle management

## Environment Variables for Testing

```bash
# Cache Configuration
CACHE_PRESET=development                 # Choose: disabled, minimal, simple, development, production, ai-development, ai-production
CACHE_REDIS_URL=redis://localhost:6379   # Override Redis connection URL
ENABLE_AI_CACHE=true                     # Toggle AI cache features

# Security Configuration
REDIS_ENCRYPTION_KEY=your-encryption-key-32-chars-long
REDIS_AUTH=password                      # Redis authentication password
REDIS_TLS_CERT_PATH=/path/to/certificate.pem
REDIS_TLS_KEY_PATH=/path/to/private.key

# Testing Configuration
CACHE_TESTING_USE_MEMORY_CACHE=false     # Toggle memory cache for testing
CACHE_TESTING_FAIL_ON_CONNECTION_ERROR=true  # Toggle connection error handling
CACHE_PERFORMANCE_MONITORING=true        # Toggle performance monitoring

# Complex Configuration Testing
CACHE_CUSTOM_CONFIG='{"compression_threshold": 500, "memory_cache_size": 2000}'

# Environment-Specific Testing
ENVIRONMENT=development                  # Choose: development, testing, staging, production
API_KEY=test-api-key-12345

# Security Testing
REDIS_SECURITY_REQUIRE_TLS=true          # Toggle TLS requirements
REDIS_SECURITY_ALLOW_INSECURE_DEVELOPMENT=false
```

## Integration Points Tested

### **Cache Factory Assembly Seam**
- CacheFactory → GenericRedisCache/AIResponseCache/InMemoryCache → Service Deployment
- Security Configuration Integration → Cache Creation → Secure Redis Connection
- Performance Monitoring Integration → Cache Operations → Metrics Collection

### **Encryption Pipeline Seam**
- Application Data → JSON Serialization → Fernet Encryption → Redis Storage
- Redis Retrieval → Fernet Decryption → JSON Deserialization → Application Data
- Environment Configuration → Key Management → Encryption Layer Creation

### **Security Configuration Seam**
- SecurityConfig → CacheFactory → Redis TLS/Auth → Secure Operations
- Environment Variables → Security Configuration → Cache Application
- Certificate Management → TLS Configuration → Secure Connection Establishment

### **Health Check Dependencies Seam**
- Health Check Request → Cache Status Assessment → Health Response
- Cache Instance Monitoring → Performance Metrics → Health Classification
- Diagnostic Information → Error Detection → Operational Guidance

### **API Management Seam**
- Administrative Request → API Authentication → Cache Operation → Administrative Response
- Cache Invalidation → Pattern Matching → Selective Cleanup → Security Preservation
- Metrics Collection → Performance Data → API Response → Operational Visibility

### **Preset Configuration Seam**
- Environment Detection → Preset Selection → Configuration Application → Cache Behavior
- Configuration Management → Parameter Validation → Factory Application → Observable Behavior
- Graceful Degradation → Redis Failure → InMemoryCache Fallback → Service Continuity

### **Lifecycle Management Seam**
- Application Startup → Cache Initialization → Service Registration → Operational State
- Application Shutdown → Cache Cleanup → Resource Release → Clean Termination
- Registry Management → Cache Instance Tracking → Dependency Resolution → Lifecycle Integration

## Performance Expectations

- **Cache Factory Assembly**: <500ms for complete cache creation and configuration
- **Cache Encryption Operations**: <5ms for small datasets (<1KB), <50ms for large datasets (>10KB)
- **Cache Basic Operations**: <10ms for get/set operations with Redis backend
- **Cache Health Checks**: <100ms for complete health status assessment
- **Cache Management APIs**: <200ms for administrative operations and metrics collection
- **Concurrent Operations**: 20 concurrent operations without data corruption or performance degradation
- **Graceful Degradation**: <100ms for Redis failure detection and InMemoryCache fallback activation
- **Performance Monitoring Overhead**: <5% overhead for cache operations with monitoring enabled

## Debugging Failed Tests

### **Cache Factory Integration Issues**
```bash
# Test factory creation methods
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_integration.py::TestCacheFactoryIntegration::test_factory_creates_appropriate_cache_types -v -s"

# Test key generator integration
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_integration.py::TestCacheKeyGeneratorIntegration::test_key_generator_with_monitoring_integration -v -s"

# Test end-to-end workflows
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_integration.py::TestEndToEndCacheWorkflows::test_complete_ai_cache_workflow -v -s"
```

### **Cache Encryption Integration Problems**
```bash
# Test encryption pipeline integrity
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionPipelineEndToEndIntegration::test_encryption_round_trip_preserves_data_integrity -v -s"

# Test Redis integration with encryption
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionRedisIntegration::test_encrypted_data_storage_and_retrieval_through_redis -v -s"

# Test concurrent operations
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionConcurrentOperationsIntegration::test_concurrent_encrypt_decrypt_operations_maintain_data_integrity -v -s"

# Test backward compatibility
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionBackwardCompatibilityIntegration::test_decryption_of_unencrypted_json_data_succeeds_with_fallback -v -s"
```

### **Cache Security Integration Failures**
```bash
# Test security configuration integration
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_security.py::TestCacheSecurityIntegration::test_security_configuration_integration -v -s"

# Test factory security integration
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_security.py::TestCacheFactorySecurityIntegration::test_factory_applies_security_configuration_to_cache_instances -v -s"

# Test authentication and TLS
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_security.py::TestCacheSecurityValidation::test_redis_authentication_security_enforcement -v -s"
```

### **Cache Lifecycle and Health Issues**
```bash
# Test health check dependencies
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_lifecycle_health.py::TestCacheLifecycleHealth::test_health_check_dependency_provides_comprehensive_diagnostic_information -v -s"

# Test cleanup dependencies
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_lifecycle_health.py::TestCacheLifecycleHealth::test_cleanup_dependency_handles_registry_cleanup_during_shutdown -v -s"

# Test dependency manager integration
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_lifecycle_health.py::TestCacheLifecycleHealth::test_dependency_manager_integration_with_fastapi_di_system -v -s"
```

### **Cache Preset Behavior Problems**
```bash
# Test preset behavioral differences
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_preset_behavior.py::TestCachePresetBehavior::test_preset_driven_behavioral_differences -v -s"

# Test graceful degradation
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_preset_behavior.py::TestCachePresetBehavior::test_graceful_degradation_maintains_service_continuity -v -s"

# Test configuration parameter acceptance
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_preset_behavior.py::TestCachePresetBehavior::test_configuration_parameter_acceptance -v -s"
```

### **Cache Management API Issues**
```bash
# Test API integration patterns
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_mgmt_api.py::TestCacheManagementAPIIntegration::test_http_to_cache_stack_validation -v -s"

# Test cache invalidation workflow
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_mgmt_api.py::TestCacheManagementAPIIntegration::test_cache_invalidation_workflow -v -s"

# Test metrics accuracy
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_mgmt_api.py::TestCacheManagementAPIIntegration::test_metrics_accuracy_verification -v -s"
```

### **End-to-End Workflow Issues**
```bash
# Test complete AI cache workflows
make test-backend PYTEST_ARGS="tests/integration/cache/test_encryption_end_to_end_workflows.py::TestEncryptedCacheEndToEndWorkflows::test_complete_ai_cache_workflow_with_encryption -v -s"

# Test cache invalidation with encryption
make test-backend PYTEST_ARGS="tests/integration/cache/test_encryption_end_to_end_workflows.py::TestEncryptedCacheEndToEndWorkflows::test_cache_invalidation_with_encryption -v -s"

# Test health check integration
make test-backend PYTEST_ARGS="tests/integration/cache/test_encryption_end_to_end_workflows.py::TestEncryptedCacheEndToEndWorkflows::test_health_check_integration_with_encryption -v -s"
```

## Test Architecture

These integration tests follow our **behavior-focused testing** principles:

1. **Test Critical Paths**: Focus on high-value cache workflows essential to system performance, security, and operational reliability
2. **Trust Contracts**: Use cache interface contracts to define expected behavior patterns across implementations
3. **Test from Outside-In**: Start from public cache interfaces and validate observable system behavior
4. **Verify Integrations**: Test real cache collaboration across all infrastructure components
5. **Use Real Infrastructure**: Real Redis containers with TLS, encryption, and authentication for production-like validation

The tests ensure cache infrastructure provides reliable operational performance, maintains security through proper encryption, and preserves service continuity through graceful degradation patterns.

## Special Test Execution Requirements

### **Redis Container Testing**
**CRITICAL**: Tests require Redis container with TLS and authentication - standard Redis will not work
```bash
# ✅ CORRECT: Tests handle Redis container startup automatically
make test-backend PYTEST_ARGS="tests/integration/cache/ -v"

# ✅ CORRECT: Individual test files handle container requirements
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_integration.py -v"
```

**Why Redis Container Required**: Tests validate TLS, authentication, and encryption features that require real Redis infrastructure with proper security configuration.

### **Cryptography Library Testing**
**CRITICAL**: Tests require cryptography library for encryption functionality
```bash
# Ensure cryptography library is installed
pip install cryptography

# ✅ CORRECT: Tests validate real encryption behavior
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py -v"
```

**Why Cryptography Required**: Tests validate actual encryption/decryption behavior, not mocked or simulated encryption.

### **Performance Testing Requirements**
**CRITICAL**: Some tests have specific performance requirements that may be affected by system load
```bash
# Run performance tests in isolation for reliable results
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionPerformanceIntegration -v -s"
```

### **Concurrent Testing Requirements**
**CRITICAL**: Concurrent operation tests require proper thread management
```bash
# Run concurrent tests with appropriate threading support
make test-backend PYTEST_ARGS="tests/integration/cache/test_cache_encryption.py::TestEncryptionConcurrentOperationsIntegration -v -s"
```

## Related Documentation

- **Test Plan**: `TEST_PLAN.md` - Comprehensive cache integration test planning
- **Encryption Test Plan**: `TEST_PLAN_encryption.md` - Detailed encryption integration testing
- **Cache Implementation**: `backend/contracts/infrastructure/cache/` - Cache service contracts and interfaces
- **Encryption Implementation**: `backend/contracts/infrastructure/cache/encryption.pyi` - Encryption layer implementation
- **Cache Factory**: `backend/contracts/infrastructure/cache/factory.pyi` - Cache factory patterns
- **Integration Testing Philosophy**: `docs/guides/testing/INTEGRATION_TESTS.md` - Testing methodology and principles
- **Cache Configuration**: `docs/guides/infrastructure/CACHE.md` - Cache configuration and usage guidelines
- **Security Configuration**: `docs/guides/developer/SECURITY.md` - Security configuration and validation
- **Performance Monitoring**: `docs/guides/infrastructure/MONITORING.md` - Performance monitoring and metrics
- **App Factory Pattern**: `docs/guides/developer/APP_FACTORY_GUIDE.md` - Testing patterns for cache integration