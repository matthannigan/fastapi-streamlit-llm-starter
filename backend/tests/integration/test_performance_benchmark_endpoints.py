"""
Integration tests for performance benchmark API endpoints.

Tests the FastAPI endpoints for running performance benchmarks,
getting performance reports, and accessing performance metrics.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestPerformanceBenchmarkEndpoints:
    """Test performance benchmark API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_get_performance_thresholds(self, client):
        """Test getting performance thresholds endpoint."""
        response = client.get("/resilience/performance/thresholds")
        assert response.status_code == 200
        
        data = response.json()
        assert "thresholds" in data
        assert "targets" in data
        assert "measurement_info" in data
        
        thresholds = data["thresholds"]
        assert "config_loading_ms" in thresholds
        assert "preset_access_ms" in thresholds
        assert "validation_ms" in thresholds
        assert "service_initialization_ms" in thresholds
        
        # Verify threshold values match our targets
        assert thresholds["config_loading_ms"] == 100.0
        assert thresholds["preset_access_ms"] == 10.0
        assert thresholds["validation_ms"] == 50.0
        assert thresholds["service_initialization_ms"] == 200.0
    
    def test_run_performance_benchmark_unauthorized(self, client):
        """Test running benchmark without authentication."""
        response = client.get("/resilience/performance/benchmark")
        assert response.status_code == 401
    
    def test_run_performance_benchmark_authorized(self, client, auth_headers):
        """Test running performance benchmark with authentication."""
        # Use minimal iterations for speed
        response = client.get(
            "/resilience/performance/benchmark?iterations=3",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "benchmark_suite" in data
        assert "summary" in data
        
        summary = data["summary"]
        assert "total_benchmarks" in summary
        assert "pass_rate" in summary
        assert "total_duration_ms" in summary
        assert "performance_target_met" in summary
        
        # Should have 7 different benchmarks
        assert summary["total_benchmarks"] == 7
        assert summary["pass_rate"] >= 0.0
        assert summary["total_duration_ms"] > 0
    
    def test_run_custom_performance_benchmark(self, client, auth_headers):
        """Test running custom performance benchmark."""
        request_data = {
            "iterations": 3,
            "include_slow": False,
            "operations": ["preset_loading", "settings_initialization"]
        }
        
        response = client.post(
            "/resilience/performance/benchmark",
            json=request_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert "summary" in data
        
        results = data["results"]
        assert len(results) == 2  # Only requested operations
        
        # Check result structure
        for result in results:
            assert "operation" in result
            assert "avg_duration_ms" in result
            assert "min_duration_ms" in result
            assert "max_duration_ms" in result
            assert "success_rate" in result
            assert "iterations" in result
            assert result["iterations"] == 3
    
    def test_run_custom_benchmark_invalid_operation(self, client, auth_headers):
        """Test running custom benchmark with invalid operation."""
        request_data = {
            "iterations": 3,
            "operations": ["invalid_operation"]
        }
        
        response = client.post(
            "/resilience/performance/benchmark",
            json=request_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Unknown benchmark operation" in response.json()["detail"]
    
    def test_get_performance_report_json(self, client, auth_headers):
        """Test getting performance report in JSON format."""
        # First run a benchmark to have data
        client.get(
            "/resilience/performance/benchmark?iterations=2",
            headers=auth_headers
        )
        
        # Then get the report
        response = client.get(
            "/resilience/performance/report?format=json",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "json"
        assert "suite" in data
        assert "analysis" in data
        
        analysis = data["analysis"]
        assert "performance_summary" in analysis
        assert "recommendations" in analysis
    
    def test_get_performance_report_text(self, client, auth_headers):
        """Test getting performance report in text format."""
        # First run a benchmark to have data
        client.get(
            "/resilience/performance/benchmark?iterations=2",
            headers=auth_headers
        )
        
        # Then get the report
        response = client.get(
            "/resilience/performance/report?format=text",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["format"] == "text"
        assert "report" in data
        assert "timestamp" in data
        
        report_text = data["report"]
        assert "RESILIENCE CONFIGURATION PERFORMANCE REPORT" in report_text
        assert "Performance Results:" in report_text
    
    def test_get_performance_history(self, client, auth_headers):
        """Test getting performance history."""
        response = client.get(
            "/resilience/performance/history?limit=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "expected_features" in data
        assert "current_results" in data
        
        # Since history is not fully implemented yet
        assert "Performance history tracking not yet implemented" in data["message"]
    
    @pytest.mark.slow
    def test_comprehensive_benchmark_performance_validation(self, client, auth_headers):
        """Test comprehensive benchmark to validate actual performance."""
        response = client.get(
            "/resilience/performance/benchmark?iterations=10",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        benchmark_suite = data["benchmark_suite"]
        results = benchmark_suite["results"]
        
        # Validate performance targets are met
        for result in results:
            operation = result["operation"]
            avg_duration = result["avg_duration_ms"]
            
            # All operations should complete quickly
            assert avg_duration < 100.0, f"{operation} took {avg_duration}ms (>100ms limit)"
            
            # Specific performance requirements
            if operation == "preset_loading":
                assert avg_duration < 10.0, f"Preset loading too slow: {avg_duration}ms"
            elif operation in ["settings_initialization", "resilience_config_loading"]:
                assert avg_duration < 100.0, f"Config loading too slow: {avg_duration}ms"
            elif operation == "validation_performance":
                assert avg_duration < 50.0, f"Validation too slow: {avg_duration}ms"
            elif operation == "service_initialization":
                assert avg_duration < 200.0, f"Service initialization too slow: {avg_duration}ms"
            
            # All operations should succeed
            assert result["success_rate"] == 1.0, f"{operation} had failures: {result['success_rate']}"
        
        # Overall performance should meet targets
        summary = data["summary"]
        assert summary["performance_target_met"] is True, "Overall performance target not met"
        assert summary["pass_rate"] >= 0.8, f"Pass rate too low: {summary['pass_rate']}"


class TestPerformanceBenchmarkErrorHandling:
    """Test error handling in performance benchmark endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_benchmark_with_service_error(self, client, auth_headers):
        """Test benchmark handling when underlying services fail."""
        with patch('app.performance_benchmarks.performance_benchmark.run_comprehensive_benchmark') as mock_benchmark:
            mock_benchmark.side_effect = Exception("Service error")
            
            response = client.get(
                "/resilience/performance/benchmark",
                headers=auth_headers
            )
            assert response.status_code == 500
            assert "Failed to run performance benchmark" in response.json()["detail"]
    
    def test_performance_report_with_no_data(self, client, auth_headers):
        """Test performance report when no benchmark data exists."""
        # Clear any existing results
        with patch('app.performance_benchmarks.performance_benchmark.results', []):
            response = client.get(
                "/resilience/performance/report",
                headers=auth_headers
            )
            # Should run a quick benchmark if no data exists
            assert response.status_code == 200


class TestPerformanceBenchmarkIntegration:
    """Test integration of performance benchmarks with configuration system."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test-api-key-12345"}
    
    def test_benchmark_reflects_actual_configuration_performance(self, client, auth_headers):
        """Test that benchmarks reflect actual configuration loading performance."""
        # Run benchmark
        response = client.get(
            "/resilience/performance/benchmark?iterations=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        results = data["benchmark_suite"]["results"]
        
        # Find config loading result
        config_result = next(
            (r for r in results if r["operation"] == "resilience_config_loading"),
            None
        )
        assert config_result is not None
        
        # Performance should be realistic for actual usage
        assert config_result["avg_duration_ms"] < 50.0  # Should be very fast
        assert config_result["success_rate"] == 1.0
        
        # Memory usage should be reasonable
        assert config_result["memory_peak_mb"] < 20.0  # Should use minimal memory
    
    def test_benchmark_validation_matches_real_validation(self, client, auth_headers):
        """Test that validation benchmarks match real validation performance."""
        # Test custom benchmark for validation
        request_data = {
            "iterations": 5,
            "operations": ["validation_performance"]
        }
        
        response = client.post(
            "/resilience/performance/benchmark",
            json=request_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        validation_result = data["results"][0]
        
        # Validation should be fast
        assert validation_result["avg_duration_ms"] < 25.0
        assert validation_result["success_rate"] == 1.0
        
        # Metadata should show successful validations
        metadata = validation_result["metadata"]
        assert "config_0_valid" in metadata
        assert "config_1_valid" in metadata
        assert "config_2_valid" in metadata