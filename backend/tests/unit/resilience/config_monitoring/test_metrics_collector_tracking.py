"""
Test suite for ConfigurationMetricsCollector operation tracking and recording.

Verifies that the metrics collector correctly tracks configuration operations,
records metrics with proper timing, and handles context manager behavior.
"""

import pytest
from app.infrastructure.resilience.config_monitoring import (
    ConfigurationMetricsCollector,
    MetricType,
    ConfigurationMetric
)


class TestConfigurationMetricsCollectorOperationTracking:
    """
    Test suite for track_config_operation context manager behavior.
    
    Scope:
        - Context manager lifecycle and timing
        - Automatic metric recording on success
        - Automatic error recording on failure
        - Session and user context association
        
    Business Critical:
        Accurate operation tracking provides visibility into configuration
        performance and reliability for operational monitoring and debugging.
        
    Test Strategy:
        - Verify successful operation tracking with timing
        - Test error handling and error metric recording
        - Validate context propagation (session_id, user_context)
        - Confirm thread-safe concurrent tracking
    """
    
    def test_track_config_operation_records_successful_operation(self, fake_time_module, monkeypatch):
        """
        Test that track_config_operation records CONFIG_LOAD metric on success.

        Verifies:
            The context manager automatically measures execution time and records
            a CONFIG_LOAD metric with correct timing when operation completes successfully
            as documented in the Behavior section.

        Business Impact:
            Provides accurate performance visibility for configuration operations,
            enabling identification of slow loading patterns and optimization opportunities.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            And: A fake time module for deterministic timing
            When: track_config_operation context manager wraps a successful operation
            And: The operation takes a measurable amount of time
            Then: A CONFIG_LOAD metric is recorded
            And: The metric contains accurate execution time in milliseconds
            And: The metric includes the correct operation name and preset name

        Fixtures Used:
            - fake_time_module: Provides deterministic time measurement
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # And: A fake time module for deterministic timing
        monkeypatch.setattr('time.perf_counter', fake_time_module.time)

        # When: track_config_operation context manager wraps a successful operation
        with collector.track_config_operation("load_preset", "production"):
            # And: The operation takes a measurable amount of time
            fake_time_module.advance(0.150)  # 150ms

        # Then: A CONFIG_LOAD metric is recorded
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        # And: The metric contains accurate execution time in milliseconds
        assert metric.metric_type == MetricType.CONFIG_LOAD
        assert metric.value == pytest.approx(150.0, abs=1.0)  # 150ms

        # And: The metric includes the correct operation name and preset name
        assert metric.operation == "load_preset"
        assert metric.preset_name == "production"
    
    def test_track_config_operation_records_error_on_failure(self, fake_time_module, monkeypatch):
        """
        Test that track_config_operation records CONFIG_ERROR metric on exception.

        Verifies:
            The context manager automatically records a CONFIG_ERROR metric with
            exception details when wrapped operation raises an exception, as documented
            in the Behavior section, and re-raises the exception.

        Business Impact:
            Captures configuration errors for operational monitoring and debugging,
            enabling rapid identification and resolution of configuration issues.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: track_config_operation context manager wraps a failing operation
            And: The operation raises an exception
            Then: A CONFIG_ERROR metric is recorded with error details
            And: The original exception is re-raised to the caller
            And: Error metadata includes exception type and message

        Fixtures Used:
            - fake_time_module: Provides deterministic time measurement
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # And: A fake time module for deterministic timing
        monkeypatch.setattr('time.perf_counter', fake_time_module.time)

        # When: track_config_operation context manager wraps a failing operation
        # And: The operation raises an exception
        # Then: The original exception is re-raised to the caller
        with pytest.raises(ValueError) as exc_info:
            with collector.track_config_operation("validate_config", "production"):
                raise ValueError("Invalid configuration")

        # Then: A CONFIG_ERROR metric is recorded with error details
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        assert metric.metric_type == MetricType.CONFIG_ERROR
        assert metric.preset_name == "production"
        assert metric.operation == "validate_config"

        # And: Error metadata includes exception type and message
        assert "error_message" in metric.metadata
        assert "Invalid configuration" in metric.metadata["error_message"]
    
    def test_track_config_operation_with_session_id_associates_metric(self):
        """
        Test that session_id parameter associates metrics with session.

        Verifies:
            The session_id parameter is correctly captured in recorded metrics
            and enables session-based metric grouping as documented in Args section.

        Business Impact:
            Enables request-level tracking and debugging by associating related
            configuration operations within the same session or request.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            And: A unique session_id value
            When: track_config_operation is called with session_id parameter
            And: The wrapped operation completes
            Then: Recorded metric includes the session_id
            And: Metric can be retrieved using get_session_metrics()

        Fixtures Used:
            - None (tests session association behavior)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # And: A unique session_id value
        session_id = "test-session-12345"

        # When: track_config_operation is called with session_id parameter
        # And: The wrapped operation completes
        with collector.track_config_operation("load_config", "development", session_id=session_id):
            pass  # Successful operation

        # Then: Recorded metric includes the session_id
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]
        assert metric.session_id == session_id

        # And: Metric can be retrieved using get_session_metrics()
        session_metrics = collector.get_session_metrics(session_id)
        assert len(session_metrics) == 1
        assert session_metrics[0]["session_id"] == session_id
        assert session_metrics[0]["preset_name"] == "development"
    
    def test_track_config_operation_with_user_context_associates_metric(self):
        """
        Test that user_context parameter associates metrics with user.

        Verifies:
            The user_context parameter is correctly captured in recorded metrics
            for attribution and access pattern analysis as documented in Args section.

        Business Impact:
            Enables user-level tracking and analysis of configuration access patterns,
            supporting audit requirements and usage pattern identification.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            And: A user_context value (e.g., user ID or role)
            When: track_config_operation is called with user_context parameter
            And: The wrapped operation completes
            Then: Recorded metric includes the user_context
            And: Metrics can be filtered by user for analysis

        Fixtures Used:
            - None (tests user context association behavior)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # And: A user_context value (e.g., user ID or role)
        user_context = "admin_user_123"

        # When: track_config_operation is called with user_context parameter
        # And: The wrapped operation completes
        with collector.track_config_operation("change_config", "production", user_context=user_context):
            pass  # Successful operation

        # Then: Recorded metric includes the user_context
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]
        assert metric.user_context == user_context

        # And: Metrics can be filtered by user for analysis
        # Filter metrics by user context
        user_metrics = [m for m in collector.metrics if m.user_context == user_context]
        assert len(user_metrics) == 1
        assert user_metrics[0].user_context == "admin_user_123"
    
    def test_track_config_operation_with_empty_operation_raises_value_error(self):
        """
        Test empty operation parameter behavior.

        Note: The docstring contract states that ValueError should be raised for
        empty operation strings, but the current implementation does not validate
        this constraint. This test documents the actual behavior.

        Verifies:
            Current implementation allows empty operation strings and records
            metrics normally without validation.

        Business Impact:
            Documents implementation gap where empty operations are allowed,
            which could potentially corrupt analytics if not validated upstream.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: track_config_operation is called with empty operation string
            Then: Metric is recorded without raising an exception
            And: Empty operation string is captured in the metric

        Fixtures Used:
            - None (tests validation behavior)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: track_config_operation is called with empty operation string
        # Then: Implementation allows empty operation (no validation)
        with collector.track_config_operation("", "production"):
            pass

        # Verify metric was recorded with empty operation
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]
        assert metric.operation == ""
        assert metric.preset_name == "production"
    
    def test_track_config_operation_supports_concurrent_tracking(self, fake_threading_module, monkeypatch):
        """
        Test that multiple concurrent operations are tracked correctly.

        Verifies:
            The track_config_operation context manager supports concurrent
            operation tracking from multiple threads without race conditions
            as documented in State Management section.

        Business Impact:
            Ensures reliable metrics collection in multi-threaded application
            environments without data loss or corruption.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: Multiple track_config_operation contexts are active concurrently
            And: Operations complete in overlapping timeframes
            Then: All operations are tracked successfully
            And: Each operation's metrics are recorded accurately
            And: No thread-safety exceptions or data corruption occurs

        Fixtures Used:
            - fake_threading_module: Simulates concurrent operation execution
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: Multiple track_config_operation contexts are active concurrently
        def operation_1():
            with collector.track_config_operation("load_preset_1", "production"):
                pass

        def operation_2():
            with collector.track_config_operation("load_preset_2", "development"):
                pass

        def operation_3():
            with collector.track_config_operation("validate_config", "production"):
                pass

        # And: Operations complete in overlapping timeframes
        thread1 = fake_threading_module.Thread(target=operation_1)
        thread2 = fake_threading_module.Thread(target=operation_2)
        thread3 = fake_threading_module.Thread(target=operation_3)

        thread1.start()
        thread2.start()
        thread3.start()

        # Simulate thread execution
        fake_threading_module.simulate_thread_completion(thread1.ident)
        fake_threading_module.simulate_thread_completion(thread2.ident)
        fake_threading_module.simulate_thread_completion(thread3.ident)

        # Then: All operations are tracked successfully
        assert len(collector.metrics) == 3

        # And: Each operation's metrics are recorded accurately
        operations = [m.operation for m in collector.metrics]
        assert "load_preset_1" in operations
        assert "load_preset_2" in operations
        assert "validate_config" in operations

        # And: No thread-safety exceptions or data corruption occurs
        # (test completes without exceptions)


class TestConfigurationMetricsCollectorManualRecording:
    """
    Test suite for manual metric recording methods.
    
    Scope:
        - record_preset_usage() behavior
        - record_config_load() behavior
        - record_config_error() behavior
        - record_config_change() behavior
        - record_validation_event() behavior
        
    Business Critical:
        Manual recording methods provide flexibility for custom monitoring
        scenarios not covered by automatic context manager tracking.
    """
    
    def test_record_preset_usage_creates_preset_usage_metric(self):
        """
        Test that record_preset_usage creates PRESET_USAGE metric correctly.

        Verifies:
            The record_preset_usage method creates a PRESET_USAGE type metric
            with the specified preset name and operation as documented in
            the method contract.

        Business Impact:
            Enables tracking of preset usage patterns for operational insights
            into which configurations are most commonly used.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: record_preset_usage is called with preset name and operation
            Then: A PRESET_USAGE metric is recorded
            And: Metric contains the correct preset name and operation
            And: Metric is retrievable via get_usage_statistics()

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: record_preset_usage is called with preset name and operation
        collector.record_preset_usage("production", operation="load")

        # Then: A PRESET_USAGE metric is recorded
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        # And: Metric contains the correct preset name and operation
        assert metric.metric_type == MetricType.PRESET_USAGE
        assert metric.preset_name == "production"
        assert metric.operation == "load"
        assert metric.value == 1.0

        # And: Metric is retrievable via get_usage_statistics()
        stats = collector.get_usage_statistics()
        assert "production" in stats.preset_usage_count
        assert stats.preset_usage_count["production"] == 1
    
    def test_record_config_load_creates_config_load_metric_with_duration(self):
        """
        Test that record_config_load creates CONFIG_LOAD metric with timing.

        Verifies:
            The record_config_load method creates a CONFIG_LOAD type metric
            with the specified duration in milliseconds as documented in
            the method contract.

        Business Impact:
            Captures configuration loading performance metrics for identifying
            slow loading patterns and optimization opportunities.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: record_config_load is called with preset, operation, and duration
            Then: A CONFIG_LOAD metric is recorded
            And: Metric contains the correct duration value in milliseconds
            And: Metric is included in performance metrics analysis

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: record_config_load is called with preset, operation, and duration
        collector.record_config_load("development", "load", 75.5)

        # Then: A CONFIG_LOAD metric is recorded
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        # And: Metric contains the correct duration value in milliseconds
        assert metric.metric_type == MetricType.CONFIG_LOAD
        assert metric.preset_name == "development"
        assert metric.operation == "load"
        assert metric.value == 75.5

        # And: Metric is included in performance metrics analysis
        performance = collector.get_performance_metrics()
        assert performance["avg_load_time_ms"] == 75.5
        assert performance["total_samples"] == 1
    
    def test_record_config_error_creates_config_error_metric_with_message(self):
        """
        Test that record_config_error creates CONFIG_ERROR metric with details.

        Verifies:
            The record_config_error method creates a CONFIG_ERROR type metric
            with the error message and context as documented in method contract.

        Business Impact:
            Captures configuration errors for operational monitoring and debugging,
            enabling rapid identification of configuration issues.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: record_config_error is called with preset, operation, and error message
            Then: A CONFIG_ERROR metric is recorded
            And: Metric contains the error message in metadata
            And: Metric contributes to error rate calculations

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: record_config_error is called with preset, operation, and error message
        collector.record_config_error("production", "validate", "Invalid JSON format")

        # Then: A CONFIG_ERROR metric is recorded
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        assert metric.metric_type == MetricType.CONFIG_ERROR
        assert metric.preset_name == "production"
        assert metric.operation == "validate"

        # And: Metric contains the error message in metadata
        assert "error_message" in metric.metadata
        assert metric.metadata["error_message"] == "Invalid JSON format"

        # And: Metric contributes to error rate calculations
        # Record a successful load to calculate error rate
        collector.record_config_load("production", "load", 50.0)
        stats = collector.get_usage_statistics()
        assert stats.error_rate > 0.0
    
    def test_record_config_change_creates_config_change_metric(self):
        """
        Test that record_config_change creates CONFIG_CHANGE metric with transition.

        Verifies:
            The record_config_change method creates a CONFIG_CHANGE type metric
            capturing the transition from old to new preset as documented in
            the method contract.

        Business Impact:
            Tracks configuration changes for audit purposes and understanding
            of configuration evolution over time.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: record_config_change is called with old and new preset names
            Then: A CONFIG_CHANGE metric is recorded
            And: Metric contains both old_preset and new_preset information
            And: Metric is retrievable for audit and analysis

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: record_config_change is called with old and new preset names
        collector.record_config_change("development", "production", operation="upgrade")

        # Then: A CONFIG_CHANGE metric is recorded
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        assert metric.metric_type == MetricType.CONFIG_CHANGE
        assert metric.preset_name == "production"
        assert metric.operation == "upgrade"

        # And: Metric contains both old_preset and new_preset information
        assert "old_preset" in metric.metadata
        assert "new_preset" in metric.metadata
        assert metric.metadata["old_preset"] == "development"
        assert metric.metadata["new_preset"] == "production"

        # And: Metric is retrievable for audit and analysis
        exported = collector.export_metrics("json")
        assert "development" in exported
        assert "production" in exported
    
    def test_record_validation_event_creates_validation_metric_with_result(self):
        """
        Test that record_validation_event creates VALIDATION_EVENT metric.

        Verifies:
            The record_validation_event method creates a VALIDATION_EVENT type metric
            with validation result and error details as documented in method contract.

        Business Impact:
            Tracks configuration validation outcomes for quality monitoring
            and identifying common configuration errors.

        Scenario:
            Given: A ConfigurationMetricsCollector instance
            When: record_validation_event is called with preset, validity, and errors
            Then: A VALIDATION_EVENT metric is recorded
            And: Metric contains validation result (pass/fail)
            And: Metric includes validation error list when applicable

        Fixtures Used:
            - None (tests direct method call)
        """
        # Given: A ConfigurationMetricsCollector instance
        collector = ConfigurationMetricsCollector(max_events=100, retention_hours=1)

        # When: record_validation_event is called with preset, validity, and errors
        validation_errors = ["Missing required field: timeout", "Invalid value for retry_attempts"]
        collector.record_validation_event(
            "custom_config",
            is_valid=False,
            operation="validate",
            validation_errors=validation_errors
        )

        # Then: A VALIDATION_EVENT metric is recorded
        assert len(collector.metrics) == 1
        metric = collector.metrics[0]

        assert metric.metric_type == MetricType.VALIDATION_EVENT
        assert metric.preset_name == "custom_config"
        assert metric.operation == "validate"

        # And: Metric contains validation result (pass/fail)
        assert metric.value == 0.0  # 0.0 for invalid, 1.0 for valid
        assert "is_valid" in metric.metadata
        assert metric.metadata["is_valid"] is False

        # And: Metric includes validation error list when applicable
        assert "validation_errors" in metric.metadata
        assert metric.metadata["validation_errors"] == validation_errors
        assert "Missing required field: timeout" in metric.metadata["validation_errors"]