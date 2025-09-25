"""
Integration Tests: Circuit Breaker State Management → Health Checks → Recovery

This module tests the integration between circuit breaker state management, health check
reporting, and automatic recovery mechanisms. It validates that circuit breakers properly
transition between states, report accurate health status, and recover from failures.

Integration Scope:
    - EnhancedCircuitBreaker → State management → Health reporting
    - Failure detection → State transitions → Recovery orchestration
    - Health checks → Monitoring integration → Operational visibility

Business Impact:
    Critical for system availability and automatic recovery during failures,
    ensuring operational visibility and preventing cascade failures

Test Strategy:
    - Test complete state transition cycles (closed → open → half-open → closed)
    - Validate health check reporting accuracy for different states
    - Test automatic recovery mechanisms and timing
    - Verify state persistence and monitoring integration
    - Test concurrent access to circuit breaker state

Critical Paths:
    - Failure detection → State management → Health reporting
    - Recovery orchestration → State transitions → System restoration
    - Health monitoring → Alert generation → Operational response
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from app.infrastructure.resilience.circuit_breaker import (
    EnhancedCircuitBreaker,
    CircuitBreakerConfig,
    ResilienceMetrics
)
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.core.config import Settings
from app.core.exceptions import ServiceUnavailableError


class TestCircuitBreakerRecovery:
    """
    Integration tests for Circuit Breaker State Management → Health Checks → Recovery.

    Seam Under Test:
        EnhancedCircuitBreaker → Health status → Recovery mechanisms → Monitoring integration

    Critical Paths:
        - Failure detection → State management → Health reporting
        - Recovery orchestration → State transitions → System restoration
        - Health monitoring → Alert generation → Operational response

    Business Impact:
        Ensures automatic service recovery and maintains system availability
        during infrastructure failures while providing operational visibility
    """

    @pytest.fixture
    def test_circuit_breaker(self):
        """Create a test circuit breaker with known configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,  # Short timeout for testing
            half_open_max_calls=1
        )

        return EnhancedCircuitBreaker(
            failure_threshold=config.failure_threshold,
            recovery_timeout=config.recovery_timeout,
            name="test_circuit_breaker"
        )

    @pytest.fixture
    def resilience_orchestrator(self):
        """Create a resilience orchestrator for health check testing."""
        settings = Settings(
            environment="testing",
            enable_circuit_breaker=True,
            enable_retry=True
        )

        return AIServiceResilience(settings)

    def test_circuit_breaker_state_transitions_complete_cycle(self, test_circuit_breaker):
        """
        Test complete circuit breaker state transition cycle.

        Integration Scope:
            Circuit breaker → State management → Recovery → State transition

        Business Impact:
            Validates automatic failure detection and recovery mechanisms

        Test Strategy:
            - Start with closed state (normal operation)
            - Trigger failures to open circuit breaker
            - Verify open state behavior (fail-fast)
            - Wait for recovery timeout
            - Test half-open state with limited calls
            - Verify closed state after successful recovery

        Success Criteria:
            - Circuit breaker transitions: closed → open → half-open → closed
            - Each state behaves according to specification
            - State transitions happen automatically
            - Health status reflects current state accurately
        """
        # Verify initial state is closed
        assert test_circuit_breaker.state == "closed"
        health_status = test_circuit_breaker.get_health_status()
        assert health_status["healthy"] is True

        # Record failures to open circuit breaker
        for i in range(3):
            try:
                # Simulate service call that fails
                raise ServiceUnavailableError(f"Service failure {i}")
            except ServiceUnavailableError:
                test_circuit_breaker.record_failure()

        # Verify circuit breaker opened
        assert test_circuit_breaker.state == "open"
        health_status = test_circuit_breaker.get_health_status()
        assert health_status["healthy"] is False
        assert "open" in health_status["state"]

        # Verify fail-fast behavior when open
        start_time = time.time()
        try:
            # This should fail immediately without calling the service
            test_circuit_breaker.call(lambda: "should_not_be_called")
        except Exception:
            pass  # Expected to fail
        end_time = time.time()

        # Should fail very quickly (fail-fast behavior)
        assert (end_time - start_time) < 0.1

        # Wait for recovery timeout (slightly longer than 30 seconds)
        time.sleep(31)

        # Verify circuit breaker transitions to half-open
        assert test_circuit_breaker.state == "half-open"

        # Test successful call in half-open state
        result = test_circuit_breaker.call(lambda: "recovery_successful")
        assert result == "recovery_successful"

        # Verify circuit breaker transitions back to closed
        assert test_circuit_breaker.state == "closed"
        health_status = test_circuit_breaker.get_health_status()
        assert health_status["healthy"] is True

    def test_health_check_reporting_accuracy(self, test_circuit_breaker):
        """
        Test that health check reporting accurately reflects circuit breaker state.

        Integration Scope:
            Circuit breaker → Health status → Monitoring integration

        Business Impact:
            Provides accurate operational visibility for monitoring systems

        Test Strategy:
            - Test health reporting in closed state
            - Open circuit breaker and verify health reporting
            - Test half-open state reporting
            - Verify state transitions are reflected in health checks

        Success Criteria:
            - Health status accurately reflects current circuit breaker state
            - Health check provides detailed state information
            - State transitions trigger appropriate health status changes
            - Health reporting includes relevant metrics and metadata
        """
        # Test closed state reporting
        closed_health = test_circuit_breaker.get_health_status()
        assert closed_health["healthy"] is True
        assert closed_health["state"] == "closed"
        assert "metrics" in closed_health
        assert "failure_threshold" in closed_health
        assert "recovery_timeout" in closed_health

        # Record failures to open circuit breaker
        for _ in range(3):
            test_circuit_breaker.record_failure()

        # Test open state reporting
        open_health = test_circuit_breaker.get_health_status()
        assert open_health["healthy"] is False
        assert open_health["state"] == "open"
        assert "last_failure_time" in open_health
        assert "failure_count" in open_health

        # Wait for recovery timeout
        time.sleep(31)

        # Test half-open state reporting
        half_open_health = test_circuit_breaker.get_health_status()
        assert half_open_health["state"] == "half-open"
        assert "recovery_timeout" in half_open_health
        assert "half_open_max_calls" in half_open_health

        # Successful call should close circuit breaker
        test_circuit_breaker.call(lambda: "success")

        # Test closed state after recovery
        recovered_health = test_circuit_breaker.get_health_status()
        assert recovered_health["healthy"] is True
        assert recovered_health["state"] == "closed"

    def test_automatic_recovery_timeout_mechanism(self, test_circuit_breaker):
        """
        Test automatic recovery timeout mechanism.

        Integration Scope:
            Circuit breaker → Recovery timeout → Half-open testing → State transition

        Business Impact:
            Ensures automatic service recovery without manual intervention

        Test Strategy:
            - Open circuit breaker with failures
            - Verify recovery timeout is properly configured
            - Test that timeout triggers half-open state transition
            - Validate half-open state allows limited testing calls

        Success Criteria:
            - Recovery timeout is correctly configured and applied
            - Circuit breaker transitions to half-open after timeout
            - Half-open state allows limited calls for testing
            - State transition timing matches configuration
        """
        # Open circuit breaker
        for _ in range(3):
            test_circuit_breaker.record_failure()

        assert test_circuit_breaker.state == "open"

        # Verify recovery timeout is configured
        health_status = test_circuit_breaker.get_health_status()
        assert "recovery_timeout" in health_status
        assert health_status["recovery_timeout"] == 30

        # Wait for recovery timeout
        time.sleep(31)

        # Verify transition to half-open
        assert test_circuit_breaker.state == "half-open"

        # Test half-open call allowance
        result = test_circuit_breaker.call(lambda: "half_open_test")
        assert result == "half_open_test"

        # Verify transition to closed after success
        assert test_circuit_breaker.state == "closed"

    def test_circuit_breaker_state_persistence(self, test_circuit_breaker):
        """
        Test circuit breaker state persistence across operations.

        Integration Scope:
            Circuit breaker → State persistence → Recovery mechanisms

        Business Impact:
            Prevents service flooding after restarts and maintains failure state

        Test Strategy:
            - Open circuit breaker and verify state persistence
            - Test that state survives multiple operations
            - Verify recovery mechanisms still work with persisted state
            - Test state transitions maintain persistence

        Success Criteria:
            - Circuit breaker state persists across multiple operations
            - State transitions maintain consistency
            - Recovery mechanisms work with persisted state
            - Health reporting reflects persistent state
        """
        # Open circuit breaker
        for _ in range(3):
            test_circuit_breaker.record_failure()

        # Verify state is persistently open
        assert test_circuit_breaker.state == "open"

        # Test multiple operations with open state
        for _ in range(3):
            try:
                test_circuit_breaker.call(lambda: "should_not_call")
                assert False, "Should have failed fast"
            except Exception:
                pass  # Expected to fail

            # State should remain open
            assert test_circuit_breaker.state == "open"

        # Verify health status reflects persistent state
        health_status = test_circuit_breaker.get_health_status()
        assert health_status["healthy"] is False
        assert health_status["state"] == "open"

        # Test recovery after timeout
        time.sleep(31)

        # Should transition to half-open
        assert test_circuit_breaker.state == "half-open"

        # Successful call should close circuit breaker
        result = test_circuit_breaker.call(lambda: "recovery_call")
        assert result == "recovery_call"
        assert test_circuit_breaker.state == "closed"

    def test_multiple_operations_isolated_circuit_breakers(self, resilience_orchestrator):
        """
        Test that multiple operations maintain separate circuit breakers.

        Integration Scope:
            Multiple operations → Separate circuit breakers → Independent state management

        Business Impact:
            Ensures failure isolation between different operations

        Test Strategy:
            - Create circuit breakers for multiple operations
            - Fail one operation and verify others remain healthy
            - Test recovery of failed operation without affecting others
            - Verify health reporting for multiple circuit breakers

        Success Criteria:
            - Each operation has independent circuit breaker
            - Failure in one operation doesn't affect others
            - Recovery of one operation doesn't impact others
            - Health reporting shows accurate status for each operation
        """
        # Register multiple operations
        resilience_orchestrator.register_operation("operation_a", resilience_orchestrator.get_operation_config("operation_a").strategy)
        resilience_orchestrator.register_operation("operation_b", resilience_orchestrator.get_operation_config("operation_b").strategy)
        resilience_orchestrator.register_operation("operation_c", resilience_orchestrator.get_operation_config("operation_c").strategy)

        # Get circuit breakers for each operation
        cb_a = resilience_orchestrator.get_or_create_circuit_breaker("operation_a", CircuitBreakerConfig())
        cb_b = resilience_orchestrator.get_or_create_circuit_breaker("operation_b", CircuitBreakerConfig())
        cb_c = resilience_orchestrator.get_or_create_circuit_breaker("operation_c", CircuitBreakerConfig())

        # Verify initial states
        assert cb_a.state == "closed"
        assert cb_b.state == "closed"
        assert cb_c.state == "closed"

        # Fail operation A
        for _ in range(3):
            try:
                cb_a.call(lambda: exec('raise ServiceUnavailableError("operation_a failed")'))
            except ServiceUnavailableError:
                cb_a.record_failure()

        # Verify operation A circuit breaker is open
        assert cb_a.state == "open"

        # Verify other operations remain closed
        assert cb_b.state == "closed"
        assert cb_c.state == "closed"

        # Test that operations B and C still work
        result_b = cb_b.call(lambda: "operation_b_success")
        result_c = cb_c.call(lambda: "operation_c_success")

        assert result_b == "operation_b_success"
        assert result_c == "operation_c_success"

        # Verify health status shows mixed state
        health_status = resilience_orchestrator.get_health_status()
        assert health_status["total_circuit_breakers"] == 3

        # Should have one open circuit breaker
        open_circuit_breakers = health_status["open_circuit_breakers"]
        assert len(open_circuit_breakers) == 1
        assert "operation_a" in open_circuit_breakers

        # Test recovery of operation A
        time.sleep(31)  # Wait for recovery timeout

        # Operation A should transition to half-open
        assert cb_a.state == "half-open"

        # Successful call should close operation A
        result_a = cb_a.call(lambda: "operation_a_recovered")
        assert result_a == "operation_a_recovered"
        assert cb_a.state == "closed"

        # Other operations should remain unaffected
        assert cb_b.state == "closed"
        assert cb_c.state == "closed"

    def test_health_endpoint_integration(self, resilience_orchestrator):
        """
        Test health endpoint integration with circuit breaker states.

        Integration Scope:
            Circuit breaker → Health monitoring → Internal API → External monitoring

        Business Impact:
            Provides operational visibility for monitoring and alerting systems

        Test Strategy:
            - Test health reporting with mixed circuit breaker states
            - Verify health endpoint accuracy during state transitions
            - Test health status with multiple operations
            - Validate health information format and completeness

        Success Criteria:
            - Health endpoint accurately reflects circuit breaker states
            - Health information includes all relevant metrics
            - State transitions are reflected in health status
            - Health endpoint provides comprehensive operational visibility
        """
        # Register test operations
        resilience_orchestrator.register_operation("healthy_operation", resilience_orchestrator.get_operation_config("healthy_operation").strategy)
        resilience_orchestrator.register_operation("failing_operation", resilience_orchestrator.get_operation_config("failing_operation").strategy)

        # Get circuit breakers
        healthy_cb = resilience_orchestrator.get_or_create_circuit_breaker("healthy_operation", CircuitBreakerConfig())
        failing_cb = resilience_orchestrator.get_or_create_circuit_breaker("failing_operation", CircuitBreakerConfig())

        # Test initial healthy state
        health_status = resilience_orchestrator.get_health_status()
        assert health_status["healthy"] is True
        assert health_status["total_operations"] == 2
        assert len(health_status["open_circuit_breakers"]) == 0

        # Fail one operation
        for _ in range(3):
            try:
                failing_cb.call(lambda: exec('raise ServiceUnavailableError("failing_operation failed")'))
            except ServiceUnavailableError:
                failing_cb.record_failure()

        # Verify health status reflects partial failure
        health_status = resilience_orchestrator.get_health_status()
        assert health_status["healthy"] is False  # One operation failed
        assert health_status["total_operations"] == 2
        assert len(health_status["open_circuit_breakers"]) == 1
        assert "failing_operation" in health_status["open_circuit_breakers"]

        # Test recovery
        time.sleep(31)
        result = failing_cb.call(lambda: "recovered")
        assert result == "recovered"

        # Verify health status after recovery
        health_status = resilience_orchestrator.get_health_status()
        assert health_status["healthy"] is True
        assert len(health_status["open_circuit_breakers"]) == 0
        assert len(health_status["half_open_circuit_breakers"]) == 0

    def test_circuit_breaker_metrics_tracking(self, test_circuit_breaker):
        """
        Test comprehensive metrics tracking for circuit breaker operations.

        Integration Scope:
            Circuit breaker → Metrics collection → Performance monitoring → Health reporting

        Business Impact:
            Provides detailed operational metrics for monitoring and alerting

        Test Strategy:
            - Test metrics tracking during normal operation
            - Verify metrics during failure scenarios
            - Test metrics during recovery and state transitions
            - Validate metrics accuracy and completeness

        Success Criteria:
            - Metrics accurately track all circuit breaker operations
            - State transitions are recorded in metrics
            - Success/failure counts are accurate
            - Metrics provide sufficient detail for operational monitoring
        """
        # Test initial metrics
        initial_metrics = test_circuit_breaker.metrics
        assert initial_metrics.total_calls == 0
        assert initial_metrics.successful_calls == 0
        assert initial_metrics.failed_calls == 0
        assert initial_metrics.circuit_breaker_opens == 0

        # Successful call
        result = test_circuit_breaker.call(lambda: "success")
        assert result == "success"

        # Verify metrics after success
        metrics = test_circuit_breaker.metrics
        assert metrics.total_calls == 1
        assert metrics.successful_calls == 1
        assert metrics.failed_calls == 0
        assert metrics.circuit_breaker_opens == 0

        # Failed calls to open circuit breaker
        for i in range(3):
            try:
                test_circuit_breaker.call(lambda: exec(f'raise ServiceUnavailableError("failure_{i}")'))
            except ServiceUnavailableError:
                test_circuit_breaker.record_failure()

        # Verify metrics after failures
        metrics = test_circuit_breaker.metrics
        assert metrics.total_calls == 4  # 1 success + 3 failures
        assert metrics.successful_calls == 1
        assert metrics.failed_calls == 3
        assert metrics.circuit_breaker_opens == 1

        # Test half-open call
        time.sleep(31)  # Wait for recovery

        result = test_circuit_breaker.call(lambda: "half_open_success")
        assert result == "half_open_success"

        # Verify final metrics
        metrics = test_circuit_breaker.metrics
        assert metrics.total_calls == 5  # Previous + half-open call
        assert metrics.successful_calls == 2
        assert metrics.failed_calls == 3
        assert metrics.circuit_breaker_opens == 1
        assert metrics.circuit_breaker_closes == 1

    def test_concurrent_circuit_breaker_access(self, test_circuit_breaker):
        """
        Test circuit breaker thread safety under concurrent access.

        Integration Scope:
            Concurrent operations → Circuit breaker → State management → Consistency

        Business Impact:
            Ensures system stability during high concurrent load

        Test Strategy:
            - Start multiple concurrent operations during state transitions
            - Verify circuit breaker state remains consistent
            - Test concurrent failure recording and state transitions
            - Validate health reporting under concurrent access

        Success Criteria:
            - Circuit breaker state remains consistent during concurrent access
            - No race conditions or state corruption
            - All concurrent operations complete successfully
            - Health reporting reflects accurate state
        """
        async def concurrent_operation(operation_id: int):
            """Simulate concurrent circuit breaker operations."""
            try:
                # All operations should fail and contribute to failure count
                test_circuit_breaker.call(lambda: exec(f'raise ServiceUnavailableError("concurrent_failure_{operation_id}")'))
                return False, "unexpected_success"
            except ServiceUnavailableError:
                test_circuit_breaker.record_failure()
                return True, f"failure_recorded_{operation_id}"

        # Run concurrent operations
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(5)]
        results = []

        async def run_concurrent():
            return await asyncio.gather(*[concurrent_operation(i) for i in range(5)])

        results = asyncio.run(run_concurrent())
        end_time = time.time()

        # Verify all operations completed
        assert len(results) == 5
        assert all(result[0] for result in results)  # All should record failures

        # Verify circuit breaker opened due to concurrent failures
        assert test_circuit_breaker.state == "open"

        # Verify response time was reasonable (no hung operations)
        assert (end_time - start_time) < 5  # Should complete within 5 seconds

        # Verify health status reflects concurrent failures
        health_status = test_circuit_breaker.get_health_status()
        assert health_status["healthy"] is False
        assert health_status["state"] == "open"

        # Verify metrics reflect concurrent operations
        metrics = test_circuit_breaker.metrics
        assert metrics.total_calls >= 5
        assert metrics.failed_calls >= 5
        assert metrics.circuit_breaker_opens == 1
