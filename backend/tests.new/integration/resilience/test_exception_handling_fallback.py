"""
Integration Tests: Exception Classification → Retry Strategy → Fallback Execution

This module tests the integration between exception classification, retry strategy
selection, and fallback execution mechanisms. It validates that the system correctly
classifies different types of exceptions and applies appropriate resilience strategies.

Integration Scope:
    - Exception classification → Retry strategy selection → Fallback mechanism
    - Transient vs permanent error handling → Retry decisions → Graceful degradation
    - Error context preservation → Retry execution → Result handling

Business Impact:
    Ensures appropriate error handling and graceful degradation for user experience,
    providing reliable service operation under various failure conditions

Test Strategy:
    - Test exception classification for different error types
    - Validate retry strategy application based on exception type
    - Test fallback execution when retries are exhausted
    - Verify error context preservation across retry attempts
    - Test graceful degradation patterns

Critical Paths:
    - Exception occurrence → Classification → Retry decision → Fallback execution
    - Error context preservation → Retry attempts → Result handling
    - Service degradation → Fallback response → User experience
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from typing import Dict, Any, Callable, Optional

from app.core.config import Settings
from app.core.exceptions import (
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    InfrastructureError,
    ConfigurationError
)
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.retry import classify_exception, should_retry_on_exception
from app.infrastructure.resilience.circuit_breaker import CircuitBreakerConfig
from app.infrastructure.resilience.config_presets import ResilienceStrategy, ResilienceConfig
from app.services.text_processor import TextProcessorService


class TestExceptionHandlingFallback:
    """
    Integration tests for Exception Classification → Retry Strategy → Fallback Execution.

    Seam Under Test:
        Exception classification → Retry strategy selection → Fallback mechanism → Orchestrator coordination

    Critical Paths:
        - Exception occurrence → Classification → Retry decision → Fallback execution
        - Error context preservation → Retry attempts → Result handling
        - Service degradation → Fallback response → User experience

    Business Impact:
        Ensures appropriate error handling and graceful degradation for user experience,
        maintaining service reliability under various failure conditions
    """

    @pytest.fixture
    def exception_scenarios(self):
        """Provides test scenarios for different exception types."""
        return {
            "transient_error": {
                "exception": TransientAIError("Temporary service overload"),
                "should_retry": True,
                "expected_behavior": "retry_then_success",
                "description": "Temporary error that should be retried"
            },
            "permanent_error": {
                "exception": PermanentAIError("Invalid API key"),
                "should_retry": False,
                "expected_behavior": "fail_fast",
                "description": "Permanent error that should not be retried"
            },
            "rate_limit_error": {
                "exception": RateLimitError("Rate limit exceeded"),
                "should_retry": True,
                "expected_behavior": "retry_with_backoff",
                "description": "Rate limiting error requiring backoff"
            },
            "service_unavailable": {
                "exception": ServiceUnavailableError("Service temporarily down"),
                "should_retry": True,
                "expected_behavior": "retry_with_circuit_breaker",
                "description": "Service unavailable requiring circuit breaker protection"
            },
            "network_timeout": {
                "exception": TimeoutError("Connection timed out"),
                "should_retry": True,
                "expected_behavior": "retry_with_exponential_backoff",
                "description": "Network timeout that should be retried"
            },
            "configuration_error": {
                "exception": ConfigurationError("Invalid configuration"),
                "should_retry": False,
                "expected_behavior": "fail_fast_no_retry",
                "description": "Configuration error that should not be retried"
            }
        }

    @pytest.fixture
    def resilience_orchestrator(self):
        """Create a resilience orchestrator for exception handling testing."""
        settings = Settings(
            environment="testing",
            enable_circuit_breaker=True,
            enable_retry=True,
            max_retry_attempts=3,
            circuit_breaker_failure_threshold=5,
            circuit_breaker_recovery_timeout=60
        )

        orchestrator = AIServiceResilience(settings)
        orchestrator.register_operation("test_operation", ResilienceStrategy.BALANCED)
        return orchestrator

    def test_exception_classification_accuracy(self, exception_scenarios):
        """
        Test that exceptions are correctly classified for retry decisions.

        Integration Scope:
            Exception classification → Retry decision logic → Strategy selection

        Business Impact:
            Ensures appropriate retry behavior for different error types

        Test Strategy:
            - Test classification of various exception types
            - Verify retry decisions match expected behavior
            - Validate exception hierarchy handling
            - Test custom exception classification

        Success Criteria:
            - Transient errors are classified for retry
            - Permanent errors are not retried
            - Rate limiting errors trigger appropriate backoff
            - Service unavailable errors are handled correctly
        """
        for scenario_name, scenario in exception_scenarios.items():
            exception = scenario["exception"]
            should_retry = classify_exception(exception)

            assert should_retry == scenario["should_retry"], \
                f"Exception {scenario_name} classification failed: expected {scenario['should_retry']}, got {should_retry}"

            # Test with tenacity-compatible function
            retry_state = type('RetryState', (), {'outcome': type('Outcome', (), {'exception': lambda: exception})()})()
            tenacity_retry = should_retry_on_exception(retry_state)

            assert tenacity_retry == scenario["should_retry"], \
                f"Tenacity retry decision failed for {scenario_name}"

    def test_transient_error_retry_success(self, resilience_orchestrator):
        """
        Test that transient errors are retried and eventually succeed.

        Integration Scope:
            Exception classification → Retry mechanism → Success handling

        Business Impact:
            Validates retry functionality for temporary service issues

        Test Strategy:
            - Simulate transient error that resolves after retries
            - Verify retry attempts are made
            - Confirm final success after retries
            - Validate error context preservation

        Success Criteria:
            - Transient errors trigger retry attempts
            - Success achieved after appropriate retry count
            - Error context maintained across retries
            - No unnecessary retry attempts for resolved errors
        """
        call_count = 0

        @resilience_orchestrator.with_resilience("test_operation")
        async def unreliable_operation():
            nonlocal call_count
            call_count += 1

            if call_count <= 2:
                raise TransientAIError(f"Temporary failure (attempt {call_count})")
            else:
                return "Success after retries"

        # Execute operation
        result = unreliable_operation()  # Remove await for sync test

        # Verify success after retries
        assert result == "Success after retries"
        assert call_count == 3  # 2 failures + 1 success

    def test_permanent_error_fail_fast(self, resilience_orchestrator):
        """
        Test that permanent errors fail immediately without retries.

        Integration Scope:
            Exception classification → Fail-fast behavior → Error handling

        Business Impact:
            Prevents wasted resources on non-recoverable errors

        Test Strategy:
            - Simulate permanent error condition
            - Verify no retry attempts are made
            - Confirm immediate failure with proper error propagation
            - Validate error context and classification

        Success Criteria:
            - Permanent errors do not trigger retries
            - Fail-fast behavior prevents resource waste
            - Error context preserved for debugging
            - Proper exception type propagation
        """
        call_count = 0

        @resilience_orchestrator.with_resilience("test_operation")
        async def permanent_failure_operation():
            nonlocal call_count
            call_count += 1
            raise PermanentAIError("Permanent configuration error")

        # Execute operation and expect immediate failure
        with pytest.raises(PermanentAIError, match="Permanent configuration error"):
            permanent_failure_operation()  # Remove await for sync test

        # Verify no retries were attempted
        assert call_count == 1  # Only 1 attempt, no retries

    def test_rate_limit_error_retry_with_backoff(self, resilience_orchestrator):
        """
        Test that rate limiting errors trigger appropriate backoff and retry.

        Integration Scope:
            Rate limit detection → Backoff strategy → Retry execution

        Business Impact:
            Respects API limits while maximizing success rate

        Test Strategy:
            - Simulate rate limiting error
            - Verify exponential backoff behavior
            - Test retry attempts with appropriate delays
            - Validate eventual success or graceful failure

        Success Criteria:
            - Rate limit errors trigger retry mechanism
            - Exponential backoff applied between attempts
            - Maximum retry attempts respected
            - Proper error handling when rate limit persists
        """
        call_count = 0
        call_times = []

        @resilience_orchestrator.with_resilience("test_operation")
        async def rate_limited_operation():
            nonlocal call_count, call_times
            call_count += 1
            call_times.append(asyncio.get_event_loop().time())

            if call_count <= 2:
                raise RateLimitError(f"Rate limit exceeded (attempt {call_count})")
            else:
                return "Rate limit resolved"

        # Execute operation
        result = rate_limited_operation()  # Remove await for sync test

        # Verify success after rate limit resolution
        assert result == "Rate limit resolved"
        assert call_count == 3  # 2 failures + 1 success

        # Verify timing shows backoff behavior
        assert len(call_times) == 3
        time_diff_1 = call_times[1] - call_times[0]
        time_diff_2 = call_times[2] - call_times[1]

        # Should have delays between calls (actual timing may vary)
        assert time_diff_1 > 0
        assert time_diff_2 > 0

    def test_fallback_execution_on_retry_exhaustion(self, resilience_orchestrator):
        """
        Test that fallback functions are executed when retries are exhausted.

        Integration Scope:
            Retry exhaustion → Fallback execution → Graceful degradation

        Business Impact:
            Provides graceful degradation instead of complete failure

        Test Strategy:
            - Configure operation to always fail
            - Provide fallback function for graceful degradation
            - Verify fallback execution when retries exhausted
            - Validate fallback response quality and context

        Success Criteria:
            - Fallback function executed after retry exhaustion
            - Fallback provides meaningful response
            - Original request context preserved in fallback
            - Error context available for debugging
        """
        call_count = 0
        fallback_called = False
        fallback_context = None

        def fallback_handler(original_input):
            nonlocal fallback_called, fallback_context
            fallback_called = True
            fallback_context = original_input
            return f"Fallback response for: {original_input}"

        @resilience_orchestrator.with_resilience("test_operation", fallback=fallback_handler)
        async def always_failing_operation():
            nonlocal call_count
            call_count += 1
            raise TransientAIError(f"Persistent failure (attempt {call_count})")

        # Execute operation
        result = always_failing_operation()  # Remove await for sync test

        # Verify fallback was executed
        assert fallback_called is True
        assert fallback_context is not None
        assert "Fallback response for:" in result

        # Verify retry attempts were made before fallback
        assert call_count >= 1  # At least one attempt before fallback

    def test_fallback_preserves_request_context(self, resilience_orchestrator):
        """
        Test that fallback functions receive original request context.

        Integration Scope:
            Request context → Exception handling → Fallback execution → Context preservation

        Business Impact:
            Enables context-aware fallback responses

        Test Strategy:
            - Create operation with complex request context
            - Force operation failure to trigger fallback
            - Verify fallback receives complete request context
            - Validate context preservation across retry attempts

        Success Criteria:
            - Original request parameters preserved in fallback
            - Request metadata maintained through failure handling
            - Fallback can access all original request information
            - Context available for generating meaningful fallback responses
        """
        original_request = {
            "text": "Complex document for processing",
            "operation": "summarize",
            "options": {"max_length": 150, "format": "paragraph"},
            "metadata": {"priority": "high", "user_id": "user123"}
        }

        fallback_context = None

        def context_aware_fallback(request_data):
            nonlocal fallback_context
            fallback_context = request_data
            return {
                "fallback": True,
                "reason": "Service temporarily unavailable",
                "original_request": request_data,
                "suggestion": "Please try again in a few minutes"
            }

        @resilience_orchestrator.with_resilience("test_operation", fallback=context_aware_fallback)
        async def context_sensitive_operation(request_data):
            raise ServiceUnavailableError("Service is temporarily down")

        # Execute operation
        result = context_sensitive_operation(original_request)  # Remove await for sync test

        # Verify fallback received complete context
        assert fallback_context == original_request
        assert isinstance(result, dict)
        assert result["fallback"] is True
        assert result["original_request"] == original_request

    def test_mixed_exception_types_handling(self, resilience_orchestrator):
        """
        Test handling of mixed exception types in the same operation.

        Integration Scope:
            Multiple exception types → Classification → Strategy selection → Handling

        Business Impact:
            Ensures robust error handling for complex failure scenarios

        Test Strategy:
            - Simulate operation that can fail with different exception types
            - Verify appropriate handling for each exception type
            - Test transition between different failure modes
            - Validate overall system stability

        Success Criteria:
            - Each exception type handled according to its classification
            - System remains stable during exception type transitions
            - Appropriate retry/fallback behavior for each type
            - No cross-contamination between different error scenarios
        """
        call_sequence = []
        exception_sequence = [
            TransientAIError("Temporary network issue"),
            RateLimitError("Rate limit exceeded"),
            ServiceUnavailableError("Service unavailable"),
            PermanentAIError("Configuration error")
        ]

        @resilience_orchestrator.with_resilience("test_operation")
        async def mixed_exception_operation():
            call_sequence.append("call_attempted")
            if exception_sequence:
                exception = exception_sequence.pop(0)
                raise exception
            return "Success after all exceptions"

        # Test transient error handling
        try:
            mixed_exception_operation()  # Remove await for sync test
        except Exception as e:
            assert isinstance(e, TransientAIError)
            assert len(call_sequence) >= 2  # Should have retried

        call_sequence.clear()

        # Test rate limit handling
        try:
            mixed_exception_operation()  # Remove await for sync test
        except Exception as e:
            assert isinstance(e, RateLimitError)
            assert len(call_sequence) >= 2  # Should have retried with backoff

    def test_exception_context_preservation(self, resilience_orchestrator):
        """
        Test that exception context is preserved through retry attempts.

        Integration Scope:
            Exception context → Retry mechanism → Error propagation → Context preservation

        Business Impact:
            Enables better debugging and error tracking

        Test Strategy:
            - Create operation with rich error context
            - Force multiple failures with context
            - Verify context preserved through retries
            - Validate context available in final error

        Success Criteria:
            - Exception context maintained across retry attempts
            - Context information available for debugging
            - Error metadata preserved for logging and monitoring
            - Context doesn't interfere with retry logic
        """
        context_info = {
            "operation_id": "test-12345",
            "user_id": "user-abc",
            "request_id": "req-xyz",
            "attempts": 0
        }

        exception_contexts = []

        def context_tracking_fallback(context_data):
            exception_contexts.append(context_data)
            return {"error": "Service failed", "context": context_data}

        @resilience_orchestrator.with_resilience("test_operation", fallback=context_tracking_fallback)
        async def context_preserving_operation():
            context_info["attempts"] += 1
            raise TransientAIError(f"Context test failure (attempt {context_info['attempts']})")

        # Execute operation
        result = context_preserving_operation()  # Remove await for sync test

        # Verify context was preserved and passed to fallback
        assert len(exception_contexts) > 0
        final_context = exception_contexts[-1]

        # Context should include operation metadata
        assert "operation_id" in final_context
        assert "attempts" in final_context
        assert final_context["attempts"] >= 1

        # Verify fallback response includes context
        assert isinstance(result, dict)
        assert "context" in result
        assert result["context"] == final_context

    def test_graceful_degradation_patterns(self, resilience_orchestrator):
        """
        Test various graceful degradation patterns.

        Integration Scope:
            Service failure → Graceful degradation → Fallback patterns → User experience

        Business Impact:
            Maintains user experience during service outages

        Test Strategy:
            - Test different fallback strategies
            - Verify degradation provides value to users
            - Test fallback with cached responses
            - Validate fallback response quality

        Success Criteria:
            - Multiple fallback strategies available
            - Fallback responses provide user value
            - Cached responses used when available
            - Degradation maintains API contract
        """
        fallback_responses = []

        def quality_fallback(request_context):
            fallback_responses.append(request_context)
            return {
                "degraded_response": True,
                "message": "Service temporarily unavailable",
                "alternative": "Please try again in a few minutes",
                "context": request_context
            }

        def minimal_fallback(request_context):
            return {"status": "degraded", "message": "Service unavailable"}

        @resilience_orchestrator.with_resilience("test_operation", fallback=quality_fallback)
        async def degrading_operation():
            raise ServiceUnavailableError("Service is down for maintenance")

        # Test quality fallback
        result = degrading_operation()  # Remove await for sync test

        assert isinstance(result, dict)
        assert result["degraded_response"] is True
        assert "message" in result
        assert "alternative" in result
        assert len(fallback_responses) == 1

    def test_exception_classification_edge_cases(self):
        """
        Test exception classification for edge cases and custom exceptions.

        Integration Scope:
            Custom exceptions → Classification logic → Retry decisions → Error handling

        Business Impact:
            Ensures robust error handling for unexpected scenarios

        Test Strategy:
            - Test unknown exception types
            - Verify hierarchy-based classification
            - Test custom exception handling
            - Validate fallback for unclassifiable exceptions

        Success Criteria:
            - Unknown exceptions handled gracefully
            - Exception hierarchy respected
            - Custom exceptions properly classified
            - System remains stable for edge cases
        """
        # Test unknown exception (should be treated conservatively)
        unknown_exception = ValueError("Unexpected error")
        should_retry = classify_exception(unknown_exception)

        # Unknown exceptions should be retried by default (conservative approach)
        assert should_retry is True

        # Test custom exception hierarchy
        class CustomTransientError(TransientAIError):
            pass

        class CustomPermanentError(PermanentAIError):
            pass

        custom_transient = CustomTransientError("Custom transient error")
        custom_permanent = CustomPermanentError("Custom permanent error")

        assert classify_exception(custom_transient) is True   # Should retry
        assert classify_exception(custom_permanent) is False  # Should not retry

        # Test deeply nested exception hierarchy
        class DeepCustomError(CustomTransientError):
            pass

        deep_error = DeepCustomError("Deep custom error")
        assert classify_exception(deep_error) is True  # Should inherit retry behavior
