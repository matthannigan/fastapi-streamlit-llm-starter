---
sidebar_label: test_cache_integration
---

# Integration tests for cache infrastructure components.

  file_path: `backend/tests/integration/cache/test_cache_integration.py`

This test suite verifies cross-component interactions using real implementations
instead of extensive mocking. Tests demonstrate how different cache components
work together to provide complete functionality.

Coverage Focus:
    - Factory + Cache + Monitor integration
    - Settings + Factory integration  
    - Cache + Key Generator + Performance Monitor integration
    - End-to-end cache workflows with real components

External Dependencies:
    Uses real components with graceful degradation for Redis unavailability.
    No internal mocking - only system boundary mocking where necessary.

## TestCacheFactoryIntegration

Integration tests for CacheFactory with other components.

Tests real component interactions rather than mocked dependencies.

### test_factory_creates_cache_with_monitoring_integration()

```python
async def test_factory_creates_cache_with_monitoring_integration(self):
```

Test complete factory workflow with performance monitoring integration.

Verifies:
    Factory creates cache with real monitoring component integration
    
Business Impact:
    Ensures end-to-end monitoring functionality works correctly
    
Integration Points:
    - CacheFactory -> Cache creation
    - Cache -> Performance monitoring integration
    - Monitor -> Metrics collection during operations

### test_factory_with_settings_creates_configured_cache()

```python
async def test_factory_with_settings_creates_configured_cache(self, test_settings):
```

Test factory integration with real Settings configuration.

Verifies:
    Factory respects actual configuration from Settings
    
Integration Points:
    - Settings -> Configuration loading
    - Factory -> Configuration application
    - Cache -> Configured behavior

### test_factory_testing_database_isolation_with_testcontainers()

```python
async def test_factory_testing_database_isolation_with_testcontainers(self):
```

Test factory creates cache with proper test database isolation using real Redis.

Verifies:
    Factory.for_testing() uses Redis database 15 for test isolation when using default URL
    
Business Impact:
    Ensures test data isolation preventing interference between test runs
    
Integration Points:
    - CacheFactory -> Test cache creation with database isolation
    - Testcontainers -> Real Redis for accurate testing
    - Default database behavior -> Standard test database isolation

## TestCacheKeyGeneratorIntegration

Integration tests for CacheKeyGenerator with cache and monitoring.

Tests real component interactions in key generation workflows.

### test_key_generator_with_cache_and_monitoring_integration()

```python
async def test_key_generator_with_cache_and_monitoring_integration(self):
```

Test complete key generation workflow with cache and monitoring.

Verifies:
    Key generator integrates properly with cache operations and monitoring
    
Business Impact:
    Ensures key generation, caching, and monitoring work together correctly
    
Integration Points:
    - KeyGenerator -> Key generation with monitoring
    - Cache -> Key-based operations
    - Monitor -> Key generation metrics

## TestEndToEndCacheWorkflows

End-to-end integration tests for complete cache workflows.

Tests realistic usage patterns with multiple integrated components.

### test_complete_ai_cache_workflow_integration()

```python
async def test_complete_ai_cache_workflow_integration(self):
```

Test complete AI cache workflow with all components integrated.

Verifies:
    All AI cache components work together in realistic workflows
    
Business Impact:
    Ensures AI cache functionality works end-to-end in production scenarios
    
Integration Points:
    - Factory -> AI cache creation
    - KeyGenerator -> AI-specific key generation
    - Cache -> AI response storage and retrieval
    - Monitor -> AI cache performance tracking

### test_cache_fallback_behavior_integration()

```python
async def test_cache_fallback_behavior_integration(self):
```

Test cache fallback behavior integration across components.

Verifies:
    Graceful degradation works across all integrated components
    
Business Impact:
    Ensures system resilience when external dependencies are unavailable
    
Integration Points:
    - Factory -> Fallback cache creation
    - Settings -> Fallback configuration
    - Components -> Graceful degradation behavior

## TestCacheComponentInteroperability

Shared Contract Tests for cache component interoperability and compatibility.

Verifies different cache implementations can be used interchangeably by testing
actual cache instances rather than factory method variations. This implements
the "Shared Contract Tests" pattern to ensure all cache implementations adhere
to the same behavioral contract.

This test suite runs the exact same test code against both a high-fidelity 
Redis instance (using Testcontainers) and a fast in-memory fake (using FakeRedis). 
This guarantees that any cache backend will adhere to the exact same behavioral contract.

Testing Approach:
    - Direct GenericRedisCache instantiation for focused contract testing
    - Real Redis via Testcontainers for complete fidelity
    - FakeRedis for fast, Redis-compatible behavior without external dependencies
    - Identical test logic ensures true behavioral equivalence

### cache_instances_via_factory()

```python
async def cache_instances_via_factory(self):
```

Alternative fixture demonstrating factory-based cache instance creation.

This approach uses CacheFactory.for_testing() to create cache instances,
then performs hot-swapping for the FakeRedis variant. This provides broader
scope testing that includes the factory's assembly logic.

Use this fixture when you want to test:
- The complete service assembly process via CacheFactory
- Factory configuration handling and parameter mapping
- Integration between factory, cache, and monitoring components

The trade-off is slightly less isolation compared to direct instantiation,
but broader coverage of the service creation pipeline.

### cache_instances()

```python
async def cache_instances(self):
```

Provides actual cache instances for shared contract testing.

Creates two cache instances for behavioral equivalence testing:
1. Real Redis cache using Testcontainers for full Redis fidelity
2. Fast in-memory fake using FakeRedis for Redis-compatible behavior

Both instances are fully-formed, real cache objects that implement the
CacheInterface contract, ensuring identical behavioral contracts.
This is a true "Shared Contract Test" - the exact same test code runs
against both backends to guarantee behavioral equivalence.

Design Choice: Direct GenericRedisCache Instantiation
    This fixture uses direct instantiation for focused contract testing
    of the GenericRedisCache class itself.
    
    Alternative Approach: Could use CacheFactory.for_testing() for broader
    scope testing that includes factory assembly logic, then perform the
    hot-swap on factory-created instances. Both approaches are valid:
    - Current (direct): Better for isolated GenericRedisCache contract testing
    - Alternative (factory): Better for testing fully assembled service contracts

### test_cache_shared_contract_basic_operations()

```python
async def test_cache_shared_contract_basic_operations(self, cache_instances):
```

Shared contract test for basic cache operations across implementations.

Verifies that all cache implementations provide identical behavior for
the core CacheInterface contract: get, set, exists, delete operations.

This test ensures behavioral equivalence between different cache backends,
making them truly interchangeable in production applications.

Contract Verification:
    - set() stores values correctly
    - get() retrieves exact values
    - exists() reports key presence accurately  
    - delete() removes keys completely
    - All operations maintain consistent behavior across implementations

### test_cache_shared_contract_ttl_behavior()

```python
async def test_cache_shared_contract_ttl_behavior(self, cache_instances):
```

Shared contract test for TTL (time-to-live) behavior across implementations.

Verifies that all cache implementations handle TTL consistently:
- Keys with TTL are stored correctly
- TTL values are respected during storage
- Key existence behavior is consistent

Note: This test focuses on TTL setting behavior rather than expiration
timing to avoid test flakiness while still verifying contract compliance.

### test_cache_shared_contract_data_types()

```python
async def test_cache_shared_contract_data_types(self, cache_instances):
```

Shared contract test for data type handling across implementations.

Verifies that all cache implementations handle various Python data types
consistently, ensuring serialization/deserialization behavior is equivalent.

### test_cache_shared_contract_interface_compliance()

```python
async def test_cache_shared_contract_interface_compliance(self, cache_instances):
```

Shared contract test for CacheInterface compliance across implementations.

Verifies that all cache implementations expose the required interface methods
and that these methods are callable with the expected signatures.

### test_factory_assembled_cache_shared_contract()

```python
async def test_factory_assembled_cache_shared_contract(self, cache_instances_via_factory):
```

Demonstration test using the factory-based fixture for broader scope testing.

This test demonstrates the alternative approach that includes factory assembly
logic in the contract testing. It tests the same behavioral contract but with
broader coverage of the service creation pipeline.

Use this approach when you want to validate that the CacheFactory correctly
assembles cache services that adhere to the same behavioral contracts.
