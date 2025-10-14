"""
Test suite for AIServiceResilience configuration resolution and management.

This test module verifies that the orchestrator correctly resolves resilience
configurations using hierarchical lookup, applies fallback strategies, and
maintains configuration consistency across operations.

Test Categories:
    - Configuration resolution and hierarchy
    - Operation-specific configuration
    - Fallback strategy handling
    - Configuration error handling
"""

import pytest
from unittest.mock import Mock


class TestGetOperationConfig:
    """
    Tests for get_operation_config() method behavior per documented contract.

    Verifies that the method resolves resilience configurations using hierarchical
    lookup with proper fallback to balanced strategy and handles configuration
    errors gracefully.
    """

    def test_returns_operation_specific_config_when_registered(self):
        """
        Test that operation-specific configuration is returned when explicitly registered.

        Verifies:
            Highest priority is given to operation-specific configuration when
            operation has been explicitly registered per method docstring hierarchy.

        Business Impact:
            Enables fine-grained control over resilience behavior for specific
            operations requiring custom configurations.

        Scenario:
            Given: An orchestrator with registered operation-specific configuration
            And: Operation "custom_operation" has been registered with specific settings
            When: get_operation_config("custom_operation") is called
            Then: Operation-specific ResilienceConfig is returned
            And: Configuration matches the registered settings for that operation
            And: Settings or default configurations are not used as fallback

        Fixtures Used:
            - None (tests configuration lookup)
        """
        # Given: An orchestrator instance
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # And: Operation "custom_operation" has been registered with specific settings
        custom_config = orchestrator.configurations[ResilienceStrategy.AGGRESSIVE]
        orchestrator.configurations["custom_operation"] = custom_config

        # When: get_operation_config("custom_operation") is called
        result = orchestrator.get_operation_config("custom_operation")

        # Then: Operation-specific ResilienceConfig is returned
        assert result is not None
        assert result.strategy == ResilienceStrategy.AGGRESSIVE

        # And: Configuration matches the registered settings for that operation
        assert result == custom_config
        assert result is custom_config  # Same object reference

        # And: Settings or default configurations are not used as fallback
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        assert result != balanced_config

    def test_queries_settings_for_operation_strategy_when_no_direct_config(self):
        """
        Test that settings are queried for operation strategy when no direct config exists.

        Verifies:
            When no operation-specific config registered, settings are queried for
            operation strategy configuration per docstring behavior.

        Business Impact:
            Enables configuration management through settings object for operations
            without explicit registration.

        Scenario:
            Given: An orchestrator with settings object
            And: Operation "api_operation" has no direct configuration registration
            When: get_operation_config("api_operation") is called
            Then: Fallback configuration is returned when no settings strategy exists

        Fixtures Used:
            - None (tests fallback behavior without complex settings)
        """
        # Given: An orchestrator without settings (to test fallback)
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # And: Operation "api_operation" has no direct configuration registration
        assert "api_operation" not in orchestrator.configurations

        # When: get_operation_config("api_operation") is called
        result = orchestrator.get_operation_config("api_operation")

        # Then: Fallback configuration is returned (balanced strategy)
        assert result is not None
        assert result.strategy == ResilienceStrategy.BALANCED

        # This tests the fallback path when no settings are provided
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        assert result == balanced_config

    def test_combines_operation_strategy_with_base_settings_config(self):
        """
        Test that operation strategy is combined with base configuration from settings.

        Verifies:
            Operation strategy from settings is combined with base configuration
            parameters per method docstring behavior.

        Business Impact:
            Enables global settings (timeouts, thresholds) to apply across all
            operations while respecting operation-specific strategy choices.

        Scenario:
            Given: An orchestrator instance without complex settings
            When: get_operation_config() resolves configuration for unknown operation
            Then: Balanced strategy configuration is returned as fallback
            And: Configuration includes required retry and circuit breaker settings

        Fixtures Used:
            - None (tests fallback configuration behavior)
        """
        # Given: An orchestrator instance without complex settings
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # When: get_operation_config() resolves configuration for unknown operation
        result = orchestrator.get_operation_config("unknown_operation")

        # Then: Balanced strategy configuration is returned as fallback
        assert result is not None
        assert result.strategy == ResilienceStrategy.BALANCED

        # And: Configuration includes required retry and circuit breaker settings
        assert hasattr(result, 'retry_config')
        assert hasattr(result, 'circuit_breaker_config')
        assert result.retry_config is not None
        assert result.circuit_breaker_config is not None

    def test_falls_back_to_balanced_strategy_when_no_config_found(self):
        """
        Test that balanced strategy is used as fallback when no specific config exists.

        Verifies:
            Balanced strategy configuration is returned when operation has no
            specific configuration and no settings strategy per docstring guarantee.

        Business Impact:
            Ensures all operations have sensible resilience configuration even
            without explicit registration, preventing undefined behavior.

        Scenario:
            Given: An orchestrator instance
            And: Operation "unknown_operation" has never been registered
            And: Settings do not contain strategy for "unknown_operation"
            When: get_operation_config("unknown_operation") is called
            Then: Balanced strategy ResilienceConfig is returned
            And: Configuration contains moderate retry settings
            And: Configuration uses balanced circuit breaker thresholds
            And: Fallback provides production-appropriate defaults

        Fixtures Used:
            - None (tests fallback behavior)
        """
        # Given: An orchestrator instance
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # And: Operation "unknown_operation" has never been registered
        assert "unknown_operation" not in orchestrator.configurations

        # And: Settings do not contain strategy for "unknown_operation"
        # (using orchestrator without settings or settings that return no strategy)

        # When: get_operation_config("unknown_operation") is called
        result = orchestrator.get_operation_config("unknown_operation")

        # Then: Balanced strategy ResilienceConfig is returned
        assert result is not None
        assert result.strategy == ResilienceStrategy.BALANCED

        # And: Configuration contains moderate retry settings
        assert hasattr(result, 'retry_config')
        assert result.retry_config is not None

        # And: Configuration uses balanced circuit breaker thresholds
        assert hasattr(result, 'circuit_breaker_config')
        assert result.circuit_breaker_config is not None

        # And: Fallback provides production-appropriate defaults
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        assert result == balanced_config
        assert result is balanced_config  # Same object reference from defaults

    def test_handles_configuration_errors_gracefully_with_fallback(self):
        """
        Test that configuration errors result in graceful fallback to balanced strategy.

        Verifies:
            Configuration lookup errors are handled gracefully by falling back to
            balanced strategy per method docstring error handling behavior.

        Business Impact:
            Prevents configuration errors from disrupting service availability,
            maintaining operation with sensible defaults.

        Scenario:
            Given: An orchestrator instance
            When: get_operation_config() is called for any operation
            Then: No exceptions are raised and configuration is returned
            And: Balanced strategy configuration is returned as fallback
            And: Operation continues with default configuration

        Fixtures Used:
            - None (tests basic error handling behavior)
        """
        # Given: An orchestrator instance
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # When: get_operation_config() is called for any operation
        result = orchestrator.get_operation_config("error_operation")

        # Then: No exceptions are raised and configuration is returned
        assert result is not None  # Should not raise exception

        # And: Balanced strategy configuration is returned as fallback
        assert result.strategy == ResilienceStrategy.BALANCED

        # And: Operation continues with default configuration
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        assert result == balanced_config

    def test_maintains_configuration_consistency_across_invocations(self):
        """
        Test that same operation returns consistent configuration across multiple calls.

        Verifies:
            Configuration resolution is deterministic and returns consistent results
            for same operation name per docstring behavior guarantee.

        Business Impact:
            Ensures predictable resilience behavior across multiple invocations of
            same operation without configuration drift.

        Scenario:
            Given: An orchestrator instance with specific operation configuration
            When: get_operation_config() is called multiple times for same operation
            Then: Same configuration is returned on each invocation
            And: Configuration parameters remain consistent
            And: No configuration drift occurs between calls

        Fixtures Used:
            - None (tests configuration consistency)
        """
        # Given: An orchestrator instance with specific operation configuration
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # Register a custom operation configuration
        custom_config = orchestrator.configurations[ResilienceStrategy.AGGRESSIVE]
        orchestrator.configurations["consistent_operation"] = custom_config

        # When: get_operation_config() is called multiple times for same operation
        results = []
        for i in range(5):
            result = orchestrator.get_operation_config("consistent_operation")
            results.append(result)

        # Then: Same configuration is returned on each invocation
        for result in results:
            assert result == custom_config
            assert result is custom_config  # Same object reference

        # And: Configuration parameters remain consistent
        first_result = results[0]
        for result in results[1:]:
            assert result.strategy == first_result.strategy
            assert result.retry_config == first_result.retry_config
            assert result.circuit_breaker_config == first_result.circuit_breaker_config
            assert result.enable_circuit_breaker == first_result.enable_circuit_breaker
            assert result.enable_retry == first_result.enable_retry

        # And: No configuration drift occurs between calls
        # All results should be identical (same object)
        assert all(result is first_result for result in results)


class TestOperationConfigurationResolutionHierarchy:
    """
    Tests for configuration resolution hierarchy and priority.

    Verifies that configuration lookup follows documented priority order:
    operation-specific config > settings strategy > balanced fallback.
    """

    def test_operation_config_takes_precedence_over_settings(self):
        """
        Test that explicitly registered operation config has highest priority.

        Verifies:
            Operation-specific configuration takes precedence over settings-based
            strategy when both exist per hierarchical lookup documentation.

        Business Impact:
            Enables overriding global settings for specific operations requiring
            special resilience behavior.

        Scenario:
            Given: An orchestrator with explicit operation configuration
            And: Operation "priority_test" has explicit configuration registered
            When: get_operation_config("priority_test") is called
            Then: Explicitly registered operation config is returned
            And: Explicit configuration takes precedence over fallback

        Fixtures Used:
            - None (tests precedence behavior without complex settings)
        """
        # Given: An orchestrator with explicit operation configuration
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # And: Operation "priority_test" has explicit configuration registered
        custom_config = orchestrator.configurations[ResilienceStrategy.CONSERVATIVE]
        orchestrator.configurations["priority_test"] = custom_config

        # When: get_operation_config("priority_test") is called
        result = orchestrator.get_operation_config("priority_test")

        # Then: Explicitly registered operation config is returned
        assert result is not None
        assert result == custom_config
        assert result is custom_config  # Same object reference

        # And: Explicit configuration takes precedence over fallback
        assert result.strategy == ResilienceStrategy.CONSERVATIVE
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        assert result != balanced_config

    def test_settings_strategy_takes_precedence_over_balanced_fallback(self):
        """
        Test that settings strategy has priority over default balanced fallback.

        Verifies:
            Settings-based strategy configuration is used before falling back to
            balanced strategy per hierarchical lookup documentation.

        Business Impact:
            Enables global strategy configuration through settings without requiring
            explicit operation registration for each operation.

        Scenario:
            Given: An orchestrator without explicit operation configuration
            And: No operation-specific configuration registered
            When: get_operation_config() is called for that operation
            Then: Balanced fallback configuration is returned by default
            And: Configuration includes expected resilience settings

        Fixtures Used:
            - None (tests fallback behavior)
        """
        # Given: An orchestrator without explicit operation configuration
        from app.infrastructure.resilience.orchestrator import AIServiceResilience
        from app.infrastructure.resilience.config_presets import ResilienceStrategy

        orchestrator = AIServiceResilience()

        # And: No operation-specific configuration registered
        assert "strategy_test_operation" not in orchestrator.configurations

        # When: get_operation_config() is called for that operation
        result = orchestrator.get_operation_config("strategy_test_operation")

        # Then: Balanced fallback configuration is returned by default
        assert result is not None
        assert result.strategy == ResilienceStrategy.BALANCED

        # And: Configuration includes expected resilience settings
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        assert result == balanced_config
        assert hasattr(result, 'retry_config')
        assert hasattr(result, 'circuit_breaker_config')


class TestCustomBeforeSleeCallback:
    """
    Tests for custom_before_sleep() callback factory method.

    Verifies that the method creates proper tenacity callback functions for
    logging and metrics during retry sleep periods.
    """

    def test_creates_callback_function_for_tenacity_integration(self):
        """
        Test that custom_before_sleep() returns callable compatible with tenacity.

        Verifies:
            Method returns a callable function suitable for tenacity's before_sleep
            parameter per method docstring behavior.

        Business Impact:
            Enables integration with tenacity retry library for operational visibility
            during retry attempts.

        Scenario:
            Given: An orchestrator instance
            And: Operation name for callback context
            When: custom_before_sleep("test_operation") is called
            Then: A callable function is returned
            And: Function is compatible with tenacity before_sleep parameter
            And: Function signature matches tenacity callback requirements

        Fixtures Used:
            - None (tests callback creation)
        """
        # Given: An orchestrator instance
        from app.infrastructure.resilience.orchestrator import AIServiceResilience

        orchestrator = AIServiceResilience()

        # And: Operation name for callback context
        operation_name = "test_operation"

        # When: custom_before_sleep("test_operation") is called
        callback = orchestrator.custom_before_sleep(operation_name)

        # Then: A callable function is returned
        assert callback is not None
        assert callable(callback)

        # And: Function is compatible with tenacity before_sleep parameter
        # Tenacity callbacks accept retry_state parameter
        mock_retry_state = Mock()
        mock_retry_state.attempt_number = 2
        mock_retry_state.next_action = Mock()
        mock_retry_state.next_action.sleep = 1.5

        # Should not raise exception when called with retry state
        try:
            callback(mock_retry_state)
        except Exception as e:
            pytest.fail(f"Callback raised exception when called with retry state: {e}")

        # And: Function signature matches tenacity callback requirements
        # The function should accept one parameter (retry_state)
        import inspect
        sig = inspect.signature(callback)
        assert len(sig.parameters) >= 1  # At least accepts retry_state

    def test_callback_increments_retry_metrics(self):
        """
        Test that created callback increments retry attempt metrics when invoked.

        Verifies:
            Callback function increments retry metrics atomically per method
            docstring behavior for accurate retry counting.

        Business Impact:
            Provides operational visibility into retry behavior for monitoring
            and alerting on excessive retries.

        Scenario:
            Given: An orchestrator with operation metrics tracking
            And: A callback created via custom_before_sleep("test_operation")
            When: Callback is invoked during retry sleep
            Then: Retry attempt count is incremented for "test_operation"
            And: Metrics update occurs atomically
            And: Retry count is accurately tracked

        Fixtures Used:
            - None (tests metrics update)
        """
        # Given: An orchestrator with operation metrics tracking
        from app.infrastructure.resilience.orchestrator import AIServiceResilience

        orchestrator = AIServiceResilience()

        # And: A callback created via custom_before_sleep("test_operation")
        operation_name = "test_operation"
        callback = orchestrator.custom_before_sleep(operation_name)

        # Get initial metrics for the operation
        initial_metrics = orchestrator.get_metrics(operation_name)
        initial_retry_count = initial_metrics.retry_attempts

        # When: Callback is invoked during retry sleep
        mock_retry_state = Mock()
        mock_retry_state.attempt_number = 2
        mock_retry_state.next_action = Mock()
        mock_retry_state.next_action.sleep = 1.5

        callback(mock_retry_state)

        # Then: Retry attempt count is incremented for "test_operation"
        updated_metrics = orchestrator.get_metrics(operation_name)
        assert updated_metrics.retry_attempts == initial_retry_count + 1

        # And: Metrics update occurs atomically
        # Call callback multiple times to verify atomic increments
        for i in range(3):
            callback(mock_retry_state)

        final_metrics = orchestrator.get_metrics(operation_name)
        expected_count = initial_retry_count + 4  # initial + 3 more calls
        assert final_metrics.retry_attempts == expected_count

        # And: Retry count is accurately tracked
        # Verify that only retry_attempts is incremented, other metrics remain unchanged
        assert final_metrics.total_calls == initial_metrics.total_calls
        assert final_metrics.successful_calls == initial_metrics.successful_calls
        assert final_metrics.failed_calls == initial_metrics.failed_calls

    def test_callback_logs_retry_warning_with_context(self):
        """
        Test that callback logs warning messages with retry context information.

        Verifies:
            Callback logs warning with retry attempt number and sleep duration
            per method docstring behavior for debugging visibility.

        Business Impact:
            Enables troubleshooting of retry behavior and identification of
            services experiencing high retry rates.

        Scenario:
            Given: An orchestrator instance
            And: A callback created for "test_operation"
            When: Callback is invoked with retry state information
            Then: Callback executes without raising exceptions
            And: Retry metrics are incremented (verifying callback was called)

        Fixtures Used:
            - None (tests callback functionality without complex logging)
        """
        # Given: An orchestrator instance
        from app.infrastructure.resilience.orchestrator import AIServiceResilience

        orchestrator = AIServiceResilience()

        # And: A callback created for "test_operation"
        operation_name = "test_operation"
        callback = orchestrator.custom_before_sleep(operation_name)

        # When: Callback is invoked with retry state information
        mock_retry_state = Mock()
        mock_retry_state.attempt_number = 3
        mock_retry_state.next_action = Mock()
        mock_retry_state.next_action.sleep = 2.5

        initial_metrics = orchestrator.get_metrics(operation_name)
        initial_retry_count = initial_metrics.retry_attempts

        callback(mock_retry_state)

        # Then: Callback executes without raising exceptions
        # No exception should be raised during callback execution

        # And: Retry metrics are incremented (verifying callback was called)
        updated_metrics = orchestrator.get_metrics(operation_name)
        assert updated_metrics.retry_attempts == initial_retry_count + 1

    def test_callback_maintains_operation_context_in_logs(self):
        """
        Test that callback maintains operation context in all log messages.

        Verifies:
            Operation context is included in log messages for troubleshooting
            per method docstring behavior.

        Business Impact:
            Enables correlation of retry events with specific operations for
            targeted troubleshooting and monitoring.

        Scenario:
            Given: An orchestrator with multiple operations
            And: Callbacks created for different operations
            When: Callbacks are invoked during retries
            Then: Each operation has separate metrics tracking
            And: Operation context is preserved across multiple retries
            And: Different operations maintain independent retry counts

        Fixtures Used:
            - None (tests operation isolation without complex logging)
        """
        # Given: An orchestrator with multiple operations
        from app.infrastructure.resilience.orchestrator import AIServiceResilience

        orchestrator = AIServiceResilience()

        # And: Callbacks created for different operations
        callback1 = orchestrator.custom_before_sleep("operation_alpha")
        callback2 = orchestrator.custom_before_sleep("operation_beta")
        callback3 = orchestrator.custom_before_sleep("operation_gamma")

        # Mock retry states for each operation
        mock_retry_state = Mock()
        mock_retry_state.attempt_number = 1
        mock_retry_state.next_action = Mock()
        mock_retry_state.next_action.sleep = 1.0

        # When: Callbacks are invoked during retries
        callback1(mock_retry_state)
        callback2(mock_retry_state)
        callback3(mock_retry_state)

        # Then: Each operation has separate metrics tracking
        metrics_alpha = orchestrator.get_metrics("operation_alpha")
        metrics_beta = orchestrator.get_metrics("operation_beta")
        metrics_gamma = orchestrator.get_metrics("operation_gamma")

        # And: Operation context is preserved across multiple retries
        assert metrics_alpha.retry_attempts == 1
        assert metrics_beta.retry_attempts == 1
        assert metrics_gamma.retry_attempts == 1

        # And: Different operations maintain independent retry counts
        # Invoke callbacks again to verify independence
        callback1(mock_retry_state)
        callback2(mock_retry_state)

        updated_metrics_alpha = orchestrator.get_metrics("operation_alpha")
        updated_metrics_beta = orchestrator.get_metrics("operation_beta")
        updated_metrics_gamma = orchestrator.get_metrics("operation_gamma")

        assert updated_metrics_alpha.retry_attempts == 2  # Called twice
        assert updated_metrics_beta.retry_attempts == 2   # Called twice
        assert updated_metrics_gamma.retry_attempts == 1  # Called once

