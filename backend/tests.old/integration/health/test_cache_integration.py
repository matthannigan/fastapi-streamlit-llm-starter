"""
Integration Tests for Cache Service Health Monitoring (SEAM 2)

Tests the integration between HealthChecker and cache infrastructure, including
Redis connectivity validation, memory fallback behavior, and dependency injection
optimization patterns. Validates that cache health checks accurately reflect
cache service operational status.

This test file validates the critical integration seam:
HealthChecker → check_cache_health → AIResponseCache → Redis/Memory Backends

Test Coverage:
- Redis backend connectivity and health validation
- Memory fallback behavior when Redis unavailable
- Dependency injection optimization for performance
- Cache metadata and status reporting accuracy
- Performance characteristics of cache health checks
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.infrastructure.monitoring.health import HealthStatus, ComponentStatus


@pytest.mark.integration
class TestCacheHealthIntegration:
    """
    Integration tests for cache health monitoring and service integration.

    Seam Under Test:
        HealthChecker → check_cache_health → AIResponseCache → Backend connectivity validation

    Critical Paths:
        - Cache health check validates Redis connectivity
        - Graceful degradation to memory-only when Redis unavailable
        - Dependency injection optimization for performance
        - Metadata collection for operational monitoring

    Business Impact:
        Validates primary caching infrastructure operational for optimal performance
        Ensures graceful degradation when cache backend fails
        Confirms cache monitoring provides accurate operational visibility

    Integration Scope:
        Health checker initialization → Cache service dependency → Health check execution
    """

    async def test_cache_health_check_reports_healthy_with_redis_available(
        self, health_checker, mock_cache_service
    ):
        """
        Test cache health check returns HEALTHY when Redis connection successful.

        Integration Scope:
            Health checker → check_cache_health → AIResponseCache → Redis backend validation

        Contract Validation:
            - ComponentStatus with status=HEALTHY per health.pyi:640
            - response_time_ms includes connectivity test timing per health.pyi:266
            - metadata contains backend information per health.pyi:267
            - Dependency injection optimization per health.pyi:644-645

        Business Impact:
            Validates primary caching infrastructure operational for optimal performance
            Confirms Redis connectivity is properly validated and monitored
            Ensures cache health monitoring provides accurate status information

        Test Strategy:
            - Configure mock cache service to simulate healthy Redis backend
            - Use real cache health check function with dependency injection
            - Verify health status reflects Redis availability
            - Validate metadata includes backend information

        Success Criteria:
            - Cache component status is "healthy"
            - Metadata indicates Redis backend in use
            - Response time is measured and reasonable (< 500ms)
            - Dependency injection is utilized (no redundant instantiation)
        """
        # Arrange: Configure mock cache service for healthy Redis backend
        mock_cache_service.get_cache_stats.return_value = {
            "redis": {"status": "ok"},
            "memory": {"status": "ok"},
            "error": None,
        }

        # Act: Execute cache health check with dependency injection
        result = await health_checker.check_component("cache")

        # Assert: Cache reports healthy with Redis backend
        assert result.name == "cache"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0
        assert result.response_time_ms < 500, "Cache health check should be fast"

        # Verify metadata indicates Redis backend
        assert result.metadata is not None
        assert result.metadata.get("cache_type") in ["redis", "Redis", "REDIS"]

        # Verify mock was called (dependency injection used)
        mock_cache_service.get_cache_stats.assert_called_once()

    async def test_cache_health_check_reports_degraded_with_memory_fallback(
        self, health_checker, mock_cache_service
    ):
        """
        Test cache health check returns DEGRADED when Redis unavailable but memory cache works.

        Integration Scope:
            Health checker → check_cache_health → AIResponseCache fallback mechanism

        Contract Validation:
            - ComponentStatus with status=DEGRADED per health.pyi:640
            - Graceful degradation documented in AIResponseCache behavior
            - Metadata indicates fallback usage for operational visibility

        Business Impact:
            Demonstrates cache resilience through fallback to memory backend
            Alerts operations to reduced cache capacity without system failure
            Validates graceful degradation patterns in cache infrastructure

        Test Strategy:
            - Configure mock cache service to simulate Redis failure with memory fallback
            - Verify degraded status reported accurately
            - Test dependency injection pattern still works in fallback scenario
            - Validate metadata indicates fallback usage

        Success Criteria:
            - Cache component status is "degraded"
            - Message indicates fallback to memory cache
            - System remains operational with degraded functionality
            - Metadata reflects memory-only cache configuration
        """
        # Arrange: Configure mock cache service for memory fallback
        mock_cache_service.get_cache_stats.return_value = {
            "redis": {"status": "error", "error": "Connection timeout"},
            "memory": {"status": "ok"},
            "error": "Redis unavailable",
        }

        # Act: Execute cache health check
        result = await health_checker.check_component("cache")

        # Assert: Cache reports degraded with fallback
        assert result.name == "cache"
        assert result.status == HealthStatus.DEGRADED
        assert result.response_time_ms > 0

        # Verify message indicates fallback behavior
        assert "degraded" in result.message.lower() or "fallback" in result.message.lower()

        # Verify metadata indicates memory cache usage
        assert result.metadata is not None
        cache_type = result.metadata.get("cache_type", "").lower()
        assert "memory" in cache_type or "fallback" in cache_type

    async def test_cache_health_check_reports_unhealthy_on_complete_failure(
        self, health_checker, mock_cache_service
    ):
        """
        Test cache health check returns UNHEALTHY when cache service completely fails.

        Integration Scope:
            Health checker → check_cache_health → Exception handling → UNHEALTHY status

        Contract Validation:
            - ComponentStatus with status=UNHEALTHY when cache infrastructure fails
            - Exception handling preserves error information in message
            - Response time measurement includes failure handling overhead

        Business Impact:
            Alerts monitoring systems to complete cache infrastructure failure
            Validates health monitoring continues even when cache fails completely
            Ensures error information is preserved for troubleshooting

        Test Strategy:
            - Configure mock cache service to raise exception (complete failure)
            - Verify UNHEALTHY status is returned with error details
            - Test exception handling doesn't crash health monitoring
            - Validate error information is preserved in response

        Success Criteria:
            - Cache component status is "unhealthy"
            - Error message provides diagnostic information
            - Health check completes despite cache service failure
            - Response time is measured even for failed checks
        """
        # Arrange: Configure mock cache service to raise exception
        mock_cache_service.get_cache_stats.side_effect = Exception("Cache service crashed")

        # Act: Execute cache health check
        result = await health_checker.check_component("cache")

        # Assert: Cache reports unhealthy with error details
        assert result.name == "cache"
        assert result.status == HealthStatus.UNHEALTHY
        assert "failed" in result.message.lower() or "crashed" in result.message.lower()
        assert result.response_time_ms > 0

    async def test_cache_health_check_uses_dependency_injection_optimization(
        self, health_checker, mock_cache_service
    ):
        """
        Test cache health check uses dependency injection for optimal performance.

        Integration Scope:
            Health checker initialization → get_cache_service() dependency → check_cache_health()

        Contract Validation:
            - Dependency injection optimization per health.pyi:644-645
            - No redundant cache service instantiation
            - Reuses existing connections for optimal performance

        Business Impact:
            Ensures health monitoring doesn't create unnecessary service instances
            Validates efficient resource usage in health checks
            Confirms dependency injection patterns work correctly

        Test Strategy:
            - Execute multiple cache health checks in sequence
            - Verify dependency injection is used consistently
            - Monitor mock service calls to ensure no redundant instantiation
            - Test performance remains optimal with repeated calls

        Success Criteria:
            - Multiple health checks use the same injected service
            - No redundant service instantiation occurs
            - Performance remains consistent across repeated calls
            - Dependency injection pattern is verified through mock usage
        """
        # Arrange: Configure healthy cache service
        mock_cache_service.get_cache_stats.return_value = {
            "redis": {"status": "ok"},
            "memory": {"status": "ok"},
            "error": None,
        }

        # Act: Execute multiple health checks in sequence
        results = []
        for _ in range(3):
            result = await health_checker.check_component("cache")
            results.append(result)

        # Assert: Dependency injection used consistently
        assert len(results) == 3
        for result in results:
            assert result.status == HealthStatus.HEALTHY
            assert result.name == "cache"

        # Verify mock was called multiple times (reusing same service)
        assert mock_cache_service.get_cache_stats.call_count == 3

    async def test_cache_health_check_performance_characteristics(
        self, health_checker, mock_cache_service, performance_time_tracker
    ):
        """
        Test cache health check performance characteristics meet operational requirements.

        Integration Scope:
            Health checker → Cache health check execution → Performance measurement

        Contract Validation:
            - ComponentStatus.response_time_ms measurement per health.pyi:266
            - Fast execution suitable for high-frequency monitoring
            - Performance optimization through dependency injection

        Business Impact:
            Ensures cache health monitoring doesn't impact application performance
            Validates health checks are suitable for high-frequency monitoring
            Confirms performance requirements are met for operational use

        Test Strategy:
            - Measure cache health check execution time
            - Verify performance meets operational requirements
            - Test performance consistency across multiple executions
            - Validate dependency injection provides performance benefits

        Success Criteria:
            - Cache health check completes in < 200ms
            - Performance remains consistent across multiple calls
            - Response time measurement is accurate and included
            - Performance meets monitoring system requirements
        """
        # Arrange: Configure healthy cache service
        mock_cache_service.get_cache_stats.return_value = {
            "redis": {"status": "ok"},
            "memory": {"status": "ok"},
            "error": None,
        }

        # Act: Measure cache health check performance
        performance_time_tracker.start_measurement()
        result = await health_checker.check_component("cache")
        measured_time_ms = performance_time_tracker.end_measurement()

        # Assert: Performance characteristics
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0
        assert result.response_time_ms < 200, f"Cache health check took {result.response_time_ms:.1f}ms (expected < 200ms)"
        assert measured_time_ms < 500, f"Total measurement took {measured_time_ms:.1f}ms (expected < 500ms)"

    async def test_cache_health_check_metadata_collection(
        self, health_checker, mock_cache_service
    ):
        """
        Test cache health check collects comprehensive metadata for operational monitoring.

        Integration Scope:
            Health checker → Cache health check → Metadata collection and reporting

        Contract Validation:
            - ComponentStatus metadata contains cache-specific information per health.pyi:267
            - Backend type identification for operational visibility
            - Performance metrics and diagnostic information

        Business Impact:
            Provides operational visibility into cache infrastructure status
            Enables monitoring systems to understand cache configuration and performance
            Supports troubleshooting and capacity planning

        Test Strategy:
            - Test metadata collection with different cache configurations
            - Verify metadata includes operational information
            - Validate metadata structure and content accuracy
            - Test metadata consistency across health states

        Success Criteria:
            - Metadata includes cache type information
            - Backend status is reflected in metadata
            - Metadata structure is consistent and valid
            - Information supports operational monitoring needs
        """
        # Test Case 1: Healthy Redis backend
        mock_cache_service.get_cache_stats.return_value = {
            "redis": {"status": "ok", "connected_clients": 5},
            "memory": {"status": "ok", "items": 100},
            "error": None,
        }

        result = await health_checker.check_component("cache")
        assert result.metadata is not None
        assert "cache_type" in result.metadata
        assert result.metadata["cache_type"].lower() == "redis"

        # Test Case 2: Memory fallback
        mock_cache_service.get_cache_stats.return_value = {
            "redis": {"status": "error"},
            "memory": {"status": "ok", "items": 50},
            "error": "Redis unavailable",
        }

        result = await health_checker.check_component("cache")
        assert result.metadata is not None
        assert "cache_type" in result.metadata
        cache_type = result.metadata["cache_type"].lower()
        assert "memory" in cache_type


@pytest.mark.integration
class TestCacheHealthIntegrationWithRealServices:
    """
    Integration tests with actual cache service instances when available.

    These tests use real cache service instances to validate integration
    behavior in more realistic scenarios. They are marked as optional
    and can be skipped when Redis is not available in the test environment.
    """

    @pytest.mark.slow
    async def test_cache_health_check_with_real_cache_service(self, health_checker):
        """
        Test cache health check with real cache service instance.

        Integration Scope:
            Health checker → Real cache service → Actual backend connectivity

        Business Impact:
            Validates integration with actual cache infrastructure
            Confirms health checks work with real Redis/memory backends
            Tests end-to-end integration behavior

        Test Strategy:
            - Attempt to use real cache service if available
            - Test health check behavior with actual infrastructure
            - Gracefully skip if Redis not available in test environment
            - Validate realistic operational behavior

        Success Criteria:
            - Health check works with real cache service
            - Results reflect actual infrastructure state
            - Test gracefully handles missing Redis infrastructure
            - Performance characteristics are realistic
        """
        try:
            # Try to get real cache service
            from app.dependencies import get_cache_service
            real_cache_service = await get_cache_service()

            # Register health check with real service
            async def cache_health_with_real_service():
                from app.infrastructure.monitoring.health import check_cache_health
                return await check_cache_health(real_cache_service)

            health_checker.register_check("cache_real", cache_health_with_real_service)

            # Act: Test with real service
            result = await health_checker.check_component("cache_real")

            # Assert: Basic health check structure
            assert result.name == "cache_real"
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
            assert result.response_time_ms > 0
            assert result.metadata is not None

        except ImportError:
            pytest.skip("Real cache service not available for testing")
        except Exception as e:
            # If Redis is not available, we expect degraded but not failure
            if "redis" in str(e).lower() or "connection" in str(e).lower():
                # This is expected behavior - skip test
                pytest.skip(f"Redis not available for integration testing: {e}")
            else:
                # Unexpected error - fail the test
                raise

    async def test_cache_health_check_timeout_handling(self, health_checker):
        """
        Test cache health check properly handles timeout scenarios.

        Integration Scope:
            Health checker timeout management → Cache health check execution

        Business Impact:
            Validates health monitoring doesn't hang on slow cache operations
            Confirms timeout mechanisms protect overall system health monitoring
            Tests graceful degradation when cache operations are slow

        Test Strategy:
            - Configure short timeout for testing
            - Simulate slow cache operations
            - Verify timeout handling doesn't crash health monitoring
            - Test timeout results in appropriate status

        Success Criteria:
            - Slow cache operations result in DEGRADED status (timeout)
            - Health check completes within configured timeout
            - Overall health monitoring remains functional
            - Timeout is properly reported in status message
        """
        # Create health checker with very short timeout
        short_timeout_checker = HealthChecker(
            default_timeout_ms=100,  # Very short timeout
            retry_count=0,  # No retries for faster testing
        )

        # Mock cache service that is slow
        slow_cache_service = AsyncMock()
        slow_cache_service.get_cache_stats.side_effect = asyncio.sleep(0.2)  # 200ms delay

        # Register slow cache health check
        async def slow_cache_health():
            from app.infrastructure.monitoring.health import check_cache_health
            return await check_cache_health(slow_cache_service)

        short_timeout_checker.register_check("slow_cache", slow_cache_health)

        # Act: Execute health check with timeout
        result = await short_timeout_checker.check_component("slow_cache")

        # Assert: Timeout handled properly
        assert result.name == "slow_cache"
        assert result.status == HealthStatus.DEGRADED  # Timeout results in degraded
        assert "timeout" in result.message.lower() or "timed out" in result.message.lower()
        assert result.response_time_ms >= 100  # Should be at least the timeout duration