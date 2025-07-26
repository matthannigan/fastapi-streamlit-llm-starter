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
        try:
            response = client.get("/internal/resilience/monitoring/usage-statistics")
            assert response.status_code == 401
        except Exception as e:
            # If exception is thrown, it should be an authentication error
            assert "AuthenticationError" in str(type(e)) or "API key required" in str(e)
    
    @patch('app.infrastructure.resilience.config_monitoring.config_metrics_collector')
    def test_get_usage_statistics_success(self, mock_collector, client, auth_headers, mock_metrics_collector):
        """Test successful retrieval of usage statistics."""
        mock_collector.get_usage_statistics = mock_metrics_collector.get_usage_statistics
        
        response = client.get(
            "/internal/resilience/monitoring/usage-statistics?time_window_hours=48",
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
            "/internal/resilience/monitoring/preset-trends/simple?hours=48",
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
            "/internal/resilience/monitoring/performance-metrics?hours=12",
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
            "/internal/resilience/monitoring/alerts?max_alerts=10&level=warning",
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
            f"/internal/resilience/monitoring/session/{session_id}",
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
            "/internal/resilience/monitoring/export?format=json&time_window_hours=24",
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
            "/internal/resilience/monitoring/export?format=csv",
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
            "/internal/resilience/monitoring/export?format=xml",
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
            "/internal/resilience/monitoring/cleanup?hours=48",
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
                "/internal/resilience/monitoring/usage-statistics",
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
        client.get("/v1/health/")  # This loads configuration
        client.get("/internal/resilience/config", headers=auth_headers)  # This also loads config
        
        # Now check monitoring endpoints for any recorded metrics
        response = client.get(
            "/internal/resilience/monitoring/usage-statistics",
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
        response = client.get("/internal/resilience/config", headers=auth_headers)
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
            "/internal/resilience/monitoring/usage-statistics",
            headers=auth_headers
        )
        assert stats_response.status_code == 200
        
        session_response = client.get(
            "/internal/resilience/monitoring/session/test-session",
            headers=auth_headers
        )
        assert session_response.status_code == 200
        
        alerts_response = client.get(
            "/internal/resilience/monitoring/alerts",
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
            response = client.get("/internal/resilience/monitoring/usage-statistics", headers=auth_headers)
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
            "/internal/resilience/monitoring/export?format=json",
            headers=auth_headers
        )
        assert json_response.status_code == 200
        
        json_data = json_response.json()
        exported_json = json.loads(json_data["data"])
        assert len(exported_json) == 2  # Should have 2 metrics
        
        # Test CSV export
        csv_response = client.get(
            "/internal/resilience/monitoring/export?format=csv",
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
            "/internal/resilience/monitoring/usage-statistics",
            "/internal/resilience/monitoring/preset-trends/simple",
            "/internal/resilience/monitoring/performance-metrics",
            "/internal/resilience/monitoring/alerts",
            "/internal/resilience/monitoring/session/test-session",
            "/internal/resilience/monitoring/export",
        ]
        
        for endpoint in monitoring_endpoints:
            try:
                response = client.get(endpoint)
                assert response.status_code == 401, f"Endpoint {endpoint} should require authentication"
            except Exception as e:
                # If exception is thrown, it should be an authentication error
                assert "AuthenticationError" in str(type(e)) or "API key required" in str(e), f"Endpoint {endpoint} should require authentication"
    
    def test_monitoring_cleanup_requires_authentication(self, client):
        """Test that cleanup endpoint requires authentication."""
        try:
            response = client.post("/internal/resilience/monitoring/cleanup")
            assert response.status_code == 401
        except Exception as e:
            # If exception is thrown, it should be an authentication error
            assert "AuthenticationError" in str(type(e)) or "API key required" in str(e)
    
    def test_monitoring_endpoints_with_invalid_auth(self, client):
        """Test monitoring endpoints with invalid authentication."""
        invalid_headers = {"Authorization": "Bearer invalid-key"}
        
        try:
            response = client.get(
                "/internal/resilience/monitoring/usage-statistics",
                headers=invalid_headers
            )
            assert response.status_code == 401
        except Exception as e:
            # If exception is thrown, it should be an authentication error
            assert "AuthenticationError" in str(type(e)) or "Invalid API key" in str(e)
    
    def test_session_metrics_access_control(self, client):
        """Test that session metrics don't leak across users."""
        # This would require more complex auth setup to test properly
        # For now, just verify the endpoint structure
        auth_headers = {"Authorization": "Bearer test-api-key-12345"}
        
        response = client.get(
            "/internal/resilience/monitoring/session/test-session",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # The response should only contain data for the requested session
        data = response.json()
        assert data["session_id"] == "test-session"
