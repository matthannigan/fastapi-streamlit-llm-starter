"""
Cache Performance Benchmarking Core

This module contains the main benchmarking orchestration classes including
the CachePerformanceBenchmark class and PerformanceRegressionDetector.

Classes:
    PerformanceRegressionDetector: Automated regression detection and alerting
    CachePerformanceBenchmark: Main benchmarking orchestration class

The core module coordinates all benchmarking activities while using the
extracted utilities, data models, and configuration from other modules.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Union

from ..base import CacheInterface
from ..monitoring import CachePerformanceMonitor
from .models import BenchmarkResult, BenchmarkSuite, ComparisonResult
from .utils import StatisticalCalculator, MemoryTracker
from .generator import CacheBenchmarkDataGenerator
from .config import BenchmarkConfig, ConfigPresets
from .reporting import ReporterFactory

# Import factory and config classes if available
try:
    from ..factory import CacheFactory
    FACTORY_AVAILABLE = True
except ImportError:
    FACTORY_AVAILABLE = False
    CacheFactory = None

try:
    from ..config import CacheConfigBuilder, EnvironmentPresets
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    CacheConfigBuilder = EnvironmentPresets = None

logger = logging.getLogger(__name__)


class PerformanceRegressionDetector:
    """
    Detect and analyze performance regressions in cache benchmarks.
    
    This class provides automated regression detection for timing, memory,
    and cache efficiency metrics. It supports configurable thresholds and
    detailed analysis of performance changes.
    
    Attributes:
        warning_threshold: Percentage change that triggers warnings
        critical_threshold: Percentage change that triggers critical alerts
    
    Example:
        >>> detector = PerformanceRegressionDetector(
        ...     warning_threshold=10.0,
        ...     critical_threshold=25.0
        ... )
        >>> regressions = detector.detect_timing_regressions(old_result, new_result)
        >>> memory_issues = detector.detect_memory_regressions(old_result, new_result)
    """
    
    def __init__(self, warning_threshold: float = 10.0, critical_threshold: float = 25.0):
        """
        Initialize regression detector with configurable thresholds.
        
        Args:
            warning_threshold: Percentage change threshold for warnings
            critical_threshold: Percentage change threshold for critical alerts
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
    
    def detect_timing_regressions(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> List[Dict[str, Any]]:
        """
        Detect timing-related performance regressions.
        
        Analyzes average duration, P95 duration, and operations per second
        to identify performance degradations that exceed the configured thresholds.
        
        Args:
            old_result: Baseline benchmark result
            new_result: New benchmark result to compare
            
        Returns:
            List of detected regressions with details and severity levels
        """
        regressions = []
        
        # Check average duration regression
        if old_result.avg_duration_ms > 0:
            avg_change = ((new_result.avg_duration_ms - old_result.avg_duration_ms) / old_result.avg_duration_ms) * 100
            if avg_change > self.warning_threshold:
                severity = "critical" if avg_change > self.critical_threshold else "warning"
                regressions.append({
                    "type": "timing_regression",
                    "metric": "average_duration",
                    "severity": severity,
                    "change_percent": avg_change,
                    "old_value": old_result.avg_duration_ms,
                    "new_value": new_result.avg_duration_ms,
                    "message": f"Average duration increased by {avg_change:.1f}%"
                })
        
        # Check P95 duration regression
        if old_result.p95_duration_ms > 0:
            p95_change = ((new_result.p95_duration_ms - old_result.p95_duration_ms) / old_result.p95_duration_ms) * 100
            if p95_change > self.warning_threshold:
                severity = "critical" if p95_change > self.critical_threshold else "warning"
                regressions.append({
                    "type": "timing_regression",
                    "metric": "p95_duration",
                    "severity": severity,
                    "change_percent": p95_change,
                    "old_value": old_result.p95_duration_ms,
                    "new_value": new_result.p95_duration_ms,
                    "message": f"P95 duration increased by {p95_change:.1f}%"
                })
        
        # Check operations per second degradation
        if old_result.operations_per_second > 0:
            ops_change = ((new_result.operations_per_second - old_result.operations_per_second) / old_result.operations_per_second) * 100
            if ops_change < -self.warning_threshold:
                severity = "critical" if ops_change < -self.critical_threshold else "warning"
                regressions.append({
                    "type": "throughput_regression",
                    "metric": "operations_per_second",
                    "severity": severity,
                    "change_percent": ops_change,
                    "old_value": old_result.operations_per_second,
                    "new_value": new_result.operations_per_second,
                    "message": f"Throughput decreased by {abs(ops_change):.1f}%"
                })
        
        return regressions
    
    def detect_memory_regressions(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> List[Dict[str, Any]]:
        """
        Detect memory-related performance regressions.
        
        Analyzes memory usage and peak memory consumption to identify
        memory-related performance degradations.
        
        Args:
            old_result: Baseline benchmark result
            new_result: New benchmark result to compare
            
        Returns:
            List of detected memory regressions with details and severity levels
        """
        regressions = []
        
        # Check memory usage increase with safe division
        if old_result.memory_usage_mb > 0:
            memory_change = ((new_result.memory_usage_mb - old_result.memory_usage_mb) / old_result.memory_usage_mb) * 100
            if memory_change > self.warning_threshold:
                severity = "critical" if memory_change > self.critical_threshold else "warning"
                regressions.append({
                    "type": "memory_regression",
                    "metric": "memory_usage",
                    "severity": severity,
                    "change_percent": memory_change,
                    "old_value": old_result.memory_usage_mb,
                    "new_value": new_result.memory_usage_mb,
                    "message": f"Memory usage increased by {memory_change:.1f}%"
                })
        
        # Check peak memory increase with safe division
        if old_result.memory_peak_mb > 0:
            peak_change = ((new_result.memory_peak_mb - old_result.memory_peak_mb) / old_result.memory_peak_mb) * 100
            if peak_change > self.warning_threshold:
                severity = "critical" if peak_change > self.critical_threshold else "warning"
                regressions.append({
                    "type": "memory_regression",
                    "metric": "peak_memory",
                    "severity": severity,
                    "change_percent": peak_change,
                    "old_value": old_result.memory_peak_mb,
                    "new_value": new_result.memory_peak_mb,
                    "message": f"Peak memory usage increased by {peak_change:.1f}%"
                })
        
        return regressions
    
    def validate_cache_hit_rates(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> Dict[str, Any]:
        """
        Validate cache hit rates haven't degraded.
        
        Args:
            old_result: Baseline benchmark result
            new_result: New benchmark result to compare
            
        Returns:
            Validation result with status and any issues found
        """
        if old_result.cache_hit_rate is None or new_result.cache_hit_rate is None:
            return {"status": "skipped", "reason": "hit_rate_data_unavailable"}
        
        hit_rate_change = new_result.cache_hit_rate - old_result.cache_hit_rate
        
        if hit_rate_change < -0.05:  # 5% degradation threshold
            return {
                "status": "degraded",
                "old_hit_rate": old_result.cache_hit_rate,
                "new_hit_rate": new_result.cache_hit_rate,
                "change": hit_rate_change,
                "message": f"Cache hit rate degraded by {abs(hit_rate_change)*100:.1f}%"
            }
        
        return {"status": "ok", "hit_rate_change": hit_rate_change}
    
    def compare_results(self, baseline: BenchmarkResult, current: BenchmarkResult) -> ComparisonResult:
        """
        Compare two benchmark results and generate a comprehensive comparison.
        
        Args:
            baseline: Baseline benchmark result
            current: Current benchmark result to compare
            
        Returns:
            ComparisonResult with detailed performance comparison and regression analysis
        """
        # Calculate performance changes
        performance_change = 0.0
        memory_change = 0.0
        ops_change = 0.0
        
        if baseline.avg_duration_ms > 0:
            performance_change = ((current.avg_duration_ms - baseline.avg_duration_ms) / baseline.avg_duration_ms) * 100
        
        if baseline.memory_usage_mb > 0:
            memory_change = ((current.memory_usage_mb - baseline.memory_usage_mb) / baseline.memory_usage_mb) * 100
        
        if baseline.operations_per_second > 0:
            ops_change = ((current.operations_per_second - baseline.operations_per_second) / baseline.operations_per_second) * 100
        
        # Detect regressions
        timing_regressions = self.detect_timing_regressions(baseline, current)
        memory_regressions = self.detect_memory_regressions(baseline, current)
        regression_detected = len(timing_regressions) > 0 or len(memory_regressions) > 0
        
        # Determine improvement and degradation areas
        improvement_areas = []
        degradation_areas = []
        
        if performance_change < -self.warning_threshold:
            improvement_areas.append("timing")
        elif performance_change > self.warning_threshold:
            degradation_areas.append("timing")
        
        if memory_change < -self.warning_threshold:
            improvement_areas.append("memory")
        elif memory_change > self.warning_threshold:
            degradation_areas.append("memory")
        
        if ops_change > self.warning_threshold:
            improvement_areas.append("throughput")
        elif ops_change < -self.warning_threshold:
            degradation_areas.append("throughput")
        
        # Generate recommendation
        if regression_detected:
            recommendation = "Performance regressions detected. Review before deployment."
        elif len(improvement_areas) > 0:
            recommendation = f"Performance improved in: {', '.join(improvement_areas)}"
        else:
            recommendation = "Performance analysis complete. No significant changes detected."
        
        return ComparisonResult(
            original_cache_results=baseline,
            new_cache_results=current,
            performance_change_percent=performance_change,
            memory_change_percent=memory_change,
            operations_per_second_change=ops_change,
            baseline_cache_name="Baseline",
            comparison_cache_name="Current",
            regression_detected=regression_detected,
            improvement_areas=improvement_areas,
            degradation_areas=degradation_areas,
            recommendation=recommendation
        )


class CachePerformanceBenchmark:
    """
    Main benchmarking orchestration class for cache performance testing.
    
    This class coordinates comprehensive cache performance testing including
    basic operations, memory testing, compression efficiency, and regression
    detection. It uses the extracted utilities and data models for modular,
    maintainable benchmarking.
    
    Attributes:
        config: Benchmark configuration settings
        data_generator: Test data generator instance
        memory_tracker: Memory tracking utility
        regression_detector: Regression detection utility
        
    Example:
        >>> config = ConfigPresets.testing_config()
        >>> benchmark = CachePerformanceBenchmark(config)
        >>> cache = SomeCache()
        >>> result = await benchmark.benchmark_basic_operations(cache)
        >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
    """
    
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        Initialize benchmark system with configuration.
        
        Args:
            config: Benchmark configuration, uses default if not provided
        """
        self.config = config if config is not None else BenchmarkConfig()
        self.data_generator = CacheBenchmarkDataGenerator()
        self.memory_tracker = MemoryTracker()
        self.regression_detector = PerformanceRegressionDetector(
            warning_threshold=self.config.thresholds.regression_warning_percent,
            critical_threshold=self.config.thresholds.regression_critical_percent
        )
        self.calculator = StatisticalCalculator()
    
    @classmethod
    def from_config(cls, config: BenchmarkConfig) -> "CachePerformanceBenchmark":
        """
        Create benchmark instance from configuration.
        
        Args:
            config: Complete benchmark configuration
            
        Returns:
            Configured CachePerformanceBenchmark instance
        """
        return cls(config)
    
    async def benchmark_basic_operations(self, cache: CacheInterface, iterations: Optional[int] = None) -> BenchmarkResult:
        """
        Benchmark basic cache operations (get/set/delete).
        
        Args:
            cache: Cache implementation to benchmark
            iterations: Number of iterations, uses config default if not provided
            
        Returns:
            BenchmarkResult containing timing and performance metrics
        """
        iterations = iterations if iterations is not None else self.config.default_iterations
        logger.info(f"Starting basic operations benchmark with {iterations} iterations")
        
        # Generate test data
        test_data = self.data_generator.generate_basic_operations_data(iterations)
        
        # Track memory before benchmark
        memory_before = self.memory_tracker.get_memory_usage()
        
        # Warmup
        await self._perform_warmup(cache, self.config.warmup_iterations)
        
        # Benchmark execution
        durations = []
        errors = 0
        
        start_time = time.time()
        
        for item in test_data:
            operation_start = time.perf_counter()
            
            try:
                # Set operation
                await cache.set(item["key"], item["text"], ttl=item.get("cache_ttl", 300))
                
                # Get operation
                result = await cache.get(item["key"])
                
                # Verify result
                if result != item["text"]:
                    errors += 1
                
                operation_duration = (time.perf_counter() - operation_start) * 1000
                durations.append(operation_duration)
                
            except Exception as e:
                logger.debug(f"Operation failed: {e}")
                errors += 1
                durations.append(float('inf'))  # Will be handled by outlier detection
        
        total_duration = (time.time() - start_time) * 1000
        
        # Track memory after benchmark
        memory_after = self.memory_tracker.get_memory_usage()
        memory_delta = self.memory_tracker.calculate_memory_delta(memory_before, memory_after)
        
        # Calculate statistics
        stats = self.calculator.calculate_statistics(durations)
        success_rate = (iterations - errors) / iterations
        
        return BenchmarkResult(
            operation_type="basic_operations",
            duration_ms=total_duration,
            memory_peak_mb=memory_after.get("process_mb", 0),
            iterations=iterations,
            avg_duration_ms=stats.get("mean", 0),
            min_duration_ms=stats.get("min", 0),
            max_duration_ms=stats.get("max", 0),
            p95_duration_ms=stats.get("p95", 0),
            p99_duration_ms=stats.get("p99", 0),
            std_dev_ms=stats.get("std_dev", 0),
            operations_per_second=(iterations / total_duration * 1000) if total_duration > 0 else 0,
            success_rate=success_rate,
            memory_usage_mb=memory_delta.get("process_mb", 0),
            median_duration_ms=stats.get("median", 0),
            error_count=errors,
            test_data_size_bytes=sum(item.get("expected_size_bytes", 0) for item in test_data)
        )
    
    async def _perform_warmup(self, cache: CacheInterface, warmup_iterations: int):
        """Perform warmup operations to stabilize performance measurements."""
        if warmup_iterations <= 0:
            return
        
        logger.debug(f"Performing {warmup_iterations} warmup operations")
        warmup_data = self.data_generator.generate_basic_operations_data(warmup_iterations)
        
        for item in warmup_data:
            try:
                await cache.set(item["key"], item["text"])
                await cache.get(item["key"])
            except Exception:
                pass  # Ignore warmup errors
    
    async def run_comprehensive_benchmark_suite(self, cache: CacheInterface, include_compression: bool = True) -> BenchmarkSuite:
        """
        Run comprehensive benchmark suite covering all cache performance aspects.
        
        Args:
            cache: Cache implementation to benchmark
            include_compression: Whether to include compression benchmarks
        
        Returns:
            BenchmarkSuite: Complete benchmark results with analysis
        """
        logger.info("Starting comprehensive cache benchmark suite")
        suite_start_time = time.time()
        
        results = []
        failed_benchmarks = []
        
        # Basic operations benchmark
        try:
            basic_result = await self.benchmark_basic_operations(cache)
            results.append(basic_result)
            logger.info(f"Basic operations: {basic_result.avg_duration_ms:.2f}ms avg")
        except Exception as e:
            logger.error(f"Basic operations benchmark failed: {e}")
            failed_benchmarks.append("basic_operations")
        
        # TODO: Add other benchmark types in future deliverables
        # - Memory cache performance benchmark
        # - Compression efficiency benchmark
        # - Concurrent access benchmark
        
        total_duration_ms = (time.time() - suite_start_time) * 1000
        pass_rate = len(results) / (len(results) + len(failed_benchmarks)) if (len(results) + len(failed_benchmarks)) > 0 else 0
        
        # Calculate overall performance grade
        if results:
            avg_performance = sum(r.avg_duration_ms for r in results) / len(results)
            if avg_performance <= self.config.thresholds.basic_operations_avg_ms:
                performance_grade = "Good"
            elif avg_performance <= self.config.thresholds.basic_operations_p95_ms:
                performance_grade = "Acceptable"
            else:
                performance_grade = "Poor"
        else:
            performance_grade = "Failed"
        
        return BenchmarkSuite(
            name="Comprehensive Cache Performance Suite",
            results=results,
            total_duration_ms=total_duration_ms,
            pass_rate=pass_rate,
            failed_benchmarks=failed_benchmarks,
            performance_grade=performance_grade,
            memory_efficiency_grade="Good",  # TODO: Calculate based on memory benchmarks
            environment_info={
                "config": self.config.environment,
                "iterations": self.config.default_iterations,
                "warmup": self.config.warmup_iterations,
                "memory_tracking": self.config.enable_memory_tracking,
                "compression_tests": self.config.enable_compression_tests
            }
        )
    
    async def compare_before_after_refactoring(self, original_cache: CacheInterface, new_cache: CacheInterface) -> ComparisonResult:
        """
        Compare performance between original and refactored cache implementations.
        
        Args:
            original_cache: Original cache implementation
            new_cache: New/refactored cache implementation
            
        Returns:
            ComparisonResult with detailed performance comparison
        """
        logger.info("Starting before/after refactoring comparison")
        
        # Benchmark original implementation
        original_result = await self.benchmark_basic_operations(original_cache)
        
        # Benchmark new implementation
        new_result = await self.benchmark_basic_operations(new_cache)
        
        # Calculate performance changes
        performance_change = 0.0
        memory_change = 0.0
        ops_change = 0.0
        
        if original_result.avg_duration_ms > 0:
            performance_change = ((new_result.avg_duration_ms - original_result.avg_duration_ms) / original_result.avg_duration_ms) * 100
        
        if original_result.memory_usage_mb > 0:
            memory_change = ((new_result.memory_usage_mb - original_result.memory_usage_mb) / original_result.memory_usage_mb) * 100
        
        if original_result.operations_per_second > 0:
            ops_change = ((new_result.operations_per_second - original_result.operations_per_second) / original_result.operations_per_second) * 100
        
        # Detect regressions
        timing_regressions = self.regression_detector.detect_timing_regressions(original_result, new_result)
        memory_regressions = self.regression_detector.detect_memory_regressions(original_result, new_result)
        regression_detected = len(timing_regressions) > 0 or len(memory_regressions) > 0
        
        return ComparisonResult(
            original_cache_results=original_result,
            new_cache_results=new_result,
            performance_change_percent=performance_change,
            memory_change_percent=memory_change,
            operations_per_second_change=ops_change,
            baseline_cache_name="Original Cache",
            comparison_cache_name="Refactored Cache",
            regression_detected=regression_detected,
            improvement_areas=["timing"] if performance_change < 0 else [],
            degradation_areas=["timing"] if performance_change > 0 else [],
            recommendation="Performance analysis complete" if not regression_detected else "Review regressions before deployment"
        )
    
    def get_reporter(self, format: str = "text"):
        """Get appropriate reporter for specified format."""
        return ReporterFactory.get_reporter(format)
    
    def generate_performance_report(self, suite: BenchmarkSuite, format: str = "text") -> str:
        """Generate performance report in specified format."""
        reporter = self.get_reporter(format)
        return reporter.generate_report(suite)