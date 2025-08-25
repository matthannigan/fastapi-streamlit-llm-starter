---
sidebar_label: benchmarks_legacy
---

# [REFACTORED] Cache Performance Benchmarking Infrastructure

  file_path: `backend/app/infrastructure/cache/benchmarks_legacy.py`

This module provides comprehensive performance benchmarking capabilities for cache implementations,
including timing analysis, memory usage tracking, compression efficiency testing, and regression
detection. It builds on the existing CachePerformanceMonitor infrastructure to provide detailed
performance validation for cache refactoring efforts.

## Key Features

- Comprehensive cache operation benchmarking (get/set/delete/exists/clear)
- Memory cache performance analysis with L1/L2 cache coordination testing
- Compression efficiency benchmarking with ratio and timing analysis
- Before/after refactoring comparison utilities for regression detection
- Realistic workload generation for text processing scenarios
- Performance trend analysis and threshold validation
- Detailed reporting with recommendations and optimization insights

## Core Components

BenchmarkResult: Dataclass for individual benchmark measurements
ComparisonResult: Dataclass for before/after performance comparisons
BenchmarkSuite: Collection of related benchmark results with analysis
CachePerformanceBenchmark: Main benchmarking class with comprehensive test methods
CacheBenchmarkDataGenerator: Realistic test data generation for various scenarios
PerformanceRegressionDetector: Automated regression detection and alerting

## Usage Example

```python
# Initialize benchmark system
benchmark = CachePerformanceBenchmark()

# Benchmark basic cache operations
cache = GenericRedisCache()
result = await benchmark.benchmark_basic_operations(cache, iterations=100)
print(f"Average operation time: {result.avg_duration_ms:.2f}ms")
print(f"Operations per second: {result.operations_per_second:.0f}")

# Test memory cache performance
memory_result = await benchmark.benchmark_memory_cache_performance(cache)
print(f"L1 cache hit rate: {memory_result.cache_hit_rate:.1f}%")

# Compare implementations
old_cache = AIResponseCache()
comparison = await benchmark.compare_before_after_refactoring(old_cache, cache)
print(f"Performance change: {comparison.performance_change_percent:+.1f}%")

# Generate comprehensive report
suite = benchmark.run_comprehensive_benchmark_suite(cache)
report = benchmark.generate_performance_report(suite)
print(report)
```

## Performance Areas Tested

1. Basic Operations:
- Get/Set/Delete operation timing with percentile analysis
- Bulk operation performance under load
- Concurrent access pattern testing
- Error handling and timeout behavior

2. Memory Cache Performance:
- L1 memory cache hit rates and timing
- Memory cache eviction efficiency
- L1/L2 cache coordination and fallback behavior
- Memory usage and entry management

3. Compression Efficiency:
- Compression ratio analysis across different data types
- Compression/decompression timing measurements
- Memory savings calculation and efficiency metrics
- Compression threshold optimization testing

4. Performance Comparison:
- Before/after refactoring validation
- Regression detection with configurable thresholds
- Performance trend analysis over time
- Optimization recommendation generation

## Benchmark Configuration

### Default Performance Thresholds

- Basic Operations: <50ms average, <100ms p95
- Memory Cache: <5ms average, <10ms p95
- Compression: <100ms average, <200ms p95
- Memory Usage: <100MB total cache size
- Regression Threshold: <10% performance degradation

## Data Collection and Analysis

The benchmarking system automatically collects:
- Timing measurements with microsecond precision
- Memory usage tracking for all cache components
- Hit/miss ratios and cache efficiency metrics
- Compression performance and savings analysis
- Error rates and timeout handling performance
- System resource utilization during testing

## Integration Points

- Cache service layer for operation benchmarking
- Performance monitoring for trend analysis
- API endpoints for automated benchmark execution
- Alert systems for regression detection
- Reporting tools for performance analysis

## Dependencies

- time, asyncio: Timing and async operation support
- statistics: Statistical analysis and percentile calculations
- psutil: System resource monitoring (optional with fallback)
- dataclasses: Structured result storage
- typing: Type hints and annotations
- datetime: Timestamp and duration management
- json: Result serialization and export

## Thread Safety

This module is designed for single-threaded use within each benchmark session.
Concurrent benchmark execution requires separate benchmark instances to prevent
data corruption and ensure measurement accuracy.

## Performance Considerations

- Minimal overhead design with efficient measurement collection
- Isolated benchmark execution to prevent interference
- Configurable iteration counts for timing vs. accuracy trade-offs
- Automatic cleanup of temporary test data
- Resource-aware testing with memory and CPU monitoring
