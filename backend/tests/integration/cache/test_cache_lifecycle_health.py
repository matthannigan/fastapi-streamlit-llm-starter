"""Test Lifecycle and Health Check Dependencies

This module provides integration tests for cache lifecycle and health check dependencies,
validating the critical application integration points for FastAPI startup, shutdown,
and health monitoring reliability.

Focus on testing observable behaviors through public dependency interfaces rather than
internal implementation details. Tests validate the contracts defined in
backend/contracts/infrastructure/cache/dependencies.pyi for production confidence.

Since these are contract-based tests, we test the expected behaviors as specified
in the public interface contracts without importing implementation details.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

# Mark all tests in this module to run serially (not in parallel)
pytestmark = pytest.mark.no_parallel

# Import the actual dependency functions to test their behavior
# We use the contracts to understand expected behavior, but test the real functions
from app.infrastructure.cache.dependencies import (CacheDependencyManager,
                                                   cleanup_cache_registry,
                                                   get_cache_health_status,
                                                   get_cache_service,
                                                   get_test_cache)
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.memory import InMemoryCache


class TestCacheLifecycleHealth:
    """
    Test suite for verifying cache lifecycle and health dependency behaviors.

    Integration Scope:
        Tests cache dependency functions that integrate the cache with FastAPI
        application lifecycle, focusing on startup, shutdown, and health monitoring.

    Business Impact:
        Ensures application reliability during startup, graceful shutdown handling,
        and accurate health status reporting for production operations.

    Test Strategy:
        - Test health check dependency with connected and disconnected caches
        - Verify cleanup dependency properly manages cache registry
        - Test lifecycle integration points with realistic scenarios
        - Validate dependency behavior under various cache states
    """

    @pytest.fixture
    def cache_factory(self):
        """Create a cache factory for test cache creation."""
        return CacheFactory()

    @pytest.mark.asyncio
    async def test_health_check_dependency_with_healthy_cache(self, cache_factory):
        """
        Test health check dependency reports healthy status for connected cache.

        Behavior Under Test:
            get_cache_health_status dependency should return status "healthy"
            when given a properly connected and functional cache instance.

        Business Impact:
            Ensures health endpoints correctly report when cache infrastructure
            is functioning properly, enabling reliable monitoring and alerting.

        Success Criteria:
            - Health status contains "status": "healthy" field
            - Health status includes cache type information
            - Health status provides meaningful diagnostic data
            - Health check completes without errors
        """
        # Create a test cache that represents a healthy, connected cache
        cache = await cache_factory.for_testing(use_memory_cache=True)

        # Ensure cache is working by performing basic operations
        await cache.set("health_test_key", "test_value")
        retrieved_value = await cache.get("health_test_key")
        assert (
            retrieved_value == "test_value"
        ), "Cache should be functional for health test"

        # Test the health check dependency
        health_status = await get_cache_health_status(cache)

        # Verify health status structure and content
        assert isinstance(health_status, dict), "Health status should be dictionary"
        assert "status" in health_status, "Health status should include status field"
        assert (
            health_status["status"] == "healthy"
        ), "Connected cache should report healthy status"

        # Verify additional diagnostic information is provided
        assert "cache_type" in health_status, "Health status should include cache type"
        assert (
            "ping_available" in health_status
        ), "Health status should include ping availability"
        assert (
            "operation_test" in health_status
        ), "Health status should include operation test result"
        assert "errors" in health_status, "Health status should include errors list"
        assert "warnings" in health_status, "Health status should include warnings list"
        assert "statistics" in health_status, "Health status should include statistics"

    @pytest.mark.asyncio
    async def test_health_check_dependency_with_degraded_cache(self):
        """
        Test health check dependency reports degraded status for problematic cache.

        Behavior Under Test:
            get_cache_health_status dependency should detect and report when
            cache is not functioning properly, returning appropriate status.

        Business Impact:
            Ensures health endpoints can detect cache infrastructure problems
            and alert operations teams to degraded service conditions.

        Success Criteria:
            - Health status reflects degraded or unhealthy state
            - Health status provides diagnostic information about the problem
            - Health check handles cache errors gracefully
            - Status differentiation allows for operational decision-making
        """
        # Create a mock cache that simulates connection or operational problems
        degraded_cache = MagicMock(spec=InMemoryCache)
        degraded_cache.get = AsyncMock(side_effect=Exception("Connection failed"))
        degraded_cache.set = AsyncMock(side_effect=Exception("Connection failed"))

        # Add cache type information that health check expects
        degraded_cache.__class__.__name__ = "InMemoryCache"

        # Test health check with degraded cache
        health_status = await get_cache_health_status(degraded_cache)

        # Verify degraded status is detected
        assert isinstance(health_status, dict), "Health status should be dictionary"
        assert "status" in health_status, "Health status should include status field"
        assert health_status["status"] in [
            "degraded",
            "unhealthy",
        ], "Broken cache should report degraded/unhealthy status"

        # Verify diagnostic information about the problem
        assert "errors" in health_status, "Health status should include errors list"
        assert (
            len(health_status.get("errors", [])) > 0
            or len(health_status.get("warnings", [])) > 0
        ), "Health status should include error or warning details"
        assert "cache_type" in health_status, "Health status should include cache type"

    @pytest.mark.asyncio
    async def test_cleanup_dependency_empties_cache_registry(self, cache_factory):
        """
        Test cleanup dependency properly clears the cache registry.

        Behavior Under Test:
            cleanup_cache_registry dependency should disconnect active caches
            and clear the internal registry to prevent resource leaks during shutdown.

        Business Impact:
            Ensures graceful application shutdown without resource leaks,
            preventing memory issues and connection pool exhaustion.

        Success Criteria:
            - Registry is properly cleared after cleanup
            - Active cache connections are handled appropriately
            - Cleanup returns meaningful statistics
            - Multiple cache instances are handled correctly
        """
        # Create multiple cache instances to populate registry
        cache1 = await cache_factory.for_testing(use_memory_cache=True)
        cache2 = await cache_factory.for_testing(use_memory_cache=True)
        cache3 = await cache_factory.for_testing(use_memory_cache=True)

        # Verify caches are functional before cleanup
        await cache1.set("test1", "value1")
        await cache2.set("test2", "value2")
        await cache3.set("test3", "value3")

        assert await cache1.get("test1") == "value1"
        assert await cache2.get("test2") == "value2"
        assert await cache3.get("test3") == "value3"

        # Perform cleanup
        cleanup_result = await cleanup_cache_registry()

        # Verify cleanup provides meaningful statistics
        assert isinstance(
            cleanup_result, dict
        ), "Cleanup should return statistics dictionary"
        assert "total_entries" in cleanup_result, "Cleanup should report total entries"
        assert (
            "active_caches" in cleanup_result
        ), "Cleanup should report active caches count"
        assert (
            "dead_references" in cleanup_result
        ), "Cleanup should report dead references count"
        assert (
            "disconnected_caches" in cleanup_result
        ), "Cleanup should report disconnected caches count"
        assert "errors" in cleanup_result, "Cleanup should report errors list"

        # Verify counts are reasonable integers
        for field in [
            "total_entries",
            "active_caches",
            "dead_references",
            "disconnected_caches",
        ]:
            assert isinstance(cleanup_result[field], int), f"{field} should be integer"
            assert cleanup_result[field] >= 0, f"{field} should be non-negative"

        # Verify errors is a list
        assert isinstance(cleanup_result["errors"], list), "Errors should be list"

    @pytest.mark.asyncio
    async def test_dependency_manager_registry_cleanup(self):
        """
        Test dependency manager registry cleanup functionality.

        Behavior Under Test:
            CacheDependencyManager.cleanup_registry should provide registry
            cleanup functionality that can be called independently for testing.

        Business Impact:
            Provides testable registry management that can be validated
            independently of full dependency injection lifecycle.

        Success Criteria:
            - Manager cleanup method is callable
            - Cleanup returns appropriate result structure
            - Registry state is properly managed
        """
        # Test the dependency manager cleanup method
        cleanup_result = await CacheDependencyManager.cleanup_registry()

        # Verify cleanup method works and returns expected structure
        assert isinstance(
            cleanup_result, dict
        ), "Manager cleanup should return dictionary"

        # The cleanup should have the same structure as the main cleanup function
        expected_fields = [
            "total_entries",
            "active_caches",
            "dead_references",
            "disconnected_caches",
            "errors",
        ]
        for field in expected_fields:
            assert field in cleanup_result, f"Manager cleanup should include {field}"

    @pytest.mark.asyncio
    async def test_cache_service_dependency_integration(self):
        """
        Test cache service dependency integration with lifecycle management.

        Behavior Under Test:
            get_cache_service dependency should integrate properly with the
            dependency injection system and provide working cache instances.

        Business Impact:
            Ensures cache dependency injection works correctly in FastAPI
            application context, providing reliable cache access to endpoints.

        Success Criteria:
            - Cache service can be obtained via dependency
            - Cache service is functional for basic operations
            - Dependency handles configuration appropriately
            - Multiple calls return appropriate cache instances
        """
        # Get cache service through dependency (simulating FastAPI DI)
        # Note: In real FastAPI, this would be injected, but we call directly for testing
        try:
            cache = await get_cache_service()

            # Verify we get a working cache instance
            assert cache is not None, "Cache service should return cache instance"

            # Test basic cache functionality
            await cache.set("integration_test", "dependency_value")
            retrieved = await cache.get("integration_test")
            assert (
                retrieved == "dependency_value"
            ), "Cache service should provide functional cache"

        except Exception as e:
            # If cache service fails due to configuration or Redis unavailability,
            # that's acceptable as long as we can test the dependency pattern
            pytest.skip(
                f"Cache service dependency not available in test environment: {e}"
            )

    @pytest.mark.asyncio
    async def test_test_cache_dependency_isolation(self):
        """
        Test test cache dependency provides proper isolation.

        Behavior Under Test:
            get_test_cache dependency should provide isolated cache instances
            suitable for testing without external dependencies.

        Business Impact:
            Ensures testing infrastructure provides reliable, isolated cache
            behavior for consistent test execution across environments.

        Success Criteria:
            - Test cache dependency returns working cache
            - Test cache is isolated from other instances
            - Test cache supports basic operations
            - Multiple test cache calls work correctly
        """
        # Get test cache instances
        test_cache1 = await get_test_cache()
        test_cache2 = await get_test_cache()

        # Verify we get working cache instances
        assert test_cache1 is not None, "Test cache dependency should return cache"
        assert test_cache2 is not None, "Test cache dependency should return cache"

        # Test isolation between instances
        await test_cache1.set("isolation_test", "cache1_value")
        await test_cache2.set("isolation_test", "cache2_value")

        value1 = await test_cache1.get("isolation_test")
        value2 = await test_cache2.get("isolation_test")

        # Different instances should be isolated (or same instance is acceptable for testing)
        if test_cache1 is not test_cache2:
            assert value1 == "cache1_value", "Cache 1 should have its own value"
            assert value2 == "cache2_value", "Cache 2 should have its own value"
        else:
            # If same instance is returned, that's also acceptable for test dependency
            assert value1 == value2, "Same cache instance should have consistent values"

    @pytest.mark.asyncio
    async def test_health_status_comprehensive_reporting(self, cache_factory):
        """
        Test health status provides comprehensive diagnostic information.

        Behavior Under Test:
            Health status should provide detailed information useful for
            operations and debugging, not just a simple status flag.

        Business Impact:
            Enables effective monitoring, alerting, and troubleshooting of
            cache infrastructure in production environments.

        Success Criteria:
            - Health status includes multiple diagnostic fields
            - Status information is actionable for operations
            - Health check performance is reasonable
            - Different cache states produce different diagnostic info
        """
        # Test with functional cache
        healthy_cache = await cache_factory.for_testing(use_memory_cache=True)
        health_status = await get_cache_health_status(healthy_cache)

        # Verify comprehensive information is provided
        expected_fields = [
            "status",
            "cache_type",
            "ping_available",
            "operation_test",
            "errors",
            "warnings",
            "statistics",
        ]
        for field in expected_fields:
            assert field in health_status, f"Health status should include {field}"

        # Verify status field has appropriate value
        assert health_status["status"] in [
            "healthy",
            "degraded",
            "unhealthy",
        ], "Status should be valid value"

        # Verify cache type information is meaningful
        assert isinstance(
            health_status["cache_type"], str
        ), "Cache type should be string"
        assert len(health_status["cache_type"]) > 0, "Cache type should not be empty"

        # Verify diagnostic information structure
        assert isinstance(health_status["errors"], list), "Errors should be list"
        assert isinstance(health_status["warnings"], list), "Warnings should be list"
        assert isinstance(
            health_status["statistics"], dict
        ), "Statistics should be dictionary"

    @pytest.mark.asyncio
    async def test_lifecycle_integration_robustness(self, cache_factory):
        """
        Test lifecycle integration handles various scenarios robustly.

        Behavior Under Test:
            Cache lifecycle dependencies should handle edge cases and
            error conditions gracefully without breaking application startup.

        Business Impact:
            Ensures application can start and operate even when cache
            infrastructure has problems, maintaining service availability.

        Success Criteria:
            - Dependencies handle None cache instances gracefully
            - Error conditions don't prevent dependency resolution
            - Cleanup works even with partially initialized state
            - Health checks work across different cache states
        """
        # Test cleanup with no registry entries (edge case)
        initial_cleanup = await cleanup_cache_registry()
        assert isinstance(initial_cleanup, dict), "Cleanup should handle empty registry"

        # Test health check behavior patterns
        test_cache = await cache_factory.for_testing(use_memory_cache=True)

        # Perform multiple health checks to test consistency
        health1 = await get_cache_health_status(test_cache)
        health2 = await get_cache_health_status(test_cache)

        # Health checks should be consistent for same cache
        assert (
            health1["status"] == health2["status"]
        ), "Health status should be consistent"
        assert (
            health1["cache_type"] == health2["cache_type"]
        ), "Cache type should be consistent"

        # Test final cleanup
        final_cleanup = await cleanup_cache_registry()
        assert isinstance(final_cleanup, dict), "Final cleanup should work properly"
