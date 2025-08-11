"""
Comprehensive tests for Performance Monitoring middleware.

Tests cover request timing, memory monitoring, slow request detection,
performance headers, and metrics collection.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.middleware.performance_monitoring import PerformanceMonitoringMiddleware
from app.core.config import Settings


class TestPerformanceMonitoringMiddleware:
    """Test Performance Monitoring middleware functionality."""
    
    @pytest.fixture
    def settings(self):
        """Test settings with performance monitoring configuration."""
        settings = Mock(spec=Settings)
        settings.performance_monitoring_enabled = True
        settings.slow_request_threshold = 100  # 100ms for testing
        settings.memory_monitoring_enabled = True
        settings.metrics_export_enabled = False
        return settings
    
    @pytest.fixture
    def app(self, settings):
        """FastAPI app with performance monitoring middleware."""
        app = FastAPI()
        
        @app.get("/fast")
        async def fast_endpoint():
            return {"message": "fast response"}
        
        @app.get("/slow")
        async def slow_endpoint():
            # Simulate slow processing
            await asyncio.sleep(0.2)  # 200ms - should trigger slow request warning
            return {"message": "slow response"}
        
        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")
        
        @app.post("/upload")
        async def upload_endpoint():
            return {"message": "upload complete"}
        
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        return app
    
    def test_middleware_initialization(self, settings):
        """Test middleware initialization with settings."""
        app = FastAPI()
        middleware = PerformanceMonitoringMiddleware(app, settings)
        
        assert middleware.settings == settings
        assert middleware.slow_request_threshold == 100
        assert middleware.memory_monitoring_enabled is True
    
    def test_middleware_initialization_defaults(self):
        """Test middleware initialization with default values."""
        settings = Mock(spec=Settings)
        # Remove attributes to test defaults
        if hasattr(settings, 'slow_request_threshold'):
            delattr(settings, 'slow_request_threshold')
        if hasattr(settings, 'memory_monitoring_enabled'):
            delattr(settings, 'memory_monitoring_enabled')
        
        app = FastAPI()
        middleware = PerformanceMonitoringMiddleware(app, settings)
        
        # Should use default values
        assert middleware.slow_request_threshold == 1000  # 1000ms default
        assert middleware.memory_monitoring_enabled is True  # True default
    
    def test_performance_headers_added(self, app):
        """Test that performance headers are added to responses."""
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        assert "x-response-time" in response.headers
        
        # Response time should be in milliseconds format
        response_time = response.headers["x-response-time"]
        assert response_time.endswith("ms")
        assert float(response_time[:-2]) >= 0  # Should be non-negative
    
    @patch('psutil.Process')
    def test_memory_monitoring_headers(self, mock_psutil_process, app):
        """Test memory monitoring headers when enabled."""
        # Mock psutil process for memory monitoring
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 1000000  # 1MB
        mock_psutil_process.return_value = mock_process
        
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        assert "x-response-time" in response.headers
        assert "x-memory-delta" in response.headers
        
        # Memory delta should be in bytes format
        memory_delta = response.headers["x-memory-delta"]
        assert memory_delta.endswith("B")
    
    @patch('psutil.Process')
    def test_memory_monitoring_disabled(self, mock_psutil_process):
        """Test when memory monitoring is disabled."""
        settings = Mock(spec=Settings)
        settings.performance_monitoring_enabled = True
        settings.slow_request_threshold = 100
        settings.memory_monitoring_enabled = False
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"message": "test"}
        
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        client = TestClient(app)
        
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "x-response-time" in response.headers
        assert "x-memory-delta" not in response.headers
        
        # psutil should not be called when memory monitoring is disabled
        mock_psutil_process.assert_not_called()
    
    @patch('psutil.Process')
    def test_memory_monitoring_exception_handling(self, mock_psutil_process, app):
        """Test graceful handling of psutil exceptions."""
        # Mock psutil to raise exception
        mock_psutil_process.side_effect = Exception("psutil error")
        
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        assert "x-response-time" in response.headers
        # Should not have memory delta header when psutil fails
        assert "x-memory-delta" not in response.headers
    
    @patch('app.core.middleware.performance_monitoring.logger')
    def test_slow_request_detection(self, mock_logger, app):
        """Test slow request detection and logging."""
        client = TestClient(app)
        
        response = client.get("/slow")
        
        assert response.status_code == 200
        assert "x-response-time" in response.headers
        
        # Should log a warning for slow request
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "Slow request detected" in warning_call
        assert "GET /slow" in warning_call
    
    @patch('app.core.middleware.performance_monitoring.logger')
    def test_fast_request_debug_logging(self, mock_logger, app):
        """Test debug logging for fast requests."""
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        
        # Should log at debug level for fast requests
        mock_logger.debug.assert_called()
        debug_call = mock_logger.debug.call_args[0][0]
        assert "Performance:" in debug_call
        assert "GET /fast" in debug_call
    
    def test_request_id_integration(self, app):
        """Test integration with request ID from request logging."""
        client = TestClient(app)
        
        # Simulate request with state containing request_id
        response = client.get("/fast")
        
        assert response.status_code == 200
        # Response should still work even without request_id in state
        assert "x-response-time" in response.headers
    
    @patch('app.core.middleware.performance_monitoring.logger')
    def test_error_request_performance_logging(self, mock_logger, app):
        """Test performance logging for failed requests."""
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/error")
        
        assert response.status_code == 500
        
        # Should log error with performance info
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args[0][0]
        assert "Performance (failed):" in error_call
        assert "GET /error" in error_call
        assert "ValueError" in error_call
    
    @patch('app.core.middleware.performance_monitoring.logger')
    def test_performance_logging_extra_data(self, mock_logger, app):
        """Test that performance logs include structured extra data."""
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        
        # Check debug log call for structured data
        mock_logger.debug.assert_called()
        _, kwargs = mock_logger.debug.call_args
        extra_data = kwargs.get('extra', {})
        
        assert 'method' in extra_data
        assert 'path' in extra_data
        assert 'duration_ms' in extra_data
        assert 'status_code' in extra_data
        assert extra_data['method'] == 'GET'
        assert extra_data['path'] == '/fast'
        assert extra_data['status_code'] == 200
    
    @patch('psutil.Process')
    @patch('app.core.middleware.performance_monitoring.logger')
    def test_memory_delta_logging(self, mock_logger, mock_psutil_process, app):
        """Test memory delta inclusion in performance logs."""
        # Mock psutil for consistent memory readings
        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 1000000  # 1MB
        mock_psutil_process.return_value = mock_process
        
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        
        # Check that memory delta is included in log extra data
        mock_logger.debug.assert_called()
        _, kwargs = mock_logger.debug.call_args
        extra_data = kwargs.get('extra', {})
        
        assert 'memory_delta_bytes' in extra_data
    
    def test_response_time_accuracy(self, app):
        """Test response time measurement accuracy."""
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get("/fast")
        end_time = time.time()
        
        actual_duration_ms = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        
        # Extract response time from header
        response_time_header = response.headers["x-response-time"]
        reported_duration_ms = float(response_time_header[:-2])  # Remove "ms" suffix
        
        # Response time should be reasonably close to actual duration
        # Allow for some variance due to middleware overhead
        assert abs(reported_duration_ms - actual_duration_ms) < 100  # Within 100ms variance
    
    def test_different_http_methods(self, app):
        """Test performance monitoring across different HTTP methods."""
        client = TestClient(app)
        
        # Test GET request
        get_response = client.get("/fast")
        assert get_response.status_code == 200
        assert "x-response-time" in get_response.headers
        
        # Test POST request
        post_response = client.post("/upload", json={"data": "test"})
        assert post_response.status_code == 200
        assert "x-response-time" in post_response.headers
    
    @patch('app.core.middleware.performance_monitoring.logger')
    def test_slow_request_threshold_boundary(self, mock_logger):
        """Test slow request detection at threshold boundary."""
        settings = Mock(spec=Settings)
        settings.performance_monitoring_enabled = True
        settings.slow_request_threshold = 50  # 50ms threshold
        settings.memory_monitoring_enabled = False
        
        app = FastAPI()
        
        @app.get("/boundary")
        async def boundary_endpoint():
            await asyncio.sleep(0.051)  # Just over threshold
            return {"message": "boundary test"}
        
        app.add_middleware(PerformanceMonitoringMiddleware, settings=settings)
        client = TestClient(app)
        
        response = client.get("/boundary")
        
        assert response.status_code == 200
        
        # Should trigger slow request warning
        mock_logger.warning.assert_called()
    
    def test_concurrent_requests_performance(self, app):
        """Test performance monitoring with concurrent requests."""
        import threading
        
        client = TestClient(app)
        results = []
        
        def make_request():
            response = client.get("/fast")
            results.append(response)
        
        # Make multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should have succeeded with performance headers
        assert len(results) == 5
        for response in results:
            assert response.status_code == 200
            assert "x-response-time" in response.headers
    
    def test_performance_header_format_validation(self, app):
        """Test that performance headers have correct format."""
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        
        # Validate response time format
        response_time = response.headers["x-response-time"]
        assert response_time.endswith("ms")
        
        # Should be able to parse as float
        time_value = float(response_time[:-2])
        assert time_value >= 0
        assert time_value < 10000  # Should be reasonable for a fast endpoint
    
    @patch('psutil.Process')
    def test_memory_delta_calculation(self, mock_psutil_process, app):
        """Test memory delta calculation logic."""
        # Mock different memory readings for start and end
        memory_readings = [1000000, 1050000]  # 1MB to 1.05MB (50KB increase)
        mock_process_instances = []
        
        def create_mock_process(*args, **kwargs):
            mock_process = Mock()
            if memory_readings:
                mock_process.memory_info.return_value.rss = memory_readings.pop(0)
            else:
                mock_process.memory_info.return_value.rss = 1050000  # fallback to end value
            mock_process_instances.append(mock_process)
            return mock_process
        
        mock_psutil_process.side_effect = create_mock_process
        
        client = TestClient(app)
        
        response = client.get("/fast")
        
        assert response.status_code == 200
        
        # Should have memory delta header
        memory_delta = response.headers["x-memory-delta"]
        assert memory_delta.endswith("B")
        
        # Extract and verify delta value
        delta_value = int(memory_delta[:-1])
        assert delta_value == 50000  # 50KB increase
