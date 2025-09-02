---
sidebar_label: monitoring
---

# Comprehensive cache performance monitoring and analytics.

  file_path: `backend/app/infrastructure/cache/monitoring.py`

This module provides real-time monitoring and analytics for cache performance across
multiple dimensions including timing, memory usage, compression efficiency, and
invalidation patterns. It helps identify bottlenecks and optimize cache strategies.

## Key Features

- **Real-Time Monitoring**: Live performance tracking for cache operations
- **Timing Analysis**: Detailed analysis for key generation and cache operations
- **Memory Tracking**: Usage monitoring with configurable threshold alerting
- **Compression Analytics**: Efficiency monitoring and optimization recommendations
- **Invalidation Analysis**: Pattern analysis and frequency monitoring
- **Historical Data**: Automatic cleanup with configurable data retention
- **Performance Insights**: Statistics, trends, and optimization recommendations

## Core Components

- **PerformanceMetric**: Individual performance measurements
- **CompressionMetric**: Compression performance tracking
- **MemoryUsageMetric**: Memory usage snapshots
- **InvalidationMetric**: Cache invalidation event tracking
- **CachePerformanceMonitor**: Main monitoring class with comprehensive analytics

## Usage

```python
# Initialize with custom thresholds
monitor = CachePerformanceMonitor(
    retention_hours=2,
    memory_warning_threshold_bytes=100 * 1024 * 1024  # 100MB
    ...     memory_critical_threshold_bytes=200 * 1024 * 1024  # 200MB
    ... )

    >>> # Record key generation performance
    >>> start_time = time.time()
    >>> # ... key generation code ...
    >>> duration = time.time() - start_time
    >>> monitor.record_key_generation_time(
    ...     duration=duration,
    ...     text_length=len(text),
    ...     operation_type="summarize"
    ... )

    >>> # Record cache operation performance
    >>> start_time = time.time()
    >>> result = cache.get(key)
    >>> duration = time.time() - start_time
    >>> monitor.record_cache_operation_time(
    ...     operation="get",
    ...     duration=duration,
    ...     cache_hit=result is not None,
    ...     text_length=len(text) if result else 0
    ... )

    >>> # Monitor memory usage
    >>> memory_metric = monitor.record_memory_usage(
    ...     memory_cache=cache._memory_cache,
    ...     redis_stats={"memory_used_bytes": 50000000, "keys": 1000}
    ... )

    >>> # Get comprehensive performance statistics
    >>> stats = monitor.get_performance_stats()
    >>> print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
    >>> print(f"Average key generation time: {stats['key_generation']['avg_duration']:.3f}s")

    >>> # Check for performance issues and get recommendations
    >>> warnings = monitor.get_memory_warnings()
    >>> for warning in warnings:
    ...     print(f"{warning['severity'].upper()}: {warning['message']}")

    >>> recommendations = monitor.get_invalidation_recommendations()
    >>> for rec in recommendations:
    ...     if rec['severity'] == 'critical':
    ...         print(f"CRITICAL: {rec['message']}")

Performance Monitoring Areas:
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

Configuration Options:
    retention_hours: Duration to keep performance measurements (default: 1 hour)
    max_measurements: Maximum measurements per metric type (default: 1000)
    memory_warning_threshold_bytes: Memory usage warning threshold (default: 50MB)
    memory_critical_threshold_bytes: Memory usage critical threshold (default: 100MB)
    key_generation_threshold: Slow key generation threshold (default: 0.1s)
    cache_operation_threshold: Slow cache operation threshold (default: 0.05s)
    invalidation_rate_warning_per_hour: Invalidation frequency warning (default: 50/hour)
    invalidation_rate_critical_per_hour: Invalidation frequency critical (default: 100/hour)

Data Retention and Cleanup:
    The monitor automatically cleans up old measurements based on:
    - Time-based retention (configurable hours)
    - Count-based limits (maximum measurements per type)
    - This prevents unbounded memory growth while maintaining recent performance data

Statistics and Analysis:
    - Real-time performance metrics with trend analysis
    - Threshold-based alerting with configurable severity levels
    - Performance recommendations based on collected data patterns
    - Comprehensive export capabilities for external analysis
    - Historical trend analysis for capacity planning

Dependencies:
    - time, logging, sys: Standard library modules
    - typing: Type hints and annotations
    - datetime, timedelta: Time-based calculations
    - dataclasses: Structured data storage
    - statistics: Mathematical analysis functions
    - psutil: Optional process memory monitoring (graceful fallback)

Thread Safety:
    This module is designed for single-threaded use within each cache instance.
    If used in multi-threaded environments, external synchronization is required
    to prevent race conditions in metric collection and analysis.

Performance Considerations:
    - Minimal overhead design with efficient data structures
    - Automatic cleanup prevents memory leaks
    - Lazy calculation of statistics (computed on-demand)
    - Configurable retention limits for memory management
    - Optional dependencies with graceful fallbacks

Integration Points:
    - Cache service layer for operation timing
    - Memory management for usage tracking
    - Invalidation services for pattern analysis
    - Monitoring endpoints for metrics export
    - Alert systems for threshold notifications

## PerformanceMetric

Data class for storing individual performance measurements.

### __post_init__()

```python
def __post_init__(self):
```

## CompressionMetric

Data class for storing compression performance measurements.

### __post_init__()

```python
def __post_init__(self):
```

## MemoryUsageMetric

Data class for storing memory usage measurements.

### __post_init__()

```python
def __post_init__(self):
```

## InvalidationMetric

Data class for storing cache invalidation measurements.

### __post_init__()

```python
def __post_init__(self):
```

## CachePerformanceMonitor

Monitors and tracks cache performance metrics for optimization and debugging.

This class tracks:
- Key generation performance
- Cache operation timing (get/set operations)
- Compression ratios and efficiency
- Memory usage of cache items
- Recent measurements with automatic cleanup

### __init__()

```python
def __init__(self, retention_hours: int = 1, max_measurements: int = 1000, memory_warning_threshold_bytes: int = 50 * 1024 * 1024, memory_critical_threshold_bytes: int = 100 * 1024 * 1024):
```

Initialize the cache performance monitor.

Args:
    retention_hours: How long to keep measurements (default: 1 hour)
    max_measurements: Maximum number of measurements to store per metric type
    memory_warning_threshold_bytes: Memory usage threshold for warnings (default: 50MB)
    memory_critical_threshold_bytes: Memory usage threshold for critical alerts (default: 100MB)

### record_key_generation_time()

```python
def record_key_generation_time(self, duration: float, text_length: int, operation_type: str = '', additional_data: Optional[Dict[str, Any]] = None):
```

Record key generation performance metrics.

Args:
    duration: Time taken to generate the cache key (in seconds)
    text_length: Length of the text being processed
    operation_type: Type of operation (summarize, sentiment, etc.)
    additional_data: Additional metadata to store with the metric

### record_cache_operation_time()

```python
def record_cache_operation_time(self, operation: str, duration: float, cache_hit: bool, text_length: int = 0, additional_data: Optional[Dict[str, Any]] = None):
```

Record cache operation performance (get/set operations).

Args:
    operation: Operation type ('get', 'set', 'delete', etc.)
    duration: Time taken for the operation (in seconds)
    cache_hit: Whether this was a cache hit (for get operations)
    text_length: Length of text being cached/retrieved
    additional_data: Additional metadata to store

### record_compression_ratio()

```python
def record_compression_ratio(self, original_size: int, compressed_size: int, compression_time: float, operation_type: str = ''):
```

Record compression performance and efficiency metrics.

Args:
    original_size: Size of data before compression (in bytes)
    compressed_size: Size of data after compression (in bytes)
    compression_time: Time taken to compress (in seconds)
    operation_type: Type of operation being compressed

### record_memory_usage()

```python
def record_memory_usage(self, memory_cache: Dict[str, Any], redis_stats: Optional[Dict[str, Any]] = None, additional_data: Optional[Dict[str, Any]] = None):
```

Record current memory usage of cache components.

Args:
    memory_cache: The in-memory cache dictionary to measure
    redis_stats: Optional Redis statistics for total cache size
    additional_data: Additional metadata to store

### record_invalidation_event()

```python
def record_invalidation_event(self, pattern: str, keys_invalidated: int, duration: float, invalidation_type: str = 'manual', operation_context: str = '', additional_data: Optional[Dict[str, Any]] = None):
```

Record cache invalidation event for frequency analysis.

Args:
    pattern: Pattern used for invalidation
    keys_invalidated: Number of keys that were invalidated
    duration: Time taken for the invalidation operation
    invalidation_type: Type of invalidation ('manual', 'automatic', 'ttl_expired', etc.)
    operation_context: Context that triggered the invalidation
    additional_data: Additional metadata to store

### get_invalidation_frequency_stats()

```python
def get_invalidation_frequency_stats(self) -> Dict[str, Any]:
```

Get invalidation frequency statistics and analysis.

Provides comprehensive analysis of cache invalidation patterns including
frequency rates, pattern analysis, and efficiency metrics. Used for
optimizing invalidation strategies and identifying potential issues.

Returns:
    Dict[str, Any]: Invalidation statistics containing:
        - rates: Invalidation frequency (hourly, daily, average)
        - thresholds: Warning/critical thresholds and current alert level
        - patterns: Most common invalidation patterns and types
        - efficiency: Average keys per invalidation, timing statistics

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> stats = monitor.get_invalidation_frequency_stats()
    >>> print(f"Hourly rate: {stats['rates']['last_hour']}")
    >>> print(f"Alert level: {stats['thresholds']['current_alert_level']}")

### get_invalidation_recommendations()

```python
def get_invalidation_recommendations(self) -> List[Dict[str, Any]]:
```

Get recommendations based on invalidation patterns and performance data.

Analyzes invalidation frequency, patterns, and efficiency to provide
actionable recommendations for optimizing cache invalidation strategies.

Returns:
    List[Dict[str, Any]]: List of recommendations, each containing:
        - severity: Recommendation level ('info', 'warning', 'critical')
        - issue: Brief description of the identified issue
        - message: Detailed explanation of the problem
        - suggestions: List of specific actions to address the issue

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> recommendations = monitor.get_invalidation_recommendations()
    >>> for rec in recommendations:
    ...     if rec['severity'] == 'critical':
    ...         print(f"CRITICAL: {rec['message']}")

### get_memory_usage_stats()

```python
def get_memory_usage_stats(self) -> Dict[str, Any]:
```

Get comprehensive memory usage statistics and trend analysis.

Provides detailed memory usage information including current consumption,
historical trends, and threshold analysis for cache components.

Returns:
    Dict[str, Any]: Memory usage statistics containing:
        - current: Current memory consumption metrics
        - thresholds: Warning/critical thresholds and status
        - trends: Historical usage patterns and growth analysis

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> stats = monitor.get_memory_usage_stats()
    >>> print(f"Current usage: {stats['current']['total_cache_size_mb']:.1f}MB")
    >>> print(f"Warning reached: {stats['thresholds']['warning_threshold_reached']}")

### get_memory_warnings()

```python
def get_memory_warnings(self) -> List[Dict[str, Any]]:
```

Get active memory-related warnings and recommendations.

Analyzes current memory usage against configured thresholds and
provides warnings with specific recommendations for addressing
memory-related issues.

Returns:
    List[Dict[str, Any]]: List of active warnings, each containing:
        - severity: Warning level ('info', 'warning', 'critical')
        - message: Human-readable description of the issue
        - recommendations: List of suggested actions to resolve the issue

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> warnings = monitor.get_memory_warnings()
    >>> for warning in warnings:
    ...     print(f"{warning['severity'].upper()}: {warning['message']}")
    WARNING: Cache memory usage exceeding threshold

### get_performance_stats()

```python
def get_performance_stats(self) -> Dict[str, Any]:
```

Get comprehensive cache performance statistics across all monitored areas.

Provides a complete performance overview including hit rates, timing
statistics, compression efficiency, memory usage, and invalidation patterns.
Automatically cleans up old measurements before generating statistics.

Returns:
    Dict[str, Any]: Comprehensive performance statistics containing:
        - timestamp: When statistics were generated
        - cache_hit_rate: Overall cache hit percentage
        - key_generation: Key generation timing and efficiency metrics
        - cache_operations: Cache operation performance by type
        - compression: Compression ratios and efficiency statistics
        - memory_usage: Memory consumption and trend analysis
        - invalidation: Invalidation frequency and pattern analysis

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> stats = monitor.get_performance_stats()
    >>> print(f"Hit rate: {stats['cache_hit_rate']:.1f}%")
    >>> print(f"Avg key gen time: {stats['key_generation']['avg_duration']:.3f}s")

### record_operation()

```python
async def record_operation(self, name: str, duration_ms: float, success: bool) -> None:
```

Record a generic operation timing for integration points.

This lightweight async API is used by other components (e.g., security
manager) to record durations without coupling to specific operation types.

### get_recent_slow_operations()

```python
def get_recent_slow_operations(self, threshold_multiplier: float = 2.0) -> Dict[str, List[Dict[str, Any]]]:
```

Get recent operations that were significantly slower than average.

Identifies operations that took significantly longer than the average
time for their category. Useful for performance troubleshooting and
identifying potential bottlenecks.

Args:
    threshold_multiplier (float, optional): Multiplier for average duration
                                           to determine "slow" threshold.
                                           Defaults to 2.0 (2x average).

Returns:
    Dict[str, List[Dict[str, Any]]]: Slow operations by category:
        - key_generation: Slow key generation operations
        - cache_operations: Slow cache get/set operations
        - compression: Slow compression operations
        Each entry includes timing, context, and performance details.

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> slow_ops = monitor.get_recent_slow_operations(threshold_multiplier=3.0)
    >>> for category, operations in slow_ops.items():
    ...     if operations:
    ...         print(f"{category}: {len(operations)} slow operations")

### reset_stats()

```python
def reset_stats(self):
```

Reset all performance statistics and measurements.

Clears all accumulated performance data including timing measurements,
hit/miss counts, compression statistics, memory usage history, and
invalidation events. Useful for starting fresh analysis periods.

Returns:
    None: This method resets statistics as a side effect.

Warning:
    This action cannot be undone. All historical performance data
    will be permanently lost. Consider exporting metrics before
    resetting if historical data is needed for analysis.

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> # Export current data if needed
    >>> data = monitor.export_metrics()
    >>> monitor.reset_stats()
    >>> print("All performance statistics have been reset")

### export_metrics()

```python
def export_metrics(self) -> Dict[str, Any]:
```

Export all raw metrics data for external analysis and archival.

Provides complete access to all collected performance measurements
in a structured format suitable for external analysis tools, data
warehouses, or long-term storage.

Returns:
    Dict[str, Any]: Complete raw metrics data containing:
        - key_generation_times: All key generation timing measurements
        - cache_operation_times: All cache operation timing measurements
        - compression_ratios: All compression performance measurements
        - memory_usage_measurements: All memory usage snapshots
        - invalidation_events: All cache invalidation events
        - cache_hits/cache_misses: Aggregate hit/miss counts
        - total_operations: Total number of operations recorded
        - export_timestamp: When the export was generated

Example:
    >>> monitor = CachePerformanceMonitor()
    >>> metrics = monitor.export_metrics()
    >>> print(f"Exported {len(metrics['cache_operation_times'])} cache operations")
    >>> # Save to file for analysis
    >>> import json
    >>> with open('cache_metrics.json', 'w') as f:
    ...     json.dump(metrics, f, indent=2)
