"""
Orchestrator module test fixtures providing external dependency isolation.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the orchestrator component from systems outside its boundary.

External Dependencies Handled:
    - tenacity: Third-party retry library (mocked)
    - app.core.exceptions: Core AI service exceptions (mocked)
"""

import pytest
from unittest.mock import Mock, MagicMock, create_autospec
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Enum for retry strategy types used in test scenarios."""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    CRITICAL = "critical"


class CircuitState(Enum):
    """Enum for circuit breaker states used in test scenarios."""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@pytest.fixture
def mock_tenacity_library():
    """
    Mock for the tenacity retry library.

    Provides a comprehensive mock that simulates tenacity's retry functionality
    including retry states, stop conditions, wait strategies, and retry callbacks.
    This isolates orchestrator tests from the actual tenacity library while
    maintaining realistic retry behavior patterns.

    Default Behavior:
        - Mocked Retrying class with configurable stop and wait conditions
        - Mocked retry_if_exception_type and retry_if_exception_callable predicates
        - Mocked wait_exponential and wait_fixed strategies
        - Mocked retry callback mechanism
        - Realistic method signatures matching tenacity library

    Configuration Methods:
        configure_retry_strategy(strategy_name): Set up predefined retry configurations
        add_retry_exception(exception_type): Mark exception type for retry
        set_max_attempts(attempts): Configure maximum retry attempts
        set_wait_strategy(strategy_type, *args): Configure wait behavior

    Use Cases:
        - Testing orchestrator retry policy enforcement
        - Testing different retry strategies for various failure scenarios
        - Testing retry callback execution and logging
        - Testing integration with tenacity patterns without actual library

    Test Customization:
        def test_orchestrator_retry_policy(mock_tenacity_library):
            # Configure aggressive retry strategy
            mock_tenacity_library.configure_retry_strategy("aggressive")
            mock_tenacity_library.add_retry_exception(ConnectionError)

    Example:
        def test_orchestrator_with_tenacity_integration(mock_tenacity_library, monkeypatch):
            from app.infrastructure.resilience.orchestrator import ResilienceOrchestrator

            # Replace tenacity with our mock
            monkeypatch.setattr('app.infrastructure.resilience.orchestrator.tenacity', mock_tenacity_library)

            # Configure retry behavior for test scenario
            mock_tenacity_library.configure_retry_strategy("balanced")
            mock_tenacity_library.add_retry_exception(TimeoutError)

            # Test orchestrator retry enforcement
            orchestrator = ResilienceOrchestrator()
            result = orchestrator.execute_with_resilience(failing_operation)

            # Verify tenacity retry was configured
            mock_tenacity_library.Retrying.assert_called_once()

    Default Retry Strategies:
        - aggressive: 5 attempts, exponential backoff, many retryable exceptions
        - balanced: 3 attempts, exponential backoff, standard retryable exceptions
        - conservative: 2 attempts, fixed backoff, minimal retryable exceptions
        - critical: 7 attempts, exponential backoff, all possible retryable exceptions

    Note:
        This is a proper system boundary mock - tenacity is an external
        third-party dependency and should be mocked to isolate our orchestrator
        implementation from library-specific behavior.
    """
    # Create mock tenacity module structure
    mock_module = MagicMock()

    # Mock Retrying class
    mock_retrying_class = create_autospec(object, instance=False)
    mock_retrying_class.__name__ = "Retrying"
    mock_module.Retrying = mock_retrying_class

    # Mock retry decorators
    mock_module.retry = Mock()
    mock_module.stop_after_attempt = Mock()
    mock_module.wait_exponential = Mock()
    mock_module.wait_fixed = Mock()
    mock_module.retry_if_exception_type = Mock()
    mock_module.retry_if_exception_callable = Mock()

    # Mock retry state and callback
    mock_module.RetryCallState = Mock()
    mock_module.retry = Mock()

    # Configuration storage
    retry_config = {
        "max_attempts": 3,
        "wait_strategy": "exponential",
        "retryable_exceptions": [ConnectionError, TimeoutError],
        "stop_condition": "max_attempts"
    }

    def configure_retry_strategy(strategy_name: str):
        """Configure predefined retry strategies."""
        strategies = {
            "aggressive": {
                "max_attempts": 5,
                "wait_strategy": "exponential",
                "retryable_exceptions": [ConnectionError, TimeoutError, OSError],
                "stop_condition": "max_attempts"
            },
            "balanced": {
                "max_attempts": 3,
                "wait_strategy": "exponential",
                "retryable_exceptions": [ConnectionError, TimeoutError],
                "stop_condition": "max_attempts"
            },
            "conservative": {
                "max_attempts": 2,
                "wait_strategy": "fixed",
                "retryable_exceptions": [ConnectionError],
                "stop_condition": "max_attempts"
            },
            "critical": {
                "max_attempts": 7,
                "wait_strategy": "exponential",
                "retryable_exceptions": [ConnectionError, TimeoutError, OSError, Exception],
                "stop_condition": "max_attempts"
            }
        }

        if strategy_name in strategies:
            retry_config.update(strategies[strategy_name])

    def add_retry_exception(exception_type):
        """Add exception type to retryable exceptions list."""
        if exception_type not in retry_config["retryable_exceptions"]:
            retry_config["retryable_exceptions"].append(exception_type)

    def set_max_attempts(attempts: int):
        """Set maximum retry attempts."""
        retry_config["max_attempts"] = attempts

    def create_mock_retry_instance():
        """Create a configured mock retry instance."""
        mock_instance = MagicMock()
        mock_instance.__iter__ = Mock(return_value=iter([None]))  # Make it iterable
        return mock_instance

    # Configure mock behaviors
    mock_retrying_class.side_effect = create_mock_retry_instance

    # Add configuration methods to mock module
    mock_module.configure_retry_strategy = configure_retry_strategy
    mock_module.add_retry_exception = add_retry_exception
    mock_module.set_max_attempts = set_max_attempts
    mock_module.retry_config = retry_config

    # Default strategy
    configure_retry_strategy("balanced")

    return mock_module


@pytest.fixture
def mock_core_exceptions():
    """
    Mock for app.core.exceptions module.

    Provides a comprehensive mock that simulates the core AI service exceptions
    used by the orchestrator for resilience decision making. This isolates
    orchestrator tests from the actual exception classification system while
    maintaining realistic exception behavior patterns.

    Default Behavior:
        - Mocked exception classes with realistic inheritance hierarchy
        - Configurable exception creation and behavior
        - Mocked exception classification functions
        - Realistic exception signatures and attributes

    Exception Classes:
        - AIServiceError: Base class for all AI service exceptions
        - AIServiceTimeoutError: Timeout-related AI service failures
        - AIServiceConnectionError: Connection-related AI service failures
        - AIServiceRateLimitError: Rate limiting exceptions
        - AIServiceAuthenticationError: Authentication/authorization failures
        - AIServiceValidationError: Input validation failures
        - AIServiceInfrastructureError: Infrastructure-related failures

    Configuration Methods:
        create_exception(exception_type, message): Create exception instance
        set_exception_severity(exception_type, severity): Configure severity level
        add_exception_metadata(exception_type, metadata): Add exception context

    Use Cases:
        - Testing orchestrator exception handling and routing
        - Testing resilience policies based on exception types
        - Testing exception classification and escalation logic
        - Testing error recovery and fallback mechanisms

    Test Customization:
        def test_orchestrator_exception_handling(mock_core_exceptions):
            # Create custom exception for test scenario
            custom_error = mock_core_exceptions.create_exception(
                "AIServiceTimeoutError",
                "Model inference timeout"
            )

    Example:
        def test_orchestrator_resilience_policies(mock_core_exceptions, monkeypatch):
            from app.infrastructure.resilience.orchestrator import ResilienceOrchestrator

            # Replace core exceptions with our mock
            monkeypatch.setattr('app.infrastructure.resilience.orchestrator.core_exceptions', mock_core_exceptions)

            # Configure exception severity for testing
            mock_core_exceptions.set_exception_severity("AIServiceTimeoutError", "high")
            mock_core_exceptions.set_exception_severity("AIServiceConnectionError", "critical")

            # Test orchestrator exception handling
            orchestrator = ResilienceOrchestrator()

            # Simulate different exception scenarios
            timeout_error = mock_core_exceptions.create_exception(
                "AIServiceTimeoutError", "Inference timeout"
            )
            result = orchestrator.handle_ai_exception(timeout_error)

            # Verify appropriate resilience action was taken
            assert result.action == "retry_with_backoff"

    Default Exception Hierarchy:
        AIServiceError (base)
        ├── AIServiceTimeoutError
        ├── AIServiceConnectionError
        ├── AIServiceRateLimitError
        ├── AIServiceAuthenticationError
        ├── AIServiceValidationError
        └── AIServiceInfrastructureError

    Note:
        This is a proper system boundary mock - app.core.exceptions is
        defined outside the resilience module and should be mocked to isolate
        orchestrator logic from the core exception classification implementation.
    """
    # Create mock exception classes
    class MockAIServiceError(Exception):
        def __init__(self, message: str, severity: str = "medium", metadata: Dict = None):
            super().__init__(message)
            self.message = message
            self.severity = severity
            self.metadata = metadata or {}
            self.error_code = self.__class__.__name__

    class MockAIServiceTimeoutError(MockAIServiceError):
        pass

    class MockAIServiceConnectionError(MockAIServiceError):
        pass

    class MockAIServiceRateLimitError(MockAIServiceError):
        def __init__(self, message: str, retry_after: int = None, **kwargs):
            super().__init__(message, **kwargs)
            self.retry_after = retry_after

    class MockAIServiceAuthenticationError(MockAIServiceError):
        pass

    class MockAIServiceValidationError(MockAIServiceError):
        def __init__(self, message: str, field: str = None, **kwargs):
            super().__init__(message, **kwargs)
            self.field = field

    class MockAIServiceInfrastructureError(MockAIServiceError):
        pass

    # Create mock module structure
    mock_module = MagicMock()
    mock_module.AIServiceError = MockAIServiceError
    mock_module.AIServiceTimeoutError = MockAIServiceTimeoutError
    mock_module.AIServiceConnectionError = MockAIServiceConnectionError
    mock_module.AIServiceRateLimitError = MockAIServiceRateLimitError
    mock_module.AIServiceAuthenticationError = MockAIServiceAuthenticationError
    mock_module.AIServiceValidationError = MockAIServiceValidationError
    mock_module.AIServiceInfrastructureError = MockAIServiceInfrastructureError

    # Exception configuration storage
    exception_config = {
        "AIServiceTimeoutError": {"severity": "high", "retryable": True},
        "AIServiceConnectionError": {"severity": "critical", "retryable": True},
        "AIServiceRateLimitError": {"severity": "medium", "retryable": True},
        "AIServiceAuthenticationError": {"severity": "high", "retryable": False},
        "AIServiceValidationError": {"severity": "low", "retryable": False},
        "AIServiceInfrastructureError": {"severity": "high", "retryable": True}
    }

    def create_exception(exception_type: str, message: str, **kwargs):
        """Create exception instance with configured behavior."""
        exception_classes = {
            "AIServiceError": MockAIServiceError,
            "AIServiceTimeoutError": MockAIServiceTimeoutError,
            "AIServiceConnectionError": MockAIServiceConnectionError,
            "AIServiceRateLimitError": MockAIServiceRateLimitError,
            "AIServiceAuthenticationError": MockAIServiceAuthenticationError,
            "AIServiceValidationError": MockAIServiceValidationError,
            "AIServiceInfrastructureError": MockAIServiceInfrastructureError
        }

        if exception_type not in exception_classes:
            raise ValueError(f"Unknown exception type: {exception_type}")

        # Apply configured severity
        config = exception_config.get(exception_type, {})
        kwargs.setdefault("severity", config.get("severity", "medium"))

        return exception_classes[exception_type](message, **kwargs)

    def set_exception_severity(exception_type: str, severity: str):
        """Configure severity level for exception type."""
        if exception_type in exception_config:
            exception_config[exception_type]["severity"] = severity

    def add_exception_metadata(exception_type: str, metadata: Dict):
        """Add metadata configuration for exception type."""
        if exception_type in exception_config:
            exception_config[exception_type]["metadata"] = metadata

    def is_retryable(exception_type: str) -> bool:
        """Check if exception type is configured as retryable."""
        return exception_config.get(exception_type, {}).get("retryable", False)

    # Add configuration methods to mock module
    mock_module.create_exception = create_exception
    mock_module.set_exception_severity = set_exception_severity
    mock_module.add_exception_metadata = add_exception_metadata
    mock_module.is_retryable = is_retryable
    mock_module.exception_config = exception_config

    return mock_module


@pytest.fixture
def orchestrator_test_scenarios():
    """
    Standardized test scenarios for orchestrator behavior testing.

    Provides comprehensive test scenarios covering various resilience patterns,
    failure combinations, and recovery strategies. Ensures thorough testing
    of orchestrator functionality across different operational conditions.

    Data Structure:
        - failure_scenarios: Common failure patterns and exception combinations
        - resilience_strategies: Different resilience policy configurations
        - recovery_patterns: Recovery and fallback mechanism scenarios
        - performance_scenarios: Performance-related orchestration scenarios
        - edge_cases: Boundary conditions and special situations

    Use Cases:
        - Standardizing orchestrator test inputs across test modules
        - Providing comprehensive failure scenario coverage
        - Testing different resilience strategy combinations
        - Reducing test code duplication while ensuring thorough coverage

    Example:
        def test_orchestrator_with_various_scenarios(orchestrator_test_scenarios):
            for scenario in orchestrator_test_scenarios['failure_scenarios']:
                # Test orchestrator response to each failure pattern
                result = orchestrator.handle_failure(scenario['exception'])
                assert result.resilience_action == scenario['expected_action']
    """
    return {
        "failure_scenarios": [
            {
                "name": "ai_service_timeout",
                "exception_type": "AIServiceTimeoutError",
                "message": "Model inference timeout after 30 seconds",
                "severity": "high",
                "retryable": True,
                "expected_action": "retry_with_backoff",
                "expected_circuit_state": "unchanged",
                "description": "AI service timeout should trigger retry with exponential backoff"
            },
            {
                "name": "ai_service_connection_error",
                "exception_type": "AIServiceConnectionError",
                "message": "Failed to connect to AI service",
                "severity": "critical",
                "retryable": True,
                "expected_action": "retry_with_circuit_breaker",
                "expected_circuit_state": "potential_open",
                "description": "Connection errors should trigger retry with circuit breaker monitoring"
            },
            {
                "name": "ai_service_rate_limit",
                "exception_type": "AIServiceRateLimitError",
                "message": "Rate limit exceeded",
                "severity": "medium",
                "retryable": True,
                "expected_action": "retry_with_respect_rate_limit",
                "expected_circuit_state": "unchanged",
                "description": "Rate limit errors should trigger retry with rate limit respect"
            },
            {
                "name": "ai_service_auth_error",
                "exception_type": "AIServiceAuthenticationError",
                "message": "Invalid API credentials",
                "severity": "high",
                "retryable": False,
                "expected_action": "fail_fast",
                "expected_circuit_state": "unchanged",
                "description": "Authentication errors should fail fast without retry"
            },
            {
                "name": "ai_service_validation_error",
                "exception_type": "AIServiceValidationError",
                "message": "Invalid input parameters",
                "severity": "low",
                "retryable": False,
                "expected_action": "fail_fast",
                "expected_circuit_state": "unchanged",
                "description": "Validation errors should fail fast without retry"
            },
            {
                "name": "infrastructure_error",
                "exception_type": "AIServiceInfrastructureError",
                "message": "Internal service error",
                "severity": "high",
                "retryable": True,
                "expected_action": "retry_with_circuit_breaker",
                "expected_circuit_state": "potential_open",
                "description": "Infrastructure errors should trigger retry with circuit breaker"
            }
        ],
        "resilience_strategies": [
            {
                "name": "conservative_strategy",
                "retry_attempts": 2,
                "circuit_threshold": 3,
                "timeout_duration": 30,
                "backoff_multiplier": 1.5,
                "description": "Minimal retries for expensive operations"
            },
            {
                "name": "balanced_strategy",
                "retry_attempts": 3,
                "circuit_threshold": 5,
                "timeout_duration": 60,
                "backoff_multiplier": 2.0,
                "description": "Standard configuration for general use"
            },
            {
                "name": "aggressive_strategy",
                "retry_attempts": 5,
                "circuit_threshold": 8,
                "timeout_duration": 120,
                "backoff_multiplier": 2.5,
                "description": "Maximum resilience for critical operations"
            },
            {
                "name": "realtime_strategy",
                "retry_attempts": 1,
                "circuit_threshold": 2,
                "timeout_duration": 10,
                "backoff_multiplier": 1.0,
                "description": "Fast fail for real-time requirements"
            }
        ],
        "recovery_patterns": [
            {
                "name": "immediate_recovery",
                "failure_duration": 1,
                "expected_recovery": "immediate",
                "circuit_state": "HALF_OPEN",
                "description": "Quick recovery from transient failures"
            },
            {
                "name": "gradual_recovery",
                "failure_duration": 30,
                "expected_recovery": "gradual",
                "circuit_state": "HALF_OPEN",
                "description": "Gradual recovery from sustained issues"
            },
            {
                "name": "full_recovery",
                "failure_duration": 300,
                "expected_recovery": "full_test",
                "circuit_state": "CLOSED",
                "description": "Complete recovery after major outage"
            }
        ],
        "performance_scenarios": [
            {
                "name": "high_load_normal",
                "request_rate": 100,
                "error_rate": 0.01,
                "expected_response_time": 2.0,
                "description": "High load with normal error rates"
            },
            {
                "name": "high_load_degraded",
                "request_rate": 100,
                "error_rate": 0.15,
                "expected_response_time": 5.0,
                "description": "High load with degraded performance"
            },
            {
                "name": "low_load_stable",
                "request_rate": 10,
                "error_rate": 0.001,
                "expected_response_time": 1.0,
                "description": "Low load with stable performance"
            }
        ],
        "edge_cases": [
            {
                "name": "concurrent_failures",
                "failure_count": 10,
                "failure_types": ["timeout", "connection", "rate_limit"],
                "expected_behavior": "circuit_opens_gracefully",
                "description": "Multiple concurrent failures should open circuit gracefully"
            },
            {
                "name": "cascade_failure",
                "initial_failure": "service_down",
                "propagation_pattern": "circuit_breaker_trigger",
                "expected_behavior": "prevent_cascade",
                "description": "Circuit breaker should prevent cascade failures"
            },
            {
                "name": "recovery_timeout",
                "failure_duration": 600,
                "recovery_attempt": "after_timeout",
                "expected_behavior": "respect_recovery_timeout",
                "description": "Should respect configured recovery timeouts"
            }
        ]
    }


@pytest.fixture
def mock_resilience_components():
    """
    Mock resilience components for orchestrator integration testing.

    Provides mock instances of circuit breaker, retry, and cache components
    that the orchestrator coordinates. This enables testing of orchestration
    logic without requiring actual implementations of the individual components.

    Mock Components:
        - MockCircuitBreaker: Simulates circuit breaker state transitions
        - MockRetryHandler: Simulates retry policy enforcement
        - MockCacheService: Simulates caching behavior
        - MockMetricsCollector: Simulates metrics and monitoring

    Use Cases:
        - Testing orchestrator component coordination
        - Testing resilience policy composition
        - Testing component state synchronization
        - Testing fallback and recovery orchestration

    Example:
        def test_orchestrator_component_coordination(mock_resilience_components):
            orchestrator = ResilienceOrchestrator(components=mock_resilience_components)

            # Simulate failure scenario
            result = orchestrator.handle_request(failing_request)

            # Verify components were coordinated correctly
            mock_resilience_components.circuit_breaker.record_failure.assert_called()
            mock_resilience_components.retry.attempt_retry.assert_called()
    """
    # Mock circuit breaker component
    mock_circuit_breaker = MagicMock()
    mock_circuit_breaker.state = "CLOSED"
    mock_circuit_breaker.failure_count = 0
    mock_circuit_breaker.call = Mock(return_value="success")
    mock_circuit_breaker.record_failure = Mock()
    mock_circuit_breaker.record_success = Mock()
    mock_circuit_breaker.force_open = Mock()
    mock_circuit_breaker.force_close = Mock()

    # Mock retry handler component
    mock_retry_handler = MagicMock()
    mock_retry_handler.should_retry = Mock(return_value=True)
    mock_retry_handler.execute_with_retry = Mock(return_value="retry_success")
    mock_retry_handler.get_retry_count = Mock(return_value=2)
    mock_retry_handler.reset_retry_count = Mock()

    # Mock cache service component
    mock_cache_service = MagicMock()
    mock_cache_service.get = Mock(return_value=None)
    mock_cache_service.set = Mock(return_value=True)
    mock_cache_service.delete = Mock(return_value=True)
    mock_cache_service.is_available = Mock(return_value=True)

    # Mock metrics collector component
    mock_metrics_collector = MagicMock()
    mock_metrics_collector.record_request = Mock()
    mock_metrics_collector.record_success = Mock()
    mock_metrics_collector.record_failure = Mock()
    mock_metrics_collector.record_retry = Mock()
    mock_metrics_collector.record_circuit_breaker_state = Mock()
    mock_metrics_collector.get_metrics = Mock(return_value={
        "success_rate": 0.95,
        "error_rate": 0.05,
        "avg_response_time": 1.2
    })

    return {
        "circuit_breaker": mock_circuit_breaker,
        "retry_handler": mock_retry_handler,
        "cache_service": mock_cache_service,
        "metrics_collector": mock_metrics_collector
    }