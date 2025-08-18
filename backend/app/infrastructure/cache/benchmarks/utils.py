"""
Cache Benchmarking Utility Functions

This module provides statistical calculations and memory tracking utilities
for cache performance benchmarking. These utilities are extracted from the
original monolithic benchmarks module for better reusability and testing.

Classes:
    StatisticalCalculator: Statistical analysis methods for benchmark data
    MemoryTracker: Memory usage tracking and measurement utilities

The utilities support comprehensive statistical analysis including percentiles,
standard deviation, outlier detection, confidence intervals, and memory tracking
with fallback mechanisms for different environments.
"""

import math
import statistics
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)


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
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (percentile / 100.0)
        f = int(k)
        c = k - f
        
        if f == len(sorted_data) - 1:
            return sorted_data[f]
        else:
            return sorted_data[f] * (1 - c) + sorted_data[f + 1] * c
    
    @staticmethod
    def calculate_standard_deviation(data: List[float]) -> float:
        """
        Calculate standard deviation with robust error handling.
        
        Args:
            data: List of numeric values
            
        Returns:
            Standard deviation, or 0.0 if insufficient data or calculation fails
        """
        if len(data) < 2:
            return 0.0
        
        try:
            return statistics.stdev(data)
        except statistics.StatisticsError:
            return 0.0
    
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
        if len(data) < 4:
            return {"outliers": [], "outlier_count": 0, "clean_data": data}
        
        sorted_data = sorted(data)
        q1 = StatisticalCalculator.percentile(sorted_data, 25)
        q3 = StatisticalCalculator.percentile(sorted_data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        clean_data = [x for x in data if lower_bound <= x <= upper_bound]
        
        return {
            "outliers": outliers,
            "outlier_count": len(outliers),
            "clean_data": clean_data,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "iqr": iqr
        }
    
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
        if len(data) < 2:
            return {"lower": 0.0, "upper": 0.0, "margin_of_error": 0.0}
        
        try:
            mean = statistics.mean(data)
            stdev = statistics.stdev(data)
            n = len(data)
            
            # Use t-distribution for small samples, normal for large
            if n >= 30:
                # Normal distribution (z-score)
                z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
                margin_of_error = z_score * (stdev / math.sqrt(n))
            else:
                # t-distribution (simplified - using approximation)
                t_score = 2.0 + (0.3 / n)  # Rough approximation for small samples
                margin_of_error = t_score * (stdev / math.sqrt(n))
            
            return {
                "lower": mean - margin_of_error,
                "upper": mean + margin_of_error,
                "margin_of_error": margin_of_error
            }
        except Exception as e:
            logger.debug(f"Could not calculate confidence intervals: {e}")
            return {"lower": 0.0, "upper": 0.0, "margin_of_error": 0.0}
    
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
        if not data:
            return {}
        
        result = {
            "mean": statistics.mean(data),
            "median": StatisticalCalculator.percentile(data, 50),
            "std_dev": StatisticalCalculator.calculate_standard_deviation(data),
            "p50": StatisticalCalculator.percentile(data, 50),
            "p95": StatisticalCalculator.percentile(data, 95),
            "p99": StatisticalCalculator.percentile(data, 99),
            "min": min(data),
            "max": max(data),
            "count": len(data)
        }
        
        # Add outlier analysis
        outlier_info = StatisticalCalculator.detect_outliers(data)
        result.update(outlier_info)
        
        # Add confidence intervals
        ci = StatisticalCalculator.calculate_confidence_intervals(data)
        result["confidence_interval"] = ci
        
        return result


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
        memory_info = {"process_mb": 0.0, "available_mb": 0.0, "total_mb": 0.0}
        
        try:
            import psutil
            
            # Process memory
            process = psutil.Process()
            memory_info["process_mb"] = process.memory_info().rss / 1024 / 1024
            
            # System memory
            vm = psutil.virtual_memory()
            memory_info["available_mb"] = vm.available / 1024 / 1024
            memory_info["total_mb"] = vm.total / 1024 / 1024
            memory_info["percent_used"] = vm.percent
            
        except ImportError:
            # Fallback for process memory only
            memory_info["process_mb"] = self.get_process_memory_mb()
        except Exception as e:
            logger.debug(f"Could not get comprehensive memory usage: {e}")
        
        return memory_info
    
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
        try:
            # Try to use psutil if available
            try:
                import psutil
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
            except ImportError:
                pass
            
            # Fallback to reading /proc/self/status on Linux
            try:
                with open("/proc/self/status", "r") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            kb = int(line.split()[1])
                            return kb / 1024
            except (IOError, ValueError, IndexError):
                pass
            
            # If all methods fail, return 0
            return 0.0
            
        except Exception as e:
            logger.debug(f"Could not determine process memory usage: {e}")
            return 0.0
    
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
        delta = {}
        
        for key in before:
            if key in after and isinstance(before[key], (int, float)) and isinstance(after[key], (int, float)):
                delta[key] = after[key] - before[key]
        
        return delta
    
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
        if not memory_measurements:
            return {}
        
        peaks = {}
        
        # Find all available keys
        all_keys = set()
        for measurement in memory_measurements:
            all_keys.update(measurement.keys())
        
        # Calculate peak for each metric
        for key in all_keys:
            values = [m.get(key, 0) for m in memory_measurements if key in m and isinstance(m[key], (int, float))]
            if values:
                peaks[key] = max(values)
        
        return peaks