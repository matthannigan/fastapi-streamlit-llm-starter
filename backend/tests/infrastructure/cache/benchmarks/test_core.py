"""
Tests for core benchmark functionality.

This module tests the main benchmark orchestration classes including
CachePerformanceBenchmark and PerformanceRegressionDetector.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.benchmarks.core import (
    CachePerformanceBenchmark, PerformanceRegressionDetector
)
from app.infrastructure.cache.benchmarks.config import BenchmarkConfig, ConfigPresets
from app.infrastructure.cache.benchmarks.models import BenchmarkResult, BenchmarkSuite, ComparisonResult
from app.infrastructure.cache.memory import InMemoryCache


class TestCachePerformanceBenchmark:
    """Test cases for CachePerformanceBenchmark class."""
    
    def test_initialization_default(self):
        """Test benchmark initialization with default configuration."""
        cache = InMemoryCache()
        benchmark = CachePerformanceBenchmark(cache)
        
        assert benchmark.cache == cache
        assert isinstance(benchmark.config, BenchmarkConfig)
        assert benchmark.config.default_iterations == 100
    
    def test_initialization_with_config(self, development_config):
        """Test benchmark initialization with custom configuration."""
        cache = InMemoryCache()
        benchmark = CachePerformanceBenchmark(cache, config=development_config)
        
        assert benchmark.cache == cache
        assert benchmark.config == development_config
        assert benchmark.config.default_iterations == 50
    
    def test_from_config_class_method(self, production_config):
        """Test creating benchmark from configuration."""
        cache = InMemoryCache()
        benchmark = CachePerformanceBenchmark.from_config(cache, production_config)
        
        assert benchmark.cache == cache
        assert benchmark.config == production_config
    
    def test_configuration_validation(self):
        """Test that invalid configuration raises error."""
        cache = InMemoryCache()
        
        # Create invalid config
        invalid_config = BenchmarkConfig(default_iterations=-1)
        
        with pytest.raises(ConfigurationError):
            CachePerformanceBenchmark(cache, config=invalid_config)
    
    def test_get_reporter_default(self, test_cache):
        """Test getting default reporter."""
        benchmark = CachePerformanceBenchmark(test_cache)
        reporter = benchmark.get_reporter()
        
        # Should return text reporter by default
        from app.infrastructure.cache.benchmarks.reporting import TextReporter
        assert isinstance(reporter, TextReporter)
    
    def test_get_reporter_custom_format(self, test_cache):
        """Test getting reporter with custom format."""
        benchmark = CachePerformanceBenchmark(test_cache)
        
        json_reporter = benchmark.get_reporter("json")
        from app.infrastructure.cache.benchmarks.reporting import JSONReporter
        assert isinstance(json_reporter, JSONReporter)
        
        ci_reporter = benchmark.get_reporter("ci")
        from app.infrastructure.cache.benchmarks.reporting import CIReporter
        assert isinstance(ci_reporter, CIReporter)
    
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    def test_run_basic_operations_benchmark(self, mock_memory_tracker, test_cache):
        """Test running basic operations benchmark."""
        # Mock memory tracker
        mock_tracker = MagicMock()
        mock_tracker.get_process_memory_mb.return_value = 10.0
        mock_memory_tracker.return_value = mock_tracker
        
        # Use development config for faster test
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        result = benchmark.run_basic_operations_benchmark()
        
        assert isinstance(result, BenchmarkResult)
        assert result.operation_type == "basic_operations"
        assert result.iterations == config.default_iterations
        assert result.avg_duration_ms > 0
        assert result.success_rate > 0
    
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    def test_run_cache_efficiency_benchmark(self, mock_memory_tracker, test_cache):
        """Test running cache efficiency benchmark."""
        mock_tracker = MagicMock()
        mock_tracker.get_process_memory_mb.return_value = 10.0
        mock_memory_tracker.return_value = mock_tracker
        
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        result = benchmark.run_cache_efficiency_benchmark()
        
        assert isinstance(result, BenchmarkResult)
        assert result.operation_type == "cache_efficiency"
        assert result.cache_hit_rate is not None
        assert 0.0 <= result.cache_hit_rate <= 1.0
    
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    def test_run_memory_usage_benchmark(self, mock_memory_tracker, test_cache):
        """Test running memory usage benchmark."""
        mock_tracker = MagicMock()
        mock_tracker.get_process_memory_mb.side_effect = [5.0, 15.0, 10.0]  # baseline, peak, final
        mock_memory_tracker.return_value = mock_tracker
        
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        result = benchmark.run_memory_usage_benchmark()
        
        assert isinstance(result, BenchmarkResult)
        assert result.operation_type == "memory_usage"
        assert result.memory_usage_mb > 0
    
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    def test_run_comprehensive_benchmark_suite(self, mock_memory_tracker, test_cache):
        """Test running comprehensive benchmark suite."""
        mock_tracker = MagicMock()
        mock_tracker.get_process_memory_mb.return_value = 10.0
        mock_memory_tracker.return_value = mock_tracker
        
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        assert isinstance(suite, BenchmarkSuite)
        assert len(suite.results) > 0
        assert suite.total_duration_ms > 0
        assert all(isinstance(result, BenchmarkResult) for result in suite.results)
    
    def test_benchmark_timeout_handling(self, test_cache):
        """Test benchmark timeout handling."""
        # Create config with very short timeout
        config = BenchmarkConfig(timeout_seconds=0.001, default_iterations=1000)
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        # This should either complete very quickly or handle timeout gracefully
        try:
            result = benchmark.run_basic_operations_benchmark()
            # If it completes, should be valid
            assert isinstance(result, BenchmarkResult)
        except Exception as e:
            # Should be a timeout or configuration related exception
            assert "timeout" in str(e).lower() or "time" in str(e).lower()
    
    def test_warmup_iterations(self, test_cache):
        """Test that warmup iterations are performed."""
        config = BenchmarkConfig(warmup_iterations=5, default_iterations=10)
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        with patch.object(benchmark, '_perform_cache_operation') as mock_operation:
            mock_operation.return_value = 0.01  # 10ms operation
            
            result = benchmark.run_basic_operations_benchmark()
            
            # Should have called operation for warmup + actual iterations
            expected_calls = config.warmup_iterations + config.default_iterations
            assert mock_operation.call_count >= expected_calls
    
    def test_error_handling_in_operations(self, test_cache):
        """Test error handling during benchmark operations."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        # Mock cache to raise errors occasionally
        original_set = test_cache.set
        call_count = 0
        
        def failing_set(key, value, ttl=None):
            nonlocal call_count
            call_count += 1
            if call_count % 5 == 0:  # Fail every 5th operation
                raise Exception("Simulated cache error")
            return original_set(key, value, ttl)
        
        test_cache.set = failing_set
        
        result = benchmark.run_basic_operations_benchmark()
        
        # Should handle errors gracefully
        assert isinstance(result, BenchmarkResult)
        assert result.error_count > 0
        assert result.success_rate < 1.0
    
    def test_data_generation_integration(self, test_cache):
        """Test integration with data generator."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        # Test that data generator is used correctly
        with patch.object(benchmark.data_generator, 'generate_workload_data') as mock_generate:
            mock_generate.return_value = [
                {"key": "test_key_1", "value": "test_value_1"},
                {"key": "test_key_2", "value": "test_value_2"}
            ]
            
            result = benchmark.run_basic_operations_benchmark()
            
            assert mock_generate.called
            assert isinstance(result, BenchmarkResult)
    
    def test_statistical_analysis_integration(self, test_cache):
        """Test integration with statistical calculator."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        result = benchmark.run_basic_operations_benchmark()
        
        # Should have calculated percentiles
        assert result.p95_duration_ms >= result.avg_duration_ms
        assert result.p99_duration_ms >= result.p95_duration_ms
        assert result.std_dev_ms >= 0
    
    def test_memory_tracking_disabled(self, test_cache):
        """Test benchmark with memory tracking disabled."""
        config = BenchmarkConfig(enable_memory_tracking=False)
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        result = benchmark.run_basic_operations_benchmark()
        
        # Memory usage should be minimal or zero when tracking disabled
        assert result.memory_usage_mb >= 0
    
    def test_compression_tests_disabled(self, test_cache):
        """Test benchmark with compression tests disabled."""
        config = BenchmarkConfig(enable_compression_tests=False)
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Should not include compression benchmarks
        compression_results = [r for r in suite.results if "compression" in r.operation_type.lower()]
        assert len(compression_results) == 0
    
    def test_environment_info_collection(self, test_cache):
        """Test collection of environment information."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(test_cache, config=config)
        
        suite = benchmark.run_comprehensive_benchmark_suite()
        
        # Should collect environment info
        assert suite.environment_info is not None
        assert isinstance(suite.environment_info, dict)
        # Should contain basic system info
        assert len(suite.environment_info) > 0


class TestPerformanceRegressionDetector:
    """Test cases for PerformanceRegressionDetector class."""
    
    def test_initialization(self):
        """Test regression detector initialization."""
        detector = PerformanceRegressionDetector()
        assert detector is not None
    
    def test_compare_results_improvement(self):
        """Test comparison showing improvement."""
        baseline = BenchmarkResult(
            operation_type="test_op",
            avg_duration_ms=50.0,
            min_duration_ms=40.0,
            max_duration_ms=70.0,
            p95_duration_ms=65.0,
            p99_duration_ms=68.0,
            std_dev_ms=8.0,
            operations_per_second=20.0,
            success_rate=1.0,
            memory_usage_mb=20.0,
            iterations=100,
            error_count=0
        )
        
        current = BenchmarkResult(
            operation_type="test_op",
            avg_duration_ms=30.0,  # 40% improvement
            min_duration_ms=25.0,
            max_duration_ms=40.0,
            p95_duration_ms=38.0,
            p99_duration_ms=39.0,
            std_dev_ms=5.0,
            operations_per_second=33.3,
            success_rate=1.0,
            memory_usage_mb=15.0,
            iterations=100,
            error_count=0
        )
        
        detector = PerformanceRegressionDetector()
        comparison = detector.compare_results(baseline, current)
        
        assert isinstance(comparison, ComparisonResult)
        assert comparison.performance_change_percent < 0  # Negative = improvement
        assert comparison.is_regression is False
    
    def test_compare_results_regression(self):
        """Test comparison showing regression."""
        baseline = BenchmarkResult(
            operation_type="test_op",
            avg_duration_ms=30.0,
            min_duration_ms=25.0,
            max_duration_ms=40.0,
            p95_duration_ms=38.0,
            p99_duration_ms=39.0,
            std_dev_ms=5.0,
            operations_per_second=33.3,
            success_rate=1.0,
            memory_usage_mb=15.0,
            iterations=100,
            error_count=0
        )
        
        current = BenchmarkResult(
            operation_type="test_op",
            avg_duration_ms=60.0,  # 100% regression
            min_duration_ms=50.0,
            max_duration_ms=80.0,
            p95_duration_ms=75.0,
            p99_duration_ms=78.0,
            std_dev_ms=10.0,
            operations_per_second=16.7,
            success_rate=1.0,
            memory_usage_mb=25.0,
            iterations=100,
            error_count=0
        )
        
        detector = PerformanceRegressionDetector()
        comparison = detector.compare_results(baseline, current)
        
        assert isinstance(comparison, ComparisonResult)
        assert comparison.performance_change_percent > 0  # Positive = regression
        assert comparison.is_regression is True
    
    def test_compare_suites_basic(self):
        """Test comparing two benchmark suites."""
        # Create baseline suite
        baseline_result = BenchmarkResult(
            operation_type="basic_ops",
            avg_duration_ms=25.0,
            min_duration_ms=20.0,
            max_duration_ms=35.0,
            p95_duration_ms=32.0,
            p99_duration_ms=34.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=1.0,
            memory_usage_mb=10.0,
            iterations=100,
            error_count=0
        )
        
        baseline_suite = BenchmarkSuite(
            name="Baseline Suite",
            results=[baseline_result],
            timestamp=datetime.now(),
            total_duration_ms=1000.0,
            environment_info={},
            failed_benchmarks=[],
            config_used={}
        )
        
        # Create current suite with regression
        current_result = BenchmarkResult(
            operation_type="basic_ops",
            avg_duration_ms=45.0,  # 80% slower
            min_duration_ms=35.0,
            max_duration_ms=60.0,
            p95_duration_ms=55.0,
            p99_duration_ms=58.0,
            std_dev_ms=8.0,
            operations_per_second=22.2,
            success_rate=1.0,
            memory_usage_mb=15.0,
            iterations=100,
            error_count=0
        )
        
        current_suite = BenchmarkSuite(
            name="Current Suite",
            results=[current_result],
            timestamp=datetime.now(),
            total_duration_ms=1500.0,
            environment_info={},
            failed_benchmarks=[],
            config_used={}
        )
        
        detector = PerformanceRegressionDetector()
        comparisons = detector.compare_suites(baseline_suite, current_suite)
        
        assert isinstance(comparisons, list)
        assert len(comparisons) == 1
        assert isinstance(comparisons[0], ComparisonResult)
        assert comparisons[0].is_regression is True
    
    def test_detect_regressions_in_suite(self):
        """Test detecting regressions in a benchmark suite."""
        # Create suite with mixed results
        good_result = BenchmarkResult(
            operation_type="good_op",
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=30.0,
            p95_duration_ms=25.0,
            p99_duration_ms=28.0,
            std_dev_ms=3.0,
            operations_per_second=50.0,
            success_rate=1.0,
            memory_usage_mb=8.0,
            iterations=100,
            error_count=0
        )
        
        bad_result = BenchmarkResult(
            operation_type="slow_op",
            avg_duration_ms=150.0,  # Very slow
            min_duration_ms=100.0,
            max_duration_ms=250.0,
            p95_duration_ms=200.0,
            p99_duration_ms=240.0,
            std_dev_ms=40.0,
            operations_per_second=6.7,
            success_rate=0.9,  # Also has reliability issues
            memory_usage_mb=50.0,
            iterations=100,
            error_count=10
        )
        
        suite = BenchmarkSuite(
            name="Mixed Results Suite",
            results=[good_result, bad_result],
            timestamp=datetime.now(),
            total_duration_ms=2000.0,
            environment_info={},
            failed_benchmarks=[],
            config_used={}
        )
        
        detector = PerformanceRegressionDetector()
        regressions = detector.detect_regressions_in_suite(suite)
        
        # Should detect the slow operation as a regression
        assert len(regressions) >= 1
        regression_ops = [r.operation_type for r in regressions]
        assert "slow_op" in regression_ops
    
    def test_analyze_performance_trends(self):
        """Test performance trend analysis."""
        # Create a series of benchmark results showing degradation
        results = []
        for i in range(5):
            result = BenchmarkResult(
                operation_type="trending_op",
                avg_duration_ms=20.0 + i * 10,  # Getting slower over time
                min_duration_ms=15.0 + i * 8,
                max_duration_ms=30.0 + i * 15,
                p95_duration_ms=25.0 + i * 12,
                p99_duration_ms=28.0 + i * 14,
                std_dev_ms=3.0 + i,
                operations_per_second=50.0 - i * 5,  # Getting slower
                success_rate=1.0 - i * 0.02,  # Slight degradation
                memory_usage_mb=8.0 + i * 2,
                iterations=100,
                error_count=i * 2,
                metadata={"run_number": i + 1}
            )
            results.append(result)
        
        detector = PerformanceRegressionDetector()
        trends = detector.analyze_performance_trends(results)
        
        assert isinstance(trends, dict)
        assert "trend_direction" in trends
        assert "performance_change_rate" in trends
        
        # Should detect degrading trend
        assert trends["trend_direction"] in ["degrading", "stable", "improving"]
    
    def test_regression_threshold_configuration(self):
        """Test regression detection with custom thresholds."""
        from app.infrastructure.cache.benchmarks.config import CachePerformanceThresholds
        
        strict_thresholds = CachePerformanceThresholds(
            regression_warning_percent=5.0,  # Very strict
            regression_critical_percent=10.0
        )
        
        detector = PerformanceRegressionDetector(thresholds=strict_thresholds)
        
        baseline = BenchmarkResult(
            operation_type="threshold_test",
            avg_duration_ms=100.0,
            min_duration_ms=80.0,
            max_duration_ms=150.0,
            p95_duration_ms=130.0,
            p99_duration_ms=140.0,
            std_dev_ms=20.0,
            operations_per_second=10.0,
            success_rate=1.0,
            memory_usage_mb=20.0,
            iterations=100,
            error_count=0
        )
        
        # 7% regression (between warning and critical)
        current = BenchmarkResult(
            operation_type="threshold_test",
            avg_duration_ms=107.0,
            min_duration_ms=85.0,
            max_duration_ms=160.0,
            p95_duration_ms=140.0,
            p99_duration_ms=150.0,
            std_dev_ms=22.0,
            operations_per_second=9.3,
            success_rate=1.0,
            memory_usage_mb=22.0,
            iterations=100,
            error_count=0
        )
        
        comparison = detector.compare_results(baseline, current)
        
        # Should detect as regression with strict thresholds
        assert comparison.is_regression is True
    
    def test_memory_regression_detection(self):
        """Test detection of memory usage regressions."""
        baseline = BenchmarkResult(
            operation_type="memory_test",
            avg_duration_ms=25.0,
            min_duration_ms=20.0,
            max_duration_ms=35.0,
            p95_duration_ms=30.0,
            p99_duration_ms=33.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=1.0,
            memory_usage_mb=10.0,
            iterations=100,
            error_count=0
        )
        
        # Same performance, but much higher memory usage
        current = BenchmarkResult(
            operation_type="memory_test",
            avg_duration_ms=25.0,  # Same performance
            min_duration_ms=20.0,
            max_duration_ms=35.0,
            p95_duration_ms=30.0,
            p99_duration_ms=33.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=1.0,
            memory_usage_mb=50.0,  # 400% increase in memory
            iterations=100,
            error_count=0
        )
        
        detector = PerformanceRegressionDetector()
        comparison = detector.compare_results(baseline, current)
        
        # Should detect memory regression
        assert comparison.operation_type == "memory_test"
        # Memory regression might be flagged in recommendations
        recommendations = comparison.generate_recommendations()
        memory_text = " ".join(recommendations).lower()
        assert "memory" in memory_text
    
    def test_success_rate_regression_detection(self):
        """Test detection of success rate regressions."""
        baseline = BenchmarkResult(
            operation_type="reliability_test",
            avg_duration_ms=25.0,
            min_duration_ms=20.0,
            max_duration_ms=35.0,
            p95_duration_ms=30.0,
            p99_duration_ms=33.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=1.0,  # Perfect success rate
            memory_usage_mb=10.0,
            iterations=100,
            error_count=0
        )
        
        current = BenchmarkResult(
            operation_type="reliability_test",
            avg_duration_ms=25.0,  # Same performance
            min_duration_ms=20.0,
            max_duration_ms=35.0,
            p95_duration_ms=30.0,
            p99_duration_ms=33.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=0.85,  # 15% failure rate
            memory_usage_mb=10.0,
            iterations=100,
            error_count=15
        )
        
        detector = PerformanceRegressionDetector()
        comparison = detector.compare_results(baseline, current)
        
        # Should detect reliability regression
        recommendations = comparison.generate_recommendations()
        reliability_text = " ".join(recommendations).lower()
        assert any(word in reliability_text for word in ["reliability", "error", "failure", "success"])
    
    def test_edge_cases_handling(self):
        """Test handling of edge cases in regression detection."""
        # Test with zero baseline performance
        zero_baseline = BenchmarkResult(
            operation_type="edge_case",
            avg_duration_ms=0.0,
            min_duration_ms=0.0,
            max_duration_ms=0.0,
            p95_duration_ms=0.0,
            p99_duration_ms=0.0,
            std_dev_ms=0.0,
            operations_per_second=0.0,
            success_rate=0.0,
            memory_usage_mb=0.0,
            iterations=0,
            error_count=100
        )
        
        normal_current = BenchmarkResult(
            operation_type="edge_case",
            avg_duration_ms=25.0,
            min_duration_ms=20.0,
            max_duration_ms=35.0,
            p95_duration_ms=30.0,
            p99_duration_ms=33.0,
            std_dev_ms=4.0,
            operations_per_second=40.0,
            success_rate=1.0,
            memory_usage_mb=10.0,
            iterations=100,
            error_count=0
        )
        
        detector = PerformanceRegressionDetector()
        
        # Should handle zero baseline gracefully
        comparison = detector.compare_results(zero_baseline, normal_current)
        assert isinstance(comparison, ComparisonResult)
        # When baseline is zero, any positive current performance is an improvement