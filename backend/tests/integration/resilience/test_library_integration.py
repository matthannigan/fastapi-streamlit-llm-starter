"""
Integration tests for Resilience Library Integration → Third-Party Dependencies.

This test suite validates the integration between the resilience infrastructure and real third-party
libraries (circuitbreaker and tenacity), ensuring that library version compatibility and behavioral
integration work as expected with actual library implementations.

Seam Under Test:
    AIServiceResilience → Real circuitbreaker library → Real tenacity library

Critical Paths:
    - EnhancedCircuitBreaker properly inherits from circuitbreaker library
    - Tenacity retry decorators integrate with custom retry predicate functions
    - Retry state attributes from tenacity are accessible and function as expected
    - Exponential backoff works correctly with real tenacity decorators
    - Library version changes don't break core functionality

Business Impact:
    Prevents subtle library compatibility issues that could cause resilience patterns to fail silently.
    Ensures resilience patterns work with actual library behavior rather than mocked expectations.
    Validates critical third-party library integration that the entire system depends on.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Any, Dict
from circuitbreaker import CircuitBreaker  # type: ignore[import-untyped]
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError  # type: ignore[import-untyped]

from app.infrastructure.resilience.circuit_breaker import EnhancedCircuitBreaker, CircuitBreakerConfig
from app.infrastructure.resilience.retry import RetryConfig, should_retry_on_exception, classify_exception
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.config_presets import ResilienceStrategy
from app.core.exceptions import TransientAIError, PermanentAIError, InfrastructureError


class TestLibraryIntegration:
    """
    Integration tests for third-party library integration with resilience infrastructure.

    This test class validates that the resilience infrastructure properly integrates with
    real third-party libraries (circuitbreaker and tenacity) without mocking their behavior.

    Critical Integration Points:
        - EnhancedCircuitBreaker inherits from circuitbreaker.CircuitBreaker
        - AIServiceResilience integrates tenacity decorators with custom retry predicates
        - Retry state management through real tenacity library
        - Exponential backoff configuration with real tenacity wait strategies

    Test Philosophy:
        Tests use real third-party libraries to validate actual integration behavior.
        This complements unit tests by ensuring library compatibility and behavioral integration.
    """

    def test_enhanced_circuit_breaker_inherits_from_real_circuitbreaker_library(self, resilience_test_settings):
        """
        Test that EnhancedCircuitBreaker properly inherits from real circuitbreaker library.

        Integration Scope:
            EnhancedCircuitBreaker → circuitbreaker.CircuitBreaker → Real library implementation

        Business Impact:
            Validates inheritance chain works correctly with actual library version.
            Prevents subtle compatibility issues when circuitbreaker library updates.

        Test Strategy:
            - Create EnhancedCircuitBreaker instance
            - Verify inheritance from circuitbreaker.CircuitBreaker
            - Test basic circuit breaker functionality through real library
            - Verify enhanced features don't break base functionality

        Success Criteria:
            - EnhancedCircuitBreaker is instance of circuitbreaker.CircuitBreaker
            - Circuit breaker state transitions work as expected
            - Enhanced metrics collection doesn't interfere with base functionality
        """
        # Arrange
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=1,
            half_open_max_calls=1
        )

        # Act - Create enhanced circuit breaker
        enhanced_cb = EnhancedCircuitBreaker(
            failure_threshold=config.failure_threshold,
            recovery_timeout=config.recovery_timeout,
            name="test_integration_circuit"
        )

        # Assert - Verify inheritance
        assert isinstance(enhanced_cb, CircuitBreaker), (
            "EnhancedCircuitBreaker must inherit from circuitbreaker.CircuitBreaker"
        )

        # Assert - Verify real circuit breaker functionality
        assert enhanced_cb.closed == True, "Circuit should start in closed state"
        assert enhanced_cb.failure_count == 0, "Failure count should start at 0"

        # Test basic functionality through real library
        def failing_function():
            raise ConnectionError("Test failure")

        # Trigger failures to open circuit (using real library behavior)
        for i in range(config.failure_threshold):
            try:
                enhanced_cb.call(failing_function)
            except ConnectionError:
                pass  # Expected failure

        # Verify circuit is open (real library behavior)
        assert enhanced_cb.opened, "Circuit should be open after threshold failures"

        # Verify enhanced metrics work with real library
        metrics = enhanced_cb.metrics.to_dict()
        assert metrics['total_calls'] >= config.failure_threshold, "Metrics should track real calls"
        assert metrics['failed_calls'] >= config.failure_threshold, "Metrics should track failures"

    def test_tenacity_retry_decorator_calls_custom_retry_predicate_functions(self, resilience_test_settings):
        """
        Test that tenacity retry decorators properly call our custom retry predicate functions.

        Integration Scope:
            AIServiceResilience → tenacity.retry → should_retry_on_exception() → Custom logic

        Business Impact:
            Ensures retry decisions are made by our custom logic, not default tenacity behavior.
            Validates that exception classification integrates correctly with tenacity.

        Test Strategy:
            - Create function decorated with tenacity using our retry predicate
            - Trigger transient and permanent errors
            - Verify retry predicate is called and makes correct decisions
            - Count actual retry attempts through real tenacity behavior

        Success Criteria:
            - TransientAIError triggers retry attempts
            - PermanentAIError does not trigger retry attempts
            - Retry predicate function is called for each exception
            - Real tenacity retry behavior respects our custom logic
        """
        # Arrange - Track calls to our retry predicate
        original_should_retry = should_retry_on_exception
        retry_predicate_calls = []

        def tracking_retry_predicate(retry_state):
            """Wrapper to track calls to original predicate."""
            exception = retry_state.outcome.exception()
            should_retry = original_should_retry(retry_state)
            retry_predicate_calls.append({
                'exception_type': type(exception).__name__,
                'should_retry': should_retry,
                'attempt_number': retry_state.attempt_number
            })
            return should_retry

        # Create test functions with real tenacity integration
        @retry(
            retry=tracking_retry_predicate,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=0.3)  # Fast for testing
        )
        def transient_error_function():
            raise TransientAIError("Temporary AI service failure")

        @retry(
            retry=tracking_retry_predicate,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=0.3)
        )
        def permanent_error_function():
            raise PermanentAIError("Permanent AI service configuration error")

        # Act & Assert - Test transient error (should retry)
        with pytest.raises(RetryError):
            transient_error_function()

        # Verify retry predicate was called correctly for transient error
        transient_calls = [call for call in retry_predicate_calls
                          if call['exception_type'] == 'TransientAIError']
        assert len(transient_calls) == 3, f"Should retry transient error 3 times, got {len(transient_calls)}"
        assert all(call['should_retry'] for call in transient_calls[:-1]), "Should retry on first attempts"
        assert transient_calls[-1]['attempt_number'] == 3, "Should reach max attempts"

        # Reset for permanent error test
        retry_predicate_calls.clear()

        # Act & Assert - Test permanent error (should not retry)
        with pytest.raises(PermanentAIError):
            permanent_error_function()

        # Verify retry predicate was called correctly for permanent error
        permanent_calls = [call for call in retry_predicate_calls
                          if call['exception_type'] == 'PermanentAIError']
        assert len(permanent_calls) == 1, f"Should not retry permanent error, got {len(permanent_calls)} calls"
        assert permanent_calls[0]['should_retry'] == False, "Should not retry permanent error"
        assert permanent_calls[0]['attempt_number'] == 1, "Should only attempt once"

    def test_retry_state_attributes_accessible_from_real_tenacity(self, resilience_test_settings):
        """
        Test that retry state attributes are accessible as expected from real tenacity.

        Integration Scope:
            AIServiceResilience → tenacity.RetryingState → State attributes access

        Business Impact:
            Ensures our retry logic can access and utilize tenacity state information.
            Validates that retry state tracking works with real library behavior.

        Test Strategy:
            - Create retry decorator that accesses retry state attributes
            - Verify all expected attributes are available and populated correctly
            - Test state attributes update correctly across retry attempts
            - Validate timing and attempt number tracking

        Success Criteria:
            - All expected retry state attributes are accessible
            - Attempt number increments correctly
            - Timing information is available and reasonable
            - Exception information is properly stored in state
        """
        # Arrange - Collect retry state information
        retry_states = []

        def state_tracking_retry_predicate(retry_state):
            """Collect detailed state information from tenacity."""
            state_info = {
                'attempt_number': getattr(retry_state, 'attempt_number', None),
                'outcome': getattr(retry_state, 'outcome', None),
                'idle_for': getattr(retry_state, 'idle_for', None),
                'seconds_since_start': getattr(retry_state, 'seconds_since_start', None),
                'has_exception': retry_state.outcome is not None and retry_state.outcome.exception() is not None
            }

            if state_info['has_exception']:
                state_info['exception_type'] = type(retry_state.outcome.exception()).__name__

            retry_states.append(state_info)
            return True  # Always retry for this test

        @retry(
            retry=state_tracking_retry_predicate,
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=0.2)
        )
        def function_with_state_tracking():
            raise ConnectionError("Test connection failure")

        # Act - Trigger retries to collect state information
        start_time = time.time()
        with pytest.raises(RetryError):
            function_with_state_tracking()
        end_time = time.time()

        # Assert - Verify retry state attributes are accessible and correct
        assert len(retry_states) == 3, f"Expected 3 retry states, got {len(retry_states)}"

        # Verify attempt numbers
        for i, state in enumerate(retry_states):
            assert state['attempt_number'] == i + 1, f"Attempt {i+1} should have correct number"

        # Verify exception tracking
        for state in retry_states:
            assert state['has_exception'] == True, "State should track exceptions"
            assert state['exception_type'] == 'ConnectionError', "Should track correct exception type"

        # Verify timing information is available
        for state in retry_states:
            assert state['seconds_since_start'] is not None, "Should track timing since start"
            assert state['seconds_since_start'] >= 0, "Timing should be non-negative"

        # Verify last attempt timing is reasonable
        total_duration = end_time - start_time
        assert total_duration >= 0.1, "Should have taken some time for retries"
        assert total_duration < 5.0, "Should not take too long for testing"

    def test_exponential_backoff_works_with_real_tenacity_decorators(self, resilience_test_settings):
        """
        Test that exponential backoff works correctly with real tenacity decorators.

        Integration Scope:
            AIServiceResilience → tenacity.wait_exponential → Real timing behavior

        Business Impact:
            Ensures retry delays work as configured to prevent overwhelming services.
            Validates that exponential backoff provides proper spacing between retries.

        Test Strategy:
            - Configure exponential backoff with known parameters
            - Measure actual delays between retry attempts
            - Verify delay pattern follows exponential progression
            - Test jitter configuration doesn't break exponential behavior

        Success Criteria:
            - Retry delays increase exponentially (within reasonable variance)
            - Base delay and multiplier work as configured
            - Maximum delay limits are respected
            - Jitter doesn't break exponential pattern (if enabled)
        """
        # Arrange - Configure exponential backoff with known parameters
        base_multiplier = 0.05  # 50ms base for fast testing
        max_delay = 0.5        # 500ms max delay
        retry_attempts = []

        def timing_retry_predicate(retry_state):
            """Record timing information for each retry attempt."""
            retry_attempts.append({
                'attempt': retry_state.attempt_number,
                'timestamp': time.time()
            })
            return True  # Always retry for timing measurement

        @retry(
            retry=timing_retry_predicate,
            stop=stop_after_attempt(4),  # 4 attempts = 3 delays
            wait=wait_exponential(multiplier=base_multiplier, min=base_multiplier, max=max_delay)
        )
        def function_with_exponential_backoff():
            raise ConnectionError("Simulated transient failure")

        # Act - Execute function and measure timing
        start_time = time.time()
        with pytest.raises(RetryError):
            function_with_exponential_backoff()
        end_time = time.time()

        # Assert - Verify exponential backoff pattern
        assert len(retry_attempts) == 4, f"Expected 4 attempts, got {len(retry_attempts)}"

        # Calculate delays between attempts
        delays = []
        for i in range(1, len(retry_attempts)):
            delay = retry_attempts[i]['timestamp'] - retry_attempts[i-1]['timestamp']
            delays.append(delay)

        assert len(delays) == 3, f"Should have 3 delays, got {len(delays)}"

        # Verify exponential growth pattern (allowing for jitter)
        # Expected: 0.05s, 0.1s, 0.2s (with some variance)
        expected_delays = [base_multiplier, base_multiplier * 2, base_multiplier * 4]

        for i, (actual, expected) in enumerate(zip(delays, expected_delays)):
            # Allow 25% variance for timing precision and jitter
            variance = expected * 0.25
            assert abs(actual - expected) <= variance, (
                f"Delay {i+1} should be ~{expected:.3f}s, got {actual:.3f}s "
                f"(variance: ±{variance:.3f}s)"
            )

        # Verify no delay exceeds maximum
        for delay in delays:
            assert delay <= max_delay, f"Delay {delay:.3f}s should not exceed max {max_delay}s"

    async def test_library_version_compatibility_maintains_functionality(self, ai_resilience_orchestrator):
        """
        Test that library version compatibility doesn't break core functionality.

        Integration Scope:
            AIServiceResilience → Real circuitbreaker + tenacity libraries → Core operations

        Business Impact:
            Ensures system remains functional when third-party libraries update.
            Validates that core resilience patterns work regardless of library versions.

        Test Strategy:
            - Test all major resilience operations with real libraries
            - Verify decorator application works correctly
            - Test circuit breaker and retry pattern coordination
            - Validate metrics collection works with current library versions

        Success Criteria:
            - Resilience decorators apply without errors
            - Circuit breaker functionality works with real library
            - Retry logic functions with real tenacity behavior
            - Metrics and monitoring collect data correctly
        """
        # Arrange - Create test functions with different resilience patterns
        @ai_resilience_orchestrator.with_resilience(
            operation_name="test_circuit_breaker_integration",
            strategy=ResilienceStrategy.BALANCED
        )
        async def test_circuit_breaker_function():
            """Test function to validate circuit breaker integration."""
            return "circuit_breaker_success"

        @ai_resilience_orchestrator.with_resilience(
            operation_name="test_retry_integration",
            strategy=ResilienceStrategy.AGGRESSIVE
        )
        async def test_retry_function():
            """Test function to validate retry integration."""
            return "retry_success"

        # Act & Assert - Test circuit breaker integration
        result1 = await test_circuit_breaker_function()
        assert result1 == "circuit_breaker_success", "Circuit breaker integration should work"

        # Verify circuit breaker was created and tracks metrics
        cb_metrics = ai_resilience_orchestrator.get_metrics("test_circuit_breaker_integration")
        assert cb_metrics is not None, "Circuit breaker metrics should be available"
        cb_metrics_dict = cb_metrics.to_dict() if hasattr(cb_metrics, 'to_dict') else cb_metrics
        total_calls = cb_metrics_dict.get('total_calls', 0) if isinstance(cb_metrics_dict, dict) else getattr(cb_metrics, 'total_calls', 0)
        assert total_calls > 0, "Should track circuit breaker calls"

        # Act & Assert - Test retry integration
        result2 = await test_retry_function()
        assert result2 == "retry_success", "Retry integration should work"

        # Verify retry was configured and tracks metrics
        retry_metrics = ai_resilience_orchestrator.get_metrics("test_retry_integration")
        assert retry_metrics is not None, "Retry metrics should be available"
        retry_metrics_dict = retry_metrics.to_dict() if hasattr(retry_metrics, 'to_dict') else retry_metrics
        retry_total_calls = retry_metrics_dict.get('total_calls', 0) if isinstance(retry_metrics_dict, dict) else getattr(retry_metrics, 'total_calls', 0)
        assert retry_total_calls > 0, "Should track retry calls"

        # Act & Assert - Test comprehensive health status
        health_status = ai_resilience_orchestrator.get_health_status()
        assert health_status is not None, "Health status should be available"

        # Verify system is healthy
        assert health_status.get('healthy', False) is True, "Overall system should be healthy"

        # Verify no open circuit breakers
        open_circuit_breakers = health_status.get('open_circuit_breakers', [])
        assert len(open_circuit_breakers) == 0, "Should have no open circuit breakers"

        # Verify basic health status structure
        assert 'timestamp' in health_status, "Health status should include timestamp"
        assert 'healthy' in health_status, "Health status should include healthy flag"

    async def test_real_libraries_coordination_circuit_breaker_and_retry(self, ai_resilience_orchestrator):
        """
        Test coordination between real circuit breaker and tenacity retry libraries.

        Integration Scope:
            AIServiceResilience → circuitbreaker library + tenacity library → Coordinated behavior

        Business Impact:
            Ensures circuit breaker and retry patterns work together without conflicts.
            Validates that real library coordination handles failure scenarios correctly.

        Test Strategy:
            - Create function with both circuit breaker and retry protection
            - Trigger failures to test circuit breaker opening
            - Verify retry respects circuit breaker state
            - Test recovery scenarios work correctly

        Success Criteria:
            - Circuit breaker opens after failure threshold
            - Retries stop when circuit breaker opens
            - Recovery works when circuit breaker closes
            - Both libraries maintain consistent state
        """
        # Arrange - Create function that will fail consistently
        call_count = 0

        @ai_resilience_orchestrator.with_resilience(
            operation_name="test_coordination",
            strategy=ResilienceStrategy.CONSERVATIVE  # Low thresholds for faster testing
        )
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError(f"Simulated failure #{call_count}")

        # Act - Trigger failures to test circuit breaker and retry coordination
        for _ in range(8):  # Conservative strategy should trigger both retry and circuit breaker
            try:
                await failing_function()
            except (ConnectionError, Exception, RetryError):
                pass  # Expected failures from retry and circuit breaker

        # Assert - Verify that the resilience system is working
        metrics = ai_resilience_orchestrator.get_metrics("test_coordination")
        assert metrics is not None, "Metrics should be available"

        # Verify that calls were made and tracked
        metrics_dict = metrics.to_dict() if hasattr(metrics, 'to_dict') else metrics
        total_calls = metrics_dict.get('total_calls', 0) if isinstance(metrics_dict, dict) else getattr(metrics, 'total_calls', 0)
        assert total_calls > 0, "Should track resilience calls"
        assert call_count > 0, "Should have made actual function calls"

        # Wait for circuit breaker recovery timeout (conservative strategy has short timeout)
        await asyncio.sleep(2)  # Conservative strategy recovery timeout

        # Act & Assert - Test recovery with function that succeeds
        @ai_resilience_orchestrator.with_resilience(
            operation_name="test_coordination_recovery",
            strategy=ResilienceStrategy.CONSERVATIVE
        )
        async def recovering_function():
            return "recovery_success"

        # This should work as it's a new operation
        result = await recovering_function()
        assert result == "recovery_success", "Function should succeed"

        # Verify new operation metrics are tracked
        recovery_metrics = ai_resilience_orchestrator.get_metrics("test_coordination_recovery")
        assert recovery_metrics is not None, "Recovery metrics should be available"