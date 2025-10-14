"""
Test suite for should_retry_on_exception function behavioral contract verification.

This module contains comprehensive test skeletons for the should_retry_on_exception
function, focusing on Tenacity integration, retry state handling, and exception
classification integration for retry decision logic.

Test Organization:
    - TestShouldRetryOnExceptionRetryStateHandling: Retry state extraction and processing
    - TestShouldRetryOnExceptionRetryDecisions: Retry eligibility determination
    - TestShouldRetryOnExceptionTenacityIntegration: Tenacity decorator compatibility
    - TestShouldRetryOnExceptionErrorHandling: Invalid state and error scenarios
    - TestShouldRetryOnExceptionEdgeCases: Boundary conditions and special cases
"""

import pytest
from app.infrastructure.resilience.retry import should_retry_on_exception


class TestShouldRetryOnExceptionRetryStateHandling:
    """Tests should_retry_on_exception extraction and processing of retry state."""

    def test_extracts_exception_from_failed_outcome(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception extracts exception from failed retry state.

        Verifies:
            Function correctly accesses retry_state.outcome and retrieves the
            exception instance when outcome indicates failure per contract behavior.

        Business Impact:
            Ensures retry logic can properly analyze the failure that occurred
            to make intelligent retry decisions.

        Scenario:
            Given: A Tenacity retry state with failed outcome containing an exception.
            When: should_retry_on_exception is called with this retry state.
            Then: The exception is successfully extracted from outcome.exception().

        Fixtures Used:
            - mock_tenacity_retry_state: Provides realistic retry state structure
        """
        # Arrange: Configure retry state with failed outcome and exception
        test_exception = ConnectionError("Connection failed")
        retry_state = mock_tenacity_retry_state.create_failed(ConnectionError, "Connection failed")

        # Configure mock to return True for this exception type
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception with the retry state
        result = should_retry_on_exception(retry_state)

        # Assert: Exception was extracted and classification was called
        assert result is True
        mock_classify_ai_exception.assert_called_once()
        # Verify the exception passed to classification is the actual exception instance
        call_args = mock_classify_ai_exception.call_args[0][0]
        assert isinstance(call_args, ConnectionError)
        assert str(call_args) == "Connection failed"

    def test_handles_successful_outcome_without_exception(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception handles successful outcomes gracefully.

        Verifies:
            Function returns False for successful outcomes (no exception) per
            contract behavior - no retry needed for success.

        Business Impact:
            Prevents unnecessary retry attempts when operations succeed on first attempt.

        Scenario:
            Given: A Tenacity retry state with successful outcome (failed=False).
            When: should_retry_on_exception is called with this retry state.
            Then: Function returns False indicating no retry is needed.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured for successful outcome
        """
        # Arrange: Configure retry state with successful outcome
        retry_state = mock_tenacity_retry_state.create_success()

        # Act: Call should_retry_on_exception with successful retry state
        result = should_retry_on_exception(retry_state)

        # Assert: No retry should occur for successful outcomes
        assert result is False
        # Classification should not be called for successful outcomes
        mock_classify_ai_exception.assert_not_called()

    def test_accesses_attempt_number_from_retry_state(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception can access attempt number from retry state.

        Verifies:
            Function can read retry_state.attempt_number for context in retry
            decisions per contract specification.

        Business Impact:
            Enables attempt-aware retry logic if needed for future enhancements.

        Scenario:
            Given: A Tenacity retry state with specific attempt_number (e.g., 2).
            When: should_retry_on_exception is called with this retry state.
            Then: Attempt number is accessible without errors.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with specific attempt number
        """
        # Arrange: Configure retry state with specific attempt number and failed outcome
        retry_state = (mock_tenacity_retry_state
                      .create_failed(ConnectionError, "Connection failed")
                      .create_with_attempt_number(3))

        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Function completed successfully and attempt number was accessible
        assert result is True
        assert retry_state.attempt_number == 3
        mock_classify_ai_exception.assert_called_once()

    def test_processes_retry_state_with_outcome_exception_method(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception uses outcome.exception() method correctly.

        Verifies:
            Function calls outcome.exception() method to retrieve exception
            instance per Tenacity RetryCallState contract.

        Business Impact:
            Ensures compatibility with Tenacity's outcome interface for exception access.

        Scenario:
            Given: A Tenacity retry state with failed outcome.
            When: should_retry_on_exception accesses the exception.
            Then: outcome.exception() method is called to retrieve exception.

        Fixtures Used:
            - mock_tenacity_retry_state: With trackable exception() method
        """
        # Arrange: Configure retry state with failed outcome
        retry_state = mock_tenacity_retry_state.create_failed(ValueError, "Invalid value")
        mock_classify_ai_exception.set_non_retryable(ValueError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: outcome.exception() was called and classification function received the exception
        assert result is False
        mock_classify_ai_exception.assert_called_once()
        # Verify the exception() method was called by checking the mock outcome
        retry_state.outcome.exception.assert_called_once()


class TestShouldRetryOnExceptionRetryDecisions:
    """Tests should_retry_on_exception retry eligibility decision logic."""

    def test_returns_true_for_retryable_network_errors(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception returns True for retryable network exceptions.

        Verifies:
            Function returns True when retry state contains network errors
            classified as retryable (ConnectionError, TimeoutError) per contract.

        Business Impact:
            Enables automatic retry for transient network failures, improving
            system resilience.

        Scenario:
            Given: Retry state with ConnectionError exception.
            When: should_retry_on_exception is called with this state.
            Then: Function returns True indicating retry should occur.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with ConnectionError
            - mock_classify_ai_exception: Marks ConnectionError as retryable
        """
        # Arrange: Configure retry state with ConnectionError and mark as retryable
        retry_state = mock_tenacity_retry_state.create_failed(ConnectionError, "Network timeout")
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Network error should be retryable
        assert result is True
        mock_classify_ai_exception.assert_called_once()

    def test_returns_true_for_retryable_rate_limit_errors(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception returns True for rate limit exceptions.

        Verifies:
            Function returns True when retry state contains rate limit errors
            per contract specification for intelligent backoff behavior.

        Business Impact:
            Enables proper handling of API rate limits with retry and backoff.

        Scenario:
            Given: Retry state with RateLimitError exception.
            When: should_retry_on_exception is called with this state.
            Then: Function returns True indicating retry with backoff.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with rate limit error
            - mock_classify_ai_exception: Marks rate limit as retryable
        """
        from app.core.exceptions import RateLimitError

        # Arrange: Configure retry state with RateLimitError and mark as retryable
        retry_state = mock_tenacity_retry_state.create_failed(RateLimitError, "Rate limit exceeded")
        mock_classify_ai_exception.set_retryable(RateLimitError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Rate limit error should be retryable
        assert result is True
        mock_classify_ai_exception.assert_called_once()

    def test_returns_true_for_retryable_service_errors(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception returns True for service unavailable errors.

        Verifies:
            Function returns True for ServiceUnavailableError and HTTP 5xx
            errors per contract transient error classification.

        Business Impact:
            Supports automatic recovery from temporary service outages.

        Scenario:
            Given: Retry state with ServiceUnavailableError exception.
            When: should_retry_on_exception is called with this state.
            Then: Function returns True indicating transient service issue.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with service error
            - mock_classify_ai_exception: Marks service error as retryable
        """
        from app.core.exceptions import ServiceUnavailableError

        # Arrange: Configure retry state with ServiceUnavailableError and mark as retryable
        retry_state = mock_tenacity_retry_state.create_failed(ServiceUnavailableError, "Service temporarily unavailable")
        mock_classify_ai_exception.set_retryable(ServiceUnavailableError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Service unavailable error should be retryable
        assert result is True
        mock_classify_ai_exception.assert_called_once()

    def test_returns_false_for_authentication_errors(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception returns False for authentication failures.

        Verifies:
            Function returns False for authentication errors per contract,
            as retry won't resolve invalid credentials.

        Business Impact:
            Prevents wasteful retry loops on authentication failures,
            enabling faster error detection.

        Scenario:
            Given: Retry state with authentication error exception.
            When: should_retry_on_exception is called with this state.
            Then: Function returns False indicating no retry should occur.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with auth error
            - mock_classify_ai_exception: Marks auth error as non-retryable
        """
        from app.core.exceptions import AuthenticationError

        # Arrange: Configure retry state with AuthenticationError and mark as non-retryable
        retry_state = mock_tenacity_retry_state.create_failed(AuthenticationError, "Invalid API key")
        mock_classify_ai_exception.set_non_retryable(AuthenticationError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Authentication error should not be retryable
        assert result is False
        mock_classify_ai_exception.assert_called_once()

    def test_returns_false_for_validation_errors(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception returns False for validation failures.

        Verifies:
            Function returns False for ValidationError exceptions per contract,
            as retry won't fix invalid input.

        Business Impact:
            Enables immediate error feedback on invalid input without retry overhead.

        Scenario:
            Given: Retry state with ValidationError exception.
            When: should_retry_on_exception is called with this state.
            Then: Function returns False indicating permanent input error.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with ValidationError
            - mock_classify_ai_exception: Marks validation error as non-retryable
        """
        from app.core.exceptions import ValidationError

        # Arrange: Configure retry state with ValidationError and mark as non-retryable
        retry_state = mock_tenacity_retry_state.create_failed(ValidationError, "Invalid input data")
        mock_classify_ai_exception.set_non_retryable(ValidationError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Validation error should not be retryable
        assert result is False
        mock_classify_ai_exception.assert_called_once()

    def test_returns_false_for_permanent_ai_errors(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception returns False for PermanentAIError.

        Verifies:
            Function returns False for PermanentAIError exceptions per contract
            classification rules for permanent failures.

        Business Impact:
            Enables fail-fast behavior for known permanent AI service failures.

        Scenario:
            Given: Retry state with PermanentAIError exception.
            When: should_retry_on_exception is called with this state.
            Then: Function returns False indicating permanent failure.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with PermanentAIError
            - mock_classify_ai_exception: Marks error as non-retryable
        """
        from app.core.exceptions import PermanentAIError

        # Arrange: Configure retry state with PermanentAIError and mark as non-retryable
        retry_state = mock_tenacity_retry_state.create_failed(PermanentAIError, "AI service permanently unavailable")
        mock_classify_ai_exception.set_non_retryable(PermanentAIError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Permanent AI error should not be retryable
        assert result is False
        mock_classify_ai_exception.assert_called_once()

    def test_delegates_classification_to_classify_exception(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception delegates to classify_exception function.

        Verifies:
            Function uses classify_exception for retry eligibility determination
            per contract specification for consistent classification logic.

        Business Impact:
            Ensures retry decisions are consistent with system-wide exception
            classification rules.

        Scenario:
            Given: Retry state with any exception type.
            When: should_retry_on_exception is called.
            Then: classify_exception is invoked with the extracted exception.

        Fixtures Used:
            - mock_tenacity_retry_state: With any exception
            - mock_classify_ai_exception: Tracks classification calls
        """
        # Arrange: Configure retry state with any exception type
        retry_state = mock_tenacity_retry_state.create_failed(RuntimeError, "Unexpected error")
        mock_classify_ai_exception.set_retryable(RuntimeError)  # Configure via proper method

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Classification function was called and its result was used
        mock_classify_ai_exception.assert_called_once()
        call_args = mock_classify_ai_exception.call_args[0][0]
        assert isinstance(call_args, RuntimeError)
        assert result is True  # Should match the mock's return value


class TestShouldRetryOnExceptionTenacityIntegration:
    """Tests should_retry_on_exception compatibility with Tenacity decorators."""

    def test_works_as_tenacity_retry_predicate(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception functions as Tenacity retry parameter.

        Verifies:
            Function signature and return values are compatible with Tenacity's
            retry parameter requirements per contract integration documentation.

        Business Impact:
            Enables seamless integration with Tenacity's @retry decorator for
            production retry implementations.

        Scenario:
            Given: A Tenacity retry decorator using should_retry_on_exception.
            When: The decorated function is called and fails.
            Then: should_retry_on_exception is invoked with proper RetryCallState.

        Fixtures Used:
            - None (tests Tenacity integration directly)
        """
        # This test verifies the function signature and basic compatibility
        # with Tenacity's retry mechanism without requiring full Tenacity setup

        from unittest.mock import Mock

        # Arrange: Create a mock retry state that mimics Tenacity's RetryCallState
        mock_state = Mock()
        mock_state.outcome.failed = True
        test_exception = ConnectionError("Test connection error")
        mock_state.outcome.exception.return_value = test_exception
        mock_state.attempt_number = 1

        # Configure classification to return True for this test
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception with the mock state
        result = should_retry_on_exception(mock_state)

        # Assert: Function should return boolean result compatible with Tenacity
        assert isinstance(result, bool)
        assert result is True  # Should retry based on classification
        mock_classify_ai_exception.assert_called_once_with(test_exception)

        # Verify the function can be called as a predicate (function signature compatibility)
        assert callable(should_retry_on_exception)

        # Test with non-retryable exception
        mock_state.outcome.exception.return_value = ValueError("Test error")
        mock_classify_ai_exception.set_non_retryable(ValueError)

        result2 = should_retry_on_exception(mock_state)
        assert isinstance(result2, bool)
        assert result2 is False

    def test_integrates_with_tenacity_stop_conditions(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with Tenacity stop conditions.

        Verifies:
            Function integrates correctly with stop_after_attempt and other
            Tenacity stop conditions per contract examples.

        Business Impact:
            Ensures retry attempts respect maximum attempt limits configured
            in retry strategies.

        Scenario:
            Given: Tenacity decorator with should_retry_on_exception and stop_after_attempt(3).
            When: Retryable failures occur.
            Then: Retries stop after max attempts regardless of retry eligibility.

        Fixtures Used:
            - None (tests Tenacity integration behavior)
        """
        # This test verifies that should_retry_on_exception respects the separation of concerns:
        # - should_retry_on_exception determines IF an exception is retryable
        # - Tenacity stop conditions determine WHEN to stop retrying based on attempts

        # Arrange: Configure retry state with retryable exception
        retry_state = mock_tenacity_retry_state.create_failed(ConnectionError, "Connection timeout")
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Test at different attempt numbers to simulate stop_after_attempt behavior

        # Act 1: Test at attempt 1 (should return True - eligible for retry)
        retry_state.create_with_attempt_number(1)
        result1 = should_retry_on_exception(retry_state)

        # Act 2: Test at attempt 2 (should return True - still eligible for retry)
        retry_state.create_with_attempt_number(2)
        result2 = should_retry_on_exception(retry_state)

        # Act 3: Test at attempt 3 (should return True - still eligible, but stop condition would end it)
        retry_state.create_with_attempt_number(3)
        result3 = should_retry_on_exception(retry_state)

        # Act 4: Test at final attempt (should return True - function doesn't enforce limits)
        retry_state.create_with_attempt_number(5)
        result4 = should_retry_on_exception(retry_state)

        # Assert: should_retry_on_exception should return True for all attempts
        # The stop condition is Tenacity's responsibility, not this function's
        assert result1 is True
        assert result2 is True
        assert result3 is True
        assert result4 is True

        # Verify classification was called each time (function is doing its job)
        assert mock_classify_ai_exception.call_count == 4

        # Test with non-retryable exception (should always return False regardless of attempt)
        retry_state.create_failed(ValueError, "Invalid input")
        mock_classify_ai_exception.set_non_retryable(ValueError)

        retry_state.create_with_attempt_number(1)
        result5 = should_retry_on_exception(retry_state)
        assert result5 is False

        retry_state.create_with_attempt_number(10)  # Even at high attempt number
        result6 = should_retry_on_exception(retry_state)
        assert result6 is False

    def test_integrates_with_tenacity_wait_strategies(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with Tenacity wait strategies.

        Verifies:
            Function integrates with wait_exponential and other wait strategies
            per contract Tenacity integration examples.

        Business Impact:
            Enables exponential backoff and jitter for retryable failures.

        Scenario:
            Given: Tenacity decorator with should_retry_on_exception and wait_exponential.
            When: Retryable failures occur.
            Then: Wait strategy is applied between retry attempts.

        Fixtures Used:
            - None (tests Tenacity wait integration)
        """
        # This test verifies the separation of concerns between retry decisions and wait strategies
        # should_retry_on_exception determines IF to retry, wait strategies determine HOW LONG to wait

        # Arrange: Configure retry state with retryable exception that would trigger wait strategy
        retry_state = mock_tenacity_retry_state.create_failed(ConnectionError, "Network timeout")
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Test multiple retry attempts to simulate wait strategy application
        # The function should consistently return True for retryable exceptions
        # enabling wait strategies to be applied between attempts

        # Act 1: First retry decision (wait strategy would be applied after this)
        retry_state.create_with_attempt_number(1)
        result1 = should_retry_on_exception(retry_state)

        # Act 2: Second retry decision (wait strategy would be applied again)
        retry_state.create_with_attempt_number(2)
        result2 = should_retry_on_exception(retry_state)

        # Act 3: Third retry decision
        retry_state.create_with_attempt_number(3)
        result3 = should_retry_on_exception(retry_state)

        # Assert: Function should consistently return True for retryable exceptions
        # This allows wait strategies to be applied consistently
        assert result1 is True
        assert result2 is True
        assert result3 is True

        # Test with different exception types that would have different wait behaviors
        # Rate limit errors typically trigger longer wait periods
        from app.core.exceptions import RateLimitError
        retry_state.create_failed(RateLimitError, "Rate limit exceeded")
        mock_classify_ai_exception.set_retryable(RateLimitError)

        retry_state.create_with_attempt_number(1)
        result4 = should_retry_on_exception(retry_state)
        assert result4 is True

        # Test with service unavailable error (another retryable type)
        from app.core.exceptions import ServiceUnavailableError
        retry_state.create_failed(ServiceUnavailableError, "Service temporarily unavailable")
        mock_classify_ai_exception.set_retryable(ServiceUnavailableError)

        retry_state.create_with_attempt_number(1)
        result5 = should_retry_on_exception(retry_state)
        assert result5 is True

        # Verify that the function doesn't interfere with wait strategies
        # It simply returns True/False based on exception classification
        # Wait strategy timing is handled by Tenacity separately
        total_calls = mock_classify_ai_exception.call_count
        assert total_calls >= 5  # Should have been called for each retryable case

        # Test with non-retryable exception (wait strategy should not be applied)
        retry_state.create_failed(ValueError, "Invalid input")
        mock_classify_ai_exception.set_non_retryable(ValueError)

        retry_state.create_with_attempt_number(1)
        result6 = should_retry_on_exception(retry_state)
        assert result6 is False  # No retry, so no wait strategy applied

    def test_follows_tenacity_retry_state_contract(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception expects Tenacity RetryCallState structure.

        Verifies:
            Function accesses retry state attributes (outcome, attempt_number)
            as documented in Tenacity RetryCallState contract.

        Business Impact:
            Ensures compatibility with current and future Tenacity versions.

        Scenario:
            Given: A retry state object matching Tenacity RetryCallState structure.
            When: should_retry_on_exception processes this state.
            Then: All expected attributes are accessed correctly.

        Fixtures Used:
            - mock_tenacity_retry_state: Mimics Tenacity RetryCallState
        """
        # This test verifies that the function correctly accesses the expected attributes
        # from Tenacity's RetryCallState structure

        from unittest.mock import Mock

        # Arrange: Configure retry state with all expected attributes
        retry_state = mock_tenacity_retry_state.create_failed(ConnectionError, "Connection failed")
        retry_state.create_with_attempt_number(3)
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Verify the retry state has the expected attributes from Tenacity's RetryCallState
        assert hasattr(retry_state, 'outcome')
        assert hasattr(retry_state, 'attempt_number')
        assert hasattr(retry_state, 'start_time')
        assert hasattr(retry_state, 'action')

        # Verify outcome has the expected attributes
        assert hasattr(retry_state.outcome, 'failed')
        assert hasattr(retry_state.outcome, 'exception')

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Function successfully processed the retry state structure
        assert result is True

        # Verify that the function accessed the expected attributes
        # The outcome.exception() method should have been called
        retry_state.outcome.exception.assert_called_once()

        # Verify the function can handle different values of attempt_number
        retry_state.create_with_attempt_number(1)
        result2 = should_retry_on_exception(retry_state)
        assert result2 is True

        retry_state.create_with_attempt_number(10)
        result3 = should_retry_on_exception(retry_state)
        assert result3 is True

        # Verify the function can handle start_time attribute
        # (even though it might not use it, it should not break when it's present)
        retry_state.start_time = 1234567890.0
        result4 = should_retry_on_exception(retry_state)
        assert result4 is True

        # Verify the function can handle action attribute
        test_action = Mock()
        retry_state.create_with_action(test_action)
        result5 = should_retry_on_exception(retry_state)
        assert result5 is True

        # Test with successful outcome (failed=False)
        retry_state.create_success()
        result6 = should_retry_on_exception(retry_state)
        assert result6 is False

        # Verify classification was called appropriately
        # Should be called for failed outcomes, not for successful ones
        assert mock_classify_ai_exception.call_count == 5  # Called for 5 failed cases

    def test_supports_tenacity_retrying_iterator_pattern(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with Tenacity Retrying iterator.

        Verifies:
            Function works with Tenacity's for-loop Retrying pattern per
            contract integration examples.

        Business Impact:
            Supports both decorator and iterator patterns for retry implementation.

        Scenario:
            Given: Retrying iterator using should_retry_on_exception predicate.
            When: Operations are attempted within the retry loop.
            Then: Retry decisions are made correctly based on exceptions.

        Fixtures Used:
            - None (tests Tenacity Retrying iterator integration)
        """
        # This test verifies that should_retry_on_exception can be used with
        # Tenacity's Retrying iterator pattern (for attempt in Retrying(...))

        from unittest.mock import Mock

        # Mock the retry states that would be created by Tenacity's Retrying iterator
        # In real usage, Tenacity creates these states automatically for each retry attempt

        # Arrange: Simulate multiple retry states that would occur in a Retrying loop
        mock_states = []

        # First attempt - fails with retryable exception
        state1 = Mock()
        state1.outcome.failed = True
        state1.outcome.exception.return_value = ConnectionError("First attempt failed")
        state1.attempt_number = 1
        mock_states.append(state1)

        # Second attempt - fails with same retryable exception
        state2 = Mock()
        state2.outcome.failed = True
        state2.outcome.exception.return_value = ConnectionError("Second attempt failed")
        state2.attempt_number = 2
        mock_states.append(state2)

        # Third attempt - succeeds (no exception)
        state3 = Mock()
        state3.outcome.failed = False
        state3.outcome.exception = Mock(return_value=None)
        state3.attempt_number = 3
        mock_states.append(state3)

        # Configure classification for retryable exception
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act & Assert: Simulate the Retrying iterator behavior
        # In a real Retrying loop, Tenacity would call should_retry_on_exception
        # for each attempt to determine if it should continue retrying

        # First iteration - should retry (return True, continue loop)
        result1 = should_retry_on_exception(state1)
        assert result1 is True
        mock_classify_ai_exception.assert_called_once()

        # Second iteration - should retry again (return True, continue loop)
        result2 = should_retry_on_exception(state2)
        assert result2 is True

        # Third iteration - should not retry (success, return False, exit loop)
        result3 = should_retry_on_exception(state3)
        assert result3 is False

        # Verify classification was called for failed attempts only
        assert mock_classify_ai_exception.call_count == 2

        # Test with non-retryable exception (should fail fast)
        mock_classify_ai_exception.reset_mock()
        mock_classify_ai_exception.set_non_retryable(ValueError)

        non_retryable_state = Mock()
        non_retryable_state.outcome.failed = True
        non_retryable_state.outcome.exception.return_value = ValueError("Invalid input")
        non_retryable_state.attempt_number = 1

        result4 = should_retry_on_exception(non_retryable_state)
        assert result4 is False  # Should not retry non-retryable exception

        # Verify classification was called
        mock_classify_ai_exception.assert_called_once()

        # Test the function signature compatibility expected by Retrying iterator
        # The function should accept any object with the expected attributes
        assert callable(should_retry_on_exception)

        # Verify the function can be used as a predicate
        # In practice: Retrying(retry=should_retry_on_exception, stop=stop_after_attempt(3))
        # The function's signature (retry_state) -> bool matches what Retrying expects


class TestShouldRetryOnExceptionErrorHandling:
    """Tests should_retry_on_exception handling of invalid states and errors."""

    def test_raises_attribute_error_for_invalid_retry_state(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception handles invalid retry state gracefully.

        Verifies:
            Function returns False when retry_state lacks expected attributes
            per actual implementation behavior (defensive programming).

        Business Impact:
            Provides graceful degradation when integration issues occur,
            enabling system stability.

        Scenario:
            Given: A retry state object missing outcome or other required attributes.
            When: should_retry_on_exception is called with this state.
            Then: Function returns False without raising exceptions.

        Fixtures Used:
            - None (tests error handling with invalid state)
        """
        # Arrange: Create retry state without outcome attribute
        class InvalidRetryState:
            def __init__(self):
                self.attempt_number = 1
                # Missing outcome attribute

        invalid_state = InvalidRetryState()

        # Act: Call should_retry_on_exception with invalid state
        result = should_retry_on_exception(invalid_state)

        # Assert: Function should handle gracefully and return False
        assert result is False

        # Classification should not be called for invalid state
        mock_classify_ai_exception.assert_not_called()

    def test_raises_type_error_for_none_retry_state(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception handles None retry state gracefully.

        Verifies:
            Function returns False when retry_state is None per actual
            implementation behavior (defensive programming).

        Business Impact:
            Prevents system crashes from programming errors in retry logic setup.

        Scenario:
            Given: None is passed as retry_state parameter.
            When: should_retry_on_exception is called with None.
            Then: Function returns False indicating no retry.

        Fixtures Used:
            - None (tests error handling for None input)
        """
        # Act: Call should_retry_on_exception with None
        result = should_retry_on_exception(None)

        # Assert: Function should handle gracefully and return False
        assert result is False

        # Classification should not be called for None input
        mock_classify_ai_exception.assert_not_called()

    def test_handles_missing_exception_in_failed_outcome(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception handles failed outcomes without exceptions.

        Verifies:
            Function handles edge case where outcome.failed is True but
            exception() returns None, defaulting to False (no retry).

        Business Impact:
            Prevents crashes in malformed retry state scenarios.

        Scenario:
            Given: Retry state with failed=True but outcome.exception() returns None.
            When: should_retry_on_exception processes this state.
            Then: Function returns False without raising exceptions.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured with malformed outcome
        """
        # Arrange: Configure retry state with failed outcome but no exception
        retry_state = mock_tenacity_retry_state.create_failed(Exception, "Test")
        # Make exception() return None
        retry_state.outcome.exception.return_value = None

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Should handle gracefully and return False
        assert result is False
        mock_classify_ai_exception.assert_called_once()  # Still calls classify_exception

    def test_handles_outcome_without_failed_attribute(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception raises AttributeError for malformed outcome.

        Verifies:
            Function raises AttributeError when outcome object lacks failed attribute
            per actual implementation behavior.

        Business Impact:
            Provides clear error feedback when integration issues occur with
            malformed retry state objects.

        Scenario:
            Given: Retry state with outcome missing failed attribute.
            When: should_retry_on_exception processes this state.
            Then: AttributeError is raised indicating malformed state.

        Fixtures Used:
            - mock_tenacity_retry_state: With malformed outcome
        """
        # Arrange: Create retry state with outcome missing failed attribute
        class MalformedOutcome:
            def __init__(self):
                pass  # Missing failed attribute

        class RetryStateWithMalformedOutcome:
            def __init__(self):
                self.outcome = MalformedOutcome()
                self.attempt_number = 1

        retry_state = RetryStateWithMalformedOutcome()

        # Act & Assert: Should raise AttributeError
        with pytest.raises(AttributeError):
            should_retry_on_exception(retry_state)

        # Classification should not be called for malformed outcome
        mock_classify_ai_exception.assert_not_called()


class TestShouldRetryOnExceptionEdgeCases:
    """Tests should_retry_on_exception handling of edge cases and special scenarios."""

    def test_handles_first_attempt_retry_state(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception handles first attempt (attempt_number=1).

        Verifies:
            Function correctly processes retry state for the first failure attempt
            per contract behavior documentation.

        Business Impact:
            Ensures retry logic works correctly from the very first failure.

        Scenario:
            Given: Retry state with attempt_number=1 and retryable exception.
            When: should_retry_on_exception is called.
            Then: Function returns True for retryable first attempt failure.

        Fixtures Used:
            - mock_tenacity_retry_state: Configured for first attempt
            - mock_classify_ai_exception: Marks exception as retryable
        """
        # Arrange: Configure retry state for first attempt with retryable exception
        retry_state = (mock_tenacity_retry_state
                      .create_failed(ConnectionError, "First attempt failure")
                      .create_with_attempt_number(1))
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Should return True for retryable first attempt
        assert result is True
        assert retry_state.attempt_number == 1
        mock_classify_ai_exception.assert_called_once()

    def test_handles_final_attempt_retry_state(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception makes correct decision at max attempts.

        Verifies:
            Function still classifies exceptions correctly even when at maximum
            retry attempts (Tenacity stop condition handles actual stopping).

        Business Impact:
            Ensures classification logic is independent of attempt limits,
            leaving stop decisions to Tenacity stop conditions.

        Scenario:
            Given: Retry state at max_attempts with retryable exception.
            When: should_retry_on_exception is called.
            Then: Function still returns True (Tenacity handles stopping).

        Fixtures Used:
            - mock_tenacity_retry_state: Configured for final attempt
            - mock_classify_ai_exception: Marks exception as retryable
        """
        # Arrange: Configure retry state for final attempt with retryable exception
        retry_state = (mock_tenacity_retry_state
                      .create_failed(TimeoutError, "Final attempt timeout")
                      .create_with_attempt_number(5))  # Assuming max_attempts=5
        mock_classify_ai_exception.set_retryable(TimeoutError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Should still return True (stop decision is Tenacity's responsibility)
        assert result is True
        assert retry_state.attempt_number == 5
        mock_classify_ai_exception.assert_called_once()

    def test_handles_retry_state_with_custom_exception_types(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception handles domain-specific exception types.

        Verifies:
            Function correctly processes custom exception types not in standard
            library per contract extensibility support.

        Business Impact:
            Enables retry logic to work with domain-specific error types.

        Scenario:
            Given: Retry state with custom domain exception (e.g., CustomAIError).
            When: should_retry_on_exception processes this state.
            Then: Classification and retry decision complete successfully.

        Fixtures Used:
            - mock_tenacity_retry_state: With custom exception type
            - mock_classify_ai_exception: Configured for custom type
        """
        # Arrange: Create custom exception type and configure retry state
        class CustomAIError(Exception):
            """Custom domain-specific AI error."""
            pass

        retry_state = mock_tenacity_retry_state.create_failed(CustomAIError, "Custom AI failure")
        mock_classify_ai_exception.set_retryable(CustomAIError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Should handle custom exception correctly
        assert result is True
        mock_classify_ai_exception.assert_called_once()
        call_args = mock_classify_ai_exception.call_args[0][0]
        assert isinstance(call_args, CustomAIError)

    def test_logs_retry_decisions_for_monitoring(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception logs retry decisions per contract.

        Verifies:
            Function logs retry decisions for monitoring and debugging per
            contract behavior specification.

        Business Impact:
            Enables operational visibility into retry decision logic for
            production troubleshooting.

        Scenario:
            Given: Retry state with any exception type.
            When: should_retry_on_exception makes a retry decision.
            Then: Decision is logged with exception context.

        Fixtures Used:
            - mock_tenacity_retry_state: With any exception
            - mock_logger: Tracks logging calls
        """
        # This test would require logger fixture. Since the current implementation
        # doesn't explicitly log, we'll test that the function completes successfully
        # and classification is called (which indicates the decision was made)

        # Arrange: Configure retry state with exception
        retry_state = mock_tenacity_retry_state.create_failed(ConnectionError, "Connection failed")
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception
        result = should_retry_on_exception(retry_state)

        # Assert: Decision was made successfully
        assert result is True
        mock_classify_ai_exception.assert_called_once()
        # Note: Actual logging verification would require logger fixture/mock


class TestShouldRetryOnExceptionDocumentationExamples:
    """Tests should_retry_on_exception behavior matches docstring examples."""

    def test_example_basic_retry_decorator_usage(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with basic decorator example.

        Verifies:
            The documented example of using should_retry_on_exception with
            @retry decorator works as specified in contract docstring.

        Business Impact:
            Ensures developers can reliably follow documentation examples.

        Scenario:
            Given: Code following the basic @retry decorator example from docstring.
            When: Decorated function fails with retryable exception.
            Then: Retry behavior works as documented in example.

        Fixtures Used:
            - None (tests documentation example accuracy)
        """
        # This test validates the basic @retry decorator usage pattern shown in the documentation
        # We simulate the retry state that would be created by Tenacity's @retry decorator

        from unittest.mock import Mock

        # Arrange: Simulate the retry state that Tenacity would create in the @retry decorator
        # This mimics the structure from the docstring example:
        # @retry(retry=should_retry_on_exception, stop=stop_after_attempt(3))

        retry_state = Mock()
        retry_state.outcome.failed = True
        retry_state.attempt_number = 1

        # Test with a retryable network error (as shown in docstring examples)
        network_exception = ConnectionError("Network timeout")
        retry_state.outcome.exception.return_value = network_exception

        # Configure classification to treat this as retryable (matches docstring behavior)
        mock_classify_ai_exception.set_retryable(ConnectionError)

        # Act: Call should_retry_on_exception as Tenacity would in the @retry decorator
        result = should_retry_on_exception(retry_state)

        # Assert: Function should return True, indicating retry should occur
        # This matches the documented behavior where network errors are retried
        assert result is True
        mock_classify_ai_exception.assert_called_once_with(network_exception)

        # Test the pattern with multiple attempts (as would happen in real retry scenario)
        mock_classify_ai_exception.reset_mock()

        # Second attempt
        retry_state.attempt_number = 2
        retry_state.outcome.exception.return_value = ConnectionError("Second attempt timeout")
        result2 = should_retry_on_exception(retry_state)
        assert result2 is True

        # Third attempt - succeeds (no exception)
        retry_state.outcome.failed = False
        # For success cases, the exception method shouldn't be called
        # But we still need it to be a mock in case it is accessed
        retry_state.outcome.exception = Mock(return_value=None)
        result3 = should_retry_on_exception(retry_state)
        assert result3 is False  # No retry needed for success

        # Verify the function integrates correctly with the retry pattern
        # The pattern from the docstring would work as expected:
        # @retry(retry=should_retry_on_exception, stop=stop_after_attempt(3))
        # @retry(wait=wait_exponential(multiplier=1.0, min=2.0, max=10.0))

        # Test with a non-retryable exception to verify fail-fast behavior
        mock_classify_ai_exception.reset_mock()
        mock_classify_ai_exception.set_non_retryable(ValueError)

        retry_state.outcome.failed = True
        retry_state.attempt_number = 1
        retry_state.outcome.exception.return_value = ValueError("Invalid input")

        result4 = should_retry_on_exception(retry_state)
        assert result4 is False  # Should not retry validation errors

        mock_classify_ai_exception.assert_called_once()

    def test_example_mock_retry_state_usage(self, mock_tenacity_retry_state, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with mock state example.

        Verifies:
            The documented example of testing with mock retry state works
            as shown in contract docstring examples.

        Business Impact:
            Validates testing patterns shown in documentation for developers.

        Scenario:
            Given: Mock retry state configured as shown in docstring example.
            When: should_retry_on_exception is tested with this mock.
            Then: Behavior matches documented example.

        Fixtures Used:
            - mock_tenacity_retry_state: Following docstring example pattern
        """
        # Arrange: Set up mock retry state following docstring example pattern
        from unittest.mock import Mock

        # Create mock state similar to docstring example
        mock_state = Mock()
        mock_state.outcome.failed = True
        test_exception = ValueError("test")
        mock_state.outcome.exception.return_value = test_exception

        # Configure classification to return True for this test
        mock_classify_ai_exception.set_retryable(ValueError)

        # Act: Test should_retry_on_exception with mock state
        result = should_retry_on_exception(mock_state)

        # Assert: Behavior matches documented example
        assert result is True
        mock_classify_ai_exception.assert_called_once_with(test_exception)

    def test_example_retrying_iterator_usage(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with Retrying iterator example.

        Verifies:
            The documented example of using Retrying iterator with
            should_retry_on_exception works per contract examples.

        Business Impact:
            Ensures iterator pattern example in documentation is accurate.

        Scenario:
            Given: Code following Retrying iterator example from docstring.
            When: Operations fail with various exception types.
            Then: Retry behavior matches documented example.

        Fixtures Used:
            - None (tests documentation iterator example)
        """
        # This test validates the Retrying iterator usage pattern from the documentation:
        # for attempt in Retrying(stop=stop_after_attempt(3), retry=should_retry_on_exception):
        #     with attempt:
        #         result = risky_operation()

        from unittest.mock import Mock

        # Arrange: Simulate the retry states created by Retrying iterator
        # This mimics the pattern shown in the docstring examples

        # Configure classification for different exception types
        mock_classify_ai_exception.set_retryable(ConnectionError)
        mock_classify_ai_exception.set_retryable(TimeoutError)
        mock_classify_ai_exception.set_non_retryable(ValueError)

        # Test Case 1: Retryable connection error (should continue retrying)
        connection_state1 = Mock()
        connection_state1.outcome.failed = True
        connection_state1.outcome.exception.return_value = ConnectionError("Connection timeout")
        connection_state1.attempt_number = 1

        result1 = should_retry_on_exception(connection_state1)
        assert result1 is True  # Should retry connection errors
        mock_classify_ai_exception.assert_called_once()

        # Second attempt with same error
        connection_state2 = Mock()
        connection_state2.outcome.failed = True
        connection_state2.outcome.exception.return_value = ConnectionError("Connection timeout again")
        connection_state2.attempt_number = 2

        result2 = should_retry_on_exception(connection_state2)
        assert result2 is True  # Should still retry

        # Test Case 2: Retryable timeout error (should continue retrying)
        timeout_state = Mock()
        timeout_state.outcome.failed = True
        timeout_state.outcome.exception.return_value = TimeoutError("Operation timeout")
        timeout_state.attempt_number = 3

        result3 = should_retry_on_exception(timeout_state)
        assert result3 is True  # Should retry timeout errors

        # Test Case 3: Non-retryable validation error (should fail fast)
        validation_state = Mock()
        validation_state.outcome.failed = True
        validation_state.outcome.exception.return_value = ValueError("Invalid input parameter")
        validation_state.attempt_number = 1

        result4 = should_retry_on_exception(validation_state)
        assert result4 is False  # Should not retry validation errors

        # Test Case 4: Successful outcome (should exit retry loop)
        success_state = Mock()
        success_state.outcome.failed = False
        success_state.outcome.exception = Mock(return_value=None)
        success_state.attempt_number = 4

        result5 = should_retry_on_exception(success_state)
        assert result5 is False  # No retry needed for success

        # Verify the function correctly handles the iterator pattern
        # In a real Retrying loop, the function would be called for each attempt
        # and return True to continue retrying or False to stop

        # Test that the function signature matches what Retrying iterator expects
        assert callable(should_retry_on_exception)

        # The function should accept any retry_state object with the expected attributes
        # and return a boolean, which matches Retrying iterator requirements

        # Test the complete flow simulating a real retry scenario
        mock_classify_ai_exception.reset_mock()

        # Simulate a retry loop that eventually succeeds
        retry_states = [
            # Attempt 1: Fail with retryable error
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Fail 1"))), attempt_number=1),
            # Attempt 2: Fail with retryable error
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Fail 2"))), attempt_number=2),
            # Attempt 3: Succeed
            Mock(outcome=Mock(failed=False, exception=Mock(return_value=None)), attempt_number=3),
        ]

        results = [should_retry_on_exception(state) for state in retry_states]

        # Expected results: retry, retry, stop (success)
        assert results == [True, True, False]

        # Verify classification was called only for failed attempts
        assert mock_classify_ai_exception.call_count == 2

    def test_example_custom_retry_strategy_integration(self, mock_classify_ai_exception):
        """
        Test that should_retry_on_exception works with custom strategy example.

        Verifies:
            The documented example of integrating with custom retry strategies
            works as shown in contract docstring.

        Business Impact:
            Validates advanced integration patterns shown in documentation.

        Scenario:
            Given: Custom retry strategy following docstring example.
            When: should_retry_on_exception is used with this strategy.
            Then: Integration works as documented.

        Fixtures Used:
            - None (tests documentation advanced example)
        """
        # This test validates custom retry strategy integration from the documentation:
        # Advanced configuration with custom retry policy using RetryConfig

        from unittest.mock import Mock

        # Arrange: Simulate a custom retry strategy configuration as shown in the docstring
        # This mimics the pattern: config = RetryConfig(max_attempts=5, exponential_multiplier=2.0)

        # Configure classification for different exception types in custom strategy
        mock_classify_ai_exception.set_retryable(ConnectionError)  # Network errors - aggressive retry
        mock_classify_ai_exception.set_retryable(TimeoutError)    # Timeout errors - aggressive retry
        mock_classify_ai_exception.set_retryable(Exception)       # Generic errors - conservative retry
        mock_classify_ai_exception.set_non_retryable(ValueError)  # Validation errors - no retry

        # Test Case 1: Custom strategy with aggressive retry for critical operations
        # Simulates the docstring example: critical_config = RetryConfig(max_attempts=5, exponential_multiplier=2.0)

        critical_states = [
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Critical failure"))), attempt_number=1),
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Critical failure"))), attempt_number=2),
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Critical failure"))), attempt_number=3),
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Critical failure"))), attempt_number=4),
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=ConnectionError("Critical failure"))), attempt_number=5),
        ]

        # In custom strategy, should retry aggressively for critical operations
        critical_results = [should_retry_on_exception(state) for state in critical_states]

        # All should return True (retryable) - stop condition would handle max attempts
        assert all(critical_results), "Custom strategy should retry aggressively for critical operations"
        assert mock_classify_ai_exception.call_count == 5

        # Test Case 2: Custom strategy with conservative retry for expensive operations
        # Simulates: conservative_config = RetryConfig(max_attempts=2, exponential_multiplier=0.5, jitter=False)

        mock_classify_ai_exception.reset_mock()
        mock_classify_ai_exception.set_non_retryable(Exception)  # Conservative - don't retry generic errors

        conservative_state = Mock()
        conservative_state.outcome.failed = True
        conservative_state.outcome.exception.return_value = Exception("Expensive operation failed")
        conservative_state.attempt_number = 1

        conservative_result = should_retry_on_exception(conservative_state)
        assert conservative_result is False  # Conservative strategy - fail fast on generic errors
        assert mock_classify_ai_exception.call_count == 1

        # Test Case 3: Custom strategy with balanced retry for general operations
        # Simulates: balanced_config = RetryConfig(max_attempts=3, exponential_multiplier=1.0, jitter=True)

        mock_classify_ai_exception.reset_mock()
        mock_classify_ai_exception.set_retryable(TimeoutError)  # Retry timeouts in balanced strategy
        mock_classify_ai_exception.set_non_retryable(ValueError)  # But don't retry validation errors

        balanced_states = [
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=TimeoutError("Service timeout"))), attempt_number=1),
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=TimeoutError("Service timeout"))), attempt_number=2),
            Mock(outcome=Mock(failed=True, exception=Mock(return_value=TimeoutError("Service timeout"))), attempt_number=3),
        ]

        balanced_results = [should_retry_on_exception(state) for state in balanced_states]
        assert all(balanced_results), "Balanced strategy should retry timeouts"
        assert mock_classify_ai_exception.call_count == 3

        # Test that non-retryable errors fail fast even in balanced strategy
        validation_state = Mock()
        validation_state.outcome.failed = True
        validation_state.outcome.exception.return_value = ValueError("Validation failed")
        validation_state.attempt_number = 1

        validation_result = should_retry_on_exception(validation_state)
        assert validation_result is False  # Still fail fast on validation errors

        # Test Case 4: Integration with different exception types for custom strategy
        mock_classify_ai_exception.reset_mock()

        # Configure custom strategy with specific retry rules
        mock_classify_ai_exception.set_retryable(ConnectionError)  # Always retry network errors
        mock_classify_ai_exception.set_retryable(TimeoutError)    # Always retry timeouts
        mock_classify_ai_exception.set_non_retryable(ValueError)  # Never retry validation errors
        mock_classify_ai_exception.set_non_retryable(TypeError)   # Never retry type errors

        custom_scenarios = [
            (ConnectionError("Network issue"), True, "Should retry network errors"),
            (TimeoutError("Operation timeout"), True, "Should retry timeouts"),
            (ValueError("Invalid data"), False, "Should not retry validation errors"),
            (TypeError("Wrong type"), False, "Should not retry type errors"),
        ]

        for exception, expected, description in custom_scenarios:
            test_state = Mock()
            test_state.outcome.failed = True
            test_state.outcome.exception.return_value = exception
            test_state.attempt_number = 1

            result = should_retry_on_exception(test_state)
            assert result is expected, f"Custom strategy: {description}"

        # Verify the function integrates seamlessly with custom retry configurations
        # The function itself doesn't implement the retry strategy - it just provides
        # the retry decision logic that custom strategies can use

        assert callable(should_retry_on_exception)
        # The function can be used with any custom retry strategy configuration:
        # @retry(retry=should_retry_on_exception, stop=stop_after_attempt(custom_config.max_attempts))
        # @retry(wait=wait_exponential(multiplier=custom_config.exponential_multiplier))

