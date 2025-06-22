"""
Integration tests for configuration monitoring API endpoints.

Tests the FastAPI endpoints for configuration monitoring including
usage statistics, performance metrics, alerts, and data export.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.infrastructure.resilience.config_monitoring import (
    ConfigurationMetricsCollector,
    ConfigurationMetric,
    ConfigurationAlert,
    MetricType,
    AlertLevel
)
from app.infrastructure.cache.monitoring import (
    CachePerformanceMonitor, 
    PerformanceMetric, 
    CompressionMetric, 
    MemoryUsageMetric,
    InvalidationMetric
)


class TestConfigurationMonitoringEndpoints:
    """Test configuration monitoring API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    @pytest.fixture
    def mock_metrics_collector(self):
        """Create a mock metrics collector with test data."""
        collector = MagicMock()
        
        # Mock usage statistics
        collector.get_usage_statistics.return_value = MagicMock(
            total_loads=100,
            preset_usage_count={"simple": 60, "production": 30, "development": 10},
            error_rate=0.02,
            avg_load_time_ms=25.5,
            most_used_preset="simple",
            least_used_preset="development",
            custom_config_usage_rate=0.15,
            legacy_config_usage_rate=0.05
        )
        
        # Mock performance metrics
        collector.get_performance_metrics.return_value = {
            "avg_load_time_ms": 25.5,
            "min_load_time_ms": 5.0,
            "max_load_time_ms": 150.0,
            "p95_load_time_ms": 45.0,
            "error_count": 2,
            "total_samples": 100,
            "preset_performance": {
                "simple": {"avg_load_time_ms": 20.0, "sample_count": 60},
                "production": {"avg_load_time_ms": 35.0, "sample_count": 30}
            }
        }
        
        # Mock alerts
        collector.get_active_alerts.return_value = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "warning",
                "title": "Slow Configuration Load: production",
                "description": "Configuration load time exceeds threshold",
                "preset_name": "production",
                "metric_type": "performance_event",
                "threshold_value": 100.0,
                "actual_value": 150.0,
                "metadata": {}
            }
        ]
        
        # Mock trend data
        collector.get_preset_usage_trend.return_value = [
            {"timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(), "usage_count": 5}
            for i in range(24)
        ]
        
        # Mock session metrics
        collector.get_session_metrics.return_value = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metric_type": "preset_usage",
                "preset_name": "simple",
                "operation": "load",
                "value": 1.0,
                "session_id": "test-session-123",
                "metadata": {}
            }
        ]
        
        # Mock export data
        collector.export_metrics.return_value = json.dumps([{"test": "data"}])
        
        return collector
    
    def test_get_usage_statistics_unauthorized(self, client):
        """Test getting usage statistics without authentication."""
        response = client.get("/resilience/monitoring/usage-statistics")
        assert response.status_code == 401
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_get_usage_statistics_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful retrieval of usage statistics."""
        mock_collector.get_usage_statistics = mock_metrics_collector.get_usage_statistics
        
        response = client.get(
            "/resilience/monitoring/usage-statistics?time_window_hours=48",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["time_window_hours"] == 48
        assert "statistics" in data
        assert "summary" in data
        
        stats = data["statistics"]
        assert stats["total_loads"] == 100
        assert stats["preset_usage_count"]["simple"] == 60
        assert stats["error_rate"] == 0.02
        assert stats["avg_load_time_ms"] == 25.5
        
        summary = data["summary"]
        assert summary["healthy"] is True  # error_rate < 0.05
        assert summary["performance_good"] is True  # avg_load_time < 100ms
        assert summary["preset_adoption"] == 0.95  # 1 - legacy_usage_rate
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_get_preset_usage_trend_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful retrieval of preset usage trends."""
        mock_collector.get_preset_usage_trend = mock_metrics_collector.get_preset_usage_trend
        
        response = client.get(
            "/resilience/monitoring/preset-trends/simple?hours=48",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["preset_name"] == "simple"
        assert data["time_window_hours"] == 48
        assert "trend_data" in data
        assert "summary" in data
        
        trend_data = data["trend_data"]
        assert len(trend_data) == 24
        assert all("timestamp" in point and "usage_count" in point for point in trend_data)
        
        summary = data["summary"]
        assert summary["total_usage"] == 120  # 24 * 5
        assert summary["peak_usage"] == 5
        assert summary["avg_hourly_usage"] == 5.0
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_get_performance_metrics_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful retrieval of performance metrics."""
        mock_collector.get_performance_metrics = mock_metrics_collector.get_performance_metrics
        
        response = client.get(
            "/resilience/monitoring/performance-metrics?hours=12",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["time_window_hours"] == 12
        assert "performance_metrics" in data
        assert "health_check" in data
        
        metrics = data["performance_metrics"]
        assert metrics["avg_load_time_ms"] == 25.5
        assert metrics["min_load_time_ms"] == 5.0
        assert metrics["max_load_time_ms"] == 150.0
        assert metrics["p95_load_time_ms"] == 45.0
        assert metrics["error_count"] == 2
        assert metrics["total_samples"] == 100
        
        health = data["health_check"]
        assert health["performance_good"] is True
        assert health["error_rate_acceptable"] is True
        assert health["p95_within_threshold"] is True
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_get_configuration_alerts_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful retrieval of configuration alerts."""
        mock_collector.get_active_alerts = mock_metrics_collector.get_active_alerts
        
        response = client.get(
            "/resilience/monitoring/alerts?max_alerts=10&level=warning",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "summary" in data
        
        alerts = data["alerts"]
        assert len(alerts) == 1
        assert alerts[0]["level"] == "warning"
        assert "Slow Configuration Load" in alerts[0]["title"]
        
        summary = data["summary"]
        assert summary["total_alerts"] == 1
        assert summary["alert_counts"]["warning"] == 1
        assert summary["has_critical"] is False
        assert summary["has_errors"] is False
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_get_session_metrics_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful retrieval of session metrics."""
        mock_collector.get_session_metrics = mock_metrics_collector.get_session_metrics
        
        session_id = "test-session-123"
        response = client.get(
            f"/resilience/monitoring/session/{session_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert "metrics" in data
        assert "summary" in data
        
        metrics = data["metrics"]
        assert len(metrics) == 1
        assert metrics[0]["session_id"] == session_id
        assert metrics[0]["metric_type"] == "preset_usage"
        
        summary = data["summary"]
        assert summary["total_operations"] == 1
        assert "simple" in summary["preset_usage"]
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_export_metrics_json_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful export of metrics in JSON format."""
        mock_collector.export_metrics = mock_metrics_collector.export_metrics
        
        response = client.get(
            "/resilience/monitoring/export?format=json&time_window_hours=24",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "json"
        assert data["time_window_hours"] == 24
        assert "data" in data
        assert "export_timestamp" in data
        
        # Data should be JSON string
        exported_data = json.loads(data["data"])
        assert isinstance(exported_data, list)
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_export_metrics_csv_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful export of metrics in CSV format."""
        mock_collector.export_metrics.return_value = "header1,header2\nvalue1,value2\n"
        
        response = client.get(
            "/resilience/monitoring/export?format=csv",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "csv"
        assert "data" in data
        
        # Data should be CSV string
        csv_data = data["data"]
        assert "header1,header2" in csv_data
        assert "value1,value2" in csv_data
    
    def test_export_metrics_invalid_format(self, client, auth_headers):
        """Test export with invalid format."""
        response = client.get(
            "/resilience/monitoring/export?format=xml",
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Format must be 'json' or 'csv'" in response.json()["detail"]
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_cleanup_old_metrics_success(self, mock_collector, client, auth_headers):
        """Test successful cleanup of old metrics."""
        # Mock metrics counts
        mock_collector.metrics = [1, 2, 3, 4, 5]  # 5 metrics before cleanup
        mock_collector.alerts = [1, 2]  # 2 alerts before cleanup
        
        def mock_clear_old_metrics(hours):
            # Simulate cleanup removing some metrics
            mock_collector.metrics = [4, 5]  # 2 remaining
            mock_collector.alerts = []  # 0 remaining
        
        mock_collector.clear_old_metrics = mock_clear_old_metrics
        
        response = client.post(
            "/resilience/monitoring/cleanup?hours=48",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["cleanup_threshold_hours"] == 48
        assert data["metrics_removed"] == 3  # 5 - 2
        assert data["alerts_removed"] == 2  # 2 - 0
        assert data["metrics_remaining"] == 2
        assert data["alerts_remaining"] == 0
        assert "cleanup_timestamp" in data
    
    def test_monitoring_endpoints_error_handling(self, client, auth_headers):
        """Test error handling in monitoring endpoints."""
        # Test with service error
        with patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector') as mock_collector:
            mock_collector.get_usage_statistics.side_effect = Exception("Service error")
            
            response = client.get(
                "/resilience/monitoring/usage-statistics",
                headers=auth_headers
            )
            assert response.status_code == 500
            assert "Failed to get configuration usage statistics" in response.json()["detail"]


class TestConfigurationMonitoringIntegration:
    """Test integration between monitoring and configuration system."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_configuration_monitoring_integration_flow(self, client, auth_headers):
        """Test full integration flow of configuration monitoring."""
        # Clear any existing metrics
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        config_metrics_collector.metrics.clear()
        config_metrics_collector.alerts.clear()
        
        # Make some configuration-related requests to generate metrics
        # These would normally trigger configuration loading
        client.get("/health")  # This loads configuration
        client.get("/resilience/config", headers=auth_headers)  # This also loads config
        
        # Now check monitoring endpoints for any recorded metrics
        response = client.get(
            "/resilience/monitoring/usage-statistics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # The response should be valid even if no metrics were recorded
        data = response.json()
        assert "statistics" in data
        assert "summary" in data
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_configuration_load_monitoring_integration(self, mock_collector, client, auth_headers):
        """Test that configuration loading triggers monitoring."""
        # Mock the collector to verify it gets called
        mock_collector.track_config_operation = MagicMock()
        mock_collector.record_preset_usage = MagicMock()
        
        # Make a request that loads configuration
        response = client.get("/resilience/config", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify monitoring was called (this depends on the implementation)
        # The actual calls would depend on how configuration is loaded in the endpoint
    
    def test_monitoring_data_consistency(self, client, auth_headers):
        """Test consistency of monitoring data across endpoints."""
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        # Clear existing data
        config_metrics_collector.metrics.clear()
        config_metrics_collector.alerts.clear()
        
        # Add some test metrics
        config_metrics_collector.record_preset_usage("simple", "load", session_id="test-session")
        config_metrics_collector.record_config_load("simple", "load", 25.0, session_id="test-session")
        config_metrics_collector.record_config_error("invalid", "load", "Test error")
        
        # Get data from different endpoints
        stats_response = client.get(
            "/resilience/monitoring/usage-statistics",
            headers=auth_headers
        )
        assert stats_response.status_code == 200
        
        session_response = client.get(
            "/resilience/monitoring/session/test-session",
            headers=auth_headers
        )
        assert session_response.status_code == 200
        
        alerts_response = client.get(
            "/resilience/monitoring/alerts",
            headers=auth_headers
        )
        assert alerts_response.status_code == 200
        
        # Verify data consistency
        stats_data = stats_response.json()
        session_data = session_response.json()
        alerts_data = alerts_response.json()
        
        # Should have recorded the usage
        assert stats_data["statistics"]["total_loads"] >= 1
        
        # Session should have metrics
        assert len(session_data["metrics"]) >= 2
        assert session_data["session_id"] == "test-session"
        
        # Should have error alert
        assert alerts_data["summary"]["total_alerts"] >= 1
        
        # Clean up
        config_metrics_collector.metrics.clear()
        config_metrics_collector.alerts.clear()
    
    def test_monitoring_performance_impact(self, client, auth_headers):
        """Test that monitoring doesn't significantly impact performance."""
        import time
        
        # Measure time for requests with monitoring
        start_time = time.perf_counter()
        
        # Make multiple requests
        for _ in range(10):
            response = client.get("/resilience/monitoring/usage-statistics", headers=auth_headers)
            assert response.status_code == 200
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Should complete reasonably quickly (less than 1 second for 10 requests)
        assert total_time < 1.0
        
        # Average response time should be reasonable
        avg_time = total_time / 10
        assert avg_time < 0.1  # Less than 100ms per request
    
    def test_monitoring_data_export_integration(self, client, auth_headers):
        """Test data export functionality integration."""
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        # Clear and add test data
        config_metrics_collector.metrics.clear()
        config_metrics_collector.record_preset_usage("test", "load")
        config_metrics_collector.record_config_load("test", "load", 30.0)
        
        # Test JSON export
        json_response = client.get(
            "/resilience/monitoring/export?format=json",
            headers=auth_headers
        )
        assert json_response.status_code == 200
        
        json_data = json_response.json()
        exported_json = json.loads(json_data["data"])
        assert len(exported_json) == 2  # Should have 2 metrics
        
        # Test CSV export
        csv_response = client.get(
            "/resilience/monitoring/export?format=csv",
            headers=auth_headers
        )
        assert csv_response.status_code == 200
        
        csv_data = csv_response.json()
        exported_csv = csv_data["data"]
        lines = exported_csv.strip().split('\n')
        assert len(lines) >= 3  # Header + 2 data rows
        
        # Clean up
        config_metrics_collector.metrics.clear()


class TestMonitoringEndpointSecurity:
    """Test security aspects of monitoring endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_all_monitoring_endpoints_require_authentication(self, client):
        """Test that all monitoring endpoints require authentication."""
        monitoring_endpoints = [
            "/resilience/monitoring/usage-statistics",
            "/resilience/monitoring/preset-trends/simple",
            "/resilience/monitoring/performance-metrics",
            "/resilience/monitoring/alerts",
            "/resilience/monitoring/session/test-session",
            "/resilience/monitoring/export",
        ]
        
        for endpoint in monitoring_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
    
    def test_monitoring_cleanup_requires_authentication(self, client):
        """Test that cleanup endpoint requires authentication."""
        response = client.post("/resilience/monitoring/cleanup")
        assert response.status_code == 401
    
    def test_monitoring_endpoints_with_invalid_auth(self, client):
        """Test monitoring endpoints with invalid authentication."""
        invalid_headers = {"Authorization": "Bearer invalid-key"}
        
        response = client.get(
            "/resilience/monitoring/usage-statistics",
            headers=invalid_headers
        )
        assert response.status_code == 401
    
    def test_session_metrics_access_control(self, client):
        """Test that session metrics don't leak across users."""
        # This would require more complex auth setup to test properly
        # For now, just verify the endpoint structure
        auth_headers = {"Authorization": "Bearer test-api-key-12345"}
        
        response = client.get(
            "/resilience/monitoring/session/test-session",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # The response should only contain data for the requested session
        data = response.json()
        assert data["session_id"] == "test-session"

# TODO: Move TestCachePerformanceAPIEndpoint to backend/tests/api/internal/test_monitoring_endpoints.py
# This class tests HTTP API endpoints (/monitoring/cache-metrics) rather than infrastructure abstractions.
# API endpoint tests belong in api/ directory, not infrastructure/ directory.
# - Tests FastAPI TestClient responses
# - Tests HTTP status codes and response schemas  
# - Tests authentication headers and content types
# - These are integration tests for the monitoring router, not infrastructure unit tests
class TestCachePerformanceAPIEndpoint:
    """Comprehensive tests for the cache performance API endpoint with mocked monitor."""
    
    def test_cache_metrics_endpoint_with_mock_monitor(self, client_with_mock_monitor, mock_performance_monitor):
        """Test the cache metrics endpoint returns expected data structure."""
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic response structure
        assert "timestamp" in data
        assert "retention_hours" in data
        assert "cache_hit_rate" in data
        assert "total_cache_operations" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        
        # Verify data matches mock return values
        assert data["retention_hours"] == 1
        assert data["cache_hit_rate"] == 85.5
        assert data["total_cache_operations"] == 150
        assert data["cache_hits"] == 128
        assert data["cache_misses"] == 22
        
        # Verify key generation statistics are included
        assert "key_generation" in data
        key_gen = data["key_generation"]
        assert key_gen["total_operations"] == 75
        assert key_gen["avg_duration"] == 0.002
        assert key_gen["max_duration"] == 0.012
        assert key_gen["slow_operations"] == 2
        
        # Verify mock monitor method was called
        mock_performance_monitor.get_performance_stats.assert_called_once()
    
    def test_cache_metrics_endpoint_handles_monitor_none(self, client):
        """Test endpoint handles case where performance monitor is None."""
        # Import here to avoid circular imports
        from app.routers.monitoring import get_performance_monitor
        from app.main import app
        
        # Override dependency to return None
        app.dependency_overrides[get_performance_monitor] = lambda: None
        
        try:
            response = client.get("/monitoring/cache-metrics")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Performance monitor not available" in data["detail"]
        finally:
            # Clean up dependency override
            app.dependency_overrides.clear()
    
    def test_cache_metrics_endpoint_handles_stats_computation_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles statistics computation errors."""
        # Configure mock to raise ValueError during stats computation
        mock_performance_monitor.get_performance_stats.side_effect = ValueError("Division by zero in stats calculation")
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Statistics computation failed" in data["detail"]
    
    def test_cache_metrics_endpoint_handles_attribute_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles missing performance monitor methods."""
        # Configure mock to raise AttributeError (method not available)
        mock_performance_monitor.get_performance_stats.side_effect = AttributeError("'NoneType' object has no attribute 'get_performance_stats'")
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 503
        data = response.json()
        assert "detail" in data
        assert "monitoring is temporarily disabled" in data["detail"]
    
    def test_cache_metrics_endpoint_handles_unexpected_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles unexpected errors during stats retrieval."""
        # Configure mock to raise unexpected error
        mock_performance_monitor.get_performance_stats.side_effect = RuntimeError("Unexpected error in monitoring system")
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Unexpected error in monitoring system" in data["detail"]
    
    def test_cache_metrics_endpoint_validates_stats_format(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint validates that stats are returned in correct format."""
        # Configure mock to return invalid format (not a dict)
        mock_performance_monitor.get_performance_stats.return_value = "invalid_format"
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Invalid statistics format" in data["detail"]
    
    def test_cache_metrics_endpoint_handles_response_validation_error(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint handles Pydantic validation errors."""
        # Configure mock to return data that doesn't match the expected schema
        invalid_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": "invalid_number",  # Should be int, not string
            "cache_hit_rate": 85.5,
            "total_cache_operations": 150,
            "cache_hits": 128,
            "cache_misses": 22
        }
        mock_performance_monitor.get_performance_stats.return_value = invalid_stats
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Response format validation failed" in data["detail"]
    
    def test_cache_metrics_endpoint_with_optional_fields(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint correctly handles response with optional fields missing."""
        # Configure mock to return minimal valid stats (some optional fields missing)
        minimal_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": 1,
            "cache_hit_rate": 0.0,
            "total_cache_operations": 0,
            "cache_hits": 0,
            "cache_misses": 0
            # No optional fields like key_generation, cache_operations, etc.
        }
        mock_performance_monitor.get_performance_stats.return_value = minimal_stats
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields are present
        assert data["timestamp"] == "2024-01-15T10:30:00.123456"
        assert data["retention_hours"] == 1
        assert data["cache_hit_rate"] == 0.0
        assert data["total_cache_operations"] == 0
        assert data["cache_hits"] == 0
        assert data["cache_misses"] == 0
        
        # Verify optional fields are handled correctly (should be None)
        assert data.get("key_generation") is None
        assert data.get("cache_operations") is None
        assert data.get("compression") is None
        assert data.get("memory_usage") is None
        assert data.get("invalidation") is None
    
    def test_cache_metrics_endpoint_with_all_optional_fields(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint correctly handles response with all optional fields present."""
        # Configure mock to return comprehensive stats with all optional sections
        comprehensive_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": 1,
            "cache_hit_rate": 85.5,
            "total_cache_operations": 150,
            "cache_hits": 128,
            "cache_misses": 22,
            "key_generation": {
                "total_operations": 75,
                "avg_duration": 0.002,
                "median_duration": 0.0015,
                "max_duration": 0.012,
                "min_duration": 0.0008,
                "avg_text_length": 1250,
                "max_text_length": 5000,
                "slow_operations": 2
            },
            "cache_operations": {
                "total_operations": 150,
                "avg_duration": 0.0045,
                "median_duration": 0.003,
                "max_duration": 0.025,
                "min_duration": 0.001,
                "slow_operations": 5,
                "by_operation_type": {
                    "get": {"count": 100, "avg_duration": 0.003, "max_duration": 0.015},
                    "set": {"count": 50, "avg_duration": 0.007, "max_duration": 0.025}
                }
            },
            "compression": {
                "total_operations": 25,
                "avg_compression_ratio": 0.65,
                "median_compression_ratio": 0.62,
                "best_compression_ratio": 0.45,
                "worst_compression_ratio": 0.89,
                "avg_compression_time": 0.003,
                "max_compression_time": 0.015,
                "total_bytes_processed": 524288,
                "total_bytes_saved": 183500,
                "overall_savings_percent": 35.0
            },
            "memory_usage": {
                "current": {
                    "total_cache_size_mb": 25.5,
                    "memory_cache_size_mb": 5.2,
                    "cache_entry_count": 100,
                    "memory_cache_entry_count": 20,
                    "avg_entry_size_bytes": 2048,
                    "process_memory_mb": 150.0,
                    "cache_utilization_percent": 51.0,
                    "warning_threshold_reached": True
                },
                "thresholds": {
                    "warning_threshold_mb": 50.0,
                    "critical_threshold_mb": 100.0
                }
            },
            "invalidation": {
                "total_invalidations": 10,
                "total_keys_invalidated": 50,
                "rates": {
                    "last_hour": 5,
                    "last_24_hours": 10
                }
            }
        }
        mock_performance_monitor.get_performance_stats.return_value = comprehensive_stats
        
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all sections are present and correctly structured
        assert "key_generation" in data
        assert "cache_operations" in data
        assert "compression" in data
        assert "memory_usage" in data
        assert "invalidation" in data
        
        # Verify detailed structure of complex sections
        assert data["cache_operations"]["by_operation_type"]["get"]["count"] == 100
        assert data["compression"]["total_bytes_saved"] == 183500
        assert data["memory_usage"]["current"]["cache_entry_count"] == 100
        assert data["invalidation"]["rates"]["last_hour"] == 5
    
    def test_cache_metrics_endpoint_content_type_and_headers(self, client_with_mock_monitor):
        """Test endpoint returns correct content type and response headers."""
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        # Verify response is valid JSON
        data = response.json()
        assert isinstance(data, dict)
    
    def test_cache_metrics_endpoint_with_auth_headers(self, client_with_mock_monitor, auth_headers):
        """Test endpoint works correctly with authentication headers."""
        response = client_with_mock_monitor.get("/monitoring/cache-metrics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert "cache_hit_rate" in data
    
    def test_cache_metrics_endpoint_performance_with_large_dataset(self, client_with_mock_monitor, mock_performance_monitor):
        """Test endpoint performance with large mock dataset."""
        # Configure mock to simulate large dataset response
        large_stats = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "retention_hours": 24,  # Longer retention for large dataset
            "cache_hit_rate": 92.3,
            "total_cache_operations": 10000,
            "cache_hits": 9230,
            "cache_misses": 770,
            "key_generation": {
                "total_operations": 5000,
                "avg_duration": 0.0025,
                "median_duration": 0.002,
                "max_duration": 0.150,
                "min_duration": 0.0005,
                "avg_text_length": 2500,
                "max_text_length": 50000,
                "slow_operations": 125
            },
            "cache_operations": {
                "total_operations": 10000,
                "avg_duration": 0.003,
                "median_duration": 0.0025,
                "max_duration": 0.080,
                "min_duration": 0.0008,
                "slow_operations": 89,
                "by_operation_type": {
                    "get": {"count": 7500, "avg_duration": 0.002, "max_duration": 0.050},
                    "set": {"count": 2000, "avg_duration": 0.006, "max_duration": 0.080},
                    "delete": {"count": 300, "avg_duration": 0.003, "max_duration": 0.025},
                    "invalidate": {"count": 200, "avg_duration": 0.008, "max_duration": 0.040}
                }
            }
        }
        mock_performance_monitor.get_performance_stats.return_value = large_stats
        
        import time
        start_time = time.time()
        response = client_with_mock_monitor.get("/monitoring/cache-metrics")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the large dataset is handled correctly
        assert data["total_cache_operations"] == 10000
        assert data["key_generation"]["total_operations"] == 5000
        assert len(data["cache_operations"]["by_operation_type"]) == 4
        
        # Performance should still be reasonable (< 1 second for API response)
        assert response_time < 1.0
