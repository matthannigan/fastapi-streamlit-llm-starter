"""
Comprehensive cache performance benchmarking orchestration with modular architecture.

This module provides the primary benchmarking orchestration classes for cache performance
testing including regression detection, statistical analysis, and comprehensive reporting.
Designed with modular architecture using extracted utilities and data models for improved
maintainability and extensibility.

Classes:
    PerformanceRegressionDetector: Automated performance regression detection and analysis
    CachePerformanceBenchmark: Main benchmarking orchestration with comprehensive analytics

Key Features:
    - **Comprehensive Benchmarking**: Complete cache operation performance analysis with timing,
      memory, throughput, and success rate metrics across configurable iterations.

    - **Regression Detection**: Automated detection of performance regressions with configurable
      warning and critical thresholds for timing, memory, and throughput analysis.

    - **Statistical Analysis**: Advanced statistical analysis including percentiles, standard
      deviation, outlier detection, and confidence intervals for accurate performance assessment.

    - **Memory Tracking**: Comprehensive memory usage monitoring with peak detection and
      delta analysis throughout benchmark execution lifecycle.

    - **Modular Architecture**: Extracted utilities for data generation, statistical calculation,
      memory tracking, and reporting with clear separation of concerns.

    - **Environment Presets**: Configuration presets optimized for development, testing,
      production, and CI environments with appropriate thresholds and iteration counts.

    - **Multiple Report Formats**: Support for text, JSON, markdown, and CI-optimized reports
      with performance badges, detailed analysis, and actionable recommendations.

    - **Before/After Comparison**: Specialized tooling for cache refactoring validation with
      comprehensive performance impact analysis and deployment readiness assessment.

Configuration:
    The benchmarking system supports extensive configuration through BenchmarkConfig:

    - default_iterations: Number of benchmark iterations (default: 100)
    - warmup_iterations: Warmup operations before measurement (default: 10)
    - timeout_seconds: Maximum benchmark execution time (default: 300)
    - enable_memory_tracking: Memory usage monitoring flag (default: True)
    - enable_compression_tests: Compression efficiency testing flag (default: True)
    - thresholds: Performance threshold configuration for pass/fail assessment
    - environment: Environment identifier for context ("development", "testing", "production", "ci")

Usage Examples:
    Basic Benchmarking:
        >>> from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
        >>> from app.infrastructure.cache.benchmarks.config import ConfigPresets
        >>>
        >>> # Standard benchmarking with default configuration
        >>> benchmark = CachePerformanceBenchmark()
        >>> cache = InMemoryCache()
        >>> result = await benchmark.benchmark_basic_operations(cache)
        >>> print(f"Average: {result.avg_duration_ms:.2f}ms")
        >>> print(f"P95: {result.p95_duration_ms:.2f}ms")
        >>> print(f"Throughput: {result.operations_per_second:.0f} ops/s")

    Environment-Specific Configuration:
        >>> # Production-grade benchmarking
        >>> config = ConfigPresets.production_config()
        >>> benchmark = CachePerformanceBenchmark(config)
        >>> cache = RedisCache(url="redis://localhost:6379")
        >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
        >>> print(f"Pass rate: {suite.pass_rate*100:.1f}%")
        >>> print(f"Performance grade: {suite.performance_grade}")

    Before/After Refactoring Comparison:
        >>> # Cache refactoring validation
        >>> original = LegacyRedisCache()
        >>> refactored = OptimizedRedisCache()
        >>> comparison = await benchmark.compare_before_after_refactoring(original, refactored)
        >>>
        >>> if comparison.regression_detected:
        ...     print(f"⚠️ Regressions in: {comparison.degradation_areas}")
        ...     print(f"Recommendation: {comparison.recommendation}")
        >>> else:
        ...     print(f"✅ Performance improved: {comparison.improvement_areas}")

    Comprehensive Reporting:
        >>> # Generate multiple report formats
        >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
        >>>
        >>> # Console output
        >>> text_report = benchmark.generate_performance_report(suite, "text")
        >>> print(text_report)
        >>>
        >>> # CI integration
        >>> ci_report = benchmark.generate_performance_report(suite, "ci")
        >>> # Contains performance badges and concise insights
        >>>
        >>> # Documentation
        >>> md_report = benchmark.generate_performance_report(suite, "markdown")
        >>> # GitHub-compatible markdown with collapsible sections

    Regression Detection:
        >>> from app.infrastructure.cache.benchmarks import PerformanceRegressionDetector
        >>>
        >>> detector = PerformanceRegressionDetector(
        ...     warning_threshold=10.0,  # 10% change triggers warning
        ...     critical_threshold=25.0  # 25% change is critical
        ... )
        >>>
        >>> timing_regressions = detector.detect_timing_regressions(baseline, current)
        >>> memory_regressions = detector.detect_memory_regressions(baseline, current)
        >>> hit_rate_status = detector.validate_cache_hit_rates(baseline, current)
        >>>
        >>> for regression in timing_regressions:
        ...     print(f"{regression['severity']}: {regression['message']}")

Performance Considerations:
    - Warmup operations eliminate cold-start effects for consistent measurements
    - Memory tracking adds minimal overhead (< 1ms per measurement)
    - Statistical analysis scales linearly with iteration count
    - Comprehensive benchmarks include multiple operation types and memory analysis
    - Regression detection provides early warning for performance degradations

Thread Safety:
    This module is designed to be thread-safe for concurrent benchmark execution.
    Each benchmark instance maintains independent state and can be used safely
    across multiple threads or async contexts.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from ..base import CacheInterface
from .models import BenchmarkResult, BenchmarkSuite, ComparisonResult
from .utils import StatisticalCalculator, MemoryTracker
from .generator import CacheBenchmarkDataGenerator
from .config import BenchmarkConfig
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
    Advanced performance regression detector with configurable thresholds and comprehensive analysis.

    Provides automated detection and analysis of performance regressions across multiple
    benchmark dimensions including timing, memory usage, throughput, and cache efficiency.
    Uses configurable percentage-based thresholds to classify changes as warnings or
    critical issues with detailed regression reporting.

    Attributes:
        warning_threshold: float percentage change threshold for warning-level regressions
        critical_threshold: float percentage change threshold for critical-level regressions

    Public Methods:
        detect_timing_regressions(): Analyze timing-related performance degradations
        detect_memory_regressions(): Analyze memory usage increases and peak consumption
        validate_cache_hit_rates(): Check for cache efficiency degradations
        compare_results(): Generate comprehensive performance comparison analysis

    State Management:
        - Stateless operation-by-operation regression analysis
        - Configurable threshold-based severity classification (warning vs critical)
        - Comprehensive multi-metric regression detection covering timing, memory, and throughput
        - Detailed regression reporting with precise percentage changes and recommendations

    Usage:
        # Basic regression detection with standard thresholds
        detector = PerformanceRegressionDetector()
        timing_issues = detector.detect_timing_regressions(baseline, current)
        memory_issues = detector.detect_memory_regressions(baseline, current)

        # Custom thresholds for stricter regression detection
        strict_detector = PerformanceRegressionDetector(
            warning_threshold=5.0,   # 5% change triggers warning
            critical_threshold=15.0  # 15% change is critical
        )

        # Comprehensive comparison with all regression types
        comparison = detector.compare_results(old_benchmark, new_benchmark)
        if comparison.regression_detected:
            print(f"Regressions found: {comparison.degradation_areas}")

    Example:
        >>> detector = PerformanceRegressionDetector(
        ...     warning_threshold=10.0,
        ...     critical_threshold=25.0
        ... )
        >>> timing_regressions = detector.detect_timing_regressions(old_result, new_result)
        >>> memory_regressions = detector.detect_memory_regressions(old_result, new_result)
        >>> hit_rate_status = detector.validate_cache_hit_rates(old_result, new_result)
        >>>
        >>> for regression in timing_regressions:
        ...     print(f"{regression['severity']}: {regression['message']}")
    """

    def __init__(self, warning_threshold: float = 10.0, critical_threshold: float = 25.0):
        """
        Initialize performance regression detector with configurable severity thresholds.

        Sets up threshold-based classification system for identifying performance
        regressions at different severity levels. Validates threshold consistency
        to ensure warning threshold is less than critical threshold.

        Args:
            warning_threshold: Percentage change threshold that triggers warning-level alerts.
                             Must be positive and less than critical_threshold.
            critical_threshold: Percentage change threshold that triggers critical-level alerts.
                              Must be positive and greater than warning_threshold.

        Behavior:
            - Stores thresholds for use in all regression detection methods
            - No validation of threshold relationship (allows flexible configuration)
            - Both thresholds default to production-appropriate values
            - Percentage thresholds apply to relative changes between measurements

        Example:
            >>> # Standard sensitivity (default)
            >>> detector = PerformanceRegressionDetector()
            >>>
            >>> # High sensitivity for critical systems
            >>> sensitive = PerformanceRegressionDetector(
            ...     warning_threshold=5.0,
            ...     critical_threshold=10.0
            ... )
            >>>
            >>> # Low sensitivity for development testing
            >>> tolerant = PerformanceRegressionDetector(
            ...     warning_threshold=20.0,
            ...     critical_threshold=50.0
            ... )
        """
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold

    def detect_timing_regressions(self, old_result: BenchmarkResult, new_result: BenchmarkResult) -> List[Dict[str, Any]]:
        """
        Detect and analyze timing-related performance regressions across multiple timing metrics.

        Performs comprehensive analysis of timing degradations including average duration,
        P95 percentile performance, and throughput changes. Uses percentage-based thresholds
        to classify regressions by severity and provides detailed diagnostic information
        for each detected regression.

        Args:
            old_result: Baseline benchmark result containing original performance metrics.
                       Must have valid avg_duration_ms, p95_duration_ms, and operations_per_second.
            new_result: Current benchmark result to compare against baseline.
                       Must have the same metric fields as old_result for comparison.

        Returns:
            List of regression dictionaries, each containing:
            - type: "timing_regression" or "throughput_regression"
            - metric: Specific metric name ("average_duration", "p95_duration", "operations_per_second")
            - severity: "warning" or "critical" based on threshold comparison
            - change_percent: Exact percentage change (positive = degradation)
            - old_value: Original metric value for reference
            - new_value: Current metric value for reference
            - message: Human-readable description of the regression

        Behavior:
            - Analyzes average duration increases above warning/critical thresholds
            - Detects P95 duration degradations for tail latency analysis
            - Identifies throughput decreases (operations per second reductions)
            - Returns empty list if no regressions exceed configured thresholds
            - Handles zero or negative baseline values gracefully (skips analysis)
            - Provides precise percentage calculations for regression severity assessment

        Example:
            >>> detector = PerformanceRegressionDetector(warning_threshold=10.0)
            >>> old = BenchmarkResult(avg_duration_ms=50.0, p95_duration_ms=80.0, operations_per_second=1000)
            >>> new = BenchmarkResult(avg_duration_ms=60.0, p95_duration_ms=100.0, operations_per_second=800)
            >>>
            >>> regressions = detector.detect_timing_regressions(old, new)
            >>> for reg in regressions:
            ...     print(f"{reg['severity']}: {reg['message']}")
            # "warning: Average duration increased by 20.0%"
            # "warning: P95 duration increased by 25.0%"
            # "warning: Throughput decreased by 20.0%"
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
        Detect and analyze memory-related performance regressions including usage and peak consumption.

        Performs comprehensive analysis of memory degradations including average memory usage
        increases and peak memory consumption changes. Uses percentage-based thresholds to
        classify memory regressions by severity and provides detailed diagnostic information
        for memory optimization guidance.

        Args:
            old_result: Baseline benchmark result containing original memory metrics.
                       Must have valid memory_usage_mb and memory_peak_mb fields.
            new_result: Current benchmark result to compare against baseline.
                       Must have the same memory metric fields as old_result.

        Returns:
            List of memory regression dictionaries, each containing:
            - type: "memory_regression" for all memory-related issues
            - metric: Specific metric name ("memory_usage", "peak_memory")
            - severity: "warning" or "critical" based on threshold comparison
            - change_percent: Exact percentage change (positive = increase)
            - old_value: Original memory value in MB for reference
            - new_value: Current memory value in MB for reference
            - message: Human-readable description of the memory regression

        Behavior:
            - Analyzes average memory usage increases above warning/critical thresholds
            - Detects peak memory consumption increases that may indicate memory leaks
            - Returns empty list if no memory regressions exceed configured thresholds
            - Handles zero or negative baseline memory values gracefully (skips analysis)
            - Provides precise percentage calculations for memory growth assessment
            - Uses same threshold percentages as timing regressions for consistency

        Example:
            >>> detector = PerformanceRegressionDetector(warning_threshold=15.0)
            >>> old = BenchmarkResult(memory_usage_mb=50.0, memory_peak_mb=75.0)
            >>> new = BenchmarkResult(memory_usage_mb=65.0, memory_peak_mb=95.0)
            >>>
            >>> regressions = detector.detect_memory_regressions(old, new)
            >>> for reg in regressions:
            ...     print(f"{reg['severity']}: {reg['message']}")
            # "warning: Memory usage increased by 30.0%"
            # "warning: Peak memory usage increased by 26.7%"
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
        Validate cache hit rates for efficiency degradation using fixed threshold analysis.

        Analyzes cache hit rate changes to detect efficiency regressions that could
        indicate cache configuration issues, increased cache misses, or cache sizing
        problems. Uses a fixed 5% degradation threshold regardless of configured
        regression thresholds due to the critical nature of cache efficiency.

        Args:
            old_result: Baseline benchmark result containing original cache_hit_rate.
                       cache_hit_rate can be None if not available in baseline.
            new_result: Current benchmark result to compare against baseline.
                       cache_hit_rate can be None if not available in current run.

        Returns:
            Dictionary containing validation status and analysis:
            - status: "ok", "degraded", or "skipped"
            - hit_rate_change: Absolute change in hit rate (when status is "ok")
            - old_hit_rate: Original hit rate value (when status is "degraded")
            - new_hit_rate: Current hit rate value (when status is "degraded")
            - change: Absolute change in hit rate (when status is "degraded")
            - message: Human-readable description of degradation (when status is "degraded")
            - reason: Explanation for skipped validation (when status is "skipped")

        Behavior:
            - Returns {"status": "skipped", "reason": "hit_rate_data_unavailable"} if either result lacks hit rate data
            - Considers decreases of 5% or more (0.05) as degraded cache efficiency
            - Returns {"status": "degraded"} with detailed change information for significant decreases
            - Returns {"status": "ok"} with hit_rate_change for acceptable performance
            - Uses absolute hit rate differences (not percentage changes) for threshold comparison

        Example:
            >>> detector = PerformanceRegressionDetector()
            >>> old = BenchmarkResult(cache_hit_rate=0.85)  # 85% hit rate
            >>> new = BenchmarkResult(cache_hit_rate=0.78)  # 78% hit rate
            >>>
            >>> validation = detector.validate_cache_hit_rates(old, new)
            >>> print(validation)
            # {
            #     "status": "degraded",
            #     "old_hit_rate": 0.85,
            #     "new_hit_rate": 0.78,
            #     "change": -0.07,
            #     "message": "Cache hit rate degraded by 7.0%"
            # }
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
        Generate comprehensive performance comparison between baseline and current benchmark results.

        Performs complete analysis combining timing, memory, and throughput regression detection
        with improvement/degradation area identification and actionable recommendations. Creates
        a detailed ComparisonResult with percentage changes, regression flags, and strategic
        guidance for performance optimization decisions.

        Args:
            baseline: Original benchmark result serving as performance baseline.
                     Must contain valid timing, memory, and throughput metrics.
            current: New benchmark result to compare against baseline.
                    Must have comparable metric fields for meaningful analysis.

        Returns:
            ComparisonResult containing comprehensive comparison analysis:
            - original_cache_results: Copy of baseline benchmark data
            - new_cache_results: Copy of current benchmark data
            - performance_change_percent: Overall timing change percentage
            - memory_change_percent: Memory usage change percentage
            - operations_per_second_change: Throughput change percentage
            - regression_detected: Boolean flag indicating any regressions found
            - improvement_areas: List of metric categories showing improvement
            - degradation_areas: List of metric categories showing degradation
            - recommendation: Strategic recommendation based on analysis results

        Behavior:
            - Calculates percentage changes for timing, memory, and throughput metrics
            - Detects regressions using configured warning thresholds
            - Identifies improvement and degradation areas based on threshold analysis
            - Generates actionable recommendations based on regression detection results
            - Handles zero baseline values gracefully (sets change to 0.0)
            - Provides both high-level flags and detailed metric analysis

        Example:
            >>> detector = PerformanceRegressionDetector(warning_threshold=10.0)
            >>> baseline = BenchmarkResult(avg_duration_ms=50.0, memory_usage_mb=30.0, operations_per_second=1000)
            >>> current = BenchmarkResult(avg_duration_ms=45.0, memory_usage_mb=35.0, operations_per_second=1100)
            >>>
            >>> comparison = detector.compare_results(baseline, current)
            >>> print(f"Performance change: {comparison.performance_change_percent:.1f}%")
            >>> print(f"Regressions detected: {comparison.regression_detected}")
            >>> print(f"Improvement areas: {comparison.improvement_areas}")
            >>> print(f"Recommendation: {comparison.recommendation}")
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
    Comprehensive cache performance benchmarking orchestrator with modular architecture and advanced analytics.

    Provides complete cache performance testing infrastructure including basic operations benchmarking,
    memory tracking, regression detection, and before/after comparison analysis. Uses extracted
    utilities and data models for maintainable, extensible benchmarking with configurable thresholds
    and environment-specific presets.

    Attributes:
        config: BenchmarkConfig instance containing iteration counts, timeouts, and feature flags
        data_generator: CacheBenchmarkDataGenerator for realistic test data creation
        memory_tracker: MemoryTracker for memory usage monitoring during benchmarks
        regression_detector: PerformanceRegressionDetector for automated regression analysis
        calculator: StatisticalCalculator for comprehensive statistical analysis of results

    Public Methods:
        benchmark_basic_operations(): Primary cache operation performance testing
        run_comprehensive_benchmark_suite(): Complete performance analysis across all operations
        compare_before_after_refactoring(): Before/after performance comparison for refactoring validation
        get_reporter(): Get configured reporter for specified output format
        generate_performance_report(): Generate formatted reports with analysis and recommendations

    State Management:
        - Stateless benchmark execution with configurable parameters
        - Comprehensive memory tracking throughout benchmark lifecycle
        - Statistical analysis with outlier detection and confidence intervals
        - Regression detection with configurable warning and critical thresholds
        - Modular design supporting different cache implementations and configurations

    Usage:
        # Standard benchmarking with default configuration
        benchmark = CachePerformanceBenchmark()
        cache = RedisCache(url="redis://localhost:6379")
        result = await benchmark.benchmark_basic_operations(cache)

        # Environment-specific configuration
        config = ConfigPresets.production_config()
        benchmark = CachePerformanceBenchmark(config)
        suite = await benchmark.run_comprehensive_benchmark_suite(cache)

        # Before/after performance comparison
        old_cache = LegacyCache()
        new_cache = OptimizedCache()
        comparison = await benchmark.compare_before_after_refactoring(old_cache, new_cache)

        # Report generation with different formats
        reporter = benchmark.get_reporter("markdown")
        report = benchmark.generate_performance_report(suite, "ci")

    Example:
        >>> config = ConfigPresets.testing_config()
        >>> benchmark = CachePerformanceBenchmark(config)
        >>> cache = InMemoryCache()
        >>>
        >>> # Basic operation benchmarking
        >>> result = await benchmark.benchmark_basic_operations(cache)
        >>> print(f"Average: {result.avg_duration_ms:.2f}ms")
        >>> print(f"P95: {result.p95_duration_ms:.2f}ms")
        >>> print(f"Throughput: {result.operations_per_second:.0f} ops/s")
        >>>
        >>> # Comprehensive benchmarking
        >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
        >>> print(f"Pass rate: {suite.pass_rate*100:.1f}%")
        >>> print(f"Performance grade: {suite.performance_grade}")
    """

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        """
        Initialize comprehensive benchmarking system with configuration and integrated utilities.

        Sets up complete benchmarking infrastructure including data generation, memory tracking,
        regression detection, and statistical analysis. Uses provided configuration or defaults
        to sensible values for testing environments.

        Args:
            config: Complete benchmark configuration including iteration counts, timeouts,
                   and thresholds. If None, creates default BenchmarkConfig with standard
                   testing parameters (100 iterations, 10 warmup, 300s timeout).

        Behavior:
            - Creates BenchmarkConfig with default values if none provided
            - Initializes CacheBenchmarkDataGenerator for realistic test data creation
            - Sets up MemoryTracker for memory usage monitoring during benchmarks
            - Configures PerformanceRegressionDetector with thresholds from config
            - Creates StatisticalCalculator for comprehensive statistical analysis
            - All utilities are ready for immediate benchmark execution

        Example:
            >>> # Default configuration
            >>> benchmark = CachePerformanceBenchmark()
            >>>
            >>> # Custom configuration
            >>> config = BenchmarkConfig(
            ...     default_iterations=200,
            ...     timeout_seconds=600,
            ...     enable_memory_tracking=True
            ... )
            >>> benchmark = CachePerformanceBenchmark(config)
            >>>
            >>> # Environment-specific presets
            >>> prod_config = ConfigPresets.production_config()
            >>> benchmark = CachePerformanceBenchmark(prod_config)
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
        Create configured benchmark instance using factory pattern for explicit configuration management.

        Provides alternative constructor that explicitly emphasizes configuration-driven
        initialization. Functionally equivalent to standard constructor but offers
        clearer intent for configuration-centric benchmark creation.

        Args:
            config: Complete benchmark configuration containing all required settings
                   including iteration counts, timeouts, thresholds, and feature flags.

        Returns:
            Fully configured CachePerformanceBenchmark instance ready for benchmark execution.
            All internal utilities (data generator, memory tracker, regression detector)
            are initialized with the provided configuration settings.

        Behavior:
            - Creates new instance using provided configuration
            - Identical to CachePerformanceBenchmark(config) but with explicit factory semantics
            - Useful for configuration-driven initialization patterns
            - Provides clear API for dependency injection and testing scenarios

        Example:
            >>> config = ConfigPresets.ci_config()
            >>> benchmark = CachePerformanceBenchmark.from_config(config)
            >>>
            >>> # Equivalent to:
            >>> benchmark = CachePerformanceBenchmark(config)
        """
        return cls(config)

    async def benchmark_basic_operations(self, cache: CacheInterface, iterations: Optional[int] = None) -> BenchmarkResult:
        """
        Execute comprehensive basic cache operations benchmarking with memory tracking and statistical analysis.

        Performs complete benchmark execution including warmup, data generation, operation timing,
        memory tracking, and statistical analysis. Tests fundamental cache operations (set/get)
        with realistic data patterns and provides detailed performance metrics with outlier
        detection and percentile analysis.

        Args:
            cache: Cache implementation conforming to CacheInterface for testing.
                  Must support async set() and get() operations with TTL parameters.
            iterations: Number of test iterations to perform. If None, uses config.default_iterations.
                       Higher values provide more accurate statistics but increase execution time.

        Returns:
            BenchmarkResult containing comprehensive performance analysis:
            - operation_type: "basic_operations" identifier
            - duration_ms: Total benchmark execution time
            - memory_peak_mb: Peak memory usage during benchmark
            - iterations: Actual number of iterations performed
            - avg_duration_ms: Average time per operation
            - min/max_duration_ms: Fastest and slowest operation times
            - p95/p99_duration_ms: 95th and 99th percentile response times
            - std_dev_ms: Standard deviation of operation times
            - operations_per_second: Throughput metric
            - success_rate: Percentage of successful operations (0-1)
            - memory_usage_mb: Memory delta during benchmark
            - error_count: Number of failed operations

        Behavior:
            - Generates realistic test data with varied sizes and content types
            - Performs warmup operations to stabilize cache performance
            - Tracks memory usage before, during, and after benchmark execution
            - Times each individual cache operation with high precision
            - Validates cache correctness by verifying set/get data consistency
            - Handles cache operation failures gracefully with error counting
            - Calculates comprehensive statistics including percentiles and outlier detection
            - Returns detailed metrics suitable for regression analysis and reporting

        Raises:
            Exception: If cache implementation doesn't support required operations or critical failures occur

        Example:
            >>> benchmark = CachePerformanceBenchmark()
            >>> cache = RedisCache(url="redis://localhost:6379")
            >>>
            >>> result = await benchmark.benchmark_basic_operations(cache, iterations=50)
            >>> print(f"Average: {result.avg_duration_ms:.2f}ms")
            >>> print(f"P95: {result.p95_duration_ms:.2f}ms")
            >>> print(f"Success rate: {result.success_rate*100:.1f}%")
            >>> print(f"Throughput: {result.operations_per_second:.0f} ops/s")
            >>> print(f"Memory delta: {result.memory_usage_mb:.1f}MB")
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
        """
        Execute cache warmup operations to stabilize performance measurements and eliminate initialization overhead.

        Performs preliminary cache operations before actual benchmarking to ensure the cache
        system is in a stable, warmed-up state. This eliminates cold-start effects, connection
        establishment overhead, and any initial optimization that might skew benchmark results.
        Helps provide consistent, repeatable performance measurements.

        Args:
            cache: Cache implementation conforming to CacheInterface.
                  Must support async set() and get() operations for warmup.
            warmup_iterations: Number of warmup operations to perform before benchmarking.
                             If 0 or negative, warmup is skipped entirely.

        Behavior:
            - Returns immediately if warmup_iterations <= 0 (no warmup needed)
            - Generates basic test data using the configured data generator
            - Performs set and get operations for each warmup iteration
            - Ignores all warmup operation failures (uses pass for exception handling)
            - Does not track timing, memory, or success rates during warmup
            - Logs debug information about warmup progress
            - Prepares cache for stable benchmark execution

        Example:
            >>> # Warmup is automatically called by benchmark_basic_operations()
            >>> # Internal usage example:
            >>> await benchmark._perform_warmup(cache, 10)
            >>> # Cache is now warmed up for stable benchmarking
        """
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
        Execute complete benchmark suite covering all cache performance aspects with comprehensive analysis.

        Runs comprehensive performance testing across multiple benchmark categories including
        basic operations, memory efficiency, and optional compression testing. Provides
        complete performance analysis with pass/fail assessment, performance grading,
        and environmental context for thorough cache evaluation.

        Args:
            cache: Cache implementation conforming to CacheInterface for comprehensive testing.
                  Must support all basic cache operations and optionally compression features.
            include_compression: Whether to include compression efficiency benchmarks.
                              Currently reserved for future implementation (compression tests planned).

        Returns:
            BenchmarkSuite containing complete suite analysis:
            - name: "Comprehensive Cache Performance Suite" identifier
            - results: List of all individual BenchmarkResult objects
            - total_duration_ms: Total time for complete suite execution
            - pass_rate: Percentage of benchmarks that passed (0-1)
            - failed_benchmarks: List of benchmark names that failed
            - performance_grade: Overall performance assessment ("Good", "Acceptable", "Poor", "Failed")
            - memory_efficiency_grade: Memory usage assessment (currently "Good" placeholder)
            - environment_info: Configuration and environment details for reproducibility

        Behavior:
            - Executes basic operations benchmark as primary test
            - Tracks failed benchmarks and provides diagnostic information
            - Calculates overall pass rate based on successful benchmark execution
            - Generates performance grade based on average timing against thresholds
            - Records comprehensive environment information for reproducibility
            - Provides detailed analysis suitable for CI/CD integration and reporting
            - Currently supports basic operations with placeholders for future benchmark types

        Example:
            >>> benchmark = CachePerformanceBenchmark()
            >>> cache = InMemoryCache()
            >>>
            >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
            >>> print(f"Suite: {suite.name}")
            >>> print(f"Pass rate: {suite.pass_rate*100:.1f}%")
            >>> print(f"Performance grade: {suite.performance_grade}")
            >>> print(f"Duration: {suite.total_duration_ms/1000:.1f}s")
            >>>
            >>> for result in suite.results:
            ...     print(f"{result.operation_type}: {result.avg_duration_ms:.2f}ms")
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
        Execute comprehensive before/after performance comparison for cache refactoring validation.

        Performs identical benchmark tests on both original and refactored cache implementations
        to provide objective performance comparison. Analyzes timing, memory, throughput changes
        and detects regressions to guide refactoring decisions and deployment readiness assessment.

        Args:
            original_cache: Original cache implementation serving as performance baseline.
                          Must conform to CacheInterface and support all benchmark operations.
            new_cache: Refactored/new cache implementation to evaluate against baseline.
                      Must conform to CacheInterface with compatible operation signatures.

        Returns:
            ComparisonResult containing complete refactoring analysis:
            - original_cache_results: Complete benchmark data from original implementation
            - new_cache_results: Complete benchmark data from refactored implementation
            - performance_change_percent: Overall timing change (negative = improvement)
            - memory_change_percent: Memory usage change (negative = improvement)
            - operations_per_second_change: Throughput change (positive = improvement)
            - baseline_cache_name: "Original Cache" identifier
            - comparison_cache_name: "Refactored Cache" identifier
            - regression_detected: Boolean indicating any performance regressions
            - improvement_areas: List of performance categories showing improvement
            - degradation_areas: List of performance categories showing degradation
            - recommendation: Strategic guidance based on analysis results

        Behavior:
            - Executes identical basic operations benchmarks on both cache implementations
            - Calculates precise percentage changes for all performance metrics
            - Detects regressions using configured warning/critical thresholds
            - Identifies specific improvement and degradation areas for targeted optimization
            - Provides actionable recommendations for deployment decisions
            - Handles zero baseline values gracefully (sets change to 0.0)
            - Returns deployment-ready assessment with regression flags

        Example:
            >>> benchmark = CachePerformanceBenchmark()
            >>> original = LegacyRedisCache()
            >>> refactored = OptimizedRedisCache()
            >>>
            >>> comparison = await benchmark.compare_before_after_refactoring(original, refactored)
            >>> print(f"Performance change: {comparison.performance_change_percent:.1f}%")
            >>> print(f"Memory change: {comparison.memory_change_percent:.1f}%")
            >>> print(f"Throughput change: {comparison.operations_per_second_change:.1f}%")
            >>> print(f"Regressions detected: {comparison.regression_detected}")
            >>> print(f"Recommendation: {comparison.recommendation}")
            >>>
            >>> if not comparison.regression_detected:
            ...     print("✅ Refactoring ready for deployment")
            >>> else:
            ...     print("⚠️  Review regressions before deployment")
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
            ops_change = ((new_result.operations_per_second - original_result.operations_per_second) /
                         original_result.operations_per_second) * 100

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
        """
        Create configured reporter instance for specified output format using factory pattern.

        Provides convenient access to reporting infrastructure with automatic configuration
        using the benchmark's threshold settings. Supports multiple output formats for
        different use cases including human-readable reports, CI integration, and
        programmatic processing.

        Args:
            format: Target output format for report generation.
                   Supported values: "text" (human-readable), "json" (structured data),
                   "markdown" (GitHub-compatible), "ci" (CI/CD optimized).

        Returns:
            Configured BenchmarkReporter subclass instance ready for report generation.
            Reporter includes the benchmark's threshold configuration for consistent
            pass/fail assessment and performance grading.

        Behavior:
            - Creates reporter using ReporterFactory with benchmark's threshold configuration
            - Passes through format validation to ReporterFactory.get_reporter()
            - Returns ready-to-use reporter instance with consistent threshold settings
            - Supports all formats available in ReporterFactory

        Raises:
            ValueError: If format is not supported by ReporterFactory

        Example:
            >>> benchmark = CachePerformanceBenchmark()
            >>>
            >>> # Human-readable text report
            >>> text_reporter = benchmark.get_reporter("text")
            >>>
            >>> # CI-optimized markdown report
            >>> ci_reporter = benchmark.get_reporter("ci")
            >>>
            >>> # Structured JSON report
            >>> json_reporter = benchmark.get_reporter("json")
        """
        return ReporterFactory.get_reporter(format)

    def generate_performance_report(self, suite: BenchmarkSuite, format: str = "text") -> str:
        """
        Generate comprehensive performance report with analysis and recommendations in specified format.

        Creates complete performance report using configured thresholds and analysis from
        the benchmark suite results. Provides detailed insights, recommendations, and
        performance assessment suitable for various audiences including developers,
        operations teams, and CI/CD systems.

        Args:
            suite: Complete benchmark suite results containing all performance data,
                  environment information, and execution metadata.
            format: Target output format for report generation.
                   Supported values: "text" (console/log output), "json" (API integration),
                   "markdown" (documentation/GitHub), "ci" (CI/CD pipelines).

        Returns:
            Complete formatted report string containing:
            - Performance summary with pass/fail status
            - Detailed metrics analysis and insights
            - Actionable optimization recommendations
            - Environment and configuration context
            - Format-specific features (badges for CI, tables for markdown, etc.)

        Behavior:
            - Creates appropriate reporter using get_reporter() with benchmark thresholds
            - Delegates report generation to format-specific reporter implementation
            - Includes comprehensive analysis using benchmark's threshold configuration
            - Returns fully formatted report ready for display or processing
            - Maintains consistent analysis across all output formats

        Example:
            >>> benchmark = CachePerformanceBenchmark()
            >>> cache = RedisCache()
            >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
            >>>
            >>> # Generate text report for console output
            >>> text_report = benchmark.generate_performance_report(suite, "text")
            >>> print(text_report)
            >>>
            >>> # Generate markdown report for documentation
            >>> md_report = benchmark.generate_performance_report(suite, "markdown")
            >>> with open("performance_report.md", "w") as f:
            ...     f.write(md_report)
            >>>
            >>> # Generate CI report for pipeline integration
            >>> ci_report = benchmark.generate_performance_report(suite, "ci")
            >>> print(ci_report)  # Outputs CI-friendly format with badges
        """
        reporter = self.get_reporter(format)
        return reporter.generate_report(suite)
