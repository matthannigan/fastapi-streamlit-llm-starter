"""
[REFACTORED] Comprehensive cache benchmarking data models with statistical analysis and comparison utilities.

This module provides complete data model infrastructure for cache performance benchmarking
including individual result containers, before/after comparison analysis, and benchmark
suite aggregation with performance grading and statistical analysis capabilities.

Classes:
    BenchmarkResult: Individual benchmark measurement with comprehensive metrics and analysis
    ComparisonResult: Before/after performance comparison with regression detection
    BenchmarkSuite: Collection of benchmark results with suite-level analysis and grading

Key Features:
    - **Comprehensive Metrics**: Complete performance data including timing percentiles,
      memory usage, throughput, success rates, and optional cache-specific metrics.
    
    - **Statistical Analysis**: Built-in performance grading, threshold validation,
      and comprehensive statistical analysis with percentile calculations.
    
    - **Comparison Analysis**: Detailed before/after comparison with percentage changes,
      regression detection, and improvement/degradation area identification.
    
    - **Suite Aggregation**: Collection-level analysis with overall scoring, performance
      grading, and operation-specific result retrieval.
    
    - **Serialization Support**: Full JSON serialization support for data persistence,
      API integration, and report generation with datetime stamping.
    
    - **Performance Grading**: Automated performance assessment using industry-standard
      thresholds with Excellent/Good/Acceptable/Poor/Critical classifications.

Data Model Structure:
    BenchmarkResult contains individual benchmark metrics:
    - Core timing metrics (avg, min, max, percentiles, std dev)
    - Memory usage tracking (usage, peak consumption)
    - Throughput and success rate analysis
    - Optional cache-specific metrics (hit rates, compression)
    - Metadata and timestamp information
    
    ComparisonResult provides before/after analysis:
    - Performance change percentages
    - Regression detection flags
    - Improvement and degradation area identification
    - Strategic recommendations
    
    BenchmarkSuite aggregates multiple results:
    - Overall performance grading
    - Suite-level scoring and pass rates
    - Failed benchmark tracking
    - Environment context preservation

Usage Examples:
    Individual Result Analysis:
        >>> result = BenchmarkResult(
        ...     operation_type="get",
        ...     avg_duration_ms=1.5,
        ...     p95_duration_ms=3.2,
        ...     operations_per_second=800.0,
        ...     success_rate=1.0
        ... )
        >>> print(result.performance_grade())  # "Excellent"
        >>> print(result.meets_threshold(5.0))  # True
        >>> data = result.to_dict()  # For serialization
        
    Before/After Comparison:
        >>> comparison = ComparisonResult(
        ...     original_cache_results=old_result,
        ...     new_cache_results=new_result,
        ...     performance_change_percent=-15.2,  # 15.2% improvement
        ...     regression_detected=False
        ... )
        >>> print(comparison.summary())  # "Performance improved by 15.2%..."
        >>> recommendations = comparison.generate_recommendations()
        
    Suite Analysis:
        >>> suite = BenchmarkSuite(
        ...     name="Redis Cache Performance",
        ...     results=[result1, result2, result3],
        ...     pass_rate=1.0,
        ...     performance_grade="Good"
        ... )
        >>> score = suite.calculate_overall_score()
        >>> get_result = suite.get_operation_result("get")
        >>> json_data = suite.to_json()  # Full suite serialization

Thread Safety:
    All data model classes are immutable after construction and thread-safe for
    concurrent access. Serialization methods are stateless and safe for concurrent use.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BenchmarkResult:
    """
    Comprehensive result data for a single cache performance benchmark.
    
    This class captures all metrics from a benchmark run including timing,
    memory usage, success rates, and optional cache-specific metrics like
    hit rates and compression ratios.
    
    Attributes:
        operation_type: Type of cache operation (get, set, delete, etc.)
        duration_ms: Total duration in milliseconds
        memory_peak_mb: Peak memory usage during benchmark
        iterations: Number of iterations performed
        avg_duration_ms: Average duration per operation
        min_duration_ms: Minimum operation duration
        max_duration_ms: Maximum operation duration
        p95_duration_ms: 95th percentile duration
        p99_duration_ms: 99th percentile duration
        std_dev_ms: Standard deviation of operation times
        operations_per_second: Throughput metric
        success_rate: Percentage of successful operations (0-1)
        memory_usage_mb: Average memory usage
        cache_hit_rate: Cache hit rate if applicable (0-1)
        compression_ratio: Compression efficiency if applicable
        compression_savings_mb: Memory saved through compression
        median_duration_ms: Median operation duration
        error_count: Number of failed operations
        test_data_size_bytes: Size of test data used
        additional_metrics: Custom metrics dictionary
        metadata: Additional metadata about the benchmark
        timestamp: ISO format timestamp of benchmark execution
    
    Example:
        >>> result = BenchmarkResult(
        ...     operation_type="get",
        ...     duration_ms=125.5,
        ...     memory_peak_mb=45.2,
        ...     iterations=1000,
        ...     avg_duration_ms=0.125,
        ...     min_duration_ms=0.05,
        ...     max_duration_ms=2.1,
        ...     p95_duration_ms=0.8,
        ...     p99_duration_ms=1.5,
        ...     std_dev_ms=0.3,
        ...     operations_per_second=8000.0,
        ...     success_rate=1.0,
        ...     memory_usage_mb=42.1
        ... )
        >>> print(result.performance_grade())
        >>> print(result.meets_threshold(1.0))
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert benchmark result to dictionary for serialization.
        
        Returns:
            Dictionary representation of all benchmark data
        """
        ...

    def meets_threshold(self, threshold_ms: float) -> bool:
        """
        Check if benchmark result meets performance threshold.
        
        Args:
            threshold_ms: Maximum acceptable average duration in milliseconds
            
        Returns:
            True if average duration is within threshold, False otherwise
        """
        ...

    def performance_grade(self) -> str:
        """
        Calculate performance grade based on standard thresholds.
        
        Grade categories:
        - Excellent: ≤5ms average
        - Good: ≤25ms average  
        - Acceptable: ≤50ms average
        - Poor: ≤100ms average
        - Critical: >100ms average
        
        Returns:
            Performance grade as string
        """
        ...


@dataclass
class ComparisonResult:
    """
    Result data for comparing performance between cache implementations.
    
    This class provides comprehensive analysis when comparing two cache
    implementations, including performance deltas, regression detection,
    and improvement recommendations.
    
    Attributes:
        original_cache_results: Benchmark results from original implementation
        new_cache_results: Benchmark results from new implementation  
        performance_change_percent: Overall performance change percentage
        memory_change_percent: Memory usage change percentage
        operations_per_second_change: Throughput change
        baseline_cache_name: Name/description of original cache
        comparison_cache_name: Name/description of new cache
        operation_comparisons: Per-operation comparison details
        overall_performance_change: Weighted overall performance delta
        cache_hit_rate_change: Hit rate improvement/degradation
        compression_efficiency_change: Compression improvement
        regression_detected: Whether performance regression was detected
        significant_differences: List of metrics with significant changes
        improvement_areas: Areas where performance improved
        degradation_areas: Areas where performance degraded
        recommendation: Overall recommendation based on analysis
        recommendations: List of specific recommendations
        timestamp: ISO format timestamp of comparison
    
    Example:
        >>> comparison = ComparisonResult(
        ...     original_cache_results=old_result,
        ...     new_cache_results=new_result,
        ...     performance_change_percent=-15.2,  # 15.2% improvement
        ...     memory_change_percent=8.5,         # 8.5% more memory
        ...     operations_per_second_change=18.3  # 18.3% faster throughput
        ... )
        >>> print(comparison.summary())
        >>> print(f"Regression: {comparison.regression_detected}")
    """

    @property
    def is_regression(self) -> bool:
        """
        Check if this comparison indicates a performance regression.
        
        Returns:
            True if regression was detected, False otherwise
        """
        ...

    @property
    def operation_type(self) -> str:
        """
        Get the operation type being compared.
        
        Returns:
            The operation type from the new cache results
        """
        ...

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert comparison result to dictionary for serialization.
        
        Returns:
            Dictionary representation of all comparison data
        """
        ...

    def summary(self) -> str:
        """
        Generate human-readable summary of comparison results.
        
        Returns:
            Concise summary string describing the performance comparison
        """
        ...

    def generate_recommendations(self) -> List[str]:
        """
        Generate performance recommendations based on comparison results.
        
        Returns:
            List of recommendation strings based on detected changes
        """
        ...


@dataclass
class BenchmarkSuite:
    """
    Collection of benchmark results with comprehensive analysis.
    
    This class aggregates multiple benchmark results into a cohesive
    analysis, providing overall performance grading, success rates,
    and suite-level metrics.
    
    Attributes:
        name: Descriptive name for the benchmark suite
        results: List of individual benchmark results
        total_duration_ms: Total time for all benchmarks
        pass_rate: Percentage of benchmarks that passed (0-1)
        failed_benchmarks: List of benchmark names that failed
        performance_grade: Overall performance grade for the suite
        memory_efficiency_grade: Overall memory efficiency grade
        timestamp: ISO format timestamp of suite execution
        environment_info: Information about test environment
    
    Example:
        >>> suite = BenchmarkSuite(
        ...     name="Redis Cache Performance",
        ...     results=[result1, result2, result3],
        ...     total_duration_ms=1250.5,
        ...     pass_rate=1.0,
        ...     failed_benchmarks=[],
        ...     performance_grade="Good",
        ...     memory_efficiency_grade="Excellent"
        ... )
        >>> score = suite.calculate_overall_score()
        >>> get_result = suite.get_operation_result("get")
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert benchmark suite to dictionary for serialization.
        
        Returns:
            Dictionary representation of all benchmark suite data
        """
        ...

    def to_json(self) -> str:
        """
        Serialize benchmark suite to JSON string.
        
        Returns:
            JSON string representation of the entire benchmark suite
        """
        ...

    def get_operation_result(self, operation_type: str) -> Optional[BenchmarkResult]:
        """
        Get benchmark result for specific operation type.
        
        Args:
            operation_type: The operation type to search for (e.g., "get", "set")
            
        Returns:
            BenchmarkResult for the operation if found, None otherwise
        """
        ...

    def calculate_overall_score(self) -> float:
        """
        Calculate overall performance score (0-100).
        
        The score is a weighted combination of:
        - Timing performance (50% weight)
        - Success rate (30% weight)  
        - Memory efficiency (20% weight)
        
        Returns:
            Overall score from 0-100, where 100 is optimal performance
        """
        ...
