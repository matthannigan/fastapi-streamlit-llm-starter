"""
Integration Tests for Graceful Degradation and Exception Isolation (SEAM 6)

Tests the system's ability to degrade gracefully when components fail, isolate exceptions
to prevent cascade failures, maintain partial functionality during infrastructure issues,
and provide meaningful status reporting even during system degradation.

This test file validates the critical integration seam:
Component Failures → Exception Isolation → Graceful Degradation → Partial Functionality

Test Coverage:
- System-wide graceful degradation when multiple components fail
- Exception isolation preventing cascade failures
- Partial functionality maintenance during infrastructure issues
- Meaningful health status reporting during degradation
- Recovery patterns when failed components become available
- Performance characteristics during degraded operation
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    HealthCheckError,
    HealthCheckTimeoutError,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
)


@pytest.mark.integration
class TestGracefulDegradationAndExceptionIsolation:
    """
    Integration tests for graceful degradation and exception isolation patterns.

    Seam Under Test:
        Component Failures → Exception Isolation → Graceful Degradation → Partial Functionality

    Critical Paths:
        - Multiple component failures trigger graceful degradation rather than complete failure
        - Exceptions in one component don't cascade to affect other components
        - System maintains partial functionality when infrastructure components fail
        - Health monitoring continues to provide meaningful status during degradation
        - Recovery patterns when failed components become available again

    Business Impact:
        Ensures system remains operational during partial infrastructure failures
        Validates monitoring systems can detect and report degradation accurately
        Confirms exception isolation prevents cascade failures across components
        Tests recovery patterns when infrastructure issues are resolved

    Integration Scope:
        HealthChecker → Multiple Component Health Checks → Exception Isolation → Aggregated Status
    """

    async def test_health_checker_degrades_gracefully_when_multiple_components_fail(self):
        """
        Test HealthChecker degrades gracefully when multiple components fail simultaneously.

        Integration Scope:
            HealthChecker → Multiple failing component checks → Graceful degradation → Aggregated status

        Contract Validation:
            - SystemHealthStatus.overall_status reflects worst component status
            - Partial failures don't prevent health checking of other components
            - Exception isolation prevents one failure from affecting others
            - Health monitoring continues despite multiple component failures

        Business Impact:
            Ensures system can report on remaining operational capacity during widespread issues
            Validates monitoring systems can track multiple concurrent failures
            Confirms partial functionality reporting during infrastructure degradation

        Test Strategy:
            - Configure multiple components to fail in different ways
            - Verify health checking continues for all components despite failures
            - Test that overall status reflects worst-case degradation
            - Validate exception isolation prevents cascade failures

        Success Criteria:
            - Health checker executes checks for all components despite failures
            - Overall status reflects most severe component failure
            - Individual component statuses are reported accurately
            - System continues providing health information during degradation
        """
        # Arrange: Create health checker with components that fail differently
        health_checker = HealthChecker(
            default_timeout_ms=1000,
            retry_count=0,  # No retries to speed up test
        )

        # Create failing health check functions
        async def failing_ai_check():
            raise HealthCheckError("AI model configuration missing")

        async def timeout_cache_check():
            await asyncio.sleep(2.0)  # Longer than timeout
            return ComponentStatus("cache", HealthStatus.HEALTHY, "Should not reach")

        async def healthy_resilience_check():
            return ComponentStatus("resilience", HealthStatus.HEALTHY, "OK")

        # Register checks with different failure modes
        health_checker.register_check("ai_model", failing_ai_check)
        health_checker.register_check("cache", timeout_cache_check)
        health_checker.register_check("resilience", healthy_resilience_check)

        # Act: Execute all health checks
        system_status = await health_checker.check_all_components()

        # Assert: Graceful degradation with accurate status reporting
        assert system_status is not None
        assert system_status.overall_status == HealthStatus.UNHEALTHY  # Worst case

        # Verify all components were checked despite failures
        assert len(system_status.component_statuses) == 3

        # Check individual component statuses
        ai_status = system_status.get_component_status("ai_model")
        cache_status = system_status.get_component_status("cache")
        resilience_status = system_status.get_component_status("resilience")

        # AI should show UNHEALTHY due to configuration error
        assert ai_status.status == HealthStatus.UNHEALTHY
        assert "configuration" in ai_status.message.lower()

        # Cache should show DEGRADED due to timeout
        assert cache_status.status == HealthStatus.DEGRADED
        assert "timeout" in cache_status.message.lower()

        # Resilience should remain HEALTHY (exception isolation)
        assert resilience_status.status == HealthStatus.HEALTHY
        assert resilience_status.message == "OK"

        # Verify system provides meaningful information during degradation
        assert system_status.timestamp is not None
        assert system_status.total_components == 3
        assert system_status.healthy_components == 1
        assert system_status.degraded_components == 1
        assert system_status.unhealthy_components == 1

    async def test_health_checker_isolates_exceptions_to_prevent_cascade_failures(self):
        """
        Test HealthChecker isolates exceptions to prevent cascade failures between components.

        Integration Scope:
            HealthChecker → Exception isolation → Independent component checking → Prevent cascade

        Contract Validation:
            - Exceptions in one component don't affect checking of other components
            - Health checker attempts all registered checks regardless of individual failures
            - Component status reporting remains independent and accurate
            - Overall system status aggregation handles mixed success/failure scenarios

        Business Impact:
            Prevents single component failures from affecting health monitoring of other components
            Ensures comprehensive system visibility even during partial outages
            Validates isolation patterns protect system stability during component failures

        Test Strategy:
            - Configure one component to raise an exception
            - Verify other components are still checked successfully
            - Test that exception doesn't prevent other health checks from executing
            - Validate independent status reporting for each component

        Success Criteria:
            - All components are checked regardless of individual failures
            - One component's exception doesn't affect others' execution
            - Component statuses are reported independently and accurately
            - System continues providing partial health information
        """
        # Arrange: Create health checker with mixed success/failure scenarios
        health_checker = HealthChecker(retry_count=0)

        execution_order = []

        async def failing_check():
            execution_order.append("failing")
            raise HealthCheckError("Component failure")

        async def healthy_check_1():
            execution_order.append("healthy_1")
            return ComponentStatus("healthy_1", HealthStatus.HEALTHY, "Component OK")

        async def healthy_check_2():
            execution_order.append("healthy_2")
            return ComponentStatus("healthy_2", HealthStatus.HEALTHY, "Component OK")

        async def timeout_check():
            execution_order.append("timeout")
            await asyncio.sleep(0.5)  # Cause timeout
            return ComponentStatus("timeout", HealthStatus.HEALTHY, "Should not reach")

        # Register checks in predictable order
        health_checker.register_check("healthy_1", healthy_check_1)
        health_checker.register_check("failing", failing_check)
        health_checker.register_check("healthy_2", healthy_check_2)
        health_checker.register_check("timeout", timeout_check)

        # Act: Execute all health checks
        system_status = await health_checker.check_all_components()

        # Assert: Exception isolation prevents cascade failures
        assert system_status is not None
        assert system_status.overall_status == HealthStatus.UNHEALTHY  # Worst case

        # Verify all components were attempted despite failures
        assert len(execution_order) == 4
        assert "healthy_1" in execution_order
        assert "failing" in execution_order
        assert "healthy_2" in execution_order
        assert "timeout" in execution_order

        # Verify independent status reporting
        healthy_1_status = system_status.get_component_status("healthy_1")
        failing_status = system_status.get_component_status("failing")
        healthy_2_status = system_status.get_component_status("healthy_2")
        timeout_status = system_status.get_component_status("timeout")

        assert healthy_1_status.status == HealthStatus.HEALTHY
        assert failing_status.status == HealthStatus.UNHEALTHY
        assert healthy_2_status.status == HealthStatus.HEALTHY
        assert timeout_status.status == HealthStatus.DEGRADED

        # Verify system maintains partial functionality reporting
        assert system_status.healthy_components == 2
        assert system_status.unhealthy_components == 1
        assert system_status.degraded_components == 1

    async def test_health_checker_maintains_partial_functionality_during_infrastructure_issues(self):
        """
        Test HealthChecker maintains partial functionality during infrastructure issues.

        Integration Scope:
            HealthChecker → Infrastructure component failures → Partial functionality → Meaningful reporting

        Contract Validation:
            - Health checking continues for available components during infrastructure issues
            - System reports what functionality remains operational
            - Partial degradation is communicated clearly through status aggregation
            - Health monitoring itself remains operational despite component failures

        Business Impact:
            Ensures monitoring systems can track remaining operational capacity
            Validates partial functionality reporting during infrastructure degradation
            Confirms health monitoring system resilience during component failures

        Test Strategy:
            - Simulate infrastructure component failures (cache, AI services)
            - Verify health checking continues for non-affected components
            - Test that partial functionality is accurately reported
            - Validate health monitoring system remains operational

        Success Criteria:
            - Health monitoring continues despite infrastructure component failures
            - Partial functionality is accurately reported in system status
            - Non-affected components continue to be checked successfully
            - System provides clear indication of what remains operational
        """
        # Arrange: Create health checker with infrastructure dependency simulation
        health_checker = HealthChecker(default_timeout_ms=500, retry_count=1)

        # Simulate infrastructure component failures
        infrastructure_failure = True

        async def cache_dependency_check():
            if infrastructure_failure:
                raise HealthCheckError("Redis connection failed")
            return ComponentStatus("cache", HealthStatus.HEALTHY, "Cache operational")

        async def ai_service_check():
            if infrastructure_failure:
                raise HealthCheckTimeoutError("AI service timeout")
            return ComponentStatus("ai", HealthStatus.HEALTHY, "AI service OK")

        async def internal_system_check():
            # This check doesn't depend on external infrastructure
            return ComponentStatus("internal", HealthStatus.HEALTHY, "Internal systems OK")

        async def database_check():
            if infrastructure_failure:
                # Simulate degraded but functional database
                return ComponentStatus("database", HealthStatus.DEGRADED, "Slow response but functional")
            return ComponentStatus("database", HealthStatus.HEALTHY, "Database OK")

        # Register checks with infrastructure dependencies
        health_checker.register_check("cache", cache_dependency_check)
        health_checker.register_check("ai", ai_service_check)
        health_checker.register_check("internal", internal_system_check)
        health_checker.register_check("database", database_check)

        # Act: Execute health checks during infrastructure failure
        system_status = await health_checker.check_all_components()

        # Assert: Partial functionality maintained during infrastructure issues
        assert system_status is not None
        assert system_status.overall_status == HealthStatus.UNHEALTHY  # Due to failures

        # Verify partial functionality reporting
        assert system_status.total_components == 4
        assert system_status.healthy_components == 1  # Only internal system
        assert system_status.degraded_components == 1  # Database
        assert system_status.unhealthy_components == 2  # Cache and AI

        # Verify individual component status accuracy
        cache_status = system_status.get_component_status("cache")
        ai_status = system_status.get_component_status("ai")
        internal_status = system_status.get_component_status("internal")
        database_status = system_status.get_component_status("database")

        assert cache_status.status == HealthStatus.UNHEALTHY
        assert ai_status.status == HealthStatus.DEGRADED  # Timeout maps to DEGRADED
        assert internal_status.status == HealthStatus.HEALTHY
        assert database_status.status == HealthStatus.DEGRADED

        # Now test recovery scenario
        infrastructure_failure = False
        recovery_status = await health_checker.check_all_components()

        # Verify recovery is detected and reported
        assert recovery_status.overall_status == HealthStatus.HEALTHY
        assert recovery_status.healthy_components == 4
        assert recovery_status.degraded_components == 0
        assert recovery_status.unhealthy_components == 0

    async def test_health_checker_provides_meaningful_status_during_degradation(self):
        """
        Test HealthChecker provides meaningful status reporting during system degradation.

        Integration Scope:
            Component failures → Status aggregation → Meaningful degradation reporting → System insights

        Contract Validation:
            - SystemHealthStatus provides detailed breakdown during degradation
            - Component-specific failure information is preserved and reported
            - Timing and metadata collection continues during component failures
            - Status aggregation logic provides insights into degradation scope and impact

        Business Impact:
            Enables operations teams to understand scope and impact of system degradation
            Provides actionable information for troubleshooting and recovery
            Validates monitoring system provides value during operational issues

        Test Strategy:
            - Create scenarios with different types and severities of component failures
            - Verify status reporting provides detailed breakdown of issues
            - Test that timing information is collected even for failed components
            - Validate aggregation logic provides meaningful degradation insights

        Success Criteria:
            - Detailed component status breakdown provided during degradation
            - Failure information preserved with specific error details
            - Timing data collected for both successful and failed components
            - System status provides clear indication of degradation scope
        """
        # Arrange: Create health checker with diverse failure scenarios
        health_checker = HealthChecker(default_timeout_ms=1000, retry_count=1)

        async def critical_component_failure():
            await asyncio.sleep(0.1)  # Add some execution time
            raise HealthCheckError("Critical service unavailable")

        async def non_critical_timeout():
            await asyncio.sleep(2.0)  # Cause timeout
            return ComponentStatus("non_critical", HealthStatus.HEALTHY, "Should not reach")

        async def degraded_service():
            return ComponentStatus("degraded", HealthStatus.DEGRADED, "Service responding slowly")

        async def healthy_component():
            await asyncio.sleep(0.05)
            return ComponentStatus("healthy", HealthStatus.HEALTHY, "Fully operational")

        # Register components with different failure modes
        health_checker.register_check("critical", critical_component_failure)
        health_checker.register_check("non_critical", non_critical_timeout)
        health_checker.register_check("degraded", degraded_service)
        health_checker.register_check("healthy", healthy_component)

        # Act: Execute health checks with diverse failure scenarios
        start_time = time.time()
        system_status = await health_checker.check_all_components()
        end_time = time.time()

        # Assert: Meaningful status reporting during degradation
        assert system_status is not None
        assert system_status.overall_status == HealthStatus.UNHEALTHY

        # Verify detailed component breakdown
        assert len(system_status.component_statuses) == 4

        critical_status = system_status.get_component_status("critical")
        non_critical_status = system_status.get_component_status("non_critical")
        degraded_status = system_status.get_component_status("degraded")
        healthy_status = system_status.get_component_status("healthy")

        # Verify status accuracy and detail
        assert critical_status.status == HealthStatus.UNHEALTHY
        assert "unavailable" in critical_status.message.lower()
        assert critical_status.response_time_ms > 0  # Timing collected

        assert non_critical_status.status == HealthStatus.DEGRADED
        assert "timeout" in non_critical_status.message.lower()
        assert non_critical_status.response_time_ms > 0

        assert degraded_status.status == HealthStatus.DEGRADED
        assert "slowly" in degraded_status.message.lower()
        assert degraded_status.response_time_ms > 0

        assert healthy_status.status == HealthStatus.HEALTHY
        assert healthy_status.response_time_ms > 0

        # Verify aggregation provides meaningful insights
        assert system_status.total_components == 4
        assert system_status.healthy_components == 1
        assert system_status.degraded_components == 2
        assert system_status.unhealthy_components == 1

        # Verify timing information is meaningful
        total_execution_time = (end_time - start_time) * 1000
        assert total_execution_time > 100  # Should take some time due to sleeps
        assert system_status.timestamp is not None

        # Verify system status provides actionable information
        status_summary = system_status.get_status_summary()
        assert status_summary is not None
        assert "UNHEALTHY" in status_summary
        assert "1 healthy" in status_summary
        assert "2 degraded" in status_summary
        assert "1 unhealthy" in status_summary

    async def test_health_checker_recovery_patterns_after_component_restoration(self):
        """
        Test HealthChecker recovery patterns when failed components become available again.

        Integration Scope:
            Component failures → Recovery detection → Status restoration → Normal operation

        Contract Validation:
            - Health checker detects when failed components become available
            - System status updates appropriately when components recover
            - Recovery patterns handle different types of failure restoration
            - Performance characteristics return to normal after recovery

        Business Impact:
            Validates system can automatically recover from infrastructure issues
            Ensures monitoring systems detect and report recovery accurately
            Confirms restoration patterns work as expected for operational recovery

        Test Strategy:
            - Create initial failure state with multiple component failures
            - Simulate component recovery scenarios
            - Verify health checker detects and reports recovery
            - Test that system status updates appropriately during recovery

        Success Criteria:
            - Component recovery is detected and reported accurately
            - System status improves appropriately as components recover
            - Full recovery returns system to healthy status
            - Recovery patterns work for different failure types
        """
        # Arrange: Create health checker with recoverable component failures
        health_checker = HealthChecker(default_timeout_ms=1000, retry_count=1)

        # Track component states for recovery simulation
        component_states = {
            "ai": "failed",
            "cache": "degraded",
            "resilience": "healthy"
        }

        async def ai_service_check():
            if component_states["ai"] == "failed":
                raise HealthCheckError("AI service configuration missing")
            elif component_states["ai"] == "degraded":
                return ComponentStatus("ai", HealthStatus.DEGRADED, "AI service slow")
            else:  # healthy
                return ComponentStatus("ai", HealthStatus.HEALTHY, "AI service OK")

        async def cache_service_check():
            if component_states["cache"] == "failed":
                raise HealthCheckError("Cache connection failed")
            elif component_states["cache"] == "degraded":
                return ComponentStatus("cache", HealthStatus.DEGRADED, "Cache high latency")
            else:  # healthy
                return ComponentStatus("cache", HealthStatus.HEALTHY, "Cache OK")

        async def resilience_service_check():
            return ComponentStatus("resilience", HealthStatus.HEALTHY, "Resilience OK")

        # Register components
        health_checker.register_check("ai", ai_service_check)
        health_checker.register_check("cache", cache_service_check)
        health_checker.register_check("resilience", resilience_service_check)

        # Act 1: Initial failure state
        initial_status = await health_checker.check_all_components()
        assert initial_status.overall_status == HealthStatus.UNHEALTHY
        assert initial_status.unhealthy_components >= 1

        # Act 2: Partial recovery (AI service recovers)
        component_states["ai"] = "degraded"
        partial_recovery_status = await health_checker.check_all_components()
        assert partial_recovery_status.overall_status == HealthStatus.DEGRADED  # Improved but not fully healthy
        assert partial_recovery_status.unhealthy_components == 0  # AI no longer unhealthy
        assert partial_recovery_status.degraded_components >= 1  # But still degraded

        # Act 3: Full recovery (all components healthy)
        component_states["ai"] = "healthy"
        component_states["cache"] = "healthy"
        full_recovery_status = await health_checker.check_all_components()
        assert full_recovery_status.overall_status == HealthStatus.HEALTHY
        assert full_recovery_status.healthy_components == 3
        assert full_recovery_status.degraded_components == 0
        assert full_recovery_status.unhealthy_components == 0

        # Assert: Recovery patterns work correctly
        # Verify AI component recovery
        ai_initial = initial_status.get_component_status("ai")
        ai_partial = partial_recovery_status.get_component_status("ai")
        ai_full = full_recovery_status.get_component_status("ai")

        assert ai_initial.status == HealthStatus.UNHEALTHY
        assert ai_partial.status == HealthStatus.DEGRADED
        assert ai_full.status == HealthStatus.HEALTHY

        # Verify Cache component recovery
        cache_initial = initial_status.get_component_status("cache")
        cache_full = full_recovery_status.get_component_status("cache")

        assert cache_initial.status == HealthStatus.DEGRADED
        assert cache_full.status == HealthStatus.HEALTHY

        # Verify system status progression
        assert initial_status.overall_status.value < partial_recovery_status.overall_status.value
        assert partial_recovery_status.overall_status.value < full_recovery_status.overall_status.value

    async def test_health_checker_performance_during_degraded_operation(self):
        """
        Test HealthChecker performance characteristics during degraded operation.

        Integration Scope:
            Component failures → Degraded operation → Performance validation → Response time analysis

        Contract Validation:
            - Health checker performance remains acceptable during component failures
            - Component timeouts don't significantly impact overall health check duration
            - Concurrent execution pattern prevents cascade performance degradation
            - Response time reporting remains accurate during failures

        Business Impact:
            Ensures health monitoring doesn't become bottleneck during system degradation
            Validates monitoring system performance under stress conditions
            Confirms health checking remains efficient during operational issues

        Test Strategy:
            - Create scenarios with component timeouts and failures
            - Measure health checker performance during degradation
            - Verify concurrent execution prevents worst-case performance
            - Test response time reporting accuracy during failures

        Success Criteria:
            - Overall health check time remains within acceptable bounds during failures
            - Concurrent execution prevents sequential timeout accumulation
            - Component failures don't disproportionately impact overall performance
            - Response time data remains accurate and meaningful during degradation
        """
        # Arrange: Create health checker with performance tracking
        health_checker = HealthChecker(
            default_timeout_ms=500,
            retry_count=0,  # No retries for faster test execution
        )

        async def fast_healthy_check():
            await asyncio.sleep(0.01)  # Very fast
            return ComponentStatus("fast", HealthStatus.HEALTHY, "Fast component")

        async def slow_timeout_check():
            await asyncio.sleep(1.0)  # Will timeout
            return ComponentStatus("slow", HealthStatus.HEALTHY, "Should not reach")

        async def moderate_degraded_check():
            await asyncio.sleep(0.1)
            return ComponentStatus("moderate", HealthStatus.DEGRADED, "Slow response")

        async def error_check():
            await asyncio.sleep(0.02)
            raise HealthCheckError("Component error")

        # Register components with different performance characteristics
        health_checker.register_check("fast", fast_healthy_check)
        health_checker.register_check("slow", slow_timeout_check)
        health_checker.register_check("moderate", moderate_degraded_check)
        health_checker.register_check("error", error_check)

        # Act: Execute health checks and measure performance during degradation
        start_time = time.time()
        system_status = await health_checker.check_all_components()
        end_time = time.time()

        total_execution_time_ms = (end_time - start_time) * 1000

        # Assert: Performance remains acceptable during degraded operation
        assert system_status is not None
        assert system_status.overall_status == HealthStatus.UNHEALTHY

        # Performance should be better than sequential execution (which would be >1000ms)
        assert total_execution_time_ms < 800, f"Health check took {total_execution_time_ms:.1f}ms, expected <800ms for concurrent execution"

        # Verify individual component timing accuracy
        fast_status = system_status.get_component_status("fast")
        slow_status = system_status.get_component_status("slow")
        moderate_status = system_status.get_component_status("moderate")
        error_status = system_status.get_component_status("error")

        # Fast component should complete quickly
        assert fast_status.response_time_ms < 50
        assert fast_status.status == HealthStatus.HEALTHY

        # Slow component should timeout (close to timeout limit)
        assert slow_status.response_time_ms >= 400  # Should be close to 500ms timeout
        assert slow_status.status == HealthStatus.DEGRADED  # Timeout maps to DEGRADED

        # Moderate component should show its actual execution time
        assert moderate_status.response_time_ms >= 80
        assert moderate_status.status == HealthStatus.DEGRADED

        # Error component should show its execution time before error
        assert error_status.response_time_ms >= 15
        assert error_status.status == HealthStatus.UNHEALTHY

        # Verify timing data is consistent and meaningful
        for component_status in system_status.component_statuses:
            assert component_status.response_time_ms > 0
            assert component_status.response_time_ms < total_execution_time_ms + 100  # Allow some margin

        # Verify system provides timing insights during degradation
        assert system_status.timestamp is not None
        timing_summary = system_status.get_timing_summary()
        assert timing_summary is not None
        assert "ms" in timing_summary


@pytest.mark.slow
@pytest.mark.performance
class TestHealthCheckerResiliencePatterns:
    """
    Performance and resilience tests for health checker under extreme degradation scenarios.

    Tests health checker behavior under stress conditions including high failure rates,
    concurrent execution patterns, and resource utilization during system degradation.
    These tests are marked as slow and should be run separately from core integration tests.

    Resilience Characteristics:
        - High failure rate handling
        - Concurrent execution under stress
        - Resource utilization patterns
        - Recovery performance after degradation
    """

    async def test_health_checker_high_failure_rate_resilience(self):
        """
        Test health checker resilience under high component failure rates.

        Resilience Characteristic:
            Validates health checker continues functioning when most components fail

        Success Criteria:
            - Health checker remains operational with 80%+ component failure rate
            - Performance remains acceptable despite widespread failures
            - Status reporting remains accurate under high failure conditions
            - Recovery patterns work after widespread failure resolution
        """
        # Arrange: Create health checker with high failure rate
        health_checker = HealthChecker(default_timeout_ms=200, retry_count=0)

        # Create 10 components with 80% failure rate
        async def healthy_check(component_id):
            return ComponentStatus(f"healthy_{component_id}", HealthStatus.HEALTHY, "OK")

        async def failing_check(component_id):
            raise HealthCheckError(f"Component {component_id} failed")

        async def timeout_check(component_id):
            await asyncio.sleep(0.5)  # Will timeout
            return ComponentStatus(f"timeout_{component_id}", HealthStatus.HEALTHY, "Should not reach")

        # Register 2 healthy, 5 failing, 3 timeout components
        for i in range(2):
            health_checker.register_check(f"healthy_{i}", lambda i=i: healthy_check(i))

        for i in range(5):
            health_checker.register_check(f"failing_{i}", lambda i=i: failing_check(i))

        for i in range(3):
            health_checker.register_check(f"timeout_{i}", lambda i=i: timeout_check(i))

        # Act: Execute health checks with high failure rate
        start_time = time.time()
        system_status = await health_checker.check_all_components()
        end_time = time.time()

        # Assert: Resilience under high failure rate
        assert system_status is not None
        assert system_status.overall_status == HealthStatus.UNHEALTHY
        assert system_status.total_components == 10
        assert system_status.healthy_components == 2
        assert system_status.unhealthy_components == 5
        assert system_status.degraded_components == 3

        # Performance should remain reasonable despite failures
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 1000, f"High failure rate check took {execution_time_ms:.1f}ms"

        # Verify all components were attempted despite high failure rate
        assert len(system_status.component_statuses) == 10

        # Verify status accuracy for each component type
        for component_status in system_status.component_statuses:
            if component_status.component_id.startswith("healthy_"):
                assert component_status.status == HealthStatus.HEALTHY
            elif component_status.component_id.startswith("failing_"):
                assert component_status.status == HealthStatus.UNHEALTHY
            elif component_status.component_id.startswith("timeout_"):
                assert component_status.status == HealthStatus.DEGRADED

    async def test_health_checker_concurrent_degradation_handling(self):
        """
        Test health checker concurrent execution during system-wide degradation.

        Resilience Characteristic:
            Validates concurrent health checking efficiency during degradation scenarios

        Success Criteria:
            - Concurrent execution prevents sequential timeout accumulation
            - Multiple health check requests can be handled simultaneously during degradation
            - Performance scales appropriately with concurrent degradation scenarios
            - Status consistency maintained across concurrent degradation scenarios
        """
        # Arrange: Create health checker with degradation-prone components
        health_checker = HealthChecker(default_timeout_ms=300, retry_count=0)

        async def variable_delay_check(delay):
            await asyncio.sleep(delay)
            return ComponentStatus(f"delay_{delay}", HealthStatus.HEALTHY, f"Delay {delay}")

        async def error_prone_check():
            await asyncio.sleep(0.05)
            raise HealthCheckError("Random failure")

        # Register components with different characteristics
        health_checker.register_check("error", error_prone_check)
        for delay in [0.1, 0.2, 0.4]:  # Mix of fast, moderate, and timeout delays
            health_checker.register_check(f"delay_{delay}", lambda d=delay: variable_delay_check(d))

        # Act: Execute concurrent health checks during degradation
        tasks = []
        for _ in range(3):  # 3 concurrent health check requests
            task = health_checker.check_all_components()
            tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Assert: Concurrent degradation handling
        assert len(results) == 3

        # All results should be consistent
        for result in results:
            assert result is not None
            assert result.overall_status == HealthStatus.UNHEALTHY
            assert result.total_components == 4

        # Concurrent execution should be faster than sequential
        total_time_ms = (end_time - start_time) * 1000
        assert total_time_ms < 600, f"Concurrent degradation took {total_time_ms:.1f}ms"

        # Verify results are consistent across concurrent requests
        first_result = results[0]
        for result in results[1:]:
            assert result.overall_status == first_result.overall_status
            assert result.total_components == first_result.total_components
            assert result.healthy_components == first_result.healthy_components
            assert result.unhealthy_components == first_result.unhealthy_components
            assert result.degraded_components == first_result.degraded_components