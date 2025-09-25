---
sidebar_label: test_redis_enhanced_preset_behavior
---

# Enhanced E2E tests using real Redis connectivity via Testcontainers.

  file_path: `backend/tests/e2e/cache/test_redis_enhanced_preset_behavior.py`

This module provides comprehensive preset behavior testing with actual Redis instances,
enabling validation of Redis-specific features and production-like cache behavior.

## TestRedisEnhancedPresetBehavior

Enhanced preset behavior tests using real Redis connectivity.

Benefits over ASGI-only tests:
    - Tests actual Redis connectivity and status reporting
    - Validates Redis-specific cache operations (SCAN, DEL, TTL)
    - Enables realistic preset behavior testing
    - Provides real performance metrics and monitoring data
    
Test Strategy:
    Uses Testcontainers to spin up real Redis instances, allowing
    comprehensive testing of Redis-backed cache presets without
    external dependencies.

### test_ai_production_preset_shows_connected_redis_status()

```python
async def test_ai_production_preset_shows_connected_redis_status(self, enhanced_client_with_preset):
```

Test that ai-production preset shows connected Redis status with real Redis.

Business Impact:
    Validates that production-grade AI workloads can rely on Redis connectivity
    for consistent caching behavior and performance optimization.
    
Enhanced Testing:
    Uses real Redis container to ensure accurate status reporting,
    unlike ASGI tests which always show "disconnected" due to test isolation.

### test_development_preset_redis_connectivity_with_fallback()

```python
async def test_development_preset_redis_connectivity_with_fallback(self, enhanced_client_with_preset):
```

Test development preset shows connected Redis with proper fallback configuration.

Business Impact:
    Development environments should maintain Redis connectivity while
    providing reliable memory fallback for uninterrupted development workflows.
    
Enhanced Testing:
    Validates that development preset properly configures both Redis
    and memory cache layers for optimal development experience.

### test_redis_pattern_invalidation_with_real_connectivity()

```python
async def test_redis_pattern_invalidation_with_real_connectivity(self, enhanced_client_with_preset):
```

Test Redis pattern-based invalidation with real Redis SCAN/DEL operations.

Business Impact:
    Pattern-based cache invalidation is critical for maintaining data consistency
    in production systems with complex caching hierarchies.
    
Enhanced Testing:
    Uses real Redis to test actual SCAN and DEL operations,
    validating that pattern matching works correctly with Redis wildcard patterns.

### test_redis_performance_metrics_with_real_operations()

```python
async def test_redis_performance_metrics_with_real_operations(self, enhanced_client_with_preset):
```

Test cache performance metrics with actual Redis operations.

Business Impact:
    Performance monitoring relies on accurate metrics from real cache operations
    to provide meaningful insights for capacity planning and optimization.
    
Enhanced Testing:
    Uses real Redis to generate authentic performance metrics,
    validating monitoring accuracy under realistic conditions.

### test_redis_security_features_with_testcontainers()

```python
async def test_redis_security_features_with_testcontainers(self, redis_container, enhanced_cache_preset_app):
```

Test Redis security features using Testcontainers configuration.

Business Impact:
    Security testing with real Redis validates that authentication,
    TLS, and other security features work correctly in production-like environments.
    
Enhanced Testing:
    Uses Testcontainers Redis to test security configurations
    without requiring complex external Redis setups.

### test_redis_preset_scenarios_comprehensive()

```python
async def test_redis_preset_scenarios_comprehensive(self, enhanced_client_with_preset, redis_preset_scenarios):
```

Test comprehensive preset scenarios with real Redis connectivity.

Business Impact:
    Validates that all supported presets work correctly with Redis,
    ensuring reliable behavior across different deployment environments.
    
Enhanced Testing:
    Uses real Redis to test preset behavior that would be impossible
    to validate accurately with ASGI-only testing.
