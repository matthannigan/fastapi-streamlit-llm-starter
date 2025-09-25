"""
Integration tests for health check timeout and retry behavior.

These tests verify the integration between health check timeout handling,
retry logic, and error recovery mechanisms, ensuring reliable health
monitoring under various failure conditions.

MEDIUM PRIORITY - Health check reliability and performance
"""

import pytest
import asyncio
import time
from unittest.mock import patch

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    HealthCheckError,
    HealthCheckTimeoutError,
)


class TestHealthCheckTimeoutRetryIntegration:
    """
    Integration tests for health check timeout and retry behavior.

    Seam Under Test:
        HealthChecker → Timeout handling → Retry logic → Error recovery

    Critical Path:
        Health check execution → Timeout detection → Retry execution →
        Status determination → Error handling

    Business Impact:
        Ensures health checks are reliable and don't hang or fail due to
        temporary issues, maintaining monitoring system availability
        and preventing monitoring gaps.

    Test Strategy:
        - Test timeout handling with various timeout configurations
        - Verify retry logic with different retry counts and backoff strategies
        - Confirm proper status determination based on timeout/retry outcomes
        - Validate performance characteristics under timeout conditions
        - Test integration between timeout and retry mechanisms

    Success Criteria:
        - Health checks don't hang indefinitely with proper timeouts
        - Retry logic executes correctly with configured parameters
        - Proper status determination based on timeout/retry outcomes
        - Response times remain reasonable despite timeouts
        - System handles timeout/retry scenarios gracefully
    """

    def test_health_check_timeout_handling_with_custom_timeout_configuration(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test health check timeout handling with custom timeout configuration.

        Integration Scope:
            HealthChecker → Custom timeouts → Timeout handling → Status determination

        Business Impact:
            Ensures health checks respect custom timeout configurations
            and handle timeout scenarios appropriately, maintaining
            monitoring system responsiveness.

        Test Strategy:
            - Use health checker with custom per-component timeouts
            - Register health check that exceeds component-specific timeout
            - Verify timeout is detected and handled correctly
            - Confirm proper status determination for timeout scenarios

        Success Criteria:
            - Component-specific timeouts are respected
            - Timeout detection works correctly
            - Health check doesn't hang beyond configured timeout
            - Status reflects timeout condition appropriately
        """
        # Register slow health check that will exceed fast_component timeout
        async def slow_component_check():
            await asyncio.sleep(1)  # 1000ms delay - exceeds 500ms timeout
            return ComponentStatus("slow_component", HealthStatus.HEALTHY, "Completed successfully")

        health_checker_with_custom_timeouts.register_check("slow_component", slow_component_check)

        result = await health_checker_with_custom_timeouts.check_component("slow_component")

        # Verify timeout handling with custom configuration
        assert result.name == "slow_component"
        assert result.status == HealthStatus.DEGRADED  # Timeout should result in degraded
        assert "timed out" in result.message.lower()
        assert result.response_time_ms > 0

        # Verify timeout was properly enforced (should be close to configured 500ms)
        assert result.response_time_ms < 1000  # Should not exceed 1 second

    def test_health_check_retry_logic_with_transient_failures(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test health check retry logic with transient failures that succeed on retry.

        Integration Scope:
            HealthChecker → Retry logic → Transient failure recovery → Status determination

        Business Impact:
            Ensures health monitoring can recover from transient failures,
            providing more reliable monitoring and reducing false
            positive alerts from temporary issues.

        Test Strategy:
            - Create health check with transient failures that succeed on retry
            - Configure retry count and backoff strategy
            - Execute health check and verify retry behavior
            - Confirm successful recovery from transient failures

        Success Criteria:
            - Retry logic executes according to configuration
            - Transient failures trigger appropriate retries
            - Successful recovery results in healthy status
            - Retry attempts are counted and limited correctly
        """
        # Create health check that fails once then succeeds (transient failure)
        attempt_count = 0
        async def transient_failure_check():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count <= 2:  # Fail first two attempts
                raise HealthCheckError(f"Transient failure attempt {attempt_count}")
            return ComponentStatus("transient", HealthStatus.HEALTHY, f"Succeeded on attempt {attempt_count}")

        health_checker_with_custom_timeouts.register_check("transient", transient_failure_check)

        result = await health_checker_with_custom_timeouts.check_component("transient")

        # Verify retry logic with transient failures
        assert result.name == "transient"
        assert result.status == HealthStatus.HEALTHY  # Should succeed on retry
        assert "Succeeded on attempt 3" in result.message
        assert attempt_count == 3  # Should have attempted 3 times

    def test_health_check_retry_logic_with_persistent_failures(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test health check retry logic with persistent failures that never succeed.

        Integration Scope:
            HealthChecker → Retry logic → Persistent failure handling → Status determination

        Business Impact:
            Ensures health monitoring properly handles persistent failures
            and reports appropriate status after exhausting retry attempts,
            providing accurate system health information.

        Test Strategy:
            - Create health check with persistent failures
            - Configure limited retry attempts
            - Execute health check and verify retry exhaustion
            - Confirm proper status determination after all retries fail

        Success Criteria:
            - Retry attempts are made according to configuration
            - Persistent failures result in unhealthy status
            - All retry attempts are exhausted before failure
            - Error context includes information about retry attempts
        """
        # Create health check that always fails
        attempt_count = 0
        async def persistent_failure_check():
            nonlocal attempt_count
            attempt_count += 1
            raise HealthCheckError(f"Persistent failure attempt {attempt_count}")

        health_checker_with_custom_timeouts.register_check("persistent", persistent_failure_check)

        result = await health_checker_with_custom_timeouts.check_component("persistent")

        # Verify retry logic with persistent failures
        assert result.name == "persistent"
        assert result.status == HealthStatus.UNHEALTHY  # Should fail after retries
        assert "Persistent failure attempt" in result.message
        assert attempt_count == 3  # Should have attempted 3 times (initial + 2 retries)

    def test_health_check_backoff_strategy_integration(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test health check backoff strategy integration with retry logic.

        Integration Scope:
            HealthChecker → Backoff strategy → Retry timing → Performance characteristics

        Business Impact:
            Ensures health check retry backoff strategy works correctly
            to prevent overwhelming failing services while still
            providing timely failure detection.

        Test Strategy:
            - Create health check that fails multiple times
            - Measure timing between retry attempts
            - Verify backoff strategy is applied correctly
            - Confirm backoff doesn't cause excessive delays

        Success Criteria:
            - Backoff strategy is applied between retry attempts
            - Retry delays increase appropriately
            - Backoff doesn't cause excessive total response time
            - Performance impact of backoff is reasonable
        """
        # Track timing of retry attempts
        attempt_timings = []
        async def timing_failure_check():
            attempt_timings.append(time.time())
            raise HealthCheckError("Timing failure for backoff testing")

        health_checker_with_custom_timeouts.register_check("timing", timing_failure_check)

        start_time = time.time()
        result = await health_checker_with_custom_timeouts.check_component("timing")
        end_time = time.time()

        # Verify backoff strategy integration
        assert result.name == "timing"
        assert result.status == HealthStatus.UNHEALTHY
        assert len(attempt_timings) == 3  # Initial + 2 retries

        # Verify backoff timing (should be approximately 0.5s, 1.0s delays)
        total_time = end_time - start_time
        assert 1.0 < total_time < 3.0  # Should complete within reasonable time

        # Verify delays between attempts follow backoff pattern
        for i in range(1, len(attempt_timings)):
            delay = attempt_timings[i] - attempt_timings[i-1]
            expected_min_delay = 0.5 * (2 ** (i-1))  # Backoff: 0.5s, 1.0s
            assert delay >= expected_min_delay * 0.8  # Allow some timing variance

    def test_health_check_timeout_and_retry_integration_scenarios(
        self, health_checker
    ):
        """
        Test integration scenarios combining timeout and retry logic.

        Integration Scope:
            HealthChecker → Timeout + Retry integration → Complex failure scenarios

        Business Impact:
            Ensures health monitoring handles complex failure scenarios
            where timeouts and retries interact, providing robust
            monitoring under adverse conditions.

        Test Strategy:
            - Create health check with timeout and retry interaction
            - Test various combinations of timeout and retry behavior
            - Verify proper handling of timeout during retry attempts
            - Confirm correct status determination for complex scenarios

        Success Criteria:
            - Timeout and retry mechanisms work together correctly
            - Complex failure scenarios are handled appropriately
            - Status determination accounts for both timeout and retry outcomes
            - System remains stable under complex failure conditions
        """
        # Create health check that times out on first attempt but succeeds on second
        attempt_count = 0
        async def timeout_then_success():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                await asyncio.sleep(0.5)  # Timeout on first attempt
                return ComponentStatus("timeout_test", HealthStatus.HEALTHY, "Should not reach here")
            return ComponentStatus("timeout_test", HealthStatus.HEALTHY, "Succeeded on retry")

        health_checker.register_check("timeout_test", timeout_then_success)

        result = await health_checker.check_component("timeout_test")

        # Verify timeout and retry integration
        assert result.name == "timeout_test"
        assert result.status == HealthStatus.HEALTHY  # Should succeed on retry
        assert "Succeeded on retry" in result.message
        assert attempt_count == 2  # Should have attempted twice

    def test_health_check_performance_under_timeout_and_retry_conditions(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test health check performance under timeout and retry conditions.

        Integration Scope:
            HealthChecker → Timeout + Retry → Performance characteristics → Monitoring

        Business Impact:
            Ensures health check performance remains acceptable even under
            timeout and retry conditions, maintaining monitoring system
            responsiveness during failure scenarios.

        Test Strategy:
            - Execute health checks with timeout and retry conditions
            - Measure performance impact of timeout/retry logic
            - Verify response times remain reasonable
            - Confirm performance degradation is acceptable

        Success Criteria:
            - Response times remain acceptable with timeout/retry
            - Performance impact of retry logic is reasonable
            - Timeout handling doesn't cause excessive delays
            - System performance is maintained under failure conditions
        """
        # Create health check that fails quickly (no timeout/retry delays)
        async def fast_failure():
            raise HealthCheckError("Fast failure for performance testing")

        health_checker_with_custom_timeouts.register_check("fast_failure", fast_failure)

        # Test performance with multiple rapid failures
        start_time = time.time()
        results = []
        for i in range(5):
            result = await health_checker_with_custom_timeouts.check_component("fast_failure")
            results.append(result)
        end_time = time.time()

        total_time = end_time - start_time
        avg_time_per_check = total_time / len(results)

        # Verify performance characteristics under failure conditions
        assert total_time < 2.0  # Total time under 2 seconds for 5 checks
        assert avg_time_per_check < 0.4  # Average under 400ms per check

        # Verify all results are consistent
        for result in results:
            assert result.name == "fast_failure"
            assert result.status == HealthStatus.UNHEALTHY
            assert "Fast failure" in result.message

    def test_health_check_timeout_configuration_flexibility(
        self
    ):
        """
        Test health check timeout configuration flexibility and validation.

        Integration Scope:
            HealthChecker → Timeout configuration → Configuration validation

        Business Impact:
            Ensures health check timeout configuration is flexible and
            properly validated, allowing operators to tune monitoring
            behavior for different deployment scenarios.

        Test Strategy:
            - Create health checkers with different timeout configurations
            - Test timeout configuration validation
            - Verify timeout settings are properly applied
            - Confirm configuration flexibility works as expected

        Success Criteria:
            - Timeout configurations are properly validated
            - Different timeout values are correctly applied
            - Configuration flexibility allows for different scenarios
            - Invalid configurations are handled appropriately
        """
        # Test various timeout configurations
        test_configs = [
            {"default_timeout_ms": 1000, "per_component_timeouts_ms": {}},
            {"default_timeout_ms": 5000, "per_component_timeouts_ms": {"slow": 10000}},
            {"default_timeout_ms": 100, "per_component_timeouts_ms": {"fast": 50}},
        ]

        for config in test_configs:
            checker = HealthChecker(**config)

            # Verify configuration is applied correctly
            assert checker._default_timeout_ms == config["default_timeout_ms"]
            assert checker._per_component_timeouts_ms == config["per_component_timeouts_ms"]

            # Test with a simple health check
            async def simple_check():
                return ComponentStatus("test", HealthStatus.HEALTHY, "Test")

            checker.register_check("test", simple_check)
            result = await checker.check_component("test")

            assert result.name == "test"
            assert result.status == HealthStatus.HEALTHY

    def test_health_check_retry_configuration_flexibility(
        self
    ):
        """
        Test health check retry configuration flexibility and validation.

        Integration Scope:
            HealthChecker → Retry configuration → Configuration validation

        Business Impact:
            Ensures health check retry configuration is flexible and
            properly validated, allowing operators to tune retry
            behavior for different reliability requirements.

        Test Strategy:
            - Create health checkers with different retry configurations
            - Test retry configuration validation
            - Verify retry settings are properly applied
            - Confirm configuration flexibility works as expected

        Success Criteria:
            - Retry configurations are properly validated
            - Different retry counts and backoff values are applied
            - Configuration flexibility allows for different scenarios
            - Invalid configurations are handled appropriately
        """
        # Test various retry configurations
        test_configs = [
            {"retry_count": 0, "backoff_base_seconds": 0.1},  # No retries
            {"retry_count": 3, "backoff_base_seconds": 0.5},  # Standard retries
            {"retry_count": 5, "backoff_base_seconds": 1.0},  # Many retries
        ]

        for config in test_configs:
            checker = HealthChecker(
                default_timeout_ms=2000,
                per_component_timeouts_ms={},
                **config
            )

            # Verify configuration is applied correctly
            assert checker._retry_count == config["retry_count"]
            assert checker._backoff_base_seconds == config["backoff_base_seconds"]

            # Test retry behavior with a failing health check
            attempt_count = 0
            async def failing_check():
                nonlocal attempt_count
                attempt_count += 1
                raise HealthCheckError("Test failure")

            checker.register_check("failing", failing_check)
            result = await checker.check_component("failing")

            # Verify retry count is respected
            expected_attempts = config["retry_count"] + 1  # Initial attempt + retries
            assert attempt_count == expected_attempts

    def test_health_check_graceful_degradation_under_timeout_pressure(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test graceful degradation under timeout pressure scenarios.

        Integration Scope:
            HealthChecker → Timeout pressure → Graceful degradation → System resilience

        Business Impact:
            Ensures health monitoring system degrades gracefully under
            timeout pressure, maintaining monitoring capabilities even
            when individual components experience timeout issues.

        Test Strategy:
            - Create scenario with multiple timeout failures
            - Test system behavior under timeout pressure
            - Verify graceful degradation mechanisms
            - Confirm system remains operational despite timeouts

        Success Criteria:
            - System handles multiple timeout failures gracefully
            - Response times don't become excessive under pressure
            - Error reporting remains accurate despite timeouts
            - Monitoring system continues operating under stress
        """
        # Create multiple components that timeout
        async def timeout_component_1():
            await asyncio.sleep(2)  # Exceed timeout
            return ComponentStatus("timeout1", HealthStatus.HEALTHY, "Should timeout")

        async def timeout_component_2():
            await asyncio.sleep(2)  # Exceed timeout
            return ComponentStatus("timeout2", HealthStatus.HEALTHY, "Should timeout")

        health_checker_with_custom_timeouts.register_check("timeout1", timeout_component_1)
        health_checker_with_custom_timeouts.register_check("timeout2", timeout_component_2)

        # Test system under timeout pressure
        start_time = time.time()
        system_health = await health_checker_with_custom_timeouts.check_all_components()
        end_time = time.time()

        total_time = end_time - start_time

        # Verify graceful degradation under pressure
        assert isinstance(system_health.overall_status, HealthStatus)
        assert system_health.overall_status == HealthStatus.DEGRADED
        assert len(system_health.components) == 2
        assert total_time < 5.0  # Should not be excessively long

        # Verify both components show timeout degradation
        for component in system_health.components:
            assert component.status == HealthStatus.DEGRADED
            assert "timed out" in component.message.lower()

    def test_health_check_exception_handling_during_timeout_scenarios(
        self, health_checker
    ):
        """
        Test exception handling during timeout scenarios.

        Integration Scope:
            HealthChecker → Timeout scenarios → Exception handling → Error recovery

        Business Impact:
            Ensures proper exception handling during timeout scenarios,
            preventing timeout issues from causing unhandled exceptions
            or monitoring system instability.

        Test Strategy:
            - Create health check that raises exception during timeout
            - Test exception handling integration with timeout logic
            - Verify proper error classification and reporting
            - Confirm system handles timeout-related exceptions correctly

        Success Criteria:
            - Exceptions during timeout are handled appropriately
            - Timeout and exception scenarios are properly distinguished
            - Error reporting includes relevant context
            - System remains stable despite timeout-related exceptions
        """
        # Create health check that raises exception and would timeout
        async def exception_during_timeout():
            await asyncio.sleep(1)  # Partial delay
            raise HealthCheckError("Exception during health check execution")

        health_checker.register_check("exception_timeout", exception_during_timeout)

        result = await health_checker.check_component("exception_timeout")

        # Verify exception handling during timeout scenario
        assert result.name == "exception_timeout"
        assert result.status == HealthStatus.UNHEALTHY  # Exception, not timeout
        assert "Exception during health check" in result.message
        assert "HealthCheckError" in result.message
        assert result.response_time_ms > 0
        assert result.response_time_ms < 1500  # Should not timeout completely

    def test_health_check_timeout_retry_error_context_preservation(
        self, health_checker_with_custom_timeouts
    ):
        """
        Test error context preservation during timeout and retry scenarios.

        Integration Scope:
            HealthChecker → Timeout/retry → Error context → Context preservation

        Business Impact:
            Ensures error context is preserved during timeout and retry
            scenarios, providing operators with detailed information
            for troubleshooting monitoring issues.

        Test Strategy:
            - Create health check with timeout and retry failure scenarios
            - Execute health check and capture error context
            - Verify error context is preserved and useful
            - Confirm context includes timing and retry information

        Success Criteria:
            - Error context includes timing information
            - Retry attempt information is preserved
            - Component identification is maintained
            - Context provides actionable debugging information
        """
        # Create health check that fails with detailed context
        async def context_failure():
            raise HealthCheckError(
                "Database connection failed during health check. "
                "Connection timeout after 2 seconds. "
                "Retry attempts: 2. "
                "Last successful connection: 10 minutes ago."
            )

        health_checker_with_custom_timeouts.register_check("context_test", context_failure)

        result = await health_checker_with_custom_timeouts.check_component("context_test")

        # Verify error context preservation
        assert result.name == "context_test"
        assert result.status == HealthStatus.UNHEALTHY
        assert "Database connection failed" in result.message
        assert "Connection timeout" in result.message
        assert "2 seconds" in result.message
        assert "Retry attempts: 2" in result.message
        assert "10 minutes ago" in result.message

        # Verify response time reflects the failure scenario
        assert result.response_time_ms > 0
        assert result.response_time_ms < 5000  # Should be bounded
