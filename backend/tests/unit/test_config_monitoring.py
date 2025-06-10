"""
Unit tests for configuration monitoring and metrics collection.

Tests the configuration monitoring functionality including metrics collection,
usage statistics, performance tracking, and alert generation.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.config_monitoring import (
    ConfigurationMetricsCollector,
    ConfigurationMetric,
    ConfigurationAlert,
    MetricType,
    AlertLevel,
    ConfigurationUsageStats,
    config_metrics_collector
)


class TestConfigurationMetricsCollector:
    """Test the ConfigurationMetricsCollector class."""
    
    @pytest.fixture
    def metrics_collector(self):
        """Create a fresh metrics collector for testing."""
        return ConfigurationMetricsCollector(max_events=100, retention_hours=24)
    
    def test_metrics_collector_initialization(self, metrics_collector):
        """Test metrics collector initializes correctly."""
        assert len(metrics_collector.metrics) == 0
        assert len(metrics_collector.alerts) == 0
        assert metrics_collector.max_events == 100
        assert metrics_collector.retention_hours == 24
        assert metrics_collector._stats_cache is None
    
    def test_record_preset_usage(self, metrics_collector):
        """Test recording preset usage metrics."""
        metrics_collector.record_preset_usage(
            preset_name="simple",
            operation="load",
            session_id="test-session",
            user_context="test-user",
            metadata={"test": "value"}
        )
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[0]
        assert metric.metric_type == MetricType.PRESET_USAGE
        assert metric.preset_name == "simple"
        assert metric.operation == "load"
        assert metric.value == 1.0
        assert metric.session_id == "test-session"
        assert metric.user_context == "test-user"
        assert metric.metadata["test"] == "value"
    
    def test_record_config_load(self, metrics_collector):
        """Test recording configuration load performance."""
        duration_ms = 45.5
        metrics_collector.record_config_load(
            preset_name="production",
            operation="load_preset",
            duration_ms=duration_ms,
            session_id="test-session"
        )
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[0]
        assert metric.metric_type == MetricType.CONFIG_LOAD
        assert metric.preset_name == "production"
        assert metric.operation == "load_preset"
        assert metric.value == duration_ms
        assert metric.session_id == "test-session"
    
    def test_record_config_error(self, metrics_collector):
        """Test recording configuration errors."""
        error_message = "Invalid preset configuration"
        metrics_collector.record_config_error(
            preset_name="invalid",
            operation="load_preset",
            error_message=error_message,
            session_id="test-session"
        )
        
        assert len(metrics_collector.metrics) == 1
        assert len(metrics_collector.alerts) == 1
        
        metric = metrics_collector.metrics[0]
        assert metric.metric_type == MetricType.CONFIG_ERROR
        assert metric.preset_name == "invalid"
        assert metric.operation == "load_preset"
        assert metric.value == 1.0
        assert metric.metadata["error_message"] == error_message
        
        alert = metrics_collector.alerts[0]
        assert alert.level == AlertLevel.ERROR
        assert "Configuration Error" in alert.title
    
    def test_record_config_change(self, metrics_collector):
        """Test recording configuration changes."""
        metrics_collector.record_config_change(
            old_preset="simple",
            new_preset="production",
            operation="change",
            session_id="test-session",
            metadata={"reason": "production_deployment"}
        )
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[0]
        assert metric.metric_type == MetricType.CONFIG_CHANGE
        assert metric.preset_name == "production"
        assert metric.operation == "change"
        assert metric.metadata["old_preset"] == "simple"
        assert metric.metadata["new_preset"] == "production"
        assert metric.metadata["reason"] == "production_deployment"
    
    def test_record_validation_event(self, metrics_collector):
        """Test recording validation events."""
        validation_errors = ["Invalid retry attempts", "Invalid timeout"]
        
        # Test successful validation
        metrics_collector.record_validation_event(
            preset_name="simple",
            is_valid=True,
            operation="validate_preset"
        )
        
        # Test failed validation
        metrics_collector.record_validation_event(
            preset_name="invalid",
            is_valid=False,
            operation="validate_custom",
            validation_errors=validation_errors
        )
        
        assert len(metrics_collector.metrics) == 2
        
        # Check successful validation
        success_metric = metrics_collector.metrics[0]
        assert success_metric.metric_type == MetricType.VALIDATION_EVENT
        assert success_metric.value == 1.0
        assert success_metric.metadata["is_valid"] is True
        
        # Check failed validation
        failed_metric = metrics_collector.metrics[1]
        assert failed_metric.metric_type == MetricType.VALIDATION_EVENT
        assert failed_metric.value == 0.0
        assert failed_metric.metadata["is_valid"] is False
        assert failed_metric.metadata["validation_errors"] == validation_errors
    
    def test_track_config_operation_context_manager(self, metrics_collector):
        """Test the configuration operation tracking context manager."""
        preset_name = "development"
        operation = "test_operation"
        
        # Test successful operation
        with metrics_collector.track_config_operation(
            operation=operation,
            preset_name=preset_name,
            session_id="test-session"
        ):
            time.sleep(0.001)  # Simulate some work
        
        assert len(metrics_collector.metrics) == 1
        metric = metrics_collector.metrics[0]
        assert metric.metric_type == MetricType.CONFIG_LOAD
        assert metric.preset_name == preset_name
        assert metric.operation == operation
        assert metric.value > 0  # Should have some duration
    
    def test_track_config_operation_with_error(self, metrics_collector):
        """Test context manager handles errors correctly."""
        preset_name = "test"
        operation = "failing_operation"
        
        with pytest.raises(ValueError):
            with metrics_collector.track_config_operation(
                operation=operation,
                preset_name=preset_name
            ):
                raise ValueError("Test error")
        
        # Should have recorded an error
        error_metrics = [m for m in metrics_collector.metrics if m.metric_type == MetricType.CONFIG_ERROR]
        assert len(error_metrics) == 1
        assert error_metrics[0].metadata["error_message"] == "Test error"
    
    def test_get_usage_statistics(self, metrics_collector):
        """Test usage statistics calculation."""
        # Add various metrics
        metrics_collector.record_preset_usage("simple", "load")
        metrics_collector.record_preset_usage("simple", "load")
        metrics_collector.record_preset_usage("production", "load")
        metrics_collector.record_config_load("simple", "load", 25.0)
        metrics_collector.record_config_load("production", "load", 75.0)
        metrics_collector.record_config_error("invalid", "load", "Error")
        
        stats = metrics_collector.get_usage_statistics()
        
        assert isinstance(stats, ConfigurationUsageStats)
        assert stats.total_loads == 2
        assert stats.preset_usage_count["simple"] == 2
        assert stats.preset_usage_count["production"] == 1
        assert stats.error_rate == 0.5  # 1 error out of 2 loads
        assert stats.avg_load_time_ms == 50.0  # (25 + 75) / 2
        assert stats.most_used_preset == "simple"
    
    def test_get_usage_statistics_with_time_window(self, metrics_collector):
        """Test usage statistics with time window filtering."""
        # Add old metric (older than time window)
        old_metric = ConfigurationMetric(
            timestamp=datetime.utcnow() - timedelta(hours=25),
            metric_type=MetricType.PRESET_USAGE,
            preset_name="old",
            operation="load",
            value=1.0,
            metadata={}
        )
        metrics_collector._record_metric(old_metric)
        
        # Add recent metric
        metrics_collector.record_preset_usage("recent", "load")
        
        # Get stats for last 24 hours
        stats = metrics_collector.get_usage_statistics(time_window_hours=24)
        
        # Should only include recent metric
        assert "recent" in stats.preset_usage_count
        assert "old" not in stats.preset_usage_count
    
    def test_get_preset_usage_trend(self, metrics_collector):
        """Test preset usage trend analysis."""
        preset_name = "simple"
        
        # Add metrics at different times
        current_time = datetime.utcnow()
        for hour_offset in range(5):
            metric_time = current_time - timedelta(hours=hour_offset)
            metric = ConfigurationMetric(
                timestamp=metric_time,
                metric_type=MetricType.PRESET_USAGE,
                preset_name=preset_name,
                operation="load",
                value=1.0,
                metadata={}
            )
            metrics_collector._record_metric(metric)
        
        trend_data = metrics_collector.get_preset_usage_trend(preset_name, hours=24)
        
        assert len(trend_data) == 24  # 24 hourly buckets
        assert all("timestamp" in point and "usage_count" in point for point in trend_data)
        
        # Should have some non-zero usage counts
        total_usage = sum(point["usage_count"] for point in trend_data)
        assert total_usage == 5  # We added 5 metrics
    
    def test_get_performance_metrics(self, metrics_collector):
        """Test performance metrics calculation."""
        # Add load time metrics
        load_times = [10.0, 20.0, 30.0, 40.0, 100.0]  # Last one should affect p95
        for i, load_time in enumerate(load_times):
            metrics_collector.record_config_load(f"preset_{i}", "load", load_time)
        
        # Add error
        metrics_collector.record_config_error("error_preset", "load", "Error")
        
        performance = metrics_collector.get_performance_metrics()
        
        assert performance["avg_load_time_ms"] == 40.0  # (10+20+30+40+100)/5
        assert performance["min_load_time_ms"] == 10.0
        assert performance["max_load_time_ms"] == 100.0
        assert performance["error_count"] == 1
        assert performance["total_samples"] == 5
        
        # Check p95 calculation
        assert performance["p95_load_time_ms"] == 100.0  # 95th percentile
    
    def test_get_active_alerts(self, metrics_collector):
        """Test getting active alerts."""
        # Generate some alerts
        metrics_collector.record_config_error("error1", "load", "Error 1")
        metrics_collector.record_config_error("error2", "load", "Error 2")
        
        alerts = metrics_collector.get_active_alerts()
        
        assert len(alerts) == 2
        assert all(alert["level"] == "error" for alert in alerts)
        assert any("error1" in alert["title"] for alert in alerts)
        assert any("error2" in alert["title"] for alert in alerts)
    
    def test_get_session_metrics(self, metrics_collector):
        """Test getting session-specific metrics."""
        session_id = "test-session-123"
        
        # Add metrics for specific session
        metrics_collector.record_preset_usage("simple", "load", session_id=session_id)
        metrics_collector.record_config_load("simple", "load", 25.0, session_id=session_id)
        
        # Add metrics for different session
        metrics_collector.record_preset_usage("other", "load", session_id="other-session")
        
        session_metrics = metrics_collector.get_session_metrics(session_id)
        
        assert len(session_metrics) == 2
        assert all(metric["session_id"] == session_id for metric in session_metrics)
    
    def test_clear_old_metrics(self, metrics_collector):
        """Test clearing old metrics."""
        # Add old metrics
        old_time = datetime.utcnow() - timedelta(hours=25)
        old_metric = ConfigurationMetric(
            timestamp=old_time,
            metric_type=MetricType.PRESET_USAGE,
            preset_name="old",
            operation="load",
            value=1.0,
            metadata={}
        )
        metrics_collector._record_metric(old_metric)
        
        # Add old alert
        old_alert = ConfigurationAlert(
            timestamp=old_time,
            level=AlertLevel.INFO,
            title="Old Alert",
            description="Old alert description",
            preset_name="old",
            metric_type=MetricType.CONFIG_ERROR,
            threshold_value=0.0,
            actual_value=1.0,
            metadata={}
        )
        metrics_collector.alerts.append(old_alert)
        
        # Add recent metrics
        metrics_collector.record_preset_usage("recent", "load")
        
        # Clear old metrics (older than 24 hours)
        metrics_collector.clear_old_metrics(hours=24)
        
        # Should only have recent metrics
        assert len(metrics_collector.metrics) == 1
        assert metrics_collector.metrics[0].preset_name == "recent"
        assert len(metrics_collector.alerts) == 0
    
    def test_export_metrics_json(self, metrics_collector):
        """Test exporting metrics in JSON format."""
        # Add some metrics
        metrics_collector.record_preset_usage("simple", "load")
        metrics_collector.record_config_load("simple", "load", 25.0)
        
        # Export as JSON
        exported_json = metrics_collector.export_metrics(format="json")
        
        # Should be valid JSON
        data = json.loads(exported_json)
        assert len(data) == 2
        assert all("metric_type" in metric for metric in data)
        assert all("timestamp" in metric for metric in data)
    
    def test_export_metrics_csv(self, metrics_collector):
        """Test exporting metrics in CSV format."""
        # Add some metrics
        metrics_collector.record_preset_usage("simple", "load")
        metrics_collector.record_config_load("simple", "load", 25.0)
        
        # Export as CSV
        exported_csv = metrics_collector.export_metrics(format="csv")
        
        # Should contain CSV headers and data
        lines = exported_csv.strip().split('\n')
        assert len(lines) >= 3  # Header + 2 data rows
        assert "metric_type" in lines[0]  # Header row
    
    def test_export_metrics_invalid_format(self, metrics_collector):
        """Test export with invalid format raises error."""
        with pytest.raises(ValueError, match="Unsupported export format"):
            metrics_collector.export_metrics(format="xml")
    
    def test_performance_alert_generation(self, metrics_collector):
        """Test automatic generation of performance alerts."""
        # Record slow configuration load (exceeds threshold)
        slow_load_time = 150.0  # Exceeds 100ms threshold
        metrics_collector.record_config_load("slow_preset", "load", slow_load_time)
        
        # Should have generated a performance alert
        performance_alerts = [a for a in metrics_collector.alerts if a.level == AlertLevel.WARNING]
        assert len(performance_alerts) == 1
        
        alert = performance_alerts[0]
        assert "Slow Configuration Load" in alert.title
        assert alert.preset_name == "slow_preset"
        assert alert.actual_value == slow_load_time
        assert alert.threshold_value == 100.0
    
    def test_statistics_caching(self, metrics_collector):
        """Test that statistics are cached for performance."""
        # Add some metrics
        metrics_collector.record_preset_usage("simple", "load")
        
        # First call should calculate and cache
        stats1 = metrics_collector.get_usage_statistics()
        assert metrics_collector._stats_cache is not None
        assert metrics_collector._stats_cache_time is not None
        
        # Second call should use cache
        stats2 = metrics_collector.get_usage_statistics()
        assert stats1 == stats2
        
        # Cache should be invalidated when new metrics are added
        metrics_collector.record_preset_usage("production", "load")
        assert metrics_collector._stats_cache is None
    
    def test_concurrent_access_thread_safety(self, metrics_collector):
        """Test thread safety of metrics collector."""
        import threading
        
        def add_metrics():
            for i in range(10):
                metrics_collector.record_preset_usage(f"preset_{i}", "load")
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=add_metrics)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have all metrics recorded safely
        assert len(metrics_collector.metrics) == 50  # 5 threads * 10 metrics each


class TestConfigurationMetric:
    """Test the ConfigurationMetric data class."""
    
    def test_metric_creation(self):
        """Test creating a configuration metric."""
        timestamp = datetime.utcnow()
        metadata = {"test": "value"}
        
        metric = ConfigurationMetric(
            timestamp=timestamp,
            metric_type=MetricType.PRESET_USAGE,
            preset_name="simple",
            operation="load",
            value=1.0,
            metadata=metadata,
            session_id="test-session",
            user_context="test-user"
        )
        
        assert metric.timestamp == timestamp
        assert metric.metric_type == MetricType.PRESET_USAGE
        assert metric.preset_name == "simple"
        assert metric.operation == "load"
        assert metric.value == 1.0
        assert metric.metadata == metadata
        assert metric.session_id == "test-session"
        assert metric.user_context == "test-user"
    
    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        timestamp = datetime.utcnow()
        metric = ConfigurationMetric(
            timestamp=timestamp,
            metric_type=MetricType.CONFIG_LOAD,
            preset_name="production",
            operation="load",
            value=45.5,
            metadata={"test": "value"}
        )
        
        metric_dict = metric.to_dict()
        
        assert metric_dict["timestamp"] == timestamp.isoformat()
        assert metric_dict["metric_type"] == "config_load"
        assert metric_dict["preset_name"] == "production"
        assert metric_dict["operation"] == "load"
        assert metric_dict["value"] == 45.5
        assert metric_dict["metadata"]["test"] == "value"


class TestConfigurationAlert:
    """Test the ConfigurationAlert data class."""
    
    def test_alert_creation(self):
        """Test creating a configuration alert."""
        timestamp = datetime.utcnow()
        
        alert = ConfigurationAlert(
            timestamp=timestamp,
            level=AlertLevel.ERROR,
            title="Test Alert",
            description="Test alert description",
            preset_name="test",
            metric_type=MetricType.CONFIG_ERROR,
            threshold_value=5.0,
            actual_value=10.0,
            metadata={"test": "value"}
        )
        
        assert alert.timestamp == timestamp
        assert alert.level == AlertLevel.ERROR
        assert alert.title == "Test Alert"
        assert alert.description == "Test alert description"
        assert alert.preset_name == "test"
        assert alert.metric_type == MetricType.CONFIG_ERROR
        assert alert.threshold_value == 5.0
        assert alert.actual_value == 10.0
    
    def test_alert_to_dict(self):
        """Test converting alert to dictionary."""
        timestamp = datetime.utcnow()
        alert = ConfigurationAlert(
            timestamp=timestamp,
            level=AlertLevel.WARNING,
            title="Performance Alert",
            description="Configuration load is slow",
            preset_name="slow",
            metric_type=MetricType.PERFORMANCE_EVENT,
            threshold_value=100.0,
            actual_value=150.0,
            metadata={}
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict["timestamp"] == timestamp.isoformat()
        assert alert_dict["level"] == "warning"
        assert alert_dict["title"] == "Performance Alert"
        assert alert_dict["metric_type"] == "performance_event"
        assert alert_dict["threshold_value"] == 100.0
        assert alert_dict["actual_value"] == 150.0


class TestGlobalMetricsCollector:
    """Test the global metrics collector instance."""
    
    def test_global_instance_available(self):
        """Test that global metrics collector instance is available."""
        from app.config_monitoring import config_metrics_collector
        
        assert isinstance(config_metrics_collector, ConfigurationMetricsCollector)
        assert config_metrics_collector.max_events == 10000
        assert config_metrics_collector.retention_hours == 24
    
    def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        from app.config_monitoring import config_metrics_collector
        
        # Clear any existing metrics for clean test
        config_metrics_collector.metrics.clear()
        config_metrics_collector.alerts.clear()
        
        # Record a metric
        config_metrics_collector.record_preset_usage("test", "load")
        
        # Should be recorded
        assert len(config_metrics_collector.metrics) >= 1
        
        # Clean up
        config_metrics_collector.metrics.clear()
        config_metrics_collector.alerts.clear()


class TestIntegrationWithConfiguration:
    """Test integration with configuration system."""
    
    @patch('app.config_monitoring.config_metrics_collector')
    def test_config_loading_monitoring_integration(self, mock_collector):
        """Test that configuration loading integrates with monitoring."""
        from app.config import Settings
        
        # Create settings with monitoring
        settings = Settings(resilience_preset="simple")
        
        # Call get_resilience_config with monitoring parameters
        config = settings.get_resilience_config(
            session_id="test-session",
            user_context="test-user"
        )
        
        # Should have called monitoring methods
        mock_collector.track_config_operation.assert_called()
        mock_collector.record_preset_usage.assert_called()
        
        # Verify the monitoring calls
        track_call = mock_collector.track_config_operation.call_args
        assert track_call[1]["operation"] == "load_config"
        assert track_call[1]["preset_name"] == "simple"
        assert track_call[1]["session_id"] == "test-session"
        assert track_call[1]["user_context"] == "test-user"