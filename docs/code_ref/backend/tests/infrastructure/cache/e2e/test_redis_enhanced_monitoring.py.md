---
sidebar_label: test_redis_enhanced_monitoring
---

# Enhanced E2E cache monitoring tests using real Redis connectivity via Testcontainers.

  file_path: `backend/tests/infrastructure/cache/e2e/test_redis_enhanced_monitoring.py`

This module provides comprehensive monitoring workflow testing with actual Redis instances,
enabling validation of Redis-specific monitoring features and production-like metrics.

## TestRedisEnhancedMonitoringWorkflow

Enhanced cache monitoring tests using real Redis connectivity.

Benefits over ASGI-only tests:
    - Tests actual Redis performance metrics and monitoring
    - Validates Redis-specific operations (TTL, memory usage, connections)
    - Enables realistic monitoring data validation
    - Provides production-like performance testing scenarios
    
Test Strategy:
    Uses Testcontainers Redis to generate authentic monitoring data,
    validating that monitoring systems accurately reflect Redis operations.

### test_redis_invalidation_updates_real_metrics()

```python
async def test_redis_invalidation_updates_real_metrics(self, enhanced_client_with_preset):
```

Test that Redis invalidation operations update metrics with real data.

Business Impact:
    Accurate invalidation metrics are critical for cache management,
    capacity planning, and operational monitoring in production systems.
    
Enhanced Testing:
    Uses real Redis to validate that invalidation operations are properly
    tracked and reported through monitoring endpoints.

### test_redis_performance_monitoring_under_load()

```python
async def test_redis_performance_monitoring_under_load(self, enhanced_client_with_preset):
```

Test Redis performance monitoring under simulated load conditions.

Business Impact:
    Performance monitoring must remain accurate and responsive during
    high-load scenarios to enable effective operational management.
    
Enhanced Testing:
    Uses real Redis to generate authentic load scenarios and validate
    that monitoring endpoints provide accurate performance data.

### test_redis_connection_monitoring_and_recovery()

```python
async def test_redis_connection_monitoring_and_recovery(self, enhanced_client_with_preset):
```

Test Redis connection monitoring and recovery scenarios.

Business Impact:
    Connection monitoring is essential for detecting and responding to
    Redis connectivity issues in production environments.
    
Enhanced Testing:
    Uses real Redis container to validate connection status reporting
    and monitoring data accuracy during connectivity scenarios.

### test_redis_memory_usage_monitoring()

```python
async def test_redis_memory_usage_monitoring(self, enhanced_client_with_preset):
```

Test Redis memory usage monitoring with real memory operations.

Business Impact:
    Memory usage monitoring is critical for Redis capacity planning
    and preventing out-of-memory conditions in production systems.
    
Enhanced Testing:
    Uses real Redis to generate authentic memory usage patterns
    and validate monitoring accuracy.

### test_redis_ttl_and_expiration_monitoring()

```python
async def test_redis_ttl_and_expiration_monitoring(self, enhanced_client_with_preset):
```

Test Redis TTL and expiration monitoring with real time-based operations.

Business Impact:
    TTL monitoring is essential for cache efficiency and ensuring
    that expired data is properly cleaned up in production systems.
    
Enhanced Testing:
    Uses real Redis to test TTL-based operations and validate
    that expiration monitoring provides accurate data.

### test_redis_monitoring_consistency_across_operations()

```python
async def test_redis_monitoring_consistency_across_operations(self, enhanced_client_with_preset):
```

Test monitoring data consistency across multiple Redis operations.

Business Impact:
    Consistent monitoring is essential for reliable operational
    visibility and accurate performance tracking.
    
Enhanced Testing:
    Uses real Redis to validate monitoring consistency across
    sequential operations with realistic timing and data patterns.
