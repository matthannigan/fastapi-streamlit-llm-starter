# Cache Performance Monitoring and Analytics Module

This module provides comprehensive monitoring, analysis, and optimization capabilities for cache
performance across multiple dimensions including timing, memory usage, compression efficiency,
and invalidation patterns. It's designed to help identify bottlenecks, optimize cache strategies,
and maintain optimal cache performance in production environments.

## Key Features

- Real-time performance monitoring for cache operations
- Detailed timing analysis for key generation and cache operations
- Memory usage tracking with threshold-based alerting
- Compression efficiency monitoring and optimization recommendations
- Cache invalidation pattern analysis and frequency monitoring
- Automatic cleanup of historical data with configurable retention
- Comprehensive statistics and trend analysis
- Performance recommendations based on collected metrics

## Core Components

PerformanceMetric: Dataclass for individual performance measurements
CompressionMetric: Dataclass for compression performance tracking
MemoryUsageMetric: Dataclass for memory usage snapshots
InvalidationMetric: Dataclass for cache invalidation event tracking
CachePerformanceMonitor: Main monitoring class with comprehensive analytics

## Usage Example

```python
# Initialize the monitor with custom thresholds
monitor = CachePerformanceMonitor(
    retention_hours=2,
    memory_warning_threshold_bytes=100 * 1024 * 1024,  # 100MB
    memory_critical_threshold_bytes=200 * 1024 * 1024  # 200MB
)
```
```python
# Record key generation performance
start_time = time.time()
# ... key generation code ...
duration = time.time() - start_time
monitor.record_key_generation_time(
    duration=duration,
    text_length=len(text),
    operation_type="summarize"
)
```
```python
# Record cache operation performance
start_time = time.time()
result = cache.get(key)
duration = time.time() - start_time
monitor.record_cache_operation_time(
    operation="get",
    duration=duration,
    cache_hit=result is not None,
    text_length=len(text) if result else 0
)
```
```python
# Monitor memory usage
memory_metric = monitor.record_memory_usage(
    memory_cache=cache._memory_cache,
    redis_stats={"memory_used_bytes": 50000000, "keys": 1000}
)
```
```python
# Get comprehensive performance statistics
stats = monitor.get_performance_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
print(f"Average key generation time: {stats['key_generation']['avg_duration']:.3f}s")
```
```python
# Check for performance issues and get recommendations
warnings = monitor.get_memory_warnings()
for warning in warnings:
    print(f"{warning['severity'].upper()}: {warning['message']}")
```
```python
recommendations = monitor.get_invalidation_recommendations()
for rec in recommendations:
    if rec['severity'] == 'critical':
        print(f"CRITICAL: {rec['message']}")
```

## Performance Monitoring Areas

1. Key Generation Performance:
- Timing for cache key generation operations
- Text length correlation analysis
- Operation type performance comparison
- Slow operation detection and alerting

2. Cache Operations:
- Get/Set operation timing
- Hit/Miss ratio tracking
- Operation type performance analysis
- Bottleneck identification

3. Memory Usage:
- Total cache memory consumption
- Memory cache vs. Redis usage breakdown
- Entry count and average size tracking
- Threshold-based alerting (warning/critical)
- Growth trend analysis

4. Compression Efficiency:
- Compression ratio tracking
- Compression time analysis
- Size savings calculations
- Performance vs. efficiency trade-offs

5. Cache Invalidation:
- Invalidation frequency monitoring
- Pattern analysis and optimization
- Efficiency metrics (keys per invalidation)
- Alert thresholds for excessive invalidation

## Configuration Options

retention_hours: Duration to keep performance measurements (default: 1 hour)
max_measurements: Maximum measurements per metric type (default: 1000)
memory_warning_threshold_bytes: Memory usage warning threshold (default: 50MB)
memory_critical_threshold_bytes: Memory usage critical threshold (default: 100MB)
key_generation_threshold: Slow key generation threshold (default: 0.1s)
cache_operation_threshold: Slow cache operation threshold (default: 0.05s)
invalidation_rate_warning_per_hour: Invalidation frequency warning (default: 50/hour)
invalidation_rate_critical_per_hour: Invalidation frequency critical (default: 100/hour)

## Data Retention and Cleanup

The monitor automatically cleans up old measurements based on:
- Time-based retention (configurable hours)
- Count-based limits (maximum measurements per type)
- This prevents unbounded memory growth while maintaining recent performance data

## Statistics and Analysis

- Real-time performance metrics with trend analysis
- Threshold-based alerting with configurable severity levels
- Performance recommendations based on collected data patterns
- Comprehensive export capabilities for external analysis
- Historical trend analysis for capacity planning

## Dependencies

- time, logging, sys: Standard library modules
- typing: Type hints and annotations
- datetime, timedelta: Time-based calculations
- dataclasses: Structured data storage
- statistics: Mathematical analysis functions
- psutil: Optional process memory monitoring (graceful fallback)

## Thread Safety

This module is designed for single-threaded use within each cache instance.
If used in multi-threaded environments, external synchronization is required
to prevent race conditions in metric collection and analysis.

## Performance Considerations

- Minimal overhead design with efficient data structures
- Automatic cleanup prevents memory leaks
- Lazy calculation of statistics (computed on-demand)
- Configurable retention limits for memory management
- Optional dependencies with graceful fallbacks

## Integration Points

- Cache service layer for operation timing
- Memory management for usage tracking
- Invalidation services for pattern analysis
- Monitoring endpoints for metrics export
- Alert systems for threshold notifications
