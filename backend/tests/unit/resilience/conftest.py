"""
Shared test fixtures for resilience infrastructure testing.

Provides Fakes and Mocks for common external dependencies used across resilience
modules following the philosophy of creating realistic test doubles that enable
behavior-driven testing while isolating components from systems outside their boundary.

External Dependencies Handled:
    - app.core.exceptions.classify_ai_exception: Exception classification function (mocked)
"""

import pytest
from unittest.mock import Mock, MagicMock, create_autospec
from typing import Dict, Optional

# Import actual exception types for realistic mock classification behavior
from app.core.exceptions import AuthenticationError


@pytest.fixture
def mock_classify_ai_exception():
    """
    Mock for the classify_ai_exception function from app.core.exceptions.

    WHY THIS IS MOCKED:
        This fixture mocks the classification FUNCTION (not exception classes themselves).
        We mock this function to isolate resilience DECISION LOGIC from the classification
        IMPLEMENTATION. Tests verify how retry logic RESPONDS to classification results,
        not how exceptions are classified.

        IMPORTANT: The actual exception classes (ValidationError, TransientAIError, etc.)
        are NEVER mocked - tests always use real exception instances. Only the function
        that processes those exceptions is mocked at this boundary.

    Purpose:
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
        - Accepts REAL exception instances (not mocked exceptions)

    Configuration Methods:
        set_retryable(exception_type): Mark exception type as retryable (returns True)
        set_non_retryable(exception_type): Mark exception type as non-retryable (returns False)
        reset_behavior(): Reset to default classification behavior

    Use Cases:
        - Testing retry decision logic based on exception classification results
        - Testing different exception scenarios with real exception instances
        - Testing tenacity integration with exception classification
        - Isolating retry logic from classification implementation details

    Test Pattern - Use Real Exceptions:
        def test_retry_stops_on_validation_error(mock_classify_ai_exception):
            # Configure mock to classify ValidationError as non-retryable
            from app.core.exceptions import ValidationError
            mock_classify_ai_exception.set_non_retryable(ValidationError)

            # Use REAL exception instance in test
            failing_op = Mock(side_effect=ValidationError("bad input"))

            # Test retry behavior with real exception
            with pytest.raises(ValidationError):
                retry_with_classification(failing_op)

            # Should not retry on non-retryable exception
            assert failing_op.call_count == 1

    Example - Testing Classification Response:
        def test_retry_respects_classification_result(mock_classify_ai_exception):
            # Mock returns False (non-retryable) for this test scenario
            mock_classify_ai_exception.return_value = False

            # Use REAL exception instance
            from app.core.exceptions import TransientAIError
            failing_op = Mock(side_effect=TransientAIError("timeout"))

            # Verify retry logic respects classification result
            with pytest.raises(TransientAIError):
                retry_with_classification(failing_op)

            # Classification said "don't retry", so should fail immediately
            assert failing_op.call_count == 1
            mock_classify_ai_exception.assert_called_once()

    Default Classification Rules:
        These defaults mirror the real classify_ai_exception function:
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

    System Boundary Rationale:
        classify_ai_exception() is defined in app.core.exceptions (outside resilience module).
        Mocking this function is acceptable because:
        1. It's a FUNCTION that processes exceptions, not an exception class itself
        2. It crosses the resilience module boundary (external dependency)
        3. Tests focus on how retry logic USES classification, not classification itself
        4. Exception classes themselves are NEVER mocked - always use real instances

    Related Documentation:
        - docs/guides/testing/MOCKING_GUIDE.md - Mocking at boundaries
        - docs/guides/developer/EXCEPTION_HANDLING.md - Exception classification
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
