"""
Cache Performance Monitoring and Analytics Module

This module provides comprehensive monitoring, analysis, and optimization capabilities for cache
performance across multiple dimensions including timing, memory usage, compression efficiency,
and invalidation patterns. It's designed to help identify bottlenecks, optimize cache strategies,
and maintain optimal cache performance in production environments.

Key Features:
    - Real-time performance monitoring for cache operations
    - Detailed timing analysis for key generation and cache operations
    - Memory usage tracking with threshold-based alerting
    - Compression efficiency monitoring and optimization recommendations
    - Cache invalidation pattern analysis and frequency monitoring
    - Automatic cleanup of historical data with configurable retention
    - Comprehensive statistics and trend analysis
    - Performance recommendations based on collected metrics

Core Components:
    PerformanceMetric: Dataclass for individual performance measurements
    CompressionMetric: Dataclass for compression performance tracking
    MemoryUsageMetric: Dataclass for memory usage snapshots
    InvalidationMetric: Dataclass for cache invalidation event tracking
    CachePerformanceMonitor: Main monitoring class with comprehensive analytics

Usage Example:
    >>> # Initialize the monitor with custom thresholds
    >>> monitor = CachePerformanceMonitor(
    ...     retention_hours=2,
    ...     memory_warning_threshold_bytes=100 * 1024 * 1024,  # 100MB
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
"""

import logging
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from statistics import mean, median
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Data class for storing individual performance measurements."""

    duration: float
    text_length: int
    timestamp: float
    operation_type: str = ""
    additional_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class CompressionMetric:
    """Data class for storing compression performance measurements."""

    original_size: int
    compressed_size: int
    compression_ratio: float
    compression_time: float
    timestamp: float
    operation_type: str = ""

    def __post_init__(self):
        if self.compression_ratio == 0 and self.original_size > 0:
            self.compression_ratio = self.compressed_size / self.original_size


@dataclass
class MemoryUsageMetric:
    """Data class for storing memory usage measurements."""

    total_cache_size_bytes: int
    cache_entry_count: int
    avg_entry_size_bytes: float
    memory_cache_size_bytes: int
    memory_cache_entry_count: int
    process_memory_mb: float
    timestamp: float
    cache_utilization_percent: float
    warning_threshold_reached: bool = False
    additional_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


@dataclass
class InvalidationMetric:
    """Data class for storing cache invalidation measurements."""

    pattern: str
    keys_invalidated: int
    duration: float
    timestamp: float
    invalidation_type: str = ""  # 'manual', 'automatic', 'ttl_expired', etc.
    operation_context: str = ""  # Context that triggered invalidation
    additional_data: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}


class CachePerformanceMonitor:
    """
    Monitors and tracks cache performance metrics for optimization and debugging.

    This class tracks:
    - Key generation performance
    - Cache operation timing (get/set operations)
    - Compression ratios and efficiency
    - Memory usage of cache items
    - Recent measurements with automatic cleanup
    """

    def __init__(
        self,
        retention_hours: int = 1,
        max_measurements: int = 1000,
        memory_warning_threshold_bytes: int = 50 * 1024 * 1024,  # 50MB
        memory_critical_threshold_bytes: int = 100 * 1024 * 1024,
    ):  # 100MB
        """
        Initialize the cache performance monitor.

        Args:
            retention_hours: How long to keep measurements (default: 1 hour)
            max_measurements: Maximum number of measurements to store per metric type
            memory_warning_threshold_bytes: Memory usage threshold for warnings (default: 50MB)
            memory_critical_threshold_bytes: Memory usage threshold for critical alerts (default: 100MB)
        """
        self.retention_hours = retention_hours
        self.max_measurements = max_measurements
        self.memory_warning_threshold_bytes = memory_warning_threshold_bytes
        self.memory_critical_threshold_bytes = memory_critical_threshold_bytes

        # Storage for different types of measurements
        self.key_generation_times: List[PerformanceMetric] = []
        self.cache_operation_times: List[PerformanceMetric] = []
        self.compression_ratios: List[CompressionMetric] = []
        self.memory_usage_measurements: List[MemoryUsageMetric] = []
        self.invalidation_events: List[InvalidationMetric] = []

        # Track overall cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_operations = 0
        self.total_invalidations = 0
        self.total_keys_invalidated = 0

        # Performance thresholds for alerting
        self.key_generation_threshold = 0.1  # 100ms
        self.cache_operation_threshold = 0.05  # 50ms

        # Invalidation frequency thresholds
        self.invalidation_rate_warning_per_hour = (
            50  # Warning if > 50 invalidations per hour
        )
        self.invalidation_rate_critical_per_hour = (
            100  # Critical if > 100 invalidations per hour
        )

    def record_key_generation_time(
        self,
        duration: float,
        text_length: int,
        operation_type: str = "",
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Record key generation performance metrics.

        Args:
            duration: Time taken to generate the cache key (in seconds)
            text_length: Length of the text being processed
            operation_type: Type of operation (summarize, sentiment, etc.)
            additional_data: Additional metadata to store with the metric
        """
        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=time.time(),
            operation_type=operation_type,
            additional_data=additional_data or {},
        )

        self.key_generation_times.append(metric)
        self._cleanup_old_measurements(self.key_generation_times)

        # Log warning if performance is poor
        if duration > self.key_generation_threshold:
            logger.warning(
                f"Slow key generation: {duration:.3f}s for {text_length} chars "
                f"in {operation_type} operation"
            )

        logger.debug(
            f"Key generation time: {duration:.3f}s for {text_length} chars "
            f"({operation_type})"
        )

    def record_cache_operation_time(
        self,
        operation: str,
        duration: float,
        cache_hit: bool,
        text_length: int = 0,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Record cache operation performance (get/set operations).

        Args:
            operation: Operation type ('get', 'set', 'delete', etc.)
            duration: Time taken for the operation (in seconds)
            cache_hit: Whether this was a cache hit (for get operations)
            text_length: Length of text being cached/retrieved
            additional_data: Additional metadata to store
        """
        metric = PerformanceMetric(
            duration=duration,
            text_length=text_length,
            timestamp=time.time(),
            operation_type=operation,
            additional_data=additional_data or {},
        )

        self.cache_operation_times.append(metric)
        self._cleanup_old_measurements(self.cache_operation_times)

        # Update cache hit/miss statistics
        self.total_operations += 1
        if operation == "get":
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

        # Log warning if operation is slow
        if duration > self.cache_operation_threshold:
            logger.warning(
                f"Slow cache {operation}: {duration:.3f}s "
                f"(hit: {cache_hit}, text_length: {text_length})"
            )

        logger.debug(
            f"Cache {operation} time: {duration:.3f}s "
            f"(hit: {cache_hit}, text_length: {text_length})"
        )

    def record_compression_ratio(
        self,
        original_size: int,
        compressed_size: int,
        compression_time: float,
        operation_type: str = "",
    ):
        """
        Record compression performance and efficiency metrics.

        Args:
            original_size: Size of data before compression (in bytes)
            compressed_size: Size of data after compression (in bytes)
            compression_time: Time taken to compress (in seconds)
            operation_type: Type of operation being compressed
        """
        compression_ratio = (
            compressed_size / original_size if original_size > 0 else 1.0
        )

        metric = CompressionMetric(
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            compression_time=compression_time,
            timestamp=time.time(),
            operation_type=operation_type,
        )

        self.compression_ratios.append(metric)
        self._cleanup_old_measurements(self.compression_ratios)

        savings = original_size - compressed_size
        savings_percent = (savings / original_size * 100) if original_size > 0 else 0

        logger.debug(
            f"Compression: {original_size} -> {compressed_size} bytes "
            f"({savings_percent:.1f}% savings, {compression_time:.3f}s, {operation_type})"
        )

    def record_memory_usage(
        self,
        memory_cache: Dict[str, Any],
        redis_stats: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Record current memory usage of cache components.

        Args:
            memory_cache: The in-memory cache dictionary to measure
            redis_stats: Optional Redis statistics for total cache size
            additional_data: Additional metadata to store
        """
        # Calculate memory cache size
        memory_cache_size_bytes = self._calculate_dict_size(memory_cache)
        memory_cache_entry_count = len(memory_cache)

        # Calculate average entry size if we have entries
        avg_entry_size_bytes = 0.0
        if memory_cache_entry_count > 0:
            avg_entry_size_bytes = memory_cache_size_bytes / memory_cache_entry_count

        # Get total cache size from Redis stats if available
        total_cache_size_bytes = memory_cache_size_bytes
        cache_entry_count = memory_cache_entry_count

        if redis_stats and "memory_used_bytes" in redis_stats:
            total_cache_size_bytes += redis_stats["memory_used_bytes"]
            if "keys" in redis_stats:
                cache_entry_count += redis_stats["keys"]

        # Get current process memory usage
        process_memory_mb = self._get_process_memory_mb()

        # Calculate cache utilization percentage (relative to warning threshold)
        cache_utilization_percent = (
            total_cache_size_bytes / self.memory_warning_threshold_bytes
        ) * 100

        # Check if warning threshold is reached
        warning_threshold_reached = (
            total_cache_size_bytes >= self.memory_warning_threshold_bytes
        )

        metric = MemoryUsageMetric(
            total_cache_size_bytes=total_cache_size_bytes,
            cache_entry_count=cache_entry_count,
            avg_entry_size_bytes=avg_entry_size_bytes,
            memory_cache_size_bytes=memory_cache_size_bytes,
            memory_cache_entry_count=memory_cache_entry_count,
            process_memory_mb=process_memory_mb,
            timestamp=time.time(),
            cache_utilization_percent=cache_utilization_percent,
            warning_threshold_reached=warning_threshold_reached,
            additional_data=additional_data or {},
        )

        self.memory_usage_measurements.append(metric)
        self._cleanup_old_measurements(self.memory_usage_measurements)

        # Log warnings based on memory usage
        if total_cache_size_bytes >= self.memory_critical_threshold_bytes:
            logger.error(
                f"Critical cache memory usage: {total_cache_size_bytes / 1024 / 1024:.1f}MB "
                f"(>{self.memory_critical_threshold_bytes / 1024 / 1024:.1f}MB threshold)"
            )
        elif warning_threshold_reached:
            logger.warning(
                f"High cache memory usage: {total_cache_size_bytes / 1024 / 1024:.1f}MB "
                f"(>{self.memory_warning_threshold_bytes / 1024 / 1024:.1f}MB threshold)"
            )

        logger.debug(
            f"Cache memory usage: {total_cache_size_bytes / 1024 / 1024:.1f}MB "
            f"({cache_entry_count} entries, {cache_utilization_percent:.1f}% of threshold)"
        )

        return metric

    def record_invalidation_event(
        self,
        pattern: str,
        keys_invalidated: int,
        duration: float,
        invalidation_type: str = "manual",
        operation_context: str = "",
        additional_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Record cache invalidation event for frequency analysis.

        Args:
            pattern: Pattern used for invalidation
            keys_invalidated: Number of keys that were invalidated
            duration: Time taken for the invalidation operation
            invalidation_type: Type of invalidation ('manual', 'automatic', 'ttl_expired', etc.)
            operation_context: Context that triggered the invalidation
            additional_data: Additional metadata to store
        """
        metric = InvalidationMetric(
            pattern=pattern,
            keys_invalidated=keys_invalidated,
            duration=duration,
            timestamp=time.time(),
            invalidation_type=invalidation_type,
            operation_context=operation_context,
            additional_data=additional_data or {},
        )

        self.invalidation_events.append(metric)
        self._cleanup_old_measurements(self.invalidation_events)

        # Update overall invalidation statistics
        self.total_invalidations += 1
        self.total_keys_invalidated += keys_invalidated

        # Check for high invalidation frequency
        current_hour_invalidations = self._get_invalidations_in_last_hour()

        if current_hour_invalidations >= self.invalidation_rate_critical_per_hour:
            logger.error(
                f"Critical invalidation rate: {current_hour_invalidations} invalidations in last hour "
                f"(>{self.invalidation_rate_critical_per_hour} threshold)"
            )
        elif current_hour_invalidations >= self.invalidation_rate_warning_per_hour:
            logger.warning(
                f"High invalidation rate: {current_hour_invalidations} invalidations in last hour "
                f"(>{self.invalidation_rate_warning_per_hour} threshold)"
            )

        logger.debug(
            f"Cache invalidation: pattern='{pattern}', keys={keys_invalidated}, "
            f"time={duration:.3f}s, type={invalidation_type}, context={operation_context}"
        )

    def _get_invalidations_in_last_hour(self) -> int:
        """
        Get the number of invalidations in the last hour.

        Counts invalidation events that occurred within the past 3600 seconds
        from the current time. Used for frequency analysis and alerting.

        Returns:
            int: Number of invalidation events in the last hour.
        """
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1 hour ago

        return len(
            [
                event
                for event in self.invalidation_events
                if event.timestamp > cutoff_time
            ]
        )

    def get_invalidation_frequency_stats(self) -> Dict[str, Any]:
        """
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
        """
        if not self.invalidation_events:
            return {
                "no_invalidations": True,
                "total_invalidations": 0,
                "total_keys_invalidated": 0,
                "warning_threshold_per_hour": self.invalidation_rate_warning_per_hour,
                "critical_threshold_per_hour": self.invalidation_rate_critical_per_hour,
            }

        current_time = time.time()
        recent_events = self.invalidation_events[-50:]  # Last 50 events for analysis

        # Time-based analysis
        last_hour_events = [
            e for e in self.invalidation_events if e.timestamp > current_time - 3600
        ]
        last_24h_events = [
            e for e in self.invalidation_events if e.timestamp > current_time - 86400
        ]

        # Pattern analysis
        pattern_counts = {}
        type_counts = {}
        for event in recent_events:
            pattern_counts[event.pattern] = pattern_counts.get(event.pattern, 0) + 1
            type_counts[event.invalidation_type] = (
                type_counts.get(event.invalidation_type, 0) + 1
            )

        # Calculate rates
        hourly_rate = len(last_hour_events)
        daily_rate = len(last_24h_events)

        # Determine alert level
        alert_level = "normal"
        if hourly_rate >= self.invalidation_rate_critical_per_hour:
            alert_level = "critical"
        elif hourly_rate >= self.invalidation_rate_warning_per_hour:
            alert_level = "warning"

        return {
            "total_invalidations": self.total_invalidations,
            "total_keys_invalidated": self.total_keys_invalidated,
            "rates": {
                "last_hour": hourly_rate,
                "last_24_hours": daily_rate,
                "average_per_hour": len(self.invalidation_events)
                / (self.retention_hours if self.retention_hours > 0 else 1),
            },
            "thresholds": {
                "warning_per_hour": self.invalidation_rate_warning_per_hour,
                "critical_per_hour": self.invalidation_rate_critical_per_hour,
                "current_alert_level": alert_level,
            },
            "patterns": {
                "most_common_patterns": dict(
                    sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[
                        :10
                    ]
                ),
                "invalidation_types": type_counts,
            },
            "efficiency": {
                "avg_keys_per_invalidation": self.total_keys_invalidated
                / self.total_invalidations
                if self.total_invalidations > 0
                else 0,
                "avg_duration": mean([e.duration for e in recent_events])
                if recent_events
                else 0,
                "max_duration": max([e.duration for e in recent_events])
                if recent_events
                else 0,
            },
        }

    def get_invalidation_recommendations(self) -> List[Dict[str, Any]]:
        """
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
        """
        recommendations = []

        if not self.invalidation_events:
            return recommendations

        stats = self.get_invalidation_frequency_stats()

        # High frequency warning
        if stats["rates"]["last_hour"] >= self.invalidation_rate_warning_per_hour:
            recommendations.append(
                {
                    "severity": "warning"
                    if stats["thresholds"]["current_alert_level"] == "warning"
                    else "critical",
                    "issue": "High invalidation frequency",
                    "message": f"Cache is being invalidated {stats['rates']['last_hour']} times per hour",
                    "suggestions": [
                        "Review invalidation triggers to reduce unnecessary clearing",
                        "Consider using more specific patterns for selective invalidation",
                        "Check if TTL values are set too low",
                        "Analyze if cache warming strategy needs improvement",
                    ],
                }
            )

        # Pattern analysis
        patterns = stats["patterns"]["most_common_patterns"]
        if len(patterns) > 0:
            most_common_pattern = list(patterns.keys())[0]
            most_common_count = patterns[most_common_pattern]

            if (
                most_common_count > len(self.invalidation_events) * 0.5
            ):  # More than 50% of invalidations
                recommendations.append(
                    {
                        "severity": "info",
                        "issue": "Dominant invalidation pattern",
                        "message": f"Pattern '{most_common_pattern}' accounts for {most_common_count} of recent invalidations",
                        "suggestions": [
                            f"Consider optimizing operations that trigger '{most_common_pattern}' invalidations",
                            "Evaluate if this pattern could be made more specific",
                            "Check if related data could be cached with different strategies",
                        ],
                    }
                )

        # Efficiency analysis
        avg_keys = stats["efficiency"]["avg_keys_per_invalidation"]
        if avg_keys < 1.0:
            recommendations.append(
                {
                    "severity": "info",
                    "issue": "Low invalidation efficiency",
                    "message": f"Average of {avg_keys:.1f} keys invalidated per operation",
                    "suggestions": [
                        "Many invalidation operations are not finding keys to clear",
                        "Consider using more targeted patterns",
                        "Review if cache keys are structured optimally for invalidation",
                    ],
                }
            )
        elif avg_keys > 100.0:
            recommendations.append(
                {
                    "severity": "warning",
                    "issue": "High invalidation impact",
                    "message": f"Average of {avg_keys:.0f} keys invalidated per operation",
                    "suggestions": [
                        "Invalidation operations are clearing large numbers of entries",
                        "Consider using more selective patterns to preserve valid cache entries",
                        "Evaluate if smaller, more frequent invalidations would be better",
                    ],
                }
            )

        return recommendations

    def _calculate_dict_size(self, obj: Any) -> int:
        """
        Calculate the approximate memory size of a Python object in bytes.

        Args:
            obj: Object to measure

        Returns:
            Estimated size in bytes
        """
        try:
            # Use sys.getsizeof for basic size calculation
            size = sys.getsizeof(obj)

            # For dictionaries, add size of keys and values
            if isinstance(obj, dict):
                for key, value in obj.items():
                    size += sys.getsizeof(key)
                    # Recursively calculate nested dict/list sizes
                    if isinstance(value, (dict, list)):
                        size += self._calculate_dict_size(value)
                    else:
                        size += sys.getsizeof(value)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        size += self._calculate_dict_size(item)
                    else:
                        size += sys.getsizeof(item)

            return size
        except Exception as e:
            logger.warning(f"Error calculating object size: {e}")
            return 0

    def _get_process_memory_mb(self) -> float:
        """
        Get current process memory usage in MB.

        Returns:
            Memory usage in MB, or 0.0 if cannot be determined
        """
        try:
            # Try to use psutil if available
            try:
                import psutil

                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024  # Convert bytes to MB
            except ImportError:
                pass

            # Fallback to reading /proc/self/status on Linux
            try:
                with open("/proc/self/status", "r") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            # Extract memory in KB and convert to MB
                            kb = int(line.split()[1])
                            return kb / 1024
            except (IOError, ValueError, IndexError):
                pass

            # If all methods fail, return 0
            return 0.0

        except Exception as e:
            logger.debug(f"Could not determine process memory usage: {e}")
            return 0.0

    def get_memory_usage_stats(self) -> Dict[str, Any]:
        """
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
        """
        if not self.memory_usage_measurements:
            return {
                "no_measurements": True,
                "warning_threshold_mb": self.memory_warning_threshold_bytes
                / 1024
                / 1024,
                "critical_threshold_mb": self.memory_critical_threshold_bytes
                / 1024
                / 1024,
            }

        # Get latest measurement
        latest = self.memory_usage_measurements[-1]

        # Calculate trends from recent measurements (last 10)
        recent_measurements = self.memory_usage_measurements[-10:]
        total_sizes = [m.total_cache_size_bytes for m in recent_measurements]
        memory_cache_sizes = [m.memory_cache_size_bytes for m in recent_measurements]
        entry_counts = [m.cache_entry_count for m in recent_measurements]

        stats = {
            "current": {
                "total_cache_size_mb": latest.total_cache_size_bytes / 1024 / 1024,
                "memory_cache_size_mb": latest.memory_cache_size_bytes / 1024 / 1024,
                "cache_entry_count": latest.cache_entry_count,
                "memory_cache_entry_count": latest.memory_cache_entry_count,
                "avg_entry_size_bytes": latest.avg_entry_size_bytes,
                "process_memory_mb": latest.process_memory_mb,
                "cache_utilization_percent": latest.cache_utilization_percent,
                "warning_threshold_reached": latest.warning_threshold_reached,
            },
            "thresholds": {
                "warning_threshold_mb": self.memory_warning_threshold_bytes
                / 1024
                / 1024,
                "critical_threshold_mb": self.memory_critical_threshold_bytes
                / 1024
                / 1024,
                "warning_threshold_reached": latest.warning_threshold_reached,
                "critical_threshold_reached": latest.total_cache_size_bytes
                >= self.memory_critical_threshold_bytes,
            },
            "trends": {
                "total_measurements": len(self.memory_usage_measurements),
                "avg_total_cache_size_mb": mean(total_sizes) / 1024 / 1024,
                "max_total_cache_size_mb": max(total_sizes) / 1024 / 1024,
                "avg_memory_cache_size_mb": mean(memory_cache_sizes) / 1024 / 1024,
                "avg_entry_count": mean(entry_counts),
                "max_entry_count": max(entry_counts),
            },
        }

        # Add growth analysis if we have enough measurements
        if len(recent_measurements) >= 2:
            size_change = total_sizes[-1] - total_sizes[0]
            time_span = (
                recent_measurements[-1].timestamp - recent_measurements[0].timestamp
            )
            if time_span > 0:
                growth_rate_mb_per_hour = (size_change / time_span) * 3600 / 1024 / 1024
                stats["trends"]["growth_rate_mb_per_hour"] = growth_rate_mb_per_hour

        return stats

    def get_memory_warnings(self) -> List[Dict[str, Any]]:
        """
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
        """
        warnings = []

        if not self.memory_usage_measurements:
            return warnings

        latest = self.memory_usage_measurements[-1]

        # Critical memory usage
        if latest.total_cache_size_bytes >= self.memory_critical_threshold_bytes:
            warnings.append(
                {
                    "severity": "critical",
                    "message": f"Cache memory usage is {latest.total_cache_size_bytes / 1024 / 1024:.1f}MB, "
                    f"exceeding critical threshold of {self.memory_critical_threshold_bytes / 1024 / 1024:.1f}MB",
                    "recommendations": [
                        "Consider reducing cache TTL values",
                        "Implement more aggressive cache eviction",
                        "Review and optimize large cached responses",
                        "Consider increasing memory limits or scaling horizontally",
                    ],
                }
            )

        # Warning memory usage
        elif latest.warning_threshold_reached:
            warnings.append(
                {
                    "severity": "warning",
                    "message": f"Cache memory usage is {latest.total_cache_size_bytes / 1024 / 1024:.1f}MB, "
                    f"exceeding warning threshold of {self.memory_warning_threshold_bytes / 1024 / 1024:.1f}MB",
                    "recommendations": [
                        "Monitor cache growth closely",
                        "Review cache key patterns for optimization",
                        "Consider reducing memory cache size limit",
                    ],
                }
            )

        # High memory cache utilization
        if latest.memory_cache_entry_count > 0:
            # Assume a max memory cache size based on common patterns (this could be injected)
            estimated_max_entries = (
                100  # This should ideally be passed from the cache instance
            )
            utilization = (
                latest.memory_cache_entry_count / estimated_max_entries
            ) * 100

            if utilization > 90:
                warnings.append(
                    {
                        "severity": "info",
                        "message": f"Memory cache is {utilization:.1f}% full ({latest.memory_cache_entry_count}/{estimated_max_entries} entries)",
                        "recommendations": [
                            "Memory cache eviction is working properly",
                            "Consider increasing memory cache size if hit rates are good",
                        ],
                    }
                )

        return warnings

    def _cleanup_old_measurements(self, measurements: List):
        """
        Clean up old measurements based on retention policy and size limits.

        Removes measurements that exceed the configured retention period or
        maximum count limits. This prevents unbounded memory growth while
        maintaining recent performance data.

        Args:
            measurements (List): List of measurement objects to clean up.
                               Modified in-place to remove old entries.

        Note:
            - Measurements older than retention_hours are removed
            - If count exceeds max_measurements, oldest entries are removed
            - List is modified in-place for efficiency
        """
        if not measurements:
            return

        current_time = time.time()
        cutoff_time = current_time - (self.retention_hours * 3600)

        # Remove measurements older than retention period
        measurements[:] = [m for m in measurements if m.timestamp > cutoff_time]

        # Limit total number of measurements
        if len(measurements) > self.max_measurements:
            # Keep the most recent measurements
            measurements[:] = measurements[-self.max_measurements :]

        logger.debug(f"Cleaned up measurements, {len(measurements)} remaining")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
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
        """
        # Clean up old measurements first
        self._cleanup_old_measurements(self.key_generation_times)
        self._cleanup_old_measurements(self.cache_operation_times)
        self._cleanup_old_measurements(self.compression_ratios)
        self._cleanup_old_measurements(self.memory_usage_measurements)
        self._cleanup_old_measurements(self.invalidation_events)

        stats = {
            "timestamp": datetime.now().isoformat(),
            "retention_hours": self.retention_hours,
            "cache_hit_rate": self._calculate_hit_rate(),
            "total_cache_operations": self.total_operations,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

        # Key generation statistics
        if self.key_generation_times:
            key_gen_durations = [m.duration for m in self.key_generation_times]
            key_gen_text_lengths = [m.text_length for m in self.key_generation_times]

            stats["key_generation"] = {
                "total_operations": len(self.key_generation_times),
                "avg_duration": mean(key_gen_durations),
                "median_duration": median(key_gen_durations),
                "max_duration": max(key_gen_durations),
                "min_duration": min(key_gen_durations),
                "avg_text_length": mean(key_gen_text_lengths),
                "max_text_length": max(key_gen_text_lengths),
                "slow_operations": len(
                    [d for d in key_gen_durations if d > self.key_generation_threshold]
                ),
            }

        # Cache operation statistics
        if self.cache_operation_times:
            cache_op_durations = [m.duration for m in self.cache_operation_times]

            # Group by operation type
            ops_by_type = {}
            for metric in self.cache_operation_times:
                op_type = metric.operation_type
                if op_type not in ops_by_type:
                    ops_by_type[op_type] = []
                ops_by_type[op_type].append(metric.duration)

            stats["cache_operations"] = {
                "total_operations": len(self.cache_operation_times),
                "avg_duration": mean(cache_op_durations),
                "median_duration": median(cache_op_durations),
                "max_duration": max(cache_op_durations),
                "min_duration": min(cache_op_durations),
                "slow_operations": len(
                    [
                        d
                        for d in cache_op_durations
                        if d > self.cache_operation_threshold
                    ]
                ),
                "by_operation_type": {
                    op_type: {
                        "count": len(durations),
                        "avg_duration": mean(durations),
                        "max_duration": max(durations),
                    }
                    for op_type, durations in ops_by_type.items()
                },
            }

        # Compression statistics
        if self.compression_ratios:
            ratios = [m.compression_ratio for m in self.compression_ratios]
            comp_times = [m.compression_time for m in self.compression_ratios]
            original_sizes = [m.original_size for m in self.compression_ratios]
            compressed_sizes = [m.compressed_size for m in self.compression_ratios]

            total_original = sum(original_sizes)
            total_compressed = sum(compressed_sizes)
            overall_savings = total_original - total_compressed
            overall_savings_percent = (
                (overall_savings / total_original * 100) if total_original > 0 else 0
            )

            stats["compression"] = {
                "total_operations": len(self.compression_ratios),
                "avg_compression_ratio": mean(ratios),
                "median_compression_ratio": median(ratios),
                "best_compression_ratio": min(ratios),
                "worst_compression_ratio": max(ratios),
                "avg_compression_time": mean(comp_times),
                "max_compression_time": max(comp_times),
                "total_bytes_processed": total_original,
                "total_bytes_saved": overall_savings,
                "overall_savings_percent": overall_savings_percent,
            }

        # Memory usage statistics
        if self.memory_usage_measurements:
            memory_stats = self.get_memory_usage_stats()
            stats["memory_usage"] = memory_stats

        # Invalidation statistics
        if self.invalidation_events:
            invalidation_stats = self.get_invalidation_frequency_stats()
            stats["invalidation"] = invalidation_stats

        return stats

    def _calculate_hit_rate(self) -> float:
        """
        Calculate cache hit rate as a percentage.

        Computes the percentage of cache operations that resulted in successful
        hits versus total operations. Used for performance analysis and monitoring.

        Returns:
            float: Hit rate as a percentage (0.0 to 100.0).
                  Returns 0.0 if no operations have been recorded.
        """
        if self.total_operations == 0:
            return 0.0
        return (self.cache_hits / self.total_operations) * 100

    def get_recent_slow_operations(
        self, threshold_multiplier: float = 2.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
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
        """
        slow_ops = {"key_generation": [], "cache_operations": [], "compression": []}

        # Analyze key generation times
        if self.key_generation_times:
            avg_duration = mean([m.duration for m in self.key_generation_times])
            threshold = avg_duration * threshold_multiplier

            for metric in self.key_generation_times:
                if metric.duration > threshold:
                    slow_ops["key_generation"].append(
                        {
                            "duration": metric.duration,
                            "text_length": metric.text_length,
                            "operation_type": metric.operation_type,
                            "timestamp": datetime.fromtimestamp(
                                metric.timestamp
                            ).isoformat(),
                            "times_slower": metric.duration / avg_duration,
                        }
                    )

        # Analyze cache operations
        if self.cache_operation_times:
            avg_duration = mean([m.duration for m in self.cache_operation_times])
            threshold = avg_duration * threshold_multiplier

            for metric in self.cache_operation_times:
                if metric.duration > threshold:
                    slow_ops["cache_operations"].append(
                        {
                            "duration": metric.duration,
                            "operation_type": metric.operation_type,
                            "text_length": metric.text_length,
                            "timestamp": datetime.fromtimestamp(
                                metric.timestamp
                            ).isoformat(),
                            "times_slower": metric.duration / avg_duration,
                        }
                    )

        # Analyze compression times
        if self.compression_ratios:
            avg_duration = mean([m.compression_time for m in self.compression_ratios])
            threshold = avg_duration * threshold_multiplier

            for metric in self.compression_ratios:
                if metric.compression_time > threshold:
                    slow_ops["compression"].append(
                        {
                            "compression_time": metric.compression_time,
                            "original_size": metric.original_size,
                            "compression_ratio": metric.compression_ratio,
                            "operation_type": metric.operation_type,
                            "timestamp": datetime.fromtimestamp(
                                metric.timestamp
                            ).isoformat(),
                            "times_slower": metric.compression_time / avg_duration,
                        }
                    )

        return slow_ops

    def reset_stats(self):
        """
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
        """
        self.key_generation_times.clear()
        self.cache_operation_times.clear()
        self.compression_ratios.clear()
        self.memory_usage_measurements.clear()
        self.invalidation_events.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_operations = 0
        self.total_invalidations = 0
        self.total_keys_invalidated = 0
        logger.info("Cache performance statistics reset")

    def export_metrics(self) -> Dict[str, Any]:
        """
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
        """
        return {
            "key_generation_times": [asdict(m) for m in self.key_generation_times],
            "cache_operation_times": [asdict(m) for m in self.cache_operation_times],
            "compression_ratios": [asdict(m) for m in self.compression_ratios],
            "memory_usage_measurements": [
                asdict(m) for m in self.memory_usage_measurements
            ],
            "invalidation_events": [asdict(m) for m in self.invalidation_events],
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_operations": self.total_operations,
            "total_invalidations": self.total_invalidations,
            "total_keys_invalidated": self.total_keys_invalidated,
            "export_timestamp": datetime.now().isoformat(),
        }
