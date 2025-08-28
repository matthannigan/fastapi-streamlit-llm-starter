"""
Comprehensive cache performance benchmarking package with modular architecture and advanced analytics.

This package provides complete performance benchmarking infrastructure for cache implementations
with sophisticated analysis, reporting, and configuration management. Refactored from monolithic
design to modular architecture for improved maintainability, testability, and extensibility
while maintaining full backward compatibility.

Package Structure:
    models.py: Comprehensive data models for benchmark results, comparisons, and suite analysis
    utils.py: Advanced statistical calculations and cross-platform memory tracking utilities
    generator.py: Realistic test data generation with comprehensive workload simulation
    config.py: Flexible configuration management with environment-specific presets
    reporting.py: Multi-format report generation (text, JSON, markdown, CI) with detailed analysis
    core.py: Main benchmarking orchestration with regression detection and performance analytics

Key Features:
    - **Comprehensive Benchmarking**: Complete cache operation performance analysis including
      timing, memory, throughput, success rates, and statistical analysis with percentiles.

    - **Advanced Analytics**: Regression detection, statistical analysis with outlier detection,
      confidence intervals, and performance grading using industry-standard thresholds.

    - **Realistic Workload Simulation**: Sophisticated test data generation with varied content
      types, sizes, and access patterns matching production cache usage scenarios.

    - **Multi-Format Reporting**: Text, JSON, markdown, and CI-optimized reports with performance
      badges, detailed analysis, and actionable optimization recommendations.

    - **Environment-Specific Configuration**: Presets for development, testing, production, and
      CI environments with appropriate thresholds, iteration counts, and feature flags.

    - **Before/After Comparison**: Specialized refactoring validation with comprehensive performance
      impact analysis and deployment readiness assessment.

    - **Memory Tracking**: Cross-platform memory monitoring with peak detection, delta analysis,
      and comprehensive memory efficiency assessment.

    - **Modular Architecture**: Clean separation of concerns with extracted utilities for improved
      testability, reusability, and maintainability.

Backward Compatibility:
    The package maintains full backward compatibility with the original benchmarks.py interface
    while providing enhanced modularity and configuration flexibility. Existing code continues
    to work without modification while gaining access to new features.

Usage Examples:
    Basic Benchmarking:
        >>> from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
        >>> from app.infrastructure.cache.benchmarks.config import ConfigPresets
        >>>
        >>> # Standard benchmarking with default configuration
        >>> benchmark = CachePerformanceBenchmark()
        >>> cache = InMemoryCache()
        >>> result = await benchmark.benchmark_basic_operations(cache)
        >>> print(f"Performance: {result.avg_duration_ms:.2f}ms")
        >>> print(f"Grade: {result.performance_grade()}")

    Environment-Specific Configuration:
        >>> # Production-grade benchmarking
        >>> config = ConfigPresets.production_config()
        >>> benchmark = CachePerformanceBenchmark(config)
        >>> suite = await benchmark.run_comprehensive_benchmark_suite(cache)
        >>> print(f"Pass rate: {suite.pass_rate*100:.1f}%")

    Before/After Comparison:
        >>> # Cache refactoring validation
        >>> comparison = await benchmark.compare_before_after_refactoring(old_cache, new_cache)
        >>> if comparison.regression_detected:
        ...     print(f"⚠️ Regressions: {comparison.degradation_areas}")
        >>> else:
        ...     print(f"✅ Improvements: {comparison.improvement_areas}")

    Comprehensive Reporting:
        >>> # Multi-format report generation
        >>> text_report = benchmark.generate_performance_report(suite, "text")
        >>> ci_report = benchmark.generate_performance_report(suite, "ci")
        >>> json_report = benchmark.generate_performance_report(suite, "json")

    Data Generation and Analysis:
        >>> from app.infrastructure.cache.benchmarks import CacheBenchmarkDataGenerator
        >>> from app.infrastructure.cache.benchmarks import StatisticalCalculator
        >>>
        >>> # Generate realistic test data
        >>> generator = CacheBenchmarkDataGenerator()
        >>> test_data = generator.generate_basic_operations_data(100)
        >>>
        >>> # Statistical analysis
        >>> calc = StatisticalCalculator()
        >>> stats = calc.calculate_statistics(performance_data)
        >>> print(f"P95: {stats['p95']:.2f}ms")

Performance Considerations:
    - Optimized for minimal benchmark execution overhead (< 1ms per operation)
    - Memory tracking with fallback mechanisms for different environments
    - Efficient statistical analysis algorithms suitable for real-time monitoring
    - Configurable iteration counts and timeouts for different performance requirements

Thread Safety:
    All package components are designed for thread-safe concurrent benchmark execution.
    Multiple benchmark instances can run safely across threads without interference.
"""

# Import all public components for backward compatibility
from .models import (
    BenchmarkResult,
    ComparisonResult,
    BenchmarkSuite,
)

from .utils import (
    StatisticalCalculator,
    MemoryTracker,
)

from .generator import (
    CacheBenchmarkDataGenerator,
)

from .config import (
    CachePerformanceThresholds,
    BenchmarkConfig,
    ConfigPresets,
    load_config_from_env,
    load_config_from_file,
    get_default_config,
)

from .reporting import (
    BenchmarkReporter,
    TextReporter,
    CIReporter,
    JSONReporter,
    MarkdownReporter,
    ReporterFactory,
)

from .core import (
    CachePerformanceBenchmark,
    PerformanceRegressionDetector,
)

# Public API exports for backward compatibility
__all__ = [
    # Data Models
    "BenchmarkResult",
    "ComparisonResult",
    "BenchmarkSuite",

    # Utilities
    "StatisticalCalculator",
    "MemoryTracker",

    # Data Generation
    "CacheBenchmarkDataGenerator",

    # Configuration
    "CachePerformanceThresholds",
    "BenchmarkConfig",
    "ConfigPresets",
    "load_config_from_env",
    "load_config_from_file",
    "get_default_config",

    # Reporting
    "BenchmarkReporter",
    "TextReporter",
    "CIReporter",
    "JSONReporter",
    "MarkdownReporter",
    "ReporterFactory",

    # Core Functionality
    "CachePerformanceBenchmark",
    "PerformanceRegressionDetector",
]
