---
sidebar_label: core
---

# [REFACTORED] Comprehensive cache performance benchmarking orchestration with modular architecture.

  file_path: `backend/app/infrastructure/cache/benchmarks/core.py`

This module provides the primary benchmarking orchestration classes for cache performance
testing including regression detection, statistical analysis, and comprehensive reporting.
Designed with modular architecture using extracted utilities and data models for improved
maintainability and extensibility.

## Classes

PerformanceRegressionDetector: Automated performance regression detection and analysis
CachePerformanceBenchmark: Main benchmarking orchestration with comprehensive analytics

## Key Features

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

## Configuration

The benchmarking system supports extensive configuration through BenchmarkConfig:

- default_iterations: Number of benchmark iterations (default: 100)
- warmup_iterations: Warmup operations before measurement (default: 10)
- timeout_seconds: Maximum benchmark execution time (default: 300)
- enable_memory_tracking: Memory usage monitoring flag (default: True)
- enable_compression_tests: Compression efficiency testing flag (default: True)
- thresholds: Performance threshold configuration for pass/fail assessment
- environment: Environment identifier for context ("development", "testing", "production", "ci")

## Usage Examples

### Basic Benchmarking

```python
from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
from app.infrastructure.cache.benchmarks.config import ConfigPresets

# Standard benchmarking with default configuration
benchmark = CachePerformanceBenchmark()
cache = InMemoryCache()
result = await benchmark.benchmark_basic_operations(cache)
print(f"Average: {result.avg_duration_ms:.2f}ms")
print(f"P95: {result.p95_duration_ms:.2f}ms")
print(f"Throughput: {result.operations_per_second:.0f} ops/s")
```

### Environment-Specific Configuration

```python
# Production-grade benchmarking
config = ConfigPresets.production_config()
benchmark = CachePerformanceBenchmark(config)
cache = RedisCache(url="redis://localhost:6379")
suite = await benchmark.run_comprehensive_benchmark_suite(cache)
print(f"Pass rate: {suite.pass_rate*100:.1f}%")
print(f"Performance grade: {suite.performance_grade}")
```
Before/After Refactoring Comparison:
```python
# Cache refactoring validation
original = LegacyRedisCache()
refactored = OptimizedRedisCache()
comparison = await benchmark.compare_before_after_refactoring(original, refactored)

if comparison.regression_detected:
    print(f"⚠️ Regressions in: {comparison.degradation_areas}")
    print(f"Recommendation: {comparison.recommendation}")
else:
    print(f"✅ Performance improved: {comparison.improvement_areas}")
```

### Comprehensive Reporting

```python
# Generate multiple report formats
suite = await benchmark.run_comprehensive_benchmark_suite(cache)

# Console output
text_report = benchmark.generate_performance_report(suite, "text")
print(text_report)

# CI integration
ci_report = benchmark.generate_performance_report(suite, "ci")
# Contains performance badges and concise insights

# Documentation
md_report = benchmark.generate_performance_report(suite, "markdown")
# GitHub-compatible markdown with collapsible sections
```

### Regression Detection

```python
from app.infrastructure.cache.benchmarks import PerformanceRegressionDetector

detector = PerformanceRegressionDetector(
    warning_threshold=10.0,  # 10% change triggers warning
    critical_threshold=25.0  # 25% change is critical
)

timing_regressions = detector.detect_timing_regressions(baseline, current)
memory_regressions = detector.detect_memory_regressions(baseline, current)
hit_rate_status = detector.validate_cache_hit_rates(baseline, current)

for regression in timing_regressions:
    print(f"{regression['severity']}: {regression['message']}")
```

## Performance Considerations

- Warmup operations eliminate cold-start effects for consistent measurements
- Memory tracking adds minimal overhead (< 1ms per measurement)
- Statistical analysis scales linearly with iteration count
- Comprehensive benchmarks include multiple operation types and memory analysis
- Regression detection provides early warning for performance degradations

## Thread Safety

This module is designed to be thread-safe for concurrent benchmark execution.
Each benchmark instance maintains independent state and can be used safely
across multiple threads or async contexts.
