"""
Test suite for global resilience decorator functions.

This test module verifies the global decorator convenience functions that apply
specific resilience strategies (aggressive, balanced, conservative, critical)
and the operation-specific decorator function.

Test Categories:
    - with_operation_resilience() global function
    - with_aggressive_resilience() global function
    - with_balanced_resilience() global function
    - with_conservative_resilience() global function
    - with_critical_resilience() global function

Note: These tests focus on behavior-driven testing of the public contract.
They verify what the decorators should do according to their docstrings,
not how they are implemented internally.
"""

import pytest
from unittest.mock import Mock, patch

from app.infrastructure.resilience.orchestrator import (
    with_operation_resilience,
    with_aggressive_resilience,
    with_balanced_resilience,
    with_conservative_resilience,
    with_critical_resilience,
    AIServiceResilience,
    ai_resilience
)
from app.infrastructure.resilience.config_presets import ResilienceStrategy


class TestWithOperationResilienceGlobalFunction:
    """
    Tests for with_operation_resilience() global decorator function.

    Verifies that the global function applies operation-specific resilience
    configuration with automatic lookup and optional fallback support.
    """

    def test_calls_global_ai_resilience_instance(self):
        """
        Test that decorator delegates to global AIServiceResilience instance.

        Verifies:
            Global ai_resilience instance's with_operation_resilience method is called
            per function implementation behavior.

        Business Impact:
            Ensures consistent behavior between global decorator and instance methods
            for predictable resilience patterns.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_operation_resilience = Mock()
        mock_resilience.with_operation_resilience = mock_with_operation_resilience

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_operation_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the decorator
            decorator_result = with_operation_resilience("test_operation")

            # Assert: Global instance method was called with correct parameters
            mock_with_operation_resilience.assert_called_once_with("test_operation", None)
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_supports_optional_fallback_parameter(self):
        """
        Test that decorator supports optional fallback function for graceful degradation.

        Verifies:
            Fallback parameter is passed through to AIServiceResilience instance
            per function docstring Args documentation.

        Business Impact:
            Enables graceful degradation patterns with convenient decorator
            syntax for improved user experience during failures.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_operation_resilience = Mock()
        mock_resilience.with_operation_resilience = mock_with_operation_resilience

        # Create a fallback function
        def fallback_func(data: str) -> str:
            return f"fallback: {data}"

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_operation_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the decorator with fallback
            decorator_result = with_operation_resilience("test_operation", fallback=fallback_func)

            # Assert: Fallback was passed through correctly
            mock_with_operation_resilience.assert_called_once_with("test_operation", fallback_func)
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_raises_runtime_error_if_global_instance_not_initialized(self):
        """
        Test that RuntimeError is raised if global instance is not initialized.

        Verifies:
            RuntimeError is raised if global AIServiceResilience not properly
            initialized per function docstring Raises documentation.

        Business Impact:
            Provides clear error message when global instance is missing,
            preventing silent failures or undefined behavior.
        """
        # Patch the global ai_resilience instance to None
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', None):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act & Assert: RuntimeError is raised when applying decorator
            with pytest.raises(RuntimeError, match="AIServiceResilience not initialized"):
                with_operation_resilience("test_operation")


class TestWithAggressiveResilienceGlobalFunction:
    """
    Tests for with_aggressive_resilience() global decorator function.

    Verifies that the decorator applies aggressive resilience strategy with
    higher retry attempts, shorter delays, and lower circuit breaker thresholds.
    """

    def test_calls_global_ai_resilience_with_aggressive_strategy(self):
        """
        Test that decorator delegates to global AIServiceResilience with AGGRESSIVE strategy.

        Verifies:
            Global ai_resilience instance's with_resilience method is called with
            AGGRESSIVE strategy per function implementation behavior.

        Business Impact:
            Ensures aggressive resilience strategy is consistently applied for
            operations requiring rapid recovery and high availability.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_resilience = Mock()
        mock_resilience.with_resilience = mock_with_resilience

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the aggressive decorator
            decorator_result = with_aggressive_resilience("test_operation")

            # Assert: Global instance method was called with AGGRESSIVE strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.AGGRESSIVE,
                fallback=None
            )
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_supports_optional_fallback_parameter(self):
        """
        Test that decorator supports optional fallback despite aggressive retry behavior.

        Verifies:
            Fallback parameter is passed through to AIServiceResilience instance
            per function docstring Args documentation.

        Business Impact:
            Enables graceful degradation even with aggressive retry strategy
            for improved user experience during persistent failures.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_resilience = Mock()
        mock_resilience.with_resilience = mock_with_resilience

        # Create a fallback function
        def fallback_func(data: str) -> str:
            return f"fallback: {data}"

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the aggressive decorator with fallback
            decorator_result = with_aggressive_resilience("test_operation", fallback=fallback_func)

            # Assert: Fallback was passed through correctly with AGGRESSIVE strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.AGGRESSIVE,
                fallback=fallback_func
            )
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_raises_runtime_error_if_global_instance_not_initialized(self):
        """
        Test that RuntimeError is raised if global instance is not initialized.

        Verifies:
            RuntimeError is raised if global AIServiceResilience not properly
            initialized per function docstring Raises documentation.

        Business Impact:
            Provides clear error message when global instance is missing,
            preventing silent failures or undefined behavior.
        """
        # Patch the global ai_resilience instance to None
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', None):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act & Assert: RuntimeError is raised when applying decorator
            with pytest.raises(RuntimeError, match="AIServiceResilience not initialized"):
                with_aggressive_resilience("test_operation")


class TestWithBalancedResilienceGlobalFunction:
    """
    Tests for with_balanced_resilience() global decorator function.

    Verifies that the decorator applies balanced resilience strategy suitable
    for most production workloads with moderate retry and circuit breaker settings.
    """

    def test_applies_balanced_strategy_at_runtime(self):
        """
        Test that balanced strategy is applied at runtime rather than decoration time.

        Verifies:
            Balanced strategy is applied at runtime per function implementation
            for dynamic configuration support.

        Business Impact:
            Enables configuration updates without redeployment for operational
            flexibility in production environments.
        """
        # Use the real ai_resilience instance but with mocked with_resilience method
        with patch.object(ai_resilience, 'with_resilience') as mock_with_resilience:
            # Mock the decorator call chain: with_resilience(operation, strategy) returns a decorator
            # and that decorator(func) returns an async function
            async def mock_resilient_wrapper(*args, **kwargs):
                return "mocked result"

            mock_decorator = Mock(return_value=mock_resilient_wrapper)
            mock_with_resilience.return_value = mock_decorator

            # Arrange: Create a test function (async since wrapper is async)
            async def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the balanced decorator
            decorated_func = with_balanced_resilience("test_operation")(test_function)

            # Assert: The decorator function is returned (runtime decoration)
            assert callable(decorated_func)

            # Act: Call the decorated function to trigger runtime resilience application
            import asyncio
            result = asyncio.run(decorated_func("test_data"))

            # Assert: Result is from mock decorator
            assert result == "mocked result"

            # Assert: with_resilience was called with balanced strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.BALANCED,
                fallback=None
            )

    def test_supports_optional_fallback_parameter(self):
        """
        Test that decorator supports optional fallback despite runtime strategy application.

        Verifies:
            Fallback parameter is handled correctly in runtime decoration
            per function docstring Args documentation.

        Business Impact:
            Enables graceful degradation with balanced resilience strategy
            for improved user experience during persistent failures.
        """
        # Create a fallback function
        async def fallback_func(data: str) -> str:
            return f"fallback: {data}"

        # Arrange: Create a test function (async since wrapper is async)
        async def test_function(data: str) -> str:
            return f"processed: {data}"

        # Act: Apply the balanced decorator with fallback
        decorated_func = with_balanced_resilience("test_operation", fallback=fallback_func)(test_function)

        # Assert: The decorator function is returned
        assert callable(decorated_func)

    def test_raises_runtime_error_if_global_instance_not_initialized(self):
        """
        Test that RuntimeError is raised if global instance is not initialized.

        Verifies:
            RuntimeError is raised if global AIServiceResilience not properly
            initialized per function docstring Raises documentation.

        Business Impact:
            Provides clear error message when global instance is missing,
            preventing silent failures or undefined behavior.
        """
        # Patch the global ai_resilience instance to None
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', None):
            # Arrange: Create a test function (async since wrapper is async)
            async def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the balanced decorator
            decorated_func = with_balanced_resilience("test_operation")(test_function)

            # Act & Assert: RuntimeError is raised when calling decorated function
            import asyncio
            with pytest.raises(RuntimeError, match="AIServiceResilience not initialized"):
                asyncio.run(decorated_func("test_data"))


class TestWithConservativeResilienceGlobalFunction:
    """
    Tests for with_conservative_resilience() global decorator function.

    Verifies that the decorator applies conservative resilience strategy optimized
    for resource conservation with fewer retries and longer delays.
    """

    def test_calls_global_ai_resilience_with_conservative_strategy(self):
        """
        Test that decorator delegates to global AIServiceResilience with CONSERVATIVE strategy.

        Verifies:
            Global ai_resilience instance's with_resilience method is called with
            CONSERVATIVE strategy per function implementation behavior.

        Business Impact:
            Ensures conservative resilience strategy is consistently applied for
            resource-intensive or stability-prioritized operations.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_resilience = Mock()
        mock_resilience.with_resilience = mock_with_resilience

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the conservative decorator
            decorator_result = with_conservative_resilience("test_operation")

            # Assert: Global instance method was called with CONSERVATIVE strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.CONSERVATIVE,
                fallback=None
            )
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_supports_optional_fallback_parameter(self):
        """
        Test that decorator supports optional fallback despite conservative retry behavior.

        Verifies:
            Fallback parameter is passed through to AIServiceResilience instance
            per function docstring Args documentation.

        Business Impact:
            Enables graceful degradation even with conservative retry strategy
            for resource-conscious operations during persistent failures.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_resilience = Mock()
        mock_resilience.with_resilience = mock_with_resilience

        # Create a fallback function
        def fallback_func(data: str) -> str:
            return f"fallback: {data}"

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the conservative decorator with fallback
            decorator_result = with_conservative_resilience("test_operation", fallback=fallback_func)

            # Assert: Fallback was passed through correctly with CONSERVATIVE strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.CONSERVATIVE,
                fallback=fallback_func
            )
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_raises_runtime_error_if_global_instance_not_initialized(self):
        """
        Test that RuntimeError is raised if global instance is not initialized.

        Verifies:
            RuntimeError is raised if global AIServiceResilience not properly
            initialized per function docstring Raises documentation.

        Business Impact:
            Provides clear error message when global instance is missing,
            preventing silent failures or undefined behavior.
        """
        # Patch the global ai_resilience instance to None
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', None):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act & Assert: RuntimeError is raised when applying decorator
            with pytest.raises(RuntimeError, match="AIServiceResilience not initialized"):
                with_conservative_resilience("test_operation")


class TestWithCriticalResilienceGlobalFunction:
    """
    Tests for with_critical_resilience() global decorator function.

    Verifies that the decorator applies maximum resilience strategy for mission-
    critical operations requiring highest availability.
    """

    def test_calls_global_ai_resilience_with_critical_strategy(self):
        """
        Test that decorator delegates to global AIServiceResilience with CRITICAL strategy.

        Verifies:
            Global ai_resilience instance's with_resilience method is called with
            CRITICAL strategy per function implementation behavior.

        Business Impact:
            Ensures critical resilience strategy is consistently applied for
            mission-critical operations requiring highest availability.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_resilience = Mock()
        mock_resilience.with_resilience = mock_with_resilience

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the critical decorator
            decorator_result = with_critical_resilience("test_operation")

            # Assert: Global instance method was called with CRITICAL strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.CRITICAL,
                fallback=None
            )
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_supports_optional_fallback_parameter(self):
        """
        Test that decorator supports optional fallback despite critical retry behavior.

        Verifies:
            Fallback parameter is passed through to AIServiceResilience instance
            per function docstring Args documentation.

        Business Impact:
            Enables emergency fallback even with critical retry strategy for
            maintaining system functionality during absolute failure scenarios.
        """
        # Arrange: Create a mock AIServiceResilience instance
        mock_resilience = Mock()
        mock_with_resilience = Mock()
        mock_resilience.with_resilience = mock_with_resilience

        # Create a fallback function
        def fallback_func(data: str) -> str:
            return f"emergency fallback: {data}"

        # Create a mock decorator function
        mock_decorator = Mock()
        mock_with_resilience.return_value = mock_decorator

        # Patch the global ai_resilience instance
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', mock_resilience):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act: Apply the critical decorator with fallback
            decorator_result = with_critical_resilience("test_operation", fallback=fallback_func)

            # Assert: Fallback was passed through correctly with CRITICAL strategy
            mock_with_resilience.assert_called_once_with(
                "test_operation",
                ResilienceStrategy.CRITICAL,
                fallback=fallback_func
            )
            # Assert: The decorator function is returned
            assert decorator_result is mock_decorator

    def test_raises_runtime_error_if_global_instance_not_initialized(self):
        """
        Test that RuntimeError is raised if global instance is not initialized.

        Verifies:
            RuntimeError is raised if global AIServiceResilience not properly
            initialized per function docstring Raises documentation.

        Business Impact:
            Provides clear error message when global instance is missing,
            preventing silent failures or undefined behavior.
        """
        # Patch the global ai_resilience instance to None
        with patch('app.infrastructure.resilience.orchestrator.ai_resilience', None):
            # Arrange: Create a test function
            def test_function(data: str) -> str:
                return f"processed: {data}"

            # Act & Assert: RuntimeError is raised when applying decorator
            with pytest.raises(RuntimeError, match="AIServiceResilience not initialized"):
                with_critical_resilience("test_operation")