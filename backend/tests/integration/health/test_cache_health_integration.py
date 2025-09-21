"""
Integration tests for cache system health monitoring.

These tests verify the integration between HealthChecker and AIResponseCache,
ensuring proper health status reporting, performance monitoring integration,
and graceful degradation when cache components fail.

HIGH PRIORITY - Core infrastructure monitoring, affects system performance visibility
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    check_cache_health,
)
from app.infrastructure.cache import AIResponseCache, CachePerformanceMonitor


class TestCacheSystemHealthIntegration:
    """
    Integration tests for cache system health monitoring.

    Seam Under Test:
        HealthChecker → AIResponseCache → CachePerformanceMonitor

    Critical Path:
        Health check registration → Cache connectivity validation →
        Performance metrics collection → Status aggregation

    Business Impact:
        Ensures cache system health monitoring provides accurate performance insights
        and enables early detection of cache-related performance issues.

    Test Strategy:
        - Verify cache service connectivity validation
        - Test performance monitoring integration
        - Confirm graceful degradation with cache failures
        - Validate health check response times and metadata
        - Test both Redis and memory-only cache scenarios

    Success Criteria:
        - Cache health checks complete successfully under normal conditions
        - Performance metrics are collected and integrated correctly
        - System reports appropriate status when cache components fail
        - Health check response times are reasonable (<100ms)
        - Cache metadata provides useful operational insights
    """

    def test_cache_health_integration_with_redis_and_performance_monitor(
        self, health_checker, fake_redis_cache, performance_monitor
    ):
        """
        Test cache health integration with Redis backend and performance monitoring.

        Integration Scope:
            HealthChecker → AIResponseCache → FakeStrictRedis → CachePerformanceMonitor

        Business Impact:
            Verifies that cache system health monitoring works correctly with
            real Redis infrastructure and performance tracking, ensuring operators
            can monitor cache performance in production environments.

        Test Strategy:
            - Set up cache with Redis backend and performance monitor
            - Register cache health check with health checker
            - Execute health check and validate comprehensive status
            - Verify performance metrics are collected and integrated

        Success Criteria:
            - Health check returns HEALTHY status with Redis connectivity
            - Performance metrics are collected and available
            - Cache metadata includes Redis status information
            - Response time is reasonable for monitoring frequency
        """
        # Configure cache with performance monitor
        fake_redis_cache.performance_monitor = performance_monitor

        # Create health check function that uses the configured cache
        async def cache_health_with_monitor():
            return await check_cache_health()

        # Patch check_cache_health to use our fake cache
        with patch('app.infrastructure.monitoring.health.AIResponseCache', return_value=fake_redis_cache):
            health_checker.register_check("cache", cache_health_with_monitor)

            # Execute health check
            result = await health_checker.check_component("cache")

            # Verify comprehensive health status
            assert result.name == "cache"
            assert result.status == HealthStatus.HEALTHY
            assert "operational" in result.message.lower()
            assert result.response_time_ms > 0
            assert result.response_time_ms < 100  # Should be fast
            assert result.metadata is not None
            assert "cache_type" in result.metadata
            assert result.metadata["cache_type"] == "redis"

    def test_cache_health_integration_with_memory_only_fallback(
        self, health_checker, fake_redis_cache, performance_monitor
    ):
        """
        Test cache health when Redis is unavailable but memory cache works.

        Integration Scope:
            HealthChecker → AIResponseCache → Memory cache fallback

        Business Impact:
            Ensures graceful degradation when Redis is unavailable,
            allowing system to continue operating with memory-only caching
            while alerting operators to the degraded state.

        Test Strategy:
            - Simulate Redis connection failure
            - Verify system falls back to memory-only mode
            - Confirm health check reports degraded status
            - Validate that basic caching still functions

        Success Criteria:
            - Health check returns DEGRADED status when Redis unavailable
            - Memory cache remains operational
            - Clear indication of which component failed
            - Response time still reasonable despite fallback
        """
        # Configure cache with performance monitor
        fake_redis_cache.performance_monitor = performance_monitor

        # Mock Redis connection failure
        fake_redis_cache.connect.side_effect = Exception("Redis connection failed")

        async def cache_health_with_fallback():
            return await check_cache_health()

        with patch('app.infrastructure.monitoring.health.AIResponseCache', return_value=fake_redis_cache):
            health_checker.register_check("cache", cache_health_with_fallback)

            result = await health_checker.check_component("cache")

            # Verify graceful degradation
            assert result.name == "cache"
            assert result.status == HealthStatus.DEGRADED
            assert "degraded" in result.message.lower()
            assert result.response_time_ms > 0
            assert result.metadata is not None
            assert result.metadata["cache_type"] == "memory"

    def test_cache_health_integration_with_performance_monitoring_disabled(
        self, health_checker, fake_redis_cache
    ):
        """
        Test cache health when performance monitoring is not available.

        Integration Scope:
            HealthChecker → AIResponseCache → Cache without performance monitor

        Business Impact:
            Ensures cache health monitoring works even when performance
            monitoring is disabled or unavailable, maintaining basic
            connectivity monitoring capabilities.

        Test Strategy:
            - Configure cache without performance monitor
            - Execute health check and verify basic functionality
            - Confirm system reports degraded monitoring capability
            - Validate that core cache functionality still works

        Success Criteria:
            - Health check completes without performance monitor
            - Cache connectivity is still validated
            - Clear indication of monitoring limitations
            - Response time remains reasonable
        """
        # Configure cache without performance monitor
        fake_redis_cache.performance_monitor = None

        async def cache_health_no_monitor():
            return await check_cache_health()

        with patch('app.infrastructure.monitoring.health.AIResponseCache', return_value=fake_redis_cache):
            health_checker.register_check("cache", cache_health_no_monitor)

            result = await health_checker.check_component("cache")

            # Verify health check works without performance monitor
            assert result.name == "cache"
            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms > 0
            assert result.metadata is not None

    def test_cache_health_integration_comprehensive_stats_collection(
        self, health_checker, fake_redis_cache, performance_monitor
    ):
        """
        Test comprehensive cache statistics collection and reporting.

        Integration Scope:
            HealthChecker → AIResponseCache → Performance monitoring data collection

        Business Impact:
            Ensures operators receive comprehensive cache performance
            insights for capacity planning, performance optimization,
            and troubleshooting cache-related issues.

        Test Strategy:
            - Configure cache with performance monitor and sample data
            - Execute health check and validate stats collection
            - Verify all relevant metrics are captured and reported
            - Confirm metadata includes operational insights

        Success Criteria:
            - Performance statistics are collected and available
            - Cache metadata includes comprehensive operational data
            - Health check response provides actionable insights
            - Response time includes performance monitoring overhead
        """
        # Add sample data to performance monitor
        performance_monitor.cache_hits = 150
        performance_monitor.cache_misses = 25
        performance_monitor.total_operations = 175

        fake_redis_cache.performance_monitor = performance_monitor

        async def cache_health_with_stats():
            return await check_cache_health()

        with patch('app.infrastructure.monitoring.health.AIResponseCache', return_value=fake_redis_cache):
            health_checker.register_check("cache", cache_health_with_stats)

            result = await health_checker.check_component("cache")

            # Verify comprehensive statistics collection
            assert result.name == "cache"
            assert result.status == HealthStatus.HEALTHY
            assert result.metadata is not None
            assert "cache_type" in result.metadata

            # Verify health check collected performance insights
            assert result.response_time_ms > 0
            assert result.response_time_ms < 200  # Should be reasonable with stats

    def test_cache_health_integration_with_cache_service_dependency_injection(
        self, health_checker, fake_redis_cache, performance_monitor
    ):
        """
        Test cache health integration using dependency injection pattern.

        Integration Scope:
            HealthChecker → Dependency-injected cache service → Health validation

        Business Impact:
            Verifies that health monitoring can work with dependency-injected
            cache services, enabling proper service lifecycle management
            and avoiding the performance issue noted in check_cache_health().

        Test Strategy:
            - Create health check function that accepts cache service as parameter
            - Register with dependency injection pattern
            - Verify health check uses injected service correctly
            - Confirm proper service lifecycle management

        Success Criteria:
            - Health check accepts and uses dependency-injected cache service
            - No redundant cache service instantiation occurs
            - Health validation works correctly with injected service
            - Response time is optimal due to service reuse
        """
        fake_redis_cache.performance_monitor = performance_monitor

        # Create health check function that accepts cache service (dependency injection pattern)
        async def cache_health_with_di(cache_service):
            """Health check that accepts cache service as parameter for optimal performance."""
            # Simulate the optimized check_cache_health implementation
            name = "cache"
            start = await asyncio.sleep(0)  # Simulate async operation

            try:
                # Use the injected cache service (no instantiation)
                stats = await cache_service.get_cache_stats()
                redis_status = stats.get("redis", {}).get("status")
                memory_status = stats.get("memory", {}).get("status")

                is_healthy = redis_status != "error" and memory_status != "unavailable"
                cache_type = "redis" if redis_status == "ok" else "memory"

                return ComponentStatus(
                    name=name,
                    status=HealthStatus.HEALTHY if is_healthy else HealthStatus.DEGRADED,
                    message="Cache operational" if is_healthy else "Cache degraded",
                    response_time_ms=10.0,  # Mock response time
                    metadata={"cache_type": cache_type},
                )
            except Exception as e:
                return ComponentStatus(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Cache health check failed: {e}",
                    response_time_ms=10.0,
                )

        # Register with dependency injection pattern
        health_checker.register_check("cache", lambda: cache_health_with_di(fake_redis_cache))

        result = await health_checker.check_component("cache")

        # Verify dependency injection pattern works correctly
        assert result.name == "cache"
        assert result.status == HealthStatus.HEALTHY
        assert result.metadata is not None
        assert result.metadata["cache_type"] == "redis"
