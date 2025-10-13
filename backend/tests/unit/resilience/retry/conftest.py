"""
Retry module test fixtures providing external dependency isolation.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the retry component from systems outside its boundary.

External Dependencies Handled:
    - app.core.exceptions.classify_ai_exception: Core exception classification function (mocked)
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Any


@pytest.fixture
def mock_classify_ai_exception():
    """
    Mock for the classify_ai_exception function from app.core.exceptions.

    Provides a controllable mock that simulates the core exception classification
    behavior used by retry logic to determine if exceptions are retryable.
    This isolates retry module tests from the actual exception classification
    implementation while maintaining realistic behavior patterns.

    Default Behavior:
        - Returns True for transient/retryable exceptions by default
        - Returns False for permanent/non-retryable exceptions by default
        - Configurable behavior for different test scenarios
        - Call tracking for assertions in tests
        - Realistic function signature matching the real classify_ai_exception

    Configuration Methods:
        set_retryable(exception_type): Mark exception type as retryable (returns True)
        set_non_retryable(exception_type): Mark exception type as non-retryable (returns False)
        reset_behavior(): Reset to default classification behavior

    Use Cases:
        - Testing retry decision logic based on exception classification
        - Testing different exception scenarios (network, auth, rate limits)
        - Testing tenacity integration with exception classification
        - Any test requiring exception classification behavior

    Test Customization:
        def test_retry_with_custom_exceptions(mock_classify_ai_exception):
            # Configure mock for specific test scenarios
            mock_classify_ai_exception.set_retryable(ConnectionError)
            mock_classify_ai_exception.set_non_retryable(AuthenticationError)

    Example:
        def test_should_retry_on_exception(mock_classify_ai_exception):
            # Configure mock behavior
            mock_classify_ai_exception.return_value = True  # Exception is retryable

            # Test retry logic
            from app.infrastructure.resilience.retry import should_retry_on_exception

            # Create mock retry state with exception
            mock_retry_state = Mock()
            mock_retry_state.outcome.failed = True
            mock_retry_state.outcome.exception.return_value = ConnectionError("timeout")

            result = should_retry_on_exception(mock_retry_state)
            assert result is True

            # Verify classification was called
            mock_classify_ai_exception.assert_called_once()

    Default Classification Rules:
        - Network errors (ConnectionError, TimeoutError): retryable (True)
        - HTTP 5xx server errors: retryable (True)
        - HTTP 429 rate limit errors: retryable (True)
        - Authentication/authorization errors: non-retryable (False)
        - HTTP 4xx client errors: non-retryable (False)
        - Unknown exceptions: conservative approach, non-retryable (False)

    State Management:
        - Maintains classification rules across test calls
        - Can be reconfigured per test scenario
        - Provides deterministic behavior for consistent testing
        - Tracks calls and exceptions for assertion verification

    Note:
        This is a proper system boundary mock - classify_ai_exception is
        defined outside the resilience module and should be mocked to isolate
        retry logic from the core exception classification implementation.
    """
    mock = Mock(spec=callable, return_value=False)  # Default: non-retryable

    # Classification behavior storage
    classification_rules = {
        # Default retryable exceptions
        ConnectionError: True,
        TimeoutError: True,
        # Default non-retryable exceptions
        ValueError: False,
        TypeError: False,
        AuthenticationError: False,
        PermissionError: False,
    }

    def configure_behavior(exception_type, is_retryable):
        """Configure classification behavior for specific exception type."""
        classification_rules[exception_type] = is_retryable

    def get_classification(exception_instance):
        """Get classification for exception instance based on configured rules."""
        exception_type = type(exception_instance)

        # Check exact type match
        if exception_type in classification_rules:
            return classification_rules[exception_type]

        # Check for subclass matches
        for base_type, is_retryable in classification_rules.items():
            if issubclass(exception_type, base_type):
                return is_retryable

        # Default to conservative non-retryable
        return False

    def mock_classify_function(exc):
        """Mock implementation that mimics real classify_ai_exception behavior."""
        result = get_classification(exc)
        mock.return_value = result
        return result

    # Configure the mock to use our implementation
    mock.side_effect = mock_classify_function

    # Add configuration methods to the mock object
    mock.set_retryable = lambda exc_type: configure_behavior(exc_type, True)
    mock.set_non_retryable = lambda exc_type: configure_behavior(exc_type, False)
    mock.reset_behavior = lambda: classification_rules.update({
        ConnectionError: True, TimeoutError: True,
        ValueError: False, TypeError: False,
        AuthenticationError: False, PermissionError: False,
    })

    return mock


@pytest.fixture
def mock_tenacity_retry_state():
    """
    Mock Tenacity retry state for testing retry predicate integration.

    Provides a configurable mock that simulates Tenacity's RetryCallState
    object structure used by should_retry_on_exception. This enables
    testing of tenacity integration without requiring actual tenacity
    library setup or real retry execution.

    Default Behavior:
        - Simulates failed outcome with generic exception
        - Configurable exception types and outcomes
        - Realistic attribute structure matching RetryCallState
        - Supports both success and failure scenarios

    Configuration Methods:
        create_failed(exception_type, message): Create failed state with specific exception
        create_success(): Create successful outcome state
        create_with_attempt_number(attempt_num): Set attempt number for testing

    Use Cases:
        - Testing should_retry_on_exception with different retry states
        - Testing tenacity integration patterns
        - Testing retry behavior at different attempt numbers
        - Any test requiring tenacity retry state simulation

    Test Customization:
        def test_retry_at_different_attempts(mock_tenacity_retry_state):
            # Test behavior at specific attempt numbers
            retry_state = mock_tenacity_retry_state.create_with_attempt_number(3)

    Example:
        def test_should_retry_integration(mock_tenacity_retry_state, mock_classify_ai_exception):
            from app.infrastructure.resilience.retry import should_retry_on_exception

            # Configure mock state with specific exception
            retry_state = mock_tenacity_retry_state.create_failed(
                ConnectionError, "Connection timeout"
            )
            retry_state = mock_tenacity_retry_state.create_with_attempt_number(2)

            # Configure classification to mark exception as retryable
            mock_classify_ai_exception.set_retryable(ConnectionError)

            # Test retry decision
            result = should_retry_on_exception(retry_state)
            assert result is True

    State Attributes:
        - outcome: Mock outcome object with failed/exception methods
        - attempt_number: Current retry attempt number (1-based)
        - start_time: Mock timestamp for attempt start time
        - action: Mock callable that triggered the retry attempt

    Default Exception Types:
        - ConnectionError: Network connectivity issues
        - TimeoutError: Operation timeout scenarios
        - ValueError: Invalid input or state
        - Exception: Generic failure scenarios

    Note:
        This mock simulates tenacity's internal state structure for testing
        integration patterns. It doesn't require the actual tenacity library
        to be available, enabling isolated unit testing.
    """

    class MockRetryState:
        def __init__(self):
            self.outcome = MagicMock()
            self.attempt_number = 1
            self.start_time = 1234567890.0  # Mock timestamp
            self.action = Mock()

        def create_failed(self, exception_type, message="Test exception"):
            """Configure state to simulate failed outcome with specific exception."""
            exception = exception_type(message)
            self.outcome.failed = True
            self.outcome.exception.return_value = exception
            return self

        def create_success(self):
            """Configure state to simulate successful outcome."""
            self.outcome.failed = False
            self.outcome.exception = Mock(side_effect=AttributeError("No exception for successful outcome"))
            return self

        def create_with_attempt_number(self, attempt_num):
            """Set specific attempt number for testing retry limits."""
            self.attempt_number = attempt_num
            return self

        def create_with_action(self, action_callable):
            """Set specific action that triggered the retry."""
            self.action = action_callable
            return self

    return MockRetryState()


@pytest.fixture
def retry_test_scenarios():
    """
    Standardized test scenarios for retry behavior testing.

    Provides consistent test scenarios covering various retry situations,
    exception types, and configuration patterns. Ensures comprehensive
    test coverage and reduces duplication across retry module tests.

    Data Structure:
        - transient_failures: Retryable exception scenarios
        - permanent_failures: Non-retryable exception scenarios
        - rate_limit_scenarios: Rate limiting retry patterns
        - config_variants: Different retry configurations
        - edge_cases: Boundary conditions and special cases

    Use Cases:
        - Standardizing retry test inputs across test modules
        - Providing comprehensive exception scenario coverage
        - Testing different retry configuration combinations
        - Reducing test code duplication

    Example:
        def test_retry_with_various_scenarios(retry_test_scenarios, mock_classify_ai_exception):
            for scenario in retry_test_scenarios['transient_failures']:
                # Test retry behavior with each transient failure scenario
                mock_classify_ai_exception.set_retryable(scenario['exception_type'])
                # ... test retry logic ...
    """
    return {
        "transient_failures": [
            {
                "name": "connection_timeout",
                "exception_type": ConnectionError,
                "message": "Connection timeout after 30 seconds",
                "expected_retry": True,
                "expected_backoff": "exponential",
                "max_retry_attempts": 3,
                "description": "Network connection timeout should trigger retry with exponential backoff"
            },
            {
                "name": "service_unavailable",
                "exception_type": TimeoutError,
                "message": "Service temporarily unavailable",
                "expected_retry": True,
                "expected_backoff": "exponential",
                "max_retry_attempts": 3,
                "description": "Service downtime should trigger retry with exponential backoff"
            },
            {
                "name": "rate_limit_exceeded",
                "exception_type": Exception,
                "message": "Rate limit exceeded",
                "expected_retry": True,
                "expected_backoff": "exponential_with_jitter",
                "max_retry_attempts": 5,
                "description": "Rate limiting should trigger retry with backoff and jitter"
            }
        ],
        "permanent_failures": [
            {
                "name": "authentication_error",
                "exception_type": Exception,
                "message": "Invalid API credentials",
                "expected_retry": False,
                "expected_behavior": "fail_fast",
                "expected_exception_propagation": True,
                "description": "Authentication errors should fail fast without retry"
            },
            {
                "name": "invalid_request",
                "exception_type": ValueError,
                "message": "Invalid request parameters",
                "expected_retry": False,
                "expected_behavior": "fail_fast",
                "expected_exception_propagation": True,
                "description": "Client errors should fail fast without retry"
            },
            {
                "name": "permission_denied",
                "exception_type": PermissionError,
                "message": "Access denied to resource",
                "expected_retry": False,
                "expected_behavior": "fail_fast",
                "expected_exception_propagation": True,
                "description": "Authorization errors should fail fast without retry"
            }
        ],
        "config_variants": [
            {
                "name": "conservative_config",
                "max_attempts": 2,
                "exponential_multiplier": 0.5,
                "jitter": False,
                "expected_total_delay": "short",
                "expected_behavior": "fast_fail",
                "description": "Minimal retries for expensive operations"
            },
            {
                "name": "balanced_config",
                "max_attempts": 3,
                "exponential_multiplier": 1.0,
                "jitter": True,
                "expected_total_delay": "moderate",
                "expected_behavior": "balanced",
                "description": "Standard configuration for general use"
            },
            {
                "name": "aggressive_config",
                "max_attempts": 5,
                "exponential_multiplier": 2.0,
                "jitter": True,
                "expected_total_delay": "long",
                "expected_behavior": "persistent_retry",
                "description": "Maximum retries for critical operations"
            }
        ],
        "edge_cases": [
            {
                "name": "unknown_exception_type",
                "exception_type": RuntimeError,
                "message": "Unexpected error occurred",
                "expected_retry": False,
                "expected_behavior": "fail_fast",
                "expected_logging": "warning",
                "description": "Unknown exceptions should be handled conservatively with warning"
            },
            {
                "name": "none_exception",
                "exception_type": None,
                "message": None,
                "expected_retry": False,
                "expected_behavior": "immediate_failure",
                "expected_logging": "error",
                "description": "Missing exception should fail immediately with error logging"
            }
        ]
    }