"""
Performance benchmarking for resilience configuration loading.

This module provides comprehensive performance testing and monitoring
for the resilience configuration system with a target of <100ms loading time.
"""

import time
import json
import os
import statistics
import tracemalloc
from typing import Dict, List, NamedTuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BenchmarkResult(NamedTuple):
    """Result of a performance benchmark."""
    operation: str
    duration_ms: float
    memory_peak_mb: float
    iterations: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    std_dev_ms: float
    success_rate: float
    metadata: Dict[str, Any]


class PerformanceThreshold(Enum):
    """Performance thresholds for different operations."""
    CONFIG_LOADING = 100.0  # <100ms target
    PRESET_ACCESS = 10.0    # <10ms for preset lookup
    VALIDATION = 50.0       # <50ms for validation
    SERVICE_INIT = 200.0    # <200ms for service initialization


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results with analysis."""
    name: str
    results: List[BenchmarkResult]
    total_duration_ms: float
    pass_rate: float
    failed_benchmarks: List[str]
    timestamp: str
    environment_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert benchmark suite to dictionary."""
        # Convert NamedTuple results to dictionaries manually
        results_dict = []
        for result in self.results:
            result_dict = result._asdict()  # NamedTuple has _asdict method
            results_dict.append(result_dict)

        return {
            "name": self.name,
            "results": results_dict,
            "total_duration_ms": self.total_duration_ms,
            "pass_rate": self.pass_rate,
            "failed_benchmarks": self.failed_benchmarks,
            "timestamp": self.timestamp,
            "environment_info": self.environment_info
        }

    def to_json(self) -> str:
        """Convert benchmark suite to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)


class ConfigurationPerformanceBenchmark:
    """
    Comprehensive performance benchmarking suite for resilience configuration loading and validation.

    Provides detailed performance testing and monitoring for the resilience configuration system
    with a target of <100ms loading time. Implements comprehensive metrics collection,
    regression detection, and performance trend analysis to ensure configuration system
    meets production performance requirements.

    Attributes:
        results: List of BenchmarkResult objects storing all benchmark execution results
        baseline_results: Dictionary mapping operation names to baseline performance metrics
                         for regression detection and performance comparison

    Public Methods:
        measure_performance(): Core performance measurement with timing and memory tracking
        benchmark_preset_loading(): Test preset loading performance across all presets
        benchmark_settings_initialization(): Test Settings class initialization performance
        benchmark_resilience_config_loading(): Test complete configuration loading pipeline
        benchmark_service_initialization(): Test AIServiceResilience initialization performance
        benchmark_validation_performance(): Test configuration validation performance
        run_comprehensive_benchmark(): Execute complete benchmark suite with all tests
        analyze_performance_trends(): Analyze performance trends across historical data
        generate_performance_report(): Create human-readable performance analysis report

    State Management:
        - Stateless benchmark execution - no persistent state between test runs
        - Thread-safe execution suitable for concurrent testing environments
        - Results accumulation within single benchmark session for trend analysis
        - Memory-efficient with automatic cleanup of completed benchmark runs

    Usage:
        # Basic benchmarking
        benchmark = ConfigurationPerformanceBenchmark()

        # Run specific benchmark
        result = benchmark.benchmark_preset_loading(iterations=100)
        print(f"Preset loading: {result.avg_duration_ms:.2f}ms avg")

        # Run comprehensive suite
        suite = benchmark.run_comprehensive_benchmark()
        print(f"Overall pass rate: {suite.pass_rate:.1%}")

        # Generate detailed report
        report = benchmark.generate_performance_report(suite)
        print(report)

        # Analyze performance trends
        trends = benchmark.analyze_performance_trends([suite1, suite2, suite3])
        print(f"Performance trend: {trends}")

    Performance Targets:
        - CONFIG_LOADING: <100ms for complete configuration loading
        - PRESET_ACCESS: <10ms for preset lookup operations
        - VALIDATION: <50ms for configuration validation
        - SERVICE_INIT: <200ms for service initialization

    Examples:
        >>> benchmark = ConfigurationPerformanceBenchmark()
        >>> result = benchmark.measure_performance("test_op", lambda: None, iterations=10)
        >>> assert result.avg_duration_ms >= 0
        >>> assert result.success_rate == 1.0
        >>>
        >>> # Test preset loading performance
        >>> preset_result = benchmark.benchmark_preset_loading(iterations=50)
        >>> assert preset_result.operation == "preset_loading"
        >>> assert preset_result.avg_duration_ms < 100  # Should meet target
    """

    def __init__(self) -> None:
        """
        Initialize the performance benchmark suite with empty result storage.

        Behavior:
            - Creates empty results list for accumulating benchmark execution data
            - Initializes baseline results dictionary for performance comparison
            - Sets up logger for benchmark execution tracking
            - Prepares clean state for comprehensive benchmark execution
            - No external dependencies or configuration required

        Examples:
            >>> benchmark = ConfigurationPerformanceBenchmark()
            >>> assert len(benchmark.results) == 0
            >>> assert isinstance(benchmark.baseline_results, dict)
        """
        self.results: List[BenchmarkResult] = []
        self.baseline_results: Dict[str, float] = {}
        logger.info("Initialized ConfigurationPerformanceBenchmark")

    def measure_performance(self, operation_name: str, operation_func: Callable, iterations: int = 1) -> BenchmarkResult:
        """
        Measure operation performance with comprehensive timing and memory tracking.

        Core performance measurement method that executes the specified operation multiple
        times while collecting detailed metrics including timing statistics, memory usage,
        success rates, and execution metadata. Uses tracemalloc for accurate memory
        tracking and high-precision timing for performance analysis.

        Args:
            operation_name: Unique identifier for the operation being measured.
                           Used for result identification, logging, and metrics aggregation
            operation_func: Callable function to measure performance for.
                          Should accept optional metadata parameter for operation context
            iterations: Number of iterations to execute for statistical significance.
                        Must be positive integer, higher values provide more accurate averages
                        but increase execution time. Default: 1

        Returns:
            BenchmarkResult containing comprehensive performance metrics:
            - operation: Name of the measured operation
            - duration_ms: Total execution time across all iterations in milliseconds
            - memory_peak_mb: Peak memory usage during execution in megabytes
            - iterations: Number of iterations executed
            - avg_duration_ms: Average execution time per iteration in milliseconds
            - min_duration_ms: Fastest single iteration execution time
            - max_duration_ms: Slowest single iteration execution time
            - std_dev_ms: Standard deviation of execution times
            - success_rate: Ratio of successful executions to total iterations
            - metadata: Operation-specific metadata provided during execution

        Behavior:
            - Executes operation_func for specified number of iterations
            - Tracks memory usage using tracemalloc for each iteration
            - Measures execution time with high-precision performance counters
            - Captures exceptions and calculates success/failure rates
            - Computes statistical metrics (mean, min, max, standard deviation)
            - Stores results in internal results list for later analysis
            - Logs completion with average execution time for monitoring

        Raises:
            No exceptions raised - all execution errors captured in result metadata
            and reflected in success_rate calculation

        Examples:
            >>> benchmark = ConfigurationPerformanceBenchmark()
            >>> def test_operation(metadata):
            ...     metadata["test"] = "value"
            ...     return "result"
            >>>
            >>> result = benchmark.measure_performance("test_op", test_operation, iterations=5)
            >>> assert result.operation == "test_op"
            >>> assert result.iterations == 5
            >>> assert result.success_rate == 1.0
            >>> assert result.avg_duration_ms > 0
            >>> assert "test" in result.metadata
            >>>
            >>> # Operation with failures
            >>> def failing_operation(metadata):
            ...     if metadata.get("fail_count", 0) < 2:
            ...         metadata["fail_count"] = metadata.get("fail_count", 0) + 1
            ...         raise ValueError("Test error")
            ...     return "success"
            >>>
            >>> result = benchmark.measure_performance("failing_op", failing_operation, iterations=5)
            >>> assert result.success_rate == 0.6  # 3 successes out of 5 attempts
            >>> assert result.metadata.get("error_0") is not None
        """
        metadata: Dict[str, Any] = {}
        durations = []
        memory_peaks = []
        successes = 0

        for i in range(iterations):
            # Start memory tracking
            tracemalloc.start()
            start_time = time.perf_counter()

            try:
                operation_func(metadata)
                successes += 1
            except Exception as e:
                logger.error(f"Benchmark iteration {i+1} failed for {operation_name}: {e}")
                metadata[f"error_{i}"] = str(e)
            finally:
                # Measure time
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000
                durations.append(duration_ms)

                # Measure memory
                current, peak = tracemalloc.get_traced_memory()
                memory_peaks.append(peak / 1024 / 1024)  # Convert to MB
                tracemalloc.stop()

        # Calculate statistics
        if durations:
            result = BenchmarkResult(
                operation=operation_name,
                duration_ms=sum(durations),
                memory_peak_mb=max(memory_peaks) if memory_peaks else 0.0,
                iterations=iterations,
                avg_duration_ms=statistics.mean(durations),
                min_duration_ms=min(durations),
                max_duration_ms=max(durations),
                std_dev_ms=statistics.stdev(durations) if len(durations) > 1 else 0.0,
                success_rate=successes / iterations,
                metadata=metadata
            )

            self.results.append(result)
            logger.info(f"Benchmark completed: {operation_name} - Avg: {result.avg_duration_ms:.2f}ms")
            return result

        # Return empty result if no durations recorded
        result = BenchmarkResult(
            operation=operation_name,
            duration_ms=0.0,
            memory_peak_mb=0.0,
            iterations=iterations,
            avg_duration_ms=0.0,
            min_duration_ms=0.0,
            max_duration_ms=0.0,
            std_dev_ms=0.0,
            success_rate=0.0,
            metadata=metadata
        )
        self.results.append(result)
        return result

    def benchmark_preset_loading(self, iterations: int = 100) -> BenchmarkResult:
        """
        Benchmark preset loading performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for preset loading
        """
        def preset_loading_operation(metadata: Dict[str, Any]) -> None:
            from app.infrastructure.resilience.config_presets import preset_manager

            # Test loading each preset
            presets = ["simple", "development", "production"]
            for preset_name in presets:
                preset = preset_manager.get_preset(preset_name)
                metadata[f"preset_{preset_name}_loaded"] = True

        return self.measure_performance("preset_loading", preset_loading_operation, iterations)

    def benchmark_settings_initialization(self, iterations: int = 50) -> BenchmarkResult:
        """
        Benchmark Settings class initialization performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for settings initialization
        """
        def settings_initialization_operation(metadata: Dict[str, Any]) -> None:
            from app.core.config import Settings

            # Test different preset configurations
            presets = ["simple", "development", "production"]
            for preset_name in presets:
                settings = Settings(resilience_preset=preset_name)
                metadata[f"settings_{preset_name}_initialized"] = True

        return self.measure_performance("settings_initialization", settings_initialization_operation, iterations)

    def benchmark_resilience_config_loading(self, iterations: int = 50) -> BenchmarkResult:
        """
        Benchmark resilience configuration loading performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for config loading
        """
        def config_loading_operation(metadata: Dict[str, Any]) -> None:
            from app.core.config import Settings

            # Test configuration loading for each preset
            presets = ["simple", "development", "production"]
            for preset_name in presets:
                settings = Settings(resilience_preset=preset_name)
                config = settings.get_resilience_config()
                metadata[f"config_{preset_name}_loaded"] = config is not None

        return self.measure_performance("resilience_config_loading", config_loading_operation, iterations)

    def benchmark_service_initialization(self, iterations: int = 25) -> BenchmarkResult:
        """
        Benchmark AIServiceResilience initialization performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for service initialization
        """
        def service_initialization_operation(metadata: Dict[str, Any]) -> None:
            from app.core.config import Settings
            from app.infrastructure.resilience.orchestrator import AIServiceResilience

            # Test service initialization with different presets
            presets = ["simple", "development", "production"]
            for preset_name in presets:
                settings = Settings(resilience_preset=preset_name)
                service = AIServiceResilience(settings=settings)

                # Test operation config access
                operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
                for operation in operations:
                    op_config = service.get_operation_config(operation)
                    metadata[f"service_{preset_name}_{operation}_config"] = op_config is not None

        return self.measure_performance("service_initialization", service_initialization_operation, iterations)

    def benchmark_custom_config_loading(self, iterations: int = 25) -> BenchmarkResult:
        """
        Benchmark custom configuration loading performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for custom config loading
        """
        custom_configs = [
            {"retry_attempts": 4, "circuit_breaker_threshold": 7},
            {"retry_attempts": 6, "circuit_breaker_threshold": 9, "operation_overrides": {"summarize": "critical"}},
            {"retry_attempts": 3, "circuit_breaker_threshold": 5, "exponential_multiplier": 1.5, "jitter_enabled": True}
        ]

        def custom_config_loading_operation(metadata: Dict[str, Any]) -> None:
            from app.core.config import Settings

            for i, custom_config in enumerate(custom_configs):
                settings = Settings(
                    resilience_preset="simple",
                    resilience_custom_config=json.dumps(custom_config)
                )
                config = settings.get_resilience_config()
                metadata[f"custom_config_{i}_loaded"] = config is not None

        return self.measure_performance("custom_config_loading", custom_config_loading_operation, iterations)

    def benchmark_legacy_config_loading(self, iterations: int = 25) -> BenchmarkResult:
        """
        Benchmark legacy configuration loading performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for legacy config loading
        """
        legacy_environments = [
            {
                "RETRY_MAX_ATTEMPTS": "3",
                "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
                "DEFAULT_RESILIENCE_STRATEGY": "balanced"
            },
            {
                "RETRY_MAX_ATTEMPTS": "5",
                "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10",
                "DEFAULT_RESILIENCE_STRATEGY": "conservative",
                "SUMMARIZE_RESILIENCE_STRATEGY": "conservative"
            }
        ]

        def legacy_config_loading_operation(metadata: Dict[str, Any]) -> None:
            from app.core.config import Settings
            from unittest.mock import patch

            for i, legacy_env in enumerate(legacy_environments):
                with patch.dict(os.environ, legacy_env):
                    settings = Settings()
                    config = settings.get_resilience_config()
                    metadata[f"legacy_config_{i}_loaded"] = config is not None
                    metadata[f"legacy_config_{i}_detected"] = settings._has_legacy_resilience_config()

        return self.measure_performance("legacy_config_loading", legacy_config_loading_operation, iterations)

    def benchmark_validation_performance(self, iterations: int = 50) -> BenchmarkResult:
        """
        Benchmark configuration validation performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult for validation performance
        """
        test_configs: List[Dict[str, Any]] = [
            {"retry_attempts": 3, "circuit_breaker_threshold": 5},
            {"retry_attempts": 6, "circuit_breaker_threshold": 9, "operation_overrides": {"summarize": "critical"}},
            {"retry_attempts": 10, "circuit_breaker_threshold": 15, "exponential_multiplier": 2.0}
        ]

        def validation_performance_operation(metadata: Dict[str, Any]) -> None:
            from app.infrastructure.resilience.config_validator import config_validator

            for i, config_dict in enumerate(test_configs):
                result = config_validator.validate_custom_config(config_dict)
                metadata[f"config_{i}_valid"] = result.is_valid
                metadata[f"config_{i}_errors"] = len(result.errors)

        return self.measure_performance("validation_performance", validation_performance_operation, iterations)

    def run_comprehensive_benchmark(self) -> BenchmarkSuite:
        """
        Execute complete performance benchmark suite covering all resilience configuration operations.

        Runs the full suite of performance tests including preset loading, settings initialization,
        configuration loading, service initialization, and validation performance. Provides
        comprehensive performance assessment with threshold-based pass/fail evaluation,
        environment context, and detailed timing analysis.

        Returns:
            BenchmarkSuite containing comprehensive results:
            - name: Suite identification ("Resilience Configuration Performance Benchmark")
            - results: List of BenchmarkResult objects for all executed benchmarks
            - total_duration_ms: Total execution time for entire suite in milliseconds
            - pass_rate: Percentage of benchmarks meeting performance thresholds
            - failed_benchmarks: List of benchmark function names that failed to execute
            - timestamp: ISO format timestamp of suite execution
            - environment_info: System environment details for result context

        Behavior:
            - Clears previous results to ensure clean benchmark execution
            - Executes all standard benchmarks in sequence with appropriate iteration counts
            - Evaluates each benchmark against predefined performance thresholds
            - Calculates overall pass rate based on threshold compliance
            - Collects environment information for result contextualization
            - Handles individual benchmark failures gracefully without stopping suite execution
            - Logs progress and completion metrics for monitoring and debugging
            - Returns comprehensive results suitable for analysis and reporting

        Examples:
            >>> benchmark = ConfigurationPerformanceBenchmark()
            >>> suite = benchmark.run_comprehensive_benchmark()
            >>> assert suite.name == "Resilience Configuration Performance Benchmark"
            >>> assert len(suite.results) > 0
            >>> assert 0.0 <= suite.pass_rate <= 1.0
            >>> assert "timestamp" in suite.environment_info
            >>>
            >>> # Check if benchmarks meet performance targets
            >>> preset_results = [r for r in suite.results if r.operation == "preset_loading"]
            >>> assert len(preset_results) == 1
            >>> preset_result = preset_results[0]
            >>> assert preset_result.avg_duration_ms < 10  # Should meet PRESET_ACCESS target
            >>>
            >>> # Generate report
            >>> report = benchmark.generate_performance_report(suite)
            >>> assert "RESILIENCE CONFIGURATION PERFORMANCE REPORT" in report

        Performance Thresholds Applied:
            - preset_loading: <10ms (PRESET_ACCESS threshold)
            - settings_initialization: <100ms (CONFIG_LOADING threshold)
            - resilience_config_loading: <100ms (CONFIG_LOADING threshold)
            - service_initialization: <200ms (SERVICE_INIT threshold)
            - custom_config_loading: <100ms (CONFIG_LOADING threshold)
            - legacy_config_loading: <100ms (CONFIG_LOADING threshold)
            - validation_performance: <50ms (VALIDATION threshold)
        """
        logger.info("Starting comprehensive performance benchmark suite")
        start_time = time.perf_counter()

        # Clear previous results
        self.results = []

        # Run all benchmarks
        benchmarks = [
            self.benchmark_preset_loading,
            self.benchmark_settings_initialization,
            self.benchmark_resilience_config_loading,
            self.benchmark_service_initialization,
            self.benchmark_custom_config_loading,
            self.benchmark_legacy_config_loading,
            self.benchmark_validation_performance
        ]

        failed_benchmarks = []

        for benchmark_func in benchmarks:
            try:
                result = benchmark_func()
                logger.info(f"Completed {result.operation}: {result.avg_duration_ms:.2f}ms avg")
            except Exception as e:
                logger.error(f"Benchmark {benchmark_func.__name__} failed: {e}")
                failed_benchmarks.append(benchmark_func.__name__)

        end_time = time.perf_counter()
        total_duration_ms = (end_time - start_time) * 1000

        # Calculate pass rate based on thresholds
        passed_benchmarks = self._check_performance_thresholds()
        pass_rate = len(passed_benchmarks) / len(self.results) if self.results else 0.0

        # Collect environment information
        environment_info = self._collect_environment_info()

        suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=self.results,
            total_duration_ms=total_duration_ms,
            pass_rate=pass_rate,
            failed_benchmarks=failed_benchmarks,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            environment_info=environment_info
        )

        logger.info(f"Benchmark suite completed in {total_duration_ms:.2f}ms with {pass_rate:.1%} pass rate")
        return suite

    def _check_performance_thresholds(self) -> List[str]:
        """
        Check benchmark results against performance thresholds.

        Returns:
            List of passed benchmark names
        """
        passed = []
        thresholds = {
            "preset_loading": PerformanceThreshold.PRESET_ACCESS.value,
            "settings_initialization": PerformanceThreshold.CONFIG_LOADING.value,
            "resilience_config_loading": PerformanceThreshold.CONFIG_LOADING.value,
            "service_initialization": PerformanceThreshold.SERVICE_INIT.value,
            "custom_config_loading": PerformanceThreshold.CONFIG_LOADING.value,
            "legacy_config_loading": PerformanceThreshold.CONFIG_LOADING.value,
            "validation_performance": PerformanceThreshold.VALIDATION.value
        }

        for result in self.results:
            threshold = thresholds.get(result.operation, 100.0)
            if result.avg_duration_ms <= threshold:
                passed.append(result.operation)
                logger.info(f"✓ {result.operation}: {result.avg_duration_ms:.2f}ms <= {threshold}ms")
            else:
                logger.warning(f"✗ {result.operation}: {result.avg_duration_ms:.2f}ms > {threshold}ms")

        return passed

    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information for benchmark context."""
        import platform
        import sys

        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor(),
            "memory_gb": self._get_system_memory_gb(),
            "cpu_count": os.cpu_count(),
            "environment_variables": {
                "DEBUG": os.getenv("DEBUG"),
                "RESILIENCE_PRESET": os.getenv("RESILIENCE_PRESET"),
                "GEMINI_API_KEY_SET": bool(os.getenv("GEMINI_API_KEY"))
            }
        }

    def _get_system_memory_gb(self) -> float:
        """Get system memory in GB."""
        try:
            import psutil
            return psutil.virtual_memory().total / (1024**3)
        except ImportError:
            return 0.0  # psutil not available

    def analyze_performance_trends(self, historical_results: List[BenchmarkSuite]) -> Dict[str, Any]:
        """
        Analyze performance trends across multiple benchmark runs.

        Args:
            historical_results: List of previous benchmark suite results

        Returns:
            Performance trend analysis
        """
        if not historical_results:
            return {"message": "No historical data available for trend analysis"}

        # Analyze each operation's performance over time
        trend_analysis = {}

        for operation in ["preset_loading", "settings_initialization", "resilience_config_loading"]:
            operation_times = []
            for suite in historical_results:
                for result in suite.results:
                    if result.operation == operation:
                        operation_times.append(result.avg_duration_ms)
                        break

            if len(operation_times) >= 2:
                # Calculate trend
                first_half = operation_times[:len(operation_times)//2]
                second_half = operation_times[len(operation_times)//2:]

                avg_first = statistics.mean(first_half)
                avg_second = statistics.mean(second_half)

                trend_percentage = ((avg_second - avg_first) / avg_first) * 100

                trend_analysis[operation] = {
                    "trend_percentage": trend_percentage,
                    "trend_direction": "improving" if trend_percentage < 0 else "degrading",
                    "first_half_avg_ms": avg_first,
                    "second_half_avg_ms": avg_second,
                    "sample_count": len(operation_times)
                }

        return trend_analysis

    def generate_performance_report(self, suite: BenchmarkSuite) -> str:
        """
        Generate human-readable performance report.

        Args:
            suite: BenchmarkSuite to generate report for

        Returns:
            Formatted performance report
        """
        report = []
        report.append("=" * 60)
        report.append("RESILIENCE CONFIGURATION PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {suite.timestamp}")
        report.append(f"Total Duration: {suite.total_duration_ms:.2f}ms")
        report.append(f"Pass Rate: {suite.pass_rate:.1%}")
        report.append("")

        # Environment information
        report.append("Environment Information:")
        report.append(f"  Platform: {suite.environment_info.get('platform', 'Unknown')}")
        report.append(f"  Python: {suite.environment_info.get('python_version', 'Unknown')}")
        report.append(f"  CPU Count: {suite.environment_info.get('cpu_count', 'Unknown')}")
        report.append(f"  Memory: {suite.environment_info.get('memory_gb', 0):.1f} GB")
        report.append("")

        # Performance results
        report.append("Performance Results:")
        report.append("-" * 40)

        for result in suite.results:
            status = "✓ PASS" if result.avg_duration_ms <= 100.0 else "✗ FAIL"
            report.append(f"{result.operation:30} {result.avg_duration_ms:6.2f}ms {status}")
            report.append(f"{'':30} {result.min_duration_ms:6.2f}ms min, {result.max_duration_ms:6.2f}ms max")
            report.append(f"{'':30} {result.memory_peak_mb:6.2f}MB peak memory")
            report.append("")

        # Failed benchmarks
        if suite.failed_benchmarks:
            report.append("Failed Benchmarks:")
            for failed in suite.failed_benchmarks:
                report.append(f"  - {failed}")
            report.append("")

        # Performance recommendations
        report.append("Recommendations:")
        for result in suite.results:
            if result.avg_duration_ms > 100.0:
                report.append(f"  - Optimize {result.operation} (currently {result.avg_duration_ms:.2f}ms)")

        if not any(result.avg_duration_ms > 100.0 for result in suite.results):
            report.append("  - All benchmarks passed! Configuration loading is well-optimized.")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)


# Global benchmark instance
performance_benchmark = ConfigurationPerformanceBenchmark()
