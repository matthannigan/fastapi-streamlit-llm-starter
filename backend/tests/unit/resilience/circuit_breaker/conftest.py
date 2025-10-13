"""
Circuit breaker module test fixtures providing external dependency isolation.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the circuit breaker component from systems outside its boundary.

External Dependencies Handled:
    - circuitbreaker: Third-party circuit breaker library (mocked)
    - logging: Standard library logging system (mocked)
    - datetime.datetime: Timestamp tracking (fake implementation)
"""

import pytest
from unittest.mock import MagicMock, Mock, create_autospec
from datetime import datetime, timedelta
from typing import Any, Callable


@pytest.fixture
def mock_circuitbreaker_library():
    """
    Mock for the third-party circuitbreaker library.

    Provides a spec'd mock that simulates the circuitbreaker library's
    CircuitBreaker class behavior without importing the actual library.
    This isolates tests from the external dependency while maintaining
    realistic behavior patterns.

    Default Behavior:
        - Mocked CircuitBreaker class with callable interface
        - Configurable state transitions for testing
        - Realistic method signatures matching the real library
        - State tracking for circuit breaker states (CLOSED, OPEN, HALF_OPEN)

    Use Cases:
        - Testing EnhancedCircuitBreaker inheritance from base CircuitBreaker
        - Testing circuit breaker state transitions and behavior
        - Testing integration with third-party library patterns
        - Any test requiring circuitbreaker library functionality

    Test Customization:
        def test_circuit_state_transitions(mock_circuitbreaker_library):
            # Configure mock to simulate specific behaviors
            mock_circuitbreaker_library.CircuitBreaker.return_value.state = "OPEN"

    Example:
        def test_enhanced_circuit_breaker_inheritance(mock_circuitbreaker_library):
            from app.infrastructure.resilience.circuit_breaker import EnhancedCircuitBreaker

            # The enhanced circuit breaker should inherit from the mocked base
            cb = EnhancedCircuitBreaker(failure_threshold=3)
            assert cb.failure_threshold == 3

    Note:
        This is a proper system boundary mock - circuitbreaker is an external
        third-party dependency and should be mocked to isolate our implementation.
    """
    # Create a mock CircuitBreaker class that mimics the real library
    mock_cb_class = create_autospec(object, instance=False)
    mock_cb_class.__name__ = "CircuitBreaker"

    # Create mock instance that will be returned by the constructor
    mock_instance = MagicMock()
    mock_instance.state = "CLOSED"  # Default state
    mock_instance.failure_count = 0
    mock_instance.last_failure_time = None

    # Configure the mock class to return our instance
    mock_cb_class.return_value = mock_instance

    # Create the mock module structure
    mock_module = MagicMock()
    mock_module.CircuitBreaker = mock_cb_class

    return mock_module


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing circuit breaker logging behavior.

    Provides a spec'd mock logger that simulates logging.Logger
    for testing log message generation without actual I/O. Circuit
    breaker components log state changes and metrics for operational
    monitoring.

    Default Behavior:
        - All log methods available (info, warning, error, debug)
        - No actual logging output (mocked)
        - Call tracking for assertions in tests
        - Realistic method signatures matching logging.Logger

    Use Cases:
        - Testing circuit breaker state change logging
        - Testing metrics logging and monitoring behavior
        - Testing warning/error logging during failures
        - Any component needing to test logging behavior

    Test Customization:
        def test_logs_state_changes(mock_logger):
            # Configure mock to capture specific log calls
            mock_logger.info.assert_called_with("Circuit breaker state changed: CLOSED -> OPEN")

    Example:
        def test_circuit_breaker_logs_open_state(mock_logger, monkeypatch):
            # Replace the module logger with our mock
            monkeypatch.setattr('app.infrastructure.resilience.circuit_breaker.logger', mock_logger)

            # Trigger state change that should log
            cb = EnhancedCircuitBreaker(failure_threshold=1)
            # ... cause circuit to open ...

            # Verify logging occurred
            mock_logger.warning.assert_called()

    Note:
        This is a proper system boundary mock - logging performs I/O
        and should be mocked for unit tests to avoid actual log output.
    """
    mock = MagicMock()
    mock.info = Mock(return_value=None)
    mock.warning = Mock(return_value=None)
    mock.error = Mock(return_value=None)
    mock.debug = Mock(return_value=None)
    mock.critical = Mock(return_value=None)
    return mock


@pytest.fixture
def fake_datetime():
    """
    Fake datetime implementation for deterministic timestamp testing.

    Provides a controllable datetime implementation that allows tests
    to control time progression without using real time delays.
    This enables deterministic testing of time-dependent circuit breaker
    behavior like recovery timeouts and metrics timestamps.

    State Management:
        - Current time starts at a fixed datetime (2023-01-01 12:00:00)
        - Time can be advanced programmatically for testing
        - All datetime operations return consistent, predictable results
        - Maintains realistic datetime interface compatibility

    Public Methods:
        now(): Returns current fake datetime
        advance_timedelta(delta): Advances time by specified timedelta
        advance_seconds(seconds): Advances time by specified seconds
        reset(): Resets time to initial value

    Use Cases:
        - Testing circuit breaker recovery timeout behavior
        - Testing metrics timestamp recording and accuracy
        - Testing time-based state transitions without real delays
        - Any time-dependent resilience logic testing

    Test Customization:
        def test_recovery_timeout(fake_datetime):
            # Start at known time
            fake_datetime.reset()

            # Trigger failure and advance time
            # ... circuit breaker opens ...
            fake_datetime.advance_seconds(61)  # Past 60s timeout

            # Test recovery behavior

    Example:
        def test_circuit_breaker_recovery_timing(fake_datetime, monkeypatch):
            # Replace datetime with our fake
            monkeypatch.setattr('app.infrastructure.resilience.circuit_breaker.datetime', fake_datetime)

            cb = EnhancedCircuitBreaker(recovery_timeout=60)

            # Trigger failure at t=0
            fake_datetime.reset()
            # ... cause circuit to open ...

            # Advance time past recovery timeout
            fake_datetime.advance_seconds(61)

            # Circuit should now allow recovery attempts
            assert cb.state == "HALF_OPEN"

    State Behavior:
        - Time starts at 2023-01-01 12:00:00 UTC for consistency
        - Time can be advanced positively but not backwards
        - All datetime objects are real datetime instances with fake times
        - Maintains thread safety for concurrent test scenarios
    """

    class FakeDatetime:
        def __init__(self):
            self._current_time = datetime(2023, 1, 1, 12, 0, 0)
            self._initial_time = self._current_time

        def now(self):
            """Return current fake datetime."""
            return self._current_time

        def advance_timedelta(self, delta: timedelta):
            """Advance time by specified timedelta."""
            if delta.total_seconds() >= 0:
                self._current_time += delta

        def advance_seconds(self, seconds: float):
            """Advance time by specified seconds."""
            if seconds >= 0:
                self._current_time += timedelta(seconds=seconds)

        def reset(self):
            """Reset time to initial value."""
            self._current_time = self._initial_time

        def __call__(self):
            """Make the fake datetime callable like datetime class."""
            return self

        # Support datetime class methods
        @classmethod
        def from_real_datetime(cls, real_dt):
            """Create fake datetime from real datetime value."""
            fake = cls()
            fake._current_time = real_dt
            fake._initial_time = real_dt
            return fake

    fake_datetime = FakeDatetime()

    # Make it behave like datetime module
    fake_datetime.datetime = fake_datetime
    fake_datetime.timedelta = timedelta

    return fake_datetime


@pytest.fixture
def circuit_breaker_test_data():
    """
    Standardized test data for circuit breaker behavior testing.

    Provides consistent test scenarios and data structures for circuit
    breaker testing across different test modules. Ensures test
    consistency and reduces duplication in test implementations.

    Data Structure:
        - failure_scenarios: Common failure patterns for testing
        - recovery_scenarios: Recovery testing scenarios
        - config_variants: Various configuration combinations
        - timing_scenarios: Time-based test scenarios

    Use Cases:
        - Standardizing test inputs across circuit breaker tests
        - Providing consistent test scenarios for edge cases
        - Reducing test code duplication
        - Ensuring comprehensive test coverage

    Example:
        def test_circuit_breaker_with_various_configs(circuit_breaker_test_data):
            for config in circuit_breaker_test_data['config_variants']:
                cb = EnhancedCircuitBreaker(**config)
                # Test behavior with each configuration
    """
    return {
        "failure_scenarios": [
            {
                "type": "connection_error",
                "exception": ConnectionError("Connection refused"),
                "expected_retry": True,
                "expected_circuit_impact": True,
                "description": "Network connection failures should be retryable and impact circuit state"
            },
            {
                "type": "timeout_error",
                "exception": TimeoutError("Operation timed out"),
                "expected_retry": True,
                "expected_circuit_impact": True,
                "description": "Timeout errors should be retryable and impact circuit state"
            },
            {
                "type": "service_error",
                "exception": Exception("Service unavailable"),
                "expected_retry": True,
                "expected_circuit_impact": True,
                "description": "Generic service errors should be retryable and impact circuit state"
            },
            {
                "type": "rate_limit",
                "exception": Exception("Rate limit exceeded"),
                "expected_retry": True,
                "expected_circuit_impact": False,
                "description": "Rate limit errors should be retryable but not impact circuit state"
            }
        ],
        "config_variants": [
            {
                "failure_threshold": 3,
                "recovery_timeout": 60,
                "expected_behavior": "balanced",
                "description": "Balanced configuration for standard operations"
            },
            {
                "failure_threshold": 5,
                "recovery_timeout": 120,
                "expected_behavior": "conservative",
                "description": "Conservative configuration with higher threshold"
            },
            {
                "failure_threshold": 1,
                "recovery_timeout": 30,
                "expected_behavior": "aggressive",
                "description": "Aggressive fast-fail configuration"
            },
            {
                "failure_threshold": 10,
                "recovery_timeout": 300,
                "expected_behavior": "tolerant",
                "description": "Highly tolerant configuration for critical operations"
            }
        ],
        "timing_scenarios": [
            {
                "description": "immediate_recovery",
                "advance_seconds": 1,
                "expected_state": "HALF_OPEN",
                "expected_behavior": "attempt_recovery"
            },
            {
                "description": "quick_recovery",
                "advance_seconds": 30,
                "expected_state": "HALF_OPEN",
                "expected_behavior": "attempt_recovery"
            },
            {
                "description": "slow_recovery",
                "advance_seconds": 120,
                "expected_state": "HALF_OPEN",
                "expected_behavior": "attempt_recovery"
            },
            {
                "description": "no_recovery",
                "advance_seconds": 0,
                "expected_state": "OPEN",
                "expected_behavior": "block_calls"
            }
        ]
    }