"""
Unit tests for performance benchmarking system.

Tests the performance benchmarking functionality including timing accuracy,
memory measurement, threshold validation, and comprehensive reporting.
"""

import pytest
import json
import os
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from app.performance_benchmarks import (
    ConfigurationPerformanceBenchmark,
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceThreshold,
    performance_benchmark
)


class TestConfigurationPerformanceBenchmark:
    """Test the ConfigurationPerformanceBenchmark class."""
    
    def test_benchmark_initialization(self):
        """Test benchmark system initializes correctly."""
        benchmark = ConfigurationPerformanceBenchmark()
        assert benchmark.results == []
        assert benchmark.baseline_results == {}
    
    def test_measure_performance_function(self):
        """Test the measure_performance function."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        def test_operation(metadata):
            # Simulate some work
            time.sleep(0.001)  # 1ms
            metadata["test_key"] = "test_value"
        
        result = benchmark.measure_performance("test_operation", test_operation, iterations=3)
        
        # Verify result was recorded
        assert len(benchmark.results) == 1
        assert result.operation == "test_operation"
        assert result.iterations == 3
        assert result.avg_duration_ms > 0
        assert result.success_rate == 1.0
        assert "test_key" in result.metadata
        assert result.metadata["test_key"] == "test_value"
    
    def test_benchmark_preset_loading_performance(self):
        """Test preset loading benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_preset_loading(iterations=5)
        
        assert result.operation == "preset_loading"
        assert result.iterations == 5
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.PRESET_ACCESS.value  # <10ms
        
        # Check that all presets were loaded
        assert "preset_simple_loaded" in result.metadata
        assert "preset_development_loaded" in result.metadata
        assert "preset_production_loaded" in result.metadata
    
    def test_benchmark_settings_initialization_performance(self):
        """Test Settings initialization benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_settings_initialization(iterations=5)
        
        assert result.operation == "settings_initialization"
        assert result.iterations == 5
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.CONFIG_LOADING.value  # <100ms
        
        # Check that all preset settings were initialized
        assert "settings_simple_initialized" in result.metadata
        assert "settings_development_initialized" in result.metadata
        assert "settings_production_initialized" in result.metadata
    
    def test_benchmark_resilience_config_loading_performance(self):
        """Test resilience configuration loading benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_resilience_config_loading(iterations=5)
        
        assert result.operation == "resilience_config_loading"
        assert result.iterations == 5
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.CONFIG_LOADING.value  # <100ms
        
        # Check that all configurations were loaded
        assert "config_simple_loaded" in result.metadata
        assert "config_development_loaded" in result.metadata
        assert "config_production_loaded" in result.metadata
    
    def test_benchmark_service_initialization_performance(self):
        """Test AIServiceResilience initialization benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_service_initialization(iterations=3)
        
        assert result.operation == "service_initialization"
        assert result.iterations == 3
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.SERVICE_INIT.value  # <200ms
        
        # Check that services and operation configs were initialized
        presets = ["simple", "development", "production"]
        operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        
        for preset in presets:
            for operation in operations:
                key = f"service_{preset}_{operation}_config"
                assert key in result.metadata
                assert result.metadata[key] is True
    
    def test_benchmark_custom_config_loading_performance(self):
        """Test custom configuration loading benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_custom_config_loading(iterations=5)
        
        assert result.operation == "custom_config_loading"
        assert result.iterations == 5
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.CONFIG_LOADING.value  # <100ms
        
        # Check that custom configurations were loaded
        assert "custom_config_0_loaded" in result.metadata
        assert "custom_config_1_loaded" in result.metadata
        assert "custom_config_2_loaded" in result.metadata
    
    def test_benchmark_legacy_config_loading_performance(self):
        """Test legacy configuration loading benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_legacy_config_loading(iterations=5)
        
        assert result.operation == "legacy_config_loading"
        assert result.iterations == 5
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.CONFIG_LOADING.value  # <100ms
        
        # Check that legacy configurations were loaded and detected
        assert "legacy_config_0_loaded" in result.metadata
        assert "legacy_config_0_detected" in result.metadata
        assert "legacy_config_1_loaded" in result.metadata
        assert "legacy_config_1_detected" in result.metadata
    
    def test_benchmark_validation_performance(self):
        """Test configuration validation benchmark."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_validation_performance(iterations=10)
        
        assert result.operation == "validation_performance"
        assert result.iterations == 10
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < PerformanceThreshold.VALIDATION.value  # <50ms
        
        # Check that validations were performed
        assert "config_0_valid" in result.metadata
        assert "config_1_valid" in result.metadata
        assert "config_2_valid" in result.metadata
    
    @pytest.mark.slow
    def test_comprehensive_benchmark_suite(self):
        """Test comprehensive benchmark suite execution."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        suite = benchmark.run_comprehensive_benchmark()
        
        assert isinstance(suite, BenchmarkSuite)
        assert suite.name == "Resilience Configuration Performance Benchmark"
        assert len(suite.results) == 7  # 7 different benchmarks
        assert suite.total_duration_ms > 0
        assert suite.pass_rate >= 0.0
        assert suite.pass_rate <= 1.0
        assert suite.timestamp is not None
        assert isinstance(suite.environment_info, dict)
        
        # Check that all expected benchmarks are present
        operation_names = [result.operation for result in suite.results]
        expected_operations = [
            "preset_loading",
            "settings_initialization", 
            "resilience_config_loading",
            "service_initialization",
            "custom_config_loading",
            "legacy_config_loading",
            "validation_performance"
        ]
        
        for expected_op in expected_operations:
            assert expected_op in operation_names
    
    def test_performance_threshold_checking(self):
        """Test performance threshold validation."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        # Add some mock results
        benchmark.results = [
            BenchmarkResult(
                operation="preset_loading",
                duration_ms=5.0,
                memory_peak_mb=1.0,
                iterations=10,
                avg_duration_ms=5.0,  # Within 10ms threshold
                min_duration_ms=4.0,
                max_duration_ms=6.0,
                std_dev_ms=0.5,
                success_rate=1.0,
                metadata={}
            ),
            BenchmarkResult(
                operation="settings_initialization",
                duration_ms=150.0,
                memory_peak_mb=2.0,
                iterations=10,
                avg_duration_ms=150.0,  # Above 100ms threshold
                min_duration_ms=140.0,
                max_duration_ms=160.0,
                std_dev_ms=5.0,
                success_rate=1.0,
                metadata={}
            )
        ]
        
        passed = benchmark._check_performance_thresholds()
        
        # Only preset_loading should pass
        assert "preset_loading" in passed
        assert "settings_initialization" not in passed
    
    def test_environment_info_collection(self):
        """Test environment information collection."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        env_info = benchmark._collect_environment_info()
        
        assert "python_version" in env_info
        assert "platform" in env_info
        assert "processor" in env_info
        assert "cpu_count" in env_info
        assert "environment_variables" in env_info
        
        env_vars = env_info["environment_variables"]
        assert "DEBUG" in env_vars
        assert "RESILIENCE_PRESET" in env_vars
        assert "GEMINI_API_KEY_SET" in env_vars
    
    def test_performance_report_generation(self):
        """Test performance report generation."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        # Create mock benchmark suite
        suite = BenchmarkSuite(
            name="Test Suite",
            results=[
                BenchmarkResult(
                    operation="test_operation",
                    duration_ms=50.0,
                    memory_peak_mb=1.5,
                    iterations=10,
                    avg_duration_ms=50.0,
                    min_duration_ms=45.0,
                    max_duration_ms=55.0,
                    std_dev_ms=2.0,
                    success_rate=1.0,
                    metadata={}
                )
            ],
            total_duration_ms=1000.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-01 12:00:00 UTC",
            environment_info={"platform": "Test Platform", "python_version": "3.8"}
        )
        
        report = benchmark.generate_performance_report(suite)
        
        assert "RESILIENCE CONFIGURATION PERFORMANCE REPORT" in report
        assert "Test Suite" in report or "50.00ms" in report
        assert "Test Platform" in report
        assert "✓ PASS" in report  # 50ms < 100ms threshold
    
    def test_performance_trend_analysis(self):
        """Test performance trend analysis."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        # Create historical benchmark results
        historical_results = [
            BenchmarkSuite(
                name="Suite 1",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=8.0,
                        memory_peak_mb=1.0,
                        iterations=10,
                        avg_duration_ms=8.0,
                        min_duration_ms=7.0,
                        max_duration_ms=9.0,
                        std_dev_ms=0.5,
                        success_rate=1.0,
                        metadata={}
                    )
                ],
                total_duration_ms=100.0,
                pass_rate=1.0,
                failed_benchmarks=[],
                timestamp="2024-01-01",
                environment_info={}
            ),
            BenchmarkSuite(
                name="Suite 2",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=12.0,
                        memory_peak_mb=1.2,
                        iterations=10,
                        avg_duration_ms=12.0,
                        min_duration_ms=11.0,
                        max_duration_ms=13.0,
                        std_dev_ms=0.8,
                        success_rate=1.0,
                        metadata={}
                    )
                ],
                total_duration_ms=120.0,
                pass_rate=1.0,
                failed_benchmarks=[],
                timestamp="2024-01-02",
                environment_info={}
            )
        ]
        
        trend_analysis = benchmark.analyze_performance_trends(historical_results)
        
        assert "preset_loading" in trend_analysis
        preset_trend = trend_analysis["preset_loading"]
        assert preset_trend["trend_direction"] == "degrading"  # 8ms -> 12ms
        assert preset_trend["trend_percentage"] > 0  # Performance got worse
        assert preset_trend["sample_count"] == 2
    
    def test_benchmark_error_handling(self):
        """Test benchmark error handling during operations."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        def failing_operation(metadata):
            from app.resilience_presets import preset_manager
            preset_manager.get_preset("simple")  # This will fail due to mock
        
        # Mock a failing operation
        with patch('app.resilience_presets.preset_manager.get_preset') as mock_get_preset:
            mock_get_preset.side_effect = Exception("Test error")
            
            result = benchmark.measure_performance("failing_operation", failing_operation, iterations=2)
        
        assert result.operation == "failing_operation"
        assert result.success_rate == 0.0  # All iterations failed
        assert "error_0" in result.metadata
        assert "error_1" in result.metadata
    
    def test_benchmark_result_serialization(self):
        """Test benchmark result serialization to JSON."""
        result = BenchmarkResult(
            operation="test_op",
            duration_ms=50.0,
            memory_peak_mb=1.5,
            iterations=10,
            avg_duration_ms=50.0,
            min_duration_ms=45.0,
            max_duration_ms=55.0,
            std_dev_ms=2.0,
            success_rate=1.0,
            metadata={"test": "value"}
        )
        
        suite = BenchmarkSuite(
            name="Test",
            results=[result],
            total_duration_ms=1000.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-01",
            environment_info={}
        )
        
        # Test serialization
        json_str = suite.to_json()
        assert isinstance(json_str, str)
        
        # Test deserialization
        data = json.loads(json_str)
        assert data["name"] == "Test"
        assert len(data["results"]) == 1
        assert data["results"][0]["operation"] == "test_op"


class TestPerformanceThresholds:
    """Test performance threshold validation."""
    
    def test_threshold_values(self):
        """Test that threshold values are reasonable."""
        assert PerformanceThreshold.CONFIG_LOADING.value == 100.0
        assert PerformanceThreshold.PRESET_ACCESS.value == 10.0
        assert PerformanceThreshold.VALIDATION.value == 50.0
        assert PerformanceThreshold.SERVICE_INIT.value == 200.0
    
    def test_all_thresholds_achievable(self):
        """Test that all thresholds are achievable in practice."""
        # This test ensures our thresholds are realistic
        thresholds = [
            PerformanceThreshold.CONFIG_LOADING.value,
            PerformanceThreshold.PRESET_ACCESS.value,
            PerformanceThreshold.VALIDATION.value,
            PerformanceThreshold.SERVICE_INIT.value
        ]
        
        # All thresholds should be positive and reasonable (< 1 second)
        for threshold in thresholds:
            assert threshold > 0
            assert threshold < 1000.0  # < 1 second


class TestBenchmarkIntegration:
    """Test integration with existing configuration system."""
    
    def test_benchmark_with_real_configuration_system(self):
        """Test benchmark with real configuration components."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        # Test that benchmarks work with real configuration loading
        result = benchmark.benchmark_preset_loading(iterations=3)
        
        assert result.success_rate == 1.0
        assert result.avg_duration_ms > 0
        assert result.avg_duration_ms < 50.0  # Should be very fast
    
    def test_global_benchmark_instance(self):
        """Test that global benchmark instance is available."""
        from app.performance_benchmarks import performance_benchmark
        
        assert isinstance(performance_benchmark, ConfigurationPerformanceBenchmark)
        assert performance_benchmark.results == []
    
    @pytest.mark.slow
    def test_end_to_end_performance_validation(self):
        """Test end-to-end performance validation meets target <100ms."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        # Run a subset of benchmarks that represent typical usage
        result_preset = benchmark.benchmark_preset_loading(iterations=10)
        result_config = benchmark.benchmark_resilience_config_loading(iterations=10)
        
        # Both should be well under 100ms target
        assert result_preset.avg_duration_ms < 100.0
        assert result_config.avg_duration_ms < 100.0
        
        # Preset loading should be very fast (<10ms)
        assert result_preset.avg_duration_ms < 10.0
        
        # All operations should succeed
        assert result_preset.success_rate == 1.0
        assert result_config.success_rate == 1.0


class TestMemoryBenchmarking:
    """Test memory usage benchmarking."""
    
    def test_memory_measurement_during_benchmark(self):
        """Test that memory usage is measured during benchmarks."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        result = benchmark.benchmark_preset_loading(iterations=3)
        
        assert result.memory_peak_mb >= 0.0
        # Memory usage should be reasonable (< 100MB for configuration loading)
        assert result.memory_peak_mb < 100.0
    
    def test_memory_efficiency_validation(self):
        """Test that configuration loading is memory efficient."""
        benchmark = ConfigurationPerformanceBenchmark()
        
        # Test multiple configuration scenarios
        results = [
            benchmark.benchmark_preset_loading(iterations=5),
            benchmark.benchmark_settings_initialization(iterations=5),
            benchmark.benchmark_resilience_config_loading(iterations=5)
        ]
        
        for result in results:
            # Memory usage should be minimal for configuration operations
            assert result.memory_peak_mb < 50.0, f"{result.operation} uses too much memory: {result.memory_peak_mb}MB"