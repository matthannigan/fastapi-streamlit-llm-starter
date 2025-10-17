"""
Test suite for ConfigurationMetricsCollector initialization and configuration.

Verifies that the metrics collector initializes correctly with various configurations
and sets up proper state management, retention policies, and thread-safety mechanisms.
"""

import pytest
from app.infrastructure.resilience.config_monitoring import ConfigurationMetricsCollector


class TestConfigurationMetricsCollectorInitialization:
    """
    Test suite for ConfigurationMetricsCollector initialization behavior.
    
    Scope:
        - Constructor parameter validation and defaults
        - State initialization for metrics storage
        - Thread-safety mechanism setup
        - Retention policy configuration
        
    Business Critical:
        Proper initialization ensures reliable metrics collection without memory leaks
        or thread-safety issues in production monitoring scenarios.
        
    Test Strategy:
        - Verify default configuration behavior
        - Test custom configuration parameters
        - Validate parameter boundary conditions
        - Confirm thread-safe structure initialization
    """
    
    def test_initialization_with_defaults_creates_functional_collector(self):
        """
        Test that collector initializes successfully with default parameters.

        Verifies:
            ConfigurationMetricsCollector can be instantiated with no arguments
            and provides a functional metrics collection system with default settings.

        Business Impact:
            Ensures zero-configuration setup for standard monitoring use cases,
            reducing deployment complexity and configuration errors.

        Scenario:
            Given: No custom configuration parameters
            When: ConfigurationMetricsCollector is instantiated with defaults
            Then: Collector instance is created successfully
            And: Default max_events is 10000
            And: Default retention_hours is 24
            And: Collector is ready to accept metrics

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Given: No custom configuration parameters
        # When: ConfigurationMetricsCollector is instantiated with defaults
        collector = ConfigurationMetricsCollector()

        # Then: Collector instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Default max_events is 10000
        assert collector.max_events == 10000

        # And: Default retention_hours is 24
        assert collector.retention_hours == 24

        # And: Collector is ready to accept metrics (test by recording a metric)
        collector.record_preset_usage("test_preset", "load")
        stats = collector.get_usage_statistics()
        assert stats is not None
    
    def test_initialization_with_custom_max_events_applies_setting(self):
        """
        Test that custom max_events parameter is applied correctly.

        Verifies:
            The max_events parameter controls the maximum number of metrics
            retained in memory as documented in the constructor contract.

        Business Impact:
            Enables memory management for high-volume environments by controlling
            metrics buffer size to prevent unbounded memory growth.

        Scenario:
            Given: A custom max_events value of 5000
            When: ConfigurationMetricsCollector is instantiated with max_events=5000
            Then: Collector instance is created successfully
            And: Collector accepts metrics up to the configured limit

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Given: A custom max_events value of 5000
        custom_max_events = 5000

        # When: ConfigurationMetricsCollector is instantiated with max_events=5000
        collector = ConfigurationMetricsCollector(max_events=custom_max_events)

        # Then: Collector instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Collector accepts metrics up to the configured limit
        assert collector.max_events == custom_max_events
        assert collector.metrics.maxlen == custom_max_events
    
    def test_initialization_with_custom_retention_hours_applies_setting(self):
        """
        Test that custom retention_hours parameter is applied correctly.

        Verifies:
            The retention_hours parameter controls how long metrics are retained
            before automatic cleanup as documented in the constructor contract.

        Business Impact:
            Provides flexible retention policies for different operational requirements,
            balancing historical analysis needs with memory constraints.

        Scenario:
            Given: A custom retention_hours value of 48
            When: ConfigurationMetricsCollector is instantiated with retention_hours=48
            Then: Collector instance is created successfully
            And: Retention policy is configured for 48 hours

        Fixtures Used:
            - None (tests direct instantiation)
        """
        # Given: A custom retention_hours value of 48
        custom_retention_hours = 48

        # When: ConfigurationMetricsCollector is instantiated with retention_hours=48
        collector = ConfigurationMetricsCollector(retention_hours=custom_retention_hours)

        # Then: Collector instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Retention policy is configured for 48 hours
        assert collector.retention_hours == custom_retention_hours
    
    def test_initialization_with_invalid_max_events_raises_value_error(self):
        """
        Test that negative or zero max_events raises ValueError per contract.

        Verifies:
            Constructor validates max_events is a positive integer and raises
            ValueError for invalid inputs as documented in Raises section.

        Business Impact:
            Prevents misconfiguration that could cause unexpected behavior or
            memory issues in production monitoring systems.

        Scenario:
            Given: An invalid max_events value (0 or negative)
            When: ConfigurationMetricsCollector instantiation is attempted
            Then: ValueError is raised
            And: Error message indicates invalid max_events value

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test with zero max_events
        with pytest.raises(ValueError) as exc_info:
            ConfigurationMetricsCollector(max_events=0)
        assert "positive integer" in str(exc_info.value).lower()

        # Test with negative max_events
        with pytest.raises(ValueError) as exc_info:
            ConfigurationMetricsCollector(max_events=-10)
        assert "positive integer" in str(exc_info.value).lower()
    
    def test_initialization_with_invalid_retention_hours_raises_value_error(self):
        """
        Test that invalid retention_hours raises ValueError per contract.

        Verifies:
            Constructor validates retention_hours is a positive integer and raises
            ValueError for invalid inputs as documented in Raises section.

        Business Impact:
            Prevents misconfiguration of retention policies that could cause
            premature data loss or unbounded memory growth.

        Scenario:
            Given: An invalid retention_hours value (0 or negative)
            When: ConfigurationMetricsCollector instantiation is attempted
            Then: ValueError is raised
            And: Error message indicates invalid retention_hours value

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Test with zero retention_hours
        with pytest.raises(ValueError) as exc_info:
            ConfigurationMetricsCollector(retention_hours=0)
        assert "positive integer" in str(exc_info.value).lower()

        # Test with negative retention_hours
        with pytest.raises(ValueError) as exc_info:
            ConfigurationMetricsCollector(retention_hours=-5)
        assert "positive integer" in str(exc_info.value).lower()
    
    def test_initialization_creates_thread_safe_storage_structures(self):
        """
        Test that initialization creates thread-safe metric storage.

        Verifies:
            Collector initializes internal storage structures that support
            concurrent access from multiple threads as documented in State Management.

        Business Impact:
            Ensures reliable metrics collection in multi-threaded application
            environments without race conditions or data corruption.

        Scenario:
            Given: Standard collector initialization
            When: ConfigurationMetricsCollector is instantiated
            Then: Collector can accept metrics from multiple concurrent operations
            And: No thread-safety exceptions occur during concurrent access

        Fixtures Used:
            - None (tests concurrent behavior)
        """
        import threading

        # Given: Standard collector initialization
        # When: ConfigurationMetricsCollector is instantiated
        collector = ConfigurationMetricsCollector()

        # Then: Collector can accept metrics from multiple concurrent operations
        # And: No thread-safety exceptions occur during concurrent access
        def record_metrics(thread_id):
            for i in range(10):
                collector.record_preset_usage(f"preset_{thread_id}", "load")

        # Create multiple threads that will record metrics concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=record_metrics, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify metrics were recorded without exceptions
        stats = collector.get_usage_statistics()
        assert stats.total_loads == 0  # No CONFIG_LOAD metrics recorded
        # But we should have recorded PRESET_USAGE metrics
        assert len(collector.metrics) == 50  # 5 threads * 10 metrics each


class TestConfigurationMetricsCollectorBoundaryConditions:
    """
    Test suite for ConfigurationMetricsCollector boundary value handling.
    
    Scope:
        - Minimum valid parameter values
        - Maximum valid parameter values
        - Edge cases at documented boundaries
        
    Business Critical:
        Correct boundary handling prevents configuration errors and ensures
        reliable operation across the full range of supported configurations.
    """
    
    def test_initialization_with_minimum_max_events_succeeds(self):
        """
        Test that minimum documented max_events value (1000) works correctly.

        Verifies:
            The minimum boundary of max_events (1000) documented in the
            constructor Args section is accepted and functional.

        Business Impact:
            Validates that lightweight configurations for testing or
            low-volume environments are supported.

        Scenario:
            Given: max_events value of 1000 (documented minimum)
            When: ConfigurationMetricsCollector is instantiated
            Then: Instance is created successfully
            And: Collector functions normally with minimal buffer size

        Fixtures Used:
            - None (tests boundary condition)
        """
        # Given: max_events value of 1000 (documented minimum)
        min_max_events = 1000

        # When: ConfigurationMetricsCollector is instantiated
        collector = ConfigurationMetricsCollector(max_events=min_max_events)

        # Then: Instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Collector functions normally with minimal buffer size
        assert collector.max_events == min_max_events
        assert collector.metrics.maxlen == min_max_events

        # Verify functional by recording a metric
        collector.record_preset_usage("test_preset", "load")
        stats = collector.get_usage_statistics()
        assert stats is not None
    
    def test_initialization_with_maximum_max_events_succeeds(self):
        """
        Test that maximum documented max_events value (100000) works correctly.

        Verifies:
            The maximum boundary of max_events (100000) documented in the
            constructor Args section is accepted and functional.

        Business Impact:
            Validates that high-volume production environments can configure
            large metric buffers for extensive historical analysis.

        Scenario:
            Given: max_events value of 100000 (documented maximum)
            When: ConfigurationMetricsCollector is instantiated
            Then: Instance is created successfully
            And: Collector supports large-scale metric collection

        Fixtures Used:
            - None (tests boundary condition)
        """
        # Given: max_events value of 100000 (documented maximum)
        max_max_events = 100000

        # When: ConfigurationMetricsCollector is instantiated
        collector = ConfigurationMetricsCollector(max_events=max_max_events)

        # Then: Instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Collector supports large-scale metric collection
        assert collector.max_events == max_max_events
        assert collector.metrics.maxlen == max_max_events

        # Verify functional by recording a metric
        collector.record_preset_usage("test_preset", "load")
        stats = collector.get_usage_statistics()
        assert stats is not None
    
    def test_initialization_with_minimum_retention_hours_succeeds(self):
        """
        Test that minimum documented retention_hours value (1) works correctly.

        Verifies:
            The minimum boundary of retention_hours (1) documented in the
            constructor Args section is accepted and functional.

        Business Impact:
            Validates short-term monitoring configurations suitable for
            testing or high-turnover metric scenarios.

        Scenario:
            Given: retention_hours value of 1 (documented minimum)
            When: ConfigurationMetricsCollector is instantiated
            Then: Instance is created successfully
            And: Short retention policy is enforced correctly

        Fixtures Used:
            - None (tests boundary condition)
        """
        # Given: retention_hours value of 1 (documented minimum)
        min_retention_hours = 1

        # When: ConfigurationMetricsCollector is instantiated
        collector = ConfigurationMetricsCollector(retention_hours=min_retention_hours)

        # Then: Instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Short retention policy is enforced correctly
        assert collector.retention_hours == min_retention_hours

        # Verify functional by recording a metric
        collector.record_preset_usage("test_preset", "load")
        stats = collector.get_usage_statistics()
        assert stats is not None
    
    def test_initialization_with_maximum_retention_hours_succeeds(self):
        """
        Test that maximum documented retention_hours value (168) works correctly.

        Verifies:
            The maximum boundary of retention_hours (168) documented in the
            constructor Args section is accepted and functional.

        Business Impact:
            Validates week-long metric retention for comprehensive
            historical analysis and trend identification.

        Scenario:
            Given: retention_hours value of 168 (documented maximum, 1 week)
            When: ConfigurationMetricsCollector is instantiated
            Then: Instance is created successfully
            And: Extended retention policy is configured properly

        Fixtures Used:
            - None (tests boundary condition)
        """
        # Given: retention_hours value of 168 (documented maximum, 1 week)
        max_retention_hours = 168

        # When: ConfigurationMetricsCollector is instantiated
        collector = ConfigurationMetricsCollector(retention_hours=max_retention_hours)

        # Then: Instance is created successfully
        assert collector is not None
        assert isinstance(collector, ConfigurationMetricsCollector)

        # And: Extended retention policy is configured properly
        assert collector.retention_hours == max_retention_hours

        # Verify functional by recording a metric
        collector.record_preset_usage("test_preset", "load")
        stats = collector.get_usage_statistics()
        assert stats is not None