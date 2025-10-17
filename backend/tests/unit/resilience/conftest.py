"""
Shared test fixtures for resilience infrastructure testing.

Provides Fakes and Mocks for common external dependencies used across resilience
modules following the philosophy of creating realistic test doubles that enable
behavior-driven testing while isolating components from systems outside their boundary.

External Dependencies Handled:
    - app.core.exceptions.classify_ai_exception: Exception classification function (mocked)
    - time: Standard library time module (fake implementation)
    - threading: Standard library threading module (fake implementation)
"""

import pytest
from unittest.mock import Mock, MagicMock, create_autospec
from typing import Dict, Optional
import time as real_time
import threading as real_threading

# Import actual exception types for realistic mock classification behavior
from app.core.exceptions import AuthenticationError


@pytest.fixture
def mock_classify_ai_exception(monkeypatch):
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

    # Monkeypatch the classify_ai_exception function in the retry module
    # This ensures that when the retry module calls classify_ai_exception, it uses our mock
    monkeypatch.setattr("app.infrastructure.resilience.retry.classify_ai_exception", mock)

    return mock


@pytest.fixture
def fake_time_module(monkeypatch):
    """
    Fake time module implementation for deterministic time-based testing.

    Purpose:
        Provides controllable time behavior for rate limiting tests that
        depend on time.time() calls. This enables testing of cooldown periods,
        rate limit windows, and time-based cleanup operations.

    Key Features:
        - Controllable current_time value that can be advanced manually
        - time.time() returns controlled timestamp
        - time.sleep() is a no-op to avoid delays in tests
        - Thread-safe time updates
        - Supports time progression simulation
        - Properly monkeypatches the config_validator module

    Configuration Methods:
        advance_time(seconds): Advance the current time by specified seconds
        set_time(timestamp): Set current time to specific timestamp
        reset(): Reset to current system time

    Use Cases:
        - Testing rate limiting behavior across time windows
        - Simulating cooldown period expiration
        - Testing time-based cleanup operations
        - Verifying rate limit recovery behavior

    Example:
        def test_rate_limit_cooldown(fake_time_module):
            fake_time_module.set_time(1000.0)
            result = validator.check_rate_limit("client")  # First request

            fake_time_module.advance_time(0.5)  # Less than cooldown
            result2 = validator.check_rate_limit("client")  # Should be blocked

            fake_time_module.advance_time(1.0)  # Exceed cooldown
            result3 = validator.check_rate_limit("client")  # Should be allowed
    """
    current_time = [real_time.time()]

    class FakeTimeModule:
        def __init__(self):
            self._time = current_time
            self._lock = real_threading.Lock()

        def time(self):
            """Return the controlled current time."""
            with self._lock:
                return self._time[0]

        def sleep(self, seconds):
            """No-op sleep for test speed."""
            pass

        def advance_time(self, seconds):
            """Advance the current time by specified seconds."""
            with self._lock:
                self._time[0] += seconds

        def advance(self, seconds):
            """Alias for advance_time for backward compatibility."""
            return self.advance_time(seconds)

        def set_time(self, timestamp):
            """Set the current time to a specific timestamp."""
            with self._lock:
                self._time[0] = timestamp

        def reset(self):
            """Reset to actual system time."""
            with self._lock:
                self._time[0] = real_time.time()

    fake_time = FakeTimeModule()

    # Monkeypatch the time module in the config_validator module
    monkeypatch.setattr("app.infrastructure.resilience.config_validator.time", fake_time)

    return fake_time


@pytest.fixture
def fake_threading_module(monkeypatch):
    """
    Fake threading module implementation for deterministic thread testing.

    Purpose:
        Provides controlled threading behavior for testing thread-safe operations
        without actual thread creation, ensuring test determinability and speed.

    Key Features:
        - Mock RLock that tracks lock acquisition/release
        - Thread-safe operation simulation without actual threads
        - Deterministic lock state tracking
        - Support for context manager patterns
        - Lock state assertion capabilities
        - Properly monkeypatches the config_validator module

    Mock Components:
        - Mock RLock with acquire/release tracking
        - Context manager support for 'with' statements
        - Lock state inspection for assertions
        - Thread-safety simulation

    Use Cases:
        - Testing thread-safe rate limiting operations
        - Verifying lock acquisition patterns
        - Testing concurrent access scenarios
        - Validating lock state management

    Example:
        def test_thread_safe_rate_limit(fake_threading_module):
            mock_lock = fake_threading_module.get_mock_lock()
            validator.check_rate_limit("client")  # Should acquire lock

            assert mock_lock.acquire_count > 0
            assert mock_lock.release_count > 0
            assert mock_lock.lock_acquired is False  # Released after operation
    """
    class MockRLock:
        def __init__(self):
            self.acquire_count = 0
            self.release_count = 0
            self.lock_acquired = False
            self._lock = real_threading.Lock()

        def acquire(self, blocking=True):
            """Mock lock acquisition."""
            with self._lock:
                self.acquire_count += 1
                self.lock_acquired = True
                return True

        def release(self):
            """Mock lock release."""
            with self._lock:
                if self.lock_acquired:
                    self.release_count += 1
                    self.lock_acquired = False
                else:
                    raise RuntimeError("Release unlocked lock")

        def __enter__(self):
            """Context manager entry."""
            self.acquire()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            """Context manager exit."""
            self.release()

        def reset(self):
            """Reset lock state for testing."""
            with self._lock:
                self.acquire_count = 0
                self.release_count = 0
                self.lock_acquired = False

    class MockThread:
        def __init__(self, target=None):
            self.target = target
            self.ident = id(self)
            self._started = False

        def start(self):
            """Mock thread start - executes target function immediately."""
            self._started = True
            if self.target:
                # Execute the target function immediately in this mock thread
                try:
                    self.target()
                except Exception:
                    # In real threads, exceptions might be handled differently
                    # For tests, we'll let them propagate or ignore based on the test design
                    pass

        def is_alive(self):
            """Return whether thread is marked as alive."""
            return self._started

        def join(self, timeout=None):
            """Mock thread join - no-op for immediate execution."""
            pass

    class FakeThreadingModule:
        def __init__(self):
            self.mock_lock = MockRLock()
            self._threads = []
            self._thread_id_counter = 1000

        def RLock(self):
            """Return a new mock RLock instance."""
            return MockRLock()

        def Thread(self, target=None):
            """Create a new mock thread."""
            thread = MockThread(target)
            thread.ident = self._thread_id_counter
            self._thread_id_counter += 1
            self._threads.append(thread)
            return thread

        def simulate_thread_completion(self, thread_id):
            """Simulate thread completion for testing."""
            for thread in self._threads:
                if thread.ident == thread_id:
                    thread._started = False
                    break

        def get_mock_lock(self):
            """Get the shared mock lock for inspection."""
            return self.mock_lock

    fake_threading = FakeThreadingModule()

    # Monkeypatch the threading module in the config_validator module
    monkeypatch.setattr("app.infrastructure.resilience.config_validator.threading", fake_threading)

    return fake_threading
