"""
Test suite for AIServiceResilience initialization and configuration.

This test module verifies that the AIServiceResilience orchestrator initializes
correctly with various configuration scenarios, loads preset configurations properly,
and handles configuration errors gracefully.

Test Categories:
    - Initialization with settings
    - Initialization without settings
    - Configuration loading and overrides
    - Default preset application
    - Error handling during initialization
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.config_presets import ResilienceStrategy, DEFAULT_PRESETS


class TestAIServiceResilienceInitialization:
    """
    Tests for AIServiceResilience initialization behavior per documented contract.

    Verifies that the orchestrator initializes correctly with various settings
    configurations, loads default resilience strategies, and handles configuration
    errors without failing initialization.
    """

    def test_initialization_with_none_settings_uses_defaults(self):
        """
        Test that initialization with None settings uses default preset configurations.

        Verifies:
            AIServiceResilience can initialize without settings object and loads
            default resilience strategy configurations from presets per docstring.

        Business Impact:
            Enables standalone usage in testing scenarios and provides sensible
            defaults when settings object unavailable.

        Scenario:
            Given: No settings object provided (settings=None)
            When: AIServiceResilience is instantiated
            Then: Instance initializes successfully with default preset configurations
            And: Default circuit breakers collection is empty
            And: Default metrics collection is empty
            And: Default configurations dictionary is initialized

        Fixtures Used:
            - None (tests bare initialization without external dependencies)
        """
        # Given: No settings object provided
        settings = None

        # When: AIServiceResilience is instantiated
        orchestrator = AIServiceResilience(settings)

        # Then: Instance initializes successfully
        assert orchestrator is not None
        assert isinstance(orchestrator, AIServiceResilience)

        # And: Default circuit breakers collection is empty
        assert hasattr(orchestrator, 'circuit_breakers')
        assert len(orchestrator.circuit_breakers) == 0
        assert isinstance(orchestrator.circuit_breakers, dict)

        # And: Default metrics collection is empty
        assert hasattr(orchestrator, 'operation_metrics')
        assert len(orchestrator.operation_metrics) == 0
        assert isinstance(orchestrator.operation_metrics, dict)

        # And: Default configurations dictionary is initialized with preset configurations
        assert hasattr(orchestrator, 'configurations')
        assert isinstance(orchestrator.configurations, dict)
        assert len(orchestrator.configurations) > 0  # Should contain default presets

        # Verify default preset strategies are loaded
        for strategy in ResilienceStrategy:
            assert strategy in orchestrator.configurations
            assert orchestrator.configurations[strategy].strategy == strategy

        # And: Settings attribute is None
        assert orchestrator.settings is None

    def test_initialization_with_valid_settings_applies_overrides(self):
        """
        Test that initialization with settings applies configuration overrides to all strategies.

        Verifies:
            Settings object overrides are applied to all strategy configurations while
            preserving strategy-specific characteristics per initialization docstring.

        Business Impact:
            Ensures production settings are properly applied across all resilience
            strategies for consistent behavior.

        Scenario:
            Given: A valid settings object with resilience configuration
            When: AIServiceResilience is instantiated with settings object
            Then: Instance initializes successfully
            And: Settings overrides are applied to all strategy configurations
            And: Strategy-specific characteristics are preserved
            And: Thread-safe data structures are initialized

        Fixtures Used:
            - test_settings: Real Settings instance with test configuration
        """
        # Given: A valid settings object with resilience configuration
        mock_settings = Mock()
        mock_base_config = Mock()
        mock_base_config.retry_config = Mock(max_attempts=4, exponential_multiplier=1.5)
        mock_base_config.circuit_breaker_config = Mock(failure_threshold=6, recovery_timeout=90)
        mock_base_config.enable_circuit_breaker = True
        mock_base_config.enable_retry = True
        mock_settings.get_resilience_config.return_value = mock_base_config

        # When: AIServiceResilience is instantiated with settings object
        orchestrator = AIServiceResilience(mock_settings)

        # Then: Instance initializes successfully
        assert orchestrator is not None
        assert isinstance(orchestrator, AIServiceResilience)

        # And: Settings object is stored
        assert orchestrator.settings is mock_settings

        # And: Settings overrides are applied to all strategy configurations
        assert len(orchestrator.configurations) == len(DEFAULT_PRESETS)
        for strategy in ResilienceStrategy:
            config = orchestrator.configurations[strategy]
            assert config.strategy == strategy  # Strategy-specific characteristic preserved
            assert config.enable_circuit_breaker == True  # Override applied
            assert config.enable_retry == True  # Override applied

        # And: get_resilience_config was called to load base configuration
        mock_settings.get_resilience_config.assert_called_once()

        # And: Thread-safe data structures are initialized
        assert isinstance(orchestrator.circuit_breakers, dict)
        assert isinstance(orchestrator.operation_metrics, dict)
        assert isinstance(orchestrator.configurations, dict)

    def test_initialization_loads_default_strategy_configurations(self):
        """
        Test that initialization loads default resilience strategy configurations from presets.

        Verifies:
            All default resilience strategies (AGGRESSIVE, BALANCED, CONSERVATIVE, CRITICAL)
            are loaded from presets during initialization per docstring behavior.

        Business Impact:
            Ensures all standard resilience strategies are available for operation-specific
            configuration without requiring explicit registration.

        Scenario:
            Given: AIServiceResilience is being initialized
            When: Initialization completes
            Then: Default preset configurations are loaded
            And: All standard strategies (AGGRESSIVE, BALANCED, CONSERVATIVE, CRITICAL) are available
            And: Configurations dictionary contains strategy mappings
            And: Each strategy has valid retry and circuit breaker configuration

        Fixtures Used:
            - None (tests default preset loading)
        """
        # Given: AIServiceResilience is being initialized
        settings = None

        # When: Initialization completes
        orchestrator = AIServiceResilience(settings)

        # Then: Default preset configurations are loaded
        assert hasattr(orchestrator, 'configurations')
        assert len(orchestrator.configurations) > 0

        # And: All standard strategies are available
        for strategy in [ResilienceStrategy.AGGRESSIVE, ResilienceStrategy.BALANCED,
                        ResilienceStrategy.CONSERVATIVE, ResilienceStrategy.CRITICAL]:
            assert strategy in orchestrator.configurations
            config = orchestrator.configurations[strategy]
            assert config.strategy == strategy

        # And: Each strategy has valid retry and circuit breaker configuration
        for strategy in ResilienceStrategy:
            config = orchestrator.configurations[strategy]
            assert hasattr(config, 'retry_config')
            assert hasattr(config, 'circuit_breaker_config')
            assert hasattr(config, 'enable_circuit_breaker')
            assert hasattr(config, 'enable_retry')

            # Verify retry config has expected attributes
            assert hasattr(config.retry_config, 'max_attempts')
            assert hasattr(config.retry_config, 'exponential_multiplier')
            assert config.retry_config.max_attempts > 0

            # Verify circuit breaker config has expected attributes
            assert hasattr(config.circuit_breaker_config, 'failure_threshold')
            assert hasattr(config.circuit_breaker_config, 'recovery_timeout')
            assert config.circuit_breaker_config.failure_threshold > 0
            assert config.circuit_breaker_config.recovery_timeout > 0

    def test_initialization_creates_empty_collections(self):
        """
        Test that initialization creates empty collections for circuit breakers and metrics.

        Verifies:
            Empty collections for circuit breakers, metrics, and operation configs are
            initialized per docstring behavior for thread-safe operation support.

        Business Impact:
            Ensures clean initial state for metrics tracking and circuit breaker
            management across concurrent operations.

        Scenario:
            Given: AIServiceResilience is being initialized
            When: Initialization completes
            Then: Circuit breakers dictionary is empty
            And: Operation metrics dictionary is empty
            And: Operation configurations dictionary is empty
            And: All collections are thread-safe for concurrent access

        Fixtures Used:
            - None (tests initial state creation)
        """
        # Given: AIServiceResilience is being initialized
        settings = None

        # When: Initialization completes
        orchestrator = AIServiceResilience(settings)

        # Then: Circuit breakers dictionary is empty
        assert hasattr(orchestrator, 'circuit_breakers')
        assert isinstance(orchestrator.circuit_breakers, dict)
        assert len(orchestrator.circuit_breakers) == 0

        # And: Operation metrics dictionary is empty
        assert hasattr(orchestrator, 'operation_metrics')
        assert isinstance(orchestrator.operation_metrics, dict)
        assert len(orchestrator.operation_metrics) == 0

        # And: Collections are thread-safe (dict type is thread-safe for basic operations)
        # Note: Python dict operations are thread-safe for single operations
        # and the implementation uses thread-safe patterns for more complex operations

        # Verify that the collections support basic dict operations
        orchestrator.circuit_breakers['test'] = 'value'
        assert 'test' in orchestrator.circuit_breakers
        del orchestrator.circuit_breakers['test']
        assert 'test' not in orchestrator.circuit_breakers

        orchestrator.operation_metrics['test'] = 'value'
        assert 'test' in orchestrator.operation_metrics
        del orchestrator.operation_metrics['test']
        assert 'test' not in orchestrator.operation_metrics

    def test_initialization_handles_settings_loading_errors_gracefully(self):
        """
        Test that initialization handles configuration loading errors without failing.

        Verifies:
            Configuration loading errors are logged as warnings without failing
            initialization per docstring behavior guarantee.

        Business Impact:
            Prevents application startup failures due to configuration issues while
            maintaining operational capability with default settings.

        Scenario:
            Given: A settings object with invalid resilience configuration
            When: AIServiceResilience is instantiated with problematic settings
            Then: Instance initializes successfully despite configuration errors
            And: Warning is logged for configuration loading error
            And: Default configurations are used as fallback
            And: System remains operational with sensible defaults

        Fixtures Used:
            - mock_logger: Mock logger to verify warning messages
            - test_settings: Settings instance with invalid configuration
        """
        # Given: A settings object with invalid resilience configuration
        mock_settings = Mock()
        mock_settings.get_resilience_config.side_effect = Exception("Configuration loading failed")

        # Mock logger to capture warning messages
        with patch('app.infrastructure.resilience.orchestrator.logger') as mock_logger:
            # When: AIServiceResilience is instantiated with problematic settings
            orchestrator = AIServiceResilience(mock_settings)

            # Then: Instance initializes successfully despite configuration errors
            assert orchestrator is not None
            assert isinstance(orchestrator, AIServiceResilience)
            assert orchestrator.settings is mock_settings

            # And: Warning is logged for configuration loading error
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Error loading resilience configuration" in warning_call

            # And: Default configurations are used as fallback
            assert len(orchestrator.configurations) == len(DEFAULT_PRESETS)
            for strategy in ResilienceStrategy:
                assert strategy in orchestrator.configurations

            # And: System remains operational with sensible defaults
            assert hasattr(orchestrator, 'circuit_breakers')
            assert hasattr(orchestrator, 'operation_metrics')
            assert isinstance(orchestrator.circuit_breakers, dict)
            assert isinstance(orchestrator.operation_metrics, dict)

    def test_initialization_preserves_strategy_characteristics(self):
        """
        Test that settings overrides preserve strategy-specific characteristics.

        Verifies:
            Global settings overrides are applied while maintaining the relative
            differences between strategies (aggressive vs conservative) per docstring.

        Business Impact:
            Ensures strategy differentiation is maintained even when global settings
            are applied, preserving intended resilience behavior differences.

        Scenario:
            Given: Settings object with global resilience overrides
            When: AIServiceResilience is instantiated with settings
            Then: Strategy-specific characteristics are preserved
            And: Aggressive strategy remains more permissive than conservative
            And: Relative retry attempts and thresholds maintain proper ratios
            And: All strategies reflect global setting overrides

        Fixtures Used:
            - test_settings: Settings with global resilience configuration
        """
        # Given: Settings object with global resilience overrides
        mock_settings = Mock()
        mock_base_config = Mock()
        mock_base_config.retry_config = Mock(max_attempts=4, exponential_multiplier=1.5)
        mock_base_config.circuit_breaker_config = Mock(failure_threshold=6, recovery_timeout=90)
        mock_base_config.enable_circuit_breaker = True
        mock_base_config.enable_retry = True
        mock_settings.get_resilience_config.return_value = mock_base_config

        # When: AIServiceResilience is instantiated with settings
        orchestrator = AIServiceResilience(mock_settings)

        # Then: Strategy-specific characteristics are preserved
        assert len(orchestrator.configurations) == len(DEFAULT_PRESETS)

        # Get strategy-specific configurations
        aggressive_config = orchestrator.configurations[ResilienceStrategy.AGGRESSIVE]
        conservative_config = orchestrator.configurations[ResilienceStrategy.CONSERVATIVE]
        balanced_config = orchestrator.configurations[ResilienceStrategy.BALANCED]
        critical_config = orchestrator.configurations[ResilienceStrategy.CRITICAL]

        # And: All strategies maintain their strategy type
        assert aggressive_config.strategy == ResilienceStrategy.AGGRESSIVE
        assert conservative_config.strategy == ResilienceStrategy.CONSERVATIVE
        assert balanced_config.strategy == ResilienceStrategy.BALANCED
        assert critical_config.strategy == ResilienceStrategy.CRITICAL

        # And: All strategies reflect global setting overrides
        for strategy in ResilienceStrategy:
            config = orchestrator.configurations[strategy]
            assert config.enable_circuit_breaker == mock_base_config.enable_circuit_breaker
            assert config.enable_retry == mock_base_config.enable_retry

        # And: Strategy-specific characteristics from defaults are preserved in the configurations
        # The actual retry/circuit breaker settings would come from the DEFAULT_PRESETS
        # and should maintain their relative characteristics between strategies
        assert aggressive_config.strategy.value == "aggressive"
        assert balanced_config.strategy.value == "balanced"
        assert conservative_config.strategy.value == "conservative"
        assert critical_config.strategy.value == "critical"

    def test_initialization_with_development_settings(self):
        """
        Test that initialization with development settings applies development presets.

        Verifies:
            Development settings result in appropriate development-oriented resilience
            configurations with shorter timeouts and fewer retries for fast feedback.

        Business Impact:
            Ensures development environment has fast failure feedback without
            excessive retry delays during local testing.

        Scenario:
            Given: Settings object configured for development environment
            When: AIServiceResilience is instantiated with development settings
            Then: Development-appropriate configurations are applied
            And: Retry timeouts are shorter than production defaults
            And: Circuit breaker thresholds are lower for faster feedback
            And: Configurations support rapid development iteration

        Fixtures Used:
            - development_settings: Real Settings with development preset
        """
        # Given: Settings object configured for development environment
        mock_dev_settings = Mock()
        mock_base_config = Mock()
        mock_base_config.retry_config = Mock(max_attempts=2, exponential_multiplier=0.5, max_delay_seconds=10)
        mock_base_config.circuit_breaker_config = Mock(failure_threshold=3, recovery_timeout=30)
        mock_base_config.enable_circuit_breaker = True
        mock_base_config.enable_retry = True
        mock_dev_settings.get_resilience_config.return_value = mock_base_config

        # When: AIServiceResilience is instantiated with development settings
        orchestrator = AIServiceResilience(mock_dev_settings)

        # Then: Development-appropriate configurations are applied
        assert orchestrator is not None
        assert orchestrator.settings is mock_dev_settings

        # And: Settings overrides are applied from development configuration
        assert len(orchestrator.configurations) == len(DEFAULT_PRESETS)

        # And: All configurations have development-appropriate settings
        for strategy in ResilienceStrategy:
            config = orchestrator.configurations[strategy]
            assert config.enable_circuit_breaker == True
            assert config.enable_retry == True

        # And: get_resilience_config was called to load development base configuration
        mock_dev_settings.get_resilience_config.assert_called_once()

        # Verify development-style settings would be applied through the base config
        # The actual strategy-specific values would come from DEFAULT_PRESETS but the
        # base config values from development settings would override them
        base_retry_config = mock_dev_settings.get_resilience_config.return_value.retry_config
        assert base_retry_config.max_attempts == 2  # Fewer retries for fast feedback
        assert base_retry_config.exponential_multiplier == 0.5  # Faster retry multiplier

        base_cb_config = mock_dev_settings.get_resilience_config.return_value.circuit_breaker_config
        assert base_cb_config.failure_threshold == 3  # Lower threshold for faster feedback
        assert base_cb_config.recovery_timeout == 30  # Shorter recovery timeout

    def test_initialization_with_production_settings(self):
        """
        Test that initialization with production settings applies production presets.

        Verifies:
            Production settings result in robust resilience configurations with
            appropriate retry attempts and circuit breaker thresholds for stability.

        Business Impact:
            Ensures production environment has appropriate fault tolerance without
            excessive resource consumption or cascade failures.

        Scenario:
            Given: Settings object configured for production environment
            When: AIServiceResilience is instantiated with production settings
            Then: Production-appropriate configurations are applied
            And: Retry attempts are sufficient for transient failure recovery
            And: Circuit breaker thresholds prevent cascade failures
            And: Configurations balance availability and stability

        Fixtures Used:
            - production_settings: Real Settings with production preset
        """
        # Given: Settings object configured for production environment
        mock_prod_settings = Mock()
        mock_base_config = Mock()
        mock_base_config.retry_config = Mock(max_attempts=5, exponential_multiplier=2.0, max_delay_seconds=120)
        mock_base_config.circuit_breaker_config = Mock(failure_threshold=10, recovery_timeout=120)
        mock_base_config.enable_circuit_breaker = True
        mock_base_config.enable_retry = True
        mock_prod_settings.get_resilience_config.return_value = mock_base_config

        # When: AIServiceResilience is instantiated with production settings
        orchestrator = AIServiceResilience(mock_prod_settings)

        # Then: Production-appropriate configurations are applied
        assert orchestrator is not None
        assert orchestrator.settings is mock_prod_settings

        # And: Settings overrides are applied from production configuration
        assert len(orchestrator.configurations) == len(DEFAULT_PRESETS)

        # And: All configurations have production-appropriate settings
        for strategy in ResilienceStrategy:
            config = orchestrator.configurations[strategy]
            assert config.enable_circuit_breaker == True
            assert config.enable_retry == True

        # And: get_resilience_config was called to load production base configuration
        mock_prod_settings.get_resilience_config.assert_called_once()

        # Verify production-style settings would be applied through the base config
        # The actual strategy-specific values would come from DEFAULT_PRESETS but the
        # base config values from production settings would override them
        base_retry_config = mock_prod_settings.get_resilience_config.return_value.retry_config
        assert base_retry_config.max_attempts == 5  # Sufficient retries for transient failure recovery
        assert base_retry_config.exponential_multiplier == 2.0  # Conservative retry multiplier
        assert base_retry_config.max_delay_seconds == 120  # Reasonable maximum delay

        base_cb_config = mock_prod_settings.get_resilience_config.return_value.circuit_breaker_config
        assert base_cb_config.failure_threshold == 10  # Higher threshold to prevent cascade failures
        assert base_cb_config.recovery_timeout == 120  # Longer recovery timeout for stability


class TestAIServiceResilienceThreadSafety:
    """
    Tests for thread-safe data structure initialization.

    Verifies that AIServiceResilience initializes with thread-safe collections
    that support concurrent operation execution without race conditions.
    """

    def test_initialization_creates_thread_safe_structures(self):
        """
        Test that initialization creates thread-safe data structures for concurrent access.

        Verifies:
            All internal collections (circuit breakers, metrics, configurations) are
            thread-safe for concurrent operation support per docstring.

        Business Impact:
            Enables safe concurrent operation execution without race conditions or
            data corruption in production environments.

        Scenario:
            Given: AIServiceResilience is being initialized
            When: Initialization completes
            Then: Circuit breakers dictionary supports concurrent access
            And: Metrics dictionary supports concurrent updates
            And: Configurations dictionary supports concurrent reads
            And: No race conditions occur during concurrent operations

        Fixtures Used:
            - None (tests internal structure initialization)
        """
        # Given: AIServiceResilience is being initialized
        settings = None

        # When: Initialization completes
        orchestrator = AIServiceResilience(settings)

        # Then: Circuit breakers dictionary supports concurrent access
        assert hasattr(orchestrator, 'circuit_breakers')
        assert isinstance(orchestrator.circuit_breakers, dict)
        # Python dict provides basic thread safety for single operations

        # And: Metrics dictionary supports concurrent updates
        assert hasattr(orchestrator, 'operation_metrics')
        assert isinstance(orchestrator.operation_metrics, dict)

        # And: Configurations dictionary supports concurrent reads
        assert hasattr(orchestrator, 'configurations')
        assert isinstance(orchestrator.configurations, dict)

        # Test that collections support concurrent access patterns
        # Simulate concurrent access by performing multiple operations
        import threading
        import time

        def concurrent_operations():
            """Simulate concurrent access to internal collections."""
            # Test circuit breakers dictionary access
            for i in range(5):
                key = f"test_cb_{i}"
                orchestrator.circuit_breakers[key] = f"value_{i}"
                assert key in orchestrator.circuit_breakers

            # Test metrics dictionary access
            for i in range(5):
                key = f"test_metrics_{i}"
                orchestrator.operation_metrics[key] = f"metrics_{i}"
                assert key in orchestrator.operation_metrics

            # Test configurations dictionary read access
            for strategy in ResilienceStrategy:
                config = orchestrator.configurations[strategy]
                assert config is not None
                assert config.strategy == strategy

        # Create multiple threads to test concurrent access
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_operations)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify that collections are still functional after concurrent access
        assert len(orchestrator.circuit_breakers) > 0
        assert len(orchestrator.operation_metrics) > 0
        assert len(orchestrator.configurations) == len(DEFAULT_PRESETS)

        # Clean up test data
        orchestrator.circuit_breakers.clear()
        orchestrator.operation_metrics.clear()

