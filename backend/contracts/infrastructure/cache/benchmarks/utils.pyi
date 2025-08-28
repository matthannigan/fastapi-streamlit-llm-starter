"""
Advanced statistical analysis and memory tracking utilities for cache performance benchmarking.

This module provides comprehensive statistical calculation and memory monitoring infrastructure
extracted from the original monolithic benchmarks module for improved reusability, testability,
and maintainability. Designed with robust error handling and fallback mechanisms for different
environments and missing dependencies.

Classes:
    StatisticalCalculator: Advanced statistical analysis with outlier detection and confidence intervals
    MemoryTracker: Cross-platform memory monitoring with fallback mechanisms

Key Features:
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

Statistical Analysis Capabilities:
    - Percentile calculations (P50, P95, P99) with linear interpolation
    - Standard deviation with robust handling of non-finite values
    - Outlier detection using 1.5*IQR method with boundary calculation
    - Confidence intervals (95%, 99%) with appropriate distribution selection
    - Comprehensive statistics aggregation in single method call

Memory Tracking Capabilities:
    - Process-specific memory usage tracking (RSS, available, total)
    - System-wide memory utilization monitoring with percentage calculations
    - Memory delta calculation between measurement points
    - Peak memory tracking across measurement series
    - Fallback mechanisms for environments without psutil dependency

Usage Examples:
    Statistical Analysis:
        >>> calc = StatisticalCalculator()
        >>> data = [1.2, 1.5, 1.8, 2.1, 1.9, 1.7, 1.6, 1.4]
        >>> stats = calc.calculate_statistics(data)
        >>> print(f"P95: {stats['p95']:.2f}ms")
        >>> print(f"Mean: {stats['mean']:.2f}ms")
        >>> print(f"Std Dev: {stats['std_dev']:.2f}ms")
        >>>
        >>> outliers = calc.detect_outliers(data)
        >>> print(f"Found {outliers['outlier_count']} outliers")
        >>>
        >>> ci = calc.calculate_confidence_intervals(data)
        >>> print(f"95% CI: [{ci['lower']:.2f}, {ci['upper']:.2f}]")

    Memory Tracking:
        >>> tracker = MemoryTracker()
        >>> before = tracker.get_memory_usage()
        >>> # ... perform operations ...
        >>> after = tracker.get_memory_usage()
        >>> delta = tracker.calculate_memory_delta(before, after)
        >>> print(f"Memory increase: {delta['process_mb']:.1f}MB")
        >>>
        >>> # Peak memory tracking
        >>> measurements = []
        >>> for i in range(10):
        ...     measurements.append(tracker.get_memory_usage())
        ...     # ... perform operations ...
        >>> peaks = tracker.track_peak_memory(measurements)
        >>> print(f"Peak memory: {peaks['process_mb']:.1f}MB")

Thread Safety:
    Both StatisticalCalculator and MemoryTracker are stateless and thread-safe.
    All methods can be called concurrently without interference or shared state issues.
"""

import math
import statistics
from typing import Any, Dict, List, Set
import logging


class StatisticalCalculator:
    """
    Statistical analysis utilities for benchmark data.
    
    This class provides methods for calculating various statistical measures
    commonly used in performance analysis, including percentiles, standard
    deviation, outlier detection, and confidence intervals.
    
    All methods are designed to handle edge cases gracefully and provide
    meaningful results even with small or irregular datasets.
    
    Example:
        >>> calc = StatisticalCalculator()
        >>> data = [1.2, 1.5, 1.8, 2.1, 1.9, 1.7, 1.6, 1.4]
        >>> p95 = calc.percentile(data, 95)
        >>> outliers = calc.detect_outliers(data)
        >>> stats = calc.calculate_statistics(data)
    """

    @staticmethod
    def percentile(data: List[float], percentile: float) -> float:
        """
        Calculate percentile for a list of values.
        
        Uses linear interpolation between data points when the percentile
        falls between two values in the sorted dataset.
        
        Args:
            data: List of numeric values
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Calculated percentile value, or 0.0 if data is empty
        
        Example:
            >>> calc = StatisticalCalculator()
            >>> data = [1, 2, 3, 4, 5]
            >>> p50 = calc.percentile(data, 50)  # Median
            >>> p95 = calc.percentile(data, 95)
        """
        ...

    @staticmethod
    def calculate_standard_deviation(data: List[float]) -> float:
        """
        Calculate standard deviation with robust error handling.
        
        Args:
            data: List of numeric values
        
        Returns:
            Standard deviation, or 0.0 if insufficient data or calculation fails
        """
        ...

    @staticmethod
    def detect_outliers(data: List[float]) -> Dict[str, Any]:
        """
        Detect outliers using the Interquartile Range (IQR) method.
        
        Outliers are defined as values that fall below Q1 - 1.5*IQR or
        above Q3 + 1.5*IQR, where Q1 and Q3 are the 25th and 75th percentiles.
        
        Args:
            data: List of numeric values
        
        Returns:
            Dictionary containing:
            - outliers: List of outlier values
            - outlier_count: Number of outliers found
            - clean_data: Data with outliers removed
            - lower_bound: Lower threshold for outliers
            - upper_bound: Upper threshold for outliers
            - iqr: Interquartile range value
        
        Example:
            >>> calc = StatisticalCalculator()
            >>> data = [1, 2, 3, 4, 5, 100]  # 100 is likely an outlier
            >>> result = calc.detect_outliers(data)
            >>> print(f"Found {result['outlier_count']} outliers")
        """
        ...

    @staticmethod
    def calculate_confidence_intervals(data: List[float], confidence: float = 0.95) -> Dict[str, float]:
        """
        Calculate confidence intervals for the mean.
        
        Uses normal distribution for large samples (n>=30) and a simplified
        t-distribution approximation for smaller samples.
        
        Args:
            data: List of numeric values
            confidence: Confidence level (default: 0.95 for 95% confidence)
        
        Returns:
            Dictionary containing:
            - lower: Lower bound of confidence interval
            - upper: Upper bound of confidence interval
            - margin_of_error: Half-width of the interval
        
        Example:
            >>> calc = StatisticalCalculator()
            >>> data = [1.5, 1.8, 2.1, 1.9, 1.7]
            >>> ci = calc.calculate_confidence_intervals(data, 0.95)
            >>> print(f"95% CI: [{ci['lower']:.2f}, {ci['upper']:.2f}]")
        """
        ...

    @staticmethod
    def calculate_statistics(data: List[float]) -> Dict[str, Any]:
        """
        Calculate comprehensive statistics for a dataset.
        
        This convenience method calculates all common statistical measures
        in a single call, including percentiles, standard deviation, outliers,
        and confidence intervals.
        
        Args:
            data: List of numeric values
        
        Returns:
            Dictionary containing all statistical measures:
            - mean, median, std_dev
            - percentiles (p50, p95, p99)
            - outlier analysis
            - confidence intervals
        
        Example:
            >>> calc = StatisticalCalculator()
            >>> data = [1.2, 1.5, 1.8, 2.1, 1.9, 1.7, 1.6, 1.4]
            >>> stats = calc.calculate_statistics(data)
            >>> print(f"Mean: {stats['mean']:.2f}")
            >>> print(f"P95: {stats['p95']:.2f}")
        """
        ...


class MemoryTracker:
    """
    Memory usage tracking and measurement utilities.
    
    This class provides methods for tracking memory usage during benchmarks,
    with fallback mechanisms for different environments and missing dependencies.
    Supports both process-specific and system-wide memory monitoring.
    
    Example:
        >>> tracker = MemoryTracker()
        >>> memory_info = tracker.get_memory_usage()
        >>> process_memory = tracker.get_process_memory_mb()
        >>> delta = tracker.calculate_memory_delta(before, after)
    """

    def get_memory_usage(self) -> Dict[str, float]:
        """
        Get comprehensive memory usage information.
        
        Attempts to gather both process-specific and system-wide memory
        information using psutil if available, with fallbacks for
        environments where psutil is not installed.
        
        Returns:
            Dictionary containing:
            - process_mb: Current process memory usage in MB
            - available_mb: Available system memory in MB (if available)
            - total_mb: Total system memory in MB (if available)
            - percent_used: System memory utilization percentage (if available)
        
        Example:
            >>> tracker = MemoryTracker()
            >>> memory = tracker.get_memory_usage()
            >>> print(f"Process: {memory['process_mb']:.1f}MB")
            >>> print(f"System: {memory.get('percent_used', 'N/A')}% used")
        """
        ...

    def get_process_memory_mb(self) -> float:
        """
        Get current process memory usage in MB.
        
        Uses multiple fallback methods to ensure memory measurement works
        across different environments:
        1. psutil (preferred)
        2. /proc/self/status on Linux
        3. Returns 0.0 if all methods fail
        
        Returns:
            Process memory usage in megabytes, or 0.0 if measurement fails
        
        Example:
            >>> tracker = MemoryTracker()
            >>> memory_mb = tracker.get_process_memory_mb()
            >>> print(f"Process using {memory_mb:.1f}MB")
        """
        ...

    def calculate_memory_delta(self, before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate memory usage delta between two measurements.
        
        Args:
            before: Memory measurement before operation
            after: Memory measurement after operation
        
        Returns:
            Dictionary containing memory deltas for all available metrics
        
        Example:
            >>> tracker = MemoryTracker()
            >>> before = tracker.get_memory_usage()
            >>> # ... perform operation ...
            >>> after = tracker.get_memory_usage()
            >>> delta = tracker.calculate_memory_delta(before, after)
            >>> print(f"Memory increase: {delta['process_mb']:.1f}MB")
        """
        ...

    def track_peak_memory(self, memory_measurements: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Track peak memory usage from a series of measurements.
        
        Args:
            memory_measurements: List of memory measurement dictionaries
        
        Returns:
            Dictionary containing peak values for each memory metric
        
        Example:
            >>> tracker = MemoryTracker()
            >>> measurements = []
            >>> for i in range(10):
            >>>     measurements.append(tracker.get_memory_usage())
            >>>     # ... perform operations ...
            >>> peaks = tracker.track_peak_memory(measurements)
            >>> print(f"Peak memory: {peaks['process_mb']:.1f}MB")
        """
        ...
