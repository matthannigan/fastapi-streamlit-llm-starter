"""
Integration tests for health check exception handling.

These tests verify the integration between health check exception handling
and the health monitoring system, ensuring proper error classification,
context preservation, and graceful degradation under failure conditions.

HIGH PRIORITY - Error handling and system stability
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

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


class TestHealthCheckExceptionHandlingIntegration:
    """
    Integration tests for health check exception handling.

    Seam Under Test:
        HealthCheckError → HealthCheckTimeoutError → Exception handling → Status aggregation

    Critical Path:
        Health check failure → Exception creation → Error context collection →
        Status determination → Error reporting

    Business Impact:
        Ensures health check failures are properly handled and don't crash
        the monitoring system, maintaining operational visibility even
        when individual components fail.

    Test Strategy:
        - Test custom exception hierarchy and error handling
        - Verify proper error context preservation
        - Confirm graceful degradation with component failures
        - Validate error reporting and status determination
        - Test timeout exception handling and recovery

    Success Criteria:
        - Custom health check exceptions are handled correctly
        - Error context is preserved and useful for debugging
        - System continues operating despite component failures
        - Proper status determination based on exception types
        - Response times remain reasonable during failures
    """

    def test_health_check_error_exception_hierarchy_and_context(
        self, health_checker, failing_health_check
    ):
        """
        Test HealthCheckError exception hierarchy and context preservation.

        Integration Scope:
            HealthChecker → HealthCheckError → Exception handling → Context preservation

        Business Impact:
            Ensures health check errors provide meaningful context for
            debugging and troubleshooting, enabling operators to quickly
            identify and resolve monitoring system issues.

        Test Strategy:
            - Register health check that raises HealthCheckError
            - Execute health check and capture exception context
            - Verify exception hierarchy and context preservation
            - Confirm error information is useful for debugging

        Success Criteria:
            - HealthCheckError is properly raised with context
            - Exception hierarchy allows for specific error handling
            - Error messages provide actionable debugging information
            - Component name is included in error context
        """
        health_checker.register_check("failing_component", failing_health_check)

        result = await health_checker.check_component("failing_component")

        # Verify error handling and context preservation
        assert result.name == "failing_component"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Simulated failure for testing" in result.message
        assert result.response_time_ms > 0

        # Verify HealthCheckError was properly handled
        assert isinstance(result, ComponentStatus)
        assert result.status != HealthStatus.HEALTHY

    def test_health_check_timeout_error_handling_and_recovery(
        self, health_checker, timeout_health_check
    ):
        """
        Test HealthCheckTimeoutError handling and recovery mechanisms.

        Integration Scope:
            HealthChecker → HealthCheckTimeoutError → Timeout handling → Recovery

        Business Impact:
            Ensures health checks don't hang indefinitely when components
            are unresponsive, maintaining monitoring system responsiveness
            and preventing monitoring system failures.

        Test Strategy:
            - Register health check that exceeds timeout
            - Execute health check and verify timeout handling
            - Confirm timeout exception is properly caught and handled
            - Verify system recovers and reports appropriate status

        Success Criteria:
            - Timeout exceptions are caught and handled gracefully
            - Health check doesn't hang indefinitely
            - Timeout errors are properly classified and reported
            - System continues operating after timeout failures
        """
        health_checker.register_check("timeout_component", timeout_health_check)

        result = await health_checker.check_component("timeout_component")

        # Verify timeout error handling
        assert result.name == "timeout_component"
        assert result.status == HealthStatus.DEGRADED  # Timeout should result in degraded status
        assert "timed out" in result.message.lower()
        assert result.response_time_ms > 0

        # Verify timeout was properly detected and handled
        assert isinstance(result, ComponentStatus)
        assert result.status != HealthStatus.HEALTHY

    def test_health_check_exception_context_preservation(
        self, health_checker
    ):
        """
        Test exception context preservation across health check failures.

        Integration Scope:
            HealthChecker → Exception context → Context preservation → Error reporting

        Business Impact:
            Ensures detailed error context is preserved and available
            for debugging and operational troubleshooting, enabling
            quick identification of health check failure causes.

        Test Strategy:
            - Create health check that fails with detailed context
            - Execute health check and verify context preservation
            - Confirm error context is useful for debugging
            - Validate context information is included in status

        Success Criteria:
            - Exception context is preserved and accessible
            - Error messages include relevant debugging information
            - Component-specific context is maintained
            - Context information aids in troubleshooting
        """
        def detailed_failure_check():
            """Health check that fails with detailed context."""
            raise HealthCheckError(
                "Database connection failed: Connection timeout after 30 seconds. "
                "Database server at db.example.com:5432 is not responding. "
                "Last successful connection was 5 minutes ago."
            )

        health_checker.register_check("database", detailed_failure_check)

        result = await health_checker.check_component("database")

        # Verify detailed context preservation
        assert result.name == "database"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Database connection failed" in result.message
        assert "Connection timeout" in result.message
        assert "db.example.com:5432" in result.message
        assert "5 minutes ago" in result.message

    def test_health_check_system_exception_aggregation(
        self, health_checker
    ):
        """
        Test system-wide exception handling and aggregation.

        Integration Scope:
            HealthChecker → Multiple component failures → Exception aggregation

        Business Impact:
            Ensures comprehensive system health monitoring works correctly
            even when multiple components fail, providing complete
            system visibility during widespread issues.

        Test Strategy:
            - Register multiple health checks with different failure types
            - Execute system health check with multiple failures
            - Verify exception aggregation and reporting
            - Confirm all failures are captured and reported

        Success Criteria:
            - Multiple component failures are all captured
            - Each failure maintains its specific error context
            - System health reflects multiple component failures
            - Response includes all relevant error information
        """
        # Register multiple failing health checks
        async def network_failure():
            raise HealthCheckError("Network connectivity lost: Unable to reach external API")

        async def service_crash():
            raise HealthCheckError("Service crashed: Process terminated unexpectedly")

        async def config_error():
            raise HealthCheckError("Configuration error: Invalid service configuration")

        health_checker.register_check("network", network_failure)
        health_checker.register_check("service", service_crash)
        health_checker.register_check("config", config_error)

        system_health = await health_checker.check_all_components()

        # Verify exception aggregation
        assert isinstance(system_health.overall_status, HealthStatus)
        assert system_health.overall_status == HealthStatus.UNHEALTHY
        assert len(system_health.components) == 3

        # Verify all individual failures are captured
        component_messages = [comp.message for comp in system_health.components]
        assert any("Network connectivity lost" in msg for msg in component_messages)
        assert any("Service crashed" in msg for msg in component_messages)
        assert any("Configuration error" in msg for msg in component_messages)

    def test_health_check_exception_handling_with_retry_logic(
        self, health_checker
    ):
        """
        Test exception handling integration with retry logic.

        Integration Scope:
            HealthChecker → Exception handling → Retry logic → Status determination

        Business Impact:
            Ensures health check retry mechanisms work correctly with
            exception handling, providing resilient monitoring that
            can recover from transient failures.

        Test Strategy:
            - Create health check with transient failures that succeed on retry
            - Execute health check with retry configuration
            - Verify retry logic works with exception handling
            - Confirm successful recovery after transient failures

        Success Criteria:
            - Retry logic executes correctly with exception handling
            - Transient failures are retried as configured
            - Successful recovery results in healthy status
            - Failed retries result in appropriate error status
        """
        # Create health check that fails once then succeeds (transient failure)
        attempt_count = 0
        async def transient_failure():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise HealthCheckError("Transient network error: Connection reset")
            return ComponentStatus("transient", HealthStatus.HEALTHY, "Service recovered")

        health_checker.register_check("transient", transient_failure)

        result = await health_checker.check_component("transient")

        # Verify retry logic with exception handling
        assert result.name == "transient"
        assert result.status == HealthStatus.HEALTHY
        assert "Service recovered" in result.message
        assert attempt_count == 2  # Should have retried once

    def test_health_check_exception_handling_performance_under_failure(
        self, health_checker
    ):
        """
        Test exception handling performance characteristics under failure conditions.

        Integration Scope:
            HealthChecker → Exception handling → Performance monitoring

        Business Impact:
            Ensures exception handling doesn't become a performance
            bottleneck during widespread component failures, maintaining
            monitoring system responsiveness even under stress.

        Test Strategy:
            - Register health checks that consistently fail
            - Execute health checks under failure conditions
            - Measure performance of exception handling
            - Verify response times remain reasonable despite failures

        Success Criteria:
            - Exception handling completes within performance requirements
            - Response times don't degrade excessively with failures
            - System remains responsive during widespread failures
            - Performance monitoring continues working despite exceptions
        """
        import time

        # Register multiple consistently failing health checks
        async def consistent_failure_1():
            raise HealthCheckError("Service 1 is down: Database connection pool exhausted")

        async def consistent_failure_2():
            raise HealthCheckError("Service 2 is down: API rate limit exceeded")

        async def consistent_failure_3():
            raise HealthCheckTimeoutError("Service 3 timeout: Processing queue overloaded")

        health_checker.register_check("service1", consistent_failure_1)
        health_checker.register_check("service2", consistent_failure_2)
        health_checker.register_check("service3", consistent_failure_3)

        start_time = time.time()
        system_health = await health_checker.check_all_components()
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        # Verify performance under failure conditions
        assert system_health.overall_status == HealthStatus.UNHEALTHY
        assert len(system_health.components) == 3
        assert response_time_ms > 0
        assert response_time_ms < 1000  # Should complete within 1 second even with failures

        # Verify all failures are properly captured
        component_messages = [comp.message for comp in system_health.components]
        assert any("Service 1 is down" in msg for msg in component_messages)
        assert any("Service 2 is down" in msg for msg in component_messages)
        assert any("Service 3 timeout" in msg for msg in component_messages)

    def test_health_check_exception_propagation_and_containment(
        self, health_checker
    ):
        """
        Test exception propagation and containment in health checks.

        Integration Scope:
            HealthChecker → Exception propagation → Containment → Status reporting

        Business Impact:
            Ensures exceptions from individual health checks are properly
            contained and don't propagate to crash the entire monitoring
            system, maintaining system stability during failures.

        Test Strategy:
            - Create health check that raises unexpected exception types
            - Execute health check and verify exception containment
            - Confirm unexpected exceptions are caught and handled
            - Verify system continues operating despite unexpected errors

        Success Criteria:
            - Unexpected exceptions are caught and contained
            - Exception information is preserved for debugging
            - System continues operating after unexpected exceptions
            - Error status reflects the underlying issue
        """
        # Create health check that raises unexpected exception
        async def unexpected_exception():
            raise ValueError("Unexpected runtime error: Null pointer exception")

        health_checker.register_check("unexpected", unexpected_exception)

        result = await health_checker.check_component("unexpected")

        # Verify exception containment and handling
        assert result.name == "unexpected"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Unexpected runtime error" in result.message
        assert "ValueError" in result.message or "Null pointer" in result.message

        # Verify health checker continues to function
        system_health = await health_checker.check_all_components()
        assert isinstance(system_health, type(system_health))
        assert len(system_health.components) > 0

    def test_health_check_exception_context_for_operational_debugging(
        self, health_checker
    ):
        """
        Test exception context for operational debugging scenarios.

        Integration Scope:
            HealthChecker → Exception context → Operational debugging → Troubleshooting

        Business Impact:
            Ensures health check exceptions provide sufficient context
            for operational teams to quickly diagnose and resolve
            monitoring system issues.

        Test Strategy:
            - Create health checks with various failure scenarios
            - Execute health checks and capture exception context
            - Verify context provides actionable debugging information
            - Confirm context helps with operational troubleshooting

        Success Criteria:
            - Exception context includes component identification
            - Error messages provide specific failure details
            - Context information aids in quick diagnosis
            - Troubleshooting information is readily available
        """
        # Create health checks with different failure contexts
        async def database_failure():
            raise HealthCheckError(
                f"Database health check failed for component '{database_failure.__name__}': "
                "Connection pool exhausted, 50/50 connections in use. "
                "Last successful query was 2 minutes ago."
            )

        async def api_failure():
            raise HealthCheckError(
                f"API health check failed for component '{api_failure.__name__}': "
                "External API returned 503 Service Unavailable. "
                "Rate limit: 1000 requests per hour, currently at 950."
            )

        health_checker.register_check("database", database_failure)
        health_checker.register_check("api", api_failure)

        # Execute health checks and verify context
        db_result = await health_checker.check_component("database")
        api_result = await health_checker.check_component("api")

        # Verify database failure context
        assert db_result.name == "database"
        assert "Database health check failed" in db_result.message
        assert "Connection pool exhausted" in db_result.message
        assert "50/50 connections in use" in db_result.message
        assert "2 minutes ago" in db_result.message

        # Verify API failure context
        assert api_result.name == "api"
        assert "API health check failed" in api_result.message
        assert "503 Service Unavailable" in api_result.message
        assert "1000 requests per hour" in api_result.message
        assert "950" in api_result.message

    def test_health_check_exception_recovery_and_resilience(
        self, health_checker
    ):
        """
        Test exception recovery and resilience in health monitoring.

        Integration Scope:
            HealthChecker → Exception recovery → System resilience → Continued operation

        Business Impact:
            Ensures health monitoring system remains operational and
            continues providing monitoring data even when individual
            components fail, maintaining operational visibility.

        Test Strategy:
            - Create mix of failing and healthy health checks
            - Execute system health check with mixed component states
            - Verify system recovers and continues operating
            - Confirm healthy components still report correctly

        Success Criteria:
            - System continues operating despite component failures
            - Healthy components are still properly monitored
            - Failed components don't prevent overall system operation
            - Recovery mechanisms work correctly after failures
        """
        # Create mix of failing and healthy components
        async def failing_component():
            raise HealthCheckError("Component is currently failing")

        async def healthy_component():
            return ComponentStatus("healthy_comp", HealthStatus.HEALTHY, "Component is working correctly")

        async def another_healthy():
            return ComponentStatus("another_healthy", HealthStatus.HEALTHY, "Another healthy component")

        health_checker.register_check("failing", failing_component)
        health_checker.register_check("healthy", healthy_component)
        health_checker.register_check("another", another_healthy)

        system_health = await health_checker.check_all_components()

        # Verify resilience and recovery
        assert system_health.overall_status == HealthStatus.DEGRADED  # One failure
        assert len(system_health.components) == 3

        # Verify healthy components still work
        healthy_components = [c for c in system_health.components if c.status == HealthStatus.HEALTHY]
        assert len(healthy_components) == 2
        assert healthy_components[0].name in ["healthy", "another"]
        assert healthy_components[1].name in ["healthy", "another"]

        # Verify failing component is properly reported
        failing_components = [c for c in system_health.components if c.status != HealthStatus.HEALTHY]
        assert len(failing_components) == 1
        assert failing_components[0].name == "failing"
        assert "Component is currently failing" in failing_components[0].message
