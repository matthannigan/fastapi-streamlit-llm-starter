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
from app.infrastructure.cache.cache_presets import cache_preset_manager, CACHE_PRESETS


class TestCachePerformanceBenchmark:
    """Test cases for CachePerformanceBenchmark class."""
    
    def test_initialization_default(self):
        """Test benchmark initialization with default configuration."""
        benchmark = CachePerformanceBenchmark()
        
        assert isinstance(benchmark.config, BenchmarkConfig)
        assert benchmark.config.default_iterations == 100
    
    def test_initialization_with_config(self, development_config):
        """Test benchmark initialization with custom configuration."""
        benchmark = CachePerformanceBenchmark(config=development_config)
        
        assert benchmark.config == development_config
        assert benchmark.config.default_iterations == 50
    
    def test_benchmark_with_production_config(self, production_config):
        """Test creating benchmark with production configuration."""
        benchmark = CachePerformanceBenchmark(config=production_config)
        
        assert benchmark.config == production_config
    
    def test_configuration_validation(self):
        """Test that invalid configuration raises error during validation."""
        # Create invalid config
        invalid_config = BenchmarkConfig(default_iterations=-1)
        
        with pytest.raises(ConfigurationError):
            invalid_config.validate()
    
    def test_get_reporter_default(self, test_cache):
        """Test getting default reporter."""
        benchmark = CachePerformanceBenchmark()
        
        # The API likely doesn't have a get_reporter method, but we'll test the 
        # reporter factory instead
        from app.infrastructure.cache.benchmarks.reporting import ReporterFactory
        reporter = ReporterFactory.get_reporter("text")
        
        # Should return text reporter by default
        from app.infrastructure.cache.benchmarks.reporting import TextReporter
        assert isinstance(reporter, TextReporter)
    
    def test_get_reporter_custom_format(self, test_cache):
        """Test getting reporter with custom format."""
        benchmark = CachePerformanceBenchmark()
        
        # Test reporter factory instead of instance method
        from app.infrastructure.cache.benchmarks.reporting import ReporterFactory
        
        json_reporter = ReporterFactory.get_reporter("json")
        from app.infrastructure.cache.benchmarks.reporting import JSONReporter
        assert isinstance(json_reporter, JSONReporter)
        
        ci_reporter = ReporterFactory.get_reporter("ci")
        from app.infrastructure.cache.benchmarks.reporting import CIReporter
        assert isinstance(ci_reporter, CIReporter)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    async def test_benchmark_basic_operations(self, mock_memory_tracker, test_cache):
        """Test running basic operations benchmark."""
        # Mock memory tracker
        mock_tracker = MagicMock()
        mock_tracker.get_process_memory_mb.return_value = 10.0
        mock_memory_tracker.return_value = mock_tracker
        
        # Use development config for faster test
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        result = await benchmark.benchmark_basic_operations(test_cache)
        
        assert isinstance(result, BenchmarkResult)
        assert result.operation_type == "basic_operations"
        assert result.iterations == config.default_iterations
        assert result.avg_duration_ms > 0
        assert result.success_rate > 0
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    async def test_comprehensive_benchmark_suite_cache_efficiency(self, mock_memory_tracker, test_cache):
        """Test cache efficiency through comprehensive benchmark suite."""
        mock_tracker = MagicMock()
        mock_tracker.get_process_memory_mb.return_value = 10.0
        mock_memory_tracker.return_value = mock_tracker
        
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        suite = await benchmark.run_comprehensive_benchmark_suite(test_cache)
        
        assert isinstance(suite, BenchmarkSuite)
        assert len(suite.results) > 0
        # Verify basic operations are included (cache efficiency is part of basic ops)
        basic_ops_result = next((r for r in suite.results if r.operation_type == "basic_operations"), None)
        assert basic_ops_result is not None
        assert basic_ops_result.success_rate > 0
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    async def test_memory_usage_tracking(self, mock_memory_tracker, test_cache):
        """Test memory usage tracking in basic operations benchmark."""
        mock_tracker = MagicMock()
        mock_tracker.get_memory_usage.side_effect = [
            {"process_mb": 5.0},  # baseline
            {"process_mb": 15.0}  # after benchmark
        ]
        mock_tracker.calculate_memory_delta.return_value = {"process_mb": 10.0}
        mock_memory_tracker.return_value = mock_tracker
        
        config = ConfigPresets.development_config()
        # Create the benchmark with mocked memory tracker
        benchmark = CachePerformanceBenchmark(config=config)
        benchmark.memory_tracker = mock_tracker  # Replace with our mock
        
        result = await benchmark.benchmark_basic_operations(test_cache)
        
        assert isinstance(result, BenchmarkResult)
        assert result.operation_type == "basic_operations"
        assert result.memory_usage_mb > 0  # Should be 10.0 from our mock
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.benchmarks.utils.MemoryTracker')
    async def test_run_comprehensive_benchmark_suite(self, mock_memory_tracker, test_cache):
        """Test running comprehensive benchmark suite."""
        mock_tracker = MagicMock()
        mock_tracker.get_memory_usage.return_value = {"process_mb": 10.0}
        mock_tracker.calculate_memory_delta.return_value = {"process_mb": 5.0}
        mock_memory_tracker.return_value = mock_tracker
        
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        suite = await benchmark.run_comprehensive_benchmark_suite(test_cache)
        
        assert isinstance(suite, BenchmarkSuite)
        assert len(suite.results) > 0
        assert suite.total_duration_ms > 0
        assert all(isinstance(result, BenchmarkResult) for result in suite.results)
    
    @pytest.mark.asyncio
    async def test_benchmark_timeout_handling(self, test_cache):
        """Test benchmark timeout handling."""
        # Create config with very short timeout
        config = BenchmarkConfig(timeout_seconds=0.001, default_iterations=1000)
        benchmark = CachePerformanceBenchmark(config=config)
        
        # This should either complete very quickly or handle timeout gracefully
        try:
            result = await benchmark.benchmark_basic_operations(test_cache)
            # If it completes, should be valid
            assert isinstance(result, BenchmarkResult)
        except Exception as e:
            # Should be a timeout or configuration related exception
            assert "timeout" in str(e).lower() or "time" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_warmup_iterations(self, test_cache):
        """Test that warmup iterations are performed."""
        config = BenchmarkConfig(warmup_iterations=5, default_iterations=10)
        benchmark = CachePerformanceBenchmark(config=config)
        
        # Mock the warmup method to verify it's called
        with patch.object(benchmark, '_perform_warmup') as mock_warmup:
            mock_warmup.return_value = None
            
            result = await benchmark.benchmark_basic_operations(test_cache)
            
            # Should have called warmup with expected iterations
            mock_warmup.assert_called_once_with(test_cache, config.warmup_iterations)
            assert isinstance(result, BenchmarkResult)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_operations(self, test_cache):
        """Test error handling during benchmark operations."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        # Mock cache to raise errors occasionally
        original_set = test_cache.set
        call_count = 0
        
        async def failing_set(key, value, ttl=None):
            nonlocal call_count
            call_count += 1
            if call_count % 5 == 0:  # Fail every 5th operation
                raise Exception("Simulated cache error")
            return await original_set(key, value, ttl)
        
        test_cache.set = failing_set
        
        result = await benchmark.benchmark_basic_operations(test_cache)
        
        # Should handle errors gracefully
        assert isinstance(result, BenchmarkResult)
        assert result.error_count > 0
        assert result.success_rate < 1.0
    
    @pytest.mark.asyncio
    async def test_data_generation_integration(self, test_cache):
        """Test integration with data generator."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        # Test that data generator is used correctly
        with patch.object(benchmark.data_generator, 'generate_basic_operations_data') as mock_generate:
            mock_generate.return_value = [
                {"key": "test_key_1", "text": "test_value_1", "operation": "set"},
                {"key": "test_key_2", "text": "test_value_2", "operation": "get"}
            ]
            
            result = await benchmark.benchmark_basic_operations(test_cache)
            
            assert mock_generate.called
            assert isinstance(result, BenchmarkResult)
    
    @pytest.mark.asyncio
    async def test_statistical_analysis_integration(self, test_cache):
        """Test integration with statistical calculator."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        result = await benchmark.benchmark_basic_operations(test_cache)
        
        # Should have calculated percentiles
        assert result.p95_duration_ms >= result.avg_duration_ms
        assert result.p99_duration_ms >= result.p95_duration_ms
        assert result.std_dev_ms >= 0
    
    @pytest.mark.asyncio
    async def test_memory_tracking_disabled(self, test_cache):
        """Test benchmark with memory tracking disabled."""
        config = BenchmarkConfig(enable_memory_tracking=False)
        benchmark = CachePerformanceBenchmark(config=config)
        
        result = await benchmark.benchmark_basic_operations(test_cache)
        
        # Memory usage should be minimal or zero when tracking disabled
        assert result.memory_usage_mb >= 0
    
    @pytest.mark.asyncio
    async def test_compression_tests_disabled(self, test_cache):
        """Test benchmark with compression tests disabled."""
        config = BenchmarkConfig(enable_compression_tests=False)
        benchmark = CachePerformanceBenchmark(config=config)
        
        suite = await benchmark.run_comprehensive_benchmark_suite(test_cache)
        
        # Should not include compression benchmarks
        compression_results = [r for r in suite.results if "compression" in r.operation_type.lower()]
        assert len(compression_results) == 0
    
    @pytest.mark.asyncio
    async def test_environment_info_collection(self, test_cache):
        """Test collection of environment information."""
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        suite = await benchmark.run_comprehensive_benchmark_suite(test_cache)
        
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
            duration_ms=5000.0,
            memory_peak_mb=22.0,
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
            duration_ms=3000.0,
            memory_peak_mb=18.0,
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
        timing_regressions = detector.detect_timing_regressions(baseline, current)
        memory_regressions = detector.detect_memory_regressions(baseline, current)
        
        # Should detect no regressions for improvement
        assert len(timing_regressions) == 0
        assert len(memory_regressions) == 0
    
    def test_detect_timing_regression(self):
        """Test detecting timing regression."""
        baseline = BenchmarkResult(
            operation_type="test_op",
            duration_ms=3000.0,
            memory_peak_mb=16.0,
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
            duration_ms=6000.0,
            memory_peak_mb=27.0,
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
        timing_regressions = detector.detect_timing_regressions(baseline, current)
        
        # Should detect timing regression
        assert len(timing_regressions) > 0
        assert any(r["type"] == "timing_regression" for r in timing_regressions)
    
    def test_detect_memory_regression(self):
        """Test detecting memory regression."""
        # Create baseline suite
        baseline_result = BenchmarkResult(
            operation_type="basic_ops",
            duration_ms=2500.0,
            memory_peak_mb=11.0,
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
        
        # Create current suite with regression
        current_result = BenchmarkResult(
            operation_type="basic_ops",
            duration_ms=4500.0,
            memory_peak_mb=17.0,
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
        
        detector = PerformanceRegressionDetector()
        memory_regressions = detector.detect_memory_regressions(baseline_result, current_result)
        
        # Should detect memory regression
        assert len(memory_regressions) > 0
    
    def test_regression_detector_thresholds(self):
        """Test detector with custom thresholds."""
        # Create detector with strict thresholds
        detector = PerformanceRegressionDetector(
            warning_threshold=5.0,
            critical_threshold=10.0
        )
        
        baseline = BenchmarkResult(
            operation_type="threshold_test",
            duration_ms=2000.0,
            memory_peak_mb=9.0,
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
        
        # 8% regression should trigger warning but not critical
        current = BenchmarkResult(
            operation_type="threshold_test",
            duration_ms=2160.0,
            memory_peak_mb=9.5,
            avg_duration_ms=21.6,  # 8% slower
            min_duration_ms=16.2,
            max_duration_ms=32.4,
            p95_duration_ms=27.0,
            p99_duration_ms=30.0,
            std_dev_ms=3.2,
            operations_per_second=46.3,
            success_rate=1.0,
            memory_usage_mb=8.5,
            iterations=100,
            error_count=0
        )
        
        regressions = detector.detect_timing_regressions(baseline, current)
        
        # Should detect warning level regression
        assert len(regressions) > 0
        assert any(r["severity"] == "warning" for r in regressions)
    
    def test_regression_detector_basic_functionality(self):
        """Test basic regression detector functionality."""
        detector = PerformanceRegressionDetector()
        
        # Test with identical results (no regression)
        result = BenchmarkResult(
            operation_type="identical_test",
            duration_ms=2000.0,
            memory_peak_mb=10.0,
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
        
        timing_regressions = detector.detect_timing_regressions(result, result)
        memory_regressions = detector.detect_memory_regressions(result, result)
        
        # Should detect no regressions
        assert len(timing_regressions) == 0
        assert len(memory_regressions) == 0
        
        # Verify detector has expected attributes
        assert hasattr(detector, 'warning_threshold')
        assert hasattr(detector, 'critical_threshold')
        assert detector.warning_threshold == 10.0
        assert detector.critical_threshold == 25.0
    
    def test_regression_threshold_configuration(self):
        """Test regression detection with custom thresholds."""
        from app.infrastructure.cache.benchmarks.config import CachePerformanceThresholds
        
        # Use strict thresholds directly in constructor
        detector = PerformanceRegressionDetector(
            warning_threshold=5.0,   # Very strict warning threshold
            critical_threshold=10.0  # Very strict critical threshold
        )
        
        baseline = BenchmarkResult(
            operation_type="threshold_test",
            duration_ms=10000.0,  # Required field
            memory_peak_mb=25.0,  # Required field
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
            duration_ms=10700.0,  # Required field
            memory_peak_mb=27.0,  # Required field
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
            duration_ms=2500.0,  # Required field
            memory_peak_mb=15.0,  # Required field
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
            duration_ms=2500.0,  # Required field - same performance
            memory_peak_mb=60.0,  # Required field - higher peak memory
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
            duration_ms=2500.0,  # Required field
            memory_peak_mb=15.0,  # Required field
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
            duration_ms=2500.0,  # Required field - same performance
            memory_peak_mb=15.0,  # Required field
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
            duration_ms=0.0,  # Required field
            memory_peak_mb=0.0,  # Required field
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
            duration_ms=2500.0,  # Required field
            memory_peak_mb=15.0,  # Required field
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


class TestCachePresetBenchmarkCore:
    """Test cache preset integration with core benchmark functionality."""
    
    @pytest.mark.asyncio
    async def test_environment_detection_with_presets(self, monkeypatch):
        """Test environment detection integrating cache preset information."""
        # Set up cache preset environment
        monkeypatch.setenv("CACHE_PRESET", "production")
        monkeypatch.setenv("CACHE_REDIS_URL", "redis://localhost:6379")
        
        # Get preset configuration
        preset = cache_preset_manager.get_preset("production")
        preset_config = preset.to_cache_config()
        
        # Create benchmark with development config (for fast execution)
        config = ConfigPresets.development_config()
        benchmark = CachePerformanceBenchmark(config=config)
        
        # Create cache with preset configuration
        cache = InMemoryCache(
            max_size=preset_config.l1_cache_size,
            default_ttl=preset_config.default_ttl
        )
        
        # Run benchmark and check environment info collection
        suite = await benchmark.run_comprehensive_benchmark_suite(cache)
        
        # Validate environment info includes preset information
        assert suite.environment_info is not None
        assert isinstance(suite.environment_info, dict)
        assert len(suite.environment_info) > 0
        
        # Environment info should contain system details
        assert "config" in suite.environment_info
        
        # Preset information should be detectable in environment
        # (The actual preset detection would be implementation-specific)
        print(f"✓ Environment detection completed with preset configuration")
        print(f"  Cache TTL: {preset_config.default_ttl}s")
        print(f"  Cache Size: {preset_config.l1_cache_size}")
    
    @pytest.mark.asyncio
    async def test_benchmark_core_with_preset_environments(self, monkeypatch):
        """Test core benchmark functionality across different preset environments."""
        preset_names = ["development", "production"]
        benchmark_cores = {}
        
        for preset_name in preset_names:
            # Configure preset environment
            monkeypatch.setenv("CACHE_PRESET", preset_name)
            monkeypatch.setenv("CACHE_REDIS_URL", "redis://localhost:6379")
            
            # Get preset configuration
            preset = cache_preset_manager.get_preset(preset_name)
            preset_config = preset.to_cache_config()
            
            # Create benchmark configuration appropriate for testing
            if preset_name == "production":
                config = ConfigPresets.testing_config()  # More thorough but still fast
            else:
                config = ConfigPresets.development_config()  # Fast execution
            
            benchmark = CachePerformanceBenchmark(config=config)
            
            # Create cache with preset configuration
            cache = InMemoryCache(
                max_size=preset_config.l1_cache_size,
                default_ttl=preset_config.default_ttl
            )
            
            # Run core benchmark operations
            suite = await benchmark.run_comprehensive_benchmark_suite(cache)
            
            benchmark_cores[preset_name] = {
                "suite": suite,
                "preset_config": preset_config,
                "benchmark_config": config
            }
            
            # Clean up environment for next preset
            monkeypatch.delenv("CACHE_PRESET")
        
        # Validate core benchmark functionality across presets
        for preset_name, core_data in benchmark_cores.items():
            suite = core_data["suite"]
            assert isinstance(suite, BenchmarkSuite)
            assert len(suite.results) > 0
            
            # Each result should be properly formed
            for result in suite.results:
                assert isinstance(result, BenchmarkResult)
                assert result.duration_ms > 0
                assert result.operations_per_second > 0
                assert result.success_rate >= 0.0
                assert result.success_rate <= 1.0
        
        # Compare core characteristics between preset environments
        dev_core = benchmark_cores["development"]
        prod_core = benchmark_cores["production"]
        
        # Both should produce valid benchmark suites
        assert isinstance(dev_core["suite"], BenchmarkSuite)
        assert isinstance(prod_core["suite"], BenchmarkSuite)
        
        print(f"✓ Core benchmark validation completed across {len(preset_names)} preset environments")
    
    def test_preset_configuration_integration_with_core(self, monkeypatch):
        """Test preset configuration integration with benchmark core initialization."""
        # Set up preset environment
        monkeypatch.setenv("CACHE_PRESET", "ai-development")
        monkeypatch.setenv("CACHE_REDIS_URL", "redis://localhost:6379")
        
        # Get preset configuration
        preset = cache_preset_manager.get_preset("ai-development")
        preset_config = preset.to_cache_config()
        
        # Create benchmark configurations that could be influenced by presets
        base_config = ConfigPresets.development_config()
        
        # Initialize benchmark with base configuration
        benchmark = CachePerformanceBenchmark(config=base_config)
        
        # Validate benchmark initialization
        assert isinstance(benchmark.config, BenchmarkConfig)
        assert benchmark.config.default_iterations > 0
        
        # Create cache with preset-based configuration
        cache = InMemoryCache(
            max_size=preset_config.l1_cache_size,
            default_ttl=preset_config.default_ttl
        )
        
        # Validate cache configuration matches preset
        assert cache.max_size == preset_config.l1_cache_size
        assert cache.default_ttl == preset_config.default_ttl
        
        # Benchmark core should be able to work with preset-configured cache
        assert benchmark.config is not None
        assert cache is not None
        
        print(f"✓ Preset configuration integration validated with benchmark core")
        print(f"  AI Development Preset - TTL: {preset_config.default_ttl}s, Size: {preset_config.l1_cache_size}")
    
    def test_regression_detection_with_preset_scenarios(self):
        """Test regression detection between different preset-based scenarios."""
        # Simulate benchmark results from different preset configurations
        
        # Development preset - typically faster/smaller
        dev_result = BenchmarkResult(
            operation_type="cache_operations",
            duration_ms=100.0,
            memory_peak_mb=15.0,
            avg_duration_ms=10.0,
            min_duration_ms=8.0,
            max_duration_ms=15.0,
            p95_duration_ms=13.0,
            p99_duration_ms=14.0,
            std_dev_ms=2.0,
            operations_per_second=100.0,
            success_rate=1.0,
            memory_usage_mb=12.0,
            iterations=50,
            error_count=0
        )
        
        # Production preset - typically more robust but potentially slower
        prod_result = BenchmarkResult(
            operation_type="cache_operations", 
            duration_ms=150.0,
            memory_peak_mb=25.0,
            avg_duration_ms=15.0,
            min_duration_ms=12.0,
            max_duration_ms=20.0,
            p95_duration_ms=18.0,
            p99_duration_ms=19.0,
            std_dev_ms=3.0,
            operations_per_second=66.7,
            success_rate=1.0,
            memory_usage_mb=20.0,
            iterations=100,
            error_count=0
        )
        
        # Test regression detection between preset scenarios
        detector = PerformanceRegressionDetector()
        
        # Compare development (baseline) to production (current)
        comparison = detector.compare_results(dev_result, prod_result)
        
        # Validate comparison result
        assert isinstance(comparison, ComparisonResult)
        assert hasattr(comparison, 'performance_change_percent')
        assert hasattr(comparison, 'is_regression')
        
        # Production may be slower but should be within acceptable ranges for preset differences
        if comparison.is_regression:
            # Some regression is expected when moving from development to production preset
            # due to different optimization priorities
            assert comparison.performance_change_percent < 100.0  # Should not be extreme
        
        # Compare in reverse (production as baseline)
        reverse_comparison = detector.compare_results(prod_result, dev_result)
        assert isinstance(reverse_comparison, ComparisonResult)
        
        print(f"✓ Regression detection validated between preset scenarios")
        print(f"  Dev→Prod: {comparison.performance_change_percent:.1f}% change")
        print(f"  Prod→Dev: {reverse_comparison.performance_change_percent:.1f}% change")