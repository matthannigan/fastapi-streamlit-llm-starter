# Cache Encryption Integration Test Plan

## Overview

This test plan identifies integration test opportunities for the cache encryption infrastructure (`app.infrastructure.cache.encryption`). The encryption layer provides mandatory, always-on application-layer encryption for all cached data, serving as a critical security component that integrates with cache operations, configuration management, and performance monitoring systems.

## Critical Integration Points Identified

Based on analysis of `backend/contracts/infrastructure/cache/encryption.pyi` and the implementation, the encryption infrastructure integrates with:

### **Primary Integration Seams:**

1. **Encryption → Cache Storage/Retrieval Pipeline** - Full round-trip encryption/decryption with Redis operations
2. **Encryption → Configuration Management** - Environment-based key management and security configuration
3. **Encryption → Performance Monitoring** - Encryption overhead tracking and alerting
4. **Encryption → Data Serialization** - JSON serialization and binary conversion pipeline
5. **Encryption → Error Handling** - ConfigurationError propagation and security validation
6. **Encryption → Cryptography Library** - Fernet encryption dependency and graceful degradation
7. **Encryption → Key Rotation and Backward Compatibility** - Handling legacy unencrypted data

### **Integration Seams Discovered:**

| Seam | Components Involved | Critical Path | Priority |
|------|-------------------|---------------|-----------|
| **Encryption Pipeline Integration** | `EncryptedCacheLayer` → `encrypt_cache_data` → Redis → `decrypt_cache_data` → Application | Data storage → Encryption → Redis → Decryption → Data retrieval | HIGH |
| **Environment Configuration Integration** | `create_encryption_layer_from_env` → Environment variables → `EncryptedCacheLayer` | Environment loading → Key validation → Encryption initialization | HIGH |
| **Performance Monitoring Integration** | `EncryptedCacheLayer` → Performance tracking → Metrics collection | Operation execution → Performance tracking → Threshold monitoring | MEDIUM |
| **Error Handling Integration** | Encryption operations → `ConfigurationError` → Application error handling | Operation failure → Error creation → Error propagation | HIGH |
| **Key Management Integration** | `create_with_generated_key` → Key generation → Encryption layer | Key generation → Validation → Encryption setup | MEDIUM |
| **Backward Compatibility Integration** | `decrypt_cache_data` → Invalid token handling → Fallback to unencrypted | Decryption attempt → Token error → Fallback handling | MEDIUM |
| **Cryptography Library Integration** | Import validation → `CRYPTOGRAPHY_AVAILABLE` → Graceful degradation | Library check → Availability detection → Error handling | HIGH |

---

## INTEGRATION TEST PLAN

### 1. SEAM: Encryption Pipeline End-to-End Integration
**HIGH PRIORITY** - Security critical, affects all cached data protection and integrity

**COMPONENTS:** `EncryptedCacheLayer`, `encrypt_cache_data`, `decrypt_cache_data`, Redis cache operations, data serialization
**CRITICAL PATH:** Application data → JSON serialization → Fernet encryption → Redis storage → Redis retrieval → Fernet decryption → JSON deserialization → Application data
**BUSINESS IMPACT:** Ensures all cached data is properly encrypted at rest and can be reliably decrypted, protecting sensitive information

**TEST SCENARIOS:**
- Complete round-trip encryption/decryption preserves data integrity for various data types (strings, numbers, booleans, nested dicts, lists)
- Encrypted data stored in Redis is properly encrypted and cannot be read without decryption
- Decryption correctly recovers original data structure and values after Redis storage
- Large datasets (>1KB, >10KB, >100KB) are encrypted and decrypted correctly with acceptable performance
- Unicode and special characters are preserved through encryption/decryption pipeline
- Empty dictionaries and None values are handled correctly through encryption pipeline
- Nested data structures (lists of dicts, dicts of lists) maintain structure through encryption
- Binary data compatibility: encrypted data can be stored and retrieved from Redis as bytes
- Multiple sequential encrypt/decrypt operations maintain data consistency
- Concurrent encrypt/decrypt operations work correctly without data corruption

**INFRASTRUCTURE NEEDS:** Redis testcontainer or fakeredis, performance measurement tools, data validation frameworks
**EXPECTED INTEGRATION SCOPE:** Complete data lifecycle from application input to encrypted Redis storage to decrypted retrieval

**REVISION TO EXISTING TESTS:**
None required. This is a new integration seam not currently covered by existing cache integration tests.

---

### 2. SEAM: Environment Configuration and Key Management Integration
**HIGH PRIORITY** - Configuration critical, affects security setup and operational deployment

**COMPONENTS:** `create_encryption_layer_from_env`, environment variables (`REDIS_ENCRYPTION_KEY`), `EncryptedCacheLayer.__init__`, key validation
**CRITICAL PATH:** Environment variable loading → Key extraction → Encryption initialization → Validation test → Ready state
**BUSINESS IMPACT:** Ensures encryption can be properly configured across different deployment environments with secure key management

**TEST SCENARIOS:**
- `create_encryption_layer_from_env` correctly loads encryption key from REDIS_ENCRYPTION_KEY environment variable
- Environment-based encryption layer successfully encrypts and decrypts data after initialization
- Missing REDIS_ENCRYPTION_KEY results in warning messages but creates functional layer (with disabled encryption)
- Invalid encryption keys trigger ConfigurationError with helpful error messages
- Empty string encryption key is handled appropriately with proper error messaging
- Environment variable changes between test runs don't cause key confusion
- Multiple encryption layers can be created from environment without conflicts
- Encryption layer initialization validates key format and cryptographic validity
- Environment-based configuration integrates correctly with CacheFactory creation methods
- Production vs development environment configurations result in appropriate encryption behavior

**INFRASTRUCTURE NEEDS:** Environment variable management (monkeypatch), key generation utilities, configuration validation
**EXPECTED INTEGRATION SCOPE:** Environment configuration to operational encryption layer with validated keys

**REVISION TO EXISTING TESTS:**
Review `test_cache_security.py` to ensure encryption key management is tested alongside Redis authentication. May need to add environment-based encryption configuration tests to existing security test suite.

---

### 3. SEAM: Performance Monitoring and Metrics Integration
**MEDIUM PRIORITY** - Operational monitoring, affects performance optimization and capacity planning

**COMPONENTS:** `EncryptedCacheLayer` performance tracking, `get_performance_stats`, `reset_performance_stats`, performance thresholds
**CRITICAL PATH:** Encryption operation → Performance measurement → Metrics accumulation → Statistics reporting → Threshold monitoring
**BUSINESS IMPACT:** Enables monitoring of encryption overhead and identification of performance bottlenecks in caching operations

**TEST SCENARIOS:**
- Performance monitoring correctly tracks encryption operation counts and timing
- Performance statistics accurately reflect actual encryption/decryption overhead
- `get_performance_stats` returns comprehensive metrics with correct calculations (averages, totals)
- Performance monitoring can be disabled via `performance_monitoring=False` parameter
- Performance statistics persist across multiple encryption/decryption operations
- `reset_performance_stats` correctly clears accumulated performance data
- Slow operation warnings are logged when encryption exceeds thresholds (>50ms)
- Average encryption time is calculated correctly from accumulated operation times
- Performance monitoring has minimal overhead on encryption operations (<5%)
- Performance metrics integrate correctly with application-wide monitoring systems

**INFRASTRUCTURE NEEDS:** Performance measurement tools, timing utilities, metric validation frameworks
**EXPECTED INTEGRATION SCOPE:** Performance tracking from operation execution to metrics reporting

**REVISION TO EXISTING TESTS:**
Consider adding performance monitoring tests to existing `test_cache_integration.py` tests that verify cache operation performance meets SLAs.

---

### 4. SEAM: Error Handling and Exception Propagation Integration
**HIGH PRIORITY** - Reliability critical, affects error visibility and operational troubleshooting

**COMPONENTS:** Encryption operations, `ConfigurationError`, error context, error messages, exception propagation
**CRITICAL PATH:** Operation failure → Error detection → ConfigurationError creation → Context enrichment → Error propagation → Application handling
**BUSINESS IMPACT:** Ensures encryption errors are properly detected, reported, and handled with actionable error messages for operations teams

**TEST SCENARIOS:**
- Invalid encryption keys raise ConfigurationError with helpful troubleshooting information
- Missing cryptography library raises ConfigurationError with installation instructions
- Non-serializable data (datetime, custom objects) raises ConfigurationError with clear error context
- Encryption failures include original error details in exception context
- Decryption of corrupted data raises ConfigurationError with diagnostic information
- Invalid token errors during decryption provide appropriate error messages
- ConfigurationError exceptions include proper error_type classification for logging
- Error messages contain actionable guidance for resolving configuration issues
- Exception propagation maintains error context through the call stack
- Error handling integrates correctly with application-wide exception handling middleware

**INFRASTRUCTURE NEEDS:** Error simulation frameworks, exception validation utilities, context verification tools
**EXPECTED INTEGRATION SCOPE:** Complete error lifecycle from detection to propagation with enriched context

**REVISION TO EXISTING TESTS:**
None required. Error handling for encryption is independent of existing cache error scenarios.

---

### 5. SEAM: Key Generation and Management Integration
**MEDIUM PRIORITY** - Development/testing utility, affects test infrastructure and key management

**COMPONENTS:** `create_with_generated_key`, `Fernet.generate_key`, key validation, encryption initialization
**CRITICAL PATH:** Key generation request → Fernet key generation → Encryption layer creation → Validation → Ready state
**BUSINESS IMPACT:** Provides convenient key generation for development and testing while ensuring proper key management patterns

**TEST SCENARIOS:**
- `create_with_generated_key` creates functional encryption layer with valid keys
- Generated keys work correctly for encrypt/decrypt operations
- Each invocation of `create_with_generated_key` produces unique keys
- Generated encryption layer can encrypt and decrypt data successfully
- Generated keys have proper format and cryptographic strength
- Generated keys work across different encryption layer instances
- Key generation handles missing cryptography library gracefully
- Generated encryption layer integrates correctly with performance monitoring
- Multiple generated encryption layers maintain key isolation
- Generated keys are base64-encoded and compatible with Fernet requirements

**INFRASTRUCTURE NEEDS:** Key generation utilities, cryptographic validation tools, isolation testing
**EXPECTED INTEGRATION SCOPE:** Key generation to operational encryption layer with validated functionality

**REVISION TO EXISTING TESTS:**
Consider adding key generation tests to existing `test_cache_security.py` for comprehensive key management coverage.

---

### 6. SEAM: Backward Compatibility and Legacy Data Integration
**MEDIUM PRIORITY** - Migration support, affects gradual encryption rollout and data migration

**COMPONENTS:** `decrypt_cache_data`, invalid token handling, fallback logic, backward compatibility warnings
**CRITICAL PATH:** Decryption attempt → Invalid token detection → Fallback to unencrypted data → Warning logging → Data return
**BUSINESS IMPACT:** Enables gradual migration to encrypted cache without breaking existing systems with unencrypted data

**TEST SCENARIOS:**
- Decryption of unencrypted JSON data succeeds with backward compatibility fallback
- Backward compatibility fallback logs appropriate warning messages
- Unencrypted data is correctly deserialized after fallback handling
- Mixed encrypted/unencrypted data in cache is handled appropriately
- Backward compatibility works across different data types and structures
- Fallback behavior maintains data integrity for legacy unencrypted data
- Performance impact of backward compatibility checks is minimal
- Backward compatibility integrates correctly with error handling for truly corrupted data
- Multiple fallback scenarios (invalid token, wrong key) are handled distinctly
- Backward compatibility behavior can be monitored through logging and metrics

**INFRASTRUCTURE NEEDS:** Legacy data simulation, fallback testing frameworks, migration validation tools
**EXPECTED INTEGRATION SCOPE:** Graceful handling of legacy unencrypted data during transition periods

**REVISION TO EXISTING TESTS:**
None required. Backward compatibility is a new integration concern for encryption migration.

---

### 7. SEAM: Cryptography Library Dependency and Graceful Degradation Integration
**HIGH PRIORITY** - Dependency management, affects deployment and installation validation

**COMPONENTS:** `CRYPTOGRAPHY_AVAILABLE` flag, import validation, `ConfigurationError` on missing dependency, graceful degradation
**CRITICAL PATH:** Module import → Cryptography import attempt → Availability detection → Graceful degradation or error → Operational state
**BUSINESS IMPACT:** Ensures proper dependency management and clear error messages when cryptography library is missing

**TEST SCENARIOS:**
- EncryptedCacheLayer initialization raises ConfigurationError when cryptography is unavailable
- Error message includes installation instructions (pip install cryptography)
- Missing cryptography library is detected early during initialization
- `CRYPTOGRAPHY_AVAILABLE` flag correctly reflects library availability
- Error context includes proper error_type classification for missing dependency
- Graceful degradation behavior is documented and validated
- Import failures don't break application startup, but provide clear errors
- Missing cryptography errors are distinct from invalid key errors
- Error handling works correctly in different Python environments
- Dependency checking integrates with application startup validation

**INFRASTRUCTURE NEEDS:** Dependency simulation frameworks, import mocking utilities, error validation
**EXPECTED INTEGRATION SCOPE:** Dependency validation from import to operational state with clear error messaging

**REVISION TO EXISTING TESTS:**
None required. Cryptography dependency validation is specific to encryption layer.

---

### 8. SEAM: Cache Factory Integration with Encryption
**HIGH PRIORITY** - Factory pattern integration, affects cache creation workflows across the application

**COMPONENTS:** `CacheFactory`, encryption layer creation, security configuration, cache instance initialization
**CRITICAL PATH:** Cache creation request → Security config → Encryption layer creation → Cache initialization → Encrypted cache ready
**BUSINESS IMPACT:** Ensures encryption is properly integrated into cache creation workflows across all factory methods

**TEST SCENARIOS:**
- CacheFactory creates caches with encryption enabled when security config includes encryption key
- Factory methods (`for_web_app`, `for_ai_app`, `for_testing`) properly integrate encryption layers
- Encryption layer configuration is correctly passed through factory to cache instances
- Cache instances created by factory support encrypted data operations
- Factory handles encryption initialization errors gracefully
- Multiple cache instances created by factory maintain encryption isolation
- Factory-created caches with encryption meet performance requirements
- Encryption configuration works consistently across different factory creation methods
- Factory properly handles missing encryption configuration with appropriate warnings
- Encrypted cache instances integrate correctly with cache registry and lifecycle management

**INFRASTRUCTURE NEEDS:** CacheFactory testing utilities, cache validation frameworks, integration test fixtures
**EXPECTED INTEGRATION SCOPE:** Complete cache creation with encryption from factory request to operational encrypted cache

**REVISION TO EXISTING TESTS:**
**REQUIRED REVISION:** Update `test_cache_integration.py` to include encryption layer validation in factory creation tests. Add tests verifying:
- Factory creates encrypted caches when security config includes encryption keys
- Encrypted cache operations work correctly after factory creation
- Factory handles encryption configuration errors appropriately
- Encryption integrates with other factory features (monitoring, presets, security)

---

### 9. SEAM: End-to-End Encrypted Cache Workflows
**HIGH PRIORITY** - Complete system validation, ensures encryption works in realistic application scenarios

**COMPONENTS:** Complete cache infrastructure with encryption, application components, API endpoints, monitoring
**CRITICAL PATH:** Application request → Cache check → Encrypted storage/retrieval → Response → Monitoring
**BUSINESS IMPACT:** Validates encryption works correctly in complete application workflows with realistic usage patterns

**TEST SCENARIOS:**
- Complete AI cache workflow with encrypted key generation, storage, retrieval
- API endpoint cache operations work correctly with encrypted data
- Cache invalidation workflows work with encrypted data patterns
- Health check workflows include encryption status reporting
- Performance monitoring includes encryption metrics in overall cache performance
- Multi-cache workflows maintain encryption isolation across different cache types
- Error handling workflows include encryption-specific error scenarios
- Security workflows validate encrypted data cannot be read without proper keys
- Configuration workflows properly initialize encryption across different environments
- Monitoring workflows track encryption performance and security metrics

**INFRASTRUCTURE NEEDS:** Complete application stack, realistic test scenarios, encryption validation tools, security testing frameworks
**EXPECTED INTEGRATION SCOPE:** Full encryption validation from application requests to encrypted storage to operational monitoring

**REVISION TO EXISTING TESTS:**
**REQUIRED REVISION:** Expand existing end-to-end cache workflow tests in `test_cache_integration.py` to include:
- Encryption validation in complete cache workflows
- Encrypted data verification in storage and retrieval paths
- Performance validation with encryption enabled
- Security validation that encrypted data is properly protected

---

## Implementation Priority and Testing Strategy

### **Priority-Based Implementation Order:**

1. **HIGHEST PRIORITY** (Security critical and foundational):
   - Encryption Pipeline End-to-End Integration (Seam 1)
   - Environment Configuration and Key Management Integration (Seam 2)
   - Error Handling and Exception Propagation Integration (Seam 4)
   - Cryptography Library Dependency and Graceful Degradation Integration (Seam 7)
   - Cache Factory Integration with Encryption (Seam 8)

2. **HIGH PRIORITY** (Complete system validation):
   - End-to-End Encrypted Cache Workflows (Seam 9)

3. **MEDIUM PRIORITY** (Operational and migration support):
   - Performance Monitoring and Metrics Integration (Seam 3)
   - Key Generation and Management Integration (Seam 5)
   - Backward Compatibility and Legacy Data Integration (Seam 6)

### **Testing Infrastructure Recommendations:**

- **Primary Testing Method**: Redis testcontainer or fakeredis with encryption enabled
  - Encrypted data storage and retrieval testing
  - Performance measurement with encryption overhead
  - Security validation with encrypted data inspection
  - Key management and rotation testing

- **Secondary Testing Method**: In-memory testing with generated keys
  - Fast encryption algorithm testing
  - Key generation and validation testing
  - Error scenario simulation
  - Performance baseline measurement

- **Tertiary Testing Method**: Complete application stack testing
  - End-to-end encrypted workflows
  - API integration with encrypted caching
  - Monitoring and alerting with encryption metrics
  - Security validation in production-like scenarios

- **Security Testing**:
  - Encrypted data validation (cannot be read without key)
  - Key management security (proper key storage and handling)
  - Error handling security (no key leakage in error messages)
  - Performance security (encryption overhead within acceptable limits)

### **Test Organization Structure:**

```
backend/tests/integration/cache/
├── test_cache_integration.py              # UPDATE: Add encryption factory integration tests
├── test_cache_security.py                 # UPDATE: Add encryption key management tests
├── test_cache_encryption.py               # NEW: Dedicated encryption integration tests
├── conftest.py                            # UPDATE: Add encryption fixtures
└── TEST_PLAN_encryption.md                # This document
```

### **Success Criteria:**

- **Security Enforcement**:
  - All data stored in Redis is properly encrypted and cannot be read without decryption
  - Encryption keys are properly managed through environment configuration
  - Missing or invalid keys result in clear error messages with troubleshooting guidance
  - Encryption errors are properly detected and reported with appropriate context

- **Data Integrity**:
  - Complete round-trip encryption/decryption preserves data exactly
  - All data types (strings, numbers, booleans, nested structures) work correctly
  - Unicode and special characters are preserved through encryption pipeline
  - Large datasets are encrypted and decrypted without corruption

- **Performance**:
  - Encryption overhead is within acceptable limits (<5ms for <1KB data)
  - Performance monitoring accurately tracks encryption overhead
  - Slow operation warnings alert operations teams to performance issues
  - Encryption doesn't introduce unacceptable latency in cache operations

- **Operational Reliability**:
  - Encryption integrates seamlessly with cache factory creation workflows
  - Error handling provides actionable information for troubleshooting
  - Backward compatibility enables gradual migration to encrypted caching
  - Missing cryptography library is detected early with clear installation guidance

- **Integration Completeness**:
  - Encryption works correctly with all cache types (AI, web, generic)
  - Encrypted caches integrate with health checks and monitoring
  - Configuration management properly initializes encryption across environments
  - End-to-end workflows demonstrate encryption working in realistic scenarios

---

## Test Implementation Guidance

### Encryption Pipeline Testing

**Complete Round-Trip Testing:**
```python
@pytest.mark.asyncio
async def test_encryption_round_trip_preserves_data():
    """
    Test that encryption/decryption preserves data integrity.

    Integration Scope:
        EncryptedCacheLayer → JSON serialization → Fernet encryption →
        Redis storage → Decryption → JSON deserialization

    Business Impact:
        Ensures cached data is protected and can be reliably recovered

    Success Criteria:
        - Original data matches decrypted data exactly
        - All data types are preserved (str, int, float, bool, None, list, dict)
        - Unicode and special characters work correctly
    """
    encryption = EncryptedCacheLayer.create_with_generated_key()

    test_data = {
        "string": "test value",
        "integer": 42,
        "float": 3.14,
        "boolean": True,
        "none": None,
        "list": [1, 2, 3],
        "nested": {"key": "value"},
        "unicode": "Hello 世界 🌍"
    }

    # Encrypt and decrypt
    encrypted = encryption.encrypt_cache_data(test_data)
    decrypted = encryption.decrypt_cache_data(encrypted)

    # Verify data integrity
    assert decrypted == test_data
    assert isinstance(encrypted, bytes)
    assert len(encrypted) > len(json.dumps(test_data))  # Should be larger when encrypted
```

**Integration with Redis:**
```python
@pytest.mark.asyncio
async def test_encrypted_cache_integration_with_redis():
    """
    Test encrypted data storage and retrieval through Redis.

    Integration Scope:
        Application → EncryptedCacheLayer → Redis → Decryption → Application

    Business Impact:
        Validates encryption works with actual Redis storage

    Success Criteria:
        - Data stored in Redis is encrypted (not human-readable)
        - Retrieved data is properly decrypted
        - Round-trip through Redis preserves data integrity
    """
    encryption = EncryptedCacheLayer.create_with_generated_key()
    redis_client = await create_test_redis_client()

    test_data = {"sensitive": "data", "user_id": 123}
    cache_key = "test:encrypted:key"

    # Encrypt and store
    encrypted = encryption.encrypt_cache_data(test_data)
    await redis_client.set(cache_key, encrypted)

    # Verify data in Redis is encrypted (not human-readable)
    raw_redis_data = await redis_client.get(cache_key)
    assert b"sensitive" not in raw_redis_data  # Original data not visible
    assert b"user_id" not in raw_redis_data

    # Retrieve and decrypt
    retrieved = await redis_client.get(cache_key)
    decrypted = encryption.decrypt_cache_data(retrieved)

    assert decrypted == test_data
```

### Environment Configuration Testing

**Environment-Based Initialization:**
```python
@pytest.mark.asyncio
async def test_encryption_from_environment_configuration(monkeypatch):
    """
    Test encryption layer creation from environment variables.

    Integration Scope:
        Environment variables → create_encryption_layer_from_env →
        EncryptedCacheLayer → Functional encryption

    Business Impact:
        Enables proper encryption configuration in production deployments

    Success Criteria:
        - REDIS_ENCRYPTION_KEY is properly loaded
        - Encryption layer functions correctly after environment initialization
        - Missing key results in warning but functional layer
    """
    # Generate and set encryption key
    from cryptography.fernet import Fernet
    test_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_key)

    # Create from environment
    encryption = create_encryption_layer_from_env()

    # Verify it works
    assert encryption.is_enabled
    test_data = {"test": "data"}
    encrypted = encryption.encrypt_cache_data(test_data)
    decrypted = encryption.decrypt_cache_data(encrypted)
    assert decrypted == test_data
```

### Error Handling Testing

**Invalid Key Handling:**
```python
def test_encryption_invalid_key_raises_configuration_error():
    """
    Test that invalid encryption keys raise ConfigurationError.

    Integration Scope:
        Invalid key → EncryptedCacheLayer.__init__ → ConfigurationError

    Business Impact:
        Ensures configuration errors are caught early with helpful messages

    Success Criteria:
        - Invalid keys raise ConfigurationError
        - Error message includes troubleshooting guidance
        - Error context includes error_type classification
    """
    with pytest.raises(ConfigurationError) as exc_info:
        EncryptedCacheLayer(encryption_key="invalid-key-format")

    error = exc_info.value
    assert "invalid encryption key" in str(error).lower()
    assert "generate_key()" in str(error) or "Fernet" in str(error)
    assert error.context.get("error_type") == "invalid_encryption_key"
```

### Performance Monitoring Testing

**Performance Metrics Validation:**
```python
@pytest.mark.asyncio
async def test_encryption_performance_monitoring():
    """
    Test encryption performance monitoring and metrics.

    Integration Scope:
        Encryption operations → Performance tracking → Metrics collection

    Business Impact:
        Enables monitoring of encryption overhead for optimization

    Success Criteria:
        - Performance statistics accurately track operations
        - Average times are calculated correctly
        - Statistics can be reset for testing
    """
    encryption = EncryptedCacheLayer.create_with_generated_key(
        performance_monitoring=True
    )

    # Perform operations
    test_data = {"test": "data" * 100}  # Larger data for measurable timing
    for _ in range(10):
        encrypted = encryption.encrypt_cache_data(test_data)
        encryption.decrypt_cache_data(encrypted)

    # Check statistics
    stats = encryption.get_performance_stats()
    assert stats["encryption_operations"] == 10
    assert stats["decryption_operations"] == 10
    assert stats["total_operations"] == 20
    assert stats["avg_encryption_time"] > 0
    assert stats["avg_decryption_time"] > 0

    # Test reset
    encryption.reset_performance_stats()
    stats = encryption.get_performance_stats()
    assert stats["total_operations"] == 0
```

### Cache Factory Integration Testing

**Factory Creates Encrypted Caches:**
```python
@pytest.mark.asyncio
async def test_cache_factory_creates_encrypted_caches():
    """
    Test CacheFactory creates caches with encryption enabled.

    Integration Scope:
        CacheFactory → SecurityConfig with encryption → EncryptedCacheLayer →
        Cache instance with encryption

    Business Impact:
        Ensures encryption is properly integrated into cache creation workflows

    Success Criteria:
        - Factory creates caches with encryption when configured
        - Encrypted caches work correctly for data operations
        - Encryption configuration propagates through factory methods
    """
    from cryptography.fernet import Fernet
    encryption_key = Fernet.generate_key().decode()

    security_config = SecurityConfig(
        encryption_key=encryption_key,
        redis_auth="test_password"
    )

    factory = CacheFactory()
    cache = await factory.for_testing(
        security_config=security_config,
        use_memory_cache=False
    )

    # Test encrypted operations
    test_key = "encrypted:test"
    test_value = {"sensitive": "data"}

    await cache.set(test_key, test_value)
    retrieved = await cache.get(test_key)

    assert retrieved == test_value

    # Verify data in Redis is encrypted (if using real Redis)
    if hasattr(cache, '_redis_client'):
        raw_data = await cache._redis_client.get(test_key)
        assert b"sensitive" not in raw_data  # Should be encrypted
```

---

## Recommended Test File: test_cache_encryption.py

Create a new dedicated test file for encryption integration tests:

**File Structure:**
```python
"""Cache Encryption Integration Tests

This module provides comprehensive integration tests for cache encryption functionality,
validating end-to-end encryption pipelines, key management, performance monitoring,
and error handling across the cache infrastructure.

Integration Focus:
    - Encryption/decryption round-trip integrity
    - Environment-based key configuration
    - Performance monitoring and metrics
    - Error handling and security validation
    - Cache factory integration with encryption
    - End-to-end encrypted cache workflows
"""

class TestEncryptionPipelineIntegration:
    """Tests for encryption/decryption pipeline integration."""
    # Complete round-trip tests
    # Data integrity validation
    # Unicode and special character handling
    # Large dataset encryption
    # Redis storage integration

class TestEncryptionConfigurationIntegration:
    """Tests for encryption configuration and key management."""
    # Environment variable loading
    # Key validation and error handling
    # Generated key functionality
    # Configuration propagation

class TestEncryptionPerformanceMonitoring:
    """Tests for encryption performance tracking."""
    # Performance metrics accuracy
    # Statistics calculation
    # Threshold monitoring
    # Performance reset functionality

class TestEncryptionErrorHandling:
    """Tests for encryption error scenarios."""
    # Invalid key handling
    # Missing cryptography library
    # Serialization errors
    # Decryption failures
    # Error context and messages

class TestEncryptionFactoryIntegration:
    """Tests for cache factory integration with encryption."""
    # Factory creates encrypted caches
    # Security config propagation
    # Multiple cache type support
    # Encryption isolation across instances

class TestEncryptionEndToEndWorkflows:
    """Tests for complete encrypted cache workflows."""
    # AI cache with encryption
    # API endpoint integration
    # Health check integration
    # Monitoring integration
```

---

## Summary

This integration test plan provides comprehensive coverage of cache encryption integration points while prioritizing security-critical functionality. The tests focus on observable behavior and real integration scenarios rather than implementation details, ensuring the encryption layer:

1. **Protects Data**: Validates all cached data is properly encrypted and secure
2. **Maintains Integrity**: Ensures encryption/decryption preserves data exactly
3. **Performs Well**: Verifies encryption overhead is within acceptable limits
4. **Handles Errors**: Confirms proper error detection and reporting with actionable guidance
5. **Integrates Seamlessly**: Ensures encryption works across all cache creation workflows
6. **Enables Operations**: Provides monitoring and management capabilities for production deployments

The plan identifies required revisions to existing tests (`test_cache_integration.py` and `test_cache_security.py`) while proposing a new dedicated test file (`test_cache_encryption.py`) for comprehensive encryption-specific integration testing.
