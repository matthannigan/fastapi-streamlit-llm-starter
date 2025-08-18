"""
Integration tests for benchmark system.

This module tests end-to-end benchmark execution, report generation pipeline,
and configuration loading with real cache implementations.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.infrastructure.cache.benchmarks.core import CachePerformanceBenchmark
from app.infrastructure.cache.benchmarks.config import (
    ConfigPresets, load_config_from_file, load_config_from_env
)
from app.infrastructure.cache.benchmarks.reporting import ReporterFactory
from app.infrastructure.cache.benchmarks.models import BenchmarkSuite
from app.infrastructure.cache.memory import InMemoryCache


class TestEndToEndBenchmarkExecution:
    """Test end-to-end benchmark execution with real cache implementations."""
    
    def test_full_benchmark_with_memory_cache(self):
        """Test complete benchmark execution with InMemoryCache."""
        cache = InMemoryCache(max_size=100, ttl_seconds=3600)
        config = ConfigPresets.development_config()  # Fast execution for tests
        
        benchmark = CachePerformanceBenchmark(cache, config=config)
        
        # Run comprehensive benchmark suite
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Validate results
        assert isinstance(suite, BenchmarkSuite)
        assert len(suite.results) > 0
        assert suite.total_duration_ms > 0
        assert suite.pass_rate >= 0.0
        
        # All results should be valid
        for result in suite.results:
            assert result.avg_duration_ms >= 0
            assert result.operations_per_second >= 0
            assert 0 <= result.success_rate <= 1
            assert result.memory_usage_mb >= 0
    
    @patch('app.infrastructure.cache.redis.RedisCache')
    def test_full_benchmark_with_mock_redis(self, mock_redis_class):
        """Test complete benchmark execution with mocked Redis cache."""
        # Mock Redis cache behavior
        mock_redis = MagicMock()
        mock_redis.set.return_value = True
        mock_redis.get.return_value = "test_value"
        mock_redis.delete.return_value = True
        mock_redis.exists.return_value = True
        mock_redis.clear.return_value = True
        mock_redis_class.return_value = mock_redis
        
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(mock_redis, config=config)
        
        # Run benchmark suite
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Validate that Redis operations were called
        assert mock_redis.set.called
        assert mock_redis.get.called
        
        # Validate results
        assert isinstance(suite, BenchmarkSuite)
        assert len(suite.results) > 0
    
    def test_benchmark_with_different_configurations(self):
        """Test benchmark execution with different configuration presets."""
        cache = InMemoryCache()
        configs = [
            ConfigPresets.development_config(),
            ConfigPresets.testing_config(),
            ConfigPresets.ci_config()
        ]
        
        results = []
        for config in configs:
            benchmark = CachePerformanceBenchmark(cache, config=config)
            suite = benchmark.run_comprehensive_benchmark_suite()
            results.append(suite)
        
        # All configurations should produce valid results
        assert len(results) == 3
        for suite in results:
            assert isinstance(suite, BenchmarkSuite)
            assert len(suite.results) > 0
        
        # Different configurations should have different iteration counts
        iterations = [suite.config_used.get("default_iterations", 0) for suite in results]
        assert len(set(iterations)) > 1  # Should have different values
    
    def test_benchmark_error_recovery(self):
        """Test benchmark behavior when cache operations fail."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        # Mock cache to fail occasionally
        original_set = cache.set
        call_count = 0
        
        def failing_set(key, value, ttl=None):
            nonlocal call_count
            call_count += 1
            if call_count % 10 == 0:  # Fail every 10th operation
                raise Exception("Simulated cache failure")
            return original_set(key, value, ttl)
        
        cache.set = failing_set
        
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Should handle errors gracefully
        assert isinstance(suite, BenchmarkSuite)
        assert len(suite.results) > 0
        
        # Some operations should have recorded errors
        total_errors = sum(result.error_count for result in suite.results)
        assert total_errors > 0
        
        # Success rates should be less than perfect but not zero
        for result in suite.results:
            if result.error_count > 0:
                assert 0 < result.success_rate < 1
    
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    def test_memory_tracking_integration(self, mock_memory_tracker):
        """Test memory tracking integration across benchmark execution."""
        # Mock memory tracker with realistic values
        mock_tracker = MagicMock()
        memory_values = [10.0, 15.0, 12.0, 18.0, 11.0]  # Varying memory usage
        mock_tracker.get_process_memory_mb.side_effect = memory_values
        mock_memory_tracker.return_value = mock_tracker
        
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        config.enable_memory_tracking = True
        
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Memory tracking should have been called
        assert mock_tracker.get_process_memory_mb.called
        
        # Results should include memory information
        for result in suite.results:
            assert result.memory_usage_mb > 0
    
    def test_compression_tests_integration(self):
        """Test compression benchmark integration."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        config.enable_compression_tests = True
        
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Should include compression-related results
        compression_results = [
            result for result in suite.results 
            if "compression" in result.operation_type.lower()
        ]
        
        # May or may not have compression results depending on implementation
        # But should execute without errors
        assert isinstance(suite, BenchmarkSuite)


class TestReportGenerationPipeline:
    """Test the complete benchmark → results → reports pipeline."""
    
    def test_benchmark_to_all_report_formats(self):
        """Test complete pipeline from benchmark to all report formats."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        # Run benchmark
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Generate all report formats
        reports = ReporterFactory.generate_all_reports(suite)
        
        # Validate all report formats were generated
        expected_formats = ["text", "ci", "json", "markdown"]
        for format_name in expected_formats:
            assert format_name in reports
            assert isinstance(reports[format_name], str)
            assert len(reports[format_name]) > 0
        
        # Validate JSON report structure
        json_data = json.loads(reports["json"])
        assert "suite" in json_data
        assert "schema_version" in json_data
        
        # Validate markdown contains expected elements
        markdown_report = reports["markdown"]
        assert "# " in markdown_report  # Title
        assert "|" in markdown_report   # Tables
        
        # Validate CI report contains badges
        ci_report = reports["ci"]
        assert "![" in ci_report or "**" in ci_report  # Badges or bold formatting
    
    def test_report_generation_with_failed_benchmarks(self):
        """Test report generation when some benchmarks fail."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        # Create a suite with failed benchmarks
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Manually add failed benchmarks for testing
        suite.failed_benchmarks = ["failed_operation_1", "failed_operation_2"]
        
        # Generate reports
        reports = ReporterFactory.generate_all_reports(suite)
        
        # All formats should handle failed benchmarks
        for format_name, report in reports.items():
            assert "failed_operation_1" in report or "Failed" in report or "FAIL" in report
    
    def test_report_generation_with_custom_thresholds(self):
        """Test report generation with custom performance thresholds."""
        from app.infrastructure.cache.benchmarks.config import CachePerformanceThresholds
        
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        # Create strict thresholds
        strict_thresholds = CachePerformanceThresholds(
            basic_operations_avg_ms=5.0,  # Very strict
            memory_usage_warning_mb=5.0
        )
        
        # Run benchmark
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Generate reports with custom thresholds
        reports = ReporterFactory.generate_all_reports(suite, thresholds=strict_thresholds)
        
        # With strict thresholds, more benchmarks might fail
        text_report = reports["text"]
        assert "✗ FAIL" in text_report or "✓ PASS" in text_report
    
    def test_multiple_format_generation_consistency(self):
        """Test that different report formats contain consistent information."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        reports = ReporterFactory.generate_all_reports(suite)
        
        # Extract key information from different formats
        json_data = json.loads(reports["json"])
        suite_name = json_data["suite"]["name"]
        
        # All formats should contain the suite name
        for format_name, report in reports.items():
            if format_name != "json":
                assert suite_name in report
        
        # All formats should reference the same operations
        if suite.results:
            first_operation = suite.results[0].operation_type
            for format_name, report in reports.items():
                assert first_operation in report


class TestConfigurationLoadingAndApplication:
    """Test configuration loading and application in benchmarks."""
    
    def test_environment_to_config_to_benchmark(self, monkeypatch):
        """Test Environment → Config → Benchmark pipeline."""
        # Set environment variables
        monkeypatch.setenv("BENCHMARK_DEFAULT_ITERATIONS", "25")
        monkeypatch.setenv("BENCHMARK_WARMUP_ITERATIONS", "3")
        monkeypatch.setenv("BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS", "30.0")
        
        # Load config from environment
        config = load_config_from_env()
        
        # Validate config loaded correctly
        assert config.default_iterations == 25
        assert config.warmup_iterations == 3
        assert config.thresholds.basic_operations_avg_ms == 30.0
        
        # Apply to benchmark
        cache = InMemoryCache()
        benchmark = CachePerformanceBenchmark(cache, config=config)
        
        # Run benchmark with environment-loaded config
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Validate that config was applied
        assert isinstance(suite, BenchmarkSuite)
        # Check that iterations were actually limited
        for result in suite.results:
            assert result.iterations <= 25
    
    def test_file_to_config_to_benchmark(self):
        """Test File → Config → Benchmark pipeline."""
        # Create temporary config file
        config_data = {
            "default_iterations": 35,
            "warmup_iterations": 4,
            "timeout_seconds": 150,
            "enable_memory_tracking": True,
            "environment": "test_integration",
            "thresholds": {
                "basic_operations_avg_ms": 40.0,
                "memory_usage_warning_mb": 25.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_file_path = f.name
        
        try:
            # Load config from file
            config = load_config_from_file(config_file_path)
            
            # Validate config loaded correctly
            assert config.default_iterations == 35
            assert config.warmup_iterations == 4
            assert config.environment == "test_integration"
            assert config.thresholds.basic_operations_avg_ms == 40.0
            
            # Apply to benchmark
            cache = InMemoryCache()
            benchmark = CachePerformanceBenchmark(cache, config=config)
            
            # Run benchmark with file-loaded config
            suite = benchmark.run_comprehensive_benchmark_suite()
            
            # Validate that config was applied
            assert isinstance(suite, BenchmarkSuite)
            assert suite.config_used["environment"] == "test_integration"
            
        finally:
            # Clean up temp file
            Path(config_file_path).unlink()
    
    def test_config_preset_application(self):
        """Test applying different configuration presets."""
        cache = InMemoryCache()
        presets = {
            "development": ConfigPresets.development_config(),
            "testing": ConfigPresets.testing_config(),
            "ci": ConfigPresets.ci_config()
        }
        
        results = {}
        for preset_name, config in presets.items():
            benchmark = CachePerformanceBenchmark(cache, config=config)
            suite = benchmark.run_comprehensive_benchmark_suite()
            results[preset_name] = suite
        
        # All presets should produce valid results
        for preset_name, suite in results.items():
            assert isinstance(suite, BenchmarkSuite)
            assert len(suite.results) > 0
            assert suite.config_used["environment"] == preset_name
        
        # Different presets should have different characteristics
        dev_suite = results["development"]
        ci_suite = results["ci"]
        
        # Development should be faster (fewer iterations)
        # CI should be more thorough
        # This is reflected in the configuration, not necessarily in results
        assert dev_suite.config_used.get("default_iterations", 0) < ci_suite.config_used.get("default_iterations", 0)
    
    def test_configuration_validation_in_pipeline(self):
        """Test that configuration validation works in the full pipeline."""
        # Create invalid configuration
        invalid_config_data = {
            "default_iterations": -10,  # Invalid
            "warmup_iterations": 20,
            "timeout_seconds": -5,      # Invalid
            "thresholds": {
                "basic_operations_avg_ms": -1.0  # Invalid
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_config_data, f)
            config_file_path = f.name
        
        try:
            # Loading invalid config should raise ConfigurationError
            from app.core.exceptions import ConfigurationError
            with pytest.raises(ConfigurationError):
                load_config_from_file(config_file_path)
                
        finally:
            Path(config_file_path).unlink()
    
    def test_config_to_reporter_pipeline(self):
        """Test configuration affecting reporter selection and behavior."""
        cache = InMemoryCache()
        config = ConfigPresets.ci_config()  # CI environment
        
        benchmark = CachePerformanceBenchmark(cache, config=config)
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # In CI environment, should default to CI reporter
        with patch.dict('os.environ', {'CI': 'true'}):
            detected_format = ReporterFactory.detect_format_from_environment()
            assert detected_format == "ci"
            
            reporter = ReporterFactory.get_reporter(detected_format)
            ci_report = reporter.generate_report(suite)
            
            # CI report should have specific formatting
            assert "##" in ci_report  # Markdown headers
            assert "![" in ci_report or "**" in ci_report  # Badges or formatting


class TestPerformanceRegressionIntegration:
    """Test performance regression detection in full pipeline."""
    
    def test_benchmark_comparison_workflow(self):
        """Test comparing two benchmark runs for regression detection."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        # Run baseline benchmark
        benchmark = CachePerformanceBenchmark(cache, config=config)
        baseline_suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Simulate performance regression by modifying cache behavior
        original_get = cache.get
        
        def slower_get(key):
            import time
            time.sleep(0.001)  # Add 1ms delay
            return original_get(key)
        
        cache.get = slower_get
        
        # Run current benchmark
        current_suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Compare results
        from app.infrastructure.cache.benchmarks.core import PerformanceRegressionDetector
        detector = PerformanceRegressionDetector()
        
        comparisons = detector.compare_suites(baseline_suite, current_suite)
        
        # Should detect some performance changes
        assert len(comparisons) > 0
        for comparison in comparisons:
            assert hasattr(comparison, 'performance_change_percent')
            assert hasattr(comparison, 'is_regression')
    
    def test_full_regression_detection_pipeline(self):
        """Test complete regression detection and reporting pipeline."""
        cache = InMemoryCache()
        config = ConfigPresets.development_config()
        
        # Create two different performance scenarios
        benchmark = CachePerformanceBenchmark(cache, config=config)
        
        # First run (baseline)
        baseline_suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Second run with artificial slowdown
        original_set = cache.set
        
        def slower_set(key, value, ttl=None):
            import time
            time.sleep(0.0005)  # Add 0.5ms delay
            return original_set(key, value, ttl)
        
        cache.set = slower_set
        current_suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Detect regressions
        from app.infrastructure.cache.benchmarks.core import PerformanceRegressionDetector
        detector = PerformanceRegressionDetector()
        comparisons = detector.compare_suites(baseline_suite, current_suite)
        
        # Generate regression report
        if comparisons:
            # Create a comparison report (this could be a new reporter type)
            comparison_data = {
                "baseline": baseline_suite.to_dict(),
                "current": current_suite.to_dict(),
                "comparisons": [comp.to_dict() for comp in comparisons]
            }
            
            assert "baseline" in comparison_data
            assert "current" in comparison_data
            assert "comparisons" in comparison_data
            assert len(comparison_data["comparisons"]) > 0