---
sidebar_label: utils
---

# [REFACTORED] Advanced statistical analysis and memory tracking utilities for cache performance benchmarking.

  file_path: `backend/app/infrastructure/cache/benchmarks/utils.py`

This module provides comprehensive statistical calculation and memory monitoring infrastructure
extracted from the original monolithic benchmarks module for improved reusability, testability,
and maintainability. Designed with robust error handling and fallback mechanisms for different
environments and missing dependencies.

## Classes

StatisticalCalculator: Advanced statistical analysis with outlier detection and confidence intervals
MemoryTracker: Cross-platform memory monitoring with fallback mechanisms

## Key Features

- **Advanced Statistical Analysis**: Comprehensive statistical calculations including percentiles,
standard deviation, outlier detection using IQR method, and confidence intervals.

- **Robust Error Handling**: Graceful handling of edge cases including empty datasets,
infinite values, and missing dependencies with appropriate fallbacks.

- **Cross-Platform Memory Tracking**: Memory usage monitoring with multiple fallback
mechanisms supporting psutil, /proc/self/status, and basic memory estimation.

- **Outlier Detection**: Interquartile Range (IQR) based outlier detection with
configurable thresholds and clean data extraction for improved analysis accuracy.

- **Confidence Intervals**: Statistical confidence interval calculation supporting
both normal distribution (large samples) and t-distribution approximation.

- **Performance Optimization**: Efficient algorithms with minimal overhead suitable
for real-time benchmarking and continuous performance monitoring.

## Statistical Analysis Capabilities

- Percentile calculations (P50, P95, P99) with linear interpolation
- Standard deviation with robust handling of non-finite values
- Outlier detection using 1.5*IQR method with boundary calculation
- Confidence intervals (95%, 99%) with appropriate distribution selection
- Comprehensive statistics aggregation in single method call

## Memory Tracking Capabilities

- Process-specific memory usage tracking (RSS, available, total)
- System-wide memory utilization monitoring with percentage calculations
- Memory delta calculation between measurement points
- Peak memory tracking across measurement series
- Fallback mechanisms for environments without psutil dependency

## Usage Examples

### Statistical Analysis

```python
calc = StatisticalCalculator()
data = [1.2, 1.5, 1.8, 2.1, 1.9, 1.7, 1.6, 1.4]
stats = calc.calculate_statistics(data)
print(f"P95: {stats['p95']:.2f}ms")
print(f"Mean: {stats['mean']:.2f}ms")
print(f"Std Dev: {stats['std_dev']:.2f}ms")

outliers = calc.detect_outliers(data)
print(f"Found {outliers['outlier_count']} outliers")

ci = calc.calculate_confidence_intervals(data)
print(f"95% CI: [{ci['lower']:.2f}, {ci['upper']:.2f}]")
```

### Memory Tracking

```python
tracker = MemoryTracker()
before = tracker.get_memory_usage()
# ... perform operations ...
after = tracker.get_memory_usage()
delta = tracker.calculate_memory_delta(before, after)
print(f"Memory increase: {delta['process_mb']:.1f}MB")

# Peak memory tracking
measurements = []
for i in range(10):
    measurements.append(tracker.get_memory_usage())
    # ... perform operations ...
peaks = tracker.track_peak_memory(measurements)
print(f"Peak memory: {peaks['process_mb']:.1f}MB")
```

## Thread Safety

Both StatisticalCalculator and MemoryTracker are stateless and thread-safe.
All methods can be called concurrently without interference or shared state issues.
